"""S3 deploy-asset sanity — cheap guards so the Docker/Space contract can't
silently drift (model id, port, entrypoint, front-matter). No Docker needed."""

from __future__ import annotations

from pathlib import Path

_SPACE = Path(__file__).resolve().parents[2] / "space"

MODEL = "qwen3.5:4b"  # must match uofa_cli.llm.config.BUNDLED_MODEL


def test_bundled_model_matches_cli():
    from uofa_cli.llm.config import BUNDLED_MODEL

    assert BUNDLED_MODEL == MODEL  # if the CLI default changes, update the image


def test_dockerfile_bakes_model_and_exposes_port():
    df = (_SPACE / "Dockerfile").read_text()
    assert f"ollama pull {MODEL}" in df
    assert "openjdk-17-jre-headless" in df          # C3 weakeners need Java
    assert "EXPOSE 7860" in df
    assert 'ENTRYPOINT ["bash", "space/start.sh"]' in df
    assert "useradd -m -u 1000 user" in df          # HF runs as UID 1000


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
