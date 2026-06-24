"""S0 spike - run the pipeline end-to-end with no UI and print findings.

Usage (from repo root, venv active):
    python -m space.spike                 # mock extract on the Morrison sample
    python -m space.spike --real           # real Ollama extract (needs `uofa setup`)

The mock path validates the full plumbing (read -> adapt -> map -> SHACL ->
weakeners -> teardown) without Ollama. It also flips two factors to
"not-assessed" to demonstrate the W-EP-04 weakener firing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from uofa_cli import paths

from space.pipeline import analyze


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true", help="use the real model instead of mock")
    ap.add_argument("--pack", default="vv40")
    args = ap.parse_args()

    root = paths.find_repo_root()
    sample = root / "packs" / "vv40" / "examples" / "morrison" / "source"
    model = None if args.real else "mock"

    # Demonstrate a couple of gaps so weakeners fire under the mock.
    edits = {"Use error": "not-assessed", "Test samples": "not-assessed"}

    outcome = analyze(
        [sample],
        args.pack,
        model=model,
        factor_edits=edits,
        on_progress=lambda m: print(f"  · {m}"),
    )

    if not outcome.ok:
        print(f"\nFAILURE [{outcome.kind}]: {outcome.user_message}")
        return 1

    p = outcome.payload
    c = p["completeness"]
    print(f"\nPack: {p['pack']}")
    print(f"Headline: {p['headline']}")
    print(f"Completeness: {c['n_assessed']} of {c['n_expected']} assessed (denom {c['denom']})")
    if c["missing"]:
        print(f"  Missing: {', '.join(c['missing'])}")
    st = p["structural"]
    print(f"SHACL conforms: {st['conforms']} ({st['n']} structural violations)")
    print(f"Weakeners fired: {len(p['weakeners'])}")
    for w in p["weakeners"]:
        factors = f" factors={w['factors']}" if w.get("factors") else ""
        print(f"  ⚡ {w['patternId']} [{w.get('severity')}] hits={w.get('hits')}{factors}")

    # Teardown invariant: the debug file must be gone after a run.
    from space.pipeline import DEBUG_RESPONSE_FILE

    print(f"\n/tmp debug file present: {DEBUG_RESPONSE_FILE.exists()} (expected False)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
