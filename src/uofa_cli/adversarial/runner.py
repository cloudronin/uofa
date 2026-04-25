"""Batch orchestration for adversarial coverage experiments — Phase 2 §9.

`uofa adversarial run` discovers spec YAMLs under each `--batch` directory,
generates packages for each via the existing single-spec
:func:`uofa_cli.adversarial.generator.run_generate`, accumulates costs
across specs, and writes a roll-up ``batch_manifest.json``.

Output layout:

    <out>/
        batch_manifest.json
        <category>/                 # mirrors spec subdir name
            <spec_id>/
                manifest.json       # per-spec (Phase 1 schema)
                *.jsonld
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli import __version__
from uofa_cli.adversarial.generator import GENERATOR_VERSION, run_generate
from uofa_cli.adversarial.spec_loader import (
    SourceTaxonomyError,
    SpecValidationError,
    load_spec,
)
from uofa_cli.output import error, info, result_line, warn


@dataclass
class _SpecResult:
    spec_id: str
    spec_path: str
    spec_hash: str
    coverage_intent: str
    target_weakener: str | None
    source_taxonomy: str | None
    out_dir: str
    succeeded: bool
    gen_invalid: bool
    requested_variants: int
    generated_variants: int
    total_tokens: int
    estimated_cost_usd: float
    shacl_retries: int
    error: str | None = None


def _discover_specs(batch_dirs: list[Path]) -> list[tuple[Path, Path]]:
    """Return a list of ``(category_subdir_name, spec_path)`` tuples.

    The category subdir name is the immediate parent of the spec file
    (e.g., ``confirm_existing``), used to mirror layout under ``--out``.
    """
    out: list[tuple[Path, Path]] = []
    for d in batch_dirs:
        if not d.exists():
            warn(f"--batch directory not found: {d}")
            continue
        for p in sorted(d.glob("*.yaml")):
            out.append((d.name, p))
    return out


def _per_spec_out(out_root: Path, category: str, spec_id: str) -> Path:
    return out_root / category / spec_id


def _existing_manifest_matches(
    spec_path: Path, target_dir: Path, spec_hash: str
) -> bool:
    manifest_path = target_dir / "manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("specHash", "").endswith(spec_hash)


def _build_args_for_spec(
    parent_args: argparse.Namespace,
    spec_path: Path,
    out_dir: Path,
) -> argparse.Namespace:
    """Construct the argparse Namespace ``run_generate`` expects."""
    return argparse.Namespace(
        spec=spec_path,
        out=out_dir,
        model=getattr(parent_args, "model", None),
        max_retries=getattr(parent_args, "max_retries", 3),
        dry_run=getattr(parent_args, "dry_run", False),
        strict_circularity=getattr(parent_args, "strict_circularity", False),
        allow_circular_model=getattr(parent_args, "allow_circular_model", False),
        force=True,  # batch always overwrites unless --resume skipped it
    )


def _read_per_spec_manifest(out_dir: Path) -> dict | None:
    p = out_dir / "manifest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _process_spec(
    parent_args: argparse.Namespace,
    category: str,
    spec_path: Path,
    out_root: Path,
    resume: bool,
) -> _SpecResult:
    try:
        spec = load_spec(spec_path)
    except (SpecValidationError, SourceTaxonomyError) as e:
        return _SpecResult(
            spec_id=spec_path.stem,
            spec_path=str(spec_path),
            spec_hash="",
            coverage_intent="?",
            target_weakener=None,
            source_taxonomy=None,
            out_dir="",
            succeeded=False,
            gen_invalid=False,
            requested_variants=0,
            generated_variants=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            shacl_retries=0,
            error=f"spec load failed: {e}",
        )

    target_dir = _per_spec_out(out_root, category, spec.spec_id)

    # --resume path: skip if matching manifest already present.
    if resume and _existing_manifest_matches(spec_path, target_dir, spec.spec_hash):
        manifest = _read_per_spec_manifest(target_dir) or {}
        info(f"  ↺ resume skip: {spec.spec_id}")
        return _SpecResult(
            spec_id=spec.spec_id,
            spec_path=str(spec_path),
            spec_hash=spec.spec_hash,
            coverage_intent=spec.coverage_intent,
            target_weakener=spec.target_weakener,
            source_taxonomy=spec.source_taxonomy,
            out_dir=str(target_dir),
            succeeded=True,
            gen_invalid=False,
            requested_variants=spec.n_variants,
            generated_variants=manifest.get("generated", 0),
            total_tokens=manifest.get("totalTokens", 0),
            estimated_cost_usd=manifest.get("estimatedCostUsd", 0.0),
            shacl_retries=manifest.get("shaclFailed", 0),
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    args = _build_args_for_spec(parent_args, spec_path, target_dir)
    rc = run_generate(args)

    manifest = _read_per_spec_manifest(target_dir) or {}
    requested = manifest.get("requested", spec.n_variants)
    generated = manifest.get("generated", 0)
    return _SpecResult(
        spec_id=spec.spec_id,
        spec_path=str(spec_path),
        spec_hash=spec.spec_hash,
        coverage_intent=spec.coverage_intent,
        target_weakener=spec.target_weakener,
        source_taxonomy=spec.source_taxonomy,
        out_dir=str(target_dir),
        succeeded=(rc == 0 and generated > 0),
        gen_invalid=(generated == 0 and rc != 0),
        requested_variants=requested,
        generated_variants=generated,
        total_tokens=manifest.get("totalTokens", 0),
        estimated_cost_usd=manifest.get("estimatedCostUsd", 0.0),
        shacl_retries=manifest.get("shaclFailed", 0),
        error=None if rc == 0 else f"generator exit {rc}",
    )


def run_batch(args) -> int:
    """Entry point for ``uofa adversarial run``."""
    batch_dirs: list[Path] = list(args.batch or [])
    out_root: Path = args.out
    out_root.mkdir(parents=True, exist_ok=True)

    discovered = _discover_specs(batch_dirs)
    if not discovered:
        error("no spec YAMLs found under any --batch directory")
        return 2

    info(f"discovered {len(discovered)} spec(s) across {len(batch_dirs)} batch dir(s)")

    results: list[_SpecResult] = []
    accumulated_cost = 0.0
    halted_at = None

    parallel = max(1, int(args.parallel or 1))

    if parallel == 1:
        for category, spec_path in discovered:
            if args.max_cost is not None and accumulated_cost >= float(args.max_cost):
                halted_at = spec_path
                warn(f"--max-cost {args.max_cost:.2f} reached; halting before {spec_path.name}")
                break
            res = _process_spec(args, category, spec_path, out_root, args.resume)
            accumulated_cost += res.estimated_cost_usd
            results.append(res)
    else:
        # Parallel mode — submit as a thread pool. Cost halt is enforced
        # cooperatively after each future completes (a few in-flight futures
        # may overshoot the budget by their own cost).
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {
                pool.submit(_process_spec, args, category, spec_path, out_root, args.resume):
                spec_path
                for category, spec_path in discovered
            }
            for fut in as_completed(futures):
                res = fut.result()
                accumulated_cost += res.estimated_cost_usd
                results.append(res)
                if args.max_cost is not None and accumulated_cost >= float(args.max_cost):
                    halted_at = futures[fut]
                    warn(f"--max-cost {args.max_cost:.2f} reached after {res.spec_id}")
                    # Cancel remaining
                    for f, _ in futures.items():
                        if not f.done():
                            f.cancel()
                    break

    # ----- batch_manifest.json -----
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    succeeded = sum(1 for r in results if r.succeeded)
    gen_invalid = sum(1 for r in results if r.gen_invalid)
    total_packages = sum(r.generated_variants for r in results)
    total_tokens = sum(r.total_tokens for r in results)
    batch_manifest = {
        "batchId": f"batch-{timestamp.replace(':', '').replace('-', '')[:14]}",
        "timestamp": timestamp,
        "generatorVersion": GENERATOR_VERSION,
        "toolVersion": f"uofa-cli {__version__}",
        "specsLoaded": len(results),
        "specsSucceeded": succeeded,
        "specsGenInvalid": gen_invalid,
        "totalPackages": total_packages,
        "totalTokens": total_tokens,
        "estimatedCostUsd": round(accumulated_cost, 4),
        "strictCircularity": bool(getattr(args, "strict_circularity", False)),
        "halted": halted_at is not None,
        "haltedBefore": str(halted_at) if halted_at else None,
        "perSpecResults": [asdict(r) for r in results],
    }
    manifest_path = out_root / "batch_manifest.json"
    manifest_path.write_text(json.dumps(batch_manifest, indent=2))
    result_line("batch_manifest", True, str(manifest_path))
    info(f"specs: {succeeded}/{len(results)} ok, {gen_invalid} gen-invalid")
    info(f"packages: {total_packages}, tokens: {total_tokens}, cost: ${accumulated_cost:.2f}")

    if succeeded == 0:
        return 2
    if gen_invalid > 0:
        return 1
    return 0
