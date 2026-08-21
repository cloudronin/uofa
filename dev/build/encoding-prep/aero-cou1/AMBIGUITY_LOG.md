# Ambiguity log — aero cou1

**ADJUDICATED 2026-08-21 — awaiting assent and signature.** Every entry has been
re-adjudicated by the author; what remains is the author's assent to
`AUTHOR_SUMMARY_COU1.md` and the signature. The original DRAFT resolutions are left as
written below, because they record what the draft decided; the author's verdicts are in the
adjudication section at the end. Entry shape per
§5 of the protocol draft: the ambiguity, the resolution chosen for the DRAFT, the rule
applied choosing it.

This log is shorter than the Johnson pilot's twenty-eight, and the reason is structural
rather than a sign of less care. Johnson is a real 7009A paper encoded under a 7009B pack,
so most of its entries are cross-standard mapping decisions. These bundles were authored
against this pack, so that whole class does not arise.

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| G-01 | Citation anchors. The extractor records no per-cell source document, although the on-ramp page says "Hover a cell for the document it came from"; the cell comments carry a confidence percentage only. | Row-level **candidate** anchors authored from `EVIDENCE_MANIFEST.txt`, each marked CANDIDATE in the cell. The author confirms or corrects them during the §3b walk. | An anchor asserted by a session that did not perform the review is a candidate, not an anchor. §1d: machine-drafted review is preparation. The on-ramp discrepancy is filed as a tooling finding. |
| G-02 | `base_uri`. §1f requires a namespace the encoder controls; `https://uofa.net` is refused as reserved for published examples. | `https://github.com/cloudronin/uofa`, the author-controlled repository namespace. **AUTHOR-CONFIRM before signing.** | Same rule and same resolution as the Johnson encoding's A-27, so the two packages mint consistently. The id is covered by the signature and cannot change afterward. |
| G-03 | Source class. The bundle is synthetic. | Admitted, and the package states its source class. | §2a: the protocol governs process rather than source authenticity. |
| G-04 | The April expectations predate this catalog. | Recorded as a version-labeled delta table in `APRIL_DELTA.md`, **not adjudicated**. | C5 convention. April expectations were written against an April catalog; R1a and the v0.5.x refinements landed after, so a difference is a labeled delta rather than a failure. |
| G-05 | Required and achieved levels. The extract prompt's default sets them equal unless the narrative names a gap. | Not reviewed by this session. protocol-check confirms they are **not** uniformly equal, so the default did not fire everywhere, but which rows are read and which are defaulted is a cell-walk question. | §3b: defaulted fields are not extracted fields, and only the source location settles which is which. |

---

## Drafted resolutions from the cell walk — 2026-08-21

**ADJUDICATED 2026-08-21.** These began as candidate resolutions produced by the mechanical walk
against the pre-registered ground truth and the author's Johnson precedent. Entries covered by
a standing ruling cite it. Entries with no precedent were restated as decidable questions and
**all were ruled by the author on 2026-08-21**; the rulings are in `AUTHOR_SUMMARY_COU1.md`.

| ID | Drafted resolution | Standing ruling applied |
|---|---|---|
| G-01 | **Resolved.** All **27** candidate anchors are resolved and zero CANDIDATE markers remain anywhere in the workbook — 19 factor rows against the ground truth's `source_file`, and 8 rows on `Model & Data` and `Validation Results` that the ground truth does not cover, resolved by opening the bundle. Where the candidate agreed with the ground truth's `source_file`, it was promoted and narrowed to the narrative section carrying the level. Where it disagreed, the anchor is **dual** — the data file for the measurement, the narrative section for the assessed level — because both genuinely carry part of it. | Johnson dual-anchor precedent (ProcessAttestation, Step 2 item 6) |
| G-02 | **Drafted: confirm as minted**, `https://github.com/cloudronin/uofa`. Same namespace, same rule, same reasoning as Johnson A-27, which the author resolved confirmed-by-author. **RULED 2026-08-21: keep as minted.** The id is covered by the signature and cannot change afterward, and the author confirmed it before signing. | Johnson A-27, resolved identically |
| G-03 | **Resolved.** Synthetic bundle admitted; the package states its source class. | §2a, standing |
| G-04 | **Resolved as prepared.** The April delta table stands; see `APRIL_DELTA.md` for the acknowledgement pass and what the cell walk changed in it. | C5 convention |
| G-05 | **Resolved by the walk.** Which rows were read and which were defaulted is now settled against the source for every factor. Required levels were compared **strictly** against the ground truth — `level_tolerance` is extraction latitude on the *achieved* level, and applying it to required would mask the defaulted-required failure by construction. | §3b; A-7 |

### Entries opened during the cell walk

Same four-column shape as the entries above, because these are new ambiguities
rather than adjudications of existing ones.

| ID | Ambiguity | Resolution | Rule applied |
|---|---|---|---|
| G-06 **ESCALATION** | **Film Cooling Validation has no factor in the pack.** Narrative §4.3 states a distinct factor — 47 film cooling holes, cascade rig not film-cooled, "The cascade therefore provides zero validation evidence for the film cooling model" — and rates it "Achieved Level 1 against Required Level 3", board-flagged as a material applicability gap (§6 open item 2). NASA-STD-7009B has no factor for it. | **Not resolved.** The extractor had merged it into factor 13 and taken its L1, which suppressed §4.2's own L2/L3 gap. The walk un-merged: factor 13 corrected to the source's Level 2, and the film-cooling gap recorded as a **visible declination** in row 17's rationale pointing here. The level is not carried anywhere. | Spec §6 escalation, Johnson **A-07** class. Fail-loud: a stated gap may lose its home, it may not lose its trace. GT `mapping_notes` permit either reading; the source settles it, and the eviction is the price. Filed as a schema finding |
| G-07 | **The pre-registered ground truth is wrong against its own named source, on Numerical solver error.** GT asserts `expected_required_level: 2` with `source_file: cfx_solver_settings.txt`. That file states no required level. Narrative §1.4 states only "Assessment: Level 1", where §1.3 and §4.3 — the two real shortfalls — both spell out "Achieved Level N against Required Level M". Narrative §6: "Verification factors: 4 of 5 meet required level; Discretization Error achieves L1 of required L3", which holds only if solver error meets its level; the §6 gaps list excludes it. GT's own W-AR-02 rationale concedes "Numerical solver (L1 with **implicit** L2 required)". | **RULED by the author, 2026-08-21: the source wins, the GT loses, the workbook stands** at required 1 / achieved 1. Recorded as **GT-DEFECT**. No downstream re-measurement: W-AR-02's `must_fire_factors` are Discretization error and Relevance of validation activities, so `count_min: 2` is met regardless. | A-7. An inferred required level is exactly what the protocol forbids the encoder to invent, and the April pre-registration embedded that failure mode. The governed process caught its own pre-registration inventing a level |

**Entries G-06 and G-07 were opened on 2026-08-21**, during the cell walk. G-06 records a gap
the pack cannot express; G-07 records a defect in the pre-registered expectations themselves.
Neither existed when this log was drafted, because neither is visible until the workbook is
walked against the source.
