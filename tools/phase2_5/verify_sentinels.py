"""Deprecated shim — use ``tools.phase2_5.analysis.verify_sentinels`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.verify_sentinels moved to "
    "tools.phase2_5.analysis.verify_sentinels. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.analysis.verify_sentinels import *  # noqa: F401,F403
from tools.phase2_5.analysis.verify_sentinels import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
