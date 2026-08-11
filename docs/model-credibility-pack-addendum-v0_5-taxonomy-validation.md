# Addendum v0.5: A16 — Group-B taxonomy validation on a real-world corpus

**Applies to:** model-credibility-pack-spec.md + addenda v0.1–v0.4 + impl plan
**Status:** design spec. Decision recorded: the Group-B weakener taxonomy is
**candidate**, not settled, until validated against a real-world corpus with
adjudicated ground truth. The settle gate sits between Phase 4 (prose
extractor) and Phase 5 (public cards). No v1.0 pack release, no published
cards, no badge outreach until the catalog settles.

Methodology is the praxis §6.7 pattern applied to this pack: method
discovers, empirics validate, catalog closes.

---

## A16.1 What is being validated, and what is not

Three questions, separated because they have different arbiters:

| Question | Arbiter | Study component |
|---|---|---|
| Firing correctness — does each rule fire iff the card lacks the property | judge panel vs gold labels | extraction validation (A16.3) |
| Finding validity — when fired, is the stated deficiency real and correctly described | adjudication panel | finding adjudication (A16.4) |
| Construct validity — are these the right bars at all | grounding audit + discovery track; NOT the panel | A16.5, A16.6 |

The panel cannot settle construct validity; claiming otherwise would launder
normative judgment through inter-rater agreement. The study reports the
first two as measurements and the third as an audit plus an open discovery
channel.

## A16.2 Corpus, sample frame, pre-registration

- **Corpus:** Liang `datasetcard_info.parquet` (32,111 cards, snapshot
  2023-10-01), pinned by repo revision and row content hash (A9.1 artifact
  pins, non-HF fallback form).
- **Sample frame (pre-registered before any judge call):** stratified by
  task category (from the parquet), card word count band, and presence of an
  eval section per the A3 detector. Eval-bearing cards are the assessment
  population; a smaller no-eval stratum validates the detector's negative
  calls. Target n: 300–500 eval-bearing cards for silver labeling, with a
  gold subset per A16.3.
- **Pre-registration artifact:** rule set frozen at the candidate catalog,
  thresholds declared, frame written, committed to
  `studies/taxonomy-validation/` BEFORE the first judge invocation. Same
  discipline as Phase 3's spec: the bar is set before the attempt.

  Candidate catalog as of 2026-08-11, after the design rulings: **W-EV-GEN-02,
  -DET-03, -NULL-04, -COU-05, -CAP-06, -DIV-07, -SUB-08, -COR-09**, plus
  COMPOUND-EV-01 and -02. Two corrections to earlier drafts of this section:
  **W-EV-UQ-01 was withdrawn** (core's W-AL-01 already fires on the same
  property and the same node, so a parallel rule would report one gap twice),
  and **W-EV-COV-09 is named COR-09** — "coverage" was the reading the design
  ruling rejected, and an id naming it invites drift back toward it. W-AL-01 is
  core's and is not under validation here; its firings are correct by
  construction on structured input (A16.8).

- **Register precondition: `furnishers.PENDING_EMISSION` must be EMPTY for any
  rule entering validation.** A rule whose firing condition is structurally
  always-true has no defined precision against ground truth — it does not
  discriminate, so measuring its discrimination is meaningless. Two rules are in
  that state today: W-EV-COR-09 fires on every reported result until DIV-07's
  constituent matching populates `corroboratedBy`, and W-EV-SUB-08 fires on
  every hosted endpoint until Phase-6 source pinning can supply
  `subjectVersionGuarantee` for a local checkpoint.

  Requiring the register empty — rather than excluding register-resident rules
  from the cohort — makes "retire your PENDING entry" a precondition of
  settling, which aligns the engineering queue with the validation gate at no
  cost. The register is asserted in both directions by
  `tests/test_group_b_rule_property_coverage.py`, so it cannot silently become a
  permanent exemption list.

## A16.3 Extraction validation (firing correctness)

RQ3 methodology carried over:

- **Gold set:** 100–150 cards hand-labeled by the author on the seven Group-B
  properties, presence/absence, with the section-scoping constraint applied
  (only content under an evaluation heading counts — the binding rule from
  the 11× temperature near-miss, now a labeling instruction).
- **Panel:** three judges, per-judge agreement vs gold ≥80%, pairwise
  κ ≥ 0.70, per Phase 3 calibration bars. Judges that fail calibration are
  replaced, not averaged.
- **Silver labels** at frame scale only after calibration passes.
- **Per-rule report:** precision and recall of each rule's firings against
  gold/silver labels, with the mentioned-vs-eval-scoped split reported so
  scope leakage is visible per property.

## A16.4 Finding adjudication (firing for the right reasons)

Phase 3 Stage 5 pattern: for a stratified sample of actual firings, judges
see the card and the rendered finding text and adjudicate whether the stated
deficiency is (a) present, (b) correctly attributed to the claimant, and
(c) correctly severity-framed. Disagreements adjudicated, not averaged.
Output: per-rule finding-validity rate, the number that decides whether a
rule's *wording* survives even where its firing logic does.

## A16.5 Construct grounding audit

Every candidate rule carries a written grounding line: the standard clause
(800-3 §, V&V40 factor, NASA-7009 configuration control) or published
defeater source (Seahaven) it operationalizes. A rule with no grounding line
does not enter validation — it is withdrawn or grounded first. The audit is
a table in the study, reviewable by the committee and by FAccT reviewers.

## A16.6 Discovery track (the catalog's second tier)

Judges additionally flag credibility-relevant deficiencies in sampled cards
that NO current rule captures. Flags are clustered and adjudicated; clusters
surviving adjudication become **candidate patterns** for a second tier,
entering the catalog only through the same validation path. This is the
§6.7 symmetry: gap_probe → adjudication → catalog closure, applied to
Group B.

## A16.7 Settle criteria (declared now)

A rule **settles** into the v1.0 catalog iff:
1. firing precision ≥ 0.90 and recall ≥ 0.80 against adjudicated labels, and
2. finding-validity rate ≥ 0.85 on adjudicated firings, and
3. its grounding line survives the audit.

A rule failing 1 or 2 is revised and re-validated on a held-out split, or
demoted to candidate tier. A rule failing 3 is withdrawn. Compounds settle
only if all constituent rules settle. The catalog closes when every shipped
rule has settled; the pack's v1.0, the public cards, and badge outreach are
gated on closure.

### The zero-prevalence settle path (amended 2026-08-11)

The gold set returned **zero positive instances** for P2, P5, P6 and P7 across
150 hand-labeled cards. Every row is a "should fire" case, so **sensitivity is
measurable and specificity is not** — and both a working rule and one that fires
unconditionally score 1.00. A16.7's criteria would be met trivially.

This is the `PENDING_EMISSION` problem arriving from the **data** side: the
register guaranteed the rules *can* discriminate, not that the population lets
them.

**Ruling.** Those four rules settle via:

1. **Prevalence reported as the finding.** 0/150 stands as a headline empirical
   result, and it is the two-source convergence
   (`studies/cohort-2026-08` n=427; `studies/card-eval-reporting-2026-08` n=49)
   confirmed at gold quality on a third population.
2. **A bounded enrichment stratum** measuring the one direction the gold set
   cannot: whether a rule falsely fires on a card that genuinely states the
   property. See `studies/taxonomy-validation/ENRICHMENT-PROTOCOL.md`, which is
   signed before any cards are pulled and whose stratum is excluded from every
   prevalence figure.

**Why both, rather than prevalence alone.** With no positives, a hallucinated
*clear* is detectable but a false *fire* is not — and the false fire is a public
accusation about a named vendor's card. Settling four rules with that direction
untested is not settling them.

**Honest exit.** If the declared search finds no positives for P6 or P7, the
documented search is the evidence and those rules settle as: *positive class
near-empty in the wild; clear-direction validated on synthetic fixtures,
false-fire direction unvalidated for want of instances, search yield reported.*
A rule stating its own limit is a stronger position than a specificity figure
computed on two cards.

### Two settle paths, because two kinds of rule (recorded 2026-08-11)

Criteria 1 and 2 presuppose a judge who can look at a card and say whether the
rule was right to fire. Not every rule admits that question.

**Panel path — prose-dependent rules.** W-EV-GEN-02, -DET-03, -NULL-04,
-COU-05, -CAP-06, and the prose half of -DIV-07 and -COR-09. Each fires on
whether a property is *stated in the card*, so a judge reading the card is the
correct arbiter and criteria 1–3 apply as written.

**Deterministic path — rules whose firing is invariant to card content.**
W-EV-SUB-08 is the case, and the reason is categorical rather than a matter of
timing. It fires on the *subject's* identity, not on anything the card says.
Verified: it fires on every `ValidationResult` at the same rate regardless of
source — 1 firing on 1 prose-extracted node, 10 on 10 furnished nodes. A judge
shown the card cannot disagree with it, because the rule makes no claim about
the card. Its precision against a card-derived gold label is not "undefined
until Phase 6"; it is undefined in principle, since the label and the rule are
about different objects.

Rules on this path settle on **A16.5's grounding audit plus the fail-once
fixture discipline** (positive, negative and boundary fixtures, each
demonstrated failing on purpose), which is how W-AL-01's invariance is
established and how every core rule in this repo is already assured. They do
not enter the panel cohort, and the study says so rather than reporting a
precision figure that would look like a measurement.

### W-EV-DIV-07 is expected-sparse, and validates in two modes (ruled 2026-08-11)

DIV-07 needs both a reported score and a furnished measurement of the SAME
constituent. Across 49 cards only 8% name any constituent this furnisher
measures, because cards report capability and raidex measures responsible-AI
properties. The Liang corpus will therefore present few genuine opportunities,
and a rule that rarely triggers cannot be settled by a cohort that rarely
triggers it. Declared now rather than discovered mid-study:

**Mode 1 — mechanism (deterministic path, already satisfied).** Matching,
tolerance selection and firing logic validate on constructed fixtures: a matched
pair beyond tolerance fires, a matched pair inside tolerance is silent, an
unmatched name produces no comparison, and a near-name collision must not match.
This covers "does the rule work" and is assured the same way every core rule is.

**Mode 2 — field behaviour (panel path, declared sparse).**

- **The denominator is OPPORTUNITIES, not cards.** An opportunity is a matched
  reported/furnished pair. Reporting firings per card would divide by a number
  the rule cannot act on and understate its rate by roughly the overlap rate.
- **Pre-register the expected opportunity count** from the frame's overlap
  measurement before any judge call, so a small number is a prediction rather
  than an excuse.
- **Finding-validity may be adjudicated on single-digit instances, or deferred.**
  If the corpus yields too few opportunities to adjudicate meaningfully, the
  study says so and defers Mode 2 rather than reporting a rate computed on three
  firings.

**The deep-study cohort is DIV-07's natural venue.** Every model there has full
raidex coverage, so the opportunity count is roughly 40x richer than a corpus
sample at 8% overlap. The frame names it as the second venue rather than
pretending the corpus can settle a rule the corpus rarely triggers. No threshold
adjustment: declared sparsity plus a named venue, and DIV-07 settles on Mode 1
plus whichever Mode 2 venue produces adjudicable n.

**The register-empty precondition (A16.2) applies per path.** So
`subjectVersionGuarantee` sitting in `PENDING_EMISSION` blocks SUB-08 from
settling on the deterministic path, but does not block the panel cohort or the
pre-registration freeze. Pre-registration is therefore independent of Phase 6
scheduling, which was the only calendar dependency between the two.

**Open scope question for A16.4, surfaced by the same check.** SUB-08 firing on
a *prose-extracted* node is not obviously correct. A score reported in an
open-weight model's card describes an artifact that IS configuration-controlled
— repo plus revision — in a way an API endpoint is not. The rule currently makes
no such distinction and fires on both. That is a finding-validity question, not
a firing-correctness one, so it belongs to adjudication rather than to the
panel's precision measurement; it is recorded here so the study looks for it
instead of discovering it.

## A16.8 Relationship to the broad study and the praxis

- This study IS the FAccT broad study's methods layer with a finding-level
  adjudication component added; the field-statistics run (silver labels at
  corpus scale) proceeds on the validated instrument, and the paper reports
  validation before prevalence. One study, two outputs.
- The praxis chapter's deterministic-path demonstration (W-AL-01 invariance,
  cohort measurement) is unaffected: its firings are correct by construction
  on structured input. Only the Group-B taxonomy's settled status rides on
  this study, and the chapter states the candidate/settled distinction
  plainly.
- Budget and calendar: judge spend sized against the Phase 3 baseline
  (~$420) — expected lower (presence labeling, shorter contexts); the
  author-labeling gold set is the binding personal-time cost. Scheduling
  against the praxis window is the user's call, per the write-first
  decision already recorded.

## A16.9 Sequencing consequence (recorded once)

Phase 5's public surfaces (cards, badges, gallery) move behind catalog
closure. Phase 4's extractor proceeds now — it is the instrument under
validation and must exist to be validated. The deep-study author-run cards
may be generated internally for calibration but are not published until the
rules they render have settled.
