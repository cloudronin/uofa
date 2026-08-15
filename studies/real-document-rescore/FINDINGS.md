# The H2 replacement gate does not clear on real documents

Run against `docs/decisions/2026-08-14-h2-replacement-thresholds.md`, committed
**before** this ran. All six annotated papers, pooled.

## Gate verdict

| condition | threshold | measured | |
|---|---|---|---|
| 1. margin over permutation null | ≥ 0.25 **and** ≥ 3 sd | **+0.044 / 0.5 sd** | **FAIL** |
| 2. no null reaches the candidate | absolute | 0.000 | PASS |
| 3. leakage detector: below the 0.714 ceiling | — | 0.054 | no leakage |
| 4. measured on the real corpus | — | yes | PASS |

**The H2 attribution replacement gate is not cleared.**

Per the declaration, and quoted so nobody has to go looking for it: *"A failure
is a result, not a prompt to look for a third metric. If the conjunction does
not clear on real documents, the finding is that H2 cannot currently be
supported on attribution, and that is what gets written."*

## The measurement

    real-document candidate   0.0536   (3/56)
    Wilson 95% CI            [0.018, 0.146]
    permutation null          0.0098   (sd 0.0950)
    worst null, any length    0.0000

| paper | pack | hits | sentences |
|---|---|---|---|
| opensim | nasa-7009b | 0/7 | 521 |
| elemance | nasa-7009b | 0/6 | 1319 |
| **ared** | nasa-7009b | **3/7** | 205 |
| bologna | vv40 | 0/13 | 895 |
| nagaraja | vv40 | 0/12 | 960 |
| morrison | vv40 | 0/11 | 676 |

**Every hit comes from one paper**, and it is the shortest one — 205 sentences
against 521–1319 for the rest. Five of six papers score zero. On 56 factors with
3 hits the Wilson interval spans 0.018 to 0.146, so the point estimate is not
worth more than one significant figure, and no single-paper rate means anything:
`nagaraja` scored 1/12 in the previous run and 0/12 in this one, same paper,
same pack, different extraction.

## What capability exists beneath the failed gate

Stated second, deliberately. Leading with it would read as a rescue.

| | candidate | permutation null | lift |
|---|---|---|---|
| synthetic | 0.4524 | 0.0526 | **8.6×** |
| real | 0.0536 | 0.0098 | **5.5×** |

The permutation null is the right reference for comparing the two worlds: it is
computed on each run's own rationales with labels shuffled, so it absorbs gold
density and the multi-constituent structure automatically. Raw rates differ 8.4×;
lift differs 1.6×.

So the rule does discriminate on real prose — 5.5× its own chance level, with no
null reaching it at any rationale length. **It does not discriminate enough to
gate a hypothesis on.** Both are true at once, and the gate's verdict is the
operative one: 0.5 sd against a required 3.

Why real is harder is structural, not mysterious. A real paper's annotation gives
roughly **one gold sentence per factor out of 500–1300**; on bologna, 13 factors
with 1 gold sentence each in 895 sentences. Synthetic gold sets carry several
sentences per factor out of a few hundred.

## Two measurement errors found on the way, one by the gate itself

**The first version was circular** and scored 0.8545 with three of six papers at
exactly 1.000 — it compared the annotation's evidence text against gold derived
from that same text. Condition 3 caught it. That condition's general statement
is now in the decisions doc: a score above the human agreement ceiling is
evidence of leakage, not excellence, because a perfect instrument cannot exceed
the agreement of the humans defining truth.

**The second had a vocabulary bug** and scored only 3 of 6 papers. The three
`cas_variant` papers key their gold by published vocabulary
(`Code/solution verification`, `Input pedigree`) while extraction emits pack
names, so all three returned n=0. Two repairs, both defined by pre-existing gold
structure: apply `cas_mapping.VARIANTS` as `v1_router_comparison` already does,
and extract those three under **nasa-7009b** rather than vv40 — their gold
includes NASA-only factors (`Data pedigree`, `Results robustness`) that a V&V 40
extraction cannot produce at all.

**The thresholds did not move**, before or after either repair. That is what
makes this number legitimate whichever way it landed.

## Recorded, not corrected

A published factor counts as hit when **any** of its pack constituents'
rationales localises into its gold sentences. `Verification` has four
constituents and gets four attempts where a one-to-one factor gets one. Left as
is because `v1_router_comparison` scores the same structure the same way and
changing it here would make the two incomparable — but it inflates the candidate
relative to a strict one-to-one reading, and the permutation null absorbs it
only partially.

## Limits

- **n = 56 factors, 3 hits.** Small enough that the CI is the honest summary.
- **One annotator**, bounded at 0.714 real-document agreement.
- **Single extraction run per paper**, no seed control, and run-to-run variance
  is visible at this scale (`nagaraja` 1/12 → 0/12).
- Everything carried from Phase 3: the +0.13 residual quoting advantage, the
  furniture-filtered gold sets, the 212 dropped synthetic rows.

## What H2 can now honestly claim

Not written as the conclusion — that is for the praxis text — but the shape the
evidence supports:

- **The detection claim is supported at ceiling and is non-discriminating.**
  Mean F1 0.9637 / 0.9544, per-factor 1.000 across all nineteen, zero crashes —
  and `control_constant_list` scores identically, delta +0.0000. Reported with
  the null beside it, always.
- **The attribution replacement gate was declared with numbers, measured on real
  documents, and not cleared.** Margin 0.5 sd against a required 3.
- **Attribution capability is characterised but below the declared bar**: 5.5×
  its permutation null on real documents, 8.6× on synthetic, no null reaching it
  at any length.

That is a narrower supported hypothesis with its instruments' limits published.
Every number in it survived an attempt to kill it — the detection gate survived
a null that tied it, the attribution rule survived a shotgun that used to beat
it, and this figure survived two measurement bugs and a leakage detector.

What is **not** available is a third metric. The sequence detection F1 →
attribution → something-else would be gate-shopping with extra steps, and
numbering the conjunction before running it was precisely so that there is
nowhere to move to now.
