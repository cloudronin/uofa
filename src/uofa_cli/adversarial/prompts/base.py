"""Shared scaffolding for Phase 2 adversarial prompt templates.

Phase 1 ships one module-level template (``d3_undercutting_inference.py`` —
W-AR-05). Phase 2 adds 22 confirm_existing + 23 gap_probe + 10 negative_control
+ 6 interaction templates following the same module-level pattern. This module
provides the shared utilities they reuse:

- ``RESERVED_PROPERTY_PREAMBLE`` — the v0.5 reserved-property guard required by
  Phase 2 Spec v1.7 §8.2. Every new template's system prompt MUST begin with
  this preamble (or include the constraint inline).
- ``apply_reserved_property_constraint(system_prompt)`` — convenience helper
  that prepends the preamble to a template's existing system prompt.
- ``validate_subtlety_examples(examples)`` — sanity check that a template's
  ``SUBTLETY_GUIDANCE`` / ``subtlety_examples`` mapping has exactly the three
  required keys.

The original W-AR-05 module is intentionally left at its legacy form for
backwards-compatibility with existing snapshots; new templates in Phase 2
should use these utilities from the start.
"""

from __future__ import annotations

from typing import Mapping

REQUIRED_SUBTLETY_KEYS: frozenset[str] = frozenset({"low", "medium", "high"})

#: Phase 2 Spec v1.7 §8.2 — generators MUST NOT emit these v0.6-reserved
#: properties in synthetic packages.
RESERVED_PROPERTY_PREAMBLE = """\
Do NOT include `uofa:residualRiskJustification`, `uofa:consideredAlternative`,
or `uofa:knownLimitation` in the generated package. These are reserved for
v0.6 rules and should not appear in v0.5-era test data.

"""


def apply_reserved_property_constraint(system_prompt: str) -> str:
    """Prepend the v0.5 reserved-property preamble to *system_prompt*.

    Idempotent: if the preamble is already present, returns the prompt unchanged.
    """
    if "uofa:residualRiskJustification" in system_prompt:
        return system_prompt
    return RESERVED_PROPERTY_PREAMBLE + system_prompt


def validate_subtlety_examples(examples: Mapping[str, str]) -> None:
    """Raise :class:`ValueError` if *examples* is missing any of the three
    required subtlety levels.
    """
    keys = set(examples.keys())
    if keys != REQUIRED_SUBTLETY_KEYS:
        missing = REQUIRED_SUBTLETY_KEYS - keys
        extra = keys - REQUIRED_SUBTLETY_KEYS
        msg = []
        if missing:
            msg.append(f"missing subtlety keys: {sorted(missing)}")
        if extra:
            msg.append(f"unexpected subtlety keys: {sorted(extra)}")
        raise ValueError("; ".join(msg))
