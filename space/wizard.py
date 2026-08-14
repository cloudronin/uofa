"""Wizard state machine - pure step transitions, no Gradio import.

Keeping these Gradio-free makes the multi-step flow unit-testable (app.py only
wires them to components). Each step returns a PipelineOutcome: failures carry a
FailureKind + friendly message; successes carry the data the next step needs.
The two human-in-the-loop pauses (confirm pack, confirm status) sit between
`prepare` -> `extract` and `extract` -> `finalize`.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from space import pipeline
from space.pipeline import (
    DEFAULT_EXTRACT_TIMEOUT,
    FailureKind,
    PipelineOutcome,
    WeakenerEngineError,
    _StageError,
)

# A downloadable pack must outlive the request that made it, so unlike the work
# dir it cannot be torn down in `finally`. It is bounded instead: a sweep on
# each finalize drops packs older than this. The window is deliberately short -
# the footer promises the user's evidence is not stored, and a zip containing
# extracted content sitting on disk for an hour strains that promise.
PACK_TTL_SECONDS = 30 * 60
PACK_DIR_PREFIX = "uofa-pack-"


def _sweep_stale_packs(now: float | None = None) -> None:
    """Drop packs older than PACK_TTL_SECONDS. Cheap, bounded, no background thread."""
    now = now if now is not None else time.time()
    root = Path(tempfile.gettempdir())
    try:
        candidates = list(root.glob(f"{PACK_DIR_PREFIX}*"))
    except OSError:
        return
    for path in candidates:
        try:
            # Same guard as the explicit discard, for the same reason: /tmp is
            # world-writable, so a symlink named uofa-pack-* is something any
            # local user can plant, and this loop deletes recursively without
            # being asked. glob() gives real paths, but not necessarily real
            # directories.
            target = _resolve_our_pack_dir(path)
            if target is not None and now - target.stat().st_mtime > PACK_TTL_SECONDS:
                shutil.rmtree(target, ignore_errors=True)
        except OSError:
            continue


def new_pack_dir() -> Path:
    """A per-run directory for the downloadable pack, separate from the work dir."""
    return Path(tempfile.mkdtemp(prefix=PACK_DIR_PREFIX))


def _resolve_our_pack_dir(pack_dir) -> Path | None:
    """Rebuild a pack directory path from trusted parts, or None if not ours.

    The caller's value contributes ONLY its final path component, reduced by
    `os.path.basename` to a bare name that cannot contain a separator or `..`.
    The directory it sits in is our own constant. So the string handed to
    `rmtree` is one this function constructed, never one it was given and then
    inspected: the difference between checking a path and guaranteeing it.

    That distinction matters because the caller is a recursive delete and the
    value arrives from Gradio session state. An earlier version validated the
    supplied path in place and passed it straight through, which left `rmtree`
    one flawed predicate away from operating outside the temp root.

    The symlink test is still needed after rebuilding: /tmp is world-writable,
    so any local user can plant `uofa-pack-*` pointing somewhere else.
    """
    name = os.path.basename(str(pack_dir).rstrip("/\\"))
    if not name.startswith(PACK_DIR_PREFIX) or name in (".", ".."):
        return None

    # Join to the trusted root, normalize, then require the result to still be
    # under that root. Redundant after basename() -- which is the point: this is
    # the containment check stated explicitly, so neither a reader nor a static
    # analyzer has to infer it from what basename() happens to strip.
    root = os.path.realpath(tempfile.gettempdir())
    candidate = os.path.normpath(os.path.join(root, name))
    if not candidate.startswith(root + os.sep):
        return None

    target = Path(candidate)
    if target.is_symlink() or not target.is_dir():
        return None
    return target


def discard_pack_dir(pack_dir) -> None:
    """Drop a session's pack directory (start-over, or a superseded run).

    Refuses anything it did not create; see _resolve_our_pack_dir.
    """
    if not pack_dir:
        return
    target = _resolve_our_pack_dir(pack_dir)
    if target is not None:
        shutil.rmtree(target, ignore_errors=True)


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


def extract(corpus, pack, *, model=None, llm_config=None, extract_fn=None,
            extract_timeout=DEFAULT_EXTRACT_TIMEOUT, on_progress=None) -> PipelineOutcome:
    """Run extraction (subprocess + timeout). Success payload: {result, rows}."""
    kwargs = {"model": model, "llm_config": llm_config,
              "extract_timeout": extract_timeout, "on_progress": on_progress}
    if extract_fn is not None:
        kwargs["extract_fn"] = extract_fn
    try:
        result = pipeline.run_extract_stage(corpus, pack, **kwargs)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    return PipelineOutcome.success({"result": result, "rows": pipeline.factor_rows(result)})


def finalize(result, pack, factor_edits, *, source_name="upload", warnings=None,
             pack_out_dir=None, llm_config=None) -> PipelineOutcome:
    """Adapt -> map -> check -> weakeners -> sign -> summary, in a throwaway work
    dir that is always torn down.

    The work dir still holds no retained state. When `pack_out_dir` is given, the
    signed zip is written THERE instead, so the download survives this teardown
    without weakening it: the raw graph and intermediates still die with the
    request, and only the finished pack outlives it."""
    _sweep_stale_packs()
    work_dir = Path(tempfile.mkdtemp(prefix="uofa-space-"))
    try:
        payload = pipeline.finalize(
            result, pack, factor_edits, work_dir, source_name=source_name,
            warnings=warnings, pack_out_dir=pack_out_dir, llm_config=llm_config,
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


def card_report(model_id, *, model=None, llm_config=None, deterministic=False,
                on_progress=None, pack_out_dir=None) -> PipelineOutcome:
    """Live card path (no confirm step): fetch an HF model card and report. Delegates
    to pipeline.card_report, which owns its temp work dir + debug-file teardown and
    never raises past the boundary (gated/absent cards become typed outcomes)."""
    _sweep_stale_packs()
    return pipeline.card_report(model_id, model=model, llm_config=llm_config,
                                deterministic=deterministic, on_progress=on_progress,
                                pack_out_dir=pack_out_dir)
