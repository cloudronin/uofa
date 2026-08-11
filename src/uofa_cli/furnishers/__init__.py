"""Furnishers of evaluation evidence for the Group-B sufficiency layer.

A *furnisher* supplies benchmark evidence about a model; the pack *assesses*
whether that evidence is sufficient to support a decision. The two roles do not
collapse into each other: a furnished score can be clean, replicated, and still
trip W-EV-COU-05 because nothing in the record says what decision it informs.
Furnishing a number is not asserting its sufficiency.

This module holds the one thing both sides must agree on -- the set of
properties a furnisher may emit onto a `ValidationResult`. It is the single
source of truth for `tests/test_group_b_rule_property_coverage.py`, which
asserts that the set of properties the Group-B rules *test* is exactly the set a
furnisher can *emit*. Addendum v0.1 §A1 requires this as a lint rather than a
convention, because the drift it prevents is silent in both directions:

  - a rule testing a property nothing emits fires on 100% of inputs forever,
    which is not a finding but a schema hole wearing a finding's clothes;
  - a property emitted with no rule consuming it is dead weight that reads,
    from the outside, exactly like a check.
"""

from __future__ import annotations

# Properties a furnisher may set on a ValidationResult node, each consumed by a
# Group-B rule in packs/mrm-nist/rules/mrm_nist_weakener.rules.
GROUP_B_RESULT_PROPERTIES: frozenset[str] = frozenset({
    "samplingAccount",             # W-EV-GEN-02, COMPOUND-EV-02
    "harnessDeterminismStatement", # W-EV-DET-03
    "nullBaselineStatement",       # W-EV-NULL-04, COMPOUND-EV-01
    "claimedCOU",                  # W-EV-COU-05 (both severities)
    "confoundControlStatement",    # W-EV-CAP-06
    "generalizedClaim",            # COMPOUND-EV-02
    # Set when the subject's identity is IMMUTABLE and verifiable by the
    # assessor -- a local checkpoint pinned by config + weight-manifest hash.
    # Absent for every hosted endpoint, whose identity is asserted by its
    # provider and can change under a stable name (addendum v0.4 A13.5). Its
    # absence is what W-EV-SUB-08 reports.
    "subjectVersionGuarantee",     # W-EV-SUB-08
    # Which side of the record a result came from: "reported" (extracted from the
    # model card's own claims) or "furnished" (measured by a furnisher). The
    # distinction is what lets corroboration be asked about at all.
    "evidenceSource",              # W-EV-COR-09, W-EV-DIV-07
    # Set on a REPORTED result when a FURNISHED result measures the same
    # constituent. Its absence is what W-EV-COR-09 reports -- and only when
    # furnished evidence exists to have corroborated it.
    "corroboratedBy",              # W-EV-COR-09
    # Set when a reported score differs from its furnished counterpart by more
    # than the tolerance. Present only on a MATCHED pair -- an unmatched reported
    # score never carries it, because no comparison happened.
    "divergesFromFurnished",       # W-EV-DIV-07
})

# Core properties the Group-B path populates rather than duplicating. W-EV-UQ-01
# was withdrawn precisely so this stays a reuse and not a parallel vocabulary:
# core's W-AL-01 fires on the absence of `hasUncertaintyQuantification` for any
# ValidationResult, which is the whole finding, already implemented, already
# grounded. See the pack spec's §3 note on the withdrawal.
CORE_RESULT_PROPERTIES_POPULATED: frozenset[str] = frozenset({
    "hasUncertaintyQuantification",
})

# Run-context properties bound to operator flags, set on the UnitOfAssurance.
# Both are deliberately distinct from same-meaning properties that mrm-nist
# bundles already carry with synthesized values -- `modelRiskLevel` is always the
# disclosed MRM_NIST_ASSUMED_MRL posture, and `hasContextOfUse` is derived from
# the model id. Keying rules on those would make COMPOUND-EV-01 fire
# unconditionally and pin W-EV-COU-05 to Critical forever (addendum v0.1 §A2).
GROUP_B_RUN_CONTEXT_PROPERTIES: frozenset[str] = frozenset({
    "decisionRiskLevel",     # <- --mrl ; COMPOUND-EV-01
    "decisionContextOfUse",  # <- --cou ; W-EV-COU-05 severity split
})

# Value-carrying fields written for the report and card renderers. These are
# NOT rule-facing in this phase and are exempt from the coverage lint; the lint
# names them explicitly so the exemption is a decision on the record rather than
# an oversight. `metricValue` becomes rule-facing in the W-EV-DIV-07 phase and
# simply moves out of this set then.
#
# None of these properties -- nor any in the sets above -- is declared in
# spec/context/v0.5.jsonld, deliberately. That context sets
# "@vocab": "https://uofa.net/vocab#", so an undeclared term already expands to
# uofa:<term> and Jena sees it. And the context is INLINED into the document
# before hashing (integrity.canonicalize_and_hash), so adding a term there
# invalidates every signed bundle in the repo -- a one-line addition put the
# Morrison reference example into C1 Integrity failure while C2 and C3 stayed
# green. Adding vocabulary here costs nothing; adding it there costs the corpus.
# Declared properties that NO furnisher emits yet, with the reason and what would
# change it. Every entry means a rule keyed on the property's absence currently
# fires unconditionally, so the list is a liability and should shrink.
#
# It exists because "declared emittable" and "actually emitted" are different
# claims and the gap is invisible: `evidenceSource` was declared, consumed by
# W-EV-COR-09's rule body, and never set by the raidex adapter -- COR-09 could
# not have fired in production while every test passed, because the firewall
# tests built their nodes by hand. Recording the pending set forces the gap to be
# a decision rather than an oversight, and removing an entry is what completing
# the work looks like.
PENDING_EMISSION: dict[str, str] = {}

VALUE_ONLY_FIELDS: frozenset[str] = frozenset({
    "metricValue",
    "name",
    "description",
    "type",
    "id",
})

__all__ = [
    "GROUP_B_RESULT_PROPERTIES",
    "CORE_RESULT_PROPERTIES_POPULATED",
    "GROUP_B_RUN_CONTEXT_PROPERTIES",
    "PENDING_EMISSION",
    "VALUE_ONLY_FIELDS",
]
