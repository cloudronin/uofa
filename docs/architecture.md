# Architecture: One UofA per Context of Use

UofA models credibility assessment at the **COU level**, not the individual factor level. Each UofA packages the complete credibility decision for one Context of Use — including all per-factor assessments as embedded CredibilityFactor nodes and any detected quality gaps as WeakenerAnnotation nodes.

<!-- Tree below reflects the actual `uofa rules` output as of v0.7.1 against
     packs/vv40/examples/morrison/{cou1,cou2}/uofa-morrison-{cou1,cou2}.jsonld.
     Re-run those commands and update if the catalog or examples change. -->

```
Morrison Blood Pump Assessment
├── morrison/cou1/uofa-morrison-cou1.jsonld (ProfileComplete)
│   COU1: CPB Use (Class II) — Model Risk Level 2
│   ├── hasContextOfUse    → COU1 node
│   ├── bindsRequirement   → hemolysis safety requirement
│   ├── bindsModel         → ANSYS CFX v.15.0 + Eulerian HI model
│   ├── bindsDataset       → [PIV data, hemolysis in vitro data]
│   ├── hasValidationResult → [mesh convergence, PIV velocity, hemolysis comparison]
│   ├── hasCredibilityFactor → [13 V&V 40 factors: 7 assessed + 6 not-assessed]
│   ├── hasWeakener        → [W-AL-01 (3×), W-AR-05 (3×), W-EP-02 (3×), W-CON-04, W-ON-02]
│   ├── hasDecisionRecord  → "Accepted for COU1"
│   ├── hash               → sha256:<real hash>
│   ├── signature          → ed25519:<real signature>
│   └── wasDerivedFrom     → Morrison DOI
│
└── morrison/cou2/uofa-morrison-cou2.jsonld (ProfileComplete)
    COU2: VAD Use (Class III) — Model Risk Level 5
    ├── hasCredibilityFactor → [13 V&V 40 factors: 7 assessed + 6 not-assessed]
    ├── hasWeakener        → [W-PROV-01 (7×), W-EP-04 (6×), W-ON-02, W-AL-02, W-CON-04] + [COMPOUND-01 (2×)]
    └── At MRL 5 the risk-driven catalog shifts: W-PROV-01 dominates COU2 (7 provenance-chain orphans),
        W-EP-04 fires 6× on not-assessed factors, and two of W-PROV-01's Criticals coexist with High
        weakeners — triggering 2 COMPOUND-01 cascades that don't fire under COU1's lower-MRL profile.
```

Shared entities (model, datasets, pump geometry) are referenced by IRI, not duplicated. The divergence between COU1 and COU2 weakener profiles is the central analytical demonstration.
