# Review packet — aero cou1 (take-off transient peak temperature)

**Vocabulary note:** the committed protocol renames verdicts Accepted→Confirmed, Not Accepted→Overruled; this packet predates the rename.

**SUPERSEDED 2026-08-21 by `AUTHOR_SUMMARY_COU1.md`.** This packet described the walk as it
stood before it ran; the walk has since run and every question it raises has been ruled. Kept
as the record of what was asked for. Read the summary instead.

**Original header —** AWAITING-AUTHOR. Prepared, not reviewed. Section 0 of the prep spec reserves the cell
walk, the verdicts, and the ambiguity re-adjudication for you, and none of them has
happened here.

Artifacts in `dev/build/encoding-prep/aero-cou1/`. The package is unsigned.

| | |
|---|---|
| Source | `aero-evidence-cou1/`, synthetic bundle, admissible per §2a |
| Package | `aero-cou1.jsonld`, 19 factors, 5 evidence rows |
| Weakeners | 20 across 11 patterns |
| Ambiguity entries | 5, prefixed G- |
| Anchors | 27 candidate row anchors, every one marked CANDIDATE |
| protocol-check | green on all seven applicable checks |
| Governing draft | `docs/Encoding_Protocol_v0_1_DRAFT.md` |

**Time estimate: about two hours.** An assumption, not a measurement, and smaller than the
Johnson packet's because the cross-standard mapping work does not arise here. These bundles
were authored against this pack.

---

## Read first: the anchors are candidates

The extractor records no per-cell source document. The published on-ramp says "Hover a cell
for the document it came from"; the comments carry a confidence percentage and nothing else.
So the anchors in the Source Anchor column were authored from `EVIDENCE_MANIFEST.txt` at row
level and every one is labelled CANDIDATE.

Confirming or correcting them is the substance of your walk, and it is the reason
protocol-check passing does not mean the anchors are right. It means they are present.

## Step 1. Confirm the namespace (5 minutes)

Mints under `https://github.com/cloudronin/uofa`, same as the Johnson encoding, because
`https://uofa.net` is refused as reserved for published examples. The id is covered by the
signature and cannot change after signing. Entry G-02.

## Step 2. The level walk, and one thing to look at hard

**16 of 18 factors carry required equal to achieved.**

protocol-check passes this because at least one differs, so the extract prompt's default did
not fire uniformly. But the default sets required equal to achieved unless the narrative
names a gap, and 16 of 18 is close enough to uniform that the ones which differ are
where your attention belongs. Check those rows against
`credibility_assessment_narrative.docx` first, then spot-check the equal ones.

This is the failure the Johnson pilot shipped in its raw extract at seventeen of seventeen,
and the reason §3b treats required and achieved as separately confirmed fields.

## Step 3. The rest of the cell walk (about an hour)

Five sheets. `REVIEW_LEDGER` does not exist for this encoding because no review pass has run;
the raw extractor output is snapshotted at `raw-extract/` so your corrections stay measurable
against it.

Decision reads Accepted (with conditions).

## Step 4. The weakeners (20 of them)

| Pattern | Hits |
|---|---|
| COMPOUND-01 | 6 |
| W-AR-05 | 4 |
| W-AR-02 | 2 |
| COMPOUND-03 | 1 |
| W-AL-02 | 1 |
| W-CON-04 | 1 |
| W-EP-04 | 1 |
| W-NASA-02 | 1 |
| W-NASA-03 | 1 |
| W-NASA-06 | 1 |
| W-ON-02 | 1 |

No candidate dispositions are drafted for these. The Johnson encoding's
`DISPOSITIONS_DRAFT.md` carries per-family reasoning that applies here unchanged, including
the finding that W-AR-05 is mis-scoped for evidence types with no comparator, which accounts
for some of the 4 hits on this package too.

Apply the §4e silence sweep as you go: every factor the pack expects needs a disposition,
not only the ones the engine raised.

## Step 5. The April delta (about 20 minutes)

`APRIL_DELTA.md`, **prepared and not adjudicated**. Every deterministic core fire and every
structural invariant meets its April expectation.

One delta is worth your time. **W-AR-01 fired zero times against an April baseline of 14.**
The prompt fix that was supposed to stop the mass-fire noise has landed, and the pattern now
has nothing to fire on because the extractor returns acceptance criteria on every factor.
Whether those criteria are correct is a cell-walk question, not a delta-table one.

## Step 6. What you are not being asked to do

No signing, no ledger changes, no marking review complete.

---

## Open items

1. **The namespace**, step 1. Blocks signing.
2. **16 of 18 factors with required equal to achieved**, step 2. The highest-value
   thing in this packet.
3. **Candidate anchors**, throughout. None has been confirmed against a source.
4. **No dispositions drafted.** Deliberate: dispositioning before the cell walk would
   adjudicate against an unreviewed package.
