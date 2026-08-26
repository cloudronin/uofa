# INV-12 — Does the demo Space build the signed pack internally?

Status: **CLOSED — the parent-spec correction now applies to v2.0 as well**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent C1, C2

---

# ADDENDUM — re-investigated against parent spec v2.0

**The correction carries forward unchanged, and is now more urgent.** v2.0 is dated
2026-08-16 but restates C1 verbatim from v1.1 — including the open INV-12
dependency, the "Gap: signed pack download not surfaced" line in the must-have
coverage map (§0), the 2-4h estimate, and the "wrap vs build follows" framing.

C1 shipped on **2026-08-13** (`535dfd52`, PR #54), three days before v2.0 was
dated. Every clause of C1's done-gate is met with test evidence (32 tests run
locally, all passing), and the emittability rule in C1 clause 2 is enforced by
[tests/space/test_emittability.py](tests/space/test_emittability.py).

Three edits to v2.0, all textual:

| Location | Says | Should say |
|---|---|---|
| §0 must-have 2 row | "Gap: signed pack download not surfaced" | surfaced and CLI-verifiable since 2026-08-13 |
| §1a ordering | "C1 (after INV-12)" | C1 complete; C2 unblocked |
| §C1 + effort roll-up | 2-4h, contingent on INV-12 | 0h; workstream C drops to C2's 1-2h |
| Investigation register | INV-12 Open | CLOSED |

Net effect on the roll-up: **workstream C falls from 3-6h to 1-2h**, and the
program total from 44-61h to roughly 41-57h.

**C2 is the live item and gains one dependency from this finding.** C2 promises
screenshots of "the pack-download step once C1 lands" — it has landed, so the
screenshots can be taken now. Two details from the original finding belong in C2's
text: the verifiable unit is `uofa.jsonld`, not the zip (the trust surface never
parses archives, deliberately), and `MANIFEST.json` is not itself signed. Both are
stated in the shipped `VERIFY.txt`; if C2's figures imply the zip is what verifies,
that is a prose defect against an artifact that is already correct.

The cold-start note (C1 clause 3) remains the one unfound item — see the original
coverage statement.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Headline

**The question is moot: C1 is already built, merged, tested, and surfaced in the
UI.** The Space does not merely construct the pack internally — it signs it,
re-verifies it through the same call `uofa verify` makes, packages it as a zip,
and exposes it behind a `gr.DownloadButton`.

This landed in commit `535dfd52`, *"feat(space): signed pack download from the
Credibility Inspector (C1) (#54)"*, **2026-08-13 17:49:46 −0700** — one day after
the parent spec v1.1 was dated (2026-08-12) and therefore not reflected in it.

**Parent-spec correction:** C1's 2-4h estimate should be struck, not confirmed.
The remaining C1 work is zero. C2 (manuscript rendering of the Inspector,
including the pack-download step) is unaffected and still open.

## Stage table (spec step 2)

Traced through `space/pipeline.py` (1,022 lines) and `space/app.py`.

| Stage | Package-construction code | Verdict |
|---|---|---|
| Read + route | `document_reader.read_corpus`, `space/router.py` | absent (correctly) |
| Factor extraction | `uofa_cli.llm_extractor.extract`, run in a child process with a hard timeout ([pipeline.py:153-193](space/pipeline.py)) | absent |
| Import mapping | `uofa_cli.excel_mapper.map_to_jsonld` — **the CLI's own JSON-LD graph assembly**, reached via `card_bundle.result_to_import_dict` ([pipeline.py:34-41](space/pipeline.py)) | **invoked** |
| C2 SHACL | `uofa_cli.commands.check.run_structured` ([pipeline.py:264-290](space/pipeline.py)) | **invoked** |
| C3 rules | `uofa_cli.commands.rules.run_structured` ([pipeline.py:293-319](space/pipeline.py)) | **invoked** |
| Signing | `uofa_cli.package_policy.sign_package` ([pipeline.py:718-719](space/pipeline.py)) | **invoked** |
| Re-verification | `uofa_cli.integrity.verify_file` — explicitly "the same call `uofa verify` makes" ([pipeline.py:663-680](space/pipeline.py)) | **invoked** |
| Pack assembly | `build_downloadable_pack` → zip of `uofa.jsonld`, `report.md`, `MANIFEST.json`, `keys/demo-reviewer.pub`, `VERIFY.txt` ([pipeline.py:584-642](space/pipeline.py)) | **invoked** |
| Reviewer / Author render | `space/reviewer.py` + `uofa_cli.report_state` | shared with CLI `uofa report` |
| PDF | browser print | n/a |
| **Download surfaced?** | `gr.DownloadButton`, shown only when the run actually produced a signed pack ([app.py:407-415, 681-686](space/app.py)) | **yes** |

Ordering inside `_sign_and_pack` is documented as load-bearing and is correct:
rules run *before* signing (so the Jena engine never sees hash/signature fields),
then sign, then re-verify with the real pubkey, then build the payload last so the
reviewer readout states a true hash rather than asserting "signed" pre-emptively
([pipeline.py:694-707](space/pipeline.py)).

## Fork-or-shared verdict (spec step 3)

**Shared, and mechanically defended.**

The module docstring states the design rule directly: *"The Space never shells out
to the CLI; it reuses the same functions the CLI wraps"*
([pipeline.py:1-16](space/pipeline.py)). Every construction step above resolves to
a `uofa_cli.*` import.

More than that, the parent spec's emittability rule — *"if the demo path can
produce a pack the CLI path would reject, that is a defect"* — has been turned
into a **test suite**: [tests/space/test_emittability.py](tests/space/test_emittability.py),
whose docstring quotes the rule and states its own reason for existing:
*"'we call the same function' is an easy thing to say and an easy thing to stop
being true."*

The one piece of Space-only logic is `result_to_import_dict`, a documented adapter
that skips the fragile Excel round-trip. It lives in `uofa_cli.card_bundle`, not in
`space/`, so the CLI and the Space share it.

### Done-gate evidence (spec step 4)

Ran locally on this worktree:

```bash
python -m pytest tests/space/test_pack_download.py tests/space/test_pack_cli_roundtrip.py tests/space/test_emittability.py -q
```

Result: **32 passed** in 23.33s (Python 3.12, conda base).

`tests/space/test_pack_cli_roundtrip.py` is literally titled *"The done-gate:
`uofa verify` (CLI) passes on a pack produced by the web path"* and asserts four
directions, all passing:

| Test | Asserts |
|---|---|
| `test_cli_verify_passes_on_a_web_produced_pack` | `uofa verify uofa.jsonld --pubkey keys/demo-reviewer.pub` succeeds |
| `test_cli_verify_fails_on_a_tampered_pack` | tamper is caught |
| `test_cli_verify_fails_against_the_wrong_trust_anchor` | a demo pack does **not** verify as a research pack |
| `test_cli_verify_without_pubkey_does_not_silently_trust_the_demo` | no implicit trust |
| `test_cli_check_needs_no_pack_flag` | the package records its own profile |

C1's stated done-gate ("pack downloads from the demo; `uofa verify` (CLI) passes on
a pack produced by the web path; walkthrough updated") is met on the first two
clauses with test evidence. The third (committee-facing walkthrough) is a doc
task; see §"Residual" below.

## Key handling (spec step 5)

Investigated because the parent spec predicted it would be the sticking point. It
was handled, and the handling is stricter than the spec asked for.

- The demo key is supplied as a **deployment secret**, never a repo file:
  `UOFA_DEMO_SIGNING_KEY` (PEM in env, preferred) or `UOFA_DEMO_SIGNING_KEY_FILE`
  (path, for local dev) ([pipeline.py:476-480, 540-555](space/pipeline.py)).
- The in-memory PEM is preferred for a stated threat reason: *"the hosted process
  serves user downloads out of a temp directory, and a private key on that
  filesystem is one path-traversal bug away from being one of them."*
- `space/deploy_to_hf.py` **hard-refuses any `*.key` in its upload payload**
  ([pipeline.py:478](space/pipeline.py) comment; enforced in
  [tests/space/test_deploy_secrets.py](tests/space/test_deploy_secrets.py)).
- **Degradation is graceful, not silent**: with no key configured the Space returns
  the unsigned readout it always showed, and the reviewer view branches on
  `signed` ([pipeline.py:376-401, 711-716](space/pipeline.py)).
- The security-model position is addressed head-on in the shipped `VERIFY.txt`
  ([pipeline.py:503-511](space/pipeline.py)): the key is named a **DEMONSTRATION
  issuer key**, and the text states that a valid signature means only that the file
  is unmodified — *"It does not mean the evidence was reviewed, accepted, or
  endorsed."* A separate test asserts a demo pack cannot verify against the
  research trust anchor.

This is the demo-scoped-key answer the item asked whether to accept, already
implemented with the disclosure attached.

## Escalation check

The escalation criterion was *"the Space pipeline is a fork with behavioral
divergence from the CLI path."* **Not triggered** — it is shared, and divergence is
guarded by a dedicated test file.

## Residual (not C1, worth naming)

1. **The zip is packaging, not the verifiable unit.** `uofa verify` stays a
   single-file command; the trust surface never parses archives, deliberately
   ([pipeline.py:461-468](space/pipeline.py)). Any committee-facing walkthrough must
   say "unzip, then verify `uofa.jsonld`" — which `VERIFY.txt` does. If C2's
   screenshots imply the *zip* is verified, that is a prose defect.
2. **The cold-start note** (parent C1 step 3, "first load up to a minute; GPU
   sleeps") was not found in any committee-facing walkthrough; see the coverage
   statement. That is a C2 doc item, ~10 minutes.
3. `MANIFEST.json` is deliberately **not** signed; only `uofa.jsonld` is
   ([pipeline.py:530-532](space/pipeline.py)). Correct, but it is the kind of detail
   a reviewer will ask about, so C2 should state it.

## Coverage statement

**Searched.** `space/` in full: file listing plus `pipeline.py` (read
lines 1-120 and 455-745 in detail, grepped whole), `app.py` (grepped for
`download`, `DownloadButton`, `gr.File`, `zip`), and the module inventory of all 16
`space/*.py`. Test suite `tests/space/` enumerated (21 files); three run and
passing. Git: `git log --follow -- space/pipeline.py`, and
`git log -S build_downloadable_pack -- space/` to date the feature. Greps for
`zipfile`, `sign`, `signature`, `hash`, `run_structured`, `canonical` inside
`space/`.

**Search terms derived from the question's own definition** (package construction =
graph assembly + provenance + signing), not from where such code was last seen:
`map_to_jsonld`, `sign_package`, `verify_file`, `canonicalize`, `MANIFEST`,
`pubkey`, `zipfile`, `DownloadButton`.

**Not searched / not verified.**
- **The live Space was not exercised.** All evidence is source + local tests. The
  deployed `cloudronin/uofa-demo` may run an older revision than this worktree;
  `space/deploy_to_hf.py` exists but no deployment log was checked. **Recommend the
  author confirm the deployed revision includes `535dfd52` before citing the live
  demo in C2.**
- The committee-facing walkthrough / cold-start note was searched for only under
  `site/src/content/docs/demo/` filenames and not read end to end; item 2 above is
  therefore reported as "not found", not "absent".
- `space/Dockerfile`, `start.sh`, and the HF Space runtime configuration were not
  read, so nothing here speaks to whether `UOFA_DEMO_SIGNING_KEY` is actually set in
  the hosted environment. If it is unset in production, the live demo silently
  serves the unsigned readout and the C1 gate is met in code but not in the artifact
  a committee member would see. **This is the one thing worth checking by hand.**
