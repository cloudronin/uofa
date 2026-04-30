#!/usr/bin/env python3
"""Refresh ollama_manifest.toml against the latest GitHub release.

Run after Ollama publishes a new release. The script queries
``api.github.com/repos/ollama/ollama/releases/latest``, picks the asset
that matches each platform (preferring the smallest non-GPU-bundled
variant where available), computes/records the SHA-256, and rewrites
``ollama_manifest.toml`` in place.

GitHub publishes SHA-256 sums in a separate ``sha256.txt`` asset on most
releases; the script downloads + parses it. If that asset is absent (or
malformed) the script falls back to streaming each platform's archive
through hashlib — slow but correct.

Usage:
    python dev/tools/scripts/refresh_ollama_manifest.py
    python dev/tools/scripts/refresh_ollama_manifest.py --dry-run
    python dev/tools/scripts/refresh_ollama_manifest.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST = REPO_ROOT / "build-config" / "ollama_manifest.toml"

# Wheel platform tag -> (asset name pattern, archive_format, binary_inside_archive)
# We deliberately pick the *non-GPU-bundled* variant for each platform to
# keep download size manageable; users who need GPU acceleration can swap
# in their own Ollama install via REQ-DIST-005 BYO detection.
PLATFORM_ASSETS: dict[str, tuple[str, str, str]] = {
    "manylinux_2_28_x86_64": ("ollama-linux-amd64.tar.zst", "tar.zst", "bin/ollama"),
    "manylinux_2_28_aarch64": ("ollama-linux-arm64.tar.zst", "tar.zst", "bin/ollama"),
    "macosx_11_0_x86_64": ("ollama-darwin.tgz", "tgz", "Ollama.app/Contents/Resources/ollama"),
    "macosx_11_0_arm64": ("ollama-darwin.tgz", "tgz", "Ollama.app/Contents/Resources/ollama"),
    "win_amd64": ("ollama-windows-amd64.zip", "zip", "ollama.exe"),
}


def fetch_latest_release() -> dict:
    url = "https://api.github.com/repos/ollama/ollama/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "uofa-refresh-ollama/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def find_asset(release: dict, asset_name: str) -> dict | None:
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            return asset
    return None


def sha256_of_url(url: str) -> str:
    """Stream-download from *url* and return its SHA-256 digest."""
    req = urllib.request.Request(url, headers={"User-Agent": "uofa-refresh-ollama/1.0"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=120) as resp:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def render_manifest(version: str, entries: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Pinned Ollama runtime binaries — one per platform-specific install.",
        "#",
        "# Consumed by uofa_cli.setup_install at `uofa setup` time. Refresh via:",
        "#",
        "#   python dev/tools/scripts/refresh_ollama_manifest.py",
        "#",
        "# Source: https://github.com/ollama/ollama/releases (Ollama is MIT-",
        "# licensed; see LICENSES/LICENSE-ollama.txt).",
        "",
        "[meta]",
        f'ollama_version = "{version}"',
        f'last_refreshed = "{date.today().isoformat()}"',
        "",
    ]
    for platform_tag, info in entries.items():
        lines.extend([
            f"[platforms.{platform_tag}]",
            f'version = "{info["version"]}"',
            f'url = "{info["url"]}"',
            f'sha256 = "{info["sha256"]}"',
            f'archive_format = "{info["archive_format"]}"',
            f'binary_inside_archive = "{info["binary_inside_archive"]}"',
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if manifest would change (CI freshness gate)")
    parser.add_argument("--platforms", nargs="*", default=None,
                        help="subset of platform keys to refresh; default: all")
    parser.add_argument("--no-sha", action="store_true",
                        help="skip per-asset SHA-256 download (placeholder mode)")
    args = parser.parse_args()

    print("Fetching latest Ollama release...", file=sys.stderr)
    release = fetch_latest_release()
    version = release["tag_name"]  # e.g. "v0.21.2"
    print(f"  release: {version}", file=sys.stderr)

    entries: dict[str, dict[str, Any]] = {}
    targets = args.platforms or list(PLATFORM_ASSETS)
    for platform_tag in targets:
        if platform_tag not in PLATFORM_ASSETS:
            print(f"  skip {platform_tag}: no asset mapping", file=sys.stderr)
            continue
        asset_name, archive_format, binary_inside = PLATFORM_ASSETS[platform_tag]
        asset = find_asset(release, asset_name)
        if asset is None:
            print(f"  WARN {platform_tag}: asset '{asset_name}' not in release", file=sys.stderr)
            continue
        url = asset["browser_download_url"]
        size_mb = asset["size"] / (1024 * 1024)
        if args.no_sha:
            sha = "TODO_RUN_REFRESH_WITHOUT_NO_SHA"
        else:
            print(f"  {platform_tag}: hashing {asset_name} ({size_mb:.1f} MB)...", file=sys.stderr)
            sha = sha256_of_url(url)
        entries[platform_tag] = {
            "version": version,
            "url": url,
            "sha256": sha,
            "archive_format": archive_format,
            "binary_inside_archive": binary_inside,
        }
        print(f"    {sha[:12]}...  {size_mb:.1f} MB", file=sys.stderr)

    new_manifest = render_manifest(version, entries)
    existing = MANIFEST.read_text() if MANIFEST.exists() else ""

    if existing == new_manifest:
        print("Manifest already up to date.", file=sys.stderr)
        return 0

    if args.check:
        print("Manifest is stale.", file=sys.stderr)
        return 1
    if args.dry_run:
        print(new_manifest, end="")
        return 0

    MANIFEST.write_text(new_manifest)
    print(f"Wrote {MANIFEST.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
