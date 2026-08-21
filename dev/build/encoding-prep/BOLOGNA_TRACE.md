# Bologna usage trace — the A3 negative-control ruling

**Determination: BRANCH M.** Bologna appears in measured runs whose numbers survive into
committed status reports, study findings, and the Ch4 numbers ledger. It is disqualified
from A3.

Read-only trace, 2026-08-22. Full history searched, not just HEAD. No encodings run, no
files touched but this one.

## Method and coverage

Searched every ref (`git rev-list --all`, `git log --all -S`, `git log --all --name-only`)
for the case-study name, the five author surnames (Aldieri, Curreli, Szyszko, La Mattina,
Viceconti), the DOI (`10.1016/j.cmpb.2023.107727`, `cmpb.2023`, `107727`), the filename
fragments (`bcthip`, `bundle_bologna`), and the manifest slug (`bologna`).

**78 files at HEAD carry a hit. 67 commits across all refs touch the string.** The result is
not close, so no hit had to be resolved under the conservative rule — see "Ambiguous hits"
below.

## Hit table

Classification: **INPUT** = the document or its transcription fed a run. **MEASURED** = a
number derived from it survives into a committed artifact. **MENTION** = named as a
candidate or discussed, no use.

### 1. Model-selection scorecard

| Path | Ref | What it fed | Number survives? |
|---|---|---|---|
| `studies/model-selection/FINDINGS.md:127,139` | HEAD, `3e6bef9f` | Instrument-recovery measurement, run on Bologna | **MEASURED.** 761 spurious decimals; 39 decimals found by the fixed reader; 15 recovered; 38% of genuine figures unfindable; groundedness 0.621 to 1.000 on the re-score |
| `studies/model-selection/DECLARATION.md` | HEAD | — | no hit |

The Bologna measurement is not incidental to this study. It is the evidence for the dated
correction to commit `82b4baf7` and the basis of the standing disclosure that **"every real-corpus
density in this table is a floor, not a point."** That disclosure qualifies the entire
scorecard. Remove Bologna and the correction loses its measurement.

### 2. Extraction evaluation corpora and ground truth

| Path | Ref | What it fed | Number survives? |
|---|---|---|---|
| `tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/ground_truth.json` | HEAD, dated 2026-08-06 | 23 `expected_factors` transcribed from the paper's Table 1, plus COU and model-risk derivation | **INPUT** to items 3a, 3b, 3c below |
| `.../bundle_bologna_bcthip/metadata.json` | HEAD | tier 1, quality real, `published_granularity: vv40_subfactors` | INPUT |
| `docs/v1/annot_bologna.json` | HEAD | 13 evidence-span annotations, 11 of 13 pack factors, at **revision 2** (revision 1 corrected for annotator bias) | **INPUT**, hand-authored twice |
| `docs/v1/valresults_bologna.json` | HEAD | K9 validation-results gold set | INPUT |
| `tests/fixtures/extract_corpus_seeded/train/bundle_seeded_{001,004,007,010,013,016,019,022,025,028}_bologna/` | HEAD | **10 of 30 training bundles** generated from the Bologna seed | **MEASURED** via seeded-corpus results |
| `tests/fixtures/extract_corpus_seeded/holdout/bundle_seeded_{001,004,007}_bologna/` | HEAD | **3 of 10 holdout bundles** | **MEASURED** |
| `tests/fixtures/extract_corpus_seeded/{train,holdout}/generation_report.json` | HEAD | `"seed": "bologna"` x10 train, x3 holdout | MEASURED |
| `tests/fixtures/extract_corpus_seeded/pilot/bundle_seeded_{001,004,007}_bologna/` | history only, incl. `source/paper.pdf` | pilot generation | MEASURED |
| `tests/test_seeded_corpus.py:147-346` | HEAD | asserts on Bologna-seeded bundle ids; docstring carries the pilot figure | **MEASURED.** "bologna 42 rows over 39 combinations (1.08)" |
| `docs/extract_eval_v1.md`, `tests/test_extract_eval.py` | all refs | — | **no hit, clean** |

Bologna is a **structural template for a third of the seeded corpus**, in both the train and
the holdout split. Anything trained or evaluated on that corpus has Bologna's shape in it.

Note on the historical `source/paper.pdf` files under `bundle_seeded_*_bologna/`: these are
**LLM-generated synthetic papers** produced by `generate_seeded_corpus.py` from the Bologna
seed, not the source document. The real PDF has never been in the repo, on any ref. That part
of the standing instruction already holds.

### 3. H2-adjacent artifacts

| Path | Ref | What it fed | Number survives? |
|---|---|---|---|
| `studies/real-document-rescore/FINDINGS.md:34,65` | HEAD, `1abbf8d6` | Per-document rescore | **MEASURED.** Row `bologna \| vv40 \| 0/13 \| 895` |
| `studies/published-rationale-ceiling/FINDINGS.md` | HEAD | **The entire study runs on Bologna's ground truth and nothing else** | **MEASURED.** 23 rationales; name-only null 12/23 = 0.522; prompt anchors 12/23 = 0.522; delta +0.000; median 8 words; 8 of 11 misses are anchors declining to fire |
| `studies/attribution-agreement/PREREGISTRATION.md:41` | HEAD, `2047ccf3` | Bologna's `ground_truth.json` named as the **declared substrate** | INPUT, pre-registered |
| `studies/ch4_numbers/LEDGER.md:239` | HEAD, `33cef6c4` | Ch4 real-corpus table under Decision 7's split | **MEASURED and MANUSCRIPT-BOUND.** Row `bologna \| vv40 \| 0/13 \| held-out` |
| `docs/keyless-hybrid-ceiling.md:14,222,506` | HEAD | Keyless ceiling measurement | **MEASURED.** `bologna (real) \| 10,998 \| 46% \| 35% \| 11/13 \| 0.05%` |
| `docs/keyless-extract-plan-v3.md:501-548` | HEAD | K4/K6 route comparison | **MEASURED.** "K4 beats K6 by 3.3x at k=5, and does so on Bologna alone as well (0.45 vs ...)" |
| `docs/keyless-extract-plan-v4.md:8,21,72,129,179` | HEAD | Per-property route table | **MEASURED.** `bologna \| 13 \| 11 \| 2`; `bologna \| 11/13 \| K4` |
| `docs/seeded-corpus-spec.md:83,132,299,350` | HEAD | Agreement and selection stats | **MEASURED.** `bologna \| 1 \| 7/12 = 0.583`; `bologna \| 0.923 \| 0.000 \| 0.917 \| 0.846` |
| `docs/valid-package-spec.md:309` | HEAD | Package validity matrix | **MEASURED.** `bologna \| Complete \| — \| yes \| yes \| fail` |
| `docs/corpus-construction-findings.md:514,573` | HEAD | Construction record | MEASURED (bundle inspection), and records the K7 premise defect |
| `docs/real-corpus-supply-survey.md:72-183` | HEAD | Supply and pathology screen | **MEASURED.** `bologna \| 0.06% \| clean`; "Bologna is the best real document found" |

**The Ch4 dependency is the decisive one.** The held-out headline is **3/33 = 0.0909**, and
that denominator is `opensim 7 + elemance 6 + ared 7 + bologna 13`. Bologna contributes 13 of
the 33 factors — **39% of the manuscript's headline denominator**. The number cannot be
restated without it.

### 4. Specs and status reports (mention-only)

None of these constitute use. Listed to discharge the distinction explicitly.

| Path | Classification |
|---|---|
| `docs/UofA_Decision_Record_2026-08-16.md:17` (Decision 8) | **MENTION** — the ruling itself |
| `docs/UofA_Investigation_Spec_v1_0.md:82` | **MENTION** — candidate list |
| `docs/UofA_Ruling_Implementation_Plan_2026-08-16.md:207,278` | **MENTION** — queue entry |
| `docs/UofA_Unified_Repair_Spec_v2_1.md:92,168`; `docs/archive/UofA_Unified_Repair_Spec_v2_0.md:234` | **MENTION** — §A10 pool assignment |
| `docs/investigations/INV-5-findings.md`, `INV-13-findings.md`, `A10-admission-arithmetic.md`, `SUMMARY.md` | **MENTION** — but each *records* prior use; INV-13:234 states Bologna is "used in at least four committed studies" |
| `dev/build/encoding-prep/BOLOGNA_STATUS.md`, `AUTHOR_QUEUE.md` | **MENTION** — the awaiting-author investigation |

### 5. Dev scratch, scripts, CI

Fourteen scripts under `dev/tools/scripts/` name Bologna as a corpus entry or measurement
target. **None is a smoke script.** Each is a measurement instrument whose output is reported
in one of the study findings above:

`corpus_profile.py:59`, `d1_annotator_agreement.py:38-124`, `generate_seeded_corpus.py:78,691,710,1065`,
`groundedness.py:802`, `keyless_k7_context_of_use.py:39-190`, `keyless_k8_model_risk.py:28-139`,
`keyless_k9_validation_results.py:98`, `keyless_trained.py:515`, `keyless_vs_model.py:50`,
`published_rationale_ceiling.py:4,58`, `real_attribution_reference.py:45`,
`seeded_agreement.py:103,197`, `v1_router_comparison.py:75`.

`generate_seeded_corpus.py:1065` makes Bologna a **default** seed: `--seeds opensim,bologna,nagaraja`.

No notebooks exist in the repo. No committed shell history. **CI workflows carry no hit on any
ref** (`.github/` clean, content-level pickaxe included).

### 6. Space sample bundles and demo content

**Clean.** `space/`, `examples/`, `packs/`, `site/` carry no hit at HEAD, and the content-level
history pickaxe over those paths returns nothing on any ref. No Bologna-named file has ever
existed under them.

### 7. Shipped source — Bologna in the rule catalog

Recorded separately because it bears directly on Branch S's stated rationale.

| Path | What it is |
|---|---|
| `src/uofa_cli/keyless/routes.py:83` | The `_CITATION` regex exists **because of a Bologna false positive**: *"accounting for its risk level [3,4]" yielded a stated risk of "3" on Bologna, from a bibliography reference.* A shipped extraction rule, introduced to fix a defect Bologna exposed |
| `src/uofa_cli/readers/pdf_reader.py:75` | Bologna in the `_X_TOLERANCE = 1.2` validation table (`bologna 0.06% -> 0.04%`). Not the driver (tavi1/tavi2 were), but a no-regression check |
| `dev/tools/scripts/keyless_k7_context_of_use.py:39` | K7's first route was built on a premise **generalised from Bologna** — *"That generalised from Bologna, where it is true, and measured on the train set it is wrong."* The premise was later discarded, but Bologna set it |

## Ambiguous hits

**None.** The conservative rule — classify MEASURED when smoke and measured cannot be
distinguished — did not have to be applied. Every hit resolved cleanly to INPUT, MEASURED, or
MENTION on the face of the artifact. Nothing in the trace resembles informal dev or smoke
testing of the extract command.

## Branch determination: BRANCH M

Branch M fires, and it fires on the trace's own primary test rather than on any marginal
reading. Bologna's numbers survive into committed artifacts at every level the branch names:
into study findings (`published-rationale-ceiling`, whose headline 12/23 = 0.522 is *entirely*
Bologna-derived and which would cease to exist without it), into the model-selection scorecard
(the instrument-recovery correction and the floor-not-point disclosure that qualifies the whole
table), into the H2 evaluation chain (`real-document-rescore`, the pre-registered
`attribution-agreement` substrate), into the extraction corpus (a third of the seeded bundles,
train and holdout both), into shipped source (a rule catalog entry that exists to fix a defect
Bologna exposed), and into the manuscript itself, where Bologna supplies 13 of the 33 factors
behind the Ch4 held-out headline of 3/33 = 0.0909. Bologna is not a document the project once
ran a command against; it is the most internally-worked real document in the corpus after the
two case studies, hand-annotated twice with revision 1 corrected for annotator bias, and the
declared substrate of two pre-registered studies. Branch S's condition — *informal dev or
smoke testing, with no measured result deriving from it* — is false on the evidence, and no
part of the trace is close enough to the line to need the conservative tiebreak.

**Bologna is disqualified from A3.**

## Two findings the author should see before the addendum is written

Both are places where the trace contradicts a premise in the pre-declared ruling. Neither
changes the branch; both change what the addendum can say.

**1. Branch S's rationale would have been factually wrong even if Branch S had fired.** The
rationale on the record reads *"the property A3 measures belongs to the rule catalog, which
never saw Bologna in tuning or validation."* The rule catalog did see Bologna.
`src/uofa_cli/keyless/routes.py:83` carries a regex introduced specifically to suppress a
Bologna false positive, and K7's original route premise was generalised from Bologna before
being discarded on train-set measurement. Since Branch S does not fire this is moot for the
ruling, but the sentence should not be carried forward into any other disclosure.

**2. Branch M's stated replacement is not what Decision 8 provides.** The investigation says
that on Branch M *"the Ahn & de Weck alternative takes the slot per Decision 8's screen."*
Decision 8 does not say this. Its text is: *screen Ahn & de Weck for the scorecard pool first.
If it qualifies, Bologna goes to A3. If not, Bologna still goes to A3; the scorecard pool takes
the measured-scarcity disclosure instead.* **Bologna goes to A3 in both of Decision 8's
branches**, and Ahn & de Weck is screened only for the *scorecard pool* — it is nowhere
designated as A3's document. Disqualifying Bologna from A3 therefore leaves **A3 with no
assigned document at all**, which is a state Decision 8 never contemplated.

This matters because A3 is on the defense path (must-have, 1 FP gate), and because
`A10-admission-arithmetic.md` §1 already recorded that rulings 7 and 8 interact: moving Bologna
out of the annotation pool drops the held-out base from 4 to 3 and makes the 11-14 admission
target **arithmetically unreachable**. A ruling that removes Bologna from every pool needs to
say which of the seven unscreened INV-13 candidates A3 draws from, or accept that A3 has no
document until one is screened. **A replacement has to be chosen; it cannot be inherited from
Decision 8.**

## Disclosure sentence

Branch S does not fire, so its sentence is not drafted. Branch M disqualifies rather than
discloses: Bologna holds no assignment, and the A3 slot has no document pending the author's
choice of replacement.

For completeness, the sentence the *scorecard pool* takes under Decision 8's second branch is
unaffected by this trace and remains the measured-scarcity disclosure.

## Side question: is Ahn & de Weck clean?

**Yes. Zero usage hits, on any ref.**

Searched `ahn`, `de weck`, `deweck`, `spacenet`, `delphi`, `sys.21266`, `21266` across all
refs at content level.

| Finding | Detail |
|---|---|
| Identification | Ahn, de Weck & Steele, *"Credibility Assessment of Models and Simulations Based on NASA's Models and Simulation Standard Using the Delphi Method,"* Systems Engineering, 2014, `doi:10.1002/sys.21266` |
| Usage hits | **None.** No fixture, no corpus bundle, no study, no script, no result JSON, no CI input, on any ref |
| Every hit's kind | **MENTION only** — `A10-admission-arithmetic.md` §3, `INV-5-findings.md`, `INV-13-findings.md:252`, `SUMMARY.md`, the Decision Record, the two repair specs, the Investigation Spec, `BOLOGNA_STATUS.md` |
| Commits touching it | 7, **all docs/specs/investigations commits**. No fixture or study commit |
| False positive to discount | Two `Delphi` hits in `dev/build/adversarial/phase2/.../adv-2026-p2-008-w-ep-04-v18.jsonld` are *"Delphi Flow Technologies"*, a fabricated manufacturer inside a generated adversarial artifact. Unrelated to the paper. INV-5 §245 already recorded the same two hits |
| Access | **Paywalled** (Wiley/INCOSE). No local copy. Never fetched |

So the document is **known-clean** in the sense the side question asks: nothing the project has
measured on has ever touched it.

**But clean is not the same as eligible, and it is not currently A3-ready.** Two caveats:

- `A10-admission-arithmetic.md` §3 **recommends screening it OUT** of the scorecard pool, on
  the pool's own criterion: Ahn's credibility levels are *elicited from a ten-person Delphi
  panel*, not declared by the model's developers, so admitting it would mix panel-consensus
  judgments into a pool of developer-declared assessments. The same category objection applies
  with more force to A3, where the negative control is specified as *"one additional published,
  accepted submission encoded straight from source."* A third-party opinion survey **about** a
  model is not a submission **by** its developers.
- The screen is **still unrun**. `INV-13-findings.md:252` records step 4 as *"not performed...
  Unanswered,"* and licensing is unverified. Its cleanliness is therefore the cleanliness of a
  document nobody has been able to open, which is not positive evidence of fitness.

**Ahn & de Weck is clean but probably ineligible, and unscreened either way.** If the author
wants A3 filled rather than left open, the candidate should come from the seven screenable
INV-13 papers, and the screen has to run first.

---

*Trace complete. Nothing else touched. No encoding of any A3 document begins until the
addendum line exists.*
