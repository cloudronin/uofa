"""excel_constants.py agrees with the SHACL it claims to be generated from.

Two failures motivated this file, both silent.

`VALID_PROFILES` is derived from `sh:in` on `conformsToProfile`; `PROFILE_URIS`
was hand-written into the generator. When v0.6 added `ProfileDisposition` to
`sh:in`, the derived list would have grown on the next regeneration while the
hardcoded map stayed at two entries — and `excel_mapper` looks the profile up
with `PROFILE_URIS.get(profile, PROFILE_URIS["Minimal"])`, so a Disposition row
would have been relabelled Minimal with no error anywhere.

Separately, `excel_constants.py` is a hybrid: most of it is generated, but the
MRM-NIST factor set and the base-URI constants are hand-maintained and the
generator does not emit them. Its own docstring points at a command that writes
a whole file, so running that command and committing the result deletes them.

Both tests are data-driven against the shapes, not against a copy of the answer.
"""

from __future__ import annotations

import pytest

from uofa_cli import excel_constants, paths

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402
from rdflib.collection import Collection  # noqa: E402

SH = Namespace("http://www.w3.org/ns/shacl#")
UOFA = Namespace("https://uofa.net/vocab#")


def _profile_uris_from_shapes() -> list[str]:
    """The live sh:in list for conformsToProfile (authoritative)."""
    g = Graph().parse(str(paths.shacl_schema()), format="turtle")
    for prop in g.objects(UOFA.UnitOfAssurance_ProfileShape, SH.property):
        if g.value(prop, SH.path) != UOFA.conformsToProfile:
            continue
        head = g.value(prop, SH["in"])
        if head is not None:
            return [str(v) for v in Collection(g, head)]
    raise AssertionError("UnitOfAssurance_ProfileShape declares no conformsToProfile sh:in")


def test_profile_constants_match_the_shapes():
    shape_uris = _profile_uris_from_shapes()
    expected = {u.rsplit("#Profile", 1)[-1]: u for u in shape_uris if "#Profile" in u}
    assert expected, "sh:in should yield at least one #Profile* URI"

    assert set(excel_constants.VALID_PROFILES) == set(expected), (
        "VALID_PROFILES is stale against the SHACL sh:in — "
        "regenerate with `uofa schema --emit python` and merge the derived section"
    )
    assert excel_constants.PROFILE_URIS == expected, (
        "PROFILE_URIS disagrees with the SHACL sh:in"
    )


def test_profile_name_and_uri_constants_cover_the_same_profiles():
    # The pairing excel_mapper depends on: every name it may read from a
    # spreadsheet has to resolve to a URI, or the .get() fallback silently
    # relabels the package as Minimal.
    assert set(excel_constants.VALID_PROFILES) == set(excel_constants.PROFILE_URIS), (
        "a profile name with no URI resolves to Minimal via the .get() fallback "
        "in excel_mapper, which mislabels the package instead of failing"
    )


# Present in the checked-in module, absent from the generator's output. If a
# regeneration is committed wholesale these vanish, and the importer loses the
# MRM-NIST factor set and starts minting user data under the wrong base URI.
HAND_MAINTAINED = [
    "MODEL_CREDIBILITY_FACTOR_NAMES",
    "MODEL_CREDIBILITY_FACTOR_CATEGORIES",
    "MODEL_CREDIBILITY_DEFAULT_OUT_OF_SCOPE",
    "FACTOR_STANDARD_MODEL_CREDIBILITY",
    "CRITERIA_BASE",
    "KNOWN_CRITERIA_SETS",
]


@pytest.mark.parametrize("name", HAND_MAINTAINED)
def test_hand_maintained_constants_survive(name):
    assert hasattr(excel_constants, name), (
        f"{name} is hand-maintained and the generator does not emit it. "
        "It looks like excel_constants.py was replaced by `uofa schema --emit python` "
        "rather than merged; restore it from git history."
    )
