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

## Quick reference

- **Validate before pushing:** `pytest tests/ -q` and (for CLI changes)
  `uofa check packs/vv40/examples/morrison/morrison.jsonld`
- **Before tagging a release:** `python dev/tools/scripts/release_check.py --tag vX.Y.Z`
- **Sign your commits:** `git commit -s -m "..."`
- **Stage by name:** `git add <specific files>`, never `git add .`
- **Confirm scope before:** deleting branches, force-pushing, rewriting history,
  removing worktrees
