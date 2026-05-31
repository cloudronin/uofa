"""The firewall chokepoint — the one boundary every pack output crosses (§0/§4).

The investigation established the firewall as the codebase's real organizing
principle: SIP *measures*, the pack *checks auditability*, the human *decides*,
and decision/action content is fenced out of the measurement region. Pack-shaped
architecture turns that principle into a single, non-bypassable boundary function
so that *any* conforming pack — open-core or premium — inherits the firewall
rather than re-implementing (or quietly skipping) it.

**One chokepoint, one mandatory policy.** Every capability output entering a
bundle goes through :func:`check_crossing`. It consults a **mandatory,
non-pluggable policy leg** — packs cannot register, replace, or weaken it — keyed
on the capability's manifest-declared ``firewallPlacement``. The initial policy is
exactly today's three layers, now centralized:

  1. **token-ban** — no :data:`FORBIDDEN_TOKENS` verdict word may name a property;
  2. **structural** — a measurement/reference output is array/object (never a bare
     scalar verdict) and carries no action-region block nested inside it;
  3. **signature-scoping** — an action-region output is admitted only when signed
     in its own scope.

**Fail closed.** An unknown/absent placement, an unsigned action, or *any* error
while evaluating the policy DENIES the crossing — the firewall never silently
allows. This is the tested invariant: when the decision is absent, ambiguous, or
errored, the answer is "no".

This module is deliberately minimal — one function and a thin raising wrapper, not
a message bus. It imports the single forbidden-token source
(:mod:`uofa_cli.interrogate.forbidden`); it is consulted by the measurement
orchestrator (each method's output crosses here) and is available to any other
leg that emits into a bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from uofa_cli.interrogate.forbidden import (
    ACTION_REGION_KEYS,
    find_forbidden_property_names,
)

PLACEMENT_MEASUREMENT = "measurement-region"
PLACEMENT_ACTION = "action-region"
PLACEMENT_REFERENCE = "reference-side"
KNOWN_PLACEMENTS = (PLACEMENT_MEASUREMENT, PLACEMENT_ACTION, PLACEMENT_REFERENCE)

# Signature fields that mark an action-region block as signed in its scope.
_ACTION_SIGNATURE_FIELDS = ("actionSignature", "decisionSignature")


class FirewallViolation(Exception):
    """Raised by :func:`enforce_crossing` when a pack output is denied."""


@dataclass(frozen=True)
class FirewallDecision:
    """The chokepoint's verdict on one crossing. ``allowed=False`` is the default
    posture on any doubt (fail-closed); ``reasons`` records why."""

    allowed: bool
    placement: str
    reasons: tuple[str, ...] = ()


def _forbidden_tokens_in(output: Any) -> list[str]:
    return [tok for _, tok in find_forbidden_property_names(output)]


def _action_keys_in(output: Any) -> list[str]:
    """Action-region block keys appearing anywhere inside ``output`` (recursive)."""
    found: list[str] = []
    if isinstance(output, dict):
        for key, value in output.items():
            if key in ACTION_REGION_KEYS:
                found.append(key)
            found.extend(_action_keys_in(value))
    elif isinstance(output, list):
        for item in output:
            found.extend(_action_keys_in(item))
    return found


def _is_signed(output: Any, signed: bool | None) -> bool:
    if signed is not None:
        return bool(signed)
    if isinstance(output, dict):
        return any(output.get(field) for field in _ACTION_SIGNATURE_FIELDS)
    return False


def check_crossing(output: Any, *, placement: str, signed: bool | None = None) -> FirewallDecision:
    """Evaluate a pack output against the mandatory firewall policy. Fails CLOSED.

    ``output`` is the value a capability contributes (a measurement block, an
    action block, reference data). ``placement`` is the capability's
    manifest-declared ``firewallPlacement``. ``signed`` lets a caller assert an
    action block is signed in its scope; when ``None`` the policy infers it from a
    signature field on the block.

    Returns a :class:`FirewallDecision`. Denies on an unknown/absent placement, an
    unsigned action-region output, or any exception raised while evaluating the
    policy — the firewall never silently allows.
    """
    try:
        if placement not in KNOWN_PLACEMENTS:
            return FirewallDecision(
                False, str(placement),
                (f"unknown firewall placement {placement!r} — fail closed",),
            )

        if placement in (PLACEMENT_MEASUREMENT, PLACEMENT_REFERENCE):
            reasons: list[str] = []
            tokens = _forbidden_tokens_in(output)
            if tokens:
                reasons.append(f"verdict token(s) {sorted(set(tokens))} in the {placement}")
            if not isinstance(output, (list, dict)):
                reasons.append(f"non-measurement-shaped (scalar) output in the {placement}")
            action_keys = _action_keys_in(output)
            if action_keys:
                reasons.append(
                    f"action-region block(s) {sorted(set(action_keys))} nested in the {placement}"
                )
            return FirewallDecision(not reasons, placement, tuple(reasons))

        # PLACEMENT_ACTION — decision/action content is legitimate here, but only
        # when signed in its own scope (the §4 boundary).
        if not _is_signed(output, signed):
            return FirewallDecision(
                False, placement,
                ("action-region output is not signed in its scope — fail closed",),
            )
        return FirewallDecision(True, placement)
    except Exception as exc:  # noqa: BLE001 — fail closed on ANY policy error
        return FirewallDecision(False, str(placement), (f"policy error (fail closed): {exc}",))


def enforce_crossing(output: Any, *, placement: str, signed: bool | None = None) -> None:
    """:func:`check_crossing`, raising :class:`FirewallViolation` on denial."""
    decision = check_crossing(output, placement=placement, signed=signed)
    if not decision.allowed:
        raise FirewallViolation(
            f"firewall denied a {placement} crossing: {'; '.join(decision.reasons)}"
        )
