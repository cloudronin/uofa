# AGENTS.md — Working in this repo

This file is for AI coding agents (Claude Code, Cursor, etc.) and human contributors
who want a fast brief on this codebase's discipline. It complements `CONTRIBUTING.md`
(which covers license, DCO, and release mechanics) by encoding the operational rules
the repo expects in day-to-day work.

If anything here conflicts with `CONTRIBUTING.md`, `CONTRIBUTING.md` wins on
license and process; this file wins on agent behavior and code conventions.

---

## 1. What UofA is, in 60 seconds

The **Unit of Assurance (UofA)** is a machine-verifiable JSON-LD bundle that
encodes a credibility-evidence decision for computational modeling and simulation.
Three properties matter:

- **C1 — Integrity:** signed hash + provenance, so the bundle can't be silently edited
- **C2 — Completeness:** SHACL shapes enforce that required evidence is present
- **C3 — Compound risk detection:** forward-chaining Jena rules surface weakener
  patterns across the bundle

The CLI (`uofa check`, `uofa validate`, `uofa import`, `uofa extract`, etc.) is the
user-facing surface. Domain packs (`packs/vv40/` for ASME V&V 40, `packs/nasa-7009b/`
for NASA-STD-7009B, `packs/iso42001/` for ISO 42001) plug in framework-specific
shapes, rules, and templates. The wheel ships a bundled Java rule engine — and,
per platform, a JRE — so end users don't need to install Java.

---

## 2. Look before you act

Verify firsthand before recommending, asserting, or doing anything destructive.
Past mistakes in this repo: assuming a branch was unmerged when it had been rebased
onto main, assuming the GitHub UI reflected current state when it was a stale cache,
recommending a function name from memory without grepping.

- **Rule:** Before recommending or modifying a function, file, or flag, grep for it.
  Memory and inference are not enough.
  **Why:** This repo has been through multiple reorgs (Phase E moved many paths) and
  several rebases. Symbols that existed last month may have moved or vanished.

- **Rule:** When checking branch merge state, run both `git branch --merged main`
  *and* `git branch -r --merged main`. The former omits remotes by default.
  **Why:** A branch can be "merged via rebase" — its commits land on main with
  different hashes — and `git branch --merged` won't see that. Check content
  equivalence, not just hash reachability.

- **Rule:** When a user reports a state in the GitHub UI, query the API before
  assuming the UI is right.
  **Why:** GitHub's contributors widget and several other UI elements run on caches
  that lag the underlying data by hours. The API is closer to source of truth.

---

## 3. Where things live

| Path | What it is |
|---|---|
| `src/uofa_cli/` | Python CLI package: commands, I/O, orchestration. Pack-neutral. |
| `src/weakener-engine/` | Apache Jena rule engine (Java). Produces a bundled JAR. |
| `packs/<name>/` | Self-contained domain assets: `shapes/` (SHACL), `rules/` (Jena), `templates/`, `examples/`, `prompts/`. The unit of pluggable framework support. |
| `spec/` *(singular)* | Canonical v0.5 schema: JSON-LD context, derived JSON Schema. |
| `dev/specs/` *(plural)* | Adversarial corpus generator YAMLs. **Not the same as `spec/` above.** Don't merge them. |
| `tests/` | pytest suite, layered fixtures (see §6). |
| `dev/tools/` | Maintainer scripts: `release_check.py`, refresh hooks, phase-loop runners. |
| `dev/build/` | Generated build outputs. Mostly gitignored — see §7. |
| `docs/` | Onboarding, architecture, phase runbooks, findings. |
| `site/` | Astro/Starlight docs site (`uofa.net`). Monorepo-integrated. |

- **Rule:** Pack-specific assets live in `packs/<name>/`. Don't put framework-specific
  shapes, rules, or examples in `src/`.
  **Why:** Packs are pluggable. Anything tied to a single framework (V&V 40, NASA,
  ISO 42001) inside `src/` breaks that pluggability and tangles the CLI with one domain.

- **Rule:** Don't hardcode pack-derived data (weakener pattern IDs, pattern→factor
  mappings, factor names, severities) in `src/` or the Space. Declare it in the owning
  pack's manifest (`packs/<name>/pack.json`, detection-capability `payload` — extra keys
  are allowed) and load it dynamically via `paths.detection_config` / a cached index like
  `paths.patternid_pack_index` / `paths.factor_focus_index`. Core patterns live in
  `packs/core`; pack-specific additions/overrides live in that pack.
  **Why:** Packs are the unit of change. A hardcoded map silently goes stale or wrong the
  moment a pack adds, renames, or removes a pattern. The loaders already resolve
  patternIds/shapes/rules from manifests; new pack-derived data must ride the same path.

- **Rule:** New JSON-LD examples reference the v0.5 context at
  `https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld`.
  Pin to the v0.5 tag if you need stability across `main` churn.
  **Why:** Per CONTRIBUTING.md — the context URL is the load-bearing schema reference
  for SHACL validation.

---

## 4. Specs are the source of truth

SHACL shapes (in `packs/*/shapes/`) are authoritative for C2 completeness. Jena rules
(in `packs/*/rules/`) are authoritative for C3 compound-risk detection. The v0.5
JSON-LD context (`spec/context/v0.5.jsonld`) is authoritative for property names.

- **Rule:** Don't hand-edit derived artifacts (JSON Schema under `spec/schemas/`,
  IDE autocomplete files, rendered prompts). Regenerate them via `uofa schema` or
  the relevant build script.
  **Why:** Derived artifacts go stale silently when their source changes. A hand-edit
  that doesn't round-trip will be reverted the next time the generator runs.

- **Rule:** The derivation pre-pass (Phase 5.4+) uses CONSTRUCT queries to compute
  derived triples before the weakener rules run. If you add a derived flag, declare
  it in the pack's manifest and extend `TestDerivedFlagCoverage`.
  **Why:** Weakener rules consume derived flags. If a flag isn't declared or covered,
  downstream rules silently miss the cases that depend on it.

- **Rule:** Run `uofa check <package>` and `uofa validate` locally before submitting
  any change to a pack, template, or shape. CI enforces this on the Morrison example.
  **Why:** Per CONTRIBUTING.md. Skipping local validation produces broken PRs that
  block the merge queue.

---

## 5. Commit and PR style

This repo uses conventional-commit prefixes with a mandatory scope. Look at
`git log` for live examples — patterns are remarkably consistent.

- **Rule:** Subject format: `<type>(<scope>): <imperative summary>`. Types in use:
  `feat`, `fix`, `chore`, `docs`, `test`, `refactor`. Scope is mandatory for
  `feat`/`fix`/`test`/`refactor` and identifies the subsystem
  (e.g., `iso42001`, `adversarial-judge`, `substrate`).
  **Why:** Scope makes `git log --grep` effective and lets reviewers tell at a glance
  which subsystem moved.

- **Rule:** Multi-line body required for anything non-trivial. Cite test counts
  where relevant ("1029/1029 pass", "12 new tests"), root cause for fixes, and any
  consumer files that needed coordinated updates. One-line subject is fine only for
  version bumps, refreshes, or trivial chores.
  **Why:** This repo's `git log` is the post-mortem record. A future you (or future
  agent) reading `git blame` should be able to reconstruct the *why* without external
  context.

- **Rule:** Stage files explicitly by name. Never `git add .` or `git add -A`.
  **Why:** Untracked secrets (`.env`, local plan files), generated artifacts, and
  unrelated stray edits all leak into commits when staging is wholesale.

- **Rule:** Split commits by intent. If a change touches an intentional edit *and*
  a regenerated artifact (a refreshed test report, an appended log), commit them
  separately so the diff history reflects one decision at a time.
  **Why:** A reviewer scanning history shouldn't have to mentally separate the
  meaningful change from the byproduct.

- **Rule:** Sign off commits with `git commit -s` (DCO trailer).
  **Why:** Per CONTRIBUTING.md, this project uses the Developer Certificate of Origin
  in lieu of a CLA. Every commit is an attestation that the contributor has the right
  to submit the work under Apache 2.0.

- **Rule:** Pass multi-line commit messages via heredoc, not `-m "..."`.
  **Why:** Shells mangle newlines, indentation, and special characters in `-m` strings.
  Heredoc preserves what you wrote.

- **Rule:** One logical feature per PR. Merge via merge-commit (not squash),
  preserving the PR title as `Merge PR #N: <title>`. PR body cites test counts and
  version bumps where applicable.
  **Why:** Squash erases the per-commit context this repo's discipline produces.
  Merge-commits keep both the granular history and the PR-level summary searchable.

---

## 6. Tests and fixture layers

`pytest tests/ -q` runs the main suite. Run it before pushing anything non-trivial.

Fixture layers, each with its own contract:

| Layer | Purpose | Mutability |
|---|---|---|
| `tests/fixtures/weakeners/` | Per-rule positive / negative / boundary cases | Hand-curated; edit when rule semantics change |
| `tests/fixtures/regression/` | **Exact bytes** of files that previously triggered shipped bugs | Never edit a file once landed; promotion criteria in its README |
| `tests/fixtures/corpus/` | Stress-test inputs | Gitignored; regenerated by `make corpus` |
| `tests/fixtures/extract_corpus/` | LLM extraction end-to-end pipeline inputs | Versioned; per-model outputs gitignored |

- **Rule:** When a bug fix lands, copy the file that triggered it into
  `tests/fixtures/regression/<category>/` with the exact bytes, and add a named test
  that asserts the fix. Follow the categories in
  [tests/fixtures/regression/README.md](tests/fixtures/regression/README.md)
  (crash-reader, false-positive-shacl, etc.).
  **Why:** The regression archive is the bug never coming back. Regenerated fixtures
  don't catch byte-level edge cases; the exact-bytes contract does.

- **Rule:** Brittleness-oracle and post-migration tests run by default. Don't `@skip`
  or `xfail` them to make CI green.
  **Why:** These tests exist because rule changes have historically broken previously
  passing fixtures. Skipping them defeats the early-warning purpose.

- **Rule:** The Morrison example (`packs/vv40/examples/morrison/`) must keep passing
  C1, C2, and C3. CI smoke-tests it on every PR.
  **Why:** Morrison is the reference end-to-end demo and is tied to NAFEMS demo
  screenshots that ship externally.

---

## 7. Committed vs. gitignored

This repo commits some generated and operational artifacts on purpose. Know which.

**Committed (operational records / regression guards):**
- `tests/fixtures/regression/**` — exact bytes from prior bugs
- Baseline reports under `tests/substrate/`, `dev/build/phase2_5/` — trend data
- `dev/tools/scripts/extract_accuracy_log.jsonl` — append-only LLM-accuracy log
- `dev/build/phase2_5/README.md` — workspace index (force-tracked exception)

**Gitignored (per-run / build / model-specific):**
- `tests/oos/test_report.json` — regenerated each pytest run
- `tests/fixtures/extract/*-extracted.xlsx` — model+prompt-specific outputs
- `dev/build/` (except the README) — build outputs
- `__pycache__/`, wheels, JRE staging

- **Rule:** Before committing a generated file, check `.gitignore`. If the file is
  not ignored, decide whether it's operational (commit it) or per-run (extend
  `.gitignore`). When in doubt, ask the user.
  **Why:** Committing per-run artifacts produces noisy diffs on every test run.
  Gitignoring operational records loses trend history.

---

## 8. Before you push

- **Rule:** Run the test suite locally for non-trivial changes. For changes touching
  CLI commands, also run `uofa check` and `uofa validate` against at least the
  Morrison example.
  **Why:** CI is enforcement, not first feedback. Pushing red tests wastes review
  cycles for everyone subscribed.

- **Rule:** For release-affecting changes, run
  `python dev/tools/scripts/release_check.py [--tag vX.Y.Z]`. Six fast checks
  (git state, version coherence, Python syntax compat across versions, CI workflow
  paths exist, devcontainer pip-install covers test imports, `uofa demo`
  end-to-end). Add `--full` to also run pytest.
  **Why:** Per CONTRIBUTING.md. Each check corresponds to a real bug that shipped to
  a tag and required a follow-up patch. If a check fires, fix the underlying issue
  rather than silencing the check.

- **Rule:** Frozen tags are immutable. Notably `v0.4.0-nafems` — NAFEMS demo
  screenshots are sourced from this tag. Don't amend it, ever. Critical fixes for
  v0.4 flow through a `release/v0.4.x` branch and tag a new `v0.4.x-nafems` version.
  **Why:** External materials (demo decks, papers, slides) reference specific tags.
  Mutating them silently breaks reproducibility for readers and reviewers.

- **Rule:** Don't push to `main` without explicit user direction. Don't force-push
  to shared branches at all without user direction.
  **Why:** Force-push rewrites everyone else's view of shared history. Pushing to
  `main` without confirmation skips the user's authorization gate.

---

## 9. Destructive operations

Reading is safe; deleting, force-pushing, rewriting history, and removing worktrees
are not. For any operation in that second class, confirm scope with the user first.

- **Rule:** Before deleting branches, categorize: merged to main, not merged, and
  remote-only. Report counts to the user and ask which subset to delete. Treat the
  three categories as separate decisions.
  **Why:** "Delete the foo branches" is ambiguous between "the merged ones" and
  "all of them including unmerged work." Categorizing first surfaces the choice
  instead of guessing.

- **Rule:** For worktrees, prune metadata before removing directories.
  `git worktree prune` drops dead worktree pointers; then `git worktree remove <path>`
  for any active ones; then `rm -rf` if the filesystem still has leftover trees
  (Dropbox-synced repos often do).
  **Why:** Deleting the directory first without pruning leaves dangling worktree
  metadata that confuses subsequent git commands.

- **Rule:** Never pass `--no-verify`, `--no-gpg-sign`, or any hook-bypass flag to
  `git commit` or `git push` without explicit user permission.
  **Why:** Hooks enforce sign-off, lint, and policy checks that exist for real
  reasons. Bypassing silently lands what the gates were supposed to catch.

- **Rule:** Prefer creating a new commit over `git commit --amend`. If a pre-commit
  hook fails, fix the issue and create a *new* commit rather than amending.
  **Why:** Amend modifies the previous commit; if a hook failed, the commit you'd
  be amending may not be what you think it is, and you can lose work.

---

## 10. What this repo doesn't accept in its files

Domain references to AI infrastructure are fine — model identifier strings
(`claude-sonnet-4-6`, `claude-opus-4-7`, `gpt-4o-mini`, etc.), the Anthropic /
OpenAI SDKs, judge configs naming specific models, and so on. Those are operational
references to the tools the project uses. What's not fine is attribution.

- **Rule:** Don't add AI-tool attribution to commit messages, file headers, docs,
  or comments. This includes co-authorship trailers attributing commits to AI
  assistants, "Generated with..." footers, robot-emoji credit markers, or
  `Author: <AI-tool-name>` lines in document frontmatter.
  **Why:** Commit-trailer attributions surface in GitHub's contributor graphs and
  indexers for months and aren't easily removed without rewriting history. File-header
  credits surface in code search. This repo's contributor list reflects humans who
  attest under DCO; AI assistance is workflow, not authorship.

- **Rule:** Don't commit absolute home-directory paths, references to local plan
  files, scratch-pad locations, or anything under `/Users/<name>/`, `~/.claude/`,
  or other tool-local state directories.
  **Why:** These leak the local environment of whoever ran the agent. They are
  useless to anyone else reading the repo and they date the artifact.

- **Rule:** When asked to remove existing AI-attribution leftovers, scan markdown
  and source files, not git history. Attribution embedded in commit trailers can't
  be removed without rewriting history (which forces every clone to reset). Do that
  only if the user explicitly asks; otherwise the cleanup is repo-content scoped.
  **Why:** History rewrites force-push everyone's clones to reset. The cost is
  usually higher than the value of removing already-buried attribution.

---

## 11. Tracking out-of-scope work

When you notice something worth fixing that's outside the current change —
a stale doc, a TODO that's now real, a follow-up to today's fix, an
inconsistency between two files — surface it as a GitHub issue rather
than bundling it into the current commit or inventing a local TODO file.

- **Rule:** Out-of-scope follow-ups go to GitHub Issues at
  <https://github.com/cloudronin/uofa/issues>, not to commit messages,
  scratch files, or a local `TODO.md` / `FOLLOWUPS.md`.
  **Why:** Bundled follow-ups bloat the current change and obscure its
  intent. A local TODO file isn't visible to other contributors, drifts
  from reality fast, and competes with the canonical tracker. Issues are
  searchable, assignable, and close cleanly when the work lands.

- **Rule:** When filing, include (a) what state you observed, (b) the
  discovering context ("Discovered during commit `<sha>` / PR #N"),
  (c) enough background that a future reader can act on it cold, and
  (d) a suggested next step if you know one.
  **Why:** Issues filed mid-session lose their context within days.
  Tying back to the originating commit lets future readers reconstruct
  why this matters and what was tried.

- **Rule:** Don't open issues for trivial fixes you can do inline in
  seconds, vague observations ("this could be cleaner"), or
  low-confidence hunches. The issue tracker is for real, actionable
  out-of-scope work — not a parking lot.
  **Why:** A noisy tracker is an ignored tracker.

---

## 12. The interrogation firewall (signature-scoped)

SIP — the Surrogate Interrogation Probe (`uofa interrogate`) — **measures; it
does not decide.** A package MAY carry an engineer's decision, but only as a
signed, attributed human act — never as something the tool authored. This is
the same enforcement class as the §10 AI-attribution prohibition. (Addendum A
superseded the earlier "these tokens never appear anywhere" rule; the thing
forbidden was always *SIP deciding*, not the vocabulary.)

- **Rule:** SIP's measurement output MUST contain no decision content (no
  pass/fail, accepted, validated, credibility score) and SIP MUST NOT author or
  sign a decision. Decision content is valid **only** inside a top-level
  `engineerDecision` block whose `decisionSignature` verifies against an
  externally supplied human key over the decision block **plus the measurements
  it references** (the A6 scope). Decision content in the measurement region, or
  in an unsigned / mis-scoped / unverifiable `engineerDecision` block, is a
  breach. The forbidden-token list lives in
  `src/uofa_cli/interrogate/forbidden.py::FORBIDDEN_TOKENS`, scoped to the
  measurement region by `find_forbidden_in_measurement_region` and consumed by
  the schema (measurement-region denylist + `engineerDecision` exempt), the
  `firewall-guard` make target, and the `tests/interrogate/` tests.
  **Why:** the signed evidence contract is the only interface between
  measurement and judgment. A verdict authored by the tool — or one crossing
  the boundary unsigned — collapses the separation that makes the evidence
  auditable rather than self-certifying.

- **Rule:** No fused step. `review` and `sign` are separate; `uofa interrogate`
  MUST NOT threshold, print a verdict, chain into `check`/`rules`/`validate`, or
  offer any measure-and-sign-in-one path. `uofa decision sign` REQUIRES the
  engineer's own `--key` — no default, no service key, no headless/batch
  stamping — and re-verifies the measurement signature before signing
  (stale-bundle refusal). The tool never suggests or defaults the criterion or
  verdict; `accepted` and `not-accepted` are symmetric.
  **Why:** "interrogate-and-decide in one step," or a default/synthesized
  decider, is the verdict-in-the-tool breach reintroduced through UX.

- **Rule:** UofA **verifies** decision signatures; it never creates, holds,
  issues, or manages the deciding key (it is the engineer's, like a git signing
  key). `uofa verify` reports the measurement and decision signatures
  independently; a missing/mis-scoped/unverifiable decision is surfaced as "no
  engineer decision," never as failure of the package. The SIP schema MUST ship
  in the wheel (`pyproject` force-includes `specs/`) so the schema layer runs
  for pip-installed users, not just source checkouts.
  **Why:** verifying without custody keeps a clean verification model from
  drifting into an identity-management product. A firewall that only runs in
  the dev tree is not a firewall.

- **Rule (vendor conformance).** The CLI and the signed-package contract are the
  integration surface; no special integration path is granted. A vendor may
  drive the CLI (passing through to the engineer's key) or consume the signed
  artifact — but the decision signature MUST be the deciding human's key.
  Substituting a platform service/identity key is non-conformant (the
  unattributed-decision breach relocated). Conformance is defined by the
  artifact — a decision signature that verifies against a real human key over
  the A6 scope — and is checkable from the package alone; UofA does not certify,
  bless, or audit integrations.

A change that violates this rule is out of scope by default and tracked per
§11, not merged as a convenience.

---

## 13. Numbers, checks, and the ways they lie

This repo measures things, and the recurring failure is not a component that
breaks loudly — it is an instrument that reports success. Of thirteen patterns in
[docs/corpus-construction-findings.md](docs/corpus-construction-findings.md),
**nine are defects in the measuring apparatus rather than the code it measured.**
Three produced confident numbers that were acted on and were wrong, and none of
them raised an error.

### Recording a result is not retiring the claims it invalidates

- **Rule:** When a measurement invalidates a published claim, grep the repo for
  that claim and fix every instance in the same change. `README.md`, the site
  under `site/src/content/`, and `docs/*.md` all restate results independently.
  **Why:** `control_constant_list` — a function that prints the standard's
  checklist and reads nothing — was shown to score **1.000 on detection** and the
  result was written down. The README's headline extraction claim still rested on
  that same detection metric **three months later**, and `site/.../install.md`
  advertised `assert F1 >= 0.95` on it. A finding does not propagate to the places
  that repeat it.

### A check that cannot fail

- **Rule:** After writing a check, make it fail on purpose once. If you cannot,
  it is not a check.
  **Why:** A test asserted `status == "not_assessed"` against code emitting
  `"not_assessed"` — green forever, and every workbook was unimportable. An import
  blocker used `find_module`, dead since Python 3.12, so the dependency imported
  anyway and "degrades gracefully without scikit-learn" was never tested. **A test
  that restates the implementation cannot catch the implementation being wrong**;
  assert against the vocabulary, the schema, or the constant the consumer reads.

- **Rule:** Never wrap a lookup in `except Exception`. Name the exceptions you
  expect.
  **Why:** `packs_recorded_in` caught bare `Exception` and called `pathlib.Path`
  in a module importing only `Path`. Every call raised `NameError` and returned
  `None` — "no pack recorded" for every package in the repo, which is
  *indistinguishable from the correct answer* for the ones that genuinely have
  none. A catch-all around a lookup turns a bug into a plausible default.

### Your environment is richer than the target's

- **Rule:** When a check depends on an external binary, a gitignored file, or a
  module name that could collide, run it **with that thing removed**. That is the
  only version of the check that can fail.
  **Why:** Three CI failures in one day, all green locally: a gitignored
  `extracted.xlsx` the paid run had produced, two colliding `conftest` modules
  (`tests/` and `tests/space/`) that only race when both are collected, and a
  missing `pdflatex`. In every case the local environment was a *superset* of
  CI's.

- **Rule:** Run the full suite before pushing anything that touches a shared
  serialisation path, import path, or shape file. A targeted run is not a faster
  full run.
  **Why:** A provenance record put vocabulary term names in JSON-LD key position
  and made every package unparseable. **C1, C2 and C3 all stayed green.** The only
  thing that caught it was one e2e test asserting no Python traceback reaches
  stderr — one test out of 2,681, which no reasoning about "related tests" would
  have selected.

### Numbers that describe the tooling

- **Rule:** A verdict measured on a corpus that has since been regenerated is not
  a result. Re-run it before quoting it.
  **Why:** A candidate was recorded at 15/20 against a control's 11/20. The script
  was untouched; the train split had been regenerated **three times** in the hours
  after. Re-run, it scored 9/20 against a control's 9/20 — the margin belonged to
  papers that no longer existed. Nothing in the tooling said the number was stale.

- **Rule:** Before recording a property as unextractable, try the method that
  already works elsewhere in this codebase.
  **Why:** Three properties were written off on one hand-written regex each, while
  the strongest method here — TF-IDF into logistic regression — had been applied
  to one property of nine. Applied to the other three, two beat their controls. **A
  negative about one implementation is not a negative about the task.**

- **Rule:** When a number is better than you expected, check the matcher before
  believing it.
  **Why:** An entity matcher counted fragments — `"balance"` matched a twenty-word
  clause — and reported 0.657 where the truth was 0.42. The same substring bug was
  then written a second and third time, in a different script and in a test.

### Forecasts, controls, and what validates

- **Rule:** Express an expectation as a **null control**, never as a predicted
  number. Where you would write "if X does not happen, the bug survives", write
  "the null control must fail".
  **Why:** A spec predicted validity would *drop* before improving and that no dip
  meant fabrication survived. It went up, and the fabrication was gone anyway —
  the fix *substituted* an attribution source rather than deleting a field. **A
  predicted number can be satisfied by a mechanism other than the one predicted,
  and the prediction cannot tell the difference.** A null model can.

- **Rule:** When reproducing a historical failure to write its guard, first
  confirm the failure still manifests the same way. The guard belongs where the
  signal is now, not where it was.
  **Why:** A9.1's mandatory round-trip test was written faithfully to the bug it
  guards — a non-datetime value against an `xsd:dateTime` coercion, which once
  **raised** and made every package in the repo unparseable. Current rdflib does
  not raise: it logs "Failed to convert Literal lexical form to value" and keeps
  the lexical form. So a test that merely parsed would have passed forever while
  proving nothing, because the failure had moved out from under it. Reproducing
  the original shape first showed where the signal now lives; the assertion moved
  onto the log and was then failed on purpose.

- **Pin inputs at read time. A hash taken at write time attests what was
  written, not what was used.**
  **Why:** `run_specificity.py` hashed its cases file while assembling the
  result rather than when loading it. A relabel that landed mid-run therefore
  produced a provenance block pinning the file's *later* state — a current hash
  beside a stale `label_status`, internally inconsistent and perfectly
  well-formed. Nothing looked wrong. The general form: a provenance record is a
  claim about the inputs a computation consumed, so it must be captured at the
  moment of consumption. Captured later, it silently attests to a different
  artifact and is worse than no pin, because it invites trust.

  **A check's target can move, and the fail-it-once step is the only thing that
  notices.** Note what this is an instance of: a dependency upgrade silently
  converted a hard failure into a soft one, degrading an assurance property (the
  parse fails loudly) into an unverified assumption (the parse logs politely)
  with nothing in the suite reacting. That is the same shape as every weakener in
  this repo, arriving in our own toolchain.

- **Rule:** A claim about an external artifact is not verified until the primary
  artifact has been read. An API summary, a search snippet, or a null field is a
  pointer, not a source.
  **Why:** A corpus was characterised in a committed spec as having "no dataset
  card" with "unclear redistribution terms", and a signature was recommended
  against on that basis. The dataset card existed; the licence was CC-BY-4.0 and
  the corpus had an accompanying paper. The error came from one API response
  returning a null `cardData`, read as absence rather than as a missing field in
  a summary. Reading the raw README took one request and reversed the
  recommendation. This happened **twice in one session, in the same direction
  both times** — dismissing an external artifact on secondary evidence. It is the
  outward-facing twin of the harness rule below: there, verification consumed a
  reconstruction of the production path; here, it consumed a summary of the
  artifact.

- **Rule:** A test harness that builds its own version of the production call
  path is testing the harness. Verification must consume the production path
  (`analysis_for`, `run()`), never a parallel reconstruction of it. If a test
  needs a payload, it gets one from the same function production calls.
  **Why:** The report goldens were generated by a harness that assembled the
  analysis payload itself and omitted `uoa_id`, so every package-level concern
  landed under documentation and **the goldens recorded that as correct** — the
  suite was green against a code path the command does not take. This is worse
  than a test that restates its own implementation: it restates a *different*
  one. The same afternoon produced three more of the same shape, including the
  identical `_sufficiencyAssessed` omission in two separate harnesses, one of
  which had already been reported as "verified by hand". The fix is structural,
  not diligence: one function both sides call, so they cannot diverge.

- **Rule:** Every derived committed artifact needs a regeneration-is-a-no-op
  test.
  **Why:** §4 tells you to regenerate derived artifacts rather than hand-edit
  them. That instruction is only safe if regenerating reproduces what is
  committed, and for `spec/schemas/uofa.schema.json` it did not — in **both**
  directions at once. `uofa schema --emit json` read core shapes only while the
  committed copy had been generated with `vv40` active, so following the
  documented instruction **deleted** the `hasContextOfUse` definition and
  downgraded the `deviceClass` enum. In the other direction the artifact was
  stale: core stopped requiring `hasContextOfUse` at the Minimal profile on
  2026-08-08 *because requiring it made 7009A documents invent the field*, and
  that fix never reached the schema — so for the whole of 0.11.0 the shipped
  schema kept demanding the field whose requirement had been removed for causing
  fabrication. Nothing failed in either direction. A derived artifact with no
  no-op test is an unverified copy of its source that everyone treats as the
  source.

- **Rule:** A purely additive change to a file that is covered by an integrity
  hash is not additive. Check what inlines or hashes a file before extending it;
  prefer mechanisms that make the change unnecessary (e.g. `@vocab` fallback)
  over versioning machinery.
  **Why:** Adding one vocabulary term to `spec/context/v0.5.jsonld` put the
  Morrison reference example into **`C1 Integrity ✗` while C2 and C3 stayed
  green** — `integrity.canonicalize_and_hash` inlines the context into the
  document *before* hashing, so the signed corpus is downstream of that file and
  every bundle referencing it re-hashes. The addition also bought nothing: the
  context sets `"@vocab": "https://uofa.net/vocab#"`, so undeclared terms already
  expand to `uofa:<term>` and the rule engine sees them either way. Note the
  evidence that this file was already frozen and the signal was missed — **no
  pack has ever added to it**, and the `hasDisposition` term the disposition pack
  needed sits in an unused `v0.6.jsonld` draft instead.

- **Rule:** `sh:minCount` requires a field to be **present**, not **correct**.
  Never emit a plausible value to satisfy one.
  **Why:** 14 turbomachinery models labelled `"Class II"` validated while packages
  honestly writing `"Turbomachinery (Centrifugal Pump)"` failed. `wasDerivedFrom`
  was satisfied for **27 of 27** packages by the template's own help text, `"DOI,
  report number, or URI"` — and the identical defect later made `bindsRequirement`
  come out as `"Stable URI or local ID"`. The constraint rewards fabrication and
  punishes accuracy; a blank that fails loudly is the correct output.

- **Rule:** Test the pipeline, not the step. A component is not done until its
  output has been through the command that consumes it.
  **Why:** The keyless extractor was exercised as far as producing a spreadsheet
  and never through `uofa import` to a package — the only artefact anyone wants.
  Every test passed while every workbook was rejected on twelve rows.

---

## Quick reference

- **Validate before pushing:** `pytest tests/ -q` and (for CLI changes)
  `uofa check packs/vv40/examples/morrison/morrison.jsonld`. The **full** suite —
  a targeted run is not a faster full run (§13)
- **Make every new check fail once**, on purpose. A check that cannot fail is not
  a check (§13)
- **When a result invalidates a claim,** grep for that claim and fix it in the
  same change — README, `site/src/content/`, and `docs/` restate results
  independently (§13)
- **Before tagging a release:** `python dev/tools/scripts/release_check.py --tag vX.Y.Z`
- **Sign your commits:** `git commit -s -m "..."`
- **Stage by name:** `git add <specific files>`, never `git add .`
- **Confirm scope before:** deleting branches, force-pushing, rewriting history,
  removing worktrees
- **File follow-ups as issues:** <https://github.com/cloudronin/uofa/issues> —
  not in commit messages, not in local TODO files
