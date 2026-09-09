# Ch4: Credibility Inspector figures and walkthrough (insertion prose)

Workstream C2, position 5 of the repair spec. The Chapter 3 subsection these
figures illustrate is in
[`ch3-inspector-usability-layer.md`](ch3-inspector-usability-layer.md).

**The figures are generated, not taken.** `dev/tools/scripts/capture_inspector_screenshots.py`
drives the deployed Space with the bundled public sample and writes all six into
`docs/img/inspector/`. Re-running it after any interface change regenerates the
chapter's figures against whatever is actually deployed, so a figure cannot
quietly describe a version of the interface that no longer exists. It costs one
metered analysis (about $0.006) because it drives the real pipeline, and it uses
the bundled sample rather than uploaded evidence so every figure shows data a
reader can reproduce.

**Status: five of the six figures exist; the sixth is outstanding.** `01`
through `05` were captured against the deployed Space on 2026-09-09 and are
committed in `docs/img/inspector/`. `06-package.png` is not, because the first
capture run failed at the package control.

That failure has since been traced and the script fixed. The control lived
inside the Reviewer panel, and the script was switching to the Author view for
figure `05` and toggling back for `06`. The round trip was the fragile step. It
now captures `06` without leaving the Reviewer panel at all. Both outcomes were
then exercised against a locally run instance of the app: a signed run writes
all six figures, and an unsigned one writes the other five, names the cause, and
leaves a full-page screenshot to look at.

Neither the script nor the deployment was at fault in the way first suspected.
The deployed Space was producing packages throughout, confirmed by driving it
directly.

Run it again and the sixth figure should land:

---

## Figures

| Figure | File | Shows |
|---|---|---|
| 4.x | `01-start.png` | Step 1: the start screen, with the processing disclosure above the file picker |
| 4.x+1 | `02-confirm-standard.png` | Step 2: the router's proposed standard, open to correction |
| 4.x+2 | `03-confirm-status.png` | Step 3: the confirm step, the interface's entire adjudication surface |
| 4.x+3 | `04-reviewer.png` | Step 4: the Reviewer reading |
| 4.x+4 | `05-author.png` | Step 4: the same analysis, Author (Gap-Finder) reading |
| 4.x+5 | `06-package.png` | Step 4: the signed package, offered as a download |

### Captions

**Figure 4.x, step 1.** The user supplies evidence, names a public model card,
or takes the bundled sample. The disclosure that documents are read by a hosted
model sits above the file picker, not below it: a disclosure a user meets after
uploading is not a disclosure.

**Figure 4.x+1, step 2.** A keyword router reads the corpus and proposes ASME
V&V 40 or NASA-STD-7009B. The proposal is shown as a choice the user may
overrule, not as a decision already taken.

**Figure 4.x+2, step 3.** Every factor the tool read, with its status, offered
for confirmation or correction. This is the only user-mutable field in the flow
and the whole of the interface's adjudication surface, which is what makes the
human-adjudication disclosure in §3.y a claim about a visible artifact rather
than about the author's intentions. Corrections are recorded in the emitted
package as `statusProvenance: corrected`; untouched factors record `extracted`,
never `confirmed`.

**Figures 4.x+3 and 4.x+4, step 4 in two readings.** One analysis, rendered for
two readers: a Reviewer deciding whether to trust a finished package, and an
Author looking for what to fix. Neither view exposes a vocabulary term, a shape,
or a rule identifier as something the user must interpret.

**Figure 4.x+5, the package.** The download emits the assurance package itself:
the signed JSON-LD graph with its provenance, a report, a manifest, the public
key, and verification instructions. The user reaches it without handling a key, a
hash, or a signature, which is the fourth falsifier in §3.x, and leaves holding
the formal artifact rather than a rendering of it.

**A note on the last figure.** It is captured at viewport size rather than full
page, because a full-page shot of a three-thousand-pixel readout does not show a
control. The capture script also asserts the control is present and fails if it
is not. See below.

---

## Where these figures come from, and one thing the capture now guards

The download control's absence is silent. In September 2026 the deployed Space
rendered a signed readout, told the reader to download the package below, and
offered nothing: no error in the interface, no line in the container log. The
code in the repository was correct throughout; the deployed image was not running
it. Three checks recorded as closing this gate in August all passed while a
visitor received nothing, because none of them ran the flow to its end.

The capture script now waits for the download control by name before writing
Figure 4.x+5, so it raises rather than producing a figure of a missing button.
The figure generation and the regression check are the same act, which is the
only arrangement that survives being forgotten.

The deployment evidence is recorded in
[`studies/inspector-live-verification-2026-09/`](../studies/inspector-live-verification-2026-09/),
with the verified package stored beside it. That record carries the deployed
commit, the pinned image tag, the package digest, the issuer key fingerprints,
and the verification command with its output.

---

## Committee-facing walkthrough

For anyone opening [uofa.net/demo](https://uofa.net/demo) directly.

1. **Give it up to a minute on first load.** The Space sleeps when idle and wakes
   on the first request. Inference is a hosted API call, so there is no model to
   download and the wake is short, but the first page can still be slow. A blank
   or slow first load is the cold start, not a fault.
2. **Use "Try a sample evidence set."** Public data, no upload needed, and it is
   the same input the figures above were captured from.
3. **Accept or change the proposed standard.** Either is a valid path; the
   proposal is a suggestion.
4. **Look at step 3 before moving past it.** It is the only place a person can
   change anything, which is the point of the section it illustrates.
5. **Switch between Reviewer and Author** on the result. Same analysis, two
   readings.
6. **Download the package and check it yourself**, which needs nothing from this
   site:

   ```bash
   pip install uofa
   unzip uofa-pack-*.zip -d pack && cd pack
   uofa verify uofa.jsonld --pubkey keys/uofa-issuer.pub
   ```

   Expect `✓ Hash match` and `✓ Signature valid`. `--pubkey` is required on
   purpose: the demonstration signs with a demonstration key that is not the
   default trust anchor, so a package from it cannot be mistaken for a formally
   issued one.

**What uploading costs, if you upload your own document.** The text is sent to a
hosted model to be read. The Space stores nothing and logs no document, but the
text leaves it. The bundled sample avoids the question entirely.
