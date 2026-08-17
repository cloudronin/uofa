# INV-13 — Read-before-admit screen of A10 candidates

Status: **PARTIAL — criterion escalation resolved by v2.0; a counting problem
replaces it**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A10, A5, A9

---

# ADDENDUM — re-investigated against parent spec v2.0

## The criterion escalation is resolved, in the direction §2 predicted

v2.0's A10 splits the pool in two and says so explicitly:

> **Scorecard pool** (per-factor table transcribable): ~5 documents… No expansion
> expected.
> **Annotation pool** (factor evidence present in prose, no scorecard required):
> the H2 reference corpus. **The survey's scorecard rejects re-qualify here.**

That is the exact distinction §2 of the original finding argued for, and it means
**the five Frontiers papers are back in scope**, not rejected. The survey's
"0 of 7 usable" verdict answers the scorecard question and says nothing about the
annotation question. The survey's own partial positive — three of the seven state
model risk, model influence or decision consequence in prose ([survey:237-241](docs/real-corpus-supply-survey.md))
— is now evidence *for* admission rather than a footnote.

The inclusion rule is also committed in v2.0 A10 §1, which the original finding
listed as blocking:

> published paper or public report containing prose evidence for **≥N** credibility
> factors of V&V 40 or NASA-STD-7009, readable by the pipeline reader. Exclusions:
> Morrison, Nagaraja, and NASA HPT sources (case-study contamination); any document
> failing the reader-pathology screen (TAVI I/II stay out unless the lost-spaces fix
> ships).

Two of my three blockers are gone. **N is still unbound** — see §"Still needed".

## The new problem: the 11-14 arithmetic does not close

A10 §3 states the target as *"11-14 total annotated documents (6 current + 5-8
admitted)."* I have now identified the 6 current documents, from
[studies/real-document-rescore/FINDINGS.md](studies/real-document-rescore/FINDINGS.md),
which reports the pooled run over "all six annotated papers":

| # | Document | Pack | Factors annotated | Sentences | Admissible under A10's own exclusions? |
|---|---|---|---|---|---|
| 1 | opensim | nasa-7009b | 7 | 521 | yes |
| 2 | elemance | nasa-7009b | 6 | 1319 | yes |
| 3 | ared | nasa-7009b | 7 | 205 | yes |
| 4 | bologna | vv40 | 13 | 895 | yes — but **contested**, see below |
| 5 | **nagaraja** | vv40 | 12 | 960 | **NO — named exclusion** |
| 6 | **morrison** | vv40 | 11 | 676 | **NO — named exclusion** |

**Two of the six current documents are the two the inclusion rule excludes by
name.** The rule is written for admission ("before admitting any paper"), so
whether it reaches back over the existing six is genuinely ambiguous — but the
reason for the exclusion, case-study contamination, does not care when the
document was annotated. Morrison and Nagaraja are the case studies; their prose is
the same prose whether it entered the pool last week or last year.

Consequences, taking the exclusion at face value:

| | count |
|---|---|
| A10's stated base | 6 |
| minus named exclusions (morrison, nagaraja) | **4** |
| admissions needed to reach 11 | **7**, not 5 |
| admissions needed to reach 14 | **10** |
| candidates available | 11, of which 2 are unidentifiable and 2 have unverified licensing → **7 screenable** |

**Reaching 11 would require admitting every screenable candidate.** That is not a
plan; it is a coincidence that would have to hold. And it gets tighter if Bologna is
also spoken for — A10 itself assigns Bologna to the **scorecard pool** ("Bologna
(Aldieri 2023) is the next bundle"), and INV-5 recommends it as A3's external
negative. One document, three claims on it.

If the exclusion is *not* read retroactively, the base is 6 and the arithmetic
closes as written — but then H2's real-corpus figure is measured partly on the two
documents that are also the H3 case studies, and A9's disclosure has to say so.
**That is the author call**, and it is a cleaner one to make now than after the
annotation hours are spent.

## Re-screen of the five Frontiers papers against the annotation criterion

Under the annotation-pool rule, the correct prior evidence is no longer the
per-factor-table column. Re-reading the survey's D3 section against A10's actual
criterion:

| Candidate | Scorecard verdict (survey) | Annotation-pool status |
|---|---|---|
| Coronary stent `10.3389/fmedt.2021.702656` | no table — *"not in the scope of this study to perform a step-by-step risk-informed credibility assessment"* | **Unscreened.** The quoted sentence rules out a *completed assessment*; it does not rule out prose evidence about model risk, validation activities, or code verification. |
| Flow-diverter `10.3389/fmedt.2021.705003` | no table — *"This work is not yet started for ANKYRAS as a clinical tool"* | **Unscreened**, same reasoning |
| EVAR stent-graft `10.3389/fmedt.2021.704806` | no table | **Unscreened** |
| Bioresorbable scaffold `10.3389/fmedt.2021.724062` | *"QoI and CoU only, qualitative"* | **Likely admissible on the survey's own words** — QoI and CoU in prose are credibility-factor evidence; whether it clears ≥N depends on N |
| Cardiovascular UQ `10.3389/fmedt.2021.748908` | no table | **Unscreened** |

Plus the survey's standing note that **three of the seven** state model risk, model
influence or decision consequence in prose — factors K7/K8 — which is direct
evidence of prose factor evidence in at least three of these five.

**Net: the annotation pool is in better shape than the original finding suggested,
and the constraint has moved from supply to arithmetic.**

## What v2.0 also settles

- **TAVI I/II are excluded by the spec itself** ("stay out unless the lost-spaces
  fix ships"), confirming the original finding's rejection and removing them from
  any recount.
- **Ahn & de Weck now has an explicit dual role**: A10 §2 says to screen it for the
  scorecard pool too, noting *"it carries a filled CAS of a named platform and sits
  outside NTRS."* That is a stronger prior than the original finding had, and it
  makes Ahn & de Weck the highest-value single fetch on the list — it can relieve
  the scorecard pool (freeing Bologna for A3) **and** count toward the annotation
  pool.
- A10 is **rank 8** and explicitly gates nothing ("precision, nothing gates on it"),
  so none of this blocks the defense-deciding tier.

## Still needed before the screen can run

| # | Blocker | Owner |
|---|---|---|
| 1 | **Bind N** in "prose evidence for ≥N credibility factors." The current six range from 6 to 13 factors, so N=6 admits documents comparable to the weakest current member; N=10 would exclude two of the current six. **N is what decides whether the pool closes.** | author |
| 2 | Rule retroactivity: do morrison and nagaraja stay in the annotation pool? | author |
| 3 | DOIs for the two unidentified candidates (3D-printed wrist-hand orthosis; 2024 pharmaceutical-manufacturing 7009 paper) | author |
| 4 | Go-ahead to fetch open-access PDFs (Frontiers ×5 CC BY, PLoS ONE, likely Pathmanathan) with manifest + SHA-256 per the `extract_corpus_real/MANIFEST.json` discipline; decision on the two paywalled ones (CMBBE, Wiley) | author |

With 1-4 answered, the screen itself is the 3-4h session described in §5 of the
original finding, and it should start with Ahn & de Weck.

## Escalation (revised)

The original escalation (criterion mismatch) is **withdrawn** — v2.0 resolves it.

**Replacing it:** A10's 11-14 target does not close under its own exclusion list.
Reaching 11 requires either admitting every screenable candidate, or reading the
morrison/nagaraja exclusion as non-retroactive and disclosing the H2/H3 corpus
overlap that follows. The done-gate's alternative — *"or the measured ceiling
disclosed with screen results"* — remains available and is well supported by the
survey. **This is a decision to take before annotation hours are spent, not after.**

## Coverage statement (addendum)

**Searched.** v2.0 §0.1 GATE-H2, A5, A9, A10 (all four numbered clauses), D8.
`studies/real-document-rescore/FINDINGS.md:1-60` for the six-document roster with
per-paper factor counts and sentence counts. Re-read `docs/real-corpus-supply-survey.md`
§D3 against A10's annotation criterion rather than its scorecard criterion.

**NOT done — unchanged from the original finding.** No PDF fetched, no
reader-pathology screen run, no factor-evidence inventory produced, Ahn & de Weck
not examined. The re-investigation changed which candidates are in scope and what
the arithmetic requires; it did not perform the screen, which still needs the four
blockers above cleared.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Headline

**Do not run this screen from scratch. Five of the eleven named candidates have
already been screened, by this project, with the result recorded and cited.**

`docs/real-corpus-supply-survey.md` §"D3: the Frontiers collection screened — 0 of
7 usable" (2026-08-06) covers the coronary-stent, flow-diverter, EVAR, scaffold and
cardiovascular-UQ papers. That screen used a **stricter** criterion than A10's
likely inclusion rule, so it does not settle admission — but it is decisive on the
question of whether these papers carry per-factor credibility tables, and it
reframes the whole item.

The item's escalation criterion — *fewer than 5 candidates survive* — is **very
likely to trigger**, and the surrounding evidence says the shortfall is a property
of the published literature, not of the search.

## 1. Prior screening already on file

| Candidate (INV-13's list) | DOI | Prior screen result | Source |
|---|---|---|---|
| Coronary stent deployment | `10.3389/fmedt.2021.702656` | **no per-factor table.** Paper states: *"it is not in the scope of this study to perform a step-by-step risk-informed credibility assessment."* | [survey:223,226-227](docs/real-corpus-supply-survey.md) |
| Flow-diverter aneurysm | `10.3389/fmedt.2021.705003` | **no per-factor table.** Paper states: *"This work is not yet started for ANKYRAS as a clinical tool."* | [survey:222,228-229](docs/real-corpus-supply-survey.md) |
| Stent-graft EVAR | `10.3389/fmedt.2021.704806` | **no per-factor table** | [survey:224](docs/real-corpus-supply-survey.md) |
| Bioresorbable vascular scaffold | `10.3389/fmedt.2021.724062` | **no** — QoI and CoU only, qualitative | [survey:221](docs/real-corpus-supply-survey.md) |
| Cardiovascular UQ | `10.3389/fmedt.2021.748908` | **no per-factor table** | [survey:219](docs/real-corpus-supply-survey.md) |

The survey's diagnosis is chronological rather than a quality judgement: *"The
collection is about V&V methodology, not completed V&V 40 assessments… these are
2021 papers, V&V 40 was published in 2018, and the completed per-factor assessments
in the corpus are 2019, 2023 and 2024"* ([survey:231-235](docs/real-corpus-supply-survey.md)).

**Crucially, the survey also records a partial positive:** *"Three of the seven do
state model risk, model influence or decision consequence in prose. They are
therefore candidates for the **K7 and K8 rows only**"* ([survey:237-241](docs/real-corpus-supply-survey.md)).

## 2. The criterion mismatch — read this before reusing the survey's verdict

The survey screened on: **does the article publish a per-factor credibility
assessment table?**

INV-13 step 3 asks for: **which V&V 40 / 7009 credibility factors have prose
evidence in the text, with one example span each.**

**These are different questions, and the second is strictly weaker.** A paper can
discuss model risk, validation activities and code verification in prose — yielding
annotatable spans — without ever printing a gradation table. Treating "no
per-factor table" as "no factor evidence" would be the exact keyword-for-claim
substitution the parent spec's ground rules warn against, and the survey's own
K7/K8 note shows it would be wrong for at least three of the five.

**Therefore:** the five Frontiers papers are **not** rejected by INV-13. They are
rejected *for the table criterion* and **unscreened for the prose-evidence
criterion**. Which of the two A10's committed inclusion rule uses is the author's
call, and it decides whether the pool is 5-short or not.

This is also why the item's note is right that admission waits on the rule: with a
table-based rule the pool is near-empty; with a prose-evidence rule several of these
return.

## 3. Exclusion check (item step 5) — clean

Checked by DOI lineage and author overlap, not title similarity, per the item.

| Anchor | Overlap with candidates? |
|---|---|
| Morrison et al. 2019, hemolysis in centrifugal blood pumps | No. Different DOI prefix (Springer `10.1007/s13239-…`), different authors, different device class. |
| Nagaraja (spinal device) | No. |
| NASA HPT (NASA-STD-7009B aerospace) | No — all candidates are FDA/biomedical or systems-engineering. |

The survey's precedent case (two alternate-version duplicates, `20240000233` and
`20240011014`) is an **NTRS** phenomenon; the NTRS corpus is disjoint from INV-13's
candidate list, which is entirely journal literature. **No alternate-version risk
detected.**

One adjacency worth naming: **Bologna** is not on INV-13's list but is in the same
V&V 40 pool and is **already a repo bundle** (`bundle_bologna_bcthip`), used in at
least four committed studies. If A10's pool draws from the same literature, Bologna
must be excluded from A10 or its prior exposure disclosed — and INV-5 wants it too.
See INV-5 §5.

## 4. Per-candidate table (as far as the evidence goes)

| Candidate | Access status | Pathology screen | Factor-evidence inventory | Scorecard flag | Exclusion |
|---|---|---|---|---|---|
| Coronary stent `10.3389/fmedt.2021.702656` | Frontiers, open access (CC BY) — processing permitted | **not run** | **not run**; no per-factor table (prior screen) | — | clean |
| Flow-diverter `10.3389/fmedt.2021.705003` | as above | not run | not run; no table | — | clean |
| EVAR `10.3389/fmedt.2021.704806` | as above | not run | not run; no table | — | clean |
| Scaffold `10.3389/fmedt.2021.724062` | as above | not run | not run; QoI/CoU only | — | clean |
| Cardiovascular UQ `10.3389/fmedt.2021.748908` | as above | not run | not run; no table | — | clean |
| FDA nozzle (Hariharan 2017, PLoS ONE) | PLoS ONE, CC BY — processing permitted | **not run** | **not run** | — | clean |
| Spine PJF V&V 40 (CMBBE 2022) | Taylor & Francis — **licensing not verified** | not run | not run | — | **check author overlap with Nagaraja** (both spinal-device V&V 40); not verifiable without the paper |
| Wrist-hand orthosis | **not identified** — no DOI, author or year given in the parent spec | — | — | — | cannot check |
| Pathmanathan applicability (2017) | likely open access | not run | not run | — | clean |
| **Ahn & de Weck, SpaceNet Delphi** (Wiley *Systems Engineering*) | Wiley — **licensing not verified** | not run | not run | **step 4 not performed** — does it print a transcribable per-factor CAS table for SpaceNet at published granularity? **Unanswered.** | clean (different domain) |
| 2024 pharma-manufacturing 7009 paper | **not identified** — no DOI or venue given | — | — | — | cannot check |

**Two of eleven candidates cannot be identified from the parent spec's
description** (wrist-hand orthosis; 2024 pharma-manufacturing 7009). They need a
DOI from the author before anything can be screened.

## 5. Why the screen was not run, and what it needs

The item's steps 1-4 require: fetching each PDF to local storage, running the
pipeline reader over it, computing the >20-char alpha-token rate plus column-interleaving
and line-wrap checks, and reading each paper for factor evidence.

**Not performed here**, for three reasons, stated plainly rather than worked around:

1. **It requires downloading eleven third-party PDFs into the working tree.** That
   is an action I do not take on my own initiative; it needs the author's explicit
   go-ahead, and the item itself constrains it (*"do not commit paywalled artifacts
   to the repo, only fetch manifests with SHA-256"*). Two candidates' licensing
   (CMBBE/T&F, Wiley) is unverified and may not permit local processing at all.
2. **Two candidates are unidentifiable** (§4), so the screen could not be complete
   in any case.
3. **The admission it feeds is blocked anyway** on the author's committed inclusion
   rule, and §2 shows the rule choice changes which papers even belong in the screen.

**What unblocks it — a 3-4 hour session, in this order:**

| Step | Needs |
|---|---|
| a | Author supplies DOIs for the two unidentified candidates |
| b | Author commits the inclusion rule (per-factor table, or prose evidence per factor) — this is A10's gate and it determines whether the five Frontiers papers are in or out |
| c | Author authorises the fetch; open-access candidates (Frontiers ×5, PLoS ONE, likely Pathmanathan) can be fetched with a manifest + SHA-256 per the existing corpus discipline in `tests/fixtures/extract_corpus_real/MANIFEST.json`. Paywalled ones (CMBBE, Wiley) need an institutional-access decision |
| d | Run the reader + pathology screen. **The tooling exists**: `src/uofa_cli/readers/pdf_reader.py` and `dev/tools/scripts/corpus_profile.py`. Hard-fail threshold per survey precedent: ~10% unusable, ~0.1% clean |
| e | Factor-evidence inventory on the survivors |

## 6. Escalation

The criterion is *"fewer than 5 candidates survive the screen."* Formally it cannot
be evaluated until §5 runs. Substantively, **the author should plan for it now:**

- 5 of 11 already fail the stricter criterion;
- 2 of 11 cannot be identified;
- 2 of 11 have unverified licensing;
- 1 (Ahn & de Weck) is systems engineering, not CM&S, and is wanted for a different
  pool;
- the same survey concludes the published population of extractable per-factor
  assessments is *genuinely thin* ([survey:243-254](docs/real-corpus-supply-survey.md)).

Best case under a prose-evidence rule: perhaps 6-8 survive. Under a table rule:
likely 1-2. A10's 11-14 target is not reachable under the table rule from this
candidate list.

**The measured-ceiling disclosure path is the likely outcome, and that is a
respectable finding, not a failure.** The survey establishes it with evidence: the
corpus is thin because the literature is thin, and that was measured in under an
hour rather than assumed. A10 can report a smaller pool with the supply constraint
documented — which is more defensible than padding the pool with papers that carry
no factor evidence.

## Coverage statement

**Searched.** `docs/real-corpus-supply-survey.md` read in full (264 lines), with
the D3 Frontiers section, the V&V 40 pool table, the pathology table and the Bologna
section read line by line. `tests/fixtures/extract_corpus_real/MANIFEST.json` (8
entries, enumerated) as the model for the fetch-manifest discipline.
`tests/fixtures/extract_corpus_vv40/` (4 bundles) to establish what is already
admitted. Repo-wide case-insensitive grep for `spacenet|delphi|de weck|deweck`
(**no real material in repo**), `bologna|aldieri` (10 files, 4 studies).
Located the screening tooling by capability rather than by name: greps for
`alpha_token`, `run_together`, `long_token` → `src/uofa_cli/readers/pdf_reader.py`,
`dev/tools/scripts/corpus_profile.py`.

**Search terms derived from the item's own criteria** (access/licensing;
extraction pathology; factor evidence; DOI lineage): `MANIFEST`, `sha256`,
`PUBLIC_USE_PERMITTED`, `provenance`, `doi:`, `published_rationale`,
`expected_factors`.

**NOT searched / NOT DONE — this item is materially incomplete.**
- **No PDF was fetched. No pathology screen was run. No factor-evidence inventory
  was produced.** §5 states why and what unblocks it. Every "not run" cell in §4 is
  literal.
- **Ahn & de Weck step 4 (scorecard-pool flag) is unanswered.** It is the one
  candidate serving two pools and it was not examined at all.
- Licensing was assessed from publisher identity (Frontiers = CC BY, PLoS = CC BY),
  **not** from each article's own licence statement. Verify per article before
  fetching.
- The five Frontiers verdicts are **quoted from the survey, not independently
  re-derived**. Two carry direct quotations from the papers; three are recorded as
  "no" without a quotation. If A10's disclosure will cite these rejections, the
  three unquoted ones should be spot-checked.
- The prior screen is dated 2026-08-06 and the papers are from 2021 — no
  version-drift risk, but no re-check was performed either.
