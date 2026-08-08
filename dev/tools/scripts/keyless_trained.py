#!/usr/bin/env python3
"""Trained keyless routes for the three properties the pattern matchers failed.

Nothing here calls a model or a network. TF-IDF over word and character n-grams
into logistic regression -- `sklearn` and the standard library, no embeddings, no
API key, no LLM. Trained on the 30-paper train split, evaluated on the 10-paper
holdout, split at the bundle level so no paper contributes to both.

## Why this exists

`bindsRequirement`, `hasDecisionRecord` and `hasValidationResult` were recorded as
having "no keyless route" on the strength of one hand-written pattern matcher
each: K3c's regexes, K5's section scan, K9's shape heuristic. That is evidence
about three specific matchers, not about the properties. The strongest keyless
method this project has -- a trained classifier, which is all K6 ever was -- had
been applied to exactly one property of nine.

## The metric was also wrong, and that mattered more

K5 "failed" at 0.033 against a control that scores **0.833 by answering
'Accepted' every time**, because 34 of 40 papers accept. That control cannot be
beaten on accuracy and is worthless in use: it never once identifies a rejection,
which is the only outcome a credibility reviewer needs the tool to catch.

This is the same shape as `control_constant_list` scoring 1.000 on factor
detection -- a null model topping a leaderboard because the measure rewards the
majority answer. So every outcome here is reported as **balanced accuracy and
per-class recall**, with raw accuracy shown alongside to make the gap visible.
A number that a constant function can beat is not measuring extraction.

## Controls, per stage

* decision outcome -- constant "Accepted", and the majority class
* decision location -- first sentence, and a random sentence
* validation results -- `control_first_comparison`, K9's own null
* requirement names -- the frequent-noun-phrase baseline that beat K3c at 0.039

A candidate that does not beat its control is reported as failing, exactly as the
pattern matchers were.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_pipeline_registry import Doc, read  # noqa: E402

SEED = 20260808          # fixed, so a rerun is a rerun and not a new sample


def _tfidf():
    """Word 1-2 grams plus character 3-5 grams. The K6 feature set, unchanged."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import make_union
    return make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                        strip_accents="unicode"),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                        sublinear_tf=True))


def _clf():
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)


def _norm(s: str) -> str:
    return " ".join(s.split()).lower()


# ── labels, read off the gold ─────────────────────────────────────────

def decision_labels(doc: Doc, gt: dict) -> tuple[list[int], str | None]:
    """Sentence indices carrying the decision, and the outcome."""
    d = gt.get("expected_decision") or {}
    src = _norm(d.get("outcome_source") or "")
    if not src:
        return [], d.get("outcome")
    hits = []
    for j, t in enumerate(doc.texts):
        n = _norm(t)
        # The gold sentence may span several extracted ones after unwrapping.
        if n and (n in src or src in n or _overlap(n, src) >= 0.6):
            hits.append(j)
    return hits, d.get("outcome")


def result_labels(doc: Doc, gt: dict) -> list[int]:
    """Sentences carrying a validation result, by the gold's own keywords."""
    hits = set()
    for r in gt.get("expected_validation_results") or []:
        kws = [_norm(k) for k in (r.get("name_keywords") or []) if len(k) > 2]
        if not kws:
            continue
        for j, t in enumerate(doc.texts):
            n = _norm(t)
            if sum(k in n for k in kws) >= max(2, len(kws) - 1):
                hits.add(j)
    return sorted(hits)


def _overlap(a: str, b: str) -> float:
    wa = {w for w in re.findall(r"[a-z]{4,}", a)}
    wb = {w for w in re.findall(r"[a-z]{4,}", b)}
    return len(wa & wb) / len(wb) if wb else 0.0


# ── the corpus, read once ─────────────────────────────────────────────

def load(split: str) -> list[tuple[Doc, dict]]:
    root = _ROOT / "tests" / "fixtures" / "extract_corpus_seeded" / split
    out = []
    for b in sorted(root.glob("bundle_*")):
        if not (b / "ground_truth.json").exists():
            continue
        out.append((read(b), json.loads((b / "ground_truth.json").read_text())))
    return out


# ── 1. hasDecisionRecord ──────────────────────────────────────────────

def decision_record(train, test) -> dict:
    """Locate the decision sentence, then classify the outcome. Both trained."""
    from sklearn.metrics import balanced_accuracy_score

    # -- stage 1: which sentence states the decision
    X, y = [], []
    for doc, gt in train:
        pos, _ = decision_labels(doc, gt)
        pos = set(pos)
        for j, t in enumerate(doc.texts):
            X.append(t)
            y.append(int(j in pos))
    feats, clf = _tfidf(), _clf()
    clf.fit(feats.fit_transform(X), y)
    col = list(clf.classes_).index(1)

    rng = random.Random(SEED)
    found = first = rand = n = 0
    outcomes_true, outcomes_pred, outcomes_const = [], [], []
    for doc, gt in test:
        pos, outcome = decision_labels(doc, gt)
        if not pos:
            continue
        n += 1
        P = clf.predict_proba(feats.transform(doc.texts))[:, col]
        top = max(range(len(doc.texts)), key=lambda j: P[j])
        found += top in pos
        first += 0 in pos
        rand += rng.randrange(len(doc.texts)) in pos
        if outcome:
            outcomes_true.append(outcome)
            outcomes_const.append("Accepted")

    # -- stage 2: the outcome, from the sentence the locator chose
    Xo, yo = [], []
    for doc, gt in train:
        pos, outcome = decision_labels(doc, gt)
        if pos and outcome:
            Xo.append(" ".join(doc.texts[j] for j in pos))
            yo.append(outcome)
    of, oc = _tfidf(), _clf()
    oc.fit(of.fit_transform(Xo), yo)
    for doc, gt in test:
        pos, outcome = decision_labels(doc, gt)
        if not pos or not outcome:
            continue
        P = clf.predict_proba(feats.transform(doc.texts))[:, col]
        top = max(range(len(doc.texts)), key=lambda j: P[j])
        outcomes_pred.append(oc.predict(of.transform([doc.texts[top]]))[0])

    return {
        "n": n,
        "locate_trained": found / max(n, 1),
        "locate_first": first / max(n, 1),
        "locate_random": rand / max(n, 1),
        "outcome_acc": _acc(outcomes_true, outcomes_pred),
        "outcome_bal": (balanced_accuracy_score(outcomes_true, outcomes_pred)
                        if len(set(outcomes_true)) > 1 else float("nan")),
        "const_acc": _acc(outcomes_true, outcomes_const),
        "const_bal": (balanced_accuracy_score(outcomes_true, outcomes_const)
                      if len(set(outcomes_true)) > 1 else float("nan")),
        "reject_recall": _recall(outcomes_true, outcomes_pred, "Not accepted"),
        "reject_recall_const": _recall(outcomes_true, outcomes_const,
                                       "Not accepted"),
        "n_reject": sum(o == "Not accepted" for o in outcomes_true),
    }


def _acc(t, p) -> float:
    return sum(a == b for a, b in zip(t, p)) / max(len(t), 1)


def _recall(t, p, cls) -> float:
    d = sum(a == cls for a in t)
    return sum(a == cls and b == cls for a, b in zip(t, p)) / d if d else float("nan")


# ── 2. hasValidationResult ────────────────────────────────────────────

_COMPARISON = re.compile(
    r"\b(compared|versus|against|within|agree\w*|differ\w*|deviat\w*)\b", re.I)


def validation_results(train, test, k: int = 5) -> dict:
    """Rank sentences by P(is a validation result). Recall@k against K9's null."""
    X, y = [], []
    for doc, gt in train:
        pos = set(result_labels(doc, gt))
        for j, t in enumerate(doc.texts):
            X.append(t)
            y.append(int(j in pos))
    feats, clf = _tfidf(), _clf()
    clf.fit(feats.fit_transform(X), y)
    col = list(clf.classes_).index(1)

    hit = ctrl = tot = 0
    for doc, gt in test:
        pos = set(result_labels(doc, gt))
        if not pos:
            continue
        P = clf.predict_proba(feats.transform(doc.texts))[:, col]
        ranked = sorted(range(len(doc.texts)), key=lambda j: -P[j])
        base = [j for j, t in enumerate(doc.texts) if _COMPARISON.search(t)]
        for g in pos:
            tot += 1
            hit += g in ranked[:k]
            ctrl += g in base[:k]
    return {"n": tot, "recall_trained": hit / max(tot, 1),
            "recall_control": ctrl / max(tot, 1), "k": k}


# ── 3. bindsRequirement ───────────────────────────────────────────────

# Candidate spans: capitalised phrases, standard identifiers, quoted terms.
_CAND = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9\-]{2,}(?:\s+(?:of|for|and|the)?\s*[A-Z][A-Za-z0-9\-]{2,}){0,4})\b"
    r"|\b(?:ISO|ASTM|IEC|ASME|FDA|EN)\s*[A-Z0-9\-]+(?::\d{4})?\b")


def _candidates(doc: Doc, cap: int = 400) -> tuple[list[str], dict[str, int]]:
    """Distinct candidate spans, and how often each occurs.

    Frequency is returned because the control that beat K3c is the *frequent*
    noun phrase, and a control that is actually "the first six in document
    order" would be a weaker opponent wearing the right label.
    """
    counts: dict[str, int] = {}
    order: list[str] = []
    for t in doc.texts:
        for m in _CAND.finditer(t):
            s = " ".join(m.group(0).split())
            if not (3 < len(s) < 80):
                continue
            k = s.lower()
            if k not in counts:
                if len(order) >= cap:
                    continue
                order.append(s)
            counts[k] = counts.get(k, 0) + 1
    return order, counts


def _name_hit(cand: str, gold: list[str]) -> bool:
    """Whole-token containment, not substring.

    K3c reported 0.657 and was corrected to 0.42 because its matcher counted
    fragments -- "balance" matched a twenty-word clause. A raw `in` test repeats
    that: "Section" sits inside "Section 5 requirements" and would score. So a
    candidate matches only if its tokens are a contiguous run of the gold's, or
    the reverse, and only when at least two tokens are shared.
    """
    ct = _norm(cand).split()
    if not ct:
        return False
    for g in gold:
        gt_ = _norm(g).split()
        if not gt_:
            continue
        if ct == gt_:
            return True
        short, long_ = (ct, gt_) if len(ct) <= len(gt_) else (gt_, ct)
        if len(short) < 2:
            continue
        for i in range(len(long_) - len(short) + 1):
            if long_[i:i + len(short)] == short:
                return True
    return False


def requirements(train, test, cap: int = 6) -> dict:
    """Score candidate spans with a trained classifier; keep the top `cap`."""
    X, y = [], []
    for doc, gt in train:
        gold = (gt.get("expected_entity_names") or {}).get("requirements") or []
        if not gold:
            continue
        cands, _ = _candidates(doc)
        for c in cands:
            X.append(c)
            y.append(int(_name_hit(c, gold)))
    if sum(y) < 5:
        return {"n": 0, "note": "too few positive requirement spans to train"}
    feats, clf = _tfidf(), _clf()
    clf.fit(feats.fit_transform(X), y)
    col = list(clf.classes_).index(1)

    hit = freq = tot = 0
    for doc, gt in test:
        gold = (gt.get("expected_entity_names") or {}).get("requirements") or []
        if not gold:
            continue
        cands, counts = _candidates(doc)
        if not cands:
            tot += len(gold)
            continue
        P = clf.predict_proba(feats.transform(cands))[:, col]
        top = [cands[j] for j in sorted(range(len(cands)),
                                        key=lambda j: -P[j])[:cap]]
        # The control that beat K3c: genuinely the most FREQUENT spans.
        freq_top = sorted(cands, key=lambda c: -counts[c.lower()])[:cap]
        for g in gold:
            tot += 1
            hit += any(_name_hit(c, [g]) for c in top)
            freq += any(_name_hit(c, [g]) for c in freq_top)
    return {"n": tot, "recall_trained": hit / max(tot, 1),
            "recall_frequent": freq / max(tot, 1), "cap": cap}


def decision_cv(docs, folds: int = 8) -> dict:
    """The outcome, cross-validated over all 40 papers at the bundle level.

    The holdout carries **one** rejection, so a holdout-only outcome figure moves
    between 0.0 and 1.0 on that single paper and says nothing. Six rejections in
    forty is still thin, and cross-validation is the only way to spend all six on
    evaluation rather than five on training.

    Folds are whole bundles. A sentence from a paper never appears in the fold
    that scores it.
    """
    from sklearn.metrics import balanced_accuracy_score

    rows = []
    for doc, gt in docs:
        pos, outcome = decision_labels(doc, gt)
        if pos and outcome:
            rows.append((" ".join(doc.texts[j] for j in pos), outcome))
    rng = random.Random(SEED)
    idx = list(range(len(rows)))
    rng.shuffle(idx)

    true, pred = [], []
    for f in range(folds):
        test_i = {idx[j] for j in range(f, len(idx), folds)}
        tr = [rows[i] for i in idx if i not in test_i]
        te = [rows[i] for i in sorted(test_i)]
        if not te or len({o for _, o in tr}) < 2:
            continue
        feats, clf = _tfidf(), _clf()
        clf.fit(feats.fit_transform([t for t, _ in tr]), [o for _, o in tr])
        for t, o in te:
            true.append(o)
            pred.append(clf.predict(feats.transform([t]))[0])
    const = ["Accepted"] * len(true)
    return {
        "n": len(true),
        "n_reject": sum(o == "Not accepted" for o in true),
        "acc": _acc(true, pred), "bal": balanced_accuracy_score(true, pred),
        "reject_recall": _recall(true, pred, "Not accepted"),
        "const_acc": _acc(true, const),
        "const_bal": balanced_accuracy_score(true, const),
        "const_reject_recall": _recall(true, const, "Not accepted"),
    }


def decision_cv_document(docs, folds: int = 8) -> dict:
    """The outcome from the WHOLE document, skipping the locator entirely.

    Locating the decision sentence scores 0.222. Classifying the outcome given
    that sentence scores 0.800 balanced. Multiplying them is the honest
    composition and it is poor -- but the composition is only forced if the
    outcome has to be read from one sentence, and it does not. Accept/reject is
    a document-level property: the abstract, the conclusion and the discussion
    all carry it.

    So this asks the question the two-stage design assumed away. If it wins, the
    locator is not a bottleneck to fix, it is a stage to delete.
    """
    from sklearn.metrics import balanced_accuracy_score

    rows = []
    for doc, gt in docs:
        outcome = (gt.get("expected_decision") or {}).get("outcome")
        if outcome:
            rows.append((" ".join(doc.texts), outcome))
    rng = random.Random(SEED)
    idx = list(range(len(rows)))
    rng.shuffle(idx)

    true, pred = [], []
    for f in range(folds):
        test_i = {idx[j] for j in range(f, len(idx), folds)}
        tr = [rows[i] for i in idx if i not in test_i]
        te = [rows[i] for i in sorted(test_i)]
        if not te or len({o for _, o in tr}) < 2:
            continue
        feats, clf = _tfidf(), _clf()
        clf.fit(feats.fit_transform([t for t, _ in tr]), [o for _, o in tr])
        for t, o in te:
            true.append(o)
            pred.append(clf.predict(feats.transform([t]))[0])
    const = ["Accepted"] * len(true)
    return {
        "n": len(true),
        "n_reject": sum(o == "Not accepted" for o in true),
        "acc": _acc(true, pred), "bal": balanced_accuracy_score(true, pred),
        "reject_recall": _recall(true, pred, "Not accepted"),
        "const_acc": _acc(true, const),
        "const_bal": balanced_accuracy_score(true, const),
        "const_reject_recall": _recall(true, const, "Not accepted"),
    }


REAL = [
    ("opensim", "extract_corpus_real/bundle_real_opensim_knee", "seed"),
    ("bologna", "extract_corpus_vv40/bundle_bologna_bcthip", "seed"),
    ("nagaraja", "extract_corpus_vv40/bundle_nagaraja", "seed"),
    ("elemance", "extract_corpus_real/bundle_real_elemance_thoracic", "CLEAN"),
    ("morrison", "extract_corpus_vv40/bundle_morrison", "CLEAN"),
]


def validation_results_real(train, k: int = 5) -> list[tuple]:
    """Train on all 40 seeded papers, test on the five real ones.

    This is the number that decides the others. Seeded-vs-real disagreements are
    resolved in favour of real by standing rule, and three of these five ARE the
    generator's seeds -- their phrasing is echoed throughout the training data.
    Only elemance and morrison are a clean read, so they are marked, and n=2 is
    stated rather than averaged away.
    """
    X, y = [], []
    for doc, gt in train:
        pos = set(result_labels(doc, gt))
        for j, t in enumerate(doc.texts):
            X.append(t)
            y.append(int(j in pos))
    feats, clf = _tfidf(), _clf()
    clf.fit(feats.fit_transform(X), y)
    col = list(clf.classes_).index(1)

    rows = []
    for tag, rel, status in REAL:
        gpath = _ROOT / "docs" / "v1" / f"valresults_{tag}.json"
        bundle = _ROOT / "tests" / "fixtures" / rel
        if not gpath.exists() or not bundle.exists():
            continue
        doc = read(bundle)
        gold = set()
        for r in json.loads(gpath.read_text())["results"]:
            for j, t in enumerate(doc.texts):
                if _norm(r["span"]) in _norm(t):
                    gold.add(j)
                    break
        if not gold:
            rows.append((tag, status, 0, 0, 0))
            continue
        P = clf.predict_proba(feats.transform(doc.texts))[:, col]
        ranked = sorted(range(len(doc.texts)), key=lambda j: -P[j])[:k]
        base = [j for j, t in enumerate(doc.texts) if _COMPARISON.search(t)][:k]
        rows.append((tag, status, len(gold), len(set(ranked) & gold),
                     len(set(base) & gold)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--real", action="store_true",
                    help="also test on the five real papers, the anchor")
    args = ap.parse_args()

    train, test = load("train"), load("holdout")
    print(f"\nTrained keyless routes — {len(train)} train / {len(test)} holdout")
    print("  TF-IDF + logistic regression. No model call, no embeddings, no key.\n")

    d = decision_record(train, test)
    print("── hasDecisionRecord ──────────────────────────────────────")
    print(f"  locating the decision sentence, n={d['n']}")
    print(f"    {'trained':22s}{d['locate_trained']:>8.3f}")
    print(f"    {'control: first sent':22s}{d['locate_first']:>8.3f}")
    print(f"    {'control: random':22s}{d['locate_random']:>8.3f}")
    print(f"\n  the outcome, {d['n_reject']} rejections in the holdout")
    print(f"    {'':22s}{'accuracy':>10s}{'balanced':>10s}{'reject recall':>15s}")
    print(f"    {'trained':22s}{d['outcome_acc']:>10.3f}{d['outcome_bal']:>10.3f}"
          f"{d['reject_recall']:>15.3f}")
    print(f"    {'control: constant':22s}{d['const_acc']:>10.3f}"
          f"{d['const_bal']:>10.3f}{d['reject_recall_const']:>15.3f}")
    print("\n    K5 was scored against the accuracy column, where a constant")
    print("    reaches 0.833 by never identifying a rejection. Balanced accuracy")
    print("    pins that constant at 0.500 by construction.")

    c = decision_cv(train + test)
    print(f"\n  the outcome again, cross-validated over all {c['n']} papers")
    print(f"  ({c['n_reject']} rejections — the holdout alone carries one, which is")
    print("   not a sample, so all forty papers are used with bundle-level folds)")
    print(f"    {'':22s}{'accuracy':>10s}{'balanced':>10s}{'reject recall':>15s}")
    print(f"    {'trained':22s}{c['acc']:>10.3f}{c['bal']:>10.3f}"
          f"{c['reject_recall']:>15.3f}")
    print(f"    {'control: constant':22s}{c['const_acc']:>10.3f}"
          f"{c['const_bal']:>10.3f}{c['const_reject_recall']:>15.3f}")
    print("    Measured on the GOLD sentence, so this is classification given")
    print("    the right input -- not end to end. Composed with a 0.222 locator")
    print("    it would be poor, which is the next table's question.")

    dc = decision_cv_document(train + test)
    print(f"\n  the outcome from the WHOLE DOCUMENT, no locator, n={dc['n']}"
          f" ({dc['n_reject']} rejections)")
    print(f"    {'':22s}{'accuracy':>10s}{'balanced':>10s}{'reject recall':>15s}")
    print(f"    {'trained':22s}{dc['acc']:>10.3f}{dc['bal']:>10.3f}"
          f"{dc['reject_recall']:>15.3f}")
    print(f"    {'control: constant':22s}{dc['const_acc']:>10.3f}"
          f"{dc['const_bal']:>10.3f}{dc['const_reject_recall']:>15.3f}")
    print("    Accept/reject is a document-level property -- abstract,")
    print("    conclusion and discussion all carry it. If this wins, the")
    print("    locator is not a bottleneck to fix but a stage to delete.")

    v = validation_results(train, test, args.k)
    print("\n── hasValidationResult ────────────────────────────────────")
    print(f"  recall@{v['k']} over {v['n']} gold results")
    print(f"    {'trained':22s}{v['recall_trained']:>8.3f}")
    print(f"    {'control: comparison':22s}{v['recall_control']:>8.3f}")
    print("    K9's shape heuristic scored 12/79 against this control's 9/79.")

    r = requirements(train, test)
    print("\n── bindsRequirement ───────────────────────────────────────")
    if not r.get("n"):
        print(f"    {r.get('note')}")
    else:
        print(f"  name recall over {r['n']} gold requirement names, top {r['cap']}")
        print(f"    {'trained':22s}{r['recall_trained']:>8.3f}")
        print(f"    {'control: frequent':22s}{r['recall_frequent']:>8.3f}")
        print("    K3c scored 0.026 here against a naive 0.039.")

    if args.real:
        rows = validation_results_real(train + test, args.k)
        print("\n── the anchor: hasValidationResult on the five REAL papers ─")
        print(f"  trained on all {len(train) + len(test)} seeded papers\n")
        print(f"  {'document':12s}{'':8s}{'gold':>6s}{'trained':>9s}{'control':>9s}")
        cg = ch = cc = 0
        for tag, status, g, h, b in rows:
            print(f"  {tag:12s}{status:8s}{g:>6d}{h:>9d}{b:>9d}")
            if status == "CLEAN":
                cg += g
                ch += h
                cc += b
        tg = sum(r[2] for r in rows)
        print(f"\n  all five        {tg:>6d}{sum(r[3] for r in rows):>9d}"
              f"{sum(r[4] for r in rows):>9d}")
        print(f"  CLEAN only      {cg:>6d}{ch:>9d}{cc:>9d}   <- n=2, the only "
              f"uncontaminated read")
        print("\n  Three of the five ARE the generator's seeds, so their phrasing")
        print("  is echoed throughout the training data. Reporting the five-paper")
        print("  total as the result would be reporting training data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
