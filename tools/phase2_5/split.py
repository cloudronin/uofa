"""Deprecated shim — use ``tools.phase2_5.refinement_loop.split`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.split moved to tools.phase2_5.refinement_loop.split. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.refinement_loop.split import *  # noqa: F401,F403
from tools.phase2_5.refinement_loop.split import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
