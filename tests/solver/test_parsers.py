"""The three parsers that carry the demo, and the firewall around them."""

from __future__ import annotations

import pytest

from uofa_cli.solver import archive, engdata, reader, wbproject
from uofa_cli.solver.facts import CERTAIN, LIBRARY_ENTRY
from uofa_cli.solver.redact import looks_redacted

from tests.solver.conftest import MINI

WBPJ = (MINI / "mini.wbpj").read_text(encoding="utf-8")
ENGD = (MINI / "mini_files/dp0/SYS/ENGD/EngineeringData.xml").read_text(encoding="utf-8")


# ── the project file ─────────────────────────────────────────


def test_reads_the_release_that_wrote_the_archive():
    """The version gap is a provenance observation, and it starts here.

    The real archives were written by 2023 R2 while the paper reports 19.0 /
    2019 R1 -- most plausibly a re-save for publication. The tool's job is to
    record which release touched the bytes, not to draw the inference.
    """
    ev = wbproject.parse(WBPJ, member="mini.wbpj")
    assert ev.by_key("project.ansys_release")[0].value == "2023 R2"
    assert ev.by_key("project.framework_build")[0].value == "23.2.142.0"
    assert ev.by_key("project.last_saved_utc")[0].value == "11/21/2024 09:00:56"
    assert ev.by_key("project.ansys_release")[0].binding_confidence == CERTAIN


def test_stored_messages_become_cautions_with_the_solvers_own_severity():
    ev = wbproject.parse(WBPJ, member="mini.wbpj")
    assert ev.severity_counts == {"information": 1, "warning": 3, "error": 1}
    summaries = " ".join(c.summary for c in ev.cautions)
    assert "Weak springs have been added" in summaries
    assert "Linear Tetrahedral elements" in summaries


def test_every_caution_quotes_its_source_member():
    ev = wbproject.parse(WBPJ, member="mini.wbpj")
    assert all(c.source_member == "mini.wbpj" for c in ev.cautions)


def test_the_archive_record_yields_the_stripped_filenames():
    """This is the completeness evidence.

    `solve.out` does not exist in a `-NoResults` archive, so there is no solver
    log to parse -- but Workbench recorded what it left out, naming the files.
    A package that testifies to its own gaps is worth more than one we merely
    failed to find things in.
    """
    ev = wbproject.parse(WBPJ, member="mini.wbpj")
    names = {a.name for a in ev.absent}
    assert names == {"ds.dat", "file.rst", "solve.out"}
    assert all(a.stated_by == "workbench-archive-record" for a in ev.absent)


def test_operator_paths_do_not_survive_into_any_record():
    ev = wbproject.parse(WBPJ, member="mini.wbpj")
    blob = " ".join([c.summary + c.detail for c in ev.cautions]
                    + [a.name + a.location for a in ev.absent])
    assert looks_redacted(blob)
    assert "testuser" not in blob.lower()
    assert "examplepc" not in blob.lower()


def test_malformed_xml_is_reported_not_raised():
    ev = wbproject.parse("<Storage><unclosed>", member="broken.wbpj")
    assert ev.unparsed and "well-formed" in ev.unparsed[0]
    assert ev.cautions == []


def test_a_message_missing_its_type_is_left_unread():
    """78 of these in one real project; being right about 70 is not a licence
    to invent the other 8."""
    xml = ('<Storage><Object Name="/Messages/StoredMessage:M">'
           '<class-type>StoredMessage</class-type>'
           '<member-data>{"Summary": "no type here"}</member-data>'
           "</Object></Storage>")
    ev = wbproject.parse(xml, member="x.wbpj")
    assert ev.cautions == []
    assert len(ev.unparsed) == 1


def test_only_stored_messages_are_treated_as_messages():
    """Other containers reuse the `member-data` tag; reading them all reported
    43 spurious unparsed records against the real project file."""
    xml = ('<Storage><Object Name="/Other/Thing"><class-type>Thing</class-type>'
           '<member-data>{"Summary": "not a message"}</member-data>'
           "</Object></Storage>")
    ev = wbproject.parse(xml, member="x.wbpj")
    assert ev.cautions == [] and ev.unparsed == []


@pytest.mark.parametrize("blob,expected", [
    ('{"MessageType": "Warning", "Summary": "plain"}', "plain"),
    ('{"MessageType": "Warning", "Summary": ""doubled""}', "doubled"),
    ('{"MessageType": "Warning", "Summary": "has \\"quotes\\" inside"}',
     'has "quotes" inside'),
    ('{"MessageType": "Warning", "Summary": "before", "Details": None}', "before"),
])
def test_member_data_quoting_variants(blob, expected):
    """Neither json.loads nor ast.literal_eval will touch these blobs: the
    timestamps are bare, `None` is Python's, and some summaries arrive
    double-quoted."""
    assert wbproject.split_member_data(blob)["Summary"] == expected


def test_details_triple_quoted_raw_string_is_unwrapped():
    blob = '{"MessageType": "Warning", "Summary": "s", "Details": r"""1. a\\b.dat"""}'
    assert wbproject.split_member_data(blob)["Details"] == r"1. a\b.dat"


def test_a_stripped_path_containing_spaces_is_one_entry():
    """`...\\Contact Tool\\x` split on whitespace produced a phantom file called
    `Contact` against the real archive."""
    detail = r"1. C:\p\Contact Tool\out.xml 2. C:\p\solve.out"
    ev = wbproject.parse(_archive_record(detail), member="x.wbpj")
    assert {a.name for a in ev.absent} == {"out.xml", "solve.out"}


def _archive_record(detail: str) -> str:
    return ('<Storage><Object Name="/Messages/StoredMessage:M">'
            '<class-type>StoredMessage</class-type>'
            '<member-data>{"MessageType": "Warning", "Summary": "The project '
            'just opened was from an archived project that did not include '
            'solution or result files.", "Details": r"""' + detail + '"""}'
            "</member-data></Object></Storage>")


# ── the materials library ────────────────────────────────────


def _materials(ev):
    out = {}
    for f in ev.facts:
        if f.key.startswith("material."):
            out.setdefault(f.scope, {})[f.key] = (f.value, f.units)
    return out


def test_matml_id_indirection_is_resolved():
    """Values live under `pr3`/`pa1` ids whose meaning is declared in a
    `<Metadata>` block that may appear after all the materials."""
    mats = _materials(engdata.parse(ENGD, member="e.xml"))
    assert mats["Ti6Al4V_Base_BISO"]["material.youngs_modulus"] == (108222.363244, "MPa")
    assert mats["Ti6Al4V_Base_BISO"]["material.poissons_ratio"] == (0.33, "")


def test_the_table_5_row_is_read_exactly():
    """The paper's Table 5, FDA column: E 108,222 / nu 0.33 / yield 967.5 /
    tangent 4,647. This is the corroboration target."""
    mats = _materials(engdata.parse(ENGD, member="e.xml"))
    ti = mats["Ti6Al4V_Base_BISO"]
    assert ti["material.yield_strength"] == (967.479362, "MPa")
    assert ti["material.tangent_modulus"] == (4646.717387, "MPa")


def test_units_are_recorded_as_declared_and_never_converted():
    """One library, two units. Coercing silently produces a wrong answer that
    validates -- the requirement layer's open question Q3."""
    mats = _materials(engdata.parse(ENGD, member="e.xml"))
    assert mats["Ti6Al4V_Base_BISO"]["material.youngs_modulus"][1] == "MPa"
    assert mats["UHMWPE"]["material.youngs_modulus"] == (690000000.0, "Pa")


def test_the_unit_error_duplicate_is_read_verbatim_not_corrected():
    """`tI6aL4vbiso` duplicates the row above with a tangent modulus off by
    10^6. Reading it faithfully is the whole point: silently repairing it would
    delete the finding."""
    mats = _materials(engdata.parse(ENGD, member="e.xml"))
    assert mats["tI6aL4vbiso"]["material.tangent_modulus"] == (0.004646717387, "MPa")


def test_material_facts_are_library_entries_not_certainties():
    """The value is certainly in the file. That the published run USED it is a
    different claim the file does not make."""
    ev = engdata.parse(ENGD, member="e.xml")
    material_facts = [f for f in ev.facts if f.key.startswith("material.")]
    assert material_facts
    assert all(f.binding_confidence == LIBRARY_ENTRY for f in material_facts)


def test_non_numeric_placeholders_are_skipped_quietly():
    ev = engdata.parse(ENGD, member="e.xml")
    assert all(isinstance(f.value, (int, float))
               for f in ev.facts if f.key.startswith("material."))


def test_every_fact_quotes_the_bytes_it_came_from():
    """What makes a fact auditable without the vendor software."""
    ev = engdata.parse(ENGD, member="e.xml")
    for f in ev.facts:
        assert f.source_member == "e.xml"
        assert f.source_text
        assert f.source_locator


# ── the folder-level read ────────────────────────────────────


def test_read_evidence_walks_into_the_archive(evidence_folder):
    ev = reader.read_evidence(evidence_folder)
    assert ev.by_key("project.ansys_release")[0].value == "2023 R2"
    assert any(f.key.startswith("material.") for f in ev.facts)
    assert {a.name for a in ev.absent} == {"ds.dat", "file.rst", "solve.out"}


def test_source_members_name_container_and_member(evidence_folder):
    ev = reader.read_evidence(evidence_folder)
    assert any("mini.wbpz!mini.wbpj" == f.source_member for f in ev.facts)


def test_disagreements_are_reported_never_resolved():
    """A library holding two Young's moduli for one material is a fact about
    the library; which is right is not this layer's call."""
    ev = engdata.parse(ENGD, member="a.xml")
    ev.extend(engdata.parse(
        ENGD.replace("<Data>108222.363244</Data>", "<Data>110000.0</Data>"),
        member="b.xml"))
    clashes = ev.disagreements()
    assert ("material.youngs_modulus", "Ti6Al4V_Base_BISO") in clashes
