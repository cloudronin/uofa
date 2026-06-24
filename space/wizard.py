"""Wizard state machine - pure step transitions, no Gradio import.

Keeping these Gradio-free makes the multi-step flow unit-testable (app.py only
wires them to components). Each step returns a PipelineOutcome: failures carry a
FailureKind + friendly message; successes carry the data the next step needs.
The two human-in-the-loop pauses (confirm pack, confirm status) sit between
`prepare` -> `extract` and `extract` -> `finalize`.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from space import pipeline
from space.pipeline import (
    DEFAULT_EXTRACT_TIMEOUT,
    FailureKind,
    PipelineOutcome,
    WeakenerEngineError,
    _StageError,
)


def prepare(sources, *, on_progress=None) -> PipelineOutcome:
    """Read the evidence and route. Success payload: {corpus, decision, warnings}."""
    try:
        corpus, decision, warnings = pipeline.read_and_route(sources, on_progress=on_progress)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    return PipelineOutcome.success({"corpus": corpus, "decision": decision, "warnings": warnings})


def requires_confirmation(decision) -> bool:
    """The Route step must not auto-advance when routing is low-confidence."""
    return bool(getattr(decision, "low_confidence", False))


def extract(corpus, pack, *, model=None, extract_fn=None, extract_timeout=DEFAULT_EXTRACT_TIMEOUT, on_progress=None) -> PipelineOutcome:
    """Run extraction (subprocess + timeout). Success payload: {result, rows}."""
    kwargs = {"model": model, "extract_timeout": extract_timeout, "on_progress": on_progress}
    if extract_fn is not None:
        kwargs["extract_fn"] = extract_fn
    try:
        result = pipeline.run_extract_stage(corpus, pack, **kwargs)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    return PipelineOutcome.success({"result": result, "rows": pipeline.factor_rows(result)})


def finalize(result, pack, factor_edits, *, source_name="upload", warnings=None) -> PipelineOutcome:
    """Adapt -> map -> check -> weakeners -> summary, in a throwaway work dir
    that is always torn down (the bundle is never retained)."""
    work_dir = Path(tempfile.mkdtemp(prefix="uofa-space-"))
    try:
        payload = pipeline.finalize(
            result, pack, factor_edits, work_dir, source_name=source_name, warnings=warnings
        )
        return PipelineOutcome.success(payload)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except WeakenerEngineError:
        return PipelineOutcome.failure(FailureKind.WEAKENER_ERROR)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    finally:
        pipeline.DEBUG_RESPONSE_FILE.unlink(missing_ok=True)
        shutil.rmtree(work_dir, ignore_errors=True)
