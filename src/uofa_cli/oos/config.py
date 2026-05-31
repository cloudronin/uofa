"""OOS execution-decision resolver.

Reads pack configuration and CLI flag values, returns an `OOSConfig` object
with the resolved decision per UofA_OOS_Productionization_Spec_v0_3.md §2.2.

Resolution order:
  1. `--oos` and `--no-oos` are mutually exclusive (raise CLI error).
  2. `--oos` set: enabled=True, source="cli_flag_force_on". Pack must declare
     `oos.rule_files`, otherwise raise.
  3. `--no-oos` set: enabled=False, source="cli_flag_force_off".
  4. Pack `oos` section present: use its `enabled` value, source="pack_config".
  5. Pack has no `oos` section: enabled=False, source="pack_default_omitted".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli import paths


SOURCE_CLI_FORCE_ON = "cli_flag_force_on"
SOURCE_CLI_FORCE_OFF = "cli_flag_force_off"
SOURCE_PACK_CONFIG = "pack_config"
SOURCE_PACK_DEFAULT_OMITTED = "pack_default_omitted"


class OOSConfigError(ValueError):
    """Raised when OOS configuration cannot be resolved (mutual exclusion,
    missing rule_files declaration, malformed pack.json, etc.).

    The CLI handler should print the message and exit non-zero before any
    OOS work begins per spec §2.2 step 1.
    """


@dataclass(frozen=True)
class OOSConfig:
    """Resolved OOS execution decision for one `uofa check` invocation."""

    enabled: bool
    rule_files: list[Path] = field(default_factory=list)
    source: str = SOURCE_PACK_DEFAULT_OMITTED


def resolve(
    pack_name: str,
    *,
    enable_flag: bool = False,
    disable_flag: bool = False,
    root: Path | None = None,
) -> OOSConfig:
    """Resolve the OOS decision per spec §2.2."""

    if enable_flag and disable_flag:
        raise OOSConfigError(
            "--oos and --no-oos are mutually exclusive; specify at most one."
        )

    try:
        manifest = paths.pack_manifest(pack_name, root=root)
    except FileNotFoundError as exc:
        raise OOSConfigError(
            f"Pack '{pack_name}' not found: {exc}"
        ) from exc

    oos_cfg = paths.detection_config(manifest).get("oos")
    oos_section = oos_cfg or {}
    rule_files_decl = oos_section.get("rule_files") or []

    if enable_flag:
        if not rule_files_decl:
            raise OOSConfigError(
                f"--oos was specified but pack '{pack_name}' does not declare "
                f"OOS rules (no `oos.rule_files` in pack.json). "
                f"Update the pack manifest or drop the --oos flag."
            )
        return OOSConfig(
            enabled=True,
            rule_files=_resolve_rule_paths(rule_files_decl, pack_name, root),
            source=SOURCE_CLI_FORCE_ON,
        )

    if disable_flag:
        return OOSConfig(
            enabled=False,
            rule_files=[],
            source=SOURCE_CLI_FORCE_OFF,
        )

    if oos_cfg is not None:
        enabled = bool(oos_section.get("enabled", False))
        rule_files = (
            _resolve_rule_paths(rule_files_decl, pack_name, root)
            if enabled and rule_files_decl
            else []
        )
        if enabled and not rule_files_decl:
            raise OOSConfigError(
                f"Pack '{pack_name}' has `oos.enabled: true` but no "
                f"`oos.rule_files` declared. Add `rule_files` or set "
                f"`oos.enabled: false`."
            )
        return OOSConfig(
            enabled=enabled,
            rule_files=rule_files,
            source=SOURCE_PACK_CONFIG,
        )

    return OOSConfig(
        enabled=False,
        rule_files=[],
        source=SOURCE_PACK_DEFAULT_OMITTED,
    )


def _resolve_rule_paths(
    rule_files_decl: list[str],
    pack_name: str,
    root: Path | None,
) -> list[Path]:
    """Resolve `rule_files` strings (relative to pack root) to absolute paths."""
    pack_root = paths.pack_dir(pack_name, root=root)
    resolved: list[Path] = []
    for rf in rule_files_decl:
        p = (pack_root / rf).resolve()
        if not p.exists():
            raise OOSConfigError(
                f"Pack '{pack_name}' declares rule file '{rf}' but the file "
                f"does not exist at resolved path: {p}"
            )
        resolved.append(p)
    return resolved
