# PhysMAP-derived examples (surrogate pack v0.2)

Three packages that carry **external applicability annotations**: weakeners an
outside tool (PhysMAP) measured, attributed to that tool, signed into the
package, and not yet dispositioned by a human. They are the uofa side of the
surrogate governance loop.

| Package | What it shows | Fires |
|---|---|---|
| `naca-entrance/` | Gnielinski (1976) closure asked about the pipe entrance region (NACA TN-1451 Fig. 10, 85 points). x/D is not a surrogate input, so the training-envelope check and input-based OOD detectors are silent. | W-SURR-05 on 45 of 85 points; quiet on the 40 fully developed points |
| `lewis-35a-gravity-on/` | Forced-convection surrogate (trained with gravity off) reused in vertical heated flow (Lewis 1992 Test 35A). Buoyancy is active (Ri = 0.287 against a window of 0 <= Ri <= 0) and material at the downstream stations. | W-SURR-06 at x/D 67.55, 101.69, 135.84 (theta = 0.10, illustrative) |
| `lewis-35a-gravity-off/` | The control: same surrogate, same visible inputs, gravity off. Ri = 0, materiality 0 at every station. | nothing |

## Where the numbers come from

PhysMAP is public at <https://github.com/cloudronin/physmap> (version 0.2.5,
commit `675729b`). Its `pipeline/assessment_v06.py` exports a UofA v0.6
subgraph (Discrepancy, CredibilityFactor, WeakenerAnnotation, OffsetRationale,
Disposition), but that export does not yet carry the W-SURR-05/06 pattern ids,
the `source: external` marker, or the structured observation fields the uofa
rules read. So these packages were **written by hand in the shape the
external-annotation rule defines**, from PhysMAP's real inputs, by
`dev/tools/scripts/build_physmap_examples.py`:

- NACA: `data/naca/cross_validated_fig10.csv` (Re, Pr, x/D, measured Nu for
  85 points), the Gnielinski formula PhysMAP's `closures/formulas.py`
  implements, and the validated bound PhysMAP's rationale names
  (x/D >= 10). PhysMAP's own run reports the same split: 45 of 45 entrance
  predictions outside the closure's supported region, 40 of 40 fully
  developed points within threshold.
- Lewis 35A: `results/lewis35A_head_to_head/stress_test_lewis_reuse.json`,
  headline design M: per-station surrogate prediction, gravity-off CFD
  control, Lewis's measured Nu and matched-ablation materiality; Ri with
  gravity on; the calibration window; theta = 0.10 recorded as
  illustrative. Lewis disowns stations x/D 0.31, 0.85 and 159.33 on his own
  authority; the stress test marks them not comparable and they carry no
  applicability observation here.

What is authored here and not by PhysMAP: the UnitOfAssurance wrapper
(requirement, context of use, training envelope, validation-result node with
its comparator and provenance), the attribution of each annotation to the
PhysMAP software agent, the `recommendedAction` values, and the decision
records. The decision records are **gate records written for the example**:
asserted, unsigned, and reported by `uofa check` as "C1b decision layer
incomplete" on purpose. That is the state the loop starts from: measurements
sealed, human disposition and decision still owed.

## Where the observation lives

On a fired point the structured observation (closure, bound variable,
validated range, observed value; or mechanism, group, window, observed value,
materiality, threshold) sits on the `WeakenerAnnotation`. On a quiet point it
sits on the quiet `CredibilityFactor` under `uofa-surr:applicabilityFactor`,
so a rule's silence is a judgement about the numbers and not an absence of
anything to judge.

## Seals

The packages ship unsigned (placeholder hash and signature), like the other
surrogate examples. `uofa validate --verify` checks shipped seals against the
shipped anchors only, so a seal under any other key would fail there. To seal
one under a key of your own, with the measurement view signed and the decision
record left owed:

```bash
uofa sign packs/surrogate/examples/physmap/naca-entrance/uofa-surrogate-naca-entrance.jsonld \
    --key <your-key> --as issuer
uofa verify packs/surrogate/examples/physmap/naca-entrance/uofa-surrogate-naca-entrance.jsonld \
    --pubkey <your-key>.pub
```

The round trip (seal, copy to a clean directory, verify, tamper, fail) runs in
`tests/surrogate/test_external_annotations.py` with a fresh key.

## Commands

```bash
uofa shacl <package> --pack surrogate --pack disposition     # C2: conforms
uofa rules <package> --pack surrogate                         # C3: summary
uofa rules <package> --pack surrogate --format json           # firings with source, recommendedAction, disposition state
uofa check <package> --pack surrogate --pubkey packs/surrogate/examples/physmap/keys/physmap-examples.pub
```
