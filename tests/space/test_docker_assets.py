"""S3 deploy-asset sanity — cheap guards so the Docker/Space contract can't
silently drift (model id, port, entrypoint, front-matter). No Docker needed."""

from __future__ import annotations

from pathlib import Path

_SPACE = Path(__file__).resolve().parents[2] / "space"

MODEL = "qwen3.5:4b"  # must match uofa_cli.llm.config.BUNDLED_MODEL


def test_bundled_model_matches_cli():
    from uofa_cli.llm.config import BUNDLED_MODEL

    assert BUNDLED_MODEL == MODEL  # if the CLI default changes, update the image


def test_base_dockerfile_bakes_model_and_deps():
    # The heavy layers (model, JRE, non-root user) live in the prebuilt base
    # image that CI pushes to GHCR — NOT in the thin Space Dockerfile.
    df = (_SPACE / "Dockerfile.base").read_text()
    assert f"ollama pull {MODEL}" in df
    assert "openjdk-17-jre-headless" in df          # C3 weakeners need Java
    assert "useradd -m -u 1000 user" in df          # HF runs as UID 1000


def test_space_dockerfile_is_thin_and_from_base():
    # HF builds this one; it must only pull the base + copy the app so the build
    # stays well inside HF's 30-min limit (baking the 3 GB model here times out).
    df = (_SPACE / "Dockerfile").read_text()
    assert "FROM ghcr.io/cloudronin/uofa-demo-base:" in df
    assert "COPY --chown=user:user space/" in df
    assert "EXPOSE 7860" in df
    assert 'ENTRYPOINT ["bash", "space/start.sh"]' in df
    # The thin image must NOT redo the base's heavy work.
    assert "ollama pull" not in df


def test_start_sh_brings_up_ollama_then_app():
    sh = (_SPACE / "start.sh").read_text()
    assert "ollama serve" in sh
    assert "pre-warm" in sh.lower()
    assert "python -m space.app" in sh


def test_readme_has_docker_space_frontmatter():
    text = (_SPACE / "README.md").read_text()
    front = text.split("---")[1]
    assert "sdk: docker" in front
    assert "app_port: 7860" in front


def test_requirements_pins_gradio():
    reqs = (_SPACE / "requirements.txt").read_text()
    assert "gradio" in reqs
