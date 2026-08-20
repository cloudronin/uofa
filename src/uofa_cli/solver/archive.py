"""Walk a Workbench archive without unpacking it.

A `.wbpz` is a plain zip of the `.wbpj` and its `_files` tree. The evidence
folder this was built for holds three of them, one of which is 405 MB, so
"extract to a temp dir and walk that" is not an option: it needs disk we may not
have, it leaves proprietary bytes lying around after a crash, and it is slower
than reading the members we actually want.

Everything here streams. `scan` hashes each member in fixed-size chunks and
keeps only metadata; `read_member` is the single place that materialises bytes,
and it refuses anything over `MAX_MEMBER_READ`.

Three guards, because an evidence archive is untrusted input even when it comes
from a journal's supplementary material:

  * **path traversal** -- a member named `../../etc/x` or `/etc/x`. We never
    write members out, so this cannot overwrite anything today, but the member
    name reaches a manifest that other tools will join against paths.
  * **member count** -- a directory bomb.
  * **expansion** -- the central directory is a claim, not a fact, so the
    declared total is checked first AND a running budget is enforced while
    reading.

Nested archives are recorded, never descended into. Depth-1 keeps the walk
bounded and the manifest readable; a Workbench project has no legitimate reason
to nest one.
"""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.solver import detect

MAX_MEMBERS = 50_000
MAX_TOTAL_UNCOMPRESSED = 8 * 1024**3      # 8 GiB
MAX_MEMBER_READ = 64 * 1024**2            # 64 MiB into memory, ever
_CHUNK = 1 << 20


class ArchiveRefused(Exception):
    """The archive tripped a guard. Carries the reason for the operator."""


@dataclass(frozen=True)
class Member:
    """One entry inside an archive. Metadata only -- never the bytes."""
    name: str
    size: int
    compressed: int
    is_dir: bool
    kind: str
    sha256: str = ""

    @property
    def readable(self) -> bool:
        return detect.is_readable(self.kind)


@dataclass
class ArchiveScan:
    """The result of walking one archive."""
    path: Path
    kind: str
    members: list[Member] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def by_kind(self, kind: str) -> list[Member]:
        return [m for m in self.members if m.kind == kind]

    def find(self, *suffixes: str) -> list[Member]:
        low = tuple(s.lower() for s in suffixes)
        return [m for m in self.members
                if not m.is_dir and m.name.lower().endswith(low)]

    @property
    def empty_dirs(self) -> list[str]:
        """Directory entries with no members beneath them.

        The `-NoResults` archives carry nine of these -- every `MECH/` folder --
        which is how the stripped solver directory shows up structurally. Worth
        reporting: an empty solver directory is a completeness fact.
        """
        files = [m.name for m in self.members if not m.is_dir]
        out = []
        for m in self.members:
            if not m.is_dir:
                continue
            prefix = m.name if m.name.endswith("/") else m.name + "/"
            if not any(f.startswith(prefix) for f in files):
                out.append(m.name)
        return out


def is_archive(path: Path) -> bool:
    """True when `path` is a zip container (Workbench archive or otherwise)."""
    try:
        with path.open("rb") as f:
            return f.read(4).startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
    except OSError:
        return False


def scan(path: Path, *, digests: bool = True) -> ArchiveScan:
    """Walk `path`, classifying and (by default) hashing every member.

    Raises `ArchiveRefused` when a guard trips. Individual unreadable members
    degrade to a warning and a blank digest -- one corrupt entry must not cost
    the operator the other eighty-four.
    """
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        _check_declared(infos)
        kind = detect.sniff(path.name, _head_of_file(path),
                            zip_names=[i.filename for i in infos])
        result = ArchiveScan(path=path, kind=kind)
        budget = MAX_TOTAL_UNCOMPRESSED

        for info in sorted(infos, key=lambda i: i.filename):
            name = _safe_name(info.filename)
            if name is None:
                result.warnings.append(
                    f"skipped member with unsafe path: {info.filename!r}")
                continue

            if info.is_dir():
                result.members.append(Member(
                    name=name, size=0, compressed=info.compress_size,
                    is_dir=True, kind="directory"))
                continue

            try:
                member_kind, digest, read = _read_member(
                    z, info, name, budget, digests=digests)
            except ArchiveRefused:
                raise
            except Exception as exc:
                result.warnings.append(f"could not read member {name}: {exc}")
                result.members.append(Member(
                    name=name, size=info.file_size,
                    compressed=info.compress_size, is_dir=False,
                    kind=detect.OPAQUE_BINARY))
                continue

            budget -= read
            result.members.append(Member(
                name=name, size=info.file_size, compressed=info.compress_size,
                is_dir=False, kind=member_kind, sha256=digest))

    return result


def read_member(path: Path, name: str) -> bytes:
    """Materialise one member. Refuses anything over `MAX_MEMBER_READ`."""
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(name)
        if info.file_size > MAX_MEMBER_READ:
            raise ArchiveRefused(
                f"{name} is {info.file_size:,} bytes, over the "
                f"{MAX_MEMBER_READ:,}-byte read cap")
        with z.open(info) as f:
            return f.read(MAX_MEMBER_READ + 1)[:MAX_MEMBER_READ]


def head_of_member(path: Path, name: str, n: int = detect.HEAD_BYTES) -> bytes:
    """Cheap peek at a member, for classification without a full read."""
    with zipfile.ZipFile(path) as z, z.open(name) as f:
        return f.read(n)


# ── internals ────────────────────────────────────────────────


def _check_declared(infos: list[zipfile.ZipInfo]) -> None:
    if len(infos) > MAX_MEMBERS:
        raise ArchiveRefused(
            f"archive declares {len(infos):,} members, over the "
            f"{MAX_MEMBERS:,} cap")
    declared = sum(i.file_size for i in infos)
    if declared > MAX_TOTAL_UNCOMPRESSED:
        raise ArchiveRefused(
            f"archive declares {declared:,} uncompressed bytes, over the "
            f"{MAX_TOTAL_UNCOMPRESSED:,} cap")


def _read_member(z, info, name, budget, *, digests):
    """Stream one member: classify from its head, hash the whole thing."""
    h = hashlib.sha256()
    head = b""
    read = 0
    with z.open(info) as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            read += len(chunk)
            if read > budget:
                raise ArchiveRefused(
                    f"expansion budget exhausted at member {name}; the central "
                    f"directory understated the uncompressed size")
            if len(head) < detect.HEAD_BYTES:
                head += chunk[: detect.HEAD_BYTES - len(head)]
            if digests:
                h.update(chunk)
            elif len(head) >= detect.HEAD_BYTES:
                break
    kind = detect.sniff(name, head)
    return kind, (f"sha256:{h.hexdigest()}" if digests else ""), read


def _safe_name(raw: str) -> str | None:
    """Normalise a member name, or None when it escapes the archive root."""
    name = raw.replace("\\", "/")
    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        return None
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return None
    normalised = "/".join(parts)
    return normalised + "/" if raw.endswith(("/", "\\")) else normalised


def _head_of_file(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read(detect.HEAD_BYTES)
