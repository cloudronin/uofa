# Security model — API keys and the LLM layer

UofA's `--explain` and `extract` commands optionally talk to remote LLM
backends (Anthropic, OpenAI, OpenAI-compatible). This document spells
out how the CLI handles credentials and what's in / out of scope for the
threat model.

For LLM provider configuration see [llm-config.md](llm-config.md); for
the user-facing flag set see [explain.md](explain.md).

## Three rules (spec v0.4 §6.4)

### Rule 1: API keys never appear in config files directly

Configs reference env var names via `api_key_env`, never literal keys:

```toml
# ✓ Allowed — env var name only
[llm]
backend = "anthropic"
api_key_env = "ANTHROPIC_API_KEY"

# ✗ Rejected by the config validator with a clear error
[llm]
backend = "anthropic"
api_key = "sk-ant-leaked-this-everywhere"
```

The validator rejects any `[llm]` section containing an `api_key` field
(literal value), with an error directing the user to `api_key_env`
instead. This addresses the version-control-leak path — `uofa.toml`
files committed to GitHub will not leak keys because keys are never
in the file.

### Rule 2: API keys never appear in cached results, error messages, or verbose output

- The cache (`~/.uofa/cache/explain.db`) stores model identifier and
  backend identifier, never the API key.
- Verbose output shows token counts and cost estimates but never echoes
  key values.
- Authentication-failure error messages say "anthropic authentication
  failed" rather than echoing the attempted credentials.

The `tests/security/` suite (and the `test_resolve_api_key_error_does_not_echo_key_value`
test in `test_llm_config.py`) verifies this invariant: even when the
relevant env var IS set, the error path doesn't leak its value.

### Rule 3: API keys are read at request time, not stored in CLI state

The CLI reads `os.environ[api_key_env]` at the moment of each LLM API
request and discards the value after the request completes. The key is
never persisted to disk by the CLI, never written to logs, never
included in the cache. Implementation: `uofa_cli.llm.resolve_api_key()`.

This matters for shared workstation scenarios: a user running
`uofa rules --explain` on a shared machine doesn't leave their API key
in any UofA-managed location. The key lives in their shell environment
or password manager, accessed by the CLI only at request time.

## What this does NOT protect against

- **Your own env var management.** If you put your API key in a shell
  history file, in an unencrypted dotenv file, or in a publicly-readable
  location, the CLI can't prevent the leak. Use a secrets manager
  (`direnv` with `.envrc.gpg`, `1Password CLI`, AWS Secrets Manager,
  etc.) for any deployment beyond local development.
- **Your network.** If you run UofA on an untrusted network where
  HTTPS termination or DNS resolution can be intercepted, that's
  outside the CLI's scope (mitigate via VPN or trusted-network policy).
- **The remote backend's logging.** Anthropic, OpenAI, and other
  providers may log API request bodies for abuse detection or billing.
  If your evidence documents are sensitive, review the provider's
  privacy policy or use a local backend (Ollama) that doesn't leave
  the machine.

## Recommended setups

### Individual practitioner (laptop)

1. Use the bundled local Ollama (no API keys at all).
2. If you need higher quality on a specific package, override per
   invocation:
   ```bash
   ANTHROPIC_API_KEY=$(op read 'op://Personal/Anthropic/api key') \
       uofa rules my-package.jsonld --explain \
       --explain-backend anthropic --explain-model claude-sonnet-5-2026
   ```

### Team with one approved vendor

1. Set up the team's preferred backend in `~/.uofa/config.toml`:
   ```toml
   [llm]
   backend = "anthropic"
   model = "claude-sonnet-5-2026"
   api_key_env = "ANTHROPIC_API_KEY"
   ```
2. Use a secrets manager that injects `ANTHROPIC_API_KEY` into the
   shell environment (direnv, 1Password CLI, chezmoi).
3. Project `uofa.toml` files contain no LLM config — they inherit
   from each user's home config.

### Air-gapped / regulated environment

1. Use Ollama exclusively. Pull a model appropriate to your hardware
   (`llama3.3:70b` if you have GPU; `qwen3.5:4b` if you don't).
2. Set `[llm] backend = "ollama"` in project `uofa.toml`.
3. No env vars, no remote calls, no third-party logging.

## Where the CLI's responsibility ends

The CLI's responsibility is bounded: do not leak keys via UofA-controlled
channels (config files, cache, output, logs). Verified by:

- **Code review of every emit path** — `output.py` helpers don't have
  access to keys; cache schema doesn't carry them; LLM error normalization
  in `litellm_backend._normalize_exception()` builds messages without
  echoing credentials.
- **Test invariants** — `tests/test_llm_config.py::TestApiKey` and
  `tests/test_litellm_backend.py::test_authentication_error_normalized`
  assert the no-leak property on the relevant code paths.
- **Config validation** — `uofa_cli.llm.config._validate_section()`
  rejects literal `api_key` fields at parse time.

What happens in your shell environment, your dotfiles, or the backend
provider's logging is outside the CLI's control. Plan accordingly.
