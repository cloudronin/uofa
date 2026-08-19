# INV-22 — the OOS calibration set contains no case that should pass, so it could not detect a rule that never passes

Status: **OPEN** — measured; the engine defect it hid is fixed, the calibration gap is not
Date: 2026-08-19
Found during: fixing [`OOSEngine.walkSufficiency`](../../src/weakener-engine/src/main/java/net/uofa/oos/OOSEngine.java) (PR #81)
Related: [INV-21](INV-21-claim-node-conventions.md) — the claim interior these rules read is also empty

## The finding in one line

Every one of the 16 OOS calibration packages is an `out_of_scope` case that
should report a gap. Nothing in the set should pass, so a rule that can only
ever report a gap scores perfectly — and 10 of the 16 shipped rules were exactly
that.

## What the set is

Two different things are called "calibration" in `specs/calibration/`, and only
the second is at issue.

**`calibration_set_v1.jsonl` — the judge calibration set.** 30 entries,
hand-annotated with `ground_truth_verdict`, `annotator` and `review_confidence`.
Deliberately balanced: **5 each** of `CORRECT-DETECTION`, `REAL-GAP`,
`GENERATOR-ARTIFACT`, `EXISTING-RULE-MISBEHAVIOR`, `OUT-OF-SCOPE` and
`UNCERTAIN`. This one is well constructed and is not the subject here.

**The OOS rule targets — 16 packages, one per shipped rule.**

| Pack | Packages | Rules |
|---|---|---|
| iso42001 (`cal-aims-001…009`) | 9 | 9 |
| vv40 (`cal-021…025`) | 5 | 5 |
| surrogate (`cal-surr-*`) | 2 | 2 |

Only the 5 vv40 packages appear in the JSONL manifest — they *are* its
`OUT-OF-SCOPE` class. The other 11 are pack-level additions on disk with no
manifest entry, no `ground_truth_verdict`, and no annotator.

## The measurement

| | |
|---|---|
| OOS calibration packages | **16** |
| …that are `out_of_scope` cases | **16** |
| …that should CLEAR — a sufficient bundle, correct verdict "no gap" | **0** |

There is no positive case. The set can measure whether a rule detects a gap. It
cannot measure whether a rule *discriminates*, which is the only thing that
distinguishes a detector from a constant.

## What that hid

`OOSEngine.walkSufficiency` committed to the first triple returned by `find()`
with no backtracking (PR #81). Sufficiency clauses traverse
`hasSupportingEvidence`, which is multi-valued, so multiple evidence variables
in one rule all bound to the same first-returned node.

**10 of the 16 rules require 2 or 3 _distinct_ evidence bindings** — all 9
iso42001 rules and `oos_surr_calibration_provenance_warranted`. Those could only
clear a bundle if a single node carried 2–3 required types at once, which never
happens. They were unconditional gap reporters for any claim they discriminated
on.

The remaining 6 — the 5 vv40 rules and `oos_surr_model_comparison_warranted` —
bind evidence once, so they *could* clear, but the answer depended on Jena's
triple iteration order rather than on the document.

> **Correction.** PR #81 and its commit message state "11 of the 16". The count
> is **10**. The claim's substance is unchanged and the remaining 6 were also
> affected, by the order-dependence rather than by never clearing. The PR body
> has been corrected; the commit message is immutable.

Measured on a bundle carrying all three types
`oos_aims_policy_appropriateness_warranted` asks for — `AIPolicy`,
`OrganizationalPurposeStatement`, `PolicyToPurposeReviewRecord`:

| Engine | Verdict |
|---|---|
| v0.1 | **1 gap — "missing documented review record linking the AI policy to the organizational purpose statement"** |
| fixed | 0 gaps |

The review record is present. That is a false OUT-OF-SCOPE on a bundle that
satisfies the rule completely — and **no package in the calibration set could
have surfaced it**, because none of them is supposed to pass.

## Why every existing signal stayed green

This is the part worth keeping. At v0.1, with 10 of 16 rules structurally unable
to clear:

- **11 / 11 Java JUnit tests passed** — none constructed a sufficient bundle.
- **37 / 37 Python OOS tests passed** — same.
- **The §5.5 byte-identical report regression passed**, which
  `docs/oos_production_v0_1.md` calls load-bearing. It compares reports against a
  pre-v0.2 baseline; the five pinned baselines in
  `tests/fixtures/baseline_reports/` are all `cal-021…025` `out_of_scope` stubs.
  It pins the answer, not the reasoning, so a rule that is right for the wrong
  reason pins clean.
- **All 7 multi-evidence calibration packages produced identical verdicts before
  and after the fix**, which is how PR #81 could truthfully report "no behaviour
  change on the shipped corpus" while the defect was real and reachable.

A detector that only ever says "gap" is indistinguishable from a correct one on
a corpus made entirely of gaps. Every instrument pointed at it agreed, because
every instrument was built from the same corpus.

## The generalisation

This is the same shape as [INV-17](INV-17-prose-versus-property-count.md)'s
standard — *count it before the chapter uses it* — applied to a test set rather
than a claim. A calibration set that contains only one class cannot calibrate;
it can only confirm.

It also rhymes with the argument-layer prototype's own near miss
(`dev/prototypes/argument-layer/RESULTS.md`, experiment 3): W-ARG-02 passed
throughout with an encoding that was measurably broken, and would have shipped
looking correct had it been the only rule tested. Both cases are the same
methodological hole — **a positive result over a one-sided sample is not
evidence**.

## What would close it

1. **One sufficient package per rule — 16 files.** Each carries every evidence
   type its rule requires, with the correct verdict "no gap". Mirrors the
   `OOSEngineTest#clearsABundleThatCarriesEveryRequiredEvidenceType` regression
   test added in PR #81, which is the same idea at unit scale.
2. **Give the 11 unmanifested packages manifest entries** — `ground_truth_verdict`,
   annotator, confidence — so the OOS targets are annotated to the same standard
   as the judge set rather than sitting on disk unannotated.
3. **Re-pin the baseline reports** once (1) exists, so the byte-identical
   regression covers a clearing case and not only gap cases.

Item 1 is the one that matters. Without it the OOS catalog has no test that can
fail when a rule stops discriminating, which is the failure mode that actually
occurred.

## Reproducing

```bash
# 16 OOS calibration packages, all out_of_scope, none expected to clear
ls specs/calibration/packages/ | grep -c out_of_scope   # 16
ls specs/calibration/packages/ | grep -c in_scope       # 0
```

```bash
# the judge set is balanced; the OOS targets are not part of that balance
/Users/vishnu/miniconda3/bin/python -c "
import json,collections
r=[json.loads(l) for l in open('specs/calibration/calibration_set_v1.jsonl') if l.strip()]
print(len(r),'entries'); print(collections.Counter(x['ground_truth_verdict'] for x in r))"
# 30 entries, 5 of each of 6 verdicts
```

```bash
# how many rules need >=2 distinct evidence bindings
/Users/vishnu/miniconda3/bin/python -c "
import re,glob
n=t=0
for f in glob.glob('packs/*/rules/oos/oos_v0.1.rules'):
    for m in re.finditer(r'# sufficiency_starts_at: (\d+)\n\[(\w+):(.*?)\n\]', open(f).read(), re.S):
        suff=re.findall(r'\(\?[^)]*\)', m.group(3))[int(m.group(1))-1:]
        t+=1; n += sum(1 for c in suff if 'hasSupportingEvidence' in c) >= 2
print(n,'of',t)"   # 10 of 16
```

## Coverage statement

Searched: `specs/calibration/` for package inventory and manifest structure; all
three `packs/*/rules/oos/oos_v0.1.rules` for rule count and evidence-binding
arity; `tests/`, `src/uofa_cli/oos/` and the Java test tree for consumers of the
corpus. Not searched: whether the *non*-OOS calibration classes have the same
one-sidedness — the judge set is balanced by verdict, but whether each verdict's
5 packages span both firing and non-firing cases was not checked, and the same
argument would apply if they do not.
