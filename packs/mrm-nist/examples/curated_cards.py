"""Curated card encodings for the MRM-NIST demo (S0, the 3-card run).

Source-grounded, human-curated factor statuses for three real open-model cards,
derived by reading each card's live README (fetched via huggingface_hub). This is
the "curate" half of the locked extraction choice: the factor statuses below are a
human reading of the real card text, committed with provenance — the same
discipline as the Morrison reviewer fixtures (tests/space/fixtures/_generate.py).

Per-card statuses partition the 17 MRM-NIST factors into:
  - assessed     : the card contains explicit content for the factor
  - not_assessed : the card is silent (a genuine documentation gap; fires W-EP-04
                   at the disclosed MRL 3 assumption)
  - scoped_out   : organizational/lifecycle factor a static card is not expected to
                   carry (out-of-scope-at-card-level), flipped to assessed only when
                   a card actually documents it (e.g. OLMo versioning/ownership)

The MRL 3 posture is a disclosed assumption (a card declares no risk tier); the
reviewer render surfaces it in the "What this model was used for" section.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from uofa_cli.excel_constants import MRM_NIST_FACTOR_NAMES

# Disclosed assessment posture, shared by every card — single source of truth in
# space.pipeline so the live path and this curated run cannot drift.
from space.pipeline import (
    MRM_NIST_ASSUMED_MRL as ASSUMED_MRL,
    MRM_NIST_RISK_ASSUMPTION as RISK_ASSUMPTION,
)


@dataclass(frozen=True)
class Card:
    model_id: str
    key: str                        # short stable slug for example dir / gallery selection
    role: str                       # one-line demo role
    cou_name: str
    cou_description: str
    assessed: tuple[str, ...]
    not_assessed: tuple[str, ...]
    # scoped_out defaults to the standard out-of-scope-at-card set minus any the
    # card documents (which move to `assessed`); overridable per card.
    scoped_out: tuple[str, ...] = ()
    validation_results: tuple[dict, ...] = ()
    entities: tuple[dict, ...] = ()
    has_uq: str = "No"
    provenance: str = ""


# ── OLMo-2-1124-13B-Instruct — frontier, well-documented ─────────────────────
OLMO = Card(
    model_id="allenai/OLMo-2-1124-13B-Instruct",
    key="olmo2-13b-instruct",
    role="Frontier, well-documented",
    cou_name="Open instruction-following language model for research and educational use",
    cou_description=(
        "OLMo-2-1124-13B-Instruct, an open post-trained language model from the "
        "Allen Institute for AI (Ai2), intended for research and educational use."
    ),
    assessed=(
        "Ownership and accountability",   # Ai2 named owner, project page, responsible-use contact
        "Intended use",                   # "intended for research and educational use"
        "License and usage terms",        # Apache 2.0 + Responsible Use Guidelines + Gemma Terms
        "Task and domain context",        # instruction-tuned LM; Dolma/Tulu 3; MATH/GSM8K/IFEval
        "Deployment setting",             # HF loading, chat template, system prompt, no in-loop filter
        "Known limitations",              # "Bias, Risks, and Limitations": limited safety training
        "Evaluation metrics",             # full 11-benchmark performance table with values
        "Evaluation methodology",         # OLMES eval code repo + named benchmark suite
        "Robustness and safety testing",  # Safety benchmark column reported
        "Test and evaluation data",       # benchmarks + training datasets named
        "Versioning and update policy",   # 1/3/2025 retraining note + staged model table + -preview
    ),
    not_assessed=(
        "Out-of-scope use",               # only a generic responsible-use link, no explicit boundary
        "Affected populations",           # English stated, but no demographic/representativeness analysis
        "Bias and fairness analysis",     # a Safety score is reported, but no bias/fairness analysis
    ),
    scoped_out=(
        "Mitigations and safeguards",
        "Residual risk",
        "Monitoring and feedback",
    ),
    validation_results=(
        {
            "name": "OLMES multi-benchmark suite",
            "evidence_type": "ValidationResult",
            "description": "Average and per-benchmark scores (AlpacaEval, BBH, DROP, "
                           "GSM8k, IFEval, MATH, MMLU, Safety, PopQA, TruthfulQA).",
            # comparedAgainst is an @id-typed property (expects an IRI), so the
            # comparator is given as the eval-suite/baseline handle the card links
            # to; a free-text value would be dropped at JSON-LD expansion and make
            # W-AR-05 fire spuriously even though the card DOES report comparisons.
            "compares_to": "https://github.com/allenai/olmes",
            "has_uq": "No",                                               # point estimates, no CIs
            "metric_value": "Average 62.0",
            "pass_fail": "Inconclusive",
        },
    ),
    entities=(
        {"entity_type": "Model", "name": "OLMo-2-1124-13B-Instruct",
         "uri": "https://huggingface.co/allenai/OLMo-2-1124-13B-Instruct",
         "description": "Post-trained 13B open language model."},
        {"entity_type": "Dataset", "name": "Tülu 3 SFT mixture (OLMo variant)",
         "description": "Supervised finetuning dataset."},
    ),
    provenance="Fetched live README via huggingface_hub (text-generation card, ~1.2k words).",
)

# ── cardiffnlp/twitter-roberta-base-sentiment — popular, holey ───────────────
CARDIFF = Card(
    model_id="cardiffnlp/twitter-roberta-base-sentiment",
    key="twitter-roberta-sentiment",
    role="Popular, holey (the contrast case)",
    cou_name="Sentiment analysis of English tweets (negative / neutral / positive)",
    cou_description=(
        "roBERTa-base trained on ~58M tweets and finetuned on the TweetEval "
        "sentiment benchmark for English-tweet sentiment classification."
    ),
    assessed=(
        "Intended use",                   # sentiment analysis, English tweets
        "Task and domain context",        # sentiment, tweets, TweetEval, ~58M tweets
        "Deployment setting",             # runnable load/inference code example
        "Test and evaluation data",       # tweet_eval / TweetEval named
    ),
    not_assessed=(
        "License and usage terms",        # NO license anywhere in the card (popular model!)
        "Out-of-scope use",               # none stated
        "Known limitations",              # none stated (only "see a newer model")
        "Affected populations",           # English tweets, no demographic analysis
        "Evaluation metrics",             # metrics by reference to the paper; only an example inference
        "Evaluation methodology",         # cites benchmark/paper, no protocol in card
        "Bias and fairness analysis",     # none
        "Robustness and safety testing",  # none
    ),
    scoped_out=(
        "Ownership and accountability",
        "Mitigations and safeguards",
        "Residual risk",
        "Monitoring and feedback",
        "Versioning and update policy",
    ),
    validation_results=(
        {
            "name": "TweetEval sentiment (reference paper)",
            "evidence_type": "ValidationResult",
            "description": "Sentiment performance is reported in the TweetEval paper; "
                           "the card itself shows only a single example inference.",
            # compares_to omitted -> no comparator in the card (fires W-AR-05)
            # has_uq omitted      -> no uncertainty quantification (fires W-AL-01)
            "pass_fail": "Inconclusive",
        },
    ),
    entities=(
        {"entity_type": "Model", "name": "twitter-roberta-base-sentiment",
         "uri": "https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment",
         "description": "roBERTa-base sentiment classifier."},
        {"entity_type": "Dataset", "name": "TweetEval (tweet_eval)",
         "description": "Tweet classification benchmark."},
    ),
    provenance="Fetched live README via huggingface_hub (~390 words). No license declared in card.",
)

# ── DeepChem/ChemBERTa-77M-MTR — thin biomedical bridge (no card) ────────────
# The repo ships NO README.md at all (confirmed via the HF API: siblings are only
# config/tokenizer/weights). The published chirality-tokenizer limitation is in the
# ChemBERTa literature but absent from the card because the card is absent. The
# assessable-documentation set is empty: every in-scope factor is not-assessed.
CHEMBERTA = Card(
    model_id="DeepChem/ChemBERTa-77M-MTR",
    key="chemberta-77m-mtr",
    role="Thin biomedical bridge (ships no model card)",
    cou_name="Not stated (no model card published)",
    cou_description="",  # reviewer shows "did not state a context of use" — honest
    assessed=(),
    not_assessed=(
        "Intended use",
        "License and usage terms",
        "Out-of-scope use",
        "Task and domain context",
        "Deployment setting",
        "Known limitations",
        "Affected populations",
        "Evaluation metrics",
        "Evaluation methodology",
        "Bias and fairness analysis",
        "Robustness and safety testing",
        "Test and evaluation data",
    ),
    scoped_out=(
        "Ownership and accountability",
        "Mitigations and safeguards",
        "Residual risk",
        "Monitoring and feedback",
        "Versioning and update policy",
    ),
    validation_results=(),  # no card -> no reported evaluation
    entities=(
        {"entity_type": "Model", "name": "ChemBERTa-77M-MTR",
         "uri": "https://huggingface.co/DeepChem/ChemBERTa-77M-MTR",
         "description": "RoBERTa-style chemical SMILES model (multi-task regression)."},
    ),
    provenance="No README.md in the repo (HF API, sha 66b895cab8...); the published "
               "chirality-tokenizer limitation is absent because the card is absent.",
)

CARDS: tuple[Card, ...] = (OLMO, CARDIFF, CHEMBERTA)


def _validate_partition(card: Card) -> None:
    """Every one of the 17 factors must appear exactly once across the three sets."""
    seen = list(card.assessed) + list(card.not_assessed) + list(card.scoped_out)
    expected = set(MRM_NIST_FACTOR_NAMES)
    dupes = [n for n in seen if seen.count(n) > 1]
    missing = expected - set(seen)
    extra = set(seen) - expected
    if dupes or missing or extra:
        raise ValueError(
            f"{card.model_id}: bad factor partition — "
            f"dupes={sorted(set(dupes))} missing={sorted(missing)} extra={sorted(extra)}"
        )


def build_import_dict(card: Card) -> dict:
    """Build the intermediate dict that excel_mapper.map_to_jsonld consumes.

    Mirrors space.pipeline.result_to_import_dict: profile forced to Complete so all
    factors map and the engine can see unassessed gaps; a synthetic Not-accepted
    decision (never surfaced) because the mapper requires one. Presence-only — no
    required/achieved levels are emitted.
    """
    _validate_partition(card)

    status_of = {}
    for n in card.assessed:
        status_of[n] = "assessed"
    for n in card.not_assessed:
        status_of[n] = "not-assessed"
    for n in card.scoped_out:
        status_of[n] = "scoped-out"

    factors = [
        {"factor_type": name, "status": status_of[name]}
        for name in MRM_NIST_FACTOR_NAMES
    ]

    summary = {
        "project_name": card.model_id,
        "cou_name": card.cou_name,
        "cou_description": card.cou_description or None,
        "profile": "Complete",
        # deviceClass is an FDA medical-device concept the core Complete shape
        # constrains to Class I/II/III; omit it for the model-card unit rather
        # than emit a bogus "N/A" that trips SHACL. (None -> mapper skips it.)
        "device_class": None,
        "model_risk_level": ASSUMED_MRL,
        "assurance_level": "Low",
        "standards_reference": "NIST-AI-RMF-1.0",
        # Honest packaging provenance so the Complete profile's wasDerivedFrom /
        # wasAttributedTo are satisfied: the assessment is derived from the public
        # HF model repo and attributed to the UofA MRM-NIST profile. This leaves
        # only the genuine card gaps (no bound requirement; empty card -> no
        # dataset/validation) as structural findings, which W-SI-02 also flags.
        "source_document": f"https://huggingface.co/{card.model_id}",
        "assessor_name": "UofA MRM-NIST assessment",
        "has_uq": card.has_uq,
    }

    return {
        "summary": summary,
        "entities": list(card.entities),
        "validation_results": list(card.validation_results),
        "factors": factors,
        "decision": {"outcome": "Not accepted",
                     "rationale": "Documentation-completeness assessment only."},
    }
