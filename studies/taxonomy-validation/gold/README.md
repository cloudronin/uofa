# A16.3 gold set

150 cards drawn from the frozen Liang corpus for hand labeling, per
[the instructions](../../../docs/A16_3_gold_labeling_instructions_v0_1.md).
Those instructions govern; this file covers mechanics only.

## Get the card texts

They are not in git (see `.gitignore` — third-party text, unclear terms):

```bash
python studies/taxonomy-validation/gold/make_gold_set.py \
  --corpus <path>/modelcard_info.parquet
```

Fixed seed (`20260811`), so this reproduces the same 150 cards and the same
`row_hash` values. **It will overwrite `gold_set.csv`** — work on a copy, or
re-run only before labeling starts.

## The sheet

One row per card, columns exactly per instructions §4. Labels are blank by
construction: this tooling samples and formats and never consults the extractor,
because the instructions require you not see extractor output for a card you are
labeling.

| Column | Notes |
|---|---|
| `card_id`, `row_hash` | `row_hash` is the A9.1 pin — it identifies which *text* was labeled, not merely which model |
| `card_file` | the `.md` to read |
| `stratum` | `eval-bearing` (120) or `no-eval` (30) |
| `calibration` | `1` on the first 10 — §5's re-label set |
| `P1..P7` | `present` / `absent` / `unclear` |
| `P1..P7_note` | required for `unclear`, encouraged for edge calls |
| `seen_before`, `link_only` | `1` or blank, per §1 |

## Order of work

1. **Calibration first.** Label the 10 `calibration=1` rows, then re-label them
   at the next session's start *before* looking at your originals. Self-agreement
   under ~90% on any property means tightening that instruction before
   continuing — cheap insurance on 150 cards of signal.
2. Sessions of 20–30, recording `session_id`. Rows are shuffled across strata,
   so order effects stay checkable rather than confounded with stratum.
3. New edge case → stop, decide, append a dated note to the instructions, apply
   forward. Do **not** retro-fit earlier labels mid-study; a final consistency
   pass applies accumulated notes once, as its own recorded step.

## The 30 no-eval cards are not filler

They validate the A3 detector's **negative** calls. A false "no reported
evaluation" claims a clean absence over evidence that exists, which is the more
damaging direction, and nothing else in the study measures it.
