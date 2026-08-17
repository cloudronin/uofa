# U-INV-1 — Fault-injection / mutation-testing citations for D4

Status: **PARTIAL — unchanged; v2.0 fixes the escort sentence, which sharpens what
the citations must support**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent D4, A2, B2

---

# ADDENDUM — re-investigated against parent spec v2.0

v2.0 §D4 clause 4 fixes the escort sentence as text:

> first mention in §1.6 and §3.7 becomes **"constructed ground truth via defect
> injection into published-case substrate, following the fault-injection and
> mutation-testing tradition,"** with two citations. U-INV-1: select citations from
> sources actually read; do not cite from memory.

Two observations.

**1. "into published-case substrate" is true today and helps the citation case.**
Skeleton mode reads the base COU from `packs/vv40/examples/{morrison,nagaraja}/`,
so the substrate genuinely is published-case. That clause needs no defence.

**2. The clause the citations must carry has narrowed to "defect injection …
following the fault-injection and mutation-testing tradition"** — and that is
exactly the clause INV-11 finds is not yet literally true of the harness, which
generates rather than mutates. The two findings are coupled: if the deterministic
mutator ships (INV-11 §4b), P1 and P2 in the table below are straightforwardly
supported and the sentence stands as drafted. If it does not, the sentence claims
membership in a tradition the harness approximates but does not join, and the
one-clause reword offered below becomes the honest option regardless of what the
two surveys say.

**Status otherwise unchanged.** Both citations remain verified bibliographically and
unread substantively; five fetch routes failed. The ~20-minute library-proxy check
is still the closing action, and everything in "The claim each citation must
support" remains **HYPOTHESIS**.

**Sequencing note:** do the reading *after* the INV-11 wrap-vs-build decision. If
the mutator is not funded, the escort sentence changes and the passages worth
extracting change with it.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## What this item asked for, and what it got

The item is explicit that abstracts are insufficient: *"the escort sentence
characterizes the tradition, so the works must actually say what the sentence
implies."* The done-gate is that the author can paste the citations *"having read
only the extracts."*

**That gate is not met.** Both candidates were located and their bibliographic
records verified to canonical-version standard, but **neither full text was
reachable** from this environment — IEEE Xplore returned no content, and three
open mirrors were unreachable (expired certificate, refused connections). So the
supporting extracts, with page numbers, are not in this file.

What follows is everything short of that: verified citations, the exact passages
to read, and the specific claim each must support. This turns a read-and-verify
task into a 20-minute check for someone with GWU library access.

## Recommended citations (bibliographic records verified)

### Mutation testing

> Y. Jia and M. Harman, "An Analysis and Survey of the Development of Mutation
> Testing," *IEEE Transactions on Software Engineering*, vol. 37, no. 5,
> pp. 649-678, Sept. 2011. doi: 10.1109/TSE.2010.62

- **Canonical version confirmed.** Journal article, not preprint. The
  widely-circulated CREST/King's College technical report (TR-09-06) is the
  preprint of this; **cite the TSE version**, per the item's step 3.
- Bibliographic fields cross-checked across three independent indexes (SciRP
  reference record, ACM DL entry for `10.1109/TSE.2010.62`, Semantic Scholar).
  Volume, issue, page range and year agree.
- It is the standard survey, as the item assumed.

### Fault injection

> M.-C. Hsueh, T. K. Tsai, and R. K. Iyer, "Fault Injection Techniques and Tools,"
> *Computer*, vol. 30, no. 4, pp. 75-82, April 1997. doi: 10.1109/2.585157

- **Recommended over Voas & McGraw.** Reasons: (a) it is a journal survey, matching
  the "tradition" framing better than a single book; (b) it is a peer-reviewed
  article rather than a monograph, which is easier to cite precisely for a specific
  claim; (c) it pairs symmetrically with Jia & Harman — two surveys, two
  traditions.
- **Keep Voas & McGraw (1998), *Software Fault Injection: Inoculating Programs
  Against Errors*, Wiley, as the alternate** if the author prefers the
  *software*-fault-injection framing specifically. Hsueh et al. covers hardware and
  software injection; the praxis's harness is squarely software-level, so a reviewer
  in that subfield might expect Voas.

## The claim each citation must support

The escort sentence: *"constructed ground truth via defect injection… following the
fault-injection and mutation-testing tradition."*

That commits to two propositions. Each is stated here with the passage to check, so
verification is targeted rather than a full re-read:

| # | Proposition the sentence needs | Where to check in Jia & Harman | Where to check in Hsueh et al. |
|---|---|---|---|
| P1 | The tradition **deliberately introduces known faults** into an otherwise-correct artifact | §1 Introduction and §2 ("The Mutation Testing Process" / mutant definition) — the definition of a mutant as a program with a deliberately seeded change | §1, the definition of fault injection and the "what it is for" framing, p. 75 |
| P2 | The point of doing so is that **the injected fault is known by construction**, giving ground truth against which a detector is evaluated | §2 (mutation adequacy score / killing mutants) — the mutant is the known fault and the score measures the test suite against it | §1-2, the argument that controlled injection permits observing the system's response to a *known* fault, which is what makes dependability evaluation possible rather than anecdotal |

**P2 is the load-bearing one and the more likely to disappoint.** Mutation testing's
canonical framing is *test-suite adequacy* — mutants measure whether tests are good
enough — rather than *ground-truth construction for a detector*. Those are close
cousins and the analogy is fair, but the sentence should not imply the survey
frames it as ground-truth construction if it does not. If P2 is not supported in
those words, the fix is a one-clause reword, not a different citation:

> *…constructed ground truth via defect injection, applying to credibility evidence
> the same seeded-fault logic that mutation testing applies to test suites and fault
> injection applies to dependability evaluation.*

That claims a method transfer rather than membership in a tradition, and it is
defensible from the abstracts alone.

## Escalation

The item's criterion — *"neither fault-injection candidate supports the framing on
actual reading"* — **cannot be evaluated**, because neither was read. Not escalated;
recorded as blocked, with §"Access" naming exactly what would unblock it.

One thing worth flagging to the author independently of the citation check, because
it bears on whether the escort sentence is accurate about *this project*:
**INV-11 finds that the harness's "injection" is LLM generation from a declared
target, not deterministic mutation of a known-good artifact.** The escort sentence's
"defect injection" is a fair description of intent and of the manifest-derived
label, but a reviewer who knows the mutation-testing literature will read
"injection" as deterministic seeding. If the deterministic injector proposed in
INV-11 §4b gets built, the sentence becomes literally true and both citations sit
comfortably. If it does not, D4's sentence and A2's mapping table should both say
"generated against a declared target flaw" somewhere nearby. **That is the more
consequential finding here than which survey gets cited.**

## Access — what was tried and what to do

| Route | Result |
|---|---|
| `ieeexplore.ieee.org/document/5487526` | returned no content to the fetcher |
| `cs.ucl.ac.uk/staff/mharman/tse-mutation-survey.pdf` | connection refused |
| `www0.cs.ucl.ac.uk/staff/mharman/tse-mutation-survey.pdf` | connection refused |
| `course.ece.cmu.edu/…/faultInjectionSurvey.pdf` (Hsueh et al. full text) | TLS certificate expired |
| `semanticscholar.org` paper page | returned no content |
| `users.ece.cmu.edu/~koopman/des_s99/fault_injection/` | **reachable**, but it is a course page quoting an unnamed source, and it does **not** cite Hsueh et al. for its definition. Not usable as evidence about either work. |

**To close this item (~20 min):** open both DOIs through GWU's library proxy, read
§1-2 of each, and paste the two or three sentences that speak to P1 and P2 into
this file with page numbers. Both are short: Hsueh et al. is 8 pages;
Jia & Harman's relevant material is in its first two sections.

## Coverage statement

**Searched.** Web search for each work's bibliographic record, cross-checked across
three indexes per citation. Five full-text fetch attempts across IEEE Xplore, two
UCL mirrors, a CMU mirror, and Semantic Scholar; one secondary source (CMU course
page) retrieved and read, then rejected as evidence. Voas & McGraw was identified
as the alternate from the item's own candidate list but not fetched.

**Search terms derived from the escort sentence's own claim** (seeded faults with
known ground truth), not from the works' titles: `seeded faults`,
`known ground truth`, `deliberate introduction of faults`, `mutation adequacy`,
`fault injection definition` — which is how the secondary source was found and also
how it was disqualified.

**NOT verified — the substance.**
- **No sentence from either work was read in its published form.** Every
  characterisation in §"The claim each citation must support" is a *prediction*
  about where the supporting text will be, derived from the works' known structure
  and abstracts. It is not evidence, and the author should treat it as a reading
  guide, not a finding. Per the parent spec's ground rule 1, everything in that
  section is **HYPOTHESIS**.
- No page numbers are given, because none were seen.
- The praxis's reference style was not checked against either citation's format
  (item step 3, second clause) — `CITATION.cff` and the manuscript's bibliography
  were not consulted.
- Voas & McGraw's ground-truth-by-construction framing is entirely unverified; it is
  carried as an alternate on the item's own recommendation, not on evidence.
