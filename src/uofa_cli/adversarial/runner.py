"""Batch orchestration for adversarial coverage experiments — Phase 2 §9.

`uofa adversarial run` discovers spec YAMLs under each `--batch` directory,
generates packages for each via the existing single-spec
:func:`uofa_cli.adversarial.generator.run_generate`, accumulates costs
across specs, and writes a roll-up ``batch_manifest.json``.

Output layout:

    <out>/
        batch_manifest.json
        <category>/                 # mirrors spec subdir name
            <spec_id>[<_suffix>]/   # suffix appended under fan-out
                manifest.json       # per-spec (Phase 1 schema)
                *.jsonld

Phase 2 v1.8 §3 fan-out flags
-----------------------------

The runner supports three flags that turn a single declared spec into
multiple realized "cells" without authoring more YAML:

* ``--subtlety-override low,medium,high`` — ignore each spec's declared
  subtlety and run once per listed value. Output dir gets ``_<subtlety>``.
* ``--base-cou-override <p1>,<p2>,...`` — ignore each spec's declared
  ``base_cou`` and run once per listed path. Output dir gets a
  ``_<vendor>-<cou>`` suffix derived from the last two path segments.

  Per §7 conventions, base_cou fan-out applies ONLY to specs with
  ``coverage_intent ∈ {confirm_existing, negative_control}``. ``gap_probe``
  and ``interaction`` specs pin a single base_cou by design and are left
  alone even when the flag is set.
* ``--cost-preview`` — walk the post-expansion cells, compute total
  package count and an estimated USD cost, print a per-battery roll-up,
  and exit 0 without invoking the LLM.

Output-dir suffixing means a single declared spec can produce N cells per
batch (each with its own per-cell ``manifest.json``); the
``batch_manifest.perSpecResults`` array contains one entry per cell.
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
from uofa_cli.adversarial.model_costs import estimate_cost
from uofa_cli.adversarial.spec_loader import (
    SourceTaxonomyError,
    SpecValidationError,
    VALID_SUBTLETIES,
    load_spec,
)
from uofa_cli.output import error, info, result_line, warn

#: Coverage intents that semantically support base_cou fan-out. Per Phase 2
#: §7, gap_probe and interaction specs pin a single base_cou by design and
#: must be left alone even when ``--base-cou-override`` is set.
_BASE_COU_FAN_INTENTS = frozenset({"confirm_existing", "negative_control"})

#: Average tokens per generated package, used by ``--cost-preview``.
#: Anchored to Phase 2 §3's $290 / 4,455 ≈ 4k tokens/package budget.
_TOKENS_PER_PACKAGE_DEFAULT = 4_000


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


# ───────────────────── fan-out + cost-preview helpers ─────────────────────


def _parse_csv_flag(raw: str | None) -> list[str]:
    """Split a comma-separated CLI flag into a clean list (or empty list)."""
    if not raw:
        return []
    return [tok.strip() for tok in raw.split(",") if tok.strip()]


def _peek_coverage_intent(spec_path: Path) -> str | None:
    """Read just ``target.coverage_intent`` from a spec YAML without running
    the full validator. Used at expansion time to decide whether base_cou
    fan-out applies (gap_probe / interaction specs are exempt). Returns
    None if the YAML is unreadable; callers fall back to "no fan-out"."""
    try:
        import yaml
        data = yaml.safe_load(spec_path.read_text())
    except Exception:  # noqa: BLE001 — best-effort peek
        return None
    target = (data or {}).get("target") or {}
    intent = target.get("coverage_intent")
    return intent if isinstance(intent, str) else None


def _cou_short(raw_path: str) -> str:
    """Compact label for an output dir suffix derived from a base_cou path.

    Examples:
        packs/vv40/examples/morrison/cou1            → morrison-cou1
        packs/vv40/examples/nagaraja/cou1            → nagaraja-cou1
        packs/nasa-7009b/examples/aerospace/uofa-... → aerospace-uofa-...
    """
    p = Path(raw_path)
    parent = p.parent.name or ""
    leaf = p.stem if p.suffix else p.name
    label = f"{parent}-{leaf}" if parent else leaf
    return label.lower().replace("_", "-")


@dataclass
class _ExpandedCell:
    """One realized (spec, subtlety, base_cou) triple after fan-out.

    ``out_dir_suffix`` is the trailing string to append to ``spec_id`` when
    constructing the per-cell output directory; empty when no overrides
    apply.
    """
    category: str
    spec_path: Path
    subtlety_override: str | None
    base_cou_override: str | None
    out_dir_suffix: str


def _expand_specs(
    discovered: list[tuple[str, Path]],
    *,
    subtlety_overrides: list[str],
    base_cou_overrides: list[str],
) -> list[_ExpandedCell]:
    """Cartesian-product spec × subtlety_override × base_cou_override.

    See module docstring for the per-battery convention enforced via
    :data:`_BASE_COU_FAN_INTENTS`.
    """
    out: list[_ExpandedCell] = []
    for category, spec_path in discovered:
        intent = _peek_coverage_intent(spec_path) or ""
        cou_eligible = intent in _BASE_COU_FAN_INTENTS

        sub_list: list[str | None] = (
            list(subtlety_overrides) if subtlety_overrides else [None]
        )
        cou_list: list[str | None] = (
            list(base_cou_overrides)
            if (base_cou_overrides and cou_eligible)
            else [None]
        )

        for sub in sub_list:
            for cou in cou_list:
                parts: list[str] = []
                if sub:
                    parts.append(sub)
                if cou:
                    parts.append(_cou_short(cou))
                suffix = ("_" + "_".join(parts)) if parts else ""
                out.append(_ExpandedCell(
                    category=category,
                    spec_path=spec_path,
                    subtlety_override=sub,
                    base_cou_override=cou,
                    out_dir_suffix=suffix,
                ))
    return out


def _run_cost_preview(
    expanded: list[_ExpandedCell],
    *,
    model: str,
    tokens_per_pkg: int = _TOKENS_PER_PACKAGE_DEFAULT,
) -> int:
    """Walk expanded cells, sum projected package counts, print a roll-up.

    No LLM calls. Each cell contributes ``spec.n_variants`` packages. We
    load each unique spec at most once (cells share a spec_path).
    Returns 0 unconditionally — preview is advisory only.
    """
    spec_cache: dict[Path, int] = {}
    by_category: dict[str, dict] = {}
    total_packages = 0
    skipped: list[tuple[Path, str]] = []

    for cell in expanded:
        n_pkgs = spec_cache.get(cell.spec_path)
        if n_pkgs is None:
            try:
                spec = load_spec(cell.spec_path)
            except (SpecValidationError, SourceTaxonomyError) as e:
                skipped.append((cell.spec_path, str(e)))
                spec_cache[cell.spec_path] = 0
                continue
            n_pkgs = spec.n_variants
            spec_cache[cell.spec_path] = n_pkgs

        total_packages += n_pkgs
        bucket = by_category.setdefault(
            cell.category, {"cells": 0, "packages": 0}
        )
        bucket["cells"] += 1
        bucket["packages"] += n_pkgs

    info("Cost preview (no LLM calls):")
    info(f"  cells: {len(expanded)} (post fan-out)")
    info(f"  unique specs: {len(spec_cache)}")
    for cat in sorted(by_category):
        b = by_category[cat]
        info(f"  {cat}: {b['cells']} cells → {b['packages']} packages")
    cost = estimate_cost(model, total_packages * tokens_per_pkg)
    info(
        f"Total: {total_packages} packages "
        f"(~{tokens_per_pkg} tokens/pkg) → est. ${cost:.2f} at {model}"
    )
    if skipped:
        warn(f"  {len(skipped)} spec(s) skipped due to load errors:")
        for path, err in skipped:
            warn(f"    {path.name}: {err}")
    return 0


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
    *,
    subtlety_override: str | None = None,
    base_cou_override: str | None = None,
) -> argparse.Namespace:
    """Construct the argparse Namespace ``run_generate`` expects.

    The two ``*_override`` parameters thread through to ``run_generate``,
    which applies them to the loaded spec in-place before dispatching to
    the generator.
    """
    return argparse.Namespace(
        spec=spec_path,
        out=out_dir,
        model=getattr(parent_args, "model", None),
        max_retries=getattr(parent_args, "max_retries", 3),
        dry_run=getattr(parent_args, "dry_run", False),
        strict_circularity=getattr(parent_args, "strict_circularity", False),
        allow_circular_model=getattr(parent_args, "allow_circular_model", False),
        force=True,  # batch always overwrites unless --resume skipped it
        subtlety_override=subtlety_override,
        base_cou_override=base_cou_override,
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
    cell: _ExpandedCell,
    out_root: Path,
    resume: bool,
) -> _SpecResult:
    spec_path = cell.spec_path
    try:
        spec = load_spec(spec_path)
    except (SpecValidationError, SourceTaxonomyError) as e:
        return _SpecResult(
            spec_id=spec_path.stem + cell.out_dir_suffix,
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

    cell_id = spec.spec_id + cell.out_dir_suffix
    target_dir = _per_spec_out(out_root, cell.category, cell_id)

    # --resume path: skip if matching manifest already present.
    if resume and _existing_manifest_matches(spec_path, target_dir, spec.spec_hash):
        manifest = _read_per_spec_manifest(target_dir) or {}
        info(f"  ↺ resume skip: {cell_id}")
        return _SpecResult(
            spec_id=cell_id,
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
    args = _build_args_for_spec(
        parent_args,
        spec_path,
        target_dir,
        subtlety_override=cell.subtlety_override,
        base_cou_override=cell.base_cou_override,
    )
    rc = run_generate(args)

    manifest = _read_per_spec_manifest(target_dir) or {}
    requested = manifest.get("requested", spec.n_variants)
    generated = manifest.get("generated", 0)
    return _SpecResult(
        spec_id=cell_id,
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

    discovered = _discover_specs(batch_dirs)
    if not discovered:
        error("no spec YAMLs found under any --batch directory")
        return 2

    # ----- override flag parsing & validation -----
    subtlety_overrides = _parse_csv_flag(getattr(args, "subtlety_override", None))
    base_cou_overrides = _parse_csv_flag(getattr(args, "base_cou_override", None))
    bad_subtlety = [s for s in subtlety_overrides if s not in VALID_SUBTLETIES]
    if bad_subtlety:
        error(
            f"--subtlety-override has invalid value(s) {bad_subtlety!r}; "
            f"allowed: {sorted(VALID_SUBTLETIES)}"
        )
        return 2

    expanded = _expand_specs(
        discovered,
        subtlety_overrides=subtlety_overrides,
        base_cou_overrides=base_cou_overrides,
    )
    fan_note = ""
    if subtlety_overrides or base_cou_overrides:
        fan_note = (
            f" (fan-out: subtlety={subtlety_overrides or '∅'}, "
            f"base_cou={base_cou_overrides or '∅'} → "
            f"{len(expanded)} cell(s))"
        )
    info(
        f"discovered {len(discovered)} spec(s) across "
        f"{len(batch_dirs)} batch dir(s){fan_note}"
    )

    # ----- --cost-preview short-circuit (no LLM, no out_root mutation) -----
    if getattr(args, "cost_preview", False):
        return _run_cost_preview(
            expanded, model=getattr(args, "model", None) or "claude-sonnet-4-6"
        )

    out_root.mkdir(parents=True, exist_ok=True)

    results: list[_SpecResult] = []
    accumulated_cost = 0.0
    halted_at = None

    parallel = max(1, int(args.parallel or 1))

    if parallel == 1:
        for cell in expanded:
            if args.max_cost is not None and accumulated_cost >= float(args.max_cost):
                halted_at = cell.spec_path
                warn(
                    f"--max-cost {args.max_cost:.2f} reached; halting before "
                    f"{cell.spec_path.name}{cell.out_dir_suffix}"
                )
                break
            res = _process_spec(args, cell, out_root, args.resume)
            accumulated_cost += res.estimated_cost_usd
            results.append(res)
    else:
        # Parallel mode — submit as a thread pool. Cost halt is enforced
        # cooperatively after each future completes (a few in-flight futures
        # may overshoot the budget by their own cost).
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {
                pool.submit(_process_spec, args, cell, out_root, args.resume):
                cell
                for cell in expanded
            }
            for fut in as_completed(futures):
                res = fut.result()
                accumulated_cost += res.estimated_cost_usd
                results.append(res)
                if args.max_cost is not None and accumulated_cost >= float(args.max_cost):
                    halted_at = futures[fut].spec_path
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
        "subtletyOverride": subtlety_overrides or None,
        "baseCouOverride": base_cou_overrides or None,
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
