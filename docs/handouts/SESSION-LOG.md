# Nagaraja case handout, build log

Build spec: UofA Nagaraja Case Handout v0.1. Run date 2026-08-04.
Catalog `core@0.5.0 + vv40@0.5.0`, engine `uofa 0.8.0`.

Every quantitative claim in the handout comes from a fresh run made in this
session at the pinned catalog version. No number was carried over from
README.md, the paper plan, prior handouts, or chat context.

---

## S0. Discovery gate

| # | Output |
|---|---|
| 0.1 | PDF `site/public/handout.pdf` (dark) and `site/public/handout-print.pdf` (light). Source `site/public/handout/index.html` |
| 0.2 | Generator is headless Chrome `--print-to-pdf` over a self-contained HTML file. Documented in commit `86d83457`. Regenerable in repo |
| 0.3 | `packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld`. Valid JSON-LD, SHACL conforms against ProfileComplete, hash and Ed25519 signature verify. COU count 1 |
| 0.4 | Catalog `core@0.5.0 + vv40@0.5.0`, read from `packs/core/pack.json` and `packs/vv40/pack.json`. Engine `uofa 0.8.0`, an editable install of this repo. 23 active weakener patterns |
| 0.5 | Nagaraja S, Loughran G, Baumann AP, Kartikeya K, Horner M. "Establishing finite element model credibility of a pedicle screw system under compression-bending: An end-to-end example of the ASME V&V 40 standard." *Methods* 225 (2024) 74-88 |

On 0.5, the package carries only the DOI in `wasDerivedFrom`. There is no full
citation string in the encoding. The DOI was expanded through Crossref, which is
keyed on the DOI the package already asserts.

Kill criterion cleared. The package exists and passes SHACL.

---

## S1. Evidence artifacts

All under `build/`, which is gitignored. `docs/handouts/build_nagaraja_handout.py`
regenerates the rule-engine JSON from the packages when it is absent, so the
handout rebuilds from a clean clone.

| Artifact | Contents |
|---|---|
| `build/nagaraja/shacl-cou1.txt` | SHACL conforms |
| `build/nagaraja/verify-cou1.txt` | hash match, signature valid |
| `build/nagaraja/rules-cou1.txt` / `.json` | 19 firings, 4 patterns |
| `build/nagaraja/weakener-summary.csv` | per pattern, with severity and hits |
| `build/nagaraja/factor-coverage.csv` | 13 of 13 assessed |
| `build/morrison/*` | same three commands on both Morrison COUs at the same catalog version |
| `build/claim-to-artifact-map.txt` | machine-checked output of `build/verify_claims.py` |

Counts at catalog `core@0.5.0 + vv40@0.5.0`:

| Record | Firings | Patterns | Severity |
|---|---|---|---|
| Nagaraja COU1 | 19 | 4 | High 19 |
| Morrison COU1 | 11 | 5 | High 10, Medium 1 |
| Morrison COU2 | 18 | 6 | Critical 9, High 7, Medium 2 |

`weakener-summary.csv` is one row per pattern, not per affected node.
`COMPOUND-01` fires twice against a single node in Morrison COU2, so expanding
rows per node undercounts the total by one. Each file asserts that its `hits`
column sums to the engine's own `summary.total_firings`.

---

## S2. Structural mirror, and the adaptation

### What the precedent actually is

The spec names an existing Morrison handout as the precedent. No such document
exists in the repo. The closest artifact is a **single page** (612x792pt, US
Letter portrait) **conference handout for the UofA project as a whole**.
Morrison COU2 appears in it only as a terminal-output centrepiece.

Section order of the precedent:

1. Masthead: logo mark, standards eyebrow, title, tagline, byline
2. The problem
3. Three cards, C1 PACKAGES / C2 DETECTS GAPS / C3 COMPARES
4. Terminal block, `uofa rules morrison/cou2`
5. Why it might fit you
6. Try it, three access routes plus QR
7. Footer, the ask and contact

None of those sections carries a paper citation, a context of use statement, a
model risk determination, factor coverage, a weakener table, a decision record,
an integrity block, a catalog version, or a reproduction command. S3 requires all
of them. A literal mirror of the section order and the one-page budget therefore
cannot satisfy S3.

### Adaptation, approved before drafting

Inherit the precedent's design system and toolchain, and drive the section
structure from S3's content list instead of the precedent's section order.

Inherited unchanged: the theme token block, Fraunces and IBM Plex Sans and IBM
Plex Mono, letter portrait at the same margins, the card, terminal, band and
footer idioms, the `?theme=light` switch, the dark plus light PDF pair, and the
headless Chrome generator.

Changed: section order and page count. Two pages rather than one, printable as
the two sides of a single sheet. The type scale is reduced a little against the
precedent so the evidence tables fit without clipping.

The COU count also differs. The precedent shows Morrison with two COUs; Nagaraja
encodes one. There is no second COU to place beside it, so the layout carries a
single COU and the Morrison comparison appears as a three-row table rather than
a side-by-side diff.

### Section map

| Handout section | Source | S3 item |
|---|---|---|
| Masthead, eyebrow carries catalog version | S0.4 | versions on page |
| Source record | S0.5 | citation and DOI |
| Context of use, as encoded | package `hasContextOfUse` | COU statement |
| Model risk, as encoded | package | risk determination and drivers |
| Factor coverage, 13 of 13 | `factor-coverage.csv` | factor coverage |
| Terminal block, `uofa check` | `rules-cou1.json` | centrepiece, mirrors precedent |
| Weakeners detected | `rules-cou1.json`, `weakener-summary.csv` | weakener table |
| Decision record and offset rationale | package `hasDecisionRecord` | decision record |
| Comparison at the same catalog version | `morrison/rules-cou*.json` | comparison row |
| Integrity band | `shacl-cou1.txt`, `verify-cou1.txt` | integrity block |
| Reproduce band | verified command | reproduction command |
| Footer run metadata | S0.4 and run date | versions and run date |

---

## S4. Voice notes

The weakener definition is stated once, immediately above the first weakener
table. The comparison section states that the counts describe evidence
completeness and do not rank the papers or the teams. Nothing in the document
states or implies a regulatory position.

No factor is unassessed in this record, so the not-reported wording did not arise.
The generator still emits a `not reported` row if a future record omits a factor.

Authored prose contains no em dashes, verified programmatically over the rendered
DOM by separating authored text from quoted evidence. Two em dashes remain inside
the offset rationale, which is reproduced verbatim from the encoded record and is
shown as a quotation with its source URI. Editing quoted evidence to satisfy a
style rule would misrepresent the record. The same reasoning applies to the
terminal block, which is engine output rather than prose.

One point is called out on the page because the paper's authors will read it. The
package sets uncertainty quantification and sensitivity analysis at the package
level and carries validation results for both, yet `W-AL-01` fires on all six
validation results. The rule reads the per-node link rather than the package
flag. Stating this plainly avoids the misreading that the tool overlooked the
uncertainty work.

---

## S5. Verification

| # | Check | Result |
|---|---|---|
| 5.1 | Every number traces to `build/` | Pass. 25 of 25 claims machine-checked by `build/verify_claims.py` |
| 5.2 | Printed catalog version matches every run | Pass. `core@0.5.0 + vv40@0.5.0` printed in the eyebrow and the footer, read from pack metadata by the generator |
| 5.3 | Reproduction command executed from a clean checkout | Pass, after a correction. See below |
| 5.4 | Page count and section order match the precedent | Adapted and reported above. Two pages rather than one |
| 5.5 | Renders correctly, no clipped tables, no overflow | Pass. Both pages report 0px overflow, terminal block 0px on both axes |
| 5.6 | Source committed alongside the PDF | Pass. HTML source and generator committed |

### 5.3, the correction

The first draft printed `uofa check <package>`. Run from a clean `git worktree`
of HEAD it **failed**: C1 and C2 passed, C3 reported
`Jena engine not built`, because the rule engine JAR is not present in a fresh
checkout. The printed command is now:

```
uofa check --build packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld
```

Verified from a clean worktree in 26 seconds. It builds the JAR and returns 19
firings across the same 4 patterns, matching the stored artifacts exactly.

### Claim to artifact map

See `build/claim-to-artifact-map.txt`, regenerated by `build/verify_claims.py`.
The script fails with a non-zero exit if any printed claim stops tracing.

---

## Open items reported back

1. **The precedent.** The Morrison handout the spec assumes does not exist. What
   exists is a project conference handout with a regenerable HTML source and a
   headless Chrome generator. The toolchain carried over; the section order could
   not. Resolved by the adaptation recorded in S2.

2. **Nagaraja COU count and factor coverage.** One COU. The encoding covers the
   full 13-factor ASME V&V 40 Table 5-1 set, all marked assessed. Twelve factors
   reach their required level. Test conditions is recorded at achieved level 1
   against required level 3, with an offset rationale in the decision record.

3. **Morrison delta: zero.** A current-version rerun reproduces the published
   handout's Morrison COU2 figure exactly, 18 firings at Critical 9, High 7,
   Medium 2. It also matches `snapshots/example-counts.json` for both COUs.

   Catalog versions on both sides: the published handout commit `7b594d6b`
   (2026-05-27) carried `core@0.5.0 + vv40@0.5.0`, and the rerun is at
   `core@0.5.0 + vv40@0.5.0`. The delta is zero for a checkable reason rather
   than by coincidence. `packs/core/rules/uofa_weakener.rules` is byte-identical
   between that commit and HEAD, so the firing behaviour could not have moved.
   The only change to the example packages since then is `316daf6f`, which
   relabels `canonicalizationAlg` and does not affect rule firing.

   Nothing to reconcile. The Morrison handout was not touched.

### Observation, not acted on

`snapshots/example-counts.json` covers the Morrison and aerospace examples but
not Nagaraja, so the site prebuild drift check does not guard the Nagaraja
counts. Adding it was out of scope here.
