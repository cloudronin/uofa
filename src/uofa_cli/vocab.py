"""The vocabulary, as the CLI sees it.

Until now the 288 labels and 240 comments in ``packs/*/shapes/*.ttl`` were read
by exactly one thing: a regex extractor in the Node site build. A user who hit a
validation error got a property name and a constraint, and had to visit a web
page to find out what the property meant.

This is the one reader the CLI side uses. Everything that wants a definition --
violation messages, ``uofa define``, the site generator -- derives from
``index()`` rather than growing its own copy. ``shacl_friendly._FIX_SUGGESTIONS``
is what happens otherwise: a hand-written map keyed on property IRI that has to
be updated in lockstep with a source it has no link to.

Two things to know before changing how the graph is loaded:

1. **Load through ``paths.all_shacl_schemas()``, never a glob.**
   ``spec/schemas/uofa_shacl.ttl`` is a symlink to
   ``packs/core/shapes/uofa_shacl.ttl``. Globbing both parses core twice, which
   re-mints its blank nodes and duplicates every property shape (128 -> 200), so
   each ``sh:message`` would be collected twice.

2. **The set of terms depends on the active packs.** Core plus vv40 is 62
   ``sh:path`` IRIs; core plus iso42001 is 90; all six packs is 108. A caller
   asking about a violation should pass the packs that produced it. Only
   ``all_packs=True`` sees everything.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from uofa_cli import paths

CORE_NS = "https://uofa.net/vocab#"
AIMS_NS = "https://uofa.net/vocab/aims#"
SURR_NS = "https://uofa.net/vocab/surrogate#"

_NAMESPACES = {CORE_NS: "core", AIMS_NS: "aims", SURR_NS: "surrogate"}


# UofA does not own these and must not define them in its own namespace. The
# gloss says what the term means where it comes from, and the renderer is
# expected to attribute it (``Means (PROV-O):``) and show the upstream IRI.
EXTERNAL_GLOSS: dict[str, tuple[str, str]] = {
    "http://www.w3.org/ns/prov#generatedAtTime": (
        "PROV-O",
        "The time at which this package was produced. Used as the package's own "
        "timestamp, so a reviewer can tell how old the evidence is.",
    ),
    "http://www.w3.org/ns/prov#wasDerivedFrom": (
        "PROV-O",
        "An earlier artifact this one was built from, so a reviewer can walk "
        "back to what it came from.",
    ),
    "http://www.w3.org/ns/prov#wasAttributedTo": (
        "PROV-O",
        "The agent responsible for this artifact, whether a person, an "
        "organization, or a piece of software.",
    ),
    "http://purl.org/dc/terms/identifier": (
        "Dublin Core",
        "An unambiguous reference to the resource within a given context.",
    ),
    "https://schema.org/description": (
        "schema.org",
        "A description of the item, in prose.",
    ),
}


@dataclass(frozen=True)
class Term:
    """One vocabulary term, assembled from the shapes graph and the contexts."""

    iri: str
    name: str
    namespace: str          # core | aims | surrogate | external
    kind: str | None        # Class | Property | None when undeclared
    label: str | None
    comment: str | None     # the definition
    domain: str | None
    range: str | None
    subclass_of: tuple[str, ...]
    deprecated: bool
    json_key: str | None
    id_typed: bool          # context declares "@type": "@id"
    since: str | None       # first context version carrying it
    dropped_in: str | None  # newest context version, when this term is absent from it

    packs: tuple[str, ...]  # packs whose shapes put this term on an sh:path
    messages: tuple[str, ...]
    defined_in: str | None  # repo-relative shapes file carrying the definition
    schema_description: str | None   # description from the generated JSON Schema
    constraints: tuple[dict, ...]    # sh:datatype / minCount / maxCount / pattern / message
    #: The last context version that actually CARRIED the term.
    #:
    #: Not derivable from `dropped_in`, which names the newest context rather
    #: than the version the term vanished in. Callers were reconstructing it as
    #: "the version before `dropped_in`", which is only correct while the
    #: removal happens in the newest context. Adding any context after a removal
    #: makes that reconstruction claim the term was live in a version that never
    #: had it -- `reviewDate` (v0.4-v0.6) began reporting "v0.4 to v0.7" the
    #: moment v0.8 was added.
    last_seen_in: str | None = None

    @property
    def external(self) -> bool:
        return self.namespace == "external"

    @property
    def source(self) -> str | None:
        """Where the definition came from, for attribution in output."""
        if self.external:
            entry = EXTERNAL_GLOSS.get(self.iri)
            return entry[0] if entry else None
        return None


# The prefixes the shapes files declare, so a CURIE round-trips to the form an
# author would recognise from the Turtle.
_CURIE_PREFIXES = {
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "https://schema.org/": "schema",
    "http://www.w3.org/ns/prov#": "prov",
    "http://purl.org/dc/terms/": "dct",
    CORE_NS: "uofa",
    AIMS_NS: "uofa-aims",
    SURR_NS: "uofa-surr",
}


def _curie(node) -> str | None:
    """Shorten a datatype IRI the way the shapes file writes it (``xsd:string``)."""
    if node is None:
        return None
    text = str(node)
    for base, prefix in _CURIE_PREFIXES.items():
        if text.startswith(base):
            return f"{prefix}:{text[len(base):]}"
    return text


def _plain(node) -> str | None:
    return None if node is None else str(node)


def _range_form(node) -> str | None:
    """A range as the site expects it.

    UofA classes stay full IRIs so the renderer can link them to their anchor;
    anything else stays a CURIE (``xsd:integer``, ``schema:Person``) because
    there is no page on the site to link it to. The renderer distinguishes the
    two by whether the value starts with ``http``.
    """
    if node is None:
        return None
    text = str(node)
    if any(text.startswith(b) for b in _NAMESPACES):
        return text
    return _curie(node)


def _datatype_of(graph, prop_shape) -> str | None:
    """The datatype a property shape allows, including an ``sh:or`` alternation.

    ``uofa:credibilityIndex`` is declared ``sh:or ([sh:datatype xsd:decimal]
    [sh:datatype xsd:double])``. The regex reader this replaced matched the
    first ``sh:datatype`` anywhere in the block and reported ``xsd:decimal``
    alone, which reads as a single permitted type rather than one of two.
    """
    from rdflib.collection import Collection
    from rdflib.namespace import SH

    direct = graph.value(prop_shape, SH.datatype)
    if direct is not None:
        return _curie(direct)

    head = graph.value(prop_shape, SH["or"])
    if head is None:
        return None
    alternatives = []
    try:
        for member in Collection(graph, head):
            dt = graph.value(member, SH.datatype)
            if dt is not None:
                alternatives.append(_curie(dt))
    except Exception:
        return None
    return " or ".join(dict.fromkeys(alternatives)) or None


def _enum_of(graph, prop_shape) -> str | None:
    """``sh:in`` rendered as the reader would say it: "Low, Medium, High"."""
    from rdflib.collection import Collection
    from rdflib.namespace import SH

    head = graph.value(prop_shape, SH["in"])
    if head is None:
        return None
    try:
        members = [str(v).rsplit("#", 1)[-1] for v in Collection(graph, head)]
    except Exception:
        return None
    return ", ".join(members) or None


def _namespace_of(iri: str) -> str:
    for base, name in _NAMESPACES.items():
        if iri.startswith(base):
            return name
    return "external"


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _version_key(stem: str) -> tuple[int, ...]:
    """Numeric sort for ``v0.7``.

    Lexicographic sorting puts v0.10 before v0.2, which would backdate every
    term's ``since`` and pick the wrong current version. The same bug was found
    and fixed in the Node extractor; do not reintroduce it here.
    """
    return tuple(int(p) for p in stem.lstrip("v").split("."))


def _context_terms(root: Path) -> tuple[dict[str, dict], list[str]]:
    """JSON key, first version and last version for every term in the contexts."""
    ctx_dir = root / "spec" / "context"
    if not ctx_dir.exists():
        return {}, []
    files = sorted(
        (f for f in ctx_dir.glob("v*.jsonld") if re.fullmatch(r"v\d+\.\d+", f.stem)),
        key=lambda f: _version_key(f.stem),
    )
    out: dict[str, dict] = {}
    for f in files:
        version = f.stem
        try:
            ctx = json.loads(f.read_text(encoding="utf-8")).get("@context", {})
        except (OSError, json.JSONDecodeError):
            continue
        for term, value in ctx.items():
            if term.startswith("@"):
                continue
            target = value.get("@id") if isinstance(value, dict) else value
            if not isinstance(target, str):
                continue
            iri = target.replace("uofa:", CORE_NS).replace(
                "uofa-aims:", AIMS_NS).replace("uofa-surr:", SURR_NS)
            if not iri.startswith("https://uofa.net/vocab"):
                continue
            entry = out.setdefault(iri, {"term": term, "since": version})
            entry["term"] = term
            entry["latest"] = version
            entry["id_typed"] = isinstance(value, dict) and value.get("@type") == "@id"
    return out, [f.stem for f in files]


def _schema_descriptions(root: Path) -> dict[str, str]:
    """Term descriptions from the generated JSON Schema.

    Keyed on the JSON property name, not the IRI, because that is what the
    schema carries. Nested under oneOf/allOf, so the whole document is walked.
    """
    out: dict[str, str] = {}
    schema_path = root / "spec" / "schemas" / "uofa.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return out

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        props = node.get("properties")
        if isinstance(props, dict):
            for term, spec in props.items():
                if isinstance(spec, dict) and isinstance(spec.get("description"), str):
                    out.setdefault(term, spec["description"])
        for value in node.values():
            walk(value)

    walk(schema)
    return out


@lru_cache(maxsize=8)
def _shape_files(root_str: str, active: tuple[str, ...] | None, all_packs: bool) -> tuple[str, ...]:
    """Resolve the shape files for a pack set.

    Cached because ``all_shacl_schemas`` re-validates every pack manifest on
    each call -- about 70ms. ``definition()`` runs once per violation, so
    without this the cost is paid per line of output rather than once.
    """
    root = Path(root_str)
    packs = [p for p in paths.list_packs(root) if p != "core"] if all_packs else (
        list(active) if active else None)
    return tuple(str(f) for f in paths.all_shacl_schemas(root, active=packs))


def _build(root: Path, files: tuple[Path, ...]) -> dict[str, Term]:
    from rdflib import Graph, URIRef
    from rdflib.namespace import RDF, RDFS, SH

    OWL_DEPRECATED = URIRef("http://www.w3.org/2002/07/owl#deprecated")

    graph = Graph()
    pack_of_path: dict[str, set[str]] = {}
    declared_in: dict[str, str] = {}

    for f in files:
        per_file = Graph()
        per_file.parse(str(f), format="turtle")
        graph += per_file
        try:
            rel = f.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = f.name
        for subj in per_file.subjects(RDFS.label, None):
            if isinstance(subj, URIRef):
                declared_in.setdefault(str(subj), rel)
        # packs/<name>/shapes/<file>.ttl -> <name>
        try:
            pack = f.resolve().relative_to(root.resolve() / "packs").parts[0]
        except ValueError:
            pack = f.stem
        for obj in per_file.objects(None, SH.path):
            if isinstance(obj, URIRef):
                pack_of_path.setdefault(str(obj), set()).add(pack)

    ctx, versions = _context_terms(root)
    current = versions[-1] if versions else None
    schema_desc = _schema_descriptions(root)

    # Structured constraints, read from the parsed graph. The JS extractor did
    # this with a regex over the Turtle and had to cut each property shape at a
    # line that is only a closing bracket, because stopping at the first "]"
    # truncated inside uofa:hash's [a-f0-9] character class and silently
    # swallowed both the pattern and the message. rdflib has no such problem.
    messages: dict[str, list[str]] = {}
    constraints: dict[str, list[dict]] = {}
    for prop_shape in graph.subjects(SH.path, None):
        path = graph.value(prop_shape, SH.path)
        if not isinstance(path, URIRef):
            continue
        key = str(path)
        msg = graph.value(prop_shape, SH.message)
        if msg is not None:
            messages.setdefault(key, []).append(str(msg))
        entry = {
            "datatype": _datatype_of(graph, prop_shape),
            "minCount": _plain(graph.value(prop_shape, SH.minCount)),
            "maxCount": _plain(graph.value(prop_shape, SH.maxCount)),
            "pattern": _plain(graph.value(prop_shape, SH.pattern)),
            # An enumeration is the most directly useful thing a page can say
            # about a property -- "must be Low, Medium or High" answers the
            # question outright. The regex reader counted these terms as
            # constrained but captured nothing to show, so the site reported 66
            # constrained terms while rendering constraints for 57.
            "in": _enum_of(graph, prop_shape),
            "message": str(msg) if msg is not None else None,
        }
        if any(v is not None for v in entry.values()):
            constraints.setdefault(key, []).append(entry)

    # Deterministic order. The order these come out of the graph is rdflib's
    # internal one, and the order the previous regex reader produced was the
    # order the files happened to sit in on disk -- neither is meaningful and
    # neither is stable across machines. Sorting makes the rendered page
    # reproducible, which is what a generated artifact needs.
    for rows in constraints.values():
        rows.sort(key=lambda c: (c["message"] or "", c["datatype"] or "",
                                 c["pattern"] or "", c["in"] or "",
                                 c["minCount"] or ""))

    iris: set[str] = set(pack_of_path) | set(ctx) | set(EXTERNAL_GLOSS)
    for subject in set(graph.subjects(RDF.type, RDFS.Class)) | set(
            graph.subjects(RDF.type, RDF.Property)):
        if isinstance(subject, URIRef):
            iris.add(str(subject))

    terms: dict[str, Term] = {}
    for iri in sorted(iris):
        # The bare namespace IRI ("...vocab#") and any sub-path are not terms.
        # A context that maps a prefix produces the former.
        local = _local_name(iri)
        if not local or "/" in local:
            continue
        node = URIRef(iri)
        kind = None
        if (node, RDF.type, RDFS.Class) in graph:
            kind = "Class"
        elif (node, RDF.type, RDF.Property) in graph:
            kind = "Property"

        comment = graph.value(node, RDFS.comment)
        comment = str(comment) if comment is not None else None
        namespace = _namespace_of(iri)
        if comment is None and namespace == "external" and iri in EXTERNAL_GLOSS:
            comment = EXTERNAL_GLOSS[iri][1]

        label = graph.value(node, RDFS.label)
        domain = graph.value(node, RDFS.domain)
        rng = graph.value(node, RDFS.range)
        entry = ctx.get(iri)

        terms[iri] = Term(
            iri=iri,
            name=_local_name(iri),
            namespace=namespace,
            kind=kind,
            label=str(label) if label is not None else None,
            comment=comment,
            domain=str(domain) if domain is not None else None,
            range=_range_form(rng),
            subclass_of=tuple(sorted(str(o) for o in graph.objects(node, RDFS.subClassOf))),
            deprecated=bool(graph.value(node, OWL_DEPRECATED)),
            json_key=entry.get("term") if entry else None,
            id_typed=bool(entry.get("id_typed")) if entry else False,
            since=entry.get("since") if entry else None,
            dropped_in=(
                current if entry and current and entry.get("latest") != current else None
            ),
            last_seen_in=entry.get("latest") if entry else None,
            packs=tuple(sorted(pack_of_path.get(iri, ()))),
            messages=tuple(messages.get(iri, ())),
            defined_in=declared_in.get(iri),
            schema_description=(
                schema_desc.get(entry["term"]) if entry else None
            ) or schema_desc.get(_local_name(iri)),
            constraints=tuple(constraints.get(iri, ())),
        )
    return terms


@lru_cache(maxsize=8)
def _cached(root_str: str, files: tuple[str, ...]) -> dict[str, Term]:
    return _build(Path(root_str), tuple(Path(f) for f in files))


def index(
    active: Sequence[str] | None = None,
    *,
    all_packs: bool = False,
    root: Path | None = None,
) -> dict[str, Term]:
    """Every term the given pack set can put in front of a user, keyed by IRI.

    ``active`` defaults to the open-core baseline (``vv40``), matching
    ``paths.all_shacl_schemas``. ``all_packs=True`` loads every installed pack,
    which is the only way to see all 108 constrained properties.
    """
    root = root or paths.find_repo_root()
    files = _shape_files(str(root), tuple(active) if active else None, all_packs)
    return _cached(str(root), files)


def lookup(
    name_or_iri: str,
    active: Sequence[str] | None = None,
    *,
    all_packs: bool = False,
    root: Path | None = None,
) -> Term | None:
    """Resolve a full IRI, a bare local name, or a JSON key.

    Bare names are matched case-sensitively first so ``acceptanceCriteria`` and
    ``AcceptanceCriteria`` -- which differ only by case and mean different
    things -- never resolve to each other.
    """
    if not name_or_iri:
        return None
    terms = index(active, all_packs=all_packs, root=root)
    if name_or_iri in terms:
        return terms[name_or_iri]
    for attr in ("name", "json_key"):
        for term in terms.values():
            if getattr(term, attr) == name_or_iri:
                return term
    lowered = name_or_iri.lower()
    for term in terms.values():
        if term.name.lower() == lowered:
            return term
    return None


def definition(
    path_iri: str,
    active: Sequence[str] | None = None,
    *,
    all_packs: bool = False,
    root: Path | None = None,
) -> tuple[str, str | None] | None:
    """``(definition, attribution)`` for a property IRI, or None when unknown.

    The resolution order that matters for user-facing output: an authored
    ``rdfs:comment`` first, then the gloss for terms UofA does not own, then
    nothing. Never ``sh:message`` -- that states the constraint, which the caller
    already renders as ``Required``, and it would read as a definition while
    saying something else.

    Returning None is the correct answer when the repository has no definition.
    A name-derived guess is forbidden for the same reason the authoring spec
    forbids one.
    """
    term = lookup(path_iri, active, all_packs=all_packs, root=root)
    if term is None or not term.comment:
        entry = EXTERNAL_GLOSS.get(path_iri)
        return (entry[1], entry[0]) if entry else None
    return (term.comment, term.source)


def definition_in(graph, path_iri: str) -> tuple[str, str | None] | None:
    """``definition()`` against a shapes graph the caller already has loaded.

    Validation parses the shapes before it can produce a violation, so building
    a second graph to explain one costs a re-parse of every active pack -- about
    230ms on a command that otherwise takes 125. This reads the graph in hand.

    Scoping is also more correct this way: a violation can only name a path from
    the shapes that were loaded, so the graph that produced it is exactly the
    right place to look, with no need to guess a pack set.

    Same resolution order as ``definition()``, and the same refusal to fall back
    to ``sh:message``.
    """
    if not path_iri or graph is None:
        return None
    from rdflib import URIRef
    from rdflib.namespace import RDFS

    comment = graph.value(URIRef(path_iri), RDFS.comment)
    if comment is not None:
        return (str(comment), None)
    entry = EXTERNAL_GLOSS.get(path_iri)
    return (entry[1], entry[0]) if entry else None
