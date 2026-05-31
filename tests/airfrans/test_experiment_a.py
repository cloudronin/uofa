"""Experiment A harness tests (UofA_AirfRANS_Corpus_Harness_MiniSpec.md §4).

Fast guards (no engine): mechanical partition, error-gap arithmetic, no-LLM in
harness/, no-verdict report, no envelope leakage. One engine-gated synthetic E2E
runs the full interrogate→import→check→gap pipeline on a tiny AirfRANS-like
corpus and confirms the fired group has substantially higher true error, with
the AoA asymmetry visible.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness import datasets, error_gap, select_split, train_surrogate
from harness.datasets import Case

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return False
    return True


# ── Fast guards (no engine, no sklearn) ──────────────────────────────────────


def _table():
    # fired cases: mostly large error (high-AoA) + a couple small (low-AoA, the
    # asymmetry); unfired (in-envelope): small error.
    return [
        {"w_surr_03_fired": True, "err_cl": 0.5, "err_cd": 0.10, "pred_cl": 1.4, "pred_cd": 0.05},
        {"w_surr_03_fired": True, "err_cl": 0.6, "err_cd": 0.12, "pred_cl": 1.5, "pred_cd": 0.06},
        {"w_surr_03_fired": True, "err_cl": 0.02, "err_cd": 0.004, "pred_cl": -0.7, "pred_cd": 0.02},  # low-side fine
        {"w_surr_03_fired": False, "err_cl": 0.03, "err_cd": 0.005, "pred_cl": 0.8, "pred_cd": 0.02},
        {"w_surr_03_fired": False, "err_cl": 0.02, "err_cd": 0.004, "pred_cl": 0.9, "pred_cd": 0.02},
    ]


def test_partition_is_mechanical():
    fired, unfired = error_gap.partition(_table())
    assert len(fired) == 3 and len(unfired) == 2
    assert all(r["w_surr_03_fired"] for r in fired)
    assert not any(r["w_surr_03_fired"] for r in unfired)


def test_error_gap_is_pure_arithmetic():
    gap = error_gap.error_gap(_table())
    # fired Cd errors {0.10, 0.12, 0.004} → median 0.10; unfired {0.005, 0.004} → median 0.0045
    assert gap["coefficients"]["cd"]["fired"]["median"] == pytest.approx(0.10)
    assert gap["coefficients"]["cd"]["median_ratio"] > 5  # flagged error >> unflagged


def test_report_has_no_verdict_token():
    from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
    report = error_gap.render_report(_table()).lower()
    for token in FORBIDDEN_TOKENS:
        assert token.lower() not in report, f"gap report leaked verdict token {token!r}"
    assert "out-of-envelope inadequacy" in report  # the scoping sentence


def test_no_llm_import_in_harness_package():
    banned = ("litellm", "ollama", "qwen", "openai", "google.generativeai", "anthropic", "import llm")
    for src in (REPO_ROOT / "harness").glob("*.py"):
        text = src.read_text(encoding="utf-8").lower()
        for term in banned:
            assert term not in text, f"{src.name} references {term!r} — no LLM allowed in the harness"


def test_declared_envelope_does_not_leak_test_range():
    corpus = datasets.synthetic_task(seed=1, n_train=60, n_eval_high=10, n_eval_low=8)
    env = train_surrogate.declared_envelope(corpus.train)
    aoa_lo, aoa_hi = env["aoa"]
    high_aoa = [c.aoa for c in corpus.evaluation if c.aoa > aoa_hi]
    low_aoa = [c.aoa for c in corpus.evaluation if c.aoa < aoa_lo]
    # The declared envelope is the train extent; out-of-band eval points exist on
    # both sides and are NOT inside it (no test-range leakage).
    assert high_aoa and low_aoa
    assert aoa_hi < min(high_aoa) and aoa_lo > max(low_aoa)


# ── Engine-gated synthetic E2E (full interrogate→import→check→gap) ────────────


def _engine_available() -> bool:
    from uofa_cli import paths
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


@pytest.mark.skipif(not _engine_available(), reason="Jena engine (Java + JAR) not available")
def test_synthetic_corpus_produces_error_gap(tmp_path):
    from harness import run_corpus

    corpus = datasets.synthetic_task(seed=0, n_train=120, n_eval_in=5, n_eval_high=7, n_eval_low=4)
    trained = train_surrogate.train_and_save(corpus, tmp_path)
    rows = run_corpus.run_corpus(corpus, trained["model_path"], trained["envelope"], tmp_path)

    # Both groups present, partitioned by the REAL uofa check (W-SURR-03).
    fired = [r for r in rows if r["w_surr_03_fired"]]
    unfired = [r for r in rows if not r["w_surr_03_fired"]]
    assert fired and unfired, "need both fired and unfired cases for a gap"

    # W-SURR-03 fired iff the eval point is out-of-envelope (SIP's containment fact).
    for r in rows:
        assert r["w_surr_03_fired"] == (r["eval_point_in_envelope"] is False)

    # The hard number: flagged-case true error is substantially larger.
    gap = error_gap.error_gap(rows)
    ratio = gap["coefficients"]["cd"]["median_ratio"]
    assert ratio is not None and ratio > 2.0, f"expected a clear error gap, got {ratio}"

    # The report renders and stays verdict-free.
    from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
    report = error_gap.render_report(rows).lower()
    assert all(t.lower() not in report for t in FORBIDDEN_TOKENS)


# ── Split selection (Step 0) ─────────────────────────────────────────────────


def _split_rows(task, in_err, out_err, *, low_err=None):
    """Synthetic error-vs-parameter rows: in-envelope + out-of-envelope (high/low)."""
    rows = [{"task": task, "param": 5.0, "err_cl": in_err, "err_cd": in_err,
             "out_of_envelope": False, "side": "in"} for _ in range(6)]
    rows += [{"task": task, "param": 20.0, "err_cl": out_err, "err_cd": out_err,
              "out_of_envelope": True, "side": "high"} for _ in range(6)]
    if low_err is not None:
        rows += [{"task": task, "param": -10.0, "err_cl": low_err, "err_cd": low_err,
                  "out_of_envelope": True, "side": "low"} for _ in range(6)]
    return rows


def test_select_split_picks_largest_elevation_and_defaults_aoa():
    # AoA separates 10x, Reynolds only 3x → AoA chosen on the measurement, not the default.
    results = {"aoa": _split_rows("aoa", 0.01, 0.10), "reynolds": _split_rows("reynolds", 0.01, 0.03)}
    chosen, justification = select_split.choose(results)
    assert chosen == "aoa"
    assert "10.0x" in justification and "reynolds=3.0x" in justification

    # On a tie, AoA wins on physical-grounds default (the tiebreak, stated honestly).
    tied = {"aoa": _split_rows("aoa", 0.01, 0.05), "reynolds": _split_rows("reynolds", 0.01, 0.05)}
    assert select_split.choose(tied)[0] == "aoa"


def test_select_split_render_has_no_verdict_token():
    from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
    results = {"aoa": _split_rows("aoa", 0.01, 0.10, low_err=0.008),
               "reynolds": _split_rows("reynolds", 0.01, 0.03)}
    report = select_split.render(results).lower()
    for token in FORBIDDEN_TOKENS:
        assert token.lower() not in report, f"split report leaked verdict token {token!r}"


def test_select_split_reports_aoa_asymmetry_without_dropping_low_side():
    # High side degrades hard; low side stays fine — the honest asymmetry.
    rows = _split_rows("aoa", 0.01, 0.10, low_err=0.008)
    asym = select_split.aoa_asymmetry(rows)
    assert asym["high_side_cd_median"] > asym["low_side_cd_median"]
    assert asym["n_high"] == 6 and asym["n_low"] == 6  # low side counted, not dropped
    report = select_split.render({"aoa": rows}).lower()
    assert "asymmetry" in report
    # data-driven: high side is worse here, so the report must name the HIGH side
    assert "higher on the high-aoa side" in report
    assert "flagged-but-fine" in report  # better-side honesty stated in the report


def test_select_split_asymmetry_names_the_low_side_when_it_is_worse():
    # Inverted case (the REAL AirfRANS finding): low side degrades more. The
    # report must name the LOW side, not a hardcoded stall narrative.
    rows = _split_rows("aoa", 0.01, 0.02, low_err=0.09)  # low_err >> high_err
    report = select_split.render({"aoa": rows}).lower()
    assert "higher on the low-aoa side" in report
    # the asymmetry line must NOT invoke stall when the high side isn't the worse one
    # (the "(stall)" in the physical-grounds default justification is separate and fine)
    assert "toward stall" not in report
    assert "flagged-but-fine" in report


def test_asymmetry_slice_distinguishes_broad_from_thickness_driven():
    from harness import asymmetry_slice
    env = {"aoa": (0.0, 10.0), "reynolds": (3e6, 5e6)}
    thick = [8, 10, 12, 14, 16, 18, 20, 22, 24]

    def _rows(errs):
        return [{"w_surr_03_fired": True, "aoa": -5.0, "reynolds": 4e6, "g1": 2.0,
                 "g2": t, "err_cd": e, "err_cl": 0.2} for t, e in zip(thick, errs)]

    # BROAD: error hovers ~0.05 with no thickness trend → dropping the thickest
    # third barely moves the median.
    broad = _rows([0.050, 0.054, 0.047, 0.052, 0.049, 0.053, 0.046, 0.051, 0.048])
    db = asymmetry_slice.confound_diagnostic(asymmetry_slice.fired_by_side(broad, env, "aoa")["low"])
    assert abs(db["median_err_cd_all"] - db["median_err_cd_excl_thickest_third"]) / db["median_err_cd_all"] < 0.15

    # THICKNESS-DRIVEN: error rises monotonically with thickness → median collapses
    # when the thickest third is removed, and rank correlation is strong.
    driven = _rows([0.01 * t for t in thick])
    dd = asymmetry_slice.confound_diagnostic(asymmetry_slice.fired_by_side(driven, env, "aoa")["low"])
    assert dd["median_err_cd_excl_thickest_third"] < dd["median_err_cd_all"]
    assert dd["spearman_thickness_vs_err_cd"] > 0.8

    # render carries no verdict token
    from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
    report = asymmetry_slice.render(driven, env, param="aoa").lower()
    assert all(t.lower() not in report for t in FORBIDDEN_TOKENS)


@pytest.mark.skipif(not _sklearn_available(), reason="scikit-learn not installed")
def test_evaluate_task_degrades_out_of_envelope():
    corpus = datasets.synthetic_task(seed=3, n_train=120, n_eval_in=6, n_eval_high=8, n_eval_low=6)
    rows = select_split.evaluate_task(corpus)
    stats = select_split.out_of_envelope_stats(rows)["err_cd"]
    # The honest surrogate degrades outside the declared envelope.
    assert stats["out_median"] > stats["in_median"]
    assert stats["elevation"] is not None and stats["elevation"] > 1.5
    # Asymmetry is real in the synthetic physics: high side worse than low side.
    asym = select_split.aoa_asymmetry(rows)
    assert asym["high_side_cd_median"] >= asym["low_side_cd_median"]
