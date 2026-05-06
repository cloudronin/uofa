"""Python wrapper that invokes the Java DerivationEngine via subprocess.

Mirrors the OOS wrapper pattern in `uofa_cli.oos.runner`:
locate Java + the unified fat JAR via `paths.py`, build the subprocess argv
(using the `derive` subcommand of net.uofa.Engine), spawn, and collect the
N-Triples output the engine writes to a temp path.

Returns `None` when the resolved `DerivationConfig` says derivations are
disabled — callers omit the `derivations` field from the report and pass the
ORIGINAL package path to downstream stages (preserving byte-identical
backward compat for packs that don't declare derivations).

When derivations ARE enabled, callers receive an `enriched_package_path`
they should pass to downstream C3/OOS stages instead of the original.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli import paths
from uofa_cli.derivations.config import DerivationConfig


DEFAULT_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class DerivationResult:
    """Structured result of one DerivationEngine invocation.

    `enriched_package_path` is the path to the merged graph (original +
    derived triples) written by the Java engine. Downstream C3/OOS engines
    should read from this path instead of the original package path when
    derivations were active.

    `derived_only_path` is set only when the runner was invoked with
    `derived_only=True` (used by tests that inspect what the pre-pass
    materialized in isolation).
    """

    config: DerivationConfig
    returncode: int
    enriched_package_path: Path | None = None
    derived_only_path: Path | None = None
    construct_count: int = 0
    derived_triple_count: int = 0
    elapsed_seconds: float = 0.0
    raw_stderr: str = ""

    @property
    def provenance(self) -> dict:
        return {
            "source": self.config.source,
            "construct_files_loaded": [str(f) for f in self.config.construct_files],
            "construct_count": self.construct_count,
            "derived_triple_count": self.derived_triple_count,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


def run(
    package_path: Path,
    config: DerivationConfig,
    *,
    context_path: Path | None = None,
    root: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    derived_only: bool = False,
) -> DerivationResult | None:
    """Invoke the Java DerivationEngine. Returns None if config disabled.

    When config.enabled is True, returns a DerivationResult with
    `enriched_package_path` pointing to a temp N-Triples file containing
    the merged graph (original + derived triples). The caller is
    responsible for deleting the temp file when done — typically the
    `check.py` orchestration deletes it after C3 + OOS complete.
    """
    if not config.enabled:
        return None

    if not package_path.exists():
        raise FileNotFoundError(f"Package not found: {package_path}")

    java = paths.java_executable()
    jar = paths.jar_path(root=root)
    if not jar.exists():
        raise FileNotFoundError(
            f"DerivationEngine JAR not found: {jar}. "
            f"Run: cd src/weakener-engine && mvn package"
        )
    ctx = context_path or paths.context_file(root=root)

    # Engine writes enriched graph to N-Triples temp file. Caller should
    # delete after downstream stages complete.
    with tempfile.NamedTemporaryFile(
        suffix=".nt", prefix="uofa_derive_", delete=False
    ) as tmp:
        out_path = Path(tmp.name)

    cmd = [
        java, "-jar", str(jar), "derive",
        "--package", str(package_path),
        "--context", str(ctx),
        "--output", str(out_path),
    ]
    for cf in config.construct_files:
        cmd.extend(["--constructs", str(cf)])
    if derived_only:
        cmd.append("--derived-only")

    start = time.monotonic()
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    elapsed = time.monotonic() - start

    if completed.returncode != 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"DerivationEngine exited non-zero ({completed.returncode}).\n"
            f"stderr:\n{completed.stderr}"
        )

    # Count triples in the output (cheap line count).
    triple_count = 0
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            triple_count = sum(1 for line in f if line.strip() and not line.startswith("#"))

    return DerivationResult(
        config=config,
        returncode=completed.returncode,
        enriched_package_path=out_path if not derived_only else None,
        derived_only_path=out_path if derived_only else None,
        construct_count=len(config.construct_files),
        derived_triple_count=triple_count if derived_only else max(0, triple_count - _count_baseline_triples(package_path, ctx)),
        elapsed_seconds=elapsed,
        raw_stderr=completed.stderr,
    )


# Lightweight helper: load the original package via JsonLdLoader-equivalent
# Python path and count triples. Used only for reporting derived_triple_count
# in non-derived-only mode (subtracts original from merged to show net derived).
# Kept simple — not a hot path.
def _count_baseline_triples(package_path: Path, context_path: Path) -> int:
    """Best-effort baseline triple count via rdflib for derived-count math.

    Returns 0 on any error rather than failing the pipeline. The derived-count
    reporting is informational; the substantive guarantee is the enriched
    file path that downstream stages consume.
    """
    try:
        from rdflib import Graph
        g = Graph()
        # rdflib needs the context inlined; skip-the-fancy by parsing the
        # JSON-LD with rdflib directly (which does its own context resolution)
        g.parse(str(package_path), format="json-ld")
        return len(g)
    except Exception:
        return 0
