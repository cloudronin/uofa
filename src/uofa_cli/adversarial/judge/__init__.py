"""Phase 3 LLM-as-judge ensemble (spec v1.5).

Three cross-family judges (GPT-5.4, Gemini 3.1 Pro, Llama 3.3 70B via
HuggingFace Inference Endpoints) verdict synthetic credibility-evidence
packages from Phase 2 into one of six classes per spec §1:

    CORRECT-DETECTION, REAL-GAP, GENERATOR-ARTIFACT,
    EXISTING-RULE-MISBEHAVIOR, OUT-OF-SCOPE, UNCERTAIN

Disagreements route to author adjudication (spec §11). Outputs feed pattern
formalization (Stage 5) into the v0.5 catalog.

This package contains the infrastructure for Stages 1–5; calibration set
construction and real LLM runs are driven separately.
"""
