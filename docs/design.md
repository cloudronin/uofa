# Research Context and Design Principles

## Research Context

UofA is the subject of a Doctor of Engineering praxis at George Washington University. The evaluation uses two FDA case studies:

- **Tier 1 (Retrospective):** Morrison et al. (2019) — FDA generic centrifugal blood pump V&V 40 credibility assessment. Re-expressed as UofA evidence packages with real cryptographic integrity. Full 13-factor assessment (7 assessed, 6 not-assessed) with risk-driven divergence across the catalog:

  - **Morrison COU1** (MRL 2, Accepted): 11 weakeners spanning 5 patterns (W-AL-01 ×3, W-AR-05 ×3, W-EP-02 ×3, W-CON-04, W-ON-02). 10 High + 1 Medium; no Critical and no compound rules fire under the lower-risk profile.
  - **Morrison COU2** (MRL 5, Not Accepted): 18 weakeners spanning 6 patterns. 9 Critical (7 W-PROV-01 provenance-chain orphans plus 2 COMPOUND-01 cascades from coexisting Critical and High), 7 High (6 W-EP-04 on unassessed factors at elevated model risk, 1 W-ON-02), 2 Medium.

  The cross-COU divergence (7 divergences between COU1 and COU2 per `uofa diff`) is the central analytical demonstration: same model, same data, different credibility requirements driven by different model risk produce measurably different credibility evidence profiles.

- **Tier 2 (Prospective):** FDA VICTRE pipeline — live computational workflow instrumented to generate UofAs during execution rather than from retrospective documents.
- **Tier 3 (Exploratory):** Multi-component stress test on VICTRE — simulates change events to test continuous re-issuance and hierarchical credibility composition.

Early findings — including the aerospace companion case study ([HPT Blade CHT, NASA-STD-7009B](examples/hpt-blade-cht.md)) that reproduces the Morrison COU1/COU2 divergence mechanism in a turbomachinery domain — will be presented at [NAFEMS Americas 2026](https://www.nafems.org/events/nafems/2026/nafems-americas-conference/) (May 27–29, St. Charles, MO).

## Design Principles

| Principle | Meaning |
|---|---|
| **Minimal** | Small JSON-LD document, human-readable, one file per COU |
| **Semantic** | Aligns with PROV-O, V&V 40, and domain ontologies |
| **Verifiable** | Real SHA-256 hashes + ed25519 signatures + SHACL validation |
| **Composable** | UofAs form nodes in system-level assurance graphs via `wasDerivedFrom` |
| **Tool-agnostic** | Works with any simulation tool, MBSE platform, or ML pipeline |
| **Hide the plumbing** | Practitioners see completeness reports and gap alerts, not triples and SPARQL |
