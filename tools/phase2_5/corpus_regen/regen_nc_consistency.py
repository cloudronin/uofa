"""v0.5.12 NC corpus consistency-stub patch tool.

Materializes a hybrid v0.5.11 batch dir whose `negative_controls/` subtree
has placeholder ``hasSensitivityAnalysis`` injected into every Complete-
profile NC that lacks one. This eliminates the residual W-CON-04 firings
on the 31 NCs whose Complete profile declaration was honored by the LLM
without the SHACL-optional SensitivityAnalysis block.

W-CON-01 and W-AR-01 — initially scoped to corpus regen — were instead
fixed via predicate tightening (factorStatus guard excluding
``'scoped-out'`` and ``'not-applicable'``) in the rules file. Empirical
finding: those rules' NC firings were on legitimately-level-less factors
where injecting placeholder values would violate the factor's stated
semantics. See `packs/core/rules/uofa_weakener.rules` for the v0.5.12
rule deltas.

Mirrors the v0.5.10 (`tools/phase2_5/regen_nc_envelope.py`) and v0.5.11
(`tools/phase2_5/regen_nc_offset_rationale.py`) patterns:

* Hybrid batch dir with symlinks for non-NC subdirs, real
  ``negative_controls/``
* ``batch_manifest.json`` copied + NC ``out_dir`` rewritten so the
  analyze classifier reads from hybrid (not source)
* Per-spec ``manifest.json`` copied into hybrid spec dirs

Operations per NC package under
``<in-batch>/negative_controls/<spec>/<variant>.jsonld``:

1. Load JSON.
2. If ``conformsToProfile`` resolves to ``uofa:ProfileComplete`` AND
   ``hasSensitivityAnalysis`` is absent → inject the SA stub via
   ``uofa_cli.adversarial.skeleton._augment_uofa_with_sensitivity_analysis_stub``.
   Mark ``PATCHED``.
3. Else → no patch needed; mark ``SKIP_NO_PATCH_NEEDED``.
4. Write to mirrored path under ``--out-batch``.
5. Re-sign via ``uofa_cli.integrity.sign_file``.

Idempotent: re-running on an already-patched directory is a no-op
(the helper short-circuits when the SA field is present).

CLI:

    python -m tools.phase2_5.regen_nc_consistency \\
        --in-batch dev/build/adversarial/phase2/2026-04-28-v0511 \\
        --out-batch dev/build/adversarial/phase2/2026-04-29-v0512 \\
        --key keys/research.key \\
        [--dry-run] [--report regen_consistency_report.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from uofa_cli.adversarial.skeleton import _augment_uofa_with_sensitivity_analysis_stub
from uofa_cli.integrity import sign_file


SYMLINK_SUBDIRS = (
    "confirm_existing",
    "gap_probe",
    "interaction",
    "coverage",
    "failed",
    "metadata",
    "review_packets",
)


@dataclass
class PatchOutcome:
    """One row of the patch report."""
    spec_id: str
    variant: str
    src_path: Path
    dst_path: Path
    status: str          # PATCHED | SKIP_NO_PATCH_NEEDED | FAILED
    note: str = ""

    def to_csv_row(self) -> dict:
        return {
            "spec_id": self.spec_id,
            "variant": self.variant,
            "src_path": str(self.src_path),
            "dst_path": str(self.dst_path),
            "status": self.status,
            "note": self.note,
        }


def _is_complete_profile(profile_value) -> bool:
    """Return True if profile_value resolves to ProfileComplete."""
    if not isinstance(profile_value, str):
        return False
    return (
        profile_value == "uofa:ProfileComplete"
        or profile_value.endswith("ProfileComplete")
    )


def _patch_doc(doc: dict) -> tuple[dict, bool]:
    """Apply W-CON-04 patch to a UofA doc.

    Returns (modified_doc, patch_applied_bool).
    """
    new_doc = deepcopy(doc)
    if not _is_complete_profile(new_doc.get("conformsToProfile")):
        return new_doc, False
    had_sa = "hasSensitivityAnalysis" in new_doc
    _augment_uofa_with_sensitivity_analysis_stub(new_doc)
    patched = (not had_sa) and ("hasSensitivityAnalysis" in new_doc)
    return new_doc, patched


def _materialize_hybrid_batch(in_batch: Path, out_batch: Path) -> None:
    """Create out_batch with symlinks to non-NC subdirs and an empty
    negative_controls/ ready for patched copies.

    Mirrors v0.5.10 / v0.5.11 patch tools so chained patches work
    transparently when ``in_batch`` is itself a hybrid dir.
    """
    out_batch.mkdir(parents=True, exist_ok=True)

    for sub in SYMLINK_SUBDIRS:
        src = in_batch / sub
        dst = out_batch / sub
        if not src.exists():
            continue
        if dst.is_symlink():
            if dst.resolve() == src.resolve():
                continue
            dst.unlink()
        elif dst.exists():
            print(
                f"  WARN: {dst} exists and is not a symlink; leaving as-is",
                file=sys.stderr,
            )
            continue
        os.symlink(src.resolve(), dst)

    # Real negative_controls/ dir
    nc_out = out_batch / "negative_controls"
    if nc_out.is_symlink():
        nc_out.unlink()
    nc_out.mkdir(parents=True, exist_ok=True)

    # Copy + rewrite batch_manifest.json so the analyze classifier reads
    # NC packages from the hybrid path.
    src_manifest = in_batch / "batch_manifest.json"
    if src_manifest.exists():
        manifest = json.loads(src_manifest.read_text())

        def _rewrite_path(p: str) -> str:
            in_str = str(in_batch)
            if p.startswith(in_str):
                return str(out_batch) + p[len(in_str):]
            in_abs = str(in_batch.resolve())
            out_abs = str(out_batch.resolve())
            if p.startswith(in_abs):
                return out_abs + p[len(in_abs):]
            return p

        rewritten = 0
        for entry in manifest.get("perSpecResults", []):
            cov = entry.get("coverage_intent", "")
            if cov != "negative_control":
                continue
            old = entry.get("out_dir", "")
            new = _rewrite_path(old)
            if old != new:
                entry["out_dir"] = new
                rewritten += 1
        print(f"  ✓ rewrote {rewritten} NC out_dir paths in batch_manifest")

        dst_manifest = out_batch / "batch_manifest.json"
        if dst_manifest.is_symlink():
            dst_manifest.unlink()
        with open(dst_manifest, "w") as f:
            json.dump(manifest, f, indent=2)


def _copy_per_spec_manifest(src_pkg: Path, dst_pkg: Path) -> None:
    src_manifest = src_pkg.parent / "manifest.json"
    dst_manifest = dst_pkg.parent / "manifest.json"
    if not src_manifest.exists():
        return
    if dst_manifest.exists():
        return
    shutil.copyfile(src_manifest, dst_manifest)


def _patch_one_package(
    src: Path, dst: Path, key: Path, *, dry_run: bool,
) -> PatchOutcome:
    spec_id = src.parent.name
    variant = src.stem

    try:
        doc = json.loads(src.read_text())
    except Exception as e:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED", note=f"json-parse-error: {e}",
        )

    new_doc, patched = _patch_doc(doc)
    status = "PATCHED" if patched else "SKIP_NO_PATCH_NEEDED"

    if dry_run:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status=status, note="dry-run",
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    _copy_per_spec_manifest(src, dst)

    with open(dst, "w", encoding="utf-8") as f:
        json.dump(new_doc, f, indent=2, ensure_ascii=False)

    try:
        sign_file(dst, key)
    except Exception as e:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED", note=f"sign-failure: {e}",
        )

    return PatchOutcome(
        spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
        status=status,
    )


def _walk_nc_packages(in_batch: Path):
    nc_root = in_batch / "negative_controls"
    for spec_dir in sorted(nc_root.iterdir()):
        if not spec_dir.is_dir() or spec_dir.name.startswith("."):
            continue
        if spec_dir.name == "failed":
            continue
        for pkg in sorted(spec_dir.glob("*.jsonld")):
            yield pkg


def run(
    in_batch: Path,
    out_batch: Path,
    key: Path,
    *,
    dry_run: bool = False,
    report_path: Path | None = None,
) -> int:
    if not in_batch.exists():
        print(f"FATAL: in_batch does not exist: {in_batch}", file=sys.stderr)
        return 1
    if not key.exists():
        print(f"FATAL: signing key does not exist: {key}", file=sys.stderr)
        return 1

    print("=== v0.5.12 NC corpus consistency-stub regen ===")
    print(f"  in-batch:  {in_batch}")
    print(f"  out-batch: {out_batch}")
    print(f"  key:       {key}")
    print(f"  dry-run:   {dry_run}")
    print()

    if not dry_run:
        _materialize_hybrid_batch(in_batch, out_batch)
        print(f"  ✓ hybrid batch materialized at {out_batch}")

    outcomes: list[PatchOutcome] = []
    for src in _walk_nc_packages(in_batch):
        rel = src.relative_to(in_batch)
        dst = out_batch / rel
        outcomes.append(_patch_one_package(src, dst, key, dry_run=dry_run))

    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    print(f"\n=== Summary ===")
    print(f"  Total NC packages: {len(outcomes)}")
    for status in ("PATCHED", "SKIP_NO_PATCH_NEEDED", "FAILED"):
        print(f"  {status}: {counts.get(status, 0)}")

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "spec_id", "variant", "src_path", "dst_path",
                "status", "note",
            ])
            w.writeheader()
            for o in outcomes:
                w.writerow(o.to_csv_row())
        print(f"  report → {report_path}")

    return 0 if counts.get("FAILED", 0) == 0 else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--in-batch", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-28-v0511"),
        help="source batch dir (typically the v0.5.11 hybrid). Read-only.",
    )
    p.add_argument(
        "--out-batch", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-29-v0512"),
        help="hybrid output batch dir (created if missing).",
    )
    p.add_argument(
        "--key", type=Path, default=Path("keys/research.key"),
        help="ed25519 private key for re-signing patched NCs.",
    )
    p.add_argument("--dry-run", action="store_true",
                   help="report what would change without writing or symlinking.")
    p.add_argument("--report", type=Path, default=None,
                   help="write per-package CSV report to this path.")
    args = p.parse_args(argv)
    return run(
        in_batch=args.in_batch,
        out_batch=args.out_batch,
        key=args.key,
        dry_run=args.dry_run,
        report_path=args.report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
