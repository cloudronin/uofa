---
title: model-credibility pack
description: A NIST AI RMF documentation factor set plus a NIST AI 800-3 evaluation-sufficiency layer, for the model-card unit. 22 factors, 10 pack weakeners, 23 core patterns.
---

The **model-credibility** pack is a model-level AI-documentation factor set and its SHACL
profile, anchored on the [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).
It applies to the **model-card unit** (one model's public documentation) and answers
two questions that are kept strictly apart:

| Group | Question | Standard | Factors |
|---|---|---|---|
| **A — documentation completeness** | does this model document itself? | NIST AI RMF 1.0 | 17 |
| **B — evaluation sufficiency** | are the reported numbers interpretable as evidence? | NIST AI 800-3 | 5 |

Group B is the addition that renamed the pack. A benchmark score with no uncertainty,
no null baseline and no stated context of use is a number, not evidence — and Group B
assesses reported results the way ASME V&V 40 assesses a simulation validation study.

It contributes a
factor taxonomy, a presence-only completeness profile (SHACL), and a per-pack
weakener→factor focus map. The core engine, shapes, and rules are untouched.

```bash
uofa report owner/model --pack model-credibility                          # fetch card + extract + report
uofa report https://huggingface.co/owner/model --pack model-credibility   # same, from a model URL
uofa report bundle.jsonld --pack model-credibility                        # a saved/curated bundle (deterministic)
```

Given an HF model id or URL, `uofa report` fetches the card, extracts factor
statuses, and runs the same report as on a bundle. The readout always states its
**extraction provenance** (an LLM backend when configured, else an *approximate*
README keyword scan), a gated/absent card renders an honest **no-card notice**
rather than a hollow all-weakeners page, and the generated bundle is saved by
default as the auditable, re-runnable source.

## Factor set

Seventeen factors, grouped by the four RMF functions. Presence-only: each factor is
`assessed`, `not-assessed`, or `scoped-out` — there are **no 1–5 levels and no risk
tiers**. Because the card is one model's documentation, MEASURE and MAP carry the
weight; several GOVERN/MANAGE subcategories are organizational acts a static card
rarely performs and are marked **out-of-scope-at-card-level** by default (†), flipped
to `assessed` only when a card documents them.

| RMF function | Factors |
|---|---|
| **GOVERN** — governance & accountability | Ownership and accountability †, Intended use, License and usage terms, Out-of-scope use |
| **MAP** — context & risk framing | Task and domain context, Deployment setting, Known limitations, Affected populations |
| **MEASURE** — evaluation & analysis | Evaluation metrics, Evaluation methodology, Bias and fairness analysis, Robustness and safety testing, Test and evaluation data |
| **MANAGE** — risk response & monitoring | Mitigations and safeguards †, Residual risk †, Monitoring and feedback †, Versioning and update policy † |

Each factor traces to an RMF subcategory (full mapping table in the
[pack README](https://github.com/cloudronin/uofa/blob/main/packs/model-credibility/README.md)).

## SHACL profile

One completeness profile over the factor set: a factor-name enum NodeShape over
`uofa:CredibilityFactor`, scoped to factors tagged `factorStandard "NIST-AI-RMF-1.0"`
so it never collides with the vv40/nasa shapes. No level-range shape (presence-only).

## Weakeners — 10 pack patterns, plus the reachable core subset

The pack declares **10 patterns of its own**, all Group B:

| Pattern | Severity | Fires when |
|---|---|---|
| `W-EV-GEN-02` | High | a score is generalized with no superpopulation account |
| `W-EV-DET-03` | High | no determinism / repeat-run policy stated for the evaluation |
| `W-EV-NULL-04` | High | the score is not calibrated against a null or chance baseline |
| `W-EV-COU-05` | Critical / High | no stated context of use for the evidence (Critical when `--cou` scopes a decision) |
| `W-EV-CAP-06` | Medium | no control for a capability confound |
| `W-EV-DIV-07` | High | a reported score diverges from an independently furnished one beyond tolerance |
| `W-EV-SUB-08` | Medium | the measured subject carries no version guarantee |
| `W-EV-COR-09` | Medium | a reported result is uncorroborated where furnished evidence exists |
| `COMPOUND-EV-01` | Critical | compound escalation at elevated risk |
| `COMPOUND-EV-02` | High | a generalized claim with no sampling account |

**The two groups are firewalled by rule structure, not by convention.** Every Group-B
rule body binds `uofa:hasValidationResult`, so a card with no reported evaluation
*structurally cannot* trip one — there is no configuration in which a documentation-only
card produces an evaluation-sufficiency finding. Group A's shapes are gated on a
matching `factorStandard`, so the two factor sets stay mutually silent.

A model card carries less structure than a V&V assurance package, so only a subset of
the **core** catalog is reachable. That honest subset is part of the instrument:

- **Fire on a card:** `W-EP-04` (an undocumented factor at the assumed risk level — the
  main cross-card signal), `W-AL-01` (evaluation without uncertainty quantification),
  `W-AR-05` (evaluation without a comparator), `W-ON-02` (intended use stated but
  out-of-scope use undocumented), `W-SI-02` and `W-CON-04` (structural).
- **Cannot fire at the card level** (need COU structure / argument hierarchy a card
  lacks): the claim- and decision-dependent patterns (`W-EP-01`, `W-PROV-01`,
  `W-AR-02`, `W-CON-01`, …). Recording the non-firing set is part of the honest method.

A model card declares no risk tier, so the profile assesses every card against a
**disclosed moderate-risk assumption (MRL 3)**, stated in the readout's "What this
model was used for" section — `W-EP-04` fires against a stated assumption, not a hidden
input.

## Worked examples (suggested, run live)

The [live demo](/demo/) offers three suggested examples; clicking one runs the same
live pathway as pasting any model id — fetch the card, extract, report:

| Card | What it shows |
|---|---|
| `allenai/OLMo-2-1124-13B-Instruct` | Well-documented — most factors evidenced, few concerns |
| `cardiffnlp/twitter-roberta-base-sentiment` | Popular but holey — no license stated, metrics by reference only |
| `DeepChem/ChemBERTa-77M-MTR` | Ships no README — the no-card readout; the published chirality limitation is absent because the card is |

The contrast is carried by **completeness first**; with an LLM backend the typed
weakeners explain the gaps, while the no-model heuristic path reports completeness and
declines sufficiency. The readout always states which path produced it.
