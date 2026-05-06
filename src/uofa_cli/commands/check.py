"""uofa check — run the full C1+C2+C3 pipeline on a UofA file.

Spec v0.4 §4.1: `run_structured(args)` returns a typed `CheckResult` that
composes the sub-results from shacl + integrity + rules. `run(args)` is the
I/O shell — preserved bit-for-bit (same step headers, same result lines).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from uofa_cli.output import header, step_header, result_line
from uofa_cli.shacl_friendly import run_shacl_multi, print_results
from uofa_cli.integrity import verify_file
from uofa_cli import paths
from uofa_cli.commands.shacl import ShaclResult
from uofa_cli.commands.rules import RulesResult
from uofa_cli.oos import config as oos_config
from uofa_cli.oos import runner as oos_runner
from uofa_cli.derivations import config as derivation_config
from uofa_cli.derivations import runner as derivation_runner

HELP = "full pipeline: SHACL + integrity + rules (C1+C2+C3)"


@dataclass(frozen=True)
class IntegrityResult:
    """Hash + signature verification outcome (C1).

    `pubkey_found` is False when the user passed a non-existent --pubkey or
    no default key is on disk; `hash_ok` and `sig_ok` are then meaningless
    and set to False to keep the overall result False.
    """

    pubkey_path: Path
    pubkey_found: bool
    hash_ok: bool
    sig_ok: bool

    @property
    def ok(self) -> bool:
        return self.pubkey_found and self.hash_ok and self.sig_ok


@dataclass(frozen=True)
class CheckResult:
    """Composed result of all three pipeline steps.

    `rules` is None when --skip-rules was passed (matches current
    `results["C3 Rules"] = None` behavior). `rules_error` carries the
    truncated error message that the printer currently emits when the rule
    engine isn't available — preserved here so `run_structured` consumers
    don't have to re-derive it from raw exceptions.
    """

    file: Path
    shacl: ShaclResult
    integrity: IntegrityResult
    rules: RulesResult | None
    rules_error: str | None
    all_ok: bool
    # OOS phase added in productionization v0.1 (T7). None when OOS is
    # disabled for the active pack — snapshot.py omits the field entirely
    # to preserve byte-identical compatibility with pre-OOS baselines per
    # spec §1.4 / §5.5. Set to an OOSResult when enabled (whether or not
    # the engine produced any firings).
    oos: oos_runner.OOSResult | None = None
    # Captured OOSConfigError message when --oos was requested but the
    # active pack doesn't declare rule files (or other resolver errors).
    # The CLI handler prints this and exits non-zero before any OOS work.
    oos_error: str | None = None
    # Derivation pre-pass (v0.5). None when no active pack declares
    # derivations — snapshot.py omits the field entirely (preserves
    # byte-identical compat for vv40, nasa-7009b, and other non-adopting
    # packs). Set to a DerivationResult when enabled.
    derivations: derivation_runner.DerivationResult | None = None
    derivations_error: str | None = None

    @property
    def exit_code(self) -> int:
        return 0 if self.all_ok else 1


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to check")
    parser.add_argument("--pubkey", type=Path, help="ed25519 public key")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--rules", "-r", type=Path, help="path to .rules file")
    parser.add_argument("--skip-rules", action="store_true", help="skip the Jena rule engine (no Java required)")
    parser.add_argument("--build", action="store_true", help="auto-build the Jena JAR if missing")
    # Productive-OOS gating per spec §1.8. Default behaviour comes from the
    # active pack's `oos.enabled` config (or false if the section is absent).
    oos_group = parser.add_mutually_exclusive_group()
    oos_group.add_argument(
        "--oos", dest="enable_oos", action="store_true",
        help="force OOS rules on for this run, overriding pack config",
    )
    oos_group.add_argument(
        "--no-oos", dest="disable_oos", action="store_true",
        help="force OOS rules off for this run, overriding pack config",
    )
    # Derivation pre-pass gating per UofA_Derivation_PrePass_Spec_v0_1.md §2.2.
    # Default behaviour comes from the active pack's `derivations.enabled`
    # config (or false if the section is absent — preserves byte-identical
    # behavior for packs that don't declare derivations).
    derive_group = parser.add_mutually_exclusive_group()
    derive_group.add_argument(
        "--derivations", dest="enable_derivations", action="store_true",
        help="force derivation pre-pass on for this run, overriding pack config",
    )
    derive_group.add_argument(
        "--no-derivations", dest="disable_derivations", action="store_true",
        help="force derivation pre-pass off for this run, overriding pack config",
    )
    from uofa_cli.interpretation.cli import add_explain_arguments
    add_explain_arguments(parser)


def run_structured(args) -> CheckResult:
    """Compose shacl + integrity + rules into a typed CheckResult.

    Does NOT print — `run()` is the I/O shell. The interpretation pipeline
    consumes `result.shacl.violations` + `result.rules.firings` to feed the
    per-section `--explain` (spec §4.5: check carries the full breakdown).
    """
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    ctx = args.context or paths.context_file()

    # ── C2: SHACL ─────────────────────────────────────────────
    shacl_paths = paths.all_shacl_schemas()
    conforms, violations = run_shacl_multi(args.file, shacl_paths)
    shacl_result = ShaclResult(
        file=args.file,
        conforms=bool(conforms),
        violations=list(violations),
        exit_code=0 if conforms else 1,
    )

    # ── C1: Integrity ─────────────────────────────────────────
    pubkey = args.pubkey or paths.default_pubkey()
    if pubkey.exists():
        hash_ok, sig_ok = verify_file(args.file, pubkey, ctx)
        integrity_result = IntegrityResult(
            pubkey_path=pubkey,
            pubkey_found=True,
            hash_ok=bool(hash_ok),
            sig_ok=bool(sig_ok),
        )
    else:
        integrity_result = IntegrityResult(
            pubkey_path=pubkey,
            pubkey_found=False,
            hash_ok=False,
            sig_ok=False,
        )

    # ── C2.5: Derivation pre-pass (v0.5) ──────────────────────
    # Per UofA_Derivation_PrePass_Spec_v0_1.md §2.1. Runs SPARQL CONSTRUCT
    # queries against the loaded JSON-LD package, materializing derived
    # analytic predicates that downstream C3 + OOS engines can discriminate
    # on. When no active pack declares derivations, this is a no-op and
    # downstream stages see the original args.file path (preserving
    # byte-identical backward compat for vv40, nasa-7009b, and any other
    # pack that doesn't declare derivations).
    derivation_result: derivation_runner.DerivationResult | None = None
    derivation_error: str | None = None
    effective_package = args.file  # default: no derivation, use original
    if not args.skip_rules:
        active_packs = paths.get_active_pack() or ["vv40"]
        pack_for_derive = active_packs[0]
        try:
            derive_cfg = derivation_config.resolve(
                pack_for_derive,
                enable_flag=getattr(args, "enable_derivations", False),
                disable_flag=getattr(args, "disable_derivations", False),
            )
            derivation_result = derivation_runner.run(
                args.file, derive_cfg, context_path=args.context,
            )
            if (derivation_result is not None
                and derivation_result.enriched_package_path is not None):
                effective_package = derivation_result.enriched_package_path
        except derivation_config.DerivationConfigError as exc:
            derivation_error = str(exc).split("\n")[0]
        except (FileNotFoundError, RuntimeError) as exc:
            derivation_error = str(exc).split("\n")[0]

    # ── C3: Rules ─────────────────────────────────────────────
    rules_result: RulesResult | None = None
    rules_error: str | None = None

    if not args.skip_rules:
        from uofa_cli.commands import rules as rules_mod
        rules_args = argparse.Namespace(
            file=effective_package,  # may be enriched .nt when pre-pass ran
            rules=args.rules,
            context=args.context,
            build=args.build,
            raw=False,
            format="summary",
            output=None,
        )
        try:
            rules_result = rules_mod.run_structured(rules_args)
        except FileNotFoundError as exc:
            # Java/JAR not available — match the existing single-line error
            rules_error = str(exc).split("\n")[0]
        except RuntimeError as exc:
            rules_error = str(exc).split("\n")[0]

    # ── OOS phase (productionization v0.1, T7) ────────────────
    # Gated by pack-level config (oos.enabled in pack.json) plus the
    # CLI flags --oos / --no-oos per spec §1.7 / §1.8. When disabled,
    # `oos_result` stays None and snapshot.py omits the field entirely
    # to preserve byte-identical compatibility with pre-OOS baselines.
    oos_result: oos_runner.OOSResult | None = None
    oos_error: str | None = None
    if not args.skip_rules:
        active_packs = paths.get_active_pack() or ["vv40"]
        pack_for_oos = active_packs[0]
        try:
            oos_cfg = oos_config.resolve(
                pack_for_oos,
                enable_flag=getattr(args, "enable_oos", False),
                disable_flag=getattr(args, "disable_oos", False),
            )
            oos_result = oos_runner.run_structured(
                effective_package, oos_cfg, context_path=args.context,
            )
        except oos_config.OOSConfigError as exc:
            oos_error = str(exc).split("\n")[0]
        except (FileNotFoundError, RuntimeError) as exc:
            oos_error = str(exc).split("\n")[0]

    # Cleanup: delete the temp enriched file produced by the derivation
    # pre-pass. C3 and OOS have finished reading it by this point.
    if (derivation_result is not None
        and derivation_result.enriched_package_path is not None):
        derivation_result.enriched_package_path.unlink(missing_ok=True)

    # ── Aggregate ─────────────────────────────────────────────
    all_ok = shacl_result.conforms and integrity_result.ok
    if rules_result is not None:
        all_ok = all_ok and rules_result.returncode == 0
    elif rules_error is not None:
        # Rule engine attempted but failed — counts as not-ok.
        all_ok = False
    # rules_result is None and rules_error is None → --skip-rules path,
    # which doesn't impact all_ok (matches existing behavior).

    # OOS errors surface but only impact all_ok when OOS was explicitly
    # requested via --oos. A pack-config-driven OOS that fails is logged
    # but doesn't fail the pipeline (defensive — bad pack config shouldn't
    # break C1+C2+C3 reporting).
    if oos_error is not None and getattr(args, "enable_oos", False):
        all_ok = False
    # An OOSResult with non-zero returncode means the engine itself failed;
    # treat as not-ok regardless of how OOS was activated.
    if oos_result is not None and oos_result.returncode != 0:
        all_ok = False

    return CheckResult(
        file=args.file,
        shacl=shacl_result,
        integrity=integrity_result,
        rules=rules_result,
        rules_error=rules_error,
        all_ok=all_ok,
        oos=oos_result,
        oos_error=oos_error,
        derivations=derivation_result,
        derivations_error=derivation_error,
    )


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    results: dict[str, bool | None] = {}

    # ── C2: SHACL ─────────────────────────────────────────────
    step_header("C2: SHACL profile validation")
    shacl_paths = paths.all_shacl_schemas()
    conforms, violations = run_shacl_multi(args.file, shacl_paths)
    print_results(conforms, violations)
    results["C2 SHACL"] = conforms

    # ── C1: Integrity ─────────────────────────────────────────
    ctx = args.context or paths.context_file()
    step_header("C1: Integrity verification (hash + signature)")
    pubkey = args.pubkey or paths.default_pubkey()
    if pubkey.exists():
        hash_ok, sig_ok = verify_file(args.file, pubkey, ctx)
        result_line("Hash match", hash_ok)
        result_line("Signature valid", sig_ok)
        results["C1 Integrity"] = hash_ok and sig_ok
    else:
        result_line("Integrity check", False, f"public key not found: {pubkey}")
        results["C1 Integrity"] = False

    # ── C3: Rules ─────────────────────────────────────────────
    import sys
    sys.stdout.flush()
    if args.skip_rules:
        results["C3 Rules"] = None
    else:
        from uofa_cli.commands import rules as rules_mod
        rules_args = argparse.Namespace(
            file=args.file,
            rules=args.rules,
            context=args.context,
            build=args.build,
            raw=False,
            format="summary",
            output=None,
        )
        try:
            rc = rules_mod.run(rules_args)
            results["C3 Rules"] = (rc == 0)
        except FileNotFoundError as exc:
            result_line("Rule engine", False, str(exc).split("\n")[0])
            results["C3 Rules"] = False

    # ── Summary ───────────────────────────────────────────────
    header(f"Summary: {args.file.name}")
    all_ok = True
    for label, ok in results.items():
        if ok is None:
            result_line(label, True, "skipped")
        else:
            result_line(label, ok)
            if not ok:
                all_ok = False

    # ── --explain pipeline (spec §3.1) ────────────────────────
    # Per spec §2.6, check supports all five functions; in P-B only `explain`
    # is implemented. Runs over both rules firings and shacl violations.
    if getattr(args, "explain", False):
        rules_firings = []
        # Re-run rules.run_structured to get firings (the run() above just
        # printed exit status). Skipped when --skip-rules.
        if not args.skip_rules:
            from uofa_cli.commands import rules as rules_mod
            try:
                rs = rules_mod.run_structured(rules_args)
                rules_firings = rs.firings
            except (FileNotFoundError, RuntimeError):
                pass

        _run_explain(args, conforms=conforms, violations=violations,
                     rules_firings=rules_firings)

    return 0 if all_ok else 1


def _run_explain(args, *, conforms: bool, violations: list,
                 rules_firings: list) -> None:
    """Invoke the interpretation pipeline for check.

    Round 1: same engine-jsonld re-invocation pattern as rules._run_explain
    so check's `--explain` output also benefits from affected-evidence
    enrichment. Falls back to legacy (no enrichment) if jsonld engine call
    fails.
    """
    import json as _json
    from uofa_cli.interpretation import interpret_check_output
    from uofa_cli.interpretation.cli import (
        args_to_options, print_degradation, print_envelope,
    )
    from uofa_cli.llm.errors import LLMError

    pack_name = (paths.get_active_pack() or ["vv40"])[0]
    try:
        package_doc = _json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print_degradation(
            LLMError(f"Could not load package for interpretation: {exc}"),
            mode="explain", format=args.explain_format or "text",
            command="check", structured_output={},
        )
        return

    # Re-invoke rules engine in jsonld mode for rich firings (P-B Round 1).
    rules_jsonld_firings = None
    rules_individual_annotations = None
    if not args.skip_rules and rules_firings:
        try:
            from uofa_cli.commands import rules as rules_mod
            jsonld_args = argparse.Namespace(
                file=args.file,
                rules=args.rules,
                context=args.context,
                build=args.build,
                raw=False, format="jsonld", output=None,
            )
            jsonld_result = rules_mod.run_structured(jsonld_args)
            if jsonld_result.returncode == 0 and jsonld_result.raw_stdout:
                rules_jsonld_firings = rules_mod.parse_firings_jsonld(jsonld_result.raw_stdout)
                rules_individual_annotations = rules_mod.parse_individual_annotations(
                    jsonld_result.raw_stdout
                )
        except (FileNotFoundError, RuntimeError):
            pass

    structured = {
        "shacl": {"conforms": conforms, "violations": violations},
        "rules": {"firings": rules_firings},
    }
    try:
        env = interpret_check_output(
            structured_output=structured,
            package_doc=package_doc,
            rules_firings=rules_firings,
            rules_jsonld_firings=rules_jsonld_firings,
            rules_individual_annotations=rules_individual_annotations,
            shacl_violations=violations if not conforms else None,
            options=args_to_options(args, pack_name=pack_name),
        )
    except LLMError as exc:
        print_degradation(
            exc, mode="explain", format=args.explain_format or "text",
            command="check", structured_output=structured,
        )
        return

    print_envelope(env, format=args.explain_format or "text")
