# A10 admission arithmetic, and two screens

Date: 2026-08-16
Session: 2
Feeds: A10 (admissions), A3 (external negative), A9 (disclosure), rulings 6, 7, 8
Status: **two author decisions surfaced, neither ruled here**

Ruling 6 bound N=3 and unblocked admissions, so this is the first pass at applying
the committed rule. Two things came up before any candidate was read, and both are
arithmetic or scope rather than screening judgment.

---

## 1. Ruling 8 and ruling 7 cannot both hold as written

INV-13 established the roster of the six currently annotated documents and the
consequences of ruling 7's exclusions:

| # | Document | Pack | Factors | Admissible under A10's exclusions |
|---|---|---|---|---|
| 1 | opensim | nasa-7009b | 7 | yes |
| 2 | elemance | nasa-7009b | 6 | yes |
| 3 | ared | nasa-7009b | 7 | yes |
| 4 | **bologna** | vv40 | **13** | yes — **contested** |
| 5 | nagaraja | vv40 | 12 | no — named exclusion |
| 6 | morrison | vv40 | 11 | no — named exclusion |

Ruling 7 reclassifies morrison and nagaraja as development documents, giving a
**held-out base of 4** — which is the figure the Decision Record records. That 4
**includes Bologna**.

**Ruling 8 then assigns Bologna to A3 as the external negative.** If that removes it
from the annotation pool, the base is **3**, and the target does not merely tighten,
it closes:

| | base 4 (Bologna stays) | base 3 (Bologna to A3) |
|---|---|---|
| Admissions needed for 11 | 7 | **8** |
| Screenable candidates available | 7 | 7 |
| Maximum reachable total | 11 | **10** |
| Is the 11–14 target reachable? | only if **all 7** qualify | **no** |

At base 3 the stated target is arithmetically unreachable regardless of how the
screens go, and ruling 7's second branch — *"or the measured ceiling disclosed with
screen results"* — becomes the only available outcome. That is a perfectly
respectable result and the spec already provides for it. It should be **chosen**,
though, not discovered at the end of the annotation work.

**RULED 2026-08-16: base of 4, Bologna serves both.** Morrison and Nagaraja stay
development-tier; the held-out base remains **4** including Bologna, which also serves
as A3's external negative. The two uses measure different things — A3 measures
false-positive rate on a clean *encoding* (H3), A10 measures extraction attribution on
*prose* (H2) — so double duty is sound on the measurement. If admissions cannot reach
11 total, **disclose the measured ceiling with the screen results** per ruling 7's
standing branch.

Consequence, restated so the screening work knows what it is for: the target is
reachable but only if **all 7** screenable candidates qualify. That is a coincidence
rather than a plan, so the measured-ceiling branch is the likely outcome and is not a
failure — it is the reportable result. Screen honestly against N=3 and let the count
land where it lands.

## 2. "External negative" overstates Bologna's independence

Independent of the arithmetic, and true whichever way (1) is ruled.

A3 specifies the external negative as *"one additional published, accepted
submission encoded straight from source, no injection."* The force of the test comes
from the word **external**: an accepted submission the engine has not been tuned
against, run clean, to see whether it fires.

Bologna is the most internally-worked real document in the project after the two
case studies:

- `tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/` — a committed bundle
  with hand-authored `ground_truth.json`, dated 2026-08-06.
- `docs/v1/annot_bologna.json` — hand annotation at **revision 2**, whose own header
  records that revision 1 was corrected because *"D1 found the first version drew
  every span from Table 1"*, with a selection rule fixed in advance *"because the
  annotator is the same one whose bias is being corrected."*
- `docs/v1/valresults_bologna.json` — a hand-built gold set for K9.
- INV-13 records it as used in **at least four committed studies**.
- It is the richest of the six at **13 annotated factors**.

None of that invalidates using it for A3 — the encoding would be new, and the FP
measurement is genuinely a different measurement from anything above. But a reader
who is told "external negative" will assume a document the project had not already
hand-annotated twice and corrected for annotator bias. **Report it as what it is:**
a published, accepted, independently-authored submission that the project has prior
annotation history with, encoded fresh for this run. The FP result stands on that
description; it does not need the stronger word, and the stronger word is the kind
of thing A4 exists to catch before a committee does.

If a genuinely untouched external negative is wanted, it has to come from the
screenable candidate list — which competes directly with the admissions the pool
needs in (1).

## 3. Ahn & de Weck: identified, not yet readable, and the screen may not need the full text

Ruling 8 makes this screen the gate on the scorecard pool's outcome (Bologna goes to
A3 either way, so nothing else waits on it).

**Bibliographic identification, complete.** Ahn, de Weck & Steele, *"Credibility
Assessment of Models and Simulations Based on NASA's Models and Simulation Standard
Using the Delphi Method,"* **Systems Engineering**, 2014. `doi:10.1002/sys.21266`.
Ten panel members assessed the SpaceNet M&S platform over a two-round Delphi against
NASA-STD-7009's eight credibility factors; SpaceNet v1.3's overall credibility landed
**between the development and production levels**, with second-round variance
significantly reduced.

**Full text is paywalled** (Wiley / INCOSE). No local copy; not in the repo, Downloads,
or the Praxis tree. Reading it needs the library proxy — the same route U-INV-1 is
queued for.

**But the screening question is already visible from the abstract, and it is a
category question rather than a content one.** The scorecard pool admits documents
whose **per-factor credibility table is transcribable** — Bologna qualifies because
its authors print their own required-vs-achieved levels. Ahn's levels are
**elicited from a ten-person expert panel**, not declared by the model's developers.
That is a third-party opinion survey *about* a model's credibility, not a credibility
argument *made by* the people who built it.

Admitting it would put panel-consensus judgments into a pool otherwise holding
developer-declared assessments, and the H2 measurement would then be attributing
extraction over two different kinds of object. My reading is that this **disqualifies
it from the scorecard pool** on the pool's own criterion, and that the full text will
confirm rather than change that — a Delphi paper will certainly contain a per-factor
table, which is exactly why the criterion has to be read as *whose* levels these are,
not *whether a table exists*.

The **annotation pool** is a separate and more permissive question: N=3 prose evidence
across credibility factors. A paper discussing eight factors across two survey rounds
will clear N=3 on word count alone. Whether it *should* clear is the same category
question — its prose evidences an assessment procedure, not the model's own V&V
evidence.

**Recommendation, pending the read:** screen it out of the scorecard pool on the
developer-declared criterion, and take ruling 8's stated fallback — the scorecard pool
takes the measured-scarcity disclosure. That is the branch ruling 8 already provides
for, so nothing is blocked. Confirm against the full text when the proxy route is run
for U-INV-1, and record the confirmation either way.

---

## What is not done here

No candidate has been admitted. The N=3 rule is committed and the seven screenable
candidates are ready to screen, but the base-count question in §1 changes what the
screening is *for* — chasing an unreachable 11, or documenting a measured ceiling —
and that is worth one line from the author before the reading time is spent.
