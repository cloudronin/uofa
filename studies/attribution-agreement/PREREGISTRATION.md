# Pre-registration: what the annotator-agreement number obliges us to do

Written 2026-08-14, **before** `dev/tools/scripts/attribution_agreement.py` is
run. The script is written, complete, and appears never to have been executed.
This file exists so the branch is fixed before the number is seen, which is the
only thing that makes a threshold a threshold.

## The question

Attribution is scored against `evidence_keywords`, which gpt-5 wrote. Every
attribution figure in this project is therefore agreement with **one annotator**
until shown otherwise. The script re-annotates a sample with a Claude model from
the same sources and compares at the **sentence** level: for factor F, did both
annotators' keywords land in the same sentence? Keyword-string comparison would
measure paraphrase, which is the error the attribution metric itself already
made once.

## The declared branch

The measurement is **same-sentence agreement rate**. The threshold is **0.60**.

### If agreement >= 0.60

The labels track something in the documents. Attribution figures stand as
written, and the annotator caveat is stated once wherever they are cited rather
than qualifying each number.

### If agreement < 0.60

Three consequences, all binding:

1. **Every attribution number in the plan re-anchors as single-annotator
   agreement**, including the 0.62 headline and K6's 0.615, and is stated that
   way at each point of use — not in a footnote.
2. **Phase 3's disagreement adjudication is redesigned.** Hand-adjudicating the
   ~100 rows where the old and new rules disagree assumes a stable ground truth
   to adjudicate against. Labels that do not agree with themselves are not that.
3. **The real-document assets become the primary anchor**, not the corroborator:
   `docs/v1/annot_*.json` (40 annotated pairs across 6 real papers) and the 23
   author-written `published_rationale` strings in
   `tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/ground_truth.json`.
   Synthetic-corpus attribution then reports *beside* a real-document figure and
   never alone.

### What no result licenses

A high agreement number does **not** rehabilitate the current attribution rule.
The rule is separately disqualified by measurement: a 20-sentence shotgun of
random source sentences, filed identically under every factor, scores 0.9284
against the extractor's 0.6383. Agreement is about whether the *labels* are
sound. Phase 1 and Phase 3 are about whether the *ruler* is. Passing here
changes nothing about that.

K6's 0.615 is the figure most at risk, because it is trained on gpt-5's labels
and tested against gpt-5's labels — the script's own docstring names this.

## Why this file exists at all

Two kill criteria in this project have been run and passed while meaning
nothing. A threshold chosen after seeing the measurement is not a gate, and the
H2 detection-F1 gate is this month's example of what that costs. The date on
this file is the point.

---

# RESULT — 2026-08-14, run after the above was committed

`attribution_agreement.py --n 10`, `claude-sonnet-4-6` re-annotating against
gpt-5's `evidence_keywords`, corpus `tests/fixtures/extract_corpus_v2/dev`.

| measurement | value |
|---|---|
| factor selection — both annotators marked the factor | 161 / 175 (0.920) |
| **same-sentence agreement (the declared measurement)** | **147 / 161 (0.913)** |
| ≥50% token overlap (the rule `score_attribution` uses) | 156 / 161 (0.969) |

gpt-5 marked 8 factors Claude did not; Claude marked 6 gpt-5 did not.

**Branch taken: agreement >= 0.60.** 0.913 clears the declared threshold by
0.313. None of the three `< 0.60` consequences bind. The labels track something
in the documents rather than one model's taste, attribution figures stand as
written, and the annotator caveat is stated once wherever they are cited rather
than qualifying each number individually.

K6's 0.615 stands as reported. The docstring's stated risk — trained on gpt-5's
labels and tested against gpt-5's labels — is not eliminated by this, but it is
bounded: a second family reading the same documents lands on the same sentence
91% of the time, so the labels are not idiosyncratic in the way that would have
made 0.615 mostly an artefact of learning one annotator's habits.

## Three things this result does not settle

**The corpus is single-standard.** All ten bundles are `bundle_nasa_*`. The
figure is agreement on NASA-STD-7009B synthetic documents and is not evidence
about V&V 40 documents or real ones.

**High agreement has two explanations and this cannot separate them.** Either
the labels are sound, or the synthetic documents are unusually unambiguous —
they were generated to carry specific evidence, so two competent readers finding
the same sentence may be a fact about the corpus rather than about annotation.
The real-document assets (`docs/v1/annot_*.json`, the 23 author-written
rationales) remain the check on that, and this result is a reason to keep them
as corroborators rather than a reason to stop needing them.

**It says nothing about the attribution rule.** As declared above: the rule is
separately disqualified because a 20-sentence shotgun scores 0.9284 against the
extractor's 0.6383. Sound labels measured with a broken ruler are still measured
with a broken ruler. Phases 1 and 3 are unaffected by this result.

## A note on the two thresholds

This pre-registration declared 0.60. The script's own printed interpretation
uses 0.80. The result clears both, so nothing turned on it — but had it landed
between them, two committed thresholds would have disagreed about the same
measurement, and the one written later would have looked chosen. Worth fixing
before the next pre-registration: check for an existing threshold in the
instrument before declaring one beside it.
