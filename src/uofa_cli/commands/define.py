"""uofa define / uofa vocab — look up what a vocabulary term means.

The definitions have been readable on the website for a while and unreadable
from the shell. This closes that: the same ``uofa_cli.vocab`` index that puts a
``Means:`` line on a validation failure also answers a direct question.

Two design calls worth naming, both about not lying by omission:

* A term the current context dropped still resolves, and says it was dropped.
  Its IRI is live on uofa.net and packages pinned to an older context still
  carry it, so reporting "not found" would be wrong.
* A term with no definition prints everything that *is* known -- IRI, JSON key,
  constraints -- and says the repository has no definition. A bare miss would be
  indistinguishable from a typo, which sends the reader looking for the wrong
  problem.
"""

from __future__ import annotations

import json

from uofa_cli import paths, vocab
from uofa_cli.output import color, header, info, muted, warn

HELP = "look up what a vocabulary term means"


def add_arguments(parser):
    parser.add_argument("term", nargs="?",
                        help="term to define: local name, full IRI, or JSON key")
    parser.add_argument("--search", metavar="TEXT",
                        help="search labels and definitions for TEXT")
    parser.add_argument("--list", action="store_true", dest="list_terms",
                        help="list the terms in scope")
    parser.add_argument("--all-packs", action="store_true", dest="all_packs",
                        help="cover every installed pack, not just the active ones")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="output format (default: text)")


def run(args) -> int:
    active = paths.resolve_active_packs(args)
    all_packs = bool(getattr(args, "all_packs", False))

    if getattr(args, "search", None):
        return _search(args.search, active, all_packs, args.format)
    if getattr(args, "list_terms", False) or not args.term:
        return _list(active, all_packs, args.format)
    return _define(args.term, active, all_packs, args.format)


# ── shaping ──────────────────────────────────────────────────

def _as_dict(t: vocab.Term) -> dict:
    return {
        "iri": t.iri,
        "name": t.name,
        "namespace": t.namespace,
        "kind": t.kind,
        "label": t.label,
        "definition": t.comment,
        "definitionSource": t.source,
        "domain": t.domain,
        "range": t.range,
        "subClassOf": list(t.subclass_of),
        "deprecated": t.deprecated,
        "jsonKey": t.json_key,
        "since": t.since,
        "droppedIn": t.dropped_in,
        "packs": list(t.packs),
        "constraints": list(t.messages),
    }


def _short(iri: str | None) -> str | None:
    if not iri:
        return None
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if iri.startswith("http") else iri


# ── define ───────────────────────────────────────────────────

def _define(name: str, active, all_packs: bool, fmt: str) -> int:
    term = vocab.lookup(name, active, all_packs=all_packs)
    if term is None and not all_packs:
        # Ask again across every pack before giving up, and say so -- the term
        # may be real but belong to a pack this invocation did not load.
        wider = vocab.lookup(name, all_packs=True)
        if wider is not None:
            if fmt == "json":
                print(json.dumps(_as_dict(wider), indent=2))
                return 0
            _print_term(wider)
            info("")
            info(f"Not in the active pack set ({', '.join(active)}). "
                 f"Defined by: {', '.join(wider.packs) or 'the context only'}.")
            return 0

    if term is None:
        if fmt == "json":
            print(json.dumps({"term": name, "found": False}, indent=2))
        else:
            warn(f"No vocabulary term matches {name!r}.")
            info("Try `uofa define --search TEXT` or `uofa define --list`.")
        return 1

    if fmt == "json":
        print(json.dumps(_as_dict(term), indent=2))
        return 0
    _print_term(term)
    return 0


def _print_term(t: vocab.Term):
    header(t.label or t.name)
    print(f"  {muted(t.iri)}")
    print()

    flags = []
    if t.kind:
        flags.append(t.kind)
    if t.deprecated:
        flags.append(color("deprecated", "yellow"))
    if t.dropped_in:
        last = _previous_version(t)
        # A term added and removed within one version reads as "(v0.6)", not
        # "(v0.6 to v0.6)".
        span = f"{t.since} to {last}" if t.since and t.since != last else last
        flags.append(color(f"not in the current context ({span})", "yellow"))
    elif t.since:
        flags.append(f"since {t.since}")
    if flags:
        print("  " + " · ".join(flags))

    if t.comment:
        print()
        attribution = f" ({t.source})" if t.source else ""
        for line in _wrap(t.comment):
            print(f"  {line}")
        if attribution:
            print(f"  {muted('definition from' + attribution)}")
    else:
        print()
        print(f"  {muted('The repository has no definition for this term.')}")

    rows = []
    if t.json_key and t.json_key != t.name:
        rows.append(("JSON key", t.json_key))
    if t.domain:
        rows.append(("on", _short(t.domain)))
    if t.range:
        rows.append(("value", _short(t.range)))
    for parent in t.subclass_of:
        rows.append(("subclass of", _short(parent)))
    if t.packs:
        rows.append(("constrained by", ", ".join(t.packs)))
    if rows:
        print()
        width = max(len(k) for k, _ in rows)
        for k, v in rows:
            print(f"  {muted(k.rjust(width))}  {v}")

    if t.messages:
        print()
        print(f"  {muted('Constraints')}")
        for m in dict.fromkeys(t.messages):
            for i, line in enumerate(_wrap(m, width=72)):
                print(f"    {'- ' if i == 0 else '  '}{line}")


def _previous_version(t: vocab.Term) -> str:
    """The last context version that carried the term.

    ``dropped_in`` names the current version, which is the one that does *not*
    have it; a reader wants to know where to look for it instead.
    """
    _, versions = vocab._context_terms(paths.find_repo_root())
    if not versions:
        return "an earlier version"
    idx = versions.index(t.dropped_in) if t.dropped_in in versions else len(versions)
    return versions[idx - 1] if idx > 0 else versions[0]


def _wrap(text: str, width: int = 76) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width=width) or [text]


# ── search and list ──────────────────────────────────────────

def _matching(needle: str, active, all_packs: bool) -> list[vocab.Term]:
    needle = needle.lower()
    terms = vocab.index(active, all_packs=all_packs).values()
    return sorted(
        (t for t in terms
         if needle in t.name.lower()
         or needle in (t.label or "").lower()
         or needle in (t.comment or "").lower()),
        key=lambda t: (t.namespace, t.name),
    )


def _search(needle: str, active, all_packs: bool, fmt: str) -> int:
    hits = _matching(needle, active, all_packs)
    if fmt == "json":
        print(json.dumps([_as_dict(t) for t in hits], indent=2))
        return 0 if hits else 1
    if not hits:
        warn(f"Nothing matches {needle!r}.")
        return 1
    header(f"{len(hits)} term(s) matching {needle!r}")
    for t in hits:
        _print_row(t)
    return 0


def _list(active, all_packs: bool, fmt: str) -> int:
    terms = sorted(vocab.index(active, all_packs=all_packs).values(),
                   key=lambda t: (t.namespace, t.name))
    if fmt == "json":
        print(json.dumps([_as_dict(t) for t in terms], indent=2))
        return 0
    scope = "all installed packs" if all_packs else ", ".join(active)
    header(f"{len(terms)} terms in scope ({scope})")
    for t in terms:
        _print_row(t)
    print()
    defined = sum(1 for t in terms if t.comment)
    info(f"{defined} of {len(terms)} carry a definition.")
    return 0


def _print_row(t: vocab.Term):
    tag = ""
    if t.deprecated:
        tag = color(" [deprecated]", "yellow")
    elif t.dropped_in:
        tag = color(" [not current]", "yellow")
    summary = (t.comment or "").split(". ")[0]
    if len(summary) > 64:
        summary = summary[:61] + "..."
    print(f"  {t.name:<34}{tag} {muted(summary)}")
