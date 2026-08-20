"""Seal an evidence folder: hash everything, read what we can, say what we did not.

This is the half of the ingest that needs no parser and no vendor software at
all. It answers three of the four questions the demo puts to an evidence
package -- integrity (digests), provenance (where the bytes came from, via a
source pin) and completeness (what is present, what is empty, what has no
reader) -- before any extractor runs.

The contract, borrowed from `keyless_extractor` and applied to bytes rather than
fields: **an artifact with no reader is sealed and reported unread, with a
reason.** It is never skipped silently and never guessed at. A manifest that
lists only what we understood would misrepresent a 405 MB archive as a small
one.

Pins are attached only when the operator supplies a real per-file URL. There is
no way to derive one from a collection URL that is honest -- a fabricated
per-file link that 404s would turn a re-derivability claim into a dead end -- so
without `--source-map` the seal carries digests and no pins, and says so.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli.furnishers import pins
from uofa_cli.solver import archive, detect

_CHUNK = 1 << 20

# Mirrors setup_bundle._sha256_of. Duplicated rather than imported: that one is
# private to the bundle installer, and a shared streaming digest is three lines.
def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class SealedMember:
    """One entry inside a sealed archive."""
    path: str
    sha256: str
    size: int
    kind: str
    read: bool
    reason: str = ""


@dataclass(frozen=True)
class SealedArtifact:
    """One top-level file in the evidence folder."""
    path: str
    sha256: str
    size: int
    kind: str
    read: bool
    reason: str = ""
    members: tuple[SealedMember, ...] = ()
    empty_dirs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass
class EvidenceSeal:
    """Everything the seal pass learned about one evidence folder."""
    root: str
    generated_at: str
    artifacts: list[SealedArtifact] = field(default_factory=list)
    source_pins: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # ── readout helpers ──
    @property
    def n_files(self) -> int:
        return len(self.artifacts)

    @property
    def n_members(self) -> int:
        return sum(len(a.members) for a in self.artifacts)

    @property
    def n_unread(self) -> int:
        return (sum(1 for a in self.artifacts if not a.read)
                + sum(1 for a in self.artifacts for m in a.members if not m.read))

    @property
    def total_bytes(self) -> int:
        return sum(a.size for a in self.artifacts)


def seal_folder(root: Path, *, source_map: dict[str, str] | None = None,
                fetched_at: str = "", digests: bool = True) -> EvidenceSeal:
    """Hash and classify every file under `root`, descending into archives once.

    `source_map` maps a top-level file name to the URL it was fetched from; only
    names present there get a pin.
    """
    root = root.resolve()
    fetched_at = fetched_at or _utc_now()
    seal = EvidenceSeal(root=str(root), generated_at=_utc_now())
    source_map = source_map or {}

    for path in _walk(root):
        rel = path.relative_to(root).as_posix()
        try:
            digest = _sha256_of(path) if digests else ""
            seal.artifacts.append(_seal_one(path, rel, digest, seal, digests=digests))
        except OSError as exc:
            seal.warnings.append(f"could not read {rel}: {exc}")
            continue

        url = source_map.get(rel) or source_map.get(path.name)
        if url and digest:
            # No `revision`: pins.py reserves it for the case where the thing
            # read and the thing addressed by the URL have different ids (an HF
            # README blob inside a repo). Here the URL addresses exactly the
            # bytes we hashed, so a revision equal to contentHash would be noise
            # asserting a distinction that does not exist.
            seal.source_pins.append(pins.artifact_pin_for_digest(
                url, digest, fetched_at=fetched_at))

    if source_map and not seal.source_pins:
        seal.warnings.append(
            "a source map was supplied but matched no file in the folder")
    return seal


def _seal_one(path: Path, rel: str, digest: str, seal: EvidenceSeal,
              *, digests: bool) -> SealedArtifact:
    head = _head(path)
    size = path.stat().st_size

    if not archive.is_archive(path):
        kind = detect.sniff(path.name, head)
        return SealedArtifact(
            path=rel, sha256=digest, size=size, kind=kind,
            read=detect.is_readable(kind),
            reason=detect.unreadable_reason(kind))

    try:
        scan = archive.scan(path, digests=digests)
    except archive.ArchiveRefused as exc:
        seal.warnings.append(f"{rel}: {exc}")
        return SealedArtifact(
            path=rel, sha256=digest, size=size, kind=detect.ZIP_ARCHIVE,
            read=False, reason=f"archive refused: {exc}")

    members = tuple(
        SealedMember(
            path=m.name, sha256=m.sha256, size=m.size, kind=m.kind,
            read=m.readable, reason=detect.unreadable_reason(m.kind))
        for m in scan.members if not m.is_dir)
    return SealedArtifact(
        path=rel, sha256=digest, size=size, kind=scan.kind, read=True,
        members=members, empty_dirs=tuple(scan.empty_dirs),
        warnings=tuple(scan.warnings))


def bundle_fields(seal: EvidenceSeal) -> dict:
    """The fields to fold into a UofA package before it is hashed and signed.

    Undeclared terms on purpose: `@vocab` in the v0.5 context already expands
    these to `uofa:<term>`, and the context is inlined into the hash preimage,
    so declaring them there would invalidate every signed package in the repo
    (furnishers/pins.py:19-25). `sourcePin` is attached through `pins.attach`
    rather than written directly, so the de-duplication rule stays in one place.
    """
    out: dict = {"artifactManifest": to_manifest(seal)}
    for pin in seal.source_pins:
        pins.attach(out, pin)
    return out


def to_manifest(seal: EvidenceSeal) -> list[dict]:
    """The manifest as plain JSON-ready dicts, keys in a stable order."""
    return [_clean(asdict(a)) for a in seal.artifacts]


def write_sidecar(seal: EvidenceSeal, path: Path) -> None:
    """Write the seal as a sidecar JSON document."""
    doc = {
        "schemaVersion": SIDECAR_SCHEMA,
        "generatedAt": seal.generated_at,
        "evidenceRoot": Path(seal.root).name,
        "artifactManifest": to_manifest(seal),
        "sourcePin": list(seal.source_pins),
        "warnings": list(seal.warnings),
    }
    path.write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n",
                    encoding="utf-8")


SIDECAR_SCHEMA = "uofa-evidence-seal/v0.1"


def summarise(seal: EvidenceSeal) -> list[str]:
    """Lines for the CLI readout. States the unread count first."""
    lines = [
        f"{seal.n_files} file(s), {seal.n_members} archive member(s), "
        f"{seal.total_bytes:,} bytes sealed",
    ]
    if seal.n_unread:
        lines.append(f"{seal.n_unread} sealed but not read (no reader) — "
                     f"listed in the manifest with a reason")
    empty = [d for a in seal.artifacts for d in a.empty_dirs]
    if empty:
        lines.append(f"{len(empty)} empty director(ies) inside archives — "
                     f"a completeness signal, not an error")
    lines.append(pins.summary({"sourcePin": seal.source_pins})
                 if seal.source_pins
                 else "no source pins — supply --source-map to make this re-derivable")
    return lines


def load_source_map(path: Path) -> dict[str, str]:
    """Read a name→URL map. JSON object, or `name<whitespace>url` per line."""
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        raw = json.loads(text)
        return {str(k): str(v) for k, v in raw.items()}
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            out[parts[0]] = parts[1].strip()
    return out


# ── internals ────────────────────────────────────────────────


def _walk(root: Path):
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path


def _head(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read(detect.HEAD_BYTES)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_JSON_KEYS = {"empty_dirs": "emptyDirs"}


def _clean(d: dict) -> dict:
    """Drop empty optional keys and camelCase the rest.

    The manifest is folded into a JSON-LD package where every other term is
    camelCase and `@vocab` turns an unrecognised key into `uofa:<key>` verbatim
    -- so a snake_case key here would mint `uofa:empty_dirs` and sit next to
    `uofa:sourcePin` looking like a different author wrote it.
    """
    out = {}
    for k, v in d.items():
        if v in ((), [], "", None):
            continue
        key = _JSON_KEYS.get(k, k)
        if k == "members":
            out[key] = [_clean(m) for m in v]
        elif isinstance(v, tuple):
            out[key] = list(v)
        else:
            out[key] = v
    return out
