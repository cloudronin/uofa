# UofA Surrogate-Credibility Pack (`packs/surrogate`)

Packages machine-verifiable **credibility evidence** for physics-based AI/ML
**surrogate** models used to complement or replace high-fidelity simulation
(CFD, FEA, CHT): data-driven emulators, reduced-order models (ROMs), operator
learning (FNO/DeepONet), physics-informed neural networks (PINNs), and ML-based
closure/turbulence models.

UofA's invariant holds: the pack checks **evidence completeness and
auditability, not model correctness**. Zero weakeners means the surrogate's
credibility package is structurally complete and auditable — *not* that the
surrogate is accurate. The credibility decision belongs to the practitioner and
the COU acceptance criteria, never to the pack.

## Status

v0.1, draft. Build template: the ISO 42001 pack. Pack version stamps
independently of the CLI release.

## Where evidence comes from

- **Document evidence** (model cards, training/validation memos) flows through
  the existing `extract → review → import` on-ramp via the LLM extract path
  (`prompts/surrogate_extract_prompt.txt`).
- **Measured evidence** (residuals, envelope coverage, physics-constraint
  residuals, UQ calibration) arrives pre-structured from the **Surrogate
  Interrogation Probe (SIP)** and is mapped directly onto this pack's
  vocabulary — no LLM step. See `SIP_Evidence_Contract_Spec_v0_1.md`.

## Vocabulary (`uofa-surr:` — `https://uofa.net/vocab/surrogate#`)

`SurrogateModel` (+`surrogateType`), `TrainingEnvelope`/`EnvelopeDimension`,
`EvaluationPoint`/`EvaluationRegion`, `PhysicsConstraint` +
`hasConstraintCheckEvidence`, `surrogateUQMethod`, `hasBenchmarkProvenance`,
and the embedded `ParentModelSnapshot` (`parentCOU`, `parentDecision`,
`parentMRL`, `parentSignatureTimestamp`, `snapshotTimestamp`). All additive and
optional at the SHACL level — the core `ProfileMinimal`/`ProfileComplete`
switch and shared patterns are untouched.

## Weakener catalog

Four reuse, three new (the real delta):

| Pattern | Defeater | Status | Severity |
|---|---|---|---|
| W-EP-03 | Training data predates model revision | reuse | High |
| W-AR-04 | Surrogate retrained, version drift | reuse | High |
| W-AL-02 | UQ declared, no surrogate sensitivity analysis | reuse | Medium |
| W-ON-02 | No operating envelope declared (presence) | reuse | High |
| **W-SURR-01** | Physics-constraint check evidence missing | new | High |
| **W-SURR-02** | Credibility inherited from un/under-validated parent | new | Critical / High |
| **W-SURR-03** | Evaluation point outside declared training envelope | new | High |

W-SURR-02 is severity-split: explicit parent `Not Accepted` → **Critical**;
parent decision absent/unrecorded → **High** (an in-progress parent is a
different epistemic state from a rejected one). W-SURR-03 is a *containment*
check (distinct from W-ON-02's *presence* check); it is a new pattern rather
than an enrichment of W-ON-02 so the shared core pattern's semantics are
unchanged across all packs.

Method-first: **W-SURR-04** (benchmark coverage gap, SIP-enabled) and
**interrogation-residuals-unlinked** stay documented gap-probe *candidates*,
promoted only through the coverage method — not pre-implemented.

## Coverage

The catalog's comprehensiveness is reported against
`docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md` (Jakeman et al. arXiv:2502.15496,
inverted to defeaters). This is an **emerging reference**: coverage is reported
as the *fraction of reference defeaters detected* with named gaps, **not** a
Cohen's-κ claim against a canonical taxonomy. See `coverage/`.

## Signed engineer decision + conformance (Addendum A)

SIP measures; it never judges. The engineer's acceptance decision is captured
as a signed, attributed human act: `uofa decision review` prints the
surrogate-vs-reference comparison (read-only, no verdict), then `uofa decision
sign --key <engineer-key> --criterion … --value <accepted|not-accepted>` writes
an `engineerDecision` block signed over the decision plus the measurements it
references. `uofa verify` checks both the SIP measurement signature and the
engineer decision signature independently; a missing or unverifiable decision
is "no engineer decision," never inferred acceptance.

**Conformance is a property of the artifact, not a partnership.** Vendors may
drive the CLI or consume the signed package, but the decision signature MUST be
the deciding human's key — a platform substituting its own service key is
non-conformant, checkable from the package alone. UofA verifies; it never holds
or issues the engineer's key (AGENTS.md §12).
