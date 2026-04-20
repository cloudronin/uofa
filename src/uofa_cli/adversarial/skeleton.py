"""Skeleton-mode loader: extract identity + factor scaffold from a base COU.

v1.1 §14 Q4 resolution. Reduces COV-WRONG outcomes caused by LLM-invented
COU metadata.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from uofa_cli.excel_constants import CONTEXT_URL, VV40_FACTOR_NAMES

# Top-level keys preserved verbatim into the skeleton identity block.
IDENTITY_KEYS = {
    "couName",
    "decision",
    "modelRiskLevel",
    "deviceClass",
    "assuranceLevel",
    "conformsToProfile",
    "name",
    "description",
    "id",
}

# Top-level keys re-stamped onto the generated package after the LLM returns.
PROVENANCE_KEYS = {
    "bindsRequirement",
    "bindsClaim",
    "bindsModel",
    "bindsDataset",
    "wasDerivedFrom",
    "wasAttributedTo",
    "generatedAtTime",
}

# Fields stripped from the base COU before the skeleton is used.
STRIP_KEYS = {
    "hash",
    "signature",
    "signatureAlg",
    "canonicalizationAlg",
}


class SkeletonLoadError(Exception):
    """Raised when the base COU cannot be loaded or parsed."""


def load_base_cou_skeleton(base_cou: Path, pack: str = "vv40") -> dict:
    """Return a skeleton dict usable by prompt.render().

    Keys: identity (dict), factor_scaffold (list of stubs), decision_shell
    (hasDecisionRecord object), context_of_use (inline object), top_level_stamps
    (dict of PROVENANCE_KEYS), context_url (string).

    Raises SkeletonLoadError on parse failure or missing identity fields.
    """
    path = _resolve_base_cou_path(base_cou)
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise SkeletonLoadError(f"failed to read base COU {path}: {e}") from e

    if not isinstance(doc, dict):
        raise SkeletonLoadError(f"base COU is not a JSON-LD object: {path}")

    identity = {k: doc[k] for k in IDENTITY_KEYS if k in doc}
    if not identity.get("name"):
        raise SkeletonLoadError(f"base COU missing required 'name' field: {path}")

    context_of_use = deepcopy(doc.get("hasContextOfUse"))
    decision_shell = deepcopy(doc.get("hasDecisionRecord"))

    factor_scaffold = _build_factor_scaffold(doc, pack)

    top_level_stamps = {k: deepcopy(doc[k]) for k in PROVENANCE_KEYS if k in doc}

    return {
        "identity": identity,
        "context_of_use": context_of_use,
        "decision_shell": decision_shell,
        "factor_scaffold": factor_scaffold,
        "top_level_stamps": top_level_stamps,
        "context_url": CONTEXT_URL,
        "source_path": str(path),
    }


def _resolve_base_cou_path(base_cou: Path) -> Path:
    p = Path(base_cou)
    if p.is_dir():
        candidates = sorted(p.glob("uofa-*.jsonld")) or sorted(p.glob("*.jsonld"))
        if not candidates:
            raise SkeletonLoadError(f"no *.jsonld file found in base COU dir: {p}")
        return candidates[0]
    if not p.exists():
        raise SkeletonLoadError(f"base COU file not found: {p}")
    return p


def _build_factor_scaffold(doc: dict, pack: str) -> list[dict]:
    """Return a list of factor stubs with factorType pre-populated.

    Uses the factor types already in the base COU if present; otherwise falls
    back to the canonical list for the pack. ``factorStandard`` is preserved.
    """
    existing = doc.get("hasCredibilityFactor", []) or []
    standard = _infer_factor_standard(existing, pack)
    if existing:
        scaffold: list[dict] = []
        for f in existing:
            if not isinstance(f, dict):
                continue
            ft = f.get("factorType")
            if not ft:
                continue
            scaffold.append({
                "type": "CredibilityFactor",
                "factorType": ft,
                "factorStandard": f.get("factorStandard", standard),
            })
        if scaffold:
            return scaffold

    # Fallback: canonical VV40 factor list.
    return [
        {"type": "CredibilityFactor", "factorType": name, "factorStandard": standard}
        for name in VV40_FACTOR_NAMES
    ]


def _infer_factor_standard(existing: list, pack: str) -> str:
    for f in existing or []:
        if isinstance(f, dict) and f.get("factorStandard"):
            return f["factorStandard"]
    if pack == "vv40":
        return "ASME-VV40-2018"
    if pack in {"nasa-7009b", "nasa"}:
        return "NASA-STD-7009B"
    return "ASME-VV40-2018"
