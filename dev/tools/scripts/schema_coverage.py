#!/usr/bin/env python3
"""Does the extractor fill the schema, and does what it fills validate?

The eval reported `mean overall F1 0.964` for a year. That number describes
`hasCredibilityFactor` and nothing else: `UnitOfAssurance_CompleteBody` requires
13 properties at `minCount >= 1`, `score_bundle` called `score_factors` and
stopped, and `score_summary`/`score_decision` only ever ran against two
regression fixtures. Twelve required properties were scored nowhere.

Worse, nobody ran the project's own validator over the extractor's output. When
finally run: **37 of 45 corpus packages failed SHACL**, while the eval reported
PASS. Two of the three causes were contradictions inside the pipeline rather
than model errors --- the extract prompts instructed the model to emit
"conditionally accepted" where the shape allowed only Accepted/Not accepted, and
core imposed FDA device classes on aerospace packages.

That second one inverted the constraint: of the packages that passed, fourteen
were turbomachinery models claiming "Class II". Packages that honestly wrote
"Turbomachinery (Centrifugal Pump)" failed. **The ones that passed were the ones
that fabricated.**

## Two questions, deliberately separate

    coverage    does the extractor PRODUCE each required property?
    validity    does what it produced satisfy the shape?

Coverage needs no ground truth, so it runs on the corpus as it stands and would
have caught the gap at any point in the last year for free. Validity needs no
ground truth either. Neither is a substitute for correctness --- a package can be
fully populated and fully valid and still say the wrong thing --- but a property
that is never emitted cannot be correct, and a package that fails the schema is
not a credibility artefact at all.

## The required set is derived, never listed

`required_properties()` reads `sh:minCount` off the shape graph. Hardcoding the
list is how `PROFILE_URIS` drifted from its `sh:in` and had to be repaired; a
constant here would silently stop tracking the schema the day someone adds a
requirement.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Produced by `uofa sign` after extraction, so an extractor is not accountable
# for them and counting them would permanently cap coverage below 1.0.
_SIGNING_PRODUCED = frozenset({"hash", "signature"})

# Stamped by `uofa import`, not written by the extractor. Excluded from coverage
# for the same reason, but see `placeholder_satisfied` -- being stamped
# downstream is not the same as being meaningful.
_IMPORT_STAMPED = frozenset({"generatedAtTime", "wasAttributedTo"})

# Strings that satisfy a shape while carrying no information. Each is the
# template's own help text, surviving into the package because nothing rejects
# it: JSON-LD coerces the string to a file:// URI, which satisfies
# `sh:nodeKind sh:IRI`, and the requirement is then met by the instructions for
# meeting it.
#
# Measured: 27 of 27 corpus packages satisfy `wasDerivedFrom` -- a required
# property of ProfileComplete -- with exactly "DOI, report number, or URI".
#
# This is the third form of the same failure the schema work kept turning up.
# The first was `deviceClass`, where packages inventing "Class II" for a
# turbomachinery model passed and honest ones failed. The second was `decision`,
# where the prompt instructed a value the shape forbade. Here the template
# supplies the passing value itself, so the property is 100% "populated" and
# 100% uninformative. A validity rate that counts these is measuring whether the
# template was filled in, not whether the model was assessed.
_PLACEHOLDERS = {
    "wasDerivedFrom": ("DOI, report number, or URI",),
    "deviceClass": ("<class designation if applicable, else N/A>",),
    "couName": ("Context of use", "<context of use>"),
}


def placeholder_satisfied(jsonld_text: str) -> list[str]:
    """Required properties met by template help text rather than by content.

    Reported separately from coverage and validity because it is invisible to
    both: the field is present, the shape passes, and the value means nothing.
    """
    return sorted(prop for prop, needles in _PLACEHOLDERS.items()
                  if any(n in jsonld_text for n in needles))


def required_properties(pack: str = "vv40",
                        shape_suffix: str = "UnitOfAssurance_CompleteBody") -> list[str]:
    """Properties the CompleteProfile body requires, read off the shape graph."""
    sys.path.insert(0, str(_ROOT / "src"))
    from rdflib import RDF, Graph, Namespace  # noqa: WPS433

    from uofa_cli import paths  # noqa: WPS433

    sh = Namespace("http://www.w3.org/ns/shacl#")
    g = Graph()
    for p in paths.all_shacl_schemas(active=[pack]):
        g.parse(p, format="turtle")

    shape = next((s for s in g.subjects(RDF.type, sh.NodeShape)
                  if str(s).endswith(shape_suffix)), None)
    if shape is None:
        raise SystemExit(f"no shape ending {shape_suffix!r} in the {pack} graph")

    out = set()
    for ps in g.objects(shape, sh.property):
        mn = g.value(ps, sh.minCount)
        path = g.value(ps, sh.path)
        if mn is not None and int(mn) >= 1 and path is not None:
            out.add(str(path).split("#")[-1])
    return sorted(out - _SIGNING_PRODUCED - _IMPORT_STAMPED)


# How to tell, from a parsed workbook, whether a required property was produced.
# Keyed by property name so a schema change surfaces as a missing key rather than
# as a silently unscored requirement -- see `unmapped_requirements`.
_POPULATED = {
    "hasCredibilityFactor":
        lambda d: bool(d.get("credibility_factors")),
    "hasValidationResult":
        lambda d: bool(d.get("validation_results")),
    "hasDecisionRecord":
        lambda d: bool((d.get("decision") or {}).get("outcome")),
    "modelRiskLevel":
        lambda d: bool((d.get("assessment_summary") or {}).get("model_risk_level")),
    "hasContextOfUse":
        lambda d: bool((d.get("assessment_summary") or {}).get("cou_name")),
    "bindsModel":
        lambda d: _has_entity(d, "model"),
    "bindsDataset":
        lambda d: _has_entity(d, "data"),
    "bindsRequirement":
        lambda d: _has_entity(d, "requirement"),
}


def _has_entity(parsed: dict, kind: str) -> bool:
    for e in parsed.get("entities") or []:
        t = (e.get("type") or e.get("entity_type") or "").lower()
        if kind in t:
            return True
    return False


def unmapped_requirements(pack: str = "vv40") -> list[str]:
    """Required properties this module cannot yet check.

    Reported rather than ignored. A requirement added to the shape with no
    detector here would otherwise vanish from the coverage denominator and make
    the score go *up*, which is the wrong direction for a new obligation.
    """
    return [p for p in required_properties(pack) if p not in _POPULATED]


@dataclass
class SchemaCoverage:
    bundles: int = 0
    populated: dict = field(default_factory=dict)   # property -> bundle count
    conforms: int = 0            # passes SHACL
    placeholder_free: int = 0    # passes SHACL *and* says something
    validated: int = 0
    violations: dict = field(default_factory=dict)  # field -> count

    def coverage(self, prop: str) -> float:
        return self.populated.get(prop, 0) / self.bundles if self.bundles else 0.0

    @property
    def validity_rate(self) -> float:
        return self.conforms / self.validated if self.validated else 0.0

    @property
    def meaningful_rate(self) -> float:
        """Conforming AND not satisfying a requirement with template help text.

        Reported beside validity_rate, never merged into it. Merging them
        produced a single 0% that read as "the schema is broken" when what it
        actually meant was "13 packages conform and none of them says anything
        under wasDerivedFrom" -- two findings with different fixes.
        """
        return self.placeholder_free / self.validated if self.validated else 0.0

    def as_dict(self) -> dict:
        return {
            "bundles": self.bundles,
            "populated": dict(self.populated),
            "conforms": self.conforms,
            "placeholder_free": self.placeholder_free,
            "validated": self.validated,
            "validity_rate": self.validity_rate,
            "meaningful_rate": self.meaningful_rate,
            "violations_by_field": dict(self.violations),
        }


def score_schema_coverage(parsed: dict, pack: str = "vv40") -> dict[str, bool]:
    """Which required properties did this one extraction produce?"""
    return {p: bool(_POPULATED[p](parsed))
            for p in required_properties(pack) if p in _POPULATED}


def validate_extracted(xlsx_path: Path, pack: str) -> tuple[bool | None, list[str]]:
    """Import the workbook and run the project's own validator over it.

    Returns (conforms, failing field names). `conforms` is None when the import
    step itself failed, which is a different result from invalid output and must
    not be averaged in with it.
    """
    env = {**_env(), "PYTHONPATH": str(_ROOT / "src")}
    with tempfile.TemporaryDirectory() as td:
        jsonld = Path(td) / "pkg.jsonld"
        imp = subprocess.run(
            [sys.executable, "-m", "uofa_cli", "import", str(xlsx_path),
             "--pack", pack, "-o", str(jsonld)],
            capture_output=True, text=True, cwd=str(_ROOT), env=env)
        if imp.returncode != 0 or not jsonld.exists():
            return None, []

        val = subprocess.run(
            [sys.executable, "-m", "uofa_cli", "shacl", str(jsonld), "--pack", pack],
            capture_output=True, text=True, cwd=str(_ROOT), env=env)
        placeholders = placeholder_satisfied(jsonld.read_text(errors="ignore"))
        if val.returncode == 0:
            return True, placeholders and [f"placeholder:{p}" for p in placeholders] or []
        fields = [ln.strip().split()[1] for ln in val.stdout.splitlines()
                  if ln.strip().startswith("[") and len(ln.strip().split()) > 1]
        return False, fields + [f"placeholder:{p}" for p in placeholders]


def _env() -> dict:
    import os
    return os.environ.copy()


def print_schema_coverage(cov: SchemaCoverage, pack: str = "vv40") -> None:
    print(f"\n  SCHEMA COVERAGE — required properties of ProfileComplete")
    print(f"  {'─' * 62}")
    for p in required_properties(pack):
        if p not in _POPULATED:
            print(f"  {p:26s}   NO DETECTOR — not scored, see unmapped_requirements()")
            continue
        n = cov.populated.get(p, 0)
        bar = "#" * (n * 24 // max(cov.bundles, 1))
        print(f"  {p:26s} {n:3d}/{cov.bundles} {cov.coverage(p):5.0%}  {bar}")

    if cov.validated:
        print(f"\n  SHACL VALIDITY   {cov.conforms}/{cov.validated} "
              f"({cov.validity_rate:.0%}) conform to the shape")
        print(f"  OF SUBSTANCE     {cov.placeholder_free}/{cov.validated} "
              f"({cov.meaningful_rate:.0%}) conform AND meet every requirement "
              f"with content")
        print(f"  {'─' * 62}")
        for f, c in sorted(cov.violations.items(), key=lambda kv: -kv[1]):
            note = "  <- template help text, not data" if f.startswith("placeholder") else ""
            print(f"    {c:3d}  {f}{note}")
        print("  The two rates are separate on purpose. A package that fails the")
        print("  shape is not a credibility artefact; one that passes by echoing")
        print("  the template is not either, but nothing downstream can tell.")
    print(f"  {'─' * 62}")
