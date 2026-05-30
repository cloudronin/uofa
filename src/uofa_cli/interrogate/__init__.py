"""Surrogate Interrogation Probe (SIP) — a measurement instrument.

SIP loads a pre-trained physics-based surrogate, exercises it against a
supplied benchmark and reference set, computes interrogation measurements, and
emits a signed, provenance-bearing evidence bundle. The UofA surrogate pack
ingests that bundle and checks it for completeness and consistency. The
practitioner and the COU acceptance criteria render the credibility decision.

**SIP never emits a verdict.** This is the firewall (``SIP_Evidence_Contract_Spec``
§8, ``AGENTS.md`` §12), enforced at schema validation, in the command surface,
and by a CI guard — all keyed off the single forbidden-token list in
:mod:`uofa_cli.interrogate.forbidden`.

Only the stdlib is imported at module top level. Heavy measurement dependencies
(numpy, conformal/UQ libraries, model frameworks) are imported lazily inside the
functions that need them, so ``import uofa_cli.interrogate`` never pulls in torch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_interrogation(
    *,
    adapter_ref: str,
    benchmark_path: str | Path,
    reference_path: str | Path,
    scope: dict,
    output_path: str | Path,
    key_path: str | Path | None = None,
    bundle_id: str | None = None,
    generated_at: str | None = None,
    sip_version: str | None = None,
    seed: int | None = None,
    context_path: Path | None = None,
) -> dict:
    """Full SIP pipeline: load → measure → assemble → validate → (sign) → write.

    Returns ``{"bundle", "output_path", "signed", "hash", "signature"}``.
    ``scope`` is the parsed declared-scope dict (subject, trainingEnvelope,
    evaluationPoint/Region, declaredPhysicsConstraint, surrogateUQMethod,
    parentModelSnapshot, completeness). Validation against the frozen contract
    happens before any signature — a forbidden field never gets signed.
    """
    import importlib.metadata
    import uuid
    from datetime import datetime, timezone

    from uofa_cli.interrogate import loader, orchestrator, packager
    from uofa_cli.interrogate import prov as prov_mod
    from uofa_cli.interrogate.adapter import load_adapter

    bundle_id = bundle_id or f"sip-bundle-{uuid.uuid4().hex[:12]}"
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if sip_version is None:
        try:
            sip_version = importlib.metadata.version("uofa")
        except Exception:
            sip_version = "0.0.0"

    adapter = load_adapter(adapter_ref)
    benchmark = loader.load_benchmark(Path(benchmark_path))
    reference = loader.load_reference(Path(reference_path))

    measurements, measurement_provenance, measured_families = orchestrator.run_measurements(
        adapter, benchmark, reference, scope, seed=seed
    )

    scope_subject = scope.get("subject", {})
    subject = {
        "surrogateId": scope_subject.get("surrogateId", "unspecified"),
        "modelVersion": scope_subject.get("modelVersion", "unspecified"),
        "surrogateType": scope_subject.get("surrogateType", "data-driven-emulator"),
        "modelFingerprint": scope_subject.get("modelFingerprint", "unspecified"),
        "adapterRef": adapter_ref,
    }

    declared_scope: dict[str, Any] = {}
    if "trainingEnvelope" in scope:
        declared_scope["trainingEnvelope"] = scope["trainingEnvelope"]
    if "evaluationPoint" in scope:
        declared_scope["evaluationPoint"] = scope["evaluationPoint"]
    if "evaluationRegion" in scope:
        declared_scope["evaluationRegion"] = scope["evaluationRegion"]
    declared_scope["declaredPhysicsConstraint"] = scope.get("declaredPhysicsConstraint", [])
    # Carry per-field scope provenance from `interrogate init` into the bundle
    # (Addendum A14.1) so the downstream reviewer sees where each field came from.
    if "scopeProvenance" in scope:
        declared_scope["scopeProvenance"] = scope["scopeProvenance"]

    completeness = {
        "fieldsPresent": measured_families,
        "fieldsDeliberatelyOmitted": scope.get("completeness", {}).get(
            "fieldsDeliberatelyOmitted", []
        ),
    }

    libraries = sorted({
        (p["producedBy"]["library"], p["producedBy"]["version"])
        for p in measurement_provenance
    })
    provenance = prov_mod.build_provenance(
        run_id=f"sip:run/{bundle_id}",
        generated_at=generated_at,
        surrogate_ref=f"sip:surrogate/{subject['surrogateId']}",
        benchmark_ref=f"sip:benchmark/{Path(benchmark_path).name}",
        reference_ref=f"sip:reference/{Path(reference_path).name}",
        bundle_id=f"sip:bundle/{bundle_id}",
        libraries=list(libraries),
    )

    bundle = packager.assemble_bundle(
        bundle_id=bundle_id,
        sip_version=sip_version,
        generated_at=generated_at,
        subject=subject,
        declared_scope=declared_scope,
        measurement_provenance=measurement_provenance,
        measurements=measurements,
        completeness=completeness,
        provenance=provenance,
        parent_snapshot=scope.get("parentModelSnapshot"),
    )

    output_path = Path(output_path)
    if key_path is not None:
        hash_hex, sig_hex = packager.emit_and_sign(
            bundle, output_path, Path(key_path), context_path=context_path
        )
        signed_bundle = json.loads(output_path.read_text(encoding="utf-8"))
        return {"bundle": signed_bundle, "output_path": output_path,
                "signed": True, "hash": hash_hex, "signature": sig_hex}

    packager.emit_unsigned(bundle, output_path)
    return {"bundle": bundle, "output_path": output_path,
            "signed": False, "hash": None, "signature": None}
