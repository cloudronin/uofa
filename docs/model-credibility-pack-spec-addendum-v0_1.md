# Addendum v0.1: `model-credibility` pack spec

**Applies to:** model-credibility-pack-spec.md (the merge spec)
**Status:** ACTIVE — same gating as the parent spec, whose POST-OCTOBER gate was
lifted on 2026-08-10. This addendum closes three execution-readiness gaps in
§3/§4/§5 and one naming note on §7. Nothing here changes the architecture, the
merge decision, or the firewall.

**Revision note (2026-08-10):** A5.2 is patched to match the parent spec's §4
input-type split, and A2's rule sketch is corrected — see the marked patches.

---

## A1. §4 patch: extraction schema must emit the fields Group B assesses

**Gap:** §4 emits score, uncertainty-if-present, harness/determinism-if-present,
baseline-if-present, claimed-COU-if-present. Two Group-B rules check fields not
in that list:

- W-EV-GEN-02 checks for a **superpopulation / sampling account** (how the
  benchmark items relate to the claimed target population).
- W-EV-CAP-06 checks for a **capability-confound control** (partialling,
  capability-matched comparison, or equivalent).

As written, both rules fire on 100% of inputs by construction — the property
they test for can never exist on the node. That is not a finding, it is a
schema hole.

**Patch:** extend the Group-B extraction emission list to:

| Property | Provenance stamp | Feeds |
|---|---|---|
| `score` | extracted | all |
| `hasUncertaintyQuantification` **(core property, PATCHED)** | extracted-if-present | **W-AL-01** (core) |
| `harnessDeterminismStatement` | extracted-if-present | W-EV-DET-03 |
| `nullBaselineStatement` | extracted-if-present | W-EV-NULL-04 |
| `claimedCOU` | extracted-if-present | W-EV-COU-05, COMPOUND-EV-01 |
| `samplingAccount` | extracted-if-present | W-EV-GEN-02, COMPOUND-EV-02 |
| `confoundControlStatement` | extracted-if-present | W-EV-CAP-06 |

**PATCHED 2026-08-10 — row 2 was going to invent a duplicate property.** The
original row read `uncertaintyStatement` → W-EV-UQ-01. Core already declares
`uofa:hasUncertaintyQuantification` and core's W-AL-01 already fires on its
absence for any `ValidationResult`. A new property for the same concept would
have produced two findings for one missing standard error. The adapter populates
the **core** property; W-EV-UQ-01 is withdrawn (parent spec §3).

All seven follow the existing provenance discipline (`extracted` /
`run-context` / `derived` / `defaulted`). No rule may test a property the
extractor does not emit; conversely, no emitted property without a consuming
rule. Impl plan should enforce this as a pack-lint check (rule-property
coverage), not a convention — it is exactly the kind of drift that recurs.

**The lint must scan core's rules too, not just the pack's.** Had it been scoped
to pack rules only, it would have reported full coverage for `uncertaintyStatement`
and never surfaced the duplication — a coverage check that cannot see the
duplicate is the "check that cannot fail" of AGENTS.md §13.

**INVESTIGATION ITEM (execution agent):** confirm the extractor prompt can
reliably distinguish "sampling account present" from generic dataset
description prose on real model cards before the field goes load-bearing.
Smoke-test on 5–10 cards spanning card quality tiers first.

---

## A2. §3 patch: MRL/COU input source for COMPOUND-EV-01 and W-EV-COU-05

**Gap:** COMPOUND-EV-01 conditions on "high-MRL COU decision." V&V40 gets MRL
from submission context; a model card has none. With no MRL source, the
compound rule is dead code. Separately, W-EV-COU-05 at Critical will fire on
essentially every public model, since almost no card states a context of use.

**Patch, MRL source:** MRL and COU are **run-context inputs**, supplied by the
operator:

```
uofa report owner/model --pack model-credibility \
  --cou "screening triage for X" --mrl 3
```

- Both stamped `run-context` in provenance (they describe the *operator's*
  decision context, not the model's published record).

  **PATCHED 2026-08-10 — both need NEW properties; the obvious ones are already
  occupied.** An `mrm-nist` bundle already carries `modelRiskLevel: 3` (the
  disclosed `MRM_NIST_ASSUMED_MRL` posture, set on *every* bundle including the
  heuristic path) and an already-synthesized `hasContextOfUse` derived from the
  model id. Keying on either would defeat this section: `greaterThan(?mrl, 2)`
  would be true for every model, so COMPOUND-EV-01 would fire unconditionally —
  precisely the dead-rule failure this patch exists to prevent — and the
  W-EV-COU-05 severity split would always take the Critical branch.

  So `--mrl` and `--cou` bind to their own properties, **absent unless supplied**:

  | Flag | New run-context property | Distinct from |
  |---|---|---|
  | `--mrl` | `uofa:decisionRiskLevel` | `uofa:modelRiskLevel` (pack-assumed posture, always 3) |
  | `--cou` | `uofa:decisionContextOfUse` | `uofa:hasContextOfUse` (synthesized from the model id) and `uofa:claimedCOU` (extracted from the card) |

  This is the same distinction this section already draws for `claimedCOU` versus
  `--cou`, applied to all three layers: what the *card claims*, what the *pack
  assumes*, and what the *operator states* are three different things and must not
  share a property. The honest-N/A then falls out of rule structure — no
  `decisionRiskLevel` triple means COMPOUND-EV-01 cannot match, and the readout
  says so.
- If `--mrl` absent: COMPOUND-EV-01 does not fire, and the readout states
  "MRL not supplied — compound risk escalation not assessed." Stated N/A, not
  silence. Same honesty pattern as the sufficiency N/A.
- `claimedCOU` (extracted from the card, A1 table) and `--cou` (run-context)
  are distinct properties. W-EV-COU-05 assesses the *published record's*
  claimed COU; the `--cou` flag scopes the *operator's* assessment. Do not
  conflate them in the shapes.

**Patch, W-EV-COU-05 calibration — DECISION RECORDED:** near-universal firing
is accepted as the finding, not suppressed. The field-wide absence of stated
context-of-use on published models is the same shape as the
sufficiency-vs-completeness argument (FAccT paper) and is the pack telling the
truth. Two mitigations so the readout stays legible:

1. Severity stays Critical only when `--cou` was supplied (an actual decision
   is on the table). With no `--cou`, W-EV-COU-05 fires at **High** — the gap
   is real but no specific decision is being informed.
2. The report renders it once with a field-prevalence note, not as a wall:
   `"no stated context of use (common: most published models lack this)"`.

**Implementation note added 2026-08-10 — the severity split rides on top of the
absence condition, never instead of it.** The finding is
`noValue(?vr, uofa:claimedCOU)` — the *published record* lacking a stated context
of use. Both rule bodies carry that clause; `--cou` only selects the severity. A
sketch that discriminated solely on whether the operator passed the flag would
manufacture a Critical against a model whose card properly states its COU, i.e.
report on the operator's input rather than on the evidence. The required boundary
fixture is exactly that case: card states its COU **and** `--cou` supplied → zero
W-EV-COU-05 firings. Note also that `claimedCOU` (extracted, on the
`ValidationResult`) and `hasContextOfUse` (run-context, on the UoA) stay distinct
properties, per the paragraph above.

---

## A3. §5 patch: heuristic tier distinguishes two absences

**Gap:** the report has two different lines — "no reported evaluation to
assess — N/A" versus "sufficiency not assessed — run with a backend." The
second requires knowing eval evidence *exists* without analyzing it. Keyless
mode as specced cannot honestly pick between them.

**Patch:** add a **presence-only eval-evidence detector** to the heuristic
tier. Cheap signals, no content analysis:

- markdown table whose header row matches benchmark-name patterns
  (MMLU, GSM8K, HumanEval, HELM, `*-bench`, `eval*`, etc. — keep the pattern
  list in pack data, not code)
- a card section heading matching `/eval|benchmark|results|performance/i`
- `model-index` / `results` block in HF card metadata (this one is
  structured and free — check it first)

Dispatch:

| Detector | Backend | Readout line |
|---|---|---|
| no eval evidence found | any | "no reported evaluation to assess — sufficiency N/A" |
| evidence found | keyless/heuristic | "reported evaluation present — sufficiency not assessed, run with a backend" |
| evidence found | LLM backend | Group-B extraction + weakeners |

The detector never asserts sufficiency and never emits `ValidationResult`
nodes — it only picks the honest sentence. This preserves the firewall: the
heuristic tier still declines sufficiency; it just stops declining blindly.

**INVESTIGATION ITEM (execution agent):** the HF `model-index` metadata check
may cover the majority of cases structurally with zero regex. Confirm coverage
rate on a sample before investing in the markdown-pattern path; the regex tier
may be a fallback, not the primary.

---

## A4. §7 note: rule-ID alignment for the thesis chapter (writing-side, due now)

**PATCHED 2026-08-10 — the claim got stronger, so this section shrinks.** It
originally asked the chapter to show the same rule-ID *pattern* across node types:
the blood-pump CFD study tripping its missing-uncertainty weakener and the LLM
benchmark tripping W-EV-UQ-01, same naming convention, different pack.

W-EV-UQ-01 is withdrawn, because core's **W-AL-01** already fires on both. So the
chapter does not need a side-by-side table of two parallel rule families. It needs
one row: **W-AL-01, `noValue(?result, uofa:hasUncertaintyQuantification)`, fires on
a blood-pump CFD study and on an LLM benchmark alike** — same ID, same rule body,
same severity, no pack-specific code. A shared naming convention is a claim about
authorship; one rule firing across two domains is a claim about the construct.
Take the second.

The Group-B rules that *are* new (GEN-02, DET-03, NULL-04, COU-05, CAP-06,
DIV-07) still follow the `W-<cat>-<n>` convention, and the chapter should say why
they are new: each encodes something eval-specific that no simulation-validation
standard needed to state. If any existing vv40 rule ID deviates from the
convention, note it in the table caption rather than renaming frozen praxis
artifacts.

---

## A5. Impl-plan constraints carried forward (restated for the execution agent)

1. The firewall is a hard constraint: no weakener fires on the other layer's
   absent inputs. **PATCHED** — enforce by rule-body structure and
   `factorStandard` gating, not by SHACL profile dispatch (parent spec §2), and
   test with a card-only fixture and a benchmark-only fixture. Both tests must be
   made to fail on purpose once.
2. **PATCHED — no *inferred* sufficiency without a backend.** The original read
   "no keyless sufficiency, ever." Parent spec §4 splits this by input type:
   structured furnisher records read deterministically, prose requires a backend,
   and an absent field stays absent. The A3 detector is presence-only and, under
   the patched rule, is not an exception to anything — it never inferred.
3. Presence/absence semantics on Group B, no 1–5 levels.
4. No new unit type. Benchmark results are `ValidationResult` nodes.
5. `mrm-nist` alias survives one version; `tests/test_report_card.py` must
   pass unmodified against the alias before the rename lands.
6. Rule-property coverage lint (A1) added to pack tests.
7. **PATCHED** — the pre-defense build gate was lifted on 2026-08-10. This
   addendum and the parent spec are both active.
