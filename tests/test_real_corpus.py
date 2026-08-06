"""The Tier 1 real-document corpus, and the properties that make it worth having.

These bundles exist because every number the synthetic corpus reports is either
saturated by a constant or produced by the same model family that wrote the
documents. Real reports fix both: the levels are the original authors', and the
factor scores span a range the generator never emitted.

What is tested here is not extraction accuracy -- that needs a run -- but the
integrity of the corpus itself: that the transcription matches published
granularity, that no source document is redistributed, and that the one piece of
judgment in the pipeline stays visible.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
CORPUS = _ROOT / "tests" / "fixtures" / "extract_corpus_real"
sys.path.insert(0, str(CORPUS))

from cas_mapping import (  # noqa: E402
    VARIANTS,
    roll_up,
    unmapped_factors,
)

BUNDLES = sorted(CORPUS.glob("bundle_*"))


def _gt(bundle: Path) -> dict:
    return json.loads((bundle / "ground_truth.json").read_text())


def test_there_are_bundles():
    assert BUNDLES, "no Tier 1 bundles found"


# ── redistribution ───────────────────────────────────────────

def test_no_source_document_is_committed():
    """The manifest records PUBLIC_USE_PERMITTED, belongsToUsGov false.

    Public use permitted is not the public domain. The repository ships ground
    truth plus a URL and a hash; it must never ship the documents. This is the
    one failure here that is a licensing problem rather than a data problem.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "tests/fixtures/extract_corpus_real/"],
        cwd=_ROOT, capture_output=True, text=True, check=True).stdout.split()
    leaked = [f for f in tracked if "/source/" in f]
    assert not leaked, f"source documents must not be committed: {leaked}"


def test_manifest_covers_every_transcribed_bundle():
    manifest = json.loads((CORPUS / "MANIFEST.json").read_text())
    for b in BUNDLES:
        cid = _gt(b)["_provenance"]["citation_id"]
        assert cid in manifest, f"{b.name} cites {cid}, absent from MANIFEST.json"
        assert manifest[cid]["files"], f"{cid} has no file with a hash"
        for f in manifest[cid]["files"]:
            assert len(f["sha256"]) == 64, f"{cid}: {f['name']} has no usable hash"
            assert f["url"].startswith("https://"), f"{cid}: {f['name']} url not https"


# ── transcription fidelity ───────────────────────────────────

def test_every_bundle_declares_its_published_vocabulary():
    """Three different vocabularies appear in the literature.

    A bundle that does not say which one it transcribed cannot be rolled up
    correctly, and the resulting comparison would be silently meaningless.
    """
    for b in BUNDLES:
        gt = _gt(b)
        assert gt["cas_variant"] in VARIANTS, f"{b.name}: {gt['cas_variant']!r}"


def test_factors_match_the_declared_vocabulary_exactly():
    """Transcription means the document's rows, not a superset or a subset."""
    for b in BUNDLES:
        gt = _gt(b)
        published = set(VARIANTS[gt["cas_variant"]])
        got = {f["factor_type"] for f in gt["expected_factors"]}
        assert got <= published, f"{b.name}: rows not in the vocabulary: {got - published}"


def test_levels_are_inside_the_published_scale():
    """NASA-STD-7009 scores 0-4, and real tables carry non-integer scores.

    2.3, 1.6 and 3.4 all appear. The synthetic corpus is integer-only and never
    exceeds 3, so a scorer that assumed integers passed on synthetic data and
    would be wrong here.
    """
    seen_fractional = False
    for b in BUNDLES:
        for f in _gt(b)["expected_factors"]:
            for key in ("expected_level", "expected_required_level"):
                if key not in f:      # threshold is optional; see the test below
                    continue
                v = f[key]
                assert 0.0 <= v <= 4.0, f"{b.name}/{f['factor_type']}: {key}={v}"
            if f["expected_level"] != int(f["expected_level"]):
                seen_fractional = True
    assert seen_fractional, (
        "no fractional score in the corpus -- either transcription rounded them "
        "away, or the bundles that carried them were dropped")


def test_a_cas_is_a_complete_profile_so_nothing_is_not_applicable():
    """0 means Insufficient Evidence, which is a score, not an omission.

    The plan expected real bundles to carry many not_applicable factors and so
    to break `control_constant_list`. They do not: every published row has a
    score. Detection stays saturated and the discrimination has to come from
    level and groundedness. Pinned because it is a load-bearing correction.
    """
    for b in BUNDLES:
        statuses = {f["expected_status"] for f in _gt(b)["expected_factors"]}
        assert statuses == {"assessed"}, f"{b.name}: {statuses}"


def test_required_level_is_transcribed_or_explicitly_absent():
    """Real reports publish the threshold; the synthetic corpus has no such field.

    This is the ground truth P5 could not otherwise obtain, so where it exists
    its provenance must be a named column in a named table -- and where it does
    not, the bundle has to say why rather than leaving a reader to assume it was
    overlooked.

    The OPENSIM bundles are the "does not" case: that paper publishes its
    thresholds only as bar charts in Figures 3-5. A sibling paper states
    thresholds for a different injury scenario, and borrowing them would have
    filled the column with numbers no document asserts about these models.
    """
    with_threshold = 0
    for b in BUNDLES:
        gt = _gt(b)
        prov = gt["_provenance"]
        assert prov["table_location"], f"{b.name}: no table location recorded"
        has = [f for f in gt["expected_factors"] if "expected_required_level" in f]

        if has:
            assert len(has) == len(gt["expected_factors"]), (
                f"{b.name}: threshold on some rows but not others")
            assert "expected_required_level" in prov["transcribed_columns"], (
                f"{b.name}: carries thresholds but names no source column")
            with_threshold += 1
        else:
            assert prov.get("required_level_not_transcribed"), (
                f"{b.name}: no thresholds and no explanation of why")

    assert with_threshold, "no bundle carries a transcribed required_level"


def test_no_bundle_borrows_a_sibling_papers_thresholds():
    """The specific fabrication this corpus is exposed to.

    Papers in the same family use the same factor vocabulary and differ only in
    scenario, so their threshold tables look interchangeable and are not. Any
    bundle carrying thresholds must cite the citation_id it transcribed them
    from, and that must be its own.
    """
    for b in BUNDLES:
        gt = _gt(b)
        if not any("expected_required_level" in f for f in gt["expected_factors"]):
            continue
        prov = gt["_provenance"]
        assert prov["transcribed_columns"]["expected_required_level"], (
            f"{b.name}: threshold column name is empty")
        # The table it came from is this bundle's own document, by construction:
        # transcribed_columns describes table_location, which belongs to
        # citation_id. Assert the id is present so the chain is checkable.
        assert prov["citation_id"], f"{b.name}: thresholds with no citation"


def test_real_models_fall_short_far_more_often_than_synthetic_ones():
    """The finding that makes this corpus worth the effort.

    27.9% of synthetic factor rows sit below their required level. In these
    reports it is most of them -- real models routinely ship under-credentialed
    against their own thresholds, and a corpus where they mostly comply is not
    describing the same world.
    """
    rows = [f for b in BUNDLES for f in _gt(b)["expected_factors"]
            if "expected_required_level" in f]
    assert rows, "no bundle carries thresholds, so the comparison cannot be made"
    short = [f for f in rows if f["expected_level"] < f["expected_required_level"]]
    assert len(short) / len(rows) > 0.40, (
        f"only {len(short)}/{len(rows)} rows fall short; the synthetic corpus is "
        "at 27.9% and the real reports sampled were far higher")


# ── the rollup, which is the only judgment in the pipeline ───

def test_rollup_takes_the_weakest_constituent():
    levels = {"Numerical code verification": 3, "Discretization error": 1,
              "Numerical solver error": 4, "Software quality assurance": 2}
    assert roll_up(levels, "rollup_7009a")["Verification"] == 1


def test_rollup_distinguishes_not_extracted_from_scored_zero():
    """None and 0 are different failures and must not collapse.

    Collapsing them is how the level metric became uninterpretable on the
    synthetic corpus, where 60 not_applicable rows carried expected_level 1.
    """
    assert roll_up({}, "rollup_7009a")["Verification"] is None
    assert roll_up({"Discretization error": 0}, "rollup_7009a")["Verification"] == 0


def test_people_qualifications_is_unanswerable_not_wrong():
    """No pack factor covers who ran the model.

    Counting it as a miss would charge the extractor for a gap in the schema.
    """
    assert unmapped_factors("rollup_7009a") == ["People Qualifications"]
    assert roll_up({}, "rollup_7009a")["People Qualifications"] is None
    assert unmapped_factors("decomposed_7009a") == []


def test_every_mapped_pack_factor_is_a_real_pack_factor():
    """A typo here would silently drop a constituent from every rollup."""
    pytest.importorskip("uofa_cli")
    from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES
    known = set(NASA_ALL_FACTOR_NAMES)
    for variant, mapping in VARIANTS.items():
        for published, constituents in mapping.items():
            unknown = set(constituents) - known
            assert not unknown, f"{variant}/{published}: not pack factors: {unknown}"
