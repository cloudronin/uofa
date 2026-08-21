# Ambiguity log — aero cou2

**DRAFT, AWAITING-AUTHOR.** Every entry is re-adjudicated by the author. Entry shape per
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

**Still AWAITING-AUTHOR.** These are candidate resolutions produced by the mechanical walk
against the pre-registered ground truth and the author's Johnson precedent. Entries covered by
a standing ruling cite it. Entries with no precedent are marked **AUTHOR-RULE** and restated as
decidable questions in `AUTHOR_SUMMARY_COU2.md`.

| ID | Drafted resolution | Standing ruling applied |
|---|---|---|
| G-01 | **Resolved.** All **27** candidate anchors are resolved and zero CANDIDATE markers remain anywhere in the workbook — 19 factor rows against the ground truth's `source_file`, and 8 rows on `Model & Data` and `Validation Results` that the ground truth does not cover, resolved by opening the bundle. Where the candidate agreed with the ground truth's `source_file`, it was promoted and narrowed to the narrative section carrying the level. Where it disagreed, the anchor is **dual** — the data file for the measurement, the narrative section for the assessed level — because both genuinely carry part of it. | Johnson dual-anchor precedent (ProcessAttestation, Step 2 item 6) |
| G-02 | **Drafted: confirm as minted**, `https://github.com/cloudronin/uofa`. Same namespace, same rule, same reasoning as Johnson A-27, which the author resolved confirmed-by-author. **The confirmation itself is still the author's act** — the id is covered by the signature and cannot change afterward. | Johnson A-27. AUTHOR-RULE: confirmation only |
| G-03 | **Resolved.** Synthetic bundle admitted; the package states its source class. | §2a, standing |
| G-04 | **Resolved as prepared.** The April delta table stands; see `APRIL_DELTA.md` for the acknowledgement pass and what the cell walk changed in it. | C5 convention |
| G-05 | **Resolved by the walk.** Which rows were read and which were defaulted is now settled against the source for every factor. Required levels were compared **strictly** against the ground truth — `level_tolerance` is extraction latitude on the *achieved* level, and applying it to required would mask the defaulted-required failure by construction. | §3b; A-7 |

### Entries opened during the cell walk

Same four-column shape as the entries above, because these are new ambiguities
rather than adjudications of existing ones.

| ID | Ambiguity | Resolution | Rule applied |
|---|---|---|---|
| G-06 | **Film Cooling Validation has no factor in the pack**, inherited form. Narrative §4.3 states "Level 1 achieved against Level 3 required" and scopes it explicitly: "this gap is inherited from COU1 and is tracked as an existing condition, not a COU2-specific applicability finding." | **Not resolved**, same class as COU1's G-06. Recorded as a visible declination on row 17's rationale. No merge occurred here — factor 13 is `not-assessed` per §6 open item 5 — so nothing was suppressed and nothing needed un-merging. | Johnson **A-07** class. The source's own scoping is carried rather than re-derived |
| G-07 | **Not applicable to this package.** COU1's ground-truth defect on Numerical solver error has no counterpart here: COU2's GT expects required 2 / achieved 2 and the workbook agrees, and narrative §6 independently confirms "Verification factors (1.1-1.5): all 5 Assessed at or above required level." | Recorded so the two logs read in parallel and the absence is deliberate rather than an omission. | — |

**Entries G-06 and G-07 were opened on 2026-08-21**, during the cell walk. G-06 records a gap
the pack cannot express; G-07 records a defect in the pre-registered expectations themselves.
Neither existed when this log was drafted, because neither is visible until the workbook is
walked against the source.
