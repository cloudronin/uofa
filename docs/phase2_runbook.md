# Phase 2 runbook (May 16–24, 2026)

Single-source operating reference for the live full-battery (M5),
secondary batteries (M6), and final analysis + tag (M7).

> **Anchored to:** Phase 2 Spec v1.8 §3 (package targets), §9 (batch run),
> §10 (analyze), §11 (HTML), §13.1 (acceptance gates), §14 (milestones).

## 0 — Pre-launch checklist (run once, ≥24 h before M5)

```bash
# 1. HEAD on main, working tree clean
git checkout main && git pull --ff-only && git status

# 2. Required env vars (per v1.8 §10.5 / §11.2)
test -n "$ANTHROPIC_API_KEY"     || echo "missing ANTHROPIC_API_KEY"
test -n "$UOFA_HW_SPEC"          || echo "missing UOFA_HW_SPEC"
test -n "$UOFA_EVAL_HOST_ID"     || echo "missing UOFA_EVAL_HOST_ID"

# 3. Cost-preview the planned launch (no LLM calls — exits 0 instantly)
uofa adversarial run \
  --batch specs/confirm_existing/ \
  --batch specs/gap_probe/ \
  --batch specs/negative_controls/ \
  --batch specs/interaction/ \
  --subtlety-override low,medium,high \
  --base-cou-override packs/vv40/examples/morrison/cou1,packs/vv40/examples/morrison/cou2,packs/vv40/examples/nagaraja/cou1 \
  --out /tmp/preview \
  --model claude-sonnet-4-6 \
  --cost-preview

# 4. Mini live smoke ($1 budget — confirms infra is live before the big run)
uofa adversarial run \
  --batch specs/confirm_existing/ \
  --out build/adversarial/phase2/SMOKE/ \
  --model claude-sonnet-4-6 \
  --max-cost 1.00 \
  --strict-circularity
uofa adversarial analyze --in build/adversarial/phase2/SMOKE/ --out build/adversarial/phase2/SMOKE/coverage/
```

If the preview reports anywhere near **4,440 primary packages** and the
mini smoke produces ≥1 COV-HIT row in `outcomes.csv`, infrastructure is
green for M5.

---

## 1 — M5: First full-battery run (May 16–17)

### Launch (Sat morning)

```bash
DATE=2026-05-16
mkdir -p build/adversarial/phase2/$DATE
uofa adversarial run \
  --batch specs/confirm_existing/ \
  --batch specs/gap_probe/ \
  --batch specs/negative_controls/ \
  --batch specs/interaction/ \
  --subtlety-override low,medium,high \
  --base-cou-override packs/vv40/examples/morrison/cou1,packs/vv40/examples/morrison/cou2,packs/vv40/examples/nagaraja/cou1 \
  --out build/adversarial/phase2/$DATE/ \
  --model claude-sonnet-4-6 \
  --max-cost 400.00 \
  --parallel 3 \
  --strict-circularity \
  2>&1 | tee build/adversarial/phase2/$DATE/run.log
```

> **Why these flags**
>
> * `--subtlety-override low,medium,high` and `--base-cou-override …` —
>   per v1.8 §3, achieving the 4,440-primary target requires fanning each
>   spec across the three subtlety levels and (for confirm_existing +
>   negative_control) the three base COUs. gap_probe and interaction
>   specs pin a single base_cou by §7 design and the runner enforces this
>   automatically — the override is silently ignored for those batteries.
> * `--max-cost 400.00` — recalibrated after the Apr 25 mini live smoke
>   showed actual sonnet-4-6 cost ≈ $0.079/package vs §3's $0.04/pkg
>   estimate (≈ 2× higher because output is ~12k tokens not 4k). Full
>   battery at 4,440 packages × $0.079 ≈ $351; the $400 cap leaves
>   ~$49 headroom for variance + retry overhead. If still hit,
>   `--resume` continues from the per-spec manifest. §3's "$330
>   ceiling" is now historical — the live spend target is
>   **~$351 actual**.
> * `--parallel 3` — Anthropic tier 4 (~80 RPM) tolerates this; back off
>   to `--parallel 1` if rate-limit errors appear in `run.log`.
> * `--strict-circularity` — gen model ≠ extract model. Mandatory for §3
>   coverage credibility.

### Monitor (during the run)

```bash
# Tail the run log for warnings + per-spec progress
tail -f build/adversarial/phase2/$DATE/run.log

# Live cost watch
watch -n 30 "jq '.estimatedCostUsd, .totalPackages, .specsSucceeded, .halted' \
  build/adversarial/phase2/$DATE/batch_manifest.json"
```

### Post-batch analyze (Sun morning)

```bash
uofa adversarial analyze \
  --in build/adversarial/phase2/$DATE/ \
  --out build/adversarial/phase2/$DATE/coverage/
```

Outputs (per v1.8 §10):

| File | Purpose |
|---|---|
| `outcomes.csv` | Per-package outcome row (D2 timing columns included) |
| `matrix.csv` | View 1: pattern × scenario hit/miss matrix |
| `summary.csv` | Per-pattern recall/precision/COU disparity |
| `index.html` | View 1/2/3 + perf appendix |
| `rule_timing.csv.FALLBACK_NOTE.txt` | (Jena fallback marker) |
| `batch_manifest.timing_fallback_note` | Same note inside the manifest |

### Triage decision tree (Sun afternoon)

| Symptom | Action |
|---|---|
| GEN-INVALID > 5% on any battery | Inspect `outcomes.csv` for the spec_ids; add a `--max-retries 5` re-run scoped to those |
| COV-CLEAN-WRONG > 5% on negative_control | Likely a too-aggressive Jena rule; flag for Phase 3 catalog audit (§13.3), do not block M5 |
| `halted: true` in batch_manifest | Cost ceiling hit — re-launch with `--resume` and a higher `--max-cost`, or accept partial run |
| COV-MISS > 30% on a confirm_existing pattern | Expected on low subtlety; investigate only if it persists across all 3 subtlety bands |
| COV-HIT-PLUS dominates | Rules are over-firing; record for §13.3 |

Acceptance gates closed at end of M5: **#11, #12, #13, #14, #15, #16, #19**.

---

## 2 — M6: Secondary batteries (May 18–22, evenings)

Each command is independent and incremental; failures of one do not
block the others. Total ~$25 across all three.

### M6.1 — Cross-pack (Mon, ~$3)

```bash
DATE=2026-05-18-crosspack
uofa adversarial run \
  --batch specs/cross_pack/ \
  --out build/adversarial/phase2/$DATE/ \
  --model claude-sonnet-4-6 \
  --strict-circularity
uofa adversarial analyze --in build/adversarial/phase2/$DATE/ --out build/adversarial/phase2/$DATE/coverage/
```

Closes gate **#17**.

### M6.2 — Paraphrasing (Tue–Wed, ~$10)

```bash
DATE=2026-05-19-paraphrasing
uofa adversarial run \
  --batch specs/paraphrasing/ \
  --out build/adversarial/phase2/$DATE/ \
  --model claude-sonnet-4-6 \
  --strict-circularity
uofa adversarial analyze --in build/adversarial/phase2/$DATE/ --out build/adversarial/phase2/$DATE/coverage/
```

Soft gate **#29** (paraphrase robustness).

### M6.3 — Quality benchmark (Thu–Fri, ~$12)

```bash
DATE=2026-05-20-quality
uofa adversarial run \
  --batch specs/quality_benchmark/ \
  --subtlety-override low,high \
  --models claude-sonnet-4-6,claude-opus-4-7,claude-haiku-4-5-20251001 \
  --out build/adversarial/phase2/$DATE/ \
  --strict-circularity
uofa adversarial analyze --in build/adversarial/phase2/$DATE/ --out build/adversarial/phase2/$DATE/coverage/
```

> Math: 8 specs × 2 subtlety × 3 models × 2 variants = **96 packages** ✓
> matches §3. Each output dir is suffixed `_<subtlety>_<model_short>`,
> e.g., `adv-2026-p2-qb-01-w-ar-01_low_sonnet/`.

Closes gate **#18**; soft gates **#30 / #31**.

---

## 3 — M7: Final analysis + tag (May 23–24)

### Saturday — exports

```bash
# One-time: install the export extras (weasyprint pulls cairo/pango)
pip install -e '.[export]'

# Re-run analyze across every batch (cheap; idempotent)
for d in build/adversarial/phase2/2026-05-{16,18,19,20}*; do
  uofa adversarial analyze --in "$d" --out "$d/coverage/"
done

# Figure 3.x PDF (View 2 — per §11.1)
python tools/scripts/export_view_pdf.py \
  --report build/adversarial/phase2/2026-05-16/coverage/index.html \
  --view 2 \
  --output build/adversarial/phase2/figure_3_x.pdf

# View 3 markdown (drop-in for Ch3 abstract)
python tools/scripts/export_view3_markdown.py \
  --summary build/adversarial/phase2/2026-05-16/coverage/summary.csv \
  --output build/adversarial/phase2/view3_precision_recall.md

# Phase 2 → Phase 3 master review packet (per §16 Q6)
python tools/scripts/build_phase2_review_packet.py \
  --batch-dir build/adversarial/phase2/2026-05-16/ \
  --output build/adversarial/phase2/phase2_review_packet.md

# D3 per-spec reviewer packets (per §10.6)
uofa adversarial prep-review \
  --outcomes build/adversarial/phase2/2026-05-16/coverage/outcomes.csv \
  --output build/adversarial/phase2/2026-05-16/review_packets/ \
  --max-cases 50
```

### Sunday — tag

```bash
git tag -a v0.5.5-phase2-complete -m "UofA v0.5.5 — Phase 2 complete"
git push origin v0.5.5-phase2-complete
```

Closes gates **#20, #21**.

---

## Appendix — fan-out math (v1.8 §3)

| Battery | Specs | × subtlety | × base_cou | × variants | Total |
|---|---|---|---|---|---|
| confirm_existing (excl. W-AR-05 legacy) | 22 | 3 | 3 | 20 | **3,960** |
| gap_probe | 22 | 3 | 1 (pinned) | 5 | **330** |
| negative_controls | 10 | 1 | 3 | 2 | **60** |
| interaction | 6 | 3 | 1 (pinned) | 5 | **90** |
| **Primary subtotal** | | | | | **4,440** |
| cross_pack | 10 | 1 | 1 | 1 | **30** |
| paraphrasing | 10 | 1 | 1 | 9 | **90** |
| quality_benchmark | 8 | 2 | 1 | 6 | **96** |
| **Secondary subtotal** | | | | | **216** |
| **GRAND TOTAL** | | | | | **4,656** |

Within rounding tolerance of v1.8 §3's "~4,671" target (15-package gap
absorbed in the §7-vs-§3 gap_probe reconciliation per
`specs/gap_probe/README.md`).

## Appendix — emergency rollback

If the M5 batch corrupts the working tree or `build/` somehow:

```bash
git restore .                    # source tree only
rm -rf build/adversarial/phase2/$DATE/    # destroy this run's artifacts
git checkout v0.5.4                     # last clean tag
```

`build/` is git-ignored; nothing in `build/adversarial/phase2/` is committed.
