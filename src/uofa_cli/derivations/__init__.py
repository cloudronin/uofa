"""Derivation pre-pass orchestration for the UofA pipeline.

Per UofA_Derivation_PrePass_Spec_v0_1.md. Adds a SPARQL CONSTRUCT pre-pass
stage between C2 SHACL and C3 Jena rules. Packs that don't declare a
`derivations` section in pack.json see zero behavior change (no-op).

Modules:
  config   — pack-config + CLI flag resolver (mirrors uofa_cli.oos.config)
  runner   — subprocess wrapper invoking the Java DerivationEngine
  snapshot — stable JSON serializer for derivation results
"""
