# Cross-browser test pass — uofa.net

> **Pre-flight:** run `node site/scripts/check-pages.mjs` against production first. If any of the automated sanity checks fail, fix those before walking the visual matrix below.

## Pass metadata

- **Deploy SHA tested:** `_______` (from footer of `https://uofa.net/`)
- **Tester:** _______
- **Date:** ____-__-__
- **Defects filed:** _______ (link to GitHub issue list)

## Browsers (B1–B5)

| ID | Browser | Device | Version (fill in) |
|---|---|---|---|
| B1 | Chrome | Desktop (Mac/Windows) | _______ |
| B2 | Safari | macOS desktop | _______ |
| B3 | Firefox | Desktop | _______ |
| B4 | Safari | iPhone (iOS 17+) | _______ |
| B5 | Chrome | Android | _______ |

## Surfaces (S1–S5)

| ID | URL |
|---|---|
| S1 | <https://uofa.net/> (splash) |
| S2 | <https://uofa.net/demo/> |
| S3 | <https://uofa.net/feedback/> |
| S4 | <https://uofa.net/reference/catalog/> |
| S5 | <https://uofa.net/research/nafems-2026/> |

---

## S1 — Splash (`/`)

For each browser, verify (60 sec per cell):

- [ ] B1 — Hero badge `v0.7.x · Live this Wed at NAFEMS Americas` on one line
- [ ] B1 — Three Hero CTAs side by side
- [ ] B1 — DemoStrip box-drawing chars (`══`, `─`, `└──`) render as solid lines
- [ ] B1 — Pillars in 4-column grid (desktop)
- [ ] B1 — Footer renders with 4-column grid + meta strip
- [ ] B1 — Footer SHA is a 7-char hex string (not "dev")

- [ ] B2 — Hero badge on one line
- [ ] B2 — Three CTAs side by side
- [ ] B2 — Box-drawing chars render correctly
- [ ] B2 — Pillars 4-column
- [ ] B2 — Footer 4-column + meta
- [ ] B2 — Footer SHA hex

- [ ] B3 — Hero badge on one line
- [ ] B3 — Three CTAs side by side
- [ ] B3 — Box-drawing chars render correctly
- [ ] B3 — Pillars 4-column
- [ ] B3 — Footer 4-column + meta
- [ ] B3 — Footer SHA hex

- [ ] B4 — Hero badge readable, no awkward wrap
- [ ] B4 — Three CTAs stack to single column
- [ ] B4 — Box-drawing chars render
- [ ] B4 — Pillars 1-column on mobile
- [ ] B4 — Footer collapses gracefully (single column or 2-column at 375px)
- [ ] B4 — Footer SHA hex

- [ ] B5 — Hero badge readable
- [ ] B5 — Three CTAs stack
- [ ] B5 — Box-drawing chars render
- [ ] B5 — Pillars 1-column
- [ ] B5 — Footer collapses gracefully
- [ ] B5 — Footer SHA hex

## S2 — `/demo/`

- [ ] B1 — Code blocks (git clone, pip install, uofa extract) render with syntax highlighting and no overflow
- [ ] B1 — 8 numbered stages render with consistent heading hierarchy
- [ ] B1 — COU 1 / COU 2 pattern tables render with all rows visible
- [ ] B1 — Internal links (`/start/`, `/start/from-excel/`, `/feedback/`) resolve

- [ ] B2 — Code blocks render
- [ ] B2 — 8 stages, consistent hierarchy
- [ ] B2 — Pattern tables fully visible
- [ ] B2 — Internal links resolve

- [ ] B3 — Code blocks render
- [ ] B3 — 8 stages, consistent hierarchy
- [ ] B3 — Pattern tables fully visible
- [ ] B3 — Internal links resolve

- [ ] B4 — Code blocks have horizontal scroll on mobile (no text overflow)
- [ ] B4 — 8 stages, hierarchy clear
- [ ] B4 — Pattern tables horizontally scrollable, no cut-off at 375px
- [ ] B4 — Internal links resolve

- [ ] B5 — Code blocks have horizontal scroll
- [ ] B5 — 8 stages, hierarchy clear
- [ ] B5 — Pattern tables scrollable, no cut-off
- [ ] B5 — Internal links resolve

## S3 — `/feedback/`

- [ ] B1 — Channel table renders without column overflow
- [ ] B1 — Blockquote questions render with visible left border
- [ ] B1 — `mailto:support@uofa.net` opens default mail handler

- [ ] B2 — Channel table OK
- [ ] B2 — Blockquote left border visible
- [ ] B2 — Mailto opens mail handler

- [ ] B3 — Channel table OK
- [ ] B3 — Blockquote left border visible
- [ ] B3 — Mailto opens mail handler

- [ ] B4 — Channel table fits at 375px (no overflow)
- [ ] B4 — Blockquote visible
- [ ] B4 — Mailto launches Mail.app

- [ ] B5 — Channel table fits
- [ ] B5 — Blockquote visible
- [ ] B5 — Mailto launches default Android mail handler

## S4 — `/reference/catalog/`

- [ ] B1 — 23-row pattern table renders without horizontal scroll
- [ ] B1 — Severity column color-codes read clearly in dark theme
- [ ] B1 — Page header inline `code` styling visible

- [ ] B2 — 23-row table fits
- [ ] B2 — Severity colors clear
- [ ] B2 — Inline code styling visible

- [ ] B3 — 23-row table fits
- [ ] B3 — Severity colors clear
- [ ] B3 — Inline code styling visible

- [ ] B4 — Table is horizontally scrollable on mobile (rather than overflowing)
- [ ] B4 — Severity colors clear
- [ ] B4 — Inline code styling visible

- [ ] B5 — Table horizontally scrollable
- [ ] B5 — Severity colors clear
- [ ] B5 — Inline code styling visible

## S5 — `/research/nafems-2026/`

- [ ] B1 — Numbered list of demo stages renders cleanly
- [ ] B1 — `git checkout v0.7.x` appears in a code block (not inline text)

- [ ] B2 — Numbered list clean
- [ ] B2 — `git checkout` in code block

- [ ] B3 — Numbered list clean
- [ ] B3 — `git checkout` in code block

- [ ] B4 — Numbered list clean
- [ ] B4 — `git checkout` in code block

- [ ] B5 — Numbered list clean
- [ ] B5 — `git checkout` in code block

---

## Cross-cutting flows (1× per browser)

### Sidebar hamburger (B4 + B5 only — desktop has full sidebar)

- [ ] B4 — Tap hamburger → sidebar slides in → tap link → sidebar closes → new page renders
- [ ] B5 — Tap hamburger → sidebar slides in → tap link → sidebar closes → new page renders

### Search modal (all browsers)

- [ ] B1 — `Ctrl+K` (or click search) → modal opens → type "weakener" → results appear → click result → navigates correctly
- [ ] B2 — `⌘K` → modal opens → search → click result → navigates
- [ ] B3 — `Ctrl+K` → modal opens → search → click result → navigates
- [ ] B4 — Tap search → modal opens → type → tap result → navigates
- [ ] B5 — Tap search → modal opens → type → tap result → navigates

### Theme toggle (all browsers — should NOT appear)

- [ ] B1 — No theme-select dropdown visible in header (site is dark-locked)
- [ ] B2 — No theme-select visible
- [ ] B3 — No theme-select visible
- [ ] B4 — No theme-select visible
- [ ] B5 — No theme-select visible

### QR scan (B4 + B5 only — print or display slide-15 / slide-19)

- [ ] B4 — Slide-15 QR → camera opens scanner → URL → page loads `/demo/`
- [ ] B4 — Slide-19/20 QR → URL → page loads `/feedback/`
- [ ] B5 — Slide-15 QR → URL → page loads `/demo/`
- [ ] B5 — Slide-19/20 QR → URL → page loads `/feedback/`

### Footer external link (all browsers)

- [ ] B1 — Click "Source on GitHub" → opens cloudronin/uofa repo
- [ ] B2 — Click → opens repo
- [ ] B3 — Click → opens repo
- [ ] B4 — Tap → opens repo
- [ ] B5 — Tap → opens repo

### Edit page link (all browsers — Starlight footer on a docs page)

- [ ] B1 — Click "Edit page" on `/demo/` → opens correct GitHub edit URL
- [ ] B2 — Click → opens correct URL
- [ ] B3 — Click → opens correct URL
- [ ] B4 — Tap → opens correct URL
- [ ] B5 — Tap → opens correct URL

---

## Defects log

File each defect as a GitHub issue with `[ui][cross-browser]` labels. Use this template per defect:

```
**Browser/version:** B_ — _________
**URL:** https://uofa.net/_______
**Expected:** _______
**Observed:** _______
**Screenshot:** [link / paste]
**Severity:** blocker / major / minor
```

Do NOT fix defects inline during the test pass. Batch-fix in a follow-up session so the test pass stays a clean cycle.

---

## Sign-off

- [ ] Desktop matrix (B1+B2+B3 × S1–S5) complete
- [ ] Mobile matrix (B4+B5 × S1–S5) complete
- [ ] Cross-cutting flows complete
- [ ] QR-scan end-to-end complete (printed slide)
- [ ] All blockers fixed and re-verified, OR explicitly accepted as known issues with mitigation noted

**Signed:** _______ — ____-__-__
