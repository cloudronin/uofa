"""Sync the Gap-Finder Space layout to the HF Docker Space in one commit.

HF Docker Spaces build the image themselves from the pushed source, so "deploy"
means: assemble the Space repo layout (root Dockerfile + HF README + the
build context the Dockerfile needs) and commit it. HF then rebuilds.

Auth: reads HF_TOKEN from the environment. In CI this is the short-lived
OIDC-exchanged token (see .github/workflows/deploy-space.yml); locally you can
export a normal write token to redeploy by hand.

Secrets safety: only `keys/research.pub` is shipped (the wheel force-includes
it); `keys/*.key`, build artifacts, caches, and the local-only build scaffold
are never uploaded.
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

REPO = os.environ.get("HF_SPACE_REPO", "cloudronin/uofa-demo")
ROOT = Path(__file__).resolve().parents[1]

# Files placed at the Space root (HF builds from the root Dockerfile + README).
ROOT_FILES = {
    "space/Dockerfile": "Dockerfile",
    "space/README.md": "README.md",
    "pyproject.toml": "pyproject.toml",
    "keys/research.pub": "keys/research.pub",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
}

# Directory trees the wheel build needs (mirrored at the same path in the Space).
TREES = ["src", "packs", "spec", "specs", "space", "build-config"]

# Substring matches that must never be uploaded (artifacts, caches, secrets, scaffold).
DENY = (
    "__pycache__",
    ".pyc",
    ".DS_Store",
    "src/weakener-engine/target",   # jar is rebuilt by the Maven stage
    "src/uofa_cli/_engine",
    "src/uofa_cli/_runtime",
    "src/uofa_cli/_data",           # wheel-generated bundle
    "space/_prebuilt.jar",          # local-only build scaffold
    "space/Dockerfile.local",
    ".key",                         # never ship private keys
)


def _denied(rel: str) -> bool:
    return any(token in rel for token in DENY)


def build_operations() -> list[CommitOperationAdd]:
    ops: list[CommitOperationAdd] = []
    for local, in_repo in ROOT_FILES.items():
        p = ROOT / local
        if p.exists():
            ops.append(CommitOperationAdd(in_repo, str(p)))

    for tree in TREES:
        base = ROOT / tree
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if _denied(rel):
                continue
            ops.append(CommitOperationAdd(rel, str(path)))
    return ops


def main() -> None:
    ops = build_operations()
    # Hard guarantee: no private key ever leaves the repo.
    leaked = [op.path_in_repo for op in ops if op.path_in_repo.endswith(".key")]
    if leaked:
        raise SystemExit(f"refusing to deploy: private key(s) in payload: {leaked}")

    sha = os.environ.get("GITHUB_SHA", "local")[:7]
    api = HfApi(token=os.environ["HF_TOKEN"])
    api.create_commit(
        repo_id=REPO,
        repo_type="space",
        operations=ops,
        commit_message=f"CI: sync Gap-Finder Space ({sha})",
    )
    print(f"synced {len(ops)} files to spaces/{REPO} (commit {sha}); HF rebuild triggered")


if __name__ == "__main__":
    main()
