# Morrison under v0.9 — the Case 1 sibling

These are **siblings**, not replacements. `../morrison/` ships the original
bytes, signed under its declared v0.5 context, and those bytes are cited by the
praxis record — the LEDGER counts and the cross-version-verify claim are about
*them*. They are frozen. Nothing here re-signs them.

What these siblings add is the same content expressed in the v0.9 decision
model, so Case 1 has a live, checkable form:

- `decisionProvenance: "extracted"` — the source already decided. The FDA-CDRH
  credibility assessment team's acceptance is **transcribed** here, not rendered.
- `decisionAnchor` — a locator plus a sha256 computed from the shipped
  `source/decision_rationale_cou{1,2}.pdf`. The pin is what separates
  transcription from invention: "the paper is their attestation" means nothing
  if a reader cannot check that the paper says it.
- **No decision signature, ever.** Morrison's team never signed a UofA package
  and never will. The anchor is their attestation; a signature slot would imply
  an act that did not happen.

They ship **unsealed** (placeholder integrity fields). CI seals them with
throwaway fixture keys, so proving the round trip never requires a production
key and no key identity in this tree implies an endorsement nobody gave.
