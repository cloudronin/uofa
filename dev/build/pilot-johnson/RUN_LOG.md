# Run log — Johnson encoding pilot

Spec: `UofA_Encoding_Pilot_Spec_v1_0_Johnson.md` v1.0 (ACTIVE, 2026-08-19)
Session date: 2026-08-20
State: **DRAFT throughout. Nothing in this tree is signed and nothing is adjudicated.**

Everything here is session work under spec §0. Dispositions are candidates; the
author re-adjudicates every one of them in the review pass, which runs later and
under the written protocol, not here.

## Pins

| What | Value |
|---|---|
| Repo HEAD at session start | `21dfcac` |
| Repo HEAD after the gitignore carve-out | `2b40dfe` |
| Site commit (on-ramp page) | **`31cb466`** (2026-08-18) |
| `uofa` version | 0.11.0 (editable install, `.[extract,excel,test]`) |
| Pack | `nasa-7009b` 0.5.0 |
| Extract prompt sha256 (first 16) | `c47bf1745a12084e` (`packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt`) |
| Rule engine | `uofa-weakener-engine-0.1.0.jar`, built from `src/weakener-engine` with Maven, 19 903 448 bytes |
| JRE | system OpenJDK 21.0.10 (no bundled runtime in this environment) |
| Source document sha256 (first 32) | `1b767b2d4128dcc67bdb6803fe33034e` |
| Source copy in tree | `source/NTRS-20200002832-Johnson-2020.pdf` |

### Site commit drift — finding F-1c

The protocol outline's Prompt 1c names `01c7372` as "today's" site commit. The
commit that currently builds the on-ramp page is `31cb466`. The pilot pins
`31cb466` and the drift is recorded rather than silently reconciled, because a
protocol that tells an encoder to pin a commit needs to say what happens when the
outline's own pin has moved on. Filed under §1 of the findings memo.

## Extractor

    uofa extract dev/build/pilot-johnson/source/NTRS-20200002832-Johnson-2020.pdf \
      --pack nasa-7009b \
      --extract-backend anthropic \
      --extract-model claude-sonnet-5 \
      -o dev/build/pilot-johnson/johnson-extracted.xlsx

| Field | Value |
|---|---|
| Backend | `anthropic` (litellm provider path, key from `ANTHROPIC_API_KEY`) |
| Model | `claude-sonnet-5` |
| Thinking mode | **off** — `--thinking` not passed; the flag defaults False |
| temperature | backend default (not set by the CLI) |
| max_tokens | 16384 (extractor default; the same value the extraction eval pinned) |

### The model string is NOT "the same as the extraction eval" — read this before citing it

Spec §2 says to use "the same frontier model the extraction eval used." Checked
against the trace, that phrase has no referent, and the run log says so rather
than asserting a lineage the repo does not support.

- `docs/extract_eval_v1.md` (2026-05-04) **is** the extraction eval, and its
  extractor ran on local `ollama/qwen3.5:4b`. Its own cost table reads
  "Iteration API ($): $0 (local qwen)", and its failure analysis is about
  qwen3.5:4b dropping closing braces in long JSON. Sonnet 4.6 appears in that
  report only as the **corpus generator** ($6.13, two-step). So the extraction
  eval used no frontier model at all.
- `dev/tools/scripts/extract_accuracy_log.jsonl` agrees: 9 rows
  `ollama/qwen3.5:4b`, 6 rows Together `Llama-3.3-70B-Instruct-Turbo`, zero
  Anthropic rows.
- The only frontier **extractor** run in the repo is arm 4 of the
  model-selection scorecard (`studies/model-selection/`,
  `dev/tools/scripts/model_selection.py`), a later and separate study. Its
  declared string `claude-sonnet-5-2026` returns HTTP 404 and it runs as
  `claude-sonnet-5` (DECLARATION.md:48-56).

**Author ruling, 2026-08-20:** run current Sonnet and disclose the divergence.
The pilot's extractor is `anthropic/claude-sonnet-5`, which postdates both the
extraction eval's `ollama/qwen3.5:4b` and the scorecard's arm 4. The pilot
measures protocol friction, not H2 comparability, so a newer extractor is fine
as long as the delta is stated. It is stated here. Filed under §3 of the
findings memo as the rule the protocol needs: an encoding names its extractor by
version and says what it is *not* the same as, rather than inheriting a claim
from a spec sentence.

## Provenance self-audit (spec §2.4)

Recorded after import. Three counts, reconciled:

| Count | Value |
|---|---|
| `field provenance:` line from `uofa import` | _pending_ |
| Cells I anchored by hand during review | _pending_ |
| Cells whose value came from Table 3 geometric recovery (author-side, never `extracted`) | _pending_ |

## Command trace

| # | Command | Outcome |
|---|---|---|
| 0 | `pip install -e '.[extract,excel,test]'` | uofa 0.11.0 |
| 0 | `mvn package` in `src/weakener-engine` | JAR built |
| 0 | `uofa check packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld` | C1 ✓ C2 ✓ C3 ✓ — toolchain sound before the pilot touches anything |
