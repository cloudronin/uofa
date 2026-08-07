"""The renderer has to produce the faults, and the reader has to survive them.

Every test that compiles is marked slow-ish but kept: the point of this file is
that the generated PDFs become the regression tests the five reader fixes never
had, and a renderer that quietly stops producing a pathology would retire one of
those tests without anyone noticing.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

pytest.importorskip("pdfplumber")

import latex_render as L  # noqa: E402

needs_tex = pytest.mark.skipif(shutil.which("pdflatex") is None,
                               reason="pdflatex not installed")


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    if shutil.which("pdflatex") is None:
        pytest.skip("pdflatex not installed")
    out = tmp_path_factory.mktemp("tex") / "paper.pdf"
    return L.measure(L.compile_pdf(L.render(L.demo_spec(0)), out))


# ----------------------------------------------------------------- escaping

@pytest.mark.parametrize("raw,must_contain", [
    ("40% of samples", r"40\%"),
    ("a & b", r"a \& b"),
    ("x_i and y_j", r"x\_i"),
    ("cost is $40", r"\$40"),
    ("set {a, b}", r"\{a, b\}"),
    ("C:\\path", r"\textbackslash{}"),
    ("#3 of 5", r"\#3"),
])
def test_prose_escaping(raw, must_contain):
    assert must_contain in L.sanitize(raw)


def test_sanitize_is_unconditional_not_heuristic():
    r"""Prose containing something that LOOKS like markup is still prose.

    An earlier version tried to preserve `\command{...}` inside model text, which
    made it impossible to distinguish a stray brace from a real one -- and it
    escaped the renderer's own tabular column spec, so the document stopped
    compiling. Now the caller guarantees no markup, so everything is escaped.
    """
    out = L.sanitize(r"we set \alpha{3} to 5")
    assert r"\textbackslash{}alpha\{3\}" in out
    assert L.validate(out) == []


def test_renderer_markup_is_not_re_escaped():
    """The bug that stopped the demo compiling: the table's own column spec."""
    body = L.factor_table([("Model form", "2", "prose")], "Caption")
    assert r"\begin{tabular}{p{0.30\linewidth}cp{0.42\linewidth}}" in body
    assert r"\{p\{" not in body


def test_hostile_content_still_validates():
    """Model output that would previously have silently corrupted the document."""
    nasty = "unmatched } and { plus $ and 100% & more \\ ~ ^ #"
    spec = dict(L.demo_spec(0))
    spec["body"] = L.section("Results", [nasty])
    assert L.validate(L.render(spec)) == []


def test_validate_catches_structural_damage():
    assert "unbalanced $" in L.validate(r"\section{a} $x")
    assert any("unclosed" in m for m in L.validate(r"\section{a"))
    assert any("tabular" in m for m in L.validate(r"\begin{tabular}{c} x"))


# ---------------------------------------------------------------- pathologies

@needs_tex
def test_paper_compiles_and_is_not_too_clean(rendered):
    assert L.check(rendered) == [], "generated paper missing required pathologies"


@needs_tex
def test_two_column_layout_is_detected(rendered):
    """Feeds the gutter detector, which 12 of 13 evidence spans once died to."""
    assert rendered["two_col_pages"] >= L.TARGETS["two_col_pages"]


@needs_tex
def test_hyphenation_is_present_but_not_excessive(rendered):
    """Two-sided: 15% is as wrong as 0%. Real papers span 0.7-8.3% per paper.

    The floor only asks whether hyphenation happened. It deliberately sits below
    elemance's 0.007, because a per-paper criterion that rejects real documents
    -- as a 0.040 floor did, failing two of the five -- is measuring the wrong
    thing. corpus_profile's band on the corpus mean is what checks the rate.
    """
    assert rendered["hyphen_lines"] >= L.TARGETS["hyphen_lines"]
    assert rendered["hyphen_lines"] <= L.CEILINGS["hyphen_lines"]


@pytest.mark.parametrize("rate", [0.083, 0.070, 0.059, 0.026, 0.007])
def test_every_real_paper_would_pass_the_per_paper_floor(rate):
    """The five real per-paper rates. A floor above any of them is wrong."""
    assert L.check({**{k: 1e9 for k in L.TARGETS}, "hyphen_lines": rate,
                    "run_together": 0.0}) == []


@needs_tex
def test_rubric_definitions_survive_as_standalone_sentences(rendered):
    """The fifth pathology, found only in Nagaraja (45 of them)."""
    assert rendered["rubric_sents"] >= L.TARGETS["rubric_sents"]


@needs_tex
def test_inter_word_spaces_are_lost_by_default_and_recovered_by_the_reader(rendered):
    """The regression test for x_tolerance=1.2, over which two real documents
    were nearly discarded.

    Both halves matter. A paper that reads cleanly at the DEFAULT tolerance never
    exercised the fix; a paper still broken after it means the fix stopped
    working. Real APL PDFs: ~10-11% before, 0.02% after.
    """
    assert rendered["run_together_default"] >= L.TARGETS["run_together_default"]
    assert rendered["run_together"] <= L._MAX_AFTER_FIX


@needs_tex
def test_check_reports_a_too_clean_paper(rendered):
    """`check` must fail a paper that lost a pathology, not shrug."""
    clean = dict(rendered, rubric_sents=0, hyphen_lines=0.0)
    miss = L.check(clean)
    assert any("rubric_sents" in m for m in miss)
    assert any("hyphen_lines" in m for m in miss)
