"""Guards on the seeded generator, and the contamination rules it enforces.

Nothing here makes an API call. The expensive failures this file exists to
prevent are the cheap ones to test: a held-back document used as a seed, gold and
its agreement check from one model family, a generator that stops withholding
factors, and prose that reaches LaTeX unescaped.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

pytest.importorskip("pdfplumber")

import generate_seeded_corpus as G  # noqa: E402
import latex_render as LR  # noqa: E402

PY = sys.executable
SCRIPT = _ROOT / "dev" / "tools" / "scripts" / "generate_seeded_corpus.py"


def _run(*flags, tmp):
    return subprocess.run(
        [PY, str(SCRIPT), "--count", "2", "--output-root", str(tmp), "--dry-run",
         *flags], capture_output=True, text=True, cwd=_ROOT)


# ------------------------------------------------------------------- guards

def test_held_back_documents_cannot_seed_generation(tmp_path):
    """elemance and morrison are the measurement surface, not training input.

    They are also valid seed names, so this must not fall through to "unknown
    seed" -- which is what happened when the membership check ran first and made
    this branch unreachable.
    """
    for name in G.HELD_BACK:
        r = _run("--seeds", name, tmp=tmp_path)
        assert r.returncode == 1
        assert "held back" in r.stderr + r.stdout
        assert "unknown seed" not in r.stderr + r.stdout


def test_gold_and_agreement_must_be_different_families(tmp_path):
    """Same family twice measures determinism, not reliability."""
    r = _run("--gold-model", "gpt-5", "--agreement-model", "gpt-5", tmp=tmp_path)
    assert r.returncode == 1
    assert "same family" in r.stderr + r.stdout

    ok = _run("--gold-model", "gpt-5", "--agreement-model", "claude-sonnet-4-6",
              tmp=tmp_path)
    assert ok.returncode == 0


def test_dry_run_makes_no_network_call_and_still_proves_the_render_path(tmp_path):
    """The lesson from the sparse campaign: a guard never dry-run cost a day."""
    r = _run(tmp=tmp_path)
    assert r.returncode == 0
    assert "no API calls made" in r.stdout
    assert (tmp_path / "_dryrun" / "paper.pdf").exists()


def test_family_detection():
    assert G._family("gpt-5") == "openai"
    assert G._family("openai/gpt-5") == "openai"
    assert G._family("claude-sonnet-4-6") == "anthropic"
    assert G._family("anthropic/claude-opus-4-7") == "anthropic"


# ------------------------------------------------------- structural omission

def test_scope_withholds_a_real_fraction_of_the_checklist():
    """R5's mechanism. Asked in a prompt, the model omitted 8-21% against a 40%
    target however it was worded; naming the INCLUDED subset makes it structural.
    """
    for std in ("V&V40", "7009A"):
        facs = G._factors(std)
        scope = G.sparse_scope(facs, "bundle_seeded_000_bologna")
        withheld = len(facs) - len(scope)
        assert withheld / len(facs) >= 0.30, (
            f"{std}: only {withheld}/{len(facs)} withheld; the >=30%-absent "
            "guard downstream would have nothing to check")


def test_scope_varies_across_bundles_but_is_reproducible():
    """A fixed subset would leave the same factors unrepresented corpus-wide."""
    facs = G._factors("V&V40")
    a = G.sparse_scope(facs, "bundle_seeded_000_bologna")
    b = G.sparse_scope(facs, "bundle_seeded_001_bologna")
    assert a != b
    assert a == G.sparse_scope(facs, "bundle_seeded_000_bologna")


def test_domains_are_distinct_so_diversity_is_designed_in():
    """Five papers off one template scored 0.898 mean cosine against a real
    0.141. Prose style does not separate papers; subject matter does."""
    devices = [d[0] for d in G.DOMAINS]
    assert len(set(devices)) == len(devices)
    assert len(devices) >= 20, "fewer domains than the 40-paper target repeats"


# ------------------------------------------------------------ body assembly

def test_model_content_never_becomes_latex_markup():
    """The model returns plain text; every backslash is the renderer's."""
    sections = [{"heading": "Results & Discussion", "level": 1,
                 "paragraphs": [r"error was 5% with \alpha{2} and $x_i$"],
                 "rubric": {"factor": "Model form",
                            "rungs": ["no study", "partial {study}", "full study"]},
                 "figure": "Overview of the 100% case",
                 "table": {"caption": "Levels & basis",
                           "rows": [["Model form", "2", "50% of cases"]]}}]
    spec = dict(LR.demo_spec(0))
    spec["body"] = G.build_body(sections)
    assert LR.validate(LR.render(spec)) == []
    assert r"\textbackslash{}alpha" in spec["body"]
    assert r"5\%" in spec["body"]


def test_body_assembly_tolerates_absent_optional_blocks():
    body = G.build_body([{"heading": "Introduction", "level": 1,
                          "paragraphs": ["text"], "rubric": None,
                          "figure": None, "table": None}])
    assert r"\section{Introduction}" in body
    assert "tabular" not in body


def test_seed_reading_never_touches_ground_truth(monkeypatch):
    """Generation may see a seed's DOCUMENT and never its labels."""
    opened: list[str] = []
    real_read = pathlib.Path.read_text

    def spy(self, *a, **k):
        opened.append(self.name)
        return real_read(self, *a, **k)

    monkeypatch.setattr(pathlib.Path, "read_text", spy)
    G._seed_text("bologna", chars=500)
    assert not any("ground_truth" in n or "extracted" in n for n in opened), opened
