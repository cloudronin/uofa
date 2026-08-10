# Addendum v0.3: A12 — embeddable assessment badge

**Applies to:** model-credibility-pack-spec.md + addenda v0.1, v0.2
**Status:** ACTIVE — same gating as the parent spec, whose POST-OCTOBER gate was
lifted on 2026-08-10. Extends the uofa.net publication pipeline (A7) with a badge
endpoint. Numbering continues from v0.2.

**Revision note (2026-08-10):** A12.4's staleness comparison is corrected (it
compared the wrong hash) and given a defined behaviour for models with no HF
source. Its investigation item is resolved.

---

## A12. The badge

A shields-style static SVG a model author embeds in their HF model card,
linking to the full report card on uofa.net. Minimal by decision (recorded):
name, pack version, assessment date. No scores, no factor counts, no weakener
counts — the badge says "this model has a verifiable assessment, dated," and
the card says everything else.

### A12.1 Format

Two-segment shields layout, pypi-badge style:

```
[ uofa ][ v1.0.2 · 2026-11-14 ]
```

- Left segment: `uofa`, flat gray.
- Right segment: pack version + assessed date (ISO, date only).
- One accent color for the right segment in the normal state; a distinct
  muted/amber state for stale (A12.4). Exact colors are a template asset
  decision, not spec-bound.
- No model name in the badge — it sits on the model's own card; the name is
  the page it's on.

### A12.2 Generation and serving

Badges are build-time artifacts of the existing static site pipeline, not a
service:

```
site build (A7):
  for each published bundle:
    → /badge/<owner>/<model>.svg            (latest assessed revision)
    → /badge/<owner>/<model>/<revision>.svg (pinned, immutable)
```

- Generated from `card.json`, same derivation discipline as the card:
  `badge = g(bundle)`, `g` versioned with the card template.
- `/badge/<owner>/<model>.svg` re-points to the newest assessment at each
  site build. The pinned form never changes after publication.
- Embed snippet rendered on every report card page for copy-paste:

```markdown
[![uofa assessment](https://uofa.net/badge/<owner>/<model>.svg)](https://uofa.net/models/<owner>/<model>)
```

- Click-through target is the `/models/<owner>/<model>` redirect (A7), which
  resolves to the latest assessed revision.
- No parameterized badge endpoint, no query strings, no dynamic rendering.
  Every badge that exists corresponds to a published, CI-verified bundle;
  there is no way to mint a badge without passing the A7 publication gate.

### A12.3 Who gets a badge

Any published card, both trust tiers (A8). The badge asserts "a CI-verified
assessment of this model exists at this URL" — the tier, submitter, and
findings all live on the card behind the click. A community-submitted
assessment produces an embeddable badge identical in form to an author-run
one, because the verification bar is identical (A8).

Authors embed voluntarily. There is no outreach obligation, no "claim your
badge" flow, no notification service. The embed snippet on the card page is
the entire distribution mechanism.

### A12.4 Staleness

The badge sits on the artifact the assessment assessed, and the author can
edit that artifact after assessment. The badge must not silently vouch for
content it never saw.

- At each site build, for every published model, CI compares the current HF
  card revision (hub API) against the bundle's pinned source revision (A9.1).

  **PATCHED 2026-08-10 — compare the `README.md` blob hash, not the repo `sha`.**
  The hub's `sha` is the *repo* revision and moves when any file in the repo
  changes, so comparing it turns the badge amber after a weights re-upload that
  left the model card byte-identical. That is a badge going stale for a reason
  the reader cannot see and the card cannot support, which A12.5.3 forbids — and
  it is AGENTS.md §13's "instrument that reports success" inverted: an instrument
  reporting a failure that did not happen. The blob hash comes from
  `/api/models/<id>/tree/main`.

  **Models with no HF-hosted source have no staleness state.** Roughly half the
  assessed cohort is API-hosted (`anthropic/*`, `openai/*`, `xai/*`) with no
  model card at all, so there is no pinned source revision and nothing that can
  diverge. Their latest-badges are treated exactly like pinned-revision badges
  below: never stale, because they never claimed a source that could change.
  Not "stale-unknown" — an amber state for an absence would assert a change that
  cannot be observed.
- On divergence, `/badge/<owner>/<model>.svg` regenerates in the stale
  state: right segment reads `<date> · superseded source` (or equivalent
  short form) in the muted/amber styling. The click-through still resolves;
  the card page shows a banner: "the model card has changed since this
  assessment (pinned <hash>, current <hash>)."
- Pinned revision badges (`.../<revision>.svg`) never go stale — they claim
  only their own revision, which is immutable.
- Re-assessment of the new revision publishes a new card (A7 URL scheme),
  and the latest-badge re-points to it, clearing the stale state.

This makes the badge self-honest: its truthfulness is checked mechanically
every build, not entrusted to the author displaying it. Same property as
everything else in the pipeline.

**INVESTIGATION ITEM — RESOLVED 2026-08-10.** Shares the A9 item, now closed.
`GET /api/models?author=<owner>&expand[]=sha&expand[]=lastModified` returns `sha`
in a bulk listing (verified against `meta-llama`), so the sweep groups the cohort
by owner and issues one call each — roughly 15 calls for a 43-model cohort, not
43. Rate limits are not a concern at this scale. The remaining work is the blob-
hash refinement in A12.4 above, not the call pattern.

### A12.5 What the badge must never carry

1. No scores, counts, grades, colors-as-verdicts, or any assessment output.
   The minimal-content decision is not cosmetic: a badge with a number
   becomes a comparison surface on HF pages, which is the leaderboard
   pressure A7 excludes, arriving through the embed. Name, version, date,
   staleness state — nothing else, in any future revision of `g`.
2. No badge without a published bundle behind it. The badge inherits the A7
   gate; there is no standalone badge path.
3. The stale state can only be *added* honesty (marking divergence). No
   badge state may ever soften a finding on the card it links to.

### A12.6 Phasing

Ships with Phase A (A10) — it is a build-time loop over already-published
bundles plus one SVG template, and the embed snippet is static page content.
No separate gate. The staleness check (A12.4) depends on A9.1 source pinning,
which is Phase-A machinery already.
