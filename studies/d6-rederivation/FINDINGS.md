# D6 re-derivation: 384/427 reproduces, and the equality holds both ways

Date: 2026-08-16
Ruling: Decision Record ruling 10 — **measure, do not reword** (~3h), re-derive 384/427
from committed artifacts and verify the equality claim in **both** directions.
Status: **COMPLETE. D6 drafting is unblocked.**
Script: `rederive.py` · Record: `results.json`
(`sha256:bdee3cdc…`) · Exit code 0 = all three checks passed.

Pinned input: `cloudronin/raidex-results` at revision
`d459f536b506dc5f82355891db19f599f374a92c`, read from the local snapshot. The script
**refuses to run against any other revision** rather than silently re-deriving against
whatever the dataset holds today — re-derivation against a moved input is not
re-derivation.

## Result

| Check | Claimed | Measured | |
|---|---|---|---|
| Validation results | 427 | **427** | ✓ |
| W-AL-01 fires | 384 | **384** | ✓ |
| W-AL-01 clears | 43 | **43** | ✓ |
| Models | 43 | **43** | ✓ |
| Direction 1 — cleared ⟹ carries stated uncertainty | asserted | **HOLDS**, 0 counterexamples | ✓ |
| Direction 2 — carries stated uncertainty ⟹ cleared | **untested** | **HOLDS**, 0 counterexamples | ✓ |

The number was prose arithmetic in `studies/cohort-2026-08/README.md`. It is now
machine-re-derivable from a pinned artifact, which is what D7's **Demonstrated** rung
requires. U-INV-3's objection is discharged.

## Why the converse is not circular

Asking the furnisher whether it set `hasUncertaintyQuantification`, then asking whether
W-AL-01 cleared, is **one question asked twice**: the rule is `noValue` on exactly that
property, so the two answers cannot disagree. A converse test built that way would pass
unconditionally and prove nothing.

So this script defines *"carries a stated uncertainty"* **without consulting the
furnisher's predicate**. It walks each result's raw block for stderr-shaped keys and
classifies every value a reader would encounter — including the ones the furnisher
discards. A result holding a stderr that a reader would call stated, but which the
furnisher declined, is a converse failure, and the script names the model and result.

**The specific failure mode it was built to catch:** `_as_number`
(`furnishers/raidex.py:117-126`) accepts `int`/`float` only and returns `None` for
**every** string, numeric ones included. A cohort publishing `"acc_stderr": "0.023"`
would state uncertainty in a form any reader would accept and still be fired on.

## What the cohort actually contains

| Reader-classification of stderr-shaped values | Count |
|---|---|
| `number` (real int/float) | **43** |
| `sentinel` (explicit "N/A" etc.) | **1118** |
| `numeric-string` (the failure mode) | **0** |
| `other` | 0 |

And the shape of the 384 fired-on results:

| How a fired-on result declines uncertainty | Count |
|---|---|
| **Silent — no stderr-shaped key at all** | **384** |
| Explicit "N/A" under a stderr-shaped key | 0 |

Two things follow, and both belong in the §4.x prose.

**1. The equality holds, and its scope is now known.** Direction 2 holds because the
cohort contains **zero** numeric-string stderrs — not because the rule captures the
concept of "stated uncertainty" exhaustively. A cohort serializing stderrs as strings
would break it. The claim is true, verified, and **contingent on a serialization
property of this corpus**, which is a more precise thing to write than an unqualified
"exactly."

**2. W-AL-01 fires on silence, not on refusal.** All 384 fired-on results have no
uncertainty field whatsoever. None says "N/A". Conversely all 1118 sentinels sit
**inside the 43 cleared results** — 1118 / 43 = exactly 26 per result, bbq's
sub-scores. So the single constituent that reports a real standard error is also the
only one explicit about where it cannot.

That asymmetry is the invariance demonstration in miniature, and it is stronger than
the current sentence: the rule is not penalising a corpus for saying "unavailable." It
is distinguishing **one furnisher that reports uncertainty from eight that do not
mention it**, on evidence in a domain — LLM benchmark results — that the rule was
never written for. An assessment that fired uniformly would be indistinguishable from
one that had not read the evidence; this one discriminates 43 from 384 on a property
it reads the same way in a blood-pump CFD study.

## Effect on the manuscript

D6's §4.x sentence can go on the **Demonstrated** rung as ruled. Two adjustments the
measurement earns:

- Keep "clears exactly the results carrying real uncertainty" — it is now **verified in
  both directions**, not asserted — but attach the scope: verified against this pinned
  revision, where uncertainty is either a float or absent.
- Prefer *"the 384 results carry no uncertainty field"* over any phrasing implying the
  corpus reports uncertainty as unavailable. The 384 are silent; the explicit "N/A"s
  are all in the cleared group.

## Reproducing

```bash
python studies/d6-rederivation/rederive.py
```

Exit code 0 iff the arithmetic reproduces **and** both directions hold. Any of the
three failing is a nonzero exit and a named counterexample list, not a silent
disagreement.

## Coverage statement

**Checked.** All 43 model records at the pinned revision; all 427 furnished validation
results; every stderr-shaped key in every result's raw block, classified independently
of the furnisher's predicate; both directions of the equality with counterexample
capture.

**Not checked.** Whether the *composite* records' uncertainty semantics differ from
constituents' (they carry no stderr-shaped key either way, so the question does not
affect these numbers). Whether uncertainty is stated anywhere outside a stderr-shaped
key — a confidence interval or a variance under a differently-named field would be
invisible to this scan, as it is to the furnisher. That is a shared blind spot of the
rule and the test, and it is the honest limit of this verification.
