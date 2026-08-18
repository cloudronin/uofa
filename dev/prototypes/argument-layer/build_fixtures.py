"""Derive the argument-layer fixtures from the real adjudication packages.

Every fixture is the untouched source package plus exactly two additions:
  1. conformsToProfile -> ProfileArgument   (the gate the W-ARG rules check)
  2. an inline claim graph + hasInferenceStep declaring the argument that the
     decision-record rationale already asserts in prose.

The rationale prose is left in place. The structure is asserted *alongside* it,
which is what `uofa extract` would emit. Nothing else is edited -- run
`--diff` to see the added keys and confirm that.
"""
import json, os, sys, copy

SRC = "dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages"
OUT = "dev/prototypes/argument-layer/fixtures"
R16 = "adv-2026-p2-119-confusion-necessary-sufficient_high-v03"
R54 = "adv-2026-p2-119-confusion-necessary-sufficient_medium-v02"
B = "https://uofa.net/proto/arg"


# The argument layer cannot ride on @vocab alone. @vocab gives an undeclared
# term its IRI, but NOT its value semantics: a plain-string object expands to a
# literal, so `supportsClaim: "<iri>"` yields a literal and every rule that
# traverses it silently matches nothing. Every IRI-valued term therefore needs
# an explicit "@type": "@id" declaration. This dict is the exact context delta
# the argument layer requires -- see UofA_Argument_Layer_Spec_v0_1.md.
ARG_CONTEXT = {
    "hasInferenceStep": {"@id": "uofa:hasInferenceStep", "@type": "@id"},
    "supportsClaim":    {"@id": "uofa:supportsClaim",    "@type": "@id"},
    "hasGround":        {"@id": "uofa:hasGround",        "@type": "@id"},
    "aboutQuantity":    {"@id": "uofa:aboutQuantity",    "@type": "@id"},
    "overScope":        {"@id": "uofa:overScope",        "@type": "@id"},
    "aboutRequirement": {"@id": "uofa:aboutRequirement", "@type": "@id"},
    "hasRebuttal":      {"@id": "uofa:hasRebuttal",      "@type": "@id"},
}


def write_context():
    """Emit v0.5 + the argument-layer terms as one reviewable context file.

    The engine inlines a context by regex-replacing a bare-string "@context"
    (JsonLdLoader.java), so the fixtures keep their original @context string
    and this file is supplied via `uofa rules --context`. That also keeps the
    delta in one place instead of duplicated across fixtures -- it is exactly
    what a v0.6 context bump would add.
    """
    with open("spec/context/v0.5.jsonld", encoding="utf-8") as fh:
        base = json.load(fh)
    base["@context"].update(ARG_CONTEXT)
    out = "dev/prototypes/argument-layer/context-v0.5-argument.jsonld"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(base, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"  wrote {out}  (v0.5 + {len(ARG_CONTEXT)} argument terms)")


def with_arg_context(d):
    return d


def load(cid):
    with open(os.path.join(SRC, cid + ".jsonld"), encoding="utf-8") as fh:
        return json.load(fh)


def q(slug, name, unit=None):
    # quantityId is a DECLARED identifier, not the node IRI. Quantity identity
    # has to be something a producer states, so a requirement, a model output
    # and a measurement can be known to refer to the same quantity -- piece 1
    # of UofA_Requirement_Layer_Spec_v0_1.md. Matching on node-IRI coincidence
    # would also make the join invisible to the rule engine (see RESULTS.md).
    n = {"id": f"{B}/quantity/{slug}", "type": "QuantityRef",
         "quantityId": slug, "name": name}
    if unit:
        n["unit"] = unit
    return n


def scope(slug, dimension, population, covers=None):
    n = {"id": f"{B}/scope/{slug}", "type": "ScopeRef",
         "dimension": dimension, "populationId": f"{B}/population/{population}"}
    if covers is not None:
        n["coversValues"] = covers
    return n


# ---------------------------------------------------------------- row 16
def row16(repaired=False):
    d = copy.deepcopy(load(R16))
    d["conformsToProfile"] = "https://uofa.net/vocab#ProfileArgument"

    rh_quantity = q("relative-hemolysis-index", "Relative hemolysis index (RH)")
    five_conditions = scope("five-evaluated-conditions", "operating-condition",
                            "cou1-evaluated", covers=5)
    tolerance_study = scope("tolerance-study", "operating-condition",
                            "cou1-tolerance-study")

    # Ground: RH < 1 met at the five evaluated conditions. The rationale itself
    # establishes this as NECESSARY -- "the established regulatory acceptance
    # metric for Class II CPB devices" is a gate that must be passed.
    ground = {
        "id": f"{B}/claim/rh-criterion-met",
        "type": "AssuranceClaim",
        "claimText": ("The relative hemolysis index criterion (RH < 1) is satisfied "
                      "across all five evaluated operating conditions."),
        "claimModality": "necessary",
        "claimKind": "model-behaviour",
        "aboutQuantity": rh_quantity,
        "overScope": five_conditions,
    }

    if repaired:
        # The honest conclusion: meeting the gate CONTRIBUTES to the case over
        # the conditions actually evaluated. Same evidence, same quantity, same
        # scope -- only the strength of the assertion changes.
        conclusion = {
            "id": f"{B}/claim/cou1-fitness",
            "type": "AssuranceClaim",
            "claimText": ("The RH < 1 criterion is met across the five evaluated "
                          "operating conditions, contributing to the safety case."),
            "claimModality": "contributory",
            "claimKind": "model-behaviour",
            "aboutQuantity": rh_quantity,
            "overScope": five_conditions,
        }
    else:
        # As written: satisfying a necessary gate is asserted to CONSTITUTE
        # sufficient evidence of fitness for purpose, over the whole COU.
        conclusion = {
            "id": f"{B}/claim/cou1-fitness",
            "type": "AssuranceClaim",
            "claimText": ("The computational model is fit for purpose for identifying "
                          "worst-case hemolysis operating conditions for this COU."),
            "claimModality": "sufficient",
            "claimKind": "model-behaviour",
            "aboutQuantity": q("worst-case-condition-identification",
                               "Worst-case hemolysis operating condition identification"),
            "overScope": tolerance_study,
        }

    d["bindsClaim"] = conclusion
    d["hasInferenceStep"] = [{
        "id": f"{B}/inference/cou1-rh-to-fitness",
        "type": "InferenceStep",
        "supportsClaim": conclusion["id"],
        "hasGround": [ground],
        # Nothing licenses a necessity->sufficiency move here; the rationale
        # offers only the measured comparison itself.
        "warrantKind": "direct-measurement",
    }]
    return with_arg_context(d)


# ---------------------------------------------------------------- row 54
def row54():
    d = copy.deepcopy(load(R54))
    d["conformsToProfile"] = "https://uofa.net/vocab#ProfileArgument"

    # The conclusion is about DETECTION SENSITIVITY over the full tolerance study.
    conclusion = {
        "id": f"{B}/claim/cou1-detection",
        "type": "AssuranceClaim",
        "claimText": ("The model will correctly identify hemolysis-adverse operating "
                      "conditions in the full device tolerance study."),
        "claimModality": "sufficient",
        "claimKind": "model-behaviour",
        "aboutQuantity": q("adverse-condition-detection-sensitivity",
                           "Hemolysis-adverse condition detection sensitivity"),
        "overScope": scope("tolerance-study", "operating-condition",
                           "cou1-tolerance-study"),
    }

    # Ground 1: the gate EXISTS. A claim about mechanism presence, not performance.
    ground_gate = {
        "id": f"{B}/claim/rh-gate-present",
        "type": "AssuranceClaim",
        "claimText": ("The RH < 1 threshold criterion is implemented as a quantitative "
                      "acceptance gate in all simulation outputs."),
        "claimModality": "contributory",
        "claimKind": "model-behaviour",
        "aboutQuantity": q("rh-gate-presence", "Presence of the RH acceptance gate"),
        "overScope": scope("all-simulation-outputs", "operating-condition",
                           "cou1-simulation-outputs"),
    }

    # Ground 2: agreement with bench measurement at five points.
    ground_agreement = {
        "id": f"{B}/claim/bench-agreement",
        "type": "AssuranceClaim",
        "claimText": ("CFD predictions deviate no more than 13% from measured values "
                      "across all 5 bench-scale operating points."),
        "claimModality": "contributory",
        "claimKind": "model-behaviour",
        "aboutQuantity": q("cfd-measurement-deviation",
                           "CFD-to-measurement deviation", unit="percent"),
        "overScope": scope("five-bench-points", "operating-condition",
                           "cou1-bench-validation", covers=5),
    }

    # Ground 3: the seven assessed factors meet their required levels. This is a
    # claim about ASSESSMENT RIGOUR, not about what the model does.
    ground_factors = {
        "id": f"{B}/claim/factors-meet-levels",
        "type": "AssuranceClaim",
        "claimText": ("The seven assessed credibility factors all meet or exceed "
                      "their required levels."),
        "claimModality": "contributory",
        "claimKind": "assessment-rigour",
        "aboutQuantity": q("credibility-factor-attainment",
                           "Credibility factor level attainment"),
        "overScope": scope("assessed-factors", "credibility-factor",
                           "cou1-assessed-factors", covers=7),
    }

    # The rationale's second move: factor levels are offered as confirmation that
    # the mechanism WORKS -- a behavioural conclusion from a rigour ground.
    claim_mechanism = {
        "id": f"{B}/claim/rh-mechanism-functions",
        "type": "AssuranceClaim",
        "claimText": "The RH threshold mechanism functions as intended.",
        "claimModality": "contributory",
        "claimKind": "model-behaviour",
        "aboutQuantity": q("rh-mechanism-function", "RH threshold mechanism function"),
        "overScope": scope("all-simulation-outputs", "operating-condition",
                           "cou1-simulation-outputs"),
    }

    d["bindsClaim"] = conclusion
    d["hasInferenceStep"] = [
        {
            "id": f"{B}/inference/cou1-gate-to-detection",
            "type": "InferenceStep",
            "supportsClaim": conclusion["id"],
            "hasGround": [ground_gate, ground_agreement],
            "warrantKind": "direct-measurement",
        },
        {
            "id": f"{B}/inference/cou1-factors-to-mechanism",
            "type": "InferenceStep",
            # supportsClaim carries the node inline: this claim is not the
            # package's bound claim, so nothing else would define it.
            "supportsClaim": claim_mechanism,
            "hasGround": [ground_factors],
            "warrantKind": "direct-measurement",
        },
    ]
    return with_arg_context(d)


def materialize_ground_coverage(d):
    """Emit each inference step's ground coverage as ORIGINAL triples.

    Jena evaluates noValue at rule-activation time, not at fixpoint, so a
    noValue over a forward-chained marker races its own seed rule -- the
    hazard the core catalog documents on W-PROV-01, and reproduced here
    (RESULTS.md, experiment 3). The discipline that avoids it is: noValue may
    only test triples present in the input.

    So the producer materializes the join. `uofa extract` knows which grounds
    it attached and which quantity each addresses, so emitting the summary is
    free at extraction time. Whether the summary faithfully reflects hasGround
    is a package-integrity question -- that join-with-negation belongs in
    SHACL (sh:sparql), not in a forward-chaining rule engine.
    """
    for step in d.get("hasInferenceStep", []):
        quantities, populations = [], []
        for g in step.get("hasGround", []):
            q_node = g.get("aboutQuantity") or {}
            if q_node.get("quantityId") and q_node["quantityId"] not in quantities:
                quantities.append(q_node["quantityId"])
            s_node = g.get("overScope") or {}
            if s_node.get("populationId") and s_node["populationId"] not in populations:
                populations.append(s_node["populationId"])
        if quantities:
            step["groundQuantity"] = quantities
        if populations:
            step["groundPopulation"] = populations
    return d


def write(name, doc):
    doc = materialize_ground_coverage(doc)
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"  wrote {p}")


def main():
    write_context()
    write("row16-argument.jsonld", row16())
    write("row16-repaired.jsonld", row16(repaired=True))
    write("row54-argument.jsonld", row54())

    # Prove the fixtures differ from source only by the added keys.
    print("\n  keys changed vs source package:")
    for name, cid in (("row16-argument.jsonld", R16), ("row54-argument.jsonld", R54)):
        src, fix = load(cid), json.load(open(os.path.join(OUT, name), encoding="utf-8"))
        added = [k for k in fix if k not in src]
        changed = [k for k in fix if k in src and fix[k] != src[k]]
        print(f"    {name}: added={added} changed={changed}")


if __name__ == "__main__":
    main()
