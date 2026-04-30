"""Deprecated shim — use ``tools.phase2_5.corpus_regen.regen_nc_consistency`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.regen_nc_consistency moved to "
    "tools.phase2_5.corpus_regen.regen_nc_consistency. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.corpus_regen.regen_nc_consistency import *  # noqa: F401,F403
from tools.phase2_5.corpus_regen.regen_nc_consistency import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
