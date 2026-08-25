# UofA Encoding Pilot Spec v1.0 — Johnson (2020), NASA-STD-7009B pack

Status: ACTIVE
Date: 2026-08-19
Owner: Vishnu Vettrivel
Source document: Johnson, K.L., "Applying NASA-STD-7009 Standard for Models and Simulations to Surrogate and Other Statistical Models," NASA NESC, NTRS 20200002832
Relates to: Encoding_Protocol_v0_1 outline (the protocol this pilot informs), Ch4 Numbers and Repairs Spec v1.0 (ledger rows unaffected by this spec), Decision Record 2026-08-19 (R5)
Execution: Claude Code, with every disposition returned to the author as DRAFT

## 0. Purpose and the one boundary that matters

This is a pilot run of the encoding procedure on a fresh, real, published document, executed before the protocol document exists, to surface the friction points the protocol must govern. Its outputs are (a) a pilot package in DRAFT state and (b) a findings memo keyed to the protocol outline's section numbers, which the author consumes when writing Encoding_Protocol_v0_1.

The boundary: **extraction, citation anchoring, and candidate dispositions are session work; every disposition is DRAFT until the author's review pass.** The praxis claim (A9) is that human judgment enters at the review pass and the disposition procedure. This session drafts; it does not adjudicate. After the protocol is written, the formal review, final dispositions, ambiguity log confirmation, and signing run under the written protocol, so the governed acts are provably post-protocol in the git record. Do not sign anything in this session. Do not place anything under `packs/`. All pilot artifacts land under `dev/build/pilot-johnson/`.

Chapter role, for context only: Johnson becomes the real-document aerospace anchor. The synthetic aero take-off/cruise encodings still run later under the written protocol to close the three PENDING-ENCODING ledger rows against the April ground truth. This spec touches neither.

## 1. Source scoping (30 min, before any extraction)

The paper is unusual and the pilot is stronger for it: it is a real NTRS publication whose worked example is a deliberately disguised real aerospace application (tire puncture regression for PRA input). Establish before extracting:

1. **The COU.** One context of use: the regression model's predictions used as PRA input for the tire-burst risk decision. State it in the package as the paper states it.
2. **The M&S artifact.** The multiple linear regression model (velocity, orientation, interaction term) plus its Excel calculator delivery. The paper's own credibility assessment covers this artifact.
3. **Admissible evidence inventory.** List every element of the paper that carries evidentiary weight before extraction begins: the predeclared credibility table (Table 3 shading), the achieved credibility assessment (the eight factor levels with rationales), the M&S 32–39 reporting responses, the LCW worksheet responses, the caveats table, the radar plot. Record page/section/table anchors for each in the inventory. This inventory is the pilot's test of the protocol outline's §2 (source intake): note anywhere the outline's admissibility framing is insufficient for a document like this.
4. **Known vocabulary hazard, pre-declared:** the paper applies 7009A; the pack encodes 7009B. Any place the A-to-B mapping is not mechanical is a mandatory ambiguity-log entry, not a silent resolution. Expect several; they are pilot findings, not defects.
5. **Known provenance note:** the example is "highly disguised" per the paper. The package encodes what the paper states, cited to the paper. The disguise is one admissibility note in the findings memo, not a reason to editorialize values.

## 2. Extraction and citation anchoring (the pilot's core, 2-3h)

Follow the published on-ramp (uofa.net/start/from-excel, pin the site commit in the run log) with the pack named: extract against the source, open the workbook, populate.

**Model: Anthropic Sonnet**, the same frontier model the extraction eval used, passed via the extractor's Anthropic provider path. Record the exact model string, provider path, and any thinking-mode setting in the run log, same discipline as pinning the site commit. Do not substitute Ollama or any other backend; if the Anthropic path fails in this environment, escalate rather than swap.

Rules for this session:
1. **Every populated cell carries a citation anchor** to page, section, table, or figure of the NTRS PDF. Decide a home for it (citation column per sheet is the default; if the workbook template has no home, add one and record the template change as finding F-2b for the protocol's §2b prompt).
2. **No cell passes on extractor confidence.** Cells are populated-with-anchor, or left blank and listed. Blanks are not failures; they are the §3b findings.
3. **Values living in figures or shaded tables** (the predeclared levels live in Table 3's shading; the achieved levels in the assessment table; the tolerance bound in the results row) get anchored to the figure/table by name. Record each as a worked-example candidate for the protocol's §2c prompt. The Table 3 shading is precisely the "value located somewhere non-obvious" case.
4. **Run the provenance self-audit** (§3c shape): after import, record the provenance counts and reconcile against the count of cells you anchored. Any surprise is a finding, not something to fix silently.

## 3. Candidate dispositions, DRAFT only (2-3h)

Run `uofa rules` on the imported package. For every weakener the engine raises, and for every factor the pack expects a disposition on:

1. Draft a candidate disposition (Accepted / Not Accepted / Not Applicable) **with the source text quoted or anchored** that supports it.
2. **State the rule applied, in testable form**, one sentence: "Accepted because the source states X at [anchor]." Where no testable rule can be written from source text, mark the candidate JUDGMENT-CLASS and write "author judgment required, considering [the consideration]." Do not resolve it.
3. The paper hands the pilot several deliberately hard cases; treat these as the §4d worked-example candidates: validation waived by TA decision (Not Accepted vs NA under a documented waiver); the M&S History level negotiated by the team (source states the negotiation, not just the level); the incomplete randomization caveat (assumption violation, disclosed, judged inconsequential by SMEs — whose judgment does the encoding record?); the outlier retained with stated rationale.
4. Output: a dispositions table, every row DRAFT, with columns: pattern/factor, candidate verdict, source anchor, rule-as-applied (testable or JUDGMENT-CLASS), confidence note.

## 4. Ambiguity log (running, throughout)

An entry is mandatory whenever the source underdetermines a field: two plausible readings, an implied value, a unit ambiguity, or a 7009A-to-7009B mapping that is not mechanical. Entry shape: the ambiguity, the resolution the session chose for the DRAFT, the rule it applied choosing it. The author re-adjudicates every entry in the review pass. Expected sources beyond the A/B mapping: the "Level 0" convention, the waived-verification cells, the disguise's effect on RWS fields, the worksheet questions the paper answers "will not be covered."

## 5. The findings memo (1h, the deliverable A7 consumes)

`dev/build/pilot-johnson/PROTOCOL_FINDINGS.md`, organized by the protocol outline's section numbers (§1 through §8). For each section: what the pilot did, where the outline's prompt was sufficient, where practice needed a rule the outline doesn't have, and the concrete case demonstrating it. Mark each finding as one of: RULE-NEEDED (protocol must state it), TEMPLATE-CHANGE (workbook needs a home for it), TOOLING (protocol-check candidate), NO-FINDING. The memo is scaffolding for the author's writing pass, not prose for the protocol; keep it as a table plus short notes.

## 6. Done-gate and escalation

Done when: import passes with every mandatory field populated or explicitly blank-listed; citation anchors present on every populated cell; the dispositions table complete with every row DRAFT; the ambiguity log populated; provenance counts recorded and reconciled; the findings memo committed under `dev/build/pilot-johnson/`; nothing signed; nothing under `packs/`; no ledger row touched.

Escalate rather than resolve: any place the pack's vocabulary cannot express something the paper states (that is a schema finding, INV-20's territory, and it must not be worked around); any mandatory field the source genuinely does not carry (candidate source-absent, but flag the first few for author calibration); anything requiring an actual disposition decision rather than a draft.

## 7. What this spec does not do

No signing, no case-study placement, no tier-table entry, no ledger changes, no protocol prose, no synthetic aero encoding. The sequence after this session: author writes Encoding_Protocol_v0_1 from the findings memo plus Morrison recall; the Johnson package then gets its governed review-disposition-sign pass under the written protocol; the synthetic aero bundles run the same path to close the ledger.
