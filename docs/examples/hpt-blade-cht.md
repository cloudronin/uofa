# Live Demo: HPT Blade CHT (NASA-STD-7009B, Aerospace)

The `packs/nasa-7009b/examples/aerospace/` directory contains a parallel NASA-STD-7009B case study — an HPT turbine-blade conjugate heat transfer CFD model assessed for two operating points:

- **COU1** (take-off transient, MRL 3) → Decision: **Accepted with conditions**
- **COU2** (cruise steady-state, MRL 4) → Decision: **Not accepted**

Same CFD model, same cascade-rig validation data, re-purposed for a different operating regime — reproducing the Morrison divergence mechanism in aerospace. The bundles ship as zipped evidence folders (10 docs each — narrative DOCX, CFX solver settings, cascade CSVs, board minutes, decision rationale PDFs), so you can exercise the full `extract → import → rules` pipeline end-to-end on real input.

## End-to-end roundtrip on COU1

```bash
# 1. Extract: LLM reads 10 evidence documents, produces a pre-filled 19-factor xlsx
uofa extract tests/fixtures/extract/aero-evidence-cou1 \
  --pack nasa-7009b --model ollama/qwen3.5:4b -o /tmp/aero-cou1.xlsx

# 2. Import: convert the xlsx to signed JSON-LD
uofa import /tmp/aero-cou1.xlsx --pack nasa-7009b -o /tmp/aero-cou1.jsonld

# 3. Rules: run the Jena weakener engine, write the reasoned jsonld
uofa rules /tmp/aero-cou1.jsonld --pack nasa-7009b \
  --format jsonld -o /tmp/aero-cou1-reasoned.jsonld --build
```

The pack ships pre-computed reasoned outputs so you can skip to the interesting part:

```bash
# COU1 (Accepted) — W-AR-02 fires on narrative-stated level gaps
uofa rules packs/nasa-7009b/examples/aerospace/uofa-aero-cou1-nasa7009b.jsonld --pack nasa-7009b

# COU2 (Not Accepted) — W-AR-02 stays at zero despite 4+ not-assessed factors
uofa rules packs/nasa-7009b/examples/aerospace/uofa-aero-cou2-nasa7009b.jsonld --pack nasa-7009b
```

## The divergence

| Pattern | COU1 (Accepted) | COU2 (Not Accepted) |
|---|---|---|
| **W-AR-02** (accept-despite-gap) | **4 fires** on level gaps | **0 fires** (hard gate) |
| W-EP-04 (not-assessed at MRL>2) | 1 | 4 |
| COMPOUND-01 (Critical + High) | 6 | 5 |
| W-NASA-02/03/06 (missing evidence linkage) | 1 each | 1 each |
| Total weakeners | 17 | 20 |
| Distinct patterns | 9 | 8 |

**Why this matters:** W-AR-02 (the rebutting-defeater rule) fires *only* when a decision says `Accepted` AND any factor has `achievedLevel < requiredLevel`. Flipping the decision to `Not accepted` disarms every instance of this rule — even though COU2 actually has *more* credibility gaps than COU1. That's the C3 rule engine correctly modeling the argument: a not-accepted decision has no "contradictory result ignored" to defeat. The same mechanism is visible in Morrison; here it repeats in aerospace.

## Reproduce the accuracy numbers

```bash
# Factor F1 + weakener gate scoring, logs to dev/tools/scripts/extract_accuracy_log.jsonl
python dev/tools/scripts/score_extraction.py --pack nasa-7009b --case cou1 \
  --model ollama/qwen3.5:4b --prompt-version v3-nasa-aero
python dev/tools/scripts/score_extraction.py --pack nasa-7009b --case cou2 \
  --model ollama/qwen3.5:4b --prompt-version v3-nasa-aero
```

The scorer runs `extract → import → rules` end-to-end and asserts gates from `tests/fixtures/extract/ground_truth/aero-cou{1,2}-nasa7009b.json`. The hard gate for COU2 is `W-AR-02 count == 0`; if it ever fires, either the extracted decision outcome isn't `"Not accepted"` or the rule engine is mis-matching. Most recent live run: COU1 F1 = 0.97, COU2 F1 = 0.85, both weakener gates pass.
