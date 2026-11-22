"""Calculation verification: run FDA SimEval `calcverif` on a declared mesh study.

The question this answers: does the mesh study in the evidence folder support
the discretization error number the report claims? UofA measures and compares.
It does not say which number is right.

Four disciplines, none of them optional:

  * **Nothing is inferred.** The engineer declares the table, the columns, the
    refinement kind, the formal order and the reported index. A column is never
    bound by its name, and an unknown key in the declaration is an error, so a
    typo cannot quietly turn a declared value into an absent one.
  * **The tool decides, the wrapper reads.** The vendored module is called as
    shipped. What it computes but does not return (the safety factor, the
    convergence type, the constrained order) is recovered by calling its own
    methods or solving its own GCI formula backward. Nothing here re-decides.
  * **Hash what is read.** The table's bytes are read once, hashed, and parsed
    from those same bytes. If they are not the bytes the seal recorded, the
    study does not run. The tool's digest is taken from the file imported.
  * **Absent means absent.** No formal order, no `cvFormalOrder`. No reported
    value, no comparison. A value that could not be recovered is left out, not
    filled with a plausible one. There are no decision words in a record.

Three statuses support different claims and are kept apart: `computed` (the
tool returned numbers), `no-estimate` (the tool ran on the data and refused),
and `not-run` (UofA could not run the tool; the gap is the assessor's, not the
record's).
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

from uofa_cli import corroborate
from uofa_cli.solver.facts import SolverEvidence, SolverFact

SCHEMA = "uofa-mesh-study/v0.1"

TOOL_NAME = "SimEval calcverif"
TOOL_COMMIT = "4a70fd3b364c0d4aa14d49a433ba7c4994c04cc3"
OUTPUT_LIMIT = 2000
INSTALL_HINT = "pip install 'uofa[calcverif]'"

# The pack's quantityIdentity key for a relative grid convergence index.
GCI_RELATIVE = "verification.gci_relative"
_GCI_ABSOLUTE = "verification.gci_absolute"  # call-local; never written anywhere

COMPUTED = "computed"
NO_ESTIMATE = "no-estimate"
NOT_RUN = "not-run"

DIVERGING = "diverging"
OSCILLATORY_THREE = "oscillatory-three-meshes"
DEPENDENCY_MISSING = "dependency-missing"
TABLE_NOT_SEALED = "table-not-sealed"
INVALID_INPUT = "invalid-input"
TOO_FEW_LEVELS = "too-few-levels"

ELEMENT_COUNT = "element-count"
MESH_SIZE = "mesh-size"

WITHIN = "within-tolerance"
OUTSIDE = "outside-tolerance"
NO_FORMAL = "no-formal-order"

# The tool's own label for a monotonically converging triplet
# (analyze_largeN_mono_case). Read, never re-derived.
_TOOL_MONOTONIC = "converging (monotonic)"
# The tool's two safety factors (_calculate_GCI).
_SAFETY_FACTORS = (1.25, 3.0)
_FS_MATCH = 1e-9

_STUDY_KEYS = {"id", "forFactorType", "table", "quantityColumn", "quantityUnits",
               "refinement", "formalOrder", "reported"}
_REFINEMENT_KEYS = {"column", "kind", "dimension"}
_REPORTED_KEYS = {"value", "units", "basis", "source"}


class MeshStudyDeclarationError(ValueError):
    """The declaration file itself is malformed. Nothing is run or written."""


@dataclass(frozen=True)
class Reported:
    value: float
    units: str
    basis: str
    source: str = ""


@dataclass(frozen=True)
class StudyDeclaration:
    id: str
    for_factor_type: str
    table: str
    quantity_column: str
    refinement_column: str
    refinement_kind: str
    quantity_units: str | None = None
    dimension: int | None = None
    formal_order: float | None = None
    reported: Reported | None = None


# ── Declaration ─────────────────────────────────────────────────────────────


def load_declaration(path: Path, factor_names) -> list[StudyDeclaration]:
    """Read and check a mesh study declaration.

    `factor_names` are the active pack's factor names; `forFactorType` must be
    one of them, so the join the rules make is against a name the pack has.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise MeshStudyDeclarationError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise MeshStudyDeclarationError(f"{path} is not JSON: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schemaVersion") != SCHEMA:
        raise MeshStudyDeclarationError(
            f"{path}: schemaVersion must be {SCHEMA!r}")
    studies = raw.get("studies")
    if not isinstance(studies, list) or not studies:
        raise MeshStudyDeclarationError(f"{path}: 'studies' must be a non-empty list")
    extra = set(raw) - {"schemaVersion", "studies"}
    if extra:
        raise MeshStudyDeclarationError(f"{path}: unknown key(s) {sorted(extra)}")

    names = set(factor_names)
    out: list[StudyDeclaration] = []
    seen: set[str] = set()
    for i, study in enumerate(studies):
        decl = _one_declaration(study, f"{path}: studies[{i}]", names)
        if decl.id in seen:
            raise MeshStudyDeclarationError(f"{path}: duplicate study id {decl.id!r}")
        seen.add(decl.id)
        out.append(decl)
    return out


def _one_declaration(study, where: str, names: set[str]) -> StudyDeclaration:
    if not isinstance(study, dict):
        raise MeshStudyDeclarationError(f"{where} must be an object")
    _no_unknown(study, _STUDY_KEYS, where)
    sid = _text(study, "id", where)
    factor = _text(study, "forFactorType", where)
    if factor not in names:
        raise MeshStudyDeclarationError(
            f"{where}: forFactorType {factor!r} is not a factor of the active pack")
    table = _text(study, "table", where)
    posix = PurePosixPath(table)
    if posix.is_absolute() or ".." in posix.parts or "\\" in table:
        raise MeshStudyDeclarationError(
            f"{where}: table must be a path relative to the evidence root")
    quantity = _text(study, "quantityColumn", where)
    units = study.get("quantityUnits")
    if units is not None and (not isinstance(units, str) or not units):
        raise MeshStudyDeclarationError(f"{where}: quantityUnits must be a non-empty string")

    ref = study.get("refinement")
    if not isinstance(ref, dict):
        raise MeshStudyDeclarationError(f"{where}: 'refinement' must be an object")
    _no_unknown(ref, _REFINEMENT_KEYS, f"{where}.refinement")
    column = _text(ref, "column", f"{where}.refinement")
    kind = ref.get("kind")
    if kind not in (ELEMENT_COUNT, MESH_SIZE):
        raise MeshStudyDeclarationError(
            f"{where}.refinement.kind must be {ELEMENT_COUNT!r} or {MESH_SIZE!r}")
    dimension = ref.get("dimension")
    if kind == ELEMENT_COUNT:
        if isinstance(dimension, bool) or dimension not in (1, 2, 3):
            raise MeshStudyDeclarationError(
                f"{where}.refinement.dimension must be 1, 2 or 3 for {ELEMENT_COUNT}")
    elif dimension is not None:
        raise MeshStudyDeclarationError(
            f"{where}.refinement.dimension applies only to {ELEMENT_COUNT}")

    formal = study.get("formalOrder")
    if formal is not None:
        if not _is_number(formal) or not formal > 0:
            raise MeshStudyDeclarationError(f"{where}: formalOrder must be a number > 0")
        formal = float(formal)

    reported = None
    if "reported" in study:
        rep = study["reported"]
        if not isinstance(rep, dict):
            raise MeshStudyDeclarationError(f"{where}: 'reported' must be an object")
        _no_unknown(rep, _REPORTED_KEYS, f"{where}.reported")
        if not _is_number(rep.get("value")):
            raise MeshStudyDeclarationError(f"{where}.reported.value must be a number")
        rep_units = _text(rep, "units", f"{where}.reported")
        basis = rep.get("basis")
        if basis not in ("relative", "absolute"):
            raise MeshStudyDeclarationError(
                f"{where}.reported.basis must be 'relative' or 'absolute'")
        source = rep.get("source", "")
        if not isinstance(source, str):
            raise MeshStudyDeclarationError(f"{where}.reported.source must be a string")
        reported = Reported(float(rep["value"]), rep_units, basis, source)

    return StudyDeclaration(
        id=sid, for_factor_type=factor, table=posix.as_posix(),
        quantity_column=quantity, refinement_column=column, refinement_kind=kind,
        quantity_units=units, dimension=dimension if kind == ELEMENT_COUNT else None,
        formal_order=formal, reported=reported)


def _no_unknown(obj: dict, allowed: set[str], where: str) -> None:
    extra = set(obj) - allowed
    if extra:
        raise MeshStudyDeclarationError(f"{where}: unknown key(s) {sorted(extra)}")


def _text(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MeshStudyDeclarationError(f"{where}.{key} must be a non-empty string")
    return value


def _is_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


# ── Running ─────────────────────────────────────────────────────────────────


def sealed_digests(seal) -> dict[str, str]:
    """Top-level artifact path -> `sha256:<hex>`, from an `EvidenceSeal`."""
    return {a.path: a.sha256 for a in seal.artifacts}


def run_studies(declarations: list[StudyDeclaration], root: Path,
                sealed: Mapping[str, str], identity: dict | None) -> list[dict]:
    """One record per declared study, in declaration order."""
    return [run_study(d, Path(root), sealed, identity) for d in declarations]


def run_study(decl: StudyDeclaration, root: Path, sealed: Mapping[str, str],
              identity: dict | None) -> dict:
    record = _base_record(decl)

    digest = sealed.get(decl.table)
    if digest is None:
        return _not_run(record, TABLE_NOT_SEALED,
                        f"{decl.table} is not in the sealed artifact manifest")
    try:
        data = (root / decl.table).read_bytes()
    except OSError as exc:
        return _not_run(record, TABLE_NOT_SEALED, f"{decl.table} could not be read: {exc}")
    read_digest = "sha256:" + hashlib.sha256(data).hexdigest()
    if read_digest != digest:
        return _not_run(record, TABLE_NOT_SEALED,
                        f"the bytes read from {decl.table} are not the bytes the seal recorded")
    record["cvSourceSha256"] = read_digest

    parsed = _parse_table(data, decl)
    if isinstance(parsed, str):
        return _not_run(record, INVALID_INPUT, parsed)
    levels = parsed
    if len(levels) < 3:
        return _not_run(record, TOO_FEW_LEVELS,
                        f"{len(levels)} level(s) in {decl.table}; at least 3 are needed")
    # Finest first: most elements, or smallest mesh size. Stable; ties are left
    # for the tool to refuse.
    levels.sort(key=lambda lv: -lv[1] if decl.refinement_kind == ELEMENT_COUNT else lv[1])
    record["cvLevel"] = [
        {"cvIndex": i, "cvRefinement": ref, "cvQoi": q, "cvSourceRow": row}
        for i, (row, ref, q) in enumerate(levels)]

    try:
        tool, np, tool_digest = _load_tool()
    except ImportError as exc:
        return _not_run(record, DEPENDENCY_MISSING,
                        f"{exc.name or 'a dependency'} is not installed; {INSTALL_HINT}")
    record.update({"cvTool": TOOL_NAME, "cvToolCommit": TOOL_COMMIT,
                   "cvToolSha256": tool_digest})

    refinement = np.asarray([lv[1] for lv in levels], dtype=float)
    qoi = np.asarray([lv[2] for lv in levels], dtype=float)
    outputs: list[str] = []

    absolute = _invoke(tool, decl, refinement, qoi, absolute=True)
    outputs.append(absolute.output)
    if absolute.error is not None:
        _set_output(record, outputs)
        return _not_run(record, INVALID_INPUT, absolute.error)
    instance = absolute.instance
    record["cvMethod"] = instance.method
    conv = instance._check_oscillatory_status(qoi[0], qoi[1], qoi[2])
    record["cvConvergenceType"] = conv.name.lower().replace("_", "-")

    if absolute.result == (None, None, None):
        _set_output(record, outputs)
        record["cvStatus"] = NO_ESTIMATE
        reason = _refusal_reason(conv.name, len(levels))
        if reason is not None:
            record["cvReason"] = reason
        else:
            record["cvReasonDetail"] = (
                f"the tool returned no estimate; convergence type {conv.name} "
                f"with {len(levels)} levels does not explain it")
        return record

    ooc, re, gci_abs = (float(v) for v in absolute.result)
    relative = _invoke(tool, decl, refinement, qoi, absolute=False)
    outputs.append(relative.output)
    gci_rel = None if relative.error is not None else float(relative.result[2])

    record["cvStatus"] = COMPUTED
    record["cvObservedOrder"] = ooc
    constrained = float(instance._compute_constrained_OOC(
        ooc, decl.formal_order, suppress_message=True))
    record["cvConstrainedOrder"] = constrained
    warnings_out: list[str] = []
    fs = _recover_safety_factor(instance, gci_abs, constrained)
    if fs is None:
        warnings_out.append("safety factor not recovered: the back-solved value "
                            "matches neither 1.25 nor 3 to 1e-9")
    else:
        record["cvSafetyFactor"] = fs
    if decl.formal_order is None:
        record["cvOrderAgreement"] = NO_FORMAL
    elif fs is not None:
        record["cvOrderAgreement"] = WITHIN if fs == 1.25 else OUTSIDE
    record["cvRichardsonValue"] = float(re)
    record["cvGciAbsolute"] = gci_abs
    if gci_rel is not None:
        record["cvGciRelative"] = gci_rel
    else:
        warnings_out.append(f"relative index not computed: {relative.error}")

    triplets = _triplets(instance)
    if triplets is not None:
        record["cvTriplet"] = triplets
        later = [t["cvConvergence"] for t in triplets[1:]]
        record["cvTripletConcern"] = "true" if any(c != _TOOL_MONOTONIC for c in later) else "false"

    if decl.reported is not None:
        verdict, detail = _compare(decl, gci_abs, gci_rel, relative.error, identity)
        record["cvGciComparison"] = verdict
        if detail:
            record["cvGciComparisonDetail"] = detail
    if warnings_out:
        record["cvWarnings"] = warnings_out
    _set_output(record, outputs)
    return record


def _base_record(decl: StudyDeclaration) -> dict:
    record = {"cvStudyId": decl.id, "forFactorType": decl.for_factor_type,
              "cvQuantity": decl.quantity_column}
    if decl.quantity_units is not None:
        record["cvQuantityUnits"] = decl.quantity_units
    record["cvSourceMember"] = decl.table
    record["cvRefinementKind"] = decl.refinement_kind
    if decl.dimension is not None:
        record["cvDimension"] = decl.dimension
    if decl.formal_order is not None:
        record["cvFormalOrder"] = decl.formal_order
    if decl.reported is not None:
        rep = {"cvValue": decl.reported.value, "cvUnits": decl.reported.units,
               "cvBasis": decl.reported.basis}
        if decl.reported.source:
            rep["cvSource"] = decl.reported.source
        record["cvReportedGci"] = rep
    return record


def _not_run(record: dict, reason: str, detail: str) -> dict:
    record["cvStatus"] = NOT_RUN
    record["cvReason"] = reason
    record["cvReasonDetail"] = detail
    return record


def _parse_table(data: bytes, decl: StudyDeclaration):
    """[(source row, refinement, qoi)], or a string saying why not. No row is dropped."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return f"{decl.table} is not UTF-8 text: {exc}"
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    for column in (decl.refinement_column, decl.quantity_column):
        if column not in header:
            return f"column {column!r} is not in {decl.table} (columns: {', '.join(header)})"
    levels = []
    for n, row in enumerate(reader, start=1):
        values = []
        for column in (decl.refinement_column, decl.quantity_column):
            cell = (row.get(column) or "").strip()
            number = _number(cell)
            if number is None:
                return f"data row {n}, column {column!r}: {cell!r} is not a finite number"
            values.append(number)
        levels.append((n, values[0], values[1]))
    return levels


def _number(cell: str):
    try:
        return int(cell)
    except ValueError:
        pass
    try:
        value = float(cell)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _load_tool():
    """Import the vendored tool headless: (module, numpy, sha256 of the file imported).

    Raises ImportError when the `calcverif` extra is not installed.
    """
    import matplotlib
    matplotlib.use("Agg")
    import numpy
    from uofa_cli._vendor.simeval import calcverif
    digest = hashlib.sha256(Path(calcverif.__file__).read_bytes()).hexdigest()
    return calcverif, numpy, digest


@dataclass
class _Invocation:
    instance: object
    result: tuple | None
    output: str
    error: str | None


def _invoke(tool, decl: StudyDeclaration, refinement, qoi, *, absolute: bool) -> _Invocation:
    instance = tool.CalculationVerificationTool(
        suppress_output=False, use_absolute_GCI=absolute)
    buf = io.StringIO()
    error = None
    result = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with contextlib.redirect_stdout(buf):
            try:
                if decl.refinement_kind == ELEMENT_COUNT:
                    result = instance.analyze_by_n_elems(
                        refinement, decl.dimension, qoi, formal_order_conv=decl.formal_order)
                else:
                    result = instance.analyze(
                        refinement, qoi, formal_order_conv=decl.formal_order)
            except ValueError as exc:
                error = str(exc)
            except AssertionError as exc:
                error = f"the tool's input assertion did not hold{': ' + str(exc) if str(exc) else ''}"
    text = buf.getvalue()
    for w in caught:
        text += f"warning: {w.category.__name__}: {w.message}\n"
    return _Invocation(instance, result, text, error)


def _refusal_reason(conv_name: str, n_levels: int) -> str | None:
    if conv_name in ("MONOTONIC_DIVERGENCE", "OSCILLATORY_DIVERGENCE"):
        return DIVERGING
    if conv_name == "OSCILLATORY_CONVERGENCE" and n_levels == 3:
        return OSCILLATORY_THREE
    return None


def _recover_safety_factor(instance, gci_abs: float, constrained: float) -> float | None:
    """Solve the tool's own formula backward for Fs.

    The tool computes `gci = Fs / (r21**p - 1) * |q2 - q1|` with r21 and q from
    the two finest levels it used (`last_h_values`, `last_qoi_values`) and p the
    constrained order. It does not return Fs.
    """
    h = instance.last_h_values
    q = instance.last_qoi_values
    diff = abs(float(q[1]) - float(q[0]))
    if diff == 0:
        return None
    r21 = float(h[1]) / float(h[0])
    fs = gci_abs * (r21 ** constrained - 1) / diff
    for candidate in _SAFETY_FACTORS:
        if abs(fs - candidate) <= _FS_MATCH:
            return candidate
    return None


def _triplets(instance) -> list[dict] | None:
    table = getattr(instance, "intermediate_triplet_metrics", None)
    if instance.method != "largeN_mono" or table is None:
        return None
    out = []
    for i, row in enumerate(table.itertuples(index=False)):
        entry = {"cvIndex": i, "cvMeshes": str(row.triplet),
                 "cvConvergence": str(row.convergence)}
        for key, value in (("cvObservedOrder", row.OOC), ("cvRichardsonValue", row.RE),
                           ("cvGciAbsolute", row.GCI)):
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                entry[key] = float(value)
        out.append(entry)
    return out


def _compare(decl: StudyDeclaration, gci_abs: float, gci_rel: float | None,
             rel_error: str | None, identity: dict | None) -> tuple[str, str]:
    """Reported index against the recomputed one, through `corroborate`."""
    rep = decl.reported
    identity = identity or {}
    if rep.basis == "relative":
        if gci_rel is None:
            return corroborate.NOT_COMPARABLE, f"the tool computed no relative index: {rel_error}"
        spec = identity.get(GCI_RELATIVE)
        return _corroborate_one(GCI_RELATIVE, decl.id, rep, gci_rel, "fraction",
                                {GCI_RELATIVE: spec} if spec is not None else {})
    # Absolute: same units as the quantity, exactly, or no comparison.
    if decl.quantity_units is None or rep.units != decl.quantity_units:
        return corroborate.NOT_COMPARABLE, (
            f"reported units {rep.units!r} are not the quantity's declared units "
            f"{decl.quantity_units!r}; an absolute index is compared only in the same units")
    spec = identity.get(GCI_RELATIVE)
    if spec is None or "tolerance" not in spec:
        return corroborate.NOT_COMPARABLE, (
            f"the active pack declares no {GCI_RELATIVE} tolerance")
    local = {_GCI_ABSOLUTE: {"canonicalUnit": rep.units, "tolerance": spec["tolerance"],
                             "units": {rep.units: 1.0}}}
    return _corroborate_one(_GCI_ABSOLUTE, decl.id, rep, gci_abs, rep.units, local)


def _corroborate_one(key: str, scope: str, rep: Reported, value: float, units: str,
                     identity: dict) -> tuple[str, str]:
    claim = corroborate.Claim(quantity=key, value=rep.value, units=rep.units,
                              scope=scope, source=rep.source)
    evidence = SolverEvidence(facts=[SolverFact(key=key, value=value, units=units,
                                                scope=scope, source_member=TOOL_NAME)])
    rows = corroborate.corroborate([claim], evidence, identity).rows
    if len(rows) != 1 or rows[0].verdict not in (
            corroborate.AGREES, corroborate.DIVERGES, corroborate.NOT_COMPARABLE):
        raise RuntimeError(f"unexpected corroboration for {key}: {rows!r}")
    return rows[0].verdict, rows[0].detail


def _set_output(record: dict, outputs: list[str]) -> None:
    text = "".join(outputs)
    if not text:
        return
    if len(text) > OUTPUT_LIMIT:
        record["cvToolOutput"] = text[:OUTPUT_LIMIT]
        record["cvToolOutputTruncated"] = "true"
    else:
        record["cvToolOutput"] = text


# ── Readout ─────────────────────────────────────────────────────────────────


def summarise(records: list[dict]) -> list[str]:
    """Human readout lines, one block per study."""
    if not records:
        return ["no mesh study declared"]
    lines: list[str] = []
    for r in records:
        head = f"{r['cvStudyId']} ({r['forFactorType']}): "
        status = r["cvStatus"]
        if status == NOT_RUN:
            lines.append(head + f"not run ({r['cvReason']})")
            lines.append(f"  {r['cvReasonDetail']}")
            continue
        if status == NO_ESTIMATE:
            lines.append(head + f"no estimate ({r.get('cvReason', 'reason not recorded')}), "
                                f"convergence type {r['cvConvergenceType']}")
            continue
        lines.append(head + f"computed, method {r['cvMethod']}")
        order = f"observed order {_fmt(r['cvObservedOrder'])}"
        if "cvFormalOrder" in r:
            agreement = r.get("cvOrderAgreement", "agreement not recovered").replace("-", " ")
            order += f", formal order {_fmt(r['cvFormalOrder'])} ({agreement})"
        else:
            order += ", no formal order declared"
        fs = r.get("cvSafetyFactor")
        order += f", safety factor {_fmt(fs)}" if fs is not None else ", safety factor not recovered"
        lines.append("  " + order)
        index = "index: "
        index += f"{_fmt(r['cvGciRelative'])} relative" if "cvGciRelative" in r else "no relative value"
        units = r.get("cvQuantityUnits", "")
        index += f", {_fmt(r['cvGciAbsolute'])} {units}".rstrip() + " absolute"
        rep = r.get("cvReportedGci")
        if rep:
            index += (f"; reported {_fmt(rep['cvValue'])} {rep['cvUnits']} {rep['cvBasis']} "
                      f"({r['cvGciComparison']})")
        else:
            index += "; no reported value"
        lines.append("  " + index)
        if r.get("cvTripletConcern") == "true":
            lines.append("  a coarser triplet does not converge monotonically")
        for w in r.get("cvWarnings", []):
            lines.append(f"  {w}")
    return lines


def _fmt(value) -> str:
    return f"{float(value):.4g}"
