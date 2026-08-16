# Disaggregate before you conclude

**Date:** 2026-08-15
**Status:** stated principle, for the methods chapter
**Instances:** 1–6 from a single working day, 2026-08-14/15; 7 added 2026-08-16

## The principle

**Every wrong conclusion this project reached in a day was a plausible reading
of a subset that happened to agree with it. Every one was caught by splitting
the population, not by more analysis of the same rows.**

The failure has a consistent shape. A pooled number, or a number from the first
few cases looked at, supports an explanation. The explanation is reasonable, it
accounts for what is visible, and there is no internal signal that anything is
missing — because the rows that would contradict it are averaged in, or were
never opened. More analysis of the same data cannot recover them. Only
partitioning can: by pack, by document, by test, by corpus, by which of six
tests actually failed.

The corollary is procedural rather than analytical. **Before concluding, ask what
partition of this population would separate my explanation from its
alternatives, and compute it.** It is usually cheap — six of the seven instances
below cost nothing but a `groupby` or a search.

## Worked instances

### 1. The routing bug, found by being wrong about prompt placement

The hypothesis was that "Include ALL 19 factors" sat 120 lines below the factor
list and was being skimmed — the same failure mode as the shopping-list defect.
Testing it meant partitioning by *prompt layout*: arm A the shipped prompt, arm
B with the instruction relocated.

**Both arms returned 19 of 19.** The hypothesis was wrong, and being wrong
located the actual bug: the prompt worked whenever it was delivered, so it was
not being delivered. `paths.extract_prompt()` took no pack name.

The partition that mattered was not the one designed. It was the accidental
difference between the probe (which read the NASA prompt explicitly) and the
pipeline (which did not).

### 2. "or implied", split by pack

The `acceptance_criteria` collapse (0.937 → 0.443 corpus-wide) had a clean
explanation: the nasa prompt asks for the criterion "stated **or implied**", and
a licence to infer produces generic answers.

Split by pack:

| pack | "or implied"? | qwen | llama | change |
|---|---|---|---|---|
| nasa-7009b | yes | 0.966 | 0.518 | −0.448 |
| vv40 | **no** | 0.933 | 0.528 | −0.405 |

**Both collapsed, by nearly the same amount, and only one pack has the clause.**
A prompt edit would have shipped against a cause that was not there. The
partition cost one `groupby` and no API call.

### 3. The segmenter "fix", split by fixture

Two fixtures were examined. On one, the change corrected Morrison COU2 from
`Accepted` to `Not accepted` — a false accept on a Class III VAD, the worst
error class the tool has. That is a compelling case on its own.

All four fixtures: **3/4 before, 3/4 after.** It fixes Morrison COU2 and breaks
nasa COU1. Net zero.

### 4. The negative control, split by test

`test_control_produces_no_package.py :: FAILED` reads exactly like the negative
control producing a package — a direct question mark on the completeness
enforcement that is the praxis contribution. It was escalated to
pre-committee priority on that reading, independently, by both people looking at
it.

The file holds six tests. **Five are about the control and all five passed
throughout.** The failure was the contrast case, about the LLM's real output,
asserting that a defect was still present — and the defect had been repaired.

Partitioning here was reading which test failed. Two minutes.

### 5. The real-document re-score, caught by its own condition

The first version scored **0.8545**, three of six papers at exactly 1.000. It
was circular: it compared the annotation's evidence text against gold sentence
sets derived from that same text.

The partition was built into the gate. Condition 3 compares the result against
the 0.714 human agreement ceiling, on the reasoning that **a perfect instrument
cannot exceed the agreement of the humans whose judgments define truth**. A
score above the ceiling is evidence of leakage, not excellence. Three papers at
exactly 1.000 is circularity's signature.

Drafted against a hypothetical, it fired on an actual, on first contact.

### 6. The blast radius, split by manifest

The routing finding claimed four packs shipped extract prompts and were affected.
**Only one does.** `iso42001`, `surrogate` and `disposition` have no `prompt`
key, so `uofa extract` never reached them.

### 7. The audit that reported a clean absence, split by search terms

A denominator-rule instance was ruled unciteable on the finding that "no
committed artifact in this repository states its figures." The artifact was
commit `08cbfc78`, in this repository's own history, merged under PR #45.

The check had grepped two directories of the working tree for the decimal
strings belonging to the **other two** instances. It never searched this
instance's own terms — firewall, Group B, the profiles — and never searched
history at all. It reported absence from a slice that could not have contained
the thing.

The partition that would have caught it is the one the audit skipped: search per
claim, not per known example. **An audit that looks for the fingerprints of the
instances it already holds will miss the instance whose fingerprint it never
loaded.** This is the keyword-not-claim substitution operating on verification
rather than on extraction. In extraction it was measured as an 11× error in the
opposite direction — 45% of cards mention a sampling temperature, only 4% state
one for their evaluation — where matching the keyword counted mentions that were
never claims. Searching by fingerprint overcounts what you have examples of and
misses what you do not.

## The ones that were ours to own

Two, and they belong here for the same reason the principle does.

**The negative-control escalation (Vishnu).** Ordered on a wrong premise, and
the premise came from the file name rather than from the failing test. The
control was always clean. That is exactly the outcome a triage is supposed to be
allowed to have — a triage that can only confirm the concern that prompted it is
not a triage — and it cost about an hour to establish, against a two-minute check
that would have prevented it.

**The "other repository" provenance claim (Vishnu).** The firewall instance was
described as living in a separate repository, as Phase 1 work in a distinct
workstream. It was in this repository the whole time. The claim was stated
confidently, and when it was challenged the correction was partial: the rule was
held correctly — produce the artifact or it stays out — while the wrong narrative
was kept and defended. It was settled by a search, not by an argument.

That puts it in the same lineage as the commit-message bias claim, which asserted
a direction without measuring it and was corrected by measuring: **asserted
without searching, corrected by searching.** The two errors are the same error
about different objects, one about a causal direction and one about a location,
and both were confident, both were cheap to check, and neither was checked before
being stated.

Filed rather than smoothed over, because the principle is only worth stating if
its counter-examples are in the same document, and it is worth less if the
counter-examples are only ever the machine's.

## Why this belongs in the methods chapter and not the changelog

The praxis argues that model credibility should be evidenced and checkable
rather than asserted. This is the same argument applied to the project's own
inference: **a number that has not been disaggregated is an assertion about a
population, made from a sample that was never separated from its alternatives.**

The instruments that caught these were not analytical sophistication. They were
partitions — by pack, by fixture, by test, by manifest — plus one declared
threshold that encoded a partition (against the human ceiling) before the data
existed.

That is the transferable claim: *the defence against a plausible wrong conclusion
is not more analysis, it is a split.*

