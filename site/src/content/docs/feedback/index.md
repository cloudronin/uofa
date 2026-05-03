---
title: Feedback and free weakener report
description: Run UofA on your own simulation evidence (no data leaves your environment), share what works and what does not, and shape the v0.6 catalog.
---

If you came here from the NAFEMS Americas 2026 talk, thank you. Three things to consider, in order of how much they help.

## 1. Run UofA on your own evidence

This is the most useful thing you can do. The CLI is fully local. No data leaves your environment.

```bash
pip install 'uofa[excel]'
uofa init my-assessment
# fill in my-assessment/my-assessment-cou1.jsonld with your own COU
uofa sign my-assessment/my-assessment-cou1.jsonld --key my-assessment/keys/my-assessment.key
uofa check my-assessment/my-assessment-cou1.jsonld
```

The `uofa check` output is a personalized weakener report. It tells you which credibility gaps the rule engine surfaces in your evidence package, with severity and affected node IDs. Critical and High firings are the ones to address before submission.

If your existing documentation is in Word and Excel rather than JSON-LD, the [Excel on-ramp](/start/from-excel/) takes you from a filled workbook to a signed JSON-LD package in one command. If your existing documentation is in source PDFs, the [live demo walkthrough](/demo/) shows how `uofa extract` ingests an evidence folder and produces the workbook for you.

## 2. Tell me what gaps you see

The most useful kind of feedback is concrete. "Pattern W-EP-04 fires on a case where I would not flag the evidence as weak" is more actionable than a thumbs-up or a thumbs-down. The Phase 2.5 catalog refinement that produced the current pattern set was driven entirely by exactly that kind of feedback.

Two channels:

| Channel | Best for |
|---|---|
| [GitHub Discussions](https://github.com/cloudronin/uofa/discussions) | Public technical discussion, pattern requests, integration questions |
| Email ([support@uofa.net](mailto:support@uofa.net)) | Confidential or company-specific feedback |

## 3. Tell me what would make UofA useful for your pipeline

Two questions I am actively trying to answer.

> **What would it take for UofA packages to flow through your existing PLM, SPDM, or CAE pipeline?**
> What format conversion, what API surface, what metadata bridge?

> **What domain pack would unlock the most value for you?**
> The current catalog ships `vv40` (FDA medical device, ASME V&V 40) and `nasa-7009b` (NASA aerospace). DO-178C, automotive ISO 26262, ISO 42001 AI Management Systems, and an SBKF aerospace shell-buckling pack are on the post-defense roadmap. Tell me which one first.

A short note via email or a GitHub Discussion thread is enough. I read every one.

## What you will see in the v0.6+ catalog

Six Tier 1 candidate patterns are gated on Phase 3 expert validation. They are not pre-shipped. They are: `W-EV-01` (stale validation data), `W-EV-02` (inadequate validation metric), `W-REQ-01` (ambiguous acceptance criterion), `W-CX-01` (configuration divergence), `W-AR-06` (eliminative argumentation absent), `W-AR-07` (sustained defeater without residual-risk justification). Three or more confirmed by the expert panel ships the next minor.

If any of these resonate with patterns you have seen in real submissions, that is exactly the practitioner signal the Phase 3 protocol is designed to capture. Drop a note.

---

*This is an open-source academic project. The code and schema are both Apache-2.0. There is no sales contact and no funnel. The single best way to support the work is to run it on your own evidence and tell me what you find.*
