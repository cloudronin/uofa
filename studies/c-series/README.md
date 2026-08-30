# C-series — the ten counted packages

The artifacts behind Chapter 4 §4.6 and the Validation Record appendix of
`docs/Encoding_Protocol_v0_2.md`.

**Archived: https://doi.org/10.5281/zenodo.22167996** (deposit version
`c-series-v1`). Cite the DOI for the manuscript; cite this directory for a reader
who wants to run the checks.

**Two DOIs, and which to cite.** `10.5281/zenodo.22167996` is the **version
DOI** — this release, these exact bytes, and what a manuscript should cite so
the reference cannot move under it. `10.5281/zenodo.22167995` is the **concept
DOI**, which always resolves to the latest version of this supplement; cite it
only where "the supplement, whatever its current version" is what is meant.

**These are published so a stranger can check the claim without asking anyone.**
Each package verifies from the anchors it ships, against the wheel on PyPI, on a
machine that has never seen this repository.

    pip install uofa
    unzip packages/C-1.zip -d C-1 && cd C-1
    uofa verify uofa.jsonld \
        --pubkey keys/uofa-issuer.pub \
        --decision-pubkey keys/demo-reviewer.pub

Thirty checks — three per package, ten packages — all of which pass.

## What is here

    packages/C-*.zip     the ten counted signed packages
    C_SERIES_PREREGISTRATION.md   filed and committed BEFORE C-1 launched
    C_SERIES_REPORT.md            the rate, composition table, void ledger
    notes/C_*_NOTE.md             one per counted run
    notes/C_5_VOID.md             the voided run, with its cause

`C-5` is absent from `packages/` deliberately: it **signed** and was **voided**
on a tool-surface breach, so its package is excluded from the numerator. The
void is ledgered rather than hidden — see `notes/C_5_VOID.md`. `C-11` is its
replacement, which is why the numbering runs to eleven for ten counted runs.

## SHA-256, as pinned in the numbers ledger

    C-1   ee5bc8205072178b…    C-2   0cda46d8125b878f…    C-3   261e24149645ab57…
    C-4   13748e34a9607c6f…    C-6   9f25f626cd76dfbe…    C-7   a67aba1189e96c5e…
    C-8   f73f90555e208bf2…    C-9   2e7e37d9ddedc32b…    C-10  eab4672f4777553e…
    C-11  8bb21486794a7f55…

Full digests: `SHA256SUMS`. Verify with `shasum -a 256 -c SHA256SUMS`.

## What these packages do and do not establish

Each package's own `SIGNING.txt` states its limits, and those words govern rather
than any summary here:

> The public keys travel inside this zip, so the package is SELF-CONSISTENT
> without fetching anything: you can check that these keys signed these bytes,
> and that nothing has changed since.
>
> They do NOT bind either key to a real-world party. That is custody's job … Here
> both identities are labeled **demonstration fixtures**.

So the signatures demonstrate independent-attestation **mechanics** — two scopes,
two keys, verified separately — and bind to real-world parties only when custody
does. That is the reference ladder, and publication is an offer of verification
rather than a claim of endorsement.

**The `credenza.review` namespace is a minted identifier under A-2's rule, not a
live endpoint.** It will not resolve in a browser, and is not meant to.

**Scope, as pre-registered.** The signatures attest completion of the governed
review **with dispositions recorded where evidence was unrecoverable** — nine of
the ten explicitly decline to claim judgment. They are not assertions that
achieved levels meet requirements. Out of scope: extraction soundness, the source
paper's assessment quality, and human-reviewer executability. This is a
model-reviewer claim.

The encoded source is `NTRS-20200002832-Johnson-2020.pdf`, a public NASA
technical report.
