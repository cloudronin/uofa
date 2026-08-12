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

> **AMENDED 2026-08-11 — there is no gold set.** Both label sets are
> machine-drafted and commit as such permanently; the confirmed-gold path is
> dropped. This section is demoted to secondary evidence and its "gold" framing
> is withdrawn. See *Label status* below, and A16.7's *Re-anchoring on finding
> validity*. Original text unedited so the change is visible as a change.

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

### Label status (amended 2026-08-11)

**Both label sets are machine-drafted, and that is now their permanent,
committed status.**

| File | Rows | Status |
|---|---:|---|
| `studies/taxonomy-validation/gold/gold_labels.csv` | 150 | machine-drafted |
| `studies/taxonomy-validation/enrichment/enriched_labels.csv` | 147 | machine-drafted |

The directory name `gold/` is kept for path stability; it no longer denotes
gold-standard labels and the column marker is authoritative over the path.

**The confirmed-gold path is dropped, not deferred.** Earlier drafts marked
every row `NOT-GOLD-until-human-confirmed`, which promised a confirmation step
and made the label status read as pending. It is not pending — it is settled at
machine-drafted. The marker now says so, and the test that asserted the pending
state is removed in the same change, because a guard against promotion to a
state that no longer exists guards nothing while looking like diligence.

**Consequence for this section.** Precision and recall against these labels are
**secondary** evidence, reported with their basis named. They measure agreement
between two machine readings of the same text — informative about extraction
consistency, not authoritative about what the card says. A16.4's
finding-validity rate, adjudicated by the author on fired findings, is the
settle authority.

## A16.4 Finding adjudication (firing for the right reasons)

Phase 3 Stage 5 pattern: for a stratified sample of actual firings, judges
see the card and the rendered finding text and adjudicate whether the stated
deficiency is (a) present, (b) correctly attributed to the claimant, and
(c) correctly severity-framed. Disagreements adjudicated, not averaged.
Output: per-rule finding-validity rate, the number that decides whether a
rule's *wording* survives even where its firing logic does.

### Extractor qualification (declared 2026-08-11, BEFORE any frontier run)

A16.4 adjudicates findings. A finding caused by extraction failing to read a
property the card states is not a finding about the card, and a panel spending
its effort on those is measuring the extractor while appearing to measure the
rules. So an extractor must **qualify** before its findings reach the panel.

**The bar, declared before the numbers exist:**

| | Threshold | Applied |
|---|---|---|
| **False-fire rate** — extraction misses a property the card states | **≤ 10%** | per property |
| **False-clear rate** — extraction invents a property the card omits | **≤ 5%** | per property |

**Every property must clear both. No averaging across properties.** A mean would
let a strong P2 carry a failing P6, and a rule settles per rule — a property that
extraction cannot read is a rule that cannot be validated, whatever the other
three do.

The asymmetry is deliberate and matches the consequences. A false clear silences
a warranted weakener: the card looks better than its record supports, and the
error is invisible. A false fire is a public accusation of an omission the
publisher did not commit. The false-clear bar is tighter because that error
cannot be discovered by a reader; the false-fire bar is looser only because
10% is already generous against the alternative of shipping nothing, and it is
not a target.

**Why this is written now.** The baseline extractor's numbers already exist
(`ollama/qwen3.5:4b`: false-fire 46–82%, false-clear 0–11%). The frontier
comparison has not run. A bar set after those numbers land would be a bar chosen
to fit the result — the exact post-hoc move the whole A16 apparatus exists to
prevent, committed at the apparatus's own gate.

Recorded consequence: **the baseline fails this bar on all four properties**, on
false-fire, by a wide margin. That is a conclusion the bar produces, not a
premise it was built from.

**Reasoning models are excluded from this table (operational scope, ruled
2026-08-11).** A model that spends a 16k-token budget before emitting visible
content, at multi-hour wall-clock over 116 short cases, is not a shippable
corpus-scale extraction backend at current economics. `Qwen/Qwen3.5-9B` on
Together returns `content: ''` with all output in a separate `reasoning` field
and `finish_reason: length`; the row is withdrawn rather than run. If the
economics change it enters with its own row, an honest token budget, and a
reasoning-field-aware parser -- not by quietly raising the cap on the shared
config.

**Any parameter that can silently truncate output is part of the configuration
pin**, alongside temperature and seed. `max_tokens` was a hidden constant until
it truncated a reasoning model into producing nothing; a truncation is a
different measurement wearing the same hash.

**Property definitions are rendered, not restated (2026-08-11).** The bar above
is only meaningful if the extractor is asked for what the labeler counts. Both
the labeling sheet and the extraction prompt now render from
`packs/mrm-nist/properties/P*.json`, and
`tests/test_property_definitions_are_one_source.py` asserts byte-identity, so
the construct drift that invalidated the first frontier comparison cannot recur
through discipline failure.

**Qualification record.** Results live in
`studies/taxonomy-validation/enrichment/specificity/QUALIFICATION.md` as an
extractor-sensitivity table — one row per configuration, each pinning model,
prompt version and temperature, with the baseline row retained. A16.4 references
that table to state which extractor produced the findings it adjudicated. An
unqualified extractor's findings may still be generated and inspected; they may
not be the basis of a settle decision.

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

> **AMENDED 2026-08-11 — A16 re-anchors on finding validity.** Criterion 1 below
> is demoted to secondary and its "adjudicated labels" basis is withdrawn. See
> *Re-anchoring on finding validity* at the end of this section. The original
> text stands unedited so the change is visible as a change.

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

### Re-anchoring on finding validity (amended 2026-08-11)

**Ruling.** A16's settle criteria run **primarily on A16.4 finding-validity
rates, measured on fired findings.** Criterion 1's label-based precision/recall
is demoted to secondary and its "adjudicated labels" basis is withdrawn.

A16.4 runs **Phase-3-style**: the **panel adjudicates all fired findings**, and
the author tie-breaks **only** on judge-split cases that pass a pre-declared
stakes filter. Routing criteria are declared below, before any adjudication
runs.

**Why.** There are no adjudicated labels and there will not be. Both label sets
-- `gold/gold_labels.csv` (150 rows) and `enrichment/enriched_labels.csv` (147)
-- are **machine-drafted**, and as of this amendment they commit as such
permanently: the confirmed-gold path is dropped rather than left standing as an
unmet promise. A criterion resting on "adjudicated labels" would rest on drafts
while reading as though it rested on adjudication -- the precise failure this
study exists to catch, committed by the study's own settle rule.

**What replaces it.** Adjudication of the findings the system actually emits:
card plus rendered finding text, judged for whether the stated deficiency is
present, correctly attributed, and correctly severity-framed (A16.4's existing
form, unchanged). This is a better instrument, not merely an available one:

- It adjudicates the **output**, not a proxy for it. A label cell that never
  produces a finding consumes adjudication effort and decides nothing.
- It is **auditable end to end** -- a reader sees the card, the finding, and the
  verdict, with no intermediate labeling step to take on trust.
- It **cannot be satisfied trivially.** A rule that fires unconditionally scores
  1.00 against a zero-prevalence label set; it scores badly on finding validity
  the moment a reader looks at what it said about a specific card.

**What the labels are still for.** They are not withdrawn. They remain the
committed case set (`tests/fixtures/specificity/cases.json`) that bounds the
search, supplies extraction inputs, and records the false-positive keepers. They
are simply not the settle authority.

**What this changes elsewhere, stated rather than left to be discovered.**

1. **The 0/150 prevalence headline is a machine-drafted result.** Item 1 of the
   zero-prevalence path above says the gold set confirmed the two-source
   convergence "at gold quality on a third population". That phrase is no longer
   accurate and is withdrawn. The figure stands as a machine-drafted measurement
   converging with two independently measured populations
   (`studies/cohort-2026-08` n=427; `studies/card-eval-reporting-2026-08` n=49),
   which is a weaker claim than the original and is the true one.
2. **Phase 5's extractor slice moves onto the critical path.** No findings exist
   to adjudicate until the extractor runs against real cards, so the narrow
   backend-gated slice is what now unblocks settling. Scope is unchanged: internal
   instrumentation only, with the public card and badge surfaces still gated
   behind catalog closure per A16.9.
3. **The enriched stratum's specificity estimate becomes secondary
   instrumentation.** It measures extraction behaviour against machine-drafted
   expectations, is reported as such, and is pinned to the extractor
   configuration that produced it. It does not settle a rule.

**Open and late-binding.** `rulings_4.csv` remains open. It binds late and
nothing here waits on it.

### A16.4 adjudication routing (declared 2026-08-11, before any adjudication)

Written before the first finding is adjudicated, for the same reason the sample
frame was written before the first judge call: a stakes filter chosen after
seeing which findings split is not a filter, it is a preference.

**Step 1 — the panel adjudicates every fired finding.** No sampling at this
stage. Panel constitution and calibration bars are A16.3's, unchanged: three
judges, per-judge agreement ≥80% on the calibration set, pairwise κ ≥ 0.70,
failing judges replaced rather than averaged.

**Step 2 — the author tie-breaks only on judge-split cases passing the stakes
filter.** A *split* is any finding on which the panel does not reach unanimity
on all three A16.4 dimensions (present / correctly attributed / correctly
severity-framed). A split is routed to the author iff it meets **at least one**:

| Criterion | Operationalized as |
|---|---|
| **Download-head** | subject model in the **top decile by downloads** within the fired-findings set, the decile computed on that set and recorded with the draw |
| **High-confidence split** | judges disagree while **≥2 report confidence at or above their own calibration-set median** — a confident disagreement, not an uncertain one |
| **Critical severity** | the finding carries `uofa:severity` = `Critical` |
| **Safety domain** | the finding attaches to a safety-relevant evaluation dimension: `safety`, `security`, `privacy`, `machine_ethics`, or a `strongreject` / `wmdp` / `xstest` constituent |

**Why a filter at all.** Author time is the scarce input. Routing every
disagreement to the author would make the panel decorative and the author the
de facto labeler, which is the arrangement this amendment just moved away from.
The filter spends author attention where a wrong finding costs most: a visible
model, a confident disagreement, a severe claim, or a safety claim.

**Step 3 — unresolved splits are recorded as `contested`.** Splits that do not
meet the filter, and filtered splits the author does not resolve, are neither
dropped nor averaged into a rate. `contested` is a reported outcome with its own
count.

This matters for what a rate means. A rule may reach a passing finding-validity
rate on its resolved findings while carrying many contested ones — that is a
rule whose *wording* is unclear enough that trained judges disagree, which is
exactly what A16.4 exists to detect. **Contested counts are reported alongside
every finding-validity rate**, and a rule may not settle on a rate computed over
a minority of its findings.

**The numeric thresholds above bind now.** The one judgment call is the
download-head decile; it is declared at the top decile rather than tuned, and if
it moves, it moves by amendment with the reason recorded, not silently.

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
