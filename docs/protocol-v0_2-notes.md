# Encoding protocol v0.2 — accumulation notes

> **CLOSED 2026-08-29. This pile stopped accumulating when v0.2 adopted.**
>
> Its items were drafted into `docs/Protocol_v0_2_Amendments_Draft.md` and adopted in a single
> event on the C-series report. The governing document is now
> **`docs/Encoding_Protocol_v0_2.md`**; Part D there records each amendment with the evidence
> that validated it, and the Validation Record appendix carries the measured completion rate.
>
> **New items opened after adoption belong in a v0.3 pile, not here.** This file is kept as the
> record of where the v0.2 items came from — the raw observations, in the words they were first
> written in, before they became rules.

**Status (historical): open pile, not a draft of v0.2.** Items land here as encodings under v0.1
surface them. Nothing here amends v0.1.

**Why a pile rather than edits.** `docs/Encoding_Protocol_v0_1.md` is committed, and the
Johnson package is signed under it as written. An encoding records the protocol version that
governed it, and that guarantee is only worth something if a governing version stops moving
once packages are signed against it. Reopening v0.1 for an improvement discovered *after*
signing would muddy exactly the version discipline the record depends on — the encoder could
no longer tell which v0.1 they read. So improvements accumulate here and land in one edit.

**When v0.2 opens.** The condition was "when the aero passes close", and **they closed on
2026-08-21**: both aero packages are adjudicated, signed and verified, and the Ch4 ledger's last
three PENDING-ENCODING rows are entered. **The gate is met and the batch is ready to write.**

The batch: the assessor rule, the D-06 worked example, the
Not-Applicable-versus-Overruled example — now a *pair* rather than a single case — the
published-wheel verification rule, and the version bump. One edit, after the encoding era ends
rather than four edits during it.

---

## Queued item 1 — the operator identity is declared, not inherited

**Ripe. Drafted below, ready to land.**

**Where it goes.** One paragraph in **A-11**, beside the import command; one check candidate
added to **F-6c**'s list in `dev/build/pilot-johnson/PROTOCOL_FINDINGS.md`.

**What raised it.** The Johnson package was signed carrying
`wasAttributedTo: …/org/claude`. `excel_mapper._operator_identity()` resolves who ran the
tool from `UOFA_ASSESSOR`, then `git config user.name`, then `$USER`. The 2026-08-20 import
ran in a container whose identity resolved to `claude`, and the value was covered by the
signature before anyone noticed it. Corrected by re-importing with `UOFA_ASSESSOR` set and
re-signing; the history is in that pilot's `RUN_LOG.md`.

**Why it is a protocol item and not a tooling one.** The value was not wrong. The mapper's R1
rule separates operator from assessor deliberately — `statedAssessor` is read from the source,
`wasAttributedTo` is whoever ran the import — and the import genuinely was machine-run. The
defect is that nobody **chose** it. This is A-2's bug with a different field: a value inherited
from the environment, frozen under a signature, that the encoder never decided. A-2 already
says the namespace is a namespace you control; the same reasoning says the operator identity is
declared.

### Draft text for A-11

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

### Draft check candidate for F-6c

> Operator identity declared rather than inherited: `UOFA_ASSESSOR` set on the import run, and
> the run log records the value. Scriptable, and it fails closed — an undeclared operator is
> indistinguishable after the fact from a declared one that happens to match the shell.

**Open question for the drafting session.** Whether `--protocol-check` can see this at all
after the fact. The package records the resolved value and not whether it was declared, so the
check may have to key on the run log rather than the package — which would make it a run-log
check like the `base_uri` one, not a package check. Worth resolving before the text lands.

---

## Queued item 2 — D-06 as a worked disposition example

**Ripe, drafting deferred to the v0.2 batch.**

**Where it goes.** Part B, the paragraph reading "Two worked examples are **v0.2 items**,
supplied after the first governed review passes."

**Why it is ready.** Part B names its own strongest candidate: "a validation activity waived by
a documented authority decision, which reads correctly whether adjudicated against source or
package." That is D-06 exactly, and it is now adjudicated rather than hypothetical:

- **Firing.** `W-AR-05` on `waived-validation-against-real-world-system-data`.
- **Verdict.** Confirmed, with an offsetRationale anchored p.19 — no RWS data exists, test data
  served as the referent, and the conservative tolerance bound plus the PRA context bound the
  model's use.
- **Why it is the good example.** It is the one firing that reads correctly on both readings:
  the source says at p.19 that no comparator data exists, and the package correctly carries
  none. Adjudicated against the package it is Confirmed; adjudicated against the source it
  would also be Confirmed. Every other firing in the pilot separates the two.
- **What it also demonstrates.** The offsetRationale lives in the disposition record and not in
  the graph, because the on-ramp has no route to `hasOffsetRationale` for a validation-result
  firing. So the example carries a second lesson: a Confirmed verdict with a real mitigating
  rationale, and the rationale housed where the template can hold it.
- **Citable as.** `dev/build/pilot-johnson/DISPOSITIONS_DRAFT.md`, D-06.

**No longer owed separately — and it grew.** The Not-Applicable-versus-Overruled example needed
a package whose decision outcome was Not accepted. Aero COU2 is now that record, signed. But the
better example is the **pair**: COU1 and COU2 share an evidence family and reach opposite
decisions, because take-off concept screening tolerates what cruise creep-life does not.
Identical weaknesses, different contexts of use, opposite defensible decisions — the tier logic
doing its one essential job. Ruled together on 2026-08-21 for exactly that reason.

---

## Queued item 3 — aero COU2 as the Not-Applicable-versus-Overruled example

**Ripe, drafting deferred to the v0.2 batch.**

**Where it goes.** Part B, the same paragraph as item 2, which states that the distinction
"needs a case from a package whose decision outcome was Not accepted, and no such record is
yet committed."

**Why it is ready.** `dev/build/encoding-prep/aero-cou2` carries
`decision: "Not accepted"`, confirmed against its pre-registered ground truth
(`tests/fixtures/extract/ground_truth/aero-cou2-nasa7009b.json`, `expected_decision.outcome`
= `Not Accepted`, qualifier "cruise validation evidence required"). It is the record Part B
said did not exist.

**What it will demonstrate.** The COU2 encoding's own numbers say why the outcome differs
from COU1's: five factors are `not-assessed` at MRL 4, which is what drives its five `W-EP-04`
firings against COU1's one. A Not-accepted decision changes which firings are *about* the
decision and which are merely about the package, and that is the axis the
Not-Applicable-versus-Overruled distinction turns on.

**Blocked on nothing but the batch.** The aero review passes must close first, which is the
same gate item 2 waits behind.

---

## Queued item 4 — sign-off verifies against the published wheel, at whatever version is current

**Ripe. One sentence, lands with the batch.**

**Where it goes.** The sign-off step, alongside the signing instruction.

**The rule.** Sign-off's verification should be run against the **published wheel at whatever
version is then current**, in a clean environment with the package outside the repository —
*precisely because* the version gap is the test. A signature that verifies only under the tool
that produced it, in the tree that produced it, demonstrates nothing about exit. One that
verifies under a later published tool, elsewhere, is the exit-is-free claim with a measurement
behind it.

**Where it came from.** Both aero packages were imported and signed under `uofa-cli 0.11.0` and
verify under the published `uofa 0.12.0` — clean virtualenv from PyPI, packages copied outside
the repository, all three gates green. The wheel bundles the packs and the Jena engine, so this
exercises C1, C2 and C3 rather than the signature alone. Recorded with its reproduction commands
in `studies/ch4_numbers/LEDGER.md` §4.5, "Exit is free, with a measurement behind it", because
the session that produced the packages is also the session that verified them and the check is
cheap enough that nobody has to take that on trust.

**Note the asymmetry this creates deliberately.** The rule cannot be "verify under the pinned
version", because that is the version the encoder already has. The gap between the signing tool
and the current published tool is the only part of the check an outside verifier cannot fake for
you.

---

## A note for whoever builds the next comparison tool

Not a protocol item; recorded here because it is the kind of thing that gets rediscovered.

**Tolerance is extraction latitude on the *achieved* level. Applying it to the *required*
level masks A-7 by construction.** A ground-truth row carrying `level_tolerance: 1` means the
extractor may land within one of the expected achieved level. Comparing the required level
under the same tolerance hides precisely the defect A-7 exists to catch — a required level
that was defaulted to the achieved level rather than read from the source — because the two
then differ by zero and the comparison reports agreement.

Found by writing the aero comparison tool with the tolerance applied to both fields. It
reported zero divergences on a package with a known masked shortfall, and only reproduced the
author's pre-registered expectations once required was compared strictly.

---

## Also landing in the same batch

- **Version bump** and the Part B calibration column refreshed against any adjudications the
  aero passes add to the 71.
- **SF-4, SF-5 and SF-6** are filed and open in `docs/SCHEMA_FINDINGS.md`. They are schema-increment
  items rather than protocol items, but v0.2's Part C cites findings by number and may want to
  cite them.
