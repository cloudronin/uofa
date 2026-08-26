# UofA Spec — The Canonical Lifecycle Example: "The Stranger Signs Johnson" v1.0

Date: 2026-09-10
Status: RULED. One example, three registers, one contrast frame. Sources of truth: the Attestation Model Complete Reference v1.0, the Unified Signing Surface spec (§8 two-role addendum), the Encoding Protocol v0.1, Praxis Writing Plan v3.1 (freeze rules bind the praxis register). Consumers: the praxis figure order (§3.4 / §4.7), the docs pass (getting-started, uofa.net), the book note, the NAFEMS deck.
Origin: the Johnson flow exercises every layer the framework has — prose in, extraction, anchors, per-cell levels judgment, dispositions, an OWNED decision (asserted — the paper reports results and decides nothing, so the verdict is genuinely the reviewer's), two-scope signing, and independent verification by the published wheel. Morrison demonstrates the extracted branch; Johnson is the lifecycle case because the judgment is live: every seam the thesis cares about is crossed on camera.

## 1. The contrast frame — before and after (the figure's top band)

The example always opens with the same two-panel contrast. Same inputs, same intent, different worlds.

### BEFORE (how this is done today, stated fairly)
A reviewer reads Johnson's paper. They assess credibility against V&V 40 / 7009B factors in their head or on a checklist. Findings land in a review memo or a spreadsheet; the evidence is cited by page number ("see §3.2, Table 4"). The assessment is signed — one signature, on the whole document, meaning everything and therefore nothing specific: argument, evidence citations, and judgments indistinguishably covered. The record of WHO judged WHAT is the memo's letterhead plus the QMS's sign-off sheet, filed beside the work. Five failure modes, each real and none exotic:
1. **Citations rot** — the cited report is revised; nothing in the assessment notices.
2. **Agreement is silent** — whether the reviewer weighed factor 12 or ratified a template leaves no residue; diligence and rubber-stamping are byte-identical.
3. **The signature smears** — one wet signature spans machine facts and human judgment; a reader cannot tell what the signer actually vouches for.
4. **Verification is a meeting** — checking the assessment means convening humans to re-read documents; a stranger cannot re-verify anything.
5. **The transformation is ungoverned** — how prose became the checklist's ticks is nobody's procedure; the standards govern the assessment, not its capture.

### AFTER (the same review, through UofA)
The same paper, the same standards, the same human judgment — with structure at every boundary:
1. Citations are **sha-pinned anchors** — resolution is machine-checked; a revised source breaks loudly.
2. Judgment **leaves residue** — every required level carries `affirmed`/`corrected` provenance with an attributed agent; ratification is distinguishable from review because agreement is an act.
3. The signature **carries its scope** — the issuer seal covers what the environment can attest (origin, integrity, well-formedness); the reviewer's signature covers the decision layer; one signature may never span both, and the format refuses the confusion.
4. Verification is **a command** — `uofa verify` re-derives every machine-checkable fact and reports, per signature, who stands behind what. A stranger with only the public wheel re-verifies everything.
5. The transformation is **governed** — a versioned, stranger-validated encoding protocol with adjudication on the record; every rule written against an observed failure.

One sentence under the panel, all registers: *the human judgment is unchanged; what changed is that everything around it stopped depending on anyone's vigilance.*

## 2. The lifecycle skeleton (shared by all three registers)

Three swimlanes by attestor kind — the attestation model's own organizing principle:

| # | MACHINE lane (attributed, never signs) | HUMAN lane (judges, signs) | RECORD lane (what accumulates) |
|---|---|---|---|
| 1 | `uofa extract` drafts the workbook from the paper | — | draft workbook; run log pins (which model read, which drove — never self-reported) |
| 2 | anchors proposed per claim | reviewer hunts, confirms/corrects anchors | sha-pinned anchors |
| 3 | required levels pre-filled (defaulted) | reviewer **affirms or corrects each level** — the sufficiency judgment, per cell | `affirmed`/`corrected` provenance + attributed activity |
| 4 | rules run; weakener patterns fire | reviewer dispositions each finding (Confirmed / Overruled / NA), records ambiguity entries | dispositions with rationales; the ambiguity log |
| 5 | protocol check names any residue | reviewer discharges or waives, on the record | owed-work trail; waivers with reasons |
| 6 | — | reviewer renders the decision — outcome, rationale, their name, now (`asserted`) | the decision record: actor + timestamp, owner required |
| 7 | the environment seals: `--as issuer` (measurement view; decision layer excluded by construction) | the reviewer signs: `--as reviewer` (decision layer, binding the measurement hash it judged) | two signatures, two scopes, each meaning one thing |
| 8 | — | — | **a stranger runs `uofa verify`** — anchors resolve, provenance checks, both signatures verified, relations derived and reported ("decided by the signer") |

Every arrow crossing machine→human is a judgment handoff; every RECORD-lane artifact answers "who stands behind this?" The lifecycle ends where the recursion bottoms out: a key in a human hand.

## 3. The three registers (what each may claim)

### 3a. Praxis register — IN-FREEZE, legal now
- **Form**: the §3.4 swimlane figure (already ruled; funded by dropping Fig 3.3) + §4.7's Johnson worked example as a traversal of the figure. The BEFORE panel's five failure modes are all in-freeze claims (they motivate C1–C4 and are already stated across Ch1–Ch2); the AFTER panel uses only results-version machinery: anchors, the protocol, the review ledgers, UOFA_ASSESSOR, the dual-scope signing that exists in the CLI at the results version.
- **May NOT claim**: the affirm act, v0.9 vocabulary, the two-role surface, runs 25/26, Credenza beyond the one sentence. Rows 3 and 7 phrase to the results-version mechanisms (required-equals-achieved review per the protocol; signed decision record per §3.4.6's two sentences).
- **Caption discipline**: per v3.1 — no legal-frame language, no post-freeze terms; the contrast sentence is the caption's close.

### 3b. Product register — post-release (step 7's wheel)
- **Form**: getting-started's walkthrough and uofa.net's front-page arc retell the same skeleton as the canonical path: paper in → `uofa extract` → review, affirm, disposition → decide → `uofa sign --key K --as issuer,reviewer` → `uofa verify`. The BEFORE/AFTER contrast is the landing frame ("how credibility review works today / with UofA").
- **The published reference artifact**: when run 26 passes, its package ships in the repo as the canonical example — the stranger-produced, dual-signed, wheel-verifiable Johnson package. The docs' standing line: *download it and run `uofa verify` yourself; everything this page claims, you can check.* No competing framework's documentation can write that sentence.
- Until run 26 passes, the deployed smoke's Walk A package serves as the interim reference (scripted, labeled as such).

### 3c. Book / NAFEMS register — the full story
- **Form**: the week as narrative — the runs, the walls, the rules written against them (the rule-to-failure table's densest stretch), the constitutional findings, the roles collapsing onto the thesis. The three-register figure appears with its full v0.9 vocabulary: the fork, derived relations, the two-role surface.
- **The claim the praxis cannot make and the book must**: the road-building was the research — the framework's own layered checks caught representational gaps in the framework itself, and every rule in the newest layer was purchased by a first traversal. Zeno's runner arrives carrying the evidence.

## 4. Build and sequencing

1. **Figure spec to Claude Code as a side order** (the v3.1 plan already assigns figure work there): the two-panel contrast band + the three-lane skeleton, praxis phrasing per §3a, one composite at half a page. Deadline: with W3's Ch4 work, since §4.7 traverses it.
2. **Docs pass** (attestation-boundary plan step 10) adopts §3b: the walkthrough restructures around the canonical path; the BEFORE/AFTER frame lands on uofa.net's front page; the reference-artifact line ships when run 26's package does.
3. **Book note gains one line**: the canonical example's name and this spec's path — the redraft session inherits it as Part III's opening exhibit.
4. **Nothing here moves a number, adds a praxis claim, or touches the freeze** — the praxis register is a presentation of in-freeze material; the other two registers ride their own clocks.

## 5. One line

One example, told three ways at three depths, always the same arc: prose in, judgment made visible, everything signed by exactly who can stand behind it, and a stranger who can check it all with one command — before UofA, a filing cabinet and a promise; after, a package and a proof.
