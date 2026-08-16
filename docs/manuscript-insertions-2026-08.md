# Manuscript insertions, August 2026 — worked list

Working the insertion checklist (`Praxis_Manuscript_Insertion_Checklist_v0_1.md`).
Every insertion lives in exactly one file so there is nothing to keep in sync;
this page is the index and holds only the section C sentences that have no other
home.

**Boundary, restated because it governs what is absent here.** The
model-selection scorecard, the misfile signal, the anchor autopsies, the
enrichment mechanics and the keyless-route gate are FAccT-paper material. The
four-arm scorecard table does **not** enter the manuscript. The praxis takes
item 11's sentence, and item 10's methods principle, and nothing else from that
study.

## Status

| # | insertion | target | lives in | status |
|---|---|---|---|---|
| 1 | narrowed H2 conclusion | Ch4 §4.3.1 | [`ch4-h2-section.md`](ch4-h2-section.md) | written, needs voice pass |
| 2 | H2 amendment, both-numbers rule | Ch3 + R4 appendix | [`2026-08-14-h2-gate-amendment.md`](decisions/2026-08-14-h2-gate-amendment.md), [thresholds](decisions/2026-08-14-h2-replacement-thresholds.md) | written, both-numbers audit pending (D3) |
| 3 | routing bug as disclosed fix | Ch4 results narrative | [`ch4-h2-section.md`](ch4-h2-section.md) § "The routing defect" | **written this pass** |
| 4 | second-annotator ask as scoped future work | Ch5 + §3.10.5 | [`ch4-h2-section.md`](ch4-h2-section.md) § "The limit on inference" | written; port to Ch5 |
| 5 | the three-drift ladder | Ch3 §3.10 | [`ch3-methods-principles.md`](ch3-methods-principles.md) | **written this pass** |
| 6 | disaggregate before you conclude | Ch3 methods narrative | [`ch3-methods-principles.md`](ch3-methods-principles.md) | **written this pass** |
| 7 | condition 3 as leakage detector | Ch3 metrics spec | [`metrics-spec-r6-u8.md`](metrics-spec-r6-u8.md) §4 | written |
| 8 | kill-criteria discipline (`evidence_span`) | Ch3 methodology | [`ch3-methods-principles.md`](ch3-methods-principles.md) | **written this pass** |
| 9 | denominator rule as governing statement | Ch3 metrics spec preamble | [`metrics-spec-r6-u8.md`](metrics-spec-r6-u8.md) preamble | written, all three instances |
| 10 | unstable at the bar + determinism irony + spread denominators | Ch3 §3.10 | [`ch3-methods-principles.md`](ch3-methods-principles.md) | **written this pass** |
| 11 | limitations sentence | §1.8 + Ch5 | below | **written this pass** |
| 11a | synthetic-vs-real proof case | Ch3 metrics spec preamble | [`metrics-spec-r6-u8.md`](metrics-spec-r6-u8.md) preamble | **written this pass** |
| 12 | U6 division-of-labor sentence | §3.4.x | below | **sentence supplied; manuscript-side verification outstanding** |
| 13 | corpus-vintage caveat | §3.4.x | below | **written this pass** |
| 14 | PDF-reader lesson, fail-loud rule | Ch3 reproducibility | below | **written this pass** |
| 14a | instrument recovery-rate discipline | Ch3 metrics spec | [`metrics-spec-r6-u8.md`](metrics-spec-r6-u8.md) preamble, rule 2 | **written this pass; unblocked by scorecard FINDINGS** |

**Item 9, resolved: the source was here all along.** The checklist names three
instances for the denominator rule. The third, firewall arithmetic, was flagged
as unciteable because "no committed artifact in this repository states its
figures." **That was false.** The artifact is commit `08cbfc78` in this
repository's own history, merged under PR #45 with the profile-dispatch tests
and firewall fixtures: the compound escalation that went ninefold to
twenty-fourfold on evaluation-layer firings while rendering under documentation,
repaired by splitting the readout into two firewalled sections.

The way the flag was wrong is worth more than the instance. The check behind it
grepped two directories of the working tree for the decimal strings belonging to
the *other two* instances. It never searched for this instance's own terms and it
never searched history at all, so it reported absence from a slice that could not
have contained the thing. **A negative result is only as wide as the search that
produced it**, and a search narrower than the claim it supports manufactures
clean absences — the denominator rule one level up: no rate, and no *zero*,
without the population it was computed over.

The default was still right and stays the default. Refusing to quote a rate whose
measurement context cannot be produced is the rule applying to itself. What
changes is that such a refusal **states the scope it searched**, so a reader can
tell whether "not found" means "not there."

---

## Section C — sentences with no other home

### Item 11 — limitations (§1.8, repeated in Ch5)

> No extractor evaluated here clears the qualification conjunction for
> judgment-bearing prose properties. Four model classes were measured across
> three model families and two orders of magnitude of capacity, and checkable
> claim density was the failing clause in every one of them, with the nearest
> candidate short of the threshold by a factor of 1.6. The pack's prose path
> therefore ships gated on panel confirmation rather than on automated
> extraction, and model selection reopens only on a declared condition: a
> candidate that clears the conjunction on the real corpus under the study's
> repeat policy.

The re-entry clause is not decoration. Without it, "no candidate cleared"
licenses an open search until one does, which is the same shape as trying
metrics until one passes.

### Item 12 — division of labor (§3.4.x)

Verification item against the manuscript, which is held outside this repository.
**Confirm the sentence still reads "deterministic path only."** If it does, the
justification available to it has changed and should be attached:

> …the deterministic path only, with judgment-bearing prose properties excluded
> pending extractor qualification.

The clause was previously a design assertion. It is now a measured one, and the
qualification table is what it rests on.

### Item 13 — corpus vintage (§3.4.x, where the external corpora are introduced)

> A 2023 snapshot cannot validate machinery aimed at publishing conventions that
> postdate it: of 11,540 eval-bearing cards in the reference corpus carrying a
> markdown table, **none** uses the header shape the route under test targets,
> because that shape is an output convention introduced after the snapshot was
> collected. The corpus validates instruments against 2023 practice, and card
> formats have moved.

### Item 14 — the reader defect, folded into reproducibility (Ch3)

> Input-format assumptions are provenance assumptions. A scoring path in this
> study read PDF-borne documents with a plain-text call that returns object
> syntax rather than prose, so for one class of document every figure was
> checked against typesetting geometry instead of against the paper. The read
> did not fail; it degraded silently and returned something shaped like text,
> which is why it survived review and was found only when a triage printed the
> source a claim had matched. **A reader that cannot handle a format must fail
> loudly rather than return a degraded result**, and every quantitative figure
> in this work is reported with the reader that produced it named.

The direction of the resulting bias was asserted before it was measured and was
asserted wrongly — the degraded read was assumed to inflate scores and in fact
suppressed them, losing 15 of 39 genuine figures on the document tested. The
correction is dated and carries the commit hash in the scorecard findings. It is
the same lesson at one remove: **an unmeasured direction stated with confidence
is the defect the instrument was built to catch.**

---

## D — verification pass

Two of the five run against repo-side artifacts and were performed on 2026-08-16.
The other three run against the manuscript, which is held outside this
repository, and remain open.

**D2 — numbers diffed against source. Done.** Items 3 and 10 checked
figure-by-figure against `studies/nasa-prompt-routing/FINDINGS.md` and
`studies/model-selection/FINDINGS.md` respectively. Items 5, 6 and 8 checked
against `CONSTRUCT-DRIFT.md`, the disaggregation decision doc, and the
`evidence-span` post-mortem.

**D3 — both-numbers audit. Done, and it found three violations.** Every
repository file citing a pre- or post-correction H2 detection figure was checked
for co-presence of the other:

| file | was | now |
|---|---|---|
| `metrics-spec-r6-u8.md` §1 | post-correction only | pre-correction column added, with the V&V 40 control |
| `2026-08-15-h2-narrowed-conclusion.md` | post-correction only | both, inline |
| `real-document-rescore/FINDINGS.md` | post-correction only | both, inline |
| `prompt-absence/FINDINGS.md` | pre-correction only | dated banner naming the defect and the post-correction figures |

Two files cite a single figure legitimately and were left alone: the thresholds
decision doc discusses the reporting rule rather than citing a result, and the
claim-density study uses `mean_overall_f1` as an unchanged control column in a
different comparison. `credibility-inspector.md` already carried its own
correction note and passes.

**Open, and assigned to the writing session rather than to this repository.**
D1, the U5 register check — no such script exists here, and it travels to the
manuscript repository as part of that session's setup. D4, the read-aloud pass
on every new paragraph. D5, grammar polish last, briefed to leave synthesis
alone. Item 4's port to Ch5 and item 12's sentence into §3.4.x land in the same
session.

Nothing on this list now waits on a measurement.
