"""judge_ready_bundle.tgz reader (spec v1.5 §2.1).

Reads the Phase 2 → Phase 3 handoff bundle: a gzipped tar containing a
manifest.json, per-package .jsonld + .outcome.json pairs under packages/,
and coverage/{matrix,summary}.csv. Validates the manifest against an
embedded JSONSchema and yields (package_jsonld, outcome_dict) pairs to
the judge runner.

Path-traversal safe: tarfile members with absolute paths or `..`
components are rejected. On Python ≥3.12 this is enforced via
`tarfile.data_filter`; older versions fall back to manual member-name
validation.
"""

from __future__ import annotations

import json
import sys
import tarfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover — surfaced via informative error
    jsonschema = None


# Manifest schema is embedded here (rather than loaded from disk) so the
# reader is self-contained: callers don't need to also locate
# specs/judge_manifest_schema.json. Mirrors spec §2.1 manifest example.
_MANIFEST_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "phase2_spec_version",
        "generated_at",
        "generator_provenance",
        "package_count",
        "coverage_class_distribution",
    ],
    "properties": {
        "phase2_spec_version": {"type": "string"},
        "generated_at": {"type": "string"},
        "generator_provenance": {
            "type": "object",
            "required": ["generator_model"],
            "properties": {
                "generator_model": {"type": "string"},
                "phase2_tag": {"type": "string"},
            },
        },
        "package_count": {"type": "integer", "minimum": 0},
        "coverage_class_distribution": {"type": "object"},
        "source_taxonomies": {"type": "array", "items": {"type": "string"}},
        "experimental_factors": {"type": "object"},
    },
}


class BundleError(Exception):
    """Raised when a bundle is malformed (manifest missing, package mismatch, etc.)."""


class UnsafeBundleError(BundleError):
    """Raised when a tar member has an unsafe (path-traversal) name."""


@dataclass(frozen=True)
class BundleEntry:
    """One (package, outcome) pair extracted from the bundle."""

    case_id: str
    package: dict  # the JSON-LD payload
    outcome: dict  # the .outcome.json payload


@dataclass
class Bundle:
    """In-memory handle to an opened bundle.

    Use as a context manager or call `.close()` explicitly. The reader
    holds the tarfile open across `iter_entries()` calls so we don't pay
    the gzip-decode cost twice.
    """

    path: Path
    manifest: dict
    _tarfile: tarfile.TarFile

    def __enter__(self) -> "Bundle":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._tarfile.close()

    def iter_entries(self) -> Iterator[BundleEntry]:
        """Yield (case_id, package_jsonld, outcome_dict) for every package.

        Iteration order matches the alphabetic order of `.jsonld` member
        names in the tar, which equals classifier output order (per
        `outcomes.csv` row order, spec v1.8 §10.3).
        """
        # Build a set of jsonld stems → outcome counterpart paths so we
        # can detect orphans up front.
        jsonld_members: dict[str, str] = {}
        outcome_members: dict[str, str] = {}
        for name in sorted(self._tarfile.getnames()):
            if not name.startswith("judge_ready_bundle/packages/"):
                continue
            base = name[len("judge_ready_bundle/packages/") :]
            if base.endswith(".outcome.json"):
                stem = base[: -len(".outcome.json")]
                outcome_members[stem] = name
            elif base.endswith(".jsonld"):
                stem = base[: -len(".jsonld")]
                jsonld_members[stem] = name

        # Detect orphans: every .jsonld must have an .outcome.json sibling.
        orphan_packages = set(jsonld_members) - set(outcome_members)
        orphan_outcomes = set(outcome_members) - set(jsonld_members)
        if orphan_packages or orphan_outcomes:
            raise BundleError(
                f"bundle has orphaned packages/outcomes: "
                f"jsonld_without_outcome={sorted(orphan_packages)}, "
                f"outcome_without_jsonld={sorted(orphan_outcomes)}"
            )

        for stem in sorted(jsonld_members):
            package = self._read_json_member(jsonld_members[stem])
            outcome = self._read_json_member(outcome_members[stem])
            yield BundleEntry(case_id=stem, package=package, outcome=outcome)

    def _read_json_member(self, name: str) -> dict:
        f = self._tarfile.extractfile(name)
        if f is None:
            raise BundleError(f"could not extract {name!r} from bundle")
        return json.loads(f.read())


def open_bundle(path: Path) -> Bundle:
    """Open a judge_ready_bundle.tgz, validate the manifest, and return a Bundle.

    Raises:
        BundleError: manifest missing or fails JSONSchema validation.
        UnsafeBundleError: a tar member has an unsafe (path-traversal) name.
        FileNotFoundError: bundle path does not exist.

    The caller is responsible for closing the Bundle (use as a context
    manager or call .close()).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"bundle not found: {path}")
    if jsonschema is None:
        raise ImportError(
            "jsonschema is required to read bundles; "
            "run `pip install uofa[judge]`"
        )

    tf = tarfile.open(path, "r:gz")
    try:
        _validate_member_safety(tf)
        manifest = _load_manifest(tf)
        jsonschema.validate(manifest, _MANIFEST_SCHEMA)
    except Exception:
        tf.close()
        raise

    return Bundle(path=path, manifest=manifest, _tarfile=tf)


def _validate_member_safety(tf: tarfile.TarFile) -> None:
    """Reject tar members with unsafe paths.

    On Python ≥3.12 we can use `tarfile.data_filter` directly. On older
    versions we replicate the data-filter checks manually: no absolute
    paths, no `..` components, no symlinks/hardlinks/device files.
    """
    if sys.version_info >= (3, 12):
        # data_filter is part of the stdlib starting 3.12 (PEP 706); it
        # raises tarfile.FilterError on unsafe members. We reuse it for
        # validation by passing every member through and discarding the
        # filtered result.
        for member in tf.getmembers():
            try:
                tarfile.data_filter(member, "/tmp")  # dest_path is unused for validation
            except tarfile.FilterError as e:
                raise UnsafeBundleError(f"unsafe tar member: {e}") from e
        return

    # Python 3.10 / 3.11 fallback: manual checks.
    for member in tf.getmembers():  # pragma: no cover — only reached on <3.12
        name = member.name
        if name.startswith("/") or name.startswith("\\"):
            raise UnsafeBundleError(f"absolute path in tar: {name!r}")
        if any(part == ".." for part in Path(name).parts):
            raise UnsafeBundleError(f"path-traversal in tar: {name!r}")
        if member.islnk() or member.issym() or member.isdev():
            raise UnsafeBundleError(f"non-regular member in tar: {name!r}")


def _load_manifest(tf: tarfile.TarFile) -> dict:
    name = "judge_ready_bundle/manifest.json"
    try:
        f = tf.extractfile(name)
    except KeyError:
        raise BundleError(f"bundle missing manifest at {name!r}")
    if f is None:
        raise BundleError(f"could not extract manifest from bundle")
    try:
        return json.loads(f.read())
    except json.JSONDecodeError as e:
        raise BundleError(f"manifest is not valid JSON: {e}") from e
