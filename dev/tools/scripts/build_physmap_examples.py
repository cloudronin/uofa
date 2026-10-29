"""Build the PhysMAP-derived surrogate examples and the W-SURR-05/06 rule fixtures.

    python dev/tools/scripts/build_physmap_examples.py

Writes, under packs/surrogate/examples/physmap/:

    naca-entrance/uofa-surrogate-naca-entrance.jsonld
    lewis-35a-gravity-on/uofa-surrogate-lewis-35a-gravity-on.jsonld
    lewis-35a-gravity-off/uofa-surrogate-lewis-35a-gravity-off.jsonld

and, under tests/fixtures/weakeners/:

    W-SURR-05/{positive,negative,boundary}.jsonld
    W-SURR-06/{positive,negative,boundary}.jsonld

WHERE THE NUMBERS COME FROM
---------------------------
PhysMAP (github.com/cloudronin/physmap, commit 675729b, version 0.2.5) exports
a UofA v0.6 subgraph from `src/physmap/pipeline/assessment_v06.py`. That export
does not yet carry the W-SURR-05/06 pattern ids, the `source: external`
marker, or the structured observation fields the uofa rules read (that is
PhysMAP's own follow-up work). So these packages are written here BY HAND in
the shape the external-annotation rule defines, from PhysMAP's real inputs:

* NACA: `data/naca/cross_validated_fig10.csv` in the PhysMAP checkout (NACA
  TN-1451 Fig. 10, bellmouth entrance; US Government work, public domain;
  two-reader digitisation). 85 rows: 5 Reynolds numbers x 17 stations, x/D 1
  to 17, Pr 0.71. The rows are copied below verbatim (Re, Pr, x/D, Nu_meas).
  The surrogate prediction is the Gnielinski (1976) correlation evaluated at
  (Re, Pr) with the published formula (Petukhov friction factor), the same
  formula PhysMAP's `closures/formulas.py::gnielinski_nu` implements. The
  validated x/D bound (x/D >= 10, fully developed) is the bound PhysMAP's
  rationale names: "beyond its validated x_over_D bound (x_over_D >= 10)".
  45 entrance points (x/D < 10) are flagged; 40 fully developed points are not.
  PhysMAP's own run (docs/talk/reproduction/naca_example.txt) reports the same
  split: "PhysMAP: 45 of 45 entrance predictions are outside the closure's
  supported region"; "gnielinski-1976 within the threshold on 40 of 40".

* Lewis 35A: `results/lewis35A_head_to_head/stress_test_lewis_reuse.json`,
  headline design M. 12 stations. The surrogate prediction, the gravity-off
  CFD control, Lewis's measured Nu and the matched-ablation materiality are
  copied per station below. Richardson number with gravity on is
  0.28657904462321093; the calibration window is 0 <= Ri <= 0 (the training
  runs had no gravity). theta = 0.10 is the study's illustrative threshold and
  is recorded as such. Lewis disowns three stations (x/D 0.31, 0.85: axial
  wall conduction; 159.33: flange heat loss, his Sec 7.1.1); PhysMAP's stress
  test marks them not comparable, and they carry no applicability observation
  here. With gravity on, materiality is at or above 0.10 at x/D 67.55, 101.69
  and 135.84: the three downstream stations. With gravity off, materiality is
  0 and Ri is 0 at every station.

WHAT IS AUTHORED HERE AND NOT BY PHYSMAP
----------------------------------------
The UnitOfAssurance wrapper (requirement, context of use, training envelope,
decision record, validation-result node), the attribution of the annotations
to the PhysMAP software agent, the `recommendedAction` values, and the choice
to carry the per-point observation on the annotation (fired points) or on the
quiet CredibilityFactor (quiet points). The decision records are gate records
written for the example: they are not PhysMAP output and not a dispositon of
anything.

The script writes placeholder hashes. Seal afterwards with
`uofa sign <file> --key <key> --as issuer` (the measurement view; the decision
record is asserted and its signature stays owed) and commit the matching public
key beside the examples; regenerating the files invalidates the seals.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "packs" / "surrogate" / "examples" / "physmap"
FIXTURES = ROOT / "tests" / "fixtures" / "weakeners"

CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.6.jsonld"
FIXTURE_CONTEXT = "../../../../spec/context/v0.6.jsonld"
SURR = "https://uofa.net/vocab/surrogate#"

PHYSMAP_AGENT_IRI = "https://github.com/cloudronin/physmap"
PHYSMAP_VERSION = "0.2.5"
PHYSMAP_COMMIT = "675729b149ee2ae0a4f43f6e428425b3fc31a546"

PLACEHOLDER_HASH = "sha256:" + "0" * 64
PLACEHOLDER_SIG = "ed25519:" + "0" * 128

# ── NACA TN-1451 Fig. 10, cross-validated digitisation (Re, Pr, x/D, Nu_meas) ──

NACA_ROWS: list[tuple[float, float, float, float]] = [
    (55570, 0.71, 1, 161.07), (55570, 0.71, 2, 137.38), (55570, 0.71, 3, 118.43),
    (55570, 0.71, 4, 113.69), (55570, 0.71, 5, 113.69), (55570, 0.71, 6, 108.96),
    (55570, 0.71, 7, 108.96), (55570, 0.71, 8, 108.96), (55570, 0.71, 9, 108.96),
    (55570, 0.71, 10, 104.22), (55570, 0.71, 11, 104.22), (55570, 0.71, 12, 104.22),
    (55570, 0.71, 13, 104.22), (55570, 0.71, 14, 104.22), (55570, 0.71, 15, 104.22),
    (55570, 0.71, 16, 104.22), (55570, 0.71, 17, 104.22),
    (50600, 0.71, 1, 151.60), (50600, 0.71, 2, 123.18), (50600, 0.71, 3, 108.96),
    (50600, 0.71, 4, 99.49), (50600, 0.71, 5, 99.49), (50600, 0.71, 6, 99.49),
    (50600, 0.71, 7, 99.49), (50600, 0.71, 8, 99.49), (50600, 0.71, 9, 99.49),
    (50600, 0.71, 10, 94.75), (50600, 0.71, 11, 94.75), (50600, 0.71, 12, 94.75),
    (50600, 0.71, 13, 94.75), (50600, 0.71, 14, 94.75), (50600, 0.71, 15, 94.75),
    (50600, 0.71, 16, 94.75), (50600, 0.71, 17, 94.75),
    (41800, 0.71, 1, 123.18), (41800, 0.71, 2, 104.22), (41800, 0.71, 3, 90.01),
    (41800, 0.71, 4, 85.27), (41800, 0.71, 5, 82.91), (41800, 0.71, 6, 80.54),
    (41800, 0.71, 7, 80.54), (41800, 0.71, 8, 80.54), (41800, 0.71, 9, 80.54),
    (41800, 0.71, 10, 80.54), (41800, 0.71, 11, 80.54), (41800, 0.71, 12, 80.54),
    (41800, 0.71, 13, 80.54), (41800, 0.71, 14, 80.54), (41800, 0.71, 15, 80.54),
    (41800, 0.71, 16, 80.54), (41800, 0.71, 17, 80.54),
    (36500, 0.71, 1, 104.22), (36500, 0.71, 2, 85.27), (36500, 0.71, 3, 71.07),
    (36500, 0.71, 4, 66.32), (36500, 0.71, 5, 71.07), (36500, 0.71, 6, 71.07),
    (36500, 0.71, 7, 71.07), (36500, 0.71, 8, 71.07), (36500, 0.71, 9, 73.91),
    (36500, 0.71, 10, 73.91), (36500, 0.71, 11, 73.91), (36500, 0.71, 12, 73.91),
    (36500, 0.71, 13, 73.91), (36500, 0.71, 14, 73.91), (36500, 0.71, 15, 73.91),
    (36500, 0.71, 16, 73.91), (36500, 0.71, 17, 73.91),
    (26400, 0.71, 1, 104.22), (26400, 0.71, 2, 75.80), (26400, 0.71, 3, 47.37),
    (26400, 0.71, 4, 47.37), (26400, 0.71, 5, 52.11), (26400, 0.71, 6, 56.85),
    (26400, 0.71, 7, 56.85), (26400, 0.71, 8, 56.85), (26400, 0.71, 9, 56.85),
    (26400, 0.71, 10, 56.85), (26400, 0.71, 11, 56.85), (26400, 0.71, 12, 56.85),
    (26400, 0.71, 13, 56.85), (26400, 0.71, 14, 56.85), (26400, 0.71, 15, 56.85),
    (26400, 0.71, 16, 56.85), (26400, 0.71, 17, 56.85),
]
NACA_XD_VALIDATED_MIN = 10.0   # fully developed: the bound PhysMAP's rationale names
GNIELINSKI = "gnielinski-1976"


def gnielinski_nu(re: float, pr: float) -> float:
    """Gnielinski (1976): Nu = (f/8)(Re-1000)Pr / (1 + 12.7 sqrt(f/8)(Pr^(2/3)-1)),
    f = (0.790 ln Re - 1.64)^-2 (Petukhov). Published formula; same as PhysMAP's."""
    f = (0.790 * math.log(re) - 1.64) ** -2.0
    return (f / 8.0) * (re - 1000.0) * pr / (1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0 / 3.0) - 1.0))


# ── Lewis (1992) Test 35A, PhysMAP stress test, headline design M ──────────────
# (x/D, comparable, surrogate prediction, gravity-off CFD control, Lewis Nu,
#  materiality with gravity on)

LEWIS_STATIONS: list[tuple[float, bool, float, float, float, float]] = [
    (0.31, False, 54.95559424934452, 54.97400055660621, 33.72, 0.0013951427554482754),
    (0.85, False, 36.52207069065153, 36.55291800583049, 32.69, 0.0025909167598138216),
    (2.45, True, 24.353220082566608, 24.35912026436245, 22.15, 0.0058982336887503095),
    (5.65, True, 17.8472277967762, 17.8572627949338, 19.07, 0.012105359332462817),
    (9.92, True, 14.527636779383984, 14.534069199954224, 14.92, 0.020225077316751494),
    (16.32, True, 12.170372974139907, 12.17563370580396, 13.95, 0.03198154152704169),
    (33.39, True, 9.578645757464876, 9.580604216163485, 10.76, 0.06100207327542362),
    (50.47, True, 8.443279201916095, 8.444175886445544, 9.38, 0.08680915434298242),
    (67.55, True, 7.776468450883519, 7.776950364076799, 9.37, 0.11089545774333265),
    (101.69, True, 7.000516750589364, 7.000797142675188, 8.41, 0.15434751126570656),
    (135.84, True, 6.550747678494179, 6.548810328666752, 7.99, 0.1947661427792411),
    (159.33, False, 6.339329989294386, 6.3266644059582156, 8.82, 0.22114884622152486),
]
LEWIS_DISOWNED = {0.31: "axial wall conduction (Lewis Sec 7.1.1)",
                  0.85: "axial wall conduction (Lewis Sec 7.1.1)",
                  159.33: "'suspect' -- flange heat loss (Lewis Sec 7.1.1)"}
LEWIS_RE, LEWIS_PR = 1143.4, 8.46
LEWIS_RI_GRAVITY_ON = 0.28657904462321093
LEWIS_THETA = 0.10
# Training-run ranges from PhysMAP data/stress_tests/lewis_reuse/cfd_profiles.json
LEWIS_TRAIN = {"reynolds": (749.9993113828558, 1550.0003307065085),
               "prandtl": (8.1090359441067, 8.755339875254418),
               "x_over_D": (0.3, 159.5)}


# ── builders ───────────────────────────────────────────────────────────────────

def _num(v: float) -> float:
    return float(v)


def _agent() -> dict:
    return {
        "id": PHYSMAP_AGENT_IRI,
        "type": "prov:SoftwareAgent",
        "name": "physmap",
        "version": PHYSMAP_VERSION,
        "commit": PHYSMAP_COMMIT,
    }


def _dimension(base: str, name: str, lo: float, hi: float) -> dict:
    return {"id": f"{base}/{name}", "type": f"{SURR}EnvelopeDimension",
            f"{SURR}dimensionName": name, f"{SURR}minBound": _num(lo), f"{SURR}maxBound": _num(hi)}


def _envelope(base: str, kind: str, dims: dict[str, tuple[float, float]]) -> dict:
    cls = "TrainingEnvelope" if kind == "env" else "EvaluationRegion"
    return {"id": f"{base}/{kind}", "type": f"{SURR}{cls}",
            f"{SURR}hasDimension": [_dimension(f"{base}/{kind}", n, lo, hi) for n, (lo, hi) in dims.items()]}


def _discrepancy(base: str, slug: str, pred: float, truth: float, region: str) -> dict:
    return {
        "id": f"{base}/discrepancy/{slug}",
        "type": "Discrepancy",
        "surrogatePrediction": _num(pred),
        "solverTruth": _num(truth),
        "discrepancyMagnitude": _num(abs(pred - truth)),
        "discrepancyRegion": region,
        "measureType": "point",
    }


def _package(base: str, *, name: str, description: str, cou_name: str, intended_use: str,
             decision: str, decision_rationale: str, validation_name: str,
             comparator_name: str, envelope: dict, region: dict, model_name: str) -> dict:
    return {
        "@context": CONTEXT_URL,
        "id": base,
        "type": ["UnitOfAssurance", "CredibilityEvidencePackage"],
        "validatedWithPacks": ["surrogate"],
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "name": name,
        "description": description,
        "couName": cou_name,
        "intendedUse": intended_use,
        "assuranceLevel": "Medium",
        "decision": decision,
        "modelRiskLevel": 2,
        "bindsRequirement": f"{base}/req",
        "bindsModel": {"id": f"{base}/model", "type": "Model", "name": model_name},
        "generatedAtTime": "2026-10-29T00:00:00Z",
        "wasAttributedTo": "https://uofa.net/surrogate/physmap/org/author",
        "hash": PLACEHOLDER_HASH,
        "signature": PLACEHOLDER_SIG,
        "hasValidationResult": {
            "id": f"{base}/applicability-screen",
            "type": "ValidationResult",
            "name": validation_name,
            "wasAttributedTo": _agent(),
            "wasGeneratedBy": {
                "id": f"{base}/applicability-screen/run",
                "type": "prov:Activity",
                "name": f"PhysMAP {PHYSMAP_VERSION} run (commit {PHYSMAP_COMMIT[:7]})",
                "wasAssociatedWith": PHYSMAP_AGENT_IRI,
            },
            "comparedAgainst": {
                "id": f"{base}/reference",
                "type": "Comparator",
                "name": comparator_name,
            },
            # PhysMAP reports its observations as values with no uncertainty
            # on them, so the screen declares no UQ rather than leaving the
            # field absent (which core reads as "missing UQ", W-AL-01).
            "hasUncertaintyQuantification": False,
        },
        "hasDecisionRecord": {
            "id": f"{base}/decision",
            "type": "DecisionRecord",
            "outcome": decision,
            "actor": "https://uofa.net/surrogate/physmap/org/reviewer",
            "rationale": decision_rationale,
            "decidedAt": "2026-10-29T00:00:00Z",
            # The record's actor participates in this package's production, so a
            # decision signature is owed. The examples ship with the measurement
            # view sealed (`uofa sign --as issuer`) and the decision unsigned:
            # that is the pre-disposition state the governance loop starts from,
            # and `uofa check` reports it as C1b incomplete on purpose.
            "decisionProvenance": "asserted",
        },
        "hasContextOfUse": {
            "id": f"{base}/cou",
            "type": "ContextOfUse",
            "name": cou_name,
            "intendedUse": intended_use,
            "hasOperatingEnvelope": envelope["id"],
        },
        f"{SURR}trainingEnvelope": envelope,
        f"{SURR}evaluationRegion": region,
    }


def build_naca() -> dict:
    base = "https://uofa.net/surrogate/physmap/naca-entrance"
    re_vals = sorted({r[0] for r in NACA_ROWS})
    envelope = _envelope(base, "env", {"reynolds": (min(re_vals), max(re_vals)), "prandtl": (0.71, 0.71)})
    region = _envelope(base, "region", {"reynolds": (min(re_vals), max(re_vals)), "prandtl": (0.71, 0.71)})
    pkg = _package(
        base,
        name="PhysMAP applicability screen: Gnielinski closure asked about the pipe entrance region (NACA TN-1451)",
        description=(
            "Hand-written in the shape the surrogate pack's external-annotation rule defines, "
            "from PhysMAP's real inputs (NACA TN-1451 Fig. 10, 85 points; PhysMAP "
            f"{PHYSMAP_VERSION}, commit {PHYSMAP_COMMIT[:7]}). PhysMAP's current v0.6 export does not "
            "yet carry W-SURR pattern ids, source: external, or the structured observation "
            "fields, so this package was built by dev/tools/scripts/build_physmap_examples.py "
            "rather than exported. A pipe's Nusselt number is predicted from (Re, Pr) by the "
            "Gnielinski (1976) correlation, which is validated for fully developed flow "
            "(x/D >= 10), and is then asked about the entrance region. x/D is not a surrogate "
            "input, so the training-envelope check (W-SURR-03) and input-based OOD detectors "
            "stay silent; the closure check (W-SURR-05) fires on all 45 entrance points and "
            "stays quiet on the 40 fully developed points. The 45 annotations arrive with no "
            "Disposition: each carries a recommendedAction, which is a recommendation and not a "
            "disposition. solverTruth here is the NACA measurement, not a solver."
        ),
        cou_name="Local Nusselt number in a heated circular pipe, entrance region included",
        intended_use="Predict local Nu along the pipe from (Re, Pr) alone, as a fast stand-in for measurement or CFD.",
        decision="Not accepted",
        decision_rationale=(
            "Gate record written for the example: 45 High applicability weakeners from PhysMAP are "
            "undispositioned, so the deployment gate stays closed until each is dispositioned by a "
            "named engineer. This record is not PhysMAP output."
        ),
        validation_name="PhysMAP applicability screen of gnielinski-1976 against NACA TN-1451 Fig. 10 (bellmouth entrance), 85 points",
        comparator_name="NACA TN-1451 (1947) Fig. 10 local Nusselt measurements, bellmouth entrance, two-reader digitisation",
        envelope=envelope, region=region,
        model_name="Gnielinski (1976) correlation standing in as the surrogate: Nu from (Re, Pr) only",
    )
    discrepancies, weakeners, factors = [], [], []
    for re_, pr, xd, nu_meas in NACA_ROWS:
        slug = f"re{int(re_)}-xd{int(xd)}"
        pred = gnielinski_nu(re_, pr)
        region_txt = f"Re={int(re_)}, Pr={pr}, x_over_D={int(xd)}"
        disc = _discrepancy(base, slug, pred, nu_meas, region_txt)
        discrepancies.append(disc)
        observation = {
            f"{SURR}closureId": GNIELINSKI,
            f"{SURR}boundVariable": "x_over_D",
            f"{SURR}validatedMin": NACA_XD_VALIDATED_MIN,
            f"{SURR}observedValue": _num(xd),
        }
        fired = xd < NACA_XD_VALIDATED_MIN
        factor = {
            "id": f"{base}/factor/{slug}",
            "type": "CredibilityFactor",
            "factorType": "literature-validity-distance",
            "factorStatus": "fired" if fired else "quiet",
            "factorStandard": GNIELINSKI,
            "affectedNode": disc["id"],
        }
        if fired:
            weakeners.append({
                "id": f"{base}/weakener/{slug}",
                "type": "WeakenerAnnotation",
                "patternId": "W-SURR-05",
                "severity": "High",
                "source": "external",
                "wasAttributedTo": PHYSMAP_AGENT_IRI,
                "affectedNode": disc["id"],
                "justification": (
                    f"Prediction relies on {GNIELINSKI} beyond its validated x_over_D bound "
                    f"(x_over_D >= 10); observed x_over_D = {int(xd)} at Re = {int(re_)}. x_over_D is "
                    "not a surrogate input (unobservable to input-based OOD detectors), and the "
                    "literature (Tam & Ghajar 1998, Exp. Thermal and Fluid Science 16(3): 187-194) "
                    "reports divergence up to -63% past this bound."
                ),
                "recommendedAction": "characterize-region",
                **observation,
            })
        else:
            # The quiet point carries the same observation, so the rule's silence is a
            # judgement about the numbers (x/D inside the validated range), not an absence
            # of anything to judge.
            factor.update(observation)
        factors.append(factor)
    pkg["hasDiscrepancy"] = discrepancies
    pkg["hasWeakener"] = weakeners
    pkg[f"{SURR}applicabilityFactor"] = factors
    return pkg


def build_lewis(gravity_on: bool) -> dict:
    state = "gravity-on" if gravity_on else "gravity-off"
    base = f"https://uofa.net/surrogate/physmap/lewis-35a-{state}"
    envelope = _envelope(base, "env", LEWIS_TRAIN)
    region = _envelope(base, "region", {"reynolds": (LEWIS_RE, LEWIS_RE), "prandtl": (LEWIS_PR, LEWIS_PR),
                                        "x_over_D": (0.31, 159.33)})
    if gravity_on:
        decision, rationale = "Not accepted", (
            "Gate record written for the example: three High weakeners from PhysMAP (buoyancy active "
            "and material at the downstream stations) are undispositioned, so the reuse is not "
            "accepted until each is dispositioned by a named engineer. This record is not PhysMAP output."
        )
    else:
        decision, rationale = "Accepted", (
            "Gate record written for the example: the gravity-off control. Every visible input is a "
            "training input, buoyancy is inactive (Ri = 0) and immaterial (0 at every station), and "
            "PhysMAP reports no applicability weakener. This record is not PhysMAP output."
        )
    pkg = _package(
        base,
        name=f"PhysMAP model-reuse stress test: forced-convection surrogate reused on Lewis (1992) Test 35A, {state}",
        description=(
            "Hand-written in the shape the surrogate pack's external-annotation rule defines, from "
            f"PhysMAP's banked stress-test record (results/lewis35A_head_to_head/stress_test_lewis_reuse.json, "
            f"headline design M; PhysMAP {PHYSMAP_VERSION}, commit {PHYSMAP_COMMIT[:7]}). PhysMAP's current "
            "v0.6 export does not yet carry W-SURR pattern ids, source: external, or the structured "
            "observation fields, so this package was built by dev/tools/scripts/build_physmap_examples.py "
            "rather than exported. A Gaussian-process surrogate trained on thirteen gravity-off CFD runs "
            "(inputs Re, Pr, x/D; gravity never varied, never an input) is reused in vertical heated flow. "
            + ("With gravity on, buoyancy is active (Ri = 0.287 against a calibration window of 0 <= Ri <= 0) "
               "and its matched-ablation materiality is at or above the illustrative theta = 0.10 at the three "
               "downstream stations x/D 67.55, 101.69 and 135.84, where W-SURR-06 fires. "
               if gravity_on else
               "With gravity off (the control), Ri = 0 and materiality is 0 at every station, so W-SURR-06 is quiet. ")
            + "Every visible deployment input is an exact training input, so the training-envelope check "
            "(W-SURR-03) and the input-based OOD detector stay silent in both states. Lewis disowns stations "
            "x/D 0.31, 0.85 and 159.33 on his own authority; PhysMAP's stress test marks them not comparable and "
            "they carry no applicability observation here. theta = 0.10 is illustrative (unlocked) and is "
            "recorded as such on every observation. solverTruth is Lewis's measurement with gravity on and the "
            "gravity-off CFD control with gravity off. Development demonstration: one run, stations not independent."
        ),
        cou_name="Local Nusselt number in vertical heated pipe flow (Lewis 1992 Test 35A), forced-convection surrogate reused",
        intended_use="Predict local Nu along the heated section from (Re, Pr, x/D) with a surrogate built without buoyancy.",
        decision=decision, decision_rationale=rationale,
        validation_name=f"PhysMAP applicability screen and matched ablation (gravity on vs off) on Lewis Test 35A, {state}, 12 stations",
        comparator_name=("Lewis (1992) Test 35A local Nusselt numbers, inlet-bulk basis (Appendix D-2)" if gravity_on
                         else "Gravity-off OpenFOAM control at the 35A operating point (matched ablation, pair_gOFF)"),
        envelope=envelope, region=region,
        model_name="Forced-convection Gaussian-process surrogate on gravity-off CFD (Matern 5/2, inputs log10 Re, Pr, log10 x/D)",
    )
    discrepancies, weakeners, factors = [], [], []
    for xd, comparable, pred, control, measured, mat_on in LEWIS_STATIONS:
        slug = f"xd{str(xd).replace('.', 'p')}"
        truth = measured if gravity_on else control
        disc = _discrepancy(base, slug, pred, truth, f"Re={LEWIS_RE}, Pr={LEWIS_PR}, x_over_D={xd}")
        discrepancies.append(disc)
        factor = {
            "id": f"{base}/factor/{slug}",
            "type": "CredibilityFactor",
            "factorType": "omitted-mechanism-materiality",
            "factorStandard": "matched-ablation",
            "affectedNode": disc["id"],
        }
        if not comparable:
            factor["factorStatus"] = "excluded"
            factor["description"] = f"Not comparable: {LEWIS_DISOWNED[xd]}. No applicability observation reported."
            factors.append(factor)
            continue
        materiality = mat_on if gravity_on else 0.0
        observation = {
            f"{SURR}mechanism": "buoyancy",
            f"{SURR}dimensionlessGroup": "richardson_number",
            f"{SURR}calibrationMin": 0.0,
            f"{SURR}calibrationMax": 0.0,
            f"{SURR}observedValue": LEWIS_RI_GRAVITY_ON if gravity_on else 0.0,
            f"{SURR}materiality": _num(materiality),
            f"{SURR}materialityThreshold": LEWIS_THETA,
            f"{SURR}materialityThresholdStatus": "illustrative",
        }
        fired = gravity_on and materiality >= LEWIS_THETA
        factor["factorStatus"] = "fired" if fired else "quiet"
        if fired:
            weakeners.append({
                "id": f"{base}/weakener/{slug}",
                "type": "WeakenerAnnotation",
                "patternId": "W-SURR-06",
                "severity": "High",
                "source": "external",
                "wasAttributedTo": PHYSMAP_AGENT_IRI,
                "affectedNode": disc["id"],
                "justification": (
                    f"Buoyancy is omitted from the surrogate (trained with gravity off, Ri never an input) "
                    f"and is active here: Ri = {LEWIS_RI_GRAVITY_ON:.3f} against a calibration window of "
                    f"0 <= Ri <= 0. Matched ablation (gravity on vs off, nothing else changed) moves Nu by "
                    f"{materiality:.3f} at x/D = {xd}, at or above the illustrative theta = {LEWIS_THETA}. "
                    "The input-based OOD detector is silent: every visible input is a training input."
                ),
                "recommendedAction": "restrict-cou",
                **observation,
            })
        else:
            factor.update(observation)
        factors.append(factor)
    pkg["hasDiscrepancy"] = discrepancies
    pkg["hasWeakener"] = weakeners
    pkg[f"{SURR}applicabilityFactor"] = factors
    return pkg


# ── per-rule fixtures (minimal; one point each) ───────────────────────────────

def _fixture(pid: str, variant: str, observation: dict, note: str) -> dict:
    base = f"https://example.org/uofa/{pid.lower()}-{variant}"
    return {
        "@context": FIXTURE_CONTEXT,
        "id": base,
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "name": f"{pid} {variant} fixture",
        "description": note,
        "bindsRequirement": f"{base}/req",
        "hasValidationResult": {"id": f"{base}/vr", "type": "ValidationResult",
                                "wasAttributedTo": _agent()},
        "hasDecisionRecord": f"{base}/dr",
        "hasContextOfUse": {"id": f"{base}/cou", "type": "ContextOfUse",
                            "hasOperatingEnvelope": f"{base}/env"},
        "generatedAtTime": "2026-10-29T00:00:00Z",
        "hash": PLACEHOLDER_HASH,
        "signature": PLACEHOLDER_SIG,
        "hasDiscrepancy": _discrepancy(base, "p1", 100.0, 120.0, "one point"),
        "hasWeakener": {
            "id": f"{base}/weakener/p1",
            "type": "WeakenerAnnotation",
            "patternId": pid,
            "severity": "High",
            "source": "external",
            "wasAttributedTo": PHYSMAP_AGENT_IRI,
            "affectedNode": f"{base}/discrepancy/p1",
            "justification": note,
            **observation,
        },
    }


def _closure_obs(observed: float) -> dict:
    return {f"{SURR}closureId": GNIELINSKI, f"{SURR}boundVariable": "x_over_D",
            f"{SURR}validatedMin": NACA_XD_VALIDATED_MIN, f"{SURR}observedValue": observed}


def _mechanism_obs(ri: float, materiality: float) -> dict:
    return {f"{SURR}mechanism": "buoyancy", f"{SURR}dimensionlessGroup": "richardson_number",
            f"{SURR}calibrationMin": 0.0, f"{SURR}calibrationMax": 0.0,
            f"{SURR}observedValue": ri, f"{SURR}materiality": materiality,
            f"{SURR}materialityThreshold": LEWIS_THETA,
            f"{SURR}materialityThresholdStatus": "illustrative"}


FIXTURE_SET = {
    ("W-SURR-05", "positive"): (_closure_obs(2.0), "x/D = 2 is below the validated lower end (10): fires."),
    ("W-SURR-05", "negative"): (_closure_obs(12.0), "x/D = 12 is inside the validated range (>= 10): quiet."),
    ("W-SURR-05", "boundary"): (_closure_obs(10.0), "x/D = 10 equals the validated lower end: inside, quiet (lessThan is strict)."),
    ("W-SURR-06", "positive"): (_mechanism_obs(LEWIS_RI_GRAVITY_ON, 0.11089545774333265),
                                "Ri = 0.287 outside [0, 0] and materiality 0.111 >= theta 0.10: fires."),
    ("W-SURR-06", "negative"): (_mechanism_obs(LEWIS_RI_GRAVITY_ON, 0.06100207327542362),
                                "Ri = 0.287 outside [0, 0] but materiality 0.061 < theta 0.10: active, not material, quiet."),
    ("W-SURR-06", "boundary"): (_mechanism_obs(LEWIS_RI_GRAVITY_ON, LEWIS_THETA),
                                "materiality exactly at theta 0.10: at the threshold counts as material, fires."),
}


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    _write(EXAMPLES / "naca-entrance" / "uofa-surrogate-naca-entrance.jsonld", build_naca())
    _write(EXAMPLES / "lewis-35a-gravity-on" / "uofa-surrogate-lewis-35a-gravity-on.jsonld", build_lewis(True))
    _write(EXAMPLES / "lewis-35a-gravity-off" / "uofa-surrogate-lewis-35a-gravity-off.jsonld", build_lewis(False))
    for (pid, variant), (obs, note) in FIXTURE_SET.items():
        _write(FIXTURES / pid / f"{variant}.jsonld", _fixture(pid, variant, obs, note))
    print("wrote 3 examples and 6 fixtures")


if __name__ == "__main__":
    main()
