# Addendum v0.2: report card output and uofa.net publication

**Applies to:** model-credibility-pack-spec.md + addendum v0.1
**Status:** ACTIVE — same gating as the parent spec, whose POST-OCTOBER gate was
lifted on 2026-08-10. Defines the report card as a first-class output artifact of
the `model-credibility` pack, its publication on uofa.net, and the path from
author-run cards to third-party submission. Sections continue v0.1 numbering.

**Revision note (2026-08-10):** A9.1's mechanism is corrected — source pinning
cannot extend `fieldProvenance` — and A9's investigation item is resolved. See the
marked patches.

---

## A6. The report card is a render of the bundle, never a separate authoring

**Core rule:** a report card is a deterministic render of a signed assessment
bundle. There is no card-authoring step, no hand-edited card content, no card
field that does not trace to a bundle field. `card = f(bundle)` and `f` is
versioned.

- New CLI surface: `uofa report owner/model --pack model-credibility --card`
  emits `card.html` + `card.json` alongside the bundle. `card.json` is the
  render-input extract (everything the template consumes); `card.html` is the
  static render. Both derived, neither signed separately — the bundle
  signature covers them transitively because they are re-derivable.
- Renderer is versioned (`cardTemplate v1.x`) and stamped on the card footer
  next to pack version. Same bundle + same template version = byte-identical
  card. This makes "the card says X" always reducible to "the bundle contains
  X."
- Anyone holding the bundle can regenerate the card offline. The published
  card is a convenience, not the artifact of record.

### Card structure (settled by mockup review, recorded)

| Section | Content | Source |
|---|---|---|
| Header | model id, developer, HF revision hash, assessed date, pack + template version, raidex `backend_version` | bundle metadata |
| Provenance line | extraction backend, provenance-stamping statement | bundle metadata |
| Verdict tiles | [1] n/17 factors present; [2] weakener count by severity. **No composite score, ever.** | Group A / Group B outputs |
| Package-level strip | **ADDED 2026-08-10.** A compact strip between the verdict tiles and section [1], labeled as package-level (whole-assessment) findings. | concerns whose affected node is the UnitOfAssurance |
| [1] Factor grid | 17 presence dots, factor name on hover | Group A |
| [2] Findings | severity-sorted weakener rows, one-line finding, prevalence note, scope sentence | Group B + cohort stats |
| [3] Furnished evidence | RAI badge (score, coverage, constituent version, "furnished composite — assessed as evidence under [2]" framing), reported-vs-furnished table, dimension radar | raidex adapter |
| Verify footer | bundle download, `uofa verify` one-liner, signature fingerprint | bundle |

### Data-driven constraints (impl-plan requirements)

1. Radar dimensions and normalization read from the raidex dataset schema at
   render time. No hardcoded axis list; raidex adding a dimension changes
   cards on re-render, not on code change. **Note (2026-08-10):** the published
   records carry **eight** `composite.dimension_scores` keys (`safety`,
   `fairness_bias`, `factuality`, `security`, `robustness`, `privacy`,
   `machine_ethics`, `sycophancy`). The mockup's six-axis radar is illustrative
   and is not the axis list — which is the whole reason this constraint exists.
2. Prevalence notes ("common: 92% of assessed models") compute from the
   published cohort at site-build time and are stamped with cohort size and
   date. They are cohort statistics, not bundle content, and the card marks
   them as such (they change as the cohort grows; the bundle does not).
3. Semantic color appears only on severity chips and Δ values. Everything
   else neutral.

3a. **Package-level findings render in their own strip, not inside [1] or [2].**
   Core compounds fire on the UnitOfAssurance and aggregate across *every*
   weakener, so filing them under documentation lets a benchmark gap appear as a
   documentation Critical whose magnitude comes from evidence the documentation
   layer never assessed — observed at 9x growing to 24x once Group-B evidence was
   attached. They belong to the whole assessment, so they sit above both sections
   and are labeled as such. The strip renders only when such findings exist; it
   carries no count when empty rather than showing a reassuring zero.
4. The scope sentence ("Findings describe the published record, not the
   model.") renders on every card unconditionally. Not configurable.
5. The `--cou`/`--mrl` run-context inputs (A2), when supplied, render in the
   header as the assessment's stated context. When absent, the card carries
   no COU line and COMPOUND-EV-01 shows the stated N/A per A2.

---

## A7. uofa.net publication pipeline (Phase A: author-run)

Static site, zero-ops. No server-side assessment, no database, no service.

```
uofa report ... --card
   → bundle.jsonld + card.html + card.json
   → commit to uofa.net site repo under /models/<owner>/<model>/<revision>/
   → CI: uofa verify every bundle in tree; site build fails on any
     verification failure
   → static site deploy; /models index page lists cards
```

- **URL scheme:** `/models/<owner>/<model>/<revision>` is the permanent card;
  `/models/<owner>/<model>` redirects to latest assessed revision and lists
  prior assessments. A card is a dated statement pinned to a model revision;
  re-assessment of a new revision is a new card, not an edit.
- **CI verification is the publication gate.** A bundle that fails
  `uofa verify` cannot ship, including the author's own. The site's integrity
  claim is "every card here re-derives from a bundle that verifies," enforced
  mechanically, not editorially.
- **Index page:** a browsable gallery — filter by developer, sort by assessed
  date. **No ranking view.** No sort-by-factors-present, no sort-by-weakener-
  count. The moment the index sorts on an assessment output it becomes a
  leaderboard and imports every gaming incentive the sufficiency layer
  critiques. Sort keys are metadata only (name, developer, date). The RAI
  score is raidex's number and raidex.ai is where models get compared on it.
- Cohort prevalence stats (A6.2) recompute at site build from all published
  bundles in the tree.

---

## A8. Phase B: third-party submission (the Geekbench-shaped part)

The end state: anyone runs the pack on a model and publishes their card to
the shared gallery, the way a Geekbench user runs the benchmark locally and
uploads a result to the browser. What transfers from that model: local run,
uploaded result, public browsable record, submitter attribution. What does
NOT transfer: the ranked leaderboard (A7) and any server-side scoring.

**Submission mechanism is a pull request, not an upload endpoint.**

```
contributor runs: uofa report ... --card
   → PR to the site repo adding their bundle + cards under
     /models/.../<revision>/ with a submitter manifest
   → CI: uofa verify (signature, schema, template-version support)
   → CI: source-pinning check (A9)
   → merge → deploy
```

Rationale, stated once: a PR pipeline keeps the trust model identical to
Phase A (CI verification is the gate, the repo history is the audit log,
GitHub handles identity, spam, and takedown) and keeps operating cost at
zero. An upload service reintroduces accounts, abuse handling, storage, and
support load — self-funded-scaling territory — for no integrity gain over
CI-verified PRs. If submission volume ever exceeds what PR review absorbs,
that is a funded-channel conversation, not a weekend service build.

**Attribution and trust tiers on the card:**

| Tier | Meaning | Card marking |
|---|---|---|
| `author` | run by the UofA project | "assessed by UofA project" |
| `community` | third-party bundle, CI-verified | "assessed by <submitter> · community submission · signature verified" |

Both tiers meet the same CI bar. The tier communicates *who ran it*, not
*whether it verifies* — verification is binary and gate-enforced for both.
The submitter's signing key fingerprint renders in the verify footer; the
gallery index shows the tier as a filter facet (a metadata facet, permitted
under A7's no-ranking rule).

---

## A9. Integrity model: what the signature does and does not claim

The signature proves the bundle is intact and unmodified since signing. It
does NOT prove the extraction inputs were honest — a submitter could run the
pack against a doctored copy of a model card. The countermeasure is source
pinning plus re-derivability, not trust in the submitter:

1. **Source pinning (extraction-side, becomes a bundle requirement):** every
   extracted field's provenance record carries the source URL and a content
   hash of the fetched source (model card revision, eval report). It is the one
   schema change this addendum adds to the pack itself.

   **PATCHED 2026-08-10 — mechanism corrected.** This originally read "extends
   the existing provenance stamping with two properties per source." It cannot.
   `excel_mapper._provenance()` emits `fieldProvenance` as a **flat list of
   `"field=class"` strings**, and the comment in that function records why: a
   nested map put vocabulary term names in JSON-LD key position, `generatedAtTime:
   "run-context"` was read as an `xsd:dateTime` literal, and rdflib failed on every
   package. Source pinning therefore gets **its own term**, `sourcePin`, carrying
   plain-string `sourceUrl` / `contentHash` / `fetchedAt` and **no `@type`
   coercion**. A round-trip-through-rdflib regression test is mandatory, because
   this is the exact bug class that once made every package unparseable while C1,
   C2 and C3 all stayed green.

   **Do NOT declare it in `spec/context/v0.5.jsonld`.** That context is inlined
   into the document before hashing, so any edit invalidates every signed bundle
   (the Morrison example fails `C1 Integrity` on a one-term addition). It is also
   unnecessary: the context sets `"@vocab": "https://uofa.net/vocab#"`, so an
   undeclared `sourcePin` already expands to `uofa:sourcePin`. See the parent
   spec's note on vocabulary additions. Plain strings and no coercion are exactly
   what `@vocab` gives for free — which is the same reason the nested-map defect
   above is avoidable without a declaration.

   **Pin the `README.md` blob hash, not the repo `sha`.** The hub's `sha` is the
   *repo* revision and changes when any file changes, so pinning it marks a
   byte-identical model card stale on a weights re-upload. The blob hash comes from
   `/api/models/<id>/tree/main`. Non-HF fallback: URL + content hash + fetch date.
2. **CI source-pinning check (Phase B gate):** for HF-hosted sources, CI
   re-fetches the pinned revision and confirms the content hash. A bundle
   whose sources cannot be re-fetched and matched publishes with a visible
   `sources unverified` marking on the card, or is rejected — build-config
   choice, default reject.
3. **Re-derivability as the dispute mechanism:** any published card can be
   challenged by re-running the pack against the pinned sources. A
   contradicting bundle is grounds for a correction PR. No adjudication
   service; the repo's PR review is the venue, same as any open-source
   correctness dispute.
4. **Model-behavior claims are out of scope for [1] and [2].** Those sections
   assess the published record; a dishonest *model card* produces a card that
   faithfully assesses dishonest documentation. Section [3] is where behavior
   enters, and only via raidex-furnished runs with their own provenance.
   The scope sentence carries this boundary for readers.

**INVESTIGATION ITEM — RESOLVED 2026-08-10.** HF exposes revision hashes in a
**bulk** listing: `GET /api/models?author=<owner>&expand[]=sha&expand[]=lastModified`
returns `sha` per model (verified against `meta-llama`). So the per-build staleness
sweep of A12.4 costs one call per *owner* — roughly 15 for a 43-model cohort — not
one per model, and is cheap at any plausible cohort size. Two caveats carried into
A9.1 above: that `sha` is the repo revision, so the pin must be the `README.md`
blob hash from the tree API; and non-HF sources fall back to URL + content hash +
fetch date.

---

## A10. Phasing and gates

| Phase | Scope | Gate to enter | Kill / hold criterion |
|---|---|---|---|
| A6–A7 build | card renderer + static site + author-run gallery over the deep-study cohort | pack (parent spec) built — the pre-defense gate was lifted 2026-08-10 | none beyond parent gating — this is the deep study's publication surface |
| A8 Phase B | PR-based community submission | Phase A live AND ≥3 unsolicited external requests to submit (issues, emails, PRs attempted) | if 6 months post-Phase-A with <3 requests, hold — the gallery stays author-run and loses nothing |
| A9.2 strict source check | default-reject unverified sources | with Phase B | relax to `sources unverified` marking only if false-reject rate on legitimate submissions exceeds ~1 in 5 |

The Phase B entry gate is demand-triggered deliberately: community submission
built ahead of demand is infrastructure for an audience that may not exist,
and the PR mechanism means enabling it later costs days, not months. Nothing
in Phase A precludes it; the bundle format, source pinning, and CI gate are
Phase-B-ready from the start because they are the same machinery.

---

## A11. Constraints carried forward

1. All v0.1 constraints (A5) apply unchanged.
2. No composite UofA score on any card, index, or API output. The RAI score
   appears only inside section [3] with its furnished-evidence framing.
3. No ranking or assessment-output sort keys on the gallery index.
4. Card content derives exclusively from the bundle; cohort prevalence is
   the sole render-time addition and is labeled as cohort data.
5. Publication gate is mechanical CI verification, both phases, no
   editorial-only path — including for the author.
6. **PATCHED** — the pre-defense build gate was lifted on 2026-08-10.
7. No furnisher error text published verbatim (parent spec §6): an excluded
   constituent's traceback carries the operator's absolute filesystem paths, and
   these bundles are published.
