"""Derivation pre-pass execution-decision resolver.

Reads pack configuration and CLI flag values, returns a `DerivationConfig`
object with the resolved decision per UofA_Derivation_PrePass_Spec_v0_1.md
§2.2.

Resolution order (mirrors uofa_cli.oos.config exactly):
  1. `--derivations` and `--no-derivations` are mutually exclusive.
  2. `--derivations` set: enabled=True, source="cli_flag_force_on". Pack
     must declare `derivations.files`, otherwise raise.
  3. `--no-derivations` set: enabled=False, source="cli_flag_force_off".
  4. Pack `derivations` section present: use its `enabled` value,
     source="pack_config".
  5. Pack has no `derivations` section: enabled=False,
     source="pack_default_omitted".

Backward compatibility: when no active pack declares derivations, the
pre-pass is a no-op and downstream stages see no behavior change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli import paths


SOURCE_CLI_FORCE_ON = "cli_flag_force_on"
SOURCE_CLI_FORCE_OFF = "cli_flag_force_off"
SOURCE_PACK_CONFIG = "pack_config"
SOURCE_PACK_DEFAULT_OMITTED = "pack_default_omitted"


class DerivationConfigError(ValueError):
    """Raised when derivation configuration cannot be resolved."""


@dataclass(frozen=True)
class DerivationConfig:
    """Resolved derivation pre-pass execution decision."""

    enabled: bool
    construct_files: list[Path] = field(default_factory=list)
    source: str = SOURCE_PACK_DEFAULT_OMITTED


def resolve(
    pack_name: str,
    *,
    enable_flag: bool = False,
    disable_flag: bool = False,
    root: Path | None = None,
) -> DerivationConfig:
    """Resolve derivation decision per spec §2.2."""

    if enable_flag and disable_flag:
        raise DerivationConfigError(
            "--derivations and --no-derivations are mutually exclusive; "
            "specify at most one."
        )

    try:
        manifest = paths.pack_manifest(pack_name, root=root)
    except FileNotFoundError as exc:
        raise DerivationConfigError(
            f"Pack '{pack_name}' not found: {exc}"
        ) from exc

    deriv_cfg = paths.detection_config(manifest).get("derivations")
    section = deriv_cfg or {}
    files_decl = section.get("files") or []

    if enable_flag:
        if not files_decl:
            raise DerivationConfigError(
                f"--derivations was specified but pack '{pack_name}' does not "
                f"declare derivation CONSTRUCT files (no `derivations.files` "
                f"in pack.json). Update the pack manifest or drop the flag."
            )
        return DerivationConfig(
            enabled=True,
            construct_files=_resolve_paths(files_decl, pack_name, root),
            source=SOURCE_CLI_FORCE_ON,
        )

    if disable_flag:
        return DerivationConfig(
            enabled=False,
            construct_files=[],
            source=SOURCE_CLI_FORCE_OFF,
        )

    if deriv_cfg is not None:
        enabled = bool(section.get("enabled", False))
        files = (
            _resolve_paths(files_decl, pack_name, root)
            if enabled and files_decl
            else []
        )
        if enabled and not files_decl:
            raise DerivationConfigError(
                f"Pack '{pack_name}' has `derivations.enabled: true` but no "
                f"`derivations.files` declared. Add `files` or set "
                f"`derivations.enabled: false`."
            )
        return DerivationConfig(
            enabled=enabled,
            construct_files=files,
            source=SOURCE_PACK_CONFIG,
        )

    return DerivationConfig(
        enabled=False,
        construct_files=[],
        source=SOURCE_PACK_DEFAULT_OMITTED,
    )


def _resolve_paths(
    files_decl: list[str],
    pack_name: str,
    root: Path | None,
) -> list[Path]:
    """Resolve `files` strings (relative to pack root) to absolute paths."""
    pack_root = paths.pack_dir(pack_name, root=root)
    resolved: list[Path] = []
    for rf in files_decl:
        p = (pack_root / rf).resolve()
        if not p.exists():
            raise DerivationConfigError(
                f"Pack '{pack_name}' declares CONSTRUCT file '{rf}' but the "
                f"file does not exist at resolved path: {p}"
            )
        resolved.append(p)
    return resolved
