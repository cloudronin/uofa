"""Auto-discovery of UofA repo assets (spec files, JAR, keys, packs)."""

import json
from pathlib import Path

_MARKER = Path("spec") / "schemas" / "uofa_shacl.ttl"
_PACK_MARKER = Path("packs") / "core" / "pack.json"
_repo_root_cache = None
_active_pack = "core"


def set_active_pack(pack_name: str):
    """Set the active pack name (called from CLI when --pack is provided)."""
    global _active_pack
    _active_pack = pack_name


def get_active_pack() -> str:
    """Return the currently active pack name."""
    return _active_pack


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
    return root / "packs" / (pack_name or _active_pack)


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
    """Return SHACL shapes path from the active pack, with fallback to spec/schemas/."""
    root = root or find_repo_root()
    try:
        manifest = pack_manifest(root=root)
        pack_path = pack_dir(root=root) / manifest["shapes"]
        if pack_path.exists():
            return pack_path
    except (FileNotFoundError, KeyError):
        pass
    # Backward compat fallback
    return root / "spec" / "schemas" / "uofa_shacl.ttl"


def context_file(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "spec" / "context" / "v0.3.jsonld"


def jar_path(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"


def engine_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine"


def rules_file(input_path: Path = None, root: Path = None) -> Path:
    """Find rules file: same dir as input, then parent dir, then pack rules dir."""
    if input_path:
        local = input_path.parent / "uofa_weakener.rules"
        if local.exists():
            return local
        parent = input_path.parent.parent / "uofa_weakener.rules"
        if parent.exists():
            return parent
    # Pack rules
    root = root or find_repo_root()
    try:
        manifest = pack_manifest(root=root)
        pack_path = pack_dir(root=root) / manifest["rules"]
        if pack_path.exists():
            return pack_path
    except (FileNotFoundError, KeyError):
        pass
    # Backward compat fallback
    return root / "examples" / "morrison" / "uofa_weakener.rules"


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
    return root / "examples" / "templates"


def examples_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "examples"
