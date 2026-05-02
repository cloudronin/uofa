"""Generate a `--explain` plain-language explanation sample for SME review.

Spec v0.4 §8.3 kill criterion: SME-rated quality ≥ 80% useful-and-correct
on a 30-firing Morrison COU1 sample after one round of prompt iteration.
If missed, the entire interpretation work stops.

This script runs the rules engine on Morrison COU1+COU2 (and other available
example packages), assembles ~30 firings, and runs the bundled-Qwen LLM
through the Phase 5 (P-B) explain function. Output is written to
`sample_<timestamp>.json` in this directory; the SME reviews it offline and
records useful-and-correct counts in `sme_scoring.md`.

Usage:
    python dev/tools/explain_sme_review/generate_sample.py
    # or with a remote backend for comparison (spec §10 stretch goal: 90% on Claude):
    UOFA_EXPLAIN_BACKEND=anthropic UOFA_EXPLAIN_MODEL=claude-sonnet-5-2026 \\
        python dev/tools/explain_sme_review/generate_sample.py

The script is intentionally not a pytest module — it's slow (one LLM call
per firing × 30 firings ≈ 5-15 minutes on local Qwen) and the scoring is
manual.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Make `uofa_cli` importable when running as a standalone script.
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uofa_cli.commands import rules
from uofa_cli.interpretation import InterpretationOptions, interpret_rules_output
from uofa_cli.llm import LLMConfig, get_backend


# Example packages that ship with the repo. Each contributes its firings to
# the sample pool. Morrison COU1 is the canonical reference per spec §8.3
# but other packages add diversity.
SAMPLE_PACKAGES = [
    REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld",
    REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou2" / "uofa-morrison-cou2.jsonld",
]


def collect_firings() -> list[tuple[Path, list[dict], list[dict], list[dict], dict]]:
    """Run rules engine on each example package in BOTH summary and jsonld modes.

    Returns [(path, summary_firings, jsonld_firings, individual_annotations, doc)]
    so the explain pipeline can use the rich jsonld data (P-B Round 1) for
    affected-evidence enrichment.
    """
    from uofa_cli.commands.rules import (
        parse_firings_jsonld,
        parse_individual_annotations,
    )

    out = []
    for pkg in SAMPLE_PACKAGES:
        if not pkg.exists():
            print(f"  SKIP (not found): {pkg.name}", file=sys.stderr)
            continue
        try:
            summary_args = argparse.Namespace(
                file=pkg, rules=None, context=None, build=False,
                raw=False, format="summary", output=None,
            )
            summary_result = rules.run_structured(summary_args)
            jsonld_args = argparse.Namespace(
                file=pkg, rules=None, context=None, build=False,
                raw=False, format="jsonld", output=None,
            )
            jsonld_result = rules.run_structured(jsonld_args)
        except FileNotFoundError as exc:
            print(f"  SKIP ({exc}): {pkg.name}", file=sys.stderr)
            continue

        jsonld_firings = parse_firings_jsonld(jsonld_result.raw_stdout) \
            if jsonld_result.raw_stdout else []
        annotations = parse_individual_annotations(jsonld_result.raw_stdout) \
            if jsonld_result.raw_stdout else []

        with open(pkg) as f:
            doc = json.load(f)
        print(f"  {pkg.name}: {len(summary_result.firings)} firings "
              f"({len(jsonld_firings)} jsonld, {len(annotations)} annotations)",
              file=sys.stderr)
        out.append((pkg, summary_result.firings, jsonld_firings, annotations, doc))
    return out


def main() -> int:
    backend_name = os.environ.get("UOFA_EXPLAIN_BACKEND", "ollama")
    model_name = os.environ.get("UOFA_EXPLAIN_MODEL", "qwen3.5:4b")
    api_key_env = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }.get(backend_name)
    base_url = os.environ.get("UOFA_EXPLAIN_BASE_URL")

    print(f"Sample generation: backend={backend_name}, model={model_name}", file=sys.stderr)
    backend = get_backend(LLMConfig(
        backend=backend_name, model=model_name,
        api_key_env=api_key_env, base_url=base_url,
    ))

    print("Collecting firings from example packages...", file=sys.stderr)
    sample_pool = collect_firings()
    if not sample_pool:
        print("ERROR: no example packages produced firings", file=sys.stderr)
        return 1

    total_firings = sum(len(firings) for _, firings, _, _, _ in sample_pool)
    print(f"Total firings across packages: {total_firings}", file=sys.stderr)
    print(f"Generating explanations (this may take several minutes)...", file=sys.stderr)

    sample = []
    t0 = time.time()
    for pkg, firings, jsonld_firings, annotations, doc in sample_pool:
        if not firings:
            continue
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc=doc,
            firings=firings,
            jsonld_firings=jsonld_firings,
            individual_annotations=annotations,
            options=InterpretationOptions(
                backend=backend,
                pack_name="vv40",
            ),
        )
        for f, e in zip(firings, env.interpretation.explanations):
            sample.append({
                "package": pkg.name,
                "firing": f,
                "explanation": e,
            })
            print(
                f"  [{len(sample):>2}/{total_firings}] {pkg.name} {f['patternId']:<14} "
                f"({f['severity']}, hits={f['hits']}) → conf={e.get('confidence', '?')}",
                file=sys.stderr,
            )

    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s ({elapsed / max(len(sample), 1):.1f}s per explanation)",
          file=sys.stderr)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = Path(__file__).parent
    out_path = out_dir / f"sample_{backend_name}_{model_name.replace('/', '_').replace(':', '_')}_{timestamp}.json"
    out_path.write_text(json.dumps({
        "metadata": {
            "backend": backend_name,
            "model": model_name,
            "elapsed_seconds": elapsed,
            "n_firings": len(sample),
            "spec_kill_criterion": "≥80% SME-rated useful-and-correct",
            "timestamp": timestamp,
        },
        "sample": sample,
    }, indent=2))
    print(f"\nWrote: {out_path}", file=sys.stderr)
    print(f"Next step: review each explanation, record useful-and-correct counts", file=sys.stderr)
    print(f"in {out_dir / 'sme_scoring.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
