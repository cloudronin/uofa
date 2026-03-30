# UofA Weakener Detection Engine

> **Status:** Implementation scaffold — rules file ready, Java CLI ready for `mvn package`  
> **Schema:** UofA v0.2 (`uofa_v0_2.jsonld` + `uofa_shacl.ttl`)  
> **Engine:** Apache Jena 5.3, GenericRuleReasoner, forward RETE mode

## Architecture

```
                    ┌─────────────────────────────────┐
                    │  examples/morrison/cou1/         │
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
    │  Phase 1: Core weakener detection rules           │
    │    W-EP-01, W-EP-02, W-AL-01, W-ON-01,           │
    │    W-AR-01, W-AR-02, W-AR-05, W-SI-01, W-SI-02   │
    │                                                   │
    │  Phase 2: Compound inference rules (chained)      │
    │    COMPOUND-01: Risk escalation                   │
    │    COMPOUND-02: Factor credibility erosion        │
    │    COMPOUND-03: Assurance level override           │
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
    ../examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../uofa_v0_2.jsonld

# Output deductions as Turtle
java -jar target/uofa-weakener-engine-0.1.0.jar \
    ../examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../uofa_v0_2.jsonld \
    --format turtle \
    --output cou1-weakeners.ttl

# Trace rule execution (debug)
java -jar target/uofa-weakener-engine-0.1.0.jar \
    ../examples/morrison/cou1/uofa-morrison-cou1.jsonld \
    --context ../uofa_v0_2.jsonld \
    --trace
```

## Expected Output: Morrison COU1

```
══════════════════════════════════════════════════════════════
  UofA Weakener Detection Report
  Input: examples/morrison/cou1/uofa-morrison-cou1.jsonld
══════════════════════════════════════════════════════════════

  SUMMARY: ~12-15 weakener(s) detected
  ─────────────────────────────────────────────────
    Critical:  ~5-7   (W-EP-01, W-AR-01 per factor, COMPOUND-03)
    High:      ~4-5   (W-AL-01 per result, W-AR-05, COMPOUND-01)
    Medium:    ~2-3   (W-SI-01 placeholder, COMPOUND-02)

  ⚠ W-EP-01 [Critical] — 1 hit(s)
      → affected: cou1-hemolysis-adequacy

  ⚠ W-AL-01 [High] — 3 hit(s)         ← fires on ALL 3 validation results
      → affected: mesh-convergence
      → affected: piv-velocity-comparison
      → affected: hemolysis-comparison-cou1

  ⚠ W-AR-01 [Critical] — 7 hit(s)     ← fires on ALL 7 credibility factors
      → affected: cou1

  ⚠ W-AR-05 [High] — 3 hit(s)
      → affected: mesh-convergence
      → affected: piv-velocity-comparison
      → affected: hemolysis-comparison-cou1

  ⚡ COMPOUND-01 [Critical] — fires    ← W-EP-01 (Critical) + W-AL-01 (High)
      → affected: cou1

  ⚡ COMPOUND-03 [High] — fires        ← assuranceLevel="Medium" + Critical weakener
      → affected: cou1
```

## Expected COU1 vs COU2 Divergence (NAFEMS Demo Point)

| Pattern | COU1 | COU2 | Why different |
|---------|------|------|---------------|
| W-EP-01 | Fires | Fires | Same claim structure |
| **W-AL-01** | **Fires** | **Does NOT fire** | COU2 has Monte Carlo UQ |
| W-AR-01 | Fires | Fires | Same schema gap |
| W-AR-02 | Does NOT fire | **Fires** | COU2 achievedLevel < requiredLevel |
| **COMPOUND-01** | **Fires** | **Different profile** | Different weakener combination |

**The W-AL-01 divergence is the C3 value proposition in one sentence:**
Same model, same data, same rules → different weakener profile because
the COU drove different requirements.

## NAFEMS Demo Script (90 seconds)

1. **Show:** Morrison COU1 JSON-LD (the evidence package)
2. **Run:** `java -jar uofa-weakener-engine.jar cou1.jsonld --context uofa_v0_2.jsonld`
3. **Show:** Summary output — 4 core weakeners + 2 compound inferences
4. **Run:** `java -jar uofa-weakener-engine.jar cou2.jsonld --context uofa_v0_2.jsonld`
5. **Show:** W-AL-01 is absent, W-AR-02 appears, COMPOUND-01 has different profile
6. **Key line:** "Same rules, same model, different evidence quality — because the
   Context of Use drove different requirements. And the compound rules caught
   something no individual SPARQL query could see."

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
