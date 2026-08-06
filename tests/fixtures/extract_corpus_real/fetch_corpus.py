#!/usr/bin/env python3
"""Download the Tier 1 source documents and verify them against MANIFEST.json.

The documents are **not vendored**. Every NTRS record in the manifest is marked
`PUBLIC_USE_PERMITTED` with `belongsToUsGov: false` -- public use is permitted,
but they are not US Government works in the public domain, so this repository
does not redistribute them. It ships the ground truth, which is ours, plus a URL
and a SHA-256 for each source, which is enough to reconstruct the corpus and to
prove that what you downloaded is what was transcribed.

    python tests/fixtures/extract_corpus_real/fetch_corpus.py
    python tests/fixtures/extract_corpus_real/fetch_corpus.py --verify-only

A hash mismatch is a hard failure, not a warning. NTRS can replace a file in
place, and a silently changed source would mean the transcribed levels no longer
describe the document being scored -- exactly the kind of drift that makes an
eval number mean less than it appears to.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MANIFEST.json"
UA = {"User-Agent": "uofa-credibility-corpus/1.0 (research; contact via repo)"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bundle_dirs_for(citation_id: str) -> list[Path]:
    """Bundles whose ground truth was transcribed from this citation."""
    out = []
    for gt in sorted(HERE.glob("bundle_*/ground_truth.json")):
        try:
            data = json.loads(gt.read_text())
        except json.JSONDecodeError:
            continue
        if (data.get("_provenance") or {}).get("citation_id") == citation_id:
            out.append(gt.parent)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify-only", action="store_true",
                    help="check hashes of what is already present, download nothing")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    ok = missing = fixed = 0
    failures: list[str] = []

    for cid, rec in sorted(manifest.items()):
        targets = bundle_dirs_for(cid)
        if not targets:
            print(f"  {cid}: no bundle transcribed from it yet, skipping")
            continue
        for f in rec["files"]:
            name, want = f["name"], f["sha256"]
            for bundle in targets:
                dest = bundle / "source" / name
                dest.parent.mkdir(parents=True, exist_ok=True)

                if dest.exists():
                    got = sha256(dest)
                    if got == want:
                        ok += 1
                        continue
                    failures.append(
                        f"{dest.relative_to(HERE)}: sha256 {got[:16]}... != "
                        f"manifest {want[:16]}...")
                    continue

                if args.verify_only:
                    missing += 1
                    print(f"  MISSING {dest.relative_to(HERE)}")
                    continue

                try:
                    req = urllib.request.Request(f["url"], headers=UA)
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = r.read()
                except (urllib.error.URLError, TimeoutError) as exc:
                    failures.append(f"{name}: download failed ({exc})")
                    continue

                got = hashlib.sha256(data).hexdigest()
                if got != want:
                    failures.append(
                        f"{name}: downloaded sha256 {got[:16]}... != "
                        f"manifest {want[:16]}... (the source document changed; "
                        f"re-verify the transcription before updating the manifest)")
                    continue
                dest.write_bytes(data)
                fixed += 1
                print(f"  + {dest.relative_to(HERE)}  {len(data)//1024} KB")

    print(f"\n  verified {ok}, downloaded {fixed}, missing {missing}, "
          f"failed {len(failures)}")
    for msg in failures:
        print(f"  FAIL  {msg}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
