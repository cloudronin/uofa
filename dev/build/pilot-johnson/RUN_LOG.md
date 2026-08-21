# Run log — Johnson encoding pilot

Spec: `UofA_Encoding_Pilot_Spec_v1_0_Johnson.md` v1.0 (ACTIVE, 2026-08-19)
Session date: 2026-08-20
Governed review session: 2026-08-21 (see **The governed review pass** below)
State: **ADJUDICATED AND SIGNED, 2026-08-21.** The dispositions and the ambiguity log
carry the author's verdicts. The package was signed, re-imported the same day to correct
its operator attribution, and re-signed. The signature in force is the second one. See
**The attribution correction** below.

Everything in the 2026-08-20 session was preparation under spec §0. Its dispositions
were candidates. The author re-adjudicated every one of them in the review pass of
2026-08-21, under the committed protocol `docs/Encoding_Protocol_v0_1.md` v0.1.

## Pins

| What | Value |
|---|---|
| Repo HEAD at session start | `21dfcac` |
| Repo HEAD after the gitignore carve-out | `2b40dfe` |
| Site commit (on-ramp page) | **`31cb466`** (2026-08-18) |
| `uofa` version | 0.11.0 (editable install, `.[extract,excel,test]`) |
| Pack | `nasa-7009b` 0.5.0 |
| Extract prompt sha256 (first 16) | `c47bf1745a12084e` (`packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt`) |
| Rule engine | `uofa-weakener-engine-0.1.0.jar`, built from `src/weakener-engine` with Maven, 19 903 448 bytes |
| JRE | system OpenJDK 21.0.10 (no bundled runtime in this environment) |
| Source document sha256 (first 32) | `1b767b2d4128dcc67bdb6803fe33034e` |
| Source copy in tree | `source/NTRS-20200002832-Johnson-2020.pdf` |
| base_uri | `https://github.com/cloudronin/uofa` (governed pass) **[AUTHOR-CONFIRMED 2026-08-21 — ruled keep as minted; A-27 resolves confirmed-by-author]**. `https://uofa.net` is refused by `resolve_base_uri` as reserved for the project's published examples, so the author-controlled repository namespace is used instead. The id is covered by the signature and cannot change after signing, so confirm this namespace before the sign-off commit. The pilot pass minted under the `example.org` placeholder and recorded it as deviation A-25; protocol-check flagged the run log's silence about the field, which is why the row exists |

### Site commit drift — finding F-1c

The protocol outline's Prompt 1c names `01c7372` as "today's" site commit. The
commit that currently builds the on-ramp page is `31cb466`. The pilot pins
`31cb466` and the drift is recorded rather than silently reconciled, because a
protocol that tells an encoder to pin a commit needs to say what happens when the
outline's own pin has moved on. Filed under §1 of the findings memo.

## Extractor

    uofa extract dev/build/pilot-johnson/source/NTRS-20200002832-Johnson-2020.pdf \
      --pack nasa-7009b \
      --extract-backend anthropic \
      --extract-model claude-sonnet-5 \
      -o dev/build/pilot-johnson/johnson-extracted.xlsx

| Field | Value |
|---|---|
| Backend | `anthropic` (litellm provider path, key from `ANTHROPIC_API_KEY`) |
| Model | `claude-sonnet-5` |
| Thinking mode | **off** — `--thinking` not passed; the flag defaults False |
| temperature | backend default (not set by the CLI) |
| max_tokens | 16384 (extractor default; the same value the extraction eval pinned) |

### The model string is NOT "the same as the extraction eval" — read this before citing it

Spec §2 says to use "the same frontier model the extraction eval used." Checked
against the trace, that phrase has no referent, and the run log says so rather
than asserting a lineage the repo does not support.

- `docs/extract_eval_v1.md` (2026-05-04) **is** the extraction eval, and its
  extractor ran on local `ollama/qwen3.5:4b`. Its own cost table reads
  "Iteration API ($): $0 (local qwen)", and its failure analysis is about
  qwen3.5:4b dropping closing braces in long JSON. Sonnet 4.6 appears in that
  report only as the **corpus generator** ($6.13, two-step). So the extraction
  eval used no frontier model at all.
- `dev/tools/scripts/extract_accuracy_log.jsonl` agrees: 9 rows
  `ollama/qwen3.5:4b`, 6 rows Together `Llama-3.3-70B-Instruct-Turbo`, zero
  Anthropic rows.
- The only frontier **extractor** run in the repo is arm 4 of the
  model-selection scorecard (`studies/model-selection/`,
  `dev/tools/scripts/model_selection.py`), a later and separate study. Its
  declared string `claude-sonnet-5-2026` returns HTTP 404 and it runs as
  `claude-sonnet-5` (DECLARATION.md:48-56).

**Author ruling, 2026-08-20:** run current Sonnet and disclose the divergence.
The pilot's extractor is `anthropic/claude-sonnet-5`, which postdates both the
extraction eval's `ollama/qwen3.5:4b` and the scorecard's arm 4. The pilot
measures protocol friction, not H2 comparability, so a newer extractor is fine
as long as the delta is stated. It is stated here. Filed under §3 of the
findings memo as the rule the protocol needs: an encoding names its extractor by
version and says what it is *not* the same as, rather than inheriting a claim
from a spec sentence.

## Provenance self-audit (spec §2.4)

The counts do not reconcile, and the gap is the finding.

| Count | Value |
|---|---|
| `field provenance:` from `uofa import` | **1 derived, 4 extracted, 6 run-context** (11 fields) |
| Review decisions taken (`REVIEW_LEDGER.md`) | **97** — 47 confirmed, 14 corrected, 36 blanked source-absent |
| Populated cells in the reviewed workbook | 155 across 29 data rows |
| Data rows carrying a `Source Anchor` | **29 of 29** |
| Required-level cells sourced from Table 3 geometric recovery (author-side, never `extracted`) | **5** — Data pedigree, Development process and product management, Results uncertainty, Results robustness, Use history |

**Reconciliation, 2026-08-21.** Post-§3c regeneration: **101 decisions, 17 corrected**. The
97/14 figure above describes the pre-addition pass and is left as written, because it is a
historical statement about that pass and is cited as one. `REVIEW_LEDGER.md` is the
authoritative count; anything citing a decision total cites the ledger.

### The surprise, recorded rather than fixed

**Four fields are counted as `extracted` after a review pass that took 97
decisions across 155 cells.** The provenance map (`excel_mapper._provenance`)
classifies eleven summary-level fields and nothing else: not one credibility
factor, not one validation result, not the decision record. So the count answers
"how much of the *summary* was read", and the on-ramp page presents it as
answering "how much of this package was actually read."

Worse for the praxis claim: the count cannot distinguish a package the author
reviewed cell by cell from one imported straight out of the extractor. Both
report 4 extracted. **The human contribution is invisible to the only field that
exists to measure it** — and Ch3's Human Adjudication Role section is meant to
rest on these counts. Filed as the §7 finding.

Also unreconcilable by construction: the 5 required-level cells recovered from
Table 3's shading are author-side work, and there is no provenance class that
says so. They are simply not counted anywhere.

### Profile: reported and written disagree

`uofa import` printed `Profile: Complete`. The package carries
`conformsToProfile: ProfileMinimal`.

`import_excel.py:169` prints `data['summary']['profile']` — the value the
*workbook declared* in cell D3. The derived value comes from
`excel_mapper.derive_profile`, whose own docstring says declaring what the
spreadsheet said "is how all five gpt-5 extractions came to claim ProfileComplete
without containing Complete's fields", and the on-ramp page promises "The declared
profile is *derived* from what the package contains rather than asserted." The
derivation is correct and the package is right. The summary line still reports the
assertion. Filed as F-6, a one-line fix.

### Derived credibility metrics all read zero

    credibilityIndex 0.00   traceCompleteness 0.00
    validationCoverage 0.00   verificationCoverage 0.00

This is the honest encoding's cost. Because no 7009A level was rewritten onto a
1-5 V&V 40 factor (A-06), the 13 V&V 40 factors carry evidence and no level, and
every derived metric that reads levels reports nothing. A paper that states
Verification achieved 4 produces `verificationCoverage 0.00`.

The raw extraction would have produced non-zero values for all four, from
synthesized levels. **There is no way to encode this source that is both honest
and non-misleading**, and that is the strongest single result of the pilot.

## Command trace

| # | Command | Outcome |
|---|---|---|
| 0 | `pip install -e '.[extract,excel,test]'` | uofa 0.11.0 |
| 0 | `mvn package` in `src/weakener-engine` | JAR built |
| 0 | `uofa check packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld` | C1 ✓ C2 ✓ C3 ✓ — toolchain sound before the pilot touches anything |

---

## The governed review pass — 2026-08-21

Protocol A-13 requires the run log to leave no ambiguity about whether a review was
machine-drafted preparation or a named person's review, and about who performed it.

| Field | Value |
|---|---|
| Reviewer | **Vishnu Vettrivel**, author |
| Date | 2026-08-21 |
| Governing protocol | `docs/Encoding_Protocol_v0_1.md` v0.1 (committed) |
| Form | Conducted in conversation, the author ruling each item |
| Record of the verdicts | `Johnson_Author_Verdict_Record.md` |
| What was ruled | the minting namespace; a cell walk over the workbook; all eleven weakener firings; the fifteen-factor silence sweep; all 28 ambiguity-log entries |
| Application to the artifacts | mechanical, by Claude Code, from the verdict record. Six divergences escalated rather than reconciled, all six dispositioned by the author the same day — `APPLY_RECORD_ESCALATIONS.md` |
| Still unadjudicated | **none.** Ambiguity entries A-13, A-19 and A-22 were displaced by the record's mis-addressed rulings, returned to the author, and confirmed as drafted on 2026-08-21. All 30 log entries are adjudicated |
| Signing | signed by the author 2026-08-21, superseded by the attribution re-import the same day, and **re-signed**. Two signatures, one in force. See the sections below |

The 2026-08-20 pass was machine-drafted preparation and is labelled as such throughout.
The 2026-08-21 pass is the review A-6 and A-13 mean. The two are recorded separately so
that no reader has to infer which produced a given value.

---

## The signing — 2026-08-21 (first signature, SUPERSEDED)

**This signature no longer holds.** It signed the package as it stood before the
attribution correction below, and the re-import discarded it. The section is kept as the
record of what was signed and verified, not as a statement about the current file.

Performed by the author with the research key held outside the tree. The apply-record
session did not sign and does not hold the key; it verified the result afterwards and
recorded it here.

| Field | Value |
|---|---|
| Signed by | **Vishnu Vettrivel**, author, with `~/.config/uofa/research.key` |
| Date | 2026-08-21 |
| `signatureAlg` | `ed25519` |
| `canonicalizationAlg` | `json-sortkeys/v1` |
| `signature` | `ed25519:78e4d877f740d0c5…a7d0501` |
| `hash` | `sha256:58e849c2bcb4971bbd3dbb320643397e191f87bbb323d4de9efd4073ded53a73` |
| Governing protocol | `docs/Encoding_Protocol_v0_1.md` v0.1 |

### Verification after signing (of the superseded package)

    uofa check dev/build/pilot-johnson/johnson-pilot.jsonld

    ✓ C2 SHACL   ✓ C1 Integrity   ✓ C3 Rules

**C1 Integrity passes for the first time.** Before signing it correctly reported the
importer's zero-filled `hash` and `signature` placeholders as invalid — the condition
finding F-6d describes. The weakener report is unchanged at **11 firings across 5
patterns**, which are the eleven the author dispositioned; signing adds no firing and
clears none, and `W-SI-01` stays silent for the reason F-6d gives rather than because
the package is now signed.

### What a signature freezes

The identifiers minted under `https://github.com/cloudronin/uofa` are covered and cannot
be corrected without re-importing and re-signing. That includes the `base_uri` confirmed
under A-27, every node identifier derived from it, and the package's `wasAttributedTo` —
which is exactly why the first signature was superseded rather than amended.

---

## The attribution correction — 2026-08-21, after the first signing

### What was wrong

The first signed package carried `wasAttributedTo: …/org/claude`.
`excel_mapper._operator_identity()` resolves **who ran the tool** from `UOFA_ASSESSOR`,
then `git config user.name`, then `$USER`. The 2026-08-20 import ran in a container — its
`provenanceChain.sourceFile` was `/home/user/uofa/dev/build/pilot-johnson/johnson-extracted.xlsx`,
not the working tree's path — and the identity there resolved to `claude`.

The value was not false. The mapper's R1 rule deliberately separates operator from
assessor: `statedAssessor` is `K.L. Johnson`, read from the source, and `wasAttributedTo`
is whoever ran the import, which genuinely was a machine agent. It was, however, an
incidental container identity that nobody chose, recorded in no pin, and frozen under a
signature. **Author ruling 2026-08-21: fix it.**

### What was done

    UOFA_ASSESSOR="Vishnu Vettrivel" uofa import \
      dev/build/pilot-johnson/johnson-extracted.xlsx \
      --pack nasa-7009b \
      --base-uri https://github.com/cloudronin/uofa \
      --protocol-check

The operator is now set explicitly rather than inherited from the environment, which is
the point: the same command in any environment produces the same attribution.

### What changed in the package, measured rather than asserted

The re-import was diffed field by field against the signed package it replaces. **Five
fields differ and no others.** All 19 credibility factors and all 6 validation results are
identical.

| Field | Before | After |
|---|---|---|
| `wasAttributedTo` | `…/org/claude` | `…/org/vishnu-vettrivel` |
| `provenanceChain[0].sourceFile` | `/home/user/uofa/…` (container) | the working tree's path |
| `provenanceChain[0].timestamp` | `2026-08-20T04:19:56Z` | `2026-08-21T03:09:27Z` |
| `generatedAtTime` | `2026-08-20T04:19:56Z` | `2026-08-21T03:09:27Z` |
| `signature` / `hash` | the author's ed25519 signature | importer placeholders again |

`toolVersion` is `uofa-cli 0.11.0` on both, matching the pinned version, so nothing moved
underneath the re-import. `uofa rules` reports the same **11 firings across 5 patterns**,
the eleven the author dispositioned.

### The signature in force — 2026-08-21, second signature

The author re-signed the corrected package with the same research key. This is the
signature that holds.

| Field | Value |
|---|---|
| Signed by | **Vishnu Vettrivel**, author, with `~/.config/uofa/research.key` |
| Date | 2026-08-21 |
| `signatureAlg` | `ed25519` |
| `canonicalizationAlg` | `json-sortkeys/v1` |
| `signature` | `ed25519:8d5b00502bfbf890…` |
| `hash` | `sha256:be683191bc7abdbb…` |
| Covers | the corrected `wasAttributedTo`, and every identifier minted under the A-27 namespace |

Verification:

    uofa check dev/build/pilot-johnson/johnson-pilot.jsonld

    ✓ C2 SHACL   ✓ C1 Integrity   ✓ C3 Rules

`uofa rules` reports the same **11 firings across 5 patterns**, matching the dispositioned
set node for node.

**The superseded first signature** is `ed25519:78e4d877f740d0c5…a7d0501` over hash
`sha256:58e849c2bcb4971b…ded53a73`, preserved in commit `d633df0e` and recoverable from
there. It signs a package that no longer exists in the tree, and it is recorded rather than
quietly dropped so the history stays legible.

Signing is the author's act. The apply-record session does not hold the key and did not
sign either time.
