# Response: attribution plan — approved with one reframe and three patches

The plan is approved. The probe findings (shotgun-beats-extractor; rationale
framing carrying the label with 94% confirmation) are accepted as the basis,
and the restraint items (no spaCy, no anchor dictionary, no router-shortlist
lead, labelled-data-not-pickle) are ratified as written.

## H2 metric moves — as a disclosed amendment, built in this order

*(Figures below are **raw** extractor output on the **synthetic** 50-bundle corpus,
**no adjudication step**. Working note, not shipped text — but the numbers are the
same ones the shipped sections carry, so the label travels with them.)*

Decision recorded: the H2 gate is amended. The pre-registered detection-F1
gate was written before its properties were known; the re-run shows null
controls EXCEEDING the extractor (0.9637/0.9544 vs 0.9035/0.8909), which
means the metric does not discriminate and can neither support nor refute
H2. That is instrument replacement upon measured invalidity — the same move
as the extractor qualification gates — and it is defensible exactly to the
extent the paper trail shows that and nothing else. Binding order:

1. **COU2 triage FIRST (Phase 0, promoted below), before the amendment
   lands.** An amendment that also happens to retire a currently-failing
   regression line is an exhibit against us. Triage nasa COU2 0.593 to
   metric-artifact / segmenter-artifact / real, file the finding, and only
   then amend. If it is real, the amendment must carry it forward under the
   new gate, not lose it.
2. **Amendment structure (R4 entry, dated):** original H2 criteria
   preserved verbatim under an amendment banner; the invalidity evidence
   attached (null-control table + shotgun sweep — self-evidently
   disqualifying to any reader); the new gate stated as the plan's
   conjunction (permutation-null margin, no null in the battery exceeds the
   figure at any length, real-corpus measurement, agreement ceiling stated,
   FP/FN published beside).
3. **Report BOTH, permanently.** Every place H2 results appear shows the
   original-gate numbers alongside the amended-gate numbers. Nobody gets to
   discover the old figure; it is disclosed next to the reason it stopped
   being load-bearing. "The gate a null could beat, and the gate it was
   replaced with" is the rigor story — it only works if both numbers stay
   visible.
4. **U-spec ripple:** U2's disclosure discipline extends to H2 — the
   praxis text's H2 wording updates with the same original-and-revised
   side-by-side treatment as RQ1, and the metrics-spec section (R6/U8)
   carries the new conjunction. `docs/credibility-inspector.md` §7 corrects
   in the same change.
5. **Meeting materials get it proactively.** The amendment goes INTO the
   committee-response packet before anyone finds it — disclosed first, it
   is evidence of the harness catching its own metric; discovered later, it
   is their post-hoc-changes critique with a date on it.

## Patch 1 — promote the two "also outstanding" items into Phase 0

A committee member running the harness hits both regardless of metric
philosophy, so neither can sit in a footer:

- **nasa COU2 at 0.593** is a failing gate in the harness today. Phase 0
  triages it to one of: metric artifact (saturated F1), segmenter artifact,
  or real regression — and files the answer as a finding either way. If it
  dissolves under the fixed segmenter, that is evidence for the plan; if
  not, we need to know before Phase 3 rebuilds the ruler.
- **90/480 factors returning no status (~19%)** feeds the completeness math
  C2 claims. Same triage, same filing.

## Patch 2 — attribution_agreement.py gets a declared go/no-go

Running it is in the plan; the consequence of failure is not. Declare before
the run: if same-sentence agreement < 0.60, then (a) every number in this
plan including the 0.62 headline re-anchors as single-annotator agreement,
stated as such wherever cited; (b) Phase 3's disagreement adjudication
design is revisited — adjudicating against labels that do not agree with
themselves is not adjudication; (c) the real-document assets (annot_*.json,
the 23 author-written rationales) become the primary anchor. Write the
branch on disk before the script runs — same fork discipline as everything
else this month.

## Patch 3 — cite the vacuous-pass rule by name

"Refuse rather than return zero" / "(0,0) renders as an omitted row,
indistinguishable from not-run" is the vacuous-pass class already promoted
to AGENTS.md §13 from the qualification-table fix (an unmeasured thing may
never display as a passed thing). Cite that rule in the plan text rather
than re-deriving it locally, so both workstreams share one lesson under one
name. Same for the xfail-strict test: it is the "every check fails once"
rule applied prospectively — say so.

## Execution order

Phase 0 (including the two promoted triages) and Phase 1 this week —
they harden the meeting surface. Phase 2's evidence_span carries its kill
criteria as written; note its convergence with the fork's span-citation
constraint (a claim must carry a quotable span — "stated, not inferable"
binding the machine) — one line in the study text, since two workstreams
arrived at it independently. Phases 3–4 on the FAccT clock, no praxis
coupling.

Everything else as written. The honest-cost line (0.638 → 0.418, the price
of a number a verbose null cannot reach) survives into whatever writeup
this feeds — it is the thesis of the whole exercise in one sentence.
