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
