"""Regenerate the Morrison COU1/COU2 reviewer fixtures from source JSON-LD.

Run:  python tests/space/fixtures/_generate.py

What is source-exact (deterministic, from packs/vv40/examples/morrison/cou{1,2}):
  - the weakener firings (pattern ids, severities, hits, descriptions, the
    factor IRIs each targets) - straight from the rule engine on the real bundle;
  - the COU name/description (from the bundle);
  - structural conformance (from SHACL on the real bundle).

What is illustrative (the JSON-LD does not encode a per-factor assessed/
scoped-out/absent status - that is an extraction-layer artifact): the
factor_statuses below. They are anchored on the engine signal where it exists -
COU2's six W-EP-04-targeted factors are marked not-assessed because that pattern
fires precisely on unassessed factors at elevated risk - and otherwise chosen to
reflect the NAFEMS reproduction (COU1 accepted at MRL2; COU2 not accepted at
MRL5). This illustrative-status point is the flagged engine-data gap.

The payload these produce is then rendered by render_reviewer_html to the golden
HTML. We do NOT hand-edit the golden; we regenerate it from a source-grounded
payload (spec rule 5).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uofa_cli.commands import rules as rules_mod
from uofa_cli.excel_constants import VV40_FACTOR_NAMES

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from space import pipeline, summary as summary_mod  # noqa: E402
from space.gloss import load_gloss  # noqa: E402
from space.reviewer import render_reviewer_html  # noqa: E402

_HERE = Path(__file__).resolve().parent
_ROOT = Path(__file__).resolve().parents[3]


def _firings(cou: str) -> list[dict]:
    p = _ROOT / f"packs/vv40/examples/morrison/{cou}/uofa-morrison-{cou}.jsonld"
    args = argparse.Namespace(file=p, rules=None, context=None, build=False, raw=False,
                              format="jsonld", output=None, active_packs=["vv40"])
    rr = rules_mod.run_structured(args)
    return rules_mod.parse_firings_jsonld(rr.raw_stdout or "")


def _bundle(cou: str) -> dict:
    p = _ROOT / f"packs/vv40/examples/morrison/{cou}/uofa-morrison-{cou}.jsonld"
    return json.loads(p.read_text(encoding="utf-8"))


# Illustrative per-factor statuses (see module docstring). Anything not listed
# defaults to "assessed".
_COU1_SCOPED = {"Use error", "Numerical solver error"}             # lower risk (MRL2)
_COU2_NOT_ASSESSED = {                                             # W-EP-04 targets these
    "Use error", "Test samples", "Model form",
    "Equivalency of input parameters", "Numerical solver error", "Model inputs",
}

_META = {
    "cou1": {"mrl": 2, "device_class": "Class II",
             "scoped": _COU1_SCOPED, "not_assessed": set()},
    "cou2": {"mrl": 5, "device_class": "Class III",
             "scoped": set(), "not_assessed": _COU2_NOT_ASSESSED},
}


def _statuses(meta: dict) -> dict[str, str]:
    out = {}
    for name in VV40_FACTOR_NAMES:
        if name in meta["scoped"]:
            out[name] = "scoped-out"
        elif name in meta["not_assessed"]:
            out[name] = "not-assessed"
        else:
            out[name] = "assessed"
    return out


def _build(cou: str) -> dict:
    meta = _META[cou]
    bundle = _bundle(cou)
    firings = _firings(cou)
    statuses = _statuses(meta)
    # Structural conformance from the real bundle.
    jsonld_path = _ROOT / f"packs/vv40/examples/morrison/{cou}/uofa-morrison-{cou}.jsonld"
    conforms, violations = pipeline._run_check(jsonld_path, "vv40")
    payload = summary_mod.compute(
        "vv40", statuses, {"conforms": conforms, "violations": violations}, firings
    )
    payload["context"] = {
        "project_name": "Morrison centrifugal blood pump",
        "cou_name": bundle.get("name"),
        "cou_description": bundle.get("description"),
        "standard": "ASME V&V 40",
        "pack": "vv40",
        "model_risk_level": meta["mrl"],
        "device_class": meta["device_class"],
        "assurance_level": None,
        "standards_reference": "ASME V&V 40-2018",
        "authenticity": pipeline._authenticity_block(),
    }
    payload["warnings"] = []
    payload["_README"] = (
        f"Source-grounded reviewer fixture for Morrison {cou.upper()}. Firings, "
        "COU text, and structural conformance are derived deterministically from "
        "packs/vv40/examples/morrison/" + cou + "/. Per-factor statuses are "
        "illustrative (the JSON-LD does not encode them); see fixtures/_generate.py."
    )
    return payload


def main() -> None:
    gloss = load_gloss()
    for cou in ("cou1", "cou2"):
        payload = _build(cou)
        (_HERE / f"morrison_{cou}_state.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        html = render_reviewer_html(payload, gloss)
        (_HERE / f"morrison_{cou}_reviewer.html").write_text(html, encoding="utf-8")
        print(f"{cou}: wrote payload + golden ({len(html)} bytes)")


if __name__ == "__main__":
    main()
