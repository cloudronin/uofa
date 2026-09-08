"""Sync the Gap-Finder Space layout to the HF Docker Space in one commit.

HF Docker Spaces build the image themselves from the pushed source. The heavy
image is prebuilt in CI and pushed to GHCR (see space/Dockerfile.base), so the
Space's Dockerfile is thin (`FROM <base> + COPY space/`). "Deploy" therefore
means: assemble the thin Space layout (root Dockerfile + HF README + the space/
app tree) and commit it. HF then rebuilds the thin image on the fresh base.

The base is pinned on the way out: the Dockerfile committed to the Space names
`<base>:<commit sha>`, not `<base>:latest`, so HF cannot build the Space on a
copy of a mutable tag it happened to be holding. See `_pin_base_image`.

Auth: reads HF_TOKEN from the environment. In CI this is the short-lived
OIDC-exchanged token (see .github/workflows/deploy-space.yml); locally you can
export a normal write token to redeploy by hand.

Secrets safety: `keys/*.key` is never uploaded (the base image already bundles
the public research key via the wheel); build artifacts, caches, and the
local-only build scaffold are excluded too.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

REPO = os.environ.get("HF_SPACE_REPO", "cloudronin/uofa-demo")
ROOT = Path(__file__).resolve().parents[1]

# The prebuilt base, without a tag. `space/Dockerfile` names it as `:latest` so
# a hand-run `docker build` still works from a checkout; CI rewrites that line
# to the commit tag on the way to HF (see `_pin_base_image`).
BASE_IMAGE = "ghcr.io/cloudronin/uofa-demo-base"

# Files placed at the Space root (HF builds from the root Dockerfile + README).
ROOT_FILES = {
    "space/Dockerfile": "Dockerfile",
    "space/README.md": "README.md",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
}

# The thin Space Dockerfile builds `FROM <prebuilt base> + COPY space/`, so the
# Space repo needs only the app tree; the base image (built in CI, see
# space/Dockerfile.base) already carries src/, packs/, spec/, specs/,
# build-config/, the wheel, and the baked model.
TREES = ["space"]

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
    "space/Dockerfile.base",        # built in CI -> GHCR, not by HF
    ".key",                         # never ship private keys
    ".pem",                         # same, other conventional suffix
    ".env",                         # dotenv files carry the demo signing key
)


def _denied(rel: str) -> bool:
    return any(token in rel for token in DENY)


def _pin_base_image(dockerfile: str, sha: str) -> str:
    """Rewrite `FROM <base>:latest` to `FROM <base>:<sha>`.

    `:latest` is a mutable tag, and the whole Space runs on whatever it resolves
    to. CI refreshes that tag immediately before this sync, but HF's builder is
    a machine we do not control: if it already holds a `:latest` for this
    reference it is free to build on the copy it has, and the Space then runs an
    image older than the source that was just pushed. Nothing in the Space's
    logs would say so -- the app starts cleanly on a stale wheel.

    That is not a theoretical worry. A signed run that could not assemble its
    downloadable pack (#128) survived five hypotheses, every one of them
    disproved against the source in the checkout, which leaves the possibility
    that the container was never running that source. Pinning removes the
    question rather than answering it: the same `base` job pushes `:<sha>`
    alongside `:latest`, that tag is written once and never moved, and the
    Space's own Dockerfile now records exactly which image it was built on.
    """
    return re.sub(rf"^FROM {re.escape(BASE_IMAGE)}:\S+",
                  f"FROM {BASE_IMAGE}:{sha}", dockerfile, flags=re.M)


def _dockerfile_bytes() -> bytes:
    """The thin Dockerfile as it should reach HF, base pinned when CI knows it.

    Outside CI there is no commit to pin to, so the file goes up verbatim and
    the Space builds on `:latest` exactly as it did before.
    """
    text = (ROOT / "space" / "Dockerfile").read_text(encoding="utf-8")
    sha = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", sha):
        text = _pin_base_image(text, sha)
    return text.encode("utf-8")


def build_operations() -> list[CommitOperationAdd]:
    ops: list[CommitOperationAdd] = []
    for local, in_repo in ROOT_FILES.items():
        p = ROOT / local
        if not p.exists():
            continue
        if local == "space/Dockerfile":
            ops.append(CommitOperationAdd(in_repo, _dockerfile_bytes()))
        else:
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


def _secrets_in(ops) -> list[str]:
    """Paths that must never reach the Space repo, which is public.

    Belt to DENY's braces: DENY is a substring filter that a renamed file can
    slip past, and this is the last gate before a public push. The demo issuer's
    private key reaches the Space only as a settings secret, never as a file.
    """
    suffixes = (".key", ".pem", ".env")
    return [op.path_in_repo for op in ops
            if op.path_in_repo.endswith(suffixes) or ".env." in op.path_in_repo]


def main() -> None:
    ops = build_operations()
    # Hard guarantee: no private key or dotenv ever leaves the repo.
    leaked = _secrets_in(ops)
    if leaked:
        raise SystemExit(f"refusing to deploy: secret(s) in payload: {leaked}")

    # Say which base the Space is about to build on. When a run comes back wrong
    # this is the line that says whether it was the source we think it was.
    from_line = next((l for l in _dockerfile_bytes().decode().splitlines()
                      if l.startswith("FROM ")), "FROM ?")
    print(f"[deploy] Space will build on: {from_line.removeprefix('FROM ').strip()}")

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
