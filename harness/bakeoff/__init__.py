"""Bakeoff harness — the post-refactor **Gate** (stock-local floor test).

Adapts the SLM spec's §3.2 scorecard + §8 kill criteria to a *stock-local floor
against absolute bars* (does the model the regulated buyer can self-host clear
the dangerous-error + selective-coverage bars), NOT the frontier non-inferiority
comparison (that is the deferred SLM P5). See
``docs/UofA_PostRefactor_Phase_A_Implementation_Plan.md`` (Gate) and the
disposition-gate addendum.

- ``score`` — the answer-key scorecard: §3.2 metric components + the headline
  selective risk-coverage, re-pointable from the explanation task to the
  disposition task, always segmented by the hard-core strata.
- ``run_p0`` — the thin runner: build the retrieval prompt per row, generate with
  the stock model (Ollama/Qwen), normalize the structured answer for scoring.
"""
