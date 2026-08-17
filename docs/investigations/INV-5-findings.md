# INV-5 — External accepted-case source for A3's external negative

Status: **ESCALATED** — the dual-use conflict is now a **three-way** conflict, named
by the parent spec itself
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A3, B3, A10

---

# ADDENDUM — re-investigated against parent spec v2.0

## v2.0 makes the contention explicit, and adds a third claimant

The original escalation was framed as dual use: Bologna wanted both as A3's
external negative and as the survey's "next routing bundle." v2.0 §A10 promotes
that from a survey recommendation to a spec assignment:

> **Scorecard pool** (per-factor table transcribable): ~5 documents, near the
> published population; **Bologna (Aldieri 2023) is the next bundle.** No expansion
> expected.

So the three standing claims on one document are now:

| Claimant | Basis |
|---|---|
| **A3** external negative (this finding's recommendation) | only candidate clearing access + extraction + factor-evidence |
| **A10 scorecard pool** | v2.0 §A10 names it as the next bundle |
| **H2 evaluation corpus** (already realised) | one of the six annotated documents in `studies/real-document-rescore/FINDINGS.md`; also the substrate for `studies/published-rationale-ceiling` and `studies/attribution-agreement` |

The third is not a plan but a fact: Bologna is already load-bearing in the H2
chain. The contamination question in §5 therefore stands unchanged and is, if
anything, harder — A3's "external" negative would be a document the H2 arm already
measures on.

## One relief route that v2.0 supplies

§A10 clause 2 directs that **Ahn & de Weck (SpaceNet Delphi) be screened for the
scorecard pool too**, noting *"it carries a filled CAS of a named platform and sits
outside NTRS."* If that screen succeeds, Ahn & de Weck can take the scorecard-pool
slot and free Bologna for A3 — removing one of the three claims without any new
sourcing.

**That makes Ahn & de Weck the highest-value single fetch across INV-5 and INV-13
combined**, and it should be the first item in INV-13's screening session. It is
also the only candidate on either list that could resolve a conflict rather than
just add a row.

## What v2.0 adds to A3 itself

Two clauses that bear on the encoding, not the sourcing:

1. **§A3 clause 1** now specifies the clean-case corpus as *"a defect-free package
   variant per case study (injected defects removed, **known weakeners dispositioned
   per the published record**)."* That dispositioning step is a JUDGMENT-class input
   by INV-1's test — the encoder decides what the published record disposes of. It
   does not weaken A3 (the clean arm measures false positives, not ground-truth
   labels), but A3's Ch3 subsection should say the dispositions are author-applied
   under A7 rather than let "defect-free" read as observed.
2. **§A3 clause 3** requires the FP table *"per pattern per label class"*, which is
   what GATE-H3's "<10% false positives, per class" is measured from. The committed
   v0.5.15.1 holdout supports this today: 9 MECHANICAL-class and 1 JUDGMENT-class
   rule-firings over the 171-package holdout (see INV-8 addendum). **A3's FP half is
   in far better shape than its recall counterpart** — worth knowing before
   budgeting A3's 5-6h.

## §3's open question is unchanged and still the gate

Whether Bologna's record shows achieved ≥ required across factors, or documents a
justified shortfall, still requires the PDF — about an hour. v2.0 does not answer
it. It remains the single action that would let this item close.

## Coverage statement (addendum)

**Searched.** v2.0 §A3 clauses 1-3, §A10 (both pools, all four clauses), §B3,
§0.1 GATE-H3's FP clause. Cross-checked against the six annotated documents
identified for INV-13's addendum. The committed v0.5.15.1 holdout `summary.csv` was
re-aggregated by label class for the FP figure.

**NOT verified — unchanged.** The Bologna PDF was not opened; Ahn & de Weck was not
fetched or screened.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Recommendation

**Bologna (Aldieri et al. 2023, `doi:10.1016/j.cmpb.2023.107727`), with one
qualification that must be settled before encoding.**

It is the only candidate that clears the access, extraction-quality and
factor-evidence bars, and it is **already sourced in this repo** — so the "external
negative" costs an encoding pass, not a sourcing hunt.

The qualification: A3's criterion is *"a document whose encoding should fire zero
critical weakeners because the record shows the evidence was adequate."* Bologna
publishes achieved credibility **per factor** (Medium/High) but **no overall
accept/reject decision record** was found in the repo's transcription. Whether it
satisfies A3's criterion therefore turns on a reading of the paper that this
investigation could not complete from the repo alone. See §3 — this is a
one-hour check on the PDF, not a re-survey.

## 1. In-repo supply (item step 1)

| Source | Result |
|---|---|
| `tests/fixtures/extract_corpus_real/MANIFEST.json` | 8 entries, **all NTRS / NASA-7009**: two IMM, two ARED-family, four whole-body/musculoskeletal FE. Two (`20240000233`, `20240011014`) are already-excluded alternate versions. **None is a CM&S submission with a published acceptance outcome**; they are internal NASA credibility assessments. |
| `tests/fixtures/extract_corpus_vv40/` | **4 real V&V 40 bundles**: `bundle_morrison`, `bundle_nagaraja`, `bundle_tavi1_s3`, **`bundle_bologna_bcthip`** |
| Case-study anchors (excluded by A3) | Morrison, Nagaraja, NASA HPT |
| **Remaining after exclusions** | **`bundle_bologna_bcthip`** and `bundle_tavi1_s3` |

`bundle_bologna_bcthip` is real, tier 1, journal-article, transcribed at published
sub-factor granularity, and carries **23 `published_rationale` strings written by
the paper's own authors**
([tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/metadata.json](tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/metadata.json);
rationale count from [studies/published-rationale-ceiling/FINDINGS.md:5-7](studies/published-rationale-ceiling/FINDINGS.md)).

## 2. Candidate screen against A3's criterion

The item is explicit that A3's criterion differs from both survey pools: not "does
it extract cleanly", not "does it have a per-factor table", but **"does the record
show the evidence was adequate, such that a faithful encoding fires zero critical
weakeners."** Screened on that:

| Candidate | Access | Extraction | Per-factor evidence | Adequacy shown? | Verdict |
|---|---|---|---|---|---|
| **Bologna** (Aldieri 2023) | CC BY-NC-ND, **already sourced** | **0.06%** >20-char alpha tokens — clean ([survey:132](docs/real-corpus-supply-survey.md)) | **Yes** — Table 1 gives available range, selected rigour, achieved credibility, and a written rationale per factor ([survey:162-170](docs/real-corpus-supply-survey.md)) | **Partly** — see §3 | **RECOMMENDED, pending §3** |
| TAVI I / II (Catalano, Scuoppo 2025) | commercial journal | **10.36% / 11.25% — unusable**, word spacing destroyed on extraction ([survey:128-140](docs/real-corpus-supply-survey.md)) | **No** per-factor table; Part I states an applicability assessment *"was, however, not carried out in this study"* | **No — the paper documents an incomplete package** | **REJECT.** Also the exemplar of why "has a per-factor process" ≠ "documents an adequate package". |
| Frontiers collection (7 papers) | open access | unscreened for pathology | **0 of 7 publish a per-factor credibility assessment** ([survey:209-241](docs/real-corpus-supply-survey.md)); two say so outright | **No** — two state the assessment was out of scope | **REJECT for A3** |
| NTRS corpus (8 manifest entries) | PUBLIC_USE_PERMITTED | 2 of 4 usable prose; ARED is a poster, IMM a 43-words-per-slide deck | 7009 CAS, not V&V 40 | Internal assessments, **no external acceptance outcome** | **REJECT** — wrong artifact class for "accepted CM&S submission" |
| SpaceNet Delphi (Ahn & de Weck) | not in repo | unknown | unknown | unknown | **NOT SCREENED** — see coverage statement |
| "accepted arms of a tiered case already encoded" | in repo | n/a | n/a | n/a | **NONE EXIST.** The tiered cases are Morrison and Nagaraja, both excluded as anchors. Reported as a negative finding, not skipped. |

## 3. The one open question on Bologna

`bundle_bologna_bcthip/ground_truth.json` has keys
`case, pack, standard, published_granularity, _provenance, expected_factors`.
**There is no decision or outcome field**, and none of the four V&V 40 bundles
carries one — the extract-eval corpus tracks factor extraction, not decision
records.

That matters because A3's negative control needs the encoding to fire **zero
critical weakeners**, and three of the six patterns that can fire Critical are
decision- or structure-dependent:

| Critical pattern | Fires on Bologna? |
|---|---|
| W-ON-01 (no COU) | **No** — the paper states CoU and QoI explicitly ([survey:159-161](docs/real-corpus-supply-survey.md)) |
| W-EP-01 (orphan claim) | encoding-dependent |
| W-AR-01 (required level, no acceptance criteria) | **Likely No** — Table 1 prints selected rigour *and* a written rationale per factor, which is what acceptance criteria encode to |
| W-AR-02 (achieved < required with an Accepted outcome and no offset) | **Cannot be determined without the decision record.** This is the pattern the whole question turns on. |
| W-PROV-01 (provenance chain incomplete) | encoding-dependent |
| COMPOUND-01/03 | derived |

**The check:** does the paper record an overall credibility verdict, and does any
factor's achieved level fall below its required level? Bologna's Table 1 prints
*achieved* credibility (Medium/High) against an *available range*, which is not
obviously the same as V&V 40's required-vs-achieved pairing. If achieved ≥ required
everywhere, or if there is no "Accepted" decision record to encode, W-AR-02 cannot
fire and Bologna is a clean negative control. If some factor falls short and the
authors accept anyway with a documented justification, then Bologna is **still**
usable — the justification encodes as an `OffsetRationale` and W-AR-02 stays quiet,
exactly as it does for Nagaraja ([rules:233-241](packs/core/rules/uofa_weakener.rules)).
Either way it is likely fine; it should be *checked* rather than assumed, because
assuming is the failure mode A3 exists to guard against.

**Effort: ~1h with the PDF open.** Not done here — see coverage statement.

## 4. Reader-pathology screen (item step 4)

Bologna was screened by the survey using the same `>20-char alpha token` test:
**0.06%**, against a known-good baseline of 0.01-0.08% and an unusable threshold
around 10% ([docs/real-corpus-supply-survey.md:126-140](docs/real-corpus-supply-survey.md)).
It is the cleanest real document in the survey. **No new candidate was introduced
that requires a fresh screen** — which is the point: the recommendation is a
document already through the pipeline.

## 5. Escalation — dual use

The item's escalation criterion: *"the best candidate is Bologna and it is also
wanted as the next routing bundle (dual use may be fine but is an author call on
contamination)."* **Triggered exactly as anticipated, and the situation is one step
further along than the item assumed.**

The survey recommends: *"**Bologna becomes the next bundle, and the first V&V 40
one.**"* ([survey:188-190](docs/real-corpus-supply-survey.md)). But Bologna is
**already** a bundle (`bundle_bologna_bcthip`) and is already load-bearing in at
least three committed studies:

- `studies/published-rationale-ceiling/FINDINGS.md` — its 23 author-written
  rationales are the substrate for the anchor-dictionary negative result
- `studies/real-document-rescore/FINDINGS.md` — bologna is one of the six annotated
  papers (`| bologna | vv40 | 0/13 | 895 |`)
- `studies/attribution-agreement/PREREGISTRATION.md`, `studies/model-selection/FINDINGS.md`

**The contamination question is therefore sharper than "dual use."** Using Bologna
as A3's external negative means the same document is simultaneously:
1. an extraction-evaluation document (H2 chain), and
2. a detection negative control (H3 chain).

Two readings, for the author:

- *Fine.* The two uses exercise different legs — H2 measures whether extraction
  recovers factors; A3 measures whether the rule engine stays quiet on an adequate
  package. Neither tunes against the other, and A3's encoding would be authored from
  the paper, not from the extraction output.
- *Not fine.* Bologna's factor structure is by now well known to the author from
  three studies, so an encoding produced by that author is not "external" in the
  sense the negative control claims. A reviewer could argue the clean result was
  authored rather than observed.

**If the second reading wins, A3 has no external negative available**, because §2
shows the pool is otherwise empty. That would activate a disclosure path rather
than a search: state that the external negative is drawn from a document already in
the evaluation corpus, and say why.

## 6. If Bologna is ruled out

Ranked fallbacks, all weaker:

1. **SpaceNet Delphi (Ahn & de Weck)** — unscreened, out-of-domain (systems
   engineering, not CM&S), and wanted for A10's scorecard pool anyway. See INV-13.
2. **Relax the criterion** as the survey itself recommends
   ([survey:250-254](docs/real-corpus-supply-survey.md)): a document stating model
   risk without a per-factor table still exercises part of the assessment. Three
   Frontiers papers qualify at that level. **But a document without a per-factor
   assessment cannot demonstrate "zero critical weakeners because the evidence was
   adequate"** — it demonstrates zero weakeners because there is nothing to assess.
   That is a false negative control and would be worse than none.
3. **Declare the absence.** The survey's own conclusion is that *"the five in the
   corpus may be close to the population of published, extractable, per-factor V&V 40
   and NASA CAS assessments as of 2026."* A3 can report the external negative as
   attempted-and-unavailable with this survey as evidence. That is a defensible
   disclosure and it is cheaper than a bad control.

## Coverage statement

**Searched.** `tests/fixtures/extract_corpus_real/MANIFEST.json` — all 8 entries
enumerated with titles via `json.load`. `tests/fixtures/extract_corpus_vv40/` — all
4 bundles listed; `bundle_bologna_bcthip/metadata.json` and the key structure of its
`ground_truth.json` read. `docs/real-corpus-supply-survey.md` read in full from
line 1 to 264 (headings, the V&V 40 pool table, the three-paper assessment, the
pathology table, the Bologna section, the D3 Frontiers screen, sources).
Repo-wide case-insensitive grep for `bologna|aldieri` (10 files) and
`spacenet|delphi|de weck|deweck` (2 hits, both inside a generated adversarial
package — i.e. **no real SpaceNet material in the repo**). Read
`studies/published-rationale-ceiling/FINDINGS.md:1-35` and grepped
`studies/real-document-rescore/FINDINGS.md` for the six-paper roster.

**Search terms derived from A3's criterion itself** (a published submission whose
record shows the evidence was adequate): `accepted`, `acceptance`, `outcome`,
`decision`, `published_rationale`, `achieved`, `required` — rather than reusing the
survey's "per-factor table" screen, which answers a different question. That
distinction is what surfaced the TAVI finding in §2 (a paper can follow the V&V 40
process and still document an inadequate package) and the §3 gap.

**NOT searched / not verified.**
- **The Bologna PDF was not opened.** §3's question — does the paper record an
  overall decision, and does any factor fall short of its required level — is the
  one thing that would settle the recommendation, and it requires the source. The
  source is not in the repo (only the transcribed ground truth is). **This is the
  single open action for INV-5.**
- **Ahn & de Weck was not fetched or screened** (see INV-13, where it is also a
  candidate). Ranked as a fallback on genre grounds alone.
- No new candidate search was run against publisher databases; this investigation
  worked the in-repo supply plus the survey's already-screened pools, per the item's
  step order. If the author wants a fresh external search, that is a separate pass
  and the survey's own conclusion suggests a low yield.
- No encoding was attempted, so "should fire zero critical weakeners" is reasoned
  from the rule bodies (INV-1) rather than measured.
