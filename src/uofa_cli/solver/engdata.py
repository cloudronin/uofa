"""Read a Workbench `EngineeringData.xml` / `.engd` materials library.

MatML reaches every value through two levels of indirection: a `<BulkDetails>`
names the material and holds `<PropertyData property="pr3">` blocks whose
`<ParameterValue parameter="pa1">` carries the number, while what `pr3` and
`pa1` actually *mean* lives in a `<Metadata>` block that may appear after all
the materials. So it is a two-pass read: resolve the ids, then walk the
materials.

Units are recorded exactly as declared and never converted here. The real
library mixes them -- titanium in MPa, UHMWPE in Pa, in the same file -- and
silently coercing produces a wrong answer that validates, which is the failure
the requirement layer's open question Q3 is about. Comparison is the
corroboration layer's job, and it needs the declared unit to refuse an unsafe
one.

Every material fact is bound at LIBRARY_ENTRY confidence, not CERTAIN. The value
is certainly in the file; that the *published run used it* is a different claim
the file does not make. Real libraries carry unused defaults, superseded
revisions and near-duplicates -- the OSF one has three mutually inconsistent
titanium definitions -- and asserting otherwise would be exactly the kind of
plausible-but-unsupported fill that `sh:minCount` cannot catch.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from uofa_cli.solver.facts import (CERTAIN, LIBRARY_ENTRY, SolverEvidence,
                                   SolverFact)
from uofa_cli.solver.redact import Redactor

# Parameter name → fact key. Names are MatML's, spelling and apostrophes intact.
_PARAMETER_KEYS = {
    "young's modulus": "material.youngs_modulus",
    "poisson's ratio": "material.poissons_ratio",
    "yield strength": "material.yield_strength",
    "tangent modulus": "material.tangent_modulus",
    "density": "material.density",
    "bulk modulus": "material.bulk_modulus",
    "shear modulus": "material.shear_modulus",
    "compressive yield strength": "material.compressive_yield_strength",
    "tensile yield strength": "material.tensile_yield_strength",
    "tensile ultimate strength": "material.tensile_ultimate_strength",
}

# Tabulated hardening curves are counted, not interpreted. "Bilinear" versus
# "multilinear" is a reading of the point count, and readings belong downstream.
_CURVE_PARAMETERS = {"plastic strain", "stress", "strain"}


def parse(text: str, *, member: str = "", redactor: Redactor | None = None
          ) -> SolverEvidence:
    """Read one materials library."""
    redactor = redactor or Redactor()
    ev = SolverEvidence()

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        ev.unparsed.append(f"{member}: not well-formed XML ({exc})")
        return ev

    names = _resolve_ids(root)
    version = root.get("version")
    if version:
        ev.facts.append(SolverFact(
            key="materials.schema_version", value=version, scope="library",
            source_member=member, source_locator="/EngineeringData/@version",
            source_text=f'<EngineeringData version="{version}">',
            binding_confidence=CERTAIN))

    for bulk in root.iter("BulkDetails"):
        material = (bulk.findtext("Name") or "").strip()
        if not material:
            ev.unparsed.append(f"{member}: material block with no name")
            continue
        _read_material(bulk, material, names, ev, member, redactor)

    ev.redaction_summary = redactor.summary()
    return ev


def _resolve_ids(root) -> dict[str, str]:
    """Map `pr*`/`pa*` ids to their declared names.

    Both id spaces are flat and disjoint in practice, so one dict serves; a
    collision would show up as a wrong key rather than a wrong value, and the
    fact still quotes the bytes it came from.
    """
    out: dict[str, str] = {}
    for tag in ("PropertyDetails", "ParameterDetails"):
        for detail in root.iter(tag):
            ident, name = detail.get("id"), detail.findtext("Name")
            if ident and name:
                out[ident] = name.strip()
    return out


def _read_material(bulk, material: str, names: dict[str, str],
                   ev: SolverEvidence, member: str, redactor: Redactor) -> None:
    for prop in bulk.iter("PropertyData"):
        property_name = names.get(prop.get("property", ""), prop.get("property", ""))
        curve_points = 0

        for pv in prop.iter("ParameterValue"):
            parameter = names.get(pv.get("parameter", ""), pv.get("parameter", ""))
            lowered = parameter.strip().lower()
            data = pv.findtext("Data")
            if data is None:
                continue
            raw = data.strip()

            if lowered in _CURVE_PARAMETERS:
                curve_points = max(curve_points, len(raw.split(",")))
                continue

            key = _PARAMETER_KEYS.get(lowered)
            if not key or not raw:
                continue
            value = _number(raw)
            if value is None:
                continue

            ev.facts.append(SolverFact(
                key=key, value=value, units=_units(pv), scope=material,
                source_member=member,
                source_locator=f"//BulkDetails[Name='{material}']"
                               f"/PropertyData[@property='{prop.get('property')}']"
                               f"/ParameterValue[@parameter='{pv.get('parameter')}']",
                source_text=redactor.redact(
                    f"{material} / {property_name} / {parameter} = {raw}"),
                binding_confidence=LIBRARY_ENTRY))

        if curve_points > 1:
            ev.facts.append(SolverFact(
                key="material.hardening_points", value=curve_points,
                scope=material, source_member=member,
                source_locator=f"//BulkDetails[Name='{material}']"
                               f"/PropertyData[@property='{prop.get('property')}']",
                source_text=f"{material} / {property_name}: "
                            f"{curve_points} tabulated point(s)",
                binding_confidence=LIBRARY_ENTRY))


def _units(pv) -> str:
    for qualifier in pv.iter("Qualifier"):
        if qualifier.get("name") == "Units":
            return (qualifier.text or "").strip()
    return ""


def _number(raw: str) -> float | None:
    """First value of a Data element, as a float. None when it is not numeric.

    A `-` placeholder and an interpolation-options string both appear in real
    libraries where a number would go; neither is a value and neither is an
    error worth reporting.
    """
    first = raw.split(",")[0].strip()
    try:
        return float(first)
    except ValueError:
        return None
