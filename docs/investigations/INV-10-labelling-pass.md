# INV-10 residual: the bucket-2 labelling pass, done

Date: 2026-08-16
Ruling: A9 item 2 — label every extraction citation raw vs adjudicated, **and**
synthetic vs real (GATE-H2's second label), adding null columns where A5 requires.
Status: **COMPLETE** for the labelling. Two things reported rather than fixed, below.

## What was applied

Every bucket-2 citation now carries, at first mention in its document, an explicit
**raw / no-adjudication-step** label and an explicit **synthetic / real** corpus label.
Ten files:

| Document | Corpus | Was missing | Now |
|---|---|---|---|
| `docs/metrics-spec-r6-u8.md` | synthetic, 30+20 | both labels | provenance note above the table |
| `docs/extract_eval_v1.md` | synthetic, 30+20 | both labels | boxed note under **Headline** — see below |
| `README.md` §"With a model" | **real**, 5 papers | raw label | clause + what the confirm step would change |
| `docs/credibility-inspector.md` | synthetic, 30+20 | "no adjudication" | completed the existing partial label |
| `docs/valid-package-spec.md` | **real**, 5 papers | raw label | clause at the corpus sentence |
| `docs/keyless-extract-plan-v4.md` | **both, contrasted** | raw label | boxed note — see below |
| `docs/keyless-hybrid-ceiling.md` | **real**, 5 docs | raw label | clause beside the one-annotator note |
| `docs/seeded-corpus-spec.md` | **real**, two genres | both labels | parenthetical at the ARED contrast |
| `docs/real-corpus-supply-survey.md` | **real**, two genres | both labels | parenthetical at the same contrast |
| `docs/message-to-claude-code-attribution-plan.md` | synthetic, 30+20 | both labels | note at the section head |

Three documents got more than a clause, as INV-10 recommended, because they sit closest
to shipped or public text:

- **`extract_eval_v1.md`** — the largest cluster and the origin of the retracted
  headline. Its note points the table at the null already stated at `:22-28` (the
  constant checklist scores **0.960** against the 0.964 headline, **+0.004**) and says
  plainly that the retraction is the disclosure the ✓ column cannot carry alone.
- **`README.md`** — public-facing. The clause names what the confirm step would change,
  so a reader understands these are unaided numbers rather than the tool's ceiling.
- **`credibility-inspector.md`** — public-facing, and already said "raw" and "synthetic".
  Only "no adjudication step" was missing; the completed sentence now also states that
  the confirm step is what separates these from the practical ceiling.

**`keyless-extract-plan-v4.md` is the interesting case.** Its synthetic/real label is
not a compliance annotation but the document's actual finding — the two corpora
**invert the method ranking** (K6 0.829 synthetic / 0.22 real; K4 0.505 / 0.38). The
note says so: a figure from that document quoted without its corpus label is not a
weakened result, it is not a result.

## Reported, not fixed

**1. A5's null columns are already present where a null exists, and three citations
have none.** `metrics-spec-r6-u8` (null column), `credibility-inspector` (null
control), `README` ("its control"), `extract_eval_v1` (null in prose, now pointed at)
and `valid-package-spec` (`0.438 vs 0.125`) all carry theirs. The routing figures in
`keyless-hybrid-ceiling` (`0.357 recall@5, 0.607@20`) and the ARED-vs-journal contrast
in `seeded-corpus-spec` / `real-corpus-supply-survey` do **not**. Those are contrast
figures rather than headline metrics, so A5's requirement is arguable — but the honest
move is to say a null was never measured for them rather than to supply one here.
**Inventing a null number to satisfy a checklist is the failure this whole workstream
exists to prevent.** If A5 wants them, they need measuring.

**2. INV-10's own bucket counts do not reconcile with its table.** The findings state
*"bucket 1 — 7 · bucket 2 — 11"*, but the table's rows give **8** bucket-1 and **9**
bucket-2 (10 file locations, since row 16 spans two files). 8 + 10 = 18, which matches
the stated total of 18; the 7/11 split does not match the rows. Immaterial to the work
— every bucket-2 row was labelled regardless of how they are counted — but the number
"11 citations" appears in v2.1's queue and in the SUMMARY, and A4 should not inherit a
count its own source table contradicts. Worth one line when INV-10 is next touched.

## Not in scope, confirmed unchanged

Bucket 1 (already labelled) untouched. Bucket 3 empty — no unlabelled adjudicated
figure exists, which INV-10 traced rather than assumed. Row 18
(`nafems-2026.md:21`) is not an extraction figure at all — deterministic C3 output on
hand-authored packages — and its live defects are tracked separately in v2.1 §0.3a,
not here.

## The observation INV-10 offered, seconded

Several of these figures have already been **retracted or re-contextualised in place**:
`README:513-525`, `credibility-inspector:244-249`, `corpus-construction-findings:1178-1184`,
`ch4-h2-section:75`. A project that names its own withdrawn numbers beside the reason
is making exactly the disclosure A4 exists to make, and it is more persuasive evidence
for must-have 5 than the raw/adjudicated split itself. A4 should cite the pattern
directly rather than leaving it as an inference from four scattered corrections.
