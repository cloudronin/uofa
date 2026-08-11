# Enrichment search protocol

**Status: SIGNED 2026-08-11.** In force. Cards may be pulled under it.

**Signed:** 2026-08-11, by the study author, conditional on the two additions
below (keyword-bias control, §5a and §7; head-card ground pinned, §4).

---

## 1. Why this exists

The gold set returned **zero positive instances** for P2 (uncertainty), P5 (null
baseline), P6 (claimed COU) and P7 (confound control) across 150 cards. Every
gold row is therefore a "the rule should fire" case, which makes **sensitivity
measurable and specificity unmeasurable**.

Specificity is the direction that matters most here. With no positive cards:

- a hallucinated *clear* (extraction inventing a property that is absent, thereby
  silencing a warranted weakener) **is** detectable — the gold set catches it;
- a false *fire* (a rule firing on a card that genuinely states the property) has
  **no test case at all**.

The second is a false accusation, on a published card, about a named vendor. It
is the most reputation-damaging error the system can make and the exact "firing
for the right reasons" concern A16 was written for. Four rules cannot settle with
it untested.

This protocol buys that one measurement and nothing else.

## 2. What it is not

- **Not a prevalence sample.** The enriched stratum is drawn deliberately for
  positives and is **excluded from every prevalence figure** the study reports.
  Mixing it into a rate would inflate the rate by construction.
- **Not an extension of the gold set.** It is a separate stratum with its own
  file, `enriched_labels.csv`, and its own column `stratum=enriched`.
- **Not a search for cards that make the tool look good.** The target is cards
  that state a property, whatever the rules then do with them. A card found this
  way that causes a rule to misfire is the finding, not a discard.

## 3. Target

**15–30 positive cards per property**, for P2, P5, P6, P7 only. P1 is already
validated (73/150); P3 and P4 have 3 positives each and are included if the
search surfaces them incidentally, not searched for separately.

Ceiling of 30 per property is deliberate: enough to estimate specificity with an
interval worth reporting, small enough to be one short labeling session.

## 4. Where to search, declared in advance

Recorded before searching so the frame is not chosen after seeing results.

| Ground | Rationale |
|---|---|
| Deep-study head models, **drawn as their modelbiome rows** | Frontier technical cards (Qwen, Gemma, Llama grade) carry the most detailed eval reporting. Pinned rows, not live HF — this is not an exception to the rule below |
| `lmqg`-style repos | Publish raw eval artifacts alongside cards, so uncertainty is more likely stated |
| Cards citing an arXiv paper | Paper-backed evals more often carry CIs and baselines |
| `model-index` bearing cards | Structured results (4% of cards per the A3 study) skew toward richer reporting |

**Search is over the pinned corpora only** — Liang and, once the amendment is in
force, the modelbiome field arm. Not live HF: the study's population is the
snapshot, and a card pulled live cannot be pinned the same way.

## 5. Method

1. Keyword pre-filter over the pinned corpus for each property's characteristic
   language (`±`, `std`, `95% CI`, `chance level`, `random baseline`, `intended
   to demonstrate`, `controlling for`), **scoped to evaluation sections** per the
   binding §1 rule.
2. Author labels each candidate under the **unchanged** A16.3 instructions. A
   candidate that turns out not to state the property is labeled `absent` and
   **kept** — it is a legitimate negative and discarding it would bias the
   stratum toward positives.
3. Record `search_ground` and `matched_pattern` per row, so the selection path is
   inspectable.
4. Stop at 30 per property or when the ground is exhausted, whichever first.

### 5a. The unfiltered micro-ground (the control for the step-1 filter's bias)

Draw **20–30 cards at random, with NO keyword filter**, from the richest ground
(`lmqg`-style or arXiv-citing), and label them identically.

This exists because the keyword pre-filter selects positives *by their
characteristic language*, and those are the phrasings extraction finds easiest.
Specificity measured only on keyword-found cards is therefore an **upper bound** —
the real false-fire risk lives in cards stating a property in unusual language
that the filter, and quite possibly the extractor, misses.

Both outcomes are informative and neither is a failure:

- **Positives the keyword pass missed** are the hardest and most valuable test
  cases in the stratum. They are the only direct evidence about the unusual-
  phrasing case.
- **Zero yield** is evidence the filter's coverage is adequate, which converts
  the upper bound into something closer to an estimate.

Report the micro-ground's yield separately from the filtered stratum.

## 6. The honest exit

If the declared search **cannot find even a handful of positive cards** for P6 or
P7, that is not a failed search — **the documented search is the evidence.**

Those rules then settle with an explicit caveat, recorded in A16.7:

> Positive class near-empty in the wild; clear-direction validated on synthetic
> fixtures, false-fire direction unvalidated for want of instances, with the
> search protocol and its yield reported.

A rule settling on that basis states its own limit, which is a stronger position
than a specificity figure computed on two cards.

## 7. What gets reported

- The enriched stratum's specificity estimate per property, with interval.
- The search yield per ground: candidates screened, positives found. A low yield
  is a finding about publishing practice and belongs in the paper.
- **The keyword-selection limitation, stated wherever specificity is reported.**
  The filtered stratum finds positives by characteristic language, so its
  specificity is an **upper bound**: cards phrasing a property unusually are
  under-represented, and they are precisely where a false fire is most likely.
  Report the §5a micro-ground's yield alongside it, since that is the only
  measurement bearing on the gap.
- Prevalence figures **from the gold set only**, stated as such wherever they
  appear beside enriched-stratum numbers.
