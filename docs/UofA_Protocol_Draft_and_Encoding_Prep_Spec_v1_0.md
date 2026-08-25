# UofA Protocol Draft and Encoding Prep Spec v1.0

Status: ACTIVE
Date: 2026-08-20
Owner: Vishnu Vettrivel
Relates to: Encoding_Protocol_Outline_v3 (the drafting instruction set), PROTOCOL_FINDINGS.md and all pilot artifacts (dev/build/pilot-johnson/), Decision Record 2026-08-19 (R5), Ch4 Numbers and Repairs Spec v1.0 (three PENDING-ENCODING ledger rows)
Execution: Claude Code drafts and preps everything below. The author's work is confined to: reading and correcting the protocol draft, the review passes, and the verdicts. Nothing in this spec asks the author to produce a first draft of anything.

## 0. Division of labor, binding

Claude Code produces: the protocol draft, the reverse-engineered §4b rules as candidates, all workbooks extracted and anchored, all candidate dispositions, all ambiguity log entries, all run logs, and the verification harness.

The author alone performs: correction of the protocol draft (red pen, not blank page), the §3b review pass on each encoding (walking cells against source), final verdicts on every disposition, and re-adjudication of every ambiguity entry. These acts are the praxis's human-adjudication claim and are never simulated, pre-filled as final, or marked complete by the session. Every author-reserved artifact ships in DRAFT state with an explicit AWAITING-AUTHOR marker.

## W1 — Draft Encoding_Protocol_v0_1.md (session work, 3-4h)

Draft the full protocol from Encoding_Protocol_Outline_v3, treating every prompt as an instruction to write the rule, not to ask the author for it. Sources, in precedence order: the outline v3, PROTOCOL_FINDINGS.md, the pilot artifacts (REVIEW_LEDGER.md, AMBIGUITY_LOG.md, DISPOSITIONS_DRAFT.md, TABLE3_RECOVERY.md, RUN_LOG.md), and the committed Morrison/Nagaraja dispositions.

Rules for the draft:
1. **§4b per-family rules are reverse-engineered, not invented.** For each weakener family, open the committed Morrison COU1 (and COU2 where NA/Not-Accepted cases live) dispositions, take two or three per family, and write the candidate rule that reproduces the recorded verdict from the recorded source anchor. Each rule carries a footnote citing the disposition it was derived from. Where no testable rule reproduces the verdict, write the JUDGMENT-class form ("author judgment applying [the consideration visible in the record]") and flag the row AUTHOR-CONFIRM. Do not smooth: if two Morrison dispositions imply conflicting rules, present both with anchors and flag AUTHOR-RESOLVE.
2. **Voice constraints are binding on the draft**: no em dashes, no tripartite lists, no colon chains, prose over bullets, no AI writing tells, direct declarative sentences. The author edits this document, so it must arrive close to his register; read docs/ch3-methods-principles.md and the Phase 2.5a REPORT for the register.
3. **Length is a gate**: 4-6 pages. The outline absorbed three documents of scaffolding; the protocol does not. Every [PILOT]/[F-nn] tag in the outline becomes at most one rule sentence plus at most one example sentence in the draft. The findings memo is cited, not reproduced.
4. **Structural markers for the author's pass**: every §4b rule row and every sentence the draft is less than confident reproduces the author's actual practice gets an inline [AUTHOR-CONFIRM] marker. The author's correction pass is a walk of those markers plus a full read. Target: fewer than 25 markers.
5. Commit as docs/Encoding_Protocol_v0_1_DRAFT.md. The author's corrected version becomes Encoding_Protocol_v0_1.md and is committed by the author alone (same convention as decision records; the protocol is an authored praxis artifact).

## W2 — Protocol-check flag (2-3h, parallel to W1)

Implement protocol-check as a flag on the existing commands, not a separate command: `uofa extract --protocol-check` runs the workbook-side checks after extraction, and the same flag on `uofa import` runs the package-side checks at import time (if a single flag home is cleaner, put it wherever the check naturally executes and say so in the session report; the constraint is no new top-level command). Checks, from findings F-6c: Source Anchor column present and non-empty per populated row; ambiguity log file exists and non-empty; required != achieved on at least one factor or an explicit waiver recorded; no template placeholder strings in data rows; run log carries model string, backend, site commit, repo HEAD, base_uri; no --sign in a pilot-labeled run log. Output is a pass/fail table per check, non-zero exit on any fail. This flag runs in W3-W5 before any artifact is handed to the author, so the author never reviews a workbook that fails mechanical checks.

## W3 — Johnson governed-pass prep (1-2h)

Bring the pilot's Johnson artifacts to author-ready state under the draft protocol: apply the fourth-verb candidates (evidence rows the source plainly supports, each marked DRAFT with anchor), clear template placeholder residue, set base_uri properly (re-import; the pilot minted under example.org), re-run rules, refresh DISPOSITIONS_DRAFT.md against the current catalog with the §4e silence sweep added (every expected factor gets a row, including the eleven no-firing factors, each with a candidate disposition or declined-mapping marker), and produce REVIEW_PACKET_JOHNSON.md: the ordered list of exactly what the author must do, cell ranges to walk, the 25+2 ambiguity entries to re-adjudicate, the disposition rows to verdict, estimated at his measured adjudication pace with batch-of-10 breaks. The packet is the author's evening; make it walkable start to finish without tool commands.

## W4 — Synthetic aero encoding prep, both COUs (2-3h)

Run the full extract-anchor-draft pipeline on the two committed synthetic evidence bundles (take-off, cruise) under the draft protocol: extraction with the declared model string per §1e, anchors per §2b, candidate dispositions with the silence sweep, ambiguity entries, run logs, protocol-check green. April ground-truth comparison prepared but not adjudicated: a delta table of expected_weakeners vs current firings, version-labeled per the C5 convention (April expectations were written against an April catalog; R1a and v0.5.x refinements produce labeled deltas, not failures). Output: REVIEW_PACKET_AERO_COU1.md and _COU2.md, same walkable format as W3.

## W5 — Bologna encoding prep (1-2h, same pipeline)

Same pipeline on the Bologna source for the A3 negative-control package. Its packet notes the chapter role: FP result on the negative arm; gate passes reported as properties of the negative control, not a case-study row. If the Bologna source materials are not yet assembled in the repo, this item is INVESTIGATION: report what exists and what is missing rather than substituting sources.

## W6 — Assembly and sequencing output (30 min)

One file, AUTHOR_QUEUE.md: the ordered list of author acts this spec leaves behind, each with its input artifact, its output artifact, and a realistic time estimate. Expected shape: (1) correct protocol draft (~1h read plus marker walk); (2) commit protocol; (3) Johnson review packet (one evening); (4) aero COU1 packet; (5) aero COU2 packet; (6) Bologna packet; (7) sign-off commits, each of which flips ledger rows per the Ch4 spec. Nothing else. If the queue exceeds these seven items, the spec has failed its purpose; escalate rather than append.

## Sequencing

W1 and W2 parallel-now. W3-W5 after W1's draft exists (they run under it) and W2 is green. W6 last. Author acts interleave at his pace; no session waits on him except where a packet is consumed.

## Escalation

Standing criteria, plus: any §4b family where the Morrison record supports no rule at all (not even a JUDGMENT form); any Johnson or aero artifact that cannot reach protocol-check green without an author decision; Bologna source gaps per W5; any place the draft protocol and the pilot findings genuinely conflict rather than compose. Escalations go in the packet for the author's pass, not in chat threads.

## Out of scope

Signing anything. Final verdicts. Marking any review complete. Ledger row changes (those flip only on the author's sign-off commits). The v0.6 schema increment. Any writing-queue manuscript prose.
