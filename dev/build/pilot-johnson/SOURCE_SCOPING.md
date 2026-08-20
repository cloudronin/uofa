# Source scoping — Johnson (2020), NTRS 20200002832

State: DRAFT. Spec §1, done before any extraction.

Source: Johnson, K.L., "Applying NASA-STD-7009 Standard for Models and Simulations
to Surrogate and Other Statistical Models," NASA Engineering and Safety Center,
Marshall Space Flight Center. NTRS 20200002832. 28 pages.
In tree at `source/NTRS-20200002832-Johnson-2020.pdf`, sha256 `1b767b2d4128dcc6…`.

Page numbers throughout are **PDF page numbers** (the document carries no printed
folios). Anchors are given as `p.N` plus the section, table or requirement tag.

## 1. The context of use

One COU, stated as the paper states it:

> "Model predictions to be used in probabilistic risk analysis (PRA) to estimate
> risk of loss of aircraft and pilot due to tire puncture." — p.14, LCW
> [M&S 8](2), M&S intended use

The decision the COU serves, in the paper's words: whether "the current ground hold
on the aircraft should be continued" (p.5). The RWS question is "the probability
that a worst-case particle at worst-case relative velocity to the tire will
penetrate the tire", worst case being "radial impact of 0.2 gram steel chip at
velocity of 1000 kph at 50°C" (p.14).

The model does not make the risk decision. It supplies one input to a PRA that
does — "The problem statement will be more directly answered through PRA using this
model as an input" (p.22). The COU is therefore *model output as PRA input*, and
that framing is what the credibility assessment attaches to.

## 2. The M&S artifact

Multiple linear regression of penetration depth on FOD particle velocity and
orientation, with a velocity × orientation interaction term (p.15, [M&S 12]).
Fitted in "a well-verified commercial statistics package" (p.16) — Statgraphics is
named once, for the radar plot (p.10).

Delivered as an Excel calculator: "Final version released dated 10/14/2019 on
password-protected Excel calculator. This was the version used to produce
predictions for PRA use" (p.20). The calculator "requires — and allows — only
inputs for orientation and velocity" (p.20) and carries "built-in warnings when
inputs exceed domain of test parameters" (p.20).

Headline result: "Expected worst-case impact depth 0.098 cm; 99% reliability/ 95%
confidence tolerance bound 0.128 cm" against a critical depth of 0.16 cm (p.22,
p.14). Residual standard deviation 0.0084 cm (p.9, p.22).

The paper's own credibility assessment covers this artifact and no other.

## 3. Admissible evidence inventory

Everything in the paper that carries evidentiary weight for the encoding, with its
anchor, listed before extraction begins. Anything not on this list is background,
argument about the Standard, or the author's teaching commentary, and is not
encoded as evidence about the model.

| # | Element | Anchor | Weight |
|---|---|---|---|
| E1 | Predeclared credibility levels | p.7, Table 3, **green shading only** | The required-level column. No text. See `TABLE3_RECOVERY.md` |
| E2 | Predeclaration narrative (what was waived and why) | p.6, "PREDECLARATIONS" | States the verification waiver and that validation will not be performed |
| E3 | M&S History predeclaration rationale | p.7 bottom – p.8 top | The negotiated-level case; spec §3.3 hard case |
| E4 | Achieved credibility levels, all eight, with rationales | p.25, "THE FINAL CREDIBILITY ASSESSMENT" | The achieved-level column |
| E5 | Reporting responses [M&S 32] – [M&S 39] | pp.8–10 | Caveats, uncertainty, review findings, risk |
| E6 | Radar plot, Required vs Achieved | p.9 (figure), described p.10 | Corroborates E1 against E4; no readable values of its own |
| E7 | LCW responses, M&S Planning | pp.11–13 | Criticality, life-cycle plan, best practices, technical reviews, training |
| E8 | LCW responses, M&S Development | pp.14–20 | RWS, model concept, design, conceptual validation, verification, empirical validation, permissible use, release |
| E9 | LCW responses, M&S Use | pp.20–24 | Use processes, scenarios, results, uncertainty, sensitivities, caveats, people, archiving |
| E10 | Caveats table | p.23 | [M&S 32](1)–(7) in table form; **conflicts with E5, see hazard H3** |
| E11 | People qualifications | p.24, [M&S 37] | **Conflicts with E5, see hazard H3** |

Not admissible as evidence about the model, and deliberately excluded: the paper's
argument for applying 7009A more widely (pp.1–5), the commentary paragraphs that
follow each worksheet block (the author teaching the reader how to fill the form),
the notes on uncertainty distributions as sub-models (p.26), and the summary and
acknowledgments (pp.26–27). These describe the Standard, not the tire model.

### Where the outline's §2 intake prompt is insufficient

Prompt 2a asks what counts as source, framed around one published paper and its
supplementary material. This document needs a distinction the prompt does not
have: **a single paper that is partly evidence about a model and partly a tutorial
about the standard being applied to it.** The same PDF supplies both, interleaved
paragraph by paragraph, and the tutorial paragraphs are written in the same voice
as the evidence. An intake rule that says "the published paper" admits all of it.
Filed as a §2 finding.

## 4. Pre-declared hazard: the 7009A → 7009B vocabulary gap

The paper applies **7009A** and its eight-factor Appendix E credibility scale on a
**0–4** range. The pack encodes **7009B** as 19 factors: 13 from ASME V&V 40 on a
**1–5** range plus 6 NASA-only on **0–4**
(`src/uofa_cli/excel_constants.py`). The mapping is declared non-mechanical here,
before extraction, so that nothing downstream can be mistaken for a silent
resolution.

| Johnson factor (0–4) | Pack home | Mechanical? |
|---|---|---|
| Data pedigree | `Data pedigree` (NASA, 0–4) | yes |
| Results robustness | `Results robustness` (NASA, 0–4) | yes |
| Uncertainty characterization | `Results uncertainty` (NASA, 0–4) | renamed |
| M&S history | `Use history` (NASA, 0–4) | renamed |
| M&S process / product management | `Development process and product management` (NASA, 0–4) | renamed |
| **Verification** | fans across 5 V&V 40 factors, and 0–4 → 1–5 | **no** |
| **Validation** | fans across 6 V&V 40 factors, and 0–4 → 1–5 | **no** |
| **Input pedigree** | **no home in the pack at all** | **no** |
| — | `Development technical review` has no 7009A counterpart | — |

Two of these are spec §6 escalations rather than ambiguity-log entries, because
they are places the pack's vocabulary cannot express what the paper states:

- **`Input pedigree` has no destination.** Johnson predeclares it at 3 and achieves
  3, with a rationale (p.25). The pack has no factor for it. The nearest name,
  `Model inputs`, is a V&V 40 validation factor about whether input data is
  accurate and well characterised, which is a different question from pedigree and
  sits on a different scale.
- **"Level 0" is inexpressible on 13 of 19 factors.** Johnson's Table 3 carries the
  convention "A lower level 0 indicates insufficient evidence to make a
  determination" (p.7). Level 0 exists on the NASA factors (0–4) and does not exist
  on any V&V 40 factor (1–5). A 7009A assessment that used Level 0 on a factor that
  maps to the V&V 40 side could not be encoded at all.

Both go to the findings memo as escalations, INV-20 territory. Neither is worked
around.

**Session ruling for the DRAFT (author-approved 2026-08-20): anchored fan-out
only.** Populate the five near-mechanical NASA-side factors, plus any V&V 40 factor
the worksheet answers *directly in its own terms* — code verification (p.18),
solution verification (p.18), conceptual validation (p.17), empirical validation
(p.19). Everything else stays blank and is listed. No level is invented for a
sub-factor the paper does not separately assess.

## 5. Pre-declared hazard: the disguise

The worked example "is from a real aerospace application highly disguised as a test
of puncture resistance in a multi-ply tire on an experimental aircraft" (p.5).

The encoding records what the paper states, cited to the paper. The disguise is an
admissibility note, not licence to editorialise values. Concretely: the RWS fields
(tire, FOD, inflation system, 0.2 g steel chip at 1000 kph) are encoded as written,
because they are what the credibility assessment was performed against. Whether the
underlying real system resembles them is outside the record and is not guessed at.

One consequence worth stating now: the package's RWS description is faithful to the
paper and *knowingly* not faithful to the world. A reference encoding whose source
declares itself disguised is a case the protocol has not met before, and the honest
handling is disclosure in the encoding rather than a silent asterisk. Filed as a §2
finding.

## 6. Pre-declared hazard H3: the paper contradicts itself

Found during scoping, not during extraction, and recorded here because it changes
what "review the cell against the source" can mean. Three places where the source
answers the same question two ways:

1. **Waivers.** p.8 [M&S 32](7) reads "Validation using RWS or independent data not
   required per investigation team, approved by Technical Authority. No waivers were
   required." That describes a TA-approved waiver and denies one in the same
   response. The caveats table at p.23 answers the same requirement "None."
2. **Verification.** p.6 says "Verification of the analysis code was waived". The
   achieved rationale at p.25 says "Analysis code in widely-used statistical
   software verified independently", and rates the factor 4 against a predeclared 3.
3. **[M&S 37], people qualifications.** p.10 answers "(Will not be covered in this
   report.)" The LCW at p.24 answers it in full, with degrees and years.

These are not encoding ambiguities in the ordinary sense — the source is not
underdetermined, it is over-determined and inconsistent. The protocol outline has
no prompt for this. Filed as the §4 finding the memo leads with.
