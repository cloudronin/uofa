"""What the iso42001 bundles report today, pinned before the pack changes.

The ISO 42001 work ahead rewrites this pack's vocabulary, shapes and mapper.
The existing tests check that each calibration package fires its own OOS rule
and that COU2 fires more than COU1. Neither would notice a weakener appearing,
vanishing or doubling. So every bundle's full `uofa check` report -- SHACL
result, weakener firings with their hit counts, OOS firings -- is committed
here, and a change to any of it is a diff someone has to look at.

Pinned as-is, including what is known to be wrong: COU1 and COU2 fire OOS rules
for a reason the rules were not written for (their evidence links are plain
strings, not IRIs), and every bundle fires the core CM&S weakeners, which
describe simulation credibility rather than a management system. Those are
recorded as today's baseline, not endorsed.

**The one date dependency.** COU2's audit record has an annual cadence and was
dated 2026-03-25, and `_auditOverdue` compares it with SPARQL `NOW()`. From
2027-03-25 COU2 would fire W-AIMS-AUDIT-STALE, and COMPOUND-01 would count it
once more. A baseline taken from the file as it stands would start failing on
that day for no change to anything. So COU2 is run from a copy whose audit date
is set relative to today -- once not yet due, once overdue -- and the report
never depends on the calendar. The copy changes that one date and nothing else.

Regenerate after an intended change, then read the diff:

    python tests/test_iso42001_baselines.py --regen
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from uofa_cli.commands.check import run_structured
from uofa_cli.oos.snapshot import to_json

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINES = REPO_ROOT / "tests/fixtures/baseline_reports/iso42001"
HYBRID = REPO_ROOT / "packs/iso42001/examples/hybrid"
PACKAGES = REPO_ROOT / "specs/calibration/packages"
COU2 = HYBRID / "cou2/uofa-iso42001-cou2.jsonld"
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"

needs_jar = pytest.mark.skipif(
    not (shutil.which("java") and JAR.exists()), reason="java + built JAR required")

AUDIT_DATE = "https://uofa.net/vocab/aims#auditDate"
AUDIT_CADENCE = "https://uofa.net/vocab/aims#auditCadence"
COU2_AUDIT = f'"{AUDIT_DATE}": "2026-03-25T00:00:00Z"'


def bundles() -> list[Path]:
    """Every iso42001 bundle this repo ships: the two COU examples and the
    calibration packages."""
    return (sorted(HYBRID.glob("cou*/*.jsonld"))
            + sorted(PACKAGES.glob("cal-aims-*.jsonld")))


def _args(path: Path) -> argparse.Namespace:
    """The default configuration: iso42001 active, OOS on by pack config."""
    return argparse.Namespace(
        file=path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, enable_oos=False, disable_oos=False, no_color=True,
        verbose=False, repo_root=None, pack=["iso42001"], active_packs=["iso42001"])


def report(path: Path, work: Path, *, overdue: bool = False) -> str:
    """The stable `uofa check` report for one bundle.

    One function for the test and for `--regen`, so the two cannot drift.
    COU2 runs from a copy under `work`, at the same relative path, with its
    audit date moved relative to today; the copy's location is written back
    as the real file's, so the report reads exactly as the real file's would.
    """
    if path != COU2:
        return to_json(run_structured(_args(path)), repo_root=REPO_ROOT) + "\n"
    copy = dated_cou2(work, overdue=overdue)
    out = to_json(run_structured(_args(copy)), repo_root=REPO_ROOT) + "\n"
    return out.replace(copy.as_posix(), COU2.relative_to(REPO_ROOT).as_posix())


def dated_cou2(work: Path, *, overdue: bool) -> Path:
    """COU2 with its audit dated one day ago, or 400 days ago; nothing else
    changed. Written under `work` at COU2's own relative path."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    when = now - timedelta(days=400 if overdue else 1)
    text = COU2.read_text(encoding="utf-8")
    assert text.count(COU2_AUDIT) == 1, "COU2's audit date moved; update COU2_AUDIT"
    copy = work / COU2.relative_to(REPO_ROOT)
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_text(text.replace(
        COU2_AUDIT, f'"{AUDIT_DATE}": "{when.strftime("%Y-%m-%dT%H:%M:%SZ")}"'),
        encoding="utf-8")
    return copy


def baseline(path: Path) -> Path:
    return BASELINES / f"{path.stem}.json"


# ── the reports ──────────────────────────────────────────────────────────────

@needs_jar
@pytest.mark.parametrize("path", bundles(), ids=lambda p: p.stem)
def test_each_bundle_reports_what_it_reported(path, tmp_path):
    fresh, pinned = report(path, tmp_path), baseline(path).read_text(encoding="utf-8")
    if fresh != pinned:
        diff = "".join(difflib.unified_diff(
            pinned.splitlines(True), fresh.splitlines(True),
            "baseline", "now", n=2))
        pytest.fail(
            f"{path.name}: the report changed. If the change is intended, run "
            f"`python tests/test_iso42001_baselines.py --regen` and commit the "
            f"diff with the change that caused it.\n{diff[:4000]}")


@needs_jar
def test_cou2_falling_due_adds_its_audit_weakener_and_nothing_else(tmp_path):
    """The date dependency, pinned as a delta, so it is stated rather than
    waited for: overdue adds W-AIMS-AUDIT-STALE once, COMPOUND-01 counts it
    once more, and nothing else moves."""
    due = json.loads(report(COU2, tmp_path / "a"))
    late = json.loads(report(COU2, tmp_path / "b", overdue=True))
    hits = lambda d: {f["patternId"]: f["hits"] for f in d["rules"]["firings"]}  # noqa: E731
    before, after = hits(due), hits(late)
    delta = {k: after.get(k, 0) - before.get(k, 0)
             for k in set(before) | set(after) if after.get(k, 0) != before.get(k, 0)}
    assert delta == {"W-AIMS-AUDIT-STALE": 1, "COMPOUND-01": 1}, delta
    assert due["oos"] == late["oos"]
    assert due["shacl"] == late["shacl"]


# ── what the pins rest on ────────────────────────────────────────────────────

def test_every_aims_bundle_has_a_baseline_and_no_baseline_is_orphaned():
    """A new calibration package that nobody pinned is a bundle whose report can
    drift unseen; a baseline whose bundle is gone pins nothing."""
    expected = {baseline(p).name for p in bundles()}
    committed = {p.name for p in BASELINES.glob("*.json")}
    assert expected == committed, (sorted(expected - committed), sorted(committed - expected))


def test_cou2_is_the_only_bundle_whose_report_depends_on_the_date():
    """`_auditOverdue` needs an audit date AND a cadence. A bundle that gains
    both reads the clock, and its baseline would start failing on a date."""
    dated = []
    for path in bundles():
        text = path.read_text(encoding="utf-8")
        if AUDIT_CADENCE in text and re.search(re.escape(AUDIT_DATE), text):
            dated.append(path)
    assert dated == [COU2], (
        f"{[p.name for p in dated]} read the clock through _auditOverdue; route "
        f"each through report()'s dated copy, as COU2 is")


def test_the_cou2_copy_changes_the_audit_date_and_nothing_else(tmp_path):
    """The copy is a stand-in for the real file; this is what licenses it."""
    real = json.loads(COU2.read_text(encoding="utf-8"))
    copy = json.loads(dated_cou2(tmp_path, overdue=True).read_text(encoding="utf-8"))

    def walk(a, b, at=""):
        if isinstance(a, dict):
            assert set(a) == set(b), at
            for k in a:
                yield from walk(a[k], b[k], f"{at}.{k}")
        elif isinstance(a, list):
            assert len(a) == len(b), at
            for i, (x, y) in enumerate(zip(a, b)):
                yield from walk(x, y, f"{at}[{i}]")
        elif a != b:
            yield at

    changed = list(walk(real, copy))
    assert len(changed) == 1 and changed[0].endswith(f".{AUDIT_DATE}"), changed


def _regen() -> None:
    import tempfile
    BASELINES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        for path in bundles():
            baseline(path).write_text(report(path, Path(work)), encoding="utf-8")
            print(f"wrote {baseline(path).relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    if sys.argv[1:] != ["--regen"]:
        sys.exit("usage: python tests/test_iso42001_baselines.py --regen")
    _regen()
