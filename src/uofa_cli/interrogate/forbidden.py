"""The interrogation firewall — the single source of truth for forbidden tokens.

SIP *measures*; it never *judges*. A SIP evidence bundle must therefore never
carry a verdict: no pass/fail, accepted, validated, credible, score, or any
other field that encodes a credibility decision. The credibility decision
belongs to the practitioner and the COU acceptance criteria, never to the
measurement instrument (``SIP_Evidence_Contract_Spec_v0_1.md`` §8).

This module is the ONE place the forbidden vocabulary is defined. Every other
enforcement point imports ``FORBIDDEN_TOKENS`` from here so the schema, the
``interrogate`` command output check, the CI ``firewall_guard.py`` script, and
the firewall tests can never drift from one another:

  - ``specs/sip_evidence_bundle_schema.json`` rejects any bundle whose property
    names intersect this list (and rejects unknown properties outright via
    ``additionalProperties: false``); a lockstep test asserts the schema's
    root denylist equals this list.
  - ``uofa interrogate`` asserts none of these tokens name a field in its output.
  - ``dev/tools/scripts/firewall_guard.py`` scans the emitted surface for them.
  - ``tests/interrogate/`` parametrizes over this list.

See ``AGENTS.md`` §12 (the interrogation firewall).

Matching is on **exact property names**, not substrings: ``decision`` is
forbidden as a bundle field, but ``parentModelSnapshot.parentDecision`` — the
recorded decision of the *parent* COU, carried as inherited provenance per
SIP §5.6 — is legitimate. Substring matching would false-positive on it.
"""

from __future__ import annotations

# Verdict / decision / rating vocabulary that must never name a field in a SIP
# evidence bundle. Exact, lowercase-or-camel as authored; see module docstring
# for why matching is exact-property-name, not substring.
FORBIDDEN_TOKENS: tuple[str, ...] = (
    "verdict",
    "passFail",
    "pass_fail",
    "accepted",
    "rejected",
    "validated",
    "credible",
    "credibilityIndex",
    "decision",
    "outcome",
    "certify",
    "certified",
    "score",
    "rating",
    "approved",
)


def forbidden_property_names_constraint() -> dict:
    """Return the JSON-Schema fragment that bans forbidden property names.

    The schema embeds this fragment (``propertyNames``) at the root and on
    every freeform object. A test asserts the on-disk schema's root denylist
    equals ``list(FORBIDDEN_TOKENS)`` so the two cannot drift.
    """
    return {"not": {"enum": list(FORBIDDEN_TOKENS)}}


# The one region where decision content is legitimate (Addendum A4/A5): a
# top-level engineerDecision block, governed by its signature, not the denylist.
DECISION_BLOCK_KEY = "engineerDecision"


def find_forbidden_property_names(obj, _path: str = "$"):
    """Yield ``(json_path, token)`` for every forbidden property name in ``obj``.

    Walks dicts/lists recursively, matching property *names* exactly (so
    ``parentDecision`` is never flagged for containing ``decision``). Used by
    the command-level firewall check and the CI guard to inspect an emitted
    bundle structurally rather than by substring grep.
    """
    forbidden = set(FORBIDDEN_TOKENS)
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in forbidden:
                yield (f"{_path}.{key}", key)
            yield from find_forbidden_property_names(value, f"{_path}.{key}")
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            yield from find_forbidden_property_names(item, f"{_path}[{index}]")


def find_forbidden_in_measurement_region(bundle):
    """Forbidden property names anywhere EXCEPT the top-level engineerDecision block.

    The signature-scoped firewall (Addendum A5, superseding the flat denylist):
    decision content is valid only inside a verifying-signed ``engineerDecision``
    block and forbidden everywhere else — the "measurement region". This walker
    enforces the "everywhere else" half. Only the *top-level* engineerDecision is
    exempt; a decision block smuggled deeper (e.g. inside ``measurements``) is
    still fully scanned, so it cannot be used to bypass the firewall.
    """
    if not isinstance(bundle, dict):
        yield from find_forbidden_property_names(bundle)
        return
    forbidden = set(FORBIDDEN_TOKENS)
    for key, value in bundle.items():
        if key == DECISION_BLOCK_KEY:
            continue
        if key in forbidden:
            yield (f"$.{key}", key)
        yield from find_forbidden_property_names(value, f"$.{key}")
