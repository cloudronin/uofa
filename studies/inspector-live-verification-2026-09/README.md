# Credibility Inspector — live verification record

**Record version:** v1.1 — complete
**Recorded:** 2026-09-09
**Supersedes:** the C1 deploy verification closed 2026-08-16
(`docs/UofA_Unified_Repair_Spec_v2_1.md` §0.5). See [Correction](#correction) below.

**Revision history.** v1.0 was issued with three fields marked provisional (the
ZIP digest, the verifying CLI version, and the run time), because those exist
only on the verifying machine. v1.1 fills all three, adds the package manifest
(§3a), and adds two cross-checks the manifest made possible (§6).

A stranger should be able to repeat every line of this without asking anyone.
That is the point of recording it.

---

## 1. What was verified

That the deployed Credibility Inspector hands a visitor a signed evidence
package, and that the package verifies with the CLI against the trust anchor
that travels inside it.

This is a **deployment** claim, not a code claim. The code has been correct and
tested since 2026-08-13; the deployed container was not running it. Section 6
records why that distinction is the whole reason this file exists.

## 2. Deployed artifact under test

| Field | Value |
|---|---|
| Repository | `cloudronin/uofa` |
| Deployed commit | `d81af388d7384fbb12f94100a4af803e67c8f4b3` |
| Commit title | Merge PR #128: fix(space): pin the Space's base image, gate the trust anchor at build time, and stop promising a download the run did not produce |
| Pinned base image | `ghcr.io/cloudronin/uofa-demo-base:d81af388d7384fbb12f94100a4af803e67c8f4b3` |
| HF Space | `cloudronin/uofa-demo` |
| HF Space repo commit | `2d4c416a9cfeaf3e07bd1d32a7c9e6265f55df61` |
| Space synced at | 2026-09-08T23:40:06Z |
| Space runtime at test time | `RUNNING`, hardware `cpu-basic` |
| Live URL (direct) | https://cloudronin-uofa-demo.hf.space |
| Live URL (public) | https://uofa.net/demo |

**The image tag is immutable and that is load-bearing.** Before this commit the
Space built `FROM ghcr.io/cloudronin/uofa-demo-base:latest`. A floating tag on a
builder we do not control cannot support a claim about which code ran. The
Dockerfile committed to the Space now reads:

```
FROM ghcr.io/cloudronin/uofa-demo-base:d81af388d7384fbb12f94100a4af803e67c8f4b3
```

Confirmed by fetching
`https://huggingface.co/spaces/cloudronin/uofa-demo/raw/main/Dockerfile`
on 2026-09-09.

## 3. Package under test

| Field | Value |
|---|---|
| Filename | `uofa-pack-vv40-20260909T001330Z-3084b1c9.zip` |
| Pack profile | `vv40` (ASME V&V 40) |
| Built by the Space at | **2026-09-09T00:13:30Z** (encoded in the filename) |
| `packageHash` | `sha256:3084b1c91e30a5dd03447ce7758ff3ce359bfd9d666d07bf6802c006a8d2c9f4` |
| **SHA-256 of the ZIP** | `bbd6edc052516eb5271892d3b61bdae117e93104337d88d37447f88ae26bba96` |
| Stored at | `packages/uofa-pack-vv40-20260909T001330Z-3084b1c9.zip` |

The two digests answer different questions and are not interchangeable. The ZIP
digest identifies the delivered file. `packageHash` is the signed content hash
over `uofa.jsonld`, and it is what the signature covers. Re-zipping the same
members changes the first and not the second.

The filename timestamp is generated server-side by `_pack_filename()` in
`space/pipeline.py` at the moment the zip is written, so it is a property of the
artifact rather than of the person who downloaded it.

**Members.** `uofa.jsonld`, `report.md`, `MANIFEST.json`, `VERIFY.txt`,
`keys/uofa-issuer.pub`.

**The verifiable unit is `uofa.jsonld`, not the zip.** The trust surface never
parses archives, deliberately. `MANIFEST.json` records a digest for every member
but is not itself signed. Both facts are stated in the shipped `VERIFY.txt`.

## 3a. Package manifest, as shipped

Transcribed from `MANIFEST.json` inside the verified package.

| Field | Value |
|---|---|
| `packageHash` | `sha256:3084b1c91e30a5dd03447ce7758ff3ce359bfd9d666d07bf6802c006a8d2c9f4` |
| `signatureAlg` | `ed25519` |
| `canonicalizationAlg` | `json-sortkeys/v1` |
| `verifiableMember` | `uofa.jsonld` |
| `signedBy` | `keys/uofa-issuer.pub` |
| `pack` | `vv40` |
| `validatedWithPacks` | `["vv40"]` |
| `toolVersion` | `0.17.0` |
| `context` | `https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.8.jsonld` |
| `contextSha256` | `59029321aeb887e5ce527e6f3e97414e08c0f38bd68d02ada8a059ac5e7c5c12` |

Member digests:

| Member | SHA-256 |
|---|---|
| `uofa.jsonld` | `3526bdaeed8d75cf9500f091d6376bff3ebcf42db815d11af2eff11bda6bef85` |
| `report.md` | `f2c5ddbf4f45793f93dc58e03124ef9eb730f38b91c2281cebb322e32202bc86` |
| `keys/uofa-issuer.pub` | `ead2e1e1068f8c6da14b2c9c384e4d00d8900308ad2e406fe294330ce0edd81d` |
| `VERIFY.txt` | `89cf55c89c1301375191bd9843a7e99ab2fd2209ea08a2ca60c6fd0bf76d2938` |

**Why `contextSha256` is recorded.** Over 98% of the signed preimage is the
inlined `@context`. A verifier whose copy of the context differs from the one
the package was signed against gets `Hash match: False` and no way to tell why.
This field turns that failure into a diagnosis. It is also what makes check 5 in
§6 possible.

## 4. Trust anchor

The issuer public key that travelled inside the package, and against which the
signature was checked.

```
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAI3HnixGCDx+bCDyrU7VPxYgzD1BL2GPWqQxjZrnmDSU=
-----END PUBLIC KEY-----
```

| Fingerprint | Value |
|---|---|
| Algorithm | Ed25519 |
| SHA-256 of SPKI DER (44 bytes) | `95f8b69c1adddb03aab80f93d18ae8dd031d7d1ce3f555672bcfe8299e0fa080` |
| SHA-256 of the raw 32-byte key | `51e733221b513934b54c3e814363b4bfd0b31a4d412bb8c5b5db7b54c4883c0e` |
| SHA-256 of the PEM file as shipped | `ead2e1e1068f8c6da14b2c9c384e4d00d8900308ad2e406fe294330ce0edd81d` |
| Raw key (hex) | `2371e78b11820f1f9b083cab53b54fc588330f504bd863d6a90c6366b9e60d25` |

Reproduce any of these from the repository copy at `keys/uofa-issuer.pub`:

```bash
python3 -c "
import base64, hashlib
pem = open('keys/uofa-issuer.pub').read()
der = base64.b64decode(''.join(l for l in pem.splitlines() if '-----' not in l))
print('spki  ', hashlib.sha256(der).hexdigest())
print('rawkey', hashlib.sha256(der[-32:]).hexdigest())"
```

The copy in the package and the copy in this repository are the same bytes. The
private half exists only as a HuggingFace Space secret
(`UOFA_ISSUER_SIGNING_KEY`) and has never been in the repository;
`space/deploy_to_hf.py` refuses to upload any `.key`, `.pem`, or `.env` file.

## 5. Verification run

Run by the author on macOS, from a directory outside this repository, against a
package downloaded through the deployed web UI.

**Command, exactly as issued:**

```
uofa verify uofa-pack-vv40-20260909T001330Z-3084b1c9/uofa.jsonld \
  --pubkey uofa-pack-vv40-20260909T001330Z-3084b1c9/keys/uofa-issuer.pub
```

**Complete output:**

```
══ C1: Integrity verification (hash + signature) ══
  verified against: uofa-pack-vv40-20260909T001330Z-3084b1c9/keys/uofa-issuer.pub (named with --pubkey)
  ✓ Hash match
  ✓ Signature valid
```

| Field | Value |
|---|---|
| Executed at (UTC) | between **2026-09-09T00:13:30Z** and **2026-09-09T01:41:23Z** |
| Verifying CLI version | `uofa 0.17.0` |
| Tool version that built the pack | `0.17.0` (`toolVersion`, §3a) |
| Platform | macOS, conda `base` environment |

**On the run time, and why it is an interval.** The lower bound is the package's
server-generated creation time; the package cannot be verified before it exists.
The upper bound is a `date` reading taken in the same shell after the run:
`Tue Sep 8 18:41:23 PDT 2026`, which is `2026-09-09T01:41:23Z` at UTC-07:00. The
exact instant of the verification was not captured and is not recoverable from
the artifact. Recording the interval that *is* supported is preferable to
recording a single time that is not.

**Builder and verifier are the same version, and that is a limit on what this
shows.** Both are 0.17.0. So this run establishes that a package from the
deployed Space verifies with a matching CLI. It does not exercise
cross-version verification, which the pinned `contextSha256` exists to
diagnose. That is a separate check, not made here.

## 6. Result

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | The deployed Space **creates** a signed package | **PASS** | Five independent runs through the live app, each ending with a distinct zip filename written by the container. Reviewer readout: *"Authenticity verified: Signed (demo key)."* |
| 2 | A visitor can **download** it | **PASS** | Download control rendered visible with a real file behind it; author downloaded `uofa-pack-vv40-20260909T001330Z-3084b1c9.zip` through the browser. |
| 3 | The package's **hash** verifies | **PASS** | `✓ Hash match` (§5) |
| 4 | The package's **signature** verifies | **PASS** | `✓ Signature valid` (§5) |

Claims 3 and 4 were checked against the key shipped inside the package (§4), on
a machine that did not consult this repository. The package is therefore
self-contained: no network fetch and no trust in the hosting site is required to
check it.

**Two cross-checks against the repository, added in v1.1.** The manifest made
these possible; neither was available when v1.0 was written. Both were run
against the deployed commit `d81af38`.

| # | Check | Result |
|---|---|---|
| 5 | The `@context` the package was signed against is the repository's | **MATCH** — `59029321…c5c12` recorded in the pack equals `sha256(spec/context/v0.8.jsonld)` |
| 6 | The trust anchor shipped in the package is the repository's | **MATCH** — `ead2e1e1…dd81d` recorded in the pack equals `sha256(keys/uofa-issuer.pub)` |

Check 6 matters more than it looks. The failure this record documents was a
package that could not be built because the public key was absent from the
image. Check 6 says the key that finally travelled in the package is the same
bytes as the anchor in the repository, so the deployed image is carrying the
right key and not merely *a* key.

**Supporting checks, same commit:**

| Check | Result |
|---|---|
| Space test suite, locally | 235 pass, 3 skip |
| `validate` workflow in CI | pass, 15m38s |
| CodeQL, four analyses | pass |
| `deploy-space` workflow: `test`, `base`, `deploy` | all pass |
| Build-time trust-anchor gate in the image | pass — the image can resolve `keys/uofa-issuer.pub` as the app's own user, from the app's own working directory |
| Wheel built as the Dockerfile builds it, installed alone into an empty environment | resolves the anchor, assembles a pack, `uofa verify` passes |

<a name="correction"></a>

## 7. Correction — the August closure was premature

`docs/UofA_Unified_Repair_Spec_v2_1.md` §0.5, "C1 deploy verification (closed
2026-08-16)", recorded three checks and closed the gate. The three checks were:
deployed `space/pipeline.py` carries C1; the `Download UofA package` component
exists in the running Gradio config; the signing secret is set.

**All three could pass while a visitor received no package.** They establish that
the control exists and that signing is configured. None of them runs the flow to
the end. On 2026-09-08 the deployed Space rendered its signed branch, told the
reader to *"Download the package below and re-check it yourself"*, and offered
no download. That state satisfies every clause of §0.5.

The defect was structural, not incidental. Signing reads the **private** key
from the environment; assembling the package needs the **public** half on disk.
The two are independent and they disagreed. `_authenticity_block(signed=True)`
was decided *before* `build_downloadable_pack` ran, so the payload could carry a
real signature and no package while the renderer had no way to tell.
`build_downloadable_pack` returned a bare `None` in that case, so the container
logs showed a clean startup and nothing else.

**What is established, and what is not.** Established: the §0.5 evidence was
insufficient to support its conclusion, and the failure was observed in
production on 2026-09-08. **Not** established: that the demo was broken on
2026-08-16. The root cause was never isolated to a date — the leading
explanation is that the Space built on a stale copy of the floating `:latest`
tag, and that is unknowable retrospectively. This record does not claim the
August verification was wrong about the state of the world on the day. It claims
the checks used could not have detected the failure that later occurred, so the
closure did not carry the weight put on it.

**Two further defects in §0.5, both textual.** It names the secret
`UOFA_DEMO_SIGNING_KEY`; the code reads `UOFA_ISSUER_SIGNING_KEY`
(`space/pipeline.py`). And it describes the silent-degradation path as *"the
download control simply does not appear."* There are two such paths now, and the
second one is what occurred: the control appears, the readout says signed, and
no package exists. Commit `d81af38` makes that second path speak, in the UI and
in the container log.

**What the gate requires from now on.** A closure of this gate must include a
package produced by the web path and a CLI verification of it, with the digest
of the exact file recorded. §5 and §6 above are that evidence.

## 8. Completeness

Every field this record calls for is filled. One physical step remains, and it
does not affect any claim above.

**The ZIP is not yet in `packages/`.** It is held by the author at
`~/Downloads/uofa-pack-vv40-20260909T001330Z-3084b1c9.zip`. Its digest is
recorded in `SHA256SUMS` and in §3, so the file can be checked against this
record whenever it is placed. To place it:

```bash
cp ~/Downloads/uofa-pack-vv40-20260909T001330Z-3084b1c9.zip \
   studies/inspector-live-verification-2026-09/packages/
cd studies/inspector-live-verification-2026-09
shasum -a 256 -c SHA256SUMS      # must print: OK
```

The digest was written into `SHA256SUMS` from the author's own `shasum` output
before the file was copied, so `shasum -c` is a real check and not a
restatement: a file that does not match this record will fail it.

## 9. Exhibits

**Screenshots are supplied separately and are not reproduced here. They have not
been reviewed as part of this record** — the author holds them; nothing in
sections 1 through 7 depends on them.

| Exhibit | Content | Location |
|---|---|---|
| A | Result page showing the signed readout and the download control | supplied separately |
| B | Reviewer / Author view toggle | supplied separately |
| C | The four-step flow | supplied separately |
| D | Terminal output of the verification run | reproduced verbatim in §5 |

If any screenshot shows the zip as the thing that verifies, that is a prose
defect against a correct artifact: the verifiable unit is `uofa.jsonld` (§3).

## 10. Reproducing this

```bash
pip install uofa
# open https://uofa.net/demo, run the bundled sample, download the package
unzip uofa-pack-*.zip -d pack && cd pack
uofa verify uofa.jsonld --pubkey keys/uofa-issuer.pub
```

Cold start: the Space sleeps when idle, so first load can take up to a minute.
Inference is a hosted API call, so there is no model to warm.
