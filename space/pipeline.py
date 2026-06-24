"""In-process pipeline: drives uofa extract -> import-mapping -> check.

The Space never shells out to the CLI; it reuses the same functions the CLI
wraps. The one piece of new logic is `result_to_import_dict`, a thin adapter
from the extractor's `ExtractionResult` to the intermediate dict shape that
`excel_mapper.map_to_jsonld` consumes (the Excel round-trip is deliberately
skipped - it is fragile and lossy).

`analyze()` is the orchestration spine. It guarantees:
  * extraction runs in a child process with a hard wall-clock timeout, and a
    timed-out child is terminated (a hung Ollama call can't hold the slot);
  * every failure mode returns a typed `PipelineOutcome.failure(...)` rather
    than raising past the boundary;
  * the per-request temp dir and the extractor's /tmp debug file are torn down
    in `finally`, even on timeout/kill/exception.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from uofa_cli import paths
from uofa_cli.document_reader import ExtractionCorpus, discover_files, read_corpus
from uofa_cli.excel_constants import ALL_FACTOR_CATEGORIES
from uofa_cli.excel_mapper import map_to_jsonld, slugify
from uofa_cli.llm.config import BUNDLED_MODEL
from uofa_cli.llm_extractor import extract as _real_extract

from space import summary as summary_mod

# The extractor writes its raw response here for debugging - a content leak we
# must scrub on every request (see _save_debug_response in llm_extractor.py).
DEBUG_RESPONSE_FILE = Path("/tmp/uofa-extract-last-response.json")

# 12 min: above the ~7-min typical extract, below Ollama's 30-min default.
DEFAULT_EXTRACT_TIMEOUT = 720

# A pubkey path that does not exist, so check skips C1 integrity cleanly
# (the public Space never signs). Using the repo's real key would make
# run_structured attempt signature verification on an unsigned doc.
_NO_PUBKEY = Path("/nonexistent/uofa-space-unsigned.pub")

_CATEGORY_BY_FACTOR = dict(ALL_FACTOR_CATEGORIES)


# ── Typed outcome ─────────────────────────────────────────────


class WeakenerEngineError(RuntimeError):
    """The Jena engine ran but aborted (e.g. a malformed literal) instead of
    emitting a valid JSON-LD result - distinct from the engine being absent."""


class FailureKind:
    EMPTY_FACTORS = "empty_factors"
    EXTRACT_TIMEOUT = "extract_timeout"
    READ_ERROR = "read_error"
    ROUTE_ERROR = "route_error"
    EXTRACT_ERROR = "extract_error"
    VALIDATE_ERROR = "validate_error"
    WEAKENER_ERROR = "weakener_error"
    INTERNAL = "internal"


_USER_MESSAGES = {
    FailureKind.EMPTY_FACTORS: (
        "We couldn't read recognizable credibility factors from these "
        "documents. Check they're the right evidence, or try the sample."
    ),
    FailureKind.EXTRACT_TIMEOUT: (
        "Analysis took too long and was stopped. Try fewer or smaller "
        "documents, or retry."
    ),
    FailureKind.READ_ERROR: (
        "We couldn't read the uploaded documents. Check the file types and "
        "try again."
    ),
    FailureKind.ROUTE_ERROR: (
        "We couldn't determine which standard applies. Please pick one and "
        "retry."
    ),
    FailureKind.EXTRACT_ERROR: (
        "Something went wrong while reading your evidence. Please retry."
    ),
    FailureKind.VALIDATE_ERROR: (
        "We couldn't assemble a valid assurance bundle from the extraction. "
        "Please retry."
    ),
    FailureKind.WEAKENER_ERROR: (
        "The weakener analysis didn't complete on this bundle. Please retry."
    ),
    FailureKind.INTERNAL: "Something went wrong. Please retry, or use the sample.",
}


@dataclass
class PipelineOutcome:
    ok: bool
    payload: dict | None = None
    kind: str | None = None
    user_message: str | None = None

    @classmethod
    def success(cls, payload: dict) -> "PipelineOutcome":
        return cls(ok=True, payload=payload)

    @classmethod
    def failure(cls, kind: str, message: str | None = None) -> "PipelineOutcome":
        return cls(
            ok=False,
            kind=kind,
            user_message=message or _USER_MESSAGES.get(kind, _USER_MESSAGES[FailureKind.INTERNAL]),
        )


# ── Adapter: ExtractionResult -> import dict ─────────────────


def _v(obj):
    """Unwrap a FieldExtraction to its .value (or pass a plain value through)."""
    return getattr(obj, "value", obj)


def _unwrap(d: dict) -> dict:
    return {k: _v(v) for k, v in d.items()}


def _parse_mrl(value) -> int | None:
    """Coerce a model-risk-level value ("MRL 2", "2", 2) to an int, mirroring
    excel_reader._read_summary so modelRiskLevel serializes as a valid xsd:integer
    (a bare string aborts the Jena engine with a DatatypeFormatException)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).upper().replace("MRL", "").strip())
    except (ValueError, TypeError):
        return None


def result_to_import_dict(result, pack: str, factor_edits: dict[str, str] | None = None) -> dict:
    """Map an ExtractionResult to the dict shape `map_to_jsonld` expects.

    `factor_edits` (factor_type -> status) overrides the extracted status for
    confirmed factors - the only user-mutable field in the confirm step.
    Profile is forced to "Complete" so all factors map and the rule engine can
    see unassessed gaps. A `decision.outcome` is synthesized because
    map_to_jsonld requires one; it is NEVER surfaced in the UI.
    """
    factor_edits = factor_edits or {}
    s = _unwrap(result.assessment_summary)
    summary = {
        "project_name": s.get("project_name") or "Uploaded evidence",
        "cou_name": s.get("cou_name") or "Context of use",
        "cou_description": s.get("cou_description"),
        "profile": "Complete",
        "device_class": s.get("device_class"),
        "model_risk_level": _parse_mrl(s.get("model_risk_level")),
        "assurance_level": s.get("assurance_level"),
        "standards_reference": s.get("standards_reference"),
        "assessor_name": s.get("assessor_name"),
        "source_document": s.get("source_document"),
        "has_uq": s.get("has_uq", "No"),
    }

    entities = [e for e in (_unwrap(ent) for ent in result.model_and_data) if e.get("entity_type")]
    validation_results = [_unwrap(vr) for vr in result.validation_results]

    factors = []
    for raw in result.credibility_factors:
        f = _unwrap(raw)
        ftype = f.get("factor_type")
        if not ftype:
            continue
        factors.append({
            "factor_type": ftype,
            "category": _CATEGORY_BY_FACTOR.get(ftype),
            "required_level": f.get("required_level"),
            "achieved_level": f.get("achieved_level"),
            "acceptance_criteria": f.get("acceptance_criteria"),
            "rationale": f.get("rationale"),
            "status": factor_edits.get(ftype, f.get("status") or "not-assessed"),
            "linked_evidence": f.get("linked_evidence"),
        })

    d = _unwrap(result.decision)
    decision = {"outcome": "Not accepted", "rationale": d.get("rationale")}  # synthetic, never shown

    return {
        "summary": summary,
        "entities": entities,
        "validation_results": validation_results,
        "factors": factors,
        "decision": decision,
    }


# ── Subprocess-isolated extraction with a hard timeout ───────


def _silence_llm_logging() -> None:
    """Best-effort: stop litellm from echoing prompts/responses (which contain
    evidence content). Called in the extract child before any model call."""
    try:
        import litellm

        litellm.turn_off_message_logging = True
        litellm.suppress_debug_info = True
    except Exception:
        pass


def _extract_worker(q, extract_fn, corpus, model, pack, prompt_path, llm_config):
    _silence_llm_logging()
    try:
        result = extract_fn(
            corpus,
            model=model,
            pack_name=pack,
            pack_prompt_path=prompt_path,
            thinking=False,
            llm_config=llm_config,
        )
        q.put(("ok", result))
    except BaseException as exc:  # report any failure back to the parent
        q.put(("err", f"{type(exc).__name__}: {exc}"))


def _run_extract(corpus, model, pack, prompt_path, llm_config, timeout, extract_fn):
    """Run extract() in a child process; terminate it if it outlives `timeout`.

    Returns ("ok", ExtractionResult) | ("err", msg) | ("timeout", None).
    ExtractionResult is small (KBs) so the queue put never blocks the child.
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    proc = ctx.Process(
        target=_extract_worker,
        args=(q, extract_fn, corpus, model, pack, prompt_path, llm_config),
    )
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        if proc.is_alive():
            proc.kill()
        return ("timeout", None)
    try:
        return q.get_nowait()
    except Exception:
        return ("err", "extraction produced no result")


def _prompt_path_for(pack: str) -> Path:
    pdir = paths.pack_dir(pack)
    manifest = json.loads((pdir / "pack.json").read_text(encoding="utf-8"))
    return pdir / manifest["prompt"]


def _has_usable_factors(result) -> bool:
    return bool(result.credibility_factors) and any(
        _v(f.get("factor_type")) for f in result.credibility_factors
    )


# ── Validation (SHACL + weakeners) ──────────────────────────


def _run_check(jsonld_path: Path, pack: str):
    """Run SHACL (C2) + integrity (C1, skipped unsigned). Returns (conforms, violations).

    skip_rules=True: weakeners come from the dedicated jsonld pass below, so
    the check step needs no Java and never double-runs the rule engine.
    """
    from uofa_cli.commands import check as check_cmd

    args = argparse.Namespace(
        file=jsonld_path,
        pubkey=_NO_PUBKEY,
        context=None,
        rules=None,
        skip_rules=True,
        build=False,
        active_packs=[pack],
        enable_oos=False,
        disable_oos=False,
        enable_derivations=False,
        disable_derivations=False,
    )
    cr = check_cmd.run_structured(args)
    return cr.shacl.conforms, list(cr.shacl.violations)


def _run_weakeners(jsonld_path: Path, pack: str) -> list[dict]:
    """Rich weakener firings via the Jena engine in jsonld mode.

    Degrades to [] only when Java/JAR are *absent* (the headline still shows
    completeness; weakeners are best-effort where the jar isn't installed).

    A non-zero return code does NOT imply failure - the engine also exits
    non-zero when it successfully *detects* weakeners. The reliable signal that
    the engine aborted (e.g. a DatatypeFormatException on a malformed literal)
    is that stdout is not a valid JSON-LD document; a successful run always
    emits one with an `@graph`, even when zero weakeners fired. An abort raises
    WeakenerEngineError rather than silently reporting "no weakeners".
    """
    from uofa_cli.commands import rules as rules_mod

    args = argparse.Namespace(
        file=jsonld_path,
        rules=None,
        context=None,
        build=False,
        raw=False,
        format="jsonld",
        output=None,
        active_packs=[pack],
    )
    try:
        rr = rules_mod.run_structured(args)
    except (FileNotFoundError, RuntimeError):
        return []  # engine genuinely unavailable - degrade, don't fail

    stdout = rr.raw_stdout or ""
    try:
        doc = json.loads(stdout)
        valid = isinstance(doc, dict) and isinstance(doc.get("@graph"), list)
    except json.JSONDecodeError:
        valid = False
    if not valid:
        stderr_head = (rr.raw_stderr or "").strip().splitlines()
        detail = stderr_head[-1] if stderr_head else "no JSON-LD output"
        raise WeakenerEngineError(
            f"weakener engine aborted (rc={rr.returncode}): {detail}"
        )

    return rules_mod.parse_firings_jsonld(stdout)


def _assign_factor_ids(doc: dict) -> None:
    """Give each credibility factor a stable IRI so weakener affectedNode IRIs
    resolve to factor names (without an @id they serialize as blank nodes)."""
    base = doc.get("id", "")
    for fac in doc.get("hasCredibilityFactor", []):
        if "id" not in fac and fac.get("factorType"):
            fac["id"] = f"{base}/factor/{slugify(fac['factorType'])}"


_PACK_DISPLAY = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B"}


def _authenticity_block() -> dict:
    """The public demo reads evidence live and never signs the bundle, so be
    honest about it. A formally issued package would populate hash/signer and
    flip these booleans; the reviewer view branches on them."""
    return {
        "signed": False,
        "integrity_checked": False,
        "package_hash": None,
        "signer": None,
        "statement": (
            "This evidence was assessed in an unsigned demo, so identity and "
            "tamper-evidence were not verified. A formally issued assurance "
            "package would carry a content hash and a cryptographic signature, "
            "shown here for a reviewer (or a technical colleague) to re-verify."
        ),
    }


def _build_context(summary: dict, pack: str) -> dict:
    """Reviewer-facing context, re-projected from already-extracted fields."""
    return {
        "project_name": summary.get("project_name"),
        "cou_name": summary.get("cou_name"),
        "cou_description": summary.get("cou_description"),
        "standard": _PACK_DISPLAY.get(pack, pack),
        "pack": pack,
        "model_risk_level": summary.get("model_risk_level"),
        "device_class": summary.get("device_class"),
        "assurance_level": summary.get("assurance_level"),
        "standards_reference": summary.get("standards_reference"),
        "authenticity": _authenticity_block(),
    }


def _build_payload(pack, data, shacl_conforms, shacl_violations, firings, warnings) -> dict:
    statuses = {f["factor_type"]: f["status"] for f in data["factors"]}
    payload = summary_mod.compute(
        pack, statuses, {"conforms": shacl_conforms, "violations": shacl_violations}, firings
    )
    payload["context"] = _build_context(data["summary"], pack)
    payload["warnings"] = warnings
    return payload


# ── Composable stages (the wizard drives these with pauses between) ──


class _StageError(Exception):
    """Internal: a stage failed with a known FailureKind."""

    def __init__(self, kind: str, message: str | None = None):
        super().__init__(kind)
        self.kind = kind
        self.message = message


def read_and_route(sources, on_progress=None):
    """Discover + read the corpus (streamed) and route to a primary pack.

    Returns (corpus, RouterDecision, warnings). Raises _StageError(READ_ERROR)
    when nothing readable is found. Cheap relative to extraction.
    """
    from space import router

    progress = on_progress or (lambda _m: None)
    try:
        file_paths, warnings = discover_files([Path(s) for s in sources])
    except Exception as exc:
        raise _StageError(FailureKind.READ_ERROR) from exc
    if not file_paths:
        raise _StageError(FailureKind.READ_ERROR, "No readable documents were found in the upload.")

    corpus = ExtractionCorpus()
    total = len(file_paths)
    for n, fp in enumerate(file_paths, 1):
        progress(f"Reading document {n} of {total}: {fp.name}")
        sub = read_corpus([fp])
        corpus.chunks.extend(sub.chunks)
        corpus.warnings.extend(sub.warnings)
        corpus.file_manifest.extend(sub.file_manifest)
    corpus.total_tokens = sum(c.token_estimate for c in corpus.chunks)
    if not corpus.chunks:
        raise _StageError(
            FailureKind.READ_ERROR, "We couldn't extract any text from the uploaded documents."
        )

    return corpus, router.route(corpus), warnings


def run_extract_stage(
    corpus,
    pack: str,
    *,
    model: str | None = None,
    llm_config=None,
    extract_timeout: int = DEFAULT_EXTRACT_TIMEOUT,
    extract_fn: Callable = _real_extract,
    on_progress=None,
):
    """Extract in an isolated subprocess with a hard timeout. Returns the
    ExtractionResult, or raises _StageError(EXTRACT_TIMEOUT/EXTRACT_ERROR/EMPTY_FACTORS)."""
    progress = on_progress or (lambda _m: None)
    progress(
        "Analyzing your evidence with the model. This runs privately and can "
        "take a few minutes..."
    )
    status, value = _run_extract(
        corpus, model or BUNDLED_MODEL, pack, _prompt_path_for(pack),
        llm_config, extract_timeout, extract_fn,
    )
    if status == "timeout":
        raise _StageError(FailureKind.EXTRACT_TIMEOUT)
    if status != "ok":
        raise _StageError(FailureKind.EXTRACT_ERROR)
    if not _has_usable_factors(value):
        raise _StageError(FailureKind.EMPTY_FACTORS)
    return value


def factor_rows(result) -> list[dict]:
    """Confirm-step rows: one per factor with its extracted status (the only
    editable field) plus read-only context."""
    rows = []
    for raw in result.credibility_factors:
        f = _unwrap(raw)
        if not f.get("factor_type"):
            continue
        rows.append({
            "factor_type": f["factor_type"],
            "status": f.get("status") or "not-assessed",
            "required_level": f.get("required_level"),
            "achieved_level": f.get("achieved_level"),
            "rationale": f.get("rationale"),
        })
    return rows


def finalize(result, pack, factor_edits, work_dir, *, source_name="upload", warnings=None) -> dict:
    """Adapt -> map -> SHACL -> weakeners -> summary. Returns the payload, or
    raises _StageError(VALIDATE_ERROR) / WeakenerEngineError."""
    try:
        data = result_to_import_dict(result, pack, factor_edits)
        doc = map_to_jsonld(data, packs=[pack], source_path=Path(source_name))
        _assign_factor_ids(doc)
        jsonld_path = Path(work_dir) / "uofa.jsonld"
        jsonld_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        shacl_conforms, shacl_violations = _run_check(jsonld_path, pack)
    except WeakenerEngineError:
        raise
    except Exception as exc:
        raise _StageError(FailureKind.VALIDATE_ERROR) from exc

    firings = _run_weakeners(jsonld_path, pack)  # may raise WeakenerEngineError
    return _build_payload(pack, data, shacl_conforms, shacl_violations, firings, warnings or [])


# ── Orchestration spine (all-in-one; used by the sample + spike) ──


def analyze(
    sources: list[Path],
    pack: str,
    *,
    model: str | None = None,
    llm_config=None,
    factor_edits: dict[str, str] | None = None,
    extract_timeout: int = DEFAULT_EXTRACT_TIMEOUT,
    on_progress: Callable[[str], None] | None = None,
    extract_fn: Callable = _real_extract,
    work_dir: Path | None = None,
) -> PipelineOutcome:
    """Run all stages end-to-end. Never raises for expected failures; always
    tears down the temp dir and the extractor's /tmp debug file."""
    progress = on_progress or (lambda _m: None)
    owns_work_dir = work_dir is None
    work_dir = work_dir or Path(tempfile.mkdtemp(prefix="uofa-space-"))

    try:
        corpus, _decision, warnings = read_and_route(sources, on_progress=progress)
        result = run_extract_stage(
            corpus, pack, model=model, llm_config=llm_config,
            extract_timeout=extract_timeout, extract_fn=extract_fn, on_progress=progress,
        )
        progress("Checking completeness and weakeners...")
        source_name = str(sources[0]) if sources else "upload"
        payload = finalize(result, pack, factor_edits, work_dir,
                            source_name=source_name, warnings=warnings)
        return PipelineOutcome.success(payload)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except WeakenerEngineError:
        return PipelineOutcome.failure(FailureKind.WEAKENER_ERROR)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    finally:
        DEBUG_RESPONSE_FILE.unlink(missing_ok=True)
        if owns_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
