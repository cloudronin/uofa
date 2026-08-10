# Addendum v0.4: A13 — live furnished runs and private cards

**Applies to:** model-credibility-pack-spec.md + addenda v0.1–v0.3 + impl plan
**Status:** design spec. Numbering continues from v0.3. Decision recorded: live
run orchestration is an **open capability** of the UofA CLI, covering
arbitrary models including privately hosted fine-tunes, with local/internal
card output as a first-class outcome. The open-core boundary is drawn below
(A13.6): single-shot assessment is open; continuous gating and optimization
remain raitune.

---

## A13.1 Capability

```
uofa report <model-ref> --pack model-credibility --raidex-run [--card]
```

where `<model-ref>` is any model raidex's backends can evaluate: an HF hub id,
a local path to a fine-tuned checkpoint, or an OpenAI-compatible endpoint
(vLLM, Ollama, hosted API). One command: raidex evaluates, UofA ingests,
assesses, signs, and renders the card.

The user-facing meaning: the card pipeline is no longer limited to models
whose evidence someone already published. A team that fine-tuned a model
yesterday gets a signed credibility card today, including the sufficiency
findings on their own fresh benchmark evidence, before the model informs a
decision.

## A13.2 Architecture: orchestration, not absorption

UofA does not implement evaluation. It shells out to `raidex eval` as a
subprocess, then ingests the output through the Phase 2 adapter unchanged.

```
uofa --raidex-run
  → preflight (A13.4)
  → subprocess: raidex eval <model-ref> --out <tmp>/results.json
  → Phase 2 adapter ingests results.json (same code path as --raidex <path>)
  → Group B assessment, bundle, card
```

- **Furnisher/assessor firewall holds:** raidex produces the numbers, the pack
  judges their sufficiency. A live run is not a sufficiency upgrade — a
  freshly furnished score with no null baseline still trips W-EV-NULL-04.
  Live-run evidence gets no severity discount anywhere.
- raidex is an **optional dependency** (`pip install uofa[raidex]`). Absent →
  `--raidex-run` fails with the install hint; `--raidex <path>` /
  `--raidex-hub` keep working. Core UofA stays dependency-light.
- Version capture: the raidex package version and backend_version are stamped
  into the bundle (`furnisherVersion`), because a live run's reproducibility
  claim is bounded by the furnisher version that produced it.
- No raidex flags are re-exposed through UofA beyond model-ref and endpoint
  config. Backend selection, judge config, and constituent selection are
  raidex's CLI surface; `--raidex-args "<passthrough>"` covers the rest.
  UofA re-wrapping raidex's interface is a maintenance treadmill and blurs
  the furnisher boundary.

## A13.3 Provenance: `furnished-run`

New provenance class alongside `extracted` / `run-context` / `derived` /
`defaulted`:

- `furnished-run` — evidence produced by a furnisher invocation during this
  assessment. Carries `furnisherVersion`, invocation timestamp, and the
  content hash of the raw furnisher output (the results.json), which is
  retained in the bundle's evidence store.
- Published-dataset lookups (`--raidex-hub`) remain `extracted` with their
  A9.1 source pin. The class distinction is load-bearing: a reader of the
  card can tell whether section [3] evidence was independently published
  before the assessment or generated within it. Both are legitimate; they
  are different claims.
- The card's section [3] header states which: "furnished by raidex vX.Y
  (live run, <date>)" vs "(published dataset, <version>)".

## A13.4 Cost honesty (preflight)

A full constituent sweep on a large model is hours of GPU and real judge
spend. The command must not discover this for the user mid-run.

- Preflight prints the constituent list, the backend/judge configuration, and
  a rough cost/time statement, then requires confirmation (`--yes` to skip
  for CI).
- Partial sweeps are permitted and honest: `rai_coverage` already expresses
  them (8/9 exists in the published dataset). A partial live run produces a
  card whose coverage says so; it does not produce an error and does not
  produce silent gaps.

## A13.5 Private and internal cards

For fine-tuned and privately hosted models, local output is the primary
outcome, not a degraded mode:

- `--raidex-run --card` on a local checkpoint emits bundle + card.json +
  card.html to the output directory. **Nothing leaves the machine.** No
  telemetry, no phone-home, no uofa.net interaction. The signed bundle is
  the enterprise's internal artifact of record; `uofa verify` works offline.
- Model-ref for local models enters the bundle as given (path or internal
  name). `sourcePin` for a local model pins the checkpoint: config hash plus
  weight-manifest hash where cheaply available, else path + fetch date +
  user-stated identifier. INVESTIGATION ITEM (execution agent): what
  checkpoint identity raidex already captures for local models; reuse rather
  than reinvent.
- Internal publication is the enterprise's own concern by design: the card
  is static HTML and the bundle is a file; an internal registry page, a
  SharePoint folder, and an S3 bucket are all equally valid card stores, and
  CI-gating on `uofa verify` works in any of them. UofA ships no internal-
  portal software and takes on no hosting or support obligation for private
  deployments.
- Badges (A12) are a uofa.net publication feature and do not apply to
  private cards. An internal card carries the verify footer instead; that is
  the equivalent trust surface for an internal audience.
- **AIMS framing, recorded for the docs:** a private card over a fine-tune is
  exactly the model-selection and model-change evidence an ISO 42001 AIMS
  audit asks for. The docs page for this capability should say so plainly —
  it is the answer to "what evidence supported this model decision" that
  currently defaults to a leaderboard screenshot.

## A13.6 Open-core boundary (decision recorded)

- **Open (UofA CLI):** single-shot assessment of any model, live furnished
  runs included, private cards included, no feature gating on model
  provenance (lab-built, fine-tuned, local, hosted — all equal).
- **raitune (paid):** continuous CI/CD gating, assessment-over-time, the
  optimizer loop (Measure→Improve→Optimize), and fleet-level views. raitune
  Measure consumes and emits the same UofA-shaped records this command
  produces; the open command seeds the artifact format the paid product
  operates on.
- The line, stated once for the README: *UofA answers "is this model's
  evidence sufficient, today"; raitune answers "keep it sufficient, and make
  it better."* No open-CLI feature will be withdrawn to sharpen this line.

## A13.7 Firewall and scope constraints

1. All A5 / A11 / A12.5 constraints unchanged. No composite score on live-run
   cards; the scope sentence renders on private cards identically.
2. Live-run evidence is section [3] evidence. It never populates Group A —
   running benchmarks does not document a model, and a no-card fine-tune gets
   the honest no-card readout in [1] next to a fully populated [3]. The
   firewall test suite gains exactly this fixture: local model, live run,
   no card.
3. A live run against a model whose card also reports scores feeds
   W-EV-DIV-07 the same as dataset evidence — the reported-vs-furnished
   comparison does not care how the furnished side was obtained.
4. `--raidex-run` and `--raidex-hub` are mutually exclusive per invocation.
   One card, one furnished-evidence source, one provenance story.

## A13.8 Phasing

Extends impl-plan Phase 2 (adapter exists; this adds the orchestration front
end) with the preflight and provenance class landing alongside. Local-model
sourcePin work joins Phase 6. No new phase gates; the demand-gated Phase B
and all publication machinery are unaffected because private cards never
touch them.
