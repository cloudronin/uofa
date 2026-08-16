# Ch3 methods principles — insertion prose

Section B of the manuscript insertion checklist, items 5, 6, 8 and 10. Written
in manuscript register for direct insertion. Items 7 and 9 are section-4 and
preamble material in [the metrics spec](metrics-spec-r6-u8.md) and are not
repeated here.

Every figure below traces to a committed artifact, named in the source line
under each item.

---

## Item 5 — The three-drift ladder (Ch3 §3.10, measurement validity)

*Source: `studies/taxonomy-validation/enrichment/CONSTRUCT-DRIFT.md`; the
SEA-LION amendment.*

An instrument can fail to measure its construct in three distinct ways, and
this study encountered each of them in turn. The first is the familiar one:
an artifact disagrees with the standard it claims to implement. The second is
subtler and is invisible to any check that reads one artifact at a time — two
of the study's own artifacts, each internally coherent, encode different
constructs, so a measurement taken across them compares two things while
appearing to compare one. The third is subtler still, and neither of the first
two checks can reach it: the artifacts agree with each other, and both are
narrower than the construct the research question is about. Agreement between
instruments is evidence of consistency, not of validity, and the only way to
detect the third drift is to adjudicate a concrete instance against the
construct's own grounding rather than against either artifact.

| drift | what disagrees | how it was found | instance |
|---|---|---|---|
| artifact vs. standard | an artifact and the external standard it implements | reading one against the other | SUB-08 |
| artifact vs. artifact | two internal artifacts, each self-consistent | placing the labeling sheet beside the extraction prompt | three of four enriched properties drifted, in the direction that produces the observed failures |
| artifacts vs. construct | both artifacts agree, and both are narrower than the construct | adjudicating an instance against the construct's grounding | SEA-LION |

The middle rung is worth stating at length because of what it cost. Three
unrelated model families read the same twenty cards as silent on property P7,
which is compelling evidence about extractor capability only if the labels and
the prompt define the same property. They did not. The labeling sheet counts an
ablation offered as a control, and an explicit limitation statement doing that
work, as present; the extraction prompt names neither. The extractor was not
asked for the category the labeled positives belong to, so the 100% miss rate
measures the drift and not the model. Any capability claim drawn from that table
was unsupported, including the specific claim that a 70B model cannot read P7.

The check itself was mechanical and cost nothing: put the two definitions side
by side and read them. Its cheapness is the point. A construct-validity failure
of the second kind cannot be found by more measurement, because every additional
measurement inherits the same drift.

The ladder also disciplines what a drift finding licenses. Drift is symmetric
evidence — it establishes that two documents disagree, not which is correct — so
alignment does not automatically mean amending the prompt to match the sheet.
Deciding which reading is better is a separate adjudication, and where the
extractor's narrower reading proves defensible, the finding flows backward into
the taxonomy rather than forward into the prompt.

---

## Item 6 — Disaggregate before you conclude (Ch3, methods narrative)

*Source: `docs/decisions/2026-08-15-disaggregate-before-you-conclude.md`; the
six-corrections list.*

Every incorrect conclusion this project reached during its hardening month was a
plausible reading of a subset that happened to agree with it, and every one was
caught by splitting the population rather than by further analysis of the same
rows. The failure has a consistent shape. A pooled figure, or a figure from the
first few cases examined, supports an explanation; the explanation accounts for
everything visible; and there is no internal signal that anything is missing,
because the rows that would contradict it are either averaged in or were never
opened. Additional analysis of the same data cannot recover them. Only
partitioning can.

Three instances show the range. A collapse in `acceptance_criteria` scores had a
clean explanation ready — the NASA prompt asks for criteria "stated or implied",
and a licence to infer produces generic answers — until the population was split
by pack, at which point both packs proved to have collapsed by nearly the same
amount and only one of them contains the clause. A prompt edit would have shipped
against a cause that was not present. A proposed segmenter fix corrected a false
acceptance on a Class III device, the worst error class the tool can produce,
which is a compelling case standing alone; across all four regression fixtures it
corrected one and broke another, for no net change. And a diagnosis of prompt
placement was tested by partitioning on prompt layout, where both arms returned
all nineteen factors — the hypothesis was wrong, and being wrong located the
actual defect, because a prompt that works whenever it is delivered is a prompt
that is not being delivered.

The corollary is procedural rather than analytical. Before concluding, ask which
partition of this population would separate the proposed explanation from its
alternatives, and compute it. It is usually cheap: six of the seven instances
recorded cost nothing beyond a grouped aggregation or a search, and one cost two
minutes of reading which of six tests had actually failed. The transferable claim
is that the defence against a plausible wrong conclusion is not more analysis but
a split, and it is the same argument the praxis makes about model credibility,
turned on the project's own inference. A figure that has not been disaggregated
is an assertion about a population made from a sample that was never separated
from its alternatives.

The seventh instance is the principle applied to verification rather than to
measurement, and it is the one worth carrying furthest. An audit concluded that
a required source did not exist in this repository; the source was in its
history. The audit had searched for the fingerprints of the two instances it
already held, and never for the terms of the one it was looking for, so it
reported absence from a slice that could not have contained the thing.
**Coverage means searching for each claim's own terms, not pattern-matching the
corpus against the examples in hand.** It is the same keyword-for-claim
substitution this study measured in extraction as an elevenfold error — 45% of
model cards mention a sampling temperature and only 4% state one for their
evaluation, so the keyword counted mentions that were never claims — running here
in the opposite direction, producing a false absence rather than a false
presence. Searching by fingerprint overcounts what one holds examples of and
misses what one does not, and it had now moved one level up, into the check that
was supposed to catch it.

This principle is stated with its counter-example attached. One triage in the
set was escalated on a premise taken from a file name rather than from the
failing test, and the concern proved groundless at a cost of roughly an hour
against a two-minute check that would have prevented it. A principle of this kind
is only worth stating if the instances that embarrass it appear in the same
document.

---

## Item 8 — Kill-criteria discipline, demonstrated (Ch3, methodology)

*Source: `studies/evidence-span/POST-MORTEM.md`, `DECLARATION.md`.*

Pre-declared kill criteria are cheap to write and are worth nothing unless
something the investigator wants is allowed to die by them. The `evidence_span`
field is this study's demonstration. It was the implementation plan's own
self-described highest-value change: a single added prompt field asking the
extractor to copy the one unbroken sentence a reviewer would read to check a
factor, which would have separated the evidence from the prose framing it,
supplied the second-opinion classifier with the unit it was trained on, and made
groundedness verbatim-checkable. Its kill conditions were committed before it
ran, with a verbatim-recovery floor of 0.70.

Two declared revisions reached 0.258 and 0.369. The field did not ship. Its
failure mode is precise enough to be worth recording: the model does not
fabricate spans, it copies the document's own words in the document's own order
and silently drops bracketed material and trailing qualifiers, so the span reads
correctly, resembles its source sentence at 0.75 to 0.86 similarity, and cannot
be found by exact search — which is the single property the field was specified
to provide. A reviewer told to search the document for the span comes back empty
roughly two times in three. The second revision addressed exactly this defect and
moved verbatim recovery from 0.258 to 0.369, real movement covering less than
half the distance to the floor.

Two features of the outcome matter more than the outcome. First, the criteria
bound the investigator against the investigator's own prior: the field remained
attractive after it failed, and it stays killed, with the rule that any
re-proposal must state 0.369 and the elision mechanism or it is proposing
something already measured without saying so. Second, the phase that depended on
it shipped anyway, having reached length-invariance on rationales alone, which
demonstrates that the kill was not quietly compensated for elsewhere. A kill
criterion that only ever fires on work nobody wanted is not evidence of
discipline.

---

## Item 10 — Unstable at the bar, and the determinism irony (Ch3 §3.10)

*Source: `studies/model-selection/FINDINGS.md` (final, four arms);
`docs/decisions/2026-08-15-scorecard-repeat-policy.md`.*

Qualification scorecards in this study report a minimum of three runs for every
hosted arm, a per-clause minimum-maximum spread beside every point value, and a
third verdict alongside pass and fail: an arm whose spread straddles a threshold
is **unstable at the bar**, which is not reducible to either of the other two.
Local arms may demonstrate run-to-run identity once and cite determinism in lieu
of repeating, which is the stronger claim. Pins on quantities measured this way
are recorded as bands wide enough to hold the observed runs. The third verdict is
the load-bearing one, because pass and fail both assert that the measurement
decided something; when a spread crosses the threshold, the run decided it rather
than the candidate, and reporting whichever run landed on the convenient side is
not a rounding error but the entire failure mode — and it is invisible in any
single-run table.

The policy exists because this study failed it. A qualification run produced
thirteen blank rationales in one pass and none in the next at an identical
configuration pin, and a separate regeneration of the synthetic baseline, also
pinned, moved claim density from 0.199 to 0.115. Both are instances of
`W-EV-DET-03`, "no determinism or repeat-run policy stated for the evaluation",
a High-severity weakener in the model-credibility pack and one this project fires
at vendors. **The study qualifying extractors briefly failed its own determinism
floor, and the taxonomy caught it because we applied it to ourselves.** The
baseline had been failing it silently for longer.

A spread, however, is only as meaningful as the population beneath it, and the
same scorecard supplies the instance that forces the distinction. Two arms
returned unstable verdicts for entirely different reasons. The frontier arm's
instability is real: across three runs at an identical pin it wrote 96, then 70,
then 58 rationales, a forty per cent swing in how many factors it answers at all.
The incumbent arm's groundedness spread of 0.000 to 1.000 looks more dramatic and
means far less, because its denominators across those three runs were zero, zero
and one checkable claim. Two runs produced nothing to check, and the third
produced a single claim, which grounded. The full-range spread is an artifact of
a ratio computed over an empty-or-singleton denominator, and the honest statement
is not that the incumbent is wildly nondeterministic but that it produces so
little checkable content that its grounding score is meaningless — one checkable
claim across 288 rationales in three passes over six papers.

Both arms are correctly labelled unstable at the bar, and the label conceals
that they have different diseases. **The incumbent's spread is a statement about
the content**: the extractor produces nothing checkable, and an unstable ratio is
simply what that condition looks like when rendered as a number. **The frontier's
is a statement about the model**: it answers a materially different number of
factors from one identical run to the next. The remedies do not overlap — one
requires an extractor that says checkable things, the other an extractor that
behaves the same way twice — so a scorecard reporting only the verdict would send
a reader after the wrong remedy half the time. The tables in this work
accordingly annotate which. This is the denominator rule of §3.10's preamble
appearing for the first time at the spread layer: no rate without its population,
and no spread without the population beneath it either.
