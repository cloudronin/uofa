# Ch3: the Credibility Inspector as usability layer (insertion prose)

Workstream C2, position 5 of the repair spec. Written in manuscript register for
direct insertion into Chapter 3. The companion figure list and captions are in
[`ch4-inspector-figures.md`](ch4-inspector-figures.md).

*Source: [`credibility-inspector.md`](credibility-inspector.md), which states the
claim at length and records what has and has not been demonstrated;
[`studies/inspector-live-verification-2026-09/`](../studies/inspector-live-verification-2026-09/)
for the deployment evidence; deployed commit `d81af38`.*

Every UI claim below was checked against the deployed Space at that commit on
2026-09-09, not against the source. The distinction is not pedantry: for three
weeks the two disagreed, and the disagreement was invisible from the repository.

---

## §3.x The usability layer

The formalism this praxis develops is a signed RDF graph validated by SHACL
shapes and evaluated by a rule engine. The practitioners it is for do not write
RDF, do not read SHACL, and have no reason to acquire either. A method that
requires them to is a method with no adopters, and an evidence-packaging format
whose only users are its author demonstrates nothing about packaging evidence.

The Credibility Inspector is the response. It is a web interface over the same
toolchain the command line drives, and its design claim is deliberately narrow
and deliberately falsifiable: **a practitioner can produce and read a Unit of
Assurance without learning what one is.**

The claim fails if any of four things leaks into the flow. The user must never be
required to know that the artifact is a graph or that the graph is RDF; to read
or write a vocabulary term; to understand SHACL, the rule engine, or what a
weakener is in order to act on one; or to handle a key, a hash, or a signature in
order to obtain a verifiable package. Stating the falsifiers first is what
separates hidden complexity from asserted simplicity, which is otherwise a
comfortable thing to claim and an easy thing to fake.

What replaces all of it is four steps. The user supplies evidence, or takes the
bundled sample. A keyword router proposes a standard and the user may overrule
it. The tool shows what it read from the evidence, factor by factor, and the user
confirms or corrects it. The result appears as plain language, in one of two
readings, with the assurance package offered as a download. Routing, mapping to a
graph, structural validation, rule evaluation, and signing all happen, and none
of them is surfaced as a task.

The user's total obligation is one thing: **confirm or correct the credibility
factor statuses the tool read.**

### Where judgment enters, and why the interface is the disclosure

That single obligation is the same sentence as the human-adjudication disclosure
in §3.y, approached from the other side: the confirm step is not merely the
user's only task but the interface's entire adjudication surface, so the place
where human judgment enters this method is a numbered step of a four-step flow
rather than an unmarked pass over the data.

Four properties make that a disclosure rather than a description. The step is
**bounded**, because factor status is the only user-mutable field and
rationales, levels, entities, validation results and the decision record cannot
be edited.
It is **visible**, occupying a numbered step that cannot be skipped. It is
**identical to the study workflow**, because the interface calls the same
functions as the command line and there is no demonstration-only adjudication
path. And it is **recorded**: each factor in the emitted package carries a
`statusProvenance` value marking the status as the model's or the human's.

The last of those was added because the disclosure was otherwise unfalsifiable
from the artifact. Before it, a human correction silently replaced the extracted
value, and a reader holding a downloaded package could not tell which statuses a
model produced and which a person changed. The claim was true of the software and
uncheckable from its output, which is the same defect this praxis attributes to
prose-borne evidence generally.

The field records `extracted` or `corrected`, and deliberately not `confirmed`.
The interface pre-fills every status and the user submits the form, so an
unchanged factor is one the user may have read and agreed with, or may have
scrolled past. "13 of 13 confirmed" would assert thirteen judgments where the
interaction evidences at most one judgment about the set.

### The package is the point

The interface's last step hands the user the assurance package itself, not a
rendering of it. The download contains the signed graph with its provenance, a
report, a manifest, the public key, and verification instructions; the graph is
the artifact and the rest are convenience copies. A recipient checks it with two
commands and needs neither this site nor its author to be trustworthy for the
check to mean something.

This is the clause that makes the usability claim more than presentational. An
interface that hid the formalism and returned only a readable verdict would have
hidden the evidence along with the complexity. The user does not see JSON-LD; the
user leaves holding it.

Two constraints keep that honest. The web path and the command-line path are the
same code, enforced by a test that drives one input through both and fails if the
digests diverge, so the interface cannot quietly become a fork that emits
packages the verifier would reject. And the demonstration signs with a
demonstration issuer key that is deliberately not the default trust anchor, so
`--pubkey` is required and a package from the demonstration cannot be mistaken
for a formally issued one. A valid signature there means the file is unmodified
since the tool produced it. It is not a review and not an acceptance decision,
and the readout says so in the same panel that displays the signature, because a
green badge beside a content hash invites precisely the inference this work
exists to discourage.

### What it cost, and what remains unshown

Responsiveness was bought with a disclosure. Extraction runs on a hosted model,
which is what lets an analysis complete in seconds rather than minutes, and it
means documents uploaded to the demonstration are sent to a third party to be
read. The Space stores nothing and logs no document, but the text leaves it. The
notice sits above the file picker rather than below it, on the reasoning that a
disclosure a user meets after uploading is not a disclosure.

Two limits bound what this section claims.

**The interface claim is argued, not user-tested.** The argument runs from what
the interface requires of a user, and the falsifiers above are what make that
argument checkable. No usability study was conducted and no external practitioner
has completed the flow under observation. What is demonstrated is that the
formalism *can* be hidden behind an upload-and-confirm interaction while still
delivering the formal artifact, not that practitioners find it easy.

**The claim is about the interface, not about the extraction being correct.**
Roughly one in five extracted factors carries no status at all in the evaluation
runs, and status is the field the completeness computation depends on. That is a
gap in the extraction path, it is unresolved, and no amount of interface design
addresses it.
