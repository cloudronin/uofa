# `--explain` — LLM-driven interpretation of UofA analysis output

The `--explain` flag layers plain-language explanation on top of the
deterministic analysis output produced by `uofa rules`, `uofa check`,
`uofa diff`, and `uofa shacl`. The structured output remains the source of
truth; `--explain` adds a human-readable interpretation block underneath.

This document covers usage. For LLM provider configuration see
[llm-config.md](llm-config.md); for API-key handling see
[security.md](security.md).

## Quick start

```bash
# Run rules and explain each firing in plain language (uses bundled qwen3.5:4b
# via Ollama; takes ~10s per firing on commodity hardware after first run).
uofa rules my-package.jsonld --explain

# Limit to the top 3 most severe firings — useful for quick triage.
uofa rules my-package.jsonld --explain --explain-max-items 3

# Render the explanation block as JSON for piping or programmatic use.
uofa rules my-package.jsonld --explain --explain-format json

# Same on check, diff, shacl:
uofa check my-package.jsonld --explain
uofa diff cou1.jsonld cou2.jsonld --explain
uofa shacl my-package.jsonld --explain
```

## How it works

Each command runs its primary analysis as before, then — when `--explain`
is set — passes the structured result to the interpretation pipeline at
`uofa_cli.interpretation`. The pipeline:

1. Extracts per-item context bundles (firing, difference, violation) and
   enriches them with pack-level metadata (pattern descriptions from
   `.rules` files, COU identity, standard).
2. Dispatches to applicable interpretation functions per the
   spec §2.6 matrix:

   | Function | rules | check | diff | shacl |
   |---|---|---|---|---|
   | Plain-language explanation | ✓ | ✓ | ✓ | ✓ |
   | Grouping | ✓ | ✓ | – | ✓ |
   | Severity contextualization | ✓ | ✓ | – | ✓ |
   | Cross-item patterns | ✓ | ✓ | – | – |
   | Surviving-set narrative | – | ✓ (when C4 present) | – | – |

   Currently shipped (v0.6.0): plain-language explanation. Other functions
   land in subsequent point releases (P-F / P-G / P-H / P-I / P-K).
3. Wraps the per-function results in an envelope per spec §4.5 and
   renders to the chosen format.

## Caching

Identical inputs produce identical outputs deterministically — the cache at
`~/.uofa/cache/explain.db` makes second invocations near-instant (≈3 ms
typical vs ≈10 s for a cold call against bundled Qwen). Cache key includes
the prompt content + backend + model + interpretation version, so:

- Re-running `uofa rules X --explain` after a successful run → cache hit
- Switching `--explain-backend anthropic` → cache miss (different model)
- Bumping the interpretation envelope schema → all entries invalidated

Bypass with `--explain-no-cache`. Clear with
`rm ~/.uofa/cache/explain.db` (a Python helper for cache management is on
the Phase 14 backlog).

## Standalone re-interpretation

`uofa explain --from-file FILE` and `uofa explain --from-stdin` interpret
JSON output captured from a previous `--explain --explain-format json`
invocation, without re-running the underlying analysis:

```bash
uofa rules my-package.jsonld --explain --explain-format json > cache.json
# ... later ...
uofa explain --from-file cache.json --format markdown
uofa explain --from-file cache.json --format markdown --backend anthropic
```

The standalone command auto-detects the input type (rules / check / diff /
shacl) by JSON shape; pass `--input-type` to override.

## Output formats

`--explain-format`: `text` (default), `json`, `markdown`, `html`.

- **text**: ANSI-colored CLI output. Auto-disables color when stdout
  isn't a TTY or when `NO_COLOR` is set.
- **json**: spec §4.5 envelope. Stable contract for the Tauri GUI and
  other programmatic consumers.
- **markdown**: GitHub-flavored, suitable for PR comments / issue bodies.
- **html**: standalone fragment (`<div class="uofa-explain">…`) for
  embedding in reports. All user-derived text is HTML-escaped.

## Graceful degradation

When no LLM is available — Ollama not running, configured remote
unreachable, API key missing, etc. — the underlying analysis still runs
and produces its structured output. The explain block is replaced with
a notice describing the failure and listing remediation options:

```
[Note: --explain was requested but no LLM is available.
Showing structured output only.

To enable, you have several options:

1. Install Ollama and pull the bundled model (local, free, private):
       curl -fsSL https://ollama.com/install.sh | sh
       ollama pull qwen3.5:4b

2. Configure a remote LLM in your project's uofa.toml or in ~/.uofa/config.toml:
       [llm]
       backend = "anthropic"
       api_key_env = "ANTHROPIC_API_KEY"
       model = "claude-sonnet-5-2026"

3. Use the proprietary UofA Copilot for higher-quality interpretation
   plus remediation suggestions, submission narrative generation, and
   conversational Q&A:
       https://uofa.net/copilot

Diagnostic: <specific reason>]
```

Exit codes:
- `--explain` degradation → exit 0 (the analysis succeeded; interpretation
  was opt-in)
- `extract` no-LLM → exit 1 (extract requires an LLM to function)

## Pack template authoring

Bundled prompt templates live at
`src/uofa_cli/interpretation/templates/<command>/<function>.jinja2` and
serve as pack-agnostic defaults. Packs that want pack-specific framing
(NASA-STD-7009B terminology, FDA terminology, etc.) ship their own
templates under `packs/<pack>/prompts/<command>/<function>.jinja2`; the
loader prefers pack-specific over bundled.

Template variables per command (full namespace in
`schemas/explain_template_vars_v0_2.md`, future):

| Command | Variables |
|---|---|
| rules / check | `firing.{patternId,severity,hits,description,affectedNode,affected_evidence,constituent_firings}`, `evidence`, `pack.{name,standard,profile}`, `cou.{name,description,device_class,model_risk_level}` |
| diff | `difference.{patternId,severity,onlyIn,description}`, `before`, `after`, `pack` |
| shacl | `violation.{constraint,severity,affectedNode,description}`, `expected`, `actual`, `pack` |

For rules/check, P-B Round 1 added two list-shaped variables:

- `firing.affected_evidence` — list of summary dicts (`iri`, `kind`, `label`,
  `status`, `required`, `achieved`) resolved from the package JSON-LD.
  Iterate to tell the model which specific items triggered the firing.
- `firing.constituent_firings` — for COMPOUND patterns: list of
  `{patternId, severity, description, affected: <summary dict>}` for each
  constituent weakener that triggered the compound.

## Output schema (v0.4.0)

The interpretation envelope's per-explanation shape:

```json
{
  "patternId": "W-EP-04",
  "severity": "High",
  "affected_evidence_summary": "Six factors are unassessed (Use error, Test samples, ...).",
  "gap_description": "The submission lacks credibility levels for these factors.",
  "relevance_to_cou": "For Class III VAD at MRL 5, this leaves the highest-risk submission category uncovered."
}
```

`patternId` and `severity` are authoritative from the firing context
(the model echoes them but its echo is discarded — closes a class of
identifier-hallucination bugs).

Schema version history:

- **0.4.0** — dropped `confidence` field. Two iterations on bundled
  qwen3.5:4b produced 11/11 high regardless of explicit criteria; the
  model can't self-assess on this task so the field was misleading.
  Failures still surface via `error: true` + diagnostic text in
  `gap_description`.
- **0.3.0** — split single `explanation` field into the three structured
  prose fields (P-B Round 1). Forces the model to do each piece of
  analytical work explicitly.
- **0.2.0** — initial P-B (Round 0) shape.

The cache invalidates automatically on version change.

## Limitations in v0.6.0

- Only the **explain** function is wired (P-B). Group / contextualize /
  cross / narrative ship in subsequent point releases (P-F / P-G / P-H / P-I).
- shacl `--explain` runs the pipeline but no shacl-specific explain
  function is registered yet (P-K). Pipeline returns an empty
  interpretation block.
- Ollama goes through a direct `/api/chat` HTTP path because
  litellm's `ollama_chat/` provider returns empty content intermittently
  for thinking-capable models (qwen3.5+). See note in
  `src/uofa_cli/llm/litellm_backend.py`.
- Pattern descriptions come from `# W-XX-NN: <name>` comment headers in
  `.rules` files. Without descriptions, explanations fall back to
  "the specific nature of W-EP-04 cannot be determined from the
  provided input"; with them, quality jumps substantially.
- 30-firing SME quality review (spec §8.3 kill criterion) is pending —
  see `dev/tools/explain_sme_review/`.
