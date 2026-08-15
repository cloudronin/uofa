# Attribution in sentence indices: the null goes from 0.753 to 0.051

Phase 3, 2026-08-14. The rule replacement. Whole corpus, committed harness,
seed 0, extraction tag `routing-fix-v1-llama33-70b`.

## The result

A rationale is correctly attributed when the sentence it is *most about* —
argmax token-F1 over the segmented source — is one of the sentences its
factor's evidence lives in.

| | old (keyword overlap) | new (sentence index) |
|---|---|---|
| **candidate** | **0.6068** (740) | **0.4524** (515) |
| document_order null | 0.0268 | 0.0019 |
| first_sentence null | 0.0064 | 0.0000 |
| shotgun k=5 | 0.2628 | 0.0388 |
| shotgun k=12 | 0.6046 | 0.0466 |
| **shotgun k=20** | **0.7527 — beats the candidate** | **0.0505** |
| candidate ÷ worst null | **0.81 — loses** | **9.0×** |

The sweep is nearly flat in k under the new rule: 0.0388 → 0.0466 → 0.0505 as
the blob grows from 5 sentences to 20. Length buys almost nothing, which is what
length-invariance looks like. Under the old rule the same sweep ran 0.263 →
0.605 → 0.753 and overtook the extractor around k=12 — the candidate's own
median rationale length.

**Honest cost: the headline falls 0.6068 to 0.4524.** That is the price of a
number a verbose null cannot reach.

## The gold sentence sets were noisy, and fixing that was declared first

Adjudicating the 209 rows where the two rules disagree (176 old-right/new-wrong,
33 old-wrong/new-right): **at least 91 of the 176 — 52% — are gold-set errors,
not rule errors.** The localiser picked a sentence that genuinely carries that
factor's evidence and the gold set does not list it. The true share is higher;
the auto-triage was conservative and misclassified at least one case where the
picked sentence and the gold sentence were the same sentence.

Cause: 783 raw gold sentences are markdown headings, table rows or bullets. An
`evidence_keywords` fragment lands in document furniture often enough to matter,
recording a location no reviewer would cite and no extractor should be asked
to hit.

The fix — exclude furniture from gold sentence sets — was **declared before it
was measured**, with its own falsifier:

> If the filter moves the candidate a lot and the nulls not at all, that is
> evidence the filter is removing noise. If it lifts the nulls too, the filter
> is removing difficulty and the raw number stands.

Measured:

| | raw gold | furniture-filtered | moved |
|---|---|---|---|
| candidate | 0.4127 | 0.4524 | **+0.0398** |
| worst null (shotgun k=20) | 0.0702 | 0.0505 | **−0.0197** |
| document_order | 0.0083 | 0.0019 | −0.0064 |
| rows scored | 727 | 515 | −212 |

The candidate rose and **every null fell**. The filter removed reference noise;
it did not remove difficulty. Both numbers are published and the raw one is not
hidden.

**The cost is real and stated: 212 rows drop out**, because every gold sentence
they had was furniture. The filtered figure covers 515 of 727 rows. A reader who
prefers the fuller denominator should use 0.4127; the conclusion — the nulls
collapse either way — does not turn on the choice.

## The localiser's own error rate

Argmax can pick the wrong sentence for a correct rationale, and the plan
required this be published rather than assumed away.

Of 176 old-right/new-wrong rows, at most **85 are localiser errors** — an upper
bound of 85/727 = **11.7%** of scored rows, and the true figure is lower because
some of those 85 are further gold-set errors the conservative triage missed. The
localiser returned nothing on 0 rows.

## Quoting parity

The old rule's docstring warns that a verbatim-only check scored sonnet 0.422
against K6's 0.645 — which says the classifier quotes and the model paraphrases,
not that the classifier attributes better. A replacement that reintroduced that
bias would trade one artefact for another.

| rationale is… | new-rule rate | n |
|---|---|---|
| verbatim in the source | 0.5714 | 49 |
| paraphrased | 0.4399 | 466 |

**A +0.13 quoting advantage remains.** Smaller than the old rule's ~0.22 in the
verbatim-only direction, and not zero. Token-F1 to a sentence does not require
quoting, but a quoted rationale is trivially most-similar to the sentence it was
quoted from, so some advantage is structural rather than removable.

Stated as a residual bias, not claimed as solved. It matters for any comparison
between an extractive method and a generative one, and both figures should
appear whenever such a comparison is made. n=49 on the quoted side is small.

## What flipped

`test_a_longer_rationale_cannot_buy_attribution` shipped in Phase 1 as
`xfail(strict=True)` and now passes. `test_the_old_rule_still_fails_this` keeps
the defect measurable beside it — a repair is only legible next to what it
repaired, and if that test ever starts passing, either the historical rule was
changed or the fixture stopped exercising the defect.

## What this does not establish

- **Not validated on real documents.** Everything here is the synthetic corpus.
  `dev/tools/scripts/real_attribution_reference.py` converts the six
  hand-annotated papers into a scoreable reference, and the real-document
  re-score is the next step. The plan's rule stands: when synthetic and real
  disagree, the real number is the result.
- **The reference is still one annotator's**, bounded by the 0.913 same-sentence
  agreement measured in `studies/attribution-agreement/`.
- **Phase 3's primary figures are rationale-based**, per the ruling on
  `studies/evidence-span/`. `evidence_span` localises 2.7× better (0.711 vs
  0.263) and is excluded by a written consequence, not by evidence.
