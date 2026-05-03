---
title: Weakeners
description: The UofA defeater taxonomy. 23 patterns across 8 categories, including 2 active compound rules.
---

A weakener is a structural credibility gap detected by the Jena rule engine. Each pattern has an ID, a severity, an affected node, and a description. Weakeners are not errors. They are evidence-package quality alerts.

The current catalog ships **23 patterns**: 21 Level-1 patterns plus 2 active compound patterns. The catalog is open and extensible via domain packs. See the [auto-generated catalog reference](/reference/catalog/) for the full table sourced from the live code.

## The catalog

| Category | Patterns | Examples |
|---|---|---|
| Epistemic | W-EP-01 to W-EP-04 | Orphan claim, broken provenance, evidence-source gap, unassessed factors at elevated risk |
| Aleatoric | W-AL-01, W-AL-02 | Missing uncertainty quantification, missing sensitivity analysis |
| Ontological | W-ON-01, W-ON-02 | Applicability gap, operating-envelope gap |
| Structural | W-SI-01, W-SI-02 | Internal consistency gaps |
| Argumentation | W-AR-01 to W-AR-05 | Comparator absence, eliminative-argumentation gap, residual-risk gap |
| Consistency | W-CON-01 to W-CON-05 | Decision-vs-factor mismatch, profile-vs-evidence mismatch |
| Provenance | W-PROV-01 | Provenance-chain orphan |
| Compound | COMPOUND-01, COMPOUND-03 | Risk escalation, assurance-level override |

Run `uofa catalog` to see the full set with descriptions and severity assignments.

## Severities

| Severity | Meaning | Example |
|---|---|---|
| Critical | Missing evidence the standard explicitly requires for the declared rigor level | W-EP-01 (orphan claim) |
| High | Significant credibility gap that affects defensibility | W-AL-01 (missing UQ) |
| Medium | Structural gap that should be addressed before submission | W-CON-04 (sensitivity analysis not linked) |
| Low | Minor evidence-completeness suggestion | (rare; no Level-1 pattern at Low currently) |

Severity is calibrated against the V&V 40 risk-tier framework. The same factor missing at MRL 2 may be Medium; missing at MRL 5 it is Critical.

## Compound patterns

Compound rules fire on the *output* of Level-1 rules. This chained inference is the differentiator over standalone SPARQL queries.

| Pattern | Severity | Fires when |
|---|---|---|
| COMPOUND-01 | Critical | Critical and High weakeners coexist on the same UofA |
| COMPOUND-03 | High | Declared assurance level is inconsistent with detected gaps |

A second compound pattern (COMPOUND-02 — factor credibility erosion) is implemented but commented out pending v0.6 calibration.

## Worked example: Morrison COU1

Morrison et al. (2019) is the FDA-co-authored worked example for ASME V&V 40. Re-expressed as a UofA evidence package, COU1 (CPB Use, Class II, MRL 2, Accepted) fires **11 weakeners across 5 patterns**:

| Pattern | Severity | Hits | What it detects |
|---|---|---|---|
| W-AL-01 | High | 3 | Missing UQ on validation results |
| W-AR-05 | High | 3 | Comparator absence — results not linked to reference entities |
| W-EP-02 | High | 3 | Broken provenance — validation results with no generation activity |
| W-ON-02 | High | 1 | COU lacks both applicability constraint and operating envelope |
| W-CON-04 | Medium | 1 | Complete profile with no sensitivity analysis linked |

No compound firings at MRL 2. Morrison's CFD-side UQ omission is methodologically defensible at this risk level (the rationale is that bench testing carries the safety determination), but the rule engine still flags it as a potential reuse blocker at higher MRLs.

## COU divergence

`uofa diff` surfaces how the same model produces different weakener profiles under different risk contexts.

```
uofa diff packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
         packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
```

| Pattern | COU1 (MRL 2) | COU2 (MRL 5) | Why |
|---|---|---|---|
| W-PROV-01 | 0 | 7 | COU2 has 7 provenance-chain orphans |
| W-EP-04 | 0 | 6 | COU2 has 6 unassessed factors at MRL 5 > 2 |
| W-EP-02 | 3 | 0 | COU2's regenerated validation activities have proper provenance |
| W-AL-01 | 3 | 0 | COU2 has Monte Carlo UQ in place of MRL-2 omission |
| W-AR-05 | 3 | 0 | COU2 results explicitly linked to comparator entities |
| W-AL-02 | 0 | 1 | COU2 reports UQ but no sensitivity analysis |
| COMPOUND-01 | 0 | 2 | Critical + High coexistence fires only at MRL 5 |

Same model. Same data. Different model risk produces a measurably different credibility evidence profile. This is the central analytical demonstration of the construct.
