"""The vendored FDA SimEval `calcverif` module: pinned bytes, upstream's numbers.

Two claims are under test.

1. The three vendored files are byte-identical to the upstream commit. The
   digests below are the ones the build spec pinned when the commit was chosen
   (spec v0.3, section 4); they are not read back from the files. These tests
   need nothing beyond the standard library.
2. The vendored module, imported the way UofA imports it (Agg backend first,
   no display), reproduces upstream's own expected values from
   `test/test_calcverif.py` at that commit, to 1e-12. These need the
   `calcverif` extra and skip without it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import uofa_cli

VENDOR = Path(uofa_cli.__file__).parent / "_vendor" / "simeval"

PINNED = {
    "calcverif.py": "e4ddc15558ce64c8c55253c4d7efc7c6679f52e47dc0e740f42872c33bef5a5d",
    "LICENSE": "6d489af6292662d9e36d34ce49423784984a5f6e41d7b58f49b01264df59fa03",
    "fda_software_disclaimer.txt": "b8ed549f22c7bc7a7a3048e016016dac5c00a2f91f7b90a8611f32a36f788cf4",
}

TOL = 1e-12  # upstream asserts to 12 places


@pytest.mark.parametrize("name", sorted(PINNED))
def test_vendored_file_matches_pinned_digest(name):
    digest = hashlib.sha256((VENDOR / name).read_bytes()).hexdigest()
    assert digest == PINNED[name], f"{name} differs from upstream commit 4a70fd3"


@pytest.fixture(scope="module")
def calcverif():
    pytest.importorskip("matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    from uofa_cli._vendor.simeval import calcverif as module
    return module


def test_imports_headless_from_the_vendored_path(calcverif):
    import matplotlib
    assert matplotlib.get_backend().lower() == "agg"
    assert Path(calcverif.__file__).resolve() == (VENDOR / "calcverif.py").resolve()


def _close(actual, expected):
    return abs(float(actual) - float(expected)) <= TOL


# Upstream test_N3_monotonic_const_r, test_relative_GCI: h = 0.1, 0.2, 0.4.
@pytest.mark.parametrize(
    "qoi, absolute, ooc, re, gci",
    [
        ([2.0, 3.0, 5.0], True, 1.0, 1.0, 1.25 * (3.0 - 2.0) / (2**1.0 - 1)),
        ([2.0, 3.0, 5.0], False, 1.0, 1.0, 1.25 * (3.0 - 2.0) / (2 * (2**1.0 - 1))),
        ([1.50325, 1.526, 1.708], True, 3.0,
         1.50325 + (1.50325 - 1.526) / (2**1.0 - 1),
         3.0 * (1.526 - 1.50325) / (2**1.0 - 1)),
    ],
    ids=["N3-absolute", "N3-relative", "N3-observed-order-3"],
)
def test_upstream_oracle_by_mesh_size(calcverif, qoi, absolute, ooc, re, gci):
    tool = calcverif.CalculationVerificationTool(suppress_output=True, use_absolute_GCI=absolute)
    got_ooc, got_re, got_gci = tool.analyze([0.1, 0.2, 0.4], qoi, formal_order_conv=1.0)
    assert tool.method == "N3_mono"
    assert _close(got_ooc, ooc), got_ooc
    assert _close(got_re, re), got_re
    assert _close(got_gci, gci), got_gci


def test_spec_oracle_table_literals(calcverif):
    """The spec's oracle table states the third row as rounded literals."""
    tool = calcverif.CalculationVerificationTool(suppress_output=True, use_absolute_GCI=True)
    ooc, re, gci = tool.analyze([0.1, 0.2, 0.4], [1.50325, 1.526, 1.708], formal_order_conv=1.0)
    assert _close(ooc, 3.0) and _close(re, 1.4805) and _close(gci, 0.06825)


# Upstream test_analyze_by_n_elems, first case: unstructured meshes by element count.
def test_upstream_oracle_by_element_count(calcverif):
    tool = calcverif.CalculationVerificationTool(suppress_output=True, use_absolute_GCI=True)
    ooc, re, gci = tool.analyze_by_n_elems([64000, 8000, 1000], 3, [2.0, 3.0, 5.0], formal_order_conv=1.0)
    assert tool.method == "N3_mono"
    assert _close(ooc, 1.0) and _close(re, 1.0) and _close(gci, 1.25)


# Upstream test_when_divergent_oscillating: the tool refuses with three Nones.
@pytest.mark.parametrize(
    "h, qoi",
    [([0.1, 0.2, 0.4], [1.0, 2.0, 1.5]), ([0.1, 0.2, 0.4], [1.0, 0.8, 2.0])],
    ids=["diverging", "oscillatory-three-meshes"],
)
def test_upstream_refusals_return_three_nones(calcverif, h, qoi):
    tool = calcverif.CalculationVerificationTool(suppress_output=True)
    assert tool.analyze(h, qoi) == (None, None, None)
    assert tool.method == "cannot_run"
