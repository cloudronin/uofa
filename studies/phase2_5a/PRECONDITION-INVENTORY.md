# Phase 2.5a step 1 — precondition inventory

Date: 2026-08-16
Gate: *"Every MECHANICAL pattern covered or reported uncoverable"* (spec §3 step 1)
Partition: 17 MECHANICAL over 21 base patterns, per Decision Record `fad31cf5`

**Result: the operator split is Class A 9 / Class B 8, not the 13/4 the plan
projected.** Two findings fall out that are worth more than the split itself. This
file is the step-1 evidence and the stop-and-report required by spec §0 before the
enrichment scope roughly doubles.

## Method

Each substrate expanded to RDF through `spec/context/v0.5.jsonld` (the same context
the engine loads), then queried for each rule's **antecedent** — the bindings the
rule body needs before a violation is even expressible. Cross-referenced against the
**actual baseline firings** from `uofa rules --pack vv40` on each unmutated
substrate, which separates two situations a bare precondition probe conflates:

- *antecedent absent* — the rule cannot bind at all, so nothing to mutate;
- *already violated* — the rule fires on the substrate as encoded, so there is no
  clean state to inject into.

## Baselines (unmutated, `uofa rules --pack vv40`)

| Substrate | Firings | Patterns |
|---|---|---|
| morrison/cou1 | 11 | W-AL-01 (3), W-AR-05 (3), W-EP-02 (3), W-ON-02 (1), W-CON-04 (1) |
| morrison/cou2 | 18 | W-PROV-01 (7), W-EP-04 (6), COMPOUND-01 (2), W-AL-02 (1), W-CON-04 (1), W-ON-02 (1) |
| nagaraja/cou1 | 19 | W-AL-01 (6), W-AR-05 (6), W-EP-02 (6), W-ON-02 (1) |

morrison/cou1 and cou2 reproduce the published figures at
`site/src/content/docs/research/nafems-2026.md:21` exactly (11 across 5 patterns;
18 across 6 including 2 COMPOUND-01). These sets are the A3 delta-scoring baselines.

## The inventory

Cells are **mutable site counts** — places a violation could be injected.

| Pattern | cou1 | cou2 | nag1 | Baseline-firing on | Class |
|---|---|---|---|---|---|
| W-EP-02 | 0 | **3** | 0 | cou1, nag1 | **A** (cou2) |
| W-AL-01 | 0 | **3** | 0 | cou1, nag1 | **A** (cou2) |
| W-AL-02 | 0 | 0 | **1** | cou2 | **A** (nag1) |
| W-AR-05 | 0 | **3** | 0 | cou1, nag1 | **A** (cou2) |
| W-ON-01 | **1** | **1** | **1** | — | **A** (all three) |
| W-SI-01 | **1** | **1** | **1** | — | **A** (all three) |
| W-SI-02 | **4** | **4** | **7** | — | **A** (all three) |
| W-CON-04 | 0 | 0 | **1** | cou1, cou2 | **A** (nag1) |
| W-PROV-01 | 0 | **4** | 0 | cou2 (7 hits) | **A** (cou2) |
| W-EP-01 | 0 | 0 | 0 | — | **B** — and see Finding 1 |
| W-EP-03 | 0 | 0 | 0 | — | **B** |
| W-AR-03 | 0 | 0 | 0 | — | **B** |
| W-AR-04 | 0 | 0 | 0 | — | **B** |
| W-CON-02 | 0 | 0 | 0 | — | **B** (`referencesIdentifier` absent everywhere) |
| W-CON-03 | 0 | 0 | 0 | — | **B** |
| W-CON-05 | 0 | 0 | 0 | — | **B** (`hasVerificationActivity` absent everywhere) |
| W-ON-02 | 0 | 0 | 0 | **all three** | **B** — and see Finding 2 |

**Class A: 9** — W-EP-02, W-AL-01, W-AL-02, W-AR-05, W-ON-01, W-SI-01, W-SI-02,
W-CON-04, W-PROV-01.
**Class B: 8** — W-EP-01, W-EP-03, W-AR-03, W-AR-04, W-CON-02, W-CON-03, W-CON-05,
W-ON-02.

Six of the nine Class A patterns are single-substrate: W-EP-02, W-AL-01, W-AR-05 and
W-PROV-01 only on morrison/cou2; W-AL-02 and W-CON-04 only on nagaraja/cou1. Their
per-pattern `n` will be 1-4, so amendment A4's wide-interval naming applies to most
of Class A, not just W-EP-02.

## Finding 0 — the NASA HPT substrates are weakener reports, not evidence packages

The parent ruling names **five** substrate packages (both Morrison CoUs, both NASA
HPT configs, Nagaraja). Only three are executable. `uofa-aero-cou1-nasa7009b.jsonld`
and its cou2 sibling are **not UofA packages**:

- `@graph`-form with no `@context`; **18 nodes: 17 `WeakenerAnnotation`s and one
  stub** carrying nothing but `@id` + `hasWeakener`.
- **No `UnitOfAssurance`, no ContextOfUse, no ValidationResult, no
  CredibilityFactor.** Every core rule opens `(?uofa rdf:type uofa:UnitOfAssurance)`,
  so none can bind.
- The source evidence lives beside them in `aero-evidence-cou{1,2}.zip` as raw
  documents (CSV, PDF, DOCX, TXT + `EVIDENCE_MANIFEST.txt`) — inputs to extraction,
  not an encoded package. **No encoded HPT package is committed.**

**Running `uofa rules` on them reports 17 and 20 weakeners, and every one is
pre-stored rather than inferred.** Demonstrated by stripping the 17 stored
annotations and re-running:

```
Data graph: 0 triples
Inferred 0 new triples (0 total)
SUMMARY: 0 weakener(s) detected
```

Two consequences.

1. **They cannot be mutation substrates** — there is nothing to mutate. Making them
   usable would require running the extraction pipeline over the zips to produce a
   package, which is an LLM step and outside Phase 2.5a's scope. So: **five ruled,
   three executable**, and the report states that with this as the ground.
2. **Worth checking before any reproduction claim rests on them.** A reader who runs
   `uofa rules` against these files sees 17 weakeners and would reasonably take that
   for live detection. `site/src/content/docs/research/nafems-2026.md:21` offers
   "optional cross-domain reproduction with the NASA-STD-7009B HPT-blade example" —
   whether that walkthrough targets these files or the zips was not checked here,
   and it should be before C2's screenshots are taken.

*(This finding cost two wrong statements first: I recorded the aero packages as
having "0 results at all" from a flat-JSON probe that could not see `@graph` form,
then over-corrected to "they fire 17 and 20" from engine output that was reading
stored annotations back. The inventory script now normalises both package shapes.)*

## Finding 1 — W-EP-01's guard names a class the schema does not define

**This is a rule finding, not a corpus finding, and it is reported rather than
fixed** (v0.5.15.1 is frozen; spec §0 OUT, §4.3).

The rule requires `(?claim rdf:type uofa:Claim)`
([rules:39](packs/core/rules/uofa_weakener.rules)). But:

| Where | What it says |
|---|---|
| `spec/context/v0.5.jsonld:13` | defines `AssuranceClaim` only — **no `Claim` term** |
| `packs/core/shapes/uofa_shacl.ttl:67` | declares `uofa:AssuranceClaim a rdfs:Class` — **no `uofa:Claim` class anywhere** |
| `packs/core/shapes/uofa_shacl.ttl:122` | `bindsClaim` has `rdfs:range uofa:AssuranceClaim` |
| `packs/core/rules/uofa_weakener.rules` | declares the `rdfs:` prefix but performs **no subclass inference** |

So the guard can only bind against a class the schema never declares, and the
schema's own range for `bindsClaim` is a *different* class. Observed in the
substrates: morrison/cou2's claim is typed `AssuranceClaim`; nagaraja/cou1's claim
carries **no `rdf:type` at all`.

**W-EP-01 cannot fire on any package that conforms to the schema.**

The provenance is documented in the rule's own comment
([rules:29-35](packs/core/rules/uofa_weakener.rules)): the guard was added in Phase
2.5 iteration 1 because without it the rule fired on every package with a bare-IRI
claim handle — nc_fpr 1.000 at M5, confirmed in
`dev/build/adversarial/phase2/2026-04-26/coverage/summary.csv` (recall 1.000,
nc_fpr 1.000: a rule that fired on everything). The fix cured the false-positive
storm and, by naming a class the schema does not define, made the rule silent on
conformant evidence instead.

**Not yet established:** whether W-EP-01 fires on the Phase 2.5 *regenerated*
corpora under `dev/build/phase2_5/`. It is absent from the v0.5.13 holdout's
zero-recall list, so it fires on something there — presumably packages that type a
claim `Claim`, i.e. against a non-schema class. That check belongs in Arm M's
write-up and would sharpen the finding from "unfirable on the substrates" to
"unfirable on conformant evidence, scoring only on synthetic packages that use a
class the schema does not define." **Do not assert the stronger form until it is
checked.**

## Finding 2 — W-ON-02 fires on every case-study encoding

W-ON-02 is baseline-positive on all three substrates: every case study has a Context
of Use carrying neither `hasApplicabilityConstraint` nor `hasOperatingEnvelope`.

Two consequences:

1. **Its detection is already evidenced without injection** — the rule demonstrably
   fires on real encodings, which is the thing Arm M exists to show.
2. **It cannot be injected as-is.** Producing a recall figure requires first
   enriching a COU to a clean state, then removing the field again — an
   enrich-to-clean operator, structurally Class B.

Worth stating in the report as a finding about the encodings rather than only as an
operator note: the project's own published case studies do not bound the validity
envelope of their Contexts of Use, which is what W-ON-02 exists to catch.

## The iso42001 substrates unlock nothing — a correction

They were admitted on my recommendation that `iso42001` hybrid/cou2 *"would host
W-AR-04 and W-CON-03 directly, no enrichment."* **That recommendation was wrong.**
It came from checking one top-level JSON key per rule (`currentModelVersion` present,
`hasEvidence` present) instead of the whole antecedent — the same
one-keyword-for-the-whole-claim shortcut this project's ground rules exist to
prevent. Measured:

| Rule | What iso42001/cou2 has | What breaks |
|---|---|---|
| **W-AR-04** | `currentModelVersion` = `v1.6.0` ✓ | its single result `model-eval` carries **0** `wasGeneratedBy`, so `hasValidationResult → wasGeneratedBy → used → cfg.modelVersion` breaks at the first hop — which is also why W-EP-02 fires on its baseline |
| **W-CON-03** | 19 `hasEvidence` nodes ✓ | **0** carry `evidenceTimestamp`, and the package has **no** `signatureTimestamp` — both halves of the antecedent absent |

**Class A stays 9, Class B stays 8.** What the two substrates do add is sites on
three patterns that were already Class A:

| Pattern | 3 substrates | 5 substrates |
|---|---|---|
| W-ON-01 | 3 | **5** |
| W-SI-01 | 3 | **5** |
| W-SI-02 | 15 | **19** |

Nothing else moves. Note these three were already the best-supported patterns; the
ones that actually need `n` are the single-substrate six (W-AL-02 and W-CON-04 at
n=1; W-EP-02, W-AL-01, W-AR-05 at n=3; W-PROV-01 at n=4), and iso42001 adds **zero**
to every one of them.

Their baselines under the core rule set are identical to each other — W-AL-01,
W-AR-05, W-EP-02, W-ON-02, one hit each — and both are `ProfileMinimal` ISO 42001
AI-management-system encodings (enterprise LLM retrieval; customer-facing LLM
drafting), not CM&S case studies. If they stay in, Arm M must report their rows
separately, and D4's "published-case substrate" framing needs a qualifying clause.

## Finding 3 — 27 of the 48 baseline firings are vacuous, and the catalog is discriminating on serialization shape

Found while writing site discovery. **This is the largest finding of step 1 and it
generalizes the report's lead.**

Three rules — W-AL-01, W-AR-05, W-EP-02 — test `noValue(?result, <property>)` on a
ValidationResult. When a package references its results as **bare IRIs** rather than
inline objects, the referenced node has no properties in the graph, so every
`noValue` succeeds vacuously and all three rules fire on every result. This is the
same pathology W-EP-01's Phase 2.5 guard was added to fix
([rules:29-35](packs/core/rules/uofa_weakener.rules)); **W-AL-01, W-AR-05 and W-EP-02
carry no equivalent guard.**

The correlation across the substrates is perfect:

| Substrate | results | shape | W-AL-01 / W-AR-05 / W-EP-02 |
|---|---|---|---|
| morrison/cou1 | 3 | all bare-IRI | **3 / 3 / 3** |
| morrison/cou2 | 3 | all inline | **0 / 0 / 0** |
| nagaraja/cou1 | 6 | all bare-IRI | **6 / 6 / 6** |

### The falsifying test

morrison/cou1's three results were inlined — **same IRIs, same count, the three
properties the rules read, nothing else altered** — and re-run:

| | W-AL-01 | W-AR-05 | W-EP-02 |
|---|---|---|---|
| as committed (bare IRIs) | 3 | 3 | 3 |
| results inlined | **0** | **0** | **0** |

All nine firings were vacuous. (`W-SI-01` appears in the inlined run only because
the signature was stripped to avoid asserting integrity over changed content — an
artifact of the test, not a finding.)

### Scale

| Substrate | baseline firings | vacuous | substantive |
|---|---|---|---|
| morrison/cou1 | 11 | **9** | 2 |
| morrison/cou2 | 18 | 0 | 18 |
| nagaraja/cou1 | 19 | **18** | 1 |
| **total** | **48** | **27** | **21** |

### Why this is the sharpest available statement of the instrument disagreement

**morrison/cou1 and morrison/cou2 encode the same study.** cou1 fires nine extra
weakeners than cou2 does on those three patterns, and the entire difference is that
cou1 references its validation results by IRI while cou2 inlines them. No difference
in the underlying evidence, the study, or its adequacy. **The catalog is
discriminating on serialization shape.**

That is the same finding as W-EP-01 (fires only on a class the schema never
declares) and W-ON-02 (fires on every real encoding), now with a controlled
comparison behind it: same study, two encodings, nine-weakener delta from
serialization alone.

### What it changes

1. **Delta-scoring baselines (amendment A3) are mostly artifacts** on two of three
   substrates. The baseline-persistence assertion still works — vacuous findings
   persist as reliably as substantive ones — but the report must not present these
   baselines as detections of inadequate evidence.
2. **A3's negative controls are exposed.** A defect-free package that references its
   results by IRI will fire W-AL-01, W-AR-05 and W-EP-02 on every result. Any clean
   variant built for A3 must inline, or the FP arm measures serialization style.
   Worth checking before the external negative is encoded.
3. **The published NAFEMS figures are affected.**
   `site/src/content/docs/research/nafems-2026.md:21` gives "COU 1 = 11 weakeners
   across 5 patterns, COU 2 = 18 across 6" as committee-facing reproduction figures.
   Nine of COU 1's eleven are vacuous. The command reproduces, the count is real,
   and what it measures is not what a reader would take it for. **C2's lane, flagged
   not fixed.**
4. **Arm M's recall for these three patterns is only interpretable on
   morrison/cou2** — the one substrate where they do not already fire vacuously.
   Which is also the only substrate hosting their mutation sites, so the battery is
   unaffected; but the interpretation note belongs in the report.

**No catalog edits.** v0.5.15.1 is frozen and this is §4.3 territory: reported, with
the failing case attached. A guard mirroring W-EP-01's would be a v0.6 candidate.

## Finding 4 — the conformance split, measured (addendum E)

All 23 Class A mutants run through `uofa shacl` at v0.5.15.1. The three substrates
pass the profile unmutated, so every split below is caused by the mutation.

| Pattern | conformant | schema-caught | Group |
|---|---|---|---|
| W-AL-01 | **3** | 0 | conformant-but-flawed |
| W-AR-05 | **3** | 0 | conformant-but-flawed |
| W-EP-02 | **3** | 0 | conformant-but-flawed |
| W-AL-02 | **1** | 0 | conformant-but-flawed |
| W-CON-04 | **1** | 0 | conformant-but-flawed |
| W-ON-01 | 0 | **3** | schema-caught — no headline row |
| W-SI-01 | 0 | **3** | schema-caught — no headline row |
| W-SI-02 | 0 | **6** | schema-caught — no headline row |

**The prediction against E was exactly right.** W-SI-01, W-ON-01 and W-SI-02 delete
fields carrying `sh:minCount`, have no value to corrupt in place, and so break
conformance by construction. They are also precisely the three patterns that have
never produced a confirmed detection at any catalog version. E's explanation holds:
**they cannot reach the rule layer in a conformant pipeline.**

### The measurement vindicates E ruling 1 directly

E requires profile status recorded as a first-class field rather than inferred from
`caught_by`. This run shows why in one line: **all 23 mutants fire their target
pattern at C3, including all 12 schema-caught ones.** Non-conformant and rule-caught
is not a contradiction — it is the common case here. Inferring conformance from
`caught_by` would have collapsed 12 of 23 mutants into the wrong group.

### Headline battery, Class A

**11 conformant-but-flawed mutants across 5 patterns**, n = 3, 3, 3, 1, 1. Every
one fires its target. That is the entire Class A contribution to a GATE-H3 headline,
and every row carries a wide Wilson interval — amendment A4's naming requirement
applies to all five, not to a subset.

### Input to the open denominator question

Session 2 recorded a recommendation of **13** (16 less the three architecturally
unreachable patterns) against the standing **16**. This measurement is the evidence
that recommendation rests on: those three cannot produce a conformant-but-flawed
mutant at all, so under E they can score no headline row, and at a ≥95% bar three
mandatory zeros cost ~19 points. **Both denominator questions remain the author's
and both must land before scoring.** Recorded here as input, not as a resolution.

## Scope impact

| | Planned | Measured |
|---|---|---|
| Class A (single edit) | 13 | **9** |
| Class B (enrichment) | 4 | **8** |

The enrichment family doubles. Against the ~16h ceiling this is the pressure spec
§4.5 says to stop and report on rather than absorb, so it is reported here before
any operator is written.

## Reproducing this

```bash
python studies/phase2_5a/inventory.py                      # the table above
uofa rules --pack vv40 packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
uofa rules --pack vv40 packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
uofa rules --pack vv40 packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld
```

## Coverage statement

**Searched.** All three substrates expanded to RDF and probed for all 17 MECHANICAL
antecedents; rule engine run on each unmutated substrate for the baselines;
`spec/context/v0.5.jsonld`, `packs/core/shapes/uofa_shacl.ttl` and
`packs/core/rules/uofa_weakener.rules` cross-read for the W-EP-01 vocabulary
question; 180 M5-era `w-ep-01` packages checked for inline claim typing.

**NOT searched.** The Phase 2.5 regenerated corpora under `dev/build/phase2_5/`
were not probed for claim typing (see Finding 1's "not yet established"). The
`iso42001` and `surrogate` example packages were not evaluated as substrates, being
outside the declared three-substrate scope, though `iso42001` hybrid/cou2 carries
`currentModelVersion` and `hasEvidence` and would host W-AR-04 and W-CON-03
directly. No mutation was performed.
