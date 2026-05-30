"""uofa interrogate — measure a surrogate (and `init` to set up the inputs).

Two surfaces, deliberately different in kind (Addendum A14):

- `uofa interrogate --adapter … --benchmark … --reference … --scope … -o pkg`
  MEASURES and emits a signed evidence bundle + an at-a-glance comparison. This
  command never judges: no pass/fail, no threshold flag, no chaining into the
  rule engine (the firewall, §8 / AGENTS.md §12).
- `uofa interrogate init` is the GUIDED, interactive setup wizard. It is
  interactive because the questions are about the *model* (what are its inputs
  in physical terms, what is the valid envelope). It never silently defaults
  scope, never fabricates reference values, and smoke-tests the generated
  adapter before declaring success (A14.1/A14.3).

Heavy deps (numpy + the user's adapter framework) are imported lazily via the
`[interrogate]` extra.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli import paths
from uofa_cli.output import error, info, result_line, step_header

HELP = "measure a surrogate and emit a signed evidence bundle (or `init` to set up)"

SURROGATE_TYPES = ["ROM", "PINN", "operator-learning", "data-driven-emulator", "ML-closure"]


def add_arguments(parser):
    # Measure-path flags live on the parent and are OPTIONAL at the argparse
    # level (validated in run), so they don't collide with the `init` subcommand.
    parser.add_argument("--adapter", help="ModelAdapter ref: 'pkg.module.ClassName' or '/path/file.py:ClassName'")
    parser.add_argument("--benchmark", type=Path, help="benchmark inputs (.npz/.json)")
    parser.add_argument("--reference", type=Path, help="reference outputs (.npz/.json) — supplied, never generated")
    parser.add_argument("--scope", type=Path, help="declared-scope config (.json/.toml)")
    parser.add_argument("--output", "-o", type=Path, help="output path for the signed evidence bundle (.json)")
    parser.add_argument("--key", "-k", type=Path, help="ed25519 SIP measurement key (auto-detected from project keys/ if omitted)")
    parser.add_argument("--seed", type=int, default=None, help="seed recorded in measurement provenance")
    # NOTE: deliberately NO --check / --decision / --threshold flag (the firewall).

    sub = parser.add_subparsers(dest="interrogate_cmd")
    init_p = sub.add_parser("init", help="guided setup: detect the model, generate adapter + scope + smoke-test")
    init_p.add_argument("--model", type=Path, help="path to the model file/dir to inspect")
    init_p.add_argument("--docs", type=Path, help="model card / training report the scope values came from (provenance)")
    init_p.add_argument("--benchmark", type=Path, help="benchmark inputs, used for the adapter smoke test")
    init_p.add_argument("--reference", type=Path, help="reference outputs (supplied; never generated)")
    init_p.add_argument("--out-dir", type=Path, default=Path("."), help="where to write the generated adapter + scope")
    # NOTE: deliberately NO --yes / --non-interactive / --accept-scope (A14.1):
    # scope is always confirmed or entered by the engineer, field by field.


def run(args) -> int:
    if getattr(args, "interrogate_cmd", None) == "init":
        return _run_init(args)
    return _run_measure(args)


# ── Measure path ─────────────────────────────────────────────────────────────


def _load_scope(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Scope config not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".toml":
        try:
            import tomllib
        except ModuleNotFoundError:  # py3.10
            import tomli as tomllib  # type: ignore[no-redef]
        return tomllib.loads(text)
    return json.loads(text)


def _resolve_key(args) -> Path | None:
    if getattr(args, "key", None):
        return Path(args.key)
    project_root = paths.find_project_root()
    if project_root:
        keys_dir = project_root / "keys"
        if keys_dir.is_dir():
            for candidate in sorted(keys_dir.glob("*.key")):
                return candidate
    return None


def _run_measure(args) -> int:
    missing = [f for f in ("adapter", "benchmark", "reference", "scope", "output")
               if getattr(args, f, None) is None]
    if missing:
        error("missing required option(s) for measurement: "
              + ", ".join(f"--{m}" for m in missing)
              + "  (or run `uofa interrogate init` for guided setup)")
        return 2

    from uofa_cli.interrogate import run_interrogation
    from uofa_cli.interrogate.forbidden import find_forbidden_in_measurement_region
    from uofa_cli.interrogate.comparison import render_comparison

    scope = _load_scope(Path(args.scope))
    key_path = _resolve_key(args)

    step_header(f"Interrogating surrogate via {args.adapter}")
    info(f"benchmark: {args.benchmark}")
    info(f"reference: {args.reference}")

    result = run_interrogation(
        adapter_ref=args.adapter, benchmark_path=args.benchmark, reference_path=args.reference,
        scope=scope, output_path=args.output, key_path=key_path, seed=getattr(args, "seed", None),
    )

    # Firewall, defense in depth (signature-scoped): no forbidden decision
    # content in the measurement region of the emitted bundle.
    leaks = list(find_forbidden_in_measurement_region(result["bundle"]))
    if leaks:
        error("Firewall violation — forbidden field(s) in the measurement region: "
              + ", ".join(sorted({token for _, token in leaks})))
        return 1

    residual_count = len(result["bundle"]["measurements"]["referenceResiduals"])
    result_line("Wrote evidence bundle", True, str(result["output_path"]))
    info(f"measured {residual_count} reference-residual QoI(s)")
    if result["signed"]:
        info(f"signed: ed25519 (sha256:{result['hash'][:12]})")
    else:
        info("bundle is unsigned (no signing key provided)")

    # At-a-glance comparison (A3). Measurements only — no threshold, no verdict.
    print()
    print(render_comparison(result["bundle"]))
    return 0


# ── Guided setup (`init`) — interactive; the questions are about the model ───


def _ask(prompt: str) -> str:
    try:
        return input(f"{prompt}: ").strip()
    except EOFError:
        raise RuntimeError("`uofa interrogate init` is interactive — run it in a terminal.")


def _ask_float(prompt: str) -> float:
    while True:
        raw = _ask(prompt)
        try:
            return float(raw)
        except ValueError:
            error("enter a number.")


def _ask_list(prompt: str) -> list[str]:
    return [tok.strip() for tok in _ask(prompt).split(",") if tok.strip()]


def _ask_yes_no(prompt: str) -> bool:
    return _ask(f"{prompt} [y/N]").lower().startswith("y")


def _ask_provenance(docs: Path | None, field: str) -> str:
    if docs and _ask_yes_no(f"  did '{field}' come from {docs}?"):
        return f"extracted-from:{docs};confirmed-by-engineer"
    return "entered-by-engineer"


def _smoke(adapter_path: Path, benchmark_path: Path, output_names: list[str]) -> tuple[bool, str]:
    from uofa_cli.interrogate.adapter import load_adapter
    from uofa_cli.interrogate import loader, init_wizard
    try:
        import numpy as np
        adapter = load_adapter(f"{adapter_path}:GeneratedAdapter")
        bench = loader.load_benchmark(benchmark_path)
        row = np.asarray(bench.inputs)[:1]
        return init_wizard.smoke_test_adapter(adapter, row, output_names)
    except Exception as exc:  # incomplete template / framework not importable
        return False, str(exc)


def _run_init(args) -> int:
    from uofa_cli.interrogate import init_wizard as wiz

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = wiz.detect_model_format(args.model) if args.model else "unknown"

    step_header("uofa interrogate init — guided setup")
    info(f"model: {args.model or '(not provided)'}   detected format: {fmt}")

    input_names = _ask_list("Name the model INPUT dimensions in physical terms (comma-separated, e.g. reynolds,aoa)")
    output_names = _ask_list("Name the model OUTPUT quantities of interest (comma-separated, e.g. lift_coefficient)")

    adapter_path = out_dir / "sip_adapter.py"
    adapter_path.write_text(
        wiz.generate_adapter_source(
            class_name="GeneratedAdapter", model_format=fmt,
            model_path=str(args.model or "PATH_TO_MODEL"),
            input_names=input_names, output_names=output_names,
        ),
        encoding="utf-8",
    )
    result_line("Wrote adapter", True, str(adapter_path))

    # Scope — confirm/enter every field; tag provenance; never silently default.
    provenance: dict[str, str] = {}
    envelope_dims = []
    info("Declare the training envelope (the surrogate's valid input domain):")
    for name in input_names:
        envelope_dims.append({"name": name,
                              "min": _ask_float(f"  {name}: minimum bound"),
                              "max": _ask_float(f"  {name}: maximum bound")})
        provenance[f"trainingEnvelope.{name}"] = _ask_provenance(args.docs, name)

    eval_point = []
    info("Declare the evaluation point (where this COU exercises the surrogate):")
    for name in input_names:
        eval_point.append({"name": name, "value": _ask_float(f"  {name}: evaluation value")})
        provenance[f"evaluationPoint.{name}"] = _ask_provenance(args.docs, name)

    constraints = []
    while _ask_yes_no("Add a declared physics constraint?"):
        cid = _ask("  constraint id (e.g. mass-conservation)")
        constraints.append({"constraintId": cid,
                            "description": _ask("  description"),
                            "kind": _ask("  kind (conservation/boundary-condition/invariant/...)")})
        provenance[f"constraint.{cid}"] = _ask_provenance(args.docs, cid)

    subject = {
        "surrogateId": _ask("Surrogate id"),
        "modelVersion": _ask("Model version"),
        "surrogateType": _ask(f"Surrogate type {SURROGATE_TYPES}"),
        "modelFingerprint": "unspecified",
    }
    scope = wiz.build_scope(subject=subject, envelope_dimensions=envelope_dims,
                            physics_constraints=constraints, provenance=provenance,
                            evaluation_point=eval_point)

    unprov = wiz.unprovenanced_scope_fields(scope)
    if unprov:  # invariant: never write a scope field without provenance
        error(f"internal: scope fields without provenance: {unprov}")
        return 1

    scope_path = out_dir / "sip_scope.json"
    scope_path.write_text(json.dumps(scope, indent=2, ensure_ascii=False), encoding="utf-8")
    result_line("Wrote scope", True, str(scope_path))

    if args.reference:
        info("reference is a SUPPLIED input — SIP never generates reference values.")

    if args.benchmark:
        ok, msg = _smoke(adapter_path, args.benchmark, output_names)
        if not ok:
            error(f"adapter smoke test failed at setup: {msg}")
            info("Complete the generated adapter (model load / output mapping), then re-run init.")
            return 1
        result_line("Adapter smoke test", True, "predict returned the declared QoIs")

    info(f"Setup complete. Next: uofa interrogate --adapter {adapter_path}:GeneratedAdapter "
         f"--benchmark <b> --reference <r> --scope {scope_path} -o pkg.json")
    return 0
