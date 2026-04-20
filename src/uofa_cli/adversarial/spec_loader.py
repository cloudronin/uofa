"""Parse and validate adversarial generation specs (YAML).

Spec format: UofA_Adversarial_Gen_Spec_v1.1 §5. Validation rules §5.2.
Loader is pack-aware: the `pack` field selects the factor registry and the
rule files used to harvest known weakener IDs.

TODO: future packs (ssp-ls-traceability, mossec) should plug in via an
abstract pack-metadata API rather than hardcoded dispatch in
``_known_factor_names``. Phase 1 keeps the dispatch explicit.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from uofa_cli import paths
from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES
from uofa_cli.integrity import canonicalize_and_hash

VALID_DEFEATERS = {"D1", "D2", "D3", "D4", "D5", "structural"}
VALID_INTENTS = {"confirm_existing", "gap_probe"}
VALID_SUBTLETIES = {"low", "medium", "high"}
VALID_DECISIONS = {"Accepted", "Not accepted", "Conditional"}
VALID_MODES = {"skeleton", "narrative-only"}
VALID_UNCERTAINTY = {"epistemic", "aleatory", "ontological", "argument", "structural"}
SPEC_ID_RE = re.compile(r"^[a-z0-9-]+$")
WEAKENER_ID_RE = re.compile(r"patternId\s+'(W-[A-Z]{2}-\d{2})'")


class SpecValidationError(ValueError):
    """Raised when a spec YAML fails validation. Generator maps to exit code 3."""


@dataclass
class AdversarialSpec:
    spec_id: str
    target_weakener: str
    defeater_type: str
    uncertainty_category: str
    coverage_intent: str
    pack: str
    mode: str
    base_cou: Path | None
    factors: list[str]
    decision: str
    mrl: int | None
    generation_model: str
    n_variants: int
    subtlety: str
    temperature: float
    max_tokens: int
    seed: int | None
    package_name_template: str
    include_provenance: bool
    spec_hash: str
    spec_path: Path
    raw: dict = field(repr=False)

    def prompt_template_id(self) -> str:
        """E.g. 'd3_undercutting_inference.W_AR_05'."""
        return f"{self._template_module()}.{self.target_weakener.replace('-', '_')}"

    def _template_module(self) -> str:
        if self.target_weakener == "W-AR-05":
            return "d3_undercutting_inference"
        raise NotImplementedError(
            f"No Phase 1 prompt template for {self.target_weakener}"
        )


def load_spec(path: Path) -> AdversarialSpec:
    """Parse YAML at *path*, validate, compute spec_hash.

    Raises SpecValidationError on any exit-3 condition.
    """
    try:
        import yaml
    except ModuleNotFoundError as e:
        raise SpecValidationError(
            "PyYAML is required to load adversarial specs. "
            "Install with: pip install -e '.[llm]'"
        ) from e

    path = Path(path)
    if not path.exists():
        raise SpecValidationError(f"spec file not found: {path}")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SpecValidationError(f"malformed YAML in {path}: {e}") from e

    if not isinstance(raw, dict):
        raise SpecValidationError(f"spec must be a YAML mapping, got {type(raw).__name__}")

    return _build_spec(raw, path)


def _build_spec(raw: dict, spec_path: Path) -> AdversarialSpec:
    spec_id = _require(raw, "spec_id", str)
    if not SPEC_ID_RE.match(spec_id):
        raise SpecValidationError(
            f"spec_id must match {SPEC_ID_RE.pattern!r}, got {spec_id!r}"
        )

    target = _require(raw, "target", dict)
    weakener = _require(target, "target.weakener", str, src=target, key="weakener")
    defeater = _require(target, "target.defeater_type", str, src=target, key="defeater_type")
    intent = _require(
        target, "target.coverage_intent", str, src=target, key="coverage_intent"
    )
    uncertainty = _require(
        target,
        "target.uncertainty_category",
        str,
        src=target,
        key="uncertainty_category",
    )

    if defeater not in VALID_DEFEATERS:
        raise SpecValidationError(
            f"target.defeater_type must be one of {sorted(VALID_DEFEATERS)}, got {defeater!r}"
        )
    if intent not in VALID_INTENTS:
        raise SpecValidationError(
            f"target.coverage_intent must be one of {sorted(VALID_INTENTS)}, got {intent!r}"
        )
    if uncertainty not in VALID_UNCERTAINTY:
        raise SpecValidationError(
            f"target.uncertainty_category must be one of {sorted(VALID_UNCERTAINTY)}, "
            f"got {uncertainty!r}"
        )

    pack_name = raw.get("pack", "vv40")
    if not isinstance(pack_name, str):
        raise SpecValidationError(f"pack must be a string, got {type(pack_name).__name__}")
    _validate_pack_exists(pack_name)

    known_weakeners = _known_weakener_ids(pack_name)
    if weakener not in known_weakeners:
        raise SpecValidationError(
            f"target.weakener {weakener!r} not found in pack {pack_name!r} rule registry. "
            f"Known weakeners: {sorted(known_weakeners)}"
        )

    pkg_ctx = _require(raw, "package_context", dict)
    mode = pkg_ctx.get("mode", "skeleton")
    if mode not in VALID_MODES:
        raise SpecValidationError(
            f"package_context.mode must be one of {sorted(VALID_MODES)}, got {mode!r}"
        )

    base_cou_raw = pkg_ctx.get("base_cou")
    base_cou = _resolve_base_cou(base_cou_raw) if base_cou_raw else None
    if mode == "skeleton" and base_cou is None:
        raise SpecValidationError(
            "package_context.mode=skeleton requires package_context.base_cou to be set"
        )

    factors_raw = _require(pkg_ctx, "package_context.factors", list, src=pkg_ctx, key="factors")
    factors = _normalize_factors(factors_raw, pack_name)

    decision = _require(pkg_ctx, "package_context.decision", str, src=pkg_ctx, key="decision")
    if decision not in VALID_DECISIONS:
        raise SpecValidationError(
            f"package_context.decision must be one of {sorted(VALID_DECISIONS)}, got {decision!r}"
        )

    mrl = pkg_ctx.get("mrl")
    if mrl is not None:
        if not isinstance(mrl, int) or mrl < 1 or mrl > 5:
            raise SpecValidationError(f"package_context.mrl must be int 1..5, got {mrl!r}")

    gen = _require(raw, "generation", dict)
    model = _require(gen, "generation.model", str, src=gen, key="model").strip()
    if not model:
        raise SpecValidationError("generation.model must be a non-empty string")

    n_variants = gen.get("n_variants", 5)
    if not isinstance(n_variants, int) or n_variants < 1 or n_variants > 50:
        raise SpecValidationError(
            f"generation.n_variants must be int 1..50, got {n_variants!r}"
        )

    subtlety = _require(gen, "generation.subtlety", str, src=gen, key="subtlety")
    if subtlety not in VALID_SUBTLETIES:
        raise SpecValidationError(
            f"generation.subtlety must be one of {sorted(VALID_SUBTLETIES)}, got {subtlety!r}"
        )

    temperature = float(gen.get("temperature", 0.7))
    max_tokens = int(gen.get("max_tokens", 4000))
    seed = gen.get("seed")
    if seed is not None and not isinstance(seed, int):
        raise SpecValidationError(f"generation.seed must be int or null, got {type(seed).__name__}")

    output = raw.get("output", {}) or {}
    name_template = output.get("package_name_template", "{spec_id}-v{variant_num:02d}")
    include_provenance = bool(output.get("include_provenance", True))

    _, spec_hash = canonicalize_and_hash(raw)

    return AdversarialSpec(
        spec_id=spec_id,
        target_weakener=weakener,
        defeater_type=defeater,
        uncertainty_category=uncertainty,
        coverage_intent=intent,
        pack=pack_name,
        mode=mode,
        base_cou=base_cou,
        factors=factors,
        decision=decision,
        mrl=mrl,
        generation_model=model,
        n_variants=n_variants,
        subtlety=subtlety,
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        package_name_template=name_template,
        include_provenance=include_provenance,
        spec_hash=spec_hash,
        spec_path=spec_path,
        raw=raw,
    )


def _require(container: dict, dotted_name: str, expected_type: type, *, src=None, key: str = None) -> Any:
    """Fetch *key* (or *dotted_name*) from *container*/*src*; raise SpecValidationError on missing/wrong type."""
    lookup = src if src is not None else container
    lookup_key = key if key is not None else dotted_name
    if lookup_key not in lookup or lookup[lookup_key] is None:
        raise SpecValidationError(f"missing required field: {dotted_name}")
    value = lookup[lookup_key]
    if not isinstance(value, expected_type):
        raise SpecValidationError(
            f"{dotted_name} must be {expected_type.__name__}, got {type(value).__name__}"
        )
    return value


def _resolve_base_cou(raw_path: str) -> Path:
    """Resolve a base_cou path (file or directory) relative to repo root.

    If the path is a directory, pick the first ``*.jsonld`` file inside
    (preferring ``uofa-*.jsonld``).
    """
    p = Path(raw_path)
    if not p.is_absolute():
        try:
            repo_root = paths.find_repo_root()
        except FileNotFoundError:
            repo_root = Path.cwd()
        p = (repo_root / p).resolve()

    if not p.exists():
        raise SpecValidationError(f"package_context.base_cou not found: {p}")

    if p.is_dir():
        candidates = sorted(p.glob("uofa-*.jsonld")) or sorted(p.glob("*.jsonld"))
        if not candidates:
            raise SpecValidationError(f"no *.jsonld file found inside base_cou directory: {p}")
        return candidates[0]

    return p


def _normalize_factors(factors_raw: list, pack_name: str) -> list[str]:
    """Normalize spec factor names to the pack's canonical sentence-case names.

    Spec YAML Appendix A uses CamelCase (``ModelForm``), the pack uses sentence
    case (``Model form``). Use fuzzy matching to bridge both. Unknown factors
    raise SpecValidationError.
    """
    if not factors_raw:
        raise SpecValidationError("package_context.factors must be a non-empty list")

    known = _known_factor_names(pack_name)
    known_lower = {n.lower(): n for n in known}
    normalized: list[str] = []
    for raw_name in factors_raw:
        if not isinstance(raw_name, str):
            raise SpecValidationError(
                f"factor names must be strings, got {type(raw_name).__name__}: {raw_name!r}"
            )
        canonical = _match_factor(raw_name, known, known_lower)
        if canonical is None:
            raise SpecValidationError(
                f"factor {raw_name!r} is not a known {pack_name} factor. "
                f"Known factors: {known}"
            )
        normalized.append(canonical)
    return normalized


def _match_factor(raw_name: str, known: list[str], known_lower: dict[str, str]) -> str | None:
    # Exact match
    if raw_name in known:
        return raw_name
    # Case-insensitive match
    if raw_name.lower() in known_lower:
        return known_lower[raw_name.lower()]
    # CamelCase → spaced
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", raw_name).lower()
    if spaced in known_lower:
        return known_lower[spaced]
    # Fuzzy match as last resort
    candidates = difflib.get_close_matches(raw_name, known, n=1, cutoff=0.6)
    if candidates:
        return candidates[0]
    candidates = difflib.get_close_matches(spaced, [n.lower() for n in known], n=1, cutoff=0.6)
    if candidates:
        return known_lower[candidates[0]]
    return None


def _known_factor_names(pack_name: str) -> list[str]:
    """Return the canonical factor name list for *pack_name*.

    TODO: replace hardcoded dispatch with pack-manifest lookup once the
    ``factors`` field in pack.json is expanded to carry names.
    """
    if pack_name == "vv40":
        return list(VV40_FACTOR_NAMES)
    if pack_name in {"nasa-7009b", "nasa"}:
        return list(NASA_ALL_FACTOR_NAMES)
    # Fallback: union of both (permissive for unknown packs)
    return list(VV40_FACTOR_NAMES) + [
        n for n in NASA_ALL_FACTOR_NAMES if n not in VV40_FACTOR_NAMES
    ]


@lru_cache(maxsize=None)
def _known_weakener_ids(pack_name: str) -> frozenset[str]:
    """Harvest W-XX-NN IDs from all active rule files for *pack_name*."""
    ids: set[str] = set()
    try:
        root = paths.find_repo_root()
    except FileNotFoundError:
        return frozenset()

    # Switch active pack temporarily so all_rules_files picks up pack-specific rules.
    saved = paths.get_active_pack()
    try:
        paths.set_active_pack([pack_name])
        rule_files = paths.all_rules_files(root=root)
    finally:
        paths.set_active_pack(saved)

    for rf in rule_files:
        try:
            text = Path(rf).read_text()
        except OSError:
            continue
        ids.update(WEAKENER_ID_RE.findall(text))
    return frozenset(ids)


def _validate_pack_exists(pack_name: str) -> None:
    try:
        installed = paths.list_packs()
    except FileNotFoundError:
        installed = []
    if pack_name not in installed:
        raise SpecValidationError(
            f"pack {pack_name!r} not found. Installed packs: {sorted(installed)}"
        )
