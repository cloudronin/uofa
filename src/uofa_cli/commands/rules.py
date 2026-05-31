"""uofa rules — run the Jena rule engine for weakener detection.

Spec v0.4 §4.1: `run_structured(args)` returns a typed `RulesResult` so the
interpretation pipeline can consume firings in-process. `run(args)` is a thin
shell that prints from the structured result. The three existing I/O paths
(`--output`, `--raw`, default) are preserved bit-for-bit.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.output import step_header, error, info, color, severity_badge
from uofa_cli import paths

HELP = "detect quality gaps with Jena rule engine (C3)"

# Patterns to colorize in Jena output
_SEVERITY_RE = re.compile(r'\[(Critical|High|Medium|Low)\]')
_COMPOUND_RE = re.compile(r'(⚡\s*COMPOUND-\d+)')
_PATTERN_RE = re.compile(r'(⚠\s*W-[A-Z]+-\d{2})')
_SUMMARY_LINE_RE = re.compile(r'^(\s*)(Critical|High|Medium|Low):\s+(\d+)$')

# Firings parser shared with diff.py (lifted here as the canonical owner).
# Matches engine summary lines like "⚠ W-EP-04 [High] — 6 hit(s)",
# "⚡ COMPOUND-01 [Critical] — 1 hit(s)", and the iso42001 pack's
# descriptive pattern names like "⚠ W-AIMS-AUDIT-STALE [High] — 1 hit(s)"
# or "⚠ W-AIMS-MODEL-EVAL-STALE [High] — 1 hit(s)" (any number of
# UPPERCASE-letter segments after the W-XX prefix).
_FIRING_RE = re.compile(
    r'[⚠⚡]\s+((?:W-[A-Z]{2,}-\d{2}|W-[A-Z]{2,}(?:-[A-Z0-9]+)+|COMPOUND-\d{2}))\s+'
    r'\[(Critical|High|Medium|Low)\]\s+—\s+(\d+)\s+hit'
)


@dataclass(frozen=True)
class RulesResult:
    """Structured result of a Jena rule engine invocation.

    `firings` is populated only when the engine ran in summary format AND
    its output was captured (i.e. not `--output` and not `--raw`). When the
    user requests a different `--format` (jsonld / turtle / ntriples), the
    engine emits RDF instead of the firings list and `firings` is empty —
    consumers that need structured firings should re-run with format=summary
    or parse `stdout` themselves.

    `raw_stdout` is empty in `--output` mode (engine wrote to file) and in
    `--raw` mode (engine printed directly without capture).
    """

    file: Path
    returncode: int
    format: str               # "summary" | "jsonld" | "turtle" | "ntriples"
    raw_stdout: str = ""
    raw_stderr: str = ""
    firings: list[dict] = field(default_factory=list)
    output_path: Path | None = None  # set when --output was used

    @property
    def exit_code(self) -> int:
        return self.returncode


def _ensure_java() -> str:
    """Return the path to a usable java binary (bundled JRE preferred)."""
    try:
        return paths.java_executable()
    except FileNotFoundError:
        raise FileNotFoundError(
            "Java not found. Install Java 17+: https://adoptium.net/\n"
            "  Or skip the rule engine: uofa check FILE --skip-rules"
        )


def _ensure_jar(build: bool):
    jar = paths.jar_path()
    if jar.exists():
        return jar

    if not build:
        raise FileNotFoundError(
            f"Jena engine not built: {jar}\n"
            "  Run: uofa rules FILE --build\n"
            "  Or:  cd weakener-engine && mvn package"
        )

    if not shutil.which("mvn"):
        raise FileNotFoundError(
            "Maven not found. Install Maven 3.8+ to build the rule engine.\n"
            "  Or build manually: cd weakener-engine && mvn package"
        )

    info("Building Jena rule engine...")
    result = subprocess.run(
        ["mvn", "package", "-q"],
        cwd=str(paths.engine_dir()),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        error(f"Maven build failed:\n{result.stderr}")
        raise RuntimeError("Failed to build Jena rule engine")

    return jar


def _colorize_line(line: str) -> str:
    """Apply severity coloring to a single line of rule engine output."""
    # Colorize summary counts: "    Critical:  16"
    m = _SUMMARY_LINE_RE.match(line)
    if m:
        indent, sev, count = m.group(1), m.group(2), m.group(3)
        sev_colors = {"Critical": "red", "High": "yellow", "Medium": "cyan", "Low": "dim"}
        c = sev_colors.get(sev, "dim")
        return f"{indent}{color(sev + ':', c)}  {color(count, c)}"

    # Colorize [Critical], [High], etc. inline
    def _replace_severity(match):
        sev = match.group(1)
        return severity_badge(sev)

    line = _SEVERITY_RE.sub(_replace_severity, line)

    # Colorize compound pattern IDs
    line = _COMPOUND_RE.sub(lambda m: color(m.group(1), "red"), line)

    # Colorize core pattern IDs
    line = _PATTERN_RE.sub(lambda m: color(m.group(1), "yellow"), line)

    return line


def _combine_rules_files(rules_paths: list[Path]) -> Path:
    """Concatenate multiple rules files into a single temp file."""
    if len(rules_paths) == 1:
        return rules_paths[0]

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".rules", delete=False)
    seen_prefixes = set()
    for rp in rules_paths:
        content = rp.read_text()
        # Deduplicate @prefix declarations
        lines = []
        for line in content.splitlines():
            if line.strip().startswith("@prefix"):
                if line.strip() not in seen_prefixes:
                    seen_prefixes.add(line.strip())
                    lines.append(line)
            else:
                lines.append(line)
        tmp.write("\n".join(lines))
        tmp.write("\n\n")
    tmp.close()
    return Path(tmp.name)


def parse_firings(stdout_text: str) -> list[dict]:
    """Parse Jena engine summary output into a deduplicated firings list.

    Each firing dict has ``patternId``, ``severity``, ``hits``. Order
    preserved by first occurrence (matches the engine's output order).

    Public so the interpretation pipeline can re-parse stdout from a
    pre-existing rules invocation (the standalone ``uofa explain --from-file``
    case in spec §3.3).
    """
    seen: dict[str, dict] = {}
    for m in _FIRING_RE.finditer(stdout_text):
        pid, sev, hits = m.group(1), m.group(2), int(m.group(3))
        if pid not in seen:
            seen[pid] = {"patternId": pid, "severity": sev, "hits": hits}
    return list(seen.values())


def attribute_firings(firings: list[dict], root: Path | None = None) -> list[dict]:
    """Stamp each firing with the detection pack that owns its patternId (§5/§7.3).

    Adds a ``pack`` key — the owning pack name, or ``None`` for an unrecognized
    patternId — so the reasoned output records *which detection pack fired which
    weakener* (the §7.3 auditability requirement). Uses the manifest-built index
    (``paths.patternid_pack_index``), the same data the loader uses. Mutates and
    returns ``firings``.
    """
    index = paths.patternid_pack_index(root)
    for firing in firings:
        pid = firing.get("patternId")
        if pid:
            firing["pack"] = index.get(pid)
    return firings


# Pattern descriptions live in .rules files as `# W-XX-NN: <description>`
# header comments preceding each rule block (or descriptive form like
# `# W-AIMS-AUDIT-STALE: <description>` for the iso42001 pack). Parsing
# them gives the interpretation pipeline the human-readable name without
# forcing the engine to round-trip them through JSON-LD.
_PATTERN_DESC_RE = re.compile(
    r"^#\s*((?:W-[A-Z]{2,}-\d{2}|W-[A-Z]{2,}(?:-[A-Z0-9]+)+|COMPOUND-\d{2}))\s*:\s*(.+?)\s*$",
    re.MULTILINE,
)


# Engine vocab IRIs used in jsonld output. Defined as constants so the
# parser breaks loudly if the engine schema changes vs silently producing
# empty firings.
_VOCAB = "https://uofa.net/vocab#"
_TYPE_WEAKENER_ANNOTATION = f"{_VOCAB}WeakenerAnnotation"
_PROP_PATTERN_ID = f"{_VOCAB}patternId"
_PROP_SEVERITY = f"{_VOCAB}severity"
_PROP_AFFECTED_NODE = f"{_VOCAB}affectedNode"
_PROP_ESCALATION_SOURCE = f"{_VOCAB}escalationSource"
_PROP_DESCRIPTION = "https://schema.org/description"


def parse_firings_jsonld(jsonld_text: str) -> list[dict]:
    """Parse the engine's `--format jsonld` output into rich firing dicts.

    Returns one dict per *patternId* (aggregated across hits, mirroring
    `parse_firings`) but with the data the summary-mode parser loses:

        {
            "patternId":           "W-EP-04",
            "severity":            "High",
            "hits":                6,
            "description":         "Credibility factor is not assessed but ...",
            "affected_nodes":      ["https://...factor/use-error", ...],
            "escalation_sources":  [],   # populated only for compound patterns
        }

    Used by the `--explain` pipeline (spec §4.3) to give the LLM the actual
    affected-node IRIs so explanations can ground in specific evidence.
    Public so the standalone `uofa explain --from-file` path can re-parse
    cached engine output.

    The shape is per-patternId (not per-individual-firing) so the
    interpretation pipeline runs one LLM call per pattern, not one per hit
    — a Critical pattern firing 7 times still produces a single
    explanation that lists all seven affected nodes.

    Args:
        jsonld_text: Stdout from `uofa rules <file> --format jsonld`. Must
            be a JSON-LD document with a top-level `@graph` array.

    Returns:
        List of firing dicts in first-occurrence order (matches the
        engine's emit order). Empty when the document has no
        WeakenerAnnotations.
    """
    try:
        doc = json.loads(jsonld_text)
    except json.JSONDecodeError:
        return []

    graph = doc.get("@graph") if isinstance(doc, dict) else None
    if not isinstance(graph, list):
        return []

    aggregated: dict[str, dict] = {}
    order: list[str] = []

    for node in graph:
        if not isinstance(node, dict):
            continue
        if node.get("@type") != _TYPE_WEAKENER_ANNOTATION:
            continue

        pid = _str_or_empty(node.get(_PROP_PATTERN_ID))
        if not pid:
            continue

        if pid not in aggregated:
            aggregated[pid] = {
                "patternId": pid,
                "severity": _str_or_empty(node.get(_PROP_SEVERITY)) or "Medium",
                "hits": 0,
                "description": _str_or_empty(node.get(_PROP_DESCRIPTION)),
                "affected_nodes": [],
                "escalation_sources": [],
            }
            order.append(pid)

        agg = aggregated[pid]
        agg["hits"] += 1

        affected = node.get(_PROP_AFFECTED_NODE)
        affected_iri = _extract_iri(affected)
        if affected_iri and affected_iri not in agg["affected_nodes"]:
            agg["affected_nodes"].append(affected_iri)

        # escalationSource may be a single object or a list of objects;
        # each is either {"@id": "..."} (IRI/blank-node ref) or a nested
        # dict. We collect the @id strings for resolution by the context
        # extractor.
        sources = node.get(_PROP_ESCALATION_SOURCE)
        for src_iri in _extract_iri_list(sources):
            if src_iri not in agg["escalation_sources"]:
                agg["escalation_sources"].append(src_iri)

    return [aggregated[pid] for pid in order]


def parse_individual_annotations(jsonld_text: str) -> list[dict]:
    """Per-annotation parse (no aggregation by patternId).

    Returns one dict per WeakenerAnnotation in the engine's jsonld output,
    keyed by the annotation's `@id` so callers can resolve compound
    `escalation_sources` blank-node references back to the constituent
    firings. Each dict carries:

        {
            "id":            "_:b1",                     # blank-node id from engine
            "patternId":     "W-AL-01",
            "severity":      "High",
            "affected_node": "https://...factor/abc",    # the IRI
            "description":   "...",                      # from schema:description
        }

    Used by the interpretation pipeline to pretty-print "COMPOUND-01 fires
    because W-AL-01 (Missing UQ) and W-EP-04 (Unassessed Factor) both
    fired" — the per-pattern aggregation in `parse_firings_jsonld` loses
    the blank-node identity needed for that mapping.
    """
    try:
        doc = json.loads(jsonld_text)
    except json.JSONDecodeError:
        return []

    graph = doc.get("@graph") if isinstance(doc, dict) else None
    if not isinstance(graph, list):
        return []

    out: list[dict] = []
    for node in graph:
        if not isinstance(node, dict):
            continue
        if node.get("@type") != _TYPE_WEAKENER_ANNOTATION:
            continue
        out.append({
            "id": _str_or_empty(node.get("@id")),
            "patternId": _str_or_empty(node.get(_PROP_PATTERN_ID)),
            "severity": _str_or_empty(node.get(_PROP_SEVERITY)) or "Medium",
            "affected_node": _extract_iri(node.get(_PROP_AFFECTED_NODE)),
            "description": _str_or_empty(node.get(_PROP_DESCRIPTION)),
        })
    return out


def _str_or_empty(value) -> str:
    """Coerce a JSON-LD literal to plain str. Handles `{"@value": "..."}` form
    plus bare strings. Returns empty string on anything unexpected."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        v = value.get("@value")
        if isinstance(v, str):
            return v
    return ""


def _extract_iri(value) -> str:
    """Pull `@id` out of a `{"@id": "..."}` dict; handle list-of-one."""
    if isinstance(value, dict):
        iri = value.get("@id")
        if isinstance(iri, str):
            return iri
    if isinstance(value, list) and value:
        return _extract_iri(value[0])
    if isinstance(value, str):
        return value
    return ""


def _extract_iri_list(value) -> list[str]:
    """Same as `_extract_iri` but always returns a list (single, list, or empty)."""
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            iri = _extract_iri(item)
            if iri:
                out.append(iri)
        return out
    iri = _extract_iri(value)
    return [iri] if iri else []


def parse_pattern_descriptions(rules_text: str) -> dict[str, str]:
    """Extract pattern descriptions from a .rules file's comment headers.

    Returns a dict mapping patternId → human-readable description (e.g.
    `{"W-EP-04": "Unassessed Factor at Elevated Risk"}`).

    Accepts the file *content* rather than a path so callers can compose
    multiple files without re-reading.
    """
    return {m.group(1): m.group(2).strip() for m in _PATTERN_DESC_RE.finditer(rules_text)}


def load_pattern_descriptions(pack_name: str | None = None) -> dict[str, str]:
    """Load pattern descriptions from every .rules file in scope.

    Walks the active pack chain via `paths.all_rules_files()`. When
    `pack_name` is given, also walks that pack's `rules/` dir directly
    so descriptions from non-active packs (e.g. `nasa-7009b` when
    interpreting an NASA package while `vv40` is active) still resolve.

    Returns a merged dict; on duplicate patternIds, last write wins (no
    current pack defines duplicates).

    Used by `context.extract_firing_contexts` to enrich each
    FiringContext with its pattern's description so the LLM doesn't
    fall back to "the specific nature of W-EP-04 cannot be determined
    from the provided input."
    """
    descriptions: dict[str, str] = {}

    # Active pack's rules (uses paths' default chain — typically core + vv40).
    try:
        for rp in paths.all_rules_files():
            try:
                descriptions.update(parse_pattern_descriptions(rp.read_text(encoding="utf-8")))
            except OSError:
                pass
    except (FileNotFoundError, KeyError):
        pass

    # Pack-specific rules dir (covers non-active packs).
    if pack_name:
        try:
            pack_root = paths.pack_dir(pack_name)
            rules_dir = pack_root / "rules"
            if rules_dir.is_dir():
                for rp in sorted(rules_dir.glob("*.rules")):
                    try:
                        descriptions.update(parse_pattern_descriptions(rp.read_text(encoding="utf-8")))
                    except OSError:
                        pass
        except (FileNotFoundError, KeyError):
            pass

    return descriptions


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to analyze")
    parser.add_argument("--rules", "-r", type=Path, help="path to .rules file")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--build", action="store_true", help="auto-build the Jena JAR if missing")
    parser.add_argument("--raw", action="store_true", help="show raw output without coloring")
    parser.add_argument("--format", "-f", default="summary",
                        choices=["summary", "turtle", "ntriples", "jsonld", "json"],
                        help="output format (default: summary). 'json' is the parsed-firings "
                             "shape suitable for snapshot tests; 'jsonld' is the raw RDF.")
    parser.add_argument("--output", "-o", type=Path,
                        help="write reasoned output to a file (default: stdout)")
    # --explain* flag set (spec §3.2) — shared across the four target commands.
    from uofa_cli.interpretation.cli import add_explain_arguments
    add_explain_arguments(parser)


def run_structured(args) -> RulesResult:
    """Run the Jena rule engine and return a typed result.

    Does NOT print — `run()` is the I/O shell. For `--output` and `--raw`
    modes the engine writes/prints directly (capture would change behavior),
    so the returned `raw_stdout` is empty in those modes.
    """
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    java = _ensure_java()
    jar = _ensure_jar(args.build)

    if args.rules:
        rules = args.rules
    else:
        rules_list = paths.all_rules_files(args.file)
        rules = _combine_rules_files(rules_list)

    ctx = args.context or paths.context_file()

    cmd = [java, "-jar", str(jar), str(args.file), "--rules", str(rules), "--context", str(ctx)]
    fmt = args.format or "summary"
    if fmt and fmt != "summary":
        cmd += ["--format", fmt]
    if args.output:
        cmd += ["--output", str(args.output)]

    # If writing to a file, the engine produces no stdout content for the
    # caller to colorize — just pipe through.
    if args.output or args.raw:
        result = subprocess.run(cmd, capture_output=False)
        return RulesResult(
            file=args.file,
            returncode=result.returncode,
            format=fmt,
            output_path=args.output if args.output else None,
        )

    # Capture and (later) colorize output. Force UTF-8 decoding so the Java
    # subprocess's box-drawing/severity glyphs (`══`, `⚠`, `⚡`, `✓`, `✗`)
    # round-trip cleanly through the parent's stdout regardless of the
    # caller's locale. Windows defaults to cp1252, which would mojibake
    # those bytes into `?`. errors='replace' is the belt-and-suspenders
    # fallback.
    completed = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )

    # Firings are NOT pack-attributed here: run_structured().firings feeds the C3
    # check report, whose serialization is a byte-stable backward-compat contract
    # (tests/oos/test_production_oos.py::test_55). Pack provenance (§5/§7.3) is
    # applied at the evidence/action boundary by the consumer that records it —
    # the guardrail — via attribute_firings, not ambiently injected into every report.
    firings = parse_firings(completed.stdout) if fmt == "summary" else []
    return RulesResult(
        file=args.file,
        returncode=completed.returncode,
        format=fmt,
        raw_stdout=completed.stdout,
        raw_stderr=completed.stderr,
        firings=firings,
    )


def run(args) -> int:
    # `--format json`: clean parsed-firings shape for snapshot tests / external
    # tooling. Runs the engine in jsonld mode internally, parses with the
    # existing parse_firings_jsonld helper, and emits a stable JSON document.
    # No coloring, no headers — pure data on stdout.
    if getattr(args, "format", None) == "json":
        original_format = args.format
        args.format = "jsonld"
        try:
            result = run_structured(args)
        finally:
            args.format = original_format
        firings = parse_firings_jsonld(result.raw_stdout)
        severity_counts: dict[str, int] = {}
        for f in firings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + f["hits"]
        document = {
            "file": str(args.file),
            "summary": {
                "total_firings": sum(f["hits"] for f in firings),
                "patterns": len(firings),
                "by_severity": severity_counts,
            },
            "firings": firings,
        }
        print(json.dumps(document, indent=2))
        return result.returncode

    step_header("C3: Jena rule engine — weakener detection")
    sys.stdout.flush()

    result = run_structured(args)

    # --output / --raw paths: engine already wrote the data; nothing more to do.
    if args.output or args.raw:
        return result.returncode

    for line in result.raw_stdout.splitlines():
        print(_colorize_line(line))

    if result.raw_stderr:
        print(result.raw_stderr, file=sys.stderr, end="")

    # ── --explain pipeline (spec §3.1) ────────────────────────
    if getattr(args, "explain", False) and result.returncode == 0:
        _run_explain(args, result)

    return result.returncode


def _run_explain(args, result: RulesResult) -> None:
    """Invoke the interpretation pipeline and print the result.

    Graceful degradation per spec §3.7: any LLMError → notice + exit 0
    (the analysis succeeded; interpretation is opt-in). Engineered to
    never raise to the caller.

    Round 1 (P-B iteration): re-invokes the rule engine in jsonld mode
    to capture rich firing data (affected node IRIs + escalation sources
    for compounds). This costs one extra subprocess call when --explain
    is set, in exchange for the LLM seeing actual evidence labels rather
    than just patternId+severity+hits. See [round1_audit.md].
    """
    import json as _json
    from uofa_cli.interpretation import interpret_rules_output
    from uofa_cli.interpretation.cli import (
        args_to_options, print_degradation, print_envelope,
    )
    from uofa_cli.llm.errors import LLMError

    try:
        package_doc = _json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        # Couldn't parse the package — degrade.
        print_degradation(
            LLMError(f"Could not load package for interpretation: {exc}"),
            mode="explain",
            format=args.explain_format or "text",
            command="rules",
            structured_output={"firings": result.firings},
        )
        return

    # Re-invoke the engine in jsonld mode for rich firing data. Reuse the
    # same args namespace but flip format. If this fails (Java not
    # installed, etc.), fall back gracefully — interpretation runs in
    # legacy mode without enrichment, which is no worse than Round 0.
    jsonld_firings = None
    individual_annotations = None
    try:
        import argparse as _ap
        jsonld_args = _ap.Namespace(
            file=args.file,
            rules=getattr(args, "rules", None),
            context=getattr(args, "context", None),
            build=getattr(args, "build", False),
            raw=False, format="jsonld", output=None,
        )
        jsonld_result = run_structured(jsonld_args)
        if jsonld_result.returncode == 0 and jsonld_result.raw_stdout:
            jsonld_firings = parse_firings_jsonld(jsonld_result.raw_stdout)
            individual_annotations = parse_individual_annotations(jsonld_result.raw_stdout)
    except (FileNotFoundError, RuntimeError):
        # Engine unavailable for the second invocation — proceed without
        # rich data. Pre-Round-1 behavior.
        pass

    try:
        env = interpret_rules_output(
            structured_output={"firings": result.firings},
            package_doc=package_doc,
            firings=result.firings,
            jsonld_firings=jsonld_firings,
            individual_annotations=individual_annotations,
            options=args_to_options(args, pack_name=_active_pack_name()),
        )
    except LLMError as exc:
        print_degradation(
            exc, mode="explain", format=args.explain_format or "text",
            command="rules", structured_output={"firings": result.firings},
        )
        return

    print_envelope(env, format=args.explain_format or "text")


def _active_pack_name() -> str:
    """Return the first active pack name; defaults to 'vv40'."""
    try:
        active = paths.get_active_pack()
        return active[0] if active else "vv40"
    except Exception:  # noqa: BLE001
        return "vv40"
