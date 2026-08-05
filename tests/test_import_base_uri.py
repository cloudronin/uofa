"""The namespace `uofa import` mints identifiers under.

Before this was configurable, every imported package carried
`https://uofa.net/instances/<project>/<cou>` identifiers. That put a user's
private evidence under a domain they do not control, and because the id sits
inside the canonicalised content covered by the hash and signature, the mistake
became permanent the moment the package was signed. Two organisations with the
same project name also minted colliding identifiers, which in RDF asserts their
unrelated evidence is the same thing.

uofa.net is reserved for this project's own published examples.
"""

from pathlib import Path

import pytest

from uofa_cli.excel_constants import DEFAULT_BASE_URI, RESERVED_BASE_URIS
from uofa_cli.excel_mapper import map_to_jsonld, resolve_base_uri


def _minimal_data(project="Acme Pump", cou="Steady state flow"):
    return {
        "summary": {
            "profile": "Minimal",
            "project_name": project,
            "cou_name": cou,
            "cou_description": "",
        },
        "entities": [],
        "validation_results": [],
        "factors": [],
        "decision": {"outcome": "Accepted"},
    }


def _doc(base_uri=None, **kw):
    return map_to_jsonld(_minimal_data(**kw), ["vv40"], Path("book.xlsx"), base_uri=base_uri)


def test_default_is_a_reserved_placeholder_domain():
    # RFC 2606 reserves example.org precisely so it reads as "replace me".
    assert DEFAULT_BASE_URI == "https://example.org"
    assert _doc()["id"] == "https://example.org/acme-pump/steady-state-flow"


def test_default_never_mints_under_uofa_net():
    doc = _doc()
    assert "uofa.net" not in doc["id"]
    assert not doc["id"].startswith("https://uofa.net/instances")


def test_caller_can_supply_a_namespace_they_control():
    doc = _doc(base_uri="https://acme.example/uofa")
    assert doc["id"] == "https://acme.example/uofa/acme-pump/steady-state-flow"
    # Every derived node inherits the same base, not just the top-level id.
    assert doc["hasContextOfUse"]["id"].startswith("https://acme.example/uofa/")
    assert doc["hasDecisionRecord"]["id"].startswith("https://acme.example/uofa/")


def test_trailing_slashes_do_not_double_up():
    assert _doc(base_uri="https://acme.example/uofa/")["id"] == (
        "https://acme.example/uofa/acme-pump/steady-state-flow"
    )


@pytest.mark.parametrize(
    "reserved",
    [
        "https://uofa.net",
        "https://uofa.net/",
        "https://uofa.net/instances",
        "https://uofa.net/instances/somewhere",
        "http://uofa.net",
    ],
)
def test_the_projects_own_namespace_is_refused(reserved):
    with pytest.raises(ValueError, match="reserved"):
        resolve_base_uri(reserved)
    with pytest.raises(ValueError, match="reserved"):
        _doc(base_uri=reserved)


def test_a_lookalike_domain_is_not_refused():
    # Only uofa.net itself is reserved. Guarding by substring would wrongly
    # reject someone's own uofa.net.example or my-uofa.net domain.
    assert resolve_base_uri("https://uofa.net.example/x") == "https://uofa.net.example/x"
    assert resolve_base_uri("https://my-uofa.net/x") == "https://my-uofa.net/x"


def test_empty_base_uri_is_an_error_not_a_silent_default():
    with pytest.raises(ValueError):
        resolve_base_uri("   ")


def test_two_orgs_sharing_a_project_name_can_avoid_collision():
    # The collision that made this worth fixing: slugify is deterministic, so
    # without distinct namespaces both packages claim the same identity.
    same = _doc(project="Pump", cou="COU1")["id"]
    other = _doc(project="Pump", cou="COU1", base_uri="https://other.example")["id"]
    assert same != other
    assert same.endswith("/pump/cou1") and other.endswith("/pump/cou1")


def test_reserved_list_is_exact_hosts_not_prefixes():
    assert RESERVED_BASE_URIS == ("https://uofa.net", "http://uofa.net")


# ── Criteria sets ────────────────────────────────────────────
#
# criteriaSet names the rubric an assessment was graded against. Published
# standards are shared concepts and keep a project-controlled identifier, the
# same reasoning that puts the vocabulary under uofa.net. An author's own rubric
# is not a shared concept and must land in the author's namespace.

from uofa_cli.excel_constants import CRITERIA_BASE, FACTOR_STANDARD_VV40
from uofa_cli.excel_mapper import resolve_criteria_set

ACME = "https://acme.example"


@pytest.mark.parametrize(
    "written",
    ["ASME-VV40-2018", "asme-vv40-2018", "ASME V&V 40", "ASME_VV40_2018", "vv40"],
)
def test_known_standard_aliases_fold_to_one_identifier(written):
    # criteria/nasa-std-7009b and criteria/NASA-STD-7009B were two different
    # things in the corpus. Spelling should not fork a shared identifier.
    assert resolve_criteria_set(written, ACME) == f"{CRITERIA_BASE}/{FACTOR_STANDARD_VV40}"


@pytest.mark.parametrize(
    "written,canonical",
    [
        ("NASA-STD-7009B", "NASA-STD-7009B"),
        ("nasa-std-7009b", "NASA-STD-7009B"),
        ("NASA 7009", "NASA-STD-7009B"),
        ("NIST AI RMF", "NIST-AI-RMF-1.0"),
        ("NIST-AI-RMF-1.0", "NIST-AI-RMF-1.0"),
    ],
)
def test_other_known_standards_resolve_canonically(written, canonical):
    assert resolve_criteria_set(written, ACME) == f"{CRITERIA_BASE}/{canonical}"


@pytest.mark.parametrize(
    "written", ["Our internal rubric v3", "ACME QA Standard 2024", "unpublished draft"]
)
def test_an_unrecognised_rubric_lands_in_the_authors_namespace(written):
    got = resolve_criteria_set(written, ACME)
    assert got.startswith(ACME + "/criteria/")
    # The project must not appear to vouch for a rubric it has never seen.
    assert "uofa.net" not in got


def test_an_authors_rubric_sits_at_org_level_not_under_a_cou():
    # A rubric is shared across an author's assessments, so burying it beneath
    # one context of use would misrepresent its scope.
    got = resolve_criteria_set("House rules", ACME)
    assert got == "https://acme.example/criteria/house-rules"


def test_criteria_set_flows_through_a_full_import():
    data = _minimal_data()
    data["summary"]["profile"] = "Complete"
    data["summary"]["standards_reference"] = "ASME V&V 40"
    doc = map_to_jsonld(data, ["vv40"], Path("b.xlsx"), base_uri=ACME)
    assert doc["criteriaSet"] == f"{CRITERIA_BASE}/{FACTOR_STANDARD_VV40}"

    data["summary"]["standards_reference"] = "Internal rubric"
    doc = map_to_jsonld(data, ["vv40"], Path("b.xlsx"), base_uri=ACME)
    assert doc["criteriaSet"] == "https://acme.example/criteria/internal-rubric"


def test_shipped_examples_use_the_canonical_criteria_iri():
    # Guards the corpus against drifting back to a slugified variant.
    import json, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    for f in root.glob("packs/*/examples/**/*.jsonld"):
        cs = json.loads(f.read_text()).get("criteriaSet")
        if isinstance(cs, str) and cs.startswith(CRITERIA_BASE):
            assert cs == f"{CRITERIA_BASE}/{cs.rsplit('/', 1)[1]}"
            assert cs.rsplit("/", 1)[1].isupper() or any(
                c.isdigit() for c in cs.rsplit("/", 1)[1]
            ), f"{f}: {cs} looks slugified rather than canonical"
