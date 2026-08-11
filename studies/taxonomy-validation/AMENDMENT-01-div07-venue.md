# Amendment 01 (DRAFT — awaiting sign-off): W-EV-DIV-07's validation venue

**Status: SIGNED 2026-08-11. In force.** `PREREGISTRATION.md` is frozen as of
2026-08-11 and is **not modified by this file**. Until signed, DIV-07's Mode 2
remains deferred to the deep-study cohort exactly as frozen.

**Raised:** 2026-08-11
**Signed:** 2026-08-11, by the study author

DIV-07's Mode 2 runs on the modelbiome field arm's ~4,700 opportunities. The
deep-study cohort is retained for mechanism, as already ruled.

An amendment rather than an edit, because a frozen pre-registration that can be
revised in place certifies nothing. The frozen text stands; if this is signed,
both documents travel together and the change is visible as a change.

---

## What prompted it

The freeze deferred DIV-07's field-behaviour validation on a measured ground:
the Liang corpus offers **24 opportunity cards in 32,111 (0.07%)**, which cannot
support adjudication at any threshold. That deferral was correct for that corpus
and remains correct for it.

A more recent corpus has since been identified —
`modelbiome/ai_ecosystem_withmodelcards`, 1,860,411 rows, cards created
**2022-03 to 2025-07** — and measured on a 200,000-row sample (98,864 non-empty
cards):

| | Liang | modelbiome (sampled) |
|---|---|---|
| DIV-07 opportunity rate | 0.07% | **0.25%** |
| Opportunities available | **24** | **~4,700** extrapolated over 1.86M |
| Constituents seen | — | ethics 166, simpleqa 53, bbq 37, xstest 6, wmdp 4 |

The difference is recency, not measurement error: SimpleQA, StrongREJECT and
XSTest largely postdate Liang's 2023-10-01 snapshot.

## What would change if signed

DIV-07's **Mode 2 (field behaviour)** moves from *deferred to the deep-study
cohort* to *adjudicated on the modelbiome field arm*, with the expected
opportunity count pre-registered from a full-corpus frame run before any judge
call — the same discipline the freeze applied to Liang.

**Mode 1 (mechanism) is unchanged** and already satisfied. The deep-study cohort
remains a valid second venue and is not withdrawn.

**Nothing else in the freeze changes.** Not the catalog, not the thresholds, not
the gold-set plan, not the panel/deterministic split, not Liang's role as the
A16 validation corpus. This amendment concerns one rule's Mode-2 venue.

## Diligence checks: RUN 2026-08-11, both clear

Findings attached per the ruling. Full detail in A17.3.

1. **Redistribution terms — PASS.** CC-BY-4.0, dataset card present, paper at
   `arXiv:2508.06811`. Quoting card text and shipping fixtures are permitted with
   attribution. The draft's "no dataset card, unclear terms" was wrong: it rested
   on a null `cardData` in one API response that I read as absence instead of
   re-checking the raw README.
2. **Pinning adequacy — PASS at corpus level, one stated limit.** Repo sha
   `4cb5d873…`, single content-hashable CSV, snapshot dates stated (models
   2025-07-13, cards 2025-07-21). **No per-row card revision exists**, so an
   individual card cannot be verified against live HF at the scraped version.
   Rows pin by content hash against the pinned corpus — the same mechanism the
   A16.3 gold set already uses.

**Both clear, so the blocking objection is withdrawn.** The remaining limit is
narrow: claims attach to the snapshot rather than to HF's revision history, which
is Liang's position too and acceptable for a study whose population is the
snapshot.

**This amendment is now ready for signature** on its merits rather than blocked
on diligence. What signing decides is only whether DIV-07's Mode 2 runs on the
modelbiome field arm (~4,700 opportunities) instead of deferring to the
deep-study cohort.

## Scope of the field arm (a scope statement, not a caveat)

**The field arm's population is the July 2025 snapshot.** Claims derived from it
attach to that snapshot, not to HuggingFace's revision history. No per-row card
revision was recorded, so "was this card altered after scraping" is not
answerable on this arm at all.

It is answerable on the small owned 2026 pull, which therefore has a second job
beyond recency: **it is the only arm with live-verifiable pins.** Any claim
requiring verification against live HF belongs there and nowhere else.

Stated here rather than in notes because it bounds what the arm can support, and
a reader of a published figure should not have to reconstruct it.

## If not signed

The freeze stands unamended and DIV-07 settles on Mode 1 plus the deep-study
cohort, which is what it says today. That outcome is already accounted for and
requires no action.
