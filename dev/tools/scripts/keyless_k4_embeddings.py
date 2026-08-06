#!/usr/bin/env python3
"""K4: can a local sentence encoder find factors a substring matcher cannot?

This is the hypothesis the investigation turns on. K1 established that the pack
prompts' anchors detect factors at **recall 0.235** with precision 0.973, and
diagnosed why: the anchors are written at the abstraction level of the standard
("QoI directly measures the safety concern") while the documents are written at
the level of the physics ("head rise prediction", "SST k-omega"). Closing that
by enumeration is unbounded.

Supplying that mapping is exactly what an embedding space claims to do. If
`"head rise prediction"` and `"quantity of interest relevant to the decision"`
are close in vector space on domain-specific engineering text, K4 recovers the
recall K1 cannot. If they are not, the answer is that small local encoders do
not carry this kind of domain knowledge, which is worth knowing and closes the
question.

    KILL K4 unless its best F1 beats `control_constant_list`

The first version of this criterion read "recall >= 0.50 at precision >= 0.90",
and K4 passed it at threshold 0.15 with P 0.914 / R 0.993. That result is
worthless: the corpus is 92% `assessed`, so a function that flags every factor
scores P 0.92 / R 1.00 without reading anything. The criterion was saturated by
the null model, which is the precise failure this whole investigation exists to
stop -- written into the criterion for the candidate meant to test it.

Any threshold is free to trade precision for recall. What a threshold cannot do
is beat a constant, so the constant is the criterion.

## Local only, and "keyless" is not "no model"

`all-MiniLM-L6-v2`, ~90 MB, no key, no network at inference. An embedding API
was considered and rejected: it reintroduces the dependency the investigation
exists to remove, so a win there would answer a different question.

The honest comparison is against `ollama/qwen3.5:4b` at ~5 GB and 170-202 s per
bundle, and against sonnet at ~$0.07 per bundle. This script reports encode time
and model size beside accuracy so the three can be read together.

## One encoder, one pooling, one sweep

The plan gives K4 the tightest leash precisely because it is the open
hypothesis and will otherwise absorb unlimited time. If MiniLM at its best
threshold misses the criterion, the finding is "not with a small local encoder"
-- trying six more models is a different investigation.

## Contamination

Factor descriptions come from the pack prompt files, asserted by
`assert_anchors_come_from_the_prompt`. `evidence_keywords` are verbatim source
spans lifted by the corpus generator; embedding those would be scoring the
answer against itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_extract_probe import (  # noqa: E402
    PROMPTS,
    assert_anchors_come_from_the_prompt,
    parse_anchors,
)

ENCODER = "all-MiniLM-L6-v2"

# Chunks shorter than this are headings and table rules; longer ones dilute the
# signal by averaging several claims into one vector.
_MIN_CHUNK, _MAX_CHUNK = 40, 300


def factor_queries(prompt_path: Path) -> dict[str, str]:
    """One query string per factor: its name plus the prompt's own anchors.

    Deliberately the same text K1 matched on. The comparison is what the encoder
    adds over substring matching against identical input, not what a better
    hand-written description would add.
    """
    txt = prompt_path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in re.finditer(r"^\s*\d+\.\s+\*\*(.+?)\*\*:\s*(.*?)$", txt, re.M):
        label, body = m.group(1).strip(), m.group(2).strip()
        out[label] = f"{label}. {body}"
    return out


def chunks(text: str) -> list[str]:
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        if _MIN_CHUNK <= len(block) <= _MAX_CHUNK:
            out.append(block)
        elif len(block) > _MAX_CHUNK:
            for i in range(0, len(block), _MAX_CHUNK):
                piece = block[i:i + _MAX_CHUNK]
                if len(piece) >= _MIN_CHUNK:
                    out.append(piece)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    args = ap.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SystemExit("pip install sentence-transformers (~90 MB model, no key)")
    import numpy as np

    anchors = {p: parse_anchors(path) for p, path in PROMPTS.items()}
    for pack, a in anchors.items():
        assert_anchors_come_from_the_prompt(a, PROMPTS[pack])
    queries = {p: factor_queries(path) for p, path in PROMPTS.items()}

    t0 = time.perf_counter()
    model = SentenceTransformer(ENCODER)
    load_s = time.perf_counter() - t0

    qvecs = {p: (list(q), model.encode(list(q.values()), normalize_embeddings=True))
             for p, q in queries.items()}

    bundles = sorted(b for b in args.corpus.glob("bundle_*") if (b / "source").is_dir())
    rows, encode_s = [], 0.0
    for b in bundles:
        pack = json.loads((b / "metadata.json").read_text()).get("standard", "vv40")
        gt = json.loads((b / "ground_truth.json").read_text())
        want = {f["factor_type"] for f in gt["expected_factors"]
                if f.get("expected_status") == "assessed"}
        src = "\n".join(p.read_text(errors="ignore")
                        for p in sorted((b / "source").glob("*")))
        cs = chunks(src)
        if not cs:
            continue
        t = time.perf_counter()
        cvec = model.encode(cs, normalize_embeddings=True)
        encode_s += time.perf_counter() - t

        labels, qv = qvecs[pack]
        sims = qv @ cvec.T                    # cosine, both normalised
        rows.append((labels, sims.max(axis=1), want))

    print(f"\nK4 — {ENCODER} on {len(rows)} bundles")
    print(f"  model load {load_s:.1f}s, encode {encode_s:.1f}s total "
          f"({encode_s/max(len(rows),1):.2f}s per bundle)\n")
    print(f"  {'threshold':>9s} {'P':>7s} {'R':>7s} {'F1':>7s}")

    # The control: flag every factor the pack lists, having read nothing.
    ctp = cfp = cfn = 0
    for labels, _sim, want in rows:
        got = set(labels)
        ctp += len(got & want); cfp += len(got - want); cfn += len(want - got)
    cp = ctp / (ctp + cfp) if ctp + cfp else 0.0
    cr = ctp / (ctp + cfn) if ctp + cfn else 0.0
    cf1 = 2 * cp * cr / (cp + cr) if cp + cr else 0.0

    best = None
    for thr in [round(x, 2) for x in np.arange(0.15, 0.66, 0.05)]:
        tp = fp = fn = 0
        for labels, best_sim, want in rows:
            got = {labels[i] for i in range(len(labels)) if best_sim[i] >= thr}
            tp += len(got & want); fp += len(got - want); fn += len(want - got)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        flag = "  <- indistinguishable from the constant" if r > 0.98 else ""
        print(f"  {thr:>9.2f} {p:>7.3f} {r:>7.3f} {f1:>7.3f}{flag}")
        if best is None or f1 > best[3]:
            best = (thr, p, r, f1)

    print(f"  {'CONTROL':>9s} {cp:>7.3f} {cr:>7.3f} {cf1:>7.3f}   "
          f"control_constant_list, reads nothing")

    thr, p, r, f1 = best
    print(f"\n  KILL CRITERION: best F1 must beat control_constant_list")
    print(f"  K4 best   threshold {thr:.2f}  P {p:.3f}  R {r:.3f}  F1 {f1:.3f}")
    print(f"  control                    P {cp:.3f}  R {cr:.3f}  F1 {cf1:.3f}")
    print(f"  delta F1  {f1 - cf1:+.3f}  -> {'PASSES' if f1 > cf1 else 'FAILS'}")
    if r > 0.98:
        print(f"\n  Note: K4's best threshold has recall {r:.3f}, meaning it flags")
        print(f"  essentially every factor. The corpus is {100*ctp/(ctp+cfp):.0f}% assessed, so that")
        print(f"  IS the constant. A high score here measures the base rate, not the encoder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
