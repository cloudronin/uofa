"""Deprecated shim — use ``tools.phase2_5.analysis.plot_pr`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.plot_pr moved to tools.phase2_5.analysis.plot_pr. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.analysis.plot_pr import *  # noqa: F401,F403
from tools.phase2_5.analysis.plot_pr import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
