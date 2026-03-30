"""Unit tests for the uofa_cli.explain module."""

from uofa_cli.explain import explain_divergence


DOC_A = {
    "name": "COU1",
    "hasContextOfUse": {"name": "COU1: Test context"},
}

DOC_B = {
    "name": "COU2",
    "hasContextOfUse": {"name": "COU2: Other context"},
}


class TestDescriptionPassthrough:
    def test_uses_description_when_present(self):
        w = {
            "patternId": "W-AL-01",
            "severity": "High",
            "affectedNode": "https://example.org/val1",
            "description": "Validation result lacks uncertainty quantification.",
        }
        lines = explain_divergence("W-AL-01", DOC_A, DOC_B, w)
        assert len(lines) == 2
        assert "COU1" in lines[0]
        assert "Validation result lacks uncertainty quantification." in lines[0]
        assert "COU2" in lines[1]
        assert "does not fire" in lines[1]

    def test_any_pattern_id_works(self):
        """The module does not hardcode any pattern IDs."""
        w = {
            "patternId": "W-CUSTOM-99",
            "severity": "Medium",
            "affectedNode": "https://example.org/node",
            "description": "Custom rule fired because of X.",
        }
        lines = explain_divergence("W-CUSTOM-99", DOC_A, DOC_B, w)
        assert "Custom rule fired because of X." in lines[0]

    def test_compound_pattern_works(self):
        w = {
            "patternId": "COMPOUND-01",
            "severity": "Critical",
            "affectedNode": "https://example.org/uofa",
            "description": "Critical and High weakeners coexist — risk escalation.",
        }
        lines = explain_divergence("COMPOUND-01", DOC_A, DOC_B, w)
        assert "risk escalation" in lines[0]


class TestFallbackBehavior:
    def test_fallback_with_affected_node(self):
        """Without description, shows pattern ID and affected node."""
        w = {
            "patternId": "W-EP-01",
            "severity": "Critical",
            "affectedNode": "https://example.org/claim1",
        }
        lines = explain_divergence("W-EP-01", DOC_A, DOC_B, w)
        assert len(lines) == 2
        assert "W-EP-01" in lines[0]
        assert "claim1" in lines[0]

    def test_fallback_without_affected_node(self):
        """Without description or affectedNode, shows just pattern ID."""
        w = {"patternId": "W-XX-99", "severity": "Low"}
        lines = explain_divergence("W-XX-99", DOC_A, DOC_B, w)
        assert "W-XX-99" in lines[0]

    def test_empty_doc_graceful(self):
        """Handles docs with no COU metadata."""
        empty = {"name": "Empty"}
        w = {"patternId": "W-AL-01", "severity": "High"}
        lines = explain_divergence("W-AL-01", empty, empty, w)
        assert len(lines) >= 1
        assert "Empty" in lines[0]
