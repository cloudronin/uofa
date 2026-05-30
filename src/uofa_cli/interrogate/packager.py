"""Evidence packager + signer (SIP §3 component 4).

Assembles the §5 contract dict and signs it. Validation against the frozen
schema runs BEFORE signing, so a forbidden verdict field can never be given a
signature — the firewall, enforced at the packaging seam. Signing reuses
UofA's ``integrity.sign_file`` (ed25519 / SHA-256), so a SIP bundle verifies
with the same ``uofa verify`` machinery as any UofA package.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.interrogate.schema import validate_bundle

SCHEMA_VERSION = "sip-evidence-bundle/v0.1"


def assemble_bundle(
    *,
    bundle_id: str,
    sip_version: str,
    generated_at: str,
    subject: dict,
    declared_scope: dict,
    measurement_provenance: list,
    measurements: dict,
    completeness: dict,
    provenance: dict,
    parent_snapshot: dict | None = None,
) -> dict:
    """Build the SIP §5 bundle dict (unsigned). ``parent_snapshot`` is optional."""
    bundle = {
        "bundleId": bundle_id,
        "sipVersion": sip_version,
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "subject": subject,
        "declaredScope": declared_scope,
        "measurementProvenance": measurement_provenance,
        "measurements": measurements,
        "provenance": provenance,
        "completeness": completeness,
    }
    if parent_snapshot is not None:
        bundle["parentModelSnapshot"] = parent_snapshot
    return bundle


def emit_unsigned(bundle: dict, output_path: Path) -> Path:
    """Validate (firewall) then write the unsigned bundle JSON."""
    validate_bundle(bundle)
    output_path = Path(output_path)
    output_path.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output_path


def emit_and_sign(
    bundle: dict, output_path: Path, key_path: Path, *, context_path: Path | None = None
) -> tuple[str, str]:
    """Validate (firewall), write, then sign the MEASUREMENT scope. Returns (hash, sig).

    Validation precedes signing so a forbidden field is rejected before any
    signature is computed. Signs over the measurement bundle (excluding any
    ``engineerDecision``) via ``signing.sign_measurement``, so the measurement
    signature keeps verifying after an engineer decision is appended (Addendum
    A6). At emit there is no decision, so this equals a whole-doc signature.
    ``context_path`` is unused — the SIP bundle carries no top-level ``@context``.
    """
    emit_unsigned(bundle, output_path)
    from uofa_cli.interrogate.signing import sign_measurement
    return sign_measurement(Path(output_path), Path(key_path))
