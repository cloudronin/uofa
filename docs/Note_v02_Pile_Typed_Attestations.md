# Note for Claude Code — add to the v0.2 protocol pile

Date: 2026-08-31
From: author (via ruling in conversation)
Action: append the following entry to the v0.2 pile document (dev/protocol/v0_2_pile.md or wherever the pile lives — locate, don't create a second pile).

---

## v0.2 pile entry: Typed attestations and actor-typed act classes

**1. Typed attestation texts become protocol law.**
v0.1 requires a signature but does not state *what the signer attests*. Since the signature is the liability interface — the point where legal accountability plugs into the record — the scope of each attestation belongs in the protocol text, not in whichever app renders the button. v0.2 states, as law:

- **Human signature = attestation of judgment.** Fixed declaration text to the effect of: "the dispositions, ambiguity closures, and decision recorded under my key are my judgments, made under protocol vN as the ledger records."
- **Machine signature = attestation of process, never judgment.** Fixed declaration text to the effect of: "this package was produced by [actor] under protocol vN, profile and boundary-set as versioned, acts as ledgered." A machine attestation can never satisfy any gate that requires judgment.
- These are **distinct signature types**, not one type with different keys. A package's verification output names which types are present; a package carrying only process attestations reports itself as such, loudly (the PROPOSAL status from the product design, promoted to protocol vocabulary).
- Multi-party packages (joint declarations, n-party routing) compose these types; the preparer/owner/reviewer/quality role texts from the product specs are absorbed here as the standard type vocabulary.

**2. §1d generalized to actor-typed act classes, carrier-neutrally.**
The division of powers stated once, in n-party form: acts are classed (mechanical / judgment / terminating); actors are typed (human / machine); machine actors of any number, in any configuration (solo agent, navigator/judge pipeline, overseer), may perform mechanical acts and author drafts, and may never perform judgment-class or terminating acts. Oversight actors may flag, halt, and annotate — acts of attention, never verdict. Machine consensus is an ensemble, not a judgment; no quorum exception exists.

**3. Placement.**
Both items fold into the already-ruled carrier-neutral restatement (normative core + tool bindings). The **commentary layer** of the restatement carries the rationale — the three-reasons argument (capability: empirical, ages; economics: structural, drifts; liability: constitutive, permanent — machines cannot be held to answer, so cannot promise, so cannot sign), written as law-with-its-reasons per the rule-to-failure spine's method, extended to rule-to-principle. Source text for the rationale: the "Why the human seat is permanent" paragraph in Credenza_Vision_Marketplace_Note.md.

**Sequencing:** post-defense, with the v0.2 restatement. Nothing here touches v0.1, which is frozen for the praxis; nothing here blocks or changes any current build (the product's joint-declaration and PROPOSAL machinery already conform to what this entry will make law).
