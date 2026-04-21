# Pre-Tester QA Corpus (v2)

Deterministic test fixtures for CLI robustness and SHACL boundary
verification. Built by `corpus/build.py` from reusable helpers in
`tests/fixtures/import/generator.py`; outputs are `.gitignore`d to keep the
repo lean.

## Build

```bash
pip install -e '.[corpus]'   # one-time: reportlab, msoffcrypto-tool, openpyxl
make corpus                  # writes 18 files under corpus/{edge-cases,import-tests}
```

## Test

```bash
pytest tests/test_corpus_edge_cases.py -v   # 10 format-robustness cases
pytest tests/test_corpus_import.py -v       # 8 SHACL-boundary cases
```

## Layout

```
corpus/
├── edge-cases/           # 10 files — format quirks; extract must not crash
└── import-tests/         # 8 xlsx  — deterministic SHACL pass/fail outcomes
```

See `UofA_Pre_Tester_QA_Corpus_v2.md` (external spec) for the full acceptance
matrix. The expected-outcomes table also lives in
`tests/test_corpus_import.py` as a parametrized SPECS list.
