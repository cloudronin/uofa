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
