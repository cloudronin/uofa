"""Read a Workbench `.wbpj`: version, addins, stored messages, stated absences.

The project file is XML, so getting into it is easy. Getting the messages out
is not: each one is a `member-data` string holding a Python-repr-ish blob that
is neither JSON nor valid Python --

    {"DisplayText": "Message", "MessageType": "Warning", "Summary": "…",
     "Details": r\"\"\"1. …\\ds.dat 2. …\\solve.out\"\"\",
     "DateTimeStamp": 10/09/2016 20:50:36, "DesignPoint": None}

`DateTimeStamp` is a bare date, `Details` is a raw triple-quoted string, `None`
is Python's, and some real summaries arrive double-quoted (`""…""`). So neither
`json.loads` nor `ast.literal_eval` will touch it, and a quote-counting parser
breaks on the first summary containing a quotation mark.

What works is splitting on the key boundaries: the key set is closed and known,
so each value is simply everything between its own colon and the next key. A
record that does not yield a `MessageType` is reported unparsed rather than
guessed at -- there are 78 of these in one real project and being right about
70 of them is not a licence to invent the other 8.

Why this matters: these archives were written without solution files, so
`solve.out` does not exist. The stored messages ARE the solver log. And one of
them is Workbench's own record of what the archive left out, which is the best
completeness evidence in the folder.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from uofa_cli.solver.facts import (CERTAIN, AbsentArtifact, SolverCaution,
                                   SolverEvidence, SolverFact)
from uofa_cli.solver.redact import Redactor

# The closed key set of a StoredMessage's member-data blob.
_MSG_KEYS = ("DisplayText", "MessageType", "MessageCategory", "Summary",
             "Details", "Association", "DateTimeStamp", "Visibility",
             "MessageSourceContainer", "MessageSourceEntity",
             "AdditionalMessageData", "DesignPoint")
_KEY_RE = re.compile(r'"(' + "|".join(_MSG_KEYS) + r')"\s*:\s*')

# Workbench's own words for a project opened from a results-stripped archive.
_ARCHIVE_RECORD = "did not include solution or result files"
_NUMBERED = re.compile(r"\d+\.\s+(.+?)(?=\s+\d+\.\s|$)", re.S)

# Version and identity fields, each a direct read with no interpretation.
_VERSION_FIELDS = {
    "external-version-string": ("project.ansys_release", ""),
    "framework-build-version": ("project.framework_build", ""),
    "last-saved-utc": ("project.last_saved_utc", ""),
}


def parse(text: str, *, member: str = "", redactor: Redactor | None = None
          ) -> SolverEvidence:
    """Read one `.wbpj`. `text` is the decoded project file."""
    redactor = redactor or Redactor()
    ev = SolverEvidence()

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        ev.unparsed.append(f"{member}: not well-formed XML ({exc})")
        return ev

    # Learn identities across the whole document before redacting any part of
    # it. `logHistory` is where the usernames and hostnames are stated, and
    # nothing reads it -- but the stripped-file list names cleanup scripts after
    # the machine, so without this pass the host rides out inside those
    # basenames. Learning per-string is not enough when the statement and the
    # use are in different strings.
    redactor.learn(text)

    _read_versions(root, ev, member, redactor)
    _read_addins(root, ev, member)
    _read_messages(root, ev, member, redactor)

    ev.redaction_summary = redactor.summary()
    return ev


def _read_versions(root, ev: SolverEvidence, member: str, redactor: Redactor) -> None:
    for elem in root.iter():
        key_units = _VERSION_FIELDS.get(elem.tag)
        if not key_units or not (elem.text or "").strip():
            continue
        key, units = key_units
        value = redactor.redact(elem.text.strip())
        ev.facts.append(SolverFact(
            key=key, value=value, units=units, scope="project",
            source_member=member, source_locator=f"//{elem.tag}",
            source_text=f"<{elem.tag}>{value}</{elem.tag}>",
            binding_confidence=CERTAIN))


def _read_addins(root, ev: SolverEvidence, member: str) -> None:
    """Addin name+version. A project that needs an addin nobody has cannot be
    re-run even with the vendor software, so the inventory is evidence."""
    for elem in root.iter("Addin"):
        name, version = elem.get("Name"), elem.get("Version")
        if not name:
            continue
        ev.facts.append(SolverFact(
            key="project.addin", value=name, units="", scope=version or "",
            source_member=member, source_locator="//Addin",
            source_text=f'<Addin Name="{name}" Version="{version or ""}" />',
            binding_confidence=CERTAIN))


def _read_messages(root, ev: SolverEvidence, member: str, redactor: Redactor) -> None:
    for obj in root.iter("Object"):
        if (obj.findtext("class-type") or "").strip() != "StoredMessage":
            continue
        blob = obj.findtext("member-data") or ""
        if not blob.strip():
            continue
        fields = split_member_data(blob)
        severity = (fields.get("MessageType") or "").strip().lower()
        summary = fields.get("Summary", "").strip()
        if not severity or not summary:
            ev.unparsed.append(
                f"{member}: stored message {obj.get('Name', '?')} has no "
                f"type or summary")
            continue

        detail = fields.get("Details", "").strip()
        summary_r = redactor.redact(summary)
        detail_r = redactor.redact(detail)
        ev.cautions.append(SolverCaution(
            severity=severity, summary=summary_r, detail=detail_r,
            reported_at=fields.get("DateTimeStamp", "").strip(),
            source_member=member))

        if _ARCHIVE_RECORD in summary:
            ev.absent.extend(_absent_from(detail_r, member))


def _absent_from(detail: str, member: str) -> list[AbsentArtifact]:
    """Pull the stripped-file list out of the archive record's Details.

    The paths are already redacted, so what survives is a directory token and
    the basename -- which is the part that carries the claim.
    """
    out = []
    for raw in _NUMBERED.findall(detail):
        path = raw.replace("\\", "/")
        location, _, name = path.rpartition("/")
        if not name:
            continue
        out.append(AbsentArtifact(
            name=name, location=location,
            stated_by="workbench-archive-record", source_member=member))
    return out


def split_member_data(blob: str) -> dict[str, str]:
    """Split a member-data blob on its known key boundaries.

    Returns raw string values with the surrounding quoting removed. Keys that
    are absent, or whose value is Python's `None`, come back missing rather
    than empty, so a caller can tell "not stated" from "stated as blank".
    """
    matches = list(_KEY_RE.finditer(blob))
    wrapped = blob.strip().startswith("{") and blob.strip().endswith("}")
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        last = i + 1 >= len(matches)
        end = len(blob) if last else matches[i + 1].start()
        value = blob[m.end():end].rstrip()
        # The final value runs to the end of the blob, which includes the
        # dict's own closing brace. Real projects hid this: the last key is
        # always `DesignPoint: None`, which is dropped anyway, so the stray
        # brace never reached a value anyone read.
        if last and wrapped and value.endswith("}"):
            value = value[:-1].rstrip()
        value = value[:-1].rstrip() if value.endswith(",") else value
        cleaned = _unquote(value)
        if cleaned is not None:
            out[m.group(1)] = cleaned
    return out


def _unquote(value: str) -> str | None:
    """Strip Python-repr quoting. `None` means the field was not stated."""
    v = value.strip()
    if not v or v == "None":
        return None
    for prefix in ('r"""', '"""'):
        if v.startswith(prefix) and v.endswith('"""') and len(v) > len(prefix) + 2:
            return v[len(prefix):-3]
    # Some real summaries arrive double-quoted: ""Update failed for 2 …"".
    while len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    return v.replace('\\"', '"').strip()
