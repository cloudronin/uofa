"""Auto-discovery of UofA repo assets (spec files, JAR, keys, packs)."""

from __future__ import annotations

import json
from pathlib import Path

_MARKER = Path("spec") / "schemas" / "uofa_shacl.ttl"
_PACK_MARKER = Path("packs") / "core" / "pack.json"
_repo_root_cache = None
_active_packs: list[str] = ["vv40"]


def set_active_pack(pack_names):
    """Set the active pack name(s) (called from CLI when --pack is provided).

    Accepts a single string or list of strings.
    """
    global _active_packs
    if isinstance(pack_names, str):
        _active_packs = [pack_names]
    elif isinstance(pack_names, list):
        _active_packs = pack_names
    else:
        _active_packs = [str(pack_names)]


def get_active_pack() -> list[str]:
    """Return the currently active pack name(s)."""
    return _active_packs


def find_repo_root(override: str = None) -> Path:
    """Find the UofA repo root by walking up from cwd looking for markers."""
    global _repo_root_cache

    if override:
        root = Path(override)
        if (root / _PACK_MARKER).exists() or (root / _MARKER).exists():
            _repo_root_cache = root
            return root
        raise FileNotFoundError(
            f"Not a UofA repo: {root} (missing {_PACK_MARKER} and {_MARKER})"
        )

    if _repo_root_cache:
        return _repo_root_cache

    # Walk up from cwd
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / _PACK_MARKER).exists() or (parent / _MARKER).exists():
            _repo_root_cache = parent
            return parent

    # Walk up from package location
    pkg_dir = Path(__file__).parent
    for parent in [pkg_dir, *pkg_dir.parents]:
        if (parent / _PACK_MARKER).exists() or (parent / _MARKER).exists():
            _repo_root_cache = parent
            return parent

    raise FileNotFoundError(
        "Could not find UofA repo root. "
        "Run from inside the repo or pass --repo-root PATH."
    )


# ── Pack resolution ──────────────────────────────────────────

def pack_dir(pack_name: str = None, root: Path = None) -> Path:
    """Return the directory for the given pack."""
    root = root or find_repo_root()
    name = pack_name or _active_packs[0] if _active_packs else "core"
    return root / "packs" / name


def pack_manifest(pack_name: str = None, root: Path = None) -> dict:
    """Load and return the pack manifest (pack.json)."""
    manifest_path = pack_dir(pack_name, root) / "pack.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Pack manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())


def list_packs(root: Path = None) -> list[str]:
    """Return names of all installed packs (directories under packs/ with pack.json)."""
    root = root or find_repo_root()
    packs_root = root / "packs"
    if not packs_root.exists():
        return []
    return sorted(
        d.name for d in packs_root.iterdir()
        if d.is_dir() and (d / "pack.json").exists()
    )


# ── Asset paths (pack-aware) ────────────────────────────────

def shacl_schema(root: Path = None) -> Path:
    """Return core SHACL shapes path (always loaded)."""
    root = root or find_repo_root()
    try:
        manifest = pack_manifest("core", root=root)
        pack_path = pack_dir("core", root=root) / manifest["shapes"]
        if pack_path.exists():
            return pack_path
    except (FileNotFoundError, KeyError):
        pass
    return root / "spec" / "schemas" / "uofa_shacl.ttl"


def validate_active_packs(root: Path = None):
    """Check that all active packs exist. Raises FileNotFoundError if not."""
    root = root or find_repo_root()
    available = list_packs(root)
    for pack_name in _active_packs:
        if pack_name != "core" and pack_name not in available:
            raise FileNotFoundError(
                f"Pack '{pack_name}' not found. "
                f"Available packs: {', '.join(available)}"
            )


def all_shacl_schemas(root: Path = None) -> list[Path]:
    """Return SHACL shape file paths for core + all active packs."""
    root = root or find_repo_root()
    validate_active_packs(root)
    paths_list = [shacl_schema(root)]

    for pack_name in _active_packs:
        if pack_name == "core":
            continue
        try:
            manifest = pack_manifest(pack_name, root=root)
            shapes_rel = manifest.get("shapes")
            if shapes_rel:
                shapes_path = pack_dir(pack_name, root=root) / shapes_rel
                if shapes_path.exists():
                    paths_list.append(shapes_path)
        except (FileNotFoundError, KeyError):
            pass

    return paths_list


def context_file(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "spec" / "context" / "v0.5.jsonld"


def jar_path(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"


def engine_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine"


def rules_file(input_path: Path = None, root: Path = None) -> Path:
    """Find rules file: same dir as input, then parent dir, then core pack rules dir."""
    if input_path:
        local = input_path.parent / "uofa_weakener.rules"
        if local.exists():
            return local
        parent = input_path.parent.parent / "uofa_weakener.rules"
        if parent.exists():
            return parent
    # Core pack rules
    root = root or find_repo_root()
    try:
        manifest = pack_manifest("core", root=root)
        pack_path = pack_dir("core", root=root) / manifest["rules"]
        if pack_path.exists():
            return pack_path
    except (FileNotFoundError, KeyError):
        pass
    return root / "packs" / "core" / "rules" / "uofa_weakener.rules"


def all_rules_files(input_path: Path = None, root: Path = None) -> list[Path]:
    """Return rules file paths for core + all active packs."""
    root = root or find_repo_root()
    paths_list = [rules_file(input_path, root)]

    for pack_name in _active_packs:
        if pack_name == "core":
            continue
        try:
            manifest = pack_manifest(pack_name, root=root)
            rules_rel = manifest.get("rules")
            if rules_rel:
                rules_path = pack_dir(pack_name, root=root) / rules_rel
                if rules_path.exists():
                    paths_list.append(rules_path)
        except (FileNotFoundError, KeyError):
            pass

    return paths_list


def template_path(root: Path = None) -> Path:
    """Return the pack template path (for future uofa import)."""
    root = root or find_repo_root()
    try:
        manifest = pack_manifest(root=root)
        return pack_dir(root=root) / manifest.get("template", "")
    except (FileNotFoundError, KeyError):
        return pack_dir(root=root) / "templates"


def extract_prompt(root: Path = None) -> Path:
    """Return the pack extract prompt path (for future uofa extract)."""
    root = root or find_repo_root()
    try:
        manifest = pack_manifest(root=root)
        return pack_dir(root=root) / manifest.get("prompt", "")
    except (FileNotFoundError, KeyError):
        return pack_dir(root=root) / "prompts"


def default_pubkey(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "keys" / "research.pub"


def templates_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "packs" / "core" / "templates"


def examples_dir(root: Path = None) -> Path:
    """Return the first pack examples directory found, for backward compat.

    For scanning all pack examples, use all_example_dirs() instead.
    """
    root = root or find_repo_root()
    # Return first pack with examples/
    packs_root = root / "packs"
    for d in sorted(packs_root.iterdir()):
        if d.is_dir() and (d / "examples").is_dir():
            return d / "examples"
    return packs_root / "vv40" / "examples"


def all_example_dirs(root: Path = None) -> list[Path]:
    """Return all pack example directories."""
    root = root or find_repo_root()
    packs_root = root / "packs"
    dirs = []
    for d in sorted(packs_root.iterdir()):
        if d.is_dir() and (d / "examples").is_dir():
            dirs.append(d / "examples")
    return dirs


# ── Project root detection (uofa.toml) ─────────────────────


def find_project_root(start: Path = None) -> Path | None:
    """Walk up from start (default: cwd) looking for uofa.toml.

    Returns the directory containing uofa.toml, or None if not found.
    """
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / "uofa.toml").is_file():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_project_config(project_root: Path) -> dict:
    """Load and parse uofa.toml from a project root.

    Returns a flat dict with resolved values.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    toml_path = project_root / "uofa.toml"
    with open(toml_path, "rb") as f:
        raw = tomllib.load(f)

    project = raw.get("project", {})
    paths_section = raw.get("paths", {})
    extract = raw.get("extract", {})

    return {
        "name": project.get("name", project_root.name),
        "pack": project.get("pack", "vv40"),
        "profile": project.get("profile", "complete"),
        "output": project_root / paths_section.get("output", "."),
        "evidence": project_root / paths_section.get("evidence", "evidence"),
        "template": project_root / paths_section.get("template", "uofa-template.xlsx"),
        "provider": extract.get("provider", "ollama"),
        "model": extract.get("model", "llama3.2"),
    }
