---
title: Evidence sufficiency
description: A benchmark score with no uncertainty, no null baseline and no stated context of use is a number, not evidence. What has to accompany a result before it can inform a decision.
---

A model card reports `MMLU 78.2`. A reader takes it as evidence the model is
capable. But the number alone does not support that, and the reasons are
specific rather than pedantic.

**How much would it move if you ran it again?** No uncertainty is stated, so a
78.2 and a 76.9 are indistinguishable — including from each other, and from the
same model measured twice.

**What does 78.2 mean?** MMLU is four-option multiple choice, so chance is 25.
Without that anchor a reader cannot tell a strong result from a weak one, and
"above chance" is not the same claim as "useful".

**Was it the same evaluation?** Temperature, seed, prompt template and repeat
policy all move a score. Unstated, the number cannot be reproduced even in
principle.

**Evidence for what?** A score supports a *use*. A card that reports numbers
without saying what decision they are meant to inform leaves the reader to
supply that connection themselves — and readers supply generous ones.

## The distinction this rests on

The [weakener catalog](/reference/catalog/) is mostly about assurance packages
someone authored deliberately. Evidence sufficiency is narrower and applies to
any reported result:

> **Completeness** asks whether a thing was documented.
> **Sufficiency** asks whether what was documented can carry the weight put on it.

A card can be entirely complete — every field filled, every section present —
and still report numbers that cannot support the claims made from them. The two
are independent, which is why the `model-credibility` pack keeps them in
[separate report sections](/reference/packs/model-credibility/) with a structural
firewall between them.

## Why this is not a documentation-quality complaint

The properties are the ones the reader needs to *interpret* the result, not the
ones that make a card look thorough. Each maps to a defeater: a specific reason
the conclusion might not follow from the evidence, drawn from ASME V&V 40's
treatment of simulation validation and from published work on benchmark
reporting failures.

That is also why an absent property is reported as an absence rather than a
fault. "No uncertainty is stated" is a fact about the record. It is not an
accusation that the model is bad, or that its authors were careless — most cards
omit these because the surrounding practice does, not through any individual
lapse.

## Reported, and furnished

A score published by a model's own authors and a score from an independent run
are different claims about the same subject, so they are recorded differently.

When both exist for one benchmark and they disagree beyond tolerance, that is a
finding — but a carefully bounded one. **It establishes that the record is
inconsistent, not which number is right.** An independent run can be wrong; a
published number can be stale; the benchmark itself may have moved. The finding
is about the disagreement, and the wording does not reach further than that.

## What this does not do

It assigns no score and ranks nothing. There is no composite credibility number,
and none is planned — a single figure would invite exactly the comparison across
models that these properties exist to make impossible without reading the
evidence.

It also does not assert that a card lacking these properties is untrustworthy.
It asserts that a reader cannot tell, which is a different and more defensible
claim.

---

**See also:** the
[model-credibility pack](/reference/packs/model-credibility/) for the ten
patterns and their grounding, and [weakeners](/concepts/weakeners/) for how a
defeater is expressed as a rule.
