#!/usr/bin/env python3
"""A component registry for the keyless stages, so combinations can be swept.

Modelled on spaCy's processing pipelines: named components, one job each, a
declared contract, assembled by name. The value here is not elegance -- it is
that three classes of bug found in this project came from every candidate being
a standalone script.

## What the duplication cost

Twelve scripts each reimplement document reading. Two of them, K5 and K3c, called
`read_text()` on a PDF, scored the resulting binary garbage, and reported it as a
failure to extract; the verdict changed once they read the corpus properly.

A script announced itself as "RRF@5 -> K2, end to end" while `quote_for` was
never called. It measured router recall and reported it as a composed pipeline
result. Nothing checked that the stage it named actually ran.

Four scripts of ten define an explicit control; the rest embed one inline or omit
it. `control_constant_list` scoring 1.000 on detection is the single most
important finding in this line of work, and it was found because someone wrote
the control down.

## The contracts

    read    (bundle)                 -> Doc          once per document
    route   (Doc, factor, ctx)       -> [int]        ranked sentence indices
    select  (Doc, [int], ctx)        -> int          one index from the shortlist

A stage that does not run cannot be silently claimed, because assembling a
pipeline names every stage and `describe()` prints what was actually used.

## Controls are components

Every null model registers in the same registry as the candidates it competes
with, under the same contract. A stage cannot be swept without its control
appearing in the same table, which is the discipline that produced this
project's most useful results and the one most easily skipped under time
pressure.
"""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Callable

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from document_furniture import strip_furniture  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

REGISTRY: dict[str, dict[str, Callable]] = {"route": {}, "select": {}}
IS_CONTROL: set[tuple[str, str]] = set()


def component(stage: str, name: str, control: bool = False):
    """Register a component under a stage. `control=True` marks it a null model."""
    if stage not in REGISTRY:
        raise ValueError(f"unknown stage {stage!r}; have {sorted(REGISTRY)}")

    def deco(fn):
        REGISTRY[stage][name] = fn
        if control:
            IS_CONTROL.add((stage, name))
        return fn
    return deco


@dataclass
class Doc:
    """A document, read once. Every stage sees the same text.

    The single most repeated bug in this project's scripts was each one reading
    documents its own way -- so a candidate could be measured against binary
    garbage and no one would know until its verdict looked strange.
    """
    bundle: pathlib.Path
    sents: list[str]
    pool: list[int]                      # indices surviving the furniture filter
    gold: dict[tuple, list[str]] = field(default_factory=dict)

    @property
    def texts(self) -> list[str]:
        return [self.sents[i] for i in self.pool]

    @property
    def low(self) -> list[str]:
        return [" ".join(t.split()).lower() for t in self.texts]


_CACHE = pathlib.Path(__file__).parent / ".doc_cache"


def _cache_key(bundle: pathlib.Path) -> pathlib.Path:
    """Keyed on the source bytes, so a regenerated corpus misses the cache.

    Content-addressed rather than path-addressed on purpose: a stale corpus read
    is the same class of defect as a stale measurement, and this project has one
    of those already.
    """
    import hashlib
    h = hashlib.sha256()
    for p in sorted((bundle / "source").glob("*")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return _CACHE / f"{bundle.name}-{h.hexdigest()[:16]}.json"


def read(bundle: pathlib.Path) -> Doc:
    """PDF or markdown, through the project's own reader either way."""
    from uofa_cli.readers.pdf_reader import read_pdf

    ck = _cache_key(bundle)
    if ck.exists():
        blob = json.loads(ck.read_text())
        sents, pool = blob["sents"], blob["pool"]
        return _with_gold(Doc(bundle=bundle, sents=sents, pool=pool), bundle)

    parts = []
    for p in sorted((bundle / "source").glob("*")):
        if p.suffix.lower() == ".pdf":
            parts.append("\n".join(c.text for c in read_pdf(p)))
        elif p.suffix.lower() in (".md", ".txt"):
            parts.append(p.read_text(errors="ignore"))
    sents = sentences("\n".join(parts))
    _, pool, _ = strip_furniture(sents, NAMES)
    _CACHE.mkdir(exist_ok=True)
    ck.write_text(json.dumps({"sents": sents, "pool": pool}))
    return _with_gold(Doc(bundle=bundle, sents=sents, pool=pool), bundle)


def _with_gold(doc: Doc, bundle: pathlib.Path) -> Doc:
    """Gold is read fresh every time, never cached -- it is the thing that moves."""
    gt_path = bundle / "ground_truth.json"
    if gt_path.exists():
        gt = json.loads(gt_path.read_text())
        for f in gt.get("findings", []):
            if f.get("status") == "ambiguous":
                continue
            key = (f["factor"], f.get("model", ""), f.get("mechanism", ""))
            doc.gold.setdefault(key, []).extend(f.get("spans") or [f["span"]])
    return doc


@dataclass
class Pipeline:
    """A named combination. `describe()` is what makes a claim checkable."""
    route: str
    select: str

    def __post_init__(self) -> None:
        for stage, name in (("route", self.route), ("select", self.select)):
            if name not in REGISTRY[stage]:
                raise ValueError(
                    f"no {stage} component {name!r}; have "
                    f"{sorted(REGISTRY[stage])}")

    def describe(self) -> str:
        tag = lambda s, n: f"{n}*" if (s, n) in IS_CONTROL else n  # noqa: E731
        return f"route={tag('route', self.route)} select={tag('select', self.select)}"

    @property
    def is_all_control(self) -> bool:
        return (("route", self.route) in IS_CONTROL
                and ("select", self.select) in IS_CONTROL)

    def run(self, doc: Doc, factor: str, ctx, k: int) -> tuple[list[int], int]:
        """Returns (shortlist, chosen index into the shortlist)."""
        ranked = REGISTRY["route"][self.route](doc, factor, ctx)[:k]
        if not ranked:
            return [], -1
        return ranked, REGISTRY["select"][self.select](doc, ranked, ctx)


def score(pipe: Pipeline, docs: list[Doc], ctx, k: int) -> dict:
    """Router recall, conditional selection, and the product of the two.

    Reported separately and then multiplied, because a single composed number
    does not say which stage to fix -- and because this project has already
    published a router-recall figure as though it were end-to-end.
    """
    reach = sel = n = end = 0
    for doc in docs:
        for (factor, _m, _x), spans in doc.gold.items():
            gl = [" ".join(s.split()).lower() for s in spans
                  if len(" ".join(s.split())) > 12]
            if not gl:
                continue
            n += 1
            shortlist, chosen = pipe.run(doc, factor, ctx, k)
            if not shortlist:
                continue
            correct = {j for j, idx in enumerate(shortlist)
                       if any(g in doc.low[idx] for g in gl)}
            if correct:
                reach += 1
                sel += chosen in correct
                end += chosen in correct
    return {"pairs": n,
            "router_recall": reach / max(n, 1),
            "select_given_reached": sel / max(reach, 1),
            "end_to_end": end / max(n, 1),
            "reached": reach}
