# Enrichment search: what the two pinned corpora yielded

**Run 2026-08-11** under `ENRICHMENT-PROTOCOL.md` (signed 2026-08-11), field-arm
venue per `AMENDMENT-01-div07-venue.md` (signed 2026-08-11).

Reproduce with `search.py --corpus <path>`; both corpora go through the same
detector, patterns, exclusions and seed, and the script refuses any corpus whose
hash is not the pinned one. Per-run numbers are in `liang/manifest.json` and
`modelbiome/manifest.json`, each stamped with the script hash that produced it.

---

## 1. The headline: the field arm supplies the stratum, Liang cannot

Distinct candidates after dedup and structural exclusion, against the protocol's
target of **15–30 per property**:

| Property | Liang (2023-10) | modelbiome (2025-07) | Target met |
|---|---|---|---|
| P2 uncertainty | 55 | **1,891** | both |
| P5 null baseline | **1** | **40** | field arm only |
| P6 claimed COU | **1** | **200** | field arm only |
| P7 confound control | **4** | **29** | field arm only |

Liang reaches target for P2 alone. For P5, P6 and P7 it offers **six distinct
cards between them** across 32,111 rows, which is §6's honest-exit condition
arriving on measurement rather than speculation.

The field arm clears all four. **The honest exit is not needed** — the four rules
can settle on a measured specificity estimate instead of a documented absence.

### The full stream was necessary, and a sample would have produced a false exit

Recorded because the decision was live and the recommendation was wrong. Offered
a 200k-row sample (proven method, ~1/9 the cost) or the full 1.86M-row stream,
the study author chose the full stream. Candidate accumulation was not uniform —
at 200,000 rows the pass held 228 distinct candidates against 2,087 at the end,
so a sample would have yielded roughly:

| Property | Full stream | ~200k sample would give | Verdict on a sample |
|---|---|---|---|
| P2 | 1,891 | ~210 | target met |
| P5 | 40 | ~4 | **false honest exit** |
| P6 | 200 | ~22 | target met |
| P7 | 29 | ~3 | **false honest exit** |

A sample would have reported P5 and P7 as near-empty in the wild and settled them
under §6's caveat. They are not near-empty; the sample would have been too small
to see them. The cheaper method would have produced a defensible-looking wrong
answer, which is the failure mode this whole study exists to catch.

## 2. §7's per-ground yield, including a falsified prediction

§4 declared four grounds in advance. One of its predictions did not survive.

**`lmqg`-style repos: 181 models, 117 eval-bearing, ZERO candidates on any of the
four properties.**

§4's rationale was that these repos "publish raw eval artifacts alongside cards,
so uncertainty is more likely stated." They do publish the artifacts. They state
none of the four interpretive properties — not one card in 117.

This is a finding, not a failed ground. It sharpens the study's headline claim:
it is not merely that most publishers omit uncertainty, but that a repo family
whose whole practice is publishing eval artifacts still omits it. The gap is not
about effort or sophistication.

Field arm, cards screened against candidates surfaced:

| Ground | Screened | P2 | P5 | P6 | P7 |
|---|---:|---:|---:|---:|---:|
| arxiv-citing | 310,269 | 730 | 57 | 122 | 209 |
| model-index | 212,379 | 590 | 7 | 50 | 10 |
| other | 45,330 | 2,252 | 12 | 101 | 40 |
| head-card | 2,026 | 126 | **0** | 60 | 24 |
| lmqg-style | 117 | **0** | **0** | **0** | **0** |

Two further readings, both against §4's expectations:

- **`arxiv-citing` was the right call and carries P7 almost alone** — 209 of 283
  confound-control candidates. Paper-backed evaluation is where controlled
  comparison gets stated, as predicted.
- **`head-card` yields no null baseline at all.** 2,026 frontier-family cards
  screened, 126 uncertainty candidates, zero stating a chance level. The ground
  §4 expected to be richest is the one place P5 is entirely absent.

Counts live in each `manifest.json` under `ground_screened` /
`ground_candidates`. A card counts once per ground it belongs to, so the columns
do not sum to the totals in §1 — which are deduplicated across grounds.

## 3. What the structural exclusions removed, and the bug they hid

Both exclusions are mechanical and neither inspects whether a card states the
property (§5.2 forbids discarding a card for looking unpromising — a candidate
that labels `absent` is kept).

| Corpus | Property | v1 hits | Excluded | Reason |
|---|---|---|---|---|
| Liang | P6 | 32 | 31 | `template-heading` |
| Liang | P7 | 16 | 11 | `wordlist` |
| modelbiome | P6 | 2,155 | 1,884 | `template-heading` |
| modelbiome | P7 | 289 | 28 | `wordlist` |

P6's exclusions are the HuggingFace card template's `## Intended uses &
limitations` — 87% of all P6 keyword hits in the field arm. P7's are
SentencePiece token inventories containing the literal token `▁CONFOUND`.

**The first version of the heading rule was wrong, and the fail-once check caught
it.** Written as plain "the match is a markdown heading", it also removed
`#### Ablation Studies 1: End-to-end v.s. Step-by-step:` — the single strongest
P7 signal in Liang. An authored heading is evidence; the template's furniture is
not, and "is it a heading" does not distinguish them. The rule now asks what the
author wrote *beyond* the matched label: 1 residual word for the template, 9 for
the ablation heading. See `_is_furniture`.

This is the same failure this build keeps producing — matching the word instead
of the claim — and it was caught only because the rule was validated against a
ground whose answer had already been established by hand.

## 4. A scope statement: the stratum's population is smaller than the frame's

`frame.json` pre-registers **21,181** eval-bearing cards in Liang, using
`card_eval.detect().found`. This search reports **16,678**, using non-empty
`card_eval.eval_sections()`. That is not a contradiction:

| | Liang |
|---|---|
| `detect().found` | 21,181 |
| `eval_sections()` non-empty | 16,678 |
| sections but not detected | **0** |
| detected but no extractable section | **4,503** |

`eval_sections()` is a strict subset. 4,503 cards report an evaluation in a form
that yields no scoped section — detected through `model-index` frontmatter or an
inline table under no heading the detector claims.

The enrichment stratum can only draw from cards with scoped text, because §1's
section scoping is binding: a `present` label may only be supported by scoped
content. So the stratum's population **is** the 16,678, and the same distinction
applies to the field arm's 562,298.

Worth its own line because 21% of eval-bearing cards reporting an evaluation the
scoper cannot reach is a fact about the extractor's coverage, and it belongs in
the record before anyone reads the two numbers as disagreeing.

## 5. What the sheet is, and what it is not

`enriched_set.csv` — regenerate with `make_sheet.py`; not committed, per
`.gitignore`.

- Column-identical to `gold/gold_set.csv` plus `stratum`, `search_ground` and
  `matched_pattern` (§5.3), so the unchanged A16.3 instructions apply as written.
- Self-contained. Card text travels in the sheet; `row_hash` ties each label to
  exact text.
- All seven properties carry label columns. P1 is validated and P3/P4 are not
  searched for, but §3 admits them incidentally and the labeler is reading the
  card anyway.
- Labels blank. Nothing here consults the extractor.

**It is not a prevalence sample** (§2). The enriched stratum is drawn for
positives and is excluded from every prevalence figure. Prevalence comes from the
gold set only. The `micro-ground` rows are the §5a control — drawn at random with
no keyword filter, and reported separately, because the filtered stratum's
specificity is an **upper bound**: it finds positives by their characteristic
language, and cards phrasing a property unusually are exactly where a false fire
is most likely.

## 6. Labeling outcome (draft, 2026-08-11)

`enriched_labels.csv`. **Status: `machine-drafted`,** carried in every row, and
permanent -- A16.3/A16.7 were amended 2026-08-11 to drop the confirmed-gold path
and re-anchor settling on A16.4 finding validity, adjudicated on fired findings.
These labels are the case set, not the settle authority. Rates computed against
them measure agreement between two machine readings of the same text.

| Property | present | absent | unclear | Against the 15–30 target |
|---|---:|---:|---:|---|
| P2 uncertainty | **33** | 114 | 0 | met |
| P5 null baseline | **22** | 121 | 4 | met |
| P6 claimed COU | **10** | 131 | 6 | marginal |
| P7 confound control | **10** | 133 | 4 | marginal |

P2 and P5 clear the target. P6 and P7 sit on the honest-exit line — enough to
estimate specificity, not enough for a tight interval, and §6's caveat may still
be the right settling position for them.

Two observations worth carrying into the paper:

- **P5's positives are concentrated.** 13 of 22 are the SEA-LION family's single
  chance-normalization sentence, repeated across related cards. A property whose
  positive class is one organization's house style is thinly evidenced whatever
  the count says.
- **Several of the strongest P6 positives are negative COUs** — "unsuitable for
  practical medical applications", "not intended to inform decisions central to
  human life". The property is satisfied by a publisher ruling a use *out*, which
  is worth stating explicitly in A16.7: a claimed context of use is a boundary,
  and boundaries are drawn from either side.

### Class rulings

Five rulings covered 62 rows, each decided against the standard the gold set
already set rather than freshly — sensitivity is measured there and specificity
here, and two standards would measure two different properties. Full reasoning
and anchors: `CLASS-RULINGS.md`.

| Class | Rows | Ruling | Moved |
|---|---:|---|---:|
| SEALION | 13 | P3 **absent** — a sample size, not a population relationship | 13 |
| STEFANIT | 10 | P4 **present** — five linked runs beat the gold anchor's best-of-5 | 0 |
| LMEVAL-P4 | 8 | P4 **absent** — n-shot is a prompting condition (**marginal**) | 8 |
| NVIDIA-P6 | 3 | P6 **absent** — template metadata, the category the filter excluded 1,884× | 3 |
| TEMPLATE-EMPTY | 28 | all **absent** — stub cards | 0 |

LMEVAL-P4 is the one most worth overturning if any is; it is isolated, and
flipping it moves 8 rows and nothing else.

## 7. The false-positive keepers are the durable output

`tests/fixtures/specificity/cases.json` — 116 cases, **13 flagged
`hard_assert`**.

The pre-filter's false positives turned out to be the most valuable thing the
run produced. Characteristic language present, property absent:

| Lure | Actually |
|---|---|
| `±` inside a SentencePiece vocabulary dump | not a dispersion statement |
| `Within ±1 Level` | a tolerance-band metric |
| `Explained Variance` | a metric name |
| `Out of Scope` | a classifier's label name |
| `unsuitable for the task` | a scoring-rubric anchor |
| `majority class` | KNN mechanics |
| `intended for research only` | a licence term |
| `ablation` | a repo or script name |

Each is a card where reading the language as the property would populate a field
that is not there and **silence a warranted weakener**. They are far more
adversarial than the gold set's ordinary absences, because the language is
present to be misread.

Only the 13 mechanically-determined cases carry `hard_assert` and may fail a
test. "Within ±1 Level is a tolerance band" is a fact about the text; "this card
states a context of use" is a judgment, and a drafted judgment must not fail a
build.

## 8. The case-set integrity harness

`tests/test_specificity_cases.py` asserts the set can still test something:
every lure survives in its excerpt, the label status is stated as settled rather
than pending, no case holds two verdicts on one property, excerpts stay minimal
spans, and no `absent` case is one the search pre-filter would have excluded
anyway (which would make it the filter's problem, not the extractor's).

Only mechanically-determined cases carry `hard_assert` and may fail a build.
All five failure modes were broken on purpose and restored.

**What remains unmeasured is finding validity** — the settle authority under
A16.7 as amended. No finding has been adjudicated, because until the extractor
runs against real cards there are no fired findings to adjudicate. The panel
routing is declared (A16.4, 2026-08-11) and waiting on Phase 5's slice.

## 9. First extraction measurement — 2026-08-11

`card_prose.extract()` now exists (the module had carried a prompt and a parser
since Phase 4 with nothing joining them), and the harness
`run_specificity.py` runs it over all 116 cases.

**Extractor `ollama/qwen3.5:4b`** — the configured default, pinned in the result
along with the prompt hash, temperature 0.0 and seed. 116 cases, **0 errors**.

| Property | False **clear** | False **fire** |
|---|---:|---:|
| P2 uncertainty | 1/9 (11%) | **15/33 (46%)** |
| P5 null baseline | 0/4 (0%) | **18/22 (82%)** |
| P6 claimed COU | 0/13 (0%) | **8/10 (80%)** |
| P7 confound control | 1/15 (7%) | **7/10 (70%)** |

**All 13 `hard_assert` cases passed.** The extractor was not fooled by `±` in a
SentencePiece vocabulary dump, `Within ±1 Level`, `Out of Scope` as a classifier
label, or `ablation` as a repo name. The keepers held.

### The asymmetry is the finding

The prompt's central instruction — *a blank is a correct, useful answer* — works
almost perfectly. Invention is near zero: the extractor does not manufacture a
property that is absent, which is the failure that would silence a warranted
weakener.

It fails in the opposite direction, hard. It **misses 46–82% of properties that
cards genuinely state**, so the weakener fires on the majority of publishers who
did the right thing. That is the reputation-damaging direction — a public
accusation of an omission the card did not commit — and at this configuration it
is disqualifying.

**This is a statement about `qwen3.5:4b`, not about the rules.** A 4B local model
is the configured default, not a production extractor, and the point of pinning
the configuration is that this number belongs to it. The rules' own wording is
not implicated: a rule cannot fire correctly on evidence extraction never
delivered. Re-measuring against a frontier extractor is the obvious next
comparison and is one flag.

### Reproducible, not a single draw

Two independent full runs produced **identical rates on all four properties**.
At temperature 0 with a fixed seed the extractor is deterministic here, so this
is an instrument reading rather than one sample of a stochastic process.

### Status of these numbers

Secondary instrumentation. Scored against machine-drafted labels, they measure
agreement between two machine readings of the same text. Per A16.7 as amended,
**they do not settle a rule** — A16.4 finding validity, adjudicated on fired
findings, does.

They are still decision-relevant: an extractor with an 82% miss rate cannot be
the one whose findings go to the adjudication panel, or the panel will spend its
effort on findings caused by extraction rather than by cards.

### A provenance bug the run surfaced

The harness first hashed the cases file when *writing* the result rather than
when *reading* it. A relabel that landed mid-run therefore produced a result
pinning the file's later state — a provenance block that was internally
inconsistent (current hash, stale `label_status`) while looking well-formed.
Fixed to hash at read time, and the run above is the clean artifact.
