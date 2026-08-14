"""S3 deploy-asset sanity — cheap guards so the Docker/Space contract can't
silently drift (model config, port, entrypoint, front-matter). No Docker needed."""

from __future__ import annotations

from pathlib import Path

_SPACE = Path(__file__).resolve().parents[2] / "space"

MODEL = "qwen3.5:4b"  # must match uofa_cli.llm.config.BUNDLED_MODEL


def test_bundled_model_matches_cli():
    """The CLI's local default. No longer what the Space runs -- the Space is
    configured for hosted inference below -- but still the fallback whenever no
    backend is declared, which includes every local run and every test."""
    from uofa_cli.llm.config import BUNDLED_MODEL

    assert BUNDLED_MODEL == MODEL


def test_base_dockerfile_declares_hosted_inference():
    df = (_SPACE / "Dockerfile.base").read_text()
    assert "UOFA_SPACE_LLM_BACKEND=openai-compatible" in df
    assert "UOFA_SPACE_LLM_BASE_URL=https://api.together.xyz/v1" in df
    assert "UOFA_SPACE_LLM_MODEL=" in df
    assert "UOFA_SPACE_LLM_KEY_ENV=TOGETHER_API_KEY" in df


def test_base_dockerfile_keeps_the_runtime_the_engine_needs():
    """JRE 17 is the trap: `_run_weakeners` degrades to [] when Java is absent,
    so removing it turns every run into a completeness-only readout with no
    error anywhere. ca-certificates became load-bearing when inference moved to
    an outbound HTTPS call."""
    df = (_SPACE / "Dockerfile.base").read_text()
    assert "openjdk-17-jre-headless" in df
    assert "ca-certificates" in df
    assert "useradd -m -u 1000 user" in df          # HF runs as UID 1000


def test_no_api_key_is_baked_into_any_image_or_app_file():
    """Configuration lives in git; the key is a Space secret and nothing else.
    The Space repo is public, so anything committed here is published."""
    suspects = [*_SPACE.glob("Dockerfile*"), *_SPACE.glob("*.sh"), *_SPACE.glob("*.py")]
    for path in suspects:
        body = path.read_text()
        assert "TOGETHER_API_KEY=" not in body, f"{path.name} assigns the API key"
        assert "tgp_" not in body, f"{path.name} may contain a Together key"
        assert "sk-" not in body, f"{path.name} may contain an API key"


def test_space_dockerfile_is_thin_and_from_base():
    # HF builds this one; it must only pull the base + copy the app so the build
    # stays well inside HF's 30-min limit.
    df = (_SPACE / "Dockerfile").read_text()
    assert "FROM ghcr.io/cloudronin/uofa-demo-base:" in df
    assert "COPY --chown=user:user space/" in df
    assert "EXPOSE 7860" in df
    assert 'ENTRYPOINT ["bash", "space/start.sh"]' in df
    # The thin image must NOT redo the base's work.
    assert "ollama pull" not in df


def test_start_sh_launches_the_app_without_a_local_daemon():
    """start.sh used to bring up Ollama and BLOCK on a pre-warm until ~3 GB of
    weights were resident, before Gradio began listening. With inference hosted
    there is nothing to warm, and that serialization was a large share of the
    Space's cold start."""
    sh = (_SPACE / "start.sh").read_text()
    # Comments are stripped first: the file explains what it used to do and why,
    # and that history is worth keeping. What must be gone is the behaviour.
    code = "\n".join(l for l in sh.splitlines() if not l.lstrip().startswith("#"))
    assert "python -m space.app" in code
    assert "ollama" not in code.lower()
    assert "pre-warm" not in code.lower()
    assert "11434" not in code       # the daemon's port, in the old wait loop


def test_readme_has_docker_space_frontmatter():
    text = (_SPACE / "README.md").read_text()
    front = text.split("---")[1]
    assert "sdk: docker" in front
    assert "app_port: 7860" in front


def test_requirements_pins_gradio():
    reqs = (_SPACE / "requirements.txt").read_text()
    assert "gradio" in reqs
