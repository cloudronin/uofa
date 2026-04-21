# UofA Weakener Detection Engine

> **Status:** Standalone Java CLI for direct Jena invocation. Most users should use the `uofa rules` Python CLI wrapper, which loads this rules file and runs the same engine.
> **Schema:** UofA v0.5 (`spec/context/v0.5.jsonld` + `spec/shapes/uofa_shacl.ttl`)
> **Engine:** Apache Jena 5.3, GenericRuleReasoner, forward RETE mode
> **Catalog:** 23 patterns in v0.5.2 (21 Level-1 + 2 active Level-2; COMPOUND-02 commented out)

## Architecture

```
                    ┌─────────────────────────────────┐
                    │  packs/vv40/examples/morrison/cou1/         │
                    │  uofa-morrison-cou1.jsonld       │
                    │  (JSON-LD evidence package)      │
                    └──────────┬──────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │   Jena JSON-LD Parser         │
               │   + external @context resolve │
               └──────────┬────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────────────────┐
    │              RDF Data Graph                       │
    │  (UnitOfAssurance + CredibilityFactor +          │
    │   ValidationResult + DecisionRecord + PROV)      │
    └──────────┬───────────────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────────────────┐
    │         GenericRuleReasoner (FORWARD RETE)        │
    │                                                   │
    │  Phase 1: Core weakener detection rules (21)      │
    │    Epistemic (W-EP-*)    × 4                      │
    │    Aleatoric (W-AL-*)    × 2                      │
    │    Ontological (W-ON-*)  × 2                      │
    │    Argument (W-AR-*)     × 5                      │
    │    Structural (W-SI-*)   × 2                      │
    │    Consistency (W-CON-*) × 5                      │
    │    Provenance (W-PROV-*) × 1                      │
    │                                                   │
    │  Phase 2: Compound inference rules (chained)      │
    │    COMPOUND-01: Risk escalation      [active]     │
    │    COMPOUND-02: Factor credibility    [commented  │
    │                 erosion                 out, v0.6] │
    │    COMPOUND-03: Assurance override   [active]     │
    │                                                   │
    │  Compound rules fire ON the output of Phase 1     │
    │  → This is what SPARQL cannot do                  │
    └──────────┬───────────────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────────────────┐
    │           WeakenerAnnotation triples               │
    │  (materialized in the deductions graph)            │
    │                                                    │
    │  + Compound annotations with escalationSource      │
    │    and erosionCause provenance links                │
    └──────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Build
cd uofa-weakener-rules
mvn package -q

# Run against Morrison COU1
java -jar target/uofa-weakener-engine-0.1.0.jar \
    ../packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../spec/context/v0.5.jsonld

# Output deductions as Turtle
java -jar target/uofa-weakener-engine-0.1.0.jar \
    ../packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../spec/context/v0.5.jsonld \
    --format turtle \
    --output cou1-weakeners.ttl

# Trace rule execution (debug)
java -jar target/uofa-weakener-engine-0.1.0.jar \
    ../packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../spec/context/v0.5.jsonld \
    --trace
```

## Expected Output: Morrison COU1 (v0.5.2)

```
══════════════════════════════════════════════════════════════
  UofA Weakener Detection Report
  Input: uofa-morrison-cou1.jsonld
══════════════════════════════════════════════════════════════

  SUMMARY: 24 weakener(s) detected
  ─────────────────────────────────────────────────
    Critical:  6
    High:  17
    Medium:  1

  ⚡ COMPOUND-01 [Critical] — 5 hit(s)
      → affected: cou1

  ⚡ COMPOUND-03 [High] — 1 hit(s)
      → affected: cou1

  ⚠ W-AL-01 [High] — 3 hit(s)         ← fires on ALL 3 validation results
      → affected: hemolysis-comparison-cou1
      → affected: mesh-convergence
      → affected: piv-velocity-comparison

  ⚠ W-AR-05 [High] — 3 hit(s)
      → affected: mesh-convergence
      → affected: hemolysis-comparison-cou1
      → affected: piv-velocity-comparison

  ⚠ W-CON-01 [High] — 6 hit(s)
      → affected: numerical-solver-error
      → affected: test-samples
      → affected: model-inputs
      → affected: model-form
      → affected: use-error
      → affected: equivalency-of-input-parameters

  ⚠ W-CON-04 [Medium] — 1 hit(s)
      → affected: cou1

  ⚠ W-EP-01 [Critical] — 1 hit(s)
      → affected: cou1-hemolysis-adequacy

  ⚠ W-EP-02 [High] — 3 hit(s)
      → affected: mesh-convergence
      → affected: hemolysis-comparison-cou1
      → affected: piv-velocity-comparison

  ⚠ W-ON-02 [High] — 1 hit(s)
      → affected: cou1-cpb

  ─────────────────────────────────────────────────
  ⚡ 6 compound inference(s) — these require
    chained rule reasoning and cannot be detected
    by standalone SPARQL queries.
```

## Expected COU1 vs COU2 Divergence (NAFEMS Demo Point, v0.5.2)

| Pattern | COU1 | COU2 | Why different |
|---------|------|------|---------------|
| W-EP-01 | Fires 1× | Does NOT fire | COU2 has full provenance chain |
| W-EP-02 | Fires 3× | Does NOT fire | COU2 has generation activities |
| **W-EP-04** | **Does NOT fire** | **Fires 6×** | COU2 has 6 unassessed factors at MRL 5 > 2 |
| **W-AL-01** | **Fires 3×** | **Does NOT fire** | COU2 has Monte Carlo UQ |
| **W-AL-02** | Does NOT fire | **Fires 1×** | COU2 reports UQ but no sensitivity analysis |
| W-AR-05 | Fires 3× | Does NOT fire | COU2 has comparator linkages |
| W-CON-01 | Fires 6× | Does NOT fire | COU2 is Not Accepted — rule gates on Accepted |
| W-CON-04 | Fires 1× | Fires 1× | Both COUs lack linked sensitivity analysis (structural gap) |
| W-ON-02 | Fires 1× | Fires 1× | Both COUs lack applicability + operating-envelope metadata |
| **W-PROV-01** | **Does NOT fire** | **Fires 7×** | COU2 has 7 provenance-chain orphans — W-EP-01 already catches COU1's direct-orphan case |
| **COMPOUND-01** | **Fires 5×** | **Fires 2×** | Both have Critical + High coexisting; v0.5.2 exposes 2 new cascades on COU2 via W-PROV-01 Criticals |
| COMPOUND-03 | Fires 1× | Does NOT fire | COU2 assurance level is already Low |

**The v0.5.2 cross-COU divergence:**
Same model, same data, same rules → COU1 (MRL 2, Accepted) has 24 weakeners
dominated by W-CON-01 (6× under the Accepted gate) and a W-EP-01 orphan claim
that cascades into 5 COMPOUND-01 firings. COU2 (MRL 5, Not Accepted) has 18
weakeners dominated by W-PROV-01 (7×) on unresolved provenance roots plus
W-EP-04 (6×) on unassessed factors at elevated model risk. Seven patterns
diverge between the two COUs. Morrison only assessed 7 of 13 factors — the
gap is invisible in the prose paper but machine-visible in the UofA.

## NAFEMS Demo Script (90 seconds, v0.5.2)

1. **Show:** Morrison COU1 JSON-LD (the evidence package — 13 factors, 7 assessed)
2. **Run:** `uofa rules packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld --build`
3. **Show:** Summary output — 24 weakeners across 9 patterns on COU1 (7 Level-1 + 2 compound), W-EP-04 does NOT fire at MRL 2
4. **Run:** `uofa rules packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld --build`
5. **Show:** 18 weakeners across 6 patterns on COU2 — W-PROV-01 dominates (7× provenance-chain orphans), W-EP-04 fires 6× on unassessed factors at MRL 5, and 2 COMPOUND-01 cascades fire where W-PROV-01 Criticals coexist with High weakeners on `cou2`
6. **Run:** `uofa diff packs/vv40/examples/morrison/cou1/...jsonld packs/vv40/examples/morrison/cou2/...jsonld`
7. **Key line:** "Morrison only assessed 7 of 13 factors. At MRL 2 the gap manifests as
   W-CON-01 missing-level assertions under the Accepted decision. At MRL 5 the same gap
   fires 6 epistemic weakeners plus 7 provenance-chain orphans. Same data, same rules —
   risk context drives the divergence. And the compound rules catch interactions no SPARQL
   query can see, including 2 new cascades on COU2 that the v0.5.2 single-engine refactor
   unblocked."

## IP Boundary

| Layer | Open | Proprietary |
|-------|------|-------------|
| Pattern taxonomy (names, IDs, categories) | ✓ | |
| Pattern descriptions & V&V 40 mapping | ✓ | |
| SPARQL reference queries (basic detection) | ✓ | |
| **Jena rule implementations** | | **✓** |
| **Compound inference rules** | | **✓** |
| **Domain-specific rule extensions** | | **✓** |
| **Severity calibration logic** | | **✓** |

## File Structure

```
uofa-weakener-rules/
├── pom.xml                              # Maven build (Jena 5.3 + picocli)
├── src/
│   └── main/
│       ├── java/com/crediblesimulation/
│       │   └── WeakenerEngine.java      # CLI entry point
│       └── resources/
│           └── uofa_weakener.rules      # ← THE IP ARTIFACT
└── README.md
```
