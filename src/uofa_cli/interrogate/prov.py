"""PROV-DM provenance for SIP evidence bundles (SIP §6).

The interrogation run is a ``prov:Activity``; the surrogate, benchmark, and
reference are ``prov:Entity`` instances ``prov:used`` by the run; the evidence
bundle is a ``prov:Entity`` ``prov:wasGeneratedBy`` the run; each measurement
library is a ``prov:SoftwareAgent`` the run ``prov:wasAssociatedWith``.

This is what keeps UofA's ``W-PROV-01`` chain check from firing spuriously on
SIP-sourced evidence: every entity has an upstream edge, so the core
provenance BFS finds no orphan. ``find_orphan_entities`` lets a SIP-side test
assert that invariant *without* importing the rule engine (firewall: no shared
judgment code).

Pure stdlib — no measurement or framework dependency.
"""

from __future__ import annotations


def build_provenance(
    *,
    run_id: str,
    generated_at: str,
    surrogate_ref: str,
    benchmark_ref: str,
    reference_ref: str,
    bundle_id: str,
    libraries: list[tuple[str, str]],
) -> dict:
    """Assemble the PROV-DM block embedded in a SIP bundle.

    ``libraries`` is a list of ``(name, version)`` pairs — one SoftwareAgent
    each. Returns a plain dict (no verdict tokens; the schema's provenance
    denylist forbids any from sneaking in).
    """
    agents = [
        {"id": f"sip:agent/{name}@{version}", "type": "prov:SoftwareAgent",
         "label": f"{name} {version}"}
        for name, version in libraries
    ]
    return {
        "@context": "http://www.w3.org/ns/prov#",
        "activity": {
            "id": run_id,
            "type": "prov:Activity",
            "startedAtTime": generated_at,
            "used": [surrogate_ref, benchmark_ref, reference_ref],
            "wasAssociatedWith": [a["id"] for a in agents],
        },
        "entities": [
            {"id": surrogate_ref, "type": "prov:Entity", "role": "surrogate"},
            {"id": benchmark_ref, "type": "prov:Entity", "role": "benchmark"},
            {"id": reference_ref, "type": "prov:Entity", "role": "reference"},
            {"id": bundle_id, "type": "prov:Entity", "role": "bundle",
             "wasGeneratedBy": run_id},
        ],
        "agents": agents,
    }


def find_orphan_entities(provenance: dict) -> list[str]:
    """Return entity ids with no upstream PROV edge (the W-PROV-01 condition).

    An entity is connected if the run ``prov:used`` it or it
    ``prov:wasGeneratedBy`` the run. A well-formed SIP provenance block has no
    orphans, so W-PROV-01 stays silent at v2 ingest.
    """
    activity = provenance.get("activity", {})
    used = set(activity.get("used", []))
    run_id = activity.get("id")
    orphans = []
    for entity in provenance.get("entities", []):
        eid = entity.get("id")
        connected = eid in used or (
            entity.get("wasGeneratedBy") == run_id and run_id is not None
        )
        if not connected:
            orphans.append(eid)
    return orphans
