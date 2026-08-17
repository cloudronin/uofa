# UofA Investigation Spec v1.0 (for Claude Code)

Status: READY for execution
Date: 2026-08-16
Owner: Vishnu Vettrivel
Parent: UofA_Unified_Repair_Spec_v2_0.md. This spec details the open items in its investigation register. Each item here is an investigation, not an implementation: the deliverable is a findings file, not a code change, unless the item explicitly says "then implement." Where a finding would change a parent-spec decision, stop and report rather than proceeding on the new assumption.

Repository: github.com/cloudronin/uofa, main branch unless an item pins otherwise.

## Ground rules

1. **Evidence over assertion.** Every finding cites the file path, line range, git commit, or command output that supports it. A finding without a citation is a hypothesis and must be labeled HYPOTHESIS.
2. **Search for each claim's own terms.** Do not pattern-match the repo against examples in hand (the survey's seventh-instance lesson: an audit that searches only for known fingerprints reports false absences). For every "does X exist" question, derive search terms from X's definition, not from where X was last seen.
3. **Coverage statement required.** Each findings file ends with a coverage statement: what was searched, with what terms/commands, and what was NOT searched. A negative finding without a coverage statement is not a finding.
4. **Stop conditions.** Each item lists an escalation criterion. When hit, write up the partial finding and stop; do not improvise a resolution to an author-level question.
5. **Output location.** One file per item at `docs/investigations/INV-<id>-findings.md`, plus a one-line-per-item summary table at `docs/investigations/SUMMARY.md`, updated as items close.
6. **No frozen-artifact edits.** Catalog v0.5.15.1, pre-registrations, and shipped study artifacts are read-only for this spec. If an investigation reveals a defect in a frozen artifact, that is a finding for the A4 disclosure section, not a fix.

---

## INV-1: MECHANICAL/JUDGMENT classification of all 23 patterns

**Question:** for each pattern in catalog v0.5.15.1, can a script re-derive the pattern's fired/not-fired label from a pinned evidence bundle with zero human input?

**Procedure:**
1. Locate the catalog source of truth (search for the pattern IDs W-EP-01, W-AR-05, COMPOUND-01 etc. across the repo; identify whether the catalog lives as data, code, or both, and which artifact is canonical at v0.5.15.1 by its git tag).
2. For each of the 23 patterns, read the actual rule implementation (Jena rule, SHACL shape, SPARQL, or code path) end to end. Classify:
   - MECHANICAL: the rule's inputs are entirely package-resident facts (field presence/absence, value comparison, checksum, signature verification, graph reachability). Re-running the rule on the pinned bundle reproduces the label deterministically.
   - JUDGMENT: the rule's firing depends at any point on a human- or LLM-authored disposition, threshold chosen per-case, prose interpretation, or an input that is itself an adjudication.
3. Record edge cases explicitly. Expected hot spots from the parent spec's provisional table: W-CON-01..05 (MECHANICAL only where the rule is pure field comparison; classify each of the five separately), W-AR-01..05 (MECHANICAL only where the rule is structural presence/absence; classify each separately). Do not classify a family as a block if its members differ.
4. For every pattern classified MECHANICAL, name the exact command or code entrypoint that re-derives its label. This list is the requirements input for `uofa verify-labels` (parent A1); if no single entrypoint exists, say so and sketch the smallest wrapper.

**Output:** table of 23 rows: pattern ID, classification, rule artifact path, re-derivation entrypoint (or NONE), one-sentence rationale, edge-case notes.
**Done-gate:** all 23 classified with citations; every MECHANICAL row has an entrypoint or an explicit NONE with wrapper sketch.
**Escalate if:** any pattern's implementation is ambiguous between the two classes after reading the code (do not resolve by intuition; present both readings).

## INV-2: feasibility of `uofa protocol-check`

**Question:** can protocol conformance (mandatory-field completeness per Encoding_Protocol_v0_1) be validated mechanically with existing machinery, and at what cost?

**Procedure:**
1. Inventory the existing validation stack: where SHACL shapes live, how completeness profiles (C2) are invoked from the CLI, and whether a field-list-driven check already exists in another guise.
2. Determine the delta between "SHACL completeness profile passes" and "protocol mandatory-field list satisfied." If the protocol's mandatory fields are (or can be) expressed as a SHACL profile, protocol-check is a thin alias and the estimate is hours; if the protocol requires checks SHACL cannot express (e.g. ambiguity-log presence per underdetermined field), enumerate those checks and estimate each.
3. Note: the protocol document does not exist yet (parent A7). Investigate against the A7 section's field structure in the parent spec; flag any A7 requirement that is mechanically uncheckable so A7 can be written checkable-first.

**Output:** feasibility memo: reuse path, gap list, estimate (hours), and a recommendation (build now / build with A7 / defer).
**Done-gate:** recommendation with estimate, citing the validation-stack entrypoints found.
**Escalate if:** the completeness-profile machinery is materially different from what C2 describes (that would be a parent-spec correction).

## INV-3: Morrison COU1 last-touch date (washout clock for A8)

**Question:** when did the author last materially touch the Morrison COU1 package and its associated notes?

**Procedure:**
1. `git log --follow` on `tests/fixtures/extract/ground_truth/morrison-cou1.json` and on every artifact the log reveals as co-evolving with it (encoded package files, ambiguity notes, disposition records; find them by searching for morrison/COU1 identifiers repo-wide).
2. Distinguish material touches (content changes to the encoding or dispositions) from incidental ones (path moves, formatting, unrelated refactors touching the file). List both, classify each commit.
3. Report the latest material-touch date; the 3-week washout clock (parent A8) starts there. Also check whether the Credibility Inspector demo or any recent study re-used the COU1 package in a way that constitutes re-exposure, and report those dates separately for the author to rule on.

**Output:** dated commit table with material/incidental classification; recommended washout-start date; re-exposure events flagged for author ruling.
**Done-gate:** date recommended with full commit citations.
**Escalate if:** material vs incidental is unclear for any commit that would move the date by more than a few days.

## INV-4: existing package-diff tooling (extend vs build for A8)

**Question:** does the repo already diff two UofA packages structurally and at the disposition level?

**Procedure:**
1. Search for existing comparison machinery under its own terms: graph isomorphism or canonicalization utilities, JSON-LD normalization, test assertions that compare whole packages, regression fixtures that imply a comparator, any CLI subcommand touching two packages.
2. If found: assess what it compares (raw bytes, canonical graph, entity-level) and what A8 needs on top (per-weakener disposition comparison with per-label-class agreement stats). Estimate the extension.
3. If not found: sketch the smallest `uofa diff-packages` meeting A8's needs, reusing whatever canonicalization the signing path already performs (signed packages must already canonicalize; find that code and cite it).

**Output:** extend-vs-build memo with the reuse points named and an estimate.
**Done-gate:** memo with cited entrypoints.
**Escalate if:** nothing in the signing path canonicalizes (that would be its own finding, worth a separate flag).

## INV-5: external accepted-case source for A3's external negative

**Question:** does a published, fully-accepted CM&S submission exist that can be encoded straight from source as a clean-package negative control?

**Procedure:**
1. First check in-repo supply: `MANIFEST.json`, the real-corpus-supply-survey findings, and existing fixtures for any already-sourced document whose published outcome is acceptance and which is NOT already a case-study anchor (Morrison, Nagaraja, NASA HPT excluded).
2. Candidates from the survey to re-examine for this different purpose: the Bologna paper (Aldieri 2023, already identified as clean-extracting with a full per-factor table; check whether its assessment outcome reads as accepted-for-COU), the accepted arms of any tiered case already encoded, and the SpaceNet Delphi assessment.
3. The criterion differs from both survey pools: what A3 needs is a document whose encoding should fire zero critical weakeners because the record shows the evidence was adequate. Screen candidates against that criterion specifically; a paper can have a per-factor table and still document an inadequate package.
4. Reader-pathology screen any new candidate (the >20-char alpha-token check from the survey) before recommending it.

**Output:** ranked candidate list with per-candidate screen results and one recommendation; or a finding that no candidate clears the criterion, with the coverage statement.
**Done-gate:** recommendation or justified absence.
**Escalate if:** the best candidate is Bologna and it is also wanted as the next routing bundle (dual use may be fine but is an author call on contamination).

## INV-6: git-history audit for post-freeze changes (feeds A4)

**Question:** what changed after each declared freeze, and is every such change already disclosed?

**Procedure:**
1. Establish the freeze inventory from the record: catalog v0.5.15.1 tag date, Phase 2/2.5 closure, Phase 3 spec v1.4 gates, A16 pre-registration commit, the H2 replacement-criterion commit (ch4-h2-section says thresholds were committed before measurement; find that commit), and any DECLARATION.md-style files (the evidence-span study has one; search for others).
2. For each freeze: `git log` on the frozen artifact from freeze date to HEAD. Classify every post-freeze commit: (a) no-op for the freeze (docs, comments), (b) disclosed change (match against existing disclosure text in the repo and shipped chapter sections), (c) UNDISCLOSED substantive change.
3. Category (c) is the entire point. For each, record what changed, when, and what results cite the artifact on either side of the change. Do not editorialize on intent; the A4 appendix will carry the author's rationale.
4. Verify the positive record too: confirm the Phase 3 gate values in the spec predate Phase 3 execution commits, and that the pinned Liang commit in study artifacts matches 6bcc76fe6142 everywhere it is cited.

**Output:** per-freeze table of post-freeze commits with classification; the (c) list separately; pin-consistency check results.
**Done-gate:** every declared freeze audited; (c) list complete with citations; coverage statement naming any freeze whose artifact could not be located.
**Escalate if:** any (c) item touches a number already reported in shipped chapter text.

## INV-8: where judge output is load-bearing for H3

**Question:** in the current manuscript text, Phase 3 spec, and study artifacts, where does LLM-judge output function as ground truth or as a hypothesis-support input for H3, rather than as realism screening?

**Procedure:**
1. Inventory the H3 support chain as currently written: locate every H3-related results table and every sentence deriving an H3 conclusion, in the manuscript sources and in `studies/` artifacts.
2. For each number in that chain, trace its provenance to either (a) an injection manifest, (b) a deterministic rule output, or (c) judge output (Gemini 2.5 Pro / GPT-4.1 / Llama 3.3 arms, calibration or adjudication stages). Build the provenance table.
3. Separately inventory where judge output legitimately remains (realism screening of generated cases, gap_probe REAL-GAP adjudication in Stage 5): these are not removals, they are relabeling targets. Distinguish the two lists cleanly, because Stage 5's judge role is different in kind from H3 ground truth and must not be swept away with it.
4. Flag any place the manuscript's current prose describes judges in ground-truth language even where the underlying number is manifest-derived (a framing defect, cheaper to fix than a data defect; the A2 rewrite needs the exact locations).

**Output:** provenance table (number, location, source class a/b/c); removal list; relabel list; prose-defect list with locations.
**Done-gate:** every H3-chain number traced; the three lists complete.
**Escalate if:** any H3-supporting number turns out to have judge-derived provenance with no manifest-derived equivalent available (that changes A2 from reframe to partial re-run, an author decision).

## INV-11: injection harness CLI exposure (feeds B2)

**Question:** how much of the Phase 2/2.5 injection-and-detection loop is invocable today as CLI commands, and what is the smallest wrap to reach `uofa inject` + `uofa detect` with a manifest?

**Procedure:**
1. Locate the harness: the Phase 2 generator, skeleton mode (W-AR-05 MVP), the 23-pattern injection classes, and the manifest writer. Map each to its invocation surface (CLI subcommand, script, test-only fixture generator, library call).
2. Determine what a single end-to-end run requires today: inputs (clean package source), configuration, outputs (corrupted package + manifest), and the detect-side invocation with report.
3. Sketch the wrap: which existing entrypoints `uofa inject --pattern <id> --package <path>` composes, what the manifest must contain for the demo narrative (flaw injected, where, expected pattern), and what the README walkthrough's exact command sequence is. Wrap, don't rewrite; if any step requires more than argument plumbing, itemize it.
4. Test the committee-runnability assumption: can the sequence run on a fresh clone with documented setup (pip install, Java for the Jena engine)? List the setup steps a committee member would actually need; if the Jena fat JAR or model dependencies make "runnable by a committee member" unrealistic, say so and propose the fallback (recorded terminal session, or a hosted variant of the same commands).

**Output:** exposure map; wrap sketch with itemized plumbing; fresh-clone runnability assessment with the honest setup-step list.
**Done-gate:** B2's implementation is fully specified by this memo, or the fallback is recommended with reasons.
**Escalate if:** the harness's clean-package inputs are themselves test-only fixtures unsuitable for a public demo (asset question for the author).

## INV-12: does the demo Space build the signed pack internally?

**Question:** does the pipeline behind HF Space cloudronin/uofa-demo construct a signed UofA package during analysis (merely unsurfaced), or does its path stop at analysis outputs?

**Procedure:**
1. Locate the Space's source: check for an in-repo app directory or a linked repo/subtree for cloudronin/uofa-demo; if the Space source is separate, fetch it.
2. Trace the upload-to-verdict path: reader → router → factor extraction → analysis → Reviewer/Author rendering → PDF. At each stage, note whether package-construction code (JSON-LD graph assembly, provenance, signing) is invoked, invoked-but-discarded, or absent.
3. Compare the Space's pipeline code against the CLI's pack-build path: same modules, forked copies, or reimplementation? A fork is a defect per parent C1's emittability rule; report divergence explicitly, file-by-file if forked.
4. If the pack is built internally: identify the smallest surfacing change (serialize + download route) and confirm `uofa verify` passes on a pack produced through that path in a local run.
5. If the path stops at analysis: itemize what the Space is missing to call the production pack-build path (signing key handling in the Space environment will be the likely sticking point; investigate how keys are provisioned and whether a demo-scoped key is acceptable, flagging the security-model doc's position).

**Output:** trace memo with the stage table; fork/shared verdict; surfacing plan or gap itemization; key-handling note.
**Done-gate:** C1's effort estimate (2-4h) confirmed or corrected with reasons.
**Escalate if:** the Space pipeline is a fork with behavioral divergence from the CLI path (parent-spec defect class, author decision on remediation scope).

## INV-13: read-before-admit screen of A10 candidates

**Question:** which of the named annotation-pool candidates clear the committed inclusion rule?

**Note:** the inclusion rule must be committed by the author before any admission (parent A10). This item prepares the screen so admission is a same-day step once the rule lands.

**Procedure:**
1. Fetch each candidate PDF where licensing permits local processing: Frontiers collection papers (coronary stent 10.3389/fmedt.2021.702656, flow-diverter 10.3389/fmedt.2021.705003, EVAR 10.3389/fmedt.2021.704806, scaffold 10.3389/fmedt.2021.724062, cardiovascular-UQ 10.3389/fmedt.2021.748908), FDA nozzle (Hariharan 2017, PLoS ONE), spine PJF V&V 40 (CMBBE 2022), wrist-hand orthosis paper, Pathmanathan applicability (2017), Ahn & de Weck SpaceNet Delphi (Wiley Systems Engineering), 2024 pharma-manufacturing 7009 paper. Record access/licensing status per paper; do not commit paywalled artifacts to the repo, only fetch manifests with SHA-256 per the existing corpus discipline.
2. Run the reader-pathology screen on each: the pipeline reader, then the >20-char alpha-token rate plus the column-interleaving and line-wrap checks already used in the survey. Hard fail per survey precedent (~10% is unusable; ~0.1% is clean).
3. For each clean-extracting paper, produce the factor-evidence inventory: which V&V 40 / 7009 credibility factors have prose evidence in the text, with one example span each. This is a screening inventory, not annotation; the author annotates under the protocol.
4. Screen Ahn & de Weck additionally for the scorecard pool: does it print a transcribable per-factor CAS table for SpaceNet at published granularity?
5. Exclusion check: confirm no candidate is a source, alternate version, or derivative of Morrison, Nagaraja, or the NASA HPT anchors (the survey caught two alternate-version duplicates; check by DOI lineage and author overlap, not title similarity).

**Output:** per-candidate table: access status, pathology screen numbers, factor-evidence inventory (or rejection reason), scorecard-pool flag for Ahn & de Weck, exclusion-check result.
**Done-gate:** every named candidate screened or its inaccessibility documented; table ready for same-day admission once the rule is committed.
**Escalate if:** fewer than 5 candidates survive the screen (parent A10's 11-14 target becomes unreachable and the measured-ceiling disclosure path activates).

## U-INV-1: fault-injection / mutation-testing citations for D4

**Question:** which two citations anchor the sentence "constructed ground truth via defect injection... following the fault-injection and mutation-testing tradition"?

**Procedure:**
1. Candidate set to fetch and actually read (abstracts insufficient; the escort sentence characterizes the tradition, so the works must actually say what the sentence implies): a mutation-testing survey (Jia & Harman 2011, IEEE TSE, is the standard survey; verify its framing covers "seeded faults with known ground truth"), and a fault-injection foundational text (Voas & McGraw's software fault injection book, or Hsueh/Tsai/Iyer 1997 IEEE Computer survey; verify the ground-truth-by-construction framing).
2. Verify each candidate's actual claims support the escort sentence; extract the one or two sentences that do, with page numbers, into the findings file so the author can confirm without re-reading.
3. Check both are citable in the praxis's reference style and are the canonical versions (journal over preprint).

**Output:** two recommended citations with supporting extracts and page numbers; alternates if either fails verification.
**Done-gate:** author can paste the citations and the escort sentence with confidence, having read only the extracts.
**Escalate if:** neither fault-injection candidate supports the framing on actual reading (the escort sentence would then need rewording, an author call).

## U-INV-3: D6 number traceability

**Question:** does every number in the planned D6 sections trace to a committed artifact?

**Numbers to trace (from the parent spec's D6):** 32,111 cards; pinned commit 6bcc76fe6142; the raidex model/result counts D6 will cite; W-AL-01 firing 384/427; the count of results carrying real uncertainty that W-AL-01 clears (D6 says "exactly the results carrying real uncertainty"; verify the clearance count and the equality claim, not just the firing count).

**Procedure:**
1. For each number: locate the committed artifact in `studies/` (or wherever the A16/cohort outputs live), cite path + commit, and re-derive the number from the artifact where a script exists.
2. The equality claim ("clears exactly the N carrying real uncertainty") is a two-sided check: every cleared result carries stated uncertainty AND every result carrying stated uncertainty is cleared. Verify both directions; a one-direction check would repeat the keyword-for-claim substitution error.
3. Confirm the pinned Liang commit is recorded identically in every artifact that cites it (overlaps with INV-6 step 4; share the result).
4. Any number that cannot be re-derived from a committed artifact goes on a blocker list; D6 drafting must not begin for that number until it lands in `studies/`.

**Output:** trace table (number, artifact path, commit, re-derivation command/result, both-directions check for the equality claim); blocker list.
**Done-gate:** all numbers traced or blocked with the blocker named.
**Escalate if:** the equality claim fails in either direction (that changes D6's central sentence, an author call).

## INV-10 residual: raw vs adjudicated audit outside the H2 section

**Question:** outside ch4-h2-section (already compliant), where does the manuscript or site cite extraction figures without the raw/adjudicated label?

**Procedure:**
1. Enumerate every extraction-quality figure cited anywhere: manuscript sources, uofa.net content (`site/src/content/`), README, demo pages, and the NAFEMS reproduction page.
2. For each citation: does the underlying artifact record whether adjudication touched the number, and is the label present in the citing text? Three buckets: labeled correctly, unlabeled but raw (label cheap to add), unlabeled and adjudicated-or-unknown.
3. For the third bucket, check whether raw pre-adjudication outputs are preserved in the artifact record; where they are not, list the affected runs (parent A9 mandates re-running extraction to regenerate raw figures rather than estimating).

**Output:** citation table with buckets; re-run list for A9.
**Done-gate:** every extraction figure citation bucketed.
**Escalate if:** the re-run list includes any figure already in shipped chapter text (disclosure interaction with A4).

---

## Execution order

All items are parallel-now except: INV-13 admission (not screening) waits on the author's committed inclusion rule, and INV-2 reads A7's section in the parent spec rather than a shipped protocol. Suggested batching for session efficiency: repo-history items together (INV-3, INV-6, INV-10 residual, U-INV-3 pin check), rule-and-code reading together (INV-1, INV-8), harness/Space tracing together (INV-11, INV-12, INV-4, INV-2), external-fetch items together (INV-5, INV-13, U-INV-1).

## Summary table format (docs/investigations/SUMMARY.md)

| Item | Status | Finding (one line) | Escalations |
|---|---|---|---|

Statuses: OPEN / IN-PROGRESS / CLOSED / ESCALATED. An item with any escalation is ESCALATED, not CLOSED, until the author rules.
