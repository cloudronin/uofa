"""Load and validate SIP evidence bundles against the frozen contract schema.

The schema lives on disk at ``specs/sip_evidence_bundle_schema.json`` (the G3
contract freeze) and is the single integration boundary between SIP and the
UofA surrogate pack. Validation runs at bundle-emit time (before signing) and
again at UofA-ingest time (v2).

``jsonschema`` is an optional dependency shipped in the ``[interrogate]`` extra;
an import error surfaces an install hint rather than a bare ``ModuleNotFound``.

The schema must be reachable both from a source checkout and from an installed
wheel. ``paths.find_repo_root()`` returns the wheel-bundled ``_data/repo``
snapshot when running from a pip install, so ``specs/`` must be force-included
into the wheel (``pyproject.toml``) for the firewall's schema layer to run for
real users — see ``AGENTS.md`` §12.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.paths import find_repo_root

SCHEMA_FILENAME = "sip_evidence_bundle_schema.json"


def schema_path(root: Path | None = None) -> Path:
    """Return the on-disk path to the SIP evidence-bundle schema."""
    root = root or find_repo_root()
    return root / "specs" / SCHEMA_FILENAME


def load_schema(root: Path | None = None) -> dict:
    """Load and parse the SIP evidence-bundle schema.

    Returns a fresh dict each call (no caching) so callers may freely mutate
    the result without poisoning a shared instance.
    """
    return json.loads(schema_path(root).read_text(encoding="utf-8"))


def validate_bundle(bundle: dict, root: Path | None = None) -> None:
    """Validate ``bundle`` against the SIP contract schema; raise if invalid.

    Raises ``jsonschema.ValidationError`` when the bundle violates the
    contract — including carrying any forbidden verdict field (the firewall).
    Callers must invoke this *before* signing so a forbidden field can never be
    given a signature.
    """
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "jsonschema is required to validate SIP evidence bundles. "
            "Install with: pip install uofa[interrogate]"
        ) from exc
    jsonschema.validate(bundle, load_schema(root))
