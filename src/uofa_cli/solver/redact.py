"""Strip operator identity out of solver artifacts before anything else sees them.

A Workbench project file is a diary. The real ones in the OSF folder carry
`logHistory` entries of the form `GVerma@PUNGVERMAPC:C:\\Users\\gverma\\AppData\\
Local\\Temp\\WorkbenchLogs\\CoreEvents19280.log`, and message details quoting
`E:\\Projects\\2020\\FDA_F1717\\August_2020\\Mesh_Refinement\\...`. Those names
match contributors credited in the paper.

Two things go wrong without this module, and both are one-way:

  * the extraction corpus is sent to a language model, so private filesystem
    layout and usernames leave the machine;
  * the package is signed, so anything embedded is fixed in a document intended
    to be published and verified by third parties. AGENTS.md §10 bans committing
    absolute home-directory paths for the weaker case of a repo file.

**The basename survives on purpose.** `…\\MECH\\ds.dat` becomes
`<redacted-path-1>\\ds.dat`, because the whole completeness argument rests on
which files are named as missing. Redacting the filename too would delete the
evidence while protecting the operator; redacting only the directory protects
the operator and keeps the evidence.

Tokens are sequential per distinct value in first-appearance order, not hashes.
A short hash of a username is a dictionary attack away from being a username
again, and a salted hash would be non-deterministic across runs -- which this
repo's canonicalisation cannot afford.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PATH = "path"
USER = "user"
HOST = "host"

# Windows drive-absolute path. Stops at whitespace and at the quote/bracket
# characters that end a path inside XML attributes and Python-repr blobs.
_WINDOWS_PATH = re.compile(r"""[A-Za-z]:\\(?:[^\\\s"'<>|*?]+\\)*[^\\\s"'<>|*?]*""")

# POSIX home and temp directories. `/tmp` is included because Workbench writes
# there on Linux and the path embeds the user's session id.
_POSIX_PATH = re.compile(r"""/(?:home|Users|root|tmp|var/folders)/[^\s"'<>|]*""")

# `USER@HOST:` as it appears in logHistory. The trailing colon is required so an
# ordinary email address in a comment is left alone.
_USER_AT_HOST = re.compile(r"""\b([A-Za-z][\w.\-]{0,63})@([A-Za-z][\w.\-]{0,63})(?=:)""")

# Usernames also appear as a path segment, which is a second place to learn them.
_USER_IN_PATH = re.compile(r"""[\\/](?:Users|home)[\\/]([^\\/\s"'<>|]{2,64})""",
                           re.IGNORECASE)

# An identity shorter than this is not scrubbed as a literal: the risk of
# mangling an unrelated word outweighs the disclosure.
_MIN_IDENTITY = 4

# Never touched: a source URL is the whole point of a re-derivable pin.
_URL = re.compile(r"""\b[a-z][a-z0-9+.\-]*://[^\s"'<>]+""", re.IGNORECASE)


@dataclass
class Redactor:
    """Assigns stable tokens across every string it is shown.

    One redactor per document, so two mentions of the same directory get the
    same token and a reader can tell they are the same place.
    """
    _tokens: dict[tuple[str, str], str] = field(default_factory=dict)
    _counts: dict[str, int] = field(default_factory=dict)

    def token(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._tokens:
            self._counts[kind] = self._counts.get(kind, 0) + 1
            self._tokens[key] = f"<redacted-{kind}-{self._counts[kind]}>"
        return self._tokens[key]

    @property
    def counts(self) -> dict[str, int]:
        """How many distinct values of each kind were replaced."""
        return dict(self._counts)

    @property
    def total(self) -> int:
        return sum(self._counts.values())

    def summary(self) -> str:
        if not self._counts:
            return "no operator paths or identities found"
        parts = [f"{n} {kind}{'s' if n != 1 else ''}"
                 for kind, n in sorted(self._counts.items())]
        return "redacted " + ", ".join(parts)

    def __call__(self, text: str) -> str:
        return self.redact(text)

    def learn(self, text: str) -> None:
        """Harvest identities without substituting anything.

        Call this over every string in a document before redacting any of them
        when the identities and their uses are split across strings. Within one
        string `redact` learns first anyway.
        """
        for m in _USER_AT_HOST.finditer(text):
            self.token(USER, m.group(1).lower())
            self.token(HOST, m.group(2).lower())
        for m in _USER_IN_PATH.finditer(text):
            self.token(USER, m.group(1).lower())

    def redact(self, text: str) -> str:
        """Replace operator paths and identities, keeping basenames."""
        if not text:
            return text

        # Park URLs first so a path-shaped tail inside one is never rewritten.
        parked: list[str] = []

        def park(m: re.Match) -> str:
            parked.append(m.group(0))
            return f"\x00URL{len(parked) - 1}\x00"

        text = _URL.sub(park, text)

        self.learn(text)
        text = _USER_AT_HOST.sub(
            lambda m: f"{self.token(USER, m.group(1).lower())}"
                      f"@{self.token(HOST, m.group(2).lower())}",
            text)
        text = _WINDOWS_PATH.sub(lambda m: self._path(m.group(0), "\\"), text)
        text = _POSIX_PATH.sub(lambda m: self._path(m.group(0), "/"), text)
        text = self._scrub_identities(text)

        for i, original in enumerate(parked):
            text = text.replace(f"\x00URL{i}\x00", original)
        return text

    def _scrub_identities(self, text: str) -> str:
        """Replace known usernames and hostnames wherever they still appear.

        Preserving basenames leaks identity when the identity is IN the
        basename, and Workbench does exactly that: a results-stripped archive
        lists `cleanup-ansys-punkkartikepc-16148.bat`, so the hostname rides out
        inside a filename the completeness check wants to keep. Scrubbing the
        literal keeps the filename's shape and drops the name.

        Case-insensitive because the same host appears as both `PUNKKARTIKEPC`
        and `punkkartikepc` in one file.
        """
        for (kind, value), token in sorted(self._tokens.items(),
                                           key=lambda kv: -len(kv[0][1])):
            if kind == PATH or len(value) < _MIN_IDENTITY:
                continue
            text = re.sub(re.escape(value), token, text, flags=re.IGNORECASE)
        return text

    def _path(self, raw: str, sep: str) -> str:
        """Token for the directory, basename kept verbatim."""
        head, found, tail = raw.rpartition(sep)
        if not found:
            return raw
        # A trailing separator means the match was a directory; there is no
        # basename to preserve and the whole thing is private.
        if not tail:
            return self.token(PATH, raw.rstrip(sep)) + sep
        return f"{self.token(PATH, head)}{sep}{tail}"


def redact(text: str) -> str:
    """One-shot redaction for a caller that does not need the counts."""
    return Redactor().redact(text)


def looks_redacted(text: str) -> bool:
    """True when nothing operator-identifying remains.

    Used as an assertion at the boundaries rather than a routine check: a
    caller that has to ask whether it redacted has already lost track of where
    the boundary is.
    """
    stripped = _URL.sub("", text)
    return not (_WINDOWS_PATH.search(stripped)
                or _POSIX_PATH.search(stripped)
                or _USER_AT_HOST.search(stripped)
                or _USER_IN_PATH.search(stripped))
