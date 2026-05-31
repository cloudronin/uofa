"""Auto-discovery of UofA repo assets (spec files, JAR, keys, packs)."""

from __future__ import annotations

import functools
import json
import os
import shutil
from pathlib import Path

_MARKER = Path("spec") / "schemas" / "uofa_shacl.ttl"
_PACK_MARKER = Path("packs") / "core" / "pack.json"
_repo_root_cache = None

# Interface versions the core provides. A pack capability declares the interface
# + version it implements; the loader enforces major-version compatibility (§7).
# All four capability legs are recognized at the load gate: detection (P2),
# measurement (§3/P3), reference (§3a/P4), guardrail (§6/P6).
CORE_INTERFACE_VERSIONS: dict[str, str] = {
    "detection": "1.0",
    "measurement": "1.0",
    "reference": "1.0",
    "guardrail": "1.0",
}


def resolve_active_packs(args=None) -> list[str]:
    """The active pack set for this invocation — the P2d explicit-threading accessor.

    Reads ``args.active_packs`` (set once by the CLI entry point) when present;
    otherwise defaults to the open-core baseline pack ``vv40``. There is no
    process global (removed in P2d-3) — commands resolve here and thread the
    result down explicitly.
    """
    explicit = getattr(args, "active_packs", None)
    return list(explicit) if explicit else ["vv40"]


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

    # Wheel-bundled snapshot: pyproject.toml force-includes packs/ + spec/
    # under <package>/_data/repo/ so installed wheels work from any cwd.
    bundled = pkg_dir / "_data" / "repo"
    if (bundled / _PACK_MARKER).exists() or (bundled / _MARKER).exists():
        _repo_root_cache = bundled
        return bundled

    raise FileNotFoundError(
        "Could not find UofA repo root. "
        "Run from inside the repo or pass --repo-root PATH."
    )


# ── Pack resolution ──────────────────────────────────────────

def pack_dir(pack_name: str = None, root: Path = None, active: list[str] = None) -> Path:
    """Return the directory for the given pack.

    ``pack_name`` wins when given; otherwise the first ``active`` pack (or
    ``core``) is used. ``active`` is the explicit active-pack set (P2d threading);
    when None it defaults to the open-core baseline pack ``vv40``.
    """
    root = root or find_repo_root()
    if active is None:
        active = ["vv40"]
    name = (pack_name or active[0]) if active else "core"
    return root / "packs" / name


def pack_manifest(pack_name: str = None, root: Path = None) -> dict:
    """Load and return the pack manifest (pack.json). Plain loader — no validation.

    Validation happens once at the load gate (``validate_active_packs``), not on
    every access, so this stays a cheap reader.
    """
    manifest_path = pack_dir(pack_name, root) / "pack.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Pack manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())


def pack_manifest_schema_path(root: Path = None) -> Path:
    """Path to the pack-manifest JSON Schema (the §7 compatibility contract)."""
    root = root or find_repo_root()
    return root / "specs" / "pack_manifest_schema.json"


@functools.lru_cache(maxsize=4)
def _manifest_schema(schema_path_str: str) -> dict:
    return json.loads(Path(schema_path_str).read_text(encoding="utf-8"))


def validate_pack_manifest(manifest: dict, pack_name: str, root: Path = None) -> None:
    """Validate a pack manifest against the pack-manifest JSON Schema. Raises ValueError.

    Pack-shaped architecture §7: real load-time enforcement replacing the old
    bare ``json.loads`` + directory-exists check. Legacy-tolerant during the
    migration (the schema still accepts the pre-``capabilities`` flat fields), so
    unmigrated packs validate unchanged.
    """
    import jsonschema

    schema = _manifest_schema(str(pack_manifest_schema_path(root)))
    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.path) or "(root)"
        raise ValueError(
            f"Pack '{pack_name}' manifest is invalid at {loc}: {exc.message}"
        ) from exc


def detection_config(manifest: dict) -> dict:
    """Detection config (shapes/rules/oos/derivations/patternIds) from a manifest.

    Reads the detection capability's payload. Every pack is migrated to the
    ``capabilities[]`` shape (the legacy flat-field fallback was removed in P2c
    drop-shim), so a pack with no detection capability returns all-None. The one
    place that knows the detection-payload shape, used by every loader /
    resolver / info-command.
    """
    for cap in manifest.get("capabilities", []):
        if cap.get("leg") == "detection":
            payload = cap.get("payload") or {}
            return {
                "shapes": payload.get("shapes"),
                "rules": payload.get("rules"),
                "oos": payload.get("oos"),
                "derivations": payload.get("derivations"),
                "patternIds": payload.get("patternIds"),
            }
    return {"shapes": None, "rules": None, "oos": None, "derivations": None, "patternIds": None}


@functools.lru_cache(maxsize=4)
def _patternid_pack_index_cached(root_str: str) -> tuple[tuple[str, str], ...]:
    root = Path(root_str)
    index: dict[str, str] = {}
    for name in list_packs(root):
        try:
            manifest = pack_manifest(name, root=root)
        except FileNotFoundError:
            continue
        for pid in detection_config(manifest).get("patternIds") or []:
            index.setdefault(pid, name)  # first declarer wins (core owns reused base ids)
    return tuple(index.items())


def patternid_pack_index(root: Path = None) -> dict[str, str]:
    """``{patternId: owning detection pack}`` built from the loaded manifests.

    The provenance-attribution index (§5/§7.3): records which detection pack
    contributes each weakener patternId, so reasoned output can stamp which pack
    fired which weakener. Same data the loader uses (``detection_config`` payloads).
    A patternId reused from core resolves to ``core`` (first declarer wins —
    matching the base-vocabulary semantics in ``_enforce_pack_compatibility``).
    Returns ``{}`` if the repo root can't be resolved.
    """
    try:
        root = root or find_repo_root()
    except FileNotFoundError:
        return {}
    return dict(_patternid_pack_index_cached(str(root)))


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
        shapes_rel = detection_config(manifest).get("shapes")
        if shapes_rel:
            pack_path = pack_dir("core", root=root) / shapes_rel
            if pack_path.exists():
                return pack_path
    except (FileNotFoundError, KeyError):
        pass
    return root / "spec" / "schemas" / "uofa_shacl.ttl"


def _version_tuple(v: str) -> tuple[int, int, int]:
    parts: list[int] = []
    for p in str(v).split(".")[:3]:
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def _satisfies(version: str, requirement: str) -> bool:
    """Minimal semver-range check: supports >=, <=, ==, >, < and a bare version (>=)."""
    req = str(requirement).strip()
    for op in (">=", "<=", "==", ">", "<"):
        if req.startswith(op):
            target, v = _version_tuple(req[len(op):]), _version_tuple(version)
            return {">=": v >= target, "<=": v <= target, "==": v == target,
                    ">": v > target, "<": v < target}[op]
    return _version_tuple(version) >= _version_tuple(req)


def _enforce_pack_compatibility(manifests, core_version, available):
    """§7 cross-pack enforcement over [(name, manifest), ...] for core + active packs.

    Checks core-version range, capability interface versions, declared
    dependencies, and patternId collisions ACROSS NON-CORE packs (core's
    patternIds are the reusable base vocabulary — iso42001 deliberately reuses
    W-PROV-01/W-AR-02/W-AL-02, so a core↔pack overlap is not a collision). Raises
    ValueError on the first incompatibility — loud, never silent.
    """
    pattern_owner: dict[str, str] = {}
    for name, m in manifests:
        cc = m.get("coreCompatibility")
        if cc and core_version and not _satisfies(core_version, cc):
            raise ValueError(
                f"Pack '{name}' requires core {cc} but the loaded core is {core_version}."
            )
        for dep in m.get("dependencies", []):
            if dep.get("pack") not in available and dep.get("pack") != "core":
                raise ValueError(
                    f"Pack '{name}' depends on pack '{dep.get('pack')}' which is not installed."
                )
        for cap in m.get("capabilities", []):
            iface = cap.get("targetInterface")
            core_iface_ver = CORE_INTERFACE_VERSIONS.get(iface)
            if core_iface_ver is None:
                raise ValueError(
                    f"Pack '{name}' capability '{cap.get('capabilityId')}' targets unknown "
                    f"interface '{iface}'. Core provides: {sorted(CORE_INTERFACE_VERSIONS)}."
                )
            if _version_tuple(cap.get("interfaceVersion", "0"))[0] != _version_tuple(core_iface_ver)[0]:
                raise ValueError(
                    f"Pack '{name}' capability '{cap.get('capabilityId')}' needs {iface} "
                    f"v{cap.get('interfaceVersion')}; core provides v{core_iface_ver} (major mismatch)."
                )
            if name != "core":
                for pid in (cap.get("payload") or {}).get("patternIds") or []:
                    if pattern_owner.get(pid, name) != name:
                        raise ValueError(
                            f"patternId '{pid}' is declared by both '{pattern_owner[pid]}' and "
                            f"'{name}' — collision across active packs."
                        )
                    pattern_owner[pid] = name


def validate_active_packs(root: Path = None, active: list[str] = None):
    """Validate core + all active packs at the load gate. Raises on first problem.

    Pack-shaped §7 enforcement (was directory-exists only): each pack must exist,
    its manifest must conform to the schema, AND the active set must be mutually
    compatible — core-version range, capability interface versions, declared
    dependencies, and no patternId collisions across active packs. A missing pack
    raises FileNotFoundError; anything else raises ValueError — loud failure,
    never silent degradation. ``active`` is the explicit active set (P2d); None
    defaults to the open-core baseline pack ``vv40``.
    """
    root = root or find_repo_root()
    if active is None:
        active = ["vv40"]
    available = list_packs(root)
    core_version = None
    manifests: list[tuple[str, dict]] = []
    seen: set[str] = set()
    for pack_name in ["core", *active]:
        if pack_name in seen:
            continue
        seen.add(pack_name)
        if pack_name != "core" and pack_name not in available:
            raise FileNotFoundError(
                f"Pack '{pack_name}' not found. "
                f"Available packs: {', '.join(available)}"
            )
        manifest = pack_manifest(pack_name, root=root)
        validate_pack_manifest(manifest, pack_name, root=root)
        manifests.append((pack_name, manifest))
        if pack_name == "core":
            core_version = manifest.get("version")
    _enforce_pack_compatibility(manifests, core_version, available)


def all_shacl_schemas(root: Path = None, active: list[str] = None) -> list[Path]:
    """Return SHACL shape file paths for core + all active packs.

    ``active`` is the explicit active set (P2d); None defaults to the open-core
    baseline pack ``vv40``.
    """
    root = root or find_repo_root()
    if active is None:
        active = ["vv40"]
    validate_active_packs(root, active=active)
    paths_list = [shacl_schema(root)]

    for pack_name in active:
        if pack_name == "core":
            continue
        try:
            manifest = pack_manifest(pack_name, root=root)
            shapes_rel = detection_config(manifest).get("shapes")
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


_BUNDLED_JAR_NAME = "uofa-weakener-engine-0.1.0.jar"


def _package_dir() -> Path:
    """Directory containing this package (the installed/editable uofa_cli/)."""
    return Path(__file__).parent


def bundled_jar() -> Path | None:
    """Return the JAR bundled inside the wheel, or None if not present.

    Populated at wheel-build time by hatch_build.py when UOFA_BUNDLE_JAR=1.
    Editable installs from a source checkout will not have it; callers fall
    back to the Maven-built JAR under src/weakener-engine/target/.
    """
    p = _package_dir() / "_engine" / _BUNDLED_JAR_NAME
    return p if p.exists() else None


def jar_path(root: Path = None) -> Path:
    bundled = bundled_jar()
    if bundled is not None:
        return bundled
    root = root or find_repo_root()
    return root / "src" / "weakener-engine" / "target" / _BUNDLED_JAR_NAME


def bundled_jre_executable() -> Path | None:
    """Return the bundled JRE's java binary, or None if not present.

    Populated at wheel-build time by hatch_build.py when
    UOFA_BUNDLE_PLATFORM=<tag> is set. Editable installs from a source
    checkout will not have it; callers fall back to the system PATH.
    """
    base = _package_dir() / "_runtime" / "jre"
    if not base.exists():
        return None
    binary = base / "bin" / ("java.exe" if os.name == "nt" else "java")
    return binary if binary.exists() else None


def java_executable() -> str:
    """Return the path to a usable java binary.

    Resolution order:
      1. Bundled JRE inside the wheel (preferred for pip installs).
      2. System ``java`` on PATH (fallback for source-tree dev work).

    Raises FileNotFoundError if neither is available. Returns a string so
    callers can drop it directly into a subprocess argv.
    """
    bundled = bundled_jre_executable()
    if bundled is not None:
        return str(bundled)
    on_path = shutil.which("java")
    if on_path:
        return on_path
    raise FileNotFoundError(
        "Java not found. Install Java 17+ (https://adoptium.net/) "
        "or use a UofA wheel that bundles a JRE."
    )


def engine_dir(root: Path = None) -> Path:
    root = root or find_repo_root()
    return root / "src" / "weakener-engine"


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
        rules_rel = detection_config(manifest).get("rules")
        if rules_rel:
            pack_path = pack_dir("core", root=root) / rules_rel
            if pack_path.exists():
                return pack_path
    except (FileNotFoundError, KeyError):
        pass
    return root / "packs" / "core" / "rules" / "uofa_weakener.rules"


def all_rules_files(input_path: Path = None, root: Path = None, active: list[str] = None) -> list[Path]:
    """Return rules file paths for core + all active packs.

    ``active`` is the explicit active set (P2d); None defaults to the open-core
    baseline pack ``vv40``.
    """
    root = root or find_repo_root()
    if active is None:
        active = ["vv40"]
    paths_list = [rules_file(input_path, root)]

    for pack_name in active:
        if pack_name == "core":
            continue
        try:
            manifest = pack_manifest(pack_name, root=root)
            rules_rel = detection_config(manifest).get("rules")
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
