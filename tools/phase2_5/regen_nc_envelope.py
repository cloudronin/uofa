"""Deprecated shim — use ``tools.phase2_5.corpus_regen.regen_nc_envelope`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.regen_nc_envelope moved to "
    "tools.phase2_5.corpus_regen.regen_nc_envelope. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.corpus_regen.regen_nc_envelope import *  # noqa: F401,F403
from tools.phase2_5.corpus_regen.regen_nc_envelope import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
