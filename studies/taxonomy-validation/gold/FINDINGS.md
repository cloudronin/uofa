# Gold set: what it validates, and what it cannot

150 cards labeled by the author per
[the instructions](../../../docs/A16_3_gold_labeling_instructions_v0_1.md).
Labels in `gold_labels.csv`; text columns dropped, re-attachable via `row_hash`.

## Quality checks (all pass)

| Check | Result |
|---|---|
| Completeness | 150/150 labeled on all 7 properties, no blanks |
| Valid values | only `present` / `absent` / `unclear` |
| `unclear` budget (§3: amend if >10%) | 1 label total, 0.7% on P2, 0% elsewhere |
| §2 consistency (P1 absent ⇒ P2–P7 absent) | no violations |
| **A3 detector, negative calls** | **0 false negatives** — of 30 `no-eval` cards, none carried a score |

The 47 eval-bearing cards with no score are not detector errors: a card can have
an evaluation section that states no number. The detector claims a section
exists, not that a score does.

The single `unclear` is the intended use — "large variation… 5 different seeds",
qualitative with no quantity attached.

## The finding: four properties have zero positive instances

| Property | present | absent | unclear |
|---|---|---|---|
| P1 score | **73** | 77 | 0 |
| P3 sampling | 3 | 147 | 0 |
| P4 determinism | 3 | 147 | 0 |
| P2 uncertainty | **0** | 149 | 1 |
| P5 null baseline | **0** | 150 | 0 |
| P6 claimed COU | **0** | 150 | 0 |
| P7 confound control | **0** | 150 | 0 |

This is not a labeling problem. It is what the population contains.

### Why it breaks validation for those four

A Group-B rule fires to mean *the property is absent*. So per gold label:

- gold `absent` → the rule **should** fire
- gold `present` → the rule should **not** fire

With zero `present` labels, **every row is a "should fire" case.** Therefore:

- **sensitivity** (fires when it should) — measurable, and would be 1.00
- **specificity** (refrains when it should) — **not measurable**, no such cases

Specificity is exactly what distinguishes a working rule from one that fires
unconditionally. **Both score 1.00 on this gold set.** A16.7's criteria
(precision ≥ 0.90, recall ≥ 0.80) would be satisfied trivially by a rule with no
discriminating power at all.

This is the `PENDING_EMISSION` problem — "a structurally always-true firing
condition has no defined precision" — arriving from the **data** side rather than
the emission side. The register guaranteed the rules *can* discriminate; it
cannot guarantee the population *lets them*.

### Scale required

Rule of three: 0 positives in 150 puts the true rate at **≤ 2%** (95%). Roughly
**n ≥ 500** would be needed to expect ~10 positive instances per property, and
that is a floor, not a design.

## What this gold set does validate

- **P1 (score)** — 73/77 split, fully validatable.
- **P3, P4** — 3 positives each. Thin, and any specificity estimate carries an
  interval wide enough to say so.
- **The A3 detector's negative calls** — 0 false negatives on 30 cards, the
  direction where a mistake claims a clean absence over evidence that exists.

## What needs a ruling

Options, none taken here; the freeze is untouched:

1. **Enrich for positives.** Purposive sampling for cards that DO state
   uncertainty / baselines / COU, labeled as a second stratum. Recovers
   specificity; the enriched stratum is not a prevalence estimate and must be
   reported separately.
2. **Scale the gold set** toward n ≥ 500. Expensive in the binding resource
   (author time) and still yields single-digit positives per property.
3. **Settle these four on the deterministic path instead.** Their firing is
   mechanically verifiable against constructed fixtures, as W-EV-SUB-08's is.
   The panel then validates P1, P3, P4 and the detector.
4. **Report them as unvalidatable at this scale**, with the prevalence finding
   (0/150) as the result — which is itself the FAccT paper's claim.

Option 4 is not a failure mode. "Four of seven interpretability-enabling
properties appear in zero of 150 cards" is a stronger empirical statement than
any precision figure, and it is the two-source convergence result
(`studies/cohort-2026-08`, n=427 furnished; `studies/card-eval-reporting-2026-08`,
n=49) confirmed at gold-label quality on a third population.
