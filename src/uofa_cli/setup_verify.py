"""Implementation of `uofa setup verify` (REQ-DIST-006).

Runs an end-to-end smoke test against a known fixture and reports the
result. The command is the user-facing reassurance step that confirms
"your install actually works" right after setup completes; it is also
the diagnostic for troubleshooting a broken install.

Failure modes reported with actionable next-step messages:

  * Daemon health check failed       → "model load timed out"
  * Extracted JSON failed validation  → "extracted JSON failed schema validation"
  * F1 below the 0.95 threshold       → "F1 below threshold (X.XX, expected ≥ 0.95)"

The verify fixture lives in src/uofa_cli/_data/fixtures/verify/ and is
calibrated for qwen3.5:4b. If the model is upgraded the fixture's
expected.json may need re-calibration.
"""

from __future__ import annotations

import importlib.resources
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from uofa_cli import setup_install, setup_state
from uofa_cli.eval_scoring import score_extraction
from uofa_cli.llm_extractor import _json_to_result


F1_THRESHOLD = 0.95


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    f1: float | None
    diagnostic: str
    elapsed_seconds: float


def _verify_fixture_dir() -> Path:
    """Locate the verify fixture inside the installed package.

    Uses importlib.resources so it works in editable installs and zipapp-
    style bundles equally.
    """
    pkg_files = importlib.resources.files("uofa_cli")
    fixture = pkg_files / "_data" / "fixtures" / "verify"
    return Path(str(fixture))


def verify(
    cfg: setup_state.SetupConfig | None = None,
    on_status: Callable[[str], None] | None = None,
) -> VerifyResult:
    """Run the end-to-end verify smoke test."""
    say = on_status or (lambda _: None)
    started = time.monotonic()

    if cfg is None:
        cfg = setup_state.load_config()
        if cfg is None:
            return VerifyResult(
                ok=False,
                f1=None,
                diagnostic="No config: run `uofa setup` first.",
                elapsed_seconds=time.monotonic() - started,
            )

    fixture_dir = _verify_fixture_dir()
    passage_path = fixture_dir / "passage.txt"
    expected_path = fixture_dir / "expected.json"
    if not passage_path.is_file() or not expected_path.is_file():
        return VerifyResult(
            ok=False,
            f1=None,
            diagnostic=f"Verify fixture missing under {fixture_dir}",
            elapsed_seconds=time.monotonic() - started,
        )

    say(f"Starting Ollama daemon on port {cfg.ollama_port}.")
    daemon = setup_install.start_managed_daemon(
        cfg.ollama_binary,
        port=cfg.ollama_port,
        models_dir=cfg.ollama_models_dir,
    )
    try:
        try:
            setup_install.wait_for_daemon(cfg.ollama_port)
        except TimeoutError as e:
            return VerifyResult(
                ok=False,
                f1=None,
                diagnostic=f"model load timed out: {e}",
                elapsed_seconds=time.monotonic() - started,
            )

        say("Running extraction against fixture passage.")
        try:
            extracted_json = _run_extraction(cfg, passage_path)
        except RuntimeError as e:
            return VerifyResult(
                ok=False,
                f1=None,
                diagnostic=f"extraction failed: {e}",
                elapsed_seconds=time.monotonic() - started,
            )

        try:
            ground_truth = json.loads(expected_path.read_text())
        except json.JSONDecodeError as e:
            return VerifyResult(
                ok=False,
                f1=None,
                diagnostic=f"expected.json is malformed: {e}",
                elapsed_seconds=time.monotonic() - started,
            )

        try:
            result = _json_to_result(extracted_json, pack_name=ground_truth.get("pack", "vv40"))
        except Exception as e:
            return VerifyResult(
                ok=False,
                f1=None,
                diagnostic=f"extracted JSON failed schema validation: {e}",
                elapsed_seconds=time.monotonic() - started,
            )

        scores = score_extraction(result, ground_truth)
        f1 = scores["f1"]
        if f1 < F1_THRESHOLD:
            return VerifyResult(
                ok=False,
                f1=f1,
                diagnostic=(
                    f"F1 below threshold ({f1:.2f}, expected >= {F1_THRESHOLD})"
                ),
                elapsed_seconds=time.monotonic() - started,
            )

        return VerifyResult(
            ok=True,
            f1=f1,
            diagnostic=f"verified: F1={f1:.2f} (>= {F1_THRESHOLD})",
            elapsed_seconds=time.monotonic() - started,
        )
    finally:
        daemon.terminate()
        try:
            daemon.wait(timeout=5)
        except subprocess.TimeoutExpired:
            daemon.kill()


def _run_extraction(cfg: setup_state.SetupConfig, passage_path: Path) -> dict:
    """Send the passage text to the daemon and return the parsed JSON.

    Bypasses the heavier extract_cmd dispatch path (which insists on a
    pack manifest, prompt template, etc.) in favor of a direct
    /api/chat call with a minimal "extract credibility factors as JSON"
    prompt. This keeps the verify fixture tiny.
    """
    import requests

    text = passage_path.read_text()
    prompt = (
        "Extract credibility factors mentioned in the following passage "
        "as a single JSON object with a 'credibility_factors' array. "
        "Each factor must include 'factor_type' (string) and "
        "'achieved_level' (integer 0-4) when stated. Return ONLY the JSON.\n\n"
        f"PASSAGE:\n{text}"
    )
    resp = requests.post(
        f"http://127.0.0.1:{cfg.ollama_port}/api/chat",
        json={
            "model": cfg.model_tag,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        },
        timeout=180,
    )
    resp.raise_for_status()
    payload = resp.json()
    content = payload.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError(f"Empty response from /api/chat: {payload}")
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"daemon returned non-JSON content: {content[:200]}") from e
