# Amendment 01 (DRAFT — awaiting sign-off): W-EV-DIV-07's validation venue

**Status: UNSIGNED DRAFT. Not in force.** `PREREGISTRATION.md` is frozen as of
2026-08-11 and is **not modified by this file**. Until signed, DIV-07's Mode 2
remains deferred to the deep-study cohort exactly as frozen.

**Raised:** 2026-08-11
**Signed:** ______________  (date, by the study author)

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

## Not recommended for signature yet

Two diligence checks are outstanding and are the same two blocking the A17 field
arm (see `docs/model-credibility-pack-addendum-v0_6-field-study.md`):

1. **Pinning adequacy.** A CSV on a HF dataset repo with no dataset card. A
   content hash pins the file; whether the repo's revision history is stable
   enough to cite is unverified.
2. **Redistribution terms.** Unstated. Whether sampled card text may be quoted in
   a paper or shipped as a fixture is unknown.

A venue that cannot be cited or quoted is not a venue for a published study,
however rich its opportunity count. **Sign only after both clear.**

## If they do not clear

The freeze stands unamended and DIV-07 settles on Mode 1 plus the deep-study
cohort, which is what it says today. That outcome is already accounted for and
requires no action.
