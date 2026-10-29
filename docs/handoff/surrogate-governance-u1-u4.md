# Surrogate governance loop, uofa side: U1 to U4 handoff

Branch: `claude/surrogate-governance-u1-u4`. Built unattended on 2026-10-29.
Nothing pushed to `main`, no pull request opened.

## In one breath

PhysMAP's applicability flags can now land in a UofA package as external,
signed, undispositioned weakeners. The surrogate pack has two new patterns
for them (W-SURR-05, W-SURR-06). `uofa rules --format json` lists them with
their source and their disposition state. A recommendation on them is never
read as a decision. All four acceptance tests pass. Every existing test
still passes. The kill criterion did not fire: no core shape changed.

## What was built

| Piece | Where | What it does |
|---|---|---|
| Vocabulary | `packs/surrogate/shapes/surrogate_shapes.ttl` §A.9 to §A.11 | Observation fields the rules read (`closureId`, `boundVariable`, `validatedMin`/`Max`, `observedValue`; `mechanism`, `dimensionlessGroup`, `calibrationMin`/`Max`, `materiality`, `materialityThreshold`, `materialityThresholdStatus`), two derived markers, `applicabilityFactor`, and the core-namespace terms `uofa:source`, `uofa:recommendedAction`, `uofa:dispositionOf` |
| Shapes | same file, §B end | `ExternalWeakenerAnnotationShape`: an annotation saying `source: external` must be attributed to a `prov:SoftwareAgent` with a name and a version, and carry a justification. `recommendedAction` must be one of the five action classes. Envelope bounds now accept double and integer (see "a pre-existing defect" below) |
| Rules | `packs/surrogate/rules/surrogate_weakener.rules` | `w_surr_05_below`/`_above` and `w_surr_06_above`/`_below`. Pure Jena, numeric builtins. They assert the catalog id and severity on the external node and leave a derived marker as the countable trace |
| Manifest | `packs/surrogate/pack.json` | version 0.2.0; `patternIds` gains W-SURR-05 and W-SURR-06 |
| JSON output | `src/uofa_cli/commands/rules.py` | `--format json` now reads the package for authored annotations and merges them with the engine's deductions. New per-firing keys: `source`, `hits_by_source`, and for authored ones `disposition`, `recommended_actions`, `annotations`. New summary keys: `by_source`, `undispositioned` |
| Examples | `packs/surrogate/examples/physmap/` | NACA entrance (85 points), Lewis 35A gravity on, Lewis 35A gravity off. Sealed with `uofa sign --as issuer` against `keys/physmap-examples.pub` (throwaway key, discarded) |
| Generator | `dev/tools/scripts/build_physmap_examples.py` | Rebuilds the three examples and the six per-rule fixtures from PhysMAP's numbers (embedded in the script, with provenance) |
| Fixtures | `tests/fixtures/weakeners/W-SURR-05/`, `W-SURR-06/` | positive, negative, boundary for each rule |
| Tests | `tests/surrogate/test_external_annotations.py` (40 tests), `tests/surrogate/test_pack_registration.py` (version and new terms) | U1 to U4 acceptance, each shape clause failed once on purpose, verify from a clean directory, tamper fails |
| Docs | `packs/surrogate/README.md`, `packs/surrogate/examples/physmap/README.md`, `CHANGELOG.md` | |

## Acceptance, per requirement

### U1: W-SURR-05, closure outside its validated range. PASS

Command and output:

```
$ uofa rules packs/surrogate/examples/physmap/naca-entrance/uofa-surrogate-naca-entrance.jsonld --pack surrogate --raw
  SUMMARY: 45 weakener(s) detected
  ⚠ W-SURR-05 [High] — 45 hit(s)
$ uofa rules <same file> --pack surrogate --format ntriples | grep -c _closureOutsideValidatedRange
45
```

45 entrance points fire. The 40 fully developed points carry the same
closure, bound and observed value (x/D 10 to 17) on their quiet factor nodes
and get no marker. W-SURR-03 stays silent: x/D is not a surrogate input, and
the Re and Pr region sits inside the training envelope. That is the point of
the pattern.

Test: `TestU1ClosureOutsideValidatedRange` (6 tests).

### U2: W-SURR-06, omitted mechanism active and material. PASS

```
$ uofa rules .../lewis-35a-gravity-on/uofa-surrogate-lewis-35a-gravity-on.jsonld --pack surrogate --raw
  SUMMARY: 3 weakener(s) detected
  ⚠ W-SURR-06 [High] — 3 hit(s)
$ uofa rules .../lewis-35a-gravity-off/uofa-surrogate-lewis-35a-gravity-off.jsonld --pack surrogate --raw
  SUMMARY: 0 weakener(s) detected
```

The three hits are x/D 67.55, 101.69 and 135.84 (materiality 0.111, 0.154,
0.195 at theta 0.10). The six other comparable stations are active (Ri 0.287
outside 0 to 0) but below theta and stay quiet. Gravity off: Ri 0,
materiality 0, nine observations, nothing fires. Every observation records
`materialityThresholdStatus: "illustrative"`.

Test: `TestU2OmittedMechanismMaterial` (7 tests).

### U3: external annotation rule. PASS

Shapes accept the three packages:

```
$ uofa shacl <each example> --pack surrogate --pack disposition
  ✓ SHACL validation  Conforms
```

and refuse each broken form once (no attribution, agent without version,
agent without name, no justification, `source: "External"`,
`recommendedAction: "deploy"`). JSON lists the external firings:

```
$ uofa rules .../uofa-surrogate-naca-entrance.jsonld --pack surrogate --format json
"summary": {"total_firings": 45, "patterns": 1, "by_severity": {"High": 45},
            "by_source": {"external": 45}, "undispositioned": 45}
"firings": [{"patternId": "W-SURR-05", "source": "external",
             "hits_by_source": {"external": 45},
             "disposition": {"undispositioned": 45, "dispositioned": 0},
             "recommended_actions": {"characterize-region": 45},
             "annotations": [{"id": ".../weakener/re55570-xd1", "source": "external",
                              "attributed_to": "https://github.com/cloudronin/physmap",
                              "recommendedAction": "characterize-region",
                              "disposition": "undispositioned", ...}, ...]}]
```

Verify on a second machine, simulated as a fresh temp directory holding
only the package and the public key:

```
$ uofa verify <copy> --pubkey physmap-examples.pub
  ✓ Measurement hash match
  ✓ Measurement signature valid
  decision layer: 1 record(s)
    decision 1: asserted by .../reviewer but carries no signature — incomplete, not invalid.
```

Changing one annotation's `observedValue` in the copy makes verify exit 1.
A sign-then-verify round trip with a fresh key also passes.

Tests: `TestU3ShapesAcceptExternalAnnotations` (9), `TestU3RulesJsonListsExternalFirings` (3), `TestU3SealedPackageVerifiesElsewhere` (3).

### U4: recommendation, not decision. PASS

The NACA package is the fixture: 45 annotations, each with
`recommendedAction: "characterize-region"`, no Disposition anywhere. The
JSON reports all 45 `undispositioned`. Positive control: adding one node
typed `Disposition` with `dispositionOf` naming one annotation moves the
count to 44 and 1, and that annotation reports the Disposition's IRI. A
Disposition that names no annotation dispositions nothing (that is
PhysMAP's current export shape). Setting every recommendation to
`accept-residual-risk` changes nothing about the disposition state.

Tests: `TestU4RecommendationIsNotADisposition` (4), `TestAuthoredAnnotationReader` (4).

## Test run

```
$ pytest tests/surrogate/test_external_annotations.py -q
40 passed
$ pytest tests/ -q
3620 passed, 63 skipped, 2 failed in 27m42s        (first full run, on the three code commits)
```

The two failures were mine and are fixed in the two follow-up commits:

| Test | Why it failed | Fix |
|---|---|---|
| `tests/test_vocab_index.py::test_external_terms_are_glossed_and_attributed` | The new `SoftwareAgentShape` constrains `schema:name`, and the vocabulary index had no gloss for it | Gloss added to `EXTERNAL_GLOSS` in `src/uofa_cli/vocab.py` |
| `tests/test_context_resolution.py::test_hash_is_independent_of_the_toolchain_context` | The test hashes every shipped example over the whole document. The PhysMAP examples are the first shipped packages sealed over the measurement view (`--as issuer`), whose hash excludes the decision layer | The test now checks the measurement-view hash for a decision-carrying package whose whole-document hash does not match. That view never inlines the context, so the toolchain default cannot reach it at all, which is the property the test protects |

Second full run, on the final branch:

```
$ pytest tests/ -q
3622 passed, 63 skipped in 26m29s
```

## Assumptions and design calls (every one)

| # | Call | Why |
|---|---|---|
| 1 | The rule fires on the external node itself and asserts the catalog id and severity onto it. A derived marker (`_closureOutsideValidatedRange`, `_omittedMechanismMaterial`) is the countable firing | Jena's deductions carry only new triples. Re-asserting `patternId` on a node that already has it leaves no trace, so a count by patternId in `--format jsonld` would read 0. Checked empirically before building |
| 2 | The external annotation carries `patternId` and `severity` in the data | The core `WeakenerAnnotationShape` (reached through `hasWeakener`) requires both. PhysMAP's P1 work would write them; the hand-written fixtures write them. If PhysMAP omits them, the rule still supplies both and the JSON reader takes the deduced id |
| 3 | The observation fields are structured properties, not parsed out of the justification text | A Jena rule cannot read prose. The justification stays as the human-readable record; the fields are what the engine checks |
| 4 | W-SURR-05 is two one-sided arms (`validatedMin` and `validatedMax` each optional) | Gnielinski's x/D bound is one-sided (>= 10). A range with only one end declared must still fire |
| 5 | W-SURR-06 requires both "active" (observed group outside the calibration window) and "material" (materiality at or above threshold); at the threshold fires | "Active and material" in the requirement. Boundary fixture pins `ge` |
| 6 | The threshold status is data (`materialityThresholdStatus`), never read by the rule | "Recorded as illustrative when it is" is a recording requirement. The number theta is the rule's input; the label is for the reader |
| 7 | On a quiet point the observation sits on the quiet `CredibilityFactor` (under `uofa-surr:applicabilityFactor`), on a fired point on the annotation | Putting it on both would fire the rule twice per point. Putting it nowhere on quiet points would make the negative control vacuous |
| 8 | `uofa:source`, `uofa:recommendedAction`, `uofa:dispositionOf` are declared in the surrogate pack's shapes file, in the core namespace | The disposition pack does the same for `uofa:Disposition`. No core file changes, no shipped package re-hashes (the context files are inlined before hashing). Candidates for core promotion when you want them there |
| 9 | `dispositionOf` is a new property (Disposition points at the annotation it answers) | Nothing in core links a Disposition to a weakener. PhysMAP's export has a Disposition per point with no edge. Without an edge there is no way to say "this annotation is answered" |
| 10 | `source` values in the JSON view: `engine` (deduced this run), `external` (authored, says so), `package` (authored, says nothing), `mixed` | Three honest states plus the collision case |
| 11 | Examples use the v0.6 context, the one PhysMAP exports | Discrepancy and Disposition terms exist there; the v0.9+ decision-record shapes stay out of jurisdiction (`_apply_jurisdiction`), which is right for a package that is pre-decision |
| 12 | Examples are sealed with `uofa sign --as issuer`; the decision record is asserted and unsigned; `uofa check` reports C1b incomplete | A bare `sign` refuses a package with a decision record, and `--as issuer` needs `decisionProvenance`. The pre-disposition state is honestly incomplete. The measurement view, which holds the annotations, is what is sealed and what verify checks |
| 13 | The examples' decision records are gate records written for the example, not PhysMAP output | ProfileMinimal requires `hasDecisionRecord`. Said so in each package's rationale and in the README |
| 14 | The PhysMAP software agent node lives on the validation result's `wasAttributedTo`; annotations point at its IRI | One node, 45 references. JSON-LD merges by id |
| 15 | PhysMAP's numbers were taken by reading its data files and banked result, not by running PhysMAP | The session's sandbox refused to execute the PhysMAP package (external code). The Gnielinski values come from the published formula, which PhysMAP's `formulas.py` implements line for line; the NACA rows and Lewis stations are copied verbatim. PhysMAP's own reproduction log reports the same 45/40 split |
| 16 | The three Lewis stations Lewis disowns carry no observation | PhysMAP's stress test marks them not comparable. Including 159.33 (materiality 0.221) would make four firings, not the three the acceptance names |
| 17 | `solverTruth` on the NACA and gravity-on Discrepancies is a measurement, not a solver | PhysMAP's export maps measured Nu to `solverTruth`. Said so in the package descriptions |
| 18 | The surrogate pack's envelope bound shapes were changed from `xsd:decimal` to decimal-or-double-or-integer | Pre-existing defect, not mine: the two shipped airfrans packages failed C2 on their own bounds (8 violations each). The new examples hit the same wall. Pack-level change, no core edit |
| 19 | No `factorFocus` added for W-SURR-05/06 | C2 was an investigation, "build nothing". Finding and the exact JSON to add are below |
| 20 | Pack version bumped to 0.2.0 | New patterns; the pack stamps its version independently |
| 21 | Commits are authored under your git identity from this repo's history, with no sign-off trailer | The session's default git identity was the assistant's name, which AGENTS.md §10 forbids in commit metadata. A DCO sign-off is a legal attestation I cannot make for you; add it with `git rebase --signoff` if you want it |
| 22 | `scikit-learn` and `statsmodels` were pip-installed into the session to run the full suite | `tests/airfrans/test_experiment_a.py` imports sklearn and failed on `main` in this environment before any change of mine. Both are declared extras in `pyproject.toml`; nothing was added to the repo |

## A pre-existing defect fixed on the way

`packs/surrogate/examples/airfrans/cou1` and `cou2` did not conform to C2
before this branch (8 `minBound`/`maxBound` datatype violations each) and do
now. No test pinned the failure. If you want the fix separate from the
feature, it is the one hunk in `surrogate_shapes.ttl` under
`EnvelopeDimensionShape` and `PointCoordinateShape`.

## U6 investigation: a package deriving from a prior package's hash

Question: what property do the praxis and the vocab use for a revision link
today, and does `verify` follow it?

| What | Where | Finding |
|---|---|---|
| Vocab | `src/uofa_cli/vocab.py:55` | `prov:wasDerivedFrom` is glossed as "an earlier artifact this one was built from, so a reviewer can walk back to what it came from". `prov:wasRevisionOf` is not in the gloss table |
| Contexts | `spec/context/v0.6.jsonld` and `spec/context/v0.10.jsonld:539` and `:551` | Both `wasDerivedFrom` and `wasRevisionOf` are declared as `@id`-typed terms in every context from v0.6 on. `wasRevisionOf` is declared and never used anywhere in `packs/`, `src/` or `docs/` |
| Core shape | `packs/core/shapes/uofa_shacl.ttl:1013` | ProfileComplete requires `prov:wasDerivedFrom` with `sh:nodeKind sh:IRI`, message "link to prior artifact (e.g., parent UoA/run logs)". No format constraint beyond "is an IRI" |
| Praxis usage | `docs/design.md:26`; `docs/architecture.md:23`; `packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld:30` | "Composable: UofAs form nodes in system-level assurance graphs via `wasDerivedFrom`". In practice the Morrison packages point it at the paper's DOI, and the extract path points it at the source document filenames (`src/uofa_cli/excel_mapper.py:316`). It is a "where did this come from" link, not a "which package did this revise" link |
| Surrogate pack | `packs/surrogate/shapes/surrogate_shapes.ttl` §A.6 (`ParentModelSnapshot`: `parentCOU`, `parentSignatureTimestamp`, `snapshotTimestamp`) | The only existing cross-package link in the pack is a snapshot of the parent's recorded decision, by COU id and timestamp, not by hash. W-SURR-02 reads it |
| Hash well-formedness | `packs/core/shapes/uofa_shacl.ttl:975` and `:1026` | The package's own `uofa:hash` is checked against `^(sha256|sha384|sha512):[a-f0-9]{64,128}$`. The same pattern is what a prior-package-hash property should reuse |
| Does verify follow a link? | `src/uofa_cli/commands/verify.py:509` (`_resolve_anchor`), `:554` (`_locate_anchor_target`) | `verify` follows exactly one link today: a decision record's `decisionAnchor` (`anchorLocator` + `anchorSha256`), for `extracted` decisions. It opens the file, hashes it, compares to the pin, and reports three states: resolved, mismatch, unreachable. Locators are `archive://` and document-relative. Nothing in `verify.py`, `integrity.py`, `sign_roles.py` or `interrogate/signing.py` reads `wasDerivedFrom` or `wasRevisionOf` |

So: there is no revision-link property in use. `wasDerivedFrom` is taken
(source documents and DOIs), `wasRevisionOf` is free and already in the
context. `verify` does not follow either. The anchor machinery is the
precedent to copy: a `priorPackage` block with a locator and a `sha256` pin,
well-formedness by the existing hash regex, and the same three outcomes
(prior present and verifies; present and does not; not reachable here,
reported as unchecked, never as failure). When the prior is present, "it
verifies" means running the prior through the same scope routing
(`integrity.verify_measurement_scope`) against the same anchors.

## C2 investigation: expected factors for W-SURR-05 and W-SURR-06

Question: which `CredibilityFactor` does each map to, does the pack declare
it, and what does the `weakener_focus` enrichment do with them?

| What | Where | Finding |
|---|---|---|
| The enrichment exists | `src/uofa_cli/weakener_focus.py:112` (`enrich_firings`), `:91` (`factor_focus`) | Each firing gets a `factors` list: factor names resolved from `.../factor/<slug>` affected-node IRIs, plus the pattern's declared focus from the pack manifests, filtered to the pack's attributable factor names |
| Where the focus map comes from | `src/uofa_cli/paths.py:278` (`factor_focus_index`) reading `detection` payload `factorFocus` | Core declares three (`packs/core/pack.json:50`): W-AR-05, W-PROV-01, W-ON-02. NASA and model-credibility add their own. **The surrogate pack declares none**, for any of its five patterns |
| The factor universe for the surrogate pack | `src/uofa_cli/weakener_focus.py:46` (`expected_factors`) | There is no surrogate branch. Anything that is not model-credibility or NASA gets `VV40_FACTOR_NAMES` (`src/uofa_cli/excel_constants.py:22`). So the surrogate pack's "expected factors" are today the thirteen V&V 40 factors |
| What happens to a W-SURR-05/06 firing | `src/uofa_cli/report_state.py:303` (`_build_concerns`) | `factors=()`. The concern is still listed, grouped by the node it affects: a Discrepancy node is neither an evaluation node nor the package id, so it files under the documentation group with no factor attached. No factor row's `targeting_weakeners` names it, so a one-row-per-factor rendering shows the concern in the concerns list but on no row. Not dropped, but unattached |
| Does the report even run? | `src/uofa_cli/commands/report.py:823` | `uofa report <naca example> --pack surrogate --deterministic` refuses: "No credibility factors found". The report reads `hasCredibilityFactor` (the standard's factor table) and the PhysMAP-derived packages carry their per-point factors under `uofa-surr:applicabilityFactor` instead. So the factor-row question is upstream of the focus map for these packages today |

Which factor each pattern maps to, in V&V 40 terms (the pack's current
universe): both are **Model form**. W-SURR-05 is a closure used outside the
range its form was validated for; W-SURR-06 is a mechanism absent from the
model form. A case can be made for "Relevance of the validation activities
to the COU" as a second focus for both (the validation did not cover the
regime), which is the focus core gives W-ON-02.

The declaration that would attach them, in `packs/surrogate/pack.json`
under the detection capability's `payload`:

```json
"factorFocus": {
  "W-SURR-05": ["Model form", "Relevance of the validation activities to the COU"],
  "W-SURR-06": ["Model form", "Relevance of the validation activities to the COU"]
}
```

That is enough for `enrich_firings` to attach them under the V&V 40
universe, which is what the pack resolves to today. If the surrogate pack
is to have its own factor universe (PCMM or V&V 20 terms), that is a new
branch in `expected_factors` plus a name list in `excel_constants.py`, and
the focus names must come from that list or they are filtered out.

## What is left

- U5 and U6: not built, by instruction. U6 has the precedent and the shape above.
- `factorFocus` for W-SURR-05/06: one JSON hunk, above, not added.
- PhysMAP P1: its export writing `patternId` W-SURR-05/06, `source: external`, the agent attribution and the structured fields. When it does, the hand-written examples can be replaced by real exports and the build script retired.
- Core promotion of `uofa:source`, `uofa:recommendedAction`, `uofa:dispositionOf`: when wanted. Promoting them means touching `uofa_shacl.ttl` only (not a context file), so no shipped package re-hashes.
- `uofa report` for surrogate packages: it needs `hasCredibilityFactor`; the PhysMAP packages carry per-point factors elsewhere. Decide whether the report should learn `applicabilityFactor` or whether these packages should also carry a standard factor table.
- The committed example key is throwaway. If you want these examples under `keys/research.pub`, re-seal them with `uofa sign --as issuer --key <research key>` and delete `packs/surrogate/examples/physmap/keys/`.

## Score against the declared criteria

End-user value first: an engineer holding a PhysMAP export can now, with
`uofa shacl`, `uofa rules --format json` and `uofa verify`, get a signed
list of undispositioned physics weakeners with the agent that measured them
and the action it recommends, and nothing in the tool will ever mistake that
recommendation for their decision. Defense milestone: W-SURR-05 and
W-SURR-06 are two catalog entries with fixtures, a null control each, and a
cross-pack story (W-SURR-03 silent while W-SURR-05 fires) that a reviewer can
run. The ledger says four of four acceptance tests pass; when the feeling
disagrees, the ledger wins.

## Amendment, 2026-10-29, after the first CI run on PR #142

Two CI failures, both outside the four requirements, both fixed on the branch:

| Check | Cause | Fix |
|---|---|---|
| Deploy site, `build` | `site/scripts/lib/iri-walk.mjs` pins the number of shipped example packages at 13; the branch ships 16 | Pin raised to 16 and `snapshots/iri-pages.json` regenerated (314 identifier pages added under `/surrogate/physmap/`) |
| Validate, `uofa validate --verify` | The command checks shipped seals against the shipped anchors only and recomputes the hash over the whole document, so the issuer-scope seal under the throwaway key read as "hash mismatch" | The three examples now ship unsigned (placeholder hash and signature) like the airfrans examples; the throwaway public key is removed; the seal round trip runs in the tests with a fresh key. Sealing under the research anchor is one `uofa sign --as issuer` per file, when wanted |

Pre-existing and not touched: the site's own unit tests (`npm test` in `site/`) fail 3 of 23 on `main` as well (stale pinned totals), and `main`'s committed `iri-pages.json` already differs from what its generator writes. Neither is run by CI.
