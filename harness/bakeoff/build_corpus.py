"""Generate the bakeoff corpus — hardened, conflicting-signal cells.

Single source of truth for ``harness/bakeoff/corpus/*.json``. Every cell is a
**conflicting-signal hard cell**: the obvious feature points the WRONG way (the
§5A dangerous-OK property), so the correct disposition is not latchable from one
feature. ``build_corpus.py`` enforces this — ``hardness_violations()`` rejects any
cell whose obvious-signal posture equals the gold posture (an easy cell), and the
test suite asserts the same.

Provenance honesty (the addendum):
- ``gold_mechanism`` is paper- or standard-grounded (real citation per cell).
- ``gold_action.posture_basis`` (block vs proceed) is **standard-derived** — ASME
  V&V 40 bounds credibility to the validated domain, so proceeding outside it is
  the dangerous error regardless of taste.
- ``gold_action.selection_basis`` (the specific §5B class among coherent ones) is
  **provisional-self-adjudicated** — the row-builder's reasoning, NOT independent.
  This slice is explanation-gate-ready; before it doubles as the disposition-gate
  slice the selections need expert/solver-derived re-adjudication.

Run: ``python -m harness.bakeoff.build_corpus``  (writes corpus/, prints a summary).
"""

from __future__ import annotations

import json
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"

FIRE_INSTR = (
    "A weakener fired on a credibility evidence package. Using ONLY the supplied pattern "
    "definition and measures, explain what the flag means, why it fired, and what the engineer "
    "should do. Choose ONE action_class from the §5B vocabulary, report a verbalized confidence, "
    "and escalate if uncertain. Stay within measure-don't-judge: report on the evidence package, "
    "never on whether the model is correct."
)
CONTROL_INSTR = (
    "Assess whether the evidence package has the gap this pattern describes. If the package is "
    "complete for this COU, the correct disposition is to accept — do NOT over-act on an alarming-"
    "looking but adequately-addressed signal. Choose ONE action_class from the §5B vocabulary, "
    "report a verbalized confidence, and escalate if uncertain. Stay within measure-don't-judge."
)

# §5B postures: BLOCK actions do not proceed on the surrogate; PROCEED actions do.
BLOCK = {"supply-evidence", "acquire-validation", "restrict-cou", "reject"}
PROCEED = {"accept-residual-risk", "accept", "none"}


def _posture(action_class: str) -> str:
    return "block" if action_class in BLOCK else "proceed"


def build_row(c: dict) -> dict:
    polarity = c["polarity"]
    gold_class = c["gold"]["class"]
    return {
        "row_id": c["id"],
        "split": "control" if polarity == "suppress" else "train:hard-core",
        "hard_core": True,
        "strata": {
            "d_category": c["dcat"], "backbone": c["backbone"], "measure_type": c["mdims"],
            "domain": c["domain"], "polarity": polarity, "archetype": c["archetype"],
        },
        "input": {
            "instruction": CONTROL_INSTR if polarity == "suppress" else FIRE_INSTR,
            "fired_pattern": {
                "id": c["pattern"][0], "d_category": c["dcat"], "interface": "weakener-interface@1",
                "definition": c["pattern"][1], "standard_anchor": c["anchor"],
            },
            "measures": c["measures"],
            # De-named rendering: the SAME information as raw signals/numbers, with the
            # conclusion-bearing field names removed, so the model must INFER the gap.
            # This is the fair test of the catalog's detection lift (ablation --measures raw).
            "measures_raw": RAW_MEASURES.get(c["id"], c["measures"]),
            "case_context": c["context"],
        },
        "answer_key": {
            "gold_mechanism": c["mechanism"],
            "gold_action": {
                "selected_class": gold_class,
                "allowed_classes": c["gold"]["allowed"],
                "coherent_alternatives": c["gold"].get("alts", []),
                "posture_basis": "standard-derived (ASME V&V 40: credibility bounded to the validated domain)",
                "selection_basis": "provisional-self-adjudicated",
                "parameters": c["gold"]["params"],
            },
            "forbidden_claims": c["forbidden"],
            "acceptable_confidence": c["acc_conf"],
        },
        "hardness": {
            "obvious_signal": c["obvious"][0],
            "obvious_posture": c["obvious"][1],
            "conflicting_signal": c["conflicting"],
            "gold_posture": _posture(gold_class),
        },
        "label_provenance": {
            "external_grounding": c["grounding"],
            "by_field": {
                "gold_mechanism": c.get("mech_prov", "paper/standard-grounded"),
                "gold_action.posture": "standard-derived (V&V 40 applicability)",
                "gold_action.selected_class": (
                    "provisional-self-adjudicated (row-builder; needs independent expert/"
                    "solver adjudication before disposition-gate use)"),
            },
            "not_sourced_from": ["pipeline output", "frontier model draft"],
        },
    }


def hardness_violations(cells: list[dict]) -> list[str]:
    """Cells where the obvious feature does NOT point the wrong way (i.e. easy)."""
    bad = []
    for c in cells:
        gold_posture = _posture(c["gold"]["class"])
        if c["obvious"][1] == gold_posture:
            bad.append(f"{c['id']}: obvious posture '{c['obvious'][1]}' == gold posture (not a hard cell)")
        if c["gold"]["class"] not in BLOCK | PROCEED:
            bad.append(f"{c['id']}: gold class '{c['gold']['class']}' not in the §5B vocabulary")
    return bad


# ── The cells. Each is a conflicting-signal hard cell (obvious feature → wrong). ──
# fp(): a fired-pattern (id, definition). Kept short; the standard_anchor carries the source.
def fp(pid, defn):
    return (pid, defn)


CELLS: list[dict] = [
    # ── Archetype: global-pass / local-inadequate (the §5A dangerous-OK family) ──
    {
        "id": "surr-dpd02-carbench-wheelhousing", "dcat": "D-PD-02", "backbone": "applicability",
        "mdims": ["global-geometry-OOD", "per-region-competence"], "domain": "automotive-aero-CFD",
        "polarity": "fire", "archetype": "global-pass-local-inadequate",
        "pattern": fp("W-SURR-03", "Per-region competence not characterized: a known high-variance region is not flagged out-of-competence even when the input is globally in-envelope."),
        "anchor": "ASME V&V 40 applicability; proto-taxonomy D-PD-02 (Jakeman arXiv:2502.15496)",
        "obvious": ("global geometry-OOD reads 41st percentile, in-distribution", "proceed"),
        "conflicting": "the wheel-housing is a known high-variance region with per-region competence ABSENT and elevated regional ensemble variance not propagated to the COU",
        "measures": {"geometry_OOD_percentile": 0.41, "global_envelope": "in-distribution",
                     "region_of_interest": "wheel-housing", "per_region_competence_characterized": False,
                     "ensemble_variance_region": "elevated, not propagated to COU"},
        "context": {"cou": "surrogate informs a drag-sensitivity decision; wheel-housing flow contributes to the QoI",
                    "model_influence": "medium-high", "decision_consequence": "design change carried forward"},
        "mechanism": "Global in-envelope status does not establish local competence in a known high-variance region; per-region characterization is absent for a region the COU depends on.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "wheel-housing region", "against": "solver-truth"}},
        "forbidden": ["asserts the surrogate is inaccurate in the region (a verdict the flag does not support)",
                      "treats the 41st-percentile global pass as competence evidence for the region"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "CarBench (arXiv:2512.07847) + DrivAerML solver truth: wheel-housing is a high-variance regime with elevated regional error despite global in-envelope status.",
        "mech_prov": "solver-derived (CarBench/DrivAerML)",
    },
    {
        "id": "surr-dpd02-turbine-tipgap", "dcat": "D-PD-02", "backbone": "applicability",
        "mdims": ["global-geometry-OOD", "per-region-competence"], "domain": "turbomachinery-CHT",
        "polarity": "fire", "archetype": "global-pass-local-inadequate",
        "pattern": fp("W-SURR-03", "Per-region competence not characterized for a region the COU depends on, despite a global in-envelope status."),
        "anchor": "ASME V&V 40 applicability; NASA-STD-7009B; proto-taxonomy D-PD-02",
        "obvious": ("global operating point sits well inside the validated envelope", "proceed"),
        "conflicting": "the blade tip-gap region drives the heat-transfer QoI and was excluded from the validation set; local secondary-flow competence is uncharacterized",
        "measures": {"global_envelope": "in-distribution", "region_of_interest": "blade-tip-gap",
                     "per_region_competence_characterized": False, "qoi_driver_region": "tip-gap secondary flow",
                     "region_in_validation_set": False},
        "context": {"cou": "surrogate predicts blade metal temperature for a life-assessment decision",
                    "model_influence": "high", "decision_consequence": "component life margin set on the prediction"},
        "mechanism": "The tip-gap region drives the heat-transfer QoI but is absent from the validation set, so local applicability is not established even though the global operating point is in-envelope.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "tip-gap region", "against": "solver-truth or rig data"}},
        "forbidden": ["asserts the surrogate under-predicts tip temperature (a correctness verdict)",
                      "treats the global in-envelope status as competence for the tip-gap region"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 applicability + turbomachinery V&V practice: heat-transfer credibility is region-specific; global envelope status does not transfer to an unvalidated driver region.",
        "mech_prov": "standard-grounded (V&V 40 applicability)",
    },
    # ── Archetype: low-aggregate-error / high-fine-scale-failure (spectral bias) ──
    {
        "id": "surr-dval09-fno-spectral", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["aggregate-error", "spectral-residual"], "domain": "PDE-operator-learning",
        "polarity": "fire", "archetype": "low-aggregate-high-finescale",
        "pattern": fp("W-SURR-04", "Validation metric does not resolve the QoI-relevant scale: a low aggregate error coexists with an uncharacterized high-frequency residual the COU depends on."),
        "anchor": "ASME V&V 40 validation metric tied to purpose; proto-taxonomy D-VAL-09 / D-VER-06",
        "obvious": ("aggregate relative-L2 validation error is low (0.03) — looks accurate", "proceed"),
        "conflicting": "FNO spectral bias: large scales captured (hence low aggregate L2) but the high-frequency band is unresolved, and the COU's QoI depends on that fine-scale structure",
        "measures": {"validation_relative_L2": 0.03, "metric_band": "all-scales aggregate",
                     "high_band_spectral_residual": "elevated (40% of high-band energy unresolved)",
                     "cou_depends_on_fine_scale": True},
        "context": {"cou": "FNO predicts a turbulence field; fine-scale mixing sizes a component",
                    "model_influence": "high", "decision_consequence": "component sizing on the field"},
        "mechanism": "The aggregate L2 metric is dominated by large scales and reads low, but FNO spectral bias leaves the high-frequency band — which the QoI depends on — unresolved, so the validation metric is not tied to the COU's purpose.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "the fine-scale / high-frequency band", "against": "a band-resolved reference"}},
        "forbidden": ["asserts the surrogate's fine-scale field is wrong (a verdict the metric does not support)",
                      "treats the low aggregate L2 as evidence of fine-scale accuracy"],
        "acc_conf": ["high", "medium", "0.65-0.92"],
        "grounding": "Failure modes of Fourier Neural Operators (arXiv:2601.11428): FNOs capture large scales (low aggregate error) but miss fine-scale oscillations.",
        "mech_prov": "paper-grounded (FNO spectral bias)",
    },
    {
        "id": "surr-dval08-climate-tails", "dcat": "D-VAL-08", "backbone": "validation-support",
        "mdims": ["aggregate-skill", "tail-coverage"], "domain": "climate-emulator",
        "polarity": "fire", "archetype": "low-aggregate-high-finescale",
        "pattern": fp("W-SURR-04", "Validation against purpose-specific criteria absent: aggregate skill is high but the decision-relevant regime (extreme tails) is not validated."),
        "anchor": "ASME V&V 40 purpose-specific validation; proto-taxonomy D-VAL-08",
        "obvious": ("overall RMSE skill score is excellent (0.96) across the record", "proceed"),
        "conflicting": "the COU is an extreme-event (tail) decision, and tail skill is not reported; aggregate RMSE is dominated by the well-sampled bulk and is blind to rare extremes",
        "measures": {"aggregate_skill_score": 0.96, "metric": "bulk RMSE skill",
                     "tail_event_skill_reported": False, "cou_regime": "99.9th-percentile extremes"},
        "context": {"cou": "emulator screens a climate-risk adaptation decision keyed to extreme events",
                    "model_influence": "high", "decision_consequence": "adaptation investment screened on the emulator"},
        "mechanism": "Aggregate skill is dominated by the well-sampled bulk and does not validate the extreme-tail regime the COU's decision depends on; purpose-specific validation for the decision regime is absent.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou", "supply-evidence"], "params": {"scope": "extreme-tail regime", "against": "held-out extreme events"}},
        "forbidden": ["asserts the emulator is unskilled at extremes (a verdict the evidence does not support)",
                      "treats the high aggregate skill as validation for the tail decision"],
        "acc_conf": ["high", "0.75-0.95"],
        "grounding": "ASME V&V 40 purpose-specific validation: the metric must be tied to the decision; aggregate skill is not evidence for an unvalidated decision-relevant regime.",
        "mech_prov": "standard-grounded (V&V 40 purpose-specific validation)",
    },
    # ── Archetype: in-distribution-calibrated / out-of-distribution-use ──
    {
        "id": "surr-dval09-ensemble-mismatch", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["uq-calibration", "train-test-mismatch"], "domain": "PDE-surrogate",
        "polarity": "fire", "archetype": "indist-calibrated-ood-use",
        "pattern": fp("W-AL-02", "Prediction UQ validated only in-distribution while the COU extrapolates: the reported coverage does not cover the regime the decision uses."),
        "anchor": "ASME V&V 40 uncertainty; proto-taxonomy D-VAL-09",
        "obvious": ("reported in-distribution interval coverage is 0.91 vs nominal 0.90 — looks calibrated", "proceed"),
        "conflicting": "coverage was measured in-distribution, the COU is a mild extrapolation, and deep ensembles underdisperse precisely under train-test mismatch — so the calibration does not transfer",
        "measures": {"surrogateUQMethod": "deep-ensemble", "in_distribution_coverage": 0.91, "nominal": 0.90,
                     "cou_regime": "mild extrapolation (outside the calibration distribution)",
                     "coverage_under_extrapolation": "not measured", "variance_trend": "decreases with members"},
        "context": {"cou": "the UQ band sets a safety margin at an operating point beyond the calibration set",
                    "model_influence": "high", "decision_consequence": "safety margin from the reported band"},
        "mechanism": "The interval coverage was validated in-distribution, but the COU extrapolates and deep ensembles underdisperse under train-test mismatch, so the in-distribution calibration is not evidence of coverage in the COU's regime.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "supply-evidence", "restrict-cou"],
                 "alts": ["restrict-cou"], "params": {"scope": "coverage in the extrapolation regime", "against": "held-out error at the COU operating point"}},
        "forbidden": ["asserts the mean prediction is inaccurate (a verdict the flag does not support)",
                      "treats in-distribution coverage as a coverage guarantee in the extrapolation regime"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "Calibration-aware uncertainty for neural PDE surrogates (arXiv:2602.11090): ensembles lack a mechanism to calibrate against train-test mismatch; UQ and Deep Ensembles (arXiv:2007.08792): ensembles underdisperse.",
        "mech_prov": "paper-grounded (ensemble underdispersion under mismatch)",
    },
    {
        "id": "surr-dval09-mlip-ood-config", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["uq-calibration", "train-test-mismatch"], "domain": "interatomic-potential",
        "polarity": "fire", "archetype": "indist-calibrated-ood-use",
        "pattern": fp("W-AL-02", "Ensemble UQ calibrated on in-distribution configurations while the COU samples novel configurations the ensemble has not been calibrated against."),
        "anchor": "ASME V&V 40 uncertainty; proto-taxonomy D-VAL-09",
        "obvious": ("the ensemble's force-error calibration looks good on the held-out test split", "proceed"),
        "conflicting": "the held-out split is drawn from the same equilibrium configurations; the COU samples high-energy transition states (a different distribution) where ML interatomic-potential ensembles are known to be overconfident",
        "measures": {"surrogateUQMethod": "deep-ensemble", "test_split_calibration": "good (ECE 0.02)",
                     "test_split_distribution": "near-equilibrium configurations",
                     "cou_distribution": "high-energy transition states", "calibration_on_cou_distribution": "absent"},
        "context": {"cou": "the potential drives a reaction-rate estimate over transition states",
                    "model_influence": "high", "decision_consequence": "reaction pathway selected on the estimate"},
        "mechanism": "Calibration was measured on near-equilibrium configurations; the COU samples transition states from a different distribution where the ensemble is uncalibrated, so the test-split ECE does not bound the COU's uncertainty.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "transition-state configurations", "against": "reference electronic-structure forces"}},
        "forbidden": ["asserts the potential's transition-state forces are wrong (a verdict the evidence does not support)",
                      "treats equilibrium-split calibration as calibration for transition states"],
        "acc_conf": ["high", "0.75-0.93"],
        "grounding": "BNN vs deep ensembles for UQ in ML interatomic potentials (arXiv:2509.19180): ensemble UQ is distribution-dependent and overconfident off-distribution.",
        "mech_prov": "paper-grounded (MLIP ensemble UQ off-distribution)",
    },
    # ── Archetype: excellent-fit / physics-constraint-violation ──
    {
        "id": "surr-dpd04-pinn-massresidual", "dcat": "D-PD-04", "backbone": "structure-support",
        "mdims": ["fit-metric", "physics-constraint-residual"], "domain": "reacting-flow-surrogate",
        "polarity": "fire", "archetype": "great-fit-physics-violation",
        "pattern": fp("W-SURR-01", "Declared governing constraint present but constraint-check evidence shows a violation the fit metric hides: low data error coexists with a large conservation residual."),
        "anchor": "ASME V&V 40 model-form; proto-taxonomy D-PD-04 (governing constraints)",
        "obvious": ("pointwise field R^2 against data is excellent (0.995) — the fit looks great", "proceed"),
        "conflicting": "the declared mass-conservation constraint residual is large (continuity violated by ~8%), which a pointwise R^2 against sparse data does not penalize",
        "measures": {"field_R2_vs_data": 0.995, "declared_constraint": "mass-conservation",
                     "continuity_residual_integral": 0.08, "constraint_check_evidence": "violation, not reconciled",
                     "data_sparsity": "sparse pointwise samples"},
        "context": {"cou": "surrogate predicts species fields feeding an emissions estimate",
                    "model_influence": "high", "decision_consequence": "emissions compliance argued on the fields"},
        "mechanism": "A high pointwise R^2 against sparse data does not enforce the declared conservation law; the integral continuity residual is large, so the model violates a governing constraint the COU's QoI depends on despite the excellent data fit.",
        "gold": {"class": "supply-evidence", "allowed": ["supply-evidence", "acquire-validation", "restrict-cou", "reject"],
                 "alts": ["acquire-validation"], "params": {"scope": "mass-conservation reconciliation", "against": "the declared constraint"}},
        "forbidden": ["asserts the species fields are quantitatively wrong (a verdict beyond the residual)",
                      "treats the high R^2 as evidence the conservation law holds"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 model-form adequacy + PINN/physics-ML practice: data fit does not imply constraint satisfaction; an unreconciled conservation residual is a model-form defeater.",
        "mech_prov": "standard-grounded (V&V 40 model-form) + physics-ML principle",
    },
    # ── Archetype: code-verified / solution-unverified ──
    {
        "id": "surr-dver05-mms-only", "dcat": "D-VER-05", "backbone": "verification-support",
        "mdims": ["code-verification", "solution-verification"], "domain": "structural-FEA-surrogate",
        "polarity": "fire", "archetype": "code-verified-solution-unverified",
        "pattern": fp("W-SURR-04", "Code-verification evidence present but solution-verification on the application domain absent: MMS/idealized tests passed, application-domain residuals unlinked."),
        "anchor": "ASME V&V 40 verification levels; proto-taxonomy D-VER-05 / D-VER-06",
        "obvious": ("a manufactured-solution (MMS) verification suite passes at expected order — verification looks done", "proceed"),
        "conflicting": "MMS exercises the discretization, not the application geometry/loads; solution-verification (residuals against a reference on the COU's actual configuration) is absent",
        "measures": {"code_verification_MMS": "passed at expected order", "solution_verification_on_cou": "absent",
                     "application_residuals_linked": False, "cou_configuration": "notched component under combined load"},
        "context": {"cou": "surrogate predicts a stress concentration for a fatigue decision",
                    "model_influence": "high", "decision_consequence": "fatigue life argued on the stress field"},
        "mechanism": "Code verification (MMS) establishes the solver's order of accuracy but not solution accuracy on the application configuration; solution-verification evidence for the COU's geometry/loads is absent, so verification does not cover the decision.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "supply-evidence", "restrict-cou"],
                 "alts": ["supply-evidence"], "params": {"scope": "solution-verification on the COU configuration", "against": "a reference solution"}},
        "forbidden": ["asserts the stress prediction is wrong (a verdict the verification gap does not support)",
                      "treats passing MMS as solution-verification for the application"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 10/40 verification hierarchy: code verification (MMS) and solution verification are distinct; passing one is not evidence for the other.",
        "mech_prov": "standard-grounded (V&V 40 verification levels)",
    },
    # ── Archetype: benchmark-spans-on-average / COU-cell-unsampled ──
    {
        "id": "surr-dver06-coverage-hole", "dcat": "D-VER-06", "backbone": "verification-support",
        "mdims": ["benchmark-coverage", "design-of-experiments"], "domain": "external-aero-CFD",
        "polarity": "fire", "archetype": "spans-on-average-cell-empty",
        "pattern": fp("W-SURR-04", "Benchmark coverage gap at the COU cell: the benchmark spans the space on average but the specific decision-relevant cell is unsampled."),
        "anchor": "ASME V&V 40 application-domain coverage; proto-taxonomy D-VER-06",
        "obvious": ("the validation benchmark covers the full Reynolds x AoA box with good average density", "proceed"),
        "conflicting": "the COU's specific cell (high-Re, high-AoA corner) has zero benchmark samples — a coverage hole the average density statistic hides",
        "measures": {"benchmark_average_density": "good across the box", "cou_cell": "high-Re x high-AoA corner",
                     "cou_cell_sample_count": 0, "coverage_metric": "box-average, not per-cell"},
        "context": {"cou": "surrogate evaluated at the high-Re high-AoA corner for a stall-margin decision",
                    "model_influence": "high", "decision_consequence": "stall margin set on the surrogate"},
        "mechanism": "An average coverage statistic over the box hides a hole at the COU's specific cell, which has no benchmark samples; solution-verification therefore does not cover the decision point even though the benchmark spans the space on average.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "the COU cell (high-Re, high-AoA)", "against": "a reference at that cell"}},
        "forbidden": ["asserts the corner prediction is wrong (a verdict the coverage gap does not support)",
                      "treats good average coverage as coverage at the unsampled cell"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "AirfRANS (NeurIPS 2022): highest error at the parameter-space boundary / under-represented cells; average coverage is not per-cell coverage.",
        "mech_prov": "paper-grounded (AirfRANS boundary error) + DoE principle",
    },
    # ── Archetype: validation-present / data-leakage (optimistic) ──
    {
        "id": "surr-dval08-leakage", "dcat": "D-VAL-08", "backbone": "validation-support",
        "mdims": ["validation-independence", "data-provenance"], "domain": "data-driven-emulator",
        "polarity": "fire", "archetype": "validation-present-leakage",
        "pattern": fp("W-AR-05", "Validation against independent data not established: a low validation error coexists with evidence the validation set overlaps training (leakage)."),
        "anchor": "ASME V&V 40 independent validation data; proto-taxonomy D-VAL-08",
        "obvious": ("validation error is very low (1.2%) — the surrogate looks well-validated", "proceed"),
        "conflicting": "the validation split was drawn AFTER feature-normalization fit on the full set and shares simulation seeds with training, so the validation set is not independent (leakage inflates the score)",
        "measures": {"validation_error": 0.012, "split_independence": "compromised",
                     "normalization_fit_on": "full dataset (incl. validation)", "shared_seeds_train_val": True},
        "context": {"cou": "emulator validated for a sign-off on a design metric",
                    "model_influence": "high", "decision_consequence": "design sign-off on the validation score"},
        "mechanism": "The validation error is optimistic because the validation set is not independent of training (shared seeds, normalization fit on the full set), so the low score is not evidence of generalization to the COU.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "supply-evidence", "reject"],
                 "alts": ["supply-evidence"], "params": {"scope": "validation on a genuinely independent set", "against": "held-out, leakage-free data"}},
        "forbidden": ["asserts the emulator does not generalize (a verdict the leakage does not establish)",
                      "treats the low (leaked) validation error as evidence of independent validation"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "ASME V&V 40 requires validation against data independent of training; well-documented ML leakage modes (shared seeds, pre-split normalization) inflate validation scores.",
        "mech_prov": "standard-grounded (V&V 40 independence) + ML leakage principle",
    },
    # ── Archetype: aleatory-UQ-present / epistemic-missing ──
    {
        "id": "surr-dval09-aleatory-only", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["uq-completeness", "epistemic-uncertainty"], "domain": "PDE-surrogate",
        "polarity": "fire", "archetype": "aleatory-present-epistemic-missing",
        "pattern": fp("W-AL-02", "Only one uncertainty source reported: aleatory (data-noise) UQ present, but model-form / extrapolation (epistemic) uncertainty not propagated to the application domain."),
        "anchor": "ASME V&V 40 uncertainty completeness; proto-taxonomy D-VAL-09",
        "obvious": ("the surrogate reports prediction intervals — UQ is present and looks complete", "proceed"),
        "conflicting": "the reported intervals are aleatory only (output-noise); model-form and extrapolation (epistemic) uncertainty are not propagated, and the COU is near the training boundary where epistemic dominates",
        "measures": {"reported_uq": "aleatory (homoscedastic output noise)", "epistemic_uq_propagated": False,
                     "cou_location": "near training boundary", "dominant_uncertainty_at_cou": "epistemic (extrapolation)"},
        "context": {"cou": "intervals gate an acceptance decision near the training-domain edge",
                    "model_influence": "high", "decision_consequence": "acceptance on the reported intervals"},
        "mechanism": "The reported UQ captures only aleatory output noise; epistemic (model-form / extrapolation) uncertainty — which dominates near the training boundary the COU sits at — is not propagated, so the intervals understate the decision-relevant uncertainty.",
        "gold": {"class": "supply-evidence", "allowed": ["supply-evidence", "acquire-validation", "restrict-cou"],
                 "alts": ["acquire-validation"], "params": {"scope": "epistemic / extrapolation uncertainty", "against": "the declared application domain"}},
        "forbidden": ["asserts the prediction is over/under-confident as a fact (a verdict beyond the completeness gap)",
                      "treats the aleatory intervals as total predictive uncertainty"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 uncertainty completeness (D-VAL-09): prediction UQ must propagate extrapolation/structure uncertainty; aleatory-only UQ is incomplete near the domain edge.",
        "mech_prov": "standard-grounded (V&V 40 uncertainty completeness)",
    },
    # ── Archetype: recent-data / wrong-regime (vintage looks fresh, regime is off) ──
    {
        "id": "surr-dccb10-vintage-regime", "dcat": "D-CCB-10", "backbone": "data-support",
        "mdims": ["data-vintage", "regime-match"], "domain": "internal-flow-surrogate",
        "polarity": "fire", "archetype": "fresh-data-wrong-regime",
        "pattern": fp("W-EP-03", "Training-data fidelity/regime not matched to the COU: the data is recent but drawn from a different operating regime than the application."),
        "anchor": "ASME V&V 40 data adequacy; proto-taxonomy D-CCB-10 (data fidelity/vintage)",
        "obvious": ("the training data was collected last quarter — it is fresh / current", "proceed"),
        "conflicting": "freshness is not regime-match: the recent data is all from low-load operation while the COU is a high-load transient, so the recent data does not represent the application regime",
        "measures": {"data_vintage": "current (last quarter)", "training_regime": "steady low-load",
                     "cou_regime": "high-load transient", "regime_overlap": "minimal"},
        "context": {"cou": "surrogate predicts a transient response for a control-margin decision",
                    "model_influence": "high", "decision_consequence": "control margin on the predicted transient"},
        "mechanism": "Data recency is not the same as regime adequacy; the recent training data is from steady low-load operation, while the COU is a high-load transient — a regime the data does not represent — so the data is inadequate for the application despite being current.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "high-load transient regime", "against": "regime-representative data"}},
        "forbidden": ["asserts the transient prediction is wrong (a verdict the regime gap does not support)",
                      "treats data recency as evidence of regime adequacy"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 data adequacy (D-CCB-10): training-data fidelity must match the application regime; vintage/recency does not establish regime match.",
        "mech_prov": "standard-grounded (V&V 40 data adequacy)",
    },
    {
        "id": "surr-dpd02-thermal-hotspot", "dcat": "D-PD-02", "backbone": "applicability",
        "mdims": ["global-field-error", "per-region-competence"], "domain": "electronics-thermal-surrogate",
        "polarity": "fire", "archetype": "global-pass-local-inadequate",
        "pattern": fp("W-SURR-03", "Per-region competence not characterized: a local hotspot region the COU depends on is not validated even though the global field error is low."),
        "anchor": "ASME V&V 40 applicability; proto-taxonomy D-PD-02",
        "obvious": ("the board-level mean-temperature field error is low (1.5 C RMS) — looks accurate", "proceed"),
        "conflicting": "the junction-hotspot peak drives the reliability decision and the surrogate's peak-temperature error there is uncharacterized; a board-mean RMS is insensitive to a localized peak",
        "measures": {"global_field_RMS_error_C": 1.5, "region_of_interest": "junction hotspot",
                     "peak_temperature_error_characterized": False, "qoi": "peak junction temperature"},
        "context": {"cou": "surrogate predicts peak junction temperature for a reliability sign-off",
                    "model_influence": "high", "decision_consequence": "reliability sign-off on the peak"},
        "mechanism": "A low board-mean field RMS is insensitive to a localized hotspot; the surrogate's peak-temperature competence at the junction — which the reliability QoI depends on — is uncharacterized, so applicability for the decision region is not established.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "restrict-cou", "supply-evidence"],
                 "alts": ["restrict-cou"], "params": {"scope": "junction-hotspot peak temperature", "against": "reference thermal solution"}},
        "forbidden": ["asserts the peak temperature is under-predicted (a verdict the gap does not support)",
                      "treats the low global RMS as competence for the local peak"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 region-specific applicability: a global aggregate error does not establish local competence at a decision-driving hotspot.",
        "mech_prov": "standard-grounded (V&V 40 applicability)",
    },
    {
        "id": "surr-dpd04-energy-residual", "dcat": "D-PD-04", "backbone": "structure-support",
        "mdims": ["fit-metric", "physics-constraint-residual"], "domain": "thermal-fluid-surrogate",
        "polarity": "fire", "archetype": "great-fit-physics-violation",
        "pattern": fp("W-SURR-01", "Declared governing constraint present but constraint-check shows an energy-balance violation a fit metric hides."),
        "anchor": "ASME V&V 40 model-form; proto-taxonomy D-PD-04",
        "obvious": ("validation MAE on temperature is excellent (0.4%) — the surrogate looks accurate", "proceed"),
        "conflicting": "the declared energy-conservation constraint is violated (global energy imbalance ~6%), which a temperature MAE does not penalize and which biases derived heat-flux QoIs",
        "measures": {"temperature_MAE_pct": 0.4, "declared_constraint": "energy-conservation",
                     "global_energy_imbalance_pct": 6.0, "constraint_check_evidence": "violation, unreconciled",
                     "derived_qoi": "wall heat flux"},
        "context": {"cou": "surrogate's field feeds a wall-heat-flux QoI for a cooling-margin decision",
                    "model_influence": "high", "decision_consequence": "cooling margin from the derived flux"},
        "mechanism": "A low temperature MAE does not enforce the declared energy balance; the unreconciled energy imbalance biases the derived heat-flux QoI the COU depends on, so a governing constraint is violated despite the good fit.",
        "gold": {"class": "supply-evidence", "allowed": ["supply-evidence", "acquire-validation", "restrict-cou", "reject"],
                 "alts": ["acquire-validation"], "params": {"scope": "energy-balance reconciliation", "against": "the declared constraint"}},
        "forbidden": ["asserts the heat flux is quantitatively wrong (a verdict beyond the residual)",
                      "treats the low temperature MAE as evidence the energy balance holds"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 model-form adequacy: a data-fit metric does not imply governing-constraint satisfaction; an unreconciled conservation residual is a model-form defeater.",
        "mech_prov": "standard-grounded (V&V 40 model-form)",
    },
    {
        "id": "surr-dccb12-seed-sensitivity", "dcat": "D-CCB-12", "backbone": "reproducibility-support",
        "mdims": ["optimization-randomness", "result-stability"], "domain": "data-driven-emulator",
        "polarity": "fire", "archetype": "single-run-looks-great",
        "pattern": fp("W-AL-02", "Sensitivity to optimization randomness not reported: a strong single-run metric is presented without seed/initialization variability."),
        "anchor": "ASME V&V 40 SQA / aleatory-from-training; proto-taxonomy D-CCB-12",
        "obvious": ("the reported validation accuracy is strong (98.5%) — the surrogate looks reliable", "proceed"),
        "conflicting": "the metric is a single training run; seed/initialization sensitivity is not reported, and for this architecture run-to-run spread is known to be wide, so one run is not a stable estimate",
        "measures": {"reported_accuracy_pct": 98.5, "runs_reported": 1, "seed_sensitivity_reported": False,
                     "architecture_run_to_run_spread": "wide (literature)"},
        "context": {"cou": "the single-run metric is cited as the credibility basis for acceptance",
                    "model_influence": "high", "decision_consequence": "acceptance on the single-run metric"},
        "mechanism": "A single-run metric without reported seed/initialization sensitivity is not a stable estimate of performance; the credibility argument rests on optimization-randomness variability that is uncharacterized.",
        "gold": {"class": "supply-evidence", "allowed": ["supply-evidence", "acquire-validation"],
                 "alts": ["acquire-validation"], "params": {"scope": "seed/initialization sensitivity", "against": "a multi-seed ensemble of runs"}},
        "forbidden": ["asserts the surrogate is unstable/poor (a verdict the missing evidence does not establish)",
                      "treats one favorable run as a characterized performance estimate"],
        "acc_conf": ["high", "medium", "0.70-0.92"],
        "grounding": "ASME V&V 40 / SQA: sensitivity to optimization randomness must be reported (D-CCB-12); a single run does not characterize run-to-run variability.",
        "mech_prov": "standard-grounded (V&V 40 / D-CCB-12)",
    },
    {
        "id": "surr-dccb14-repro-gap", "dcat": "D-CCB-14", "backbone": "reproducibility-support",
        "mdims": ["reproducibility-artifacts", "SQA"], "domain": "data-driven-emulator",
        "polarity": "fire", "archetype": "results-strong-but-unreproducible",
        "pattern": fp("W-AR-04", "Reproducibility artifacts absent: strong reported results without trained weights, environment, or repro scripts to independently verify them."),
        "anchor": "ASME V&V 40 SQA; proto-taxonomy D-CCB-14 (reproducibility)",
        "obvious": ("the report presents strong, signed results — the package looks complete and authoritative", "proceed"),
        "conflicting": "the trained weights, environment specification, and reproduction scripts are absent, so the strong results cannot be independently reproduced or verified — a SQA/reproducibility defeater the polished report hides",
        "measures": {"results": "strong, signed", "trained_weights_archived": False,
                     "environment_pinned": False, "repro_scripts_present": False},
        "context": {"cou": "a regulated submission that requires independent reproducibility",
                    "model_influence": "high", "decision_consequence": "submission relies on reproducible evidence"},
        "mechanism": "Reproducibility artifacts (weights, environment, scripts) are absent, so the reported results cannot be independently reproduced; for a regulated submission this SQA gap is a defeater regardless of how strong or well-presented the results are.",
        "gold": {"class": "supply-evidence", "allowed": ["supply-evidence", "reject"],
                 "alts": [], "params": {"scope": "reproducibility package (weights, environment, scripts)", "against": "independent reproduction"}},
        "forbidden": ["asserts the results are wrong/fabricated (a verdict the missing artifacts do not establish)",
                      "treats a signed, polished report as reproducibility evidence"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "ASME V&V 40 SQA + reproducibility (D-CCB-14): independent reproducibility requires archived weights/environment/scripts; their absence is a defeater.",
        "mech_prov": "standard-grounded (V&V 40 SQA)",
    },
    {
        "id": "surr-surr02-parent-rejected", "dcat": "D-PD-01", "backbone": "applicability",
        "mdims": ["inheritance", "parent-decision"], "domain": "surrogate-of-surrogate",
        "polarity": "fire", "archetype": "child-fine-parent-rejected",
        "pattern": fp("W-SURR-02", "Inherited credibility defect: the surrogate's parent reference model carries a recorded 'Not Accepted' decision the child package does not reconcile."),
        "anchor": "ASME V&V 40 hierarchical credibility; proto-taxonomy D-PD-01 (declared limitations / provenance)",
        "obvious": ("the surrogate's own validation metrics against its parent are excellent (R^2 0.99)", "proceed"),
        "conflicting": "the parent reference model the surrogate was trained against carries a recorded parentDecision = 'Not Accepted' for an overlapping COU, so the child inherits the parent's unresolved credibility defect — fidelity to a rejected parent is not credibility",
        "measures": {"child_vs_parent_R2": 0.99, "parent_model": "RANS closure surrogate",
                     "parentDecision": "Not Accepted", "parent_cou_overlap": "high", "inheritance_reconciled": False},
        "context": {"cou": "the surrogate stands in for a parent whose decision was Not Accepted",
                    "model_influence": "high", "decision_consequence": "decision carried on the child surrogate"},
        "mechanism": "The surrogate is faithful to its parent (high R^2), but the parent carries a recorded Not-Accepted decision for an overlapping COU that the child does not reconcile; inheriting fidelity to a rejected parent inherits the rejection, so the credibility defect propagates.",
        "gold": {"class": "reject", "allowed": ["reject", "acquire-validation", "restrict-cou"],
                 "alts": ["acquire-validation"], "params": {"basis": "unreconciled parent 'Not Accepted' decision", "blocks": "use for the overlapping COU"}},
        "forbidden": ["asserts the surrogate itself is inaccurate (a verdict the inheritance does not establish)",
                      "treats high fidelity to the parent as independent credibility"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "ASME V&V 40 hierarchical credibility: a surrogate's credibility is bounded by its reference; an unreconciled parent rejection propagates to the child.",
        "mech_prov": "standard-grounded (V&V 40 hierarchical credibility)",
    },
    {
        "id": "surr-dver06-resolution-hole", "dcat": "D-VER-06", "backbone": "verification-support",
        "mdims": ["benchmark-coverage", "resolution-generalization"], "domain": "PDE-operator-learning",
        "polarity": "fire", "archetype": "spans-on-average-cell-empty",
        "pattern": fp("W-SURR-04", "Benchmark coverage gap at the COU resolution: the verification set spans a resolution range on average but the COU's specific resolution is unsampled."),
        "anchor": "ASME V&V 40 application-domain coverage; proto-taxonomy D-VER-06",
        "obvious": ("the verification set covers 32x32 through 512x512 grids — looks like broad resolution coverage", "proceed"),
        "conflicting": "the COU runs at 1024x1024, beyond every verified grid; operator-learning surrogates do not automatically generalize past the verified resolution, so the broad-but-bounded coverage does not include the decision point",
        "measures": {"verified_resolutions": "32x32..512x512", "cou_resolution": "1024x1024",
                     "cou_resolution_in_verification_set": False, "coverage_metric": "range-average"},
        "context": {"cou": "the operator surrogate is queried at 1024x1024 for a fine-scale decision",
                    "model_influence": "high", "decision_consequence": "decision on the 1024x1024 prediction"},
        "mechanism": "The verification set spans resolutions on average but excludes the COU's 1024x1024 grid; neural operators do not guarantee resolution generalization past the verified range, so verification does not cover the decision point.",
        "gold": {"class": "restrict-cou", "allowed": ["restrict-cou", "acquire-validation", "supply-evidence"],
                 "alts": ["acquire-validation"], "params": {"scope": "restrict to verified resolutions (<=512x512)", "blocks": "use of the 1024x1024 prediction"}},
        "forbidden": ["asserts the 1024x1024 prediction is wrong (a verdict the coverage gap does not support)",
                      "treats average resolution coverage as coverage at the unsampled COU resolution"],
        "acc_conf": ["high", "medium", "0.65-0.92"],
        "grounding": "FNO failure modes (arXiv:2601.11428): resolution generalization is not automatic; verification at coarser grids does not cover a finer COU resolution.",
        "mech_prov": "paper-grounded (FNO resolution generalization)",
    },
    {
        "id": "surr-dval09-conditional-coverage", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["uq-calibration", "conditional-coverage"], "domain": "structural-FEA-surrogate",
        "polarity": "fire", "archetype": "marginal-calibrated-conditional-fails",
        "pattern": fp("W-AL-02", "UQ marginally calibrated but conditional coverage at the COU subgroup fails: average coverage hides a subgroup the decision depends on."),
        "anchor": "ASME V&V 40 uncertainty; proto-taxonomy D-VAL-09",
        "obvious": ("marginal (overall) interval coverage is 0.90 vs nominal 0.90 — calibration looks correct", "proceed"),
        "conflicting": "conditional coverage on the high-stress subgroup the COU's fatigue decision depends on is only 0.62; marginal coverage averages over subgroups and hides the under-coverage where it matters",
        "measures": {"marginal_coverage": 0.90, "nominal": 0.90, "cou_subgroup": "high-stress elements",
                     "conditional_coverage_cou_subgroup": 0.62, "calibration_metric": "marginal only"},
        "context": {"cou": "the intervals gate a fatigue decision driven by high-stress elements",
                    "model_influence": "high", "decision_consequence": "fatigue margin from the intervals"},
        "mechanism": "Marginal coverage averages over subgroups and reads nominal, but conditional coverage on the high-stress subgroup the COU depends on is far below nominal, so the UQ is not validated for the decision-relevant regime.",
        "gold": {"class": "acquire-validation", "allowed": ["acquire-validation", "supply-evidence", "restrict-cou"],
                 "alts": ["restrict-cou"], "params": {"scope": "conditional coverage on the high-stress subgroup", "against": "held-out high-stress cases"}},
        "forbidden": ["asserts the intervals are wrong everywhere (a verdict beyond the subgroup gap)",
                      "treats marginal coverage as conditional coverage for the COU subgroup"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "Conformal/UQ practice + ASME V&V 40: marginal coverage does not imply conditional coverage; the decision-relevant subgroup must be validated.",
        "mech_prov": "standard-grounded (V&V 40) + conformal conditional-coverage principle",
    },

    # ── Controls: the obvious feature points toward OVER-action; correct is accept ──
    {
        "id": "surr-dval09-largevar-calibrated-control", "dcat": "D-VAL-09", "backbone": "uncertainty-support",
        "mdims": ["uq-calibration", "interval-width"], "domain": "PDE-surrogate",
        "polarity": "suppress", "archetype": "alarming-but-calibrated",
        "pattern": fp("W-AL-02", "Prediction UQ present but not validated."),
        "anchor": "ASME V&V 40 uncertainty; proto-taxonomy D-VAL-09",
        "obvious": ("the prediction intervals are very WIDE — the model looks alarmingly uncertain", "block"),
        "conflicting": "the wide intervals are HONEST: empirical coverage in the COU's regime matches nominal (0.90), epistemic uncertainty is propagated, so the large-but-calibrated uncertainty is exactly what should be reported",
        "measures": {"interval_width": "wide", "empirical_coverage_in_cou_regime": 0.90, "nominal": 0.90,
                     "epistemic_propagated": True, "calibration_evidence_linked": True},
        "context": {"cou": "the calibrated wide band informs a margin decision the engineer can act on",
                    "model_influence": "high", "decision_consequence": "margin set from the calibrated band"},
        "mechanism": "The UQ-validation gap the pattern describes is absent: the intervals are wide but calibrated (coverage matches nominal in the COU regime, epistemic propagated), so the honest large uncertainty is complete evidence — there is no defeater to act on.",
        "gold": {"class": "accept-residual-risk", "allowed": ["accept-residual-risk"], "alts": [],
                 "params": {"justification": "intervals wide but calibrated; coverage 0.90 vs nominal 0.90; epistemic propagated"}},
        "forbidden": ["restricts or rejects on the basis of wide-but-calibrated intervals (over-action)",
                      "asserts the surrogate is credible/correct (a verdict the package does not adjudicate)"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "Honest, calibrated large uncertainty is the desired UQ outcome (arXiv:2007.08792); over-acting on calibrated width is the over-action error a control must catch.",
        "mech_prov": "standard-grounded (V&V 40) + calibration principle",
    },
    {
        "id": "surr-dpd02-edge-but-validated-control", "dcat": "D-PD-02", "backbone": "applicability",
        "mdims": ["envelope-containment", "local-validation"], "domain": "external-aero-CFD",
        "polarity": "suppress", "archetype": "outside-box-but-validated-there",
        "pattern": fp("W-SURR-03", "Evaluation point not contained in the declared training envelope."),
        "anchor": "ASME V&V 40 applicability; proto-taxonomy D-PD-02",
        "obvious": ("the evaluation point sits just OUTSIDE the nominal training box — looks like extrapolation", "block"),
        "conflicting": "the package supplies a dedicated solution-verification at exactly this point (the validated domain was deliberately extended to it), so applicability IS established for the evaluation point",
        "measures": {"evaluationPointInEnvelope": False, "nominal_box_margin": "5% beyond AoA max",
                     "dedicated_validation_at_point": True, "point_residual_vs_reference": "within stated bound",
                     "validated_domain_extended_to_point": True},
        "context": {"cou": "evaluation at a deliberately-validated point just past the nominal box",
                    "model_influence": "high", "decision_consequence": "design decision at the validated point"},
        "mechanism": "Although the point is outside the NOMINAL box, the package establishes applicability at exactly this point via a dedicated solution-verification within bound, so the validated domain covers the evaluation and the containment flag is satisfied by direct evidence — no defeater to act on.",
        "gold": {"class": "accept-residual-risk", "allowed": ["accept-residual-risk"], "alts": [],
                 "params": {"justification": "dedicated validation at the point; residual within bound; validated domain extended to it"}},
        "forbidden": ["restricts or demands re-validation despite a point-specific validation already present (over-action)",
                      "treats the nominal-box boundary as the validated domain when direct evidence extends it"],
        "acc_conf": ["high", "0.80-0.95"],
        "grounding": "ASME V&V 40: the validated domain is defined by validation evidence, not a nominal box; a point with dedicated validation is inside the validated domain.",
        "mech_prov": "standard-grounded (V&V 40 applicability)",
    },
    {
        "id": "surr-dpd03-omitted-but-not-asserted-control", "dcat": "D-PD-03", "backbone": "applicability",
        "mdims": ["qoi-scope", "bundle-sufficiency"], "domain": "data-driven-emulator",
        "polarity": "suppress", "archetype": "omitted-but-cou-doesnt-assert",
        "pattern": fp("W-ON-02", "A credibility dimension is absent from the evidence package."),
        "anchor": "ASME V&V 40 COU scoping; proto-taxonomy D-PD-03 (QoI scoped to the COU)",
        "obvious": ("a whole credibility dimension (transient response) is MISSING from the package — looks incomplete", "block"),
        "conflicting": "the COU explicitly declares a steady-state-only quantity of interest and disclaims transient behaviour, so the omitted dimension is legitimately out of scope, not a gap",
        "measures": {"missing_dimension": "transient-response evidence", "cou_declared_qoi": "steady-state coefficient only",
                     "cou_disclaims_transient": True, "omission_declared_in_scope": True},
        "context": {"cou": "surrogate used for a steady-state-only decision that disclaims transients",
                    "model_influence": "medium", "decision_consequence": "steady-state decision only"},
        "mechanism": "The absent dimension is outside the COU's declared scope (a steady-state-only QoI that disclaims transients), so its omission is a deliberate, declared boundary — productive out-of-scope, not a credibility gap to act on.",
        "gold": {"class": "accept-residual-risk", "allowed": ["accept-residual-risk"], "alts": [],
                 "params": {"justification": "omitted dimension is outside the declared steady-state-only COU scope"}},
        "forbidden": ["demands evidence for a dimension the COU legitimately disclaims (over-action)",
                      "treats a declared scope boundary as a missing-evidence defeater"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 COU scoping + UofA productive-OOS: a dimension a COU does not assert is out of scope, not a gap; flagging it is over-action.",
        "mech_prov": "standard-grounded (V&V 40 COU scoping)",
    },
    {
        "id": "surr-dval08-modesterror-but-within-tolerance-control", "dcat": "D-VAL-08", "backbone": "validation-support",
        "mdims": ["validation-error", "acceptance-criterion"], "domain": "data-driven-emulator",
        "polarity": "suppress", "archetype": "looks-weak-but-within-declared-tolerance",
        "pattern": fp("W-AR-05", "Validation against purpose-specific criteria: a validation error must be judged against the COU's declared acceptance criterion."),
        "anchor": "ASME V&V 40 acceptance criteria tied to the COU; proto-taxonomy D-VAL-08",
        "obvious": ("the validation error is modest (8%) — the surrogate looks weak / not very accurate", "block"),
        "conflicting": "the COU's declared acceptance criterion is 15% (a screening-stage use), and the 8% error is comfortably within it with documented margin, so the modest error is adequate for THIS purpose",
        "measures": {"validation_error_pct": 8.0, "cou_acceptance_criterion_pct": 15.0,
                     "error_within_criterion": True, "cou_stage": "early screening", "criterion_provenance": "documented, COU-tied"},
        "context": {"cou": "screening-stage decision with a declared 15% tolerance",
                    "model_influence": "medium", "decision_consequence": "candidates screened, not finalized"},
        "mechanism": "The validation error must be judged against the COU's declared acceptance criterion, not an absolute notion of accuracy; an 8% error within a documented 15% screening tolerance satisfies the purpose-specific criterion, so there is no defeater to act on.",
        "gold": {"class": "accept-residual-risk", "allowed": ["accept-residual-risk"], "alts": [],
                 "params": {"justification": "8% error within the documented 15% COU acceptance criterion for a screening decision"}},
        "forbidden": ["restricts or rejects because the error 'looks high' against an absolute standard the COU did not set (over-action)",
                      "asserts the surrogate is inaccurate without reference to the declared criterion"],
        "acc_conf": ["high", "0.75-0.93"],
        "grounding": "ASME V&V 40: adequacy is judged against COU-tied acceptance criteria; an error within the declared criterion is adequate, and over-acting on it is the over-action error.",
        "mech_prov": "standard-grounded (V&V 40 acceptance criteria)",
    },
    {
        "id": "surr-dpd04-residual-declared-bounded-control", "dcat": "D-PD-04", "backbone": "structure-support",
        "mdims": ["physics-constraint-residual", "model-form-uncertainty"], "domain": "reacting-flow-surrogate",
        "polarity": "suppress", "archetype": "residual-present-but-accounted",
        "pattern": fp("W-SURR-01", "Declared governing constraint with constraint-check evidence."),
        "anchor": "ASME V&V 40 model-form uncertainty; proto-taxonomy D-PD-04",
        "obvious": ("a non-zero physics-constraint (continuity) residual is present — a constraint violation, looks like a defeater", "block"),
        "conflicting": "the residual is DECLARED, bounded within the stated model-form uncertainty allowance, and propagated into the QoI uncertainty; an accounted-for residual is not an unreconciled defeater",
        "measures": {"continuity_residual": "2%", "model_form_uncertainty_allowance": "5%",
                     "residual_within_allowance": True, "residual_propagated_to_qoi": True, "reconciled": True},
        "context": {"cou": "the bounded residual is carried as documented model-form uncertainty in the QoI",
                    "model_influence": "medium-high", "decision_consequence": "decision with documented model-form margin"},
        "mechanism": "The constraint residual is present but reconciled: it is within the declared model-form uncertainty allowance and propagated into the QoI uncertainty, so the governing constraint is addressed with documented margin — there is no unreconciled defeater to act on.",
        "gold": {"class": "accept-residual-risk", "allowed": ["accept-residual-risk"], "alts": [],
                 "params": {"justification": "2% continuity residual within the declared 5% model-form allowance and propagated to the QoI"}},
        "forbidden": ["demands reconciliation of a residual already declared, bounded, and propagated (over-action)",
                      "treats any non-zero constraint residual as an automatic defeater"],
        "acc_conf": ["high", "0.78-0.95"],
        "grounding": "ASME V&V 40 model-form uncertainty: a declared, bounded, propagated residual is accounted-for; flagging an accounted-for residual is over-action.",
        "mech_prov": "standard-grounded (V&V 40 model-form uncertainty)",
    },
]


# De-named measures: the SAME underlying information as the cell's `measures`, but as
# raw signals/numbers with the conclusion-bearing field names removed. The model must
# now INFER the gap (e.g. "0 validation samples in a QoI-dominant region + regional std
# 5x global, not in the propagated uncertainty" ⇒ per-region competence uncharacterized)
# rather than read a boolean that already states it. This is the fair detection test.
RAW_MEASURES: dict[str, dict] = {
    "surr-dpd02-carbench-wheelhousing": {
        "global_geometry_OOD_percentile": 0.41, "validation_samples_in_wheel_housing": 0,
        "wheel_housing_contribution_to_qoi": "dominant", "ensemble_std_wheel_housing": 0.19,
        "ensemble_std_global_mean": 0.04, "cou_propagated_uncertainty_sources": ["global ensemble std"]},
    "surr-dpd02-turbine-tipgap": {
        "global_operating_point": "interior of envelope (~0.6 of range)",
        "validation_cases_covering_tip_gap": 0, "tip_gap_contribution_to_heat_transfer_qoi": "primary driver",
        "tip_gap_secondary_flow_error": "not evaluated"},
    "surr-dval09-fno-spectral": {
        "validation_relative_L2_allscales": 0.03, "validation_relative_L2_high_freq_band": 0.38,
        "qoi_scale": "fine-scale mixing structure", "metric_reported": "all-scales aggregate only"},
    "surr-dval08-climate-tails": {
        "bulk_rmse_skill_score": 0.96, "skill_on_99_9th_percentile_events": "not reported",
        "decision_regime": "99.9th-percentile extreme events", "fraction_of_record_that_is_extreme": 0.001},
    "surr-dval09-ensemble-mismatch": {
        "uq_method": "deep ensemble (5 members)", "interval_coverage_on_indist_test": 0.91,
        "nominal_coverage": 0.90, "cou_input_vs_training_support": "outside (mild extrapolation)",
        "interval_coverage_on_extrapolation_set": "not measured",
        "ensemble_std_5_members": 0.08, "ensemble_std_3_members": 0.11},
    "surr-dval09-mlip-ood-config": {
        "uq_method": "deep ensemble", "force_error_ece_on_test_split": 0.02,
        "test_split_configurations": "near-equilibrium", "cou_configurations": "high-energy transition states",
        "ece_on_transition_states": "not measured"},
    "surr-dpd04-pinn-massresidual": {
        "pointwise_field_R2_vs_data": 0.995, "data_samples": "sparse scattered points",
        "declared_constraint": "mass conservation (continuity)", "integrated_continuity_residual": 0.08},
    "surr-dver05-mms-only": {
        "mms_verification": "2nd order, passed", "residuals_vs_reference_on_application_config": "not provided",
        "application_config": "notched component, combined load"},
    "surr-dver06-coverage-hole": {
        "benchmark_samples_total": 480, "benchmark_box": "Re [2e6,6e6] x AoA [-5,15]",
        "cou_point": "Re 5.8e6, AoA 14", "benchmark_samples_within_5pct_of_cou_point": 0},
    "surr-dval08-leakage": {
        "reported_validation_error": 0.012, "feature_normalization_fit_on": "train+validation combined",
        "simulation_seeds_shared_between_train_and_val": True, "val_split_drawn": "after normalization"},
    "surr-dval09-aleatory-only": {
        "reported_interval_source": "homoscedastic output-noise variance",
        "model_form_or_extrapolation_variance_in_interval": "absent",
        "cou_input_distance_to_nearest_training_point": "at the training-domain edge"},
    "surr-dccb10-vintage-regime": {
        "training_data_collected": "last quarter", "training_data_operating_points": "steady, 20-40% load",
        "cou_operating_point": "90% load, transient", "training_points_in_cou_regime": 0},
    "surr-dpd02-thermal-hotspot": {
        "board_mean_temperature_rms_error_C": 1.5, "qoi": "peak junction temperature",
        "validation_points_at_junction_hotspot": 0, "peak_vs_mean_temperature_gradient": "steep"},
    "surr-dpd04-energy-residual": {
        "temperature_mae_pct": 0.4, "declared_constraint": "energy conservation",
        "global_energy_imbalance_pct": 6.0, "qoi_derived_from_field": "wall heat flux"},
    "surr-dccb12-seed-sensitivity": {
        "reported_accuracy_pct": 98.5, "training_runs_reported": 1, "seeds_or_inits_varied": "none reported",
        "published_run_to_run_spread_for_architecture_pct": "3-6"},
    "surr-dccb14-repro-gap": {
        "report": "strong, signed", "trained_weights_provided": False,
        "environment_specification_provided": False, "reproduction_scripts_provided": False},
    "surr-surr02-parent-rejected": {
        "child_vs_parent_r2": 0.99, "parent_model": "RANS closure surrogate",
        "parent_model_recorded_decision": "Not Accepted", "parent_cou_overlap_with_child_cou": "high",
        "reconciliation_of_parent_decision_in_child_package": "none"},
    "surr-dver06-resolution-hole": {
        "verified_grid_resolutions": ["32x32", "64x64", "128x128", "256x256", "512x512"],
        "cou_grid_resolution": "1024x1024", "verification_at_1024x1024": "none"},
    "surr-dval09-conditional-coverage": {
        "marginal_interval_coverage": 0.90, "nominal_coverage": 0.90,
        "cou_decision_subgroup": "high-stress elements", "interval_coverage_on_high_stress_subgroup": 0.62},
    "surr-dval09-largevar-calibrated-control": {
        "interval_width": "wide (~2x typical)", "empirical_coverage_in_cou_regime": 0.90,
        "nominal_coverage": 0.90, "epistemic_variance_included_in_interval": True,
        "calibration_holdout_set": "disjoint, in COU regime"},
    "surr-dpd02-edge-but-validated-control": {
        "evaluation_point": "AoA 12.6 (nominal box AoA max = 12.0)",
        "dedicated_reference_run_at_evaluation_point": "present",
        "residual_at_point_vs_reference": "within stated bound", "validation_evidence_covers_point": True},
    "surr-dpd03-omitted-but-not-asserted-control": {
        "evidence_dimensions_present": ["steady-state validation", "UQ", "provenance"],
        "evidence_dimension_absent": "transient response", "cou_declared_qoi": "steady-state coefficient only",
        "cou_statement_on_transients": "explicitly out of scope"},
    "surr-dval08-modesterror-but-within-tolerance-control": {
        "validation_error_pct": 8.0, "cou_declared_acceptance_criterion_pct": 15.0,
        "cou_stage": "early screening", "acceptance_criterion_provenance": "documented, COU-tied"},
    "surr-dpd04-residual-declared-bounded-control": {
        "continuity_residual_pct": 2.0, "declared_model_form_uncertainty_allowance_pct": 5.0,
        "residual_propagated_into_qoi_uncertainty": True, "residual_documented": True},
}


def main() -> int:
    violations = hardness_violations(CELLS)
    if violations:
        print("HARDNESS / SCHEMA VIOLATIONS (fix before writing):")
        for v in violations:
            print("  -", v)
        return 1

    ids = [c["id"] for c in CELLS]
    if len(ids) != len(set(ids)):
        print("duplicate row_id in CELLS"); return 1

    missing_raw = [c["id"] for c in CELLS if c["id"] not in RAW_MEASURES]
    if missing_raw:
        print("cells missing a RAW_MEASURES (de-named) entry — the fair detection test needs one:")
        for m in missing_raw:
            print("  -", m)
        return 1

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    # Replace the generated set (keep README.md; remove stale *.json).
    for stale in CORPUS_DIR.glob("*.json"):
        stale.unlink()
    fires = controls = 0
    for c in CELLS:
        row = build_row(c)
        (CORPUS_DIR / f"{c['id']}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n",
                                                    encoding="utf-8")
        if c["polarity"] == "suppress":
            controls += 1
        else:
            fires += 1
    print(f"wrote {len(CELLS)} cells to {CORPUS_DIR}  ({fires} fire, {controls} control)")
    print("hardness: every cell's obvious-signal posture conflicts with the gold posture (enforced).")
    print("provenance: mechanism paper/standard-grounded; posture standard-derived; "
          "selection provisional-self-adjudicated (needs independent re-adjudication).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
