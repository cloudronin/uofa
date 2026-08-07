"""PDF reader — extracts text per page via pdfplumber.

## Multi-column pages are detected, not assumed

`page.extract_text()` reads a page in raster order, so on a two-column layout it
emits the left column's line then the right column's line, joined. Every sentence
becomes two half-sentences from unrelated paragraphs spliced together. The words
all survive; no sentence does.

Measured on the OpenSim credibility paper against 13 hand-annotated evidence
spans -- the spans a reviewer would cite for each NASA-STD-7009A factor:

    extract_text()                1/13 contiguous  ( 8%)
    extract_text(layout=True)     1/13 contiguous  ( 8%)
    per-column extraction        12/13 contiguous  (92%)

Token recall was ~1.00 in every case. This is invisible to anything that counts
words and fatal to anything that quotes, classifies, or attributes a *sentence* --
which is what the extraction pipeline downstream does.

It went unnoticed because the synthetic corpus is markdown, where the question
never arises. Only real PDFs are affected.

## Why detection rather than always splitting

Splitting a single-column page at its midpoint would cut every line in half and
break the documents that currently work. So the gutter is detected: a vertical
band spanning most of the page's height that no word crosses. No gutter, no
split, and the page is read exactly as before.
"""

from __future__ import annotations

import re
from pathlib import Path

from uofa_cli.document_reader import DocumentChunk

# Only look for a gutter in the middle of the page. A margin is not a gutter.
_SEARCH_LO, _SEARCH_HI = 0.30, 0.70

# Below this many words a page is a figure, a title page, or a table; column
# inference from a handful of words is noise.
_MIN_WORDS = 40

# A line wider than this fraction of the page is a running head, a figure
# caption or a rule -- a full-width element that legitimately crosses the
# gutter. Leaving these in hides the gutter completely.
_FULL_WIDTH_FRAC = 0.80

# Fraction of body words that may overlap the candidate gutter. Measured
# separation on the corpus is wide, so the threshold is not finely tuned:
#
#     two-column pages   0.000 - 0.010     (opensim journal article, 8 pages)
#     single-column      0.056 - 0.071     (opensim supplemental, elemance)
#
# 0.03 sits ~3x above the highest two-column value and ~half the lowest
# single-column one. A few words genuinely do cross a real gutter (an italic
# run-in, a wide inline formula), so zero tolerance rejects real two-column
# pages -- that was the first version of this check and it detected nothing.
_MAX_GUTTER_COVERAGE = 0.03

_BINS = 120

# pdfplumber infers word boundaries from horizontal character gaps, and its
# default threshold is too wide for some publishers' fonts: the APL Bioengineering
# PDFs came out as "thisworkseekstoperformapopulation-basedvalidation", losing
# ~10% of tokens into run-together strings and roughly halving the token count.
#
# Measured over every document in the corpus. Two are repaired and none regress:
#
#     document    default -> x_tolerance=1.2   (fraction of tokens >20 chars)
#     tavi1        9.98%  ->  0.02%            3,746 -> 6,549 tokens
#     tavi2       11.25%  ->  0.01%            3,963 -> 7,129 tokens
#     bologna      0.06%  ->  0.04%
#     nagaraja     0.00%  ->  0.00%
#     morrison     0.02%  ->  0.01%
#     opensim      0.08%  ->  0.08%
#     elemance     0.01%  ->  0.01%
#     ared         0.06%  ->  0.06%
#
# Two documents were discarded from the corpus over this before it was diagnosed
# as a tooling default rather than a property of the documents.
_X_TOLERANCE = 1.2


def _find_gutter(words: list[dict], x0: float, x1: float) -> float | None:
    """The x of a low-coverage vertical band, or None for a single column.

    Coverage, not word-start clustering: justified text starts words at many x
    positions, so left-margin modes do not separate the two layouts. What does
    separate them is that in a two-column page a vertical band exists that
    almost no *body* word overlaps, and in a single-column page every band in
    the text block is crossed by most lines.
    """
    if len(words) < _MIN_WORDS:
        return None
    width = x1 - x0
    if width <= 0:
        return None

    # Group into visual lines and drop the full-width ones before measuring.
    lines: dict[int, list[dict]] = {}
    for w in words:
        lines.setdefault(round(w["top"] / 3), []).append(w)
    body = [
        w
        for ws in lines.values()
        if (max(a["x1"] for a in ws) - min(a["x0"] for a in ws)) < width * _FULL_WIDTH_FRAC
        for w in ws
    ]
    if len(body) < 30:
        return None

    coverage = [0] * _BINS
    for w in body:
        lo = max(0, int((w["x0"] - x0) / width * _BINS))
        hi = min(_BINS - 1, int((w["x1"] - x0) / width * _BINS))
        for i in range(lo, hi + 1):
            coverage[i] += 1

    lo_bin, hi_bin = int(_BINS * _SEARCH_LO), int(_BINS * _SEARCH_HI)
    best = min(range(lo_bin, hi_bin), key=lambda i: coverage[i])
    if coverage[best] > len(body) * _MAX_GUTTER_COVERAGE:
        return None
    return x0 + width * (best + 0.5) / _BINS


# A word split across a line break by hyphenation. Measured across the corpus,
# 0.7%-14% of lines end this way -- 14% in the APL Bioengineering PDFs -- and
# each one breaks a sentence in two.
#
# Rejoining needs a decision the hyphen itself does not carry:
#
#     "signifi-" + "cant"    -> "significant"       drop the hyphen
#     "patient-" + "specific" -> "patient-specific"  keep it
#
# There is no lexicon here, so the document's own vocabulary is used as one: if
# the joined form appears elsewhere in the text, drop the hyphen; if the
# hyphenated form appears, keep it; if neither, keep it, because inventing a
# word is worse than leaving a real compound hyphenated.
_HYPHEN_SPLIT = re.compile(r"([A-Za-z]{2,})-$")


def _dehyphenate(prev: str, nxt: str, vocab: frozenset[str]) -> str | None:
    """The rejoined word, or None if this is not a hyphenation split."""
    m = _HYPHEN_SPLIT.search(prev.rstrip())
    if not m:
        return None
    tail = nxt.lstrip().split(" ", 1)[0].strip(".,;:)")
    if not tail or not tail[:1].islower():
        return None
    joined, hyphened = m.group(1) + tail, m.group(1) + "-" + tail
    if joined.lower() in vocab:
        return joined
    if hyphened.lower() in vocab:
        return hyphened
    return hyphened


def _unwrap(text: str) -> str:
    """Join lines a PDF wrapped mid-sentence.

    The second half of the same problem as column interleaving, and it survived
    for the same reason. Downstream, `sentences()` splits on newlines before it
    splits on punctuation -- correct for markdown, where a line is a logical
    unit, and wrong for a PDF, where a newline is where the typesetter ran out
    of column. Without this, a recovered sentence is still delivered as
    fragments: "The assessment score for code verification is 0 and 1" stops
    there, and the clause that says what the 1 refers to is a separate unit.

    A line is joined to the next when it does not end at a sentence boundary and
    the next line continues in lower case. Blank lines stay paragraph breaks,
    and a line ending in terminal punctuation stays a break, so headings, list
    items and table rows are unaffected.
    """
    vocab = frozenset(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{2,}", text))
    out: list[str] = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            out.append("")
            continue
        prev = out[-1] if out else ""
        if prev:
            fixed = _dehyphenate(prev, line, vocab)
            if fixed is not None:
                rest = line.lstrip().split(" ", 1)
                out[-1] = (_HYPHEN_SPLIT.sub("", prev.rstrip()) + fixed
                           + (" " + rest[1] if len(rest) > 1 else ""))
                continue
        cont = (
            prev
            and not prev.rstrip().endswith((".", "!", "?", ":", ";", "•", "-"))
            and (line.lstrip()[:1].islower() or line.lstrip()[:1].isdigit())
        )
        if cont:
            out[-1] = f"{prev.rstrip()} {line.lstrip()}"
        else:
            out.append(line)
    return "\n".join(out)


def _page_text(page) -> str:
    """Page text, read per column when the page has columns."""
    try:
        words = page.extract_words()
    except Exception:  # noqa: BLE001 — malformed page: fall back to raster order
        return _unwrap(page.extract_text(x_tolerance=_X_TOLERANCE) or "")

    x0, _, x1, _ = page.bbox
    gutter = _find_gutter(words, x0, x1)
    if gutter is None:
        return _unwrap(page.extract_text(x_tolerance=_X_TOLERANCE) or "")

    parts = []
    for lo, hi in ((x0, gutter), (gutter, x1)):
        try:
            col = page.crop((lo, page.bbox[1], hi, page.bbox[3])).extract_text(
                x_tolerance=_X_TOLERANCE)
        except Exception:  # noqa: BLE001
            return page.extract_text(x_tolerance=_X_TOLERANCE) or ""
        if col and col.strip():
            parts.append(col)
    # A split that recovered only one side is not a split.
    if len(parts) != 2:
        return _unwrap(page.extract_text(x_tolerance=_X_TOLERANCE) or "")
    return _unwrap("\n".join(parts))


def read_pdf(path: Path) -> list[DocumentChunk]:
    """Read a PDF and return one chunk per page with page numbers."""
    import pdfplumber

    chunks: list[DocumentChunk] = []
    with pdfplumber.open(path) as pdf:
        if not pdf.pages:
            return [DocumentChunk(
                text="(empty PDF)",
                source_file=path.name,
                source_path=str(path),
                format="pdf",
            )]

        has_text = False
        for i, page in enumerate(pdf.pages, start=1):
            text = _page_text(page)
            if text.strip():
                has_text = True
            chunks.append(DocumentChunk(
                text=text,
                source_file=path.name,
                source_path=str(path),
                page_number=i,
                format="pdf",
            ))

        if not has_text:
            # Image-only PDF warning — return empty chunk
            return [DocumentChunk(
                text="(image-only PDF — no extractable text)",
                source_file=path.name,
                source_path=str(path),
                format="pdf",
            )]

    return chunks
