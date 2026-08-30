# C-2 — signed-export

Read against `docs/donetest/C_SERIES_PREREGISTRATION.md`, frozen at C-1's launch.

    slug           c2-ef7791
    seat           claude-opus-5   gated, confirmed from the child's own init
    claim tier     surface-audited; touch-void enforced
    surface        11 browser tools, no MCP strays; tool surface held: browser only
    messages       799
    journal        1113 events -> run-C-2.jsonl
    ENDING         signed-export

## Pins — a trial of the frozen condition

    ok Prompt hash / Source sha256 / Backend / Extractor model   all same

`dev/stranger/c_pins.py --run 2`, exit 0.

## Verification — fresh environment, package's own anchors

    ✓ Measurement hash match
    ✓ Measurement signature valid
    ✓ decision 1: reviewer signature valid

## Composition

    dispositions   10 not-recoverable, 9 source-absent
    ambiguity      4 entries
    extraction     34 cells against 19 expected factors
    cover          "still unsigned" 0; judgment overclaim 0

Extraction within the observed envelope (T-9: 29, C-1: 56, T-8: 58). No meter
anomaly.

**A third disposal split, on one frozen document.** T-8 read 18/1, T-9 8/11,
C-1 17/2, C-2 10/9 — same source, same prompt, same build. Recorded, not
interpreted: §6 forbids analysis beyond the fixed readings, and the batch report
after C-10 is where the composition table belongs.

**Running count: 2 of 2 signed-export.**
