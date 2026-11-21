"""The W-CV rules, run through the production `check.run_structured` path.

Fixtures (tests/fixtures/weakeners/W-CV-0N/) are synthetic packages: one
assessed `Discretization error` factor and one folded
`calculationVerification` record each. A boundary fixture is the silent
neighbour of its positive one.

The null controls are the point (spec v0.3, section 8, G4). Silence without
`--calcverif` is only meaningful next to the same package firing with it, so
that silence is shown to come from the switch, not from a broken rule.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands.check import run_structured as check_run_structured

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "weakeners"

JENA_AVAILABLE = shutil.which("java") is not None and paths.jar_path().exists()
pytestmark = pytest.mark.skipif(not JENA_AVAILABLE, reason="weakener engine JAR not built")

CASES: list[tuple[str, str, set[str]]] = [
    # (pattern_id, variant, W-CV ids expected with --calcverif)
    ("W-CV-01", "positive", {"W-CV-01"}),
    ("W-CV-01", "negative", set()),   # reported index agrees
    ("W-CV-01", "boundary", set()),   # not-comparable: only diverges may fire
    ("W-CV-02", "positive", {"W-CV-02"}),
    ("W-CV-02", "negative", set()),   # the tool computed an estimate
    ("W-CV-02", "boundary", set()),   # not-run: the assessor's gap, not the record's
    ("W-CV-03", "positive", {"W-CV-03"}),
    ("W-CV-03", "negative", set()),   # order within 10% of formal
    ("W-CV-03", "boundary", set()),   # no formal order declared
    ("W-CV-04", "positive", {"W-CV-04"}),
    ("W-CV-04", "negative", set()),   # every triplet converges monotonically
    ("W-CV-04", "boundary", set()),   # factor not assessed
]


def _check(path: Path, *, on=False, off=False):
    args = argparse.Namespace(
        file=path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, raw=False, format="jsonld", output=None, strict=False,
        no_color=True, verbose=False, repo_root=None, explain=None,
        active_packs=["vv40"], enable_calcverif=on, disable_calcverif=off,
    )
    return check_run_structured(args)


def _ids(result) -> set[str]:
    assert result.rules is not None, result.rules_error
    return {f.get("patternId") or f.get("pattern_id") for f in result.rules.firings}


def _cv(ids: set[str]) -> set[str]:
    return {i for i in ids if i.startswith("W-CV-")}


def _variant(tmp_path, pid, variant, mutate):
    """A copy of a fixture with one change, written beside a context link."""
    doc = json.loads((FIXTURES / pid / f"{variant}.jsonld").read_text())
    mutate(doc)
    doc["@context"] = str((REPO_ROOT / "spec" / "context" / "v0.5.jsonld").resolve())
    out = tmp_path / f"{pid}-{variant}-variant.jsonld"
    out.write_text(json.dumps(doc, indent=2))
    return out


@pytest.mark.parametrize("pid, variant, expected", CASES,
                         ids=[f"{p}-{v}" for p, v, _ in CASES])
def test_rule_fires_as_expected(pid, variant, expected):
    assert _cv(_ids(_check(FIXTURES / pid / f"{variant}.jsonld", on=True))) == expected


@pytest.mark.parametrize("pid", ["W-CV-01", "W-CV-02", "W-CV-03", "W-CV-04"])
def test_silent_without_the_switch_and_with_it_off(pid):
    """Null control: the positive fixture, rules not loaded -> no W-CV, and the
    rest of C3 is exactly what it is with the switch on, minus the W-CV id."""
    path = FIXTURES / pid / "positive.jsonld"
    on, default, off = _ids(_check(path, on=True)), _ids(_check(path)), _ids(_check(path, off=True))
    assert _cv(on) == {pid}
    assert _cv(default) == set() and _cv(off) == set()
    assert on - {pid} == default == off


def test_no_reported_value_cannot_fire_w_cv_01(tmp_path):
    def drop_reported(doc):
        rec = doc["calculationVerification"][0]
        for key in ("cvReportedGci", "cvGciComparison", "cvGciComparisonDetail"):
            rec.pop(key, None)
    path = _variant(tmp_path, "W-CV-01", "positive", drop_reported)
    assert "W-CV-01" not in _ids(_check(path, on=True))


def test_factor_not_assessed_silences_every_rule(tmp_path):
    for pid in ("W-CV-01", "W-CV-02", "W-CV-03", "W-CV-04"):
        def unassess(doc):
            doc["hasCredibilityFactor"][0]["factorStatus"] = "not-assessed"
        path = _variant(tmp_path, pid, "positive", unassess)
        assert _cv(_ids(_check(path, on=True))) == set(), pid


def test_study_for_another_factor_does_not_bind(tmp_path):
    def other_factor(doc):
        doc["calculationVerification"][0]["forFactorType"] = "Numerical solver error"
    path = _variant(tmp_path, "W-CV-01", "positive", other_factor)
    assert _cv(_ids(_check(path, on=True))) == set()


def _vv40_examples():
    return sorted((REPO_ROOT / "packs" / "vv40" / "examples").rglob("*.jsonld"))


@pytest.mark.parametrize("example", _vv40_examples(), ids=lambda p: p.parent.name + "/" + p.name)
def test_switch_changes_nothing_on_shipped_examples(example):
    """None of them carries a mesh study, so the switch must not move C3."""
    with_flag = _check(example, on=True)
    without = _check(example)
    assert _ids(with_flag) == _ids(without)
    assert [f.get("hits") for f in with_flag.rules.firings] == \
           [f.get("hits") for f in without.rules.firings]
    assert without.calcverif_rules is None
    assert with_flag.calcverif_rules == ["vv40/rules/calcverif/calcverif_v0.1.rules"]


# ── Through the CLI: readout, errors before work ────────────────────────────


def _uofa(*args, cwd=REPO_ROOT):
    return subprocess.run([sys.executable, "-m", "uofa_cli.cli", "--no-color", *args],
                          cwd=cwd, capture_output=True, text=True)


def test_cli_readout_names_the_switch_only_when_on():
    path = str(FIXTURES / "W-CV-01" / "positive.jsonld")
    on = _uofa("check", path, "--pack", "vv40", "--calcverif")
    off = _uofa("check", path, "--pack", "vv40")
    assert "W-CV-01" in on.stdout and "calculation-verification rules on" in on.stdout
    assert "W-CV-01" not in off.stdout and "calculation-verification" not in off.stdout


def test_cli_both_flags_refused_before_work():
    path = str(FIXTURES / "W-CV-01" / "positive.jsonld")
    both = _uofa("check", path, "--calcverif", "--no-calcverif")
    assert both.returncode != 0 and "not allowed with" in both.stderr
    assert "C2: SHACL" not in both.stdout


def test_cli_flag_on_a_pack_without_the_block_stops_before_work():
    path = str(FIXTURES / "W-CV-01" / "positive.jsonld")
    res = _uofa("check", path, "--pack", "nasa-7009b", "--calcverif")
    assert res.returncode != 0
    assert "does not declare" in res.stdout + res.stderr
    assert "C2: SHACL" not in res.stdout


def test_cli_import_flag_needs_check(tmp_path):
    template = REPO_ROOT / "packs" / "vv40" / "templates" / "uofa-starter-filled.xlsx"
    res = _uofa("import", str(template), "-o", str(tmp_path / "x.jsonld"), "--calcverif")
    assert res.returncode == 2
    assert "add --check" in res.stdout + res.stderr
    assert not (tmp_path / "x.jsonld").exists()
