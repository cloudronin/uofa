"""Read every solver artifact in an evidence folder into one SolverEvidence.

Dispatches on the sniffed kind, never the suffix, and descends into archives
through the streaming walker rather than unpacking them. One `Redactor` spans
the whole folder so that a username learned in one project file is scrubbed
from a filename in another.

Budget discipline, stated once here because it is easy to lose: **seal
everything, read some, send even less to a model.** `seal.py` accounts for all
85 members of each archive. This module reads the four kinds that carry
evidence. `readers/ansys_reader.py` renders a compact digest of what this found
for the extraction corpus. A Workbench tree has thousands of files and none of
those three numbers should be the same.
"""

from __future__ import annotations

from pathlib import Path

from uofa_cli.solver import archive, detect, engdata, wbproject
from uofa_cli.solver.facts import SolverEvidence
from uofa_cli.solver.redact import Redactor

# Kinds this module knows how to turn into facts. A readable kind that is not
# here (a journal, a design-point table) is sealed and surfaced as text by the
# corpus reader; it simply yields no structured facts yet.
_PARSERS = {
    detect.WORKBENCH_PROJECT: wbproject.parse,
    detect.ENGINEERING_DATA: engdata.parse,
}

# Enough for a 233 KB project file and a 132 KB materials library, and far under
# archive.MAX_MEMBER_READ.
_MAX_PARSE_BYTES = 16 * 1024 * 1024


def read_evidence(source: Path, *, redactor: Redactor | None = None
                  ) -> SolverEvidence:
    """Read one folder, one archive, or one loose artifact."""
    redactor = redactor or Redactor()
    out = SolverEvidence()

    for path in _artifacts(source):
        if archive.is_archive(path):
            _read_archive(path, out, redactor)
        else:
            _read_file(path, out, redactor)

    out.redaction_summary = redactor.summary()
    return out


def _artifacts(source: Path):
    if source.is_file():
        yield source
        return
    for path in sorted(source.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path


def _read_archive(path: Path, out: SolverEvidence, redactor: Redactor) -> None:
    try:
        scan = archive.scan(path, digests=False)
    except archive.ArchiveRefused as exc:
        out.unparsed.append(f"{path.name}: {exc}")
        return

    for member in scan.members:
        parser = _PARSERS.get(member.kind)
        if member.is_dir or parser is None:
            continue
        if member.size > _MAX_PARSE_BYTES:
            out.unparsed.append(
                f"{path.name}!{member.name}: {member.size:,} bytes, over the "
                f"{_MAX_PARSE_BYTES:,}-byte parse cap")
            continue
        try:
            raw = archive.read_member(path, member.name)
        except Exception as exc:
            out.unparsed.append(f"{path.name}!{member.name}: {exc}")
            continue
        # `!` separates container from member, the convention jar: URLs use.
        out.extend(parser(_decode(raw), member=f"{path.name}!{member.name}",
                          redactor=redactor))


def _read_file(path: Path, out: SolverEvidence, redactor: Redactor) -> None:
    try:
        head = path.open("rb").read(detect.HEAD_BYTES)
    except OSError as exc:
        out.unparsed.append(f"{path.name}: {exc}")
        return
    parser = _PARSERS.get(detect.sniff(path.name, head))
    if parser is None:
        return
    if path.stat().st_size > _MAX_PARSE_BYTES:
        out.unparsed.append(f"{path.name}: over the parse cap")
        return
    out.extend(parser(_decode(path.read_bytes()), member=path.name,
                      redactor=redactor))


def _decode(raw: bytes) -> str:
    text, _ = detect.decode_head(raw)
    return text if text is not None else raw.decode("utf-8", errors="replace")
