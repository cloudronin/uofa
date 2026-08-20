# What the extractor returned, and what was wrong with it

State: DRAFT. Spec §2, and the evidence behind the §2c and §3b findings.

Measured against `raw-extract/johnson-extracted-RAW.xlsx`, committed before any
review-pass edit. Every claim here is checkable against that file.

Run: `anthropic/claude-sonnet-5`, thinking off, 16 860-token corpus, 2m24s,
142 pre-filled cells, 19 factors mapped, 1 green / 141 yellow.

---

## 1. The finding: the required-level column is synthesized, not read

**Required Level equals Achieved Level on 17 of 17 factors that carry both.**
Not approximately, not mostly. Every one.

That is not the extractor guessing badly. It is the extract prompt doing exactly
what it says: `packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt` reads

> **Default rule**: For each factor, set `required_level = achieved_level`. A
> factor that was assessed at Level N is assumed to meet its required level at N
> *unless* the narrative explicitly calls out a gap.

and then lists the phrases that would override it — "Achieved Level X against
Required Level Y", "L1 of required L3", "gap", "carried as condition". Johnson's
paper contains none of those phrases, because Johnson does not write his required
levels in prose at all. He shades them into Table 3.

So the rule fires on every factor, and the package acquires a complete,
schema-valid, plausible required-level column that came from nowhere.

### What that erases

Johnson's Table 3 (recovered geometrically, see `TABLE3_RECOVERY.md`) against the
achieved levels he states on p.25:

| 7009A factor | Predeclared | Achieved | |
|---|---|---|---|
| Data Pedigree | 3 | 3 | met |
| **Verification** | **3** | **4** | **exceeded** |
| Validation | 1 | 1 | met |
| Input Pedigree | 3 | 3 | met |
| Uncertainty Characterization | 4 | 4 | met |
| Results Robustness | 4 | 4 | met |
| M&S History | 3 | 3 | met |
| **M&S Process / Product Management** | **2** | **4** | **exceeded by two** |

Two of eight factors exceed their requirement. That is the paper's own headline:
its p.9 radar plot is titled **"Credibility Meets or Exceeds Requirements"**, and
the *exceeds* half is the part the plot exists to show.

After extraction, every factor reads "met exactly". Both exceedances are gone, and
nothing downstream can tell. `uofa check` verifies a field is present, not that it
is right; a synthesized required level validates exactly as well as a read one.

### The one factor where this is checkable as a plain error

`Development process and product management` maps 1:1 onto Johnson's
`M&S Process / Product Management`, same 0-4 scale, no fan-out, no judgment call.

    extractor:  required 4, achieved 4
    source:     predeclared 2 (Table 3), achieved 4 (p.25)

Wrong by two levels, in the direction that makes the assessment look less
impressive than it was. This is the §3b case in its purest form: a cell that is
confidently populated, internally consistent, schema-valid, and false.

## 2. The fan-out moves the validation claim upward

Johnson rates **Validation = 1** — the bottom of the scale — and says why:
"No validation runs planned. RWS data not available" (p.25); "Validation directly
to RWS or known standards not possible" (p.19); "Validation will not be performed"
(p.6). It was waived, and the waiver is the paper's most conservative disclosure.

The pack has no factor carrying 7009A's Validation column. The evidence
distributes across the V&V 40 validation family, and the extractor scored it:

| V&V 40 factor | Extractor level |
|---|---|
| Model form | 3 |
| Model inputs | 3 |
| Test samples | 3 |
| Test conditions | 3 |
| Equivalency of input parameters | 3 |
| Output comparison | 4 |

**These are not obviously wrong.** V&V 40 asks narrower questions — was the
comparator experiment well run, were the instruments calibrated, did outputs get
compared quantitatively — and Johnson's DOE genuinely answers them well. 7009A's
Validation column asks one broader question, whether M&S outputs agree with data
from the *real world system*, and the answer there is nothing at all.

Both readings are defensible. That is what makes this the finding rather than a
bug: **the two frameworks disagree about what the same evidence is worth, and the
encoding silently adopts the more generous one.** A reader of the resulting
package sees a validation family at 3 and 4 with no trace anywhere that the source
rated its own validation at 1 and said so three times.

The same shape, less sharply, on Verification: one 7009A factor at 4 becomes
`Software quality assurance` 4, `Numerical code verification` 4, `Use error` 3,
with `Discretization error` not-assessed and `Numerical solver error` scoped-out.

## 3. Everything else the review pass has to fix

| Cell | Extractor | Source | Class |
|---|---|---|---|
| `Standards Reference` | `NASA-STD-7009B` | the paper applies **7009A** (p.1, throughout) | **Wrong.** Predicted as A-10 before the run. Entering the natural string would also have tripped `resolve_criteria_set("NASA-STD-7009") -> …/NASA-STD-7009B` |
| `Model Risk Level` | `MRL 3` | no MRL anywhere; V&V 40 construct absent from a 7009A paper | Invented (A-12) |
| `Assurance Level` | `Medium` | not stated | Invented (A-13) |
| `Device Class` | `N/A` | not applicable; also not a member of the controlled list | Invalid value (A-14) |
| `Assessment Date` | `Date of this assessment (YYYY-MM-DD)` | — | **Template placeholder left in a data row** |
| `Model & Data` E3/F3 | `Version number (optional)`, `Where this came from (optional)` | — | Same |
| `Validation Results` C3/G3/H3 | `Stable URI or local ID`, `If Yes, describe the method`, `Quantitative result if applicable` | — | Same |
| `Decision Date` | `2019-10-14` | that is the **model release** date (p.20, "Final version released dated 10/14/2019") | Repurposed, not stated |
| `Decided By` | `Investigation team / Technical Authority` | the TA approved the **validation waiver** (p.8), not an acceptance of the model | Promoted a waiver approval into a credibility decision |
| `Decision Outcome` | `Accepted` | partially supported: "Model acceptance requirements set by the Project were met" (p.19) | Defensible with an anchor, but see below |
| `Development technical review` | required 3, achieved 3 | Johnson has review *content* ([M&S 36], p.10 and p.24) but never rates this as a factor — it does not exist in 7009A | Level invented from content (A-09) |
| `Input pedigree` | absent | predeclared 3, achieved 3, with rationale (p.25) | **Not the extractor's fault — the pack has no such factor** (A-07) |

The placeholder leaks are their own small finding: `write_extraction` clears the
template's hint text only where it writes a value, so any field the model skipped
keeps its instruction string and arrives at import looking like data.

### On the decision record

The paper states that acceptance requirements were met (p.19) and offers the
results "with the credibility level required for use of the results in the
investigation's risk model" (p.10). It records no decision *act*: no decider, no
date, and a `(Signed)` line with nothing after it.

"Requirements were met" is not "a stakeholder accepted". The DRAFT keeps
`Accepted` because p.19 anchors it and `hasDecisionRecord` is required at
`minCount 1` for the Complete profile, but marks it JUDGMENT-CLASS and blanks
`Decided By` and `Decision Date` rather than inheriting the extractor's answers.

## 4. What the extractor did well, stated because a finding is not a verdict

Worth recording precisely, so the memo does not read as an indictment of the tool:

- The prose fields are good. The COU description, the RWS framing, the entity
  descriptions and the factor rationales are accurate, specific, and anchored in
  the document rather than generic.
- It correctly declined two factors nothing in the source supports:
  `Discretization error` → `not-assessed` ("no spatial/temporal discretization
  scheme"), `Numerical solver error` → `scoped-out` (Johnson's p.18 solution
  verification answer is "No. Not required").
- It found the 0.0084 cm residual, the 99%/95% tolerance bound of 0.128 cm, and
  the 0.16 cm critical depth, and put them in the right cells.
- Its own confidence was honest: 141 of 142 cells came back yellow, not green.
  The tool said "review this". The problem is not that it was overconfident; it is
  that reviewing a synthesized required-level column requires knowing that Table 3
  exists and is shaded, which no amount of reading the extractor's output reveals.

**The rule this hands §3b:** a cell is not reviewed by being read back against the
extractor's own rationale, because a synthesized value comes with a plausible
rationale attached. It is reviewed only against the source location that should
carry it — and where the source carries it in a form the extractor cannot read,
the reviewer has to know to go looking.
