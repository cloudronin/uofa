# Security Policy

## Signing key revocation — 2026-08-13

**If you hold a UofA package signed before 2026-08-13, it carries no
authenticity guarantee.**

The ed25519 private key behind the project's default trust anchor
(`keys/research.pub`) was committed to this public repository from 2026-03-29
to 2026-08-13. For that window anyone holding it could produce a package that
passed `uofa verify` with no flags.

**The key also shipped inside every published sdist** — `uofa` 0.7.0, 0.7.1,
0.8.0, 0.9.0, 0.10.0, and 0.11.0 — so cloning was not required. Anyone who ran
`pip download uofa` or installed with `--no-binary :all:` received it. Wheels
are unaffected; they carry only the public half. PyPI files are immutable, so
these sdists stay retrievable even if the releases are yanked.

The key has been rotated. Every signed artifact in this repository has been
re-signed; package hashes are unchanged, since re-signing rewrites only the
`signature` field.

| | Fingerprint — `sha256(DER SubjectPublicKeyInfo)` |
|---|---|
| **Revoked** (2026-03-29 → 2026-08-13) | `2f622df995d41f9e6bf8057e343b455debea4792a4fb5bba57ccde3f99c18617` |
| **Current** (2026-08-13 → ) | `ec22097e31ae1b4faf4556a130b673242a1994fb607fbda11a7124c9c2550f08` |

To check whether a package you hold was signed with the revoked key:

```bash
uofa verify <package> --pubkey keys/REVOKED-research-2026-03-29.pub
```

The old key remains in git history, in existing clones and forks, and in
published release artifacts. It cannot be retracted, which is why the
mitigation is rotation and disclosure rather than a history rewrite.

Full detail: [docs/security.md](docs/security.md#signing-keys).

## Reporting a vulnerability

Open a [security advisory](https://github.com/cloudronin/uofa/security/advisories/new)
rather than a public issue.

## API keys

UofA's optional LLM features read provider credentials from environment
variables at request time and never write them to config, cache, logs, or
output. See [docs/security.md](docs/security.md#api-keys-and-the-llm-layer).
