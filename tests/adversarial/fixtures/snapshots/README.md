# Adversarial prompt snapshots

Phase 2 prompt-template snapshot fixtures live here. One snapshot per
`(template, subtlety)` pair. Spec reference: Phase 2 Spec v1.7 §12.3
(~105 snapshots when the full battery of 35+ templates ships).

## Snapshot file naming

`snapshot_<module>_<weakener_id>_<subtlety>.txt`

Examples:
- `snapshot_d3_w_ar_05_high.txt`
- `snapshot_epistemic_w_ep_01_low.txt`
- `snapshot_evidence_validity_data_drift_medium.txt`

Each snapshot contains the rendered system + user prompts joined with the
`── SYSTEM ──` / `── USER ──` markers used by the existing
`test_prompt_templates.py::test_snapshot_prompt`.

## Refreshing snapshots

To regenerate snapshots after a prompt-template change, set the env var and
re-run the snapshot tests:

```bash
UOFA_UPDATE_SNAPSHOTS=1 pytest tests/adversarial/test_prompt_templates.py
```

The tests skip when running in update mode. Re-run without the env var to
verify the new snapshots match.

## Phase 1 legacy

The original W-AR-05 snapshots live one level up at
`tests/adversarial/fixtures/snapshot_d3_w_ar_05_*.txt` (Phase 1 convention,
preserved to keep snapshot diffs reviewable). New Phase 2 templates put their
snapshots in this directory.

## Why text snapshots, not pytest-snapshot

The existing convention (read snapshot files via `Path.read_text()`, refresh
via the `UOFA_UPDATE_SNAPSHOTS=1` env var) is functionally equivalent to
`pytest-snapshot` and predates the Phase 2 work. Phase 2 Spec §12.3 explicitly
allows "pytest-snapshot or equivalent"; we keep the equivalent to avoid a new
dev dependency for Phase 2.
