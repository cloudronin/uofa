"""AirfRANS Corpus Harness (Experiment A).

Drives the existing UofA surrogate pack + SIP over a real (or, for CI, a
synthetic AirfRANS-like) corpus to produce a *measured* result: the gap in true
surrogate error (Cl/Cd vs RANS ground truth) between cases where the envelope
weakener W-SURR-03 fired and cases where it did not.

Boundaries (load-bearing — see UofA_AirfRANS_Corpus_Harness_MiniSpec.md):
  - NO LLM anywhere in this package. The arbiter is RANS ground truth.
  - NO verdict / threshold / pass-fail. The harness reports an error-gap
    measurement; the engineer decides.
  - The flag is the rule: "W-SURR-03 fired" is read from the real `uofa check`
    structured output (the derivation-aware path), never recomputed here.
  - Reuse, don't reimplement: it drives the pack + SIP, authoring no weakeners
    and no measurement path of its own.

Not a praxis artifact (product/conference track).
"""

from __future__ import annotations
