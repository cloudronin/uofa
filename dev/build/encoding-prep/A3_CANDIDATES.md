# A3 negative control — candidate search and screen

Work order of 2026-08-22, Part 2. Run under **R-A3-SCREEN**
(`docs/UofA_Decision_Record_2026-08-16_Addenda.md`), which R-B invokes after disqualifying
Bologna.

**Recommended pick: Kurtz et al. 2025**, the 3Spine MOTUS lumbar total joint replacement FEM
(`10.3390/bioengineering12030229`, CC BY). **Runner-up: Maquer et al. 2024**, the Zimmer
Biomet humeral stem model (`10.1007/s10439-024-03452-w`), which is cleaner on independence but
paywalled.

Nothing was downloaded into the tree. One document body was read before selection, recorded
in §4 below with what was seen.

## 1. What the slot needs, and what killed most candidates

A3 wants a real, independently produced credibility assessment whose value is that **nobody on
this project constructed, tuned on, or measured with it**. Two failure modes dominated:

- **The document is already ours under a different name.** The single most promising literature
  hit — the ASME V&V 40 end-to-end pedicle-screw example — turned out to be `bundle_nagaraja`,
  a named Decision 7 *development* document. Same DOI, `10.1016/j.ymeth.2024.03.003`. Screen 3
  caught it on the DOI before any reading time was spent.
- **The pool is smaller than it looks.** The NASA 7009 human-research family is essentially
  consumed by this project already (§3.1), and a large share of the V&V 40 literature is
  reviews, frameworks, and plans rather than performed assessments.

## 2. Ranked table

Screens: **1** developer-declared · **2** assessment substance · **3** zero usage hits ·
**4** citable and fetchable · **5** license sanity · **6** pack fit.
`PASS` / `FAIL` / `?` = needs the stated confirmation.

| # | Candidate | Identifier | 1 | 2 | 3 | 4 | 5 | 6 | Character sketch | Disqualifier / open question |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Kurtz, Rundell, Spece, Yarbrough — lumbar TJR contact stresses under misalignment** | `10.3390/bioengineering12030229`, *Bioengineering* 12(3):229, 2025; PMC11939812 | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** (vv40) | 3Spine's own MOTUS device model, formally V&V-40'd, ten V&V activities, and **five limitations disclosed in the authors' own voice** | Factor table lives in **Supplementary S1**, not the body. Confirm it prints goal-vs-achieved per factor before encoding |
| **2** | **Maquer, Mueri, Henderson, Bischoff, Favre — humeral stem primary stability** | `10.1007/s10439-024-03452-w`, *Ann Biomed Eng*, 2024 | **PASS** (all five authors Zimmer Biomet) | **?** | **PASS** (spotless) | **FAIL** | **FAIL** | PASS (vv40) | Manufacturer's own implant model, benchtop **and** clinical validation, built for an in-silico trial in a regulatory submission | **Paywalled, no OA licence.** Abstract does not name V&V 40; framework adoption unconfirmed |
| 3 | Hennigs et al. — computational respiratory system model for mechanical ventilation | arXiv `2607.06210`, 2026-07-07, CC BY 4.0 | **?** | PASS | PASS | PASS | PASS | PASS (vv40) | Explicitly operationalizes V&V 40 + FDA principles; ends in a stated fit-for-purpose decision at medium-low risk | **Preprint — not an accepted submission**, which A3's wording requires. Model's originating developer not identified |
| 4 | Kizilski, Recco et al. — patient-specific patch-planning workflow | `10.1007/s10439-025-03870-4`, *Ann Biomed Eng*, 2025; PMC12685992 | PASS | **?** | **AMBER** | PASS | PASS | PASS | Congenital cardiovascular reconstruction planning, credibility evaluated against a recent framework | **Co-author Brent Craven appears in a corpus fixture** (`morrison-cou1/2.json`); co-author Pathmanathan is on INV-13's candidate list. Document clean, authors are not |
| 5 | Godfrey, Humphreys, Funk, Perusek, Lewandowski — MPCV exercise operational volume | NTRS `20170005224`, GRC-E-DAA-TN38780, 2017, public use permitted | PASS | **FAIL** | PASS (mention-only) | PASS | PASS | ? (7009A, needs `cas_mapping.roll_up`) | NASA GRC assessing its own analysis before delivery to the MPCV program | **A presentation.** States that a 7009 assessment was performed but publishes no factor scores. Repo's own survey classes it as a slide deck |
| — | Scuoppo et al. — aneurysmal ascending thoracic aorta | `10.1007/s13239-025-00801-1`, 2025 | PASS | PASS | **FAIL** | PASS | PASS | PASS | Palermo group's own patient-specific assessment | **Author trace hits a fixture:** Scuoppo and Catalano are both in `bundle_tavi1_s3/ground_truth.json` |
| — | Scuoppo et al. — TAVI credibility assessment Part 2 | `10.1063/5.0280959`, 2025 | PASS | **FAIL** | **FAIL** | PASS | PASS | PASS | Part 2 of the series whose Part 1 is `bundle_tavi1_s3` | Sibling of a corpus document; **no per-factor table** (repo survey: *"neither TAVI paper publishes a per-factor table"*); tavi2 already screened **unusable** at 11.25% pathology |
| — | Curreli et al. — TB dose–response in-silico model | `10.1007/s10439-022-03078-w`, 2023 | PASS | **FAIL** | **FAIL** | PASS | PASS | PASS | Risk-informed V&V 40 credibility **plan** | Its own words: *"a detailed risk-informed credibility assessment **plan**"*, proof-of-concept only — no achieved levels. **Curreli is a Bologna co-author** |
| — | Nagaraja, Loughran, Baumann, Kartikeya, Horner — pedicle screw end-to-end V&V 40 | `10.1016/j.ymeth.2024.03.003`, *Methods* 225:74-88, 2024 | PASS | PASS | **FAIL** | PASS | — | PASS | The obvious literature pick | **Already in the repo as `bundle_nagaraja`**, a Decision 7 named development document. Same DOI |
| — | Ahn, de Weck & Steele — SpaceNet Delphi | `10.1002/sys.21266`, 2014 | **FAIL** | PASS | PASS | FAIL | ? | ? | Ten-person Delphi panel over NASA-STD-7009 factors | Panel opinion, not a developer assessment (A10 §3). Ruled out by R-B. Paywalled |
| — | NASA EVA whole-body FE credibility assessments | NTRS `20230017197` / `20240000233`, `10.1080/10255842.2023.2293653` | PASS | PASS | **FAIL** | PASS | PASS | — | — | **Is the source of `bundle_real_elemance_*` and `bundle_real_thums_*`** |
| — | ASME VVUQ 40.1 — tibial tray worst-case size | ASME technical report | **FAIL** | PASS | PASS | **FAIL** | FAIL | PASS | Subcommittee's illustrative example | Teaching exemplar by the standard's own committee; sold, not fetchable without purchase |
| — | Five Frontiers CM&S papers; FDA nozzle (Hariharan 2017); Pathmanathan applicability | per INV-13 §4 | PASS | **FAIL** | PASS | PASS | PASS | — | — | Prior screen: **no per-factor table** (Frontiers ×5); the other two are round-robin validation and an applicability method, not credibility assessments |

### A distinction screen 3 forced, worth naming

`Kurtz` returns hits at HEAD, and **none of them is a usage hit**. Every one is an
LLM-fabricated bibliography string inside synthetic content — `"(Kurtz 2009)"` and
`"Kurtz et al. (2005)"` in adversarial JSON-LD and in `bundle_nasa_fea_004/source/report.md`,
plus one echo of that same fabricated citation extracted into
`studies/hosted-model-specificity/extracted_rows_2026-08-07_qwen35-4b.json`. The generator
reached for the standard UHMWPE citation. The candidate document, its DOI, its device, its
sponsor and its four co-authors return **zero on every ref**:

    3Spine  MOTUS  rundell  spece  yarbrough  bioengineering12030229   -> 0 files, 0 commits

So this is a third category beyond use and mention: a **synthetic-artifact name collision**.
Recorded rather than waved past, because a name-only grep would have flagged it and a careless
reading would have disqualified the best candidate.

## 3. Pools searched, and what surfaced

Reported so absence is evidenced rather than assumed.

### 3.1 NTRS / NASA-STD-7009 — **largely exhausted by this project**

Nine NTRS documents are already consumed: eight in
`tests/fixtures/extract_corpus_real/MANIFEST.json` (IMM `20150021308`, ARED `20140011878`,
whole-body EVA `20230017197` + `20240000233`, musculoskeletal spacesuit-fit `20240016501` +
`20240011014`, fall-from-heights `20230000585`, boot/ankle `20230000583`), plus Johnson
`20200002832` as the pilot encoding.

Queried NTRS for `"credibility assessment" "7009"` and `"credibility assessment"` broadly. What
came back that was *not* already consumed: `20170005224` (MPCV, ranked 5), `20140013389` (renal
stone — same IMM family as a corpus document), `20140003849` (an alternate NTRS record for the
ARED paper already held), and a methodology cluster that fails screen 2 by definition —
`20140017305`, `20120006603`, `20090005963`, `20080015742`, `20100031270`, `20140017017`.

This matches the repo's own survey, which put the realistic NTRS ceiling at **roughly 7
distinct documents, about 3 of them journal prose**, and concluded *"NTRS is thin for prose."*
**No new NASA candidate of assessment substance surfaced.**

### 3.2 ASME V&V 40 / JVVUQ / VVUQ symposium — the productive pool

Systematic pass over Europe PMC for `("V&V 40" OR "VV40") AND "credibility assessment"`, plus
targeted searches. Of sixteen records returned, **seven perform an assessment on their own
model**; the rest are reviews, frameworks, regulatory updates, or plans. Of those seven, three
are already ours or adjacent (pedicle screw = `bundle_nagaraja`; TAVI I = `bundle_tavi1_s3`;
TAVI II and ATAA = same group), one is a plan (Curreli), and one is Morrison — leaving
**Kurtz** and, from separate searches, **Maquer** and **Kizilski**.

ASME's own **VVUQ 40.1** technical report (tibial tray) is a committee exemplar and is sold
rather than published — fails screens 1 and 4.

### 3.3 FDA / MDIC — no standalone candidate

The FDA guidance (`fda.gov/media/154985`) and the 2024 FDA/MDIC symposium materials are
guidance and presentations, not assessments of a named model. FDA staff appear as *co-authors*
on candidates 1-4's pool rather than as publishers of a separate assessable document. The FDA
blood-pump case study is Morrison, already corpus.

### 3.4 Regulatory submissions / EPARs — poor fit, not pursued past screening

EMA PBPK qualification material is guidance plus an aggregate review of assessment reports; the
underlying model reports are not separately published, and the vocabulary is PBPK qualification
rather than 7009 or V&V 40 — **screen 6 would fail on cross-standard mapping burden well past
Johnson-sized.** Recorded as searched and set aside.

### 3.5 National labs (Sandia, LLNL) — methodology, not assessments

Sandia's PCMM material (OSTI 1480395, 976951, 1645881) and the ASME JVVUQ Sandia V&V Challenge
Problem paper describe the PCMM *framework* or a challenge exercise. PCMM is also a **third
standard tradition** — its maturity dimensions do not map onto `nasa-7009b` or `vv40` without
inventing vocabulary, so screen 6 fails even where screen 2 might pass. **No candidate.**

### 3.6 One INV-13 gap closed in passing

INV-13 §4 lists the *"2024 pharma-manufacturing 7009 paper"* as **unidentifiable** — no DOI or
venue. It is *"Enhancing simulation credibility through data model development: A case study
using NASA-STD-7009,"* ScienceDirect `S2665917424004379`. Recorded so INV-13's open item can
close; **not ranked**, because it is a data-model methodology case study rather than a
credibility assessment of a named model, and the publisher returned 403 to run-time fetch.

## 4. Recommended pick — Kurtz et al. 2025

**Kurtz SM, Rundell SA, Spece H, Yarbrough RV.** *Sensitivity of Lumbar Total Joint Replacement
Contact Stresses Under Misalignment Conditions — Finite Element Analysis of a Spine Wear
Simulator.* Bioengineering (Basel) 2025;12(3):229. `10.3390/bioengineering12030229`.
PMC11939812. **CC BY.**

It is the only candidate that passes all six screens on evidence rather than on expectation.
Screen 1 is unambiguous in a way most of the pool is not: the work is institutionally funded by
3Spine, a 3Spine employee is a co-author, and the model is of 3Spine's own MOTUS device — this
is the developers' assessment of their own model for their own use decision, not a third party
writing about someone else's device. Screen 2 is satisfied in the body, which states the FEM
was *"formally verified and validated using the risk-informed credibility assessment framework
established by ASME V&V 40 and FDA guidance,"* carries a stated context of use (bearing
stresses under reasonably worst-case misalignment against Mode I and Mode IV wear-test
conditions), ten V&V activities, and a stated adequacy conclusion with numbers attached.
Screens 4 and 5 are as clean as this literature gets — CC BY, mirrored in PMC, no credential
anywhere on the path — and screen 6 needs no mapping at all, because the document speaks native
V&V 40 into the `vv40` pack.

What decides it over the runner-up is the ranking rule's second term. **The paper discloses
five limitations in the authors' own voice** — the QOI is misalignment rather than misuse or
revision, validation is tied to one specific L-TJR design, the analysis addresses stresses and
strains rather than wear, boundary conditions simulate the simulator without bone-implant
effects, and other scenarios would need further V&V. That is exactly the texture that makes an
adjudicated FP case study worth reading: a firing on a disclosed limitation is a governed
Overruled-on-merit decision with something real to adjudicate, whereas a flawless document
produces an uninformative n=1. It also carries a full conflict-of-interest disclosure, which
gives the encoding real provenance material to work with.

**One thing to confirm before encoding, not after.** The credibility detail sits in
**Supplementary Material S1** — *"Table S1: Summary of seven verification and three validation
activities performed for the L-TJR FEM in accordance with ASME V&V 40-2018 and FDA guidance"* —
not in the main text, and the body does not print required-versus-achieved levels per factor.
Ten activities is also fewer than V&V 40's twenty-three factors. So the open question is
whether S1 is a *goal-versus-achieved table* (Bologna-shaped, richly encodable) or an
*activities list* (thinner, still encodable but a different packet). Fetch S1 from the PMC or
MDPI record and confirm before the packet-prep runs. If S1 turns out to be an activities list
only, the pick still stands on screens 1 and 3-6, but the packet should be scoped accordingly
and the author told the assessment is activity-level.

**Access note for screen 4:** `mdpi.com` returned **403** to automated fetch (bot protection).
The **Europe PMC / PMC route works** — `PMC11939812`, full text retrievable without
credentials. Record that as the fetch path in the manifest so the run-time fetch does not fail
against the publisher's front door.

## 5. Runner-up — Maquer et al. 2024

**Maquer G, Mueri C, Henderson A, Bischoff J, Favre P.** *Developing and Validating a Model of
Humeral Stem Primary Stability, Intended for In Silico Clinical Trials.* Ann Biomed Eng 2024.
`10.1007/s10439-024-03452-w`.

Strongest candidate on the two screens that matter most for a negative control, and the reason
it is the runner-up rather than the pick is entirely about access. Screen 1 is the best in the
slate: **all five authors are Zimmer Biomet**, assessing their own humeral stem model, with the
stated purpose of enriching clinical data in a regulatory submission. Screen 3 is spotless —
`maquer`, `zimmer`, `biomet`, `humeral` and `shoulder arthroplasty` return **zero files and
zero commits on every ref**, with none of the synthetic-collision noise that Kurtz carries and
none of the co-author entanglement that sinks Kizilski. It is the most genuinely *external*
document found.

It loses on screens 4 and 5: **Springer subscription, no open licence**, so it is not
retrievable at run time without credentials and the cited-not-committed rule has nowhere clean
to stand. Screen 2 is also unconfirmed — the abstract describes a twofold benchtop-plus-clinical
validation scheme but does not name ASME V&V 40 or credibility factors, so whether it prints an
assessment or a validation study is an open question that the paywall prevented settling.
**If the author wants this one, both questions resolve together in a single library-proxy read**
— the same access route U-INV-1 is already queued for. Should that read confirm a V&V 40 factor
table, this becomes the better document and the licence question is the only remaining obstacle.

## 6. What was read, and when

Per the work order's instruction to note pre-selection body reads:

| Document | Depth | When |
|---|---|---|
| Kurtz et al. 2025 (`PMC11939812`) | **Full text read via Europe PMC**, pre-selection — required to settle screen 2, which the abstract could not | Before ranking |
| All others | **Abstract, landing page or indexed metadata only** | Before ranking |

No PDF was downloaded into the working tree. Nothing was committed but this report. No document
was encoded.

## 7. Author's acts

1. Read §2 and pick, or send the runner-up to the library-proxy queue.
2. Commit the R-B addendum (staged, not committed).
3. Packet-prep for the chosen document then runs under the standing aero work-order pattern.
