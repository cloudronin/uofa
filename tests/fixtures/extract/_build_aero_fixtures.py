"""Generate pre-canned aero COU1/COU2 JSON-LD fixtures for C3 rule-engine tests.

These fixtures are NOT produced by the live pipeline. They are hand-crafted
minimal UofA documents whose factor state mirrors the intentional-gap profile
in each COU's ground truth. They exist so the C3 rule engine can be tested
independently of the LLM extraction non-determinism.

Emitted files (committed):
    tests/fixtures/extract/aero-cou1-imported.jsonld  (4 intentional gaps)
    tests/fixtures/extract/aero-cou2-imported.jsonld  (5 not-assessed factors)

Every assessed factor is populated with acceptanceCriteria to avoid
W-AR-01 mass-fire drowning out the signal. Validation results are populated
with prov:wasGeneratedBy, comparedAgainst, and hasUncertaintyQuantification
so W-EP-02 / W-AR-05 / W-AL-01 do not fire.

Run:
    python tests/fixtures/extract/_build_aero_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

CTX = "../../../spec/context/v0.5.jsonld"  # relative to the fixture file

# All 19 NASA-STD-7009B factor names in canonical order
VV40_FACTORS = [
    "Software quality assurance",
    "Numerical code verification",
    "Discretization error",
    "Numerical solver error",
    "Use error",
    "Model form",
    "Model inputs",
    "Test samples",
    "Test conditions",
    "Equivalency of input parameters",
    "Output comparison",
    "Relevance of the quantities of interest",
    "Relevance of the validation activities to the COU",
]
NASA_ONLY_FACTORS = [
    "Data pedigree",
    "Development technical review",
    "Development process and product management",
    "Results uncertainty",
    "Results robustness",
    "Use history",
]

# category -> NASA assessmentPhase (for the 6 NASA-only factors)
NASA_PHASE_BY_FACTOR = {
    "Data pedigree": "capability",
    "Development technical review": "capability",
    "Development process and product management": "capability",
    "Results uncertainty": "results",
    "Results robustness": "results",
    "Use history": "capability",
}


def _factor(
    factor_type: str,
    status: str = "assessed",
    required: int | None = None,
    achieved: int | None = None,
    acceptance_criteria: str = "Factor meets required level per NASA-STD-7009B CAS scale.",
    rationale: str = "See credibility assessment narrative for evidence summary.",
) -> dict:
    f: dict = {
        "type": "CredibilityFactor",
        "factorType": factor_type,
        "factorStatus": status,
    }
    # factorStandard
    if factor_type in NASA_ONLY_FACTORS:
        f["factorStandard"] = "NASA-STD-7009B"
        f["assessmentPhase"] = NASA_PHASE_BY_FACTOR[factor_type]
    else:
        f["factorStandard"] = "ASME-VV40-2018"
    if required is not None:
        f["requiredLevel"] = required
    if achieved is not None:
        f["achievedLevel"] = achieved
    # Populate acceptanceCriteria whenever requiredLevel is set, so W-AR-01 doesn't
    # mass-fire and drown out the intentional weakener signal.
    if required is not None:
        f["acceptanceCriteria"] = acceptance_criteria
    if status == "assessed":
        f["rationale"] = rationale
    return f


def _cou1_factors() -> list[dict]:
    # Per aero-cou1-nasa7009b.json: 3 level-gaps (factors 3, 13 merged, decision
    # Accepted) + 1 not-assessed (factor 17). All others meet required level.
    gaps = {
        "Discretization error":                                (3, 1),
        "Relevance of the validation activities to the COU":   (3, 1),
    }
    not_assessed = {"Results uncertainty"}
    # Default (required, achieved) for all other factors — meeting required
    defaults = {
        "Software quality assurance":                    (2, 2),
        "Numerical code verification":                   (3, 3),
        "Numerical solver error":                        (2, 1),
        "Use error":                                     (2, 2),
        "Model form":                                    (3, 3),
        "Model inputs":                                  (3, 3),
        "Test samples":                                  (2, 2),
        "Test conditions":                               (3, 3),
        "Equivalency of input parameters":               (2, 2),
        "Output comparison":                             (3, 3),
        "Relevance of the quantities of interest":       (2, 2),
        "Data pedigree":                                 (3, 3),
        "Development technical review":                  (3, 3),
        "Development process and product management":    (2, 2),
        "Results robustness":                            (2, 2),
        "Use history":                                   (2, 2),
    }
    all_factors = []
    for name in VV40_FACTORS + NASA_ONLY_FACTORS:
        if name in not_assessed:
            all_factors.append(_factor(name, status="not-assessed", required=3))
        elif name in gaps:
            req, ach = gaps[name]
            all_factors.append(_factor(name, required=req, achieved=ach))
        else:
            req, ach = defaults[name]
            all_factors.append(_factor(name, required=req, achieved=ach))
    return all_factors


def _cou2_factors() -> list[dict]:
    # Per aero-cou2-nasa7009b.json: 5 not-assessed factors (6, 9, 10, 11, 13)
    # Decision: Not Accepted. MRL 4.
    not_assessed = {
        "Model form",
        "Test conditions",
        "Equivalency of input parameters",
        "Output comparison",
        "Relevance of the validation activities to the COU",
    }
    # All other factors at their assessed level (matching ground truth)
    assessed_levels = {
        "Software quality assurance":                    (2, 2),
        "Numerical code verification":                   (3, 3),
        "Discretization error":                          (3, 3),
        "Numerical solver error":                        (2, 2),
        "Use error":                                     (2, 2),
        "Model inputs":                                  (3, 3),
        "Test samples":                                  (2, 2),
        "Relevance of the quantities of interest":       (3, 3),
        "Data pedigree":                                 (3, 3),
        "Development technical review":                  (3, 3),
        "Development process and product management":    (3, 3),
        "Results uncertainty":                           (3, 2),
        "Results robustness":                            (2, 2),
        "Use history":                                   (2, 1),
    }
    all_factors = []
    for name in VV40_FACTORS + NASA_ONLY_FACTORS:
        if name in not_assessed:
            all_factors.append(_factor(name, status="not-assessed", required=3))
        else:
            req, ach = assessed_levels[name]
            all_factors.append(_factor(name, required=req, achieved=ach))
    return all_factors


def _validation_result(iri: str, name: str, compared_to: str, uq_iri: str) -> dict:
    return {
        "id": iri,
        "type": "ValidationResult",
        "name": name,
        "prov:wasGeneratedBy": {"id": f"{iri}/activity"},
        "comparedAgainst": {"id": compared_to},
        "hasUncertaintyQuantification": {"id": uq_iri},
    }


def _build(
    output_path: Path,
    iri_base: str,
    cou_name: str,
    mrl: int,
    outcome: str,
    factors: list[dict],
    summary_qualifier: str,
) -> None:
    doc = {
        "@context": CTX,
        "id": f"{iri_base}",
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileComplete",
        "name": f"{cou_name} — NASA-STD-7009B credibility assessment",
        "bindsRequirement": f"{iri_base}/req/primary",
        "bindsClaim": {
            "id": f"{iri_base}/claim/primary",
            "type": "Claim",
            "prov:wasDerivedFrom": {"id": f"{iri_base}/source/narrative"},
        },
        "bindsModel": f"{iri_base}/model/cfx-cht",
        "bindsDataset": [f"{iri_base}/data/cascade-rig"],
        "hasContextOfUse": {
            "id": f"{iri_base}/cou",
            "type": "ContextOfUse",
            "name": cou_name,
            "modelRiskLevel": mrl,
        },
        "hasValidationResult": [
            _validation_result(
                f"{iri_base}/validation/cascade",
                f"Cascade rig comparison for {cou_name}",
                f"{iri_base}/data/cascade-rig",
                f"{iri_base}/uq/cascade",
            ),
        ],
        "wasDerivedFrom": f"{iri_base}/report/credibility",
        "wasAttributedTo": f"{iri_base}/org/propulsion",
        "generatedAtTime": "2026-04-18T00:00:00Z",
        "hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        "signature": "ed25519:0000000000000000000000000000000000000000000000000000000000000000" + "0" * 64,
        "signatureAlg": "ed25519",
        "canonicalizationAlg": "RDFC-1.0",
        "hasCredibilityFactor": factors,
        "hasWeakener": [],
        "hasDecisionRecord": {
            "id": f"{iri_base}/decision/primary",
            "type": "DecisionRecord",
            "actor": f"{iri_base}/org/propulsion",
            "outcome": outcome,
            "rationale": f"{summary_qualifier}.",
            "decidedAt": "2026-04-10T00:00:00Z",
        },
        "assuranceLevel": "Medium" if mrl < 4 else "High",
        "criteriaSet": "https://uofa.net/criteria/NASA-STD-7009B",
        "modelRiskLevel": mrl,
        "couName": cou_name,
        "decision": outcome,
        "hasUncertaintyQuantification": True,
    }
    output_path.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {output_path} ({len(factors)} factors, outcome={outcome!r})")


def main() -> None:
    out_dir = Path(__file__).parent
    _build(
        out_dir / "aero-cou1-imported.jsonld",
        iri_base="https://uofa.net/aero-cou1",
        cou_name="Take-off peak metal temperature prediction",
        mrl=3,
        outcome="Accepted",
        factors=_cou1_factors(),
        summary_qualifier="Accepted with conditions for preliminary screening",
    )
    _build(
        out_dir / "aero-cou2-imported.jsonld",
        iri_base="https://uofa.net/aero-cou2",
        cou_name="Cruise peak temperature and creep-life prediction",
        mrl=4,
        outcome="Not Accepted",
        factors=_cou2_factors(),
        summary_qualifier="Cruise-regime validation evidence required before MRL 4 acceptance",
    )


if __name__ == "__main__":
    main()
