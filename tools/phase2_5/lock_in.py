"""Deprecated shim — use ``tools.phase2_5.refinement_loop.lock_in`` instead.

This file preserves the pre-Phase-2.5-reorg import path
(``tools.phase2_5.lock_in``) for one release cycle. New code should
import from ``tools.phase2_5.refinement_loop.lock_in``.
"""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.lock_in moved to tools.phase2_5.refinement_loop.lock_in. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.refinement_loop.lock_in import *  # noqa: F401,F403
from tools.phase2_5.refinement_loop.lock_in import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
