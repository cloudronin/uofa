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
    # Addendum E ruling 3: design intent, deliberately NOT diff-derived, compared
    # against measured. Not exclusive -- measurement shows 12 of 23 mutants are
    # non-conformant AND rule-caught, because check.run_structured never
    # short-circuits on a SHACL failure. So "schema+rules" is a real expectation,
    # not a hedge, and an operator expecting it that comes back rules-only (or
    # vice versa) is a finding either way.
    expected_catch_layer: str = "rules"      # rules | schema+rules
    notes: str = ""
    # site discovery + application are attached by engine.py at import time
    find_sites: Callable | None = field(default=None, compare=False, repr=False)
    apply: Callable | None = field(default=None, compare=False, repr=False)


# ── Class A: the substrate carries the field ────────────────────────────────
# Site counts here are ENGINE-MEASURED (`engine.site_table()`), which is the
# authority for every reported n. The step-1 inventory's probe counted elements
# and disagreed twice: W-SI-02 15 vs 6, and W-PROV-01 4 vs 0-additive. Measured
# denominators beat projected ones. Five of the eight are single-substrate and
# two are n=1, so most Class A rows carry wide Wilson intervals -- amendment A4
# requires n in every reported row and the gate paragraph names which rows clear
# on wide intervals.

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
        expected_catch_layer="schema+rules",
        summary="remove hasContextOfUse from the UofA",
        antecedent="hasContextOfUse present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="1 site per substrate, 3 total. Never fired at any measured version.",
    ),
    Operator(
        id="MUT-DEL-05", pattern="W-SI-01", family="integrity", class_ab="A",
        expected_catch_layer="schema+rules",
        summary="strip the signature block from the signed serialization",
        antecedent="signature present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="1 site per substrate. Second of the committee's named flaw types "
              "('remove signatures'); the walkthrough's second demo. Applied AFTER "
              "signing so it models tamper. Never fired at any measured version.",
    ),
    Operator(
        id="MUT-DEL-06", pattern="W-SI-02", family="deletion", class_ab="A",
        expected_catch_layer="schema+rules",
        summary="remove one required binding (bindsRequirement or hasValidationResult)",
        antecedent="bindsRequirement or hasValidationResult present",
        substrates=("morrison/cou1", "morrison/cou2", "nagaraja/cou1"),
        notes="6 sites (2/2/2), engine-measured. The step-1 probe said 15 (4/4/7) by "
              "counting elements; the rule fires on whole-property absence, so "
              "bindsRequirement with one value and hasValidationResult with six are "
              "two sites, not seven. NOTE: the rule emits two distinct findings "
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
        notes="1 site, one substrate. Produces a BYTE-IDENTICAL mutant to MUT-DEL-07 "
              "— equal diff hashes, one removed triple — because on nagaraja/cou1 "
              "deleting hasSensitivityAnalysis fires both W-AL-02 and W-CON-04. "
              "Scored at the MUTANT level per author ruling: one test case with two "
              "expected findings, counted once in the denominator. The coupling is a "
              "catalog-redundancy observation (two rules reading one field) for the "
              "findings section, and the diff-derived manifest catches it by "
              "construction rather than by anyone noticing.",
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
        id="MUT-REF-01", pattern="W-PROV-01", family="referential", class_ab="B",
        summary="add a dangling node into provenance scope, or strip ALL upstream "
                "edges from an in-scope node, so it becomes chain-terminal",
        antecedent="an in-scope node that can be made terminal without leaving scope",
        notes="RECLASSIFIED A→B ON MEASUREMENT, not projection. Every single-edit form "
              "was tried on morrison/cou2 and every one is SUPPRESSING:\n"
              "  claim-edge deletion (4 sites)         -> ΔW-PROV-01 -1 to -2\n"
              "  intermediate-edge deletion (6 sites)  -> ΔW-PROV-01 -1 at every site\n"
              "  isFoundationalEvidence deletion       -> NO SITE EXISTS, see below\n"
              "The rule seeds scope at the claim and extends upstream, so severing any "
              "edge removes the subtree below it — which held the firing terminal node "
              "— while the severed node keeps its OTHER upstream edge and so does not "
              "become terminal. Making it terminal needs every upstream edge gone: two "
              "edits, hence Class B by the engine's own single-edit criterion.\n"
              "Separately: isFoundationalEvidence — the suppression flag whose "
              "structural-vs-dispositional reading decided this pattern's MECHANICAL "
              "class under ruling 4 — appears in ZERO encodings across all five packs. "
              "The ruling stands (an unused structural declaration is still structural) "
              "but the flag that settled the classification has no instance in the corpus.",
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


def coverage(registry: tuple[Operator, ...] | None = None) -> dict:
    """Step-1 gate: every MECHANICAL pattern covered, counted from the registry.

    Counts the structure rather than a prose list, per §1.2 — which is the check
    that would have caught the plan's 13-that-enumerated-12.

    Pass `engine.REGISTRY` for the *bound* view: `implemented` is only meaningful
    there, since site-discovery and application hooks are attached at engine import.
    Called bare it reports the declaration, and `implemented` reads 0 by
    construction — which is itself a trap worth naming rather than leaving to be
    rediscovered.
    """
    registry = REGISTRY if registry is None else registry
    covered = {op.pattern for op in registry}
    dupes = [p for p in covered if sum(1 for op in registry if op.pattern == p) > 1]
    return {
        "registry_size": len(REGISTRY),
        "patterns_covered": len(covered),
        "partition_size": len(MECHANICAL_PATTERNS),
        "missing": sorted(MECHANICAL_PATTERNS - covered),
        "extra": sorted(covered - MECHANICAL_PATTERNS),
        "duplicate_patterns": sorted(dupes),
        "class_a": sorted(op.pattern for op in registry if op.class_ab == "A"),
        "class_b": sorted(op.pattern for op in registry if op.class_ab == "B"),
        "gate_scored": sorted(op.pattern for op in registry if op.gate_scored),
        "reported_separately": sorted(op.pattern for op in registry if not op.gate_scored),
        "implemented": sorted(op.pattern for op in registry if op.implemented),
    }


def gate_denominator(conformance_path: str = "studies/phase2_5a/conformance.json") -> dict:
    """GATE-H3's denominator, computed from measured profile status.

    Addendum F rules 13. It is computed rather than set so that a change in the
    measurement moves the number and surfaces the contradiction, instead of the
    number silently agreeing with a stale premise:

        17  MECHANICAL partition (scopes the battery, not the gate)
        -1  W-EP-01, unfireable as shipped
        -3  patterns with ZERO conformant-but-flawed mutants
        =13

    The -3 term reads `conformance.json`; it is never hand-set. If the measurement
    changes, so does the denominator, and a mismatch against the ruled 13 is a
    finding rather than a config drift.

    NOTE ON THE RATIONALE, not the arithmetic. Addendum F justifies the -3 as the
    completeness profile "intercepting before C3 runs". **Measured, that is not what
    the pipeline does.** `check.run_structured` runs C2 → C1 → C2.5 → C3
    unconditionally with no short-circuit, and on a schema-caught mutant C3 runs and
    fires the target: 12 of 23 mutants are non-conformant AND rule-layer-caught. The
    arithmetic survives on the narrower true ground — under addendum E headline
    recall comes from conformant-but-flawed mutants only, and these three patterns
    admit none — but the architectural claim as worded is falsifiable with one CLI
    invocation and should be restated before it reaches A4.
    """
    import json as _json
    from pathlib import Path as _Path

    data = _json.loads(_Path(conformance_path).read_text())
    by_pattern: dict[str, list[bool]] = {}
    for m in data["mutants"]:
        by_pattern.setdefault(m["pattern"], []).append(m["conformant"])

    no_conformant = sorted(p for p, v in by_pattern.items() if not any(v))
    unfireable = sorted(op.pattern for op in REGISTRY if not op.gate_scored)
    excluded = sorted(set(no_conformant) | set(unfireable))
    return {
        "partition": len(MECHANICAL_PATTERNS),
        "excluded_unfireable": unfireable,
        "excluded_no_conformant_mutant": no_conformant,
        "denominator": len(MECHANICAL_PATTERNS) - len(excluded),
        "gate_patterns": sorted(MECHANICAL_PATTERNS - set(excluded)),
        "measured_from": conformance_path,
        "catalog_version": data.get("catalog_version"),
    }


def by_id(operator_id: str) -> Operator:
    for op in REGISTRY:
        if op.id == operator_id:
            return op
    raise KeyError(f"no such operator: {operator_id}")


def for_pattern(pattern_id: str) -> list[Operator]:
    return [op for op in REGISTRY if op.pattern == pattern_id]
