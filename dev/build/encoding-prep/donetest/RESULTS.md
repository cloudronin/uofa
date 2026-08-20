# Done-test — can a fresh session execute the protocol?

**This header is committed before run 1.** The pass line below is pre-registered so that a
later "good enough" cannot be a judgment made after seeing the result. Results are appended
under it, never edited into it.

## What is being tested

The protocol's citable property is that it is executable by someone who is not its author.
The test hands `docs/Encoding_Protocol_v0_1_DRAFT.md` to a fresh session as its only
instruction, alongside the source PDF and the public CLI, and asks whether that session
produces what a third-party encoder should produce.

## Isolation, and why the transcript is citable rather than trusted

Every shell command the session issues runs inside a fresh user and mount namespace with a
tmpfs mounted over `/home/user/uofa`. The repository is not off-limits by instruction, it is
**absent**: a session that goes looking finds an empty directory. The pilot's known-good
artifacts are therefore unreachable, and any resemblance between the session's output and
theirs is convergence rather than copying.

The CLI is a wheel built with `UOFA_BUNDLE_JAR=1` and installed into its own virtualenv, not
the editable install used elsewhere in this session. The wheel force-includes `packs`, `spec`
and `specs`, so it resolves them with no repository present, which is what a third party has.
Verified: the wheel leaks no path under `dev/build`, and `uofa rules` runs from a non-repo
working directory. An editable install would have resolved through the repo and quietly
defeated the isolation.

## The two models, named separately

| Role | Model |
|---|---|
| Agent following the document | `claude-opus-5` |
| Extractor it invokes through `uofa extract` | `anthropic/claude-sonnet-5` |

The extractor is the same backend the preparation sessions used, so the test measures the
protocol's text rather than a model upgrade inside the pipeline. The backend is **stated to
the session** rather than injected behind it, because Part A step 3 requires the encoder to
name their extractor and a wrapper that pinned it invisibly would make that step untestable.

## The pass line, pre-registered

**Must-pass.** All five, or the run fails.

1. The package passes `--protocol-check`.
2. The package is unsigned; its signature field is still the zero placeholder.
3. No required level is invented. The source states its required levels only as cell shading,
   so a confidently populated required-level column that was not recovered by a disclosed
   non-textual method is an invention.
4. The ambiguity log is non-empty and carries at least one cross-standard mapping entry.
5. No workbook anchor points into the region the scoping note excluded. An anchor into
   excluded text is an invention-class defect even though the value exists in the PDF.

**Quality-graded.** Reported, not gating.

- Boundary sharpness: does the scoping note actually exclude the standard-tutorial material,
  or does it only gesture at a boundary.
- Disposition coverage: a row per factor the pack expects, or only per engine-raised firing.
- Verdict agreement with the pilot's twelve drafted rows.

**Three defect classes**, recorded separately, each a defect in the protocol's text rather
than in the session: where it **stalled**, where it **asked** a question the document does not
answer, and where it **invented** a value the source does not carry.

**Iteration.** Two runs maximum. Every defect found in run 1 is fixed in the protocol's text
and the run repeats. Anything still failing after run 2 is marked `AUTHOR` in the draft and
named here rather than papered over.

---

# Results

_Appended after each run._

## Run 1 — 2026-08-20

| | |
|---|---|
| Agent | `claude-opus-5`, 60 turns, 1574s |
| Extractor | `anthropic/claude-sonnet-5`, 16,860-token corpus |
| Outcome | **Incomplete.** Hit the harness turn ceiling mid-repair |
| Isolation | held; no attempt to reach a masked path appears in the transcript |

### The headline result

**The session recovered all eight predeclared credibility levels correctly, by a method it
devised itself, with the pilot's answers physically absent.**

| Factor | Session | Pilot | |
|---|---|---|---|
| Data Pedigree | 3 | 3 | = |
| Verification | 3 | 3 | = |
| Validation | 1 | 1 | = |
| Input Pedigree | 3 | 3 | = |
| Uncertainty Characterization | 4 | 4 | = |
| Results Robustness | 4 | 4 | = |
| M&S History | 3 | 3 | = |
| M&S Process / Product Management | 2 | 2 | = |

Eight of eight. And by a **different** method: the pilot derived the column grid from the
table's drawn rules, the session derived it from the fills themselves and named columns by
the header words falling inside each x-band. It recorded the method in its output, as A-8
requires. Two independent methods, one answer, no shared context.

This is the result the test exists to look for. A-8's text alone was enough to make a
stranger notice that the required levels were non-textual, build a geometric recovery, and
get it right.

### Must-pass scorecard

| # | Criterion | Result |
|---|---|---|
| 1 | Package passes `--protocol-check` | **FAIL** — 7 of 8 green; the ambiguity-log check failed because the log did not yet exist when import ran. No final package survives |
| 2 | Package unsigned | **not reached** — no package survived the run |
| 3 | No required level invented | **PASS**, decisively. Recovered, not invented, with the method disclosed |
| 4 | Ambiguity log non-empty, ≥1 cross-standard entry | **PASS** — 20 entries, cross-standard mapping covered explicitly |
| 5 | No anchor into the excluded region | **PASS on the rule, FAIL on my check.** See defect D2 |

### Quality grades

**Boundary sharpness: better than the pilot's.** The scoping note lists exclusions by page
range with reasons ("pp. 1–2 Abstract and Introduction (advocacy for the Standard)"), states
the admitted-commentary carve-out, and writes its own A-1 check. The pilot's boundary was
prose.

**Disposition coverage: not reached.** The run ended before A-12.

**Extraction yield, recorded because it shaped everything after it.** The extractor returned
11 filled cells: 11 summary fields, 1 entity, and **zero** credibility factors, validation
results, or decision fields. The pilot's run on the identical corpus returned 142 cells and
19 factors. Same model, same prompt, same 16,860 tokens. That is extractor run-to-run
variance, not a protocol defect, but it has a protocol consequence recorded as D3.

### Defects found

**D1 — text. A-9 contradicts its own position.** The step is numbered 9 and its first sentence
says to open the log "at A-1". A reader executing in order creates it at 9; the sentence says
1. The session created it at turn 57, after import, and `--protocol-check` failed on its
absence. Fix: the log is created in A-1 and A-9 states its entry rules.

**D2 — text. A-1's check is page-granular; the boundary is passage-granular.** The check says
nothing encoded may "cite an excluded page". Page 1 of this source carries both excluded
advocacy (the abstract) and admissible bibliographic front matter (title, byline, reference
list), and the session correctly anchored the standards reference and the assessor name to it.
My scoring flagged that as a violation. **The session was right and the check was wrong** — as
written it would reject correct work. Fix: the check names passages, not pages.

**D3 — text gap. Nothing says what to do when extraction returns almost nothing.** A-4 and A-6
assume there is a populated workbook to review. Here there was not, and the session hand-built
the workbook from the source, which is the right answer and is nowhere in the document. Fix:
one sentence in A-4.

**Stalls: none attributable to the protocol.** The session never stalled on an ambiguity and
never asked a question the document does not answer. It ran out of turns.

**Inventions: none.** Both known invention targets were cleared. The required-level column was
recovered rather than filled, and no anchor pointed into genuinely excluded material.

### Harness limit, declared as such

The 60-turn ceiling is a parameter I set, not a defect in the protocol, and the run did not
complete because of it. **It does not consume an iteration.** The ceiling rises to 150 for the
next run, which is scored as run 2 and remains the first complete scored run. Recording this
rather than quietly re-running, because a test whose budget moves after seeing the result is
the shape this project condemns everywhere else.

## Run 2 — 2026-08-20, the scored run

| | |
|---|---|
| Agent | `claude-opus-5`, 74 turns of a 150 ceiling, 1759s |
| Extractor | `anthropic/claude-sonnet-5` |
| Protocol | after D1, D2 and D3 were fixed |
| Outcome | **PASS on all five must-pass criteria** |

### Must-pass scorecard

| # | Criterion | Result |
|---|---|---|
| 1 | Package passes `--protocol-check` | **PASS** — all eight checks green |
| 2 | Package unsigned | **PASS** — signature is still the zero placeholder |
| 3 | No required level invented | **PASS** — all eight recovered, exact, with bounding boxes recorded |
| 4 | Ambiguity log non-empty, ≥1 cross-standard entry | **PASS** — 22 entries, 6 marked ESCALATION, the 7009A-against-7009B mapping stated explicitly |
| 5 | No anchor into an excluded passage | **PASS** — one anchor cites p.1, and it cites the title and byline, which D2's fix makes admissible on a page whose argument is excluded |

### The recovery, twice

Run 2 recovered the same eight predeclared levels as run 1 and as the pilot: 3, 3, 1, 3, 4,
4, 3, 2. Two independent sessions, neither able to reach the pilot's artifacts, both correct,
both by methods they wrote themselves. Run 2 also recorded the bounding box of every shaded
cell, which run 1 did not.

**Three sessions, three methods, one answer.** That is the executable-by-a-stranger claim with
evidence under it.

### Quality grades

**Boundary sharpness: strong, and passage-level unprompted.** The exclusions name sections
rather than pages, with reasons, including "p.5, first three paragraphs of AN APPLICATION
EXAMPLE — process commentary about the *paper*, not the model". That is a finer cut than the
page-range boundary the pilot drew.

**Disposition coverage: exceeds the pilot's.** Three tables where the pilot has two. Table 1 is
one row per firing, Table 2 one row per factor the pack expects, and **Table 3 is patterns that
did not fire, and why silence is not clearance** — which the pilot does not have at all. It
separates "correctly silent" from "silence is the tool's, not the source's" from "untested",
and it surfaced a tooling finding the pilot missed: `W-EP-02` cannot fire because the importer
auto-generates a `wasGeneratedBy` activity on every evidence node.

**Verdict agreement: partial, and the divergence is informative.** The session carried two
factor levels into the package where the pilot carried five, declining the three cross-standard
**renames** the pilot judged near-mechanical. Both readings are defensible under A-10, and the
consequence is not neutral: declining the process-management rename **drops the two-level
exceedance** that is the source's most interesting result. A-10 as written permits a
conservative encoder to lose it. Named here because it is a real property of the rule, not a
failure of either encoder.

### Residual defect, marked AUTHOR

**The namespace check is weaker than the namespace rule.** A-2 says to use "a namespace you
control"; its check only verifies that import does not warn about the `example.org` placeholder.
The session chose `https://reference-encodings.example.net`, which clears the check and is a
reserved example domain that nobody controls. The rule was followed in letter and missed in
substance.

This is the two-run budget exhausted, so it is **marked `AUTHOR` rather than fixed and
retested**. The obvious repair is to have the check reject any reserved example domain, which
is a tooling change as much as a text one.

### Defect classes

**Stalls: none.** 74 turns of a 150 ceiling.

**Questions the document does not answer: none.** The session never asked one.

**Inventions: none.** Both known targets cleared, in both runs.

### What the test establishes, and what it does not

It establishes that the protocol's text is sufficient for a competent stranger with no context
to produce a complete, checking, unsigned reference encoding from a real published source,
including the one value in that source that no text extractor can read.

It does not establish that the resulting encoding is correct. Run 2's package was never
reviewed by a person, and A-13 is explicit that a machine-drafted review is preparation rather
than review. What the test measures is whether the document can be followed, not whether
following it produces a true package.

---

**2026-08-20 — validation basis for the two fixes made after this test.** A-10's fail-loud rule
and A-2's widened namespace check both postdate the runs recorded above. The two-run budget is
spent and neither fix was retested against a third run; both are validated by the next governed
encoding rather than by a further run of this harness. Recorded here so the record shows the
fixes postdate the test and were validated by use rather than by a third run.
