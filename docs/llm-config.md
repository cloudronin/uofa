# LLM configuration — `[llm]` section

The `[llm]` section in `uofa.toml` (project-level) and `~/.uofa/config.toml`
(user-level) configures the LLM backend used by both `uofa extract` and
`uofa <command> --explain`. One config, two consumers (spec §3.6).

For API-key handling and the threat model see [security.md](security.md).

## Precedence

Highest priority first:

1. **Command-line flags** — `--extract-backend` / `--extract-model` for
   extract; `--explain-backend` / `--explain-model` for explain
2. **Project `[llm]`** — `<project_root>/uofa.toml`
3. **User `[llm]`** — `~/.uofa/config.toml`
4. **Bundled** — Ollama + the model recorded by `uofa setup`
   (typically `qwen3.5:4b`)

Per-field fallthrough: a CLI flag setting only `backend` falls through to
project config for `model`. So `uofa rules X --explain --explain-backend
anthropic` inherits the model name from `uofa.toml` if one is set.

## Supported backends

| Backend | Description | Local/Remote |
|---|---|---|
| `ollama` | Local Ollama with any pulled model | Local |
| `anthropic` | Anthropic API (Claude models) | Remote |
| `openai` | OpenAI API (GPT models) | Remote |
| `openai-compatible` | Any OpenAI-compatible endpoint (Together AI, Groq, vLLM, …) | Configurable |
| `bundled` | Explicit alias for the bundled Ollama setup | Local |
| `mock` | In-process canned responses (testing / offline dev) | Local |

## Project config (`uofa.toml`)

Default — bundled Ollama + qwen3.5:4b:

```toml
# (no [llm] section needed — the default is the bundled setup)
```

Switch to Claude:

```toml
[llm]
backend = "anthropic"
model = "claude-sonnet-5-2026"
api_key_env = "ANTHROPIC_API_KEY"
```

OpenAI-compatible endpoint (Together AI, vLLM, etc.):

```toml
[llm]
backend = "openai-compatible"
base_url = "https://api.together.xyz/v1"
model = "meta-llama/Llama-3.3-70B-Instruct"
api_key_env = "TOGETHER_API_KEY"
```

Local Ollama with a non-default model:

```toml
[llm]
backend = "ollama"
model = "llama3.3:70b"   # user has pulled this larger model
```

Optional fields:

```toml
[llm]
backend = "anthropic"
model = "claude-sonnet-5-2026"
api_key_env = "ANTHROPIC_API_KEY"
max_tokens = 4096          # default 2048
timeout_seconds = 60       # default 30 / 60 depending on call site
```

## User config (`~/.uofa/config.toml`)

For practitioners who want one LLM for all UofA projects without
copying configs:

```toml
# ~/.uofa/config.toml — applies to every project that doesn't override
[llm]
backend = "anthropic"
model = "claude-sonnet-5-2026"
api_key_env = "ANTHROPIC_API_KEY"
```

The `[llm]` section coexists with the existing `[runtime]` / `[model]` /
`[meta]` sections that `uofa setup` manages — they live in the same file
but `[llm]` is owned by the LLM config layer.

## Per-command overrides

Use the same backend everywhere via `[llm]`, override on the command line
when you want to differ for one invocation:

```bash
# Project default = Ollama. Quick check on Claude for a single run.
uofa rules my-package.jsonld --explain \
    --explain-backend anthropic \
    --explain-model claude-sonnet-5-2026

# Project default = Anthropic. Pull this extract through bundled Qwen
# specifically so evidence documents don't leave the local machine.
uofa extract evidence/ --extract-backend bundled
```

Per-command `[llm.extract]` / `[llm.explain]` config sections are NOT
supported in v0.6.0 — flags are the only way to differ per command. If you
need this and the use case justifies the config-schema complexity, file
an issue (spec §11 Q11).

## Diagnosing config issues

```bash
# Drop into Python and see what the resolver returns:
python -c "from uofa_cli.llm import resolve_llm_config; \
           c = resolve_llm_config(); \
           print(c)"
```

`LLMConfig.provenance` shows the source of every resolved field
(`'cli'` / `'project'` / `'user'` / `'bundled'`), so you can trace why
a particular value was chosen.

## Adding a backend

The current `LiteLLMBackend` covers everything `litellm` supports — that's
the bulk of providers in production use. To add a backend not covered by
litellm:

1. Add `<NAME>` to `ALLOWED_BACKENDS` in
   `src/uofa_cli/llm/config.py`
2. Add a default capability row in `_DEFAULT_CAPS` in
   `src/uofa_cli/llm/litellm_backend.py`
3. If the backend doesn't fit litellm's model-string convention,
   override `_litellm_model()` for it — or add a direct path like the
   one Ollama uses
4. Add tests under `tests/test_litellm_backend.py`
