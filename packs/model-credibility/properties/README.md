# Property definitions — the single source of truth

One file per Group-B property. **Both** the labeling instruction sheet and the
extraction prompt RENDER from these files. Neither restates a definition in its
own words.

## Why this exists

On 2026-08-11 the two documents were compared and found to define three of four
enriched properties differently (`studies/taxonomy-validation/enrichment/
CONSTRUCT-DRIFT.md`). The drift was invisible because each document read
correctly on its own:

- P7's sheet counted "ablations offered as controls"; the prompt named neither
  ablations nor limitation statements. Three model families scored 100%
  false-fire on P7 as a direct result.
- P6's prompt asked what "this score" supports, per benchmark block; the sheet
  accepted a section-level tie.
- P2's prompt omitted "variance across runs/seeds", the largest positive cluster
  in the enrichment stratum.

Nobody edited either document carelessly. They were written months apart, each
faithful to its own purpose, and they drifted the way two paraphrases of one
intent always drift.

**A labeling instruction and an extraction prompt that define the same property
in their own words are two constructs wearing one name.** The fix is not
vigilance. It is that they share text.

## The contract

Each `P*.json` carries the definition once. `uofa_cli.properties` renders:

| Target | Region | Rendered by |
|---|---|---|
| `docs/A16_3_gold_labeling_instructions_v0_1.md` | between `<!-- BEGIN/END property-definitions -->` | `render_sheet()` |
| `packs/model-credibility/prompts/card_eval_extract_prompt.txt` | between `# BEGIN/END property-fields` | `render_prompt_fields()` |

`tests/test_property_definitions_are_one_source.py` asserts the committed regions
are byte-identical to a fresh render. Editing either artifact by hand fails the
build; the definition changes here or not at all.

## Editing

Change the JSON, run `python -m uofa_cli.properties --write`, commit both the
source and the rendered artifacts together.

**Changing a definition changes what was measured.** The extraction prompt's
hash is pinned into every specificity result, so a render is a new measurement,
not a fix — see `A16.4`'s qualification section.
