"""Classify a simulation artifact by what its bytes are, not what it is called.

Suffix routing is already wrong in this repo for exactly the inputs this package
exists to read. `document_reader._READERS` maps `.dat` to the plain-text reader,
but a Workbench project carries `dp0/act.dat` -- 266 KB of ACT extension state
that is not a solver deck and must not be fed to an extractor as though it were.
The same tree carries `.log` files that are UTF-16, and the evidence corpus
already contains generic `.zip` bundles (`packs/nasa-7009b/examples/aerospace/`)
that are NOT Workbench archives.

So the rule here is: **content decides, suffix only breaks ties.** A caller that
knows only a name and the first few KB of a member can still classify it, which
is what lets `archive.py` sniff inside a zip without extracting it.

Nothing in this module reads a whole file. `sniff` takes a head buffer, and
`HEAD_BYTES` is the amount the callers are expected to hand it.
"""

from __future__ import annotations

import re

# Enough for any XML prolog plus root element, and for the ANSYS solver banner.
HEAD_BYTES = 8192

# ── Kinds ────────────────────────────────────────────────────
# Plain strings rather than an Enum: these travel into JSON manifests and are
# compared against pack-declared data, where an Enum member would serialise to
# something a pack author did not write.

WORKBENCH_ARCHIVE = "workbench-archive"
WORKBENCH_PROJECT = "workbench-project-xml"
ENGINEERING_DATA = "engineering-data-xml"
WORKBENCH_JOURNAL = "workbench-journal"
DESIGN_POINT_TABLE = "design-point-table"
PROJECT_CACHE = "project-cache"
HDF5_CONTAINER = "hdf5-container"
RASTER_IMAGE = "raster-image"
APDL_DECK = "apdl-deck"
SOLVER_LOG = "solver-log"
MECHANICAL_DB = "mechanical-db"
GEOMETRY_DB = "geometry-db"
RESULT_BINARY = "result-binary"
ZIP_ARCHIVE = "zip-archive"
TABULAR = "tabular"
TEXT = "text"
XML = "xml"
OPAQUE_BINARY = "opaque-binary"
EMPTY = "empty"

# Kinds a reader exists for. Everything else is sealed and reported unread --
# see seal.py, and the honest-blank contract in keyless_extractor.py.
READABLE = frozenset({
    WORKBENCH_ARCHIVE, WORKBENCH_PROJECT, ENGINEERING_DATA, WORKBENCH_JOURNAL,
    DESIGN_POINT_TABLE, PROJECT_CACHE, APDL_DECK, SOLVER_LOG, TABULAR, TEXT, XML,
})

# Why a given kind cannot be read, stated once so the manifest and the CLI agree.
UNREADABLE_REASON = {
    MECHANICAL_DB: "Mechanical database: binary, no open-source reader exists",
    GEOMETRY_DB: "CAD geometry database: binary, no open-source reader exists",
    RESULT_BINARY: "solver result file: needs the optional [ansys] extra",
    HDF5_CONTAINER: "HDF5 container: structure is readable, schema is not documented",
    RASTER_IMAGE: "figure capture: an image, with no text this tool can read",
    ZIP_ARCHIVE: "archive is not a Workbench project",
    OPAQUE_BINARY: "unrecognised binary",
    EMPTY: "file is empty",
}

_ZIP_MAGICS = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"

# Workbench writes result screenshots into `global/MECH/<SYS>/Figures and Images/`.
# They are evidence -- a saved contour plot of a solved model -- but there is no
# text in them this tool can read, and "unrecognised binary" would say we did not
# know what they were when we did.
_IMAGE_MAGICS = (
    (b"\x89PNG\r\n\x1a\n", RASTER_IMAGE),
    (b"\xff\xd8\xff", RASTER_IMAGE),          # JPEG
    (b"GIF87a", RASTER_IMAGE), (b"GIF89a", RASTER_IMAGE),
    (b"BM", RASTER_IMAGE),                      # BMP
)

_BOMS = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xfe\xff", "utf-16-be"),
)

# Binary formats with no usable magic number. Suffix is the only signal these
# ever give, and that is fine: they are all classified as unreadable anyway, so
# a misclassification costs a manifest label, never a parse.
_BINARY_BY_SUFFIX = {
    ".mechdb": MECHANICAL_DB, ".mechdat": MECHANICAL_DB,
    ".agdb": GEOMETRY_DB, ".scdoc": GEOMETRY_DB, ".pmdb": GEOMETRY_DB,
    ".dsdb": GEOMETRY_DB,
    ".rst": RESULT_BINARY, ".rth": RESULT_BINARY, ".rmg": RESULT_BINARY,
}

_APDL_MARKERS = re.compile(
    r"^\s*(/BATCH|/PREP7|/SOLU|/COM|NBLOCK|EBLOCK|ET,|MP,|TB,|ANTYPE|NLGEOM)",
    re.IGNORECASE | re.MULTILINE,
)
_SOLVER_BANNER = re.compile(
    r"ANSYS.{0,40}(RELEASE|Mechanical Enterprise)|NUMBER OF (TOTAL )?(NODES|ELEMENTS)",
    re.IGNORECASE,
)


def decode_head(head: bytes) -> tuple[str, str] | tuple[None, None]:
    """Decode a head buffer to text, honouring a BOM. Returns (text, encoding).

    Returns (None, None) when the bytes are not plausibly text. The BOM branch
    is load-bearing: the real evidence folder ships a UTF-16LE
    `optiSLang_protocol.log`, which decodes under UTF-8 to interleaved
    replacement characters rather than raising -- i.e. it fails silently, which
    is the failure mode this whole module is built to avoid.
    """
    for bom, enc in _BOMS:
        if head.startswith(bom):
            try:
                return head[len(bom):].decode(enc, errors="replace"), enc
            except LookupError:  # pragma: no cover - stdlib always has these
                return None, None

    # No BOM. A NUL in the first block means binary for every text format we
    # care about; UTF-16 without a BOM is indistinguishable from binary here and
    # is correctly left to the seal path.
    if b"\x00" in head:
        return None, None
    try:
        return head.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            return head.decode("latin-1"), "latin-1"
        except UnicodeDecodeError:  # pragma: no cover - latin-1 cannot fail
            return None, None


def sniff(name: str, head: bytes, *, zip_names: list[str] | None = None) -> str:
    """Classify one artifact from its name and the first `HEAD_BYTES` bytes.

    `zip_names` lets a caller that has already opened a container distinguish a
    Workbench archive from a generic zip without this module reopening it.
    """
    if not head:
        return EMPTY

    suffix = _suffix(name)

    if head.startswith(_ZIP_MAGICS):
        # A SpaceClaim `.scdoc` is a zip. So is an Office file. Consult the
        # suffix here or a CAD database is reported as an archive we declined
        # to descend into, which reads as a tooling failure rather than a
        # deliberate seal-only decision.
        if suffix in _BINARY_BY_SUFFIX:
            return _BINARY_BY_SUFFIX[suffix]
        if zip_names is None:
            return ZIP_ARCHIVE
        return (WORKBENCH_ARCHIVE
                if any(n.lower().endswith(".wbpj") for n in zip_names)
                else ZIP_ARCHIVE)

    text, _enc = decode_head(head)

    if text is None:
        # Binary. Prefer the suffix when it names a format we can describe:
        # `.mechdb` and `.agdb` are *both* HDF5 underneath, so testing the magic
        # first would flatten two informative labels into one useless one. HDF5
        # is the fallback for containers we cannot name -- `dp0/act.dat`, which
        # document_reader._READERS would have routed to the plain-text reader.
        named = _BINARY_BY_SUFFIX.get(suffix)
        if named:
            return named
        for magic, kind in _IMAGE_MAGICS:
            if head.startswith(magic):
                return kind
        if head.startswith(_HDF5_MAGIC):
            return HDF5_CONTAINER
        return OPAQUE_BINARY

    stripped = text.lstrip()

    if name.endswith(".project_cache"):
        return PROJECT_CACHE

    if stripped.startswith("<?xml") or stripped.startswith("<"):
        if re.search(r"<EngineeringData\b", text):
            return ENGINEERING_DATA
        # `.wbdp` is XML too, and shares the `<Project Version=` marker with the
        # project file, so it has to be separated by name before that test.
        if suffix == ".wbdp":
            return DESIGN_POINT_TABLE
        if re.search(r"framework-build-version|<Project\s+Version=", text):
            return WORKBENCH_PROJECT
        return XML

    if suffix == ".wbjn" or "WB.AppletList" in text or "SetScriptVersion" in text:
        return WORKBENCH_JOURNAL

    if _SOLVER_BANNER.search(text):
        return SOLVER_LOG
    if _APDL_MARKERS.search(text):
        return APDL_DECK

    if suffix in (".csv", ".tsv"):
        return TABULAR
    return TEXT


def is_readable(kind: str) -> bool:
    """True when a reader exists for this kind."""
    return kind in READABLE


def unreadable_reason(kind: str) -> str:
    """Why `kind` is sealed but not read. Empty string when it is readable."""
    if kind in READABLE:
        return ""
    return UNREADABLE_REASON.get(kind, "no reader for this format")


def _suffix(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    dot = base.rfind(".")
    return base[dot:].lower() if dot > 0 else ""
