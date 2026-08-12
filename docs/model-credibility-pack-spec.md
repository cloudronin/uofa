# Spec: extend `model-credibility` into a comprehensive model-credibility pack

**Status:** ACTIVE — being built. The original "POST-OCTOBER, do not build before
the praxis defense" gate was lifted by explicit decision on 2026-08-10; the code
lands now alongside the thesis chapter rather than after it. The praxis remains
UofA with FDA beachhead + aerospace cross-domain, and the generalization
*argument* this pack embodies still goes in the chapter — building it early makes
that argument evidence rather than a forward reference.

**Revision note (2026-08-10):** this document has been corrected against the
artifacts it describes. §2 and §4 changed mechanism (see the marked patches),
§3 gained W-EV-DIV-07, and §6a's characterization of raidex was overstated and is
now restated against the published records. Where this spec previously described
machinery the implementation deliberately does not have, the spec was wrong, not
the implementation.

**Repo:** github.com/cloudronin/uofa. Target pack: `packs/model-credibility/` (renamed on
merge — see §1). Verified against current tree: packs are `core`, `vv40`,
`nasa-7009b`, `surrogate`, `model-credibility`, `iso42001`, `disposition`.

---

## 0. What this is and the one design decision behind it

Merge two standards into **one comprehensive model-credibility pack** so that a
single reviewer runs a single pass over a model and its published evidence, and
gets both:

- **Documentation completeness** — does this model document itself against the
  NIST AI RMF (the current `model-credibility` job, presence-only, 17 factors).
- **Evaluation sufficiency** — are the model's *reported benchmark results*
  credible, assessed as validation evidence the way `vv40` assesses a
  simulation validation study, specialized to AI evals via NIST AI 800-3
  (statistical validity, benchmark-vs-generalized accuracy, uncertainty) and
  the Seahaven-derived sufficiency weakeners (null calibration, per-model
  determinism floor).

**Decision (user's call, recorded):** merge rather than ship sibling packs.
Rationale is audience, not taxonomy — one operator, one sitting, one pass;
two `--pack` invocations would serve the standard's tidiness over the user.
This is a legitimate merge because it gives the weakeners and gaps *more
meaning together*: a documentation gap and an evaluation-sufficiency gap on the
same model inform one credibility judgment.

**The one thing that does NOT merge: the firewall.** Completeness and
sufficiency remain separately addressable *within* the pack. This is not the
standard's tidiness — it is the honesty guardrail. A model with a card but no
reported benchmarks must get a clean completeness readout, NOT a wall of
benchmark-sufficiency weakeners for evals it never claimed. This is the same
"plausible validates as well as correct" firewall that `model-credibility` already
implements as its heuristic-vs-LLM tiers. Keep it.

---

## 1. Pack identity after merge

- **Rename** `model-credibility` → `model-credibility` (keep `model-credibility` as an alias in
  the pack loader for one version so existing `--pack model-credibility` invocations and
  `tests/test_report_card.py` don't break; deprecation note in README).
- **`standards`** in `pack.json` becomes:
  `["NIST-AI-RMF-1.0", "NIST-AI-800-3", "ASME-VV40-2018"]`.
  V&V40 is listed because the evaluation-sufficiency layer reuses its
  validation-evidence assessment pattern (`ValidationResult` node assessed
  against credibility factors, weakeners fire on missing UQ / comparator /
  COU-relevance). 800-3 is the AI-eval statistical-validity anchor.
- **`factors`**: two factor groups under one pack, tagged by `factorStandard`
  so the existing multi-pack `factorStandard`-gating machinery (already in
  `vv40_shapes.ttl`) keeps them separable:
  - Group A (existing 17): `factorStandard "NIST-AI-RMF-1.0"`, presence-only,
    no levels. Unchanged.
  - Group B (new, eval-sufficiency): `factorStandard "NIST-AI-800-3"`, assessed
    against a benchmark `ValidationResult` node. Levels optional (see §3).

---

## 2. The two layers, firewalled

**PATCHED 2026-08-10 — mechanism changed, constraint unchanged.** This section
originally specified two SHACL *profiles* dispatched like `ProfileDisposition`.
That does not work: `excel_mapper.derive_profile()` iterates candidate profiles
most-demanding-first and **returns on the first satisfied one**, so it selects
exactly one. This section's own requirement — that a comprehensively assessed
model runs both — cannot be expressed in single-winner semantics. The firewall
below is unchanged; only how it is enforced changed.

| Layer | Fires when | Runs | Degrades to |
|---|---|---|---|
| Documentation completeness (Group A) | a model card / doc bundle present | Group-A presence shapes; heuristic tier OK; declines sufficiency | honest no-card readout on 404, hard-fail on 403 (existing behavior) |
| Evaluation sufficiency (Group B) | a benchmark `ValidationResult` node present | Group-B weakeners; structured input reads deterministically, prose requires a backend (§4) | "no reported evaluation to assess — sufficiency N/A" when absent |

**Firewall rule (the honesty guardrail, stated as a constraint):** neither
layer's weakeners fire on the other's absent inputs. No benchmark node →
zero eval-sufficiency weakeners, not N failures. No card → zero
doc-completeness weakeners, not N failures. Each absence is a *stated N/A*, not
a wall of red.

**How it is enforced.** Not by profile dispatch — by two properties the
implementation already has, plus a test:

1. **Rule bodies.** A Jena rule whose body binds `(?uofa uofa:hasValidationResult
   ?vr)` structurally cannot fire when no `ValidationResult` exists. Group-B
   weakeners are silent on a card-only model by construction, not by suppression.
2. **`factorStandard` gating.** Group A's SHACL shape requires a matching
   `factorStandard` triple (the required-match form, not vv40's `!BOUND`
   fallback), so each group's shapes stay silent on the other group's factors.
3. **A firewall test, which is the actual guarantee.** A raidex-only fixture must
   produce zero Group-A completeness weakeners; a card-only fixture must produce
   zero `W-EV-*` firings. Both must be made to fail on purpose once (AGENTS.md
   §13) — a firewall that cannot be observed failing is not a firewall.

This is strictly less machinery than profile dispatch and touches no core shape.
A model assessed comprehensively runs BOTH layers and the readout has two
clearly-labeled sections. A model with only a card runs one and says so.

---

## 3. Group B: the evaluation-sufficiency factors and weakeners

The benchmark result is a `ValidationResult` node — the SAME node type `vv40`
already assesses. The AI-eval factor taxonomy is the `vv40` assessment cluster
specialized for evaluations:

| Eval factor | V&V40 analog | Asks |
|---|---|---|
| Score + uncertainty | Output comparison | Is the reported number carried with an uncertainty estimate? |
| Item sampling | Test samples | Is the benchmark set a fair sample of the target population? (800-3 benchmark-vs-generalized accuracy) |
| Harness determinism | Test conditions | Is the eval reproducible; is per-model nondeterminism characterized? |
| Null calibration | (new, Seahaven) | Is the score calibrated against a comprehension-free / chance baseline? |
| COU relevance | Relevance of validation to COU | Is this benchmark relevant to the decision the score informs? |

**New weakener rules** (Group B `.rules`, fire on the benchmark
`ValidationResult` node; naming follows existing W-<cat>-<n> convention):

| Rule | Severity | Detects | Grounding |
|---|---|---|---|
| ~~W-EV-UQ-01~~ | — | **WITHDRAWN 2026-08-10 — core's W-AL-01 already does this.** See below. | |
| W-EV-GEN-02 | High | benchmark accuracy presented as generalized accuracy (no superpopulation account) | 800-3 core distinction |
| W-EV-DET-03 | High | no per-model determinism floor / reproducibility statement | Seahaven TRAP 35 |
| W-EV-NULL-04 | High | score not calibrated against a null/chance/comprehension-free baseline | Seahaven null-calibration |
| W-EV-COU-05 | Critical / High | benchmark used to support a decision with no stated context-of-use relevance | V&V40 COU-relevance, applied to eval |
| W-EV-CAP-06 | Medium | separation/claim attributable to general capability, not the measured construct, with no partialling | Seahaven capability-confound |
| W-EV-DIV-07 | High | reported score diverges from an independently furnished score for the same constituent, beyond tolerance | V&V40 output comparison applied to eval; the §6a furnisher/assessor firewall made testable |
| W-EV-SUB-08 | High | evaluation subject not configuration-controlled: the subject carries only claimed identity, with no immutable version guarantee | NASA-STD-7009 configuration-control expectations, applied to the measured subject |

**W-EV-UQ-01 withdrawn — the invariance claim is stronger without it.** This row
originally read "reported score with no uncertainty / CI · grounding: 800-3;
parallels W-AL-01." It does not parallel W-AL-01; it *is* W-AL-01. Core's rule
already fires on `noValue(?result, uofa:hasUncertaintyQuantification)` for any
`ValidationResult`, and `model-credibility` already runs all 23 core patterns — so adding
W-EV-UQ-01 would report one missing standard error twice under two IDs, which §6
forbids.

Instead the adapter populates **core's existing `hasUncertaintyQuantification`**
when a constituent furnishes a real uncertainty, and omits it otherwise. W-AL-01
then fires, unchanged, on an LLM benchmark.

That is a better result for §7 than a parallel rule. Addendum v0.1 §A4 asks the
chapter to show "the same rule-ID *pattern* firing across node types." The pack
can now show something stronger: **the identical rule — same ID, same body, same
severity — firing on a blood-pump CFD study missing its uncertainty band and on
an LLM benchmark missing its determinism floor.** Not a naming convention shared
across two packs; one rule, two domains, no new code. Invariance demonstrated
rather than argued. Rewrite the §A4 side-by-side table accordingly: it has one
column, not two.

Seven other core rules also bind `hasValidationResult` and will fire on Group-B
nodes — notably **W-AR-05** (`noValue(?result, uofa:comparedAgainst)`), since
raidex furnishes no comparator at all. That is a real and separate finding, kept.
It does **not** absorb W-EV-NULL-04: a V&V40 comparator is the data a result was
validated against, while a null baseline is the comprehension-free floor a score
must clear. A constituent can have one without the other, and collapsing them
would lose the ability to say so.

Because core rules now fire per Group-B node, the readout **must** aggregate by
`patternId` with an affected-node count ("9 of 10 validation results carry no
uncertainty") rather than printing one row per node. Ten nodes must not become
ten rows; that is the wall of red arriving from core instead of from Group B.

W-EV-COU-05 carries two severities per addendum v0.1 §A2: Critical when `--cou`
was supplied (a specific decision is on the table), High otherwise. **The finding
itself is the published record lacking a stated context of use** —
`noValue(?vr, uofa:claimedCOU)` — and that clause is present in both rule bodies.
The flag modulates severity; it never creates the finding. Without the absence
clause, an operator passing `--cou` would manufacture a Critical against a model
whose card properly states its COU, i.e. the rule would report on the operator's
input instead of on the evidence.

**W-EV-SUB-08 — the subject is not fixed, which is prior to how it varies.**
Distinct from W-EV-DET-03, and the distinction is the whole point: DET-03 asks
whether sampling variance *within a fixed subject* is characterized; SUB-08 asks
whether the subject was fixed at all. A determinism floor on a subject that can
change under its own name measures the wrong thing precisely.

Fires when the `ValidationResult`'s subject carries only an **occasion pin**
(addendum v0.2 A9.1) — a provider-asserted identifier with no immutable version
guarantee. Every API-hosted model qualifies: **41 of the 43 published records**,
so this fires near-universally and that is the finding, not a calibration error.
Prevalence framing absorbs it the same way W-EV-COU-05's does.

The honest statement it encodes: **a closed-weight score is evidence about an
occasion, not about an artifact.** It can be re-performed and cannot be
re-derived, and nothing in the assessment can promise otherwise.

**W-EV-DIV-07 tolerance, as a defended constant.** Use the furnished uncertainty
when one exists; otherwise `DIV_TOLERANCE_NORMALIZED = 5.0` points on the 0–100
scale. The fixed form is the dominant path, not the fallback: across the raidex
fixtures in `tests/fixtures/raidex/`, `bbq` is the *only* constituent of nine that
publishes a standard error. A rule firing only where uncertainty exists would go
silent on 8 of 9 constituents — precisely where the evidence is weakest, which
inverts the point of having the rule.

The constant is measured, not chosen, **across the entire published cohort**
(43 models, 427 validation results, measured 2026-08-10):

| | |
|---|---|
| results carrying a real uncertainty | **43 of 427 (10.1%)** — `bbq` in every model, nothing else |
| observed `bbq` stderr, normalized 0–100 | min **1.84**, mean **3.35**, max **4.08** |
| `DIV_TOLERANCE_NORMALIZED = 5.0` | sits above the cohort maximum — **holds** |

A tolerance at or below 4.08 would fire on sampling noise at raidex's own sample
sizes. Note `n_samples` is **not** constant across constituents (observed 108
through 738), so the constant is anchored to the observed standard-error range
rather than to any one sample size. Re-derive if that range moves; the check is
one pass over the dataset and should be rerun whenever the cohort grows.

**Framing constraint.** A divergence establishes that the published number and an
independent run disagree. It does **not** establish which is correct, and the rule
description must not imply that it does. Like every other Group-B finding, it is a
finding about the record.

**Compound rules** (fire on Group-B output, chained, the C3 differentiator):

| Rule | Detects |
|---|---|
| COMPOUND-EV-01 | reported score drives a high-MRL COU decision AND lacks both UQ and null calibration → Critical escalation |
| COMPOUND-EV-02 | claimed generalized performance AND item-sampling weakener present → the generalization is unsupported by the sample |

Levels: default presence/absence like `model-credibility`, NOT 1–5. If a levels variant
is wanted later it's a separate profile, not baked in — do not over-build.

---

## 4. Extraction

- Group A: existing `model-credibility` model-card extraction, unchanged. Heuristic tier
  keeps declining sufficiency.
- Group B: new extraction target — a model's **reported evaluation evidence**
  (raidex output, eval card, results table, benchmark section of the model card,
  linked eval report). Emits `ValidationResult` nodes carrying the seven
  properties of addendum v0.1 §A1.

  **PATCHED 2026-08-10 — "backend-required, never keyless" is now split by input
  type.** The original rule read: *backend-required, never keyless; sufficiency
  needs content analysis, and the firewall already forbids a keyless sufficiency
  claim.* The purpose of that rule is to stop a **plausible inferred value**
  passing as read evidence. Reading `results.bbq.raw["acc_stderr,none"]` out of a
  raidex record infers nothing — it is a field read, and paying an LLM to perform
  it would buy no honesty. So:

  | Input | Extraction | Provenance |
  |---|---|---|
  | Structured furnisher output (raidex JSON, HF `model-index` metadata) | deterministic field read, no backend | `extracted` |
  | Prose (model-card benchmark tables, eval reports) | **backend required**, unchanged | `extracted` |
  | Field absent in either | stays absent — never a placeholder | not stamped |

  The guardrail is unchanged in substance: nothing is inferred without a backend,
  and an absence is never filled to satisfy a constraint. This also stops the
  presence-only eval detector of addendum v0.1 §A3 from reading as an exception to
  a rule it never actually violated.

  A structured record may also *decline* to furnish a constituent. In the raidex
  fixtures, an excluded constituent carries `value: null` with a populated
  `error`; it must not become a `ValidationResult` with a null score. That
  exclusion is what `rai_coverage` counts, and it is furnished evidence of the
  composite-exclusion rule working, not a gap.
- Every extracted field keeps the existing provenance stamping
  (`extracted` / `run-context` / `derived` / `defaulted`) so "how much of this
  was actually read" stays answerable — the existing honesty property, extended
  to eval evidence.

---

## 5. Reporting

`uofa report owner/model --pack model-credibility` produces one readout, two
labeled sections:

```
MODEL CREDIBILITY: owner/model
  extraction: LLM - anthropic/<model>   [or Heuristic - approximate for docs only]

  [1] DOCUMENTATION COMPLETENESS  (NIST AI RMF, 17 factors)
      <existing model-credibility output>

  [2] EVALUATION SUFFICIENCY  (NIST AI 800-3 / V&V40 validation-evidence)
      <Group-B weakeners, OR "no reported evaluation to assess — N/A">
      <if heuristic/keyless: "sufficiency not assessed — run with a backend">
```

Honesty guardrails carry over verbatim: provenance line always shown; heuristic
mode declines sufficiency; no-card → honest no-card; benchmark-absent →
sufficiency N/A. Bundle kept in temp cache, re-runnable, `--save-bundle` honored.

---

## 6. What must not happen

- **No fusing the two layers into one undifferentiated check.** The firewall
  is the honesty property; a comprehensive pack that fires benchmark weakeners
  on a model with no benchmarks reproduces exactly the failure Seahaven closed.
- **No inferred sufficiency without a backend.** Completeness can be cheap;
  *inferring* sufficiency from prose cannot, and claiming it cheaply is the
  "plausible validates as correct" trap. Deterministically reading a structured
  furnisher record is not inference and is permitted (§4) — the line is
  inference, not cost.
- **No plausible value to fill an absence.** A missing uncertainty is missing.
  `"N/A"`, `null`, and absent all mean absent; none of them may become a number,
  a placeholder string, or a default. This is the same constraint AGENTS.md §13
  states as "a blank that fails loudly is the correct output."
- **No 1–5 levels on Group B by default.** Presence/absence like `model-credibility`;
  levels are a later opt-in variant if ever.
- **No new *unit*.** A benchmark result is validation evidence about the model,
  not a separate unit — that is the whole reason this merges into a
  model-credibility pack instead of standing alone.
- **No publishing a furnisher's raw error text.** Excluded-constituent tracebacks
  carry the operator's absolute filesystem paths; bundles from this pack get
  published, so an exclusion is recorded as a short classification, never as the
  verbatim traceback.

---

## 6a. raidex as the benchmark-evidence furnisher

raidex (github.com/cloudronin/raidex, `pip install raidex`, results published at
[cloudronin/raidex-results](https://huggingface.co/datasets/cloudronin/raidex-results))
is the **furnisher** of benchmark `ValidationResult` nodes for this pack's Group-B
sufficiency layer. It is not a separate integration to invent — it is the evidence
pipeline that already exists.

**CORRECTED 2026-08-10.** This section previously credited raidex with
"per-model scoring, versioned constituents, the composite-exclusion rule, and
'hold a constituent out until externally replicated'." Checked against the 43
published records, two of those four are not there. What raidex actually
publishes, per record:

| Claimed | Actually published |
|---|---|
| per-model scoring | **yes** — one record per model, 9 constituents each |
| the composite-exclusion rule | **yes** — an excluded constituent carries `value: null` + a populated `error`, and `rai_coverage` counts it (`8/9`, `rai_coverage_pct`) |
| versioned constituents | **no** — `config.backend_version` is a *backend* version (`"0.1.0"`); per-constituent provenance is only `eval_source: "automated"`. The package README's "pinned dataset versions" is not in the record schema. |
| hold-until-externally-replicated | **no** — there is no replication-status field. `badge` is a coverage tier (`full` at 9/9, `independent` at 8/9), not a replication signal. |

Recording the correction rather than building against the claim is the point of
AGENTS.md §13: a spec that asserts a schema the artifact does not have produces an
adapter that reads fields which are never there. The two absent properties are
not a criticism of raidex — they are two of the gaps the loop below is *for*.

The furnisher/assessor firewall (measure-don't-judge, again):

- **raidex furnishes the score.** Per-model, per-constituent, with its
  provenance (which constituent, which version, replication status).
- **The pack assesses whether that score is credible evidence for a decision.**
  A raidex number can be clean and replicated and still trip W-EV-COU-05 (no
  stated context of use) or W-EV-NULL-04 (constituent has no null baseline).
  Furnishing the number is not asserting its sufficiency.
- **Neither side collapses into the other.** raidex sits on the furnisher side
  of the same firewall that runs through UofA, SIP, and Seahaven.

The loop that makes both more than the sum: **the pack's Group-B weakeners are
a specification for what a raidex constituent should carry.** W-EV-DET-03
(per-model determinism floor, Seahaven TRAP 35), W-EV-NULL-04 (null
calibration, the parrot work), W-EV-UQ-01 (uncertainty, the thing most
leaderboards skip) are simultaneously assessment gaps and a credibility bar
raidex constituents can be built to clear. raidex furnishes evidence → the pack
assesses sufficiency → the assessment gaps tell raidex what its next
constituent needs. Furnisher and assessor sharpen each other against one shared
credibility standard.

### Vocabulary additions must NOT touch `spec/context/v0.5.jsonld`

Recorded 2026-08-10 after making this mistake and catching it on the Morrison
smoke test. Two facts, either of which is sufficient:

1. **The context is inside the integrity envelope.** `integrity.canonicalize_and_hash`
   hashes the document *after* `_inline_context` replaces the `@context` URL with
   the file's full contents. So adding one term to `v0.5.jsonld` changes the
   canonical hash of **every** bundle that references it — the Morrison reference
   example went `C1 Integrity ✗` on a purely additive vocabulary change, with C2
   and C3 still green. The signed corpus is downstream of that file.
2. **The addition buys nothing anyway.** `v0.5.jsonld` declares
   `"@vocab": "https://uofa.net/vocab#"`, so *any* undeclared term already
   expands to `uofa:<term>`. `samplingAccount`, `claimedCOU`,
   `decisionRiskLevel` and the rest are visible to Jena with no declaration at
   all — verified by running the full Group-B rule set against a pristine
   context and getting identical firings.

So Group B adds **no** context entries. `v0.5.jsonld` is effectively frozen:
note that no pack has added to it, and the `hasDisposition` term the disposition
pack would have needed lives in the unused `v0.6.jsonld` draft instead. A future
property that genuinely needs a declaration (a datatype coercion or `@id`
typing, which `@vocab` cannot supply) is a context-version bump plus a re-sign of
the example corpus, not an edit in place.

This generalizes past this pack, and is a candidate rule for AGENTS.md §13: *a
purely additive change to a file that is hashed is not additive.*

**Engineering (ACTIVE):** a raidex furnisher adapter for Group-B extraction —
read raidex per-model output, emit `ValidationResult` nodes with score /
uncertainty-if-present, provenance-stamped like every other extracted field.
Constituent-version and replication-status are **not** emitted, because the
records do not carry them (see the correction above); an adapter reading fields
that do not exist would emit a uniform absence and call it a measurement.

**The gap set, measured over all 43 published records (427 validation results,
2026-08-10):**

| Property | Furnished | Consequence |
|---|---|---|
| `metricValue` | 427/427 | — |
| `wasGeneratedBy` | 427/427 | core W-EP-02 clears; raidex does record how each number was produced |
| `hasUncertaintyQuantification` | **43/427 (`bbq` only)** | core W-AL-01 fires on 384, clears on 43 |
| `samplingAccount` | 0/427 | W-EV-GEN-02 fires cohort-wide |
| `harnessDeterminismStatement` | 0/427 | W-EV-DET-03 fires cohort-wide |
| `nullBaselineStatement` | 0/427 | W-EV-NULL-04 fires cohort-wide |
| `claimedCOU` | 0/427 | W-EV-COU-05 fires cohort-wide |
| `confoundControlStatement` | 0/427 | W-EV-CAP-06 fires cohort-wide |

Coverage: 40 models at 9/9, 3 at 8/9; the exclusions classify as two
connection errors and one timeout, none unclassified.

Two things this table establishes that the architecture diagram could not. First,
**the assessment discriminates**: `W-AL-01` clears on exactly the 10% of results
that carry an uncertainty and fires on the other 90%, so the readout distinguishes
a furnisher that reports uncertainty from one that does not, rather than
blanket-failing everything. Second, **the four all-zero rows are a specification,
not a complaint** — they are precisely what a raidex constituent would have to
carry to clear the bar, which is the furnisher/assessor loop as a measurement
rather than a claim.

## 7. Thesis hook (the part that IS due, as writing not code)

The generalization claim this pack embodies, for the chapter: *a benchmark
result is a unit of validation evidence, the COU-scoped credibility-factor
construct is invariant across the standard it targets, and the same
weakener-on-validation-evidence machinery that flags a blood-pump CFD study
missing its uncertainty band flags an LLM benchmark missing its determinism
floor.* One construct — validation evidence assessed against COU-scoped
credibility factors — demonstrated across simulation (`vv40`, `nasa-7009b`),
surrogates (`surrogate`), and AI models-and-their-evals (this pack), with
Seahaven supplying the specialized eval weakeners (W-EV-DET-03, W-EV-NULL-04,
W-EV-CAP-06).

And the ecosystem form, which is the strongest version because it grounds in
three already-built systems: **raidex furnishes machine-verifiable benchmark
evidence, the `model-credibility` pack assesses its sufficiency against NIST
AI 800-3 and the V&V40 validation-evidence pattern, and the assessment
weakeners — several Seahaven-derived — specify the credibility bar the
furnisher targets.** Three projects turn out to be three roles in one
credibility system: UofA the packaging-and-assessment framework, raidex the
evidence furnisher, Seahaven the instrument that discovered the sufficiency
weakeners. Not three side projects — one thesis with three worked components
and running code for each. That is the durable contribution.

Building it now rather than after October strengthens the chapter rather than
competing with it: the invariance claim is demonstrated on a real cohort instead
of promised, and §6a's furnisher/assessor loop becomes a measured gap set instead
of an architecture diagram.
