#!/usr/bin/env python3
"""Refresh jre_manifest.toml against the latest Eclipse Adoptium 17 LTS GA.

Run quarterly (or after a known-good Adoptium release lands). The script
queries Adoptium's v3 API for each platform we ship a wheel for, updates
the URL + SHA-256 + strip_prefix in jre_manifest.toml, and prints a diff
so a maintainer can review before committing.

The script does NOT auto-commit. It only rewrites the manifest file.

Usage:
    python scripts/refresh_jre_manifest.py
    python scripts/refresh_jre_manifest.py --dry-run    # print, don't write
    python scripts/refresh_jre_manifest.py --check       # exit non-zero if stale
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "jre_manifest.toml"

# Wheel platform tag -> (Adoptium API os, Adoptium API architecture).
PLATFORM_MAP: dict[str, tuple[str, str]] = {
    "manylinux_2_28_x86_64": ("linux", "x64"),
    "manylinux_2_28_aarch64": ("linux", "aarch64"),
    "macosx_11_0_x86_64": ("mac", "x64"),
    "macosx_11_0_arm64": ("mac", "aarch64"),
    "win_amd64": ("windows", "x64"),
}

API_TEMPLATE = (
    "https://api.adoptium.net/v3/assets/feature_releases/17/ga"
    "?architecture={arch}&heap_size=normal&image_type=jre&jvm_impl=hotspot"
    "&os={os}&page=0&page_size=1&project=jdk&sort_method=DEFAULT"
    "&sort_order=DESC&vendor=eclipse"
)


def fetch_latest(os_tag: str, arch: str) -> dict:
    url = API_TEMPLATE.format(os=os_tag, arch=arch)
    # Adoptium's API rejects requests without a recognizable User-Agent,
    # which urllib does not set by default.
    req = urllib.request.Request(url, headers={"User-Agent": "uofa-refresh-jre/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not data:
        raise RuntimeError(f"Adoptium returned no releases for {os_tag}/{arch}")
    release = data[0]
    binary = release["binaries"][0]["package"]
    release_name = release["release_name"]  # e.g. "jdk-17.0.19+10"

    # Adoptium tarballs/zips extract to a top-level directory named
    # "<release>-jre" by convention. On macOS the JRE is wrapped in a
    # BSD-style app bundle, so the actual bin/java lives nested under
    # Contents/Home — strip past it.
    strip_prefix = f"{release_name}-jre"
    if os_tag == "mac":
        strip_prefix = f"{strip_prefix}/Contents/Home"

    fmt = "zip" if binary["name"].endswith(".zip") else "tar.gz"
    return {
        "version": release_name,
        "url": binary["link"],
        "sha256": binary["checksum"],
        "strip_prefix": strip_prefix,
        "archive_format": fmt,
        "size_bytes": binary["size"],
    }


def render_manifest(platform_data: dict[str, dict]) -> str:
    lines: list[str] = [
        "# Pinned OpenJDK 17 LTS JRE binaries — one per platform-specific wheel.",
        "#",
        "# These URLs and checksums are consumed by hatch_build.py at wheel-build",
        "# time when UOFA_BUNDLE_PLATFORM=<key> is set. Refresh quarterly via:",
        "#",
        "#   python scripts/refresh_jre_manifest.py",
        "#",
        "# Source of truth: Eclipse Adoptium Temurin (https://adoptium.net/), the",
        "# OpenJDK distribution we redistribute under GPL-2.0 with Classpath",
        "# Exception. See LICENSES/LICENSE-openjdk.txt.",
        "",
        "[meta]",
        f'last_refreshed = "{date.today().isoformat()}"',
        "",
    ]
    for platform_tag, info in platform_data.items():
        lines.extend([
            f"[platforms.{platform_tag}]",
            f'version = "{info["version"]}"',
            f'url = "{info["url"]}"',
            f'sha256 = "{info["sha256"]}"',
            f'strip_prefix = "{info["strip_prefix"]}"',
            f'archive_format = "{info["archive_format"]}"',
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def load_existing_platforms() -> list[str]:
    """Return ordered list of platform tags currently in the manifest."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    if not MANIFEST.exists():
        # Default to all 5 PR 3 platforms when bootstrapping.
        return list(PLATFORM_MAP.keys())
    with MANIFEST.open("rb") as f:
        data = tomllib.load(f)
    platforms = list(data.get("platforms", {}).keys())
    return platforms or list(PLATFORM_MAP.keys())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print, do not write")
    parser.add_argument(
        "--check", action="store_true",
        help="exit 1 if the manifest would change (CI freshness gate)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="refresh all known platforms (PLATFORM_MAP), not just the "
             "ones currently in the manifest",
    )
    args = parser.parse_args()

    platforms = list(PLATFORM_MAP.keys()) if args.all else load_existing_platforms()
    print(f"Refreshing {len(platforms)} platform(s)...", file=sys.stderr)

    fetched: dict[str, dict] = {}
    for platform_tag in platforms:
        if platform_tag not in PLATFORM_MAP:
            print(f"  skip {platform_tag}: no API mapping", file=sys.stderr)
            continue
        os_tag, arch = PLATFORM_MAP[platform_tag]
        info = fetch_latest(os_tag, arch)
        fetched[platform_tag] = info
        size_mb = info["size_bytes"] / (1024 * 1024)
        print(f"  {platform_tag}: {info['version']} ({size_mb:.1f} MB)", file=sys.stderr)

    new_manifest = render_manifest(fetched)
    existing = MANIFEST.read_text() if MANIFEST.exists() else ""

    if existing == new_manifest:
        print("Manifest already up to date.", file=sys.stderr)
        return 0

    if args.check:
        print("Manifest is stale — run without --check to refresh.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(new_manifest, end="")
        return 0

    MANIFEST.write_text(new_manifest)
    print(f"Wrote {MANIFEST.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
