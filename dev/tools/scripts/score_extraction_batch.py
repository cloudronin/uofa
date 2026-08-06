#!/usr/bin/env python3
"""Batch-score the extract pipeline against a synthetic eval corpus.

Wraps score_extraction.py functions to iterate over a corpus directory of
bundles produced by generate_extract_corpus.py. Computes per-bundle and
per-factor F1, plus a failure-mode catalog for triage.

Usage:
    # Dev set (during iteration)
    python dev/tools/scripts/score_extraction_batch.py \
        --corpus tests/fixtures/extract_corpus/dev \
        --model ollama/qwen3.5:4b \
        --prompt-version v4-iter-1 \
        --output runs/extract_eval_$(date +%Y%m%d_%H%M%S).json

    # Test set (one-shot, after prompt freeze) — guarded
    python dev/tools/scripts/score_extraction_batch.py \
        --corpus tests/fixtures/extract_corpus/test \
        --model ollama/qwen3.5:4b \
        --prompt-version v4-frozen \
        --output runs/test_eval.json \
        --allow-test

Test-set guards (spec §5.3):
    1. .test_set_lock sentinel in the corpus dir requires --allow-test.
    2. --prompt-version must contain neither 'iter' nor 'dev' if --allow-test.
    3. Manifest's "split" field must equal "test" for --allow-test paths.

Per-bundle pipeline mirrors score_extraction.py: extract -> parse xlsx ->
factor scoring. Crash isolation: a bundle that fails extraction is recorded
in `crashes` and the loop continues.
"""

import argparse
import json
import re
import sys
import tempfile
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from schema_coverage import (  # noqa: E402
    SchemaCoverage,
    score_schema_coverage,
    validate_extracted,
)
from groundedness import (  # noqa: E402
    GroundednessResult,
    read_source_text,
    score_factor_rationales,
)
from score_extraction import (  # noqa: E402
    _ROOT,
    parse_extracted_xlsx,
    resolve_bundle,
    run_extraction,
    score_factors,
)

# Fields summed when rolling per-bundle groundedness up to the corpus. Ratios
# are recomputed from the totals rather than averaged over bundles: a bundle
# contributing two claims should not weigh the same as one contributing thirty.
_GROUNDEDNESS_COUNTERS = ("factors_total", "factors_with_rationale",
                          "rationales_with_claims", "claims_total", "claims_grounded")


# Pattern that disqualifies a prompt version from running against the test set.
# Matches "iter" or "dev" anywhere in the version string, case-insensitive.
_DEV_VERSION_PATTERN = re.compile(r"(iter|dev)", re.IGNORECASE)


def load_manifest(corpus_dir: Path) -> dict:
    """Load `<corpus_dir>/{dev,test}_manifest.json`. Falls back to scanning the dir."""
    for split in ("dev", "test"):
        candidate = corpus_dir.parent / f"{split}_manifest.json"
        if candidate.exists() and candidate.parent.joinpath(split) == corpus_dir:
            return json.loads(candidate.read_text())
    raise SystemExit(
        f"No matching manifest for {corpus_dir}. "
        f"Expected one of: {corpus_dir.parent}/dev_manifest.json or test_manifest.json"
    )


def enforce_test_set_guard(corpus_dir: Path, manifest: dict, prompt_version: str, allow_test: bool) -> None:
    """Refuse to score the test set unless explicit guards are satisfied.

    Three checks (any failure aborts):
    1. If the corpus dir contains .test_set_lock, --allow-test must be set.
    2. If --allow-test is set, prompt_version must not match 'iter' or 'dev'.
    3. If --allow-test is set, manifest['split'] must equal 'test'.
    """
    sentinel = corpus_dir / ".test_set_lock"
    if sentinel.exists() and not allow_test:
        raise SystemExit(
            f"Refusing to score corpus {corpus_dir}: .test_set_lock present. "
            f"Pass --allow-test to score the held-out test set (use only after prompt freeze)."
        )
    if allow_test:
        if _DEV_VERSION_PATTERN.search(prompt_version):
            raise SystemExit(
                f"Refusing to score test set with prompt version {prompt_version!r}. "
                f"Test set must only be scored against frozen prompts (no 'iter' or 'dev' in version)."
            )
        if manifest.get("split") != "test":
            raise SystemExit(
                f"--allow-test requested but manifest split is {manifest.get('split')!r}, not 'test'."
            )


def score_factors_with_confusion(
    extracted_factors: list,
    ground_truth_factors: list,
    factor_names: list[str],
) -> dict:
    """Extend score_factors() with confusion analysis.

    Returns the same dict score_factors() returns, plus:
        - false_positives: list[str] — factor types extracted but absent from GT
        - missed_factors: list[str] — factor types in GT but not extracted
        - level_mismatches: list[{factor, expected, got, delta}]
        - status_mismatches: list[{factor, expected, got}]
        - failure_modes: list[(mode, factor_type)] flattened tuples for Counter aggregation
    """
    base = score_factors(extracted_factors, ground_truth_factors)

    extracted_types = {f.get("factor_type", "") for f in extracted_factors}
    gt_types_assessed = {f["factor_type"] for f in ground_truth_factors if f.get("expected_status") == "assessed"}
    gt_types_all = {f["factor_type"] for f in ground_truth_factors}

    # FP: extracted factors that aren't in GT at all (hallucination), or
    # extracted as "assessed" when GT marked "not_applicable" (mis-status).
    false_positives = sorted(t for t in extracted_types if t and t not in gt_types_all)
    missed_factors = sorted(gt_types_assessed - extracted_types)

    level_mismatches = []
    status_mismatches = []
    for gt_type, fr in base["per_factor"].items():
        if fr.get("status") != "FOUND":
            continue
        if fr.get("level_match") is False:
            level_mismatches.append({
                "factor": gt_type,
                "detail": fr.get("level_detail", ""),
            })
        if fr.get("status_match") is False:
            status_mismatches.append({"factor": gt_type})

    failure_modes = []
    for ft in missed_factors:
        failure_modes.append(("missed", ft))
    for ft in false_positives:
        failure_modes.append(("hallucinated", ft))
    for lm in level_mismatches:
        failure_modes.append(("level_mismatch", lm["factor"]))
    for sm in status_mismatches:
        failure_modes.append(("status_mismatch", sm["factor"]))

    base["false_positives"] = false_positives
    base["missed_factors"] = missed_factors
    base["level_mismatches"] = level_mismatches
    base["status_mismatches"] = status_mismatches
    base["failure_modes"] = failure_modes
    return base


def score_bundle(
    bundle_dir: Path,
    model: str,
    pack_override: str | None,
    skip_extract: bool,
) -> dict:
    """Score one bundle. Returns a per-bundle result record."""
    source_dir, gt_path, factor_names, metadata = resolve_bundle(bundle_dir, pack=pack_override)
    pack = pack_override or metadata.get("standard")
    ground_truth = json.loads(gt_path.read_text())
    # Ground truth schema (matches Morrison/aero fixtures): expected_factors is
    # the authoritative key. Older synthetic bundles may use `credibility_factors`;
    # accept both for forward compat.
    gt_factors = ground_truth.get("expected_factors") or ground_truth.get("credibility_factors", [])

    record = {
        "bundle_id": bundle_dir.name,
        "metadata": metadata,
        "pack": pack,
    }

    xlsx_path = bundle_dir / "extracted.xlsx"
    if not skip_extract:
        with tempfile.TemporaryDirectory() as td:
            tmp_xlsx = Path(td) / "extracted.xlsx"
            ok = run_extraction(model, source_dir, tmp_xlsx, pack=pack)
            if not ok:
                record["crashed"] = True
                record["error"] = "extraction failed (see stderr)"
                return record
            tmp_xlsx.replace(xlsx_path)
    elif not xlsx_path.exists():
        record["crashed"] = True
        record["error"] = f"--skip-extract set but {xlsx_path} missing"
        return record

    try:
        extracted = parse_extracted_xlsx(xlsx_path, factor_names)
    except Exception as exc:  # noqa: BLE001
        record["crashed"] = True
        record["error"] = f"parse failed: {exc}"
        record["traceback"] = traceback.format_exc()
        return record

    factor_score = score_factors_with_confusion(
        extracted.get("credibility_factors", []),
        gt_factors,
        factor_names,
    )
    record["factor_score"] = factor_score
    record["overall_f1"] = factor_score["overall_f1"]

    # Schema coverage and SHACL validity, scored on every run.
    #
    # For a year this function scored `hasCredibilityFactor` and stopped, so the
    # headline F1 described one of the thirteen properties ProfileComplete
    # requires -- on a metric a zero-parameter constant reaches 0.960 on. Nobody
    # had run the project's own validator over the output either; when finally
    # run, 37 of 45 packages failed it.
    #
    # Neither of these needs ground truth, so both run on any corpus, and both
    # would have caught that gap for free.
    record["schema_coverage"] = score_schema_coverage(extracted, pack)
    conforms, findings = validate_extracted(xlsx_path, pack)
    record["shacl_conforms"] = conforms
    record["shacl_findings"] = findings

    # Groundedness is scored on every run, and it is the only metric here that a
    # constant function cannot reach: the checklist control scores F1 0.960
    # having read nothing, but it cannot cite a figure from the document.
    # Failures are recorded rather than raised -- a bundle with no readable
    # source should cost its groundedness row, not the whole run's F1.
    try:
        grounded = score_factor_rationales(
            extracted.get("credibility_factors", []), read_source_text(bundle_dir))
        record["groundedness"] = grounded.as_dict()
        record["ungrounded"] = grounded.ungrounded
    except SystemExit as exc:
        record["groundedness_error"] = str(exc)
    return record


def aggregate(per_bundle: list[dict], factor_names: list[str]) -> dict:
    """Aggregate per-bundle results into per-factor stats and a failure-mode catalog."""
    crashed = [r for r in per_bundle if r.get("crashed")]
    scored = [r for r in per_bundle if not r.get("crashed")]

    bundle_f1 = [r["overall_f1"] for r in scored]

    # Per-factor stats: across all bundles where the factor appears in GT,
    # how often was it detected? (Per-factor recall.)
    factor_gt_count: Counter = Counter()
    factor_found_count: Counter = Counter()
    factor_level_correct: Counter = Counter()
    factor_status_correct: Counter = Counter()
    for r in scored:
        for ft, fr in r["factor_score"]["per_factor"].items():
            factor_gt_count[ft] += 1
            if fr.get("status") == "FOUND":
                factor_found_count[ft] += 1
                if fr.get("level_match"):
                    factor_level_correct[ft] += 1
                if fr.get("status_match"):
                    factor_status_correct[ft] += 1

    per_factor = {}
    for ft in factor_names:
        n = factor_gt_count[ft]
        per_factor[ft] = {
            "gt_appearances": n,
            "detected": factor_found_count[ft],
            "detection_rate": factor_found_count[ft] / n if n else None,
            "level_correct": factor_level_correct[ft],
            "level_accuracy": factor_level_correct[ft] / factor_found_count[ft] if factor_found_count[ft] else None,
            "status_correct": factor_status_correct[ft],
        }

    # Failure-mode catalog: rank (mode, factor) by frequency
    mode_counter: Counter = Counter()
    for r in scored:
        for mode, ft in r["factor_score"].get("failure_modes", []):
            mode_counter[(mode, ft)] += 1

    top_modes = [
        {"mode": m, "factor": ft, "count": c}
        for (m, ft), c in mode_counter.most_common(20)
    ]

    schema = SchemaCoverage()
    for r in scored:
        cov = r.get("schema_coverage") or {}
        if not cov:
            continue
        schema.bundles += 1
        for prop, ok in cov.items():
            if ok:
                schema.populated[prop] = schema.populated.get(prop, 0) + 1
        conforms = r.get("shacl_conforms")
        if conforms is None:
            continue
        findings = r.get("shacl_findings") or []
        schema.validated += 1
        if conforms:
            schema.conforms += 1
            if not any(f.startswith("placeholder") for f in findings):
                schema.placeholder_free += 1
        for f in findings:
            schema.violations[f] = schema.violations.get(f, 0) + 1

    grounded = GroundednessResult()
    for r in scored:
        g = r.get("groundedness")
        if not g:
            continue
        for k in _GROUNDEDNESS_COUNTERS:
            setattr(grounded, k, getattr(grounded, k) + g[k])
        grounded.ungrounded += r.get("ungrounded", [])

    return {
        "n_bundles": len(per_bundle),
        "n_scored": len(scored),
        "n_crashed": len(crashed),
        "mean_overall_f1": sum(bundle_f1) / len(bundle_f1) if bundle_f1 else None,
        "groundedness": grounded.as_dict(),
        "ungrounded": grounded.ungrounded,
        "schema": schema.as_dict(),
        "min_overall_f1": min(bundle_f1) if bundle_f1 else None,
        "max_overall_f1": max(bundle_f1) if bundle_f1 else None,
        "per_factor": per_factor,
        "top_failure_modes": top_modes,
        "crashes": [
            {"bundle_id": r["bundle_id"], "error": r.get("error"), "traceback": r.get("traceback")}
            for r in crashed
        ],
    }


def write_markdown_summary(out_path: Path, header: dict, agg: dict) -> None:
    lines = []
    lines.append(f"# Extract Eval — {header['prompt_version']} on {header['corpus_dir']}\n")
    lines.append(f"**Run:** {header['run_at']} · **Model:** {header['model']}\n")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Bundles: {agg['n_scored']} scored / {agg['n_crashed']} crashed / {agg['n_bundles']} total")
    if agg["mean_overall_f1"] is not None:
        lines.append(f"- Mean overall F1: **{agg['mean_overall_f1']:.3f}** (min {agg['min_overall_f1']:.3f}, max {agg['max_overall_f1']:.3f})")
    lines.append("")

    s = agg.get("schema") or {}
    if s.get("bundles"):
        lines.append("## Schema coverage and validity")
        lines.append("")
        lines.append("The detection F1 above describes `hasCredibilityFactor`. ProfileComplete")
        lines.append("requires thirteen properties. These are the rest.")
        lines.append("")
        lines.append("| Required property | Populated | |")
        lines.append("|---|---:|---|")
        for prop, n in sorted(s["populated"].items()):
            lines.append(f"| `{prop}` | {n}/{s['bundles']} | {n/s['bundles']:.0%} |")
        lines.append("")
        if s.get("validated"):
            lines.append(f"- SHACL conformance: **{s['conforms']}/{s['validated']}** "
                         f"({s['validity_rate']:.0%})")
            lines.append(f"- Conforming *and* free of template placeholders: "
                         f"**{s['placeholder_free']}/{s['validated']}** "
                         f"({s['meaningful_rate']:.0%})")
            lines.append("")
            lines.append("Reported as two rates, never merged: a package that fails the shape is")
            lines.append("not a credibility artefact, and one that passes by echoing the template")
            lines.append("is not either — but nothing downstream can tell them apart.")
            lines.append("")
            if s.get("violations_by_field"):
                lines.append("| Finding | Count |")
                lines.append("|---|---:|")
                for f, c in sorted(s["violations_by_field"].items(), key=lambda kv: -kv[1]):
                    lines.append(f"| `{f}` | {c} |")
                lines.append("")

    g = agg.get("groundedness") or {}
    if g.get("factors_total"):
        lines.append("## Rationale groundedness")
        lines.append("")
        lines.append("Detection F1 above is reachable by a function that reads no input — the")
        lines.append("pack's checklist scores 0.960. These three are not: citing a figure from")
        lines.append("the document requires having read it.")
        lines.append("")
        lines.append("| | | |")
        lines.append("|---|---:|---|")
        lines.append(f"| Coverage | **{g['coverage']:.3f}** | "
                     f"{g['factors_with_rationale']}/{g['factors_total']} factors given a rationale |")
        lines.append(f"| Claim density | **{g['claim_density']:.3f}** | "
                     f"{g['rationales_with_claims']}/{g['factors_with_rationale']} carry a checkable claim |")
        lines.append(f"| Groundedness | **{g['groundedness']:.3f}** | "
                     f"{g['claims_grounded']}/{g['claims_total']} claims trace to source |")
        lines.append("")
        lines.append(f"Ungrounded rationales: **{len(agg.get('ungrounded', []))}**. "
                     "Read all three together — coverage 0 means the method wrote nothing, "
                     "high coverage with low density means it wrote filler, and high density "
                     "with low groundedness means it wrote confident fiction.")
        lines.append("")
        lines.append("Measures **fabrication, not attribution**: a real figure cited under the "
                     "wrong factor scores as grounded. Sign is not checked.")
        lines.append("")
    lines.append("## Per-factor detection rate")
    lines.append("")
    lines.append("| Factor | GT appearances | Detected | Rate | Level acc |")
    lines.append("|---|---:|---:|---:|---:|")
    for ft, stats in agg["per_factor"].items():
        rate = f"{stats['detection_rate']:.2f}" if stats["detection_rate"] is not None else "—"
        lacc = f"{stats['level_accuracy']:.2f}" if stats["level_accuracy"] is not None else "—"
        lines.append(f"| {ft} | {stats['gt_appearances']} | {stats['detected']} | {rate} | {lacc} |")
    lines.append("")
    lines.append("## Top 10 failure modes")
    lines.append("")
    lines.append("| Rank | Mode | Factor | Count |")
    lines.append("|---:|---|---|---:|")
    for i, m in enumerate(agg["top_failure_modes"][:10], 1):
        lines.append(f"| {i} | {m['mode']} | {m['factor']} | {m['count']} |")
    if agg["crashes"]:
        lines.append("")
        lines.append("## Crashes")
        lines.append("")
        for c in agg["crashes"]:
            lines.append(f"- **{c['bundle_id']}**: {c['error']}")
    lines.append("")
    out_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--corpus", type=Path, required=True, help="Corpus directory (e.g. tests/fixtures/extract_corpus/dev)")
    parser.add_argument("--model", default="ollama/qwen3.5:4b", help="LLM model spec (litellm format)")
    parser.add_argument("--prompt-version", required=True, help="Prompt version tag for logging (avoid 'iter'/'dev' if --allow-test)")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the JSON results")
    parser.add_argument("--markdown-summary", type=Path, default=None, help="Optional: also write a markdown summary")
    parser.add_argument("--pack-filter", default=None, help="Only score bundles whose standard matches this pack (vv40 | nasa-7009b)")
    parser.add_argument("--max-bundles", type=int, default=None, help="Limit to N bundles for sanity runs")
    parser.add_argument("--skip-extract", action="store_true", help="Use existing extracted.xlsx in each bundle (don't re-run model)")
    parser.add_argument("--allow-test", action="store_true", help="Required to score the test set (sentinel-locked)")
    args = parser.parse_args()

    corpus_dir = args.corpus.resolve()
    if not corpus_dir.is_dir():
        raise SystemExit(f"Corpus dir not found: {corpus_dir}")

    manifest = load_manifest(corpus_dir)
    enforce_test_set_guard(corpus_dir, manifest, args.prompt_version, args.allow_test)

    bundles_to_score = manifest["bundles"]
    if args.pack_filter:
        bundles_to_score = [b for b in bundles_to_score if b["standard"] == args.pack_filter]
    if args.max_bundles:
        bundles_to_score = bundles_to_score[: args.max_bundles]

    if not bundles_to_score:
        raise SystemExit(f"No bundles to score in {corpus_dir} after filters")

    # Load factor names per pack so the aggregator knows what to report on
    from uofa_cli import excel_constants  # noqa: WPS433
    pack_factors = {
        "vv40": list(excel_constants.VV40_FACTOR_NAMES),
        "nasa-7009b": list(excel_constants.NASA_ALL_FACTOR_NAMES),
    }
    union_factors = sorted(set(pack_factors["vv40"]) | set(pack_factors["nasa-7009b"]))

    run_at = datetime.now(timezone.utc).isoformat()
    print(f"[{run_at}] Scoring {len(bundles_to_score)} bundles from {corpus_dir}")
    print(f"  Model: {args.model}  ·  Prompt: {args.prompt_version}")

    per_bundle = []
    for i, b in enumerate(bundles_to_score, 1):
        bundle_dir = corpus_dir / b["id"]
        if not bundle_dir.is_dir():
            per_bundle.append({"bundle_id": b["id"], "crashed": True, "error": "bundle dir missing"})
            print(f"  [{i}/{len(bundles_to_score)}] {b['id']}: MISSING")
            continue
        try:
            r = score_bundle(bundle_dir, args.model, b["standard"], args.skip_extract)
        except Exception as exc:  # noqa: BLE001
            r = {"bundle_id": b["id"], "crashed": True, "error": str(exc), "traceback": traceback.format_exc()}
        per_bundle.append(r)
        f1 = r.get("overall_f1")
        status = "CRASH" if r.get("crashed") else f"F1={f1:.3f}" if f1 is not None else "scored"
        print(f"  [{i}/{len(bundles_to_score)}] {b['id']}: {status}")

    agg = aggregate(per_bundle, union_factors)

    output = {
        "run_at": run_at,
        "model": args.model,
        "prompt_version": args.prompt_version,
        "corpus_dir": str(corpus_dir.relative_to(_ROOT)) if str(corpus_dir).startswith(str(_ROOT)) else str(corpus_dir),
        "manifest_split": manifest.get("split"),
        "n_bundles_in_manifest": len(manifest["bundles"]),
        "pack_filter": args.pack_filter,
        "skip_extract": args.skip_extract,
        "aggregate": agg,
        "per_bundle": per_bundle,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults written to {args.output}")

    if args.markdown_summary:
        args.markdown_summary.parent.mkdir(parents=True, exist_ok=True)
        write_markdown_summary(args.markdown_summary, output, agg)
        print(f"Markdown summary written to {args.markdown_summary}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
