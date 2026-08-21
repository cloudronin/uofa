# Encoding protocol v0.2 — accumulation notes

**Status: open pile, not a draft of v0.2.** Items land here as encodings under v0.1 surface
them. Nothing here amends v0.1.

**Why a pile rather than edits.** `docs/Encoding_Protocol_v0_1.md` is committed, and the
Johnson package is signed under it as written. An encoding records the protocol version that
governed it, and that guarantee is only worth something if a governing version stops moving
once packages are signed against it. Reopening v0.1 for an improvement discovered *after*
signing would muddy exactly the version discipline the record depends on — the encoder could
no longer tell which v0.1 they read. So improvements accumulate here and land in one edit.

**When v0.2 opens.** When the aero passes close. The natural batch is: the assessor rule, the
D-06 worked example, the Not-Applicable-versus-Overruled example from aero COU2, and the
version bump — one edit after the encoding era ends, rather than four edits during it.

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

**Still owed alongside it.** The Not-Applicable-versus-Overruled example, which needs a package
whose decision outcome was Not accepted. Aero COU2 is the candidate and its outcome is not yet
recorded. This is why the batch waits.

---

## Also landing in the same batch

- **Version bump** and the Part B calibration column refreshed against any adjudications the
  aero passes add to the 71.
- **SF-4, SF-5 and SF-6** are filed and open in `docs/SCHEMA_FINDINGS.md`. They are schema-increment
  items rather than protocol items, but v0.2's Part C cites findings by number and may want to
  cite them.
