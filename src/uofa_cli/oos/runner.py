"""Python wrapper that invokes the Java OOS engine via subprocess.

Mirrors the C3 wrapper pattern in `uofa_cli/commands/rules.py:run_structured()`:
locates the Java binary and the unified fat JAR via `paths.py`, builds the
subprocess argv (using the `oos` subcommand of net.uofa.Engine), spawns,
and parses the JSON result file the engine writes to a temp path.

Returns `None` when the resolved `OOSConfig` says OOS is disabled — callers
omit the `oos_results` field from the report entirely (per spec §1.4 and the
load-bearing "omit None fields" rule that preserves byte-identical reports).
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli import paths
from uofa_cli.oos.config import OOSConfig


DEFAULT_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class OOSResult:
    """Structured result of one OOS engine invocation.

    `firings` is the parsed JSON array the Java engine writes — one element
    per OOS verdict (rule × candidate-binding pair). Each element matches the
    schema in `src/uofa_cli/oos/SCHEMA_NOTES.md` §2 (top-level fields plus a
    nested `evidence_gap` with `path_two_metadata`).

    `provenance` records which path activated OOS (per OOSConfig.source) so
    report consumers can tell at a glance whether OOS was on or off because
    of pack config, CLI flag, or pack absence — used by spec §2.4.
    """

    config: OOSConfig
    returncode: int
    firings: list[dict] = field(default_factory=list)
    raw_stdout: str = ""
    raw_stderr: str = ""

    @property
    def provenance(self) -> dict:
        return {
            "source": self.config.source,
            "rule_files_loaded": [str(rf) for rf in self.config.rule_files],
        }


def run_structured(
    package_path: Path,
    config: OOSConfig,
    *,
    context_path: Path | None = None,
    root: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> OOSResult | None:
    """Invoke the Java OOS engine. Returns None if `config.enabled` is False.

    Caller is responsible for omitting the `oos_results` / `oos_provenance`
    fields from the unified report when this returns None — that's how
    byte-identical compatibility with pre-OOS reports is preserved
    (spec §1.4, §5.5).
    """
    if not config.enabled:
        return None

    if not package_path.exists():
        raise FileNotFoundError(f"Package not found: {package_path}")

    java = paths.java_executable()
    jar = paths.jar_path(root=root)
    if not jar.exists():
        raise FileNotFoundError(
            f"OOS engine JAR not found: {jar}. "
            f"Run: cd src/weakener-engine && mvn package"
        )
    ctx = context_path or paths.context_file(root=root)

    # Engine writes results to a JSON file. Use a temp file scoped to this
    # call so concurrent invocations don't trample each other.
    with tempfile.NamedTemporaryFile(
        suffix=".json", prefix="oos_engine_", delete=False
    ) as tmp:
        out_path = Path(tmp.name)

    try:
        cmd = [
            java, "-jar", str(jar), "oos",
            "--package", str(package_path),
            "--context", str(ctx),
            "--output", str(out_path),
        ]
        for rf in config.rule_files:
            cmd.extend(["--rules", str(rf)])

        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

        firings: list[dict] = []
        if out_path.exists() and out_path.stat().st_size > 0:
            try:
                firings = json.loads(out_path.read_text(encoding="utf-8"))
                if not isinstance(firings, list):
                    raise RuntimeError(
                        f"OOS engine produced non-array JSON output: "
                        f"{type(firings).__name__}"
                    )
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"OOS engine produced invalid JSON at {out_path}: {exc}\n"
                    f"engine stderr:\n{completed.stderr}"
                ) from exc

        if completed.returncode != 0:
            # Surface the engine's stderr so the failure is diagnosable.
            raise RuntimeError(
                f"OOS engine exited non-zero ({completed.returncode}).\n"
                f"stderr:\n{completed.stderr}"
            )

        return OOSResult(
            config=config,
            returncode=completed.returncode,
            firings=firings,
            raw_stdout=completed.stdout,
            raw_stderr=completed.stderr,
        )
    finally:
        out_path.unlink(missing_ok=True)
