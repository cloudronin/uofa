# INV-4 — Existing package-diff tooling: extend vs build

Status: **CLOSED — requirements confirmed by parent spec v2.0**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A8 (only if elected), B1

---

# ADDENDUM — re-investigated against parent spec v2.0

v2.0 §A8 now states the comparison requirement and its thresholds, and they match
the gap analysis in §2 exactly:

> Comparison run mechanically via `uofa diff-packages`: **structural agreement plus
> per-weakener disposition agreement, per label class.** Pre-committed threshold:
> **JUDGMENT disposition raw agreement ≥0.85**; below, report and root-cause via the
> ambiguity logs. **MECHANICAL agreement below ~1.0 indicates a protocol or tool
> defect**, itself reportable.

Three confirmations and one addition:

1. **The three gaps in §2 are exactly the spec's three requirements** —
   per-weakener (not per-pattern-id) comparison, factor-disposition comparison, and
   per-label-class agreement. No re-scoping needed; the 4-6h estimate holds.
2. **The MECHANICAL ≈1.0 expectation makes the §2 keying caveat load-bearing.** If
   `W-SI-02`'s two distinct findings collapse under a `patternId`-only key, a
   perfectly consistent re-encode reports MECHANICAL agreement below 1.0 and the
   spec's own rule reads that as *a tool defect* — which it would be, but in the
   comparator rather than the encoder. Key on annotation identity, as §2 says.
3. **Reuse `judge.adjudication.compute_agreement` for the raw-agreement figure**;
   the ≥0.85 threshold is on raw agreement, not κ, so the simpler of the two
   existing computations applies.
4. **New dependency:** the threshold text routes JUDGMENT disagreements to
   root-causing *"via the ambiguity logs"*, which do not exist until A7 ships
   (INV-2). A8 therefore depends on A7, not just on the washout clock.

One consequence of INV-1's corrected partition worth flagging here: **the JUDGMENT
class contains 6 patterns and the MECHANICAL class 15**, not the 10/13 split the
provisional table implied. A8's ≥0.85 JUDGMENT threshold is therefore measured over
a smaller set of dispositions than the spec's drafting assumed, so its effective n
will be small. Worth stating in A8's design that the JUDGMENT agreement figure
carries a wide interval, per A5's Wilson-CI rule.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Recommendation

**Extend, don't build.** `uofa diff` already exists and already does the hard part
(two-package comparison, rule-engine invocation, typed structured result,
divergence explanation). What A8 needs is a second comparison layer on top of it.

Estimate: **4-6h** for `uofa diff-packages` as an extension of the existing
`commands/diff.py`, versus ~2 days from scratch.

**The escalation criterion did not trigger** — the signing path does canonicalize —
but *what* it canonicalizes is narrower than "canonicalization" implies, and that
constrains the design. See §3.

## 1. What exists today

`uofa diff <a.jsonld> <b.jsonld>` — [src/uofa_cli/commands/diff.py](src/uofa_cli/commands/diff.py),
470 lines. Registered in the CLI dispatcher at
[cli.py:68,82](src/uofa_cli/cli.py).

| Capability | Present? | Citation |
|---|---|---|
| Accepts two packages | yes | `commands/diff.py` |
| Runs the Jena engine on each and compares **firings** | yes | `diff.py:377-390`; parses via the canonical `_FIRING_RE` owned by [rules.py:35-41](src/uofa_cli/commands/rules.py) |
| Static fallback when Jena is absent (compares recorded `hasWeakener`) | yes | `DiffResult.used_static_fallback`, `diff.py:44-48` |
| Typed structured result for programmatic reuse | yes | `DiffResult` with `weakeners_a/b`, `only_a`, `only_b`, `all_pids`, `cou_identity_a/b` — `diff.py:29-60` |
| Divergence explanation (per-pattern prose) | yes | `explain.explain_divergence`, `diff.py:313-330` |
| JSON output mode | yes | `diff.py:446-455` |
| **Per-weakener disposition comparison** | **no** | comparison key is `patternId` only (`pids_a - pids_b`, `diff.py:377-378`) |
| **Per-label-class agreement stats (κ / raw agreement)** | **no** | nothing in the module computes agreement |
| **Factor-level or entity-level comparison** | **no** | `cou_identity_*` carries only header fields (cou_name, device_class, model_risk_level, outcome, assurance_level) |

Adjacent machinery found by searching for comparison under its own terms rather
than by name:

- **Agreement statistics already exist**, in the judge subsystem:
  `compute_agreement`, `confusion_matrix`, `AgreementStats`, `VERDICT_CLASSES` in
  [src/uofa_cli/adversarial/judge/adjudication.py](src/uofa_cli/adversarial/judge/adjudication.py),
  imported by `judge/runner.py:24-34`. These compute pairwise/ensemble κ over
  categorical verdicts. **A8's per-label-class agreement is the same shape of
  computation** over a different label set. Reuse this, do not re-derive κ.
- **Golden-file comparison** of whole rendered reports:
  `tests/fixtures/report_goldens/morrison_vv40.{json,text,markdown}` +
  `tests/test_report_goldens.py`. Implies a comparator, but at the rendering layer,
  not the disposition layer.
- **`uofa decision`** — "review a SIP comparison (read-only) or sign an engineer
  decision" ([commands/decision.py:28](src/uofa_cli/commands/decision.py)). A
  comparison surface exists here for SIP evidence bundles; worth 20 minutes of the
  implementer's time to check whether its comparison shape is reusable, though it
  is scoped to a different artifact.
- **`packs/disposition/`** — a v0.6 schema pack validating typed `Disposition`
  actions with a controlled `actionClass` vocabulary
  ([packs/disposition/pack.json](packs/disposition/pack.json)). **This is the
  vocabulary A8's disposition comparison should key on**, if disposition-completion
  packages are in scope for the re-encode. It is opt-in and never required of a v0.5
  package, so a v0.5-only re-encode would not exercise it.

## 2. What A8 needs on top

A8 compares two encodings *of the same source* by the same author, so the
interesting divergence is not "which patterns fired" (that is the visible
consequence) but "which dispositions differ" (the cause).

| Gap | Work |
|---|---|
| Compare **per-weakener**, not per-pattern-id | Change the comparison key from `patternId` to `(patternId, affectedNode-role, severity)`. Note `W-SI-02` emits two distinct findings under one id ([rules:337,350](packs/core/rules/uofa_weakener.rules)) — keying on `patternId` alone silently merges them. |
| Compare **credibility-factor dispositions** | New: align `hasCredibilityFactor` entries across the two packages by `factorType` (the pack's canonical factor names, already available via `weakener_focus.py:46`), then diff `factorStatus`, `requiredLevel`, `achievedLevel`, `acceptanceCriteria` presence. This is the substance of a self-consistency study. |
| **Per-label-class agreement stats** | Consumes INV-1's partition. Report MECHANICAL agreement (expect ≈1.0; anything less is a tool or protocol defect and is itself the finding) and JUDGMENT agreement separately. Reuse `judge/adjudication.compute_agreement`. |
| Entity alignment across two independent encodings | **The real design problem.** Two independent encodings mint different IRIs for the same factor. Alignment must be by `factorType` + pack taxonomy, not by IRI. Same for validation results (align by name/metric). |

## 3. Canonicalization in the signing path (spec step 3)

**Escalation criterion not met — canonicalization exists.** But read it carefully
before reusing it:

`canonicalize_and_hash(doc)` — [src/uofa_cli/integrity.py:130-142](src/uofa_cli/integrity.py):

```python
canonical = json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
```

The module labels this honestly. `INTEGRITY_FIELDS` are stripped before hashing
(`integrity.py:18`), and the comment at `integrity.py:20-23` states that this is
canonicalization of *the JSON serialization*, **not** RDF/JSON-LD canonicalization,
and that RFC 8785 JCS / RDFC is "a separate, later capability." The
`canonicalizationAlg` field was relabelled from the aspirational `RDFC-1.0` to the
truthful `json-sortkeys/v1` in commit `316daf6f` (2026-05-31) — an unusually good
piece of self-correction that A4 should cite.

**Consequence for `diff-packages`:** you cannot use hash equality, or any
byte-level comparison built on this, as the comparator. Sorted-key JSON is stable
against key ordering but **not** against IRI minting, array ordering, blank-node
labelling, or `@context` compaction differences — all of which differ between two
independent encodings by construction. The comparator must be **entity-level**, as
§2 describes. The signing path gives you a stable *identity* for each package
(useful for pinning which two packages were compared, and for the A8 record), not a
usable *comparison*.

## 4. Sketch

```
uofa diff-packages A.jsonld B.jsonld --pack vv40 \
    [--label-classes docs/investigations/INV-1-findings.md|catalog] \
    [--format json|table]
```

1. Reuse `commands.diff.run_structured` for the firing-level layer (free).
2. New: align credibility factors by `factorType`; emit a per-factor row
   (`status_a`, `status_b`, `req_a/b`, `ach_a/b`, agree?).
3. New: per-weakener alignment keyed as §2 specifies.
4. New: agreement block, **scoped by INV-1 label class**, via
   `judge.adjudication.compute_agreement`.
5. Record both package hashes from `integrity.canonicalize_and_hash` in the output
   header, so the comparison is pinned to exact bytes.

Steps 1 and 4 are reuse. Steps 2, 3, 5 are the new code, and none of it is
inference.

## Coverage statement

**Searched.** `src/uofa_cli/commands/` full listing (24 modules); `diff.py` header
+ grep for `only_a`, `only_b`, `patternId`, `disposition`, `factor`; `cli.py`
command registry. Derived search terms from the question's own definition
(graph isomorphism / canonicalization / normalization / whole-package assertion /
two-package subcommand): greps for `canonical`, `urdna`, `normalize`, `jcs` across
`integrity.py` and `package_policy.py`; `compute_agreement`, `confusion_matrix`,
`kappa` across `src/`. Read `integrity.py:130-142` and its comments. Listed
`packs/disposition/` and read its manifest. Checked `tests/fixtures/report_goldens/`
and `commands/decision.py` HELP line.

**NOT searched / not verified.**
- `uofa decision`'s SIP comparison logic was identified but **not read**. If its
  comparison is entity-level it may cut the estimate; if it is bundle-level it is
  irrelevant. 20 minutes to settle, not done here.
- No test was written or run against `uofa diff`; the capability table is from
  source reading, not execution.
- `src/weakener-engine/` (Java) was not read — the diff path shells the engine via
  `uofa rules` and parses its summary lines, so engine internals do not bear on the
  extend-vs-build call.
- The estimate assumes A8 compares v0.5 packages. If disposition-completion
  (`ProfileDisposition`, `packs/disposition/`) is in scope, add ~2h for the
  `actionClass` comparison layer.
