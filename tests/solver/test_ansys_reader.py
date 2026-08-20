"""The corpus adapter, and the two boundaries it must not cross."""

from __future__ import annotations

import re

from uofa_cli.document_reader import _READERS, discover_files, read_corpus
from uofa_cli.readers.ansys_reader import read_ansys
from uofa_cli.solver import redact


def test_workbench_formats_are_registered():
    for suffix in (".wbpz", ".wbpj", ".engd"):
        assert _READERS[suffix] == ("uofa_cli.readers.ansys_reader", "read_ansys")


def test_an_evidence_folder_of_archives_is_no_longer_invisible(evidence_folder):
    """Before this, `uofa extract` on the real OSF folder exited 1 with
    "No supported files found" -- `.wbpz` was not in `_READERS` and not in
    `_DEFERRED_SUFFIXES`, so `discover_files` dropped it at the unsupported-
    suffix `continue` without a word."""
    files, warnings = discover_files([evidence_folder])
    assert any(f.suffix == ".wbpz" for f in files)


def test_a_workbench_tree_is_deep_enough_to_reach(tmp_path):
    """`proj_files/dp0/SYS-15/ENGD/EngineeringData.xml` is four levels down;
    the old max_depth of 3 stopped one short."""
    deep = tmp_path / "proj_files/dp0/SYS-15/ENGD"
    deep.mkdir(parents=True)
    (deep / "material.engd").write_text("<EngineeringData/>", encoding="utf-8")
    files, _ = discover_files([tmp_path])
    assert [f.name for f in files] == ["material.engd"]


def test_unreadable_simulation_formats_are_named_not_dropped(tmp_path):
    (tmp_path / "model.mechdb").write_bytes(b"\x00binary")
    (tmp_path / "results.rst").write_bytes(b"\x00binary")
    files, warnings = discover_files([tmp_path])
    assert files == []
    joined = " ".join(warnings)
    assert "model.mechdb" in joined and "results.rst" in joined
    assert "uofa evidence seal" in joined, "say what WILL handle it"


def test_chunks_are_sectioned_and_attributed(evidence_folder):
    chunks = read_ansys(evidence_folder / "mini.wbpz")
    headings = [c.section_heading for c in chunks]
    assert "Solver project and software" in headings
    assert "Materials defined in the project" in headings
    assert "Artifacts the package states are absent" in headings
    assert all(c.format == "ansys" for c in chunks)
    assert all(c.source_file == "mini.wbpz" for c in chunks)


def test_nothing_operator_identifying_reaches_the_corpus(evidence_folder):
    """The last point before text leaves for a language model."""
    text = "\n".join(c.text for c in read_ansys(evidence_folder / "mini.wbpz"))
    assert redact.looks_redacted(text)
    assert "testuser" not in text.lower()
    assert "examplepc" not in text.lower()


def test_the_stripped_solver_files_lead_the_absence_list(evidence_folder):
    """Alphabetical order buries `solve.out` behind sixty cleanup scripts."""
    text = "\n".join(c.text for c in read_ansys(evidence_folder / "mini.wbpz"))
    section = text[text.index("## Artifacts the package states are absent"):]
    assert section.index("ds.dat") < section.index("Other files named")


def test_the_corpus_is_a_digest_not_the_artifacts(evidence_folder):
    """A project file is 233 KB of XML that is mostly storage plumbing.

    Seal everything, read some, send even less: the corpus must be far smaller
    than the bytes it describes.
    """
    corpus = read_corpus(discover_files([evidence_folder])[0])
    archive_bytes = (evidence_folder / "mini.wbpz").stat().st_size
    assert corpus.total_tokens * 4 < archive_bytes


# ── the terminology firewall ─────────────────────────────────

_WEAKENER_WORDS = re.compile(r"weakener|defect|violation|non-?conform", re.I)


def test_solver_messages_are_never_called_weakeners(evidence_folder):
    """"Weakener" names a catalog rule with an id. Nothing here has one.

    These are cautions the solver itself raised, carried through for a human to
    weigh. A reviewer who hears "weakener" for a finding with no rule behind it
    will rightly ask where the rule is -- and this build deliberately mints no
    catalog rules, since the case-study packages are frozen until after the
    mutation measurement run.
    """
    text = "\n".join(c.text for c in read_ansys(evidence_folder / "mini.wbpz"))
    found = _WEAKENER_WORDS.findall(text)
    assert not found, f"catalog vocabulary leaked into the corpus: {found}"


def test_the_corpus_says_whose_findings_these_are(evidence_folder):
    text = "\n".join(c.text for c in read_ansys(evidence_folder / "mini.wbpz"))
    assert "not findings of this tool" in text
