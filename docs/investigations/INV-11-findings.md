# INV-11 — Injection harness CLI exposure (feeds B2)

Status: **ESCALATED — recommendation upgraded from "worth it" to "required" by
parent spec v2.0**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent B2, A2, A1, D4, and **GATE-H3**

---

# ADDENDUM — re-investigated against parent spec v2.0

## The wrap-vs-build decision is no longer a judgement call

The original finding put two options to the author: wrap the LLM generator (~2h,
approximate) or build a deterministic mutator (4-6h, literal). v2.0 makes the
second one the only route to a gate the spec itself sets.

**GATE-H3 (§0.1) requires MECHANICAL-class detection ≥95%.** Aggregating the
committed per-pattern outcomes by INV-1's partition gives MECHANICAL recall of
**0.5908** at M5 (v0.5.7) and **0.7260** at the v0.5.13 holdout. The shortfall is
not distributed — it is five patterns scoring exactly 0.000 plus two that have
never produced a single confirm-existing row:

| Pattern | Class | Recall | Why the generator cannot produce the flaw |
|---|---|---|---|
| W-EP-03 | MECH | 0.000 | needs `dataVintage < modelRevisionDate` as two comparably-typed literals; Jena's `lessThan` fails silently on a mistyped one |
| W-CON-03 | MECH | 0.000 | same, `greaterThan` on two timestamps |
| W-AR-04 | MECH | 0.000 | needs two `modelVersion` strings that differ; the generator writes them consistently |
| W-SI-02 | MECH | 0.000 at v0.5.7 | fires on absent `bindsRequirement` / `hasValidationResult`, both ProfileMinimal-mandatory — **SHACL rejects the flawed package during generation and the retry loop removes the flaw** |
| W-AL-02 | MECH | 0.000 at v0.5.7 | rule defect, fixed at v0.5.9 |
| W-ON-01 | MECH | not_measurable | zero CE rows at every version |
| W-SI-01 | MECH | not_measurable | zero CE rows at every version |

**Every one of these is a defect the §4b mutator produces in a single line.**
Delete `hasContextOfUse` → W-ON-01 fires. Strip `signature` → W-SI-01 fires. Write
a correctly-typed `dataVintage` one day earlier → W-EP-03 fires. Delete
`bindsRequirement` → W-SI-02 fires, and whether the result is re-validated is a
choice the mutator makes rather than a gate that erases the test.

So the position is: **GATE-H3's MECHANICAL clause is unreachable with the LLM
generator and reachable by construction with the mutator.** The 4-6h is not a
quality improvement to B2; it is the enabling instrument for rank-1 and rank-2 work
in v2.0's own priority ordering.

## Two more v2.0 clauses that point the same way

**A2 §3's null-control standard** — *"every headline metric reported beside a null
that a non-reading system would achieve"* — is easy to satisfy for deterministic
injection (recall beside FP from one run at one catalog version) and awkward for
generated injection, where recall and specificity were measured at different
versions on different corpora. See INV-8's addendum §"version-mismatch".

**D4 §4's escort sentence** is now fixed text: *"constructed ground truth via defect
injection into published-case substrate, following the fault-injection and
mutation-testing tradition."* Two clauses of that sentence are already true of the
harness — the substrate genuinely is published-case (skeleton mode reads
`packs/vv40/examples/{morrison,nagaraja}/`), and the ground truth genuinely is
constructed from a declared target. **"Defect injection … following the
fault-injection and mutation-testing tradition" is the clause that a reader from
that literature will read as deterministic seeding**, and today it is not. The
mutator makes the sentence literally true; without it, D4's escort and A2's mapping
table both need a hedge, and U-INV-1's citations get harder to defend. One 4-6h
build closes all three.

## Revised recommendation

**Build the mutator, and schedule it before P25-A.** Sequencing:

| Step | Work | Cost |
|---|---|---|
| 1 | `uofa inject` deterministic mutator over the 15 MECHANICAL patterns (§4b) | 4-6h |
| 2 | `uofa detect` alias with manifest comparison (§4a) | 1h |
| 3 | README walkthrough (§4d) — B2's done-gate | inside B2's 2-3h |
| 4 | **P25-A full-battery holdout at v0.5.15.1**, with MECHANICAL-class recall measured on deterministically injected flaws | 3-5h + ~$50 |

Steps 1-3 are B2 and cost 5-7h against v2.0's 2-3h estimate — **that is the one
budget correction this item asks for.** Step 4 is a Phase 2.5 item that was already
scoped and costed in `PHASE2_5_STATUS_REPORT.md:46-48`; it is listed here only
because the ordering matters.

One design note that becomes load-bearing under this plan: §4b item 4 flagged the
re-sign decision as something to take deliberately. It now has a second reason.
If injected packages are re-signed with a demo key, W-SI-01's injection must be the
deliberate exception; if they are left unsigned, **every** injected package fires
W-SI-01 and the MECHANICAL-class recall figure is contaminated by a pattern firing
for the wrong reason. Re-sign, with W-SI-01 injected by stripping the signature
after re-signing.

## Escalation (revised)

Unchanged in substance, sharper in stakes: **B2 as v2.0 writes it ("wrap, don't
rewrite", 2-3h) does not produce the instrument GATE-H3 needs.** The author should
either fund the mutator at 5-7h for B2, or accept that MECHANICAL-class detection
cannot be measured above ~0.73 and revise GATE-H3's ≥95% clause **before** P25-A
runs rather than after.

## Coverage statement (addendum)

**Searched.** v2.0 §0.1 GATE-H3, §A2 clauses 1-4, §B2, §D4 clauses 1 and 4, §A5's
null-control row. Three committed per-pattern `summary.csv` artifacts parsed and
aggregated by INV-1's partition (see INV-8's addendum for the method and the
correction to my earlier claim that these were gitignored — they are force-tracked
by `.gitignore:41-43`).

**NOT verified.** The mutator was not built and no injection was performed. The
literal-typing explanation for the three value-comparison zeros is **HYPOTHESIS**
— consistent with the rule bodies and with which patterns fail, but no failing
generated package was opened to confirm the datatype. Opening two or three
`…confirm_existing/…w-ep-03…` packages would settle it in ~15 minutes and should
precede writing the mutation table.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Headline

The **detect** side is fully exposed, deterministic, and runs on a fresh `pip
install` with no Java and no network. The **inject** side is not an injector: it is
an LLM package generator driven by spec YAMLs, and it needs an API key, costs
money, and produces a different package every run.

So B2 splits cleanly:

| Half | Today | To reach B2 |
|---|---|---|
| `uofa detect` | `uofa rules` / `uofa check` already do exactly this | rename/alias + a manifest-aware comparison line. **~1h** |
| `uofa inject` | `uofa adversarial generate --spec <yaml>` — LLM, keyed, non-deterministic | either (a) wrap the LLM path honestly, **~2h**, or (b) write a small **deterministic mutator**, **~4-6h**, which is what the professors' sentence actually describes |

**Recommendation: build (b).** It is the difference between a demo that shows the
prescribed test and one that approximates it, and it is a few hours. Details in §4.

## 1. Exposure map

| Component | Where | Invocation surface |
|---|---|---|
| Phase 2 generator | [src/uofa_cli/adversarial/generator.py](src/uofa_cli/adversarial/generator.py) (864 lines) | **CLI** — `uofa adversarial generate --spec <yaml> --out <dir>` ([commands/adversarial.py:18-46](src/uofa_cli/commands/adversarial.py)) |
| Batch orchestration | `adversarial/runner.py` | **CLI** — `uofa adversarial run --batch <dir> --out <dir>` |
| Skeleton mode (identity + factor scaffold from a base COU) | [src/uofa_cli/adversarial/skeleton.py](src/uofa_cli/adversarial/skeleton.py) (416 lines) | **library only** — selected by `package_context.mode: skeleton` in the spec YAML |
| The 23 injection classes | `dev/specs/confirm_existing/*.yaml` (23 files, one per pattern) | **data**, consumed by `generate` |
| Manifest writer | `runner.py` → per-spec `manifest.json` + roll-up `batch_manifest.json` ([runner.py:6-39](src/uofa_cli/adversarial/runner.py)) | automatic side effect of `generate`/`run` |
| Outcome classifier (the detect-and-score half) | [src/uofa_cli/adversarial/classifier.py](src/uofa_cli/adversarial/classifier.py) | **CLI** — `uofa adversarial analyze` |
| Rule engine (the actual detection) | `uofa rules` → `run_structured()` | **CLI + typed API** |
| W-AR-05 skeleton-mode MVP | `dev/specs/confirm_existing/w-ar-05.yaml` + skeleton mode | data + library |

**Nothing is test-only.** Every piece is in the shipped package under
`src/uofa_cli/`, not under `tests/`. That is better than the parent spec assumed.

## 2. What one end-to-end run needs today

```bash
uofa adversarial generate \
    --spec dev/specs/confirm_existing/w-ar-05.yaml \
    --out dev/build/demo/
uofa adversarial analyze --manifest dev/build/demo/manifest.json ...
```

| Input | Value | Note |
|---|---|---|
| Clean package source | `packs/vv40/examples/morrison/cou1` — the `base_cou` in the spec YAML | **A shipped example package, not a test fixture.** The escalation the item anticipated does not apply; see §5. |
| Configuration | the spec YAML: `target.weakener`, `coverage_intent`, `pack`, `package_context` (base_cou, mode, factors, decision, mrl), `generation` (model, n_variants, subtlety, max_tokens) | |
| **LLM backend** | `generation.model: claude-sonnet-4-6`, dispatched through litellm / ollama / mock ([generator.py:517-540](src/uofa_cli/adversarial/generator.py)) | **The hard dependency.** `--dry-run` renders prompts without calling the model. |
| Outputs | corrupted package(s) + per-spec `manifest.json` (spec id, spec hash, target weakener, model, token counts) | |
| Detect side | `uofa rules --pack vv40 <package>`, invoked by the classifier as a subprocess ([classifier.py:206-211](src/uofa_cli/adversarial/classifier.py)) | deterministic |

## 3. The finding that shapes B2

The professors' sentence — *"starts with a perfect evidence package and
systematically injects known flaws"* — describes deterministic mutation. The
harness does something adjacent but distinct:

> declare the target weakener in a YAML → ask an LLM to author a package
> exhibiting it → run the rule engine → classify the outcome mechanically.

The **label** is manifest-derived (see INV-8 §2: `_classify` takes the declared
target and the observed firings, nothing else). The **stimulus** is model-authored.
Consequences for a live demo:

- **Not reproducible run-to-run.** A committee member running it twice gets two
  different packages and possibly two different outcome classes.
- **Costs money and needs a key.** The M5 batch cost $386.49 (manuscript ¶450).
- **Can fail to inject.** `GEN-INVALID` was 8.3% overall — the model sometimes
  produces a SHACL-invalid package. A demo that fails one run in twelve, live, in
  front of a committee, is worse than no demo.
- **The clean-in / flawed-out contrast is not visible.** Skeleton mode generates a
  fresh standalone package rather than a delta against the base, which the
  classifier docstring states outright: *"each synthetic package is a fresh
  standalone generation, not a delta against the underlying base COU"*
  ([classifier.py:33-38](src/uofa_cli/adversarial/classifier.py)). So there is no
  before/after diff to show — which is the single most persuasive thing the demo
  could show.

## 4. Wrap sketch

### 4a. `uofa detect` — pure plumbing (~1h)

```bash
uofa detect <package.jsonld> --pack vv40 [--manifest <manifest.json>]
```

Composes `commands.rules.run_structured` (already typed). With `--manifest`, add
one comparison line: *"expected W-AR-05 (from manifest) — DETECTED / MISSED",*
reusing `classifier._classify`. Both functions exist; this is argument plumbing
plus one print block.

### 4b. `uofa inject` — the recommendation: a deterministic mutator (~4-6h)

```bash
uofa inject --pattern W-AR-05 --package packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
            --out flawed.jsonld --manifest manifest.json
```

For the **15 MECHANICAL patterns of INV-1**, injection is a JSON edit, because the
rule bodies are presence/absence and value comparison:

| Pattern | Mutation |
|---|---|
| W-AR-05 | delete `comparedAgainst` from one validation result |
| W-AL-01 | delete `hasUncertaintyQuantification` from one result |
| W-EP-01 | delete `prov:wasDerivedFrom` from the claim |
| W-EP-02 | delete `prov:wasGeneratedBy` from one result |
| W-ON-01 | delete `hasContextOfUse` |
| W-ON-02 | delete both `hasApplicabilityConstraint` and `hasOperatingEnvelope` |
| W-SI-01 | strip `signature` |
| W-SI-02 | delete `bindsRequirement` (or `hasValidationResult`) |
| W-AR-04 | rewrite one `modelVersion` |
| W-CON-03 | push one `evidenceTimestamp` past `signatureTimestamp` |
| W-EP-03 | pull one `dataVintage` before `modelRevisionDate` |
| … | (the remaining MECHANICAL rows are the same shape) |

This maps **directly onto the professors' named examples** — remove uncertainty
(W-AL-01), change version numbers (W-AR-04), remove signatures (W-SI-01) — which is
exactly the mapping table A2 step 2 needs, and it becomes demonstrable rather than
asserted.

Manifest contents for the demo narrative:

```json
{"source_package": "…/uofa-morrison-cou1.jsonld",
 "source_hash": "sha256:…",
 "pattern": "W-AR-05",
 "mutation": {"op": "delete", "path": "$.hasValidationResult[0].comparedAgainst"},
 "expected_finding": {"patternId": "W-AR-05", "severity": "High"},
 "output_hash": "sha256:…"}
```

Hashes come free from `integrity.canonicalize_and_hash`. Deterministic, offline,
no key, no cost, byte-identical every run, and the before/after diff is one line.

Itemised plumbing beyond argument passing:
1. JSON-path delete/set helper (~30 lines).
2. Per-pattern mutation table for the 15 MECHANICAL patterns (~60 lines of data).
3. Manifest writer (~30 lines) — do **not** reuse `runner.py`'s manifest, whose
   schema is generation-oriented (`specHash`, token counts).
4. Re-sign or explicitly leave unsigned after mutation. **Decide this deliberately:**
   mutating a signed package invalidates its signature, so W-SI-01's injection is
   free but every *other* injection also breaks C1 unless re-signed. Cleanest is to
   re-sign with the demo key so the demo shows C3 detection on a C1-valid package,
   with W-SI-01 as the deliberate exception.
5. The 8 JUDGMENT/ambiguous patterns cannot be injected this way; `--pattern` should
   reject them with a message pointing at `uofa adversarial generate`. That
   restriction is itself an A1 talking point.

### 4c. Keep the LLM path, renamed honestly

`uofa adversarial generate` stays as the research apparatus. B2's README walkthrough
uses `uofa inject`; Ch3 describes both and says which produced which numbers.

### 4d. README walkthrough

```bash
pip install uofa
uofa demo                       # bundled fixture, full C1+C2+C3, no network
uofa check clean.jsonld         # 0 findings
uofa inject --pattern W-AL-01 --package clean.jsonld --out flawed.jsonld --manifest m.json
uofa detect flawed.jsonld --manifest m.json    # W-AL-01 DETECTED — matches manifest
```

Five commands, offline, deterministic. That is the committee-runnable artifact.

## 5. Fresh-clone runnability

Better than the parent spec feared. From [README.md:10-23,144,158-161,561-569](README.md):

| Requirement | Reality |
|---|---|
| Install | `pip install uofa` — one command |
| Java / Maven for Jena | **Not needed.** The wheel bundles the rule-engine JAR **and an OpenJDK 17 JRE**. Exception: Intel macOS, where the bundled JRE does not ship, and source-tree dev outside the wheel. |
| Network | Not needed for detect. `uofa demo` runs the full C1+C2+C3 pipeline against a bundled fixture with "no Java install, no LLM runtime, no internet." |
| LLM key | Needed **only** for `uofa adversarial generate` / `uofa extract`, not for detection |
| Extras | `pip install 'uofa[extract]'` for the extraction path only |

**Verdict: `uofa detect` is genuinely committee-runnable today.** With the §4b
deterministic injector, the whole inject-and-detect loop becomes so — no key, no
cost, no cold start. **No fallback (recorded terminal session / hosted variant) is
needed.** Flag one line in the walkthrough for Intel-macOS users, who need a
system Java 17.

## 6. Escalation

The item's stated escalation was *"the harness's clean-package inputs are
themselves test-only fixtures unsuitable for a public demo."* **Not triggered** —
the base COUs are shipped example packages under
`packs/vv40/examples/{morrison,nagaraja}/`, published as part of the pack, with
their source documents alongside in `packs/vv40/examples/morrison/source/`.

**A different escalation is raised instead**, because it changes what B2 is:

> B2 as written ("expose the existing harness") delivers a demo whose injection
> step is an LLM call: non-deterministic, keyed, billable, ~8% failure rate, and
> with no visible clean→flawed delta. That is not what must-have 1 describes and it
> is weaker in exactly the dimension the committee cares about. Building a small
> deterministic mutator over the 15 MECHANICAL patterns costs a few hours more and
> delivers the prescribed test literally.

Author decision: **wrap (2h, approximate) or build (4-6h, literal)?** The B2
done-gate — "B2's implementation is fully specified by this memo" — is met for the
wrap path either way; §4b specifies the build path to the same level.

## Coverage statement

**Searched.** `src/uofa_cli/adversarial/` full tree (14 modules + `judge/` 20 +
`prompts/` 14). `commands/adversarial.py:1-120` (the argparse surface, subcommands
`generate|run|analyze|prep-review|bundle|judge|triage|adjudicate`). `skeleton.py:1-95`
and its NC-stub helpers. `classifier.py` docstring, `_run_rules`, `_classify`,
`_CORE_PATTERN_IDS`. `runner.py` manifest schema. `generator.py` grepped for
`def generate`, `llm`, `provider`, `api_key`, `dry_run`, and its LLM dispatch read.
`dev/specs/` census (7 directories, 113 specs) plus two YAMLs read in full
(`confirm_existing/w-ep-01.yaml`, `negative_controls/nc-clean-compound-free.yaml`).
`README.md` grepped for `Java`, `JRE`, `jena`, `pip install`, `uofa setup`.
`cli.py` command registry (24 subcommands; **`uofa inject` and `uofa detect` do not
exist** — verified by repo-wide grep).

**Search terms derived from the question's own definition** (injection = a known
flaw placed into a known-good package, with a record of what was placed):
`inject`, `mutate`, `mutation`, `corrupt`, `seed`, `manifest`, `base_cou`,
`target.weakener`, `skeleton` — rather than searching only for the Phase 2 names.

**NOT searched / not verified.**
- **No command was executed.** `uofa adversarial generate --dry-run` was not run,
  so the prompt-rendering path is described from source. Effort estimates are
  read-derived.
- The JSON structure of a real generated package was not inspected, so §4b's
  JSON-path expressions are illustrative; the mutation table must be written against
  an actual `uofa-morrison-cou1.jsonld` (~30 min).
- `uofa demo`'s bundled fixture was not run to confirm the "no internet" claim; it
  is quoted from README. Worth one verification run before it appears in a
  committee-facing walkthrough.
- Intel-macOS JRE behaviour is quoted from README, not tested.
- Phase 2.5 refinement tooling (`dev/tools/phase2_5/`) was enumerated but not read;
  it refines rules rather than injecting flaws, so it is outside B2.
