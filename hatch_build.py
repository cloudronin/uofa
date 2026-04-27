"""Hatchling custom build hook for UofA wheel bundling.

Activates only when UOFA_BUNDLE_JAR=1 or UOFA_BUNDLE_PLATFORM=<tag> is set;
otherwise no-op so editable installs (pip install -e .) and source-tree dev
work continue to function without any wheel-build machinery.

Modes:
    UOFA_BUNDLE_JAR=1
        Bundle the pre-built rule-engine JAR. Produces a py3-none-any wheel
        that still requires system Java 17+ at runtime.

    UOFA_BUNDLE_PLATFORM=<wheel-platform-tag>   (e.g. manylinux_2_28_x86_64)
        Bundle BOTH the JAR and a per-platform OpenJDK 17 LTS JRE from
        Eclipse Adoptium. Produces a py3-none-<platform> wheel that requires
        no system Java at runtime. The JRE URL + SHA256 + strip prefix come
        from jre_manifest.toml; refresh via scripts/refresh_jre_manifest.py.

Environment variables:
    UOFA_JAR_PATH=<path>    Override the default JAR source location
                            (defaults to weakener-engine/target/<jar>).
    UOFA_KEEP_BUNDLE=1      Skip the post-build cleanup of staged artifacts
                            (useful when inspecting a wheel build by hand).

Cleanup behavior: the staged JAR + JRE are removed from the source tree
in finalize(), AFTER the wheel is sealed. This prevents the bundled
artifacts from shadowing system Java for subsequent editable-install or
test runs in the same checkout — a wrong-architecture JRE on PATH causes
"Exec format error" at runtime.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


_JAR_NAME = "uofa-weakener-engine-0.1.0.jar"


def _load_toml(path: Path) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
    with path.open("rb") as f:
        return tomllib.load(f)


class UofaBundleHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        bundle_platform = os.environ.get("UOFA_BUNDLE_PLATFORM") or None
        bundle_jar = bundle_platform is not None or os.environ.get("UOFA_BUNDLE_JAR") == "1"

        if not bundle_jar:
            return

        self._bundle_jar()
        if bundle_platform:
            self._bundle_jre(bundle_platform, build_data)

    def finalize(self, version: str, build_data: dict, artifact_path: str) -> None:
        if os.environ.get("UOFA_KEEP_BUNDLE") == "1":
            return
        bundle_platform = os.environ.get("UOFA_BUNDLE_PLATFORM") or None
        bundle_jar = bundle_platform is not None or os.environ.get("UOFA_BUNDLE_JAR") == "1"
        if not bundle_jar:
            return
        self._cleanup_staged()

    def _cleanup_staged(self) -> None:
        """Remove staged artifacts so they don't shadow system Java post-build.

        Without this, a Linux x86_64 JRE staged under src/uofa_cli/_runtime/
        on a macOS dev box causes 'Exec format error' the next time the
        contributor runs the test suite from the same checkout.
        """
        root = Path(self.root)
        targets = [
            root / "src" / "uofa_cli" / "_engine" / _JAR_NAME,
            root / "src" / "uofa_cli" / "_runtime" / "jre",
            root / "src" / "uofa_cli" / "_runtime" / "PLATFORM",
            root / "src" / "uofa_cli" / "_runtime" / "JRE_VERSION",
        ]
        for path in targets:
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self._log(f"cleanup: removed {path.relative_to(root)}")

    # ── JAR bundling ──────────────────────────────────────────────

    def _bundle_jar(self) -> None:
        src = self._resolve_jar_source()
        dest_dir = Path(self.root) / "src" / "uofa_cli" / "_engine"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / _JAR_NAME
        shutil.copy2(src, dest)
        self._log(f"bundled JAR: {src} -> {dest.relative_to(Path(self.root))}")

    def _resolve_jar_source(self) -> Path:
        explicit = os.environ.get("UOFA_JAR_PATH")
        if explicit:
            p = Path(explicit)
            if not p.exists():
                raise FileNotFoundError(f"UOFA_JAR_PATH={p} does not exist.")
            return p

        default = Path(self.root) / "weakener-engine" / "target" / _JAR_NAME
        if not default.exists():
            raise FileNotFoundError(
                f"Bundled-wheel build requested but JAR not found at {default}.\n"
                "  Build it: cd weakener-engine && mvn package\n"
                "  Or set UOFA_JAR_PATH to an alternate location."
            )
        return default

    # ── JRE bundling ──────────────────────────────────────────────

    def _bundle_jre(self, platform_tag: str, build_data: dict) -> None:
        manifest_path = Path(self.root) / "jre_manifest.toml"
        manifest = _load_toml(manifest_path)
        platforms = manifest.get("platforms", {})
        entry = platforms.get(platform_tag)
        if entry is None:
            raise ValueError(
                f"UOFA_BUNDLE_PLATFORM={platform_tag} not in jre_manifest.toml. "
                f"Known platforms: {list(platforms)}"
            )

        url = entry["url"]
        expected_sha = entry["sha256"]
        strip_prefix = entry["strip_prefix"]
        archive_format = entry["archive_format"]
        # Per-platform JRE version (Adoptium rolls out unevenly across
        # platforms, so a single global label would mislabel half the wheels).
        release = entry.get("version", "unknown")

        runtime_dir = Path(self.root) / "src" / "uofa_cli" / "_runtime"
        jre_dir = runtime_dir / "jre"
        if jre_dir.exists():
            shutil.rmtree(jre_dir)
        runtime_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive_path = tmp_path / f"jre.{archive_format}"
            self._log(f"downloading JRE: {url}")
            self._download_with_sha(url, archive_path, expected_sha)

            extract_dir = tmp_path / "extract"
            extract_dir.mkdir()
            self._extract(archive_path, extract_dir, archive_format)

            # Adoptium archives extract to a single top-level directory like
            # 'jdk-17.0.19+10-jre/'; strip that prefix into _runtime/jre/.
            source_root = extract_dir / strip_prefix
            if not source_root.exists():
                # macOS Adoptium archives nest under Contents/Home (handled
                # in PR 3 via a different strip_prefix in the manifest).
                contents = sorted(p.name for p in extract_dir.iterdir())
                raise FileNotFoundError(
                    f"Expected directory '{strip_prefix}' inside the archive; "
                    f"top-level contents: {contents}"
                )
            shutil.copytree(source_root, jre_dir, symlinks=True)

        # Marker files for diagnostics; paths.py does not consume them.
        (runtime_dir / "PLATFORM").write_text(platform_tag + "\n")
        (runtime_dir / "JRE_VERSION").write_text(release + "\n")

        # Sanity-check: the java binary the runtime helper expects must exist.
        java_name = "java.exe" if platform_tag.startswith("win_") else "java"
        java = jre_dir / "bin" / java_name
        if not java.exists():
            raise FileNotFoundError(
                f"Bundled JRE missing java binary at {java.relative_to(Path(self.root))}"
            )

        # Mark the wheel as platform-specific so pip serves the right one.
        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{platform_tag}"
        self._log(f"bundled JRE: {release} ({platform_tag})")

    @staticmethod
    def _download_with_sha(url: str, dest: Path, expected_sha: str) -> None:
        # Adoptium and other download hosts reject blank User-Agents.
        req = urllib.request.Request(url, headers={"User-Agent": "uofa-build/1.0"})
        h = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as f:
            while True:
                chunk = resp.read(1 << 20)  # 1 MiB
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
        actual = h.hexdigest()
        if actual != expected_sha:
            dest.unlink(missing_ok=True)
            raise ValueError(
                f"SHA256 mismatch for {url}\n"
                f"  expected: {expected_sha}\n"
                f"  actual:   {actual}"
            )

    @staticmethod
    def _extract(archive: Path, dest: Path, fmt: str) -> None:
        if fmt == "tar.gz":
            # System tar preserves permissions, symlinks, and (on macOS) the
            # extended attributes that Python's tarfile silently drops —
            # critical for macOS Gatekeeper acceptance of bundled binaries.
            subprocess.run(
                ["tar", "-xzf", str(archive), "-C", str(dest)],
                check=True,
            )
        elif fmt == "zip":
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(dest)
        else:
            raise ValueError(f"Unsupported archive_format: {fmt}")

    @staticmethod
    def _log(msg: str) -> None:
        print(f"[uofa-build] {msg}", file=sys.stderr)
