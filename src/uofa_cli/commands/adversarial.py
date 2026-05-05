"""uofa adversarial — generate, run, and analyze synthetic credibility
evidence packages for Phase 2 coverage experiments."""

from __future__ import annotations

from pathlib import Path

HELP = "generate / orchestrate / classify synthetic credibility evidence packages"


def add_arguments(parser):
    sub = parser.add_subparsers(
        dest="adversarial_command",
        title="adversarial commands",
        metavar="{generate,run,analyze,prep-review,bundle,judge,triage,adjudicate}",
    )

    # ----- generate (Phase 1 single-spec entry point) -----
    gen = sub.add_parser(
        "generate",
        help="generate a batch of synthetic packages from a single spec YAML",
    )
    gen.add_argument("--spec", type=Path, required=True, help="path to adversarial spec YAML")
    gen.add_argument("--out", type=Path, required=True, help="output directory (created if missing)")
    gen.add_argument("--model", default=None, help="override generation model from spec")
    gen.add_argument(
        "--max-retries", type=int, default=3, help="SHACL retries per variant (default: 3)"
    )
    gen.add_argument(
        "--dry-run", action="store_true", help="render prompts to stdout without calling the LLM"
    )
    gen.add_argument(
        "--strict-circularity",
        action="store_true",
        help="exit 4 if generation model matches extract model (recommended for coverage experiments)",
    )
    gen.add_argument(
        "--allow-circular-model",
        action="store_true",
        help="explicit opt-in required when --model matches the extract model",
    )
    gen.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing manifest with matching spec_id",
    )

    # ----- run (Phase 2 batch orchestration, spec §9) -----
    run_sub = sub.add_parser(
        "run",
        help="batch-orchestrate adversarial generation across one or more spec directories",
    )
    run_sub.add_argument(
        "--batch",
        type=Path,
        action="append",
        required=True,
        help="directory of spec YAMLs to process (may be repeated)",
    )
    run_sub.add_argument(
        "--out", type=Path, required=True, help="output root directory"
    )
    run_sub.add_argument(
        "--model", default=None, help="override generation model from each spec"
    )
    run_sub.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="halt the batch when accumulated estimated cost (USD) reaches this threshold",
    )
    run_sub.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="number of concurrent spec generations (default: 1)",
    )
    run_sub.add_argument(
        "--resume",
        action="store_true",
        help="skip specs whose output already contains a valid manifest with matching spec_hash",
    )
    run_sub.add_argument(
        "--strict-circularity",
        action="store_true",
        help="exit 4 if generation model matches extract model",
    )
    run_sub.add_argument(
        "--allow-circular-model",
        action="store_true",
        help="explicit opt-in required when --model matches the extract model",
    )
    run_sub.add_argument(
        "--max-retries", type=int, default=3, help="SHACL retries per variant"
    )
    run_sub.add_argument(
        "--dry-run", action="store_true", help="dry-run mode (per-spec render, no LLM)"
    )
    run_sub.add_argument(
        "--subtlety-override",
        default=None,
        help=(
            "comma-separated list of subtlety values (low,medium,high) — when "
            "set, ignore each spec's declared subtlety and run once per value; "
            "output dirs gain a _<subtlety> suffix"
        ),
    )
    run_sub.add_argument(
        "--base-cou-override",
        default=None,
        help=(
            "comma-separated list of base_cou paths — when set, ignore each "
            "spec's declared base_cou and run once per path; applies only to "
            "specs whose coverage_intent is confirm_existing or "
            "negative_control (gap_probe and interaction stay pinned per §7); "
            "output dirs gain a _<vendor>-<cou> suffix"
        ),
    )
    run_sub.add_argument(
        "--cost-preview",
        action="store_true",
        help=(
            "walk discovered specs (with overrides applied), report total "
            "package count and estimated USD cost, exit 0 without invoking "
            "the LLM"
        ),
    )
    run_sub.add_argument(
        "--models",
        default=None,
        help=(
            "comma-separated list of model ids — when set, ignore --model "
            "and run each spec once per listed model (Phase 2 §7.7 quality "
            "benchmark fan-out); output dirs gain a _<model_short> suffix"
        ),
    )

    # ----- analyze (Phase 2 outcome classifier, spec §10) -----
    an = sub.add_parser(
        "analyze",
        help="classify a batch's outcomes and write CSV + HTML coverage reports",
    )
    an.add_argument(
        "--in", dest="in_dir", type=Path, required=True,
        help="batch output directory (the --out from `uofa adversarial run`)",
    )
    an.add_argument(
        "--out", type=Path, required=True, help="report output directory (created if missing)"
    )
    an.add_argument(
        "--check-pack", default="vv40", help="pack to use for `uofa check` (default: vv40)"
    )
    an.add_argument(
        "--parallel", type=int, default=1,
        help=(
            "concurrent Jena workers for the per-package rule run (default: 1). "
            "Each `uofa rules` call spawns its own JVM subprocess so parallelism "
            "is thread-safe. M5-scale batches (4-5K packages) benefit from "
            "parallel=5+. See docs/m5_findings.md F7."
        ),
    )
    an.add_argument(
        "--emit-judge-bundle",
        action="store_true",
        help=(
            "after writing outcomes.csv, package the batch into a Phase 3 "
            "judge_ready_bundle.tgz at <out>/judge_ready_bundle.tgz "
            "(spec v1.5 §2.1; off by default; default analyze behavior is unchanged)"
        ),
    )

    # ----- prep-review (Phase 2 D3 v1.8) -----
    pr = sub.add_parser(
        "prep-review",
        help="generate Phase 3 reviewer prep packets from a classified outcomes.csv",
    )
    pr.add_argument(
        "--outcomes", type=Path, required=True,
        help="path to outcomes.csv produced by `uofa adversarial analyze`",
    )
    pr.add_argument(
        "--output", type=Path, required=True,
        help="output directory for review packets (created if missing)",
    )
    pr.add_argument(
        "--include", default="cov-miss,cov-wrong",
        help="comma-separated outcome classes to package (default: cov-miss,cov-wrong)",
    )
    pr.add_argument(
        "--max-cases", type=int, default=50,
        help="cap the total number of packets emitted (default: 50)",
    )

    # ----- bundle (Phase 3 §2.1; package an already-analyzed Phase 2 batch) -----
    bd = sub.add_parser(
        "bundle",
        help="package an already-analyzed Phase 2 batch into a judge_ready_bundle.tgz (Phase 3 §2.1)",
    )
    bd.add_argument("--batch-dir", type=Path, required=True,
                    help="Phase 2 batch dir (output of `uofa adversarial run`)")
    bd.add_argument("--outcomes-csv", type=Path, default=None,
                    help="path to outcomes.csv (default: <batch-dir>/coverage/outcomes.csv)")
    bd.add_argument("--out", type=Path, required=True,
                    help="output path for judge_ready_bundle.tgz")

    # ----- calibrate-anchor (Phase 3 v1.6 §8.0) -----
    ca = sub.add_parser(
        "calibrate-anchor",
        help="ingest the Judge D calibration anchor and capture author overrides (Phase 3 v1.6 §8.0)",
    )
    ca_sub = ca.add_subparsers(dest="anchor_action", title="anchor actions",
                               metavar="{ingest,regenerate}")
    ca_ingest = ca_sub.add_parser(
        "ingest",
        help="validate the committed calibration set and capture author overrides",
    )
    ca_ingest.add_argument(
        "--in", dest="in_path", type=Path,
        default=Path("specs/calibration/calibration_set_v1.jsonl"),
        help="calibration set JSONL (default: specs/calibration/calibration_set_v1.jsonl)",
    )
    ca_ingest.add_argument(
        "--overrides", type=Path, default=None,
        help="optional author overrides JSONL (judge_d_author_overrides.jsonl)",
    )
    ca_ingest.add_argument(
        "--out", type=Path, default=None,
        help="optional output dir; writes normalized judge_d_anchor.jsonl when set",
    )
    ca_regen = ca_sub.add_parser(
        "regenerate",
        help="regenerate the Judge D anchor by re-running Claude over packages (deferred)",
    )
    ca_regen.add_argument(
        "--in", dest="in_path", type=Path,
        default=Path("specs/calibration/calibration_set_v1.jsonl"),
    )

    # ----- judge (Phase 3 §9.1) -----
    jg = sub.add_parser(
        "judge",
        help="run the LLM-as-judge ensemble against a judge_ready_bundle.tgz (Phase 3)",
    )
    jg.add_argument("--in", dest="in_bundle", type=Path, required=True,
                    help="judge_ready_bundle.tgz path (spec §2.1)")
    jg.add_argument("--out", type=Path, required=True,
                    help="output directory for per-judge judgments (created if missing)")
    jg.add_argument(
        "--judges", required=True,
        help="comma-separated provider tokens (e.g. openai,gemini,hf-llama or mock_a,mock_b,mock_c)",
    )
    jg.add_argument("--prompt-version", default="v0.1.0-tier-a",
                    help="judge prompt template version (default v0.1.0-tier-a)")
    jg.add_argument("--parallel", type=int, default=1,
                    help="HF Endpoints in-flight requests (default 1 sequential; "
                         "only meaningful when hf-llama is in --judges)")
    jg.add_argument("--model-openai", default=None,
                    help="override OpenAI model (default: per-provider built-in)")
    jg.add_argument("--model-gemini", default=None,
                    help="override Gemini model (default: per-provider built-in)")
    jg.add_argument("--model-hf-llama", default=None,
                    help="override HF Llama model (default: per-provider built-in)")
    jg.add_argument("--model-anthropic", default=None,
                    help="override Anthropic model (default: per-provider built-in)")
    jg.add_argument(
        "--calibration-only", action="store_true",
        help="judge only the calibration set, not the full bundle (spec §14.3 smoke)",
    )
    jg.add_argument(
        "--allow-same-family-judge", action="store_true",
        help="override family circularity check (smoke-test only; spec §6.2)",
    )
    jg.add_argument(
        "--dry-run", action="store_true",
        help="estimate per-judge token + USD cost, print a table, exit 0 "
             "without calling any provider (Wave F)",
    )
    jg.add_argument(
        "--max-cost", type=float, default=None,
        help="halt the run when accumulated estimated cost reaches this USD "
             "ceiling; writes cost_manifest.json on halt (Wave F)",
    )
    jg.add_argument(
        "--resume", action="store_true",
        help="skip cases already present in existing judgments_*.jsonl files "
             "(Wave I); writes resume_manifest.json with the skip count",
    )
    jg.add_argument(
        "--concurrency", type=int, default=1,
        help="per-judge max concurrent in-flight calls (default: 1, serial). "
             "Pilot v2 (2026-05-05) showed Gemini at p50=31s is the bottleneck; "
             "production runs benefit from --concurrency 15 to drop wall-clock "
             "from ~9h → ~2-3h. Per-vendor overrides via --concurrency-per-judge.",
    )
    jg.add_argument(
        "--concurrency-per-judge", default=None,
        help="per-vendor concurrency overrides as comma-separated token=N pairs, "
             "e.g. 'gemini=20,openai=10,hf-llama=10,anthropic=5'. Tokens not "
             "listed inherit --concurrency.",
    )
    jg.add_argument(
        "--max-requests-per-judge", default=None,
        help="per-vendor daily-request caps as comma-separated token=N pairs, "
             "e.g. 'gemini=950'. Vendor RPD limits force multi-day runs "
             "(Gemini 2.5 Pro caps at 1000 RPD; 50-call buffer recommended). "
             "On cap-hit the run halts gracefully + writes request_manifest.json; "
             "re-run with --resume the next UTC day to continue. Same-day "
             "resumes accumulate; new-UTC-day resumes reset to fresh quota.",
    )
    jg.add_argument(
        "--max-tpm-per-judge", default=None,
        help="per-vendor TPM (tokens-per-minute) caps as comma-separated "
             "token=N pairs, e.g. 'mistral=550000,gemini=950000'. Soft "
             "throttle: TokenRateTracker uses a 1-minute sliding window "
             "and sleeps until room is available (vs --max-requests-per-judge "
             "which hard-halts). When unset, defaults are auto-derived "
             "from each judge's `default_tpm_cap` in the capability table; "
             "set --no-auto-tpm to disable.",
    )
    jg.add_argument(
        "--no-auto-tpm", dest="auto_tpm", action="store_false",
        default=True,
        help="disable auto-derivation of TPM caps from the capability "
             "table (the default behavior). Combine with empty "
             "--max-tpm-per-judge to run completely uncapped.",
    )

    # ----- triage (Phase 3 §10.1) -----
    tg = sub.add_parser(
        "triage",
        help="majority-of-3 inter-judge agreement triage (Phase 3 Stage 3)",
    )
    tg.add_argument("--judgments-a", type=Path, required=True,
                    help="judgments_<A>.jsonl from judge A (typically GPT)")
    tg.add_argument("--judgments-b", type=Path, required=True,
                    help="judgments_<B>.jsonl from judge B (typically Gemini)")
    tg.add_argument("--judgments-c", type=Path, required=True,
                    help="judgments_<C>.jsonl from judge C (typically Llama)")
    tg.add_argument("--out", type=Path, required=True,
                    help="output directory (created if missing)")
    tg.add_argument(
        "--confidence-floor", type=float, default=0.6,
        help="confidence below which an agreeing verdict routes to DIVERGENT (default 0.6, spec §10.1)",
    )

    # ----- calibrate (Phase 3 v1.6 §8.1–8.4, Stage 1) -----
    cb = sub.add_parser(
        "calibrate",
        help="Stage 1 production-judge calibration vs Judge D anchor "
             "(Phase 3 v1.6 §8.1–8.4, hard gates 5/6/7)",
    )
    cb.add_argument(
        "--judges", required=True,
        help="comma-separated provider tokens. Production trio is the "
             "first 3 (A/B/C); optional 4th token is Judge E for sanity "
             "check (e.g. 'openai,gemini,hf-llama,mistral')",
    )
    cb.add_argument(
        "--out", type=Path, required=True,
        help="output directory; results land in <out>/<prompt_version>/...",
    )
    cb.add_argument(
        "--prompt-version", dest="prompt_version", default="v1.1.0",
        help="pinned prompt template version (default v1.1.0). Spec §8.3 "
             "permits up to 3 prompt-tuning iterations on hard-gate failure; "
             "override here to re-run calibration on a v1.2.0 / v1.3.0 prompt",
    )
    cb.add_argument(
        "--calibration-set", dest="calibration_set", type=Path, default=None,
        help="path to calibration_set_v1.jsonl (default: specs/calibration/calibration_set_v1.jsonl)",
    )
    cb.add_argument(
        "--overrides", type=Path, default=None,
        help="optional author overrides JSONL (judge_d_author_overrides.jsonl)",
    )
    cb.add_argument(
        "--concurrency", type=int, default=5,
        help="per-judge max concurrent in-flight calls (default 5)",
    )
    cb.add_argument(
        "--no-judge-e-sanity-check", action="store_true",
        help="skip Judge E sanity check vs Judge D (informational only; "
             "default ON when 4th judge is provided)",
    )

    # ----- arbitrate (Phase 3 v1.6 §6.7, §10.2) -----
    ar = sub.add_parser(
        "arbitrate",
        help="Judge E (Mistral) arbitration over the DISAGREEMENT queue (Phase 3 v1.6 Stage 3b)",
    )
    ar.add_argument("--judgments-a", type=Path, required=True)
    ar.add_argument("--judgments-b", type=Path, required=True)
    ar.add_argument("--judgments-c", type=Path, required=True)
    ar.add_argument(
        "--disagreement-queue", type=Path, required=True,
        help="triage Stage 3a output CSV (DISAGREEMENT cases)",
    )
    ar.add_argument("--out", type=Path, required=True,
                    help="output directory (created if missing)")
    ar.add_argument(
        "--judge-e", default="mistral",
        help="Judge E provider token (default mistral; mock_e for smoke)",
    )
    ar.add_argument(
        "--confidence-floor", type=float, default=0.6,
        help="Judge E confidence threshold for ARBITRATED vs ESCALATED (default 0.6, spec §10.2)",
    )

    # ----- adjudicate (Phase 3 §12.1) -----
    aj = sub.add_parser(
        "adjudicate",
        help="compute Cohen's κ + Fleiss' κ + confusion matrices (Phase 3 Stage 4)",
    )
    aj.add_argument("--judgments-a", type=Path, required=True)
    aj.add_argument("--judgments-b", type=Path, required=True)
    aj.add_argument("--judgments-c", type=Path, required=True)
    aj.add_argument("--out", type=Path, required=True,
                    help="output directory (created if missing)")
    aj.add_argument(
        "--adjudications", type=Path, default=None,
        help="optional author adjudications JSONL (spec §11); when present, "
             "compute author-vs-each-judge confusion matrices",
    )
    aj.add_argument(
        "--judgments-e", type=Path, default=None,
        help="optional Judge E arbitration JSONL (spec v1.6 §10.2); when "
             "present, emit EA/EB/EC confusion matrices and Judge E vs "
             "production-judge κ on the disagreement queue",
    )
    aj.add_argument(
        "--judgments-d", type=Path, default=None,
        help="optional Judge D calibration anchor JSONL (spec v1.6 §8.0); "
             "when present alongside --judgments-e, compute Judge E vs "
             "Judge D agreement on the calibration set (informational)",
    )
    aj.add_argument(
        "--author-adjudications", type=Path, default=None,
        help="optional author final-verdict JSONL on the escalation queue "
             "(spec v1.6 §11.1); when present alongside --judgments-e, "
             "emit author_E confusion matrix",
    )
    aj.add_argument(
        "--spot-check-overrides", type=Path, default=None,
        help="optional author spot-check overrides JSONL on CONVERGENT "
             "cases (spec v1.6 §11.4); reports override rate (target ≤ 0.10)",
    )
    aj.add_argument(
        "--confidence-floor", type=float, default=0.6,
        help="Judge E confidence floor for ARBITRATED vs ESCALATED partition "
             "in adjudication summary (default 0.6, spec §10.2)",
    )

    # ----- finalize (Phase 3 v1.6 §10.3, Delta 5) -----
    fn = sub.add_parser(
        "finalize",
        help="assemble final_verdicts.jsonl across CONVERGENT / ARBITRATED / "
             "AUTHOR_FINAL / AUTHOR_OVERRIDE layers (Phase 3 v1.6 §10.3)",
    )
    fn.add_argument("--judgments-a", type=Path, required=True)
    fn.add_argument("--judgments-b", type=Path, required=True)
    fn.add_argument("--judgments-c", type=Path, required=True)
    fn.add_argument("--judgments-e", type=Path, default=None,
                    help="Judge E arbitration JSONL (judgments_E.jsonl)")
    fn.add_argument("--author-adjudications", type=Path, default=None,
                    help="author final-verdict JSONL on the escalation queue")
    fn.add_argument("--spot-check-overrides", type=Path, default=None,
                    help="author spot-check override JSONL on CONVERGENT cases")
    fn.add_argument("--confidence-floor", type=float, default=0.6,
                    help="Judge E confidence floor for ARBITRATED selection")
    fn.add_argument("--out", type=Path, required=True,
                    help="output directory (created if missing)")

    # ----- formalize (Phase 3 v1.6 §13.1, Wave J — forward-chaining only) -----
    fz = sub.add_parser(
        "formalize",
        help="generate Jena rule + test scaffolds from REAL-GAP final verdicts "
             "(Phase 3 v1.6 §13.1; forward-chaining C3 weakeners only — "
             "OOS substrate test is separate engineering)",
    )
    fz.add_argument("--final-verdicts", type=Path, required=True,
                    help="path to final_verdicts.jsonl from `finalize`")
    fz.add_argument("--judgments-a", type=Path, default=None,
                    help="judgments_A.jsonl for §6.7 candidate lookup")
    fz.add_argument("--judgments-b", type=Path, default=None)
    fz.add_argument("--judgments-c", type=Path, default=None)
    fz.add_argument("--severity-overrides", type=Path, default=None,
                    help="optional JSON dict {'W-EV-01': 'Critical', ...} "
                         "overriding the §6.7 default severity table")
    fz.add_argument("--out", type=Path, required=True,
                    help="output directory; rules/, tests/, formalization_summary.json")

    # ----- case-study-rerun (Phase 3 v1.6 §13.3, Wave K) -----
    cs = sub.add_parser(
        "case-study-rerun",
        help="run two catalog versions across the published case-study COUs "
             "(Morrison + Nagaraja); emit delta_table.md + .json (Phase 3 v1.6 §13.3)",
    )
    cs.add_argument(
        "--catalog", action="append", required=True,
        help="catalog version (specify twice: --catalog v0.4.1 --catalog v0.5)",
    )
    cs.add_argument(
        "--cou", action="append", required=True,
        help="case-study COU id (e.g. morrison-cou1, nagaraja-cou1); repeat for each",
    )
    cs.add_argument("--out", type=Path, required=True,
                    help="output directory (created if missing)")


def run(args) -> int:
    cmd = getattr(args, "adversarial_command", None)
    if cmd == "generate":
        from uofa_cli.adversarial.generator import run_generate
        return run_generate(args)
    if cmd == "run":
        from uofa_cli.adversarial.runner import run_batch
        return run_batch(args)
    if cmd == "analyze":
        from uofa_cli.adversarial.classifier import run_analyze
        return run_analyze(args)
    if cmd == "prep-review":
        from uofa_cli.adversarial.prep_review import run_prep_review
        return run_prep_review(args)
    if cmd == "bundle":
        from uofa_cli.adversarial.judge.runner import run_bundle
        return run_bundle(args)
    if cmd == "calibrate-anchor":
        from uofa_cli.adversarial.judge.runner import run_calibrate_anchor
        return run_calibrate_anchor(args)
    if cmd == "calibrate":
        from uofa_cli.adversarial.judge.runner import run_calibrate
        return run_calibrate(args)
    if cmd == "arbitrate":
        from uofa_cli.adversarial.judge.runner import run_arbitrate
        return run_arbitrate(args)
    if cmd == "judge":
        from uofa_cli.adversarial.judge.runner import run_judge
        return run_judge(args)
    if cmd == "triage":
        from uofa_cli.adversarial.judge.runner import run_triage
        return run_triage(args)
    if cmd == "adjudicate":
        from uofa_cli.adversarial.judge.runner import run_adjudicate
        return run_adjudicate(args)
    if cmd == "finalize":
        from uofa_cli.adversarial.judge.runner import run_finalize
        return run_finalize(args)
    if cmd == "formalize":
        from uofa_cli.adversarial.judge.runner import run_formalize
        return run_formalize(args)
    if cmd == "case-study-rerun":
        from uofa_cli.adversarial.judge.runner import run_case_study_rerun
        return run_case_study_rerun(args)

    print("usage: uofa adversarial <subcommand>")
    print()
    print("subcommands:")
    print("  generate     generate from a single spec (Phase 1)")
    print("  run          batch-orchestrate generation across spec directories (Phase 2)")
    print("  analyze      classify a batch's outcomes; emit CSV + HTML reports (Phase 2)")
    print("  prep-review  generate Phase 3 reviewer prep packets from outcomes.csv (Phase 2 D3)")
    print("  bundle       package an already-analyzed batch into judge_ready_bundle.tgz (Phase 3 §2.1)")
    print("  judge        run the LLM-as-judge ensemble (Phase 3 Stage 1/2)")
    print("  triage       majority-of-3 inter-judge triage (Phase 3 Stage 3)")
    print("  adjudicate   compute Cohen's κ + Fleiss' κ + confusion matrices (Phase 3 Stage 4)")
    return 0
