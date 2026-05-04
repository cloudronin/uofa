#!/usr/bin/env python3
"""Two-step Claude-driven generator for the synthetic extract eval corpus.

Per the implementation plan (and an explicit deviation from spec §3.4 which
proposes single-call co-emission): split generation into two API calls per
bundle.

  Step A — given (standard, domain, quality, format), generate 1-2 source
           documents (markdown prose, varied terminology and ordering)
  Step B — given the *generated source from Step A*, extract a canonical
           ground_truth.json conforming to the existing extract schema
           (assessment_summary + expected_factors).

Co-emission risks self-consistent hallucinations: model invents a factor in
the source, then writes the ground truth to match. Two-step lets Step B
operate on observable text only, eliminating that failure mode.

Cost: ~$0.30-0.50 per bundle on Sonnet 4.6 ($3/$15 per 1M tok). 50 bundles
≈ $20-30 + iteration overhead. --max-cost halts before exceeding the cap.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python dev/tools/scripts/generate_extract_corpus.py \
        --manifest tests/fixtures/extract_corpus/dev_manifest.json \
        --output-root tests/fixtures/extract_corpus/dev \
        --report runs/corpus_gen_dev_$(date +%Y%m%d_%H%M%S).json \
        --max-cost 40

    # Sanity run (1 bundle) before committing to the full set:
    python dev/tools/scripts/generate_extract_corpus.py ... --limit 1

    # See the plan without spending money:
    python dev/tools/scripts/generate_extract_corpus.py ... --dry-run

Idempotent: bundles whose source/, ground_truth.json, and metadata.json
already exist are skipped (resume after partial completion).
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from uofa_cli import excel_constants  # noqa: E402
from uofa_cli.adversarial.model_costs import estimate_cost  # noqa: E402
from uofa_cli.llm.backend import GenerationOptions  # noqa: E402
from uofa_cli.llm.litellm_backend import LiteLLMBackend  # noqa: E402


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PARALLEL = 3
DEFAULT_MAX_COST = 60.0
DEFAULT_TIMEOUT_S = 240.0


SOURCE_GENERATION_PROMPT = """\
You are generating a SYNTHETIC engineering credibility-assessment evidence
bundle for testing an LLM-based extraction pipeline. Output realistic
engineering prose that a human SME might produce; do NOT use canonical
factor terminology verbatim — vary phrasing, ordering, and depth so the
resulting bundle is a meaningful test of whether the extractor can find
the right concepts in real-language documents.

## Bundle parameters

- **Standard:** {standard} (the framework whose factors should be discoverable)
- **Domain:** {domain}
- **Quality:** {quality}
- **Format:** {format}

## What "quality" means

- `complete`: every factor in {standard} has clear, well-supported evidence
  in the document(s). A diligent human reviewer should be able to assign
  a defensible level (1-4) to each factor.
- `sparse`: roughly half the factors in {standard} have explicit evidence.
  The rest you must OMIT ENTIRELY from the source documents — do not
  mention them at all, not even in passing. Pick a realistic subset of
  4-7 factors to leave out (more for NASA-7009B's 19 factors). Engineers
  leave things out for reasons: out of scope for this phase, vendor data
  not available, deferred to next milestone, no time before review,
  competing priorities. The goal is for the GROUND-TRUTH extractor (you,
  in Step B) to mark those omitted factors `not_applicable`. If you only
  shorten descriptions but mention every factor, that's NOT sparse —
  that's just a shorter complete bundle.
- `ambiguous`: at least 3-4 factors have CONTRADICTORY or MISLEADING
  evidence (e.g., the document says one thing in §2 and another in §5;
  or the methodology described doesn't match the rigour level claimed).

## What "format" means

- `report-md`: a formal credibility assessment report. Sections such as:
  Background, Methodology, Results, Credibility, Limitations.
  Length: 1500-2500 words across 1-2 markdown files.
- `memo`: a shorter technical memo (300-700 words) addressed to a project
  lead, summarizing the V&V status. Less formal tone.
- `slides`: bullet-style slide notes (markdown formatted as nested bullets,
  one heading per slide). Roughly 8-15 slides' worth in one .md file.

## What "domain" means

- `cfd`: computational fluid dynamics (e.g., centrifugal pump, blood flow,
  HVAC duct, turbomachinery). Use vocabulary like turbulence model, RANS/LES,
  mesh convergence, residuals, GCI, boundary conditions.
- `fea`: finite-element analysis (e.g., structural frame, hip implant,
  bridge truss). Use vocabulary like mesh refinement, stress concentration,
  element formulation, contact mechanics, modal analysis.
- `cht`: coupled thermal-fluid / conjugate heat transfer (e.g., turbine
  blade cooling, electronics, reactor channel). Vocabulary spans both.

## Output format

Return your output in this EXACT delimited format (NOT JSON — JSON string
escaping breaks on multi-line markdown). Use plain literal text between
the delimiters; any characters including quotes, backslashes, and newlines
are fine.

===FILE START===
filename: report.md
<full markdown content for this file, multi-line OK>
===FILE END===

===FILE START===
filename: appendix.md
<content of second file, optional>
===FILE END===

===META START===
domain_hint: <single-line phrase identifying the specific scenario>
ambiguity_notes: <for quality=ambiguous, name the factors with contradictory evidence; otherwise leave blank on one line>
===META END===

Number of FILE blocks: 1 for `memo` and `slides`; 1 or 2 for `report-md`.
The META block is required and appears once at the end.

## Constraints

1. Vary terminology away from canonical factor names. Write
   "mesh refinement study" instead of "discretization error",
   "code verification" instead of "numerical code verification",
   "human factors review" instead of "use error", etc.
2. Vary the ORDER in which factors are addressed — don't go top-to-bottom
   of the {standard} factor list.
3. Make the prose specific. Mention real-sounding numbers, methodologies,
   and product names. The goal is to look like real engineering writing.
4. Do NOT include any structured data labelled with the canonical factor
   names. The extractor should have to find concepts, not labels.
5. For `quality=sparse`, make the omissions PLAUSIBLE — engineers leave
   things out for reasons (out of scope, deferred to next phase, vendor
   data not available).
6. For `quality=ambiguous`, make the contradictions REALISTIC — the kind
   of thing an SME would catch on careful reading but a quick skim might miss.

Generate the bundle now.
"""


GROUND_TRUTH_EXTRACTION_PROMPT = """\
You are reviewing a synthetic engineering credibility-assessment document
that was just generated. Your job is to produce the GROUND TRUTH for an
extraction-quality eval — the canonical answer the extractor will be
scored against.

The standard is {standard}, with these {n_factors} canonical factors:

{factor_list}

## Source documents

{source_documents}

## What to produce

Return JSON conforming exactly to this schema (no prose, no fences):

{{
  "case": "{bundle_id}",
  "pack": "{standard}",
  "assessment_summary": {{
    "project_name": "<short>",
    "cou_name": "<context of use>",
    "profile": "Complete" | "Partial" | "Minimal",
    "device_class": "Class I" | "Class II" | "Class III" | "N/A",
    "model_risk_level": "MRL 1" | "MRL 2" | "MRL 3" | "MRL 4",
    "assurance_level": "Low" | "Medium" | "High",
    "standards_reference": "<standard ref>",
    "has_uq": "Yes" | "No"
  }},
  "expected_factors": [
    {{
      "factor_type": "<exact canonical name from list above>",
      "expected_status": "assessed" | "not_applicable",
      "expected_level": 1 | 2 | 3 | 4,
      "level_tolerance": 1,
      "evidence_keywords": ["<3-6 distinctive words/phrases pulled from source>"],
      "source_file": "<filename in source/>"
    }}
  ]
}}

Include ONE entry per canonical factor. expected_factors length must equal {n_factors}.

## Rules

1. INCLUDE every canonical factor as an entry in expected_factors.
   Determine `expected_status` strictly from what is actually in the source:
   - `assessed`: the source contains substantive discussion of this factor
     (methodology described, results given, OR explicit claims about the
     factor being addressed). A passing one-line mention is NOT enough.
   - `not_applicable`: the source does not address this factor in any
     substantive way. This includes: the factor is never mentioned, OR
     the factor is mentioned only in a list/table-of-contents without
     content, OR the source explicitly says "out of scope". For
     `quality=sparse` bundles, EXPECT to mark 4-7 factors not_applicable
     (the bundle was generated specifically to omit them). If you find
     yourself marking 0 factors not_applicable on a sparse bundle, you
     are being too charitable — re-read and identify the omitted factors.
2. `expected_level` ∈ {{1, 2, 3, 4}} represents the credibility/rigour
   level a careful reviewer would assign. Calibrate strictly — most
   well-documented factors land at level 2, not level 4. Use these anchors:

   - **Level 1**: factor is mentioned but barely supported. Single sentence,
     no methodology described, no quantitative basis.
   - **Level 2**: standard practice with clear methodology described. THIS
     IS THE DEFAULT for well-documented factors. Examples: "we used SST
     k-omega and achieved residuals < 1e-5", "convergence was monitored
     and the run stopped when QoIs stabilized".
   - **Level 3**: above-standard rigor with explicit UQ or systematic
     sensitivity analysis. Example: GCI computed via Roache method;
     formal sensitivity sweep on inlet conditions; documented comparison
     against published benchmark.
   - **Level 4**: exhaustive validation including ALL OF: multi-method
     cross-validation, formal UQ propagation with quantified uncertainty,
     AND independent literature comparison. RARE — most factors in most
     real projects do NOT reach this level even when well-documented.

   For a `quality=complete` bundle, the realistic distribution is roughly
   60% at level 2, 30% at level 3, 10% at level 4. If you find yourself
   assigning level 4 to more than 2-3 factors, you are being too generous —
   downgrade the weaker ones to level 3 or 2. Compare your distribution
   against the existing real fixtures (Morrison case has factors mostly
   at level 2-3, only `Discretization error` at level 3).

3. `evidence_keywords` should be 3-6 phrases that appear LITERALLY in
   the source documents and would help a human reviewer find the
   relevant passage. Don't invent keywords — pull them from the source.
4. `source_file` should match the actual filename of the source document
   the evidence appears in.
5. For `quality=ambiguous` bundles, the ground truth should reflect what
   a CAREFUL reviewer would conclude after resolving the contradictions —
   not the most charitable reading. If the contradiction is unresolvable,
   choose the LOWER of the two possible levels.
6. For `expected_status: "not_applicable"`, set `expected_level: 1` and
   `evidence_keywords: []`.
7. Always include `"level_tolerance": 1` in each factor entry (the eval
   uses this to score within ±1 of expected_level as correct).
8. Do not output any text outside the JSON object.

Bundle metadata for context:
- bundle_id: {bundle_id}
- domain: {domain}
- quality: {quality}
- format: {format}

Now produce the ground truth.
"""


def _format_factor_list(factor_names: list[str]) -> str:
    return "\n".join(f"- {name}" for name in factor_names)


def _format_source_documents(files: list[dict]) -> str:
    parts = []
    for f in files:
        parts.append(f"### File: {f['name']}\n\n{f['content']}\n")
    return "\n---\n\n".join(parts)


def _make_backend(model: str) -> LiteLLMBackend:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set in environment.")
    return LiteLLMBackend(
        backend_name="anthropic",
        model_name=model,
        api_key=api_key,
        default_timeout_seconds=DEFAULT_TIMEOUT_S,
    )


def _approx_tokens(text: str) -> int:
    """Cheap token estimate: ~4 chars per token. Used for cost estimation."""
    return max(1, len(text) // 4)


def _parse_json_response(raw: str) -> dict:
    """Tolerantly parse Claude's JSON output. Strips ```json fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = lines[1:]  # drop opening ``` line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return json.loads(raw)


_FILE_BLOCK_RE = re.compile(
    r"===FILE START===\s*(.*?)\s*===FILE END===",
    re.DOTALL,
)
_META_BLOCK_RE = re.compile(
    r"===META START===\s*(.*?)\s*===META END===",
    re.DOTALL,
)
_FILENAME_RE = re.compile(r"^\s*filename:\s*(\S+)\s*\n(.*)$", re.DOTALL)


def _parse_step_a_response(raw: str) -> dict:
    """Parse Step A's delimiter-based output into {files, domain_hint, ambiguity_notes}.

    Format (literal text between markers, no JSON escaping):
        ===FILE START===
        filename: <name>
        <content>
        ===FILE END===
        ... more FILE blocks ...
        ===META START===
        domain_hint: <line>
        ambiguity_notes: <line or multi-line, ends at META END>
        ===META END===
    """
    files: list[dict] = []
    for block in _FILE_BLOCK_RE.findall(raw):
        m = _FILENAME_RE.match(block)
        if not m:
            raise ValueError(f"FILE block missing 'filename:' header: {block[:100]!r}")
        files.append({"name": m.group(1).strip(), "content": m.group(2).rstrip() + "\n"})

    if not files:
        raise ValueError("no FILE blocks found in Step A response")

    domain_hint = ""
    ambiguity_notes = ""
    meta_match = _META_BLOCK_RE.search(raw)
    if meta_match:
        meta_text = meta_match.group(1)
        # Split on the field markers; allow ambiguity_notes to span multiple lines
        m_dh = re.search(r"^\s*domain_hint:\s*(.*?)(?=\n\s*ambiguity_notes:|\Z)",
                         meta_text, re.DOTALL | re.MULTILINE)
        m_an = re.search(r"^\s*ambiguity_notes:\s*(.*)$", meta_text, re.DOTALL | re.MULTILINE)
        if m_dh:
            domain_hint = m_dh.group(1).strip()
        if m_an:
            ambiguity_notes = m_an.group(1).strip()

    return {"files": files, "domain_hint": domain_hint, "ambiguity_notes": ambiguity_notes}


def _failed(bundle_id: str, started: datetime, error: str) -> dict:
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return {
        "bundle_id": bundle_id, "status": "failed",
        "tokens_in": 0, "tokens_out": 0, "cost_estimate_usd": 0.0,
        "elapsed_s": elapsed, "error": error,
    }


def generate_one_bundle(
    bundle_spec: dict,
    backend: LiteLLMBackend,
    output_root: Path,
    pack_to_factors: dict[str, list[str]],
    raw_dir: Path | None = None,
) -> dict:
    """Generate (or skip) one bundle. Returns a per-bundle generation report.

    If `raw_dir` is set, the raw Step A and Step B response strings are
    written to `<raw_dir>/<bundle_id>_step_{a,b}.txt` for debugging
    parser issues (e.g., META block format drift).
    """
    bundle_id = bundle_spec["id"]
    bundle_dir = output_root / bundle_id
    src_dir = bundle_dir / "source"
    gt_path = bundle_dir / "ground_truth.json"
    md_path = bundle_dir / "metadata.json"

    started = datetime.now(timezone.utc)
    if src_dir.is_dir() and gt_path.exists() and md_path.exists():
        return {
            "bundle_id": bundle_id, "status": "skipped",
            "tokens_in": 0, "tokens_out": 0, "cost_estimate_usd": 0.0,
            "elapsed_s": 0.0,
        }

    standard = bundle_spec["standard"]
    domain = bundle_spec["domain"]
    quality = bundle_spec["quality"]
    fmt = bundle_spec["format"]
    factor_names = pack_to_factors[standard]

    # ----- Step A: source generation -----
    step_a_prompt = SOURCE_GENERATION_PROMPT.format(
        standard=standard, domain=domain, quality=quality, format=fmt,
    )
    options_a = GenerationOptions(temperature=0.7, max_tokens=8192)
    try:
        step_a_response = backend.generate(step_a_prompt, options_a)
    except Exception as exc:  # noqa: BLE001
        return _failed(bundle_id, started, f"step-A backend error: {exc}")

    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{bundle_id}_step_a.txt").write_text(step_a_response)

    try:
        step_a_data = _parse_step_a_response(step_a_response)
        files = step_a_data["files"]
    except Exception as exc:  # noqa: BLE001
        return _failed(bundle_id, started, f"step-A parse error: {exc}")

    # ----- Step B: ground-truth extraction -----
    step_b_prompt = GROUND_TRUTH_EXTRACTION_PROMPT.format(
        standard=standard,
        n_factors=len(factor_names),
        factor_list=_format_factor_list(factor_names),
        source_documents=_format_source_documents(files),
        bundle_id=bundle_id,
        domain=domain,
        quality=quality,
        format=fmt,
    )
    options_b = GenerationOptions(temperature=0.2, max_tokens=8192)
    try:
        step_b_response = backend.generate(step_b_prompt, options_b)
    except Exception as exc:  # noqa: BLE001
        return _failed(bundle_id, started, f"step-B backend error: {exc}")

    if raw_dir is not None:
        (raw_dir / f"{bundle_id}_step_b.txt").write_text(step_b_response)

    try:
        ground_truth = _parse_json_response(step_b_response)
        if "expected_factors" not in ground_truth:
            raise ValueError("ground_truth missing expected_factors")
        gt_factor_count = len(ground_truth["expected_factors"])
        if gt_factor_count != len(factor_names):
            raise ValueError(
                f"expected_factors length {gt_factor_count} != "
                f"{len(factor_names)} canonical factors for {standard}"
            )
    except Exception as exc:  # noqa: BLE001
        return _failed(bundle_id, started, f"step-B parse error: {exc}")

    # ----- Write artifacts -----
    src_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        (src_dir / f["name"]).write_text(f["content"])
    gt_path.write_text(json.dumps(ground_truth, indent=2))
    md_path.write_text(json.dumps({
        **bundle_spec,
        "generated_at": started.isoformat(),
        "model": backend.model_name,
        "domain_hint": step_a_data.get("domain_hint"),
        "ambiguity_notes": step_a_data.get("ambiguity_notes", ""),
    }, indent=2))

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    tokens_in = _approx_tokens(step_a_prompt) + _approx_tokens(step_b_prompt)
    tokens_out = _approx_tokens(step_a_response) + _approx_tokens(step_b_response)
    total_tokens = tokens_in + tokens_out
    cost = estimate_cost(
        backend.model_name,
        total_tokens,
        output_ratio=tokens_out / max(1, total_tokens),
    )
    return {
        "bundle_id": bundle_id,
        "status": "generated",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate_usd": cost,
        "elapsed_s": elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", type=Path, required=True,
                        help="Path to {dev,test}_manifest.json")
    parser.add_argument("--output-root", type=Path, required=True,
                        help="Output corpus dir (e.g. tests/fixtures/extract_corpus/dev)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Anthropic model id (default: {DEFAULT_MODEL})")
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL,
                        help=f"Concurrent bundles (default: {DEFAULT_PARALLEL})")
    parser.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST,
                        help=f"Halt before total estimated cost exceeds USD (default: {DEFAULT_MAX_COST})")
    parser.add_argument("--limit", type=int, default=None,
                        help="Generate only the first N bundles (sanity runs)")
    parser.add_argument("--report", type=Path, default=None,
                        help="Path to write a JSON generation report")
    parser.add_argument("--save-raw", type=Path, default=None,
                        help="Directory to dump raw Step A/B responses for debugging")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the bundle plan without making API calls")
    args = parser.parse_args()

    if not args.manifest.exists():
        raise SystemExit(f"Manifest not found: {args.manifest}")
    manifest = json.loads(args.manifest.read_text())
    bundles = manifest["bundles"]
    if args.limit:
        bundles = bundles[: args.limit]

    pack_to_factors = {
        "vv40": list(excel_constants.VV40_FACTOR_NAMES),
        "nasa-7009b": list(excel_constants.NASA_ALL_FACTOR_NAMES),
    }

    if args.dry_run:
        print(f"DRY RUN: would generate {len(bundles)} bundles into {args.output_root}")
        for b in bundles:
            already = (args.output_root / b["id"] / "ground_truth.json").exists()
            mark = "  [would skip — already exists]" if already else ""
            print(f"  {b['id']:30s} {b['standard']:12s} {b['domain']:5s} "
                  f"{b['quality']:10s} {b['format']:12s}{mark}")
        return 0

    backend = _make_backend(args.model)
    args.output_root.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(bundles)} bundles into {args.output_root}")
    print(f"Model: {args.model}  ·  parallel={args.parallel}  ·  max_cost=${args.max_cost:.2f}")

    accumulated_cost = 0.0
    reports: list[dict] = []
    halted = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(
                generate_one_bundle, b, backend, args.output_root, pack_to_factors, args.save_raw,
            ): b
            for b in bundles
        }
        for future in concurrent.futures.as_completed(futures):
            b = futures[future]
            try:
                rep = future.result()
            except concurrent.futures.CancelledError:
                continue
            except Exception as exc:  # noqa: BLE001
                rep = {
                    "bundle_id": b["id"], "status": "failed", "error": str(exc),
                    "tokens_in": 0, "tokens_out": 0,
                    "cost_estimate_usd": 0.0, "elapsed_s": 0.0,
                }
            reports.append(rep)
            accumulated_cost += rep["cost_estimate_usd"]
            tag = rep["status"].upper()
            print(f"  [{len(reports)}/{len(bundles)}] {rep['bundle_id']:32s} {tag:9s} "
                  f"(${rep['cost_estimate_usd']:.3f}, total ${accumulated_cost:.2f})")
            if rep["status"] == "failed":
                print(f"      error: {rep.get('error')}")
            if accumulated_cost >= args.max_cost and not halted:
                print(f"\n!! --max-cost ${args.max_cost:.2f} reached. Cancelling pending bundles.")
                halted = True
                for f in futures:
                    if not f.done():
                        f.cancel()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(args.manifest),
        "output_root": str(args.output_root),
        "model": args.model,
        "n_total": len(bundles),
        "n_generated": sum(1 for r in reports if r["status"] == "generated"),
        "n_skipped":   sum(1 for r in reports if r["status"] == "skipped"),
        "n_failed":    sum(1 for r in reports if r["status"] == "failed"),
        "total_cost_estimate_usd": round(accumulated_cost, 4),
        "halted_at_max_cost": halted,
        "reports": reports,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2))
        print(f"\nReport: {args.report}")
    print(f"\nGenerated: {summary['n_generated']}  Skipped: {summary['n_skipped']}  Failed: {summary['n_failed']}")
    print(f"Total estimated cost: ${accumulated_cost:.2f}")

    return 0 if summary["n_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
