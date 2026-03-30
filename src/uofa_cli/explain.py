"""Generic divergence explanations for weakener patterns.

Reads the ``description`` field from WeakenerAnnotation objects.
Falls back to a generic message when no description is present.
No pattern-specific logic — the rule engine is the authority on *why*
a weakener fires.
"""


def _cou_name(doc: dict) -> str:
    """Extract a short COU display name from a UofA document."""
    cou = doc.get("hasContextOfUse", {})
    if isinstance(cou, dict):
        return cou.get("name", doc.get("name", "unknown"))
    return doc.get("name", "unknown")


def _short_iri(iri: str) -> str:
    """Extract the local name from an IRI."""
    if isinstance(iri, str):
        return iri.rsplit("/", 1)[-1]
    return str(iri)


def explain_divergence(pattern_id: str, doc_with: dict, doc_without: dict,
                       weakener: dict) -> list[str]:
    """Generate explanation lines for a divergent weakener.

    Args:
        pattern_id: The weakener pattern ID (e.g. "W-AL-01").
        doc_with: The UofA doc where the weakener IS present.
        doc_without: The UofA doc where the weakener is NOT present.
        weakener: The weakener annotation dict.

    Returns:
        List of 1-2 explanation strings.
    """
    name_with = _cou_name(doc_with)
    name_without = _cou_name(doc_without)

    description = weakener.get("description", "")
    affected = weakener.get("affectedNode", "")
    short = _short_iri(affected) if affected else ""

    lines = []

    if description:
        lines.append(f"{name_with}: {description}")
    elif short:
        lines.append(f"{name_with}: pattern {pattern_id} fires — affects {short}.")
    else:
        lines.append(f"{name_with}: pattern {pattern_id} fires.")

    lines.append(f"{name_without}: pattern does not fire.")

    return lines
