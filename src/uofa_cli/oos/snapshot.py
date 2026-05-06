"""Stable JSON serializer for `CheckResult`.

Used in three places:
  - T3 baseline capture: snapshots cal-02[1-5] reports under the pre-OOS code
    path into `tests/fixtures/baseline_reports/`.
  - T7 CLI integration: `uofa check --json` output mode writes this same shape.
  - T8 backward-compat regression test (§5.5): byte-compare a fresh `--json`
    run against the baseline.

Stability rules:
  - Drop volatile fields (raw_stdout/stderr, raw_text, file timestamps).
  - Path → repo-relative POSIX string.
  - Lists of dicts (violations, firings) sorted canonically.
  - `None` fields are OMITTED from the output (not serialized as `null`).
    This is what makes "OOS disabled → field absent" work for byte-identical
    backward compat per spec §1.4 and §5.5.
"""

from __future__ import annotations

import json
from dataclasses import is_dataclass, fields
from pathlib import Path
from typing import Any


def _path_to_relative(p: Path | str | None, repo_root: Path | None) -> str | None:
    if p is None:
        return None
    p = Path(p)
    if repo_root is not None:
        try:
            return p.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            pass
    return p.as_posix()


def _sort_firings(firings: list[dict]) -> list[dict]:
    """Canonical sort by (patternId, affectedNode, owner) tuples."""
    return sorted(
        firings,
        key=lambda f: (
            f.get("patternId", ""),
            f.get("affectedNode", ""),
            f.get("owner", ""),
        ),
    )


def _sort_violations(violations: list[dict]) -> list[dict]:
    """Canonical sort by (severity, path, focus_node, message)."""
    return sorted(
        violations,
        key=lambda v: (
            v.get("severity", ""),
            v.get("path", ""),
            v.get("focus_node", ""),
            v.get("message", ""),
        ),
    )


def _strip_volatile(obj: Any) -> Any:
    """Drop fields that vary between runs without semantic meaning.

    Currently strips:
      - raw_stdout, raw_stderr (RulesResult)
      - raw_text (ShaclResult)
      - format (RulesResult — orthogonal to firings; mode of invocation)
      - output_path (RulesResult — None at run_structured layer)
      - exit_code (ShaclResult — derivable from `conforms`)
    """
    VOLATILE = {"raw_stdout", "raw_stderr", "raw_text", "format",
                "output_path", "exit_code"}
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in VOLATILE}
    return obj


def to_stable_dict(check_result: Any, repo_root: Path | None = None) -> dict:
    """Convert a `CheckResult` (from uofa_cli.commands.check) to a stable dict.

    The shape is the v0.1 JSON contract for `uofa check --json`. Adding the
    OOS phase later means an additional optional `oos` field; when None it is
    omitted entirely so pre-OOS baseline reports remain byte-identical.
    """
    if not is_dataclass(check_result):
        raise TypeError(
            f"Expected dataclass, got {type(check_result).__name__}"
        )

    result: dict = {}
    for f in fields(check_result):
        name = f.name
        value = getattr(check_result, name)
        # Omit None fields entirely (this is the load-bearing rule).
        if value is None:
            continue
        result[name] = _serialize_value(name, value, repo_root)
    return _strip_volatile(result)


def _serialize_value(name: str, value: Any, repo_root: Path | None) -> Any:
    if isinstance(value, Path):
        # Several Path fields carry user/host context; relativize.
        if name in {"file", "pubkey_path"}:
            return _path_to_relative(value, repo_root)
        return _path_to_relative(value, repo_root)
    if is_dataclass(value):
        # Special-case OOSResult: emit the spec §2.4 shape (results +
        # provenance) rather than the dataclass's internal field layout.
        # Drops volatile config / raw_stdout / raw_stderr / returncode and
        # keeps the JSON contract aligned with what report consumers expect.
        cls = value.__class__
        if cls.__name__ == "OOSResult" and cls.__module__ == "uofa_cli.oos.runner":
            return {
                "results": list(value.firings),
                "provenance": {
                    "source": value.config.source,
                    "rule_files_loaded": [
                        _path_to_relative(p, repo_root)
                        for p in value.config.rule_files
                    ],
                },
            }
        nested = {}
        for f in fields(value):
            v = getattr(value, f.name)
            if v is None:
                continue
            nested[f.name] = _serialize_value(f.name, v, repo_root)
        nested = _strip_volatile(nested)
        # Field-specific canonical sorts.
        if "firings" in nested and isinstance(nested["firings"], list):
            nested["firings"] = _sort_firings(nested["firings"])
        if "violations" in nested and isinstance(nested["violations"], list):
            nested["violations"] = _sort_violations(nested["violations"])
        return nested
    if isinstance(value, list):
        return [_serialize_value(name, v, repo_root) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(k, v, repo_root) for k, v in value.items()}
    return value


def to_json(check_result: Any, repo_root: Path | None = None,
            indent: int = 2) -> str:
    """Convenience: stable dict → pretty-printed JSON string with sorted keys."""
    return json.dumps(
        to_stable_dict(check_result, repo_root=repo_root),
        indent=indent,
        sort_keys=True,
    )
