# Attribution measured against its nulls, on one reproducible run

Phase 1, 2026-08-14. No rule change — this is the same metric, reported honestly
for the first time.

Run: the committed harness, whole corpus (30 dev + 20 held-out test bundles),
**740 scored rationales**, seed 0, extraction tag `routing-fix-v1-llama33-70b`.
Every figure below comes from that one run. The denominator is stated because
the earlier ad-hoc probes did not state theirs, and disagreed as a result.

## The three numbers, where there was one

| | value | |
|---|---|---|
| attribution, loose (the historical figure) | **0.6068** | 449 / 740 |
| attribution, verbatim | **0.3716** | 275 / 740 |
| attribution over gold (abstention counted wrong) | **0.6068** | 449 / 740, abstained 0 |
| misfiled / unmatched | **132 / 159** | of 291 misses |
| rationale length | median **13** content tokens, p90 **19** | |

Loose and verbatim differ by 0.235. The loose rule is the right one — 98% of
sonnet's rationales are written rather than quoted, and a verbatim-only rule
scored it 0.422 against K6's 0.645, which would have read as "a TF-IDF
classifier attributes better than sonnet". But reporting only the loose number
hides how much of it is paraphrase.

## Correction: the abstention gap was the routing bug

The plan predicted `rate_over_gold` would come in around 0.537 against a
reported 0.638 — abstention inflating the headline by ten points. **It does
not. Abstention is zero and the two rates are identical.**

That prediction was measured before `paths.extract_prompt` was fixed, when six
of nineteen NASA factors were never asked about and so left the denominator
entirely. Those 90 missing rows *were* the abstention. With the prompt routed
correctly every gold-scorable factor gets a row, and the gap closes to nothing.

`rate_over_gold` stays in the record. It is the number that does not reward
declining to answer, and it will diverge again the moment anything abstains —
but it is not currently evidence of anything, and it would be dishonest to
present the machinery as though it were catching something today.

## The null battery

Mean over bundles. A shotgun rationale is *k* random source sentences, the
identical blob filed under every factor, carrying no attribution judgment by
construction. Whatever it scores is what rationale length alone buys.

| null | dev | test | pooled | vs candidate 0.6068 |
|---|---|---|---|---|
| first_sentence | 0.0063 | 0.0065 | 0.0064 | −0.600 |
| document_order | 0.0270 | 0.0264 | 0.0268 | −0.580 |
| shotgun k=1 | 0.0462 | 0.0944 | 0.0655 | −0.541 |
| permutation (labels shuffled) | 0.0905 | 0.0984 | 0.0936 | −0.513 |
| shotgun k=5 | 0.2173 | 0.3312 | 0.2628 | −0.344 |
| shotgun k=12 | 0.5812 | 0.6398 | 0.6046 | **−0.002** |
| shotgun k=20 | 0.7349 | 0.7794 | **0.7527** | **BEATS IT** |

The candidate itself is 0.5861 on dev and 0.6382 on the held-out test split.
**The k=20 shotgun beats it on both splits independently**, so this is not an
artefact of pooling.

**Two things are true and both must be reported.**

There is real signal. The permutation null — this run's own rationales with
their labels shuffled, so it inherits their length and vocabulary exactly — sits
at 0.094. The candidate is roughly 35 standard deviations above chance. The
document-order constant router scores 0.027 against the extractor's 0.607, a
23× separation. Whatever the metric is doing, it is not noise.

And the metric does not isolate that signal. A blob of 20 random sentences,
which cannot possibly be *about* the factor it is filed under because it is the
same blob under every factor, scores 0.753. The crossing is at roughly k=12,
which is where the candidate's own median of 13 content tokens sits. The
extractor is scoring at the length its rationales happen to be.

Reporting only the permutation null would read as "far above chance, therefore
good". Reporting only the sweep would read as "meaningless". Neither alone is
honest.

## One reproducible number, replacing two that disagreed

Two earlier shotgun probes existed and did not agree — 0.740 from one, 0.9284
from another — because they used different denominators: the shotgun never
abstains, so it scored 447 rows against the extractor's 376. Neither was
committed, and neither can go in a committee packet.

**0.7527 at k=20, over 740 scored rationales, from the committed harness, is the
figure.** The direction was never in doubt in any version; the number now has a
denominator and a script behind it.

## What was built

In `groundedness.py`:

- `AttributionResult` — the record, mirroring `GroundednessResult`. Carries
  `scored`, `right`, `right_verbatim`, `gold_scorable`, `abstained`, `misfiled`,
  `unmatched`, `extra_factor_rows`, the raw rationale token lengths, and the
  permutation null.
- `score_attribution_full` — same rule, keeps what the two-integer return threw
  away. `(res.right, res.scored)` is pinned equal to `score_attribution`'s
  return on the live corpus, so nothing re-baselines silently.
- `null_document_order`, `null_first_sentence`, `null_shotgun`,
  `permutation_null`, `null_battery`.
- `assert_attribution_available` — a corpus with no reference now raises instead
  of returning `(0, 0)`, which rendered as an omitted row and was
  indistinguishable from a clean run. This is the vacuous-pass class AGENTS.md
  §13 already names.

`score_extraction_batch.py` reports all of it on every run: three rates, the
null table with a `BEATS IT` marker, the candidate's own median length placed on
the sweep, and the misfiled/unmatched split.

Nine tests in `test_groundedness.py`, which had sixteen tests and none for
attribution — in a module whose docstring says every rule "is pinned in
test_groundedness.py with that provenance".

## The test that should have existed

`test_a_longer_rationale_cannot_buy_attribution`, committed **`xfail(strict=True)`**.

A 20-sentence blob scores 0.700 against the extractor's 0.600 on the test
fixture, mirroring the corpus. Phase 3 flips it, and `strict=True` means an
unannounced pass is reported as a failure — so the change that fixes this is
visible in one diff. AGENTS.md §13's "make every new check fail once", applied
prospectively.

The first version of this test failed for the wrong reason: on an eight-sentence
fixture a k=12 blob *is* the whole document, so it matched everything
tautologically and would have passed under a length-invariant rule too. The
fixture is now thirty sentences with a deliberately imperfect candidate scoring
0.600, so the failure is the real defect and not an artefact of the fixture.

## What this does not do

No rule changed. The 0.5 overlap threshold, the `len >= 4` keyword filter and
the paraphrase allowance are all exactly as they were. Phase 3 replaces the rule;
this makes the case that it has to.
