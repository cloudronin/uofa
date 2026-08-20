"""The prose-versus-artifact join, and the two things it refuses to do."""

from __future__ import annotations

import json

import pytest

from uofa_cli import corroborate, paths
from uofa_cli.corroborate import (AGREES, ARTIFACT_ONLY, CLAIM_ONLY, DIVERGES,
                                  NOT_COMPARABLE, Claim)
from uofa_cli.solver import engdata
from uofa_cli.solver.facts import LIBRARY_ENTRY, SolverEvidence, SolverFact

from tests.solver.conftest import MINI

ENGD = (MINI / "mini_files/dp0/SYS/ENGD/EngineeringData.xml").read_text(encoding="utf-8")


@pytest.fixture
def identity():
    return paths.detection_config(paths.pack_manifest("vv40"))["quantityIdentity"]


@pytest.fixture
def evidence():
    return engdata.parse(ENGD, member="EngineeringData.xml")


def _claim(quantity, value, units="", scope="Ti6Al4V_Base_BISO"):
    return Claim(quantity=quantity, value=value, units=units, scope=scope,
                 source="Table 5, FDA")


def test_the_pack_declares_quantity_identity_not_the_code(identity):
    """AGENTS.md §3: pack-derived data lives in the pack manifest, loaded
    through `paths.detection_config`, never hardcoded in src/ or the Space."""
    assert "material.youngs_modulus" in identity
    assert identity["material.youngs_modulus"]["canonicalUnit"] == "MPa"


def test_table_5_corroborates(identity, evidence):
    """The paper's FDA column against the archive's own library."""
    claims = [_claim("material.youngs_modulus", 108222, "MPa"),
              _claim("material.poissons_ratio", 0.33),
              _claim("material.yield_strength", 967.5, "MPa"),
              _claim("material.tangent_modulus", 4647, "MPa")]
    result = corroborate.corroborate(claims, evidence, identity)
    assert [r.verdict for r in result.rows if r.verdict != ARTIFACT_ONLY] == [AGREES] * 4


def test_a_divergence_is_found_and_not_resolved(identity, evidence):
    """The paper gives FDA's UHMWPE as 1,100 MPa; the archive says 690.

    A library carries unused, superseded and duplicate entries, so this may be
    an unused entry, a later edit, or a table error. The row says the values
    differ and stops there.
    """
    claims = [_claim("material.youngs_modulus", 1100, "MPa", scope="UHMWPE")]
    rows = [r for r in corroborate.corroborate(claims, evidence, identity).rows
            if r.verdict == DIVERGES]
    assert len(rows) == 1
    assert rows[0].fact_value == 690000000.0 and rows[0].fact_units == "Pa"
    assert "1100 vs 690 MPa" in rows[0].detail


def test_units_convert_only_through_the_declared_table(identity, evidence):
    """690000000 Pa and 1100 MPa ARE comparable: Pa is in the table."""
    claims = [_claim("material.youngs_modulus", 690, "MPa", scope="UHMWPE")]
    rows = [r for r in corroborate.corroborate(claims, evidence, identity).rows
            if r.verdict in (AGREES, DIVERGES)]
    assert [r.verdict for r in rows] == [AGREES]


def test_an_undeclared_unit_is_refused_never_assumed(identity):
    """The requirement layer's open question Q3, enforced.

    A per-system `.engd` states 108222363244 with no unit. It is almost
    certainly Pa. "Almost certainly" is a conversion, and a silent conversion
    that is wrong produces an answer that validates.
    """
    ev = SolverEvidence(facts=[SolverFact(
        key="material.youngs_modulus", value=108222363244.0, units="",
        scope="Ti6Al4V_Base_BISO", source_member="material.engd",
        binding_confidence=LIBRARY_ENTRY)])
    rows = corroborate.corroborate(
        [_claim("material.youngs_modulus", 108222, "MPa")], ev, identity).rows
    assert [r.verdict for r in rows] == [NOT_COMPARABLE]
    assert "refusing to assume" in rows[0].detail


def test_a_quantity_with_no_identity_entry_is_not_compared(evidence):
    """A quantity the active pack does not declare has no conversion table and
    no tolerance, so there is nothing to compare it with. Matching the scope is
    not enough to license a comparison."""
    rows = corroborate.corroborate(
        [_claim("material.youngs_modulus", 108222, "MPa")], evidence,
        identity={}).rows
    assert [r.verdict for r in rows] == [NOT_COMPARABLE]
    assert "no quantity-identity entry" in rows[0].detail


def test_a_claim_about_a_quantity_no_artifact_records(identity, evidence):
    """Distinct from not-comparable: there is nothing on the other side."""
    rows = corroborate.corroborate(
        [_claim("material.density", 4430, "kg m^-3")], evidence, identity).rows
    assert rows[0].verdict == CLAIM_ONLY
    # The fixture records density for Structural Steel only, so the detail
    # names that as the binding candidate rather than claiming silence.
    assert "Structural Steel" in rows[0].detail

    absent = corroborate.corroborate(
        [_claim("material.tensile_ultimate_strength", 900, "MPa")],
        evidence, identity).rows
    assert "no artifact records this quantity" in absent[0].detail


def test_string_comparison_for_a_release(identity):
    ev = SolverEvidence(facts=[SolverFact(
        key="project.ansys_release", value="2023 R2", scope="project",
        source_member="p.wbpj")])
    claim = Claim(quantity="project.ansys_release", value="19.0",
                  scope="project", source="Table 5")
    rows = corroborate.corroborate([claim], ev, identity).rows
    assert rows[0].verdict == DIVERGES


def test_scope_binding_is_declared_never_guessed(identity, evidence):
    """A paper writes "Ti-6Al-4V ELI"; a library writes `Ti6Al4V_Base_BISO`.

    Aliases come from whoever wrote the claim. Inferring the binding from
    string similarity would silently bind two different materials -- and this
    library holds three mutually inconsistent titanium entries.
    """
    unbound = Claim(quantity="material.youngs_modulus", value=108222,
                    units="MPa", scope="Ti-6Al-4V ELI", source="Table 5")
    rows = [r for r in corroborate.corroborate([unbound], evidence, identity).rows
            if r.verdict == CLAIM_ONLY]
    assert len(rows) == 1
    assert "Ti6Al4V_Base_BISO" in rows[0].detail, "name the binding candidates"

    bound = Claim(quantity="material.youngs_modulus", value=108222, units="MPa",
                  scope="Ti-6Al-4V ELI", aliases=("Ti6Al4V_Base_BISO",),
                  source="Table 5")
    assert any(r.verdict == AGREES
               for r in corroborate.corroborate([bound], evidence, identity).rows)


def test_repeated_libraries_collapse_to_distinct_readings(identity, evidence):
    """One archive carries eleven materials libraries. A naive join emits the
    same comparison ten times and buries the rows anyone came to see."""
    doubled = SolverEvidence()
    doubled.extend(engdata.parse(ENGD, member="a.engd"))
    doubled.extend(engdata.parse(ENGD, member="b.engd"))
    claims = [_claim("material.youngs_modulus", 108222, "MPa")]
    rows = [r for r in corroborate.corroborate(claims, doubled, identity).rows
            if r.verdict == AGREES]
    assert len(rows) == 1
    assert "further member(s) agreeing" in rows[0].fact_source


def test_a_disagreement_between_members_gets_a_row_each(identity):
    ev = SolverEvidence(facts=[
        SolverFact(key="material.youngs_modulus", value=108222.0, units="MPa",
                   scope="Ti6Al4V_Base_BISO", source_member="a.engd"),
        SolverFact(key="material.youngs_modulus", value=110000.0, units="MPa",
                   scope="Ti6Al4V_Base_BISO", source_member="b.engd")])
    rows = [r for r in corroborate.corroborate(
        [_claim("material.youngs_modulus", 108222, "MPa")], ev, identity).rows
        if r.verdict in (AGREES, DIVERGES)]
    assert sorted(r.verdict for r in rows) == [AGREES, DIVERGES]


def test_artifact_values_with_no_claim_are_listed(identity, evidence):
    result = corroborate.corroborate([], evidence, identity)
    assert result.rows
    assert all(r.verdict == ARTIFACT_ONLY for r in result.rows)


def test_binding_confidence_travels_into_the_row(identity, evidence):
    """A match is corroboration, not proof: the file does not say which library
    entry the published run used."""
    claims = [_claim("material.youngs_modulus", 108222, "MPa")]
    row = next(r for r in corroborate.corroborate(claims, evidence, identity).rows
               if r.verdict == AGREES)
    assert row.binding_confidence == LIBRARY_ENTRY


def test_claim_files_load_from_list_or_object(tmp_path):
    rows = [{"quantity": "material.youngs_modulus", "value": 1, "units": "MPa"}]
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(rows))
    b.write_text(json.dumps({"claims": rows}))
    assert corroborate.load_claims(a) == corroborate.load_claims(b)


def test_no_catalog_vocabulary_in_any_verdict_or_detail(identity, evidence):
    """"Weakener", "defect" and "violation" name catalog rules with ids.

    This build mints none, so a row that used those words would send a reviewer
    looking for a rule that does not exist.
    """
    import re
    claims = [_claim("material.youngs_modulus", 1100, "MPa", scope="UHMWPE")]
    result = corroborate.corroborate(claims, evidence, identity)
    blob = json.dumps(result.as_list()) + " ".join(result.summarise())
    assert not re.search(r"weakener|defect|violation|non-?conform", blob, re.I)
