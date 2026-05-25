"""End-to-end NASA aero pipeline test: evidence → extract → import → reports → diff.

This is the only test that chains the *entire* user-facing flow on real
evidence folders for both COUs of the NAFEMS aero case study. It catches
integration regressions that the per-step tests miss — like today's
vocab-mismatch bug (a real LLM produced non-canonical evidence_type values
that the importer rejected; the per-step extract test used mock data and
didn't see it).

Two variants:

* **TestAeroFullPipelineE2EMock** — always runs. Uses ``--model mock`` for
  deterministic canned LLM output. Asserts that every step in the chain
  completes without crashing and produces the expected file artifacts.
  Does NOT assert semantic content (mock data doesn't reproduce the
  level-gap pattern that drives W-AR-02 firings).

* **TestAeroFullPipelineE2ERealLLM** — gated by ``UOFA_RUN_REAL_LLM=1``.
  Uses a real local Ollama model (``ollama/qwen3.5:4b``). Asserts the
  semantic NAFEMS divergence pattern: W-AR-02 fires on COU1 (Accepted,
  with gap factors) and stays at zero on COU2 (Not Accepted), and the
  diff command surfaces a non-empty divergence.

Both share the helper that does ``extract → import → check → rules`` for
one COU. Class-scoped fixtures keep the heavy steps (extract, import)
to once per class.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# Reuse the run_uofa helper from the existing integration test module.
# pytest's rootdir-import mode (no tests/__init__.py) puts the tests
# directory on sys.path, so the bare module name resolves. Don't use
# `from tests.test_extract_integration` — that breaks CI collection.
from test_extract_integration import run_uofa, AERO_COU1_DIR, AERO_COU2_DIR

REAL_LLM_ENABLED = os.environ.get("UOFA_RUN_REAL_LLM") == "1"

pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl required")


# ── Shared chain runner ───────────────────────────────────────


def _extract_and_import(tmp_dir: Path, evidence_dir: Path, cou_label: str, model: str):
    """Run extract → import for one COU, return paths to xlsx and jsonld.

    Raises AssertionError if either step fails so the chain stops at the
    real point of failure rather than cascading useless errors.
    """
    xlsx = tmp_dir / f"{cou_label}.xlsx"
    jsonld = tmp_dir / f"{cou_label}.jsonld"

    extract_result = run_uofa(
        "extract", str(evidence_dir),
        "--model", model,
        "--pack", "nasa-7009b",
        "--output", str(xlsx),
    )
    assert extract_result.returncode == 0, (
        f"extract failed for {cou_label}:\n"
        f"STDOUT: {extract_result.stdout}\nSTDERR: {extract_result.stderr}"
    )
    assert xlsx.exists(), f"extract did not produce {xlsx}"

    import_result = run_uofa(
        "--pack", "nasa-7009b", "import", str(xlsx),
        "--output", str(jsonld),
    )
    assert import_result.returncode == 0, (
        f"import failed for {cou_label}:\n"
        f"STDOUT: {import_result.stdout}\nSTDERR: {import_result.stderr}"
    )
    assert jsonld.exists(), f"import did not produce {jsonld}"

    return xlsx, jsonld


# ── Mock variant: always runs in CI ───────────────────────────


@pytest.mark.skipif(not AERO_COU1_DIR.exists(), reason="aero-evidence-cou1 not available")
@pytest.mark.skipif(not AERO_COU2_DIR.exists(), reason="aero-evidence-cou2 not available")
class TestAeroFullPipelineE2EMock:
    """Plumbing-level e2e: verify every step in the chain completes.

    Does NOT assert semantic content — mock data is canned and doesn't
    reproduce the level-gap pattern needed to drive specific rule firings.
    See TestAeroFullPipelineE2ERealLLM for semantic assertions.
    """

    @pytest.fixture(scope="class")
    def chain(self, tmp_path_factory):
        """Extract + import both COUs once per class."""
        tmp = tmp_path_factory.mktemp("aero_e2e_mock")
        cou1_xlsx, cou1_jsonld = _extract_and_import(tmp, AERO_COU1_DIR, "cou1", "mock")
        cou2_xlsx, cou2_jsonld = _extract_and_import(tmp, AERO_COU2_DIR, "cou2", "mock")
        return {
            "tmp": tmp,
            "cou1_xlsx": cou1_xlsx, "cou1_jsonld": cou1_jsonld,
            "cou2_xlsx": cou2_xlsx, "cou2_jsonld": cou2_jsonld,
        }

    def test_extract_cou1_produces_19_factors(self, chain):
        import openpyxl
        from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES
        wb = openpyxl.load_workbook(chain["cou1_xlsx"])
        ws = wb["Credibility Factors"]
        found = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        nasa = [v for v in found if v in NASA_ALL_FACTOR_NAMES]
        assert len(nasa) == 19, f"COU1 has {len(nasa)} NASA factors, expected 19"

    def test_extract_cou2_produces_19_factors(self, chain):
        import openpyxl
        from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES
        wb = openpyxl.load_workbook(chain["cou2_xlsx"])
        ws = wb["Credibility Factors"]
        found = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        nasa = [v for v in found if v in NASA_ALL_FACTOR_NAMES]
        assert len(nasa) == 19, f"COU2 has {len(nasa)} NASA factors, expected 19"

    def test_imports_produce_valid_jsonld(self, chain):
        import json
        for label in ("cou1", "cou2"):
            doc = json.loads(chain[f"{label}_jsonld"].read_text())
            # Two minimum-viable checks: the v0.5 context is referenced
            # (so SHACL has shapes to bind against) and at least one
            # bindsRequirement is present (so the rule engine has something
            # to chain from). Don't assert optional fields that depend on
            # what the mock populates — `rules` and `diff` tests below
            # exercise the rest of the structure.
            assert "v0.5.jsonld" in str(doc.get("@context", "")), (
                f"{label}.jsonld missing v0.5 context")
            assert "bindsRequirement" in doc, (
                f"{label}.jsonld missing bindsRequirement")

    def test_rules_runs_on_cou1_without_crash(self, chain):
        result = run_uofa(
            "rules", str(chain["cou1_jsonld"]),
            "--pack", "nasa-7009b",
            "--build",
        )
        # Don't assert specific firings (mock data is canned); just that
        # the rule engine successfully consumed the imported JSON-LD.
        assert result.returncode == 0, (
            f"rules failed on cou1:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_rules_runs_on_cou2_without_crash(self, chain):
        result = run_uofa(
            "rules", str(chain["cou2_jsonld"]),
            "--pack", "nasa-7009b",
            "--build",
        )
        assert result.returncode == 0, (
            f"rules failed on cou2:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_diff_chains_both_cous_without_crash(self, chain):
        result = run_uofa(
            "diff", str(chain["cou1_jsonld"]), str(chain["cou2_jsonld"]),
            "--pack", "nasa-7009b",
            "--build",
        )
        # Diff exits non-zero when files diverge (semantic signal, not error)
        # and 0 when they're identical. With mock data both COUs get
        # identical canned content, so diff should be 0. Either way, no crash.
        assert result.returncode in (0, 1), (
            f"diff crashed unexpectedly (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )


# ── Real-LLM variant: gated by env var ────────────────────────


@pytest.mark.skipif(not REAL_LLM_ENABLED,
                    reason="set UOFA_RUN_REAL_LLM=1 to run real-LLM e2e")
@pytest.mark.skipif(not AERO_COU1_DIR.exists(), reason="aero-evidence-cou1 not available")
@pytest.mark.skipif(not AERO_COU2_DIR.exists(), reason="aero-evidence-cou2 not available")
class TestAeroFullPipelineE2ERealLLM:
    """Semantic e2e with a real LLM: asserts the NAFEMS divergence pattern.

    Expected outputs (the canonical NAFEMS-aero narrative):
      COU1 (Accepted, has level-gap factors)    → W-AR-02 fires N≥1 times
      COU2 (Not Accepted, no level-gap factors) → W-AR-02 fires 0 times
      diff(cou1, cou2)                           → reports non-zero divergence
    """

    @pytest.fixture(scope="class")
    def chain(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("aero_e2e_real")
        cou1_xlsx, cou1_jsonld = _extract_and_import(
            tmp, AERO_COU1_DIR, "cou1", "ollama/qwen3.5:4b")
        cou2_xlsx, cou2_jsonld = _extract_and_import(
            tmp, AERO_COU2_DIR, "cou2", "ollama/qwen3.5:4b")
        return {"tmp": tmp,
                "cou1_jsonld": cou1_jsonld, "cou2_jsonld": cou2_jsonld}

    def test_cou1_w_ar_02_fires(self, chain):
        from uofa_cli.commands.rules import parse_firings
        result = run_uofa(
            "rules", str(chain["cou1_jsonld"]),
            "--pack", "nasa-7009b", "--build",
        )
        assert result.returncode == 0
        firings = parse_firings(result.stdout)
        w_ar_02 = [f for f in firings if f["patternId"] == "W-AR-02"]
        assert len(w_ar_02) >= 1, (
            f"expected W-AR-02 to fire on COU1 (Accepted + level gaps); "
            f"got firings: {[f['patternId'] for f in firings]}"
        )

    def test_cou2_w_ar_02_stays_at_zero(self, chain):
        from uofa_cli.commands.rules import parse_firings
        result = run_uofa(
            "rules", str(chain["cou2_jsonld"]),
            "--pack", "nasa-7009b", "--build",
        )
        assert result.returncode == 0
        firings = parse_firings(result.stdout)
        w_ar_02 = [f for f in firings if f["patternId"] == "W-AR-02"]
        assert len(w_ar_02) == 0, (
            f"COU2 (Not Accepted) should not fire W-AR-02; got {len(w_ar_02)} firings"
        )

    def test_diff_shows_divergence(self, chain):
        result = run_uofa(
            "diff", str(chain["cou1_jsonld"]), str(chain["cou2_jsonld"]),
            "--pack", "nasa-7009b", "--build",
        )
        # Exit code 1 = files diverge (the expected semantic outcome here).
        assert result.returncode == 1, (
            f"expected divergence (rc=1); got rc={result.returncode}\n"
            f"STDOUT: {result.stdout}"
        )
        # Some weakener-related divergence keyword should appear.
        combined = result.stdout + result.stderr
        assert any(k in combined.lower() for k in
                   ("diverge", "weakener", "w-ar-02", "only in")), (
            f"diff output didn't mention divergence vocabulary:\n{combined}"
        )
