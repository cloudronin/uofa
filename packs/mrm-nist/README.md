# MRM-NIST pack

A model-level AI-documentation factor set and its SHACL profile, anchored on the
**NIST AI RMF**. It is the *MRM documentation profile* — the documentation slice of
model risk management, not the full lifecycle program — applied to the **model-card
unit** (a single model's public documentation).

It runs the **23 core weakener patterns with no new rules**. The pack contributes a
factor taxonomy, a presence-only completeness profile (SHACL), and a per-pack
weakener→factor focus map. The core engine, shapes, and `.rules` files are untouched.

```
uofa check  <card-derived>.jsonld --pack mrm-nist     # C1/C2/C3
uofa report <card-derived>.jsonld --pack mrm-nist     # deterministic readout (text/markdown/json)
```

## Factor set (17 factors, grouped by RMF function)

Presence-only: each factor is `assessed`, `not-assessed`, or `scoped-out`. There are
**no 1–5 levels and no risk tiers** (that is the V&V40/NASA unit, not this one). The
card is one model's documentation, so MEASURE and MAP carry the weight; several
GOVERN/MANAGE subcategories are organizational acts a static card rarely performs and
are marked **out-of-scope-at-card-level** by default (flipped to `assessed` when a
card actually documents them).

| RMF function | Factor | Card-level read | RMF subcategory (trace) |
|---|---|---|---|
| **GOVERN** | Ownership and accountability † | Owner / maintainer / point of contact | GOVERN 2.1 |
| | Intended use | Primary intended purpose and use cases | MAP 1.1 / GOVERN 1.1 |
| | License and usage terms | License + usage restrictions | GOVERN 1.1 |
| | Out-of-scope use | Uses it is *not* for; misuse | MAP 1.1 / GOVERN 1.2 |
| **MAP** | Task and domain context | Task + domain / data distribution | MAP 1.2 / 2.1 |
| | Deployment setting | Intended environment / operating conditions | MAP 1.5 / 3.1 |
| | Known limitations | Documented limitations / failure modes | MAP 2.3 / MEASURE 2.6 |
| | Affected populations | People/groups affected; representativeness | MAP 1.1 / 3.1 |
| **MEASURE** | Evaluation metrics | Reported metrics + values | MEASURE 2.3 |
| | Evaluation methodology | How evaluation was done; reproducibility | MEASURE 1.1 / 2.3 |
| | Bias and fairness analysis | Bias / fairness / subgroup analysis | MEASURE 2.11 |
| | Robustness and safety testing | Robustness / adversarial / safety / red-team | MEASURE 2.7 / 2.6 |
| | Test and evaluation data | Eval data, provenance, train/test overlap | MEASURE 2.2 / MAP 2.2 |
| **MANAGE** | Mitigations and safeguards † | Mitigations / guardrails applied | MANAGE 1.3 / 2.1 |
| | Residual risk † | Risk remaining after mitigation | MANAGE 1.4 |
| | Monitoring and feedback † | Post-deployment monitoring / drift / feedback | MANAGE 4.1 |
| | Versioning and update policy † | Version history / changelog / update policy | MANAGE 4.2 / 2.4 |

† Out-of-scope-at-card-level by default (see `MRM_NIST_DEFAULT_OUT_OF_SCOPE`).

Encoded as `MRM_NIST_FACTOR_NAMES` in `src/uofa_cli/excel_constants.py`; the SHACL
factor-name enum is `shapes/mrm_nist_shapes.ttl`, scoped to factors tagged
`factorStandard "NIST-AI-RMF-1.0"` (so it never collides with the vv40/nasa shapes).

## SHACL profile

One completeness profile over the factor set: a factor-name enum NodeShape over
`uofa:CredibilityFactor`. No level-range shape (presence-only). Structural
conformance (C2) is the core UofA profile; a card-derived bundle legitimately lacks
a bound requirement (and, for an undocumented model, a validation result), so those
are reported as honest structural findings rather than papered over.

## Weakeners: the 23 core patterns, no new rules

The pack adds **no** weakener rules. The card-derived UofA is evaluated by the 23
core patterns. A model card carries less structure than a V&V assurance package, so
only a subset is reachable — that subset is the honest instrument:

**Fire on card-derived documents**

- `W-EP-04` — a documentation factor is undocumented at the assumed risk level *(the
  completeness→defeater bridge; the main cross-card signal)*
- `W-AL-01` — a reported evaluation has no uncertainty quantification
- `W-AR-05` — a reported evaluation has no comparator / baseline
- `W-ON-02` — intended use stated but the applicability boundary (out-of-scope use) is undocumented
- `W-SI-02` — no bound requirement / no validation result (structural)
- `W-CON-04` — Complete-profile bundle documents no sensitivity analysis (structural)

**Cannot fire at the card level** (need COU structure or argument hierarchy a card
lacks, or are suppressed by construction): `W-EP-01`, `W-PROV-01` (no inline claims);
`W-EP-02` (generation activity auto-stamped); `W-SI-01` (placeholder signature);
`W-AR-02`, `W-CON-01` (no Accepted decision at the card level); `W-AR-03`/`W-AR-04`,
`W-CON-02`/`-03`/`-05`, `W-ON-01`, `W-EP-03`, `W-AL-02`, the COMPOUND rules.

Recording the non-firing set is part of the honest method: this is a documentation
profile, not the full COU-level argument.

### Weakener→factor focus

Most card-level weakeners fire on a validation-result or COU node, not a factor. The
detection-capability `payload.factorFocus` declares which factor each implicates so a
concern demotes the right factor (`W-ON-02`→Out-of-scope use, `W-AL-01`→Evaluation
metrics, `W-AR-05`→Evaluation methodology). `W-EP-04` resolves to its factor by IRI
and needs no entry; `W-SI-02`/`W-CON-04` are structural and map to no factor.

## Disclosed risk assumption

A model card declares no deployment context or risk tier, so the profile assesses
every card against one **disclosed assumption: a moderate-risk deployment, MRL 3**.
`W-EP-04` therefore fires against a *stated* assumption, surfaced in the readout's
"What this model was used for" section — not a hidden input. (Single source:
`space.pipeline.MRM_NIST_RISK_ASSUMPTION`.)

## Worked examples

`examples/_generate.py` fetches each card's live README via `huggingface_hub`, runs
the engine through the shared report pipeline, and writes `card.md` + `state.json` +
`reviewer.html` per example. Per-factor statuses are a committed human reading of the
real card text (provenance in `examples/curated_cards.py`).

| Example | Card | Readout |
|---|---|---|
| `olmo2-13b-instruct` | `allenai/OLMo-2-1124-13B-Instruct` | Well-documented: 11/14 in-scope factors, few concerns |
| `twitter-roberta-sentiment` | `cardiffnlp/twitter-roberta-base-sentiment` | Popular but holey: 4/12, no license, metrics by reference |
| `chemberta-77m-mtr` | `DeepChem/ChemBERTa-77M-MTR` | Ships no README: 0/12 — the published chirality limitation is absent because the card is |

Regenerate: `python packs/mrm-nist/examples/_generate.py` (needs the built engine JAR
and `huggingface_hub`).

## Scope

This is the demo pack: a factor set + SHACL profile + a curated 3-card run. The
open-model corpus study (the 32K-card scale run and its analysis) is separate and not
part of this pack.
