# UofA Phase 2.5a Spec v1.3: Deterministic Mutation Arm

Status: READY for implementation
Date: 2026-08-16 (v1.1 and v1.2 amendments same day, before any operator was written)
Owner: Vishnu Vettrivel
Parent specs: UofA_Unified_Repair_Spec_v2_1.md (items A2, B2, GATE-H3), UofA_Investigation_Spec_v1_0.md findings (INV-8, INV-11, INV-1)

## Change log — v1.0 → v1.1

v1.0's §0.1 required a typing check before any code. **The check ran, and it falsified
the diagnosis v1.0 was built on.** Rather than let the implementation proceed against a
spec that contradicts its own precondition result, v1.1 folds in the falsification and
the author's amendment rulings. Sources: session 1's Phase 2.5a implementation plan
§§1–4, `docs/investigations/INV-8-findings.md` addendum 2, and
`docs/UofA_Decision_Record_2026-08-16.md` addenda A and B (committed alone at
`fad31cf5`, before the run they govern).

| # | v1.0 said | v1.1 says | Why |
|---|---|---|---|
| 1 | MECHANICAL set is **15** patterns | **17** — the partition and battery scope (gate denominator is **13**, see v1.3 below) | Ruling 4 (W-PROV-01) and addendum A (W-AR-03) both restore patterns to MECHANICAL |
| 2 | Typing check pending; falsification escalates | Check **RUN, diagnosis FALSIFIED**; escalation resolved here | Typing was correct; the antecedents never bind |
| 3 | MUT-TYP-01/02/03 (datatype family) | **Deleted.** Replaced by Class B `MUT-ANT-*` | The datatype theory was the falsified one |
| 4 | MUT-INT-02 (re-sign after mutation) | **Dropped as a finding**, not worked around | The issuer path refuses to sign synthetic packages — a positive architectural claim |
| 5 | Stack order "SHACL → rules → signature" | **C2 SHACL → C1 Integrity → C2.5 Derivation pre-pass → C3 Rules** | Verified against `commands/check.py`; a fourth layer v1.0 omitted |
| 6 | "the three case-study encodings" | Five distinct encoded packages, delta-scored from baseline | Substrate ruling, v2.1 §8 delta note |
| 7 | Gate treatment of enrichment unstated | Full battery gates; split reported as ecological validity | Addendum B, pre-committed before scoring |
| 8 | Operator split projected at 13 A / 4 B | **Measured: 9 A / 8 B** (§1.2.1) | `studies/phase2_5a/PRECONDITION-INVENTORY.md` at `fed5a37e` probed all 17 antecedents against the substrates. The enrichment family doubles — standing scope escalation |
| 9 | `iso42001` proposed as the Class A recovery path and walkthrough substrate | **Falsified and removed** (§1.2.1, §1.4) | `2ecf24cf`. The proposal rested on a top-level key check; the full antecedents break. Admitted as substrates and re-measured, iso42001 unlocks **zero** new patterns |
| 10 | NASA HPT substrates carry "zero ValidationResults", then "they fire 17 and 20" | **Both wrong. They are not UofA packages** (§2.1) | Three passes: JSON keys, then expanded graph, then inference. The files hold only stored `WeakenerAnnotation`s; 24 of 29 rules open on `UnitOfAssurance`, which is absent. Five substrates ruled, **three executable** |
| 11 | W-EP-01 finding held in its weak form pending a corpus check | **Strong form established** (§1.2.1 finding 1) | `uofa:Claim` declared nowhere; 256 synthetic packages emit bare `type: "Claim"` resolving to it via `@vocab`. The rule scores 1.000 on non-schema evidence and is silent on conformant evidence |

**v1.3a (measured, `5bb1051a` / `87463323`) — E applied over all 23 Class A mutants.** Class A/B is **8/9** (W-PROV-01 moved A→B: every single-edit form suppresses rather than adds). The conformance split is measured and confirms addendum F's three exclusions from evidence rather than argument: W-ON-01, W-SI-01 and W-SI-02 produce **zero** conformant mutants. Headline Class A battery is **11 conformant-but-flawed mutants across 5 patterns**, all firing, all on wide intervals. One finding for the methods text: **all 23 mutants fire at C3, including all 12 schema-caught ones**, so inferring profile status from `caught_by` would have misfiled 12 of 23 — E's first-class-field requirement is now measured, not argued. A source-version precondition is added at §1.3: conformance readings require `2a1d3544` in the measuring branch.

**v1.3 (Decision Record addendum F) — the gate denominator is 13, with four named exclusions.** 17 scopes the battery; the gate is evaluated over 13. Out: **W-EP-01** (unfireable as shipped — guard names a class the schema never declares; reported as a discovered catalog defect) and **W-SI-01, W-ON-01, W-SI-02** (architecturally unreachable — the completeness profile intercepts their defect before the rule layer runs). A defect the schema catches is not a rule-engine miss, and a gate that cannot mathematically pass regardless of rule quality is a foregone conclusion wearing one. **Two conditions:** the three deletion mutants are still built and reported in a schema-caught table beside the rule-layer table, so cross-layer detection stays visible; and A4 states the arithmetic plainly, including what the 16-denominator version would have scored. All four exclusions named, mechanism'd and dated **before** scoring — which is the only thing distinguishing this from post-hoc scoping. See §2.2.

**v1.2 (Decision Record addendum E) — the SHACL-conformance split becomes the organizing structure**, not a footnote. A mutant that flunks the profile never tests the rules; it tests the schema. Changes: profile status recorded per mutant (§1.3); the corpus and report split conformant-but-flawed vs schema-caught, with **the gate scored from the conformant group only** (§2.2); operator design prefers value corruption over field deletion (§1.2.2); a one-time precondition test asserts the substrates were valid before mutation (§0.2); the manifest gains an expected-catch-layer field checked against the measured one (§1.1); and Class B enrichments must assert conformance after enrichment, before violation (§1.2.1).
Positioning: this is Phase 2.5 closing its measurement debt, not a new phase. Phase 2.5 left MECHANICAL-class recall measured against a corrupt denominator (LLM generation failed to mechanically realize typed-literal and structural flaws; five patterns at 0.000, two never measurable, all as generation artifacts per INV-8/INV-11). Phase 2.5a repairs the instrument with a deterministic mutator, measures the shipped catalog once at v0.5.15.1, and exposes the loop as the committee-runnable `uofa inject` / `uofa detect` demo (parent B2).

Budget: 9-13h paired total (mutator 4-6h, CLI+walkthrough 1-2h, P25-A run 3-5h + ~$50 LLM spend for the generator-arm rerun if included). Hard scope cap below.

---

## 0. Scope cap (kill criteria)

IN: mutation operators covering exactly the **17 MECHANICAL patterns** of the ruled partition. All three rulings are landed and the count is final — decision 3 excluded the compounds (21 base patterns), decision 4 restored W-PROV-01, and Decision Record addendum A ruled W-AR-03 MECHANICAL:

| Class | n | Patterns |
|---|---|---|
| MECHANICAL | **17** | W-EP-01..03, W-AL-01..02, W-ON-01..02, W-AR-03..05, W-SI-01..02, W-CON-02..05, W-PROV-01 |
| JUDGMENT | 4 | W-EP-04, W-AR-01, W-AR-02, W-CON-01 |
| Excluded | 2 | COMPOUND-01, COMPOUND-03 |

**17 is the partition size, which scopes this battery. GATE-H3 is evaluated over 13** (addendum F, §2.2). `docs/investigations/INV-1-findings.md` §3 carries the partition table as ruled. Two distinctions, both of which have already caused an error in a parent document:

- **17 scopes the battery; 13 is the gate denominator.** Every one of the 17 gets an operator or a documented reason it cannot have one. Four are then excluded from the *gate*, individually named and mechanism'd — see §2.2.
- **Pattern count is not instance count.** The ≥95% is measured on **defect instances** per A5's effective-n rule. Do not substitute one for the other.

Single-fault mutants only — Class B's two edits carry one fault (§1.2). Substrates: §2.1. One measurement run at v0.5.15.1.

OUT (post-defense, JVVUQ paper): compound mutants, operator taxonomy research, higher-order mutation, additional substrates, JUDGMENT-pattern mutation (prose-level flaws stay with the LLM generator), any rule or catalog change (v0.5.15.1 is frozen; a rule found defective is a REPORTED finding, not a fix).

If implementation pressure pushes against any OUT item, stop and report rather than expanding.

## 0.1 Precondition: the typing check — RUN, and it FALSIFIED the diagnosis

**Do not re-run this check.** It executed 2026-08-16 and is recorded in
`docs/investigations/INV-8-findings.md` addendum 2, the first entry of this phase's
evidence trail. The escalation clause fired; this section is its resolution.

**Typing is correct and was never the problem.** `spec/context/v0.5.jsonld` declares
`dataVintage`, `modelRevisionDate`, `evidenceTimestamp` and `signatureTimestamp` as
`xsd:dateTime`, so expansion yields typed literals and Jena's `lessThan` / `greaterThan`
work as written. `modelVersion` / `currentModelVersion` are untyped, correctly — W-AR-04
compares them with `notEqual` on strings.

**The real cause: the rules' antecedents never bind.** Across all 180 committed
`w-ep-03` packages in `dev/build/adversarial/phase2/2026-04-26/confirm_existing/`:

- **180/180** carry **zero** ValidationResults with `wasGeneratedBy`, so W-EP-03's chain
  `hasValidationResult → prov:wasGeneratedBy → prov:used → Dataset.dataVintage` cannot bind.
- **65/180** park datasets under `dataset` / `datasets` / `uofa:bindsDatasetInline` — terms
  **absent from the context**, so expansion silently drops those nodes.
- The staleness is real in the prose and real in the values (vintage 2025-10-10 < revision
  2025-11-03). It is absent from the graph.

**The finding that outranks the recall number.** Four of the seventeen MECHANICAL rules —
W-EP-03, W-AR-04, W-CON-03, W-AR-03 — read structures that **no encoding produced by the
project's own protocol ever instantiates**, across five packs and seven example packages.
`bindsRequirement` is a bare IRI everywhere, so W-AR-03's `requiredVerificationMethod` has
nothing to bind to; `activityType` appears nowhere. This belongs in Ch4 regardless of what
Arm M measures, and it feeds v0.6 (encodings should instantiate `wasGeneratedBy` chains and
inline their requirements).

The consequence for this spec is §1.2's two operator classes: the four affected patterns
cannot be tested by editing a field that is not there, so their operators must **instantiate
the antecedent and then violate it**.

---

## 0.2 Precondition: the substrates were valid before mutation (one-time, v1.2)

**Before any scoring**, assert that the unmutated substrates pass `uofa verify` and run
`uofa check` cleanly apart from their known measured baselines, at the shipped catalog
version v0.5.15.1. Record the output as a committed artifact.

The report has to be able to say **"mutation started from valid packages" with a
citation, not an implication.** Every recall number in Arm M rests on that premise, and
it is currently unstated. It costs one command per substrate and it closes the gap
between what the report asserts and what it can show — which is the same gap this
phase exists to close everywhere else.

Baselines are known and measured (§2.1), so "cleanly apart from their baselines" is a
defined comparison, not a judgment call.

---

## 1. Deliverable 1: the mutator (`uofa inject`)

### 1.1 Architecture

A mutation is a pure function: `(package_graph, target_spec) -> (mutated_graph, mutation_record)`. The engine:

1. Loads a substrate package via the SAME loading/canonicalization path the CLI verify/detect flow uses (find it; do not reimplement parsing — the emittability rule from parent C1 applies here identically: a mutant the CLI path cannot load is a defect in the mutator).
2. Applies exactly one operator at one target site.
3. Verifies the mutant is LIVE: canonical-graph diff against the substrate must be non-empty. Canonicalization-erased mutations are logged as EQUIVALENT and excluded from the corpus and the denominator. (Standard mutation-testing hygiene; the equivalent-mutant log is itself a reportable artifact.)
4. Writes the mutant package plus a manifest entry derived FROM THE DIFF, never from the operator's intent: manifest records operator ID, target pattern, site (subject/predicate/object or byte range for signature mutations), the before/after values, and the canonical diff hash. The manifest is ground truth by construction; keep it mechanically derived so that property is literally true.

   **v1.2 adds one field that is deliberately *not* diff-derived: `expected_catch_layer`** (`schema` | `rules`), set by the operator's **design intent**. It is compared against the measured catch layer, and **divergence in either direction is a finding**: an operator that expected the rule layer and was caught by the schema has not tested what it was written to test; one that expected the schema and reached the rules means the profile is looser than assumed. Both are cheap to detect and neither is visible without stating the intent up front. This is the one place intent belongs in the manifest, and it is safe precisely because it is never used as ground truth — only as the thing the measurement is checked against.
5. Signature-family mutations operate on the serialized signed form (mutate AFTER signing to model tamper; also support re-sign-after-mutation variants to model fraudulent-but-valid packages where the flaw is content, not integrity).

Determinism: seedable RNG for site selection when a package offers multiple valid target sites; default run enumerates ALL valid sites per operator per substrate (the corpus is small; exhaustive beats sampled at this scale).

### 1.2 Operator table

Implement per-operator against the corrected INV-1 MECHANICAL list. The table below is organized by family; the implementer maps each operator to its target pattern(s) from the INV-1 findings file and records the mapping in the code as data (operator registry), not comments. Where INV-1's corrected table differs from this draft mapping, INV-1 wins.

| ID | Family | Operator | Draft target patterns |
|---|---|---|---|
| MUT-DEL-01 | Field deletion | Remove uncertainty bounds from a ValidationResult | W-AL-01 adjacency check only if MECHANICAL per INV-1; else nearest MECHANICAL completeness rule |
| MUT-DEL-02 | Field deletion | Delete a provenance link (remove prov:wasDerivedFrom / equivalent edge) | W-PROV-01 |
| MUT-DEL-03 | Field deletion | Strip signature block entirely | signature-presence rule |
| MUT-DEL-04 | Field deletion | Remove a mandatory metadata field below SHACL-mandatory level (see §1.3 layer note) | completeness rules |
| MUT-VAL-01 | Value corruption | Version-pin mismatch: evidence cites model version N, package carries N+1 | W-CON version rules |
| MUT-VAL-02 | Value corruption | Checksum/hash mismatch: alter recorded digest, leave payload | integrity comparison rule |
| MUT-VAL-03 | Value corruption | Out-of-range or contradictory numeric (e.g. negative sample size) where a rule compares values | applicable W-CON members |
| MUT-REF-01 | Referential break | Point an evidence reference at a nonexistent entity IRI | reachability rules |
| MUT-REF-02 | Referential break | Sever provenance chain mid-graph (delete intermediate node, leave endpoints) | W-PROV-01 |
| MUT-INT-01 | Integrity | Flip bytes in signed content after signing | signature-verify rule |
| ~~MUT-INT-02~~ | Integrity | **DROPPED AS A FINDING — do not build.** See §1.2.2 | — |
| MUT-TMP-01 | Temporal | Validation activity timestamp precedes model creation | ordering rules |
| MUT-TMP-02 | Temporal | Superseded-version timestamps inverted | ordering rules |
| MUT-CRD-01 | Cardinality/conflict | Duplicate a mandatory node with conflicting values | uniqueness/contradiction rules |
| MUT-SI-01 | Structural | The W-SI-01 flaw form, per what the rule actually tests (read the rule first; this pattern has never produced a confirmed detection at any version, so its operator is written FROM the rule's precondition) | W-SI-01 |
| MUT-SI-02 | Structural | The W-SI-02 flaw form, injected at the layer BELOW SHACL enforcement (see §1.3) | W-SI-02 |
| MUT-ON-01 | Structural | The W-ON-01 flaw form, written from the rule's precondition (same never-fired status as W-SI-01) | W-ON-01 |

Coverage requirement: every one of the 17 MECHANICAL patterns has ≥1 operator whose mutants it should catch. If a pattern's precondition cannot be violated by any operator, that is a FINDING (the pattern may be misclassified, or its rule untestable as written) — report it, do not force an operator.

### 1.2.1 The two operator classes (v1.1, measured)

§0.1's falsification splits the 17 patterns by whether a substrate can host the flaw at all. **The split is measured, not projected** — `studies/phase2_5a/PRECONDITION-INVENTORY.md` (commit `fed5a37e`) expanded all three substrates through the engine's own context, probed all 17 antecedents, and cross-referenced actual baseline firings. Its numbers govern this section:

| | Projected in the plan | Measured (step 1) | **Measured after E** |
|---|---|---|---|
| Class A (single edit) | 13 | 9 | **8** |
| Class B (enrichment) | 4 | 8 | **9** |

**W-PROV-01 moved A → B on measurement**: every single-edit form *suppresses* rather than adds (claim-edge −1 to −2, intermediate-edge −1 at all six sites), and `isFoundationalEvidence` has no site in any encoding.

**Class A — edit a field the substrate already has.** Single edit. **8 patterns**, and the conformance split (addendum E) partitions them measured at v0.5.15.1 over all 23 Class A mutants:

| Pattern | conformant-but-flawed | schema-caught | Gate-eligible |
|---|---|---|---|
| W-AL-01 | **3** | 0 | yes |
| W-AR-05 | **3** | 0 | yes |
| W-EP-02 | **3** | 0 | yes |
| W-AL-02 | **1** | 0 | yes |
| W-CON-04 | **1** | 0 | yes |
| W-ON-01 | 0 | **3** | no — architecturally unreachable |
| W-SI-01 | 0 | **3** | no — architecturally unreachable |
| W-SI-02 | 0 | **6** | no — architecturally unreachable |

**Headline Class A battery: 11 conformant-but-flawed mutants across 5 patterns, n = 3, 3, 3, 1, 1. All fire.** Every row carries a wide Wilson interval, so §2.2's wide-interval naming requirement covers **all five**, not a subset. The three substrates pass the profile unmutated, so every split above is caused by the mutation and not by the substrate.

The zero-conformant result for W-ON-01, W-SI-01 and W-SI-02 was **predicted from the `sh:minCount` read and then measured**, which is why addendum F's exclusion of those three rests on evidence rather than on the shapes argument alone.

> **Measured finding that vindicates E's first-class-field requirement.** All 23 Class A mutants fire their target at C3 — **including all 12 schema-caught ones**. Non-conformant-and-rule-caught is not an edge case here, it is the common case. **Inferring profile status from `caught_by` would have filed 12 of 23 mutants into the wrong group.** That is the concrete reason `conformant` must be recorded independently, and it is now measured rather than argued. It belongs in the methods text.

> **Gate composition, worth stating plainly.** The 13 gate patterns decompose as **5 Class A conformant + 8 Class B** (Class B's 9 less W-EP-01). So **8 of the 13 rest on enrichment-class mutants** — structures the project's own encodings never instantiate. That is legitimate under addendum B, whose whole point is that the gate asks a unit-detection question, and the ecological-validity split reports the limitation alongside. But a gate that is majority-enrichment is a different object from one that is majority as-encoded, and the report should say so in the same breath as the number rather than leaving a reader to derive it.

**Class B — `MUT-ANT-*`, antecedent instantiation plus violation.** Two edits carrying **one fault**: the first instantiates the structure the rule reads, the second violates it. **8 patterns:**

| ID | Target | What it must instantiate before it can violate |
|---|---|---|
| MUT-ANT-01 | W-EP-03 | A ValidationResult with a `prov:wasGeneratedBy` → `prov:used` → Dataset chain, then a stale `dataVintage` |
| MUT-ANT-02 | W-AR-04 | `currentModelVersion` alongside the config's `modelVersion`, then a mismatch |
| MUT-ANT-03 | W-CON-03 | A comparable `evidenceTimestamp` / `signatureTimestamp` pair, then an inversion |
| MUT-ANT-04 | W-AR-03 | `bindsRequirement` inlined as a typed node carrying `requiredVerificationMethod`, plus `activityType` on the generating activity — the largest enrichment |
| MUT-ANT-05 | W-CON-02 | A `referencesIdentifier` target, absent from every substrate, then break its reachability |
| MUT-ANT-06 | W-CON-05 | A `hasVerificationActivity` node, absent from every substrate, then sever its `wasGeneratedBy` link |
| MUT-ANT-07 | W-ON-02 | **Enrich-to-clean.** The rule is baseline-positive on all three substrates; a recall figure requires first adding `hasApplicabilityConstraint` / `hasOperatingEnvelope`, then removing one again |
| MUT-ANT-08 | W-EP-01 | **Read finding 1 before building this.** Any mutant must type a claim `uofa:Claim`, a class the schema does not define — so this operator cannot produce a MECHANICAL-rollup row, only a separately-reported finding |

Every Class B mutant carries **`enrichment: true`** in its manifest, so the report can split the rollup per §2.2.

**Two findings from the inventory that change what the numbers mean.**

*Finding 1 — W-EP-01 scores 1.000 on evidence the schema does not define, and cannot fire on evidence it does.* **Established in the strong form; no longer provisional.** Its guard requires `(?claim rdf:type uofa:Claim)`. `uofa:Claim` is declared **nowhere**: the context defines `AssuranceClaim` only, the SHACL shapes declare `uofa:AssuranceClaim a rdfs:Class` and make it `bindsClaim`'s `rdfs:range`, and the rules perform no subclass inference. Meanwhile the synthetic corpus emits bare `type: "Claim"`, which resolves through `@vocab` to `uofa:Claim` and fires the rule — 256 packages in the Phase 2 `confirm_existing` tree alone. That is the source of its 20/20 recall on the v0.5.13 holdout. The three case-study substrates type their claim `AssuranceClaim` (morrison/cou2) or carry no `rdf:type` at all (nagaraja), so the rule is silent on every conformant encoding.

The guard was added in Phase 2.5 to cure a false-positive storm (nc_fpr 1.000 at M5) and cured it by making the rule silent on conformant packages while leaving it firing on synthetic ones. **Rule finding, reported not fixed** — v0.5.15.1 is frozen, §4.3.

The measurement-validity consequence is now sharp enough to state without hedging, and the report must state it: **W-EP-01's recall number measures the synthetic corpus's use of a non-schema class, not the rule's ability to detect anything in real evidence.** It does not belong in the MECHANICAL rollup as a plain row. Report it separately, with the mechanism named. A pattern scoring 1.000 for this reason is a more useful finding than the same pattern scoring 1.000 for the reason a reader would assume — and the difference is exactly what Arm M was built to expose.

*Finding 2 — W-ON-02 fires on every case-study encoding.* Its detection is therefore already evidenced without injection, which is what Arm M exists to show; but it cannot be injected as-is, hence the enrich-to-clean operator. Report it as a finding about the encodings, not merely an operator note: **the project's own published case studies do not bound the validity envelope of their Contexts of Use**, which is precisely what W-ON-02 exists to catch.

> **Scope escalation, standing.** The enrichment family doubles, 4 → 8, against a ~16h ceiling. The inventory reports this rather than absorbing it, per §4.5. The author's call is whether to fund the wider enrichment scope, or to cut Class B to the four patterns whose enrichment was already scoped and report the other four as uncoverable-within-budget. **Do not resolve this inside the implementation.**

**Class B is not a weaker test.** The gate's question is unit detection: does the rule fire when its precondition is present and violated. Class B answers exactly that question. What it cannot answer — whether such evidence occurs in packages the project's own protocol produces — is §2.2's ecological-validity split, reported separately and never folded into the gate.

### 1.2.1a Operator design preference: corrupt in place, don't delete (v1.2)

Where a pattern can be exercised **either** by deleting a mandatory field (likely
schema-caught) **or** by corrupting a value in place (stays conformant), **prefer the
corruption form.**

Valid-but-wrong is both the harder test and the realistic threat model: a package that
fails schema validation gets bounced at intake; **the dangerous package conforms and is
still wrong.** That is the package the rule catalog exists for, and it is the only kind
whose detection says anything about C3.

Where only the deletion form exists, keep it and let it land in the schema-caught group
**honestly** — do not contrive a conformant variant to manufacture a recall row.

> **Three patterns have no corruption form, and it is the expected three.** W-SI-01
> (delete `uofa:signature`), W-ON-01 (delete `uofa:hasContextOfUse`) and W-SI-02
> (`noValue` on required bindings) are pure presence/absence rules with no value to
> corrupt. Both named fields carry `sh:minCount` in `packs/core/shapes/uofa_shacl.ttl`,
> so deleting them breaks conformance by construction. All three land schema-caught and
> produce no headline recall row — and all three are exactly the patterns that have
> never produced a confirmed detection at any catalog version. The conformance split
> supplies the reason: **they cannot reach the rule layer in a conformant pipeline.**
> Report that as the positive architectural finding v1.0 §1.3 item 4 anticipated. The
> denominator consequence is **ruled: they leave the gate denominator, which becomes 13** (addendum F, §2.2). They do **not** leave the battery or the report — build all three deletion mutants, let the completeness layer catch them, and report that table beside the rule-layer one.

**Class B enrichments must assert conformance after enrichment, before violation.**
An enrichment that adds a non-conformant structure produces a schema-caught mutant and
**the target rule never runs** — the enrichment would have bought nothing, and the
pattern would score zero for a reason unrelated to the rule. Assert profile conformance
on the enriched-but-not-yet-violated intermediate, and fail loudly if it does not hold.

### 1.2.2 MUT-INT-02: dropped as a finding, not worked around

`package_policy.sign_package` calls `assert_issuable`, and `is_synthetic` (`package_policy.py:52-64`) is True for any package marked `synthetic: true`. **The production signing path refuses to sign mutants.** MUT-INT-02 (re-sign after content mutation, modelling a fraudulent-but-valid package) therefore cannot be built.

Report this; do not engineer around it. It is a second instance of §1.3 item 4's positive architectural claim — *the production signing path cannot produce a fraudulent-but-valid package* — and it is a stronger result than the operator would have been. Consequences for the build: mutants stay honestly marked `synthetic`; signature-family operators mutate already-signed substrate bytes rather than re-signing; and the walkthrough uses `uofa check` / `uofa detect`, never `uofa verify`, on a mutant.

### 1.3 The layer-attribution design (W-SI-02 lesson)

W-SI-02 zeroed because SHACL validation rejects its flaw before the rule engine runs. That is not a detection miss; it is the C2 layer catching what C3 never sees. The mutator and scorer must make this visible instead of burying it:

1. Every mutant runs through the FULL assessment stack in production order. **v1.1: the order is no longer an open question, and it is not what v1.0 assumed.** Verified against `check.run_structured` (`commands/check.py:130-215`), the actual order is:

   **C2 SHACL → C1 Integrity → C2.5 Derivation pre-pass → C3 Rules**

   Two consequences v1.0 got wrong. Signature verification runs **before** the rule engine, not after. And there is a **fourth layer the spec did not mention**: a derivation pre-pass that can hand C3 an *enriched* package rather than the mutant on disk. It is verified inert for the packs in scope (`vv40`, `nasa-7009b` and `core` declare no `derivations`), but "inert here" is not "absent," and a future pack that declares derivations would silently change what the rule layer sees.

   This satisfies escalation criterion 4 (stack order differs from what the manuscript describes) — it is reported here rather than discovered during scoring, and Ch3's description needs the same correction.
2. The detection record per mutant captures WHICH layer flagged it: `caught_by: shacl | integrity | derivations | rules | none`. The `derivations` value is required even though the pre-pass is expected to be a no-op, and the report must state explicitly where it was one — an absent column and a no-op column are different claims.

   > **Source-version precondition, before any conformance reading.** The branch taking the measurement **must contain `2a1d3544`** (`fix(shacl): resolve @context from the shipped file, not over the network`). It changes `shacl_friendly.py` and the derivations runner — i.e. the conformance path itself. Measured on a branch without it, conformance readings are artifacts of network `@context` resolution: session 1 obtained 0/23 non-conformant and then 23/23 conformant, both garbage, before spotting the staleness. Neither result announces itself as wrong, which is what makes this worth a precondition rather than a footnote. **Merge main before recording profile status**, and record the commit the measurement ran at. (A static read of the shapes file — such as the `sh:minCount` check behind §1.2.1a — is unaffected; this applies to anything that runs the stack.)

   **v1.2: record SHACL profile status for every mutant as a first-class field**, not as an inference from `caught_by`. **Measured justification (§1.2.1): all 23 Class A mutants fire at C3, including all 12 schema-caught ones — inferring status from `caught_by` would misfile 12 of 23.** The full stack already runs; this is the same data elevated. `conformant: true|false` is what §2.2 partitions the corpus on, and it must be recorded even when some later layer also fires — a mutant can be non-conformant *and* caught by the rules, and collapsing that into one column loses the distinction the split depends on.
3. Recall is scored at the package-assessment level (was the defect flagged by ANY layer) AND reported per-layer. GATE-H3's ≥95% MECHANICAL claim is the package-assessment-level number; the per-layer table is the defense-in-depth finding for Ch4.
4. For patterns whose flaw is SHACL-mandatory (W-SI-02 class): additionally generate the variant that bypasses the SHACL check if one exists in a realistic threat model (e.g. a profile not applied), and report both. If no realistic bypass exists, the finding is "this defect class cannot reach the rule layer in a conformant pipeline," which is a positive architectural claim, stated as such.

### 1.4 CLI surface (parent B2)

```
uofa inject --pattern <pattern-id> --package <path> [--operator <mut-id>] [--site <n>] [--seed <s>] --out <dir>
uofa inject --all --package <path> --out <dir>          # full battery on one substrate
uofa detect --package <mutant-path>                      # existing detection, report to stdout
uofa inject-verify --manifest <path> --results <path>    # scores detect output against manifest; exits nonzero on any miss
```

Wrap existing entrypoints per INV-11's exposure map; plumbing only, no logic forks. README walkthrough (`docs/demo/inject-and-detect.md`): fresh-clone setup steps (honest list per INV-11's runnability assessment, including Java/Jena), then the professors' narrative verbatim: perfect package in, known flaw injected, flaw caught, manifest confirms. Three worked examples, one per letter-named flaw type (remove uncertainty → MUT-DEL-01 on W-AL-01; change version numbers → see the note below; remove signatures → MUT-DEL-03 on W-SI-01).

> **v1.1 note on the middle demo — it has no Class A route on the three substrates.** "Change version numbers" maps to W-AR-04, which the measured inventory puts in **Class B**: none of `morrison/cou1`, `morrison/cou2` or `nagaraja/cou1` carries `currentModelVersion`, so the demo would have to *instantiate* the field before it could mismatch it. That undercuts the letter's own narrative — *perfect package in, known flaw injected, flaw caught* — because a walkthrough that first adds a field the package never had invites the question of what else was staged. The W-CON version rules do not rescue it: W-CON-02/03/05 are Class B too, and the only Class A member of that family, W-CON-04, is not a version-pin rule.
>
> **There is no Class A route for it anywhere.** An earlier draft of this spec proposed `iso42001` hybrid/cou2 on the grounds that it carries `currentModelVersion` and `hasEvidence`. **That was measured and falsified** (`2ecf24cf`): cou2 does carry `currentModelVersion` = `v1.6.0`, but its only validation result has zero `wasGeneratedBy`, so W-AR-04's chain `hasValidationResult → wasGeneratedBy → used → cfg.modelVersion` breaks at the first hop; and its 19 `hasEvidence` nodes carry no `evidenceTimestamp`, with no `signatureTimestamp` anywhere, so W-CON-03 has neither half. The original note came from a top-level key check rather than the whole antecedent — the failure mode this spec exists to guard against, caught by the same inventory method that found it.
>
> **Build the walkthrough as: remove uncertainty (W-AL-01, morrison/cou2) and remove signatures (W-SI-01, any substrate).** Both are Class A, both are the committee's own named flaw types, neither needs enrichment narration. For the third, either run an honest enrichment demo and narrate it as one — "this field is not present in the published encoding, so the demo adds it before breaking it, and here is why that is still a real test of the rule" — or ship two demos. Two clean demonstrations are worth more than three where one needs a paragraph of explanation to be honest. **Never narrate an enrichment mutant as a plain injection.**

---

## 2. Deliverable 2: P25-A measurement at v0.5.15.1

One measurement, two arms, one report. Already scoped as P25-A in `PHASE2_5_STATUS_REPORT.md:46-48`; this section binds its design to the mutation arm.

### 2.1 Arms

**Arm M (mutation):** full operator battery, all valid sites, scored via inject-verify. Ground truth: manifests (perfect by construction). Primary output: per-pattern recall for MECHANICAL patterns at v0.5.15.1, package-assessment level, with per-layer attribution.

**Substrates (v1.1 rebinding).** v1.0 said "the three case-study encodings," which is ambiguous where a case study has more than one CoU. The substrate ruling (v2.1 §8) binds it to **every distinct encoded package — five**: `morrison/cou1`, `morrison/cou2`, `nasa-hpt/take-off`, `nasa-hpt/cruise`, `nagaraja/cou1`. Session 1's precondition inventory qualifies what each can host:

| Substrate | Hosts result-bound patterns? |
|---|---|
| morrison/cou1 | Yes — 3 ValidationResults, none with `wasGeneratedBy` |
| morrison/cou2 | Yes — **3/3 results carry `wasGeneratedBy`**; sole host for W-EP-02 |
| nagaraja/cou1 | Yes — 6 results, none with `wasGeneratedBy` |
| nasa-hpt/take-off, /cruise | **No — they are not UofA packages.** See below |

**Five substrates ruled, three executable.** That is the finding to report, and it took three passes to reach because the first two each checked one layer and reported as if they had checked the stack.

The aero `.jsonld` files are **weakener reports, not packages**. Their `@graph` holds 17 `WeakenerAnnotation` nodes plus one `@id`/`hasWeakener` stub (cou1), and 20 plus a stub (cou2) — no `UnitOfAssurance`, no ContextOfUse, no ValidationResult, no CredibilityFactor. **24 of the catalog's 29 rules open on `(?uofa rdf:type uofa:UnitOfAssurance)`**, so nothing binds. The apparent "17 and 20 firings" are exactly the 17 and 20 annotations already serialized in the files, read back. Strip them and the engine reports `Data graph: 0 triples / Inferred 0 new triples / 0 weakener(s) detected`. **W-AR-05 does not fire on them.**

The source evidence sits beside them as `aero-evidence-cou{1,2}.zip` (CSV/PDF/DOCX/TXT plus a manifest). **No encoded HPT package is committed anywhere in the repo.** Making one requires running extraction over the zips — an LLM step, out of scope for this phase (§0 OUT).

So the battery runs on the three case-study encodings, and the report states the five-vs-three gap with *this* as the ground: two of the ruled substrates have no encoded package to mutate. Not "excluded, no results," and not a presumed zero.

> **Method note, earned.** Three successive readings of these two files were wrong — JSON top-level keys instead of the expanded graph, then engine output instead of inference. Each was a real check at one layer reported as a conclusion about the stack. The rule this phase adopts: **run the falsifying test first.** For a detection claim that means stripping the stored result and confirming the engine reproduces it, not reading the engine's output and assuming it inferred what it printed.

`iso42001` and `surrogate` are **out** as well: admitted and re-measured, iso42001 unlocked zero new patterns (Class A stayed 9, Class B stayed 8), adding only sites on W-ON-01, W-SI-01 and W-SI-02 — none of them among the six single-substrate patterns that actually need `n`.

> **Escalation to the author, outside this phase. The NAFEMS page now has two separate defects, and they are independent.**
>
> **(a) The HPT step reports stored annotations.** `site/src/content/docs/demo/nafems.mdx:138-142` instructs a reader to run `uofa rules` against these two files and frames it as "the same CLI runs against an HPT-blade thermal-analysis example" — cross-domain reproduction, directly after the Morrison section where the output *is* live detection. A reader sees 17 and 20 weakeners and has every reason to read that as detection. It is a read-back. The source table (`:154`) lists them as "HPT blade JSON-LD — Hand-authored", and the published site renders them as "The UofA package node …".
>
> **(b) The Morrison COU1 figure is 9/11 serialization artifact.** The same page publishes "COU 1 = 11 weakeners across 5 patterns, COU 2 = 18 across 6" as committee-facing reproduction figures. Nine of COU 1's eleven are the vacuous `noValue` firings described in v2.1's A3 precondition. The command reproduces and the count is real; what it measures is not what a reader would take it for.
>
> (b) is the harder one, because unlike (a) it is not fixed by relabelling — the number is correct and the walkthrough works. It needs the figure reported with its composition, or a different figure. Both are C2's, both are public, and both are committee-facing per v2.1 §0.3 item 2. Reported, not touched.

**Delta-from-baseline scoring, all substrates.** No substrate has an empty baseline. Measured by the inventory with `uofa rules --pack vv40` on each unmutated substrate:

| Substrate | Firings | Patterns |
|---|---|---|
| morrison/cou1 | 11 | W-AL-01 (3), W-AR-05 (3), W-EP-02 (3), W-ON-02 (1), W-CON-04 (1) |
| morrison/cou2 | 18 | W-PROV-01 (7), W-EP-04 (6), COMPOUND-01 (2), W-AL-02 (1), W-CON-04 (1), W-ON-02 (1) |
| nagaraja/cou1 | 19 | W-AL-01 (6), W-AR-05 (6), W-EP-02 (6), W-ON-02 (1) |

The Morrison figures reproduce `site/src/content/docs/research/nafems-2026.md:21` exactly (11 across 5; 18 across 6 including 2 COMPOUND-01), which is the independent check that the harness and the published record agree. These sets **are** the delta-scoring baselines. A mutant's detection set is therefore never compared against zero. `inject-verify` scores the **delta**:

1. the injected finding **appears** in the mutant's detection set, **and**
2. the baseline findings **persist undisturbed** (set equality on the remainder).

Condition 2 is the one worth having. A mutation that silently *suppresses* an existing finding would score as a clean pass under naive scoring while having broken something; that failure mode is currently invisible. Baseline persistence is a unit-test assertion **per substrate**, not a post-hoc report column.

**Arm G (generation):** the existing 180-package holdout (and Phase 2.5 battery per the P25-A scoping) rerun at v0.5.15.1, JUDGMENT patterns primary, MECHANICAL reported with the known-instrument-limitation caveat and cross-referenced to Arm M. NC clean rate re-measured at v0.5.15.1 in the same run, killing the version-mismatched pair the manuscript currently carries (73.4% recall at v0.5.7 beside 97.1% NC at v0.5.15.1 — one version, one table, per `PHASE2_5_STATUS_REPORT.md:34`).

**Null controls (A2's standard, non-negotiable):** every headline number reported beside the score a non-reading system achieves. For detection recall: a fire-on-everything strategy (recall 1.0, specificity ~0) and a fire-on-nothing strategy (specificity 1.0, recall 0) bracket the table; the informative null is a random-firing rate matched to the catalog's base firing frequency. For the NC clean rate: the fire-on-nothing null. State each null in the table header, not a footnote.

### 2.2 Metrics and gates

Per A5's specification: per-pattern recall with Wilson 95% CIs (n per pattern will be small-to-moderate; report n in every row), per-class rollups (MECHANICAL from Arm M; JUDGMENT from Arm G), FP characterization from clean substrates run through the same stack (the zero-injection arm: the three unmutated substrates plus, when INV-5 resolves, the external negative).

Gate evaluation (GATE-H3, held as set): MECHANICAL ≥95% (Arm M, package-assessment level, **denominator 13**), JUDGMENT ≥80% (Arm G), overall ≥80%, FP <10% per class. The gate is evaluated ONCE against this run. Misses are reported as findings with root-cause per pattern; the catalog is not patched and re-run inside this phase (a fix-and-remeasure cycle is a disclosed v0.6 event, post-defense or explicitly author-approved).

**The denominator and its four exclusions (addendum F, ruled before scoring).**

| Step | n | Excluded | Ground |
|---|---|---|---|
| MECHANICAL partition | 17 | — | Scopes the battery |
| less unfireable-as-shipped | 16 | W-EP-01 | Guard names `uofa:Claim`, never declared by the schema. Reported as a **discovered catalog defect** |
| less architecturally unreachable | **13** | W-SI-01, W-ON-01, W-SI-02 | Deleted fields carry `sh:minCount`; the completeness profile intercepts before C3 runs |

A defect the schema intercepts is not a rule-engine miss — it is the completeness layer working upstream. Scoring those three as zeros would make the gate measure the architecture's layering rather than the catalog's detection, and a gate that cannot mathematically pass regardless of rule quality is a foregone conclusion wearing one.

**Two conditions, and they are not optional — they are what makes this not gate-softening:**

1. **Build and report the schema-caught demonstrations anyway.** The three deletion mutants are constructed, the completeness layer catches them, and that table appears **beside** the rule-layer table. Total system detection across layers must be visible, so a reader can see nothing was quietly dropped. A pattern excluded from the gate is not a pattern excluded from the report.
2. **State the arithmetic plainly in A4:** denominator 13, **what the 16-version would have scored**, and why 13 is the honest framing. Both numbers, not just the favourable one.

Disclosed reasoning **before** measurement is the only thing separating this from post-hoc scoping, and the record's timestamp is the evidence. The same four exclusions decided after seeing the numbers would be indistinguishable from tuning.

**The conformance split decides which mutants count (Decision Record addendum E, v1.2).** The corpus and the report partition on profile status, and this partition is prior to every other rollup:

| Group | Definition | What it is evidence of |
|---|---|---|
| **Conformant-but-flawed** | passes the profile, carries the injected defect | **The true test of the rule catalog. Headline per-pattern recall and the GATE-H3 evaluation come from this group only.** |
| **Schema-caught** | the mutation breaks profile conformance | Defense-in-depth at the validation layer. Confirms C2 does its job; **says nothing about C3**, and is never reported as a rule-engine detection |

The reasoning is the catalog's own job description: it exists to catch what schema validation cannot see. A mutant that flunks the profile never reached the rules, so scoring it as a rule detection measures the wrong layer and inflates the number in the direction that flatters. Both groups are reported; only one gates.

This changes **which mutants count toward the gate**, not the gate itself or the substrate set. The one arithmetic question it raised — patterns with no conformant form at all — is **ruled in addendum F: the denominator becomes 13.**

**Enrichment-split treatment, pre-committed (Decision Record addendum B).** The **full battery — Class A plus Class B — evaluates the gate.** The gate's question is unit detection: does the rule fire when its precondition is present and violated, which Class B mutants test legitimately.

The as-encoded vs enrichment-required split is reported **alongside**, as the **ecological-validity result**, and is **not folded into the gate arithmetic**: four rules proven to work *and* proven unable to fire on evidence the project's own protocol currently produces. Both halves of that sentence are findings, and the second one is the more important. This treatment is fixed here, before any result exists, precisely so it cannot be chosen after seeing which framing is more flattering.

**Report tiny n as tiny.** A per-pattern `n` column is mandatory in every row. W-EP-02 has **n=3 sites on a single substrate** (morrison/cou2 is the sole host of the `wasGeneratedBy` chain) and will carry a Wilson interval spanning most of the unit interval. The gate paragraph must **name which patterns clear on wide intervals**, so no reader can take the rollup as uniformly supported. A pattern that "passes" on n=3 is a different claim from one that passes on n=40, and the table has to say so without being asked.

### 2.3 Report artifact

`studies/phase2_5a/REPORT.md` + machine-readable results (same discipline as existing studies/ artifacts: pinned inputs, SHA-256 manifests, re-derivation script). Contents: the per-pattern table (both arms, nulls, CIs, layer attribution), the equivalent-mutant log with exclusion counts, the gate evaluation, the generator-vs-mutator delta table per pattern (interpretation column: rule-works-generator-cant-express vs rule-gap), and the version-consistent recall/NC pair that replaces the mismatched one.

---

## 3. Sequencing

| Step | Work | Gate to next |
|---|---|---|
| ~~0a~~ | **DONE.** Ruling record committed alone at `fad31cf5`, carrying addenda A and B, before the run it governs | Ordering provable; A4 cites the commit, not the file |
| ~~0b~~ | **DONE.** §0.1 check run; `INV-8-findings.md` addendum 2 written (five findings); `INV-1-findings.md` §3 updated to the ruled 17/4 | Falsification on record ahead of any operator |
| 0c | **§0.2 substrate-validity precondition** (v1.2): `verify` + `check` on each unmutated substrate at v0.5.15.1, output committed | "Mutation started from valid packages" becomes citable, not implied |
| 1 | Operator registry + engine + liveness check | **All 17** MECHANICAL patterns covered or reported uncoverable — count the registry, do not trust the prose enumeration (§1.2.1) |
| 2 | CLI wrap + inject-verify | Fresh-clone walkthrough executes end to end |
| 3 | Arm M run | Manifest-scored results committed |
| 4 | Arm G rerun at v0.5.15.1 (+NC) | Version-consistent table committed |
| 5 | REPORT.md + gate evaluation | A2/D8 prose can start with real numbers |

Steps 3 and 4 are parallel once step 2 lands. Do not begin manuscript A2 text before step 5; the parent spec's ranks 1-2 both consume this report.

## 4. Escalation criteria

1. ~~§0.1 check falsifies the typing diagnosis~~ → **FIRED AND RESOLVED in v1.1.** The check falsified it for all three patterns; the resolution is §1.2.1's Class B. No further action.
2. Any MECHANICAL pattern uncoverable by mutation → finding, not forced operator. **Live:** the two NASA HPT substrates host no result-bound pattern (§2.1).
3. Arm M recall below gate on any pattern where the mutant is confirmed live and correctly targeted → rule finding; report with the failing mutant attached; NO catalog edits.
4. ~~The assessment stack's layer order differs from what the manuscript describes~~ → **FIRED AND RESOLVED in v1.1 §1.3.** The order is C2 → C1 → C2.5 → C3, with a fourth layer v1.0 omitted. Ch3's description still needs the correction; that is a writing-queue item, not a blocker here.
5. Budget exceeds 13h or any OUT-scope pressure → stop and report. Session 1's plan budgets ~16h against this spec's 9-13h; the overage is the redesigned operator classes and is accepted, but §4.5's stop-and-report still binds at the revised ceiling.
6. **New:** any operator whose construction would require editing the catalog, the context, or `package_policy` → stop. v0.5.15.1 is frozen and the issuer path's refusal to sign synthetic packages is a finding, not an obstacle (§1.2.2).

## 5. Done-gate (phase)

All five: (1) every MECHANICAL pattern has measured recall at v0.5.15.1 from Arm M with live-mutant-verified denominators; (2) `uofa inject`/`detect`/`inject-verify` run from a fresh clone per the walkthrough; (3) the three letter-named flaw demos execute; (4) REPORT.md committed with nulls, CIs, layer attribution, and the single-version recall/NC pair; (5) GATE-H3 evaluated once, result recorded whichever way it lands.
