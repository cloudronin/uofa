# Documentation refresh plan

**Audited 2026-08-12**, after Phases 0–7 landed. Scope: repo `README.md`,
`packs/README.md`, `packs/model-credibility/README.md`, and the uofa.net site
content under `site/src/content/docs/`.

---

## What the audit found

Checked every user-facing doc for the five things Phases 1–7 added:

| Doc | `model-credibility` | `W-EV-*` | raidex | `sourcePin` | 800-3 |
|---|---|---|---|---|---|
| `README.md` | ✗ | ✗ | ✗ | ✗ | ✗ |
| `packs/README.md` | ✗ | ✗ | ✗ | ✗ | ✗ |
| `packs/model-credibility/README.md` | ✓ | ✗ | ✗ | ✗ | ✗ |
| site `reference/cli.md` | ✓ | ✗ | ✗ | ✗ | ✗ |
| site `reference/catalog.md` | ✗ | ✗ | ✗ | ✗ | ✗ |
| site `reference/packs/model-credibility.md` | ✓ | ✗ | ✗ | ✗ | ✗ |
| site `docs/repo-layout.md` | ✗ | ✗ | ✗ | ✗ | ✗ |

**No document anywhere describes the evaluation-sufficiency layer.** The rename
propagated because it was a string replace; the functionality did not, because
nothing replaces prose.

---

## P0 — Corrections. These are wrong, not merely incomplete.

### 1. My rename missed every uppercase variant (19 occurrences)

I replaced `mrm-nist` and `MRM_NIST` but not `MRM-NIST`. Survivors:

| File | Why it matters |
|---|---|
| `tests/test_mrm_nist_pack.py` | the **filename** still carries the old name |
| `src/uofa_cli/card_bundle.py:214` | `"assessor_name": "UofA MRM-NIST assessment"` — **written into every emitted bundle** |
| `packs/.../curated_cards.py:275` | same string, curated path |
| `packs/.../prompts/…_extract_prompt.txt:70` | same string, in the prompt |
| `packs/model-credibility/README.md:1` | title |
| `packs/.../shapes/…_shapes.ttl:5,20` | SHACL `sh:message` shown to users on violation |
| `site/.../reference/index.md:11`, `packs/model-credibility.md:2,6` | site titles and link text |
| `src/uofa_cli/excel_constants.py`, `commands/schema.py`, 2 test files | comments and docstrings |

**`assessor_name` needs a ruling, not a blind replace** — see Open Decisions.

### 2. The site pack page states something now false

`site/src/content/docs/reference/packs/model-credibility.md:54`:

> `## Weakeners — the 23 core patterns, no new rules`

The pack declares **10 patternIds of its own**: `W-EV-GEN-02`, `-DET-03`,
`-NULL-04`, `-COU-05`, `-CAP-06`, `-SUB-08`, `-COR-09`, `-DIV-07`,
`COMPOUND-EV-01`, `-02`. A reader is being told the opposite of the truth.

### 3. The generated weakener catalog omits two packs

`reference/catalog.md` frontmatter: `packs: [core, iso42001, nasa-7009b, surrogate]`,
35 patterns. Missing **`model-credibility` (10)** and **`disposition`**.

It regenerates on site build via `uofa catalog --format md`, so the fix is in
whatever pack set that invocation passes — **not in the file**. Editing the file
would be overwritten on the next build and is the wrong layer.

### 4. `packs/README.md` lists 4 of 7 packs

Documents `core`, `vv40`, `nasa-7009b`, `iso42001`. Omits `surrogate`,
`disposition`, `model-credibility`. Last touched 2026-05-06.

---

## P1 — The missing surface

The root `README.md` has **zero occurrences** of `uofa report`, "model card", or
"huggingface". The entire model-card assessment path is undocumented, including:

- `uofa report <owner/model>` — the HF card front end
- the **two-section readout** (documentation completeness / evaluation
  sufficiency) and the firewall between them
- `--cou` / `--mrl` run-context flags and the honest-N/A they produce
- `--raidex` / `--raidex-hub` furnished evidence
- **source pinning** (A9.1): artifact pins vs occasion pins, README blob oid
- the **keyless table route** for P2 uncertainty, its qualification and its two
  published defects

---

## The plan, per document

### `README.md` (repo root)
Add one section after **Domain Packs**: *"Assessing a model card"*. Contents:
the `uofa report` invocation, the two-section readout with a real example, the
run-context flags, raidex attachment, and a pointer to the pack README. Keep it
short — the root README is already 550 lines and its job is the on-ramp.

### `packs/README.md`
Add the three missing packs to the **Installed Packs** listing in the existing
format. `model-credibility` gets the fullest entry: 17 Group-A factors + 5
Group-B factors, two `factorStandard` values, the rules file, the properties
directory, and the prompts.

### `packs/model-credibility/README.md`
The largest rewrite. Currently 151 lines describing a documentation-completeness
pack. Needs: the Group-A/Group-B split and why the firewall is structural (rule
bodies bind `hasValidationResult`), the 10 weakeners with grounding, the
furnisher contract, the property definitions as a rendered single source, and the
keyless route with its qualification row.

### Site: `reference/packs/model-credibility.md`
Retitle, fix the false weakener claim, add the Group-B factor set and the
evidence-source distinction (`reported` vs `furnished`).

### Site: `reference/cli.md`
Document `--cou`, `--mrl`, `--raidex`, `--raidex-hub` and the `uofa report`
id-path behaviour.

### Site: `docs/repo-layout.md`
Add `packs/model-credibility/properties/`, `src/uofa_cli/furnishers/`, and
`studies/` with a one-line note that `studies/` holds measurement records whose
pins are historical (see `studies/PACK-RENAME-NOTE.md`).

### Site: `reference/catalog.md`
Not edited. Fix the generator's pack set, rebuild, verify 45 patterns across 6
packs.

### New: site `docs/concepts/evidence-sufficiency.md`
The one genuinely new *concept* on the site. Existing `concepts/weakeners.md`
explains weakeners generally; nothing explains why a reported score needs
uncertainty, a null baseline, and a stated context of use to be interpretable.
This is the pack's thesis and it has no home.

---

## Sequencing

1. **P0.1** rename residue (code + docs, one commit, `assessor_name` per ruling)
2. **P0.3** catalog generator pack set — mechanical, verifiable by rebuild
3. **P0.2 + P0.4** the false claim and the pack listing
4. **P1** root README section, pack README rewrite, site pages
5. **New concept page** last, since it is additive rather than corrective

Steps 1–3 are corrections and should land before anything else; a doc that is
wrong is worse than a doc that is silent.

---

## Open decisions

**1. `assessor_name: "UofA MRM-NIST assessment"`.** This string is written into
every emitted bundle, so it is *data*, not documentation. Options: (a) rename it,
accepting that new bundles differ from existing ones on a field that identifies
the assessor; (b) leave it, accepting a stale name in output; (c) rename and add
it to the alias' one-version note. My recommendation is (a) — the field names the
profile, the profile is renamed, and bundles are already regenerated per run —
but it changes emitted output and is yours to call.

**2. How much of the validation apparatus belongs on the public site.** The
studies, the qualification table, the holdout gates, the published route defects.
Argument for including: it is the strongest evidence the instrument is honest,
and the paper will reference it. Argument against: it is unsettled, the catalog
has not closed, and publishing an in-progress validation invites citation of
provisional numbers. My recommendation: a single site page that *links* to the
repo's `studies/` without restating any figure, so nothing has to be kept in sync.

**3. Whether to document Phase 5 surfaces as forthcoming.** Cards and badges are
specced and gated behind catalog closure. Mentioning them sets an expectation
with no date; omitting them means the docs will need another pass. I lean toward
one sentence in the pack README naming the gate, and nothing on the site.
