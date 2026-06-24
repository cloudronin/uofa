"""Free-tier findings: completeness + weakeners, computed honestly.

Thin Space-facing shim over `uofa_cli.report_state`: the completeness math,
weakener factor-focus enrichment, and payload assembly all live CLI-side now
(shared with the `uofa report` command), so the Space and the CLI cannot drift.
There is deliberately NO Accepted/Not-Accepted headline - that verdict is a
human act and is deferred.
"""

from __future__ import annotations

from uofa_cli.report_state import compute_findings as compute  # noqa: F401
from uofa_cli.weakener_focus import expected_factors  # noqa: F401

__all__ = ["compute", "expected_factors"]
