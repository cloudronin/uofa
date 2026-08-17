# INV-2 — Feasibility of `uofa protocol-check`

Status: **CLOSED — recommendation strengthened against parent spec v2.0**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A7, B1

---

# ADDENDUM — re-investigated against parent spec v2.0

The original finding flagged that it was working from A7's five-line element list
in v1.1 rather than a field structure, and that §3-§4 would need recomputing if a
specified A7 existed. v2.0 §A7 supplies it. Recomputed below.

**The recommendation does not change — build with A7, and the estimate holds at
3-5h — but it lands better than predicted.** v2.0's A7 is already written
checkable-first in three of its five clauses, apparently independently. Two of the
four gap items shrink to SHACL, and the §4 rewrite table is mostly already applied.

## v2.0's A7, clause by clause, against what SHACL can carry

| A7 clause (v2.0) | Checkable? | Where |
|---|---|---|
| **1. Source-evidence intake rules; citation-anchoring — every encoded assertion cites page/section/table** | **Yes, and this is new.** "Every encoded assertion carries a citation anchor" is a pure cardinality constraint over assertion nodes | SHACL `sh:minCount 1` on a `citationAnchor` path, once the property exists |
| **2. Ordered extraction passes: per pass, which entities instantiate and which fields are mandatory** | **Mostly yes.** v2.0 binds mandatory fields **to a pass**, which is stronger than a flat list: it makes the per-pass field set a closed enumeration | SHACL per-pass shapes; ordering itself still needs G2 |
| **3. Disposition procedure: testable Accepted / Not Accepted / Not Applicable criteria referencing source text** | **Partly** | the criterion-reference binding is SHACL; "references source text" needs G4 |
| **4. Mandatory ambiguity log: entry per underdetermined field, recording ambiguity, resolution, rule applied** | **Structure yes, coverage no** | G1 unchanged — see below |
| **5. Stopping rule: complete when all mandatory fields are populated or logged source-absent** | **Yes — fully mechanical as written** | This is the single most consequential improvement; see below |

## Clause 5 is already the checkable-first rewrite

The original §4 predicted the tempting wording *"encoding stops when no further
evidence can be extracted"* (unfalsifiable) and proposed replacing it with a closed
`stoppingCondition` vocabulary. **v2.0 did something better.** Its stopping rule —
*"complete when all mandatory fields are populated or logged source-absent"* — is
not an attestation at all; it is a **derived predicate over the package**:

```
for every mandatory field f (from clause 2's per-pass field sets):
    f is populated  OR  f has a source-absent log entry
```

That is a pure completeness check with a two-branch disjunction. It needs **no new
vocabulary, no attestation, and no author honesty**, and it composes directly with
the existing profile-completeness machinery (§2(a) of the original finding). G3
drops out of the gap list entirely.

It also removes the failure mode the original finding worried about most: a
stopping rule that a package can claim to satisfy without evidence.

## Clause 4 is the one real residue, and it is now well-posed

Clause 4 requires an ambiguity-log entry **per underdetermined field**. The
original G1 analysis holds exactly, and v2.0 makes it *more* tractable than
feared, because clause 2 supplies the field universe: a field is checkable as
underdetermined-and-unlogged only if the mandatory-field set is enumerated, and
clause 2 enumerates it per pass.

Remaining gap: SHACL can require that an `AmbiguityLogEntry` is well-formed (has
`ambiguity`, `resolution`, `ruleApplied` — v2.0 names all three, so the shape is
writable today). It **cannot** check that one exists for each field that needed one,
because "needed one" is a judgement. The check is therefore:

- **mechanical half:** every mandatory field is populated **or** carries a log entry
  (this is clause 5, already free)
- **judgement half:** was a *populated* field nonetheless underdetermined? Not
  checkable, and should not be attempted.

**Recommendation for A7's text:** state that boundary explicitly in the protocol —
`protocol-check` verifies the log's structure and its coverage of *unpopulated*
fields, and the completeness of the log over *populated-but-ambiguous* fields is an
author obligation the tool cannot enforce. Saying so in A7 is stronger than
implying enforcement the checker does not provide, and it is exactly the kind of
sentence A9's disclosure wants to be able to point at.

## Revised gap list and estimate

| # | Check | Status vs original | Est. |
|---|---|---|---|
| G1 | Ambiguity-log coverage | **Halved.** The unpopulated-field half is clause 5's check; only the log's own well-formedness shape remains, which is SHACL | 30m |
| G2 | Pass-order attestation | Unchanged — ordering is still not a graph property. v2.0 clause 2 makes the pass set closed, so this is a list-equality check | 45m |
| G3 | Stopping-rule attestation | **Eliminated** — clause 5 is derived, not attested | 0 |
| G4 | Disposition-criterion binding resolves to a protocol clause | Unchanged; still needs the clause-id scheme recommended in the original §4 | 45m |
| **New** | Citation-anchoring (clause 1): every encoded assertion cites page/section/table | **New requirement in v2.0**; pure SHACL cardinality once the property is added to the context | 30m + a context/schema addition |

**Residue ≈ 2.5h** (was 2.75h), plus ~1-2h for the SHACL alias and CLI surface.
**Total still 3-5h.** The composition shifted toward SHACL, which is the better
direction: more of the check survives in the shapes, where it also runs under
`uofa check` for free.

## One structural recommendation, restated because v2.0 does not yet include it

The original finding recommended a **protocol version and clause-id scheme**
(`A7-§3.2`) plus `encodedUnderProtocol` on the package. v2.0's A7 names the artifact
`Encoding_Protocol_v0_1.md` and says it will be *"published and tagged"*, which
supplies the version. What is still missing is the **clause-id scheme** and the
package-side field. Without both, G4 has nothing to resolve against, and
`protocol-check` cannot report *which* protocol version a package claims. **Add
both while drafting; the cost is a naming convention.**

## Coverage statement (addendum)

**Searched.** v2.0 §A7 (all five numbered clauses), §B1, §D5 clause 3 (the
author-encoded escort that depends on A7), §D8's "Encoding Protocol and
Reproducibility" row, §A9 clause 1 (which cites A7 as the mitigation). Re-checked
against the validation-stack inventory established in the original finding; no new
code reading was required, because the recomputation is a delta on A7's text, not
on the machinery.

**NOT verified.** `Encoding_Protocol_v0_1.md` still does not exist — confirmed
again by `find -iname "*encoding*protocol*"`. Every estimate here remains
contingent on A7's clauses surviving drafting in the form v2.0 states them. The
1,280-line shapes file remains grepped rather than read end to end.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Recommendation

**Build with A7, not before, and expect it to be mostly thin.** Estimate
**3-5h** total, of which ~1-2h is a SHACL alias over machinery that already exists
and ~2-3h is the residue SHACL cannot express.

The single most valuable output of this investigation is not the estimate. It is
the list in §4: **the A7 requirements that are mechanically uncheckable as
normally worded**, and the rewording that makes each checkable. A7 should be
drafted against that list, which is exactly what the item asked for
("flag any A7 requirement that is mechanically uncheckable so A7 can be
written checkable-first").

## 1. Validation-stack inventory

| Layer | Where | CLI entrypoint | Typed API |
|---|---|---|---|
| **C1 integrity** (hash + ed25519) | [src/uofa_cli/integrity.py](src/uofa_cli/integrity.py) | `uofa verify` | `integrity.verify_file` |
| **C2 SHACL** | pack shapes, resolved across active packs by `paths.all_shacl_schemas(active=…)` ([commands/shacl.py:48-60](src/uofa_cli/commands/shacl.py)) | `uofa shacl` | `commands.shacl.run_structured → ShaclResult` |
| **C3 rules** (the 23 weakeners) | `packs/core/rules/uofa_weakener.rules` | `uofa rules` | `commands.rules.run_structured → RulesResult` |
| **Full pipeline** | composes all three | `uofa check` | `commands.check.run_structured → CheckResult` |
| **Completeness (report layer)** | [src/uofa_cli/report_state.py:64-95, 331-413](src/uofa_cli/report_state.py) | `uofa report` | `report_state.build_report_state` |

Core shapes: [packs/core/shapes/uofa_shacl.ttl](packs/core/shapes/uofa_shacl.ttl),
1,280 lines. Per-pack shapes in `packs/{vv40,nasa-7009b,iso42001,surrogate,disposition}/shapes/`.

## 2. Is there already a field-list-driven check "in another guise"? Yes — two.

Searching under the concept rather than the name turned up two mechanisms that do
what protocol-check would do:

**(a) Profile-conditional mandatory fields, in SHACL.** The shapes implement a
two-tier profile system with `sh:xone`-style dispatch on the declared profile:

- `conformsToProfile` is constrained to `sh:in ( ProfileMinimal ProfileComplete
  ProfileDisposition )` ([uofa_shacl.ttl:724-727](packs/core/shapes/uofa_shacl.ttl))
- separate node shapes apply the Minimal body and the Complete body **only when the
  corresponding profile is declared** ([uofa_shacl.ttl:793-796, 835-838](packs/core/shapes/uofa_shacl.ttl))
- the field lists are documented in [docs/profiles.md](docs/profiles.md): Minimal =
  7 properties, Complete = Minimal + 13 more + the per-factor `CredibilityFactor`
  shape

**This is exactly the shape of a "protocol mandatory-field list" check, already
built and already wired to the CLI.** If A7's mandatory fields are package fields,
protocol-check is a thin alias: a fourth profile (`ProfileProtocol`) plus a
subcommand that runs `shacl.run_structured` with a protocol-scoped shape graph and
prints violations in protocol vocabulary.

**(b) A completeness computation, at the report layer.** `report_state` derives
`completeness_pct = evidenced / expected` against the pack's canonical factor
universe ([weakener_focus.py:46-74](src/uofa_cli/weakener_focus.py),
[report_state.py:379-399](src/uofa_cli/report_state.py)). This is *factor* coverage,
not *field* presence — a different denominator. Useful to reuse for A7's
per-factor completeness requirement; not a substitute for the field check.

**Correction to the parent spec, minor.** The item's escalation criterion is *"the
completeness-profile machinery is materially different from what C2 describes."*
It is not materially different, but C2 in the parent spec is described as
*"manuscript rendering of the Inspector"* (workstream C), whereas the C2 referred
to throughout the codebase is *the SHACL leg of the C1/C2/C3 pipeline*. Two
different C2s. Not a defect — but A7 and B1 text should disambiguate, or a reader
will look for completeness profiles in the web UI.

## 3. Delta: what SHACL can and cannot carry

**A7's stated content** (parent spec §A7): intake rules, ordered extraction
passes, testable disposition criteria, ambiguity log, stopping rule.

| A7 element | SHACL-expressible? | Why |
|---|---|---|
| Mandatory-field completeness per profile | **Yes** — alias | §2(a) |
| Value-domain constraints (status enums, level ranges 1-5 / 0-4) | **Yes** | already present, e.g. `factorStatus` enums are enforced in the shapes and mirrored in the Space UI's `STATUS_CHOICES` ([space/app.py:27](space/app.py)) |
| Per-factor structure (`factorType`, `factorStandard`, `assessmentPhase`) | **Yes** | `CredibilityFactor` shape, [docs/profiles.md](docs/profiles.md) |
| **Ambiguity-log presence per underdetermined field** | **No** | Requires *conditional* logic over a judgement — "this field was underdetermined" is not a graph property. SHACL can check that an ambiguity-log node exists and is well-formed; it cannot check that one exists *for each field that needed one*. |
| **Ordered extraction passes** | **No** | Ordering is a property of the process, not of the artifact. Checkable only if the package records a pass-provenance trail. |
| **Testable disposition criteria** | **Partly** | SHACL can require that a disposition carries a criterion reference. It cannot check the criterion was *applied*. |
| **Stopping rule** | **No** | A process property. Checkable only via a recorded terminal state. |
| Intake rules (was this document in scope?) | **No** | Judgement about a source, not about the package. |

### The gap list, with per-item estimates

| # | Check | Why not SHACL | Implementation | Est. |
|---|---|---|---|---|
| G1 | Ambiguity-log coverage: every field the protocol marks underdetermined has a log entry | conditional over a per-field judgement | Python pass over the package + a protocol-declared underdetermined-field list; assert 1:1 | 1h |
| G2 | Pass-order attestation: the recorded extraction passes match the protocol's declared order | ordering is not a graph property | compare a `provenanceChain`-style ordered list against the protocol's list | 45m |
| G3 | Stopping-rule attestation: the package records which stopping condition terminated encoding, from a closed vocabulary | needs a vocabulary A7 must define | `sh:in` **once A7 names the vocabulary** — then it *is* SHACL, ~15m | 15m |
| G4 | Disposition-criterion binding: every non-trivial disposition cites a criterion id from the protocol | SHACL can require the property; it cannot check the id resolves to a protocol clause | resolve ids against the published protocol's clause list | 45m |

**Total residue ≈ 2.75h**, plus ~1-2h for the SHACL alias and CLI surface.

## 4. A7 requirements that are mechanically uncheckable as normally worded

This is the item's real deliverable. Each row is a sentence A7 will want to write,
why it cannot be checked, and the rewrite that makes it checkable. **Writing A7
against the right-hand column costs nothing extra and makes `protocol-check`
almost entirely SHACL.**

| Tempting A7 wording | Uncheckable because | Checkable-first rewrite |
|---|---|---|
| "The encoder logs every ambiguity encountered." | "encountered" is unobservable | "Every field in the protocol's **underdetermined set** (an enumerated list published with the protocol) carries either a value or an `AmbiguityLogEntry`." → G1 becomes a mechanical 1:1 check |
| "Extraction proceeds in the order: intake → structure → factors → dispositions." | ordering is not in the artifact | "The package records `encodingPass[]` as an ordered list of pass identifiers from a closed vocabulary." → G2, or SHACL with `sh:in` |
| "Encoding stops when no further evidence can be extracted." | unfalsifiable | "The package records `stoppingCondition` from {`evidence-exhausted`, `scope-boundary`, `time-box`, `source-unavailable`}." → pure SHACL |
| "Dispositions are made against testable criteria." | "testable" is a property of the criterion, not the package | "Every `CredibilityFactor` with `factorStatus != not-assessed` carries `acceptanceCriteria` **and** a `criterionRef` resolving to a clause id in the published protocol." → SHACL + G4 |
| "The encoder does not infer beyond the source." | not mechanically checkable at all | Do not attempt. Route to the groundedness measurement that already exists (`docs/metrics-spec-r6-u8.md` §groundedness triple, README's 0.988 figure) and cite it as the empirical proxy. State plainly in A7 that this is measured, not enforced. |
| "Intake admits only documents meeting the inclusion rule." | property of the corpus, not the package | Make it an A10 corpus-level assertion checked once per corpus, not per package. |

**One structural recommendation:** give the protocol a **version and a clause-id
scheme** from day one (`A7-§3.2`), and have packages record
`encodedUnderProtocol: "uofa-encoding-protocol/0.1"`. Without it, G4 has nothing to
resolve against and `protocol-check` cannot say *which* protocol version a package
claims to satisfy — which is the first thing a reviewer asks.

## 5. Sketch

```bash
uofa protocol-check <package.jsonld> [--protocol-version 0.1]
```

1. Read `encodedUnderProtocol`; fail loudly if absent (this alone catches the
   common case).
2. Run `shacl.run_structured` with the protocol shape graph added to the active
   pack shapes — reuses `paths.all_shacl_schemas` and the existing friendly-message
   renderer (`shacl_friendly.print_results`).
3. Run G1/G2/G4 as Python checks.
4. Print one section per protocol element; exit non-zero on any failure.

Steps 1-2 are the alias; step 3 is the residue.

## 6. Verdict on the item's own question

> *"If the protocol's mandatory fields are (or can be) expressed as a SHACL
> profile, protocol-check is a thin alias and the estimate is hours."*

They can be, and it is — **for the field-completeness half**. The estimate is
hours, not days: **3-5h**, contingent on A7 being written checkable-first.

**Build with A7.** Building now would mean guessing the field list; building later
means A7 ships without a checker and the "documented procedure" that must-have 5
points to has no enforcement. Drafting them together, with §4's table in hand, is
the cheapest path and it improves A7 itself.

## Coverage statement

**Searched.** `src/uofa_cli/commands/` (24 modules), reading `shacl.py:41-61`,
`check.py:1-45`, `verify.py:1-40`. `packs/core/shapes/uofa_shacl.ttl` grepped for
`ProfileMinimal`, `ProfileComplete`, `ProfileDisposition`, `sh:NodeShape`,
`conformsToProfile`, `sh:in`, `activityType`. `docs/profiles.md` read in full for
the mandatory-field lists. `src/uofa_cli/report_state.py` and `weakener_focus.py`
grepped for `completeness`. `packs/` census including `packs/disposition/pack.json`.
Repo-wide grep for `protocol-check`, `verify-labels`, `diff-packages` — **none
exists**. Repo-wide search for an encoding protocol document
(`find -iname "*encoding*protocol*"`, grep for `Encoding Protocol` /
`Encoding_Protocol` across `docs/`) — **no such document exists**, confirming the
item's premise that A7 is unwritten.

**Search terms derived from the question's own definition** (mandatory-field
completeness): `mandatory`, `required`, `minCount`, `sh:in`, `Profile*`,
`completeness`, `conformsTo` — rather than searching only for "protocol".

**NOT searched / not verified.**
- **No parent spec v2.0 exists on disk.** The item says to "investigate against the
  A7 section's field structure in the parent spec." The available parent is
  `UofA_Unified_Repair_Spec_v1_1.md` (2026-08-12), whose A7 section is five lines
  and lists elements without a field structure. **This investigation therefore
  works from A7's element list, not from a field structure, and §4 is written as
  guidance for drafting rather than as a delta against a specified list.** If a v2.0
  with an A7 field table exists, §3's delta must be recomputed against it. See the
  cross-cutting note in SUMMARY.md.
- The 1,280-line shapes file was grepped, not read end to end; the profile-dispatch
  mechanism was confirmed at the cited lines but the full constraint inventory was
  not enumerated. A protocol-check implementer should read it fully first.
- `pyshacl` behaviour and per-pack shape merge semantics were not tested.
- No estimate was validated against an actual implementation attempt.
