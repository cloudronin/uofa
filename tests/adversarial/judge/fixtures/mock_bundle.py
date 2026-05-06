"""5-case mock judge_ready_bundle.tgz generator (spec v1.5 §2.1).

Used as a stable test fixture for the bundle reader and downstream judge
modules. The five cases are hand-designed to cover the four normalized
outcome classes (COV-HIT, COV-MISS, COV-WRONG, GEN-INVALID) plus one
duplicate-class case so list-vs-set semantics in the reader get exercised.

The real Phase 2 corpus at dev/build/adversarial/phase2/2026-04-26/ is too
large for unit-test speed (4,221 packages, 7,101 jsonld files); we test
read-side semantics against this 5-case fixture and verify writer
correctness against the real corpus in Wave 6 integration.
"""

from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


# Schema constant: the manifest fields we emit. Mirrors the spec §2.1
# example. Lifted out so tests can assert against a stable copy.
MOCK_PACKAGE_COUNT = 5
MOCK_GENERATOR_MODEL = "anthropic/claude-sonnet-4-6"
MOCK_PHASE2_TAG = "v0.4.1-phase2-complete"


@dataclass(frozen=True)
class _MockCase:
    """One case in the mock bundle: package + outcome pair."""

    case_id: str
    coverage_class: str  # normalized class
    coverage_class_raw: str  # original Phase 2 class
    expected_rule: str | None
    rules_fired: list[str]
    source_taxonomy: str
    section_6_7_mapping: str | None
    coverage_intent: str
    subtlety: str


# Five hand-picked cases spanning the normalized class space. Covers a
# Tier-1 §6.7 candidate (W-EV-01), a confirm-existing hit (W-AR-01), a
# confirm-existing wrong-rule case, a negative-control false positive,
# and a SHACL-failed package.
MOCK_CASES: list[_MockCase] = [
    _MockCase(
        case_id="adv-2026-p2-101-data-drift-v01",
        coverage_class="COV-MISS",
        coverage_class_raw="COV-MISS",
        expected_rule="W-EV-01",
        rules_fired=[],
        source_taxonomy="gohar/evidence_validity/data-drift",
        section_6_7_mapping="W-EV-01",
        coverage_intent="gap_probe",
        subtlety="medium",
    ),
    _MockCase(
        case_id="adv-2026-p2-001-w-ar-01-v01",
        coverage_class="COV-HIT",
        coverage_class_raw="COV-HIT-PLUS",
        expected_rule="W-AR-01",
        rules_fired=["W-AR-01", "W-AR-05", "W-EP-01"],
        source_taxonomy="jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
        section_6_7_mapping=None,
        coverage_intent="confirm_existing",
        subtlety="high",
    ),
    _MockCase(
        case_id="adv-2026-p2-005-w-ep-01-v02",
        coverage_class="COV-WRONG",
        coverage_class_raw="COV-WRONG",
        expected_rule="W-EP-01",
        rules_fired=["W-EP-03"],
        source_taxonomy="jarzebowicz-wardzinski/evidence_defeaters/E2-stale-evidence",
        section_6_7_mapping=None,
        coverage_intent="confirm_existing",
        subtlety="high",
    ),
    _MockCase(
        case_id="adv-2026-p2-200-clean-cou-v01",
        coverage_class="COV-WRONG",
        coverage_class_raw="COV-CLEAN-WRONG",
        expected_rule=None,
        rules_fired=["W-AL-02"],
        source_taxonomy="negative_control/clean_morrison_cou1",
        section_6_7_mapping=None,
        coverage_intent="negative_control",
        subtlety="low",
    ),
    _MockCase(
        case_id="adv-2026-p2-115-configuration-v03",
        coverage_class="GEN-INVALID",
        coverage_class_raw="GEN-INVALID",
        expected_rule="W-CX-01",
        rules_fired=[],
        source_taxonomy="gohar/contextual/configuration",
        section_6_7_mapping="W-CX-01",
        coverage_intent="gap_probe",
        subtlety="medium",
    ),
]


def _manifest_dict() -> dict:
    """Build the §2.1 manifest.json contents for the mock bundle."""
    distribution: dict[str, int] = {}
    for case in MOCK_CASES:
        distribution[case.coverage_class] = distribution.get(case.coverage_class, 0) + 1

    return {
        "phase2_spec_version": "1.3",
        "generated_at": "2026-05-04T00:00:00Z",
        "generator_provenance": {
            "generator_model": MOCK_GENERATOR_MODEL,
            "phase2_tag": MOCK_PHASE2_TAG,
        },
        "package_count": MOCK_PACKAGE_COUNT,
        "coverage_class_distribution": distribution,
        "source_taxonomies": sorted({c.source_taxonomy.split("/")[0] for c in MOCK_CASES}),
        "experimental_factors": {
            "subtlety_levels": ["low", "medium", "high"],
            "base_cous": ["morrison_cou1", "morrison_cou2", "nagaraja_cou1"],
            "model_families": ["claude"],
            "prompt_paraphrase_versions": ["v01", "v02", "v03"],
        },
    }


def _package_jsonld(case: _MockCase) -> dict:
    """Minimal JSON-LD that round-trips through the bundle reader.

    Real Phase 2 packages are far richer; this fixture keeps the structure
    minimal so reader tests focus on bundle plumbing, not graph parsing.
    """
    return {
        "@context": "https://uofa.net/context/v0.4.jsonld",
        "@type": "EvidencePackage",
        "spec_id": case.case_id,
        "source_taxonomy": case.source_taxonomy,
        "coverage_intent": case.coverage_intent,
        "subtlety": case.subtlety,
        "_mock_fixture": True,
    }


def _outcome_json(case: _MockCase) -> dict:
    """Per-package .outcome.json matching spec §2.1 schema with class normalization extras."""
    return {
        "case_id": case.case_id,
        "coverage_class": case.coverage_class,  # normalized
        "phase2_outcome_class_raw": case.coverage_class_raw,  # provenance
        "expected_rule": case.expected_rule,
        "rules_fired": list(case.rules_fired),
        "source_taxonomy": case.source_taxonomy,
        "section_6_7_mapping": case.section_6_7_mapping,
        "experimental_factors": {
            "subtlety_level": case.subtlety,
            "base_cou": "morrison_cou1",
            "model_family": "claude",
            "prompt_paraphrase_version": "v01",
        },
    }


_MATRIX_CSV = (
    "pattern,subtlety,hit_rate,hits,total\n"
    "W-AR-01,high,1.000,1,1\n"
)

_SUMMARY_CSV = (
    "pattern_id,confirm_existing_count,confirm_existing_hits,recall\n"
    "W-AR-01,1,1,1.000\n"
)


def write_mock_bundle(out_path: Path) -> Path:
    """Write a 5-case judge_ready_bundle.tgz to `out_path` and return it.

    The tar contains:
        judge_ready_bundle/manifest.json
        judge_ready_bundle/packages/<case_id>.jsonld
        judge_ready_bundle/packages/<case_id>.outcome.json
        judge_ready_bundle/coverage/matrix.csv
        judge_ready_bundle/coverage/summary.csv

    `out_path` is created if missing. The function is idempotent: rerunning
    overwrites the existing bundle.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(out_path, "w:gz") as tf:
        _add_member(tf, "judge_ready_bundle/manifest.json", json.dumps(_manifest_dict(), indent=2))

        for case in MOCK_CASES:
            _add_member(
                tf,
                f"judge_ready_bundle/packages/{case.case_id}.jsonld",
                json.dumps(_package_jsonld(case), indent=2),
            )
            _add_member(
                tf,
                f"judge_ready_bundle/packages/{case.case_id}.outcome.json",
                json.dumps(_outcome_json(case), indent=2),
            )

        _add_member(tf, "judge_ready_bundle/coverage/matrix.csv", _MATRIX_CSV)
        _add_member(tf, "judge_ready_bundle/coverage/summary.csv", _SUMMARY_CSV)

    return out_path


def _add_member(tf: tarfile.TarFile, name: str, payload: str) -> None:
    data = payload.encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tf.addfile(info, BytesIO(data))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m tests.adversarial.judge.fixtures.mock_bundle <out.tgz>", file=sys.stderr)
        sys.exit(2)
    p = write_mock_bundle(Path(sys.argv[1]))
    print(f"wrote {MOCK_PACKAGE_COUNT}-case mock bundle to {p}")
