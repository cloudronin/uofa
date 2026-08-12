# model-credibility pack

A model-level AI-documentation factor set and its SHACL profile, anchored on the
**NIST AI RMF**. It is the *MRM documentation profile* — the documentation slice of
model risk management, not the full lifecycle program — applied to the **model-card
unit** (a single model's public documentation).

It runs the **23 core weakener patterns with no new rules**. The pack contributes a
factor taxonomy, a presence-only completeness profile (SHACL), and a per-pack
weakener→factor focus map. The core engine, shapes, and `.rules` files are untouched.

```
uofa report owner/model --pack model-credibility                          # fetch the card + extract + report
uofa report https://huggingface.co/owner/model --pack model-credibility   # same, from a model URL
uofa report bundle.jsonld --pack model-credibility                        # a saved/curated bundle (deterministic)
uofa check  bundle.jsonld --pack model-credibility                        # C1/C2/C3 on a bundle
```

## Reporting on a live model card

`uofa report` accepts an HF model id (`owner/model`) or model URL as well as a
`.jsonld` bundle. For an id/URL it fetches the card, extracts the factor statuses,
maps to a bundle, and runs the same report. Honesty guardrails:

- **Extraction provenance is always stated in the readout** — `LLM extraction -
  <backend>/<model>` when a backend is configured (`--extract-backend anthropic`
  …, reusing the `uofa extract` flags), or `Heuristic - … approximate` for the
  no-model README scan (the default when no backend is set, or `--deterministic`).
- **The heuristic path reports completeness only and DECLINES sufficiency.** A
  keyword/heading scan can support documentation completeness but not
  sufficiency-level weakeners, so it skips the weakener engine and shows
  *"Sufficiency (weakener) analysis not assessed in heuristic mode — run with an LLM
  backend"* in place of the concerns section. A keyword scan is never presented as
  the tool's verdict.
- **No card → an honest no-card readout**, not a hollow all-weakeners page: a gated
  (403) card is a hard failure; a missing/empty card (404) renders 0/N under a
  prominent "no model card published" notice (sufficiency not applicable).
- **The generated bundle is kept by default in a temp cache** (printed, e.g.
  `<tmpdir>/uofa-report-bundles/<owner>__<model>.model-credibility.jsonld`) as the auditable,
  re-runnable source — not dropped into the working directory. `--save-bundle PATH`
  writes where asked; `--no-save-bundle` discards. Re-running `uofa report
  <saved-bundle>` reproduces the readout, provenance line included.

The deterministic scan is coarse by design; its divergence from the curated baseline
is bounded and tracked in `tests/test_report_card.py`, not left to surface live.

## Factor set — 22 factors in two standards

**Group A (17, NIST AI RMF 1.0)** below, grouped by RMF function. **Group B
(5, NIST AI 800-3)** is the evaluation-sufficiency layer, documented further
down. Each factor carries a `factorStandard`, and the SHACL profile is gated on
it, so the two sets never collide.

### Group A — documentation completeness, grouped by RMF function

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

† Out-of-scope-at-card-level by default (see `MODEL_CREDIBILITY_DEFAULT_OUT_OF_SCOPE`).

Encoded as `MODEL_CREDIBILITY_FACTOR_NAMES` in `src/uofa_cli/excel_constants.py`; the SHACL
factor-name enum is `shapes/model_credibility_shapes.ttl`, scoped to factors tagged
`factorStandard "NIST-AI-RMF-1.0"` (so it never collides with the vv40/nasa shapes).

## SHACL profile

One completeness profile over the factor set: a factor-name enum NodeShape over
`uofa:CredibilityFactor`. No level-range shape (presence-only). Structural
conformance (C2) is the core UofA profile; a card-derived bundle legitimately lacks
a bound requirement (and, for an undocumented model, a validation result), so those
are reported as honest structural findings rather than papered over.

## Group B — evaluation sufficiency (NIST AI 800-3)

Group A asks whether the model documents itself. **Group B asks whether the
numbers it reports mean anything.** A benchmark score with no uncertainty, no
null baseline and no stated context of use is a number, not evidence — and this
is the layer that renamed the pack.

Five factors, tagged `factorStandard "NIST-AI-800-3"`, and **ten weakener
patterns of the pack's own**:

| Pattern | Severity | Fires when | Grounding |
|---|---|---|---|
| `W-EV-GEN-02` | High | a score is generalized with no superpopulation account | V&V 40 applicability |
| `W-EV-DET-03` | High | no determinism / repeat-run policy stated for the evaluation | Seahaven TRAP 35 |
| `W-EV-NULL-04` | High | the score is not calibrated against a null or chance baseline | Seahaven null calibration |
| `W-EV-COU-05` | Critical / High | no stated context of use for the evidence | 800-3 §; Critical when `--cou` scopes a decision |
| `W-EV-CAP-06` | Medium | no control for a capability confound | Seahaven |
| `W-EV-DIV-07` | High | a reported score diverges from an independently furnished one beyond tolerance | V&V 40 output comparison |
| `W-EV-SUB-08` | Medium | the measured subject carries no version guarantee | NASA-7009 configuration control |
| `W-EV-COR-09` | Medium | a reported result is uncorroborated where furnished evidence exists | 800-3 independence |
| `COMPOUND-EV-01` | Critical | compound escalation at elevated declared risk | — |
| `COMPOUND-EV-02` | High | a generalized claim with no sampling account | — |

### The firewall is rule structure, not convention

**Every Group-B rule body binds `uofa:hasValidationResult.`** A card with no
reported evaluation therefore *structurally cannot* trip one — there is no flag,
no configuration, and no card content that produces an evaluation-sufficiency
finding on a documentation-only card. Group A's shapes are gated on a matching
`factorStandard`, so the two factor sets stay mutually silent in the other
direction.

The readout says **"no reported evaluation to assess"**, which is a different
claim from finding nothing wrong and is rendered differently.

### Reported vs furnished

`evidenceSource` separates a score the card's authors published (`reported`) from
one an independent run produced (`furnished`). Two things depend on it:

- **`W-EV-DIV-07`** is only expressible because both can exist for one
  constituent. When they disagree beyond tolerance, that is a finding *about the
  record*. It does **not** establish which number is correct, and the rule's
  wording does not imply it does.
- **`W-EV-COR-09`** fires on a reported result that furnished evidence does not
  corroborate — and its body requires furnished evidence to exist, so it cannot
  fire on a card nobody has independently measured.

Tolerance is `DIV_TOLERANCE_NORMALIZED = 5.0` points normalized, used where the
furnisher publishes no uncertainty of its own. The constant is derived, not
chosen: bbq's `acc_stderr` of 0.04083 at n=150 is 4.08 points normalized, so a
tighter bar would fire on sampling noise at the furnisher's own sample size.

### Where the property definitions live

`properties/P1..P7.json` is the **single source** for what each Group-B property
means. The labeling instruction sheet and the extraction prompt both *render*
from it, and `tests/test_property_definitions_are_one_source.py` asserts
byte-identity.

That machinery exists because they once drifted: the sheet counted "ablations
offered as controls" while the prompt named neither ablations nor limitation
statements, and three model families scored 100% false-fire on P7 as a direct
result. Two faithful paraphrases of one intent drift because nothing holds them
together. They no longer paraphrase.

### Extraction routing

Group-B evidence is read by structure, not by one path:

| Evidence | Route | Status |
|---|---|---|
| table-borne (a `Stderr` column, `71.3 ± 0.4` in a cell) | **keyless field read**, no model | qualified: false-fire 2/27, false-clear 1/33 on 60 unseen cards |
| prose-borne | LLM extraction, backend required | unresolved; 44–100% miss depending on property |
| relational (`claimedCOU`, `confoundControlStatement`) | adjudication panel | pre-committed — extraction may propose, nothing renders without panel confirmation |

The keyless route is **v1 and immutable**: its qualification row reports
measurements of that exact logic, so its two published defects — compound
dispersion headers (`reward_std`) unread, and a standalone `SE` metric column
misread as standard error at a measured 3% — stay published rather than patched.
Any improvement is v2 against a fresh holdout draw.

## Weakeners — the reachable core subset

Besides its own ten, the card-derived UofA is evaluated by the 23 **core** patterns.
A model card carries less structure than a V&V assurance package, so only a subset of
those is reachable — and that subset is part of the honest instrument:

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
`uofa_cli.card_bundle.MODEL_CREDIBILITY_RISK_ASSUMPTION`.)

## Worked examples (suggested, run live)

The demo Space offers three suggested examples; clicking one runs the **same live
pathway** as pasting the id (fetch → extract → report), not a static render. The
curated factor-status reading lives in `examples/curated_cards.py` as the baseline for
the LLM-vs-deterministic divergence test; `examples/_generate.py` refreshes the
committed `card.md` snapshots that test reads.

| Example | Card | What it shows |
|---|---|---|
| `allenai/OLMo-2-1124-13B-Instruct` | Frontier, well-documented | Most factors documented, few gaps |
| `cardiffnlp/twitter-roberta-base-sentiment` | Popular but holey | No license stated, metrics by reference |
| `DeepChem/ChemBERTa-77M-MTR` | Ships no README | The no-card readout (0 documented); the published chirality limitation is absent because the card is |

Refresh the committed card snapshots: `python packs/model-credibility/examples/_generate.py`.

## Source pinning

Assessing an artifact you do not control means recording which bytes you read.
`sourcePin` carries two kinds, supporting different claims:

- **artifact pin** — supports *re-derivation*. For a HuggingFace card this is the
  `README.md` **blob oid**, never the repo sha: a repo sha moves when any file in
  the repo changes, so pinning it would mark a byte-identical card stale on a
  weights re-upload — a badge going amber for a reason the reader cannot see.
- **occasion pin** — supports *re-performance only*. A hosted endpoint's identity
  is what the provider asserts and can change under a stable name with nothing to
  diff, so a furnished score pins when it was measured and records that the
  assessor did not verify the subject.

## Scope, and what is gated

This pack ships the factor sets, the SHACL profile, the ten Group-B weakeners and
the extraction routing. **Public report cards and badges are specified but gated
behind catalog closure** (addendum v0.5, A16.9): no rule enters the v1.0 catalog
until its finding-validity rate is adjudicated, and no card is published before
that.

The validation apparatus — corpora, labeling protocol, extractor qualification,
holdout gates — lives in `studies/taxonomy-validation/`. Its records pin paths
and hashes as they were at measurement time and are deliberately **not** updated
by later renames; see `studies/PACK-RENAME-NOTE.md`.
