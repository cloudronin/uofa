# Response: keyless table route, holdout gate, fork re-scope

The result is accepted as a development result and the routing-by-evidence-
structure architecture is ratified. Four rulings before anything ships or
enters the qualification table.

## 1. The 0/24 is in-sample — holdout gate before qualification

The route was developed, diagnosed, and repaired against the same 24 cases it
now scores perfectly on: the eight lm-eval header misses were found on these
cases and fixed for these cases. That is training on the test set. The LLM
rows do not share the defect (prompt v2 renders from the sheet and was never
tuned against case outcomes), so the comparison table as committed is
asymmetric.

Required before the route wires into `card_prose` or claims a qualification
row:

- **Held-out set:** table-borne P2 positives the route has never seen — the
  gold set's trainer-table cluster plus a fresh corpus draw, covering format
  variety (stefan-it five-run tables, HTML tables per enriched row 146,
  model-index-rendered tables, lm-eval variants beyond the repaired shape).
- **Bar declared before the run**, same as everything else: false-fire ≤10%,
  false-clear ≤5%, per property.
- The in-sample 0/24 stays in the study as the development record, labeled
  in-sample; the holdout number is what the qualification table carries.

Expectation: it holds — table parsing generalizes better than prompts. But
expectation is not measurement.

## 2. Label review queue — batch to me

The `ibraheemmoosa/xlmindic-base-multiscript` P2 cell joins the queue,
correctly unflipped. The queue is now ~10 rows (P5 holds + this). Send the
whole batch in the seven-flip format — card, verbatim quote, sheet clause,
confirm/keep boxes — and I clear it in one pass. That unblocks corrected
denominators for the holdout gate and the fork.

## 3. Three-arm fork re-scopes to the prose residue

Table-borne evidence exits the LLM comparison entirely: it has a
qualified-pending-holdout route, and LLM arms competing on it would measure a
task that needs no model. The fork's arms (single-pass v2 baseline,
per-property, multi-pass extract-then-adjudicate) now run on prose-borne
positives only. Consequences to encode in the fork declaration:

- Denominators shrink and per-arm cost drops; state the new expected-n per
  property in the declaration.
- The arms now test exactly one question: is prose-relational reading
  recoverable by staging, or does it stay panel-only per the A16.4
  pre-commitment. Thresholds for all three arms declared before the first
  call.
- Multi-pass arm constraint (binding): pass two must cite the span it
  judged, and the emitted property carries that span in provenance. A
  "present" without a quotable anchor is inference wearing extraction's
  clothes — "stated, not inferable" binds the machine exactly as it bound
  the labelers.

## 4. P5 table extension — authorized behind the same gate

Random-Baseline / chance-value rows in tables are in-scope for the keyless
route as an extension. Same discipline: developed on whatever it's developed
on, qualified only on held-out cases, bar declared first. No property enters
the keyless route on in-sample evidence alone.

## For the study text

Keep two sentences close to verbatim:

1. "The pin is the code": the keyless route's reproducibility claim — no
   temperature, no seed, no prompt hash, no provider availability — is
   categorically different from an LLM row's, and the qualification table
   should carry a pin-type column making that visible.
2. The null-model contract caught over-tooling: an 8% LLM miss rate on a
   deterministic field-read was the signature of a task that never needed a
   model, and it surfaced only because every route is measured against
   blanks-are-the-feature. That is the D2 principle discovered one layer
   down — prose cards contain structured islands — and it is a methods
   paragraph, not a footnote.

Order of operations: batch me the label queue → holdout draw and gate →
fork declaration (prose residue, three arms, spans required) → runs.
Nothing else waits on me.
