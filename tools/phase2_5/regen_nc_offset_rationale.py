"""Deprecated shim — use ``tools.phase2_5.corpus_regen.regen_nc_offset_rationale`` instead."""
import warnings as _warnings

_warnings.warn(
    "tools.phase2_5.regen_nc_offset_rationale moved to "
    "tools.phase2_5.corpus_regen.regen_nc_offset_rationale. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from tools.phase2_5.corpus_regen.regen_nc_offset_rationale import *  # noqa: F401,F403
from tools.phase2_5.corpus_regen.regen_nc_offset_rationale import main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
