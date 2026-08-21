# Protocol findings — the Johnson pilot

Input for writing `Encoding_Protocol_v0_1`. Organized by the section numbers in
`docs/Encoding_Protocol_Outline_and_Prompts.md`. Scaffolding for the author's
writing pass, not prose for the protocol.

Tags: **RULE-NEEDED** (protocol must state it) · **TEMPLATE-CHANGE** (workbook
needs a home for it) · **TOOLING** (protocol-check or code candidate) ·
**NO-FINDING**.

Everything the pilot produced is DRAFT. Nothing was signed, nothing was placed
under `packs/`, no ledger row was touched.

---

## The three findings that matter most

Read these even if nothing else.

**1. The source's required-level column was unreadable, and the extractor filled
it anyway.** Johnson shades his predeclared levels into Table 3 rather than
writing them. The extract prompt's documented default — "set `required_level =
achieved_level`" — fired on 17 of 17 factors, producing a complete, plausible,
schema-valid column that came from nowhere and erased both exceedances the paper
exists to demonstrate. Nothing downstream can catch this. §2 and §3 both need a
rule.

**2. Provenance counts cannot see the human.** After 97 review decisions across
155 cells, `uofa import` reports **4 extracted**. The count classifies eleven
summary fields and no factor, validation result or decision, so it cannot
distinguish a package reviewed cell by cell from one imported straight out of the
extractor. §7's whole argument rests on this number.

**3. Honest and non-misleading are not both available for this source.** Refusing
to rewrite 7009A's 0-4 levels onto V&V 40's 1-5 factors leaves 13 of 19 factors
without levels, and every derived metric reads 0.00 — including
`verificationCoverage 0.00` for a paper stating Verification achieved 4. Invent
the levels and the package overstates; decline and it understates. The protocol
cannot resolve this; it can require that the choice be disclosed.

---

## §1 Purpose and scope

| # | Finding | Tag |
|---|---|---|
| F-1a | The outline's Prompt 1c tells the encoder to pin the site commit and names `01c7372`. The commit currently building the on-ramp is `31cb466`. A protocol that mandates a pin needs a rule for when its own example pin has moved on. | RULE-NEEDED |
| F-1b | The on-ramp page never mentions `base_uri`. Import warns that identifiers are minted under the `example.org` placeholder and that "the id is covered by the signature, so this cannot be changed after signing." An encoder following only the published on-ramp signs a package in a namespace they do not control. | RULE-NEEDED, TOOLING |
| F-1c | §2 of the pilot spec says to use "the same frontier model the extraction eval used". No such model exists: `docs/extract_eval_v1.md` ran its extractor on local `qwen3.5:4b` and `extract_accuracy_log.jsonl` has zero Anthropic rows. The protocol should require an encoding to name its extractor by version and state what it is **not** the same as, rather than inheriting a lineage claim from a spec sentence. | RULE-NEEDED |

## §2 Source-evidence intake

| # | Finding | Tag |
|---|---|---|
| F-2a | **Admissibility needs a within-document distinction.** Johnson is half evidence about a model and half tutorial about the Standard, interleaved paragraph by paragraph and written in one voice. Prompt 2a's framing ("the published paper") admits both. `SOURCE_SCOPING.md` §3 had to draw the line by hand before extraction. | RULE-NEEDED |
| F-2b | **The workbook has no home for a citation anchor, and the home added does not survive import.** A `Source Anchor` column appended past the columns `_read_factors` reads is provably non-breaking — the reader's payload is byte-identical with and without it, 5294 bytes both ways — and that is exactly why the anchors never reach the JSON-LD. They live where humans review and are absent from what a downstream reviewer receives. | TEMPLATE-CHANGE, TOOLING |
| F-2c | **Anchor granularity does not fit the artifact.** §2.1 asks for an anchor per *cell*; a spreadsheet row is the natural unit and one row often cites several pages. Resolved here by carrying a row-level anchor in the workbook and the cell-level anchor in `REVIEW_LEDGER.md`. The protocol should say which it requires. (A-20) | RULE-NEEDED |
| F-2d | **The §2c worked example, in a harder form than the prompt anticipates.** Johnson's predeclared levels are green cell fill on p.7 with no text at all. Recovered from page geometry with pdfplumber (`table3_recover.py`), corroborated three ways against text the recovery did not use. Proposed rule: *where a value is recoverable only by non-textual means, the citation anchor names the recovery method as well as the location, the value is recorded as an author-side correction rather than extractor output, and the method ships with the encoding.* | RULE-NEEDED |
| F-2e | **A source that declares itself disguised.** "highly disguised as a test of puncture resistance" (p.5). The encoded RWS is faithful to the paper and knowingly not to the world. The protocol needs a disclosure rule; a reference encoding whose source is disguised is not a defect but must not be silent. | RULE-NEEDED |

## §3 The extract-review-import procedure

| # | Finding | Tag |
|---|---|---|
| F-3a | **"No cell passes on extractor confidence" is necessary and not sufficient.** The extractor's confidence was honest — 141 of 142 cells came back yellow. Reviewing against the extractor's own rationale still fails, because a synthesized value arrives with a plausible rationale attached. Proposed rule: *a cell is reviewed against the source location that should carry it, not against the extractor's output; where the source carries it in a form the extractor cannot read, the reviewer must know to go looking.* | RULE-NEEDED |
| F-3b | **The required-level column specifically.** The prompt's `required_level = achieved_level` default converts an unreadable source field into a confident value on every factor. Proposed rule: *required and achieved levels are reviewed against different source locations and confirmed separately; a required level equal to achieved on every factor is treated as unreviewed until the predeclaration is located.* Tooling counterpart: protocol-check can flag required==achieved across all factors. | RULE-NEEDED, TOOLING |
| F-3c | **Review has three verbs and the pass needed a fourth.** §2 defines confirm / correct / mark-source-absent, all acting on an existing cell. W-NASA-03 (D-10) is clearable by adding a `ProcessAttestation` row the source plainly supports (p.25), which no verb covers. The pass declined and escalated. (A-24) | RULE-NEEDED |
| F-3d | **`write_extraction` leaves template hint text in data rows.** Placeholders survived in `Assessment Date`, `Model & Data` E3/F3, and `Validation Results` C3/G3/H3, arriving at import looking like data. The clearing logic runs only where the model wrote a value. | TOOLING |
| F-3e | **Import reports a profile it did not write.** `uofa import` printed `Profile: Complete`; the package carries `ProfileMinimal`. `import_excel.py:169` prints the workbook's declared value while `derive_profile` computes the real one — and that function's docstring names declaring-what-the-spreadsheet-said as the bug it exists to fix. One-line fix. | TOOLING |

## §4 Disposition procedure

| # | Finding | Tag |
|---|---|---|
| F-4a | **Source or package? The outline does not say.** Nine of twelve firings are true of the package and false of the source. Adjudicating on the source reading suppresses warnings that are correct about the artifact the reviewer holds. §4 must state which object a disposition adjudicates, or require both. This is the pilot's largest §4 gap. | RULE-NEEDED |
| F-4b | **The source contradicts itself, and §5's trigger does not cover it.** The ambiguity-log trigger fires when the source *underdetermines* a field. Johnson is over-determined and inconsistent three times: the TA waiver described and denied in one response (p.8) and answered "None" at p.23; verification waived at p.6 and rated 4 on independent verification at p.25; [M&S 37] declined at p.10 and answered in full at p.24. Morrison never produced this case. Only the third has a defensible ordering rule (*an answer outranks a declination; the declination is context*). | RULE-NEEDED |
| F-4c | **Disposition vocabulary collision.** The spec asks for Accepted / Not Accepted / Not Applicable. `uofa:Disposition.actionClass` is a different controlled vocabulary — restrict-cou, acquire-validation, characterize-region, accept-residual-risk, change-cou. §4 must name which it means and whether the two ever meet. | RULE-NEEDED |
| F-4d | **Worked-example candidates**, all present and all harder than Morrison's: the TA-waived validation (D-06, the one firing that is right on both readings), the negotiated M&S History predeclaration (p.7-8), the incomplete randomization judged inconsequential by SMEs (p.8, p.15, p.23 — whose judgment does the encoding record?), and the retained outlier (p.21, "pulling it less than 0.003 cm in nonconservative direction"). | NO-FINDING (material, not a gap) |
| F-4d, ruled 2026-08-21 | All four candidates are now adjudicated. **The TA-waived validation** is D-06, ruled Confirmed with an offsetRationale anchored p.19 and **designated the protocol v0.2 worked example**. **The negotiated M&S History predeclaration** (p.7-8, carried on `Use history`, row 23) is **CONFIRMED**: the value is carried and the provenance note that the predeclaration was negotiated stands with it. It is recorded here rather than in the ambiguity log, because it was never a log entry — the E-1 round-trip established that. **The incomplete randomization** and **the retained outlier** became ambiguity entries A-29 and A-30, ruled the same day: the first recorded as the source's SME judgment and not encoder endorsement, the second recorded as disclosure without an encoder ruling. | NO-FINDING (material, now adjudicated) |
| F-4e | **Silence is not a clean bill.** The eleven factors carrying no level and a non-`assessed` status drew no weakener, because W-CON-01 excludes those statuses by design. The encoding's largest gap is the one the engine says least about. §4 needs a rule for dispositioning factors no rule raised. | RULE-NEEDED |

## §5 The ambiguity log

| # | Finding | Tag |
|---|---|---|
| F-5a | 25 entries, of which **two are escalations left unresolved** per spec §6: `Input pedigree` has no factor anywhere in the pack though Johnson predeclares and achieves it at 3 (A-07), and Level 0 is inexpressible on 13 of 19 factors (A-08). Both are INV-20 territory. The log needs an entry class that is explicitly *not* a resolution. | RULE-NEEDED |
| F-5b | The outline's §5b suggests a log sheet in the workbook. This pilot's log is a separate committed file because 25 entries with quoted source text do not fit a spreadsheet column, and because the escalations must survive independently of the package. | TEMPLATE-CHANGE |
| F-5c | Prompt 5a's worry — "if you cannot recall any, that likely means they went unrecorded" — is answered emphatically. A single real paper produced 25 in one session, 19 of them before extraction even ran. | NO-FINDING |

## §6 Completion and the stopping rule

| # | Finding | Tag |
|---|---|---|
| F-6a | **The done-gate's "import passes" is satisfied by a package that understates its source.** Import passed, SHACL conformed, and all four derived metrics read 0.00. A stopping rule keyed on import success cannot see this. §6 needs a completion check on the derived metrics, or an explicit statement that they are not part of completeness. | RULE-NEEDED |
| F-6b | The profile is derived, not asserted, and the pilot earned Minimal rather than the declared Complete — correctly, and the machinery worked. §6a's claim that "the import already derives it" holds. | NO-FINDING |
| F-6d | **An unsigned package does not raise the missing-signature weakener.** `excel_mapper` writes `hash = "sha256:" + "0"*64` and `signature = "ed25519:" + "0"*128` as placeholders for `sign_file` to replace. W-SI-01 fires on `noValue(?uofa, uofa:signature)`, and a zero-filled placeholder is a value, so it never fires. C1 integrity correctly reports both as invalid, so nothing is broken — but the C3 weakener report, which is the summary a reviewer reads, is silent about a package that was never signed. Directly relevant to this pilot, whose whole point is that it is unsigned. | TOOLING |
| F-6c | Protocol-check candidates from this pilot, all scriptable: citation column present and non-empty on every populated row; ambiguity log exists and is non-empty; no `--sign` in the run log; required != achieved on at least one factor, or an explicit waiver recorded; no template placeholder strings in data rows. | TOOLING |

## §7 Provenance and the human contribution

| # | Finding | Tag |
|---|---|---|
| F-7a | **The counts cannot see the review pass.** 97 decisions, 155 cells, 47 confirmations, 14 corrections → `4 extracted`. `_provenance` classifies eleven summary-level fields and nothing else. A cell-by-cell reviewed package and a straight-from-extractor package report identical counts. Prompt 7a's paragraph ("the counts are the auditable record of how much of the package the human shaped") is **not currently true**, and it feeds Ch3 nearly verbatim. | TOOLING, RULE-NEEDED |
| F-7b | **No provenance class says "author-side recovery".** The five required-level cells recovered from Table 3's shading are human work by any reading and are counted nowhere. `extracted` would be false; `run-context` and `defaulted` are wrong. | TOOLING |
| F-7c | Until F-7a is fixed, the protocol should require a review ledger committed beside the package, as this pilot's `REVIEW_LEDGER.md`. It is the only artifact that records what the human did. | RULE-NEEDED |

## §8 Versioning and deviation

| # | Finding | Tag |
|---|---|---|
| F-8a | The deviation rule works and was exercised: the anchored-fan-out ruling, the anchor-granularity compromise (A-20) and the declined evidence-row addition (A-24) are all recorded with rationale. | NO-FINDING |
| F-8b | An encoding must record the **pack version and the standard version separately**. This package is `nasa-7009b` 0.5.0 encoding a `NASA-STD-7009A` assessment, and those are different facts. Note `resolve_criteria_set("NASA-STD-7009")` folds the version-agnostic alias onto the **7009B** identifier, so a 7009A assessment entered the natural way is silently graded as 7009B. | RULE-NEEDED, TOOLING |

---

## Cross-cutting: things the workbook cannot carry

Eight of twelve weakener firings trace to this, so it is worth stating once
rather than per-section.

| Missing | Source has it | Consequence |
|---|---|---|
| `SensitivityAnalysis` node / `hasSensitivityAnalysis` | p.22 [M&S 30]; p.25 Results Robustness 4 | W-AL-02, W-NASA-06 fire. The class, its shape and the property all exist in `uofa_shacl.ttl`; the name appears **nowhere** in `excel_constants.py`, `excel_reader.py` or `excel_mapper.py`, so the published on-ramp cannot produce one. Three shipped rules key on it. Morrison, hand-authored, also lacks it and fires W-CON-04 |
| COU `hasApplicabilityConstraint` / `hasOperatingEnvelope` | p.19 [M&S 14]; p.19 [M&S 18]; p.18 [M&S 16]; p.23 [M&S 26] | W-ON-02 fires. **Known observation**: the Ch4 spec records it on 65/71 queue packages and asks for verification against canonical encodings — this pilot is one, and Morrison COU1 fires it too |
| An offset-rationale route for a validation-result firing | p.19 — no RWS data exists, test data served as referent, tolerance bound and PRA context bound the use | D-06 is Confirmed **with** an offsetRationale, and the rationale has nowhere to go. `uofa:OffsetRationale` and `hasOffsetRationale` are in the v0.5 context and `packs/vv40/examples/nagaraja/cou1` carries one, but `excel_mapper.py` has no offset handling and the template has no column. Nagaraja's `refersToFactor` also points at a *factor*, and D-06's firing is on a validation result, so the referent shape is an open question too. **Ruled 2026-08-21: disposition record only, no package node** — same rule as the envelope gap below. Filed beside it |
| A comparator identity for non-entity comparators | p.17, p.24, p.19 | W-AR-05 ×5. `Compares To` expects a URI; SME judgment and "no RWS data available" are not URI-shaped. Import drops them as non-well-formed subjects |
| `Input pedigree` factor | p.25, predeclared 3 / achieved 3 | No disposition possible. ESCALATION |
| Level 0 on V&V 40 factors | p.7 Table 3 convention | Not triggered by Johnson; would block a 7009A encoding that used it. ESCALATION |

## What the pilot did not test

Stated so the memo is not read as broader than it is. One COU, one source, one
extractor, one session, and no second encoder. The A-to-B mapping findings are
specific to a 7009A source encoded under the 7009B pack and say nothing about a
source written against 7009B directly.

**Update, 2026-08-21.** The disposition table has now been through the author's review
pass, and §4's rules were tested by it. Every verdict is in `DISPOSITIONS_DRAFT.md`, the
session record is `Johnson_Author_Verdict_Record.md`, and the divergences the pass
surfaced between the record and the artifacts are in `APPLY_RECORD_ESCALATIONS.md`. Three
findings from this memo were filed to the schema channel as SF-4, SF-5 and SF-6. Still one
COU, one source, one extractor and no second encoder.
