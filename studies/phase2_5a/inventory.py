"""Precondition inventory: for each MECHANICAL rule, can each substrate host its mutation?

Expands each substrate to RDF through the same context the engine uses, then asks
whether the rule's ANTECEDENT is satisfiable -- i.e. whether a violation is even
expressible. Reports Class A (edit an existing field) vs Class B (instantiate the
antecedent first) per pattern per substrate.
"""
import json, sys
from pathlib import Path
from rdflib import Graph, URIRef, Namespace, RDF

U = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SCHEMA = Namespace("https://schema.org/")

SUBS = {
    "morrison/cou1": "packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld",
    "morrison/cou2": "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld",
    "nagaraja/cou1": "packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld",
}

def load(p):
    g = Graph()
    doc = json.loads(Path(p).read_text())
    # inline the local context so expansion is offline and matches the engine
    doc["@context"] = json.loads(Path("spec/context/v0.5.jsonld").read_text())["@context"]
    g.parse(data=json.dumps(doc), format="json-ld")
    return g

def uoa(g):
    for s in g.subjects(RDF.type, U.UnitOfAssurance):
        return s
    return None

# each probe returns (n_sites, note). n_sites>0 => Class A on this substrate.
def probes(g, u):
    P = {}
    P["W-EP-01"] = len([c for c in g.objects(u, U.bindsClaim)
                        if (c, RDF.type, U.Claim) in g and list(g.objects(c, PROV.wasDerivedFrom))])
    P["W-EP-02"] = len([r for r in g.objects(u, U.hasValidationResult) if list(g.objects(r, PROV.wasGeneratedBy))])
    n = 0
    for r in g.objects(u, U.hasValidationResult):
        for a in g.objects(r, PROV.wasGeneratedBy):
            for d in g.objects(a, PROV.used):
                if list(g.objects(d, U.dataVintage)): n += 1
    P["W-EP-03"] = n if list(g.objects(u, U.modelRevisionDate)) else 0
    P["W-AL-01"] = len([r for r in g.objects(u, U.hasValidationResult) if list(g.objects(r, U.hasUncertaintyQuantification))])
    P["W-AL-02"] = 1 if (list(g.objects(u, U.hasUncertaintyQuantification)) and list(g.objects(u, U.hasSensitivityAnalysis))) else 0
    P["W-ON-01"] = len(list(g.objects(u, U.hasContextOfUse)))
    P["W-ON-02"] = len([c for c in g.objects(u, U.hasContextOfUse)
                        if list(g.objects(c, U.hasApplicabilityConstraint)) or list(g.objects(c, U.hasOperatingEnvelope))])
    n = 0
    for req in g.objects(u, U.bindsRequirement):
        if not list(g.objects(req, U.requiredVerificationMethod)): continue
        for r in g.objects(u, U.hasValidationResult):
            for a in g.objects(r, PROV.wasGeneratedBy):
                if list(g.objects(a, U.activityType)): n += 1
    P["W-AR-03"] = n
    n = 0
    for r in g.objects(u, U.hasValidationResult):
        for a in g.objects(r, PROV.wasGeneratedBy):
            for cfg in g.objects(a, PROV.used):
                if list(g.objects(cfg, U.modelVersion)): n += 1
    P["W-AR-04"] = n if list(g.objects(u, U.currentModelVersion)) else 0
    P["W-AR-05"] = len([r for r in g.objects(u, U.hasValidationResult) if list(g.objects(r, U.comparedAgainst))])
    P["W-SI-01"] = len(list(g.objects(u, U.signature)))
    P["W-SI-02"] = len(list(g.objects(u, U.bindsRequirement))) + len(list(g.objects(u, U.hasValidationResult)))
    P["W-CON-02"] = len([o for s, o in g.subject_objects(U.referencesIdentifier)
                         if list(g.objects(o, RDF.type)) or list(g.objects(o, SCHEMA.url))])
    n = 0
    if list(g.objects(u, U.signatureTimestamp)):
        n = len([e for e in g.objects(u, U.hasEvidence) if list(g.objects(e, U.evidenceTimestamp))])
    P["W-CON-03"] = n
    P["W-CON-04"] = 1 if ((u, U.conformsToProfile, U.ProfileComplete) in g and list(g.objects(u, U.hasSensitivityAnalysis))) else 0
    P["W-CON-05"] = len([a for a in g.objects(u, U.hasVerificationActivity)
                         if list(g.subjects(PROV.wasGeneratedBy, a))])
    n = 0
    for c in g.objects(u, U.bindsClaim):
        n += len(list(g.objects(c, PROV.wasDerivedFrom)))
    P["W-PROV-01"] = n
    return P

ORDER = ["W-EP-01","W-EP-02","W-EP-03","W-AL-01","W-AL-02","W-ON-01","W-ON-02",
         "W-AR-03","W-AR-04","W-AR-05","W-SI-01","W-SI-02","W-CON-02","W-CON-03",
         "W-CON-04","W-CON-05","W-PROV-01"]

res = {}
for name, path in SUBS.items():
    g = load(path)
    u = uoa(g)
    print(f"{name}: {len(g)} triples, UoA={'yes' if u else 'NO'}", file=sys.stderr)
    res[name] = probes(g, u)

print(f"\n{'pattern':11} " + " ".join(f"{n:>14}" for n in SUBS) + "   class")
cls_counts = {"A": [], "B": []}
for p in ORDER:
    row = [res[n][p] for n in SUBS]
    cls = "A" if any(v > 0 for v in row) else "B"
    cls_counts[cls].append(p)
    print(f"{p:11} " + " ".join(f"{v:>14}" for v in row) + f"   {cls}")
print(f"\nClass A ({len(cls_counts['A'])}): {', '.join(cls_counts['A'])}")
print(f"Class B ({len(cls_counts['B'])}): {', '.join(cls_counts['B'])}")
