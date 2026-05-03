---
title: NAFEMS Americas 2026
description: UofA at NAFEMS Americas 2026, May 27, St. Charles, MO.
---

UofA is being presented at NAFEMS Americas 2026 in the Simulation Process and Data Management track.

<dl class="uofa-meta-strip">
  <div><dt>When</dt><dd>Wednesday, May 27, 2026 — 11:30 AM</dd></div>
  <div><dt>Where</dt><dd>Room 102, SPDM Session 1</dd></div>
  <div><dt>Conference</dt><dd>NAFEMS Americas 2026, St. Charles, MO</dd></div>
  <div><dt>Track</dt><dd>Simulation Process and Data Management</dd></div>
</dl>

## What the talk covers

The talk demonstrates UofA as the atomic evidence object inside simulation evidence pipelines. The session opens with two adjacent talks (Saha on PLM-driven CAE data governance, Ratsep on data-to-decision backbone for multidisciplinary CAE) that prime the audience with digital-thread and infrastructure framings. UofA is positioned as the per-COU artifact that flows through those pipelines with cryptographic integrity and machine-verifiable completeness.

## Live demo

The live demo runs from the frozen `v0.7.1` tag against the bundled Morrison UofA packages (hand-authored from Morrison et al. 2019). Two `uofa rules` invocations and a `uofa diff` reproduce the slide-16 output: COU 1 = 11 weakeners across 5 patterns, COU 2 = 18 weakeners across 6 patterns including 2 `COMPOUND-01` firings. Optional round-trip of the `uofa extract` → `uofa import` pipeline against a synthetic evidence folder. Optional cross-domain reproduction with the NASA-STD-7009B HPT-blade example.

Step-by-step at [/demo/](/demo/).

## Why this audience

The Simulation Process and Data Management track attracts attendees whose job is evidence flow, data governance, lifecycle integration, and digital thread — practitioners directly responsible for the last-mile problem UofA addresses. Cross-track networking targets include the Simulation Quality Assurance track and the Simulation Governance and Management Working Group.

## Reproducing the demo

```bash
git clone https://github.com/cloudronin/uofa
cd uofa
git checkout v0.7.1

pip install -e '.[excel]'

uofa rules packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld --build
uofa rules packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
uofa diff  packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
           packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
```

## Slides and Q&A material

Slides will be posted here after the talk. The most-asked-likely questions and their prepared answers are tracked in the [praxis presentation outline](https://github.com/cloudronin/uofa/blob/main/docs/NAFEMS_Presentation_Outline_v9.md) in the repository.

## Contact

If you are attending NAFEMS and want to meet during the conference, the best path is to reach out via GitHub Discussions or the email listed on the speaker page.
