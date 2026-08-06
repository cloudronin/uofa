# Keyless extract: findings

Running record for the keyless-extraction investigation. One section per
candidate, including the ones that failed, with what each cost.

Companion to `keyless-extract-investigation-spec.md`. Measured against the
50-bundle corpus in `tests/fixtures/extract_corpus/`.

## The measurement was broken, and repairing it is the first finding

Two constant functions saturate the metrics this eval reports. Neither reads a
word of the input:

| Control | Parameters | Detection F1 | Level (±1) | Status |
|---|---|---|---|---|
| `control_constant_list` — emit the pack's checklist | 0 | **0.960** | — | — |
| `control_constant_level` — predict 2 | 0 | — | **1.000** | — |
| `control_majority_status` — say `assessed` | 0 | — | — | **0.928** |
| `control_empty` — emit nothing | 0 | 0.000 | 0.000 | 0.000 |

Ground truth: 740 of 800 factor rows are `assessed` (92.5%), and every assessed
level is 1, 2 or 3 — **never 4, never 5**. So emitting the standard's fixed
checklist scores 0.960 on detection, and the constant 2 lands inside the ±1
tolerance on every row.

The sharpest way to see it: a **perfect oracle** — every factor, level and
status exactly right — reports `delta +0.000` against the control, because
detection F1 cannot distinguish it from a compile-time list. Both also clear the
report's `F1 >= 0.70` gate.

**Consequence.** No detection number from this corpus means anything on its own,
including the 1.000 previously reported for the LLM. Every candidate is now
reported as a delta against these controls, printed in the same table, never
suppressed.

The level metric was worse than uninformative. `extract_eval_v1.md` reports the
LLM at 0.55 on Numerical solver error — *below a constant* — which reads as the
model failing to assess. It is the model predicting 4 and 5 into a corpus whose
generator was tightened until it stopped emitting them. That is a corpus and
metric defect, not a finding about qwen.

## C1 — substring match on the pack prompts' `Look for:` anchors

`dev/tools/scripts/keyless_extract_probe.py`. 124 anchor phrases parsed from the
two pack prompts (49 across 13 vv40 factors, 75 across 19 nasa). ~0.25 s, no key,
no download.

| | P | R | F1 |
|---|---|---|---|
| C1 dictionary | **0.973** | 0.235 | **0.367** |
| `control_constant_list` | 0.928 | 1.000 | **0.960** |
| delta | **+0.045** | −0.765 | **−0.593** |

**Verdict: fails.** Kill criterion 1 asked for ≥ 5 points of precision at equal
recall. C1 delivers **+4.5** points — narrowly under, and worth reporting as a
near miss rather than rounding to a clean verdict — at **a quarter** of the
recall. It fails both clauses.

Stratification behaves as a lexical method should. Recall roughly halves from
report to memo (0.300 → 0.161) and from complete to sparse (0.294 → 0.159).
Precision never moves.

### Why recall fails, and why a bigger dictionary will not fix it

Per-factor recall makes the boundary concrete. The factors a dictionary handles
are the ones the standard names with a term of art; the ones it cannot are about
physics, comparison and relevance.

| Missed in | Factor |
|---|---|
| 49/50 | Relevance of the quantities of interest |
| 48/50 | Model inputs |
| 47/50 | Equivalency of input parameters |
| 46/50 | Output comparison |
| 46/50 | Relevance of the validation activities to the COU |
| 45/50 | Model form |
| 42/50 | Test samples |

Against **Discretization error at 98% recall** — because the standard coined one
canonical name for it: GCI, Richardson extrapolation.

The anchors are written at the abstraction level of the standard ("QoI directly
measures the safety concern"); the documents are written at the level of the
physics ("head rise prediction", "SST k-ω"). Closing that by enumeration means
listing every quantity of interest and every turbulence model in every domain
the tool serves — unbounded, and unbounded in exactly the direction the
cross-domain claim points. Supplying that mapping is what the LLM is doing.

## Groundedness — the first metric a constant cannot reach

`dev/tools/scripts/groundedness.py`, wired into `score_extraction_batch.py` and
reported on every run. Three numbers, over the 50-bundle corpus:

| | | |
|---|---:|---|
| Coverage | **0.974** | 779/800 factors given a rationale |
| Claim density | **0.565** | 440/779 rationales carry a checkable claim |
| Groundedness | **0.9942** | 859/864 claims trace to the source documents |

Detection F1 0.960 is reachable by printing the pack's checklist. Nothing here
is: citing a figure from the document requires having read it. A method emitting
no rationale — which is what a dictionary backend does — scores **coverage 0**,
and the metric reports that as absent rather than as unmeasurable.

All three are needed. A backend writing *"evidence was reviewed and found
adequate"* for every factor scores coverage 1.0 and contributes **zero rows** to
the groundedness denominator, so against a two-number metric contentless prose
is the optimal play. Claim density is what exposes it: the filler generator
scores 0, the LLM 0.565.

**Not measured: attribution.** A rationale citing the GCI figure under
*Numerical solver error* is fully grounded and entirely wrong — real number,
right document, wrong factor. This measures **fabrication**, because that is
checkable without a reference answer. Sign is not checked either.

### The triage, and why the stopping rule earned its place

The plan set a gate: hand-classify every ungrounded row, and **if metric
artefacts exceed 20%, no groundedness figure ships**. The first pass reported 42
ungrounded rows. **28 of them — 67% — were artefacts of the metric's own number
parsing.** The gate fired, and it was right to.

| Pass | Artefacts | Cause |
|---|---:|---|
| v0 naive | 28/42 (67%) | range hyphen read as a minus (21), `k` suffix (4), rounding (2), identifier fragment (1) |
| v1 | 19/32 (59%) | **the fix made it worse** — see below |
| v2 | 7/13 (54%) | U+2212 minus (4), numbers spelled out (3) |
| v3 | 1/5 (20%) | sign applied to a magnitude the source states unsigned |
| **v4** | **0/4 (0%)** | gate clears |

**The v1 regression is the most useful thing here.** Fixing the `k` suffix so
`65k` matched a source reading `65,000`, I wrote the character class `[kK]` —
which read the K in `±33K`, `>1100K` and `1.8K convergence` as kilo and turned 33
into 33000. It invented **twelve** fresh fabrication reports while repairing
four. K is kelvin; k is thousands.

An automated re-triage reported that pass as **0% artefacts**, because the
classifier only knew the mechanisms already fixed. Only reading the 32 rows
caught it. That is the argument for the plan's insistence on hand-checking a
bounded set rather than trusting a script to grade its own homework.

The repairs did **not** inflate the headline. Groundedness moved 0.959 → 0.994
while the claim pool *shrank* from 1181 to 864, because the artefacts were being
counted in both the numerator and the denominator. What actually moved was claim
density, 0.669 → 0.565 — the identifier rule stopped scoring "ISO 17025" and
"CC-2024-017/018" as quantitative claims, which they are not.

**The rules cut both ways, and the second direction is quieter.** An early
identifier rule was case-insensitive and allowed any word between the keyword and
the number, so *"table shows 88% agreement"* masked the 88 and *"reference 7
locations"* masked the 7 — deleting real claims rather than inventing false ones.
No row in this corpus hit that path, so no number moved and nothing downstream
would have reported it; the metric would simply have measured less than it
claimed to. Tightening it recovered 22 claims.

Every rule in `normalise_numbers` traces to a row where the metric accused a
correct rationale, or to one where it quietly declined to check a real claim, and
each is pinned in `tests/test_groundedness.py` with that provenance.

### The four survivors

Zero fabrications in 864 checkable claims. All four remaining rows are
hand-classified against the source text:

| Bundle | Claim | Class | Source says |
|---|---|---|---|
| `nasa_cht_001` | 83% of locations | derived | "within ±15°C for **20 of 23** locations" — 87%, and the extractor computed 83% |
| `nasa_cht_005` | 10⁻⁶ to 10⁻⁸ | derived | 2.4e-8, 3.1e-8, 1e-7 — an order-of-magnitude paraphrase |
| `vv40_cfd_003` | 101.325 kPa | out-of-bundle | standard atmosphere; world knowledge, not in the documents |
| `nasa_cfd_006` | "<2.4%" | derived | observed max 2.3%; a bound stated just above it |

Three derived, one out-of-bundle, **no fabrication**. Worth stating plainly: the
metric cannot separate *derived-and-slightly-wrong* from *fabricated* — the 83%
row is the example, since 20/23 is 87% — so a nonzero ungrounded count is a
prompt to look, not a hallucination count.

## Corrections made while measuring

Recorded because each would have produced a wrong number, and two were mine.

**The probe's label normalisation was a no-op.** It stripped punctuation and
case before comparing, commented "GT labels vs prompt labels differ". They do
not: the two sets match **19/19 exactly**, empty in both directions. Removed.
The useful consequence is that a rules backend emitting the prompt's own factor
labels scores through `score_factors` with **no translation layer**.

**Level was being scored on rows that have no level to assign.** The 60
`not_applicable` rows carry `expected_level: 1`, and `score_factors` scored
level wherever a level existed — mixing "did you assign the right rigour" with
"did you notice this does not apply". Both slices are now reported: over all
scored rows the constant 2 gets exact **0.646** / MAE **0.354**; over assessed
rows only, **0.697** / **0.303**. Assessed-only is the sub-task C figure.

**The `cou_name` match rule accepted a clause.** The fallback took substring
containment in either direction for any expected value over 10 characters, so a
`cou_name` sharing one phrase with the truth passed. Replaced with token-level
F1 at a 0.60 threshold for generative fields. Measured against a real COU
string: exact 1.00 pass, close paraphrase 0.80 pass, **shares-one-clause 0.40
now fails**, unrelated 0.11 fails.

**The groundedness tokeniser read kelvin as a kilo-suffix.** Recorded above in
full because it is the sharpest case: a fix I wrote to remove four false
fabrication reports introduced twelve, and the automated re-check scored it
clean. Hand-reading the rows is what caught it.

**The first contamination guard tested the wrong thing.** It asserted that no
anchor appears in `evidence_keywords`, and immediately blocked its own probe on
"Richardson extrapolation" and "grid convergence index". Those appear in both
places because they are the canonical names — which is *why* Discretization
error recalls at 98%. Convergence on a term of art is the mechanism working, not
a leak. Set overlap cannot distinguish copying from agreement; the guard now
checks **provenance** instead — every anchor must trace back to the prompt file
it claims to come from.

## What is measured, and what is not

Measured: C1, and the controls that make it interpretable.

Not measured: C2 (expanded lexicon), C3 (spaCy rules), C4 (TF-IDF), C5
(embeddings), C6 (NLI), C7 (fine-tuned encoder). C5 is the hypothesis the
investigation turns on — whether `"head rise prediction"` and `"quantity of
interest relevant to the decision"` are close in embedding space on
domain-specific engineering text — and it is untested here.

Not measured, and the gap an examiner reaches first: **any real document.** The
corpus is Claude-generated prose. An LLM extractor can lean on that because it
generalises across phrasing; a lexical extractor cannot borrow the same
assurance, since its score is a direct function of surface form. Whether
synthetic prose flatters or penalises a dictionary is unresolved, and that
ambiguity is itself why this corpus cannot settle the question.
