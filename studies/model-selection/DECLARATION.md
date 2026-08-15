# Extraction model selection: the full scorecard, declared first

Authorized 2026-08-15. Written **before any arm runs**. This document sets the
candidates, the bar and the verdict logic; the runner reports against them and
does not set them.

## Why this study exists

`studies/specificity-discriminator/` established a **measured tradeoff frontier
with no current point on the right side of it**: the C3 migration traded
checkable specificity for grounding and coverage. Qwen produces ten times the
checkable content and one in ten of its claims does not ground; Llama grounds
everything and produces almost nothing checkable. **Neither clears the
conjunction.**

Prompt has been refuted twice (the pack split, and Q2's direct intervention
which *halved* density). Temperature is closed — it moves the same direction in
both models and lowering it degrades distinctness. What is left is the model.

## Candidates — four, fixed

| # | arm | model identifier | backend | why it is here |
|---|---|---|---|---|
| 1 | **local-4b** | `qwen3.5:4b` | ollama | density champion, incumbent before the migration |
| 2 | **incumbent** | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | openai-compatible @ Together | the incumbent |
| 3 | **family-72b** | `Qwen/Qwen2.5-72B-Instruct-Turbo` | openai-compatible @ Together | **its own axis**: is density a *family* trait or a *small-model* trait? Same family as arm 1, 18× the parameters, same hosted path as arm 2 — so it separates family from scale from serving. |
| 4 | **frontier** | `claude-sonnet-5-2026` | anthropic | the backend `docs/llm-config.md` already names. Makes this a **qualification run for the configuration uofa would actually ship**, not a curiosity. |

Arm 3 resolved by probing the Together model list rather than assumed;
`Qwen/Qwen2.5-72B-Instruct-Turbo` is the mid-size qwen-family instruct model
available on the path arm 2 already uses.

**No candidate is added after seeing results.** If an arm cannot run — model
unavailable, key missing, budget — the honest outcome is that **that arm did not
run**, recorded as such, and the verdict is computed over the arms that did with
the absence stated. Substituting a different model mid-study would change the
question.

## The bar — the full scorecard, not one clause

A candidate passes only by clearing **all** of:

1. **The Q2 conjunction** — claim density ≥ 0.40 **and** groundedness ≥ 0.98
   **and** ungrounded triage set ≤ 4
2. **Detection F1 within 0.004 of the incumbent** — the demonstrated noise floor
   of this corpus. A candidate that recovers density by losing factor detection
   has traded one failure for another.
3. **Coverage ≥ 0.95**

**Measured on BOTH corpora**, and **the real six papers decide** per the standing
rule: paired synthetic and real figures are inseparable in every citation, and
where they disagree the real number is the result.

Qwen's 0.420 density is **synthetic-only**. Its real-document density is
unmeasured, and this study measures it. That gap is the reason the incumbent's
apparent challenger cannot be adopted on the numbers currently in hand.

## Verdict logic — every outcome named in advance, symmetric for the frontier arm

**(a) A candidate clears the conjunction** on real documents. Adoption becomes a
cost-and-availability decision, and the cost column below is what it is decided
against.

**(b) The frontier arm lands on the same specificity/grounding tradeoff curve as
the others.** This *upgrades* the finding rather than being a null: checkable
specificity trades against grounding across three model classes spanning two
orders of magnitude of capacity, which makes it **construct-shaped rather than
capacity-shaped**. Consistent with the qualification-table result where frontier
models failed the four-property extraction worse than expected.

**(c) A different tradeoff point that still fails the conjunction.** The frontier
arm sits off the curve — better on both axes, or better on one without the usual
cost — but does not clear the bar. Records where the frontier is without
licensing adoption.

**(d) No candidate clears.** **Named in advance as legitimate and likely.** That
is a finding about the tooling landscape, not a failure of the study: it would
say the property uofa needs from an extractor is not currently supplied by any
of four models across two orders of magnitude, and that is worth writing down.

## Carried rules

**Pin everything, per row.** Model identifier, prompt hash (the current reverted
prompts — the Q2 intervention stays out), temperature, max_tokens. A
qualification row whose configuration is not reconstructable is not a
qualification row.

**Cost per document lands in the qualification row, next to the pin.** Same
honesty as the reasoning-model exclusion. **A frontier extractor clearing the
bar at 100× the 4B's cost is itself a tradeoff finding**, and burying it would
make the scorecard misleading in the direction of the most expensive option.

**The triple reports together everywhere, never a lone clause.** The correction
in `studies/specificity-discriminator/` — where "qwen clears the threshold" was
written on the strength of one clause of three — is the standing example, and it
is cited rather than re-derived.

**Budget.** Hosted arms against the existing cap. The 4B rows already exist
where reusable at identical config; they are reused rather than re-run, and any
row that is reused says so.

## Boundary — stated once, and it governs

**The praxis ships with the H2 result as written.**

If a candidate clears the conjunction on real documents, re-measuring against the
**unchanged** H2 gate is legitimate engineering — same bar, both results reported
— but it is **papers-track**. No re-attempt is folded into the defense window,
where it would read as thrashing after a failed gate.

The narrowed conclusion is the defense artifact. Model selection is its **named
future work**, and the praxis text may say exactly that in one sentence.
