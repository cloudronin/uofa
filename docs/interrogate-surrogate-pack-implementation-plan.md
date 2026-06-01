# Implementation Plan — Surrogate Pack + SIP

## Context

UofA today checks credibility-evidence completeness for physics **solvers** (V&V 40, NASA-7009B, ISO 42001). This work extends it into the emerging modality of physics-based AI/ML **surrogates** (ROMs, PINNs, operator-learning, data-driven emulators, ML closures) *inside* UofA's home domain — without changing the core engine. Two deliverables, defined by three attached specs:

- **`packs/surrogate`** — a new domain pack (mirrors the ISO 42001 pack) that checks surrogate-credibility evidence for completeness/auditability. Spec: `UofA_Surrogate_Pack_Spec_v0_1.md`.
- **SIP (Surrogate Interrogation Probe)** — a measurement instrument that loads a pre-trained surrogate, exercises it against a supplied benchmark/reference, and emits a **signed, schema-validated, provenance-bearing evidence bundle** with **no verdict**. Spec: `SIP_Evidence_Contract_Spec_v0_1.md`. Orchestration: `SURROGATE_SIP_BUILD_HANDOFF.md`.

The architecture's whole point is a **firewall**: SIP *measures*, the pack *checks auditability*, the practitioner + COU acceptance criteria *judge*. No verdict ever enters SIP or the pack.

> The specs' "defense-complete + Paper A submitted" start gate **no longer applies** and is dropped from this plan — the build is clear to proceed.

### Decisions locked (this session)

1. **SIP packaging → `uofa interrogate` subcommand** behind a `[interrogate]` optional extra (isolating torch/onnx/conformal libs), reusing UofA signing + PROV-DM. Resolves SIP §10 / handoff §3.
2. **G1 taxonomy gate → resolved** via `docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md` (Jakeman et al. arXiv:2502.15496, inverted to defeaters). This is the **declared coverage reference** for Phase D. It is an *emerging reference* and **makes no Cohen's-κ claim** — coverage = "fraction of the 16 reference defeaters a pattern detects," not inter-rater κ against a canonical taxonomy.
3. **v1 measured-evidence carrier → signed JSON bundle is canonical + carried as a linked evidence artifact; xlsx is only a lossy human-review summary.** Pure-xlsx ingestion is rejected (see Integration §). Zero core change for v1.
4. **Evidence-contract schema → on-disk** at `specs/sip_evidence_bundle_schema.json` (mirrors `specs/judge_output_schema.json`), force-included into the wheel.

### Two separable workstreams (key architectural finding)

The `W-SURR-*` patterns and surrogate vocabulary **do not exist yet** — they currently appear only as candidate entries in `packs/core/source_taxonomies.json` and judge prompts. Because the firewall forbids SIP and the rule engine from sharing code, **SIP can be built and tested with zero dependency on the pack**. The SIP↔pack field-to-pattern map only becomes load-bearing at **v2** ingestion. Plan accordingly: Workstream A (SIP) and Workstream B (pack) proceed largely in parallel; the contract field-name freeze (G3) is the one hard ordering dependency between them.

---

## Phase 0 — Gates (resolve before code; handoff §1)

| Gate | Status | Resolution carried into plan |
|---|---|---|
| **G1** Reference taxonomy | ✅ Resolved | Use `docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md` as Phase D reference. Emerging-reference caveat (its §6) reproduced verbatim in coverage report. No κ claim. |
| **G2** Inheritance architecture | ✅ Decided (v1) | Embed a parent-credibility **snapshot** in the surrogate package (`parentModelSnapshot`: parentCOU, parentDecision, parentMRL, parentSignatureTimestamp, snapshotTimestamp). **No engine change.** W-SURR-02 reads the embedded snapshot. True multi-package cross-COU reasoning deferred to v2. |
| **G3** Contract freeze | ⛳ First task | Freeze the evidence-contract field names (SIP §5). Both the pack vocabulary (pack §5) and SIP's emit fields derive from this. **Freeze first, then scaffold both sides.** |

---

## Workstream A — SIP (`uofa interrogate`)

Four deliberately thin components (SIP §3), all heavy deps lazily imported (the established `document_reader.py` / `extract_cmd.py` pattern), so the base install stays lean.

### A1. Module layout (new package `src/uofa_cli/interrogate/`)

Mirrors the `adversarial/` and `readers/` sub-package style; keeps framework-specific logic out of the pack-neutral top level (AGENTS.md §3).

| Module | Responsibility |
|---|---|
| `__init__.py` | exports `run_interrogation()`; **stdlib-only at top level** |
| `adapter.py` | `ModelAdapter` ABC with single contract `predict(inputs)->outputs`; `load_adapter(ref)` resolves a user module by dotted/file path (importlib). SIP **never** imports torch/onnx/sklearn — the user's adapter subclass does. This is the sprawl containment. |
| `loader.py` | benchmark + reference loader (npz/h5/csv); lazy numpy/h5py |
| `orchestrator.py` | the only module touching heavy UQ libs; wraps conformal-prediction / UQpy / SMT-class libs to compute measurements; records `{library, version (via importlib.metadata), config, seed, runEnvironment}` per measurement |
| `measurements/{residuals,envelope,physics,uq}.py` | one thin wrapper per measured quantity |
| `prov.py` | PROV-DM triple construction (run=Activity; surrogate/benchmark/reference=Entity `prov:used`; bundle=Entity `prov:wasGeneratedBy`; each lib=SoftwareAgent) |
| `forbidden.py` | **single source of truth** `FORBIDDEN_TOKENS` (firewall) |
| `schema.py` | loads `specs/sip_evidence_bundle_schema.json` via `paths.find_repo_root()`; `validate_bundle()` |
| `packager.py` | assembles contract dict, attaches PROV-DM, **validates-then-signs** via `integrity.sign_file` |
| `xlsx_render.py` | v1 staged-ingestion authoring view (Integration §) |
| `commands/interrogate.py` | CLI surface: `HELP` / `add_arguments` / `run` |

### A2. Evidence contract + schema (G3 keystone)

Author `specs/sip_evidence_bundle_schema.json` (JSON Schema draft 2020-12) covering all SIP §5 sections: bundle metadata, subject (incl. `surrogateType` enum), declared scope, measurement provenance, measurements, `parentModelSnapshot`, completeness self-declaration (`fieldsPresent[]`, `fieldsDeliberatelyOmitted[]` + reason). Allow the four `INTEGRITY_FIELDS` (`hash`/`signature`/`signatureAlg`/`canonicalizationAlg`) as optional top-level props so a signed bundle still validates.

**Forbidden-field rejection — three layers (belt-and-suspenders):**
1. `"additionalProperties": false` at **every** object level (the repo idiom — see `judge_output_schema.json:5,46,111,126,156`).
2. `propertyNames.not.enum` denylist generated from `FORBIDDEN_TOKENS` at root + freeform-ish nests.
3. **No** `passFail`/`outcome`/`decision`/`credibilityIndex`-style property anywhere in the whitelist (these are legit in the *decision* package — `excel_mapper.py:157,205` — and forbidden in the *measurement* bundle; that contrast is the firewall).

### A3. Command wiring

Register `interrogate` in `cli.py` (`from uofa_cli.commands import …` line 69 + `modules` dict lines 72–92). Args: `--adapter` (dotted/file path to a `ModelAdapter`), `--benchmark`, `--reference`, `--scope` (declared trainingEnvelope/evaluationPoint/declaredPhysicsConstraint config), `--output/-o`, `--key/-k` (ed25519; auto-detect from project `keys/` like `import_excel.py:117–128`). **Deliberately NO `--check`, `--decision`, or threshold flag** (firewall). `run()` flow: lazy-import → load adapter/bench/scope → orchestrate → assemble bundle + PROV-DM → `schema.validate_bundle()` **before** signing → write JSON → `integrity.sign_file(out, key, paths.context_file())` (embeds ed25519/RDFC-1.0/SHA-256 exactly as UofA packages, so `uofa verify` works) → print only the output path + hash prefix. **No verdict line. Exit 0 regardless of any measured value** (a high residual is not a failure).

### A4. `[interrogate]` extra (pyproject.toml)

New optional-dependency group isolating heavy deps (conformal libs, onnx, torch as needed) + `jsonschema` + `pytest` for tests, mirroring `[judge]` (pyproject.toml:82–97). Recommend a separate `[interrogate-corpus]` extra for `airfrans` so AirfRANS/torch stay out of the default test install.

---

## Workstream B — `packs/surrogate`

Mirror the ISO 42001 pack at every layer. Pack version stamps **independently** of the CLI (pack starts at its own `0.x.0`, like `iso42001` 0.5.0 vs CLI 0.9.0).

### B1. Scaffold (Phase A) — `packs/surrogate/`

`pack.json` mirroring `packs/iso42001/pack.json`: `name: "surrogate"`, own `version`, `standards` (VVUQ-20 / V&V-40 / PCMM cross-anchors per proto-taxonomy §2), `shapes: shapes/surrogate_shapes.ttl`, `rules: rules/surrogate_weakener.rules`, `oos.enabled: true` + `rules/oos/oos_v0.1.rules`, `derivations.enabled: true` + `derivations/surrogate_derivations_v0.1.sparql`, `weakener_patterns: <count>`.

### B2. Vocabulary (Phase A) — `shapes/surrogate_shapes.ttl`

New optional, backward-compatible properties in a `uofa-surrogate:` namespace, embedded RDFS-in-shapes like iso42001 (§A vocab + §B/C shapes). Carried as a pack-local context extension over v0.5; packages declare a **`ProfileMinimal`-style profile** (a real switch — see `packs/core/shapes/uofa_shacl.ttl`, `excel_constants.py`, and the iso42001 example packages) so new vocab is optional at the SHACL level. Terms (pack §5, names frozen at G3 to match SIP §5): `trainingEnvelope`, `evaluationPoint`/`evaluationRegion`, `declaredPhysicsConstraint`, `hasConstraintCheckEvidence`, `surrogateUQMethod`, `parentModelSnapshot` (block), `surrogateType` enum, plus `hasBenchmarkProvenance` (W-SURR-04 candidate support) and `dataVintage` reuse.

### B3. Weakener catalog (Phase B) — `rules/surrogate_weakener.rules`

Jena forward-chaining rules in the iso42001 style (`w_surr_<descriptor>` anchor / `'W-SURR-NN'` patternId; `noValue`/`notEqual`/`makeSkolem`). **No core mutation** (handoff §0.4): W-ON-02 stays a presence check in core; W-SURR-03 is the new containment check.

**Reuse as-is (wire, don't reimplement):** W-EP-03 (data vintage, High), W-AR-04 (version drift, High), W-AL-02 (UQ declared / no sensitivity, Medium), W-ON-02 (no envelope declared — presence, High).

**Implement new (pack §6):**
- **W-SURR-01 (High)** — `declaredPhysicsConstraint` present but `hasConstraintCheckEvidence` absent/unlinked. Pure Jena `noValue`.
- **W-SURR-02 (severity split)** — reads the embedded parent snapshot (G2); loosely analogous to W-PROV-01 chain logic. **Two arms, distinct severities** (do NOT collapse): explicit `parentDecision = "Not Accepted"` → **Critical**; `parentDecision` absent / no decision recorded → **High**. Active parental rejection and an in-progress/unrecorded parent decision are different epistemic states; collapsing both to Critical over-fires on legitimately in-progress parent COUs. Implement as two rule arms (or one rule branching severity). `cal-surr-02` boundary cases must exercise **both** arms.
- **W-SURR-03 (High)** — `evaluationPoint`/`evaluationRegion` not contained in `trainingEnvelope`. Containment math → materialize an `_evalOutsideEnvelope` flag via a SPARQL CONSTRUCT in `derivations/surrogate_derivations_v0.1.sparql` (mirrors the iso42001 numeric-derivation precedent `_modelEvalStaleByVersion`/`_auditOverdue`), then a thin Jena rule consumes the flag. Falls to a Python post-pass only if multi-dim geometry exceeds SPARQL FILTER (the W-CON-02/W-PROV-01 split, pack §6).

**Method-first — keep as CANDIDATES, do NOT pre-implement** (handoff §0.3, proto-taxonomy §4/§7): **W-SURR-04** (Benchmark Coverage Gap, SIP-enabled, D-VER-06) and **interrogation-residuals-unlinked**. They are documented gap-probe targets, validated/promoted only through the coverage method — never pre-built to inflate coverage.

### B4. OOS bundle-sufficiency (Phase C) — `rules/oos/oos_v0.1.rules`

Productive-OOS rules following the `src/uofa_cli/oos/` substrate and the iso42001 backward-syntax rule shape (discriminator clauses + `sufficiency_starts_at` + `defeater_type`/`missing_evidence` comment metadata). Declares which surrogate-credibility dimensions a COU is/ isn't asserting, so a COU that legitimately omits a dimension isn't penalized.

### B5. Coverage matrix (Phase D) — `packs/surrogate/coverage/surrogate_proto_taxonomy_coverage.md`

Transcribe proto-taxonomy §4 into the iso42001 coverage-matrix format (`nist_ai_rmf_govern_coverage.md` is the template) with **dual-detection** columns (C3 weakener path + OOS path) per defeater (D-PD/VER/VAL/CCB-* + D-X-01), producing COVERED/PARTIAL/GAP/CANDIDATE per row. **Reproduce the proto-taxonomy §6 caveat verbatim in substance**; report the 5 GAP + 5 PARTIAL rows as named, traceable uncovered dimensions. **Coverage is fraction-covered, not κ** — this is the deliberate divergence from the ISO template (which anchored to NIST AI RMF GOVERN at κ). Expected shape ≈ proto-taxonomy §5: 5 COVERED, 1 CANDIDATE, 5 PARTIAL, 5 GAP, +D-X-01 beyond-reference.

### B6. Calibration packages (Phase E) — `specs/calibration/packages/cal-surr-NNN-*.jsonld`

`cal-surr-01/02/03` minimum (one per new pattern), each with positive/negative/boundary cases, matching the `cal-aims-NNN-out_of_scope-*.jsonld` structure + `adversarialProvenance` block. Add a supplier-evidence-style boundary package if envelope declarations can come from a third party.

### B7. Extract prompt (Phase A/B) — `packs/surrogate/prompts/surrogate_extract_prompt.txt`

Pulls SIP §5 fields **from document evidence only** (model cards, training/validation memos). v4-kv key-value block format (`=== SECTION ===` + flat `key: value`), reusing the enum-echo + template-placeholder rejection guards (per `packs/vv40/prompts/vv40_extract_prompt.txt`). **Measured evidence does not flow through this prompt** — it arrives pre-structured from SIP (Integration §).

### B8. Case study (Phase F) — `packs/surrogate/examples/airfrans/{cou1,cou2}/`

Two COUs of the **same AirfRANS surrogate** (no synthetic models), reusing AirfRANS's own splits:
- **COU1 in-envelope** — eval point inside `trainingEnvelope`; W-SURR-03 silent; expected Accepted.
- **COU2 extrapolation** — eval drawn from AirfRANS Reynolds/AoA extrapolation split; point outside envelope; W-SURR-03 fires (+ inherited/constraint weakeners as present); expected Not Accepted.

Reference is a parent RANS solver → `parentModelSnapshot` populated, W-SURR-02 exercisable. Conservation residuals (W-SURR-01) computed from provided velocity/pressure fields. `uofa diff` shows the divergence in **one figure** (the surrogate analogue of the NASA take-off-vs-cruise divergence). **PDEBench breadth check** confirms the pack isn't airfoil-specific.

---

## Integration (SIP ↔ UofA)

### v1 — staged ingestion, **zero core change** (SIP §7.3)

Pure-xlsx ingestion is **rejected** — the fixed import sheets are scalar-per-cell (no home for `referenceResiduals[]`/`physicsConstraintResidual[]` arrays or per-measurement provenance — `excel_reader.py:469–518`), the Validation Results `pass_fail` column is itself a forbidden token (`excel_mapper.py:205`), and the Decision sheet *requires* a verdict SIP may not author (`excel_reader.py:610–659`). Therefore:

- The **signed JSON bundle is canonical** and never lossily flattened.
- `xlsx_render.py` emits a **human-reviewable authoring view**: Assessment Summary + Model & Data (surrogate as a Model row, benchmark/reference as Dataset rows) + Validation Results with **one row per measurement** carrying a short scalar summary (mean/max residual, empirical UQ coverage) and a `description` naming the QoI/constraint; **`pass_fail` left empty**; Decision left for the human reviewer.
- The signed `.json` bundle **travels alongside as a linked evidence artifact** (referenced from a Validation Results `Identifier/URI` cell → `excel_mapper.py:185–188`). Lossless data is carried + linked; the xlsx is the lossy-but-reviewable summary that flows through the existing `extract → review → import` on-ramp with **no edits to core import/extract**.
- PROV-DM in the bundle keeps UofA's `W-PROV-01` from firing spuriously: every SIP entity has an upstream `prov:` edge, so the core BFS finds no orphan. UofA re-signs its own package on import; the SIP signature is preserved as evidence provenance.

### v2 — native reader (one thin import adapter)

`src/uofa_cli/readers/sip_bundle_reader.py` + a branch wired into `import_excel.py`'s input resolution: re-runs `schema.validate_bundle()` + `integrity.verify_file()` on the incoming bundle, then maps SIP §5 fields directly to `packs/surrogate` JSON-LD per the field-to-pattern map (SIP §7.4), skipping the LLM step for measured fields.

---

## Firewall enforcement (cross-cutting, load-bearing — SIP §8)

Single source of truth `src/uofa_cli/interrogate/forbidden.py::FORBIDDEN_TOKENS` (e.g. `verdict, passFail, pass_fail, accepted, rejected, validated, credible, credibilityIndex, decision, outcome, certify, certified, score, rating, approved`). Consumed by **all** of:
- **Schema** — `propertyNames.not.enum` denylist generated from the list (a small `dev/tools/` generator, run like `uofa schema`; don't hand-edit derived artifacts — AGENTS.md §4).
- **Command** — `uofa interrogate` prints only progress + output path; never chains into check/rules/validate; no decision token; exit 0 regardless of measured values.
- **CI grep guard** — new `dev/tools/scripts/firewall_guard.py` (a Python script, not raw grep, so it *imports* the one token list and can't drift) wired as a `firewall-guard` phony target into `build-config/Makefile`'s `all` chain (CI runs `make all` in the devcontainer — there is no pre-commit config today) and added to `release_check.py`.
- **AGENTS.md** — append **§12 "The interrogation firewall"** in the repo's Rule/Why voice (same enforcement class as the §10 AI-attribution prohibition): no pass/fail/accepted/validated/credible/score/decision field in any bundle/schema/output; the token list is the single source; name outputs for measurement, never judgment; violations are out-of-scope-by-default tracked per §11.
- **Wheel fix (promoted to a v1 acceptance gate — NOT a follow-up)** — add `"specs" = "uofa_cli/_data/repo/specs"` to `[tool.hatch.build.targets.wheel.force-include]` so the schema is reachable after a real `pip install`. Today `specs/` is **not** force-included and `bundle.py` sidesteps this by embedding; if the schema isn't reachable post-install, **the firewall's schema layer silently never runs for real (non-editable) users** — i.e. "looks done" diverges from "is done" on the load-bearing constraint. Gate: schema-rejects-a-forbidden-field-bundle must pass after a clean **non-editable** `pip install` (see Tests & acceptance gates).

---

## Build order (handoff §2 — interleaves A & B)

1. **G3 freeze** → `specs/sip_evidence_bundle_schema.json` + schema-validation tests incl. forbidden-field rejection (SIP §5, §8).
2. **Pack scaffold** — `pack.json`, vocabulary, ProfileMinimal switch (Pack §5 / Phase A).
3. **Weakeners** — wire reuse (W-EP-03/W-AR-04/W-AL-02/W-ON-02); implement W-SURR-01/02/03 (Pack §6 / Phase B).
4. **SIP components** — adapter, loader, orchestrator, packager + signer + PROV-DM (SIP §3).
5. **SIP v1 view** — render import-ready view; verify zero-core-change flow through `extract → review → import` (SIP §7.3 v1).
6. **OOS + coverage + calibration** — bundle-sufficiency rules; coverage matrix vs proto-taxonomy; `cal-surr-*` (Pack §7–9 / Phases C–E).
7. **Case study** — dual-COU AirfRANS (in-dist vs extrapolation); PDEBench breadth check (Pack §11 / Phase F).
8. **Test suites** — E2E to ISO 58-test parity; coverage validation harness (Pack §12 / Phases G–H).
9. **SIP v2 reader** — native SIP-bundle reader; skip LLM step for measured fields (SIP §7.3 v2).

---

## Tests & acceptance gates (don't call a phase done until its gate passes — handoff §4)

- **Firewall:** schema rejects any forbidden-field bundle (parametrized over `FORBIDDEN_TOKENS`, importing the list so it grows automatically); **the same rejection passes after a clean non-editable `pip install` (not just an editable/source checkout) — proves the `specs/` wheel force-include works and the schema layer actually runs for real users**; `firewall_guard.py` self-test catches a poisoned fixture; `uofa interrogate` CLI output asserted free of any decision token; PROV-DM well-formedness (no orphan entity — the W-PROV-01 condition, tested SIP-side **without** importing the rule engine).
- **Zero core change (v1):** a SIP bundle reaches a valid UofA package through the existing on-ramp with no edits to core import/extract.
- **Case study:** surrogate/reference/splits from AirfRANS (no synthetic models); in-dist COU clean on W-SURR-03; extrapolation COU fires W-SURR-03; `uofa diff` shows divergence in one figure; PDEBench confirms non-airfoil-specificity.
- **Coverage:** matrix verifies against the proto-taxonomy with the emerging-reference caveat present; reported as fraction-covered (not κ).
- **Tests:** E2E parity with the ISO 42001 58-test bar (`tests/surrogate/` paralleling `tests/test_iso42001_pack.py`); real-LLM E2E parameterized via `UOFA_E2E_MODEL` and gated by `UOFA_RUN_REAL_LLM=1`; all green in CI with `[interrogate]` installed.
- **Fixtures (AGENTS.md §6/§7):** PDEBench small baselines **committed** under `tests/fixtures/interrogate/pdebench/` (vendorable, offline-CI) — **license precondition (do first):** confirm each committed file is CC-BY and **not** under the PDEBench NLE academic-use-only carve-out that covered parts of the suite; preserve attribution and record a per-file `LICENSE.md`/manifest in the fixtures dir. **Nothing lands in `tests/fixtures/interrogate/pdebench/` until this check passes.** AirfRANS **gitignored + skipif-gated** on a `UOFA_AIRFRANS_DIR`/presence check (ODbL share-alike — never commit), pulled via a new `make interrogate-corpus` target.

---

## Critical files

**Reused / templates (read, mirror — do not mutate core):**
- `src/uofa_cli/cli.py` (register `interrogate`), `src/uofa_cli/integrity.py` (`sign_file`, `INTEGRITY_FIELDS`), `src/uofa_cli/commands/import_excel.py` (run-flow + key auto-detect + v1/v2 seam), `src/uofa_cli/excel_{reader,mapper,constants}.py` (xlsx capability limits).
- `specs/judge_output_schema.json` + `tests/adversarial/judge/test_evidence_gap_schema.py` (schema + forbidden-field test precedent).
- `packs/iso42001/` whole tree (pack template): `pack.json`, `shapes/iso42001_shapes.ttl`, `rules/iso42001_weakener.rules`, `rules/oos/oos_v0.1.rules`, `derivations/iso42001_derivations_v0.1.sparql`, `coverage/nist_ai_rmf_govern_coverage.md`, `examples/hybrid/{cou1,cou2}/`.
- `packs/core/rules/uofa_weakener.rules` (W-PROV-01 / W-ON-02 / W-AL-02 / W-EP-03 / W-AR-04 to reuse), `src/uofa_cli/oos/` substrate, `pyproject.toml`, `build-config/Makefile`, `AGENTS.md`, `docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md`.

**New (create):**
- SIP: `src/uofa_cli/interrogate/**`, `src/uofa_cli/commands/interrogate.py`, `specs/sip_evidence_bundle_schema.json`, `dev/tools/scripts/firewall_guard.py`, `tests/interrogate/**`, `tests/fixtures/interrogate/pdebench/**`.
- Pack: `packs/surrogate/**` (pack.json, shapes, rules, oos, derivations, coverage, prompts, examples), `specs/calibration/packages/cal-surr-*.jsonld`, `tests/surrogate/**`.
- Edits: `cli.py` (+1 module), `pyproject.toml` (`[interrogate]` extra + `specs/` force-include), `build-config/Makefile` (`firewall-guard`, `interrogate-corpus`), `AGENTS.md` (§12), `CHANGELOG.md`.

---

## Verification (end-to-end)

1. `pip install -e '.[interrogate]'`; `pytest tests/interrogate/ tests/surrogate/ -q` green.
2. Firewall: confirm schema rejects a forbidden-field bundle; `python dev/tools/scripts/firewall_guard.py` exits non-zero on a poisoned fixture, zero clean; `uofa interrogate` output contains no decision token.
3. v1 flow: `uofa interrogate` an AirfRANS baseline → signed bundle; `uofa verify` the bundle; render xlsx view → `uofa import` → `uofa check`/`rules` with no core edits.
4. Case study: run both COUs → `uofa diff cou1 cou2` shows W-SURR-03 divergence in one figure; PDEBench breadth run completes.
5. `make all` (incl. `firewall-guard`) green; `python dev/tools/scripts/release_check.py` clean.

## Out of scope (track as GitHub issues per AGENTS.md §11; don't merge as convenience — handoff §5)

Any verdict / fused validate command / correctness check; reimplementing UQ/metrics/sampling instead of wrapping libs; native per-framework model support beyond the single `predict` adapter; live multi-package cross-COU reasoning (v2+); pre-implementing W-SURR-04 / residuals-unlinked candidates (method-first — promoted only via the coverage method); COMPOUND cascades across the new Python+Jena surrogate rules.
