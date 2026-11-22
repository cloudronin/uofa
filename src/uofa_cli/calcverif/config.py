"""Calculation-verification rules resolver.

A copy of the `uofa_cli.oos.config` pattern with the names changed. Reads the
pack's `calcverif` block and the CLI flags, and returns a `CalcVerifConfig`.

Resolution order:
  1. `--calcverif` and `--no-calcverif` are mutually exclusive (raise).
  2. `--calcverif` set: enabled=True, source="cli_flag_force_on". The pack
     must declare `calcverif.rule_files`, otherwise raise.
  3. `--no-calcverif` set: enabled=False, source="cli_flag_force_off".
  4. Pack `calcverif` block present: use its `enabled` value,
     source="pack_config". The shipped vv40 block says false.
  5. Pack has no `calcverif` block: enabled=False,
     source="pack_default_omitted".

Unlike OOS, the resolved rule files are not run by a separate engine. They
are ordinary forward weakener rules and are appended to the normal C3 rules
list (`rules.run_structured`), so no change to the Java engine is needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli import paths


SOURCE_CLI_FORCE_ON = "cli_flag_force_on"
SOURCE_CLI_FORCE_OFF = "cli_flag_force_off"
SOURCE_PACK_CONFIG = "pack_config"
SOURCE_PACK_DEFAULT_OMITTED = "pack_default_omitted"


class CalcVerifConfigError(ValueError):
    """Raised when the calcverif switch cannot be resolved (both flags given,
    `--calcverif` against a pack with no `calcverif.rule_files`, a declared
    file missing, malformed block).

    The CLI handler prints the message and exits non-zero before any work.
    """


@dataclass(frozen=True)
class CalcVerifConfig:
    """Resolved calcverif decision for one invocation."""

    enabled: bool
    rule_files: list[Path] = field(default_factory=list)
    source: str = SOURCE_PACK_DEFAULT_OMITTED


def resolve(
    pack_name: str,
    *,
    enable_flag: bool = False,
    disable_flag: bool = False,
    root: Path | None = None,
) -> CalcVerifConfig:
    """Resolve the calcverif decision. See the module docstring for the order."""

    if enable_flag and disable_flag:
        raise CalcVerifConfigError(
            "--calcverif and --no-calcverif are mutually exclusive; specify at most one."
        )

    try:
        manifest = paths.pack_manifest(pack_name, root=root)
    except FileNotFoundError as exc:
        raise CalcVerifConfigError(
            f"Pack '{pack_name}' not found: {exc}"
        ) from exc

    cv_cfg = paths.detection_config(manifest).get("calcverif")
    cv_section = cv_cfg or {}
    rule_files_decl = cv_section.get("rule_files") or []

    if enable_flag:
        if not rule_files_decl:
            raise CalcVerifConfigError(
                f"--calcverif was specified but pack '{pack_name}' does not declare "
                f"calculation-verification rules (no `calcverif.rule_files` in "
                f"pack.json). Use a pack that does, or drop the --calcverif flag."
            )
        return CalcVerifConfig(
            enabled=True,
            rule_files=_resolve_rule_paths(rule_files_decl, pack_name, root),
            source=SOURCE_CLI_FORCE_ON,
        )

    if disable_flag:
        return CalcVerifConfig(
            enabled=False,
            rule_files=[],
            source=SOURCE_CLI_FORCE_OFF,
        )

    if cv_cfg is not None:
        enabled = bool(cv_section.get("enabled", False))
        if enabled and not rule_files_decl:
            raise CalcVerifConfigError(
                f"Pack '{pack_name}' has `calcverif.enabled: true` but no "
                f"`calcverif.rule_files` declared. Add `rule_files` or set "
                f"`calcverif.enabled: false`."
            )
        rule_files = (
            _resolve_rule_paths(rule_files_decl, pack_name, root)
            if enabled
            else []
        )
        return CalcVerifConfig(
            enabled=enabled,
            rule_files=rule_files,
            source=SOURCE_PACK_CONFIG,
        )

    return CalcVerifConfig(
        enabled=False,
        rule_files=[],
        source=SOURCE_PACK_DEFAULT_OMITTED,
    )


def _resolve_rule_paths(
    rule_files_decl: list[str],
    pack_name: str,
    root: Path | None,
) -> list[Path]:
    """Resolve `rule_files` strings (relative to the pack root) to absolute paths."""
    pack_root = paths.pack_dir(pack_name, root=root)
    resolved: list[Path] = []
    for rf in rule_files_decl:
        p = (pack_root / rf).resolve()
        if not p.exists():
            raise CalcVerifConfigError(
                f"Pack '{pack_name}' declares rule file '{rf}' but the file "
                f"does not exist at resolved path: {p}"
            )
        resolved.append(p)
    return resolved
