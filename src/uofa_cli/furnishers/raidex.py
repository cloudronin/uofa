"""raidex furnisher adapter: raidex per-model output -> ValidationResult nodes.

raidex (raidex.ai, `pip install raidex`) measures a model against nine
constituent benchmarks and publishes one JSON record per model. This module maps
such a record onto the `uofa:ValidationResult` nodes the Group-B sufficiency
layer assesses -- the SAME node type vv40 uses for a simulation validation study,
because a benchmark result is validation evidence about a model, not a new kind
of thing.

**Deterministic, no backend.** Reading `results.bbq.raw["acc_stderr,none"]` is a
field read; it infers nothing, so it needs no LLM and stamps `extracted`. That is
the input-type split in the pack spec's extraction section: structured furnisher
output reads directly, prose still requires a backend. What the rule forbids is a
*plausible inferred value* passing as read evidence, and nothing here is inferred.

**The furnisher/assessor firewall.** raidex furnishes the number; the pack
assesses whether that number is sufficient evidence for a decision. This module
lives strictly on the furnishing side: it copies what the record says and omits
what it does not, and it never decides whether a score is good enough. A raidex
number can be clean and still trip W-EV-COU-05.

**Absence is omission, never a falsy value.** Every Group-B rule tests
`noValue(...)`. Emitting `false`, `0`, `"N/A"`, or `"unknown"` would make the
triple exist and silence the rule -- satisfying a constraint with a plausible
value, which AGENTS.md §13 identifies as the defect that rewards fabrication and
punishes accuracy. If the record does not carry a property, the key is absent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HUB_REPO = "cloudronin/raidex-results"
HUB_URL = f"https://huggingface.co/datasets/{HUB_REPO}"

# The nine constituents, in the order the report and card present them.
CONSTITUENTS = (
    "bbq", "wmdp", "simpleqa", "strongreject", "ethics",
    "xstest", "advglue", "confaide", "sycophancy",
)

# Human-facing constituent names. Kept here rather than derived from the key so a
# rename upstream is a visible diff, not a silently changed label.
CONSTITUENT_NAMES = {
    "bbq": "BBQ", "wmdp": "WMDP", "simpleqa": "SimpleQA",
    "strongreject": "StrongREJECT", "ethics": "ETHICS", "xstest": "XSTest",
    "advglue": "AdvGLUE", "confaide": "ConfAIde", "sycophancy": "Sycophancy",
}

# Exclusion classes for a constituent raidex could not score.
#
# The record's `error` is a raw harness traceback carrying the operator's
# absolute filesystem paths (`/Users/<name>/Documents/raidex-mono/...`). These
# bundles get published to uofa.net, so the traceback is CLASSIFIED and never
# copied: republishing a third party's directory structure is not a thing an
# assessment tool should do on the way to reporting a coverage gap.
# Ordered most-specific-first; the first match wins.
_EXCLUSION_CLASSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("connection-error", ("serverdisconnected", "connectionerror", "aiohttp", "econnreset")),
    ("timeout", ("timeout", "timed out")),
    ("judge-unavailable", ("no judge", "judge not configured", "judge unavailable")),
    ("harness-error", ("lm_eval", "lm-eval", "traceback")),
)
_UNCLASSIFIED = "unclassified-error"

# A stderr value must be a real number to count. raidex writes the *string*
# "N/A" for sub-scores it did not compute, and `null` for others; both mean
# absent. Reading "N/A" as a value would silence W-AL-01 on a result that has no
# uncertainty at all -- the precise inversion this pack exists to catch.
_MISSING_SENTINELS = frozenset({"n/a", "na", "none", "null", "", "-"})


@dataclass(frozen=True)
class RaidexFetch:
    """Outcome of locating a raidex record. Never raises past this boundary."""
    record: dict[str, Any] | None
    status: str            # "ok" | "notfound" | "unreadable" | "schema" | "error"
    detail: str = ""
    source_url: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True)
class FurnishedEvidence:
    """ValidationResult nodes plus what could not be furnished, and why."""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[dict[str, str]] = field(default_factory=list)
    coverage: str = ""          # e.g. "8/9", verbatim from the record
    coverage_pct: int | None = None
    backend_version: str = ""
    eval_date: str = ""
    source_url: str = ""
    dimension_scores: dict[str, float] = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)


def _classify_exclusion(error: Any) -> str:
    """Map a raw harness error to a short class. Never returns the raw text."""
    text = str(error or "").lower()
    if not text:
        return _UNCLASSIFIED
    for label, keywords in _EXCLUSION_CLASSES:
        if any(k in text for k in keywords):
            return label
    return _UNCLASSIFIED


def _as_number(value: Any) -> float | None:
    """Return a real number, or None. Strings that merely look like absence -- and
    strings generally -- are absence; only an actual int/float counts."""
    if isinstance(value, bool):           # bool is an int subclass; never a score
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip().lower() in _MISSING_SENTINELS:
        return None
    return None


def _find_stderr(raw: Any) -> tuple[float, str] | None:
    """Locate a genuine standard error inside a constituent's `raw` block.

    Returns (value, key_path) or None. Across the published cohort only `bbq`
    carries one -- its `raw.bbq_generate["acc_stderr,none"]` is a float while its
    26 sub-scores carry the string "N/A". That asymmetry is why W-AL-01 fires
    selectively instead of uniformly, so this function must keep distinguishing
    the two rather than treating any stderr-shaped key as present.
    """
    found: list[tuple[str, float]] = []

    def walk(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif "stderr" in path.lower():
            num = _as_number(node)
            if num is not None:
                found.append((path, num))

    walk(raw or {})
    if not found:
        return None
    # Prefer the primary accuracy stderr over any per-subgroup one.
    for path, num in found:
        if "acc_stderr" in path:
            return (num, path)
    path, num = found[0]
    return (num, path)


def fetch_record(model_id: str, local_path: str | Path | None = None) -> RaidexFetch:
    """Locate a raidex record, locally or from the published dataset.

    `model_id` is the raidex `config.model_id` form (`openai/gpt-5.6`), which maps
    to the flat dataset filename `openai__gpt-5.6.json`.

    A model absent from the dataset is `notfound`, not an error: most models have
    no raidex run, and the honest readout for that is "no reported evaluation to
    assess", not a failure. Schema drift is reported as `schema` and names the
    missing key -- the dataset has already shifted once (a `judge` field broke its
    own viewer), so drift is demonstrated rather than hypothetical.
    """
    if local_path is not None:
        p = Path(local_path)
        if not p.exists():
            return RaidexFetch(None, "notfound", f"{p} does not exist.", str(p))
        try:
            record = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            return RaidexFetch(None, "unreadable", f"{type(exc).__name__}: {exc}", str(p))
        return _validate_shape(record, str(p))

    filename = f"{model_id.replace('/', '__')}.json"
    url = f"{HUB_URL}/resolve/main/{filename}"
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        return RaidexFetch(None, "error",
                           "huggingface_hub is not installed (pip install huggingface_hub).",
                           url)
    try:
        path = hf_hub_download(repo_id=HUB_REPO, filename=filename, repo_type="dataset")
    except Exception as exc:  # network boundary: classify, never leak past here
        name = type(exc).__name__
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if "EntryNotFound" in name or "NotFound" in name or code == 404:
            return RaidexFetch(None, "notfound",
                               f"{model_id} has no published raidex evaluation.", url)
        return RaidexFetch(None, "error", f"{name}: {exc}", url)

    try:
        record = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return RaidexFetch(None, "unreadable", f"{type(exc).__name__}: {exc}", url)
    return _validate_shape(record, url)


def _validate_shape(record: Any, source_url: str) -> RaidexFetch:
    """Confirm the three top-level blocks exist before anything reads them."""
    if not isinstance(record, dict):
        return RaidexFetch(None, "schema",
                           f"expected a JSON object, got {type(record).__name__}.", source_url)
    missing = [k for k in ("config", "results", "composite") if k not in record]
    if missing:
        return RaidexFetch(None, "schema",
                           f"record is missing top-level {', '.join(missing)} "
                           f"(raidex schema drift?).", source_url)
    return RaidexFetch(record, "ok", "", source_url)


def _generating_activity(base: str, slug: str, entry: dict[str, Any],
                         config: dict[str, Any]) -> dict[str, Any]:
    """The raidex run that produced a number, as a prov:Activity.

    This is furnished provenance, not a formality. raidex records when each
    constituent ran, on what backend version, by what route, and under which
    judge where one was used -- so a ValidationResult built from it genuinely
    has a generating activity, and omitting the link would make core's W-EP-02
    report "no provenance chain" about evidence that carries one. A false
    finding is worse than a missed one: it spends the reader's trust on a gap
    that is not there, and every other finding on the page is priced off that
    trust.
    """
    activity: dict[str, Any] = {
        "id": f"{base}/validation/raidex-{slug}/activity",
        "type": "prov:Activity",
        "activityType": "raidex evaluation run",
    }
    when = entry.get("eval_date") or config.get("eval_date")
    if when:
        activity["endedAtTime"] = str(when)
    source = entry.get("eval_source")
    if source:
        activity["description"] = f"raidex {source} run"
    judge = entry.get("judge_model")
    if judge:
        activity["description"] = (
            f"{activity.get('description', 'raidex run')}, judged by {judge}"
        )
    return activity


def _constituent_node(base: str, key: str, entry: dict[str, Any],
                      config: dict[str, Any]) -> dict[str, Any]:
    """Build one ValidationResult from one scored constituent."""
    label = CONSTITUENT_NAMES.get(key, key)
    normalized = _as_number(entry.get("normalized"))
    n_samples = entry.get("n_samples")
    n_failed = entry.get("n_failed")

    node: dict[str, Any] = {
        # Which side of the record this came from. W-EV-COR-09 and W-EV-DIV-07
        # both key on telling a furnished measurement from a self-reported score;
        # without it COR-09 cannot bind a furnished result and never fires.
        "evidenceSource": "furnished",
        "id": f"{base}/validation/raidex-{key}",
        "type": "ValidationResult",
        "name": f"raidex {label}",
        "description": (
            f"{label} measured by raidex over {n_samples} items"
            + (f", {n_failed} failed" if isinstance(n_failed, int) and n_failed else "")
            + "."
        ),
        "wasGeneratedBy": _generating_activity(base, key, entry, config),
    }
    if normalized is not None:
        node["metricValue"] = round(normalized * 100, 2)

    # Uncertainty: core's property, populated ONLY from a genuine numeric stderr.
    # W-EV-UQ-01 was withdrawn so that core's W-AL-01 assesses this, unchanged,
    # on an LLM benchmark exactly as it does on a blood-pump CFD study.
    stderr = _find_stderr(entry.get("raw"))
    if stderr is not None:
        value, key_path = stderr
        node["hasUncertaintyQuantification"] = True
        node["uqMethod"] = (
            f"standard error {round(value * 100, 2)} (normalized 0-100) "
            f"reported as {key_path}"
            + (f" over n={n_samples}" if n_samples else "")
        )

    # Everything else Group B asks for -- a sampling account relating these items
    # to a target population, a determinism floor, a null baseline, a stated
    # context of use, a capability-confound control -- is simply not in the
    # record. Those keys stay absent so the weakeners fire honestly. That gap set
    # is the specification for what a raidex constituent could carry next.
    return node


def _composite_node(base: str, composite: dict[str, Any],
                    config: dict[str, Any]) -> dict[str, Any] | None:
    """Build the ValidationResult for the RAI composite, if one is present."""
    score = _as_number(composite.get("rai_score"))
    if score is None:
        return None
    coverage = composite.get("rai_coverage") or ""
    node: dict[str, Any] = {
        "evidenceSource": "furnished",
        "id": f"{base}/validation/raidex-composite",
        "type": "ValidationResult",
        "name": "raidex RAI composite",
        "description": (
            f"Mean of normalized constituent scores; coverage {coverage}."
            if coverage else "Mean of normalized constituent scores."
        ),
        "metricValue": round(score, 2),
        "wasGeneratedBy": _generating_activity(base, "composite", {}, config),
        # The composite is definitionally a cross-constituent index presented as a
        # general claim about the model. Marking it here -- and ONLY here, never on
        # an individual constituent -- makes COMPOUND-EV-02 fire once per model
        # rather than once per node.
        "generalizedClaim": True,
    }
    return node


def dataset_pin(record: dict[str, Any], constituent: str) -> dict[str, str] | None:
    """The ARTIFACT pin for a constituent's eval data, if the record carries one.

    raidex 0.1.4 records `provenance.datasets[<id>] = {source, revision}`. That is
    an artifact pin in the A9.1 sense: re-fetch the source at the revision and you
    get identical items, so the eval INPUTS are re-derivable.

    Deliberately does NOT feed `samplingAccount`. A pin says which items were
    drawn from which dataset; W-EV-GEN-02 asks how those items relate to the
    target population the score is read against, and how the sample was drawn.
    Those are different questions, and answering the easy one to silence the hard
    one is the "plausible value satisfies a constraint" failure this pack exists
    to catch. The published cohort has no provenance block at all, so this is
    absent there and present only on fresh runs.
    """
    datasets = ((record.get("provenance") or {}).get("datasets") or {})
    pin = datasets.get(constituent)
    if not isinstance(pin, dict) or not pin.get("source"):
        return None
    out = {"source": str(pin["source"])}
    if pin.get("revision"):
        out["revision"] = str(pin["revision"])
    return out


def subject_identity(record: dict[str, Any]) -> dict[str, Any]:
    """How the measured subject is identified, and whether that is verifiable.

    Hosted endpoint -> the identifier is ASSERTED by the provider. It can change
    under a stable name with no notice and nothing to diff, so it is an occasion
    pin (A9.1) and carries no version guarantee. Every such subject trips
    W-EV-SUB-08, which is the honest reading: a closed-weight score is evidence
    about an occasion, not about an artifact.

    raidex never sees weights -- it talks to an endpoint via litellm -- so there
    is no path here to a verified subject identity for a hosted model. A local
    checkpoint pinned by config + weight-manifest hash would carry one, and that
    pin has to come from the operator, not from raidex.
    """
    prov_model = ((record.get("provenance") or {}).get("model") or {})
    config = record.get("config") or {}
    return {
        "modelId": prov_model.get("model_id") or config.get("model_id") or "",
        "servedName": prov_model.get("served_name") or None,
        "apiBase": prov_model.get("api_base") or None,
        # Verifiable immutability is what W-EV-SUB-08 tests for. raidex cannot
        # supply it for a hosted endpoint, and inventing one from the model
        # string would assert an assurance nobody holds.
        "versionGuarantee": None,
    }


def furnish(record: dict[str, Any], base: str, source_url: str = "") -> FurnishedEvidence:
    """Map a validated raidex record onto ValidationResult nodes."""
    results = record.get("results") or {}
    composite = record.get("composite") or {}
    config = record.get("config") or {}

    nodes: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []

    ordered = list(CONSTITUENTS) + [k for k in results if k not in CONSTITUENTS]
    for key in ordered:
        entry = results.get(key)
        if not isinstance(entry, dict):
            continue
        # An excluded constituent carries value/normalized null with a populated
        # `error`. It must NOT become a ValidationResult with a null score: a node
        # asserting "measured, result unknown" is a fabricated measurement. The
        # exclusion is what rai_coverage counts, and reporting it as an exclusion
        # is reporting the composite-exclusion rule working.
        if _as_number(entry.get("normalized")) is None:
            excluded.append({
                "constituent": key,
                "name": CONSTITUENT_NAMES.get(key, key),
                "reason": _classify_exclusion(entry.get("error")),
            })
            continue
        nodes.append(_constituent_node(base, key, entry, config))

    comp = _composite_node(base, composite, config)
    if comp is not None:
        nodes.append(comp)

    raw_pct = _as_number(composite.get("rai_coverage_pct"))
    dims = {k: float(v) for k, v in (composite.get("dimension_scores") or {}).items()
            if _as_number(v) is not None}

    return FurnishedEvidence(
        nodes=nodes,
        excluded=excluded,
        coverage=str(composite.get("rai_coverage") or ""),
        coverage_pct=int(raw_pct) if raw_pct is not None else None,
        backend_version=str(config.get("backend_version") or ""),
        eval_date=str(config.get("eval_date") or ""),
        source_url=source_url,
        dimension_scores=dims,
    )
