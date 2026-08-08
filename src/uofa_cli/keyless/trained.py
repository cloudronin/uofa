"""Trained keyless routes, fitted from shipped labelled data.

TF-IDF over word and character n-grams into logistic regression. No network, no
API key, no language model. `scikit-learn` is an optional dependency: without it
these routes report themselves unavailable and the properties they serve come out
absent, which is the same contract as every other route here.

## What each route is worth, measured

| route | measured | its control |
|---|---|---|
| validation results, recall@5 | **0.438** | 0.125 |
| decision outcome, balanced accuracy | **0.917** | 0.500 |
| decision outcome, rejections caught | **5 of 6** | **0 of 6** |
| decision sentence, top-1 / top-3 | 0.400 / **0.700** | 0.000 |

Both properties were recorded as having "no keyless route" on the strength of one
hand-written pattern matcher each. That was a result about two matchers.

## Why the decision outcome is reported as balanced accuracy

34 of 40 corpus papers accept, so a function that answers "Accepted" every time
scores **0.833 on raw accuracy** and identifies **no rejection at all**. It cannot
be beaten on accuracy and is useless in review, where the rejections are the
cases that matter. Balanced accuracy pins that constant at 0.500 by construction.

## Why the locator cannot be skipped

Accept/reject reads like a document-level property, so classifying it from the
whole document should remove the weak locator. Measured: 0.850 / 0.500 / 0.000 --
identical to the constant, because across 200+ sentences the classifier learns to
answer "Accepted" always. The signal is localised and dilution destroys it.

## Fitting, and why the data ships instead of the model

The estimator is fitted on first use from `data/keyless_training.jsonl.gz` and
cached. A pickled estimator would start faster and break on the next scikit-learn
release; the labelled sentences survive upgrades and can be read by anyone asking
what the classifier was taught.
"""
from __future__ import annotations

import gzip
import json
import pathlib
from dataclasses import dataclass

_DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "keyless_training.jsonl.gz"

# Measured on the seeded corpus. Reported with each emitted value so a reader can
# weigh it; never rounded up, and never a number chosen to look reasonable.
CONFIDENCE = {
    "validation_result": 0.438,
    "decision": 0.400,          # locating it; the outcome given it is 0.917
    "decision_outcome": 0.917,
}


class Unavailable(RuntimeError):
    """scikit-learn or the training data is missing. Never a silent fallback."""


def available() -> tuple[bool, str]:
    """Whether the trained routes can run, and if not, precisely why."""
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return False, ("scikit-learn is not installed; install it with "
                       "`pip install scikit-learn` to enable the trained routes")
    if not _DATA.exists():
        return False, (f"training data missing at {_DATA.name}; regenerate with "
                       f"dev/tools/scripts/dump_keyless_training.py")
    return True, ""


def _rows() -> list[dict]:
    return [json.loads(ln) for ln in
            gzip.decompress(_DATA.read_bytes()).decode().splitlines() if ln]


def _tfidf():
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


def positional(fractions) -> "object":
    """Where a sentence sits, as features a bag of n-grams structurally cannot see.

    The decision sits at median 0.79 through the document and 20 of 34 are in the
    back half. Adding these four columns took the locator from 0.222 to 0.400 --
    it had been asked to find a positional thing with position withheld.
    """
    import numpy as np
    p = np.asarray(list(fractions), dtype=float)
    return np.column_stack([p, (p > 0.75).astype(float),
                            (p > 0.90).astype(float), (p < 0.10).astype(float)])


@dataclass
class Prediction:
    """A value with the evidence and the measured confidence behind it."""
    value: object
    confidence: float
    spans: list[str]


class TrainedRoutes:
    """Fitted once per process. Construct via `load()`."""

    def __init__(self) -> None:
        from scipy.sparse import csr_matrix, hstack

        ok, why = available()
        if not ok:
            raise Unavailable(why)
        rows = _rows()
        texts = [r["t"] for r in rows]

        # -- which sentence states the decision (text + position)
        self._lf, self._lc = _tfidf(), _clf()
        X = hstack([self._lf.fit_transform(texts),
                    csr_matrix(positional(r["p"] for r in rows))]).tocsr()
        self._lc.fit(X, [r["d"] for r in rows])
        self._lcol = list(self._lc.classes_).index(1)

        # -- what the decision was, given that sentence
        dec = [(r["t"], r["o"]) for r in rows if r["d"] and r["o"]]
        self._of, self._oc = _tfidf(), _clf()
        self._oc.fit(self._of.fit_transform([t for t, _ in dec]),
                     [o for _, o in dec])

        # -- which sentences are validation results
        self._rf, self._rc = _tfidf(), _clf()
        self._rc.fit(self._rf.fit_transform(texts), [r["r"] for r in rows])
        self._rcol = list(self._rc.classes_).index(1)
        self.n_trained_on = len(rows)

    def _stack(self, sentences: list[str]):
        from scipy.sparse import csr_matrix, hstack
        n = len(sentences)
        frac = [i / max(n - 1, 1) for i in range(n)]
        return hstack([self._lf.transform(sentences),
                       csr_matrix(positional(frac))]).tocsr()

    def validation_results(self, sentences: list[str], k: int = 5) -> Prediction:
        if not sentences:
            return Prediction(None, 0.0, [])
        P = self._rc.predict_proba(self._rf.transform(sentences))[:, self._rcol]
        top = sorted(range(len(sentences)), key=lambda j: -P[j])[:k]
        return Prediction([sentences[j] for j in top],
                          CONFIDENCE["validation_result"],
                          [sentences[j] for j in top])

    def decision(self, sentences: list[str], top_n: int = 3) -> Prediction:
        """Three candidates, not one.

        Top-1 is 0.400 and top-3 is 0.700. Emitting only the best sentence
        discards a result nearly twice as good for no benefit to the reader, who
        is going to check the candidates either way.
        """
        if not sentences:
            return Prediction(None, 0.0, [])
        P = self._lc.predict_proba(self._stack(sentences))[:, self._lcol]
        top = sorted(range(len(sentences)), key=lambda j: -P[j])[:top_n]
        outcome = self._oc.predict(self._of.transform([sentences[top[0]]]))[0]
        return Prediction({"outcome": outcome,
                           "candidates": [sentences[j] for j in top]},
                          CONFIDENCE["decision"],
                          [sentences[j] for j in top])


_CACHED: TrainedRoutes | None = None


def load() -> TrainedRoutes:
    """Fit once per process, then reuse. Raises `Unavailable` with the reason."""
    global _CACHED
    if _CACHED is None:
        _CACHED = TrainedRoutes()
    return _CACHED
