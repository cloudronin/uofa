# INV-6 — Git-history audit for post-freeze changes

Status: **ESCALATED** (one positive-record claim in shipped chapter text is not
corroborated by commit ordering). One finding below is **corrected**.
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A4

---

# ADDENDUM — re-investigated against parent spec v2.0

## Correction: the Phase 3 gate artifacts are committed, and F3 is closable

§5 of the original finding reported that the Phase 3 gate values could not be
substantiated because `dev/build/adversarial/phase3/` is gitignored, and
recommended moving `GATE7_DECISION.md` into `studies/`. **That was wrong.**
`.gitignore:41-43` ignores `dev/build/*` but force-tracks `dev/build/adversarial/`
and `dev/build/phase2_5/`. Sixty Phase 3 files are committed, including every
artifact the original finding said was unreachable. The recommendation to relocate
them is withdrawn; they are already in the record.

**F3 — Phase 3 gates — re-audited:**

| Artifact | Added | Content |
|---|---|---|
| `calibration-v2/v1.1.0/` … `calibration-v4/v1.1.0/` | `e050d819`, 2026-06-09 18:39 | per-judge calibration JSONL + results JSON + summary, prompt v1.1.0 |
| `calibration-v5/gate7_result.md` | `c117d7e9`, 2026-06-09 20:24 | v5 (prompt v1.2.0) hard-gate table: gate 5 A 96.7% / B 90.0% / C **63.3% ❌**; gate 7 UNCERTAIN A 80% / B 60% / C **0% ❌**; Fleiss κ 0.804; `all_pass = false` |
| `GATE7_DECISION.md` | `c117d7e9`, 2026-06-09 20:24 | decision record dated 2026-06-10: **RELAX**, with the amended spec §15.1 #7 clause, a drafted Ch3 disclosure paragraph, and a named residual risk |
| `STAGE2_LAUNCH_CHECKLIST.md`, `production/run-1/*`, `STAGE3_RESULT.md`, `triage/*` | 2026-07-17 → 2026-08-04 | execution, all **after** the gate decision |

**The positive record verifies here, and cleanly.** The gate decision (2026-06-09
20:24) precedes every Stage 2 execution artifact (first progress snapshot
2026-07-17), by commit ordering, not by document self-dating. That is exactly the
form of evidence A4 item 2 needs and the form the H2 claim (§4) lacks.

**Category (c) list, revised:**

| # | Item | Status |
|---|---|---|
| ~~C1~~ | Gate-7 post-hoc relaxation | **Downgraded to (b) — disclosed.** It has a dated decision record, the amended clause in full, a pre-drafted Ch3 disclosure paragraph, and an explicit statement of the residual risk. It still needs an **A4 appendix entry** (v2.0 A4 item 2 covers it), but it is not an undisclosed change. |
| ~~C2~~ | Gate artifacts not in the committed record | **Withdrawn — factually wrong.** |

**The (c) list is now empty.** Every declared freeze this audit could locate has
either no post-freeze substantive change (F1, the catalog) or a dated, in-record
disclosure (F3, F4). That is a strong result for A4 and it should be stated as such.

## The one escalation stands, and v2.0 sharpens it

v2.0 A4 item 6 now names the disclosure explicitly:

> every post-freeze change with rationale, including **the H2 routing-defect
> correction and criterion replacement already documented in ch4-h2-section**.

So the H2 criterion replacement is a named A4 entry. §4's problem is unchanged and
is now more visible: `ch4-h2-section.md:82-84` claims the thresholds were
*"committed to the record before the measurement was performed"*, and the
thresholds document and `studies/real-document-rescore/FINDINGS.md` landed in the
**same squashed commit** `ade81bd3`.

The contrast with F3 is what makes this worth fixing rather than arguing:
**Phase 3's gate decision is provable from commit order; H2's is not.** A4 will sit
both entries in one table, and a reader who checks will see one that verifies and
one that rests on document self-dating.

Recommendations unchanged, with option 1 now clearly worth attempting first: PR #62
is a squash merge, so if the branch commits survive on GitHub the ordering is
recoverable and citable. If not, reword to what the record supports.

## A4's six-item list, audited

v2.0 A4 specifies the appendix contents. Status of each against this audit:

| A4 item | Evidence available? |
|---|---|
| 1. Catalog version history through v0.5.15.1, freeze dates, git tags | **Yes.** 30 tags enumerated; freeze commit `7716ebe4` 2026-04-29; the byte-identity diff is the headline (§2) |
| 2. Phase 2/2.5 closure; Phase 3 gates shown to precede execution | **Yes for Phase 3** (above, provable by commit order). **Partial for Phase 2/2.5:** closure is the v0.5.15.1 tag; the status reports are retrospective (`eea66d34`, 2026-07-16) |
| 3. A16 pre-registration date + pinned Liang commit | **Yes.** `d3d07bd2`, 2026-08-10 22:12; pin `6bcc76fe6142` occurs once repo-wide (§5) |
| 4. GATE-H2 / GATE-H3 entries with the letter's dual figures and the author's rationale | **Not an audit item** — these are v2.0's own new resolutions, drafted in §0.1. Note for the author: **GATE-H3's "(the holdout supports it)" parenthetical is contradicted by the committed per-class data** (see INV-8 addendum); an A4 entry asserting it would be an undisclosed-inaccuracy risk |
| 5. Hypothesis rewording, original vs revised, dated | Manuscript-side; not in this audit's scope |
| 6. Post-freeze disclosure incl. H2 routing-defect and criterion replacement | **Yes**, with the §4 caveat above as the one open item |

## Coverage statement (addendum)

**Searched.** `.gitignore:33-46`. `git ls-files dev/build/adversarial/phase3/`
(60 files) and the full non-calibration subtree. Read `GATE7_DECISION.md` (head, 30
lines), `calibration-v5/gate7_result.md` (head, 30 lines), `STAGE3_RESULT.md`
(head, 25 lines). `git log --diff-filter=A` on the three gate artifacts and
`git log` over `dev/build/adversarial/phase3/` (6 most recent). v2.0 §A4 items 1-6,
§0.1.

**Still NOT searched.** The **Phase 3 spec itself (v1.4 / v1.6 / v1.7) remains
absent from the repository.** `GATE7_DECISION.md` quotes the gate clause it amends,
which is strong secondary evidence that the gate pre-existed, but the spec that set
it is still not in the record. If A4 item 2 is to cite the gate *values* as
pre-set, the spec should be committed alongside — otherwise the appendix cites a
document a reader cannot fetch. F8 (`harness/bakeoff/results/PREREGISTRATION-2026-05-31-*.md`)
remains unaudited.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## 1. Freeze inventory established from the record

| # | Freeze | Artifact | Freeze point | Evidence |
|---|---|---|---|---|
| F1 | **Catalog v0.5.15.1** | `packs/core/rules/uofa_weakener.rules` (+ pack manifest, shapes) | tag `v0.5.15.1-phase2v3-shacl-threadsafe-and-sa-boolean` → commit `7716ebe4`, **2026-04-29 11:15:52 −0700** | `git log -1 <tag>` |
| F2 | **Phase 2 / 2.5 closure** | `PHASE2_STATUS_REPORT.md`, `PHASE2_5_STATUS_REPORT.md` | both added `eea66d34`, **2026-07-16 21:26:33 −0700**; substantive closure is the v0.5.15.1 tag (F1) — the reports are retrospective | `git log -1 -- PHASE2*_STATUS_REPORT.md` |
| F3 | **Phase 3 spec v1.4 gates** | **artifact not located — see §5** | — | — |
| F4 | **A16 pre-registration** | `studies/taxonomy-validation/PREREGISTRATION.md` | added `cbb1b6e1` 22:08:59, frozen `d3d07bd2` **2026-08-10 22:12:45 −0700** ("studies: freeze the A16 pre-registration against the pinned Liang corpus") | `git log --diff-filter=A` |
| F5 | **H2 replacement criterion** | `docs/decisions/2026-08-14-h2-replacement-thresholds.md` | **committed `ade81bd3`, 2026-08-15 08:44:22 −0700**; document self-dated 2026-08-14 | see §4 |
| F6 | **DECLARATION.md-class artifacts** (4 found) | `studies/evidence-span/`, `studies/claim-density/`, `studies/specificity-discriminator/`, `studies/model-selection/` | 2026-08-15 08:44 / 08:53 / 10:05 / 16:42 | `git log --diff-filter=A` per file |
| F7 | **Second pre-registration** | `studies/attribution-agreement/PREREGISTRATION.md` | `ade81bd3`, 2026-08-15 08:44:22 | |
| F8 | (bakeoff) | `harness/bakeoff/results/PREREGISTRATION-2026-05-31-{coverage-B,ablation-n60}.md` | 2026-05-31 (from filename) | **not audited — see coverage statement** |

## 2. F1 — catalog v0.5.15.1: post-freeze changes

23 commits touched `packs/core/` between the freeze tag and HEAD. Classification:

| Class | Artifact | Finding |
|---|---|---|
| **(a) no-op for the freeze** | `packs/core/rules/uofa_weakener.rules` | **The rule logic is byte-identical to the freeze.** The only diff across the whole window is one copyright line (`crediblesimulation.com` → `uofa.net`) in `8d1d42fd`. Verified with `git diff <tag>..HEAD -- <rules file>`: 1 line changed, inside a comment block. **This is the strongest single fact available to A4** and should be stated with the command that proves it. |
| **(b) disclosed / non-substantive** | `packs/core/pack.json` (+99 lines) | Manifest restructure to the `capabilities[]` schema (`4009bf52`), core version 0.5.0 → 0.6.0 (`69af3d61`), relicense CC0-1.0 → Apache-2.0 (`34767740`), plus an explicit `patternIds` list. **The pattern set is unchanged**: the freeze manifest declared `"weakener_patterns": 23`; HEAD enumerates 23 ids, matching the classifier's independent list ([classifier.py:57-70](src/uofa_cli/adversarial/classifier.py)). No detection semantics moved. |
| **(b) disclosed** | `packs/core/shapes/uofa_shacl.ttl` (+785 lines) | Vocabulary and v0.6 schema work: class/property definitions (`74cbefff`, `b0fcc660`, `eee1b0e1`, `6e17ed6a`), deprecation marks (`97abac5e`), additive `ProfileDisposition` (`1f89dc81`), a patternId-regex reconciliation (`9d8b5a9c`), and a shape fix `a79d1706` *"stop the shape rewarding fabrication, and measure what it fills"*. **These are C2 (validation) changes, not C3 (detection) changes.** They do not alter the 23 rules. |
| **(c) UNDISCLOSED substantive** | — | **None found at the catalog layer.** |

**A4 wording that the evidence supports:** *the detection catalog frozen at
v0.5.15.1 has not changed since; the validation shapes around it have, additively,
and are versioned separately.* That is a clean, checkable claim.

One caveat A4 should carry: `packs/core/pack.json`'s `version` field now reads
`0.6.0` while the frozen catalog is cited as v0.5.15.1. A reader diffing the repo
against the manuscript will hit that mismatch. One sentence resolves it.

## 3. F4 — A16 pre-registration: post-freeze changes

Ten commits touched `studies/taxonomy-validation/` after `d3d07bd2`. All are
**(b) disclosed**, and the disclosure mechanism is exemplary — amendments are
separate, dated, signed files rather than edits to the frozen text:

- `AMENDMENT-01-div07-venue.md` (`39fd1c26`, *"docs: sign AMENDMENT-01"*)
- `AMENDMENT-02-microground-redraw.md`
- `ENRICHMENT-PROTOCOL.md` signed at `f44c2854`, DRAFT title dropped at `a0db615f`
- gold set, enrichment search, specificity case set (`4fed8e6a`, `9bb01573`, `f1f2849c`)

**No (c) items.** This is the pattern A4 should hold up as the standard.

## 4. ESCALATION — F5: the ordering claim in shipped chapter text

[docs/ch4-h2-section.md:82-84](docs/ch4-h2-section.md) states:

> "Six conditions were given numeric thresholds, and those thresholds were
> **committed to the record before the measurement was performed**."

and at :97-100:

> "The thresholds it failed against were fixed in advance and were not revised
> afterwards — not when an initial measurement was found to be circular, not when a
> defect in the scoring code was corrected, and not when the sample was completed
> from three papers to six."

**Git does not corroborate this.** The thresholds document and the measurement
landed in **the same commit**:

```
ade81bd3  2026-08-15 08:44:22 -0700   fix(extract): send each pack its own prompt … (#62)
  + docs/decisions/2026-08-14-h2-replacement-thresholds.md
  + docs/decisions/2026-08-14-h2-gate-amendment.md
  + studies/real-document-rescore/FINDINGS.md          (203 lines)
  + studies/real-document-rescore/conditions_5_and_6.json (58 lines)
  + studies/evidence-span/DECLARATION.md
  + studies/attribution-agreement/PREREGISTRATION.md
```

The commit adds the pre-registration **and** the results it pre-registers, in one
atomic change. Commit ordering therefore cannot separate them.

**This is not evidence the claim is false.** Contemporaneous internal evidence
supports it:
- the thresholds file self-dates **2026-08-14** and carries the status line
  *"DECLARED, NOT YET MEASURED against the real corpus"*
  ([2026-08-14-h2-replacement-thresholds.md:1-18](docs/decisions/2026-08-14-h2-replacement-thresholds.md));
- it states its own anti-retrofit rationale: *"numbering it in the same breath as
  reporting 0.9637 would have been the retroactive thresholding the amendment
  exists to avoid"*;
- every figure in it is labelled synthetic-corpus or pre-existing.

**The problem is evidentiary, not factual.** `ade81bd3` is a squashed PR merge
(`(#62)`), which collapses whatever ordering existed on the branch. A4 claims
git-provable precedence for something git cannot show.

**Escalation triggered** on the item's own criterion — this touches text already in
a shipped chapter section. **Author decisions:**

1. **Recover the ordering from the PR.** If PR #62's individual commits survive on
   GitHub, the pre-squash order is recoverable and citable. Check first; it may
   resolve this at zero cost. (Not checkable from the local clone — the branch
   commits are not present.)
2. **Reword to what the record supports:** *"the thresholds were declared before the
   measurement, as the decision record's own status line attests; both were
   committed together in PR #62."* Honest, and it still defeats the retroactive-
   thresholding objection.
3. **Adopt a commit discipline going forward** so this stops recurring: pre-registrations
   land in their **own** commit, before the run. F6's four DECLARATION.md files
   have the same exposure — `studies/evidence-span/DECLARATION.md` also landed in
   `ade81bd3`, in the same commit as the study it declares.

Recommending option 2 with option 1 attempted first, but this is A4's author call
and the wording is chapter text.

## 5. Pin-consistency check (item step 4, shared with U-INV-3)

**Result: consistent, with two stale filename references.**

- `6bcc76fe6142` occurs **once** repo-wide, at
  `studies/taxonomy-validation/PREREGISTRATION.md:101`, with a content pin
  (`sha256:79aa662d…`, 31,620,407 bytes). No conflicting citation exists.
- **Two artifacts still name the superseded corpus file** that the pre-registration
  explicitly corrected (`datasetcard_info.parquet` → `modelcard_info.parquet`):
  [docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md:32](docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md)
  and [studies/taxonomy-validation/frame.py:4](studies/taxonomy-validation/frame.py)
  (the usage docstring of the frame-computing script). Ten other artifacts carry the
  corrected name. **Two-word fixes; neither changes a number**, but the addendum is a
  citable document and the script is the one that computes the frame. Fix before D6.

**Phase 3 gate values (item step 4, first clause): NOT VERIFIED — artifact not
located.** No `Phase 3 spec v1.4` document exists in the repo; `find -iname "*Phase3*"`
returns only `PHASE3_STATUS_REPORT.md` and the gitignored `dev/build/adversarial/phase3/`.
The status report cites gate values and a `GATE7_DECISION.md` under
`dev/build/adversarial/phase3/`, which is **gitignored** and therefore not in the
committed record at all. Two consequences for A4:

- The claim "Phase 3 gates were set before execution" cannot currently be
  substantiated from the repository.
- `PHASE3_STATUS_REPORT.md:47` independently flags that **gate 7 was relaxed
  post-hoc** (deviation D8), calling it *"the deviation most open to committee
  challenge."* That is a category (c)-adjacent item that the status report already
  discloses internally but which has no A4 entry yet. **It should get one.**

**Recommend:** move `GATE7_DECISION.md` and the calibration summary out of
`dev/build/` and into `studies/` before A4 is drafted, or A4 cites artifacts a
reader cannot fetch.

## 6. The (c) list

| # | Item | Freeze | Severity |
|---|---|---|---|
| C1 | **Phase 3 gate-7 post-hoc relaxation** — hard gate (per-class ≥50% on UNCERTAIN) failed for judges B and C; a v1.7 relaxation was proposed and the frozen prompt is v1.1.0, not the spec's v1.6 | F3 | Disclosed inside `PHASE3_STATUS_REPORT.md:47` (D8) and in the deviation log, **but not in any A4-class appendix, and the deciding artifact is gitignored** |
| C2 | **Phase 3 gate artifacts are not in the committed record** (`dev/build/adversarial/phase3/` is gitignored) | F3 | The "gates set before execution" claim is unverifiable as the repo stands |

Nothing else reached category (c). Notably, the catalog itself is clean (§2), which
is the claim A4 most needs.

## Coverage statement

**Searched.** Tag enumeration (`git tag -l`, 30 tags) and resolution of
`v0.5.15.1-*` to commit + date. `git log <tag>..HEAD` and `git diff <tag>..HEAD`
over `packs/core/rules/`, `packs/core/pack.json`, `packs/core/shapes/`, `spec/`,
and `dev/specs/`. `git show <tag>:packs/core/pack.json` to compare the frozen
manifest against HEAD. `git log --diff-filter=A` and `git log -1` on all four
`DECLARATION.md` files, both `studies/*/PREREGISTRATION.md`, all five
`docs/decisions/2026-08-1*` files, `docs/ch4-h2-section.md`, `docs/metrics-spec-r6-u8.md`,
and `studies/real-document-rescore/`. `git show --stat ade81bd3 -- studies/real-document-rescore/`
to establish what that commit actually contained. Repo-wide
`find -iname "*DECLARATION*" -o -iname "*prereg*"` (4 + 5 hits) and
`find -iname "*Phase3*"`. Repo-wide grep for `6bcc76fe6142`, `datasetcard_info`,
`modelcard_info`.

**Search terms derived from the freeze concept itself** (a freeze = a dated
artifact plus a claim of immutability): `DECLARATION`, `PREREGISTRATION`, `freeze`,
`frozen`, `pinned`, `GATE`, `AMENDMENT`, `decisions/` — rather than searching only
for the freezes the parent spec happened to name. This surfaced F6 (four
DECLARATION.md files, of which the parent spec named only the evidence-span one),
F7, and F8.

**NOT searched / not audited.**
- **F3's artifact was never located.** The Phase 3 spec v1.4 (and v1.6/v1.7) is not
  in this repository. Its gate values are quoted second-hand from
  `PHASE3_STATUS_REPORT.md` and `TIER_A_HANDOFF.md`. **This is the largest hole in
  this audit.** If the spec lives in `Praxis/Writing/Drafts/` or elsewhere, F3 needs
  a separate pass.
- **F8 (`harness/bakeoff/results/PREREGISTRATION-2026-05-31-*.md`, 2 files) was
  identified but not audited.** Out of the parent spec's named list; flagged so the
  list is complete.
- `dev/build/adversarial/` is gitignored, so no Phase 2/2.5/3 output artifact was
  examined; per-freeze classification for F2 rests on the committed status reports.
- `TIER_A_HANDOFF.md` (47 KB) was read only via the status report's line citations.
- Post-freeze commits to `packs/vv40/`, `packs/nasa-7009b/`, `packs/model-credibility/`
  were **not** audited — only `packs/core/`, which is what "catalog v0.5.15.1"
  denotes. If A4 claims any other pack was frozen, that needs its own pass.
- No claim here rests on commit *messages* alone: every (a)/(b) classification in §2
  was checked against an actual diff or file-content comparison, except the shapes
  file, where the 785-line diff was classified from its commit set and subjects
  rather than read line by line.
