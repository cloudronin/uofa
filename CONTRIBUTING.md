# Contributing to UofA

Thanks for helping make the **Unit of Assurance (UofA)** better!

## License of contributions

This project is licensed under the **Apache License 2.0**. By submitting
a contribution (a pull request, patch, issue with a code suggestion, or
any other change), you agree that your contribution is licensed under
Apache 2.0 — the same license as the rest of the project.

We use the **Developer Certificate of Origin (DCO)** in lieu of a CLA.
The DCO is a lightweight per-commit attestation that you have the right
to submit the work under the project license. To sign off, add the `-s`
flag when committing:

```bash
git commit -s -m "Your commit message"
```

That appends a `Signed-off-by: Your Name <email>` line to your commit
message. The full DCO text is at <https://developercertificate.org/>.
There is **no separate CLA, no extra paperwork, and no copyright
assignment** — every contribution stays under the contributor's name
and the project license.

If you forget the `-s` on a commit, you can amend the most recent commit
with `git commit --amend -s`, or rebase a branch and add sign-offs with
`git rebase --signoff <base>`.

## Branch discipline (release tags)

- `v0.4.0-nafems` — **frozen reference for NAFEMS demo slides.** Morrison COU1 = 14 weakeners, COU2 = 6. Do not change this commit; demo screenshots are sourced from this tag regardless of what `main` looks like.
- `v0.5.0-pre-phase2` — Phase 2 experimental baseline on `main`. Expanded 23-pattern core catalog. Morrison COU1 = 24, COU2 = 16 (see `CHANGELOG.md` and `docs/v0.5-morrison-deltas.md` for per-rule attribution).
- Work that targets Phase 2 or later lands on `main`. Bug fixes that must flow back to `v0.4.0-nafems` land on a `release/v0.4.x` branch and tag a new `v0.4.x-nafems` version — never amend the frozen tag.

## Quick Start

1. **Fork** the repo and create a feature branch.
2. If adding examples, put them in `/examples` and open a PR — CI will run SHACL validation.

## Adding Examples

Start from a template in `packs/core/templates/`, import from an Excel workbook (`uofa import`), or customize manually. Your example should:

- Use the v0.5 JSON-LD context:
  ```json
  "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
  ```
- Conform to either Minimal or Complete profile
- Include a signed hash and signature (see [Onboarding Guide](docs/onboarding.md))

## Validating Before Submitting

```bash
# Install the CLI
pip install -e .

# Validate your example passes SHACL
uofa check packs/your-pack/examples/your-uofa.jsonld

# Or validate all examples at once
uofa validate
```

CI runs `uofa validate` and `uofa check` on the Morrison example for every PR.

## Pre-tag release checklist

Before tagging a new release, run [release_check.py](dev/tools/scripts/release_check.py) to catch the kinds of drift that have slipped past local testing in past tags. The script is fast (no pytest by default) and exits non-zero on any failure so you can chain it before `git tag`:

```bash
# Fast checks only (~10 seconds)
python dev/tools/scripts/release_check.py --tag v0.6.5

# Same plus the full pytest suite (~10-15 minutes)
python dev/tools/scripts/release_check.py --tag v0.6.5 --full
```

The six fast checks are:

| Check | What it catches |
|---|---|
| Git state | Uncommitted changes, wrong branch, behind origin/main. |
| Version coherence | `pyproject.toml` `version` matches the intended tag. |
| Python syntax compat | `ast.parse`s `src/uofa_cli/**.py` under **every** installed Python ≥ the project minimum. *Catches: v0.6.2 backslash-in-fstring that parsed fine on 3.12 but broke pytest collection on the 3.11 CI runner.* |
| CI workflow paths | Greps `cd <path>`, `path:`, and `paths:` entries from every `.github/workflows/*.yml` and verifies each target exists on disk. *Catches: v0.6.4 release-wheels.yml referencing pre-reorg paths (`weakener-engine`, root `hatch_build.py`) after the Phase E reorg moved them.* |
| Test imports vs devcontainer install | Parses every top-level import in `tests/` and checks the devcontainer `postCreateCommand`'s `pip install -e .[extras]` line covers them all. *Catches: post-v0.6.4 devcontainer hot-fix where `[test,excel]` didn't include `[extract]`, so 46 tests degraded with "Jinja2 not installed" in CI.* |
| uofa demo smoke | Runs `uofa demo` end-to-end and confirms C1 + C2 + C3 all report ✓. *Catches: the v0.6.5 `commands/demo.py` regression where the JAR-staging path still pointed at the pre-Phase-E `weakener-engine/target/` location. Static path audits don't catch source-code path strings, so the catch-all is to actually run the bundled command (~30s).* |

Pass `--full` to also run `pytest tests/ -q` as a seventh check. The `--tag` argument is optional — without it, the version-coherence check is skipped (useful for sanity-checking `main` between releases).

If a check fires, fix the underlying issue rather than silencing the check. Each one corresponds to a real bug that shipped to a tag and required a follow-up patch.

## Building wheels (release maintainers)

The `release-wheels.yml` workflow produces five wheels per release: a
`py3-none-any` wheel that bundles only the rule-engine JAR (system Java
17+ still required), plus per-platform wheels for macOS arm64,
Linux x86_64 / aarch64, and Windows x86_64 that bundle the JAR **and** an
OpenJDK 17 JRE so end users need no Java install.

> **Intel macOS users**: as of v0.7.0 we no longer build a `macosx_11_0_x86_64`
> wheel. GitHub Actions' `macos-13` queue waits routinely ran 20–60+ minutes
> and would block the PyPI publish job. Intel Mac users should install the
> `py3-none-any` wheel and provide a system Java 17 (`brew install openjdk@17`).
> If Intel-Mac usage signal grows, the wheel can come back.

The same workflow also builds an sdist and publishes everything (5 wheels +
sdist) to [PyPI](https://pypi.org/project/uofa/) automatically on every
`v*` tag push, gated on every smoke job passing. Auth is via PyPI Trusted
Publishing (OIDC) — no API tokens are stored in GitHub secrets.

Local wheel builds use the same Hatchling custom hook in `hatch_build.py`:

```bash
# Bundle JAR only (no JRE) — Python-only wheel.
UOFA_BUNDLE_JAR=1 python -m build --wheel

# Bundle JAR + per-platform JRE (downloads ~40 MB from Adoptium).
UOFA_BUNDLE_PLATFORM=manylinux_2_28_x86_64 python -m build --wheel
UOFA_BUNDLE_PLATFORM=macosx_11_0_arm64     python -m build --wheel
# ...etc. Valid keys are the headings under [platforms.*] in jre_manifest.toml.
```

The hook auto-cleans staged artifacts in `finalize()` so the bundled JRE
never lingers in your source tree between builds. If you ever interrupt a
build mid-flight (Ctrl-C, OOM, etc.) and end up with a stale staged JRE,
restore the source tree with:

```bash
make clean-bundled
```

This matters because `paths.bundled_jre_executable()` prefers the staged
JRE over your system Java for any subsequent in-source-tree test run, and
a wrong-architecture binary surfaces as `[Errno 8] Exec format error`.

The pinned Adoptium URLs and SHA-256s live in `jre_manifest.toml`. Refresh
quarterly:

```bash
python dev/tools/scripts/refresh_jre_manifest.py            # update existing platforms
python dev/tools/scripts/refresh_jre_manifest.py --all      # bootstrap full set
python dev/tools/scripts/refresh_jre_manifest.py --check    # CI freshness gate
```

When OpenJDK 17 CVEs land, run the refresh, run the wheel build CI, and
ship a patch release.

## Questions?

If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out at [uofa.net](https://uofa.net) or via [GitHub Discussions](https://github.com/cloudronin/uofa/discussions).
