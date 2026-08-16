# No extractor clears the conjunction

Run 2026-08-15 against `DECLARATION.md`, committed before the runner existed,
and under the repeat policy in
`docs/decisions/2026-08-15-scorecard-repeat-policy.md`. Real corpus, six
hand-annotated papers, prompt pinned at `e67cc74b06f2c622` (the reverted prompt
— Q2's intervention stays out).

## The scorecard

| arm | runs | coverage | density | groundedness | $/doc | verdict |
|---|---|---|---|---|---|---|
| local-4b | 1† | 0.878 | **0.244** | 1.000 (n=38) | $0.000 | fails: density, coverage |
| incumbent | 3 | 1.000 | **0.003** `[0.000–0.010]` | 0.333 `[0.000–1.000]` **(n = 0, 0, 1)** | $0.0139 | **UNSTABLE AT THE BAR** |
| family-72b | 3 | 1.000 | **0.048** `[0.021–0.073]` | 1.000 (n = 2, 6, 8) | $0.0057 | fails: density |
| frontier | 3 | 0.940 `[0.854–1.000]` | **0.139** `[0.103–0.157]` | 1.000 (n = 25, 21, 8) | $0.0473 | **UNSTABLE AT THE BAR** |

† cites determinism in lieu of repeating, per policy §4.

**Exclusion, stated on the table rather than absorbed:** `elemance` failed on
two arms for two different reasons — a timeout on `family-72b`, a `ValueError`
on `frontier`. Affected arms are five-paper. Both tracebacks are filed. Two
distinct failure modes on one document is a fixture question, not noise; it is
the largest paper in the set at 1,319 sentences.

## The verdict

**No candidate clears.** Outcome (d), named in the declaration in advance as
legitimate and likely.

**Density is the stable failing clause in every arm** — 0.244 / 0.003 / 0.048 /
0.139 against ≥ 0.40. Nearest miss **1.6×**, furthest **133×**. No spread on
that clause straddles the floor in any arm, so the verdict does not depend on
which run is taken.

Four model classes, three families, two orders of magnitude of capacity.

## The two unstable arms are unstable for different reasons, and the difference matters

This is the denominator rule appearing at the **spread** layer for the first
time: *a spread is only as meaningful as the population beneath it.*

**The incumbent's `[0.000–1.000]` is not model nondeterminism.** Its
groundedness denominators across three runs are **0, 0 and 1 claims**. Two runs
produced no checkable claim at all — groundedness returns 0.0 there by the
deliberate convention that making no claim is not the same as making only true
ones — and the third produced exactly one, which grounded. The full-range spread
is an artefact of a ratio computed over an empty-or-singleton denominator.

The truer statement is **not** "the incumbent is wildly nondeterministic". It is
**"the incumbent produces so little checkable content that its grounding score
is meaningless"** — 1 checkable claim across 288 rationales in three passes over
six papers. A groundedness figure at n≈1 is precisely the kind the taxonomy
exists to flag, and reporting it as a model-stability finding would have been
the error.

**The frontier's spread is real.** Its coverage rests on a genuine population:
rationales written per run went **96 → 70 → 58**, a 40% swing in how many
factors it answers at all, at an identical pin. Its groundedness denominators
are 25, 21, 8 — small, but populations rather than singletons.

So: `UNSTABLE AT THE BAR` is correct for both arms, and the writeup must
distinguish **instability of the model** (frontier) from **instability of a
ratio resting on ~one claim** (incumbent). Both fail; only one is a statement
about the model.

## The synthetic-to-real collapse: the standing rule's proof case

**The 4B is the best of the four and still fails**, and how it got there is the
finding.

    claim density, qwen3.5:4b     synthetic 0.420     real 0.244

It was the density champion on synthetic and the only arm that looked like a
challenger. On the corpus that decides, it lands at 0.244 — below the floor, and
it fails **coverage** too at 0.878, the only arm to miss two clauses.

**Adoption on the synthetic figure would have shipped a model that fails the bar
on the corpus that matters.** That is the standing rule — paired synthetic and
real figures are inseparable, and where they disagree the real number is the
result — with a worked instance at corpus level.

## The tradeoff frontier, now measured across four classes

Nobody escapes it; they pick a different point on it.

- The two arms holding coverage at a clean 1.000 (incumbent, family-72b) have
  essentially no density — 0.003 and 0.048.
- The two arms with the most density (local-4b 0.244, frontier 0.139) are the
  two that fail or destabilise coverage — 0.878 and 0.854–1.000.

Checkable specificity trades against coverage and grounding across three
families spanning two orders of magnitude. **Construct-shaped, not
capacity-shaped**, and consistent with the qualification-table result where
frontier models failed the four-property extraction worse than expected.

Cost lands where the declaration put it, next to the pin: the frontier arm is
**8× the family-72b's cost** and fails more clauses.

## Instrument recovery, and why every density here is a floor

Dated note, 2026-08-15, correcting a claim made in commit **`82b4baf7`**.

That commit's message asserts the PDF-reading bias was **optimistic** — that raw
object syntax carries more numbers, so claims ground too easily. **That is
wrong, and it was asserted without measurement.**

Measured on bologna: the broken reading carries 761 spurious decimals **and is
missing 15 of the 39 decimals that appear in the prose**, because PDF text lives
in compressed streams and `read_text` surfaces structure, not sentences. **38% of
genuine figures were unfindable**, so honest claims failed to ground. Confirmed
by the re-score: the frontier arm's groundedness moved **0.621 → 1.000** when the
noise was *removed*. Removing junk raised the score, which is only possible if
the junk was suppressing real matches.

History cannot be edited, so the correction is dated here and cites the commit by
hash. `read_source_text`'s docstring carries it too.

**The recovery rate itself is unmeasured against an independent reference.** The
fixed reader finds 39 decimals on bologna and recovers 15 the broken one could
not, but no second extractor is available on this machine (`pdftotext` and
`mutool` both absent) and the corpus carries no ground truth for total document
figures.

**Therefore every real-corpus density in this table is a floor, not a point.**
That does not threaten the verdict — the nearest miss is 1.6× with headroom — but
a committee-grade table states its instrument's recovery rather than leaving it
inferable. Establishing it needs a second independent extractor and is filed as
follow-up.

## The meta-lesson, joining the lineage by name

A confident causal claim, stated in a commit message without measurement, caught
by measuring. Same class as the session's other self-catches — the routing bug
found by being wrong about prompt placement, `"or implied"` refuted by splitting
by pack, the segmenter's net-zero found by checking the other two fixtures, the
contaminated no-op control caught because the numbers moved the wrong way for
the change.

Every one was a plausible conclusion from a subset that agreed with it, and every
one was caught by splitting the population rather than by more analysis of the
same rows. The lineage is stronger with this instance in it than without.

## Re-entry condition, so this closes rather than stays open

**A candidate must clear the conjunction on the real corpus under the repeat
policy.** That is the condition for reopening model selection.

Without it, "no candidate cleared" quietly licenses trying models indefinitely
until one does — the same shape as trying metrics until one passes, which the
replacement-thresholds doc forbids by name.

Consequence for the pack: the prose path ships **gated on the panel** for
judgment-bearing properties, and the qualification table documents why, with
four families of evidence behind it.

---

**The study set out to pick a model and produced the evidence that no pickable
model exists at the declared bar.**
