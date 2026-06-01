# Product A — Post-Refactor Implementation Plan

**Status:** approved plan (2026-05-31). Sits alongside `docs/interrogate-surrogate-pack-implementation-plan.md` (the SIP + surrogate-pack build, the substrate this rides on). Source specs: `UofA_ProductA_PostRefactor_Phases_v0_2.md` (spine), `UofA_Appliance_and_Packaging_Spec_v0_1.md`, `UofA_Explainer_SLM_Training_and_Moat_Spec_v0_1.md`.

## Context

The pack-shaped architecture refactor has landed: the four versioned interfaces are real, the firewall is enforced at one chokepoint, and packs load behind fixed contracts. The job now is to bring **Product A** to life as a self-serve, shift-left confidence tool for simulation engineers adopting physics-AI surrogates — *"point it at your surrogate, get a principled, auditable read on when to trust it, run it yourself in minutes."*

The spec (`UofA_ProductA_PostRefactor_Phases_v0_2.md`) makes **first-contact the product**: the evaluator's first run is the value. The core deliverable is therefore the **concept appliance container** (stock Qwen + open UofA, behind the four interfaces), which is simultaneously the evaluator on-ramp **and** the P0 bakeoff baseline. The bakeoff gate then forks the path into "ship the stock-model tool on the convention moat" vs. "build the trained-SLM moat." Honest promise to keep marketing matched to: *measurement for a human to judge, never an automated verdict.*

**This plan covers**: a short refactor-tail (P2d) → **Phase A** (the appliance + on-ramp, detailed) → **the Gate** (a runnable bakeoff) → **Phase B** (the basic guardrail) → **Phase C/D** (conditional). Everything behind the gate (SLM corpus/fine-tune, premium packs, MCP) stays parked per the spec.

**User decisions locked for this plan**: ① appliance **bundles the ship-target stock model (Qwen 2.5 7B) in-image** (self-contained, air-gap-faithful); ② the bakeoff runs against a **minimal answer-keyed stratified slice built now**; ③ the demo uses a **real PhysicsNeMo-CFD** signal source.

---

## Current state — the reuse surface (verified)

The refactor and the surrogate/SIP build are largely done. Most of Phase A is **wiring existing parts into a container**, not new logic.

| Capability | State | Where |
|---|---|---|
| Four interfaces (measurement, reference, detection, guardrail) | ✅ real, versioned | `interrogate/measurement_method.py`, `interrogate/reference_source.py`, `specs/pack_manifest_schema.json`, `guardrail.py` |
| Firewall chokepoint + forbidden tokens | ✅ enforced | `firewall.py`, `interrogate/forbidden.py` |
| Action-region signing (§4 carve-out, generalized) | ✅ `engineerDecision` + `guardrailAction` | `interrogate/signing.py` (`sign_scoped_block`) |
| `interrogate` **measure** path (adapter→bundle→sign→compare) | ✅ runs | `commands/interrogate.py`, `interrogate/comparison.py` |
| **Verdict-free output framing (A3)** | ✅ mostly done | `comparison.py` ("no threshold, no pass, no verdict"); firewall |
| `packs/surrogate/` (shapes, rules, oos, derivations, coverage, examples) | ✅ complete | `packs/surrogate/**` |
| SIP bundle → surrogate JSON-LD → `check pack=surrogate` | ✅ proven blueprint | `harness/run_corpus.py`, `readers/sip_bundle_reader.py` |
| **Stock-Qwen explanation stage** (firings → plain language) | ✅ exists, reuse | `interpretation/` + `interpretation/functions/explain.py`, Ollama backend in `llm/litellm_backend.py` |
| Guardrail interface | ✅ ABC + **stub only** | `guardrail.py` (`ThresholdGuardrailStub`, `build_guardrail_action`) |
| `interrogate init` | ⚠️ interactive-only (hard-fails non-TTY by design) | `commands/interrogate.py` `_run_init` / `_ask` |
| README on-ramp for SIP/surrogate | ❌ **zero mentions** | `README.md` |
| Appliance container / compose | ❌ none exist | — (only `.devcontainer/`) |
| P0 bakeoff harness + answer-keyed corpus | ❌ none exist | — |
| Real guardrail logic, JVM daemon | ❌ stub / 3 cold spawns | `guardrail.py`; `derivations/runner.py:118`, `rules.py:513`, `oos/runner.py:103` |

---

## Phase 0 — Land the refactor tail (P2d)

The four interfaces are merged to `main`; the in-flight branch `feat/pack-shaped-architecture` is finishing **P2d** (kill the `paths._active_packs` process-global, thread `active` explicitly — commits P2d-1/2a/2b, ~25 modified files in the working tree). Land this first so Phase A builds on a clean active-pack API (`paths.resolve_active_packs(args)`, `pack_dir(..., active=...)`).

- **Do**: finish/verify the P2d threading, run the full suite green, merge.
- **Acceptance**: `pytest` green (the ~2131-test bar); no `_active_packs` global remains; `--pack surrogate` reliably activates the pack end-to-end.

---

## Phase A — The evaluator on-ramp (the concept appliance) — *core deliverable, detailed*

A simulation engineer brings up one container, points `interrogate` at a surrogate + benchmark + reference, runs it (including non-interactively), gets an explained signed report, and reads it correctly as trust-calibration evidence — in well under an hour from the README alone.

### A1 — README SIP on-ramp (pure docs, highest impact)
- **File**: `README.md` only. Insert a new H2 **`## Interrogate a Surrogate (SIP)`** as a top-of-README front door — after the 30-second demo, **before `## Why UofA?` (≈line 52)**. Cross-link to `## Domain Packs`.
- **Content** (pull verbatim framing from `packs/surrogate/README.md` and `comparison.py`): what `interrogate` is (a measurement instrument, **verdict-free**); the four things the engineer supplies (`--adapter`, `--benchmark`, `--reference`, `--scope` — reference is *supplied, never generated*); a copy-pasteable **container** invocation; how to read the `render_comparison` output, stressing **zero weakeners ≠ accurate** — the engineer judges (`uofa decision sign`).
- **Risk**: keep the copy-paste example runnable without AirfRANS data — use the committed `packs/surrogate/examples/airfrans/cou1/*.jsonld` fixture (`uofa rules <that> --pack surrogate --explain`), not the live-measure path.

### A2 — Non-interactive `interrogate init --yes`/defaults
- **File**: `src/uofa_cli/commands/interrogate.py` only. This **reverses** the deliberate "NO --yes" comment (lines 51-52) — scoped to *interactivity*, not to the no-silent-scope / no-fabricated-reference invariants, which stay.
- **Design**: add `--yes`/`--non-interactive`, `--scope <file>` (adopt a pre-written scope verbatim — the cleanest path), `--input-names`/`--output-names`, and subject fields (`--surrogate-id`, `--model-version`, `--surrogate-type`). Branch at the top of `_run_init`: in `--yes` mode collect inputs from flags/`--scope`; else the existing `_ask*` prompts. Everything downstream (`init_wizard.generate_adapter_source`, `build_scope`, the `unprovenanced_scope_fields` invariant, `smoke_test_adapter`) is **shared, unchanged** — the pure logic already lives in `init_wizard.py`.
- **Defaults that keep rigor**: every field's provenance defaults to `entered-by-engineer` (or `extracted-from:<docs>`); **fail loudly** if `--yes` is given with neither `--scope` nor envelope bounds (never silently invent an envelope); the smoke test still runs when `--benchmark` is supplied.

### A3 — Output framing (verdict-free)
- **Mostly done** in `comparison.py` + the firewall. **Remaining**: (a) the README framing (A1), and (b) when the appliance appends the **Qwen explanation** to the report, label it `role: reference-annotation` (decode, never adjudicator) — already the firewall's stance; just ensure the demo report renders that label.

### A4 + the appliance container (bundle Qwen in-image)
- **Files (new)**: `Dockerfile.appliance`, `.dockerignore` (exclude `site/node_modules`, `runs/`, `dev/build`, `.git`), `docker/appliance/uofa.toml`, `docker/appliance/run-demo.sh`, plus `appliance-image` / `appliance-demo` targets in `build-config/Makefile` (mirror the existing `airfrans-*`/`corpus` target style).
- **Image (multi-stage)**: ① `maven:3-eclipse-temurin-17` → `mvn package` (the rule-engine JAR); ② `python:3.11-slim` → `UOFA_BUNDLE_JAR=1 pip wheel .` (existing `hatch_build.py` hook bundles the JAR + force-includes `packs/` and `specs/` into the wheel — the surrogate pack and SIP schema travel with it); ③ runtime `python:3.11-slim-bookworm` → `apt-get install openjdk-17-jre-headless` (system `java`, the `paths.java_executable()` fallback) → `pip install uofa[interrogate,extract]` → **bundle Ollama + the ship-target stock model `qwen2.5:7b`** (SLM spec §4 — top of the small band; **the appliance baseline and the gate model must be the same artifact**, so bundle the size you would actually ship, not 3–4B; reuse `build-config/ollama_manifest.toml` for the pinned Ollama binary; `ollama pull qwen2.5:7b` baked as an image layer — the ~5 GB layer is the accepted cost of a self-contained, air-gap-faithful appliance) → COPY `uofa.toml` + `run-demo.sh`.
- **Model serving = a config line**: baked `docker/appliance/uofa.toml` sets `[llm] backend=ollama, model=qwen2.5:7b, base_url=http://127.0.0.1:11434` (in-container Ollama). `llm/config.py` → `get_backend()` threads `base_url` through with **zero code change**. Entrypoint starts the Ollama server in the background, then runs the CLI.
- **Default-activate the pack** via `--pack surrogate` in `run-demo.sh`/entrypoint. (Note: `cli.py:127` reads `args.pack`, **not** `uofa.toml [project] pack` — `--pack` is the reliable lever; an optional `UOFA_PACK` env hook is a 1-line `cli.py` add if wanted.)
- **Omit** `[interrogate-corpus]` (airfrans/torch/sklearn) from the appliance — those belong in the signal-source container.

### The two-container demo + the SIP-interface adapter (real PhysicsNeMo-CFD)
- **Files (new)**: `docker-compose.yml` (root), `docker/physicsnemo/Dockerfile`, `examples/sip_adapters/physicsnemo_adapter.py`, `examples/sip_adapters/physicsnemo_reference.py`.
- **The adapter splits across two interfaces** (verified against what each measurement reads from `MeasurementContext` in `interrogate/measurements.py`) — **not** a `MeasurementMethod` (that seam is reserved for premium *measurements*):
  - `physicsnemo_adapter.py` subclasses `interrogate.adapter.ModelAdapter`; `predict(inputs)` HTTP-calls the PhysicsNeMo container's inference endpoint → `{qoi: predictions}` (feeds `referenceResiduals`). A thin HTTP client — **no torch/checkpoints in the appliance image**.
  - `physicsnemo_reference.py` subclasses `interrogate.reference_source.ReferenceSource` (serve-only, `supports_generate()→False`): `reference()` = truth QoIs, `constraint_fields()` = PhysicsNeMo residual fields (→ `physicsConstraintResidual`), `uq_intervals()` = ensemble-variance bounds (→ `uqCalibration`). Mirrors `FileReferenceSource` but live-sourced.
  - Both resolved by `--adapter path.py:Class` / `--reference path.py:Class` (`load_adapter`/`load_reference_source` already accept this form). Geometry-OOD enters as the declared `--scope` evaluation-point/envelope, as today.
- **Compose**: `physicsnemo` (real PhysicsNeMo-CFD inference server, Apache 2.0, checkpoints via volume/build — **never** in the appliance) + `appliance` (`depends_on: physicsnemo`, healthchecked; `run-demo.sh` sets `PHYSICSNEMO_URL=http://physicsnemo:8000`). `docker compose up` shows **signals-in → explained-signed-evidence-out**.
- **Demo chain** (`run-demo.sh`, mirroring `harness/run_corpus.py` + an explain step): `interrogate init --yes` → `interrogate --adapter …physicsnemo… --reference …physicsnemo… --scope … -o bundle.json --key …` (signed bundle + `render_comparison`) → `read_sip_bundle` → write COU → `uofa rules cou.jsonld --pack surrogate --explain` (firings + Qwen explanations).
- **Wiring note**: `--explain` is wired on `uofa rules` (`rules.py:_run_explain`) — use that for the demo (**zero new code**). A `--explain` branch on `check.py` (≈30 lines reusing `interpret_check_output`) is optional, not required.
- **Risks to flag**: PhysicsNeMo base images are large and may need NGC access — decide checkpoint source (a small pretrained airfoil checkpoint keeps it portable); keep the `ReferenceSource` **serve-only** (precomputed truth) so the demo never crosses into the un-built `generate` path.

### Phase A acceptance
A clean-machine engineer runs `docker compose up`, the demo completes signals-in→explained-signed-evidence-out, and `interrogate` runs non-interactively against a surrogate+benchmark+reference to a signed, explained, verdict-free report — understood as trust-calibration evidence, from the README alone, in under an hour.

---

## Gate — Run the bakeoff (stock-local floor test; minimal answer-keyed slice, built now)

The concept appliance *is* the stock-model baseline (stock Qwen + catalog/measures/standard-text in context). Run the bakeoff as the cheap kill before any **moat** work. This gate **adapts** the SLM spec's §3.2 scorecard and §8 kill criteria; it is **not** a verbatim re-run of SLM-spec P0 (see below).

**What this gate is / isn't — a conscious choice, not a silent one.** SLM-spec P0 is *frontier-with-full-context*, and the non-inferiority story ("matches frontier, wins on cost + air-gap") needs a frontier number. **This gate deliberately does not run frontier.** It tests the **stock-local floor against absolute bars** — does the model the regulated buyer can actually self-host clear the dangerous-error and selective-coverage bars at α — which is the more relevant question for an air-gapped context where frontier is unavailable anyway. The **frontier non-inferiority comparison is deferred to the post-gate SLM P5 bakeoff** and is out of scope here. Do not read a non-inferiority number into this gate's output; it does not produce one.

**Gate model = the size you would actually ship (resolve before running — this is the wrong-verdict risk).** The appliance bundles **Qwen 2.5 7B** (SLM spec §4 ship target; the server removes the hardware ceiling, so 7–8B, not 3–4B; 3B is held only for desktop-only enclaves). The gate must run against the **ship size**, because the verdict is model-size-dependent and the failure mode is **asymmetric**:
  - **Pass at the tested size → conclusive kill.** Cheap, done; the appliance ships as a stock-model product on the convention + deployment moat.
  - **Fail at a smaller size → NOT yet fine-tune-justified.** You do not know whether 7–8B would clear the bars. The ladder is **small-fail → escalate to stock 7–8B → only if 7–8B *also* fails is the corpus build justified.** Never jump small-fail → fine-tune; that risks committing to a corpus build a larger stock model would have made unnecessary.

- **Files (new)**: `harness/bakeoff/corpus/*.json` (the slice), `harness/bakeoff/run_p0.py` (runner), `harness/bakeoff/score.py` (scorecard), `tests/bakeoff/`.
- **The corpus slice (the real cost)**: hand-curate a small **answer-keyed, D-category-stratified** set (strata = D-category × measure-type × domain × fire/suppress, **not** pattern ID — SLM spec §5), seeded from the AirfRANS case studies (`packs/surrogate/examples/airfrans/{cou1,cou2}`) plus a few hand-built cells, including **controls** (clean packages that must *not* fire) and the worked dangerous-OK pattern (SLM spec §5A). Each row carries the four-field key: correct mechanism, gold action (D-category-keyed vocabulary, §5B), forbidden-claims list, acceptable-confidence range. Label provenance external to the tool and to the teacher (SLM spec §5 tautology guards). **Build the dangerous-OK §5A + multi-coherent §5B cells adjudication-ready** — those hard cells double as the seed of the **disposition slice** (addendum) if the explanation gate returns commodity, where `gold_action` also carries `coherent_alternatives` + `selection_basis: adjudicated`.
- **The runner (mostly reuse)** — `run_p0.py`: for each row build the retrieval prompt (flag + measures + catalog def + standard text + few-shot) and generate the explanation via the existing `interpretation/` machinery over the Ollama/Qwen backend (`llm/litellm_backend.py`). The runner is thin.
- **The scorecard (new logic)** — `score.py`: apply each row's key → mechanism/action buckets (correct/partial/wrong/**harmful**), forbidden-claim violations (binary gate), grounding/hallucination, calibration (ECE + selective curve), and the **headline selective risk-coverage** at α (start 2%). **Pin confidence elicitation to verbalized confidence** — the model's structured output already carries a `confidence` field (SLM spec §5A) mapped to the acceptable-confidence ranges; record the method in `score.py` so the selective curve is reproducible. (Cross-model elicitation-matching, SLM spec §3.2, only bites at the later frontier P5; for this single-model gate, fixing verbalized is sufficient.) **Design `score.py` re-pointable** from the explanation output to the **disposition** output (selected §5B action class + params + confidence) — the disposition gate (below) reuses this exact machinery. **Always segment by the hard-core strata**, never just the aggregate.
- **Why the headline metric is right (affirm, don't lose this)**: selective risk-coverage catches the degenerate pass — a model that clears the dangerous-error bar only by **abstaining constantly** scores high safety but **low coverage = low value**, so "abstains on everything" cannot masquerade as a passing grade.
- **If stock clears the explanation bars — do NOT kill the SLM leg** (disposition-gate addendum, `docs/UofA_PostRefactor_Gate_Addendum_DispositionGate.md`). Explanation is then *commodity*, but **disposition under uncertainty** — which coherent §5B action is right for this COU + scoping + calibrated confidence — is untested, and that is where the moat actually lives. Move the gate **up one level**: build a small **expert-adjudicated** hard-cell **disposition slice** (dangerous-OK §5A + multi-coherent §5B + accept-controls), re-point `score.py` at the disposition output (action correctness incl. **harmful**, selection quality on multi-coherent rows, selective risk-coverage), run the same stock-vs-target bakeoff, and read it **on the hard-core strata**. Stock clears disposition too → SLM leg genuinely dead (convention + deployment moat only); stock fails disposition → corpus build justified *by evidence*, that slice is its seed (build to the **disposition** task, not explanation). The disposition answer keys **cannot** be cheaply grounded (expert adjudication / Tier-3 only) — that irreducibility *is* the moat. Auto-act stays parked regardless (its own Tier-3 dependency).
- **Guard against the false-positive kill**: an aggregate pass that masks hard-cell failure means the **slice is too easy** (rebuild the hard cells, rerun), not that the task is commodity. Read every gate on the hard-core strata.
- **Acceptance**: a scorecard exists for every metric component on the stratified slice **at the ship-size model**, **segmented by hard-core strata**, the selective risk-coverage result is recorded, and the gate verdict is written down with the numbers — one of **kill** (explanation+disposition commodity) / **escalate-to-7–8B** / **run-disposition-gate** (explanation commodity, disposition untested) / **corpus-justified** (disposition fails).

---

## Phase B — The basic guardrail (rides on the §6 interface)

The interface + stub exist; build the **basic** logic. Scope discipline: engineer-commanded, mechanically-simple tier only — sophisticated guardrail and actual mitigation/fixing are **Product B, parked**.

**Not gated by the bakeoff.** B is **core Product A** (the spec's stated scope), blocked only by Phase A — **only the SLM/premium/MCP moat work waits behind the gate**. B is sequenced after the gate for narrative ordering and may safely overlap it; the gate verdict (kill/escalate/justify) does not block B.

- **B1 — real threshold + simple fixes**: replace `ThresholdGuardrailStub` in `src/uofa_cli/guardrail.py` with a real `ThresholdGuardrail` implementing `assess(firings, context) -> dict`: a threshold trigger (e.g. on severity/count over `attribute_firings(...)` firings) plus the small engineer-commanded action set (envelope-restriction refuse/clip — the mechanically-simple responses). Output is the `guardrailAction` block, signed in **action-region scope** via the existing `sign_guardrail_action()` (`interrogate/signing.py`). `build_guardrail_action()` already wires firings→assess; this swaps the stub for real logic.
- **Surface it**: expose via a `uofa guardrail` command (or a `--guardrail` flag on `check`) that calls `build_guardrail_action()`. No chaining into a verdict; the guardrail acts, it doesn't adjudicate credibility.
- **B2 — guardrail in the evaluator story**: the appliance demo shows the full shift-left loop — run surrogate → trust-calibration evidence → basic guardrail flags/acts when the surrogate is out of competence — closing the "with confidence" narrative inside the same container, with **no Product-B fixing logic exposed**.
- **Acceptance**: the guardrail consumes firings, emits a correctly action-scoped, signed output (verifies via `verify_scoped_block`), and the container demonstrates surrogate→evidence→guardrail end-to-end.

---

## Phase C — Daemonize the rule engine (usability, conditional)

`uofa check` cold-starts the JVM **3×** (derive `derivations/runner.py:118` → rules `rules.py:513` → oos `oos/runner.py:103`); no reuse. For a self-serve tool, repeated cold starts read as "slow."

- **Gated on measurement**: first measure the evaluator path (single case + a small multi-case run). If already fast enough, **defer**.
- **If it bites — cheapest win first**: add a single combined `pipeline` subcommand to the fat JAR (`src/weakener-engine/`) that runs derive→rules→oos in **one** JVM process, and call it from `commands/check.py` — turning 3 cold starts into 1 (reuse `paths.java_executable()`/`jar_path()`). A long-lived daemon/socket server is the heavier option, natural in appliance mode (persistent runtime), only if batch throughput demands it.
- **Acceptance**: the evaluator path completes without latency that reads as slow; the per-check cold-start multiplier is gone.

---

## Phase D — Real canonicalization (decide, likely park)

The honesty relabel already happened in the refactor (RDFC-1.0 told to the truth). The open question is *capability*, not honesty: does the "independently machine-verifiable across tools" claim need to be load-bearing for Product A's shift-left buyer?

- **Decide**: for the engineer-confidence buyer, honestly-labeled sorted-key JSON (in `integrity.py`) is likely sufficient. Real JCS/RDF canonicalization is upside for a future submission-grade / cross-org-verification use. **Flag, decide, probably park** — defer the build unless the cross-tool claim must be load-bearing.

---

## Sequencing

1. **Phase 0** — land the P2d refactor tail (clean active-pack API).
2. **Phase A** — appliance container + A1–A4 + two-container demo. *Do first; the core deliverable.*
3. **Gate** — build the minimal answer-keyed slice + runner/scorecard; run it against the **ship-size (7B)** model; record the verdict. *Blocks the SLM/premium/MCP moat work only.*
4. **Phase B** — basic guardrail; close the "with confidence" loop in the appliance. *Core Product A — not gated by the bakeoff; may overlap the Gate.*
5. **Phase C** — daemonize, only if measured evaluator latency bothers.
6. **Phase D** — decide canonicalization, likely park.

A + B bring Product A to life as a container an evaluator brings up in an afternoon; the gate sits between A and any moat work; C is conditional usability; D is a deferred capability call.

---

## Effort (rough, paired-throughput sized)

Hours assume Claude Code pairing on **implementation** rows (the 3–5× throughput is already applied). **Curation / decision / adjudication** rows do **not** take the acceleration (SLM spec §7 discipline). Container / PhysicsNeMo rows carry build-and-iterate wall-clock that pairing doesn't compress. The reuse surface means most of Phase A is hours, not days.

| Phase | Work | Accelerates? | Est. hours |
|---|---|---|---|
| 0 | Land the in-flight P2d threading; full suite green; merge | partial | 4–8 |
| A1 | README SIP on-ramp | no (writing) | 3–5 |
| A2 | Non-interactive `init --yes` (reuse `init_wizard`) | yes | 4–8 |
| A3 | Report `reference-annotation` label + README framing | partial | 2–3 |
| A4 | Appliance `Dockerfile` + bundle 7B + entrypoint/Makefile | yes (+ build wall-clock) | 16–24 |
| A-demo | Two-container compose + SIP adapters (**real PhysicsNeMo** is the wildcard) | adapters yes; PhysicsNeMo container no | 16–30 |
| **A total** | | | **~45–70** |
| Gate-corpus | Hand-curate the answer-keyed stratified slice + grounding | **no (the bulk; does not accelerate)** | 20–40 |
| Gate-run | `run_p0.py` (reuse) + `score.py` (new metric) + run/escalate/writeup | mostly yes | 16–28 |
| **Gate total** | | | **~36–68** (curation-dominated) |
| B1 | Real `ThresholdGuardrail` + simple engineer-commanded fixes | yes | 10–16 |
| B2 | Wire the guardrail into the appliance demo loop | yes | 4–8 |
| **B total** | | | **~14–24** |
| C | Combined single-JVM `pipeline` subcommand (daemon variant 30h+) — *conditional* | yes | 12–20 |
| D | Canonicalization decision (no build) | no (decision) | 2–4 |

---

## Scope boundary — NOT in this plan (gated or Product B)

Behind the bakeoff gate (start only if the gate says the trained model earns its keep): the **explainer-SLM corpus build + fine-tune** (`UofA_Explainer_SLM…` spec), **premium measurements** (Wasserstein/density/sparse-tail packs on the §3 interface), the **MCP interface** beyond a read-and-attest stub (`Appliance` spec §6A). Product B, parked regardless: sophisticated guardrail + actual mitigation/fixing, generating-`ReferenceSource` internals (VTK/OpenFOAM solver-ingest), the verified-outcome label + mitigation loop + DVC, the expert-calibration moat study.

---

## Verification (end-to-end)

1. **Build + demo**: `make appliance-image`; `docker compose up` → the two-container demo runs PhysicsNeMo signals → SIP adapter/reference → signed verdict-free bundle → surrogate-pack check → Qwen explanations, with no PhysicsNeMo weights in the appliance image.
2. **Non-interactive on-ramp**: `uofa interrogate init --yes --scope … --benchmark …` succeeds in a non-TTY (the smoke test runs; provenance tagged); follow with `uofa interrogate …` to a signed bundle; `uofa verify` it.
3. **README**: a fresh reader follows the new `## Interrogate a Surrogate (SIP)` section and reaches a working explained report from the committed `examples/airfrans/cou1` fixture.
4. **Bakeoff**: `python -m harness.bakeoff.run_p0` over `harness/bakeoff/corpus/` → a §3.2 scorecard + selective risk-coverage curve; the kill/justify verdict is recorded.
5. **Guardrail**: `uofa guardrail` (or `check --guardrail`) over firings → a signed, action-scoped `guardrailAction`; `verify_scoped_block` passes; no decision token leaks (firewall guard green).
6. **Tests**: new `tests/` for non-interactive init, the guardrail logic, the bakeoff scorer, and the two SIP adapters; full suite green with `[interrogate]` installed.
