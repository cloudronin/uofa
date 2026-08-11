# A16 enrichment stratum

The gold set returned **zero positives** for P2, P5, P6 and P7 across 150 cards,
which makes sensitivity measurable and specificity unmeasurable. This stratum
buys the missing measurement and nothing else. Rationale, targets and reporting
rules: `../ENRICHMENT-PROTOCOL.md` (signed 2026-08-11).

Results: **`FINDINGS.md`**.

## Running it

```bash
python studies/taxonomy-validation/enrichment/search.py --corpus <corpus>
python studies/taxonomy-validation/enrichment/make_sheet.py \
    --candidates studies/taxonomy-validation/enrichment/modelbiome/candidates.jsonl \
    --out studies/taxonomy-validation/enrichment
```

`search.py` takes either pinned corpus and refuses anything else — it hashes the
file and compares against `CORPUS_PINS` before reading a row. Output lands in
`liang/` or `modelbiome/` by corpus, so the two runs cannot overwrite each other.

## What is committed and what is not

Committed: the scripts, `FINDINGS.md`, both `manifest.json` files, and — once the
session runs — `enriched_labels.csv`.

Not committed: `candidates.jsonl` and `enriched_set.csv`. Both embed card bodies
verbatim so the sheet is self-contained, and each card carries its own model
licence regardless of the corpus's CC-BY-4.0 wrapper. See `.gitignore`.

Nothing is lost by that. Both scripts are deterministic on a fixed seed against a
hash-pinned corpus, each manifest records the script hash that produced it, and
every row carries a `row_hash` tying its label to exact text.

## Labeling

Use `../../../docs/A16_3_gold_labeling_instructions_v0_1.md` **unchanged** — the
protocol does not modify them (§5.2), and the sheet is column-identical to
`gold/gold_set.csv` apart from three recording columns.

Two rules that matter more here than in the gold session:

1. **A candidate that does not state the property is labeled `absent` and
   KEPT.** It is a legitimate negative. Discarding it biases the stratum toward
   positives and destroys the specificity estimate this stratum exists to buy.
2. **`micro-ground` rows are the control**, drawn at random with no keyword
   filter. Label them identically. Their yield is reported separately (§7) and
   both outcomes are informative: positives the keyword pass missed are the most
   valuable cases in the stratum; zero yield is evidence the filter's coverage is
   adequate.

Save the completed sheet as `enriched_labels.csv` in this directory.
