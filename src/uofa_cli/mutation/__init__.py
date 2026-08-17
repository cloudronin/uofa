"""Deterministic mutation arm (Phase 2.5a).

Produces single-fault mutants of UofA packages with manifests derived from the
graph diff rather than from operator intent, so the ground truth is true by
construction rather than by assertion.
"""

from uofa_cli.mutation.operators import REGISTRY, coverage, by_id, for_pattern

__all__ = ["REGISTRY", "coverage", "by_id", "for_pattern"]
