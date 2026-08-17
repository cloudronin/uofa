"""Mutation operator registry — data, not comments.

Phase 2.5a §1.2 requires the operator-to-pattern mapping to live in the code as
data so it can be counted rather than read off a prose list. That requirement
earned itself: the implementation plan's prose said "Class A, 13 patterns" and
enumerated 12, and a registry built from that list would have passed the step-1
coverage gate while missing W-ON-02.

Every MECHANICAL pattern of the ruled partition appears here exactly once. The
coverage check counts THIS structure.

Classes (`class_ab`), measured in `studies/phase2_5a/PRECONDITION-INVENTORY.md`:

  A  the substrate already carries the field, so one edit produces the defect
  B  the rule's antecedent is absent from every substrate, so the operator must
     instantiate it and then violate it -- two edits, one fault

`gate_scored=False` marks a pattern reported separately with its mechanism rather
than carried as a plain row in the MECHANICAL rollup. Only W-EP-01 qualifies, per
the Decision Record addenda C-D; see `GATE_DENOMINATOR_NOTE`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# The label-class criterion, stated once and carried as data so the asymmetry is
# auditable (Decision Record ruling 4 + addendum A). Reused verbatim in A1's Ch3 text.
LABEL_CLASS_CRITERION = (
    "isFoundationalEvidence is a structural declaration of the package as encoded; "
    "factorStatus and hasOffsetRationale are dispositional. That is why W-PROV-01 "
    "and W-AR-03 are MECHANICAL while W-EP-04, W-AR-01, W-AR-02 and W-CON-01 are not."
)

# Settled before Arm M scores, never after -- the gate is evaluated once.
GATE_DENOMINATOR_NOTE = (
    "MECHANICAL partition = 17 (scopes the battery). GATE-H3 denominator = 16 "
    "(17 less W-EP-01, reported separately). Gate measurement basis = defect "
    "instances, per A5's effective-n rule, not pattern count. The 16-vs-17 reading "
    "carries an author check in Decision Record addenda C-D; scoring MUST NOT run "
    "until it is confirmed."
)


@dataclass(frozen=True)
class Operator:
    """One mutation operator, bound to exactly one pattern."""

    id: str
    pattern: str
    family: str          # deletion | value | temporal | referential | integrity | antecedent
    class_ab: str        # "A" or "B"
    summary: str         # what the mutation does, in one line
    antecedent: str      # what the rule needs bound before a violation is expressible
    substrates: tuple[str, ...] = ()   # measured hosts; empty for Class B
    gate_scored: bool = True
    implemented: bool = False
    notes: str = ""
    # site discovery + application are attached by engine.py at import time
    find_sites: Callable | None = field(default=None, compare=False, repr=False)
    apply: Callable | None = field(default=None, compare=False, repr=False)


# ── Class A: the substrate carries the field ────────────────────────────────
# Site counts are from studies/phase2_5a/inventory.py over the three executable
# substrates. Six of the nine are single-substrate, so most Class A rows will
# carry wide Wilson intervals -- amendment A4 requires n in every reported row.

_CLASS_A: tuple[Operator, ...] = (
    Operator(
        id="MUT-DEL-01", pattern="W-AL-01", family="deletion", class_ab="A",
        summary="remove hasUncertaintyQuantification from one ValidationResult",
        antecedent="a ValidationResult carrying hasUncertaintyQuantification",
        substrates=("morrison/cou2",),
        notes="3 sites. One of the committee's three named flaw types "
              "('remove uncertainty'); the walkthrough's first demo.",
    ),
    Operator(
        id="MUT-DEL-02", pattern="W-AR-05", family="deletion", class_ab="A",
        summary="remove comparedAgainst from one ValidationResult",
        antecedent="a ValidationResult carrying comparedAgainst",
        substrates=("morrison/cou2",),
        notes="3 sites. The skeleton-mode MVP pattern.",
    ),
    Operator(
        id="MUT-DEL-03", pattern="W-EP-02", family="deletion", class_ab="A",
        summary="remove prov:wasGeneratedBy from one ValidationResult",
        antecedent="a ValidationResult carrying prov:wasGeneratedBy",
        substrates=("morrison/cou2",),
        notes="3 sites, and morrison/cou2 is the ONLY substrate with the chain — "
              "cou1 has 0/3 and nagaraja 0/6. n=3 on one substrate.",
    ),
    Operator(
        id="MUT-DEL-04", pattern="W-ON-01", family="deletion", class_ab="A",
        summary="remove hasContextOfUse from the UofA",
        antecedent="hasContextOfUse present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="1 site per substrate, 3 total. Never fired at any measured version.",
    ),
    Operator(
        id="MUT-DEL-05", pattern="W-SI-01", family="integrity", class_ab="A",
        summary="strip the signature block from the signed serialization",
        antecedent="signature present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="1 site per substrate. Second of the committee's named flaw types "
              "('remove signatures'); the walkthrough's second demo. Applied AFTER "
              "signing so it models tamper. Never fired at any measured version.",
    ),
    Operator(
        id="MUT-DEL-06", pattern="W-SI-02", family="deletion", class_ab="A",
        summary="remove one required binding (bindsRequirement or hasValidationResult)",
        antecedent="bindsRequirement or hasValidationResult present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="15 sites total (4/4/7). NOTE: the rule emits two distinct findings "
              "under one patternId (rules:337, rules:350), so scoring must key on "
              "annotation identity, not patternId alone, or the two collapse. "
              "Also SHACL-mandatory, so expect caught_by=shacl — the layer-attribution "
              "case Phase 2.5a §1.3 exists for.",
    ),
    Operator(
        id="MUT-DEL-07", pattern="W-AL-02", family="deletion", class_ab="A",
        summary="remove hasSensitivityAnalysis while hasUncertaintyQuantification stays true",
        antecedent="hasUncertaintyQuantification=true AND hasSensitivityAnalysis present",
        substrates=("nagaraja/cou1",),
        notes="1 site, one substrate. n=1 — the widest interval in the battery.",
    ),
    Operator(
        id="MUT-DEL-08", pattern="W-CON-04", family="deletion", class_ab="A",
        summary="remove hasSensitivityAnalysis from a ProfileComplete package",
        antecedent="conformsToProfile=ProfileComplete AND hasSensitivityAnalysis present",
        substrates=("nagaraja/cou1",),
        notes="1 site, one substrate. Shares its field with MUT-DEL-07: on "
              "nagaraja/cou1 a single deletion fires BOTH W-AL-02 and W-CON-04, so "
              "these two operators are not independent there. Recorded rather than "
              "engineered around — the coupling is a property of the catalog.",
    ),
    Operator(
        id="MUT-REF-01", pattern="W-PROV-01", family="referential", class_ab="A",
        summary="delete one prov:wasDerivedFrom edge from a claim in provenance scope",
        antecedent="a claim carrying prov:wasDerivedFrom",
        substrates=("morrison/cou2",),
        notes="4 sites. Restored to the battery by ruling 4 (isFoundationalEvidence "
              "is structural, so the label is machine-re-derivable). Already fires 7 "
              "times on the cou2 baseline, so delta scoring must compare "
              "(patternId, affectedNode) pairs, not pattern sets.",
    ),
)

# ── Class B: the antecedent is absent from every substrate ──────────────────
# Funded in full per Decision Record addendum C. "Uncoverable within budget" is
# withdrawn as a verdict: expensive gets built; only genuinely-unmutatable earns
# a non-result.

_CLASS_B: tuple[Operator, ...] = (
    Operator(
        id="MUT-ANT-01", pattern="W-EP-03", family="antecedent", class_ab="B",
        summary="instantiate modelRevisionDate + a wasGeneratedBy→used→Dataset chain, "
                "then set dataVintage earlier than the revision date",
        antecedent="modelRevisionDate AND hasValidationResult→prov:wasGeneratedBy→"
                   "prov:used→Dataset.dataVintage",
        notes="Both literals are xsd:dateTime in the context, so typing is NOT the "
              "obstacle — the chain is. 180/180 generated packages lack wasGeneratedBy.",
    ),
    Operator(
        id="MUT-ANT-02", pattern="W-AR-04", family="antecedent", class_ab="B",
        summary="instantiate currentModelVersion + a used→ModelConfiguration chain, "
                "then set the config's modelVersion to differ",
        antecedent="currentModelVersion AND hasValidationResult→prov:wasGeneratedBy→"
                   "prov:used→cfg.modelVersion",
        notes="Third of the committee's named flaw types ('change version numbers'). "
              "Class B, so if it appears in the walkthrough the enrichment must be "
              "narrated honestly — never as a plain injection.",
    ),
    Operator(
        id="MUT-ANT-03", pattern="W-CON-03", family="antecedent", class_ab="B",
        summary="instantiate signatureTimestamp + hasEvidence.evidenceTimestamp, "
                "then push the evidence timestamp past the signature",
        antecedent="signatureTimestamp AND hasEvidence→evidenceTimestamp",
    ),
    Operator(
        id="MUT-ANT-04", pattern="W-AR-03", family="antecedent", class_ab="B",
        summary="inline bindsRequirement as a typed node with requiredVerificationMethod, "
                "add activityType to the generating activity, then make them differ",
        antecedent="bindsRequirement inlined with requiredVerificationMethod AND "
                   "an activity carrying activityType",
        notes="The largest enrichment of the eight: bindsRequirement is a bare IRI in "
              "all three substrates and activityType appears nowhere in the repo. "
              "Neither property carries sh:in, so the comparison is free-text "
              "inequality — ruling 5 deferred that hardening to v0.6.",
    ),
    Operator(
        id="MUT-ANT-05", pattern="W-CON-02", family="antecedent", class_ab="B",
        summary="instantiate referencesIdentifier pointing at a node, then strip the "
                "target's rdf:type and schema:url so it resolves nowhere",
        antecedent="referencesIdentifier present",
        notes="referencesIdentifier appears in no substrate. The rule uses rdf:type as "
              "a local-subject proxy for RETE-safety reasons (rules:452-458).",
    ),
    Operator(
        id="MUT-ANT-06", pattern="W-CON-05", family="antecedent", class_ab="B",
        summary="instantiate hasVerificationActivity with a linked Evidence, then remove "
                "the prov:wasGeneratedBy link so the activity is a placeholder",
        antecedent="hasVerificationActivity with some Evidence linked via prov:wasGeneratedBy",
        notes="hasVerificationActivity appears in no substrate.",
    ),
    Operator(
        id="MUT-ANT-07", pattern="W-ON-02", family="antecedent", class_ab="B",
        summary="enrich the COU to a clean state (add an operating envelope), then "
                "remove it again",
        antecedent="a ContextOfUse carrying hasApplicabilityConstraint or hasOperatingEnvelope",
        notes="ENRICH-TO-CLEAN, not enrich-to-express. W-ON-02 fires on ALL THREE "
              "baselines: every case-study encoding has a COU bounded by neither "
              "constraint nor envelope. So its detection is already evidenced without "
              "injection, and producing a recall row requires manufacturing the clean "
              "state first. Report the baseline-positive fact as a finding about the "
              "encodings, not only as an operator note.",
    ),
    Operator(
        id="MUT-ANT-08", pattern="W-EP-01", family="antecedent", class_ab="B",
        gate_scored=False,
        summary="instantiate a claim typed uofa:Claim carrying prov:wasDerivedFrom, "
                "then remove the derivation edge",
        antecedent="a claim inline-typed uofa:Claim carrying prov:wasDerivedFrom",
        notes="CANNOT PRODUCE A MECHANICAL-ROLLUP ROW. uofa:Claim is declared nowhere: "
              "the context defines AssuranceClaim only, the shapes declare "
              "AssuranceClaim and make it bindsClaim's rdfs:range, and the rules file "
              "does no subclass inference. The synthetic corpus emits bare "
              "type: 'Claim', which resolves through @vocab to uofa:Claim and fires "
              "the rule — that is the whole of its 20/20 on the v0.5.13 holdout. Any "
              "mutant this operator builds would have to type the claim against a "
              "class the schema does not declare, i.e. measure the same artifact. "
              "Excluded from the gate denominator (16 = 17 less this) and reported "
              "separately with its mechanism named.",
    ),
)

REGISTRY: tuple[Operator, ...] = _CLASS_A + _CLASS_B

# The ruled partition. The battery must cover exactly this set.
MECHANICAL_PATTERNS: frozenset[str] = frozenset({
    "W-EP-01", "W-EP-02", "W-EP-03",
    "W-AL-01", "W-AL-02",
    "W-ON-01", "W-ON-02",
    "W-AR-03", "W-AR-04", "W-AR-05",
    "W-SI-01", "W-SI-02",
    "W-CON-02", "W-CON-03", "W-CON-04", "W-CON-05",
    "W-PROV-01",
})


def coverage() -> dict:
    """Step-1 gate: every MECHANICAL pattern covered, counted from the registry.

    Counts the structure rather than a prose list, per §1.2 — which is the check
    that would have caught the plan's 13-that-enumerated-12.
    """
    covered = {op.pattern for op in REGISTRY}
    dupes = [p for p in covered if sum(1 for op in REGISTRY if op.pattern == p) > 1]
    return {
        "registry_size": len(REGISTRY),
        "patterns_covered": len(covered),
        "partition_size": len(MECHANICAL_PATTERNS),
        "missing": sorted(MECHANICAL_PATTERNS - covered),
        "extra": sorted(covered - MECHANICAL_PATTERNS),
        "duplicate_patterns": sorted(dupes),
        "class_a": sorted(op.pattern for op in REGISTRY if op.class_ab == "A"),
        "class_b": sorted(op.pattern for op in REGISTRY if op.class_ab == "B"),
        "gate_scored": sorted(op.pattern for op in REGISTRY if op.gate_scored),
        "reported_separately": sorted(op.pattern for op in REGISTRY if not op.gate_scored),
        "implemented": sorted(op.pattern for op in REGISTRY if op.implemented),
    }


def by_id(operator_id: str) -> Operator:
    for op in REGISTRY:
        if op.id == operator_id:
            return op
    raise KeyError(f"no such operator: {operator_id}")


def for_pattern(pattern_id: str) -> list[Operator]:
    return [op for op in REGISTRY if op.pattern == pattern_id]
