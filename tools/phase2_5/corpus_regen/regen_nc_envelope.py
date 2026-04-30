"""v0.5.10 NC corpus envelope-stub patch tool.

Materializes a hybrid M5 batch dir whose `negative_controls/` subtree has
placeholder `hasApplicabilityConstraint` and `hasOperatingEnvelope` injected
into every COU. This eliminates the W-ON-02 vacuous-noValue firing on
158 minimal NC packages without modifying the rule predicate (which is
structurally correct).

The tool is the deterministic regenerator referenced by the
v0.5.10-phase2.5-w-on-02-nc-regen tag — re-running it on a fresh M5
checkout reconstructs the v0.5.10 corpus state.

Operations:

1. Materialize hybrid output batch dir at ``--out-batch``:

   * `confirm_existing/`, `gap_probe/`, `interaction/`, `coverage/`,
     `failed/`, `metadata/`, etc. → symlink to corresponding dirs in
     ``--m5-batch`` (preserves M5 corpus pristine).
   * `negative_controls/` → real (mkdir) directory with patched copies.

2. For each NC package under ``<m5-batch>/negative_controls/adv-*/adv-*.jsonld``:

   * Skip ``failed/`` subtree.
   * Load JSON.
   * Inspect ``doc["hasContextOfUse"]``. If both
     ``hasApplicabilityConstraint`` AND ``hasOperatingEnvelope`` are
     present → write unchanged (still re-sign for consistency); mark
     ``SKIP_ALREADY_OK``.
   * Else → inject the missing stub(s) via
     ``uofa_cli.adversarial.skeleton._augment_cou_with_envelope_stubs``;
     mark ``PATCHED``.
   * Write to mirrored path under ``--out-batch``.
   * Re-sign via ``uofa_cli.integrity.sign_file`` against ``--key``.

3. Print summary table; optional ``--report <path>`` writes per-package
   CSV.

Idempotent: re-running on an already-patched directory produces the same
result (the helper short-circuits when both fields are present).

CLI:

    python -m tools.phase2_5.regen_nc_envelope \\
        --m5-batch dev/build/adversarial/phase2/2026-04-26 \\
        --out-batch dev/build/adversarial/phase2/2026-04-28-v0510 \\
        --key keys/research.key \\
        [--dry-run] [--report regen_report.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from uofa_cli.adversarial.skeleton import _augment_cou_with_envelope_stubs
from uofa_cli.integrity import sign_file


# Subdirs of the M5 batch that we symlink (NOT copied/modified) into the
# hybrid output dir. The negative_controls/ subtree is the only one we
# actually rewrite.
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
    status: str          # PATCHED | SKIP_ALREADY_OK | FAILED
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


def _materialize_hybrid_batch(m5_batch: Path, out_batch: Path) -> None:
    """Create out-batch with symlinks to non-NC subdirs and an empty
    negative_controls/ ready for patched copies.

    Idempotent: existing symlinks pointing at the right targets are
    preserved; existing negative_controls/ is reused (the patch loop
    overwrites individual files).
    """
    out_batch.mkdir(parents=True, exist_ok=True)

    for sub in SYMLINK_SUBDIRS:
        src = m5_batch / sub
        dst = out_batch / sub
        if not src.exists():
            continue
        if dst.is_symlink():
            # Already a symlink; verify target. If wrong, re-link.
            if dst.resolve() == src.resolve():
                continue
            dst.unlink()
        elif dst.exists():
            # Real dir/file already there — leave it (may be a manual
            # override). Print a warning.
            print(
                f"  WARN: {dst} exists and is not a symlink; leaving as-is",
                file=sys.stderr,
            )
            continue
        # Use absolute path for the symlink so analyze invocations from
        # any cwd resolve correctly.
        os.symlink(src.resolve(), dst)

    # Real negative_controls/ dir
    nc_out = out_batch / "negative_controls"
    if nc_out.is_symlink():
        # If a stale symlink from an earlier run, remove it.
        nc_out.unlink()
    nc_out.mkdir(parents=True, exist_ok=True)

    # batch_manifest.json: copy (NOT symlink) and rewrite NC perSpecResults
    # `out_dir` so the analyze classifier reads from the patched hybrid
    # NCs instead of the M5 originals. Other intent dirs keep their
    # original paths (which resolve via the symlinked subdirs above).
    #
    # `out_dir` is stored in the manifest as a path relative to the repo
    # root (e.g., "dev/build/adversarial/phase2/2026-04-26/negative_controls/<spec>").
    # We rewrite the m5_batch portion to out_batch — both relative-to-repo
    # and absolute forms.
    src_manifest = m5_batch / "batch_manifest.json"
    if src_manifest.exists():
        manifest = json.loads(src_manifest.read_text())

        def _rewrite_path(p: str) -> str:
            # Try relative form first (most common)
            m5_str = str(m5_batch)
            if p.startswith(m5_str):
                return str(out_batch) + p[len(m5_str):]
            # Then absolute form
            m5_abs = str(m5_batch.resolve())
            out_abs = str(out_batch.resolve())
            if p.startswith(m5_abs):
                return out_abs + p[len(m5_abs):]
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
        # Remove any stale symlink from an earlier run
        if dst_manifest.is_symlink():
            dst_manifest.unlink()
        with open(dst_manifest, "w") as f:
            json.dump(manifest, f, indent=2)


def _copy_per_spec_manifest(src_pkg: Path, dst_pkg: Path) -> None:
    """Copy the per-spec `manifest.json` from M5's spec dir to the hybrid
    spec dir if not already present (or if the hybrid one is stale).

    The per-spec manifest's `packagePath` field is a bare filename (relative
    to the spec dir), so no rewrite needed — just copy.
    """
    src_manifest = src_pkg.parent / "manifest.json"
    dst_manifest = dst_pkg.parent / "manifest.json"
    if not src_manifest.exists():
        return
    if dst_manifest.exists():
        return  # already copied this run
    import shutil
    shutil.copyfile(src_manifest, dst_manifest)


def _patch_one_package(
    src: Path, dst: Path, key: Path, *, dry_run: bool,
) -> PatchOutcome:
    """Read src, optionally inject envelope stubs, write to dst, re-sign.

    Returns a PatchOutcome describing what happened.
    """
    spec_id = src.parent.name
    variant = src.stem

    try:
        doc = json.loads(src.read_text())
    except Exception as e:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED", note=f"json-parse-error: {e}",
        )

    cou = doc.get("hasContextOfUse")
    if not isinstance(cou, dict):
        # Unexpected — NC packages should always have an inline COU.
        # Skip and mark FAILED for visibility.
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status="FAILED",
            note=f"hasContextOfUse is not an inline object: {type(cou).__name__}",
        )

    already_ok = (
        "hasApplicabilityConstraint" in cou
        and "hasOperatingEnvelope" in cou
    )
    status = "SKIP_ALREADY_OK" if already_ok else "PATCHED"

    if not already_ok:
        # Mutate the COU in-place via the shared helper. Use deepcopy so
        # we never accidentally share refs between packages.
        new_cou = _augment_cou_with_envelope_stubs(deepcopy(cou))
        doc["hasContextOfUse"] = new_cou

    if dry_run:
        return PatchOutcome(
            spec_id=spec_id, variant=variant, src_path=src, dst_path=dst,
            status=status, note="dry-run",
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    # Copy the per-spec manifest.json once per spec dir (the analyzer
    # reads it to enumerate variants).
    _copy_per_spec_manifest(src, dst)

    with open(dst, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    # Re-sign — sign_file rewrites hash + signature in place at dst.
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


def _walk_nc_packages(m5_batch: Path):
    """Yield Path objects for every NC package, excluding failed/."""
    nc_root = m5_batch / "negative_controls"
    for spec_dir in sorted(nc_root.iterdir()):
        if not spec_dir.is_dir() or spec_dir.name.startswith("."):
            continue
        if spec_dir.name == "failed":
            continue
        for pkg in sorted(spec_dir.glob("*.jsonld")):
            yield pkg


def run(
    m5_batch: Path,
    out_batch: Path,
    key: Path,
    *,
    dry_run: bool = False,
    report_path: Path | None = None,
) -> int:
    """Top-level: materialize hybrid + patch each NC + write report.

    Returns 0 on success, 1 on any FAILED outcome.
    """
    if not m5_batch.exists():
        print(f"FATAL: m5_batch does not exist: {m5_batch}", file=sys.stderr)
        return 1
    if not key.exists():
        print(f"FATAL: signing key does not exist: {key}", file=sys.stderr)
        return 1

    print(f"=== v0.5.10 NC corpus regen ===")
    print(f"  m5-batch:  {m5_batch}")
    print(f"  out-batch: {out_batch}")
    print(f"  key:       {key}")
    print(f"  dry-run:   {dry_run}")
    print()

    if not dry_run:
        _materialize_hybrid_batch(m5_batch, out_batch)
        print(f"  ✓ hybrid batch materialized at {out_batch}")

    outcomes: list[PatchOutcome] = []
    for src in _walk_nc_packages(m5_batch):
        # Mirror the spec_dir/file structure into out_batch
        rel = src.relative_to(m5_batch)
        dst = out_batch / rel
        outcomes.append(_patch_one_package(src, dst, key, dry_run=dry_run))

    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    print(f"\n=== Summary ===")
    print(f"  Total NC packages: {len(outcomes)}")
    for status in ("PATCHED", "SKIP_ALREADY_OK", "FAILED"):
        print(f"  {status}: {counts.get(status, 0)}")

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "spec_id", "variant", "src_path", "dst_path", "status", "note",
            ])
            w.writeheader()
            for o in outcomes:
                w.writerow(o.to_csv_row())
        print(f"  report → {report_path}")

    return 0 if counts.get("FAILED", 0) == 0 else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--m5-batch", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26"),
        help="M5 baseline batch dir (read-only).",
    )
    p.add_argument(
        "--out-batch", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-28-v0510"),
        help="hybrid output batch dir (created if missing). NC subtree is real; other subdirs are symlinks to --m5-batch.",
    )
    p.add_argument(
        "--key", type=Path, default=Path("keys/research.key"),
        help="ed25519 private key for re-signing patched NCs.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="report what would change without writing or symlinking.",
    )
    p.add_argument(
        "--report", type=Path, default=None,
        help="write per-package CSV report to this path.",
    )
    args = p.parse_args(argv)
    return run(
        m5_batch=args.m5_batch,
        out_batch=args.out_batch,
        key=args.key,
        dry_run=args.dry_run,
        report_path=args.report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
