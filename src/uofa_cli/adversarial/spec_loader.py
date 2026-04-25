"""Parse and validate adversarial generation specs (YAML).

Spec format: UofA_Adversarial_Gen_Spec_v1.1 §5. Validation rules §5.2.
Phase 2 source-taxonomy field added per UofA_Adversarial_Gen_Phase2_Spec_v1_7.md §5.2.
Loader is pack-aware: the `pack` field selects the factor registry and the
rule files used to harvest known weakener IDs.

TODO: future packs (ssp-ls-traceability, mossec) should plug in via an
abstract pack-metadata API rather than hardcoded dispatch in
``_known_factor_names``. Phase 1 keeps the dispatch explicit.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from uofa_cli import paths
from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES
from uofa_cli.integrity import canonicalize_and_hash

VALID_DEFEATERS = {"D1", "D2", "D3", "D4", "D5", "structural"}
VALID_INTENTS = {"confirm_existing", "gap_probe", "negative_control", "interaction"}
VALID_SUBTLETIES = {"low", "medium", "high"}
VALID_DECISIONS = {"Accepted", "Not accepted", "Conditional"}
VALID_MODES = {"skeleton", "narrative-only"}
VALID_UNCERTAINTY = {"epistemic", "aleatory", "ontological", "argument", "structural"}
SPEC_ID_RE = re.compile(r"^[a-z0-9-]+$")
WEAKENER_ID_RE = re.compile(r"patternId\s+'((?:W-[A-Z]+-\d{2})|(?:COMPOUND-\d{2}))'")
NEGATIVE_CONTROL_SENTINEL = "control/none"


class SpecValidationError(ValueError):
    """Raised when a spec YAML fails validation. Generator maps to exit code 3."""


class SourceTaxonomyError(SpecValidationError):
    """Raised when source_taxonomy validation fails. Generator maps to exit code 5.

    Per UofA_Adversarial_Gen_Phase2_Spec_v1_7.md §5.2, gap_probe specs must declare
    a source_taxonomy that resolves against ``packs/core/source_taxonomies.json``;
    negative_control specs must use the sentinel ``"control/none"``.
    """


@dataclass
class AdversarialSpec:
    spec_id: str
    target_weakener: str | None
    defeater_type: str | None
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
    source_taxonomy: str | None
    raw: dict = field(repr=False)

    def prompt_template_id(self) -> str:
        """E.g. ``'d3_undercutting_inference.W_AR_05'`` or
        ``'evidence_validity.gohar_evidence_validity_data_drift'`` for
        gap_probe specs without a target weakener.
        """
        if self.target_weakener:
            suffix = self.target_weakener.replace("-", "_")
        elif self.source_taxonomy:
            suffix = (
                self.source_taxonomy.replace("/", "_").replace("-", "_")
            )
        else:
            suffix = "unknown"
        return f"{self._template_module()}.{suffix}"

    def _template_module(self) -> str:
        from uofa_cli.adversarial.prompts import resolve_template_module_path

        mod_path = resolve_template_module_path(self)
        if not mod_path:
            raise NotImplementedError(
                f"No prompt template registered for spec {self.spec_id!r} "
                f"(coverage_intent={self.coverage_intent!r}, "
                f"target_weakener={self.target_weakener!r}, "
                f"source_taxonomy={self.source_taxonomy!r})"
            )
        return mod_path.rsplit(".", 1)[-1]


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
    intent = _require(
        target, "target.coverage_intent", str, src=target, key="coverage_intent"
    )
    if intent not in VALID_INTENTS:
        raise SpecValidationError(
            f"target.coverage_intent must be one of {sorted(VALID_INTENTS)}, got {intent!r}"
        )

    # gap_probe specs may declare weakener: null and defeater_type: null per
    # spec §6.2 — they target literature-defined defeaters that do NOT map
    # to a UofA pattern. confirm_existing / interaction / negative_control
    # specs must declare a weakener.
    weakener_required = intent in ("confirm_existing", "interaction", "negative_control")
    weakener_raw = target.get("weakener")
    defeater_raw = target.get("defeater_type")

    if weakener_required:
        if not isinstance(weakener_raw, str):
            raise SpecValidationError(
                f"target.weakener must be a string for coverage_intent={intent!r}, "
                f"got {type(weakener_raw).__name__}"
            )
        if not isinstance(defeater_raw, str):
            raise SpecValidationError(
                f"target.defeater_type must be a string for coverage_intent={intent!r}, "
                f"got {type(defeater_raw).__name__}"
            )
        weakener = weakener_raw
        defeater = defeater_raw
    else:
        # gap_probe: weakener and defeater_type may be null
        if weakener_raw is not None and not isinstance(weakener_raw, str):
            raise SpecValidationError(
                f"target.weakener must be a string or null, got {type(weakener_raw).__name__}"
            )
        if defeater_raw is not None and not isinstance(defeater_raw, str):
            raise SpecValidationError(
                f"target.defeater_type must be a string or null, got {type(defeater_raw).__name__}"
            )
        weakener = weakener_raw
        defeater = defeater_raw

    uncertainty = _require(
        target,
        "target.uncertainty_category",
        str,
        src=target,
        key="uncertainty_category",
    )

    if defeater is not None and defeater not in VALID_DEFEATERS:
        raise SpecValidationError(
            f"target.defeater_type must be one of {sorted(VALID_DEFEATERS)} or null, got {defeater!r}"
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

    if weakener is not None:
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

    source_taxonomy = _validate_source_taxonomy(target, intent, weakener)

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
        source_taxonomy=source_taxonomy,
        raw=raw,
    )


# ----- Source-taxonomy registry (Phase 2, spec §6.1) ----- #


@lru_cache(maxsize=1)
def _load_source_taxonomy_registry() -> dict:
    """Load and cache ``packs/core/source_taxonomies.json``.

    Returns an empty dict on FileNotFoundError so spec_loader can still parse
    existing fixtures during early Phase 2 work where the registry may not yet
    be populated. Validation that requires the registry will fall back gracefully.
    """
    try:
        root = paths.find_repo_root()
    except FileNotFoundError:
        return {}
    registry_path = root / "packs" / "core" / "source_taxonomies.json"
    if not registry_path.exists():
        return {}
    try:
        with open(registry_path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SourceTaxonomyError(
            f"failed to parse source taxonomy registry at {registry_path}: {e}"
        ) from e


def resolve_taxonomy_path(path: str, registry: dict | None = None) -> bool:
    """Return True if *path* resolves against the registry's categories tree.

    Path format: ``<taxonomy>/<category>/[<sub_category>/]<sub_type>``. Two- and
    three-level nesting both supported (e.g., ``gohar/requirements/missing`` or
    ``gohar/logical_fallacies/relevance/red-herring``).
    """
    if registry is None:
        registry = _load_source_taxonomy_registry()
    if not registry:
        return False
    parts = path.split("/")
    if len(parts) < 3:
        return False
    tax_name, *rest = parts
    tax = registry.get("taxonomies", {}).get(tax_name)
    if not tax:
        return False
    node: Any = tax.get("categories", {})
    for p in rest[:-1]:
        if isinstance(node, dict):
            node = node.get(p)
            if node is None:
                return False
        else:
            return False
    leaf = rest[-1]
    if isinstance(node, list):
        return leaf in node
    if isinstance(node, dict):
        return leaf in node
    return False


def default_taxonomy_for_pattern(weakener_id: str, registry: dict | None = None) -> str | None:
    """Return the default source_taxonomy attribution for a UofA pattern, if defined.

    Used when ``coverage_intent: confirm_existing`` and the spec omits the
    ``source_taxonomy`` field.
    """
    if registry is None:
        registry = _load_source_taxonomy_registry()
    if not registry:
        return None
    table = registry.get("default_attribution_for_uofa_pattern", {})
    return table.get(weakener_id)


def _validate_source_taxonomy(
    target: dict, coverage_intent: str, weakener_id: str
) -> str | None:
    """Validate ``target.source_taxonomy`` per spec §5.2 and return resolved value.

    - ``gap_probe``: required, must resolve in registry. Missing/unresolved → SourceTaxonomyError.
    - ``confirm_existing``: optional. If omitted, use the registry's default attribution
      for the target weakener. If supplied, must resolve.
    - ``negative_control``: must equal the sentinel ``"control/none"``.
    - ``interaction``: optional, no resolution required (multi-target attribution
      is recorded per-template, not per-spec).
    """
    raw_value = target.get("source_taxonomy")
    if raw_value is not None and not isinstance(raw_value, str):
        raise SourceTaxonomyError(
            f"target.source_taxonomy must be a string, "
            f"got {type(raw_value).__name__}"
        )

    registry = _load_source_taxonomy_registry()

    if coverage_intent == "negative_control":
        if raw_value != NEGATIVE_CONTROL_SENTINEL:
            raise SourceTaxonomyError(
                f"target.source_taxonomy for coverage_intent=negative_control must be "
                f"{NEGATIVE_CONTROL_SENTINEL!r}, got {raw_value!r}"
            )
        return NEGATIVE_CONTROL_SENTINEL

    if coverage_intent == "gap_probe":
        if not raw_value:
            raise SourceTaxonomyError(
                "target.source_taxonomy is required for coverage_intent=gap_probe. "
                "Provide a path like 'gohar/evidence_validity/data-drift' "
                "(see packs/core/source_taxonomies.json)."
            )
        if registry and not resolve_taxonomy_path(raw_value, registry):
            raise SourceTaxonomyError(
                f"target.source_taxonomy {raw_value!r} does not resolve in the "
                f"registry at packs/core/source_taxonomies.json"
            )
        return raw_value

    if coverage_intent == "confirm_existing":
        if raw_value:
            if registry and not resolve_taxonomy_path(raw_value, registry):
                raise SourceTaxonomyError(
                    f"target.source_taxonomy {raw_value!r} does not resolve in the "
                    f"registry at packs/core/source_taxonomies.json"
                )
            return raw_value
        # Fall back to the default attribution for this UofA pattern
        default = default_taxonomy_for_pattern(weakener_id, registry)
        return default

    # interaction: optional, no validation required
    if raw_value and registry and not resolve_taxonomy_path(raw_value, registry):
        raise SourceTaxonomyError(
            f"target.source_taxonomy {raw_value!r} does not resolve in the "
            f"registry at packs/core/source_taxonomies.json"
        )
    return raw_value


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
