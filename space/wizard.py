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
            # Same guard as the explicit discard: /tmp is world-writable, so a
            # symlink named uofa-pack-* is something anyone on the host can
            # plant, and this loop deletes recursively without being asked.
            if _is_our_pack_dir(path) and now - path.stat().st_mtime > PACK_TTL_SECONDS:
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            continue


def new_pack_dir() -> Path:
    """A per-run directory for the downloadable pack, separate from the work dir."""
    return Path(tempfile.mkdtemp(prefix=PACK_DIR_PREFIX))


def _is_our_pack_dir(path: Path) -> bool:
    """True only for a directory this module created.

    Three conditions, and all three are load-bearing because the caller is a
    recursive delete:

    1. resolve() first, so `..` segments and symlinks are collapsed BEFORE any
       check. A prefix test on the raw name accepts `/tmp/../etc/uofa-pack-x`,
       whose basename matches while the real target is somewhere else entirely.
    2. the parent must be the temp root itself, so only direct children of the
       directory mkdtemp writes into are eligible.
    3. the basename must carry our prefix, and it must be a real directory
       rather than a symlink to one.

    The value reaching discard_pack_dir comes from Gradio session state. That is
    server-side today, but "the framework will not hand us an attacker's string"
    is not a property worth betting an rmtree on.
    """
    try:
        resolved = path.resolve(strict=True)
        temp_root = Path(tempfile.gettempdir()).resolve()
    except (OSError, RuntimeError):
        return False
    return (
        resolved.parent == temp_root
        and resolved.name.startswith(PACK_DIR_PREFIX)
        and resolved.is_dir()
        and not path.is_symlink()
    )


def discard_pack_dir(pack_dir) -> None:
    """Drop a session's pack directory (start-over, or a superseded run).

    Refuses anything it did not create; see _is_our_pack_dir.
    """
    if not pack_dir:
        return
    path = Path(pack_dir)
    if _is_our_pack_dir(path):
        shutil.rmtree(path, ignore_errors=True)


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


def finalize(result, pack, factor_edits, *, source_name="upload", warnings=None,
             pack_out_dir=None) -> PipelineOutcome:
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
            warnings=warnings, pack_out_dir=pack_out_dir,
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


def card_report(model_id, *, model=None, deterministic=False, on_progress=None,
                pack_out_dir=None) -> PipelineOutcome:
    """Live card path (no confirm step): fetch an HF model card and report. Delegates
    to pipeline.card_report, which owns its temp work dir + debug-file teardown and
    never raises past the boundary (gated/absent cards become typed outcomes)."""
    _sweep_stale_packs()
    return pipeline.card_report(model_id, model=model, deterministic=deterministic,
                                on_progress=on_progress, pack_out_dir=pack_out_dir)
