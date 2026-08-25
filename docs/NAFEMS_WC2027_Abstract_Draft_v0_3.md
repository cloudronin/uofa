# NAFEMS World Congress 2027 — Abstract Draft v0.3

**Title (set):** From Evidence to Argument: Human-in-the-Loop, AI-Powered Credibility Inspection for Simulation-Based Decisions

**Deadline:** November 9, 2026 · Decisions mid-December 2026 · Full paper January 31, 2027 · Congress April 25–28, 2027, Vancouver

**v0.3 change:** end-to-end demo is Nagaraja + OSF evidence folder (was NTRS 20200002832, now backup).

---

## Abstract (~400 words)

Simulation credibility standards — ASME V&V 40, NASA-STD-7009B — define what to assess, but not whether an evidence package will survive regulatory review. The Unit of Assurance (UofA) is an open-source framework that packages credibility evidence as signed, machine-verifiable units and runs a weakener rule catalog detecting quality gaps no single query or manual check can surface. That core answers whether an assessment was adequately conducted and whether the package is intact. It cannot answer whether the model meets its engineering requirement, or whether the evidence actually supports the claim being made — both are settled by reading prose, and corpus analysis found roughly 200 review judgments that depend on exactly that.

This presentation introduces the Credibility Inspector, new work built on UofA that closes both gaps under an explicit division of labor between AI and human judgment. AI-assisted extraction reads the source evidence and proposes credibility-factor statuses; extraction is fast but never authoritative. A practitioner adjudicates at the single editable surface in the workflow, and every factor records whether its status came from extraction or human correction — the judgment is bounded, visible, and cryptographically part of the signed record. Out come a signed evidence package and a weakener report, with no RDF, SHACL, or JSON-LD exposed to the user.

Two new layers extend the UofA core. A requirement layer, borrowing the SysML v2 frame (subject, assume/require constraints, pinned content-hashed references to the requirement authority), makes satisfaction checkable: a reported value outside its bound, two requirements over the same quantity with disjoint satisfying sets, an evaluation outside its assumed applicability region. An argument layer records explicit inference steps between evidence and assurance claims, mapped to GSN and SACM, with rules detecting quantity gaps, scope undercoverage, modality substitution (a necessary condition used as sufficient), and compliance appeals — defects in the reasoning step, not in the evidence.

We demonstrate the full path end to end on a published V&V 40 credibility study and its publicly archived simulation evidence: the paper and the authors' original ANSYS project files and solver logs go in; human-adjudicated extraction, a signed Unit of Assurance carrying the proprietary simulation artifacts as sealed, hash-verified evidence, and a weakener report come out — without ever needing the software that produced the simulation. We report measurement at corpus scale: a 4,556-package adversarially generated evidence corpus adjudicated by a three-judge ensemble (99.5% raw agreement, Fleiss' κ 0.77), aggregate planted-defect detection of 35/35 conformant mutants (Wilson lower bound 0.90), and a 97.1% clean rate on negative-control holdouts. One open-source CLI, medical device and aerospace packs, both regulated domains.

---

## The end-to-end example — Nagaraja (decided)

**Primary: Nagaraja pedicle screw** ([paper](https://www.sciencedirect.com/science/article/pii/S1046202324000665), [OSF evidence folder](https://osf.io/n4pjz/overview) with ANSYS Workbench project files, simulation logs, and data). Already encoded; demo already sketched (2026-08-16 script: extract → protocol-governed human review → signed import → rules → Inspector, ~7 min live). Why it wins for this audience:

- The OSF folder contains the artifacts NAFEMS attendees actually produce — solver project files and logs — and the demo's central claim ("verify integrity, provenance, completeness, and known weaknesses without opening the proprietary files") answers the first question every regulated-industry simulation audience asks.
- Same asset, fourth use: defense exhibit, MDIC session, baked-in Inspector example, NWC27 demo.
- Reference-by-hash to OSF sidesteps the redistribution license question entirely (per the sketch's own closing check).

**Deltas the NWC version needs beyond the 2026-08-16 sketch:**

1. **Layer beat.** The sketch predates both layers. Add one scene moment where a requirement-layer check (the paper's acceptance criteria projected as bounds) and an argument-layer rule fire on Nagaraja; if Nagaraja's prose doesn't carry a clean argument-layer instance, the layer demonstration stays on Morrison (rows 16/54 for argument, RH < 1 for requirement) and the e2e run stays pure workflow.
2. **Tier label.** Nagaraja is a development-tier document under Decision 7. The demo shows the workflow; any extraction-quality figure quoted near it is labeled development, never held-out.

**Backups / secondary material:** NTRS 20200002832 (Johnson surrogate paper — cleanest single-document self-labelling bundle, public domain, aerospace; keeps the §4.1 encoding synergy if run through the protocol). IMM VV&C family (richest NASA 7009 multi-document trail, but slides-heavy). Morrison stays as the layer-motivation anchor and the cross-COU divergence case.

## Numbers — what the ch4 ledger supports citing

| Figure | Value | Ledger status | Abstract? |
|---|---|---|---|
| Adjudicated corpus size | 4,556 packages | entered, re-derivable | yes |
| Judge agreement | raw 99.5%, Fleiss' κ 0.7685 | entered | yes |
| Planted-defect detection, aggregate | 35/35, Wilson [0.9011, 1.0] | entered | yes |
| NC clean rate | 97.1% (166/171), v0.5.15.1 holdout | entered | yes |
| CE recall | 75.9% (287/378) | entered, gate FAIL at ≥80% | paper only, with gate context |
| Extraction F1 0.964 | dev, synthetic | margin over its own null is +0.004 | no — can't travel without its null; extraction quality shown live, not claimed numerically |
| Real-document extraction | 3/33 held-out | entered | no — it's the argument *for* HITL, and the workflow framing carries it |
| 76.4% / 75.4% (2026 slides) | M5 development corpus | superseded by ledger figures | dropped |

Ledger rule carried forward: abstract rounds, full paper pins every figure to catalog version and artifact.

## Scope promised

All three layers: UofA core (packaging, integrity, weakener catalog), requirement layer, argument layer — the three-question frame (adequately conducted? / meets requirement? / evidence supports claim?) is the novelty claim versus the 2026 talk. Both layer specs share piece 1 (quantity identity); build window is post-defense through January 31. Demo build is ~1 day per the sketch and sequences after the mutation measurement run (case-study packages frozen until then).
