"""`uofa report`: deterministic credibility report from a bundle.

Source-grounded — runs the real rule engine + SHACL on the Morrison bundles, so
the numbers are the bundle's ground truth (its actual factorStatus), not the
demo Space's illustrative fixture statuses. Asserts the validation/COU-scoped
concerns demote the factor they implicate, that the six invariants hold, and
that the three render formats work.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands import report
from uofa_cli.report_state import Status, build_report_state

_ROOT = paths.find_repo_root()
_COU = {c: _ROOT / f"packs/vv40/examples/morrison/{c}/uofa-morrison-{c}.jsonld"
        for c in ("cou1", "cou2")}


def _args(file, fmt="text", output=None, pack="vv40"):
    # `report` now takes a positional `source` (a bundle path, an HF id, or a URL)
    # plus the id-mode flags; a .jsonld path routes to the unchanged file mode.
    return argparse.Namespace(source=str(file), format=fmt, output=output,
                              active_packs=[pack], pack=[pack], repo_root=None,
                              deterministic=False, revision=None, save_bundle=None,
                              no_save_bundle=False, extract_backend=None,
                              extract_model=None, extract_base_url=None)


def _state(cou):
    """Build the ReportState the command would render (no I/O)."""
    bundle = json.loads(_COU[cou].read_text(encoding="utf-8"))
    shacl = report._shacl(_COU[cou], "vv40")
    firings = report._firings(_COU[cou], "vv40")
    from uofa_cli.report_state import compute_findings
    analysis = compute_findings("vv40", report._factor_statuses(bundle), shacl, firings)
    analysis["context"] = report._context(bundle, "vv40")
    return build_report_state(analysis)


# ── ground-truth numbers (both Morrison bundles: 7 assessed in the JSON-LD) ──

@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_completeness_reflects_bundle_and_demotions(cou):
    s = _state(cou)
    # 7 assessed in the bundle; Output comparison + Relevance-to-COU are demoted
    # by their concerns -> 5 evidenced of 13 = 38%.
    assert s.n_expected == 13
    assert s.n_evidenced == 5
    assert s.completeness_pct == 38
    assert not s.required_all_accounted


@pytest.mark.parametrize("cou,prov_pattern", [("cou1", "W-AR-05"), ("cou2", "W-PROV-01")])
def test_output_comparison_demoted_by_its_concern(cou, prov_pattern):
    s = _state(cou)
    oc = next(f for f in s.factors if f.name == "Output comparison")
    assert oc.status is Status.NOT_STATED
    assert prov_pattern in oc.targeting_weakeners


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_cou_relevance_demoted_by_unbounded_envelope(cou):
    s = _state(cou)
    rel = next(f for f in s.factors if f.name == "Relevance of the validation activities to the COU")
    assert rel.status is Status.NOT_STATED
    assert "W-ON-02" in rel.targeting_weakeners


# ── the command runs end to end in every format ──

@pytest.mark.parametrize("fmt", ["text", "markdown", "json"])
def test_report_runs_and_writes(tmp_path, fmt):
    out = tmp_path / f"report.{fmt}"
    rc = report.run(_args(_COU["cou2"], fmt=fmt, output=out))
    assert rc == 0
    body = out.read_text(encoding="utf-8")
    if fmt == "json":
        payload = json.loads(body)
        assert payload["completeness_pct"] == 38
        # the semantic focus is carried on the concern in the machine output
        prov = next(c for c in payload["concerns"] if c["pattern_id"] == "W-PROV-01")
        assert prov["factors"] == ["Output comparison"]
    else:
        assert "Output comparison" in body
        assert "38%" in body


# ── guard: a non-evidence file is rejected, not silently 0% ──

def test_rejects_file_without_factors(tmp_path):
    dump = tmp_path / "reasoned.jsonld"
    dump.write_text(json.dumps({"@graph": [{"@id": "_:b0",
                    "https://uofa.net/vocab#patternId": "COMPOUND-01"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="No credibility factors"):
        report.run(_args(dump))
