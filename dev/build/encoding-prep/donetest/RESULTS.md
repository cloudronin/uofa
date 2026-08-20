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
