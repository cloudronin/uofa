"""v0.5.11 NC corpus offset-rationale patch tool.

Materializes a hybrid M5 batch dir whose `negative_controls/` subtree has
placeholder `uofa:hasOffsetRationale` injected into the DecisionRecord
of every NC package whose `decision == 'Accepted'` AND any
CredibilityFactor has `achievedLevel < requiredLevel`. This eliminates
the W-AR-02 vacuous-noValue firing on 42 NCs that faithfully reproduce
the Nagaraja-paper Test-conditions shortfall pattern.

Mirrors the v0.5.10 W-ON-02 pattern (`tools/phase2_5/regen_nc_envelope.py`):
hybrid batch dir with symlinks for non-NC subdirs, real `negative_controls/`,
batch_manifest.json copied + NC `out_dir` rewritten, per-spec
`manifest.json` copied into hybrid spec dirs.

Operations:

1. Materialize hybrid output batch dir at ``--out-batch``:

   * `confirm_existing/`, `gap_probe/`, `interaction/`, `coverage/`,
     `failed/`, `metadata/`, `review_packets/` → symlink to
     ``--in-batch``
   * `negative_controls/` → real (mkdir) directory with patched copies
   * `batch_manifest.json` → copied with NC `out_dir` paths rewritten
     so analyze classifier reads from hybrid (not source)
   * Per-spec `manifest.json` copied into each hybrid NC spec dir

2. For each NC package under ``<in-batch>/negative_controls/adv-*/adv-*.jsonld``:

   * Skip ``failed/`` subtree
   * Read JSON. Inspect ``doc["hasDecisionRecord"]`` and
     ``doc["hasCredibilityFactor"]``.
   * If decision outcome is NOT 'Accepted' → write unchanged + re-sign;
     mark ``SKIP_NOT_ACCEPTED``.
   * If no factor has ``achievedLevel < requiredLevel`` → write
     unchanged + re-sign; mark ``SKIP_NO_SHORTFALL``.
   * For each shortfall factor, build an OffsetRationale stub and
     append to ``hasDecisionRecord.hasOffsetRationale``. If the DR
     already has an OffsetRationale referring to the factor, skip that
     factor (idempotent). If all shortfall factors are already offset,
     mark ``SKIP_ALREADY_OFFSET``.
   * Else → mark ``PATCHED`` with a count of factors offset.
   * Write to mirrored path under ``--out-batch``.
   * Re-sign via ``uofa_cli.integrity.sign_file``.

3. Print summary table; optional ``--report <path>`` writes per-package
   CSV.

Idempotent: re-running on an already-patched directory is a no-op
(the helper short-circuits when the relevant offset is already present).

CLI:

    python -m tools.phase2_5.regen_nc_offset_rationale \\
        --in-batch dev/build/adversarial/phase2/2026-04-28-v0510 \\
        --out-batch dev/build/adversarial/phase2/2026-04-28-v0511 \\
        --key keys/research.key \\
        [--dry-run] [--report regen_offset_report.csv]
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

from uofa_cli.adversarial.skeleton import (
    _augment_dr_with_offset_rationale,
    make_offset_rationale_stub,
)
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
    status: str          # PATCHED | SKIP_NOT_ACCEPTED | SKIP_NO_SHORTFALL | SKIP_ALREADY_OFFSET | FAILED
    factors_offset: int = 0
    note: str = ""

    def to_csv_row(self) -> dict:
        return {
            "spec_id": self.spec_id,
            "variant": self.variant,
            "src_path": str(self.src_path),
            "dst_path": str(self.dst_path),
            "status": self.status,
            "factors_offset": self.factors_offset,
            "note": self.note,
        }


# NOTE: ``make_offset_rationale_stub`` and ``_augment_dr_with_offset_rationale``
# are imported from ``uofa_cli.adversarial.skeleton`` (Phase 2.5 v0.5.12.1).
# Previously they lived here but were unimportable from the installed wheel,
# silently breaking the post-LLM hook in `uofa adversarial generate`. The
# patch tool re-uses the same helpers so the corpus-regen logic is identical
# whether applied at generation time or post-hoc on existing M5 corpus.


def _materialize_hybrid_batch(in_batch: Path, out_batch: Path) -> None:
    """Create out_batch with symlinks to non-NC subdirs and an empty
    negative_controls/ ready for patched copies.

    Mirrors `tools/phase2_5/regen_nc_envelope.py` so future v0.5.x
    corpus-regen patches can chain (in_batch may itself be a v0.5.10
    hybrid batch, in which case we follow the symlinks back to M5).
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
    # NC packages from the new hybrid path.
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

    dr = doc.get("hasDecisionRecord")
    if not isinstance(dr, dict):
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED",
            note=f"hasDecisionRecord is not an inline object: {type(dr).__name__}",
        )

    if dr.get("outcome") != "Accepted":
        status = "SKIP_NOT_ACCEPTED"
        new_offsets = []
    else:
        new_doc, new_offsets = _augment_dr_with_offset_rationale(deepcopy(doc))
        # Determine status: shortfall existed? was it already offset?
        cf = doc.get("hasCredibilityFactor", [])
        if not isinstance(cf, list):
            cf = [cf] if cf else []
        has_shortfall = any(
            isinstance(f, dict)
            and (f.get("requiredLevel") is not None and
                 f.get("achievedLevel") is not None and
                 f.get("achievedLevel") < f.get("requiredLevel"))
            for f in cf
        )
        if not has_shortfall:
            status = "SKIP_NO_SHORTFALL"
        elif not new_offsets:
            status = "SKIP_ALREADY_OFFSET"
        else:
            status = "PATCHED"
            doc = new_doc

    if dry_run:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status=status, factors_offset=len(new_offsets), note="dry-run",
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    _copy_per_spec_manifest(src, dst)

    with open(dst, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    try:
        sign_file(dst, key)
    except Exception as e:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED", note=f"sign-failure: {e}",
        )

    return PatchOutcome(
        spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
        status=status, factors_offset=len(new_offsets),
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

    print("=== v0.5.11 NC corpus offset-rationale regen ===")
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
    factors_offset_total = 0
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
        factors_offset_total += o.factors_offset
    print(f"\n=== Summary ===")
    print(f"  Total NC packages: {len(outcomes)}")
    for status in (
        "PATCHED", "SKIP_NO_SHORTFALL", "SKIP_NOT_ACCEPTED",
        "SKIP_ALREADY_OFFSET", "FAILED",
    ):
        print(f"  {status}: {counts.get(status, 0)}")
    print(f"  Total factor-offset rationales injected: {factors_offset_total}")

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "spec_id", "variant", "src_path", "dst_path",
                "status", "factors_offset", "note",
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
        default=Path("dev/build/adversarial/phase2/2026-04-28-v0510"),
        help="source batch dir (typically the v0.5.10 hybrid; otherwise an M5 batch). Read-only.",
    )
    p.add_argument(
        "--out-batch", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-28-v0511"),
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
