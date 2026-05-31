"""Phase A: surrogate pack scaffold + vocabulary registration tests.

Asserts the pack manifest loads, the pack is discoverable, the shapes file
parses as valid Turtle, and the uofa-surr: vocabulary terms required by the
weakener catalog and the SIP field-to-pattern map are declared.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli import paths

PACK = "surrogate"
SURR = "https://uofa.net/vocab/surrogate#"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_pack_discoverable() -> None:
    assert PACK in paths.list_packs(root=_repo_root())


def test_manifest_loads_and_is_versioned() -> None:
    manifest = paths.pack_manifest(PACK, root=_repo_root())
    assert manifest["name"] == "surrogate"
    # Pack version stamps independently of the CLI release.
    assert manifest["version"] == "0.1.0"
    # Detection config is read source-agnostically: surrogate is migrated to the
    # capabilities[] shape (shapes live in the detection capability's payload), so
    # assert via the accessor rather than the legacy flat field.
    assert paths.detection_config(manifest)["shapes"] == "shapes/surrogate_shapes.ttl"


def test_shapes_file_exists() -> None:
    shapes = paths.pack_dir(PACK, root=_repo_root()) / "shapes" / "surrogate_shapes.ttl"
    assert shapes.is_file()


def _load_graph():
    rdflib = pytest.importorskip("rdflib")
    shapes = paths.pack_dir(PACK, root=_repo_root()) / "shapes" / "surrogate_shapes.ttl"
    graph = rdflib.Graph()
    graph.parse(str(shapes), format="turtle")  # raises on malformed Turtle
    return rdflib, graph


def test_shapes_parse_as_turtle() -> None:
    _, graph = _load_graph()
    assert len(graph) > 0


@pytest.mark.parametrize(
    "cls",
    [
        "SurrogateModel",
        "TrainingEnvelope",
        "EnvelopeDimension",
        "EvaluationPoint",
        "EvaluationRegion",
        "PhysicsConstraint",
        "ConstraintCheckEvidence",
        "ParentModelSnapshot",
        "BenchmarkProvenance",
    ],
)
def test_vocabulary_class_declared(cls: str) -> None:
    rdflib, graph = _load_graph()
    rdf_type = rdflib.RDF.type
    rdfs_class = rdflib.RDFS.Class
    term = rdflib.URIRef(SURR + cls)
    assert (term, rdf_type, rdfs_class) in graph, f"{cls} not declared as rdfs:Class"


@pytest.mark.parametrize(
    "prop",
    [
        "surrogateType",
        "trainingEnvelope",
        "evaluationPoint",
        "evaluationRegion",
        "declaredPhysicsConstraint",
        "hasConstraintCheckEvidence",
        "surrogateUQMethod",
        "hasBenchmarkProvenance",
        "parentModelSnapshot",
        "parentDecision",
        "_evalOutsideEnvelope",
    ],
)
def test_vocabulary_property_declared(prop: str) -> None:
    rdflib, graph = _load_graph()
    rdf_property = rdflib.RDF.Property
    term = rdflib.URIRef(SURR + prop)
    assert (term, rdflib.RDF.type, rdf_property) in graph, f"{prop} not declared as rdf:Property"


def test_surrogate_model_subclass_of_core_model() -> None:
    rdflib, graph = _load_graph()
    surrogate = rdflib.URIRef(SURR + "SurrogateModel")
    core_model = rdflib.URIRef("https://uofa.net/vocab#Model")
    assert (surrogate, rdflib.RDFS.subClassOf, core_model) in graph
