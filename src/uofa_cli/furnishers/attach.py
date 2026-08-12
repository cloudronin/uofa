"""Apply operator run-context and furnished evaluation evidence to a bundle.

One place where CLI flags become bundle content, so the report path and any test
exercise the same code. Nothing here judges evidence; it attaches it.

Two kinds of input, kept apart because they are different claims:

  * **Run context** (`--cou`, `--mrl`) -- what the OPERATOR says this assessment
    is scoped to. Stamped `run-context`. Bound to `decisionContextOfUse` and
    `decisionRiskLevel`, deliberately NOT to the model's own `hasContextOfUse` /
    `modelRiskLevel`, which model-credibility bundles already carry with synthesized
    values (a disclosed MRL-3 posture and a COU derived from the model id).
    Keying rules on those would make COMPOUND-EV-01 fire for every model and pin
    W-EV-COU-05 to Critical forever.

  * **Furnished evidence** (`--raidex*`) -- benchmark results about the model,
    from a furnisher. Stamped `extracted` for a published record, `furnished-run`
    for one this assessment generated (A13.3). A reader of the card can tell
    whether section [3] evidence existed before the assessment or was produced
    inside it; both are legitimate and they are not the same claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli.furnishers import pins, raidex

# Provenance classes. The first four are the existing vocabulary; `furnished-run`
# is added by addendum v0.4 A13.3 for evidence generated during the assessment.
PROV_RUN_CONTEXT = "run-context"
PROV_EXTRACTED = "extracted"
PROV_FURNISHED_RUN = "furnished-run"


@dataclass(frozen=True)
class AttachResult:
    """What was attached, for the caller to report honestly."""
    ok: bool
    detail: str = ""
    source: str = ""            # "local" | "hub" | "run" | ""
    n_nodes: int = 0
    coverage: str = ""
    excluded: tuple = ()
    furnisher_version: str = ""
    live_run: bool = False


def _stamp(bundle: dict, field: str, cls: str) -> None:
    """Append a `field=class` provenance entry, replacing any prior one.

    Flat strings, not a nested map: putting vocabulary term names in JSON-LD key
    position once made every package unparseable (see excel_mapper._provenance).
    """
    prov = [p for p in (bundle.get("fieldProvenance") or [])
            if not p.startswith(f"{field}=")]
    prov.append(f"{field}={cls}")
    bundle["fieldProvenance"] = sorted(prov)


def apply_run_context(bundle: dict, *, cou: str | None = None,
                      mrl: int | None = None) -> list[str]:
    """Stamp operator-supplied --cou / --mrl. Returns the fields set.

    Absent flags set nothing at all, which is what makes the honest N/A work: no
    `decisionRiskLevel` triple means COMPOUND-EV-01 structurally cannot match and
    the readout says the escalation was not assessed, rather than the reader
    assuming it ran and passed.
    """
    applied = []
    if cou:
        bundle["decisionContextOfUse"] = cou
        _stamp(bundle, "decisionContextOfUse", PROV_RUN_CONTEXT)
        applied.append("decisionContextOfUse")
    if mrl is not None:
        bundle["decisionRiskLevel"] = int(mrl)
        _stamp(bundle, "decisionRiskLevel", PROV_RUN_CONTEXT)
        applied.append("decisionRiskLevel")
    return applied


def record_hash(record: dict) -> str:
    """Content hash of the raw furnisher output (A13.3).

    Canonical JSON rather than raw bytes, so a record fetched from the hub and
    the same record read from disk hash identically -- the claim being pinned is
    "this content", not "this file".
    """
    canon = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(canon).hexdigest()


def _attach_nodes(bundle: dict, evidence, record: dict, *, live_run: bool,
                  package_version: str = "") -> None:
    bundle["hasValidationResult"] = list(evidence.nodes)
    prov_class = PROV_FURNISHED_RUN if live_run else PROV_EXTRACTED
    _stamp(bundle, "hasValidationResult", prov_class)

    # Bounded reproducibility claim: a furnished score is reproducible only
    # against the furnisher version that produced it (A13.2). For a live run that
    # is BOTH the installed package version and the backend_version in the
    # output -- either alone under-specifies what produced the number.
    version = evidence.backend_version or ""
    if package_version:
        version = f"raidex {package_version} / backend {version}" if version else f"raidex {package_version}"
    if version:
        bundle["furnisherVersion"] = version
        _stamp(bundle, "furnisherVersion", prov_class)

    bundle["furnisherOutputHash"] = record_hash(record)
    _stamp(bundle, "furnisherOutputHash", prov_class)

    # A9.1: a furnished score pins an OCCASION, not an artifact. raidex talks to
    # an endpoint via litellm and never sees weights, so the subject's identity
    # is what the provider asserts -- it can change under a stable name with
    # nothing to diff. Re-running tomorrow is a new occasion even if every byte
    # of the config matches.
    identity = raidex.subject_identity(record)
    subject = identity.get("modelId") or str(bundle.get("id") or "")
    if subject:
        # The record's OWN eval_date, not attach time: the occasion is when the
        # measurement happened, not when we got around to reading it.
        measured = str((record.get("config") or {}).get("eval_date") or "")
        pins.attach(bundle, pins.occasion_pin(
            subject,
            measured_at=measured or datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            version_claim=identity.get("servedName") or "",
            claimed_by="provider",
        ))


def attach_raidex(bundle: dict, *, local_path=None, model_id: str = "",
                  use_hub: bool = False) -> AttachResult:
    """Attach a published raidex record (local file or hub lookup).

    A model absent from the dataset is a stated N/A, not an error: the pack has
    nothing to assess and says so, which is a different claim from finding
    nothing wrong.
    """
    if local_path:
        fetched = raidex.fetch_record("", local_path=Path(local_path))
        source = "local"
    elif use_hub:
        fetched = raidex.fetch_record(model_id)
        source = "hub"
    else:
        return AttachResult(ok=False, detail="no raidex source requested")

    if not fetched.ok:
        return AttachResult(ok=False, detail=fetched.detail, source=source)

    evidence = raidex.furnish(fetched.record, str(bundle.get("id") or ""),
                              fetched.source_url or source)
    _attach_nodes(bundle, evidence, fetched.record, live_run=False)
    return AttachResult(
        ok=True, source=source, n_nodes=len(evidence.nodes),
        coverage=evidence.coverage, excluded=tuple(evidence.excluded),
        furnisher_version=evidence.backend_version, live_run=False,
    )


# ── A13: live run (orchestration, not absorption) ───────────────────────────
#
# UNVERIFIED AGAINST A LIVE RUN. Everything below is exercised through a stubbed
# subprocess only: raidex is an optional dependency and is not installed in the
# development environment. The subprocess contract, the preflight estimate, and
# the local-model path all need a machine with `pip install uofa[raidex]` and
# provider keys before any of this can be called verified.
# Checklist: docs/live-run-verification.md. Do not remove this notice on the
# strength of green unit tests -- they mock the seam this warns about.

RAIDEX_UNVERIFIED = (
    "raidex live-run orchestration has not been verified against a real "
    "`raidex eval`; see docs/live-run-verification.md"
)

# Constituents raidex sweeps, for the preflight statement. Read from the record
# after a run; before one there is nothing to read, so this is the published
# cohort's constituent set and is labelled as an expectation, not a promise.
_KNOWN_CONSTITUENTS = (
    "bbq", "wmdp", "simpleqa", "strongreject", "ethics",
    "xstest", "advglue", "confaide", "sycophancy",
)
_JUDGE_REQUIRED = ("simpleqa", "xstest", "strongreject")


def raidex_installed() -> tuple[bool, str]:
    """(available, version). Never raises; absence is a normal, reportable state."""
    try:
        from importlib.metadata import version
        return True, version("raidex")
    except Exception:
        return False, ""


def preflight_statement(model_ref: str, *, judge: str = "", tier: str = "A+B",
                        runner=None) -> str:
    """What a sweep will do and cost, before it spends anything (A13.4).

    Asks raidex via `--dry-run` rather than inventing a number. raidex knows its
    own constituents, sample sizes and per-benchmark pricing; UofA does not, and
    a second estimator here would drift from the thing it estimates. It also
    reports which constituents will be skipped for want of a judge, and the
    coverage that results -- a partial sweep is honest, and the operator should
    see the coverage before agreeing rather than discover it in the card.

    If the dry run cannot be reached, this says the cost is unknown. It never
    substitutes a guess: an under-stated preflight turns an informed decision
    into a false assurance the operator only tests by spending.
    """
    import subprocess

    cmd = ["raidex", "eval", "--model", model_ref, "--tier", tier, "--dry-run"]
    if judge:
        cmd += ["--judge", judge]
    if runner is None:
        runner = lambda c: subprocess.run(c, capture_output=True, text=True)  # noqa: E731
    try:
        proc = runner(cmd)
    except FileNotFoundError:
        return (f"raidex eval --model {model_ref} --tier {tier}\n"
                "  cost / time  : UNKNOWN - raidex is not installed, so its cost\n"
                "                 estimate could not be obtained.")

    out = ((getattr(proc, "stdout", "") or "") + (getattr(proc, "stderr", "") or "")).strip()
    if getattr(proc, "returncode", 1) != 0 or not out:
        return (f"raidex eval --model {model_ref} --tier {tier}\n"
                "  cost / time  : UNKNOWN - raidex's own dry run did not report one.\n"
                "                 Proceeding means agreeing to an unbounded spend.")
    body = "\n".join(f"  {line}" for line in out.splitlines())
    note = "\n  NOTE: costs are raidex's estimate, not a quote. Time is not estimated."

    # A zero total is almost never true; it means litellm had no pricing for the
    # model. litellm returns (0, 0) for an unknown model rather than raising, so
    # raidex's no-pricing fallback never fires and the estimate reads $0.00 for a
    # sweep the provider will bill. Relaying that unchallenged is the exact
    # under-stated preflight this whole step exists to prevent, so say so.
    total = next((ln for ln in out.splitlines() if "TOTAL" in ln.upper()), "")
    if total and _looks_like_zero(total):
        note = ("\n  WARNING: the estimate is $0.00, which almost certainly means no"
                "\n  pricing is known for this model, NOT that the sweep is free."
                "\n  Treat the cost as UNKNOWN and bound it with --limit." + note)
    return (f"raidex eval --model {model_ref} --tier {tier}   [raidex --dry-run]\n"
            + body + note)


def _looks_like_zero(total_line: str) -> bool:
    import re
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)", total_line)
    return m is not None and float(m.group(1)) == 0.0





def run_raidex(bundle: dict, model_ref: str, *, extra_args: str = "",
               tier: str = "A+B", judge: str = "", runner=None, workdir=None) -> AttachResult:
    """Run `raidex eval` and attach its output (A13.2).

    Orchestration, not absorption: raidex writes results.json and the SAME Phase-2
    adapter ingests it, unchanged. If this ever needs adapter changes, the
    "same code path as --raidex <path>" claim is false and the spec is wrong.

    `runner` is the subprocess seam, injectable for tests. Tests that pass one are
    testing this function's orchestration, NOT raidex -- see RAIDEX_UNVERIFIED.

    A live run gets no severity discount: freshly furnished evidence with no null
    baseline still trips W-EV-NULL-04. Nothing here touches severity.
    """
    import subprocess
    import tempfile

    available, package_version = raidex_installed()
    if runner is None and not available:
        return AttachResult(
            ok=False, source="run",
            detail="raidex is not installed - `pip install uofa[raidex]`. "
                   "--raidex <path> and --raidex-hub still work.")

    out_dir = Path(workdir or tempfile.mkdtemp(prefix="uofa-raidex-"))
    out_path = out_dir / "results.json"
    # Verified against raidex 0.1.4: --model is a required NAMED flag (not
    # positional) and the output flag is --output (not --out). The stubbed
    # version of this had both wrong and passed, because a stub that ignores
    # argv cannot falsify argv.
    cmd = ["raidex", "eval", "--model", model_ref, "--output", str(out_path)]
    cmd += ["--tier", tier]
    if judge:
        cmd += ["--judge", judge]
    if extra_args:
        cmd += extra_args.split()

    if runner is None:
        runner = lambda c: subprocess.run(c, capture_output=True, text=True)  # noqa: E731
    proc = runner(cmd)

    rc = getattr(proc, "returncode", 1)
    if rc != 0:
        # raidex's own stderr, not a paraphrase: the furnisher knows why it
        # failed and swallowing that leaves the operator guessing.
        err = (getattr(proc, "stderr", "") or "").strip()
        return AttachResult(ok=False, source="run",
                            detail=f"raidex eval exited {rc}" + (f":\n{err}" if err else ""))
    if not out_path.exists():
        return AttachResult(ok=False, source="run",
                            detail=f"raidex eval reported success but wrote no {out_path.name}")

    fetched = raidex.fetch_record("", local_path=out_path)
    if not fetched.ok:
        return AttachResult(ok=False, source="run",
                            detail=f"raidex output not ingestible: {fetched.detail}")

    evidence = raidex.furnish(fetched.record, str(bundle.get("id") or ""), str(out_path))
    if not evidence.nodes:
        # The sweep ran and furnished nothing usable. Reporting success here made
        # the readout say "no reported evaluation to assess", which is a
        # different and much more reassuring claim than "the sweep failed".
        reasons = ", ".join(sorted({e["reason"] for e in evidence.excluded})) or "unknown"
        return AttachResult(
            ok=False, source="run", coverage=evidence.coverage,
            excluded=tuple(evidence.excluded), live_run=True,
            detail=(f"raidex ran but furnished no usable results "
                    f"(coverage {evidence.coverage}; "
                    f"{len(evidence.excluded)} constituent(s) failed: {reasons})"))
    _attach_nodes(bundle, evidence, fetched.record, live_run=True,
                  package_version=package_version)
    return AttachResult(
        ok=True, source="run", n_nodes=len(evidence.nodes), coverage=evidence.coverage,
        excluded=tuple(evidence.excluded), furnisher_version=package_version, live_run=True,
    )


def resolve_source_flags(args) -> tuple[str, str]:
    """Which furnisher source the flags select, or an error (A13.7.4).

    Returns (source, error). Mutually exclusive by construction: silently
    preferring one over another would make the card's provenance line -- which
    states whether evidence was published or generated here -- a guess.
    """
    chosen = [name for name, on in (
        ("local", bool(getattr(args, "raidex", None))),
        ("hub", bool(getattr(args, "raidex_hub", False))),
        ("run", bool(getattr(args, "raidex_run", False))),
    ) if on]
    if len(chosen) > 1:
        flags = {"local": "--raidex", "hub": "--raidex-hub", "run": "--raidex-run"}
        return "", ("choose one evidence source: "
                    + ", ".join(flags[c] for c in chosen)
                    + " are mutually exclusive (they make different provenance claims)")
    return (chosen[0] if chosen else ""), ""
