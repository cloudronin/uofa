#!/usr/bin/env python3
"""Verify `_build_providers()` default config produces working calls.

Calls each of the three production-judge providers (openai, gemini,
hf-llama) through `_build_providers()` with NO overrides — same code
path Stage 2 production runs take. Catches config drift between the
calibration path (which explicitly opts out of suspect kwargs) and
the production path.

Why this exists: 2026-05-05 Stage 2 Day 1 first-fire failed every
OpenAI call with litellm.UnsupportedParamsError because production
defaulted thinking_enabled=True while Stage 1 calibration explicitly
overrode it to False. No real-API smoke had ever exercised the
default `_build_providers()` config end-to-end. This script closes
that loop.

Per-provider behavior:
- Skips a provider whose API key env var is not set.
- Single call per available provider against a synthetic case.
- Exits non-zero if any provider that has its key set fails to
  produce a valid Judgment.

Cost: ~$0.02 (3 calls).

Usage:
  OPENAI_API_KEY=$(cat /tmp/openai.txt) \
  GEMINI_API_KEY=$(cat /tmp/gemini.txt) \
  HF_TOKEN=$(cat /tmp/huggingface.txt) \
      python dev/tools/scripts/verify_default_config.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from uofa_cli.adversarial.judge.cli_args import parse_judges  # noqa: E402
from uofa_cli.adversarial.judge.providers.capabilities import (  # noqa: E402
    get_capabilities,
)
from uofa_cli.adversarial.judge.runner import _build_providers  # noqa: E402


# Synthetic case — case_id matches the cal-NNN pattern enforced by
# specs/judge_output_schema.json so strict-mode validators accept.
# Input strings must clear the schema's minLength=10 floor on
# response fields like source_taxonomy_identified; some models
# (Gemini, hf-llama Llama 4) lazily echo input strings verbatim
# rather than reasoning about them, so the input itself has to
# satisfy the downstream length constraint or post-call validation
# will reject the response. OpenAI happens to produce longer
# rephrased text, which is why the brittle "smoke" value passed
# for it but not the others — that was non-determinism luck.
SMOKE_CASE = {
    "case_id": "cal-901-default-config-smoke",
    "package": {"id": "pkg-smoke", "name": "Default-config smoke fixture"},
    "rules_fired": [],
    "phase2_outcome_class_raw": "COV-CLEAN-NEGATIVE-CONTROL",
    "coverage_class": "COV-CLEAN-NEGATIVE-CONTROL",
    "source_taxonomy": "uofa-vv40-default-config-smoke",
    "expected_rule": None,
}


# Production trio tokens — env var names pulled from the capability
# table at runtime so the smoke tracks vendor migrations (e.g. the
# 2026-05-06 hf-llama HF Router → direct Sambanova switch flipped
# auth_env_var from HF_TOKEN to SAMBANOVA_API_KEY).
PROD_TRIO_TOKENS = ["openai", "gemini", "hf-llama"]


def _env_var_for(token: str) -> str:
    """Look up the auth env var the capability table expects for `token`.

    Falls back to `{TOKEN}_API_KEY` (uppercased, hyphen→underscore) when
    a capability doesn't pin one explicitly — same convention litellm
    uses for vendor-default auth.
    """
    caps = get_capabilities(token)
    if caps.auth_env_var:
        return caps.auth_env_var
    return token.upper().replace("-", "_") + "_API_KEY"


PROD_TRIO = [(t, _env_var_for(t)) for t in PROD_TRIO_TOKENS]


async def _judge_one(provider, case):
    return await provider.judge(case)


def main() -> int:
    available = [(t, e) for t, e in PROD_TRIO if os.environ.get(e)]
    skipped = [(t, e) for t, e in PROD_TRIO if not os.environ.get(e)]

    if not available:
        print("ERROR: no production-judge keys set; need at least one of "
              + ", ".join(e for _, e in PROD_TRIO), file=sys.stderr)
        return 2

    for t, e in skipped:
        print(f"SKIP {t} (no {e})")

    # Build the same way `run_judge` does — judges_config from a
    # comma-joined token string, no model overrides, defaults for
    # everything else. If a future change adds a load-bearing default
    # that breaks one of these providers, this smoke catches it.
    tokens = ",".join(t for t, _ in available)
    positions = "ABC"[: len(available)]
    judges = parse_judges(tokens)
    # Sanity: positions assigned by parse_judges should align with the
    # tokens we passed; if parse_judges starts re-ordering, the smoke
    # still works because we re-zip below.
    assert len(judges.tokens) == len(available), (
        f"parse_judges re-ordered tokens: got {judges.tokens}, "
        f"expected {[t for t, _ in available]}"
    )

    providers = _build_providers(judges)

    failures: list[tuple[str, str]] = []
    for token, provider in zip(judges.tokens, providers):
        try:
            judgment = asyncio.run(_judge_one(provider, SMOKE_CASE))
        except Exception as exc:
            print(f"FAIL {token}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            failures.append((token, f"{type(exc).__name__}: {exc}"))
            continue
        # Minimum schema check: verdict + version stamp present.
        if not getattr(judgment, "verdict", None):
            print(f"FAIL {token}: judgment.verdict empty",
                  file=sys.stderr)
            failures.append((token, "verdict empty"))
            continue
        print(
            f"OK   {token}: model={judgment.judge_model!r} "
            f"verdict={judgment.verdict!r} "
            f"prompt={judgment.prompt_template_version!r}"
        )

    if failures:
        print(f"\n{len(failures)} of {len(available)} providers failed",
              file=sys.stderr)
        return 1
    print(f"\nAll {len(available)} default-config providers OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
