# Adversarial Generation (research instrument)

`uofa adversarial generate` synthesizes JSON-LD evidence packages that target specific weakener patterns, then validates them against SHACL. The tool is an **instrument** for empirically characterizing rule coverage — it feeds the methodology section of Chapter 3 and the September 2026 JVVUQ paper. Synthetic packages are flagged and refused by `uofa sign` and `uofa verify` so they can never be mistaken for real evidence.

```bash
pip install -e '.[extract]'                          # one-time: adds litellm + pyyaml
export ANTHROPIC_API_KEY=sk-ant-...                  # generation defaults to claude-opus-4-7

# Generate 5 synthetic packages targeting W-AR-05 (comparator absence / mismatch)
uofa adversarial generate \
  --spec dev/specs/confirm_existing/w_ar_05.yaml \
  --out build/adversarial/w_ar_05/

# Dry-run: render the prompt without calling the LLM
uofa adversarial generate --spec dev/specs/confirm_existing/w_ar_05.yaml --out /tmp/dry --dry-run

# Run the full Phase 1 acceptance script
bash tests/adversarial/test_acceptance.sh
```

Every generated package carries an `adversarialProvenance` block (spec id, prompt template version, generation model, timestamp, target weakener) and a `provenanceBlockHash` that `uofa verify` recomputes to detect tampering with the synthetic flag. `--strict-circularity` refuses to run when the generation model matches the configured extract model; `--allow-circular-model` is an explicit opt-in for debugging runs.

Spec file format and the full design are documented in `UofA_Adversarial_Gen_Spec_v1.1.md`. Phase 1 ships the W-AR-05 (D3 undercutting) template; the registry in `src/uofa_cli/adversarial/prompts/__init__.py` scales to additional weakener patterns by adding keys.
