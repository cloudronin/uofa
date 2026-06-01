# Addendum — If Stock 4B Clears the Explanation Bar (Disposition Gate)

> Contingency branch of the bakeoff **Gate** in `docs/UofA_PostRefactor_Phase_A_Implementation_Plan.md`. It applies **only** if the P0 bakeoff verdict is "stock Qwen-4b clears the explanation bars." If 4b fails, ignore this note and follow the main plan's fail branch (escalate to stock 7-8B first, per the gate-model fix, before concluding the fine-tune is justified).

## Why this note exists

The P0 gate tests the **explanation** task: decode a firing, say what it means, recommend an action, report confidence. If stock 4b clears that, the naive reading is "the SLM moat is dead, ship the stock-model appliance on the convention moat." That reading is correct about the explanation layer but it is **incomplete about the moat**, and acting on the naive reading would either (a) prematurely kill a moat leg that was never actually tested, or (b) tempt a contrived "harder explanation task" built only to give the model something to beat. Both are wrong. This note specifies the correct move.

## The two readings of a 4b-clears result

**What it definitively kills.** If 4b clears explanation, the **explanation layer is commodity.** A stock model anyone can pull does the decode-and-recommend job. That means the explainer was never going to be defensible *as an explainer*, fine-tuned or not, because a competitor's stock model does the same thing. Do not move the moat to "defend the appliance's explanation stage" — there is nothing to defend there.

**What it does NOT test.** Explanation maps a firing to a *known* meaning, which is exactly why a stock model with the catalog in context can do it. It says nothing about the task one level up: **disposition under uncertainty** — choosing *which* of the coherent actions is right for this COU's risk posture and this domain's idioms, and how confident to be. That task depends on the tacit practitioner-correction knowledge that is in **no** stock model's training and in **none** of the UofA publications. A stock model clearing explanation therefore carries **zero information** about whether it clears disposition.

**The correct conclusion:** explanation was never the moat. **Disposition is.** The moat was always meant to live in the §5B selection-among-coherent-actions (the human-adjudicated residue) and the calibration that makes confidence trustworthy enough to gate action. So a 4b-clears-explanation result is an instruction to **move the gate up one level**, not to delete the SLM branch.

## The rule (refuse the trap)

Do **not** make the explanation task artificially harder so the small model struggles and the fine-tune looks justified. Reverse-engineering a hard problem to fit the desired moat fails the same honesty test as a rigged bakeoff.

**Test for any "harder task":** does a regulated buyer actually need this harder thing done? If yes, it is a legitimate gate. If it exists only to give the model a job, it is the trap. Disposition-under-uncertainty passes this test (a submitter genuinely needs the right action chosen and scoped under a defensible confidence bound). A more elaborate explanation task does not.

## The disposition gate (the legitimate harder task)

Run the **same stock-vs-target bakeoff structure** as P0, but on the disposition task instead of the explanation task.

### Task definition
Input: a fired weakener + measures + catalog definition + COU context (same retrieval surface as P0). Output: the **selected action class** from the §5B D-category-keyed vocabulary, its **structured parameters** (scope, against-what, blocks-what), and a **calibrated confidence**. The model is no longer decoding a known meaning; it is *choosing among coherent actions* and *scoping* the choice.

### The honest catch — this gate is NOT free
The explanation gate was cheap because explanation answer keys could be grounded in solver truth and source papers. **Disposition answer keys cannot.** The gold action + correct confidence for the hard cases need either **expert adjudication** or the **verified-mitigation-outcome (Tier-3) data** that is adoption-gated and does not exist yet. So testing the disposition task requires *building a small disposition-labeled hard slice*, and that build is itself a piece of the moat-corpus work the gate was meant to scope.

This is the clarifying finding, not a dead end: the disposition task's ground truth **is** the moat asset, which is *why* it is defensible. You cannot cheaply test the hard task the way you tested the easy one, because the hard task's answer key is the thing a competitor cannot reproduce.

### What to build (minimal, hardest cells only)
A small **disposition-labeled slice**, deliberately concentrated on the cells where disposition is genuinely hard — do **not** spend on easy cells:
- The **dangerous-OK** dispositions (global-pass / local-inadequate, e.g. the §5A CarBench wheel-housing pattern): the action is not obvious from the firing alone.
- The **multi-coherent-action** rows (§5B): cases where the D-category admits more than one coherent class and the *selection* is the tacit judgment.
- A few **controls** where the correct disposition is "accept / no action," so the gate measures over-action as well as under-action.

Each row carries:
- `gold_action`: selected class (§5B vocabulary) + structured parameters + `coherent_alternatives` + `selection_basis: adjudicated`.
- `acceptable_confidence`: the range a correct disposition should land in.
- `forbidden_claims`: same firewall list as P0 (no correctness verdict, no relabeling a measurement as a pass).
- `label_provenance`: **expert-adjudicated** for the selection; solver-derived for any factual parameters. Provenance is per-field (SLM spec §5B field-level provenance). **Never** sourced from the pipeline or a frontier draft (tautology guards, SLM spec §5).

Target size: a few dozen hard-cell rows is enough to separate the models on this gate. This is intentionally a *small expensive slice*, not the full corpus — its only job is to answer the gate question.

### The scorecard (reuse, re-pointed)
Reuse the P0 scorecard machinery (`harness/bakeoff/score.py`), re-pointed at the disposition output:
- **Action correctness**: selected class matches gold (bucket: correct / partial / wrong / **harmful**). A *harmful* disposition (acts when it should restrict, or restricts wrongly) is the headline danger.
- **Selection quality on multi-coherent rows**: did the model pick the adjudicated-best class, or a merely-coherent alternative? This is where tacit knowledge shows up.
- **Calibration / selective risk-coverage**: same α (start 2%), same headline metric. Disposition is the task the auto-act phase would eventually rest on, so the selective curve here is the one that matters most.
- Pin the **confidence elicitation method** (verbalized vs logprobs) in `score.py` and use it identically for stock and target, or the calibration comparison is meaningless.

### Read as the gate
- **Stock 4b clears the disposition hard cells too** → the task is commodity all the way up. The SLM leg is genuinely dead. You learned it for the cost of a small hard slice, not a full corpus. Redirect fully to the convention moat (see below).
- **Stock fails disposition** → you have found the task where the trained model and the proprietary corpus earn their keep. The corpus build is now justified **by evidence**, and the disposition slice you just built is its seed. Proceed to the SLM corpus build (`UofA_Explainer_SLM…` spec), scoped to the disposition task, not the explanation task.

## If the SLM leg is genuinely dead (both gates clear)

A 4b-clears-everything world means the explainer (and the disposition layer) is commodity. The moat then lives **entirely** in the layers a stock model does not touch:
- **Convention moat:** open core + coverage methodology (C1) + catalog + signed-evidence format. Land Paper A so the coverage methodology is the cited definition of comprehensiveness; freeze the evidence format as an independently citable spec; publish the catalog as a versioned reference; anchor to VVUQ 70 and the standards channel. None of this depends on a model advantage.
- **Deployment lock:** the air-gapped, possess-and-run appliance emitting the cited standard format is still something frontier-dependent and platform competitors cannot match for the regulated buyer.

The appliance still ships — but as the carrier of the convention moat and the deployment lock, with a **commodity explainer that is table stakes, not the differentiator.** Do not price or position the explainer as the moat in this world.

## Guard against the false-positive kill

Before accepting **either** gate as a kill, segment the result by the **hard-core strata**, not the aggregate. The danger is an aggregate pass that masks hard-case failure: the model clears the easy bulk and quietly fails the dangerous-OK and multi-coherent cells — the exact cells the moat would live in. If the aggregate passes but the hard cells fail, the **slice was too easy**, not the task. That is a "slice underpowered, rebuild the hard cells" finding, not a "task is commodity" finding. Always read the gate on the hard-core strata.

## One-line decision tree

```
P0 explanation gate:
  4b fails        → escalate to stock 7-8B (main plan), then fine-tune only if 7-8B also fails
  4b clears       → segment by hard-core strata:
                      hard cells fail too → slice too easy; rebuild hard cells; rerun
                      hard cells clear    → explanation is commodity → run DISPOSITION GATE:
                          build small expert-adjudicated hard-cell disposition slice
                          run stock-vs-target bakeoff on disposition task
                            stock clears disposition hard cells → SLM leg dead → convention + deployment moat only
                            stock fails disposition             → corpus build justified by evidence;
                                                                  this slice is its seed; build to the DISPOSITION task
```

## Scope discipline (unchanged)

The disposition gate is still a **gate**, not a green light to build. It costs one small expensive slice and answers one question. The full corpus build, fine-tune, conformal calibration, and any auto-act work stay parked until the disposition gate says the trained model earns its keep. And note: the disposition task is adjacent to the parked **auto-act** Product B line — testing whether a model *can* choose actions well is not the same as shipping a model that *acts*. Auto-act remains parked behind its own Tier-3 data dependency regardless of how the disposition gate reads.
