# Inject and detect: a defect you choose, caught by the rules

This is the committee's own description, run end to end: a valid evidence package
goes in, a known flaw is injected, the flaw is caught, and a manifest confirms it
was the flaw that was injected and not something else.

Every command below is deterministic. Run it twice and you get byte-identical
mutants — no model, no API key, no network.

## Setup

```bash
pip install uofa
```

That is the whole install for this walkthrough. The wheel bundles the rule-engine
JAR **and** an OpenJDK 17 JRE, so there is no separate Java or Maven step.

Two honest exceptions:

- **Intel macOS** does not get the bundled JRE and needs a system Java 17.
- Running from a **source checkout** rather than an installed wheel also needs a
  system Java 17, since the bundled JRE only activates inside the wheel.

Nothing here needs an LLM. The `uofa extract` and `uofa adversarial` paths do; this
one does not.

## 1. Start from a valid package

```bash
uofa verify packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
uofa check --pack vv40 packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
```

`verify` confirms the content hash and the ed25519 signature. `check` runs the full
stack: SHACL profile, integrity, rule engine. The package passes all three.

It also reports 18 weakeners, which is not a contradiction — this is a real
published case study, and those are findings about the *evidence*, not about the
package's validity. They are the baseline the injection is measured against.

## 2. Remove uncertainty — the committee's first named flaw type

```bash
uofa inject --pattern W-AL-01 \
  --package packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld \
  --out /tmp/demo
```

One validation result loses its uncertainty quantification. Nothing else changes.
The manifest records the site, the removed triple, and a SHA-256 of the graph diff.

```bash
uofa rules /tmp/demo/uofa-morrison-cou2__MUT-DEL-01__site0.jsonld
uofa inject verify --manifest /tmp/demo/manifest.json
```

```
⚠ W-AL-01 [High] — 1 hit(s)          ← the detector, blind
✓ MUT-DEL-01  W-AL-01  DETECTED  (delta +1)   ← the manifest, confirming
```

`uofa rules` is the detection step, and it is the **production** detector — the
same command anyone runs on a real package. It has no `--manifest` flag and no
notion that an injection happened; it reports 20 findings on this mutant and
cannot tell you which one was planted. That is the point. A detector that could
read the answer key would make the demonstration circular.

`uofa inject verify` is what knows. It compares against the pre-injection
baseline, so `W-AL-01` going 0 → 1 is the claim, not `W-AL-01` merely being
present. Exit code 0; had the rule missed it, 1.

## 3. Remove the signature — the second named flaw type

```bash
uofa inject --pattern W-SI-01 \
  --package packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld \
  --out /tmp/demo
uofa rules /tmp/demo/uofa-morrison-cou2__MUT-DEL-05__site0.jsonld
uofa inject verify --manifest /tmp/demo/manifest.json
```

The signature is stripped *after* signing, so this models tamper rather than an
unsigned draft: the content hash still covers the original bytes.

This one is caught **twice** — the SHACL profile rejects it (signature is a
mandatory field) and the rule engine fires W-SI-01. Run `uofa check` on the mutant
and both layers report it. That is redundant coverage, not a handoff; the pipeline
does not stop at the first failure.

## 4. Change a version number — the third named flaw type, and why it needs a caveat

```bash
uofa inject --pattern W-AR-04 \
  --package packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld \
  --out /tmp/demo
```

**This one is not a plain injection, and the walkthrough says so rather than
letting the output imply otherwise.**

W-AR-04 fires when a validation result was produced against a model version that
differs from the package's current version. No case-study encoding in this
repository carries `currentModelVersion`, or a
result → activity → configuration chain to hang a version on. So the operator has
to **build that structure first**, then introduce the mismatch.

Two edits, one fault. The manifest records both, and the comparison baseline is the
enriched package *before* the mismatch — not the original — so the added structure
is never counted as part of the injected defect. The tool asserts the enriched
package still passes SHACL before injecting, because a defect injected into an
invalid package tests the schema rather than the rules.

**That the structure has to be built is itself a finding**, and a more interesting
one than the detection: three rules in the catalog read structures that no encoding
this project produces has ever instantiated. See
`studies/phase2_5a/REPORT.md`.

## 5. Run the whole battery

```bash
uofa inject --all \
  --package packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld \
  --out /tmp/battery
uofa inject verify --manifest /tmp/battery/manifest.json
```

```
✓ 22/22 injections detected
```

Scoring is **delta against each mutant's own baseline**, on two conditions: the
declared flaw appears, and no pre-existing finding disappears. The second matters —
a mutation that quietly suppresses an existing finding would score as a clean pass
under a simpler check, and one operator's first design did exactly that before this
check caught it.

Suppressions are reported rather than auto-failed. Every one measured so far has
been a correct consequence: delete a structure, and a rule that needed it can no
longer bind.

## What this does and does not show

**Shows:** the ground truth is the manifest, not anyone's judgement. The flaw is
chosen, the site is recorded from the graph diff rather than from the operator's
intent, and the check is reproducible by anyone with the package.

**Does not show:** that these are the defects real evidence carries. The battery
tests whether the rules detect defects that are *expressible* in a package. Which
defects real submissions actually contain is a separate question, and
`studies/phase2_5a/REPORT.md` reports what this arm found about it — including
three rules that had never fired at any catalog version, and one that fires only
against a class the schema does not declare.
