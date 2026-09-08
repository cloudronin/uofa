# UofA Credibility Inspector Verification and Repair Spec v1.0

**Status:** READY FOR EXECUTION  
**Owner:** Vishnu Vettrivel  
**Executor:** Codex  
**Target:** the current UofA checkout and the deployed Credibility Inspector at `https://uofa.net/demo/`  
**Purpose:** verify the committee-facing usability artifact end to end, repair reproducible defects, and produce a concise evidence handoff for the praxis.

## 1. Objective

Determine whether the Credibility Inspector actually provides the promised workflow:

1. accept public credibility-evidence documents or the bundled public sample;
2. propose the applicable standard while allowing the user to correct it;
3. expose the factor-status review step as the only human-editable assessment surface;
4. render Reviewer and Author views from the same analysis;
5. hide RDF, SHACL, JSON-LD, rule syntax, hashes, keys, and signatures from the ordinary workflow;
6. produce a downloadable UofA package when the demo issuer is configured;
7. allow that package to be independently verified with the public CLI; and
8. avoid presenting structural validity, a signature, or a model-generated summary as regulatory acceptance or human judgment.

Codex must diagnose before modifying. A fix is required only when the current implementation, deployment, test contract, or documentation fails one of the gates in Section 8.

## 2. Questions Protected by This Spec

| Question | Protected boundary |
| --- | --- |
| Does the interface hide the semantic-web machinery? | A user can complete the normal workflow without handling RDF, SHACL, JSON-LD, vocabulary terms, keys, hashes, or signature commands. |
| Can machine extraction be mistaken for reviewed evidence? | Human correction is visible and bounded, and the emitted package distinguishes extracted statuses from corrected statuses. |
| Can a demo signature be mistaken for approval? | The service may seal integrity, but it must not represent itself as a human decision-maker or regulatory authority. |
| Is the web output a real UofA artifact? | The downloaded JSON-LD package verifies using the public CLI, and tampering or the wrong trust anchor fails. |
| Do the public claims match the deployed system? | Documentation and manuscript handoff state only behavior reproduced against the deployed version. |

## 3. Authority Order

When sources disagree, use this order:

1. executable behavior and passing/failing tests;
2. the signing and attestation specifications in `docs/UofA_Spec_Attestation_Boundary_Signing_v1_0.md` and `docs/UofA_Spec_Unified_Signing_Surface_v1_0.md`;
3. the current CLI and Space implementation;
4. `docs/reviewer-render-protocol-spec.md`;
5. `docs/credibility-inspector.md`, `space/README.md`, `space/DEPLOY.md`, and the public site;
6. archived plans and repair specifications, which provide history but do not override current behavior.

Do not use an archived status statement as proof that the present deployment works.

## 4. Scope

### In scope

- `space/app.py`, `space/pipeline.py`, `space/wizard.py`, reviewer-state and rendering modules;
- Space signing, downloadable-package generation, temporary-file lifetime, and trust-anchor behavior;
- `tests/space/**` and any narrowly required CLI verification tests;
- `site/src/content/docs/demo/index.mdx`;
- `docs/credibility-inspector.md`, `space/README.md`, and `space/DEPLOY.md`;
- the deployed demo and its bundled public sample;
- reproducible screenshots of the verified flow;
- a short manuscript handoff describing what may and may not be claimed.

### Out of scope

- changing H1, H2, or H3 measurements;
- changing the frozen weakener catalog or historical experiment artifacts;
- conducting a practitioner usability study;
- redesigning the entire website or CLI;
- collecting or submitting lead-capture information;
- uploading confidential or personal evidence;
- creating, displaying, rotating, or committing persistent deployment, research, or production private keys; an ephemeral test-only key in a temporary directory is permitted for local verification;
- changing HuggingFace secrets, deploying, pushing, or opening a pull request without separate user authorization;
- editing the praxis manuscript itself.

## 5. Safety and Repository Rules

1. Read `AGENTS.md` and `CONTRIBUTING.md` before editing.
2. Record the current branch, `HEAD`, `origin/main`, and worktree status. Preserve all pre-existing changes.
3. Do not reset, clean, switch branches, delete user files, or rewrite unrelated work.
4. Use only the bundled public sample for live document testing. Do not upload user files.
5. Never print, copy, log, or persist a private signing key or provider token.
6. A missing deployment secret is an external configuration finding, not authorization to create or change one.
7. Keep pack-derived factors, patterns, and labels in their owning packs. Do not hardcode them into the Space.
8. Do not weaken a test or public statement merely to make the current deployment pass.

## 6. Execution Plan

### Phase 0: Establish the current state

Record in the results report:

- local branch and commit;
- `origin/main` commit;
- whether the current branch contains commits not on `origin/main`;
- worktree status;
- commit shown by the deployed `uofa.net` site;
- commit or revision reported by the deployed HuggingFace Space, if publicly observable;
- whether local code, GitHub `main`, the public site, and the Space are version-aligned.

If they are not aligned, test both the checked-out code and the deployed behavior. Do not describe a deployment mismatch as a code defect.

### Phase 1: Static contract audit

Trace the complete path from the UI through package creation:

1. `space/app.py`: Step 1 through Step 4/5 wiring, factor controls, view toggle, and download-button visibility.
2. `space/wizard.py`: source preparation, extraction, finalization, and temporary-directory cleanup.
3. `space/pipeline.py`: factor edits, `statusProvenance`, package construction, signing, re-verification, and download payload.
4. reviewer-state and renderer modules: one shared state and no contradictory Reviewer/Author conclusions.
5. signing specifications and CLI implementation: determine exactly what the web service is authorized to sign.
6. site and documentation: compare every public statement with the code contract.

Resolve these specific questions in writing before changing code:

- Does the web path apply a machine/issuer integrity seal only, or does it also create a decision signature?
- If a decision signature exists, which named human decision does it attest? A service key must not impersonate a reviewer.
- Which environment-variable names are current: `UOFA_ISSUER_SIGNING_KEY`, `UOFA_DEMO_SIGNING_KEY`, or both, and what distinct scope does each serve?
- Does submitting an unchanged factor prove review? Preserve the current honest distinction unless the UI records a separate per-factor confirmation act.
- Does the package-download documentation list the exact files the current ZIP actually contains?

Where documentation and code disagree, align both to the signing specifications and executable behavior. Do not invent a second attestation merely to match stale documentation.

### Phase 2: Run the local verification suite

Run the targeted suite first:

```bash
pytest tests/space/test_app_wiring.py \
  tests/space/test_pipeline.py \
  tests/space/test_reviewer.py \
  tests/space/test_reviewer_state.py \
  tests/space/test_reviewer_invariants.py \
  tests/space/test_pack_download.py \
  tests/space/test_pack_cli_roundtrip.py \
  tests/space/test_deploy_secrets.py -q
```

Then run:

```bash
pytest tests/space -q
```

If code changes touch the CLI, package format, packs, schema, or signing layer, also run the repository-required checks from `AGENTS.md`, including the Morrison smoke test and the full relevant pytest suite.

Do not treat skipped Jena-dependent tests as passes. State what was skipped and why.

### Phase 3: Verify the local web path

Run the Space locally using a temporary test issuer key created outside the repository. Never use a research or production key.

Drive the bundled sample through the full workflow and verify:

1. the privacy disclosure appears before upload;
2. the router proposes V&V 40 and allows correction;
3. every factor status is editable at the confirmation step;
4. change exactly one factor status;
5. the result defaults to Reviewer view;
6. toggling to Author view performs presentation-only work and does not rerun analysis;
7. both views remain consistent on factor status, completeness, and weakener counts;
8. the result remains explicitly indicative and does not issue an acceptance decision;
9. the download control appears only after a signed package is successfully produced;
10. the downloaded artifact records the changed factor as `corrected`;
11. unchanged factors remain `extracted`, not falsely recorded as individually confirmed;
12. starting over removes the prior downloadable file and cannot delete a path the Space did not create.

### Phase 4: Verify the package boundary

For the locally downloaded ZIP:

1. compare the actual member list with the documented member list;
2. verify every manifest digest;
3. run the exact command printed in `VERIFY.txt`;
4. require CLI return code 0, hash match, and valid signature;
5. modify one signed field and require verification to fail;
6. verify against the research/default trust anchor and require failure;
7. verify that the package and report never equate signature validity with credibility acceptance;
8. confirm that no private key, provider credential, raw uploaded evidence, or temporary working file is present in the ZIP.

The web-produced package must be accepted by the same public CLI code path used for non-web packages. A Space-only verifier is insufficient.

### Phase 5: Verify the deployed system

Use the bundled public sample against `https://uofa.net/demo/`. Do not submit an email address.

Record screenshots or machine-readable observations for:

- start and privacy disclosure;
- proposed standard and override control;
- factor-status confirmation;
- Reviewer result;
- Author result;
- package-download control;
- authenticity statement.

Download the package only if the public control is present. If present, repeat the Section 6 Phase 4 checks against the deployed artifact.

If the live result remains unsigned and the download control is absent:

1. confirm that local signed-package tests pass;
2. confirm that the deployed Space contains the expected code version;
3. identify the exact missing or mismatched configuration name without reading its value;
4. report the deployment as blocked on external configuration;
5. do not change secrets or deploy without user authorization;
6. update public documentation only if the intended deployment will remain unsigned. Do not silently downgrade the intended signed-package capability because a secret is temporarily absent.

### Phase 6: Repair only reproduced failures

For every failure, record:

| Field | Required content |
| --- | --- |
| Observation | What failed and where it was observed |
| Expected contract | Which gate or specification it violates |
| Root cause | Code, configuration, deployment drift, documentation drift, or test gap |
| Fix | Smallest change that restores the intended contract |
| Regression test | Test that fails before the fix and passes afterward |
| Scope check | Why unrelated behavior is unchanged |

Permitted repair classes:

- implementation defect with a reproducible failing test;
- missing regression coverage for a reproduced defect;
- stale or contradictory public documentation;
- site/Space version drift that can be corrected in repository configuration;
- inaccurate signing-scope or trust-language presentation;
- missing provenance distinction between extracted and corrected statuses;
- inconsistent Reviewer and Author rendering from the same analysis.

Do not broaden the feature, add new standards, tune extraction quality, or change weakener rules under this spec.

### Phase 7: Re-run and capture evidence

After repairs:

1. rerun every initially failing targeted test;
2. rerun all `tests/space` tests;
3. run any broader suite required by the touched files;
4. rebuild the site if site content changed;
5. regenerate Inspector screenshots only after the behavior is final;
6. inspect the generated images before accepting them;
7. rerun the live gate only after deployment is separately authorized and completed.

## 7. Required Outputs

Codex must produce:

1. code, test, and documentation changes required by reproduced failures;
2. `dev/build/credibility-inspector-verification/RESULTS.md`, containing:
   - tested commits and deployment versions;
   - commands run and test totals;
   - gate table from Section 8;
   - reproduced defects and fixes;
   - any external configuration blocker;
   - exact artifact and screenshot paths;
3. `dev/build/credibility-inspector-verification/MANUSCRIPT_HANDOFF.md`, containing only:
   - verified facts suitable for Chapter 1;
   - verified workflow facts suitable for Chapter 3;
   - evidence and figure references suitable for Chapter 4;
   - limitations suitable for Chapter 5;
   - prohibited claims not supported by the verification.

Do not put private configuration, tokens, secret values, or personal data into either report.

## 8. Acceptance Gates

| Gate | Pass condition |
| --- | --- |
| **CI-1 Local tests** | All applicable `tests/space` tests pass; skips and unavailable dependencies are disclosed. |
| **CI-2 Hidden complexity** | The ordinary web workflow requires no RDF, SHACL, JSON-LD, vocabulary, key, hash, or signature manipulation. |
| **CI-3 Human boundary** | Factor status is the bounded editable assessment surface; corrected statuses are attributable; unchanged statuses are not overstated as confirmed. |
| **CI-4 Shared analysis** | Reviewer and Author views derive from one analysis state and cannot disagree on common facts. |
| **CI-5 Non-acceptance** | No screen, report, package, or signature implies regulatory acceptance, model correctness, or human approval. |
| **CI-6 Package production** | With the intended demo issuer configured, the download control appears and returns the documented ZIP. |
| **CI-7 Independent verification** | The exact `VERIFY.txt` CLI command succeeds; tampering and the wrong/default trust anchor fail. |
| **CI-8 Signing scope** | The service signs only the scope it is authorized to attest; no service key impersonates a human reviewer. |
| **CI-9 Privacy and lifetime** | Disclosure precedes upload; no evidence is logged; temporary artifacts are removed within the documented lifetime. |
| **CI-10 Public consistency** | Site, Inspector documentation, deployment guide, live behavior, and manuscript handoff make the same bounded claims. |

Use `PASS`, `FAIL`, or `BLOCKED`. `BLOCKED` is allowed only for a dependency outside the checkout, such as an unavailable deployment secret or missing deployment authorization. A local code or test failure is `FAIL`, not `BLOCKED`.

## 9. Final Done Gate

The task is complete only when:

- every locally testable acceptance gate passes;
- every reproduced defect has a regression test;
- the public documentation matches the corrected behavior;
- the live deployment either passes the full bundled-sample and package-verification flow or is explicitly recorded as blocked on a named external configuration or authorization requirement;
- the manuscript handoff distinguishes implemented interface behavior from unperformed practitioner usability validation; and
- no deployment, secret change, push, or pull request has occurred without explicit user authorization.
