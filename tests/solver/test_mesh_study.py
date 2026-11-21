"""The calcverif wrapper: declaration, statuses, recovery, comparison, readout.

Studies run through the production path: the tables are sealed with
`seal.seal_folder`, and `run_studies` gets the digests the seal recorded.
Every record any test produces is scanned for decision words, keys and values,
including the captured tool output.

Expected numbers come from upstream's own test file (see
tests/fixtures/mesh_study/README.md), never from this wrapper.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
from uofa_cli.solver import mesh_study as ms
from uofa_cli.solver import seal as sealmod
from uofa_cli.weakener_focus import attributable_factors

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mesh_study"
FACTOR = "Discretization error"
TOL = 1e-12
PINNED_TOOL_SHA256 = "e4ddc15558ce64c8c55253c4d7efc7c6679f52e47dc0e740f42872c33bef5a5d"

# The spec's quantityIdentity entry (spec v0.3, section 5.5). G4 puts it in the
# vv40 manifest; tests that read it from the pack live with the rules tests.
SPEC_IDENTITY = {ms.GCI_RELATIVE: {"canonicalUnit": "fraction", "tolerance": 0.25,
                                   "units": {"fraction": 1.0, "%": 0.01}}}

DECISION_WORDS = re.compile(
    r"\b(pass|passed|passes|fail|failed|fails|failure|accept|accepted|"
    r"converged|validated)\b", re.IGNORECASE)

needs_tool = pytest.mark.usefixtures("tool_installed")


@pytest.fixture
def tool_installed():
    pytest.importorskip("matplotlib")


def _study(table, *, sid="s1", column="qoi", refinement="mesh_size",
           kind=ms.MESH_SIZE, dimension=None, formal=None, reported=None,
           units=None, **extra):
    ref = {"column": refinement, "kind": kind}
    if dimension is not None:
        ref["dimension"] = dimension
    study = {"id": sid, "forFactorType": FACTOR, "table": table,
             "quantityColumn": column, "refinement": ref}
    if units is not None:
        study["quantityUnits"] = units
    if formal is not None:
        study["formalOrder"] = formal
    if reported is not None:
        study["reported"] = reported
    study.update(extra)
    return study


def _declare(tmp_path, *studies, schema=ms.SCHEMA):
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "study.json"
    path.write_text(json.dumps({"schemaVersion": schema, "studies": list(studies)}))
    return ms.load_declaration(path, attributable_factors("vv40"))


def _evidence(tmp_path, *tables):
    root = tmp_path / "evidence"
    root.mkdir(exist_ok=True)
    for name in tables:
        shutil.copy(FIXTURES / name, root / name)
    return root


def _run(tmp_path, *studies, tables=None, identity=SPEC_IDENTITY):
    decls = _declare(tmp_path, *studies)
    root = _evidence(tmp_path, *(tables if tables is not None else {s["table"] for s in studies}))
    seal = sealmod.seal_folder(root)
    records = ms.run_studies(decls, root, ms.sealed_digests(seal), identity)
    for record in records:
        _assert_no_decision_words(record)
    return records


def _assert_no_decision_words(record):
    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                assert key not in FORBIDDEN_TOKENS, f"{path}.{key}"
                assert not DECISION_WORDS.search(key), f"{path}.{key}"
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
        elif isinstance(node, str):
            hit = DECISION_WORDS.search(node)
            assert hit is None, f"decision word {hit.group(0)!r} at {path}"
    walk(record, "record")


def _close(a, b):
    return abs(float(a) - float(b)) <= TOL


# ── Declaration ─────────────────────────────────────────────────────────────


def test_declaration_round_trip(tmp_path):
    rep = {"value": 0.3, "units": "%", "basis": "relative", "source": "Table 3"}
    [d] = _declare(tmp_path, _study("t.csv", formal=2.0, units="m/s", reported=rep))
    assert (d.id, d.for_factor_type, d.table, d.refinement_kind) == ("s1", FACTOR, "t.csv", ms.MESH_SIZE)
    assert d.formal_order == 2.0 and d.quantity_units == "m/s"
    assert d.reported == ms.Reported(0.3, "%", "relative", "Table 3")


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s.update(formalorder=2.0), "unknown key"),          # a typo must not mean "absent"
    (lambda s: s.update(forFactorType="Mesh quality"), "not a factor"),
    (lambda s: s.update(table="/abs/t.csv"), "relative"),
    (lambda s: s.update(table="../t.csv"), "relative"),
    (lambda s: s.update(formalOrder=0), "formalOrder"),
    (lambda s: s.update(formalOrder=True), "formalOrder"),
    (lambda s: s["refinement"].update(kind="cells"), "kind"),
    (lambda s: s["refinement"].update(kind=ms.ELEMENT_COUNT), "dimension"),
    (lambda s: s["refinement"].update(dimension=3), "dimension"),
    (lambda s: s.update(reported={"value": 1, "units": "%", "basis": "both"}), "basis"),
    (lambda s: s.update(reported={"value": "0.3", "units": "%", "basis": "relative"}), "value"),
    (lambda s: s.update(reported={"value": 1, "units": "%", "basis": "relative", "note": 1}), "unknown key"),
])
def test_malformed_declaration_is_an_error(tmp_path, mutate, message):
    study = _study("t.csv")
    mutate(study)
    with pytest.raises(ms.MeshStudyDeclarationError, match=message):
        _declare(tmp_path, study)


def test_declaration_rejects_wrong_schema_and_duplicates(tmp_path):
    with pytest.raises(ms.MeshStudyDeclarationError, match="schemaVersion"):
        _declare(tmp_path, _study("t.csv"), schema="uofa-mesh-study/v9")
    with pytest.raises(ms.MeshStudyDeclarationError, match="duplicate"):
        _declare(tmp_path, _study("t.csv"), _study("u.csv"))


# ── computed: upstream oracles ──────────────────────────────────────────────


@needs_tool
def test_n3_within_tolerance_matches_upstream(tmp_path):
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0))
    assert r["cvStatus"] == ms.COMPUTED and r["cvMethod"] == "N3_mono"
    assert r["cvConvergenceType"] == "monotonic-convergence"
    assert _close(r["cvObservedOrder"], 1.0) and _close(r["cvRichardsonValue"], 1.0)
    assert _close(r["cvGciAbsolute"], 1.25) and _close(r["cvGciRelative"], 0.625)
    assert r["cvSafetyFactor"] == 1.25 and r["cvOrderAgreement"] == ms.WITHIN
    assert r["cvConstrainedOrder"] == 1.0
    assert r["cvFormalOrder"] == 1.0
    assert "cvTriplet" not in r and "cvTripletConcern" not in r


@needs_tool
def test_n3_outside_tolerance_matches_upstream(tmp_path):
    [r] = _run(tmp_path, _study("upstream_n3_order3.csv", formal=1.0))
    assert _close(r["cvObservedOrder"], 3.0)
    assert _close(r["cvRichardsonValue"], 1.4805) and _close(r["cvGciAbsolute"], 0.06825)
    assert r["cvSafetyFactor"] == 3.0 and r["cvOrderAgreement"] == ms.OUTSIDE


@pytest.mark.parametrize("table, formal, absolute, fs", [
    ("upstream_n3_const_r.csv", 1.0, 1.25, 1.25),
    ("upstream_n3_const_r.csv", 1.0, 1.25, 1.25),      # relative oracle row; Fs comes from the absolute run
    ("upstream_n3_order3.csv", 1.0, 0.06825, 3.0),
])
@needs_tool
def test_safety_factor_recovered_on_every_oracle(tmp_path, table, formal, absolute, fs):
    [r] = _run(tmp_path, _study(table, formal=formal))
    assert _close(r["cvGciAbsolute"], absolute)
    assert r["cvSafetyFactor"] == fs


@needs_tool
def test_element_counts_sorted_finest_first_and_order_recorded(tmp_path):
    [r] = _run(tmp_path, _study("upstream_elements_unsorted.csv", refinement="element_count",
                                kind=ms.ELEMENT_COUNT, dimension=3, formal=1.0))
    assert [lv["cvRefinement"] for lv in r["cvLevel"]] == [64000, 8000, 1000]
    assert [lv["cvSourceRow"] for lv in r["cvLevel"]] == [2, 3, 1]
    assert [lv["cvIndex"] for lv in r["cvLevel"]] == [0, 1, 2]
    assert r["cvDimension"] == 3 and r["cvRefinementKind"] == ms.ELEMENT_COUNT
    assert _close(r["cvObservedOrder"], 1.0) and _close(r["cvGciAbsolute"], 1.25)
    assert r["cvSafetyFactor"] == 1.25


@needs_tool
def test_absent_formal_order_stays_absent(tmp_path):
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv"))
    assert "cvFormalOrder" not in r
    assert r["cvOrderAgreement"] == ms.NO_FORMAL
    assert r["cvSafetyFactor"] == 3.0       # the tool's choice with no formal order


@needs_tool
def test_absent_reported_value_means_no_comparison(tmp_path):
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0))
    assert "cvReportedGci" not in r and "cvGciComparison" not in r
    assert "cvGciComparisonDetail" not in r


@needs_tool
def test_tool_provenance_pinned_and_source_hashed_at_read(tmp_path):
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0))
    assert r["cvToolSha256"] == PINNED_TOOL_SHA256
    assert r["cvToolCommit"] == ms.TOOL_COMMIT and r["cvTool"] == ms.TOOL_NAME
    import hashlib
    expected = "sha256:" + hashlib.sha256((FIXTURES / "upstream_n3_const_r.csv").read_bytes()).hexdigest()
    assert r["cvSourceSha256"] == expected


@needs_tool
def test_least_squares_path(tmp_path):
    [r] = _run(tmp_path, _study("upstream_least_squares.csv", formal=3.0))
    assert r["cvStatus"] == ms.COMPUTED and r["cvMethod"] == "least_squares"
    assert r["cvConvergenceType"] == "oscillatory-convergence"
    assert r["cvSafetyFactor"] in (1.25, 3.0)
    assert "cvTriplet" not in r and "cvTripletConcern" not in r


@needs_tool
def test_large_n_triplet_concern(tmp_path):
    [r] = _run(tmp_path, _study("upstream_largeN_triplet_concern.csv", formal=1.0))
    assert r["cvMethod"] == "largeN_mono"
    assert len(r["cvTriplet"]) == 4
    assert r["cvTriplet"][-1]["cvConvergence"] != "converging (monotonic)"
    assert "cvObservedOrder" not in r["cvTriplet"][-1]      # the tool left it empty
    assert r["cvTripletConcern"] == "true"
    # upstream: the first triplet row equals the returned result
    assert _close(r["cvTriplet"][0]["cvGciAbsolute"], r["cvGciAbsolute"])
    assert _close(r["cvTriplet"][1]["cvGciAbsolute"], 2.5)


@needs_tool
def test_morrison_copy_exercises_four_level_path_only(tmp_path):
    """Morrison's table drives the largeN_mono path. Nothing is compared."""
    [r] = _run(tmp_path, _study("morrison_mesh_convergence_study.csv", column="max_velocity_m_s",
                                refinement="element_count", kind=ms.ELEMENT_COUNT, dimension=3,
                                formal=2.0, units="m/s"))
    assert r["cvMethod"] == "largeN_mono" and len(r["cvLevel"]) == 4
    assert r["cvTripletConcern"] == "false"
    assert "cvReportedGci" not in r and "cvGciComparison" not in r
    # the table's own `converged` and `GCI_percent` columns are never read
    assert set(r) >= {"cvQuantity"} and r["cvQuantity"] == "max_velocity_m_s"
    assert "converged" not in json.dumps(r)


# ── no-estimate ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("table, reason", [
    ("upstream_diverging.csv", ms.DIVERGING),
    ("upstream_oscillatory.csv", ms.OSCILLATORY_THREE),
])
@needs_tool
def test_tool_refusal_is_no_estimate(tmp_path, table, reason):
    rep = {"value": 0.3, "units": "%", "basis": "relative"}
    [r] = _run(tmp_path, _study(table, formal=1.0, reported=rep))
    assert r["cvStatus"] == ms.NO_ESTIMATE and r["cvReason"] == reason
    assert r["cvMethod"] == "cannot_run"
    for key in ("cvObservedOrder", "cvGciAbsolute", "cvGciRelative", "cvSafetyFactor",
                "cvOrderAgreement", "cvGciComparison"):
        assert key not in r
    assert r["cvReportedGci"]["cvValue"] == 0.3     # the declaration is still recorded


# ── not-run ─────────────────────────────────────────────────────────────────


def test_table_not_in_seal(tmp_path):
    decls = _declare(tmp_path, _study("upstream_n3_const_r.csv"))
    root = _evidence(tmp_path)          # empty folder: nothing sealed
    [r] = ms.run_studies(decls, root, ms.sealed_digests(sealmod.seal_folder(root)), SPEC_IDENTITY)
    assert (r["cvStatus"], r["cvReason"]) == (ms.NOT_RUN, ms.TABLE_NOT_SEALED)
    assert "cvSourceSha256" not in r and "cvTool" not in r


def test_bytes_changed_after_seal_do_not_run(tmp_path):
    decls = _declare(tmp_path, _study("upstream_n3_const_r.csv"))
    root = _evidence(tmp_path, "upstream_n3_const_r.csv")
    digests = ms.sealed_digests(sealmod.seal_folder(root))
    (root / "upstream_n3_const_r.csv").write_text("mesh_size,qoi\n0.1,2.0\n0.2,3.0\n0.4,9.0\n")
    [r] = ms.run_studies(decls, root, digests, SPEC_IDENTITY)
    assert (r["cvStatus"], r["cvReason"]) == (ms.NOT_RUN, ms.TABLE_NOT_SEALED)
    assert "not the bytes the seal recorded" in r["cvReasonDetail"]


@pytest.mark.parametrize("table, column, reason", [
    ("synthetic_non_numeric.csv", "qoi", ms.INVALID_INPUT),
    ("upstream_n3_const_r.csv", "pressure", ms.INVALID_INPUT),
    ("synthetic_two_levels.csv", "qoi", ms.TOO_FEW_LEVELS),
])
def test_unusable_table_does_not_run(tmp_path, table, column, reason):
    [r] = _run(tmp_path, _study(table, column=column))
    assert (r["cvStatus"], r["cvReason"]) == (ms.NOT_RUN, reason)
    assert "cvTool" not in r and "cvObservedOrder" not in r


@needs_tool
def test_tool_value_error_is_invalid_input_with_its_message(tmp_path):
    [r] = _run(tmp_path, _study("upstream_equal_neighbours.csv"))
    assert (r["cvStatus"], r["cvReason"]) == (ms.NOT_RUN, ms.INVALID_INPUT)
    assert "Two consecutive values in qoi_values are equal" in r["cvReasonDetail"]
    assert r["cvToolSha256"] == PINNED_TOOL_SHA256      # the tool did run


def test_dependency_missing_is_a_recorded_state(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    monkeypatch.delitem(sys.modules, "uofa_cli._vendor.simeval.calcverif", raising=False)
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0))
    assert (r["cvStatus"], r["cvReason"]) == (ms.NOT_RUN, ms.DEPENDENCY_MISSING)
    assert ms.INSTALL_HINT in r["cvReasonDetail"]
    assert "cvTool" not in r and "cvToolSha256" not in r
    assert any(ms.INSTALL_HINT in line for line in ms.summarise([r]))


# ── comparison ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value, verdict", [
    (60.0, "agrees"),
    (46.875, "agrees"),     # exactly 25% below 0.625: the tolerance edge, inclusive
    (46.8, "diverges"),     # just past it
    (0.3, "diverges"),
])
@needs_tool
def test_relative_comparison_against_recomputed_index(tmp_path, value, verdict):
    rep = {"value": value, "units": "%", "basis": "relative", "source": "synthetic"}
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0, reported=rep))
    assert _close(r["cvGciRelative"], 0.625)
    assert r["cvGciComparison"] == verdict
    if verdict == "diverges":
        assert "tolerance 25.0%" in r["cvGciComparisonDetail"]
    assert r["cvReportedGci"] == {"cvValue": value, "cvUnits": "%", "cvBasis": "relative",
                                  "cvSource": "synthetic"}


@needs_tool
def test_comparison_not_comparable_cases(tmp_path):
    odd_units = {"value": 6.0, "units": "permille", "basis": "relative"}
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0, reported=odd_units))
    assert r["cvGciComparison"] == "not-comparable" and "permille" in r["cvGciComparisonDetail"]

    no_entry = {"value": 60.0, "units": "%", "basis": "relative"}
    [r] = _run(tmp_path / "b", _study("upstream_n3_const_r.csv", formal=1.0, reported=no_entry),
               identity={})
    assert r["cvGciComparison"] == "not-comparable"

    [r] = _run(tmp_path / "c", _study("synthetic_zero_finest.csv", formal=1.0, reported=no_entry))
    assert r["cvStatus"] == ms.COMPUTED and "cvGciRelative" not in r
    assert r["cvGciComparison"] == "not-comparable"
    assert "QOI on finest mesh is zero" in r["cvGciComparisonDetail"]


@needs_tool
def test_absolute_comparison_needs_identical_units(tmp_path):
    same = {"value": 1.2, "units": "m/s", "basis": "absolute"}
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0, units="m/s", reported=same))
    assert r["cvGciComparison"] == "agrees"
    other = {"value": 1.2, "units": "mm/s", "basis": "absolute"}
    [r] = _run(tmp_path / "b", _study("upstream_n3_const_r.csv", formal=1.0, units="m/s", reported=other))
    assert r["cvGciComparison"] == "not-comparable"


# ── readout and output capture ──────────────────────────────────────────────


@needs_tool
def test_readout_lines(tmp_path):
    rep = {"value": 0.3, "units": "%", "basis": "relative"}
    recs = _run(tmp_path,
                _study("upstream_n3_order3.csv", sid="a", formal=1.0, reported=rep),
                _study("upstream_diverging.csv", sid="b"),
                _study("synthetic_two_levels.csv", sid="c"))
    text = "\n".join(ms.summarise(recs))
    assert f"a ({FACTOR}): computed, method N3_mono" in text
    assert "formal order 1 (outside tolerance), safety factor 3" in text
    assert "reported 0.3 % relative (diverges)" in text
    assert f"b ({FACTOR}): no estimate (diverging)" in text
    assert f"c ({FACTOR}): not run (too-few-levels)" in text
    assert DECISION_WORDS.search(text) is None


@needs_tool
def test_tool_output_captured_and_cut(tmp_path, monkeypatch):
    [r] = _run(tmp_path, _study("upstream_n3_const_r.csv", formal=1.0))
    assert "Method: standard method" in r["cvToolOutput"]
    assert "cvToolOutputTruncated" not in r
    monkeypatch.setattr(ms, "OUTPUT_LIMIT", 20)
    [r] = _run(tmp_path / "b", _study("upstream_n3_const_r.csv", formal=1.0))
    assert len(r["cvToolOutput"]) == 20 and r["cvToolOutputTruncated"] == "true"
