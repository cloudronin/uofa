"""Pre-extract rule router: pick ONE primary standard from raw evidence.

Routing signals like factorStandard only exist *after* extraction, but the
chosen pack selects the (pack-specific) extraction prompt - so the router must
decide up front from raw text + filenames. It is deliberately simple and
explainable (the product is credibility): keyword cues, an absolute-weight
floor, and a human-readable "why". Core is always-on and never a choice here.

Crucially, confidence is NOT just winner/(winner+runnerup) - that ratio is
meaningless when both standards score near zero (a generic bundle). We gate on
the *absolute* winning weight: below MIN_SIGNAL, `low_confidence` is set so the
UI requires explicit confirmation instead of silently defaulting to vv40.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# (keyword, weight) - lowercased substring match over filenames + corpus text.
VV40_CUES: list[tuple[str, int]] = [
    ("v&v 40", 3), ("vv40", 3), ("vv-40", 3), ("asme", 2),
    ("context of use", 2), ("model risk", 2), ("medical device", 2),
    ("device class", 2), ("intended use", 1), ("fda", 1),
    ("verification and validation", 1), ("hemolysis", 1),
]
NASA_CUES: list[tuple[str, int]] = [
    ("nasa", 3), ("7009", 3), ("credibility assessment scale", 3),
    ("aerospace", 2), ("spaceflight", 2), ("results robustness", 2),
    ("use history", 2), ("data pedigree", 2), ("assessment phase", 2),
    ("modeling and simulation", 1), ("m&s", 1),
]

# Absolute winning weight below which we don't trust the pick.
MIN_SIGNAL = 3

_LABEL = {"vv40": "V&V 40", "nasa-7009b": "NASA-STD-7009B"}


@dataclass
class RouterDecision:
    primary: str
    alternative: str
    confidence: float
    low_confidence: bool
    why: str
    scores: dict = field(default_factory=dict)


def _corpus_text(corpus) -> str:
    parts = [m.get("name", "") for m in getattr(corpus, "file_manifest", [])]
    parts += [c.source_file or "" for c in getattr(corpus, "chunks", [])]
    parts += [c.text or "" for c in getattr(corpus, "chunks", [])]
    return "\n".join(parts).lower()


def _score(text: str, cues: list[tuple[str, int]]) -> tuple[int, list[str]]:
    hits = [(kw, w) for kw, w in cues if kw in text]
    return sum(w for _, w in hits), [kw for kw, _ in hits]


def route(corpus) -> RouterDecision:
    text = _corpus_text(corpus)
    vv_score, vv_hits = _score(text, VV40_CUES)
    na_score, na_hits = _score(text, NASA_CUES)

    # Tie or vv40-favoured -> vv40 (documented primary / sample standard).
    if na_score > vv_score:
        primary, alt, win, runner, hits = "nasa-7009b", "vv40", na_score, vv_score, na_hits
    else:
        primary, alt, win, runner, hits = "vv40", "nasa-7009b", vv_score, na_score, vv_hits

    total = win + runner
    confidence = round(win / total, 2) if total else 0.0
    low_confidence = win < MIN_SIGNAL

    label = _LABEL[primary]
    if low_confidence:
        why = (
            f"We couldn't confidently route this bundle. Best guess {label}. "
            "Please confirm or switch before we analyze."
        )
    else:
        matched = ", ".join(f"'{h}'" for h in hits[:3])
        why = f"Detected {label}. Matched {matched}."

    return RouterDecision(
        primary=primary,
        alternative=alt,
        confidence=confidence,
        low_confidence=low_confidence,
        why=why,
        scores={"vv40": vv_score, "nasa-7009b": na_score},
    )
