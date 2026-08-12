"""Production adapter for the gated keyless table route (P2 uncertainty).

The route itself is frozen (`studies/taxonomy-validation/enrichment/
keyless_route.py`, v1, gated 2026-08-12) and **must not be edited** -- its
qualification row reports measurements of that exact logic. So this adapter is a
WRAPPER: it calls the frozen reader and adds what production needs, and it can
change freely because changing it does not change what was gated.

## Span provenance is mandatory here, exactly as for the LLM path

Every emitted `hasUncertaintyQuantification` carries the route version, the
branch that read it, and **the matched cell text**. A property with no quotable
anchor is inference wearing extraction's clothes -- "stated, not inferable" binds
the machine as it bound the labelers, and a deterministic reader can satisfy it
perfectly because it already holds the cell.

## Published limitations of route v1, carried onto every emission

- **compound dispersion headers** (`reward_std`) are not read -- measured 2/27
  false-fire on the holdout;
- **a standalone `SE` metric column is misread as standard error** -- measured
  1/33 (3.0%) false-clear. That mode credits a card with an uncertainty it does
  not state, which **silences W-AL-01 on that card**.

The obvious fix for the second -- rejecting implausibly large values -- is
refused: the moment the route reasons about magnitude it stops being a field read
and becomes inference, which is the backend's job under D2.

Scope: **table-borne P2 only.** Silent on prose, and on P6/P7 by construction.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_STUDY = (Path(__file__).resolve().parents[3]
          / "studies/taxonomy-validation/enrichment")

ROUTE_VERSION = "keyless-table-route/v1"
# Gated 2026-08-12: false-fire 2/27 (7.4%), false-clear 1/33 (3.0%), n=60 unseen.
ROUTE_GATE = "holdout 2026-08-12: ff 2/27 (7.4%), fc 1/33 (3.0%)"


def _route():
    if str(_STUDY) not in sys.path:
        sys.path.insert(0, str(_STUDY))
    import keyless_route
    return keyless_route


def read(eval_sections: str) -> dict[str, Any] | None:
    """Read a table-borne uncertainty with its span, or None.

    Returns `{value, branch, cell, routeVersion, gate}`. None means the route
    read nothing, which is a real answer and leaves the field empty.
    """
    kr = _route()
    value = kr.read_uncertainty(eval_sections)
    if value is None:
        return None

    # Attribute the branch and recover the containing cell WITHOUT re-deriving
    # the route's decision: ask whether the value it returned is reachable
    # inline, using the frozen module's own public pattern. A wrapper that
    # re-implemented the search could disagree with the reader it wraps and
    # attribute a span the route never looked at.
    branch, cell = "columnar", value
    for line in kr._table_lines(eval_sections):
        m = kr.INLINE.search(line)
        if m and m.group(0).strip() == value:
            branch = "inline"
            cell = next((c for c in kr._cells(line) if value in c), line.strip())
            break
    else:
        for i, line in enumerate(kr._table_lines(eval_sections)):
            idx = [j for j, c in enumerate(kr._cells(line)) if kr.HEADER.match(c)]
            if not idx:
                continue
            hdr = [kr._cells(line)[j] for j in idx]
            cell = f"{'/'.join(hdr)} column -> {value}"
            break

    return {"value": value, "branch": branch, "cell": cell,
            "routeVersion": ROUTE_VERSION, "gate": ROUTE_GATE}


def attach(node: dict, eval_sections: str) -> bool:
    """Populate a ValidationResult's uncertainty from a table. True if it did.

    Never overwrites: an uncertainty already read by the backend path stays,
    because two routes disagreeing is a finding and silently preferring one
    would erase it.
    """
    if node.get("hasUncertaintyQuantification"):
        return False
    got = read(eval_sections)
    if got is None:
        return False
    node["hasUncertaintyQuantification"] = True
    node["uqMethod"] = f"as reported in the model card table: {got['value']}"
    node["uqProvenance"] = {
        "route": got["routeVersion"],
        "branch": got["branch"],
        "matchedCell": got["cell"][:200],
        "gate": got["gate"],
        "knownLimitations": [
            "compound dispersion headers (reward_std) are not read",
            "a standalone SE metric column is misread as standard error "
            "(3.0% measured; silences W-AL-01 on that card)",
        ],
    }
    return True
