"""Apply operator run-context and furnished evaluation evidence to a bundle.

One place where CLI flags become bundle content, so the report path and any test
exercise the same code. Nothing here judges evidence; it attaches it.

Two kinds of input, kept apart because they are different claims:

  * **Run context** (`--cou`, `--mrl`) -- what the OPERATOR says this assessment
    is scoped to. Stamped `run-context`. Bound to `decisionContextOfUse` and
    `decisionRiskLevel`, deliberately NOT to the model's own `hasContextOfUse` /
    `modelRiskLevel`, which mrm-nist bundles already carry with synthesized
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
from pathlib import Path

from uofa_cli.furnishers import raidex

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


def preflight_statement(model_ref: str, *, judge: str = "") -> str:
    """What a sweep will do, before it spends anything (A13.4).

    Deliberately states no cost or duration number. The estimate has never been
    checked against a real sweep, and a preflight that under-states spend is
    worse than none: it converts an informed decision into a false assurance and
    the user only discovers the truth mid-run. It lists what WILL happen -- which
    is checkable now -- and says plainly that the magnitude is unknown.
    """
    judged = ", ".join(_JUDGE_REQUIRED)
    lines = [
        f"raidex eval {model_ref}",
        f"  constituents : {len(_KNOWN_CONSTITUENTS)} ({', '.join(_KNOWN_CONSTITUENTS)})",
        f"  judge needed : {judged}" + (f"  [judge: {judge}]" if judge else "  [no judge configured]"),
        "  cost / time  : NOT ESTIMATED. A full sweep is hours of inference and",
        "                 real judge spend. This tool has no measured basis for a",
        "                 number and will not invent one.",
        "  partial runs : permitted and honest - skipped constituents lower",
        "                 rai_coverage rather than failing or leaving silent gaps.",
    ]
    return "\n".join(lines)


def run_raidex(bundle: dict, model_ref: str, *, extra_args: str = "",
               runner=None, workdir=None) -> AttachResult:
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
    cmd = ["raidex", "eval", model_ref, "--out", str(out_path)]
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
