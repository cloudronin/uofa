# From an evidence folder to a signed package, without the solver

Three Ansys Workbench project archives and a paper go in. A signed Unit of
Assurance carrying those archives as sealed, hash-verified evidence comes out,
along with an account of what is in them, what is missing from them, and where
the paper and the archives do not agree — **without ever needing the software
that produced the simulation.**

The case is Nagaraja et al., *Methods* 225 (2024) 74-88, an end-to-end ASME
V&V 40 example for a pedicle screw system under compression-bending. Its
evidence is archived publicly at <https://osf.io/n4pjz/>.

Running time is about seven minutes. Nothing below needs an Ansys installation,
an Ansys licence, or a language model.

---

## Two things to say before starting, and to keep saying

**"Weakener" is not the word for anything on these slides.** A weakener is a
catalog rule with an id, detected by `uofa rules`. The solver messages this demo
surfaces have no rule behind them — they are cautions *the solver itself*
raised, carried through as evidence for a human to weigh. Calling them weakeners
invites a reviewer to ask which rule fired, and there isn't one. Say
**solver-reported cautions**, and say whose findings they are.

**Divergences are observations, not accusations.** This is an FDA-coauthored
paper with named contributors, and the corroboration step reports that their
public archive does not match their published Table 5 in two places. Both have
ordinary explanations, and the demo should offer them. Notify the authors before
presenting this anywhere.

---

## Setup

```bash
pip install uofa
mkdir osf-n4pjz && cd osf-n4pjz
# Download the three .wbpz files from https://osf.io/n4pjz/
```

The archives are not redistributed with UofA. They are referenced by URL and
digest — see `packs/vv40/examples/nagaraja/source/EVIDENCE_MANIFEST.txt`, which
records the two known digests and the reasons.

## 1. What is actually in the folder

```bash
uofa evidence inventory osf-n4pjz/
```

Three `.wbpz` archives — 85 members each in the two that have been inspected;
the 405 MB one has not been opened yet. The inventory classifies every member by
its *content*, hashes it, and states which ones have no reader and why. It never
unpacks anything — the largest archive is 405 MB and is read in place.

The beat to land: **everything is accounted for.** A Mechanical database and a
CAD geometry file are sealed and reported unread, with the reason, rather than
quietly omitted. A manifest that lists only what a tool understood would
misrepresent a folder of proprietary archives as a small one.

Point at `dp0/act.dat`. It is an HDF5 container, and its extension is `.dat`.
Under extension-based routing it would have been handed to a text reader and
shipped to a language model as mojibake.

## 2. What the archives say about themselves

```bash
uofa evidence seal osf-n4pjz/ --source-map osf-urls.txt -o evidence.json
```

Every `MECH/` directory in the two inspected archives is empty — eight of them
in one, nine in the other. There is no
`ds.dat`, no `solve.out`, no `file.rst` — the filenames say `NoResults` and they
mean it.

**The archives say so themselves.** A stored Workbench message records that the
project was opened from an archive written without solution files, and lists each
omitted file by name. That is the completeness evidence, and it is stronger than
anything a tool could conclude from failing to find things: the package testifies
to its own gaps.

Alongside it, 78 stored messages spanning 2016-2024 — 40 warnings and 30 errors.
Among them: weak springs added to reach a solution, a matrix coefficient ratio
above 1e8, linear tetrahedral elements used in regions with linear materials, and
a unit-system mismatch on a contact command object. These are the solver's own
words. **Solver-reported cautions.** Not weakeners.

The operator's username, machine name and directory tree are redacted before any
of this is displayed, stored or sent anywhere. The *filenames* survive on
purpose: `ds.dat` and `solve.out` are the finding.

## 3. Corroborate the paper against the artifacts

```bash
uofa evidence seal osf-n4pjz/ --claims nagaraja-table5-fda.json -o evidence.json
```

The claim set is the paper's Table 5, FDA column, transcribed. The archives'
materials library answers:

| Table 5 (FDA) | `EngineeringData.xml` | |
|---|---|---|
| Ti-6Al-4V ELI, E = 108,222 MPa | 108222.363244 MPa | agrees |
| Poisson's ratio 0.33 | 0.33 | agrees |
| Yield 967.5 MPa | 967.479362 MPa | agrees |
| Tangent modulus 4,647 MPa | 4646.717387 MPa | agrees |
| UHMWPE, E = 1,100 MPa | 690 MPa | **diverges** |
| Ansys Mechanical 19.0 | 2023 R2 | **diverges** |

Four exact agreements, from a 130 KB XML file inside a proprietary archive, with
no Ansys involved.

**On the two divergences, offer the ordinary explanation first.**

The release gap is almost certainly a re-save: the paper is 2024, the archive was
last saved in November 2024 and uploaded that December. The defensible statement
is *"the archived artifact is a later re-save under 2023 R2, and the package
records that fact, so a reader knows the bytes on OSF are not the bytes that
produced Table 5."* It is a provenance observation worth recording. It is not
evidence that the published results came from a different model, and presenting
it as a gotcha would be wrong.

The UHMWPE modulus is a genuine mismatch between a published table and a public
archive. It may be an unused library entry, a later edit, or a table error. The
library holds nine materials including three mutually inconsistent titanium
definitions and a near-duplicate whose tangent modulus is off by a factor of
10^6 — which is exactly what a real materials library looks like. **The tool
reports that the values differ and stops.** Which one is right is the reader's
call, and the demo should say so out loud.

Note also four comparisons the tool *refused*. The per-system `.engd` files state
`108222363244` with no declared unit. It is almost certainly Pa. "Almost
certainly" is a conversion, and a silent conversion that is wrong produces an
answer that validates.

## 4. Extraction proposes, a human decides

```bash
uofa extract osf-n4pjz/ nagaraja-paper.pdf --pack vv40 -o extracted.xlsx
```

The workbook is the single editable surface in the workflow. Correct a factor
status in it and the emitted package records `statusProvenance: corrected`;
leave one alone and it records `extracted`. Never `confirmed` — the interface
pre-fills every status and the user submits the form, so an unchanged row may
have been read and agreed with or scrolled past, and recording that as a judgment
would assert something the interaction does not evidence.

Say the quiet part: this step is not optional and is not a formality.

## 5. Seal it inside the signature

```bash
uofa import extracted.xlsx --evidence evidence.json \
    --sign --key keys/my.key --check
uofa verify uofa-nagaraja.jsonld
```

The manifest, the source pins, the solver facts, the stated absences and the
corroboration table are folded into the package **before** it is hashed. That
ordering is the demonstration:

```bash
# Change one digest inside the sealed manifest.
uofa verify tampered.jsonld    # hash and signature both fail
```

A manifest written *beside* a signed package proves nothing about the package.

## What this does and does not show

**Does.** That integrity, provenance, completeness and solver-reported cautions
can be established over proprietary vendor archives with no vendor software, no
licence and no language model; that the evidence can be carried by reference and
digest rather than by copying it; and that a published claim can be put next to
the artifact it rests on.

**Does not.** It does not exercise the requirement or argument layers. Those
still demonstrate on Morrison — rows 16/54 for argument, RH < 1 for requirement —
unless and until Nagaraja carries encoded layer instances. Corroboration gives
quantity identity a live instance and a good exhibit for the units question; it
does not close that gap, and the talk should not imply it does.

It also does not read `file.rst`. There is no `file.rst` in either inspected
archive to read.

**On numbers.** Nagaraja is a development-tier document under Decision 7. Any
extraction-quality figure quoted near this demo is labelled development, never
held-out.
