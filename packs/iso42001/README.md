# iso42001 — ISO/IEC 42001:2023 AIMS pack (v0.4)

## What this pack does

The iso42001 pack adds AI Management System (AIMS) evidence packaging to UofA, with structural completeness validation against ISO/IEC 42001:2023 Annex A, C3 forward-chaining defect detection adapted for AI assurance evidence, and productive-OOS bundle-sufficiency evidence-gap reporting for the judgment-required half of AIMS evaluation. It is the praxis Tier 4 cross-domain validation, demonstrating that the UofA methodology generalizes from regulated CM&S (medical via V&V 40, aerospace via NASA-STD-7009B) to regulated AI assurance.

## What you need to use it

UofA core v0.5 or higher and the OOS engine v0.1 or higher (both shipped). JSON-LD evidence packages structured per the AIMS vocabulary at `https://uofa.net/vocab/aims#`. Optional: `--explain` flag for auditor-readable interpretation of pack outputs.

## Quick start

```bash
# Verify the pack loads
python -m uofa_cli packs iso42001 --detail

# Validate an AIMS evidence package against the SHACL profile
python -m uofa_cli shacl path/to/uofa-aims-package.jsonld --pack iso42001

# Run dual-output evaluation (SHACL + C3 weakeners + OOS bundle-sufficiency)
python -m uofa_cli check --pack iso42001 path/to/uofa-aims-package.jsonld

# Run end-to-end on the bundled hybrid case study (COU1 + COU2)
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou1/uofa-iso42001-cou1.jsonld
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou2/uofa-iso42001-cou2.jsonld
```

OOS evaluation is **on by default** for this pack (`pack.json::oos.enabled: true`). To disable at runtime, pass `--no-oos`.

**Derivation pre-pass (v0.5):** the pack also runs SPARQL CONSTRUCT queries between SHACL and C3 to materialize derived analytic predicates that downstream rules consume. Per `UofA_Derivation_PrePass_Spec_v0_1.md`. Eight CONSTRUCTs at `packs/iso42001/derivations/iso42001_derivations_v0.1.sparql` fix brittleness in 8 W-AIMS rules that pure Jena rule expressivity couldn't handle (negated existentials, date arithmetic, semver comparison, set difference, multi-valued cross-entity checks). Pre-pass is on by default for this pack (`pack.json::derivations.enabled: true`); disable at runtime with `--no-derivations`.

## What is in the pack

- **Vocabulary** (`shapes/iso42001_shapes.ttl` §A) — `uofa-aims:` namespace with ~50 classes covering management-system clauses 4-10, Annex A controls A.2-A.10, eight AIMS claim types, and supporting evidence types for the OOS rule catalog.
- **SHACL completeness profile** (`shapes/iso42001_shapes.ttl` §B-§D) — deep Annex A artifact shapes, light clause attestation shapes (one per management-system clause family), and Statement of Applicability (SoA) shape with workbook-shape DE/OE field validation.
- **C3 forward-chaining weakener catalog** (`rules/iso42001_weakener.rules`) — 13 patterns for structural defects within structurally complete bundles (audit staleness, data lineage discontinuity, model evaluation/deployment drift, role assignment gaps, crosswalk validity).
- **OOS bundle-sufficiency rule catalog** (`rules/oos/oos_v0.1.rules`) — 8 rules covering judgment-required AIMS controls: policy appropriateness, risk identification completeness, control operational effectiveness, impact assessment scope adequacy, stakeholder consultation adequacy, internal audit independence, nonconformity root cause adequacy, AIMS objective measurement methodology validity. One rule per management-system clause family (per spec §2.4).
- **Coverage matrix** (`coverage/nist_ai_rmf_govern_coverage.md`) — dual-detection matrix against NIST AI RMF GOVERN function failure modes with C3-detected, OOS-detected, combined, and out-of-pack-scope cells. Combined coverage target ≥ 70%.
- **Hybrid case study** (`examples/hybrid/`) — two contrast Contexts of Use (COU1 low-risk LLM knowledge retrieval, COU2 high-risk LLM regulatory communication) demonstrating differential dual output across both detection paths.
- **Calibration packages** (`specs/calibration/packages/cal-aims-001..008-*.jsonld`) — eight hybrid-construction packages, one per OOS rule, used as production-judge calibration anchors and over-firing discipline tests.

## Dual-output methodology

The pack produces three classes of output for any AIMS evidence package. **Structural validation** pass/fail per Annex A control and management-system clause. **C3 firings** identifying defects in structurally complete bundles (stale audits, broken data lineage, missing role assignments). **OOS evidence-gap reports** identifying judgment-required evidence the bundle does not contain (independent verification of control effectiveness, expert review of root cause analysis, methodology validation for AIMS objective measurement).

The dual output is intended for auditor workflow. C3 firings flag credibility weaknesses to address. OOS firings flag documentation requests to send back to the audited organization. The pack does not produce remediation suggestions (per the Copilot boundary in the Explain spec). Differential dual-output across the COU1/COU2 case study pair demonstrates that bundle-sufficiency depends on assurance level: a control-operational-effectiveness OOS firing on a low-risk knowledge retrieval system is contextualized as appropriate for the assurance level; the same firing on a high-risk regulatory system is a substantive gap.

## Hybrid case study

Two Contexts of Use following the Morrison COU1/COU2 pattern (see `packs/vv40/examples/morrison/`):

- **COU1 — low-risk LLM knowledge retrieval.** Internal employee-facing LLM application that retrieves and summarizes information from the organization's internal knowledge base. ISO 42001 risk profile: Low. Expected output: small C3 firing set, several OOS firings contextualized as appropriate for assurance level.
- **COU2 — high-risk LLM regulatory communication.** Customer-facing LLM application generating draft responses for regulated communications. ISO 42001 risk profile: High. Expected output: larger C3 firing set with multiple high-severity firings, substantial OOS firings *not* contextualized away — high-risk AI demands independent verification, stakeholder validation, expert root cause review, and methodology validation.

```bash
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou1/uofa-iso42001-cou1.jsonld
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou2/uofa-iso42001-cou2.jsonld
```

Public-anchor categories (StackAware-anchored per spec §2.6.2): AI policy structure, AIMS scope statement, risk assessment methodology, impact assessment methodology, Statement of Applicability structure. Synthetic-supplement categories: AI system inventory entry, full impact assessment content, data resource catalog, model evaluation report, deployment configuration, monitoring metrics, incident response and remediation tracking.

## Methodology context

This pack is the praxis Tier 4 cross-domain validation. The C1 catalog coverage methodology is reused with NIST AI RMF GOVERN as the external taxonomy. The C2 SHACL completeness profile machinery is reused with new shapes including the v0.4 SoA shape. The C3 Jena weakener detection engine is reused with new patterns. The productive-OOS framework (introduced May 4, 2026) is reused as core infrastructure — this pack is the strongest empirical demonstration of bundle-sufficiency as the cross-domain methodology spine. See `Product Requirements/UofA_iso42001_Pack_Spec_v0_4.md` for full methodology grounding.

## AIUC-1 forward pointer

The agentic AI assurance space is moving fast. AIUC-1 is the leading consortium standard candidate for agentic AI assurance and may converge with or extend ISO 42001 over the next 12-18 months. The UofA dual-output methodology generalizes naturally to AIUC-1 because the bundle-sufficiency framing operates on evidence rather than standard-specific structure. AIUC-1 encoding is post-defense work, building on this pack's vocabulary and shape conventions.

## Acknowledgments and attribution

The hybrid case study evidence categories anchor in StackAware's publicly documented AIMS materials authored by Walter Haydock and corroborated by Schellman as accredited certification body. Specific organizational content is synthesized; structural patterns (AI policy outline, risk methodology structure, impact assessment template, SoA structure) are inspired by StackAware's published materials with attribution. The Statement of Applicability shape design is informed by shape evidence from real-world AIMS practice (per the Qualtrics workbook reviewed during v0.4 design); workbook content does not appear in pack artifacts (per spec §1.2 organizational-content exclusion).

## License

Apache-2.0. See repository root LICENSE file.
