"""Auto-discovery of UofA repo assets (spec files, JAR, keys)."""

from pathlib import Path

_MARKER = Path("spec") / "schemas" / "uofa_shacl.ttl"
_repo_root_cache = None


def find_repo_root(override: str = None) -> Path:
    """Find the UofA repo root by walking up from cwd looking for the SHACL marker."""
    global _repo_root_cache

    if override:
        root = Path(override)
        if (root / _MARKER).exists():
            _repo_root_cache = root
            return root
        raise FileNotFoundError(
            f"Not a UofA repo: {root} (missing {_MARKER})"
        )

    if _repo_root_cache:
        return _repo_root_cache

    # Walk up from cwd
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / _MARKER).exists():
            _repo_root_cache = parent
            return parent

    # Walk up from package location
    pkg_dir = Path(__file__).parent
    for parent in [pkg_dir, *pkg_dir.parents]:
        if (parent / _MARKER).exists():
            _repo_root_cache = parent
            return parent

    raise FileNotFoundError(
        "Could not find UofA repo root. "
        "Run from inside the repo or pass --repo-root PATH."
    )


def shacl_schema(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "spec" / "schemas" / "uofa_shacl.ttl"


def context_file(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "spec" / "context" / "v0.2.jsonld"


def jar_path(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"


def engine_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "weakener-engine"


def rules_file(input_path: Path = None, root: Path = None) -> Path:
    """Find rules file: same dir as input, then parent dir, then default location."""
    if input_path:
        local = input_path.parent / "uofa_weakener.rules"
        if local.exists():
            return local
        parent = input_path.parent.parent / "uofa_weakener.rules"
        if parent.exists():
            return parent
    root = root or find_repo_root()
    return root / "examples" / "morrison" / "uofa_weakener.rules"


def default_pubkey(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "keys" / "research.pub"


def templates_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "examples" / "templates"


def examples_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "examples"
