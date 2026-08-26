"""Auto-discovery of UofA repo assets (spec files, JAR, keys, packs)."""

from __future__ import annotations

import functools
import json
import os
import shutil
import re
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


def packs_recorded_in(path) -> list[str] | None:
    """The pack set a package records having been built under, if any.

    A package used to record nothing about which standard it follows, so
    validation was relative to a flag the operator remembered to pass -- and the
    default is ``vv40``. That meant a NASA-STD-7009B package validated as plain
    ``uofa shacl pkg.jsonld`` was asked for a V&V 40 context of use and failed
    for a reason belonging to a different standard.

    Returns None for the 64 packages that predate the stamp; the caller falls
    back to the default AND says so, because an assumed standard that goes
    unannounced is the whole defect repeating one layer up.
    """
    import json
    try:
        blob = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        # Narrow ON PURPOSE. The first version caught bare Exception and used
        # `pathlib.Path` in a module that imports only `Path`, so every call
        # raised NameError and returned None -- a silent, plausible-looking
        # "no pack recorded" for every package in the repo. A catch-all around
        # a lookup turns a bug into a default.
        return None
    for node in ([blob] + (blob.get("@graph") or [])):
        if not isinstance(node, dict):
            continue
        for key in ("uofa:validatedWithPacks", "validatedWithPacks",
                    "https://uofa.net/vocab#validatedWithPacks"):
            v = node.get(key)
            if v:
                return [v] if isinstance(v, str) else list(v)
    return None


# One-version rename alias. `mrm-nist` became `model-credibility` when the pack
# grew the NIST AI 800-3 evaluation-sufficiency layer and stopped being about
# model risk management alone.
#
# Discovery is filesystem-only (`list_packs` reads directory names), so without
# this map every `--pack mrm-nist` invocation and every bundle that RECORDED
# `mrm-nist` in its packs list would fail to resolve. A saved bundle is a pinned
# artifact; a rename must not make it unreadable.
#
# ONE VERSION. Remove after the next release, by which time recorded bundles
# have been through a regeneration cycle.
PACK_ALIASES = {"mrm-nist": "model-credibility"}


def canonical_pack_name(name: str) -> str:
    """Resolve a pack name through the rename alias. Unknown names pass through
    unchanged so a genuine typo still produces the `not found` error naming the
    available packs, rather than being silently rewritten."""
    return PACK_ALIASES.get(name, name)


def resolve_active_packs(args=None) -> list[str]:
    """The active pack set for this invocation — the P2d explicit-threading accessor.

    Order: an explicit ``--pack``, then the set the package records, then the
    ``vv40`` default. There is no process global (removed in P2d-3) — commands
    resolve here and thread the result down explicitly.
    """
    explicit = getattr(args, "active_packs", None)
    if explicit:
        return [canonical_pack_name(p) for p in explicit]
    target = getattr(args, "file", None)
    if target is not None:
        recorded = packs_recorded_in(target)
        if recorded:
            # A bundle written before the rename records the old name.
            return [canonical_pack_name(p) for p in recorded]
    return ["vv40"]


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
                "factorFocus": payload.get("factorFocus"),
                "quantityIdentity": payload.get("quantityIdentity"),
            }
    return {"shapes": None, "rules": None, "oos": None, "derivations": None,
            "patternIds": None, "factorFocus": None, "quantityIdentity": None}


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


@functools.lru_cache(maxsize=16)
def _factor_focus_index_cached(root_str: str, packs_key: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    root = Path(root_str)
    merged: dict[str, list[str]] = {}
    for name in packs_key.split(","):
        try:
            manifest = pack_manifest(name, root=root)
        except FileNotFoundError:
            continue
        focus = detection_config(manifest).get("factorFocus") or {}
        for pid, names in focus.items():
            bucket = merged.setdefault(pid, [])
            for fac in names or []:
                if fac not in bucket:  # union across packs, order-preserving
                    bucket.append(fac)
    return tuple((pid, tuple(names)) for pid, names in merged.items())


def factor_focus_index(packs: list[str] = None, root: Path = None) -> dict[str, list[str]]:
    """``{patternId: [credibility factor name, ...]}`` merged from manifests.

    The semantic weakener→factor map (declared in each detection payload's
    ``factorFocus``): which credibility factor(s) a weakener implicates when its
    ``affectedNode`` is a validation-result/COU node rather than a factor IRI, so
    a concern can demote the factor it bears on. Merged over ``core`` + the active
    packs (union, order-preserving), so a pack augments core (e.g. NASA adds
    ``Data pedigree`` to core's ``W-PROV-01`` focus). Callers filter the result to
    factors expected for the bundle's pack. Returns ``{}`` if root can't resolve.
    """
    try:
        root = root or find_repo_root()
    except FileNotFoundError:
        return {}
    active = packs or ["vv40"]
    # core first so it owns the base mapping; dedup while preserving order.
    ordered = ["core"] + [p for p in active if p != "core"]
    seen, packs_norm = set(), []
    for p in ordered:
        if p not in seen:
            seen.add(p)
            packs_norm.append(p)
    return {pid: list(names) for pid, names in _factor_focus_index_cached(str(root), ",".join(packs_norm))}


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
    active = [canonical_pack_name(p) for p in active]
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
    """The context used when a document names none that can be resolved.

    **Deliberately still v0.5.** `integrity.resolve_context` uses this as its
    last resort before hashing, so moving it re-hashes every document that
    reaches that branch. Signing is not the place to chase the newest file.

    Validation is a different question and must not share this answer: see
    `latest_context_file`.
    """
    root = root or find_repo_root()
    return root / "spec" / "context" / "v0.5.jsonld"


def _context_version(name: str) -> tuple[int, ...]:
    digits = re.findall(r"\d+", name)
    return tuple(int(d) for d in digits) if digits else ()


def latest_context_file(root: Path = None) -> Path:
    """The newest context this checkout ships, found by looking.

    **Computed, not written down.** Three constants in this codebase have now
    been caught naming a version the repo had moved past -- `CONTEXT_URL` at
    v0.5 while v0.7 shipped, the workbook with no declaration at all, and this
    validation default. Patching a hardcoded v0.5 to a hardcoded v0.8 re-arms
    the identical failure for v0.9, so the fallback reads the directory.

    Falls back to `context_file()` when nothing matches, so a checkout without
    the directory behaves as it did before rather than raising.
    """
    root = root or find_repo_root()
    d = root / "spec" / "context"
    versions = sorted((p for p in d.glob("v*.jsonld") if _context_version(p.name)),
                      key=lambda p: _context_version(p.name))
    return versions[-1] if versions else context_file(root)


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


def extract_prompt(pack_name: str = None, root: Path = None) -> Path:
    """Return the extract prompt path for ``pack_name``.

    ``pack_name`` used to be absent from this signature, so every call resolved
    through ``pack_dir()`` with its ``active=["vv40"]`` default and returned the
    V&V 40 prompt no matter which pack was being extracted. `uofa extract --pack
    nasa-7009b` therefore sent the model a prompt that defines 13 factors and
    never names the six NASA-STD-7009B ones, and the model returned what it was
    asked for: 13 factors, and `standards_reference: ASME-VV40-2018` for a NASA
    assessment.

    Nothing downstream noticed. `_json_to_result` selects NASA_ALL_FACTOR_NAMES
    from the pack name it *was* given, and the workbook writer pre-fills all 19
    rows from the pack, so the output looked like a NASA extraction with six
    factors the model had declined to fill in. Measured cost: 13 of 19 factors
    in 27 of 27 NASA extractions (15 dev, 10 test, both aerospace COUs), with
    those six factors at per-factor F1 0.000 on both splits.

    See studies/nasa-prompt-routing/FINDINGS.md.
    """
    root = root or find_repo_root()
    try:
        manifest = pack_manifest(pack_name, root=root)
        return pack_dir(pack_name, root=root) / manifest.get("prompt", "")
    except (FileNotFoundError, KeyError):
        return pack_dir(pack_name, root=root) / "prompts"


#: The anchors the wheel ships, in the order a keyless verify tries them, each
#: with the label it is reported under. A fallback is always NAMED: "verified"
#: with no statement of against-what is a claim whose subject the reader cannot
#: recover, and `keys/research.pub` sat here as an unnamed default for 692
#: commits precisely because nothing ever had to say its name out loud.
#:
#: The production issuer anchor is deliberately absent: trusting an issuer is an
#: explicit act, so it requires `--pubkey`.
SHIPPED_ANCHORS: tuple[tuple[str, str], ...] = (
    ("keys/research.pub", "research anchor (rotated 2026-03-29; signs the shipped examples)"),
    ("keys/demo-reviewer.pub", "demo reviewer anchor (labeled fixture)"),
)


def shipped_anchors(root: Path = None) -> list[tuple[Path, str]]:
    """Existing wheel-shipped anchors as (path, label)."""
    root = root or find_repo_root()
    return [(root / rel, label) for rel, label in SHIPPED_ANCHORS
            if (root / rel).exists()]


def default_pubkey(root: Path = None) -> Path:
    """RETIRED as a silent default. Kept only so a caller that still reaches for
    one gets an error naming the replacement rather than a key nobody chose."""
    raise RuntimeError(
        "there is no default trust anchor. Name a key with `--pubkey`, or let "
        "verify try the shipped anchors and report which one matched "
        "(`uofa.paths.shipped_anchors`).")


def issuer_pubkey(root: Path = None) -> Path:
    """Trust anchor for the ISSUER seal: origin, integrity, well-formedness.

    Held by the producing infrastructure. What it attests is everything a
    machine can know about a package and nothing a person judged -- the
    tamper-evident bag and the calibration sticker, never the finding.

    Deliberately NOT the no-flag default, for the same reason the demo anchor
    never was: trusting an issuer is an explicit act, and every pack ships this
    file plus instructions so the choice is visible.
    """
    root = root or find_repo_root()
    return root / "keys" / "uofa-issuer.pub"


def reviewer_pubkey(root: Path = None) -> Path:
    """Trust anchor for DECISION signatures made by the demo reviewer identity.

    Renamed from `reviewer_pubkey`, and the rename is the point: this key used to
    seal packages as the hosted demo's issuer, and it now signs judgments. A
    file whose name says "issuer" while its key signs decisions is the
    two-scopes-one-key confusion the format exists to make unrepresentable.

    The identity it stands for is a labeled fixture. An instrument run's package
    must tell any reader truthfully which KIND of signer signed; in production
    the same route carries the customer engineer's own key, and only then is the
    signature a commitment.
    """
    root = root or find_repo_root()
    return root / "keys" / "demo-reviewer.pub"


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
        # Namespace for identifiers minted by `uofa import`. None means fall
        # back to the placeholder default; uofa.net is refused downstream.
        "base_uri": project.get("base_uri"),
        "output": project_root / paths_section.get("output", "."),
        "evidence": project_root / paths_section.get("evidence", "evidence"),
        "template": project_root / paths_section.get("template", "uofa-template.xlsx"),
        "provider": extract.get("provider", "ollama"),
        "model": extract.get("model", "llama3.2"),
    }
