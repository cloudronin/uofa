"""A `uofa check` report is the same twice, for a pack with derivations too.

`oos/snapshot.py` promises a stable report: volatile fields dropped, paths
repo-relative, lists sorted -- the property every baseline under
`tests/fixtures/baseline_reports/` rests on. The derivation pre-pass arrived
later and the serializer never learned about it, so for iso42001 and surrogate
the report carried three things that change on every run:

- `derivations.elapsed_seconds`, a wall-clock timing;
- `derivations.enriched_package_path`, a temp file;
- `rules.file`, the same temp file -- the rules run on the enriched copy -- so
  the report named, as the package it described, a file `run_structured` had
  already deleted.

Found pinning the iso42001 bundles: all eleven baselines failed straight after
being written.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from uofa_cli.commands.check import run_structured
from uofa_cli.oos.snapshot import to_json

REPO_ROOT = Path(__file__).resolve().parents[1]
COU1 = REPO_ROOT / "packs/iso42001/examples/hybrid/cou1/uofa-iso42001-cou1.jsonld"
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"

pytestmark = pytest.mark.skipif(
    not (shutil.which("java") and JAR.exists()), reason="java + built JAR required")


def _check(path: Path):
    return run_structured(argparse.Namespace(
        file=path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, enable_oos=False, disable_oos=False, no_color=True,
        verbose=False, repo_root=None, pack=["iso42001"], active_packs=["iso42001"]))


def test_the_report_is_the_same_twice():
    first = to_json(_check(COU1), repo_root=REPO_ROOT)
    second = to_json(_check(COU1), repo_root=REPO_ROOT)
    assert first == second


def test_the_derivation_pass_still_reports_what_it_did():
    """Stable, not silent: the counts and the config stay."""
    d = json.loads(to_json(_check(COU1), repo_root=REPO_ROOT))["derivations"]
    assert d["returncode"] == 0 and d["construct_count"] == 1
    assert "derived_triple_count" in d and d["config"]["enabled"] is True
    assert "elapsed_seconds" not in d and "enriched_package_path" not in d


def test_the_rules_result_names_the_package_that_was_checked():
    result = _check(COU1)
    assert result.derivations is not None, "iso42001 runs the derivation pre-pass"
    assert result.rules.file == COU1
    assert json.loads(to_json(result, repo_root=REPO_ROOT))["rules"]["file"] == \
        COU1.relative_to(REPO_ROOT).as_posix()
