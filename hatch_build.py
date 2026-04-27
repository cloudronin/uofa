"""Hatchling custom build hook for UofA wheel bundling.

Activates only when UOFA_BUNDLE_JAR=1 is set; otherwise no-op so that
editable installs (pip install -e .) and source-tree dev work continue to
function without any wheel-build machinery.

PR 1 scope: bundle the pre-built rule-engine JAR into the wheel. Later PRs
will extend this hook to also bundle a per-platform JRE driven by
UOFA_BUNDLE_PLATFORM.

Environment variables:
    UOFA_BUNDLE_JAR=1     Activate the hook.
    UOFA_JAR_PATH=<path>  Override the default JAR source location
                          (defaults to weakener-engine/target/<jar>).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


_JAR_NAME = "uofa-weakener-engine-0.1.0.jar"


class UofaBundleHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        if os.environ.get("UOFA_BUNDLE_JAR") != "1":
            return

        src = self._resolve_jar_source()
        dest_dir = Path(self.root) / "src" / "uofa_cli" / "_engine"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / _JAR_NAME

        shutil.copy2(src, dest)
        print(
            f"[uofa-build] bundled JAR: {src} -> {dest.relative_to(Path(self.root))}",
            file=sys.stderr,
        )

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
                f"UOFA_BUNDLE_JAR=1 set but JAR not found at {default}.\n"
                "  Build it: cd weakener-engine && mvn package\n"
                "  Or set UOFA_JAR_PATH to an alternate location."
            )
        return default
