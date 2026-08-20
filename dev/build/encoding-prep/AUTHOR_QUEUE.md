# Author queue

**AWAITING-AUTHOR.** The ordered list of acts this session leaves behind. Seven items, per
W6. Nothing here is done on your behalf and nothing is marked complete.

Every estimate is an assumption. The repo records no adjudication pace, so they are built
from item counts. Correct the first one and the rest follow.

| # | Act | Input | Output | Estimate |
|---|---|---|---|---|
| 1 | Correct the protocol draft | `docs/Encoding_Protocol_v0_1_DRAFT.md`, 14 `[AUTHOR-CONFIRM]` markers | corrected text | ~1h read plus marker walk |
| 2 | Commit the protocol | your corrected text | `docs/Encoding_Protocol_v0_1.md`, committed by you alone | 15 min |
| 3 | Johnson review pass | `REVIEW_PACKET_JOHNSON.md` | verdicts on 11 firings, 20 factor rows, 28 ambiguity entries | one evening, ~3h |
| 4 | Aero COU1 review pass | `aero-cou1/REVIEW_PACKET_AERO_COU1.md` | verdicts, and the 16-of-18 level question settled | ~2h |
| 5 | Aero COU2 review pass | `aero-cou2/REVIEW_PACKET_AERO_COU2.md` | verdicts, and the 12-of-14 level question settled | ~2h |
| 6 | Bologna: rule INV-5 | `BOLOGNA_STATUS.md` | a ruling, not an encoding | 30 min |
| 7 | Sign-off commits | your verdicts | signed packages; ledger rows flip per the Ch4 spec | 1h |

Total, if nothing surprises you: about ten hours, spread across four sittings.

## What changed under you, and where

Item 1 is a red-pen job rather than a blank page, but three of its markers are questions the
draft cannot answer from the repository and you should expect to write those yourself.
Prompts 4b, 4c, 2a and 5a all ask for Morrison recall, and there is no committed record of
Morrison dispositions to reverse-engineer from. The draft says so at each point rather than
inventing a rule and attributing it to you.

Item 3 is the largest because Johnson is a real 7009A paper encoded under a 7009B pack, so
most of its twenty-eight ambiguity entries are cross-standard mapping decisions. Items 4 and
5 are smaller for the same reason inverted: those bundles were authored against this pack.

Item 6 is not an encoding and should not become one until you rule. Bologna is already
load-bearing in the H2 chain, and §1 of the protocol draft you are about to commit excludes
H2 references from the extract path. Running it would settle an open escalation by executing
it.

## Three things that block item 7 specifically

**The namespace.** All three packages mint under `https://github.com/cloudronin/uofa`,
because `https://uofa.net` is refused as reserved. The identifier is inside the signature and
cannot be corrected afterward. Confirm it before you sign anything, not after.

**The Johnson decision record.** The paper says acceptance requirements were met and records
no decision act, no decider, and a `(Signed)` line with nothing after it. The encoding reads
Accepted with `Decided By` and `Decision Date` blank. That is the one summary-level cell
where your judgment carries the whole weight.

**Two escalations that are not yours to close here.** `Input pedigree` has no factor in the
pack though Johnson predeclares and achieves it, and Level 0 is inexpressible on thirteen of
nineteen factors. Both are INV-20 territory and both are marked ESCALATION in the ambiguity
log so they survive the encoding.

## What this session did not do

No signing. No final verdicts. No review marked complete. No ledger row touched. No v0.6
schema work. No manuscript prose.

One item was added to the tooling rather than the queue, because it is not an author act:
`--protocol-check` now gates `uofa import` and reports on `uofa extract`. Every packet above
passes it before reaching you, which is what it is for.
