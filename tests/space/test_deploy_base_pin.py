"""The Space must build on the image CI just pushed, not on a tag's namesake.

`space/Dockerfile` says `FROM ghcr.io/cloudronin/uofa-demo-base:latest`, which
is the right thing for a hand-run `docker build` from a checkout and the wrong
thing to hand HuggingFace. `:latest` is mutable, HF's builder is not ours, and a
builder holding an older copy of that reference is free to use it. The Space
then runs a wheel that is not the source that was pushed, starts cleanly, and
says nothing about it.

That failure mode is why these tests exist: a signed run in the deployed Space
could not assemble its downloadable pack while every hypothesis about the source
was disproved against the checkout. `_pin_base_image` removes the possibility
that the container was never running that source.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("huggingface_hub")

from space import deploy_to_hf

SHA = "0123456789abcdef0123456789abcdef01234567"
_DOCKERFILE = Path(deploy_to_hf.ROOT) / "space" / "Dockerfile"


def test_checkout_dockerfile_still_names_the_floating_tag():
    """The file in git stays `:latest`. Pinning is a deploy-time rewrite, so a
    developer building the Space image by hand does not have to know a sha."""
    assert f"FROM {deploy_to_hf.BASE_IMAGE}:latest" in _DOCKERFILE.read_text()


def test_pin_rewrites_the_from_line_to_the_commit_tag():
    out = deploy_to_hf._pin_base_image(
        f"FROM {deploy_to_hf.BASE_IMAGE}:latest\nCOPY space/ /app/space/\n", SHA)
    assert out.splitlines()[0] == f"FROM {deploy_to_hf.BASE_IMAGE}:{SHA}"
    assert "COPY space/ /app/space/" in out


def test_pin_leaves_every_other_line_alone():
    """Only the base's own FROM moves. A comment mentioning `:latest`, or a
    second stage from an unrelated image, must survive untouched."""
    src = (f"# pinned to :latest on purpose\n"
           f"FROM python:3.11-slim AS builder\n"
           f"FROM {deploy_to_hf.BASE_IMAGE}:latest\n")
    out = deploy_to_hf._pin_base_image(src, SHA)
    assert "# pinned to :latest on purpose" in out
    assert "FROM python:3.11-slim AS builder" in out
    assert f"FROM {deploy_to_hf.BASE_IMAGE}:{SHA}" in out


def test_ci_uploads_the_pinned_dockerfile(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", SHA)
    body = deploy_to_hf._dockerfile_bytes().decode()
    assert f"FROM {deploy_to_hf.BASE_IMAGE}:{SHA}" in body
    assert f"FROM {deploy_to_hf.BASE_IMAGE}:latest" not in body


@pytest.mark.parametrize("sha", ["", "local", "abc1234", "not-a-sha" * 5])
def test_a_non_sha_never_becomes_a_tag(sha, monkeypatch):
    """A short sha, a placeholder, or an unset variable would each pin the Space
    to a tag that does not exist and break the build. Anything but a full commit
    sha means "no pin", and the Space builds on `:latest` as it always did."""
    monkeypatch.setenv("GITHUB_SHA", sha)
    body = deploy_to_hf._dockerfile_bytes().decode()
    assert f"FROM {deploy_to_hf.BASE_IMAGE}:latest" in body


def test_outside_ci_the_dockerfile_goes_up_verbatim(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    assert deploy_to_hf._dockerfile_bytes() == _DOCKERFILE.read_bytes()


def test_the_pinned_tag_is_one_ci_actually_pushes():
    """The rewrite is only as good as the tag existing. The `base` job pushes
    `:latest` and `:${{ github.sha }}`; drop the second and every deploy after
    it fails on HF with a manifest-not-found that this repo never sees."""
    wf = (Path(deploy_to_hf.ROOT) / ".github" / "workflows"
          / "deploy-space.yml").read_text()
    assert re.search(r"uofa-demo-base:\$\{\{\s*github\.sha\s*\}\}", wf)
