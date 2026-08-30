# C-1 — signed-export

Read against `docs/donetest/C_SERIES_PREREGISTRATION.md`, frozen at this launch.

    slug           c1-dc03eb
    seat           claude-opus-5   gated, confirmed from the child's own init
    claim tier     surface-audited -- 7 bundled skills / 4 built-in agent types
                   present and irremovable; touch-void enforced
    surface        11 browser tools, no MCP strays; tool surface held: browser only
    messages       1033
    journal        1420 events -> run-C-1.jsonl
    ENDING         signed-export
    downloads      credenza-your-evidence-signed.zip (34,930 bytes)

## Pins — a trial of the frozen condition

    ok Prompt hash        same
    ok Source sha256      same
    ok Backend            same
    ok Extractor model    same

`dev/stranger/c_pins.py --run 1`, exit 0. Read from the run's own signed package.

## Verification — fresh environment, package's own anchors

    ✓ Measurement hash match
    ✓ Measurement signature valid
    ✓ decision 1: reviewer signature valid
      issuer and decision scopes signed by different keys — independent attestation

`uofa==0.16.0` in a clean venv, `--pubkey keys/uofa-issuer.pub
--decision-pubkey keys/demo-reviewer.pub` from inside the zip.

## Composition

    dispositions   17 not-recoverable, 2 source-absent
    required levels  no required level was judged; this package does not claim otherwise
    ambiguity      4 entries
    extraction     56 cells against 19 expected factors
    cover          "still unsigned" 0 occurrences; judgment overclaim 0 occurrences

Extraction within the observed envelope (T-8: 58 cells, T-9: 29). No meter
anomaly; the batch proceeds.

## Seat findings

None recorded here beyond the fixed readings. Findings fork to the queue per
§4.5 and do not modify the batch, the prompt, or the build.

**Running count: 1 of 1 signed-export.**
