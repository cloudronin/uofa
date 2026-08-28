# Encoding Protocol v0.2 — amendments draft

**This is a draft of the v0.2 batch. It amends nothing.** `docs/Encoding_Protocol_v0_1.md`
governs every encoding until the adoption event described at the end of this file.

This document consolidates `docs/protocol-v0_2-notes.md` (the accumulation pile), the
docs-review findings, and the author's adoption ruling into one instruction.

**It edits nothing.** Not v0.1, not the pile, not any shipped record. The pile is superseded by
this draft *in substance*, and gains its pointer and stops accumulating **at adoption** — see the
final section. Until then the pile stands unmodified, which is the same discipline that keeps
v0.1 frozen: a document does not quietly change state because a successor exists.

## The discipline this draft inherits

From the pile's own header, kept because the reasoning is the point:

> **Why a pile rather than edits.** `docs/Encoding_Protocol_v0_1.md` is committed, and the
> Johnson package is signed under it as written. An encoding records the protocol version that
> governed it, and that guarantee is only worth something if a governing version stops moving
> once packages are signed against it. Reopening v0.1 for an improvement discovered *after*
> signing would muddy exactly the version discipline the record depends on — the encoder could
> no longer tell which v0.1 they read. So improvements accumulate here and land in one edit.

v0.2 lands as **one edit and one adoption event**. Improvements accumulate until then.

## The two batches are in different validation states, and the difference is not cosmetic

| | validation state | blocked on |
|---|---|---|
| **Batch A** | **evidence-complete.** The v0.1-era gate was met on 2026-08-21: both aero packages are adjudicated, signed and verified, and the Ch4 ledger's last three PENDING-ENCODING rows are entered. | nothing but the batch |
| **Batch B** | **pending C-series validation.** Drawn from the stranger series; each item cites committed records, but the measured completion rate that would validate them does not yet exist. | the C-series reporting |

Every Batch B item is marked accordingly at its head. An item Batch B cannot validate against
that evidence is marked unvalidated or dropped at adoption; it does not land on the strength of
having been drafted.

---

# Batch A — v0.1-era, evidence-complete

## A1. Operator identity is declared, not inherited

**Where it goes.** One paragraph in **A-11**, beside the import command; one check candidate
added to **F-6c**'s list in `dev/build/pilot-johnson/PROTOCOL_FINDINGS.md`.

**What raised it**, from `docs/protocol-v0_2-notes.md`: the Johnson package was signed carrying
`wasAttributedTo: …/org/claude`. The 2026-08-20 import ran in a container whose identity
resolved to `claude`, "and the value was covered by the signature before anyone noticed it."
The pile's own diagnosis is the load-bearing sentence:

> The value was not wrong. … The defect is that nobody **chose** it. This is A-2's bug with a
> different field: a value inherited from the environment, frozen under a signature, that the
> encoder never decided.

### Draft text for A-11 (from the pile, verbatim)

> **Declare the operator identity; do not inherit it.**
>
> Set `UOFA_ASSESSOR` explicitly on the import, to the person or agent that is running the
> tool:
>
> ```
> UOFA_ASSESSOR="<operator>" uofa import <workbook>.xlsx --pack <pack> \
>   --base-uri <your-namespace> --protocol-check
> ```
>
> Left unset, the importer falls back to `git config user.name` and then to `$USER`, and
> writes whichever it finds into `wasAttributedTo`. Those are properties of the shell the
> import happened to run in, not decisions about the encoding, and the field is covered by the
> signature like any other. An encoding run in a container inherits the container's identity;
> the same workbook imported on a laptop inherits the laptop's. Neither is a claim anyone made.
>
> `wasAttributedTo` is **who ran the tool** and is not the assessor. Where the source names who
> performed the assessment, that is read into `statedAssessor` and the two stay distinguishable.
> A machine-run import declaring a machine operator is correct and is not a defect to hide: it
> is the same distinction A-13 draws when it requires the run log to say whether a review was
> machine-drafted preparation or a named person's work.
>
> **Check:** `--protocol-check` fails when the operator identity was not explicitly declared.

### The open question, resolved

The pile deferred one thing: *"Whether `--protocol-check` can see this at all after the fact."*

**Resolved by reading the code. It cannot see it in the package, and the check must live in the
run log.**

`excel_mapper._operator_identity()` (`src/uofa_cli/excel_mapper.py:184`) returns a **string** and
nothing else — `UOFA_ASSESSOR`, else `git config user.name`, else `$USER`. `map_to_jsonld` then
writes `doc["wasAttributedTo"] = f"{base}/org/{slugify(operator)}"` (line 328). The resolved
value is recorded; **which branch produced it is not**. A package-side check therefore cannot
distinguish a declared operator from an inherited one, exactly as the pile's own draft F-6c text
predicted: *"an undeclared operator is indistinguishable after the fact from a declared one that
happens to match the shell."*

So A1's check is a **run-log check**, in the same family as `base_uri`, and there is a working
precedent to follow rather than a pattern to invent:

- `protocol_check.RUN_LOG_FIELDS = ("model", "backend", "site commit", "repo head", "base_uri")`
  (`src/uofa_cli/protocol_check.py:59`) — the fields A-3's check reads from the log.
- `_BASE_URI_LINE = re.compile(r"^\s*base_uri\s*[:=]\s*(\S+)", …)` (line 77) — how a declared
  value is read out of it.
- `_check_namespace()` (line 403) — cross-references the run log's declared value against the
  package's own id.

### Draft check candidate for F-6c (revised from the pile)

> **Operator identity declared rather than inherited.** The run log records the operator, and
> the recorded value matches the package's `wasAttributedTo`. A **run-log** check, not a package
> check: the package carries the resolved value only, so declaredness is not recoverable from it.
>
> It **fails closed rather than skipping.** `_check_namespace` skips when no minted identifier or
> declared `base_uri` is present, because absence there is a legitimate state. Absence here is
> the defect itself, so a log with no declared operator fails.

**Recommended, and larger than a text amendment.** The durable form is for the importer to
**record which branch it took**, because `_operator_identity()` is the only party that knows.
That converts declaredness from something the encoder asserts into a fact recorded at the moment
it is known. It is a tooling change and belongs with the schema increment; the run-log check
above is the form that can land with v0.2's text alone. Filed here so the stronger option is not
lost by being harder.

### Cross-era note

This is **the same law as the stranger harness's lineage rule**, arrived at independently on the
instrument side. `POST /p/<slug>/lineage` in the Credenza harness is written only by the
launcher, is reachable from no screen, and exists because — in that route's own words — *"Run 17
typed `claude-3-7-sonnet-20250219` into the control this replaces while being
`google/gemini-3.7-flash`."*

One principle, two eras, three failure modes it covers:

- **inherited** — the Johnson import took the container's identity (A1's case);
- **self-reported** — run 17 typed a name it was not (the lineage route's case);
- **collapsed** — two names folded into one, which is why A-3 requires both the extractor's
  model and the agent's.

**Identity facts are declared by the party that knows them, never inherited from the environment
and never self-reported.**

## A2. D-06 as the worked disposition example

**Where it goes.** Part B, the paragraph reading *"Two worked examples are **v0.2 items**,
supplied after the first governed review passes."*

**Citable as** `dev/build/pilot-johnson/DISPOSITIONS_DRAFT.md`, row D-06.

- **Firing.** `W-AR-05` on `waived-validation-against-real-world-system-data`.
- **Verdict.** Confirmed, with an offsetRationale anchored p.19.
- **The record's own words:** *"Confirmed because the source states at p.19 that no comparator
  data exists and the package correctly carries none."* The offsetRationale reads: *"no RWS data
  exists; test data served as the referent; the conservative tolerance bound and the PRA context
  bound the model's use."*
- **Why it is the right example.** Part B named its own strongest candidate — *"a validation
  activity waived by a documented authority decision, which reads correctly whether adjudicated
  against source or package"* — and D-06 is that case, now adjudicated rather than hypothetical.
  It is the one firing in the pilot that reads Confirmed on **both** readings; every other firing
  separates them.
- **Its second lesson.** The record carries an explicit ruling: *"RULED on the E-3 escalation:
  disposition record only, no package node."* The offsetRationale lives in the disposition record
  because the on-ramp has no route to `hasOffsetRationale` for a validation-result firing, and
  minting one *"would be a hand-crafted graph edit of the class the fixtures finding warned
  about."* So the worked example also demonstrates a Confirmed verdict with a real mitigating
  rationale, housed where the template can hold it.

## A3. The COU1/COU2 pair as the Not-Applicable-versus-Overruled example

**Where it goes.** Part B, the same paragraph as A2, which states the distinction *"needs a case
from a package whose decision outcome was Not accepted, and no such record is yet committed."*
Aero COU2 is now that record, signed.

**Ruled together on 2026-08-21**, because the pair teaches what neither case teaches alone:
identical weaknesses, different contexts of use, opposite defensible decisions — take-off concept
screening tolerates what cruise creep-life does not. That is the tier logic's one essential job.

**The firing counts are the axis.** Cite both rows:

- `dev/build/encoding-prep/aero-cou1/DISPOSITIONS_DRAFT.md`, **A1-13** — `W-EP-04 [High]`, ×1,
  Confirmed. *"Results uncertainty is `not-assessed` at MRL 3, and §5.4 states probabilistic UQ
  is required there … The disposition notes that the decision already prices it: the conditions
  attached to the acceptance exist because of these gaps."* The decision stands as
  `Accepted (with conditions)` (row A1-16).
- `dev/build/encoding-prep/aero-cou2/DISPOSITIONS_DRAFT.md`, **A2-12** — `W-EP-04 [High] ×5`,
  Confirmed, emphatically. *"At cruise-creep stakes, five risk-conditioned unassessed factors are
  precisely why the source's own answer is Not Accepted: **the firings and the decision agree.**"*
  The five share one root cause: §4.2 *"The cascade (Re 1.20e6) is outside the cruise operating
  envelope (Re 0.85e6)"*.

**What the pair demonstrates.** A Not-accepted decision changes which firings are *about* the
decision and which are merely about the package, and that is the axis the
Not-Applicable-versus-Overruled distinction turns on. Both rows record the same rule applied to
both packages — *"which is what makes it a rule rather than two decisions."*

## A4. Sign-off verifies against the published wheel, at whatever version is current

**Where it goes.** The sign-off step, alongside the signing instruction.

**The rule.** Verification is run against the **published wheel at whatever version is then
current**, in a clean environment, with the package outside the repository. *The version gap is
the test.*

**The measurement behind it**, from `studies/ch4_numbers/LEDGER.md` §4.5, "Exit is free, with a
measurement behind it":

> Both NASA substrates were **imported and signed under `uofa-cli 0.11.0` and verify under the
> published `uofa 0.12.0`** — installed from PyPI into a clean virtualenv, with the packages
> copied outside the repository so nothing resolves from the working tree. All three gates pass
> there: C1 integrity, C2 SHACL, C3 rules.
>
> The version gap is the point rather than an inconvenience. A signature that holds only under
> the tool that made it proves nothing about exit; one that holds under a later published tool,
> on a different machine, outside the repository, is the exit-is-free claim with a measurement
> behind it.

Reproduction, as the ledger records it:

    python3 -m venv venv && ./venv/bin/pip install "uofa==0.12.0"
    ./venv/bin/uofa check --pack nasa-7009b aero-cou1.jsonld

**The deliberate asymmetry**, which the amendment must keep: the rule cannot be *"verify under
the pinned version"*, because that is the version the encoder already has. *"The gap between the
signing tool and the current published tool is the only part of the check an outside verifier
cannot fake for you."*

## A5. Also landing in the same batch

- **The version bump.**
- **Part B's calibration column**, refreshed against the adjudications the aero passes add to
  the 71.
- **SF-4, SF-5 and SF-6 cited by number** where Part C references findings. They are
  schema-increment items rather than protocol items; see the appendix.

---

# Batch B — stranger-series amendments

**Every item in this batch is marked: pending C-series validation.** Each cites committed
records and none is validated by a measured completion rate, because none exists yet.

## P2-1 — the completion boundary *(pending C-series validation)*

**The rule.** An encoding is complete when **no gates are owed AND the decision has been
signed**. Taking away an unsigned export is a legitimate act and the package says honestly what
it owes; it is not completion.

**Evidence.**

`dev/donetest/RUN_26_ATTEMPT3.md` records a run that reached `SIGNABLE - all gates clear`,
authored a Conditional decision, exported the **unsigned** package, and ended voluntarily — under
a task prompt whose scan, hash-verified against `transcript-run26.json → harness.case_file_sha256`
(`9d7071342305fbd3…`, `case_file_steered: false`), *"contains **zero** occurrences of `sign`,
`signed`, `signature`, `package`, `unsigned`, `export`, `download`, `deliverable`, `wheel`,
`verify`, or `decision`."* Its whole definition of done was one sentence — *"The review is
complete when protocol-check reports no owed gates"* — and **protocol-check clears before
signing**. The note's own verdict: *"The run was scored against a criterion its prompt never
named."*

`dev/donetest/T_3_NOTE.md` records the same boundary from the other side, under a prompt that did
name it. T-3 *"did not locate 'done' early, and it did not claim to be finished"*; its closing
statement opens *"The deliverable you asked for — a signed decision — does not exist."* It
pressed the sign control and reported why it could not pass.

**Convergence with A4, stated because the two are one claim from two sides.** A4 fixes *who
checks* a finished encoding — an outside verifier, under a later published wheel, outside the
repository. P2-1 fixes *what finished means* — gates clear and the decision signed. Neither owns
the definition alone: an unsigned package cannot be verified as a signed one, and a signature
nobody can verify elsewhere is not exit. **The engagement letter given to any reviewer should
cite both rather than owning either.**

## P2-2 — temporal grammar: judgment before verdict *(pending C-series validation)*

**The rule.** The verdict is authored after the judgments it rests on, not before them. A
decision recorded while the levels it depends on stand unaffirmed is a verdict in search of its
grounds.

**Evidence**, quoted from `dev/donetest/events/run-26.jsonl` rather than recalled:

- The `Conditional` verdict was authored at **turn 335** (`action.dispatched`,
  `{"label": "Conditional"}`).
- At turns 334 and 335 the application displayed, simultaneously,
  `A-11: import has not passed --protocol-check unsigned` in a headline reading
  **`1 owed across 1 check`** — and **`18 required levels not yet affirmed or corrected`**.
- The run ended at **turn 386** at `SIGNABLE - all gates clear`: **51 turns after the verdict**.

**A precision the record forces.** The unaffirmed-levels string appears in the journal only at
turns 334–335, so the record supports *the state at the decision* and *the span to the run's
end*. It does not support a claim about how each of those 51 turns was spent, and this draft
does not make one.

**Why it must be stated as a rule.** The seat was a frontier model under no time pressure, no
budget pressure and no instruction to hurry, and it chose the inversion anyway — authoring the
verdict while eighteen of the levels beneath it were unaffirmed, and while the headline said one
gate owed. A grammar that a careful agent inverts unprompted is a grammar the protocol has not
yet stated.

**Note the second thing the same reading shows**, which belongs to P2-4: the headline said
`1 owed` while eighteen required levels stood unaffirmed. The checker's summary and the
encoding's substance disagreed at the moment of the verdict.

## P2-3 — template furniture, and the obligation that cannot be discharged *(pending C-series validation)*

**Two rules, and the second is the one that matters.**

1. **Instruction rows are never evidence and are never anchored.** A row whose text identifies
   it as template scaffolding is not encoder content, wherever it sits in the sheet.
2. **An obligation that cannot be lawfully discharged is recorded as a finding, never
   fabricated past.** The record carries the obligation, why it cannot be met, and the route that
   was declined.

**Evidence.** `docs/donetest/FIVE_SEATS_ONE_TRAP.md` (Credenza) records five unsteered sessions
meeting one fabrication affordance between 2026-08-23 and 2026-08-27, and producing five distinct
responses with **zero surviving fabrications**: anchored-then-self-caught (run 22),
excluded-by-scoping (run 24), named-as-template (run 25), filed-as-finding (run 26), and refused
with the contradiction stated (T-3).

The affordance: `Credibility Factors` carried a row reading
`Factor name (pre-filled, do not edit)`. A-6 counted it as a populated row with no anchor, so the
gate could not clear, and the application's guided path offered exactly one act against it —
anchoring it, which would assert that a real page of the source reads *"Factor name (pre-filled,
do not edit)"*. T-3's statement of the trap: *"anchoring it would assert that p.7 ¶5 of Johnson
(2020) states 'Factor name (pre-filled, do not edit)' — a fabricated citation that would satisfy
half the rule by violating the other half."*

**This defect was catalogued and open the entire time.** `docs/SCHEMA_FINDINGS.md` **SF-7**, "the
placeholder check is blind at the row where placeholders survive", whose own consequence
paragraph reads:

> A check written specifically to catch Johnson finding F-3d passes on F-3d's own case, and
> passes with an affirmative green rather than a skip. Any encoder trusting the check would ship
> a package identified by template boilerplate. This is a **vacuous green with an affirmative
> face** — the failure shape the instrument-lessons thread documents — occurring in the tool that
> exists because of the previous instance.

**Why the rule exists.** Five seats declined; the record stayed clean because the seats had
virtue. That is the dependency the protocol exists to remove. **Rule 2 gives the sixth seat a
lawful move instead of an improvisation** — and the five responses above were five different
improvisations, three of which (scoping exclusion, recovery-method annotation, ambiguity entry)
disposed of the row by routing around the obligation rather than discharging it.

## P2-4 — attestation is a separate act *(pending C-series validation)*

**The rule.** Gates clearing establishes **readiness**, not completion. No checker state
substitutes for the accountable party's signature, and no interface may present one as the other.

**Evidence.** Run 26 reached `SIGNABLE - all gates clear` and ended unsigned
(`RUN_26_ATTEMPT3.md`). And the interface that told it so had, at that time, three names for one
binary: `SIGNABLE`, `NOT SIGNABLE`, and `IN REVIEW`, where `Status.signable` is `not self.owed` —
one fact, three renderings, two of which named the same state. The Credenza Phase 0 amendment
replaced them with `READY TO SIGN` / `NOT READY TO SIGN` and added the sentence *"Signing is a
separate act and has not happened yet."*

**Why it is stated in protocol vocabulary rather than left to the interface.** The vocabulary fix
binds one product. The rule binds any interface: a checker reporting that nothing is owed has
said something about the package's readiness and nothing about whether anyone has attested to it.
P2-2's reading is the same claim seen earlier in time — a headline of `1 owed` beside eighteen
unaffirmed levels — and P2-1 is its consequence for what "done" means.

---

# Instrument-side, and therefore not amendments

> The following govern **the measurement instrument** and live in the harness specifications
> (`credenza/docs/specs/Spec_Free_Stranger_Claude_Code_Tuning_v1_0.md`, whose own header
> reads v1.1, and the run records beside it). They are
> listed here so the boundary is visible, not because they are candidates:
>
> - **seat gates** — which model drives a run, verified from the child's own account of itself;
> - **room isolation** — the tool surface a run is handed, and what it excludes;
> - **prompt versioning** — `stranger-prompt.md`, pv1 and its successors;
> - **ending derivation** — what the downloads directory testifies to, and what it does not;
> - **the A-7 affordance defect** — a confirmed open product defect in Credenza, queued for
>   deploy: the "Locate the required level →" control renders only under
>   `{% if r.required_defaulted %}`, so it vanishes once the cell is anchored and no rendered
>   route returns to it.
>
> **The protocol governs the work, whoever performs it.** These govern how the work is measured
> when the performer is a test subject. A rule that would be meaningless for a human reviewer
> working alone belongs on this side of the line.

---

# A note for whoever builds the next comparison tool

Preserved verbatim from `docs/protocol-v0_2-notes.md`. **Not a protocol item**; recorded because
it is the kind of thing that gets rediscovered expensively.

> **Tolerance is extraction latitude on the *achieved* level. Applying it to the *required*
> level masks A-7 by construction.** A ground-truth row carrying `level_tolerance: 1` means the
> extractor may land within one of the expected achieved level. Comparing the required level
> under the same tolerance hides precisely the defect A-7 exists to catch — a required level
> that was defaulted to the achieved level rather than read from the source — because the two
> then differ by zero and the comparison reports agreement.
>
> Found by writing the aero comparison tool with the tolerance applied to both fields. It
> reported zero divergences on a package with a known masked shortfall, and only reproduced the
> author's pre-registered expectations once required was compared strictly.

---

# Appendix — SF citations

Part C references findings by number. These are the schema findings this batch may cite, with
their status at drafting. All are in `docs/SCHEMA_FINDINGS.md`.

| id | title | bears on |
|---|---|---|
| **SF-4** | non-comparison evidence has no predicate of its own | A2 (D-06's mis-scoping context); Part C |
| **SF-5** | real comparators are not always URI-shaped | Part C |
| **SF-6** | a context of use has no cell for its operating envelope | A3 (COU2's envelope gap); D-11's ruling |
| **SF-7** | the placeholder check is blind at the row where placeholders survive | **P2-3**, directly |

SF-4 and SF-5 are referred to as "SF-1" and "SF-2" respectively in
`docs/Ruling_WAR05_Schema_Findings.md` and in the Johnson verdict record; that file's own
labelling note explains the renumbering. **A citation by number must name the file it is numbered
in**, or the two schemes silently merge.

**A standing process item, filed unbuilt**, from `FIVE_SEATS_ONE_TRAP.md`: *an Open schema
finding that a live product path exercises is a deploy queue entry, not a catalog entry.* SF-7 was
catalogued, precise, and Open while five sessions walked into it. Nothing was missing from its
analysis; what was missing was a transition. The finding ledger and the deploy queue need a join.

---

# The adoption condition

**v0.2 adopts in a single event, when the C-series reports.**

At that event:

1. The measured completion rate enters the **validation appendix**, as v0.1's stranger test did.
2. **Batch A lands as drafted.** It is validated by the v0.1-era evidence already committed and
   does not wait on the stranger series for anything.
3. **Batch B items are marked validated, marked unvalidated, or dropped**, each against the
   C-series evidence. An item that evidence cannot validate does not land on the strength of
   having been drafted.
4. `docs/protocol-v0_2-notes.md` gains a pointer to this draft and **stops accumulating**. New
   items after adoption open a v0.3 pile.

**Until that event, v0.1 governs everything.** Nothing in this draft edits v0.1, the pile, or any
shipped record.
