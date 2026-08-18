package net.uofa.oos;

import net.uofa.JsonLdLoader;

import org.apache.jena.graph.Node;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.reasoner.rulesys.Rule;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link OOSEngine#evaluateRule} — the path-two LHS-decomposition
 * core. Tests build small in-memory packages and rules and assert on the
 * resulting OOSResult shape.
 */
class OOSEngineTest {

    /** Locate the repo root by walking up looking for the production rules file. */
    private static Path repoRoot() {
        Path p = Path.of("").toAbsolutePath();
        while (!Files.exists(p.resolve("packs/vv40/rules/oos/oos_v0.1.rules"))) {
            Path parent = p.getParent();
            if (parent == null) throw new RuntimeException("Cannot find repo root");
            p = parent;
        }
        return p;
    }

    @Test
    void firesOnCal021WithProductionRules() throws Exception {
        Path root = repoRoot();
        Path pkg = root.resolve("specs/calibration/packages/cal-021-out_of_scope-stub.jsonld");
        Path rules = root.resolve("packs/vv40/rules/oos/oos_v0.1.rules");
        Path ctx = root.resolve("spec/context/v0.5.jsonld");

        Model data = JsonLdLoader.load(pkg, ctx);
        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata = OOSEngine.CommentBlockParser.parse(rules);

        // Find the model-form rule and evaluate
        Rule modelFormRule = ruleList.stream()
            .filter(r -> "oos_modelform_adequacy_warranted".equals(r.getName()))
            .findFirst()
            .orElseThrow();
        OOSEngine.RuleMetadata meta = metadata.get(modelFormRule.getName());

        List<OOSEngine.OOSResult> results = OOSEngine.evaluateRule(modelFormRule, meta, data);
        assertEquals(1, results.size(), "Expected exactly 1 OOS firing on cal-021");

        OOSEngine.OOSResult r = results.get(0);
        assertEquals("oos_modelform_adequacy_warranted", r.ruleName);
        // The claim binding should map to the cal-021 claim URI
        Node claim = r.binding.get("claim");
        assertNotNull(claim);
        assertEquals("https://uofa.net/calibration/oos-021/claim", claim.getURI());

        // The failing clause should mention hasSupportingEvidence (clause 5,
        // the first sufficiency clause that fails because the package has no
        // hasSupportingEvidence triple linking the claim to evidence).
        String rendered = OOSEngine.renderTriplePattern(r.failure.failingClause, r.failure.bindings);
        assertTrue(rendered.contains("hasSupportingEvidence"),
            "Expected failing clause to involve hasSupportingEvidence, got: " + rendered);
    }

    @Test
    void doesNotFireOnInScopePackage() throws Exception {
        Path root = repoRoot();
        Path pkg = root.resolve(
            "specs/calibration/packages/cal-001-correct_detection-inconsistent.jsonld");
        Path rules = root.resolve("packs/vv40/rules/oos/oos_v0.1.rules");
        Path ctx = root.resolve("spec/context/v0.5.jsonld");

        Model data = JsonLdLoader.load(pkg, ctx);
        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata = OOSEngine.CommentBlockParser.parse(rules);

        // Aggregate firings across all 5 rules. In-scope packages should
        // produce zero firings (discriminator clauses don't match because
        // there's no OOS sourceTaxonomy literal in the package).
        int totalFirings = 0;
        for (Rule rule : ruleList) {
            totalFirings += OOSEngine.evaluateRule(rule, metadata.get(rule.getName()), data).size();
        }
        assertEquals(0, totalFirings,
            "Expected no OOS firings on in-scope cal-001 package");
    }

    @Test
    void multiBindingCase(@TempDir Path tmp) throws Exception {
        // Construct a synthetic package with TWO UnitOfAssurance instances
        // matching the same OOS taxonomy. The engine should emit two OOS
        // results — one per binding.
        Path pkg = tmp.resolve("two_uofas.jsonld");
        Files.writeString(pkg, ""
            + "{\n"
            + "  \"@context\": {\n"
            + "    \"@vocab\": \"https://uofa.net/vocab#\",\n"
            + "    \"id\": \"@id\",\n"
            + "    \"type\": \"@type\"\n"
            + "  },\n"
            + "  \"@graph\": [\n"
            + "    {\n"
            + "      \"id\": \"https://example.test/uofa-A\",\n"
            + "      \"type\": \"UnitOfAssurance\",\n"
            + "      \"bindsClaim\": {\"id\": \"https://example.test/claim-A\"},\n"
            + "      \"adversarialProvenance\": {\n"
            + "        \"sourceTaxonomy\": \"oos/subjective-model-form-adequacy\"\n"
            + "      }\n"
            + "    },\n"
            + "    {\n"
            + "      \"id\": \"https://example.test/uofa-B\",\n"
            + "      \"type\": \"UnitOfAssurance\",\n"
            + "      \"bindsClaim\": {\"id\": \"https://example.test/claim-B\"},\n"
            + "      \"adversarialProvenance\": {\n"
            + "        \"sourceTaxonomy\": \"oos/subjective-model-form-adequacy\"\n"
            + "      }\n"
            + "    }\n"
            + "  ]\n"
            + "}\n");

        Path rules = repoRoot().resolve("packs/vv40/rules/oos/oos_v0.1.rules");
        Model data = JsonLdLoader.load(pkg, null);
        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata = OOSEngine.CommentBlockParser.parse(rules);
        Rule modelForm = ruleList.stream()
            .filter(r -> "oos_modelform_adequacy_warranted".equals(r.getName()))
            .findFirst()
            .orElseThrow();

        List<OOSEngine.OOSResult> results = OOSEngine.evaluateRule(
            modelForm, metadata.get(modelForm.getName()), data);
        assertEquals(2, results.size(), "Expected one OOS result per UofA");

        // Verify both claims are represented
        java.util.Set<String> claimUris = new java.util.HashSet<>();
        for (OOSEngine.OOSResult r : results) {
            Node claim = r.binding.get("claim");
            assertNotNull(claim);
            claimUris.add(claim.getURI());
        }
        assertTrue(claimUris.contains("https://example.test/claim-A"));
        assertTrue(claimUris.contains("https://example.test/claim-B"));
    }

    @Test
    void rejectsInvalidSufficiencyStartsAt(@TempDir Path tmp) throws Exception {
        // Build a 3-clause rule and set sufficiency_starts_at=10 (out of range).
        Path rules = tmp.resolve("invalid.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.\n"
            + "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#>.\n"
            + "# defeater_type: x\n"
            + "# missing_evidence: y\n"
            + "# sufficiency_starts_at: 10\n"  // way out of range
            + "[r1: (?u uofa:bundleSufficient \"true\"^^xsd:boolean) <-\n"
            + "  (?u rdf:type uofa:UnitOfAssurance)\n"
            + "  (?u uofa:bindsClaim ?c)\n"
            + "  (?c uofa:hasSupportingEvidence ?e)\n"
            + "]\n");

        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata = OOSEngine.CommentBlockParser.parse(rules);

        org.apache.jena.rdf.model.Model emptyData =
            org.apache.jena.rdf.model.ModelFactory.createDefaultModel();

        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> OOSEngine.evaluateRule(ruleList.get(0), metadata.get("r1"), emptyData));
        assertTrue(ex.getMessage().contains("sufficiency_starts_at"));
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Backtracking over multi-valued sufficiency clauses
    // ────────────────────────────────────────────────────────────────────────

    private static final String STUDY =
        "{\"id\": \"https://example.test/ev/study\", "
        + "\"type\": \"StructuredComparisonStudy\"}";
    private static final String OTHER =
        "{\"id\": \"https://example.test/ev/other\", "
        + "\"type\": \"ValidationResult\"}";

    /** A cal-021-shaped package whose claim carries the given evidence list. */
    private static String packageWithEvidence(String evidenceJsonArray) {
        return ""
            + "{\n"
            + "  \"@context\": {\n"
            + "    \"@vocab\": \"https://uofa.net/vocab#\",\n"
            + "    \"id\": \"@id\",\n"
            + "    \"type\": \"@type\"\n"
            + "  },\n"
            + "  \"id\": \"https://example.test/uofa\",\n"
            + "  \"type\": \"UnitOfAssurance\",\n"
            + "  \"adversarialProvenance\": {\n"
            + "    \"sourceTaxonomy\": \"oos/subjective-model-form-adequacy\"\n"
            + "  },\n"
            + "  \"bindsClaim\": {\n"
            + "    \"id\": \"https://example.test/claim\",\n"
            + "    \"type\": \"AssuranceClaim\",\n"
            + "    \"hasSupportingEvidence\": " + evidenceJsonArray + "\n"
            + "  }\n"
            + "}\n";
    }

    private static List<OOSEngine.OOSResult> runModelFormRule(Path pkg) throws Exception {
        Path rules = repoRoot().resolve("packs/vv40/rules/oos/oos_v0.1.rules");
        Model data = JsonLdLoader.load(pkg, null);
        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata =
            OOSEngine.CommentBlockParser.parse(rules);
        Rule modelForm = ruleList.stream()
            .filter(r -> "oos_modelform_adequacy_warranted".equals(r.getName()))
            .findFirst()
            .orElseThrow();
        return OOSEngine.evaluateRule(modelForm, metadata.get(modelForm.getName()), data);
    }

    /**
     * The required evidence is present in BOTH orderings, so neither is a gap.
     * Before backtracking the engine bound ?evidence to the first triple
     * returned and never reconsidered, so whichever ordering left the study out
     * of that binding produced a false OUT-OF-SCOPE — a verdict that depended
     * on Jena's triple iteration order rather than on the document.
     */
    @Test
    void backtracksWhenRequiredEvidenceIsNotFirstCandidate(@TempDir Path tmp) throws Exception {
        String[][] variants = {
            {"required_first",  "[" + STUDY + ", " + OTHER + "]"},
            {"required_second", "[" + OTHER + ", " + STUDY + "]"},
        };
        for (String[] variant : variants) {
            Path pkg = tmp.resolve(variant[0] + ".jsonld");
            Files.writeString(pkg, packageWithEvidence(variant[1]));
            assertEquals(0, runModelFormRule(pkg).size(),
                "Ordering '" + variant[0] + "' contains the required "
                + "StructuredComparisonStudy, so no gap should be reported");
        }
    }

    /**
     * Control for the fix above: backtracking must not turn every package into
     * a pass. A claim whose evidence genuinely lacks the required type still
     * reports the gap, and still names the clause that could not be satisfied.
     */
    @Test
    void stillReportsGapWhenRequiredEvidenceIsGenuinelyAbsent(@TempDir Path tmp) throws Exception {
        Path pkg = tmp.resolve("no_study.jsonld");
        Files.writeString(pkg, packageWithEvidence("[" + OTHER + "]"));

        List<OOSEngine.OOSResult> results = runModelFormRule(pkg);
        assertEquals(1, results.size(), "Missing evidence type must still fire");
        assertTrue(
            results.get(0).failure.failingClause.getObject().toString()
                .contains("StructuredComparisonStudy"),
            "The failing clause should be the unsatisfiable rdf:type check");
    }

    /**
     * The decisive case: a bundle that is genuinely SUFFICIENT must clear.
     *
     * <p>The iso42001 rules chain three separate hasSupportingEvidence clauses,
     * each followed by its own rdf:type check. Under v0.1 every one of those
     * three variables bound to the same first-returned evidence node, so the
     * rule could only clear if a single node carried all three required types
     * at once — which never happens. Those rules were in effect unconditional
     * gap reporters for any claim they discriminated on.
     *
     * <p>It went unnoticed because every OOS calibration package is an
     * out_of_scope case that SHOULD report a gap, so the rules were never
     * exercised against a bundle that should pass. This test is that case.
     */
    @Test
    void clearsABundleThatCarriesEveryRequiredEvidenceType(@TempDir Path tmp) throws Exception {
        Path pkg = tmp.resolve("aims_sufficient.jsonld");
        Files.writeString(pkg, ""
            + "{\n"
            + "  \"@context\": {\n"
            + "    \"@vocab\": \"https://uofa.net/vocab#\",\n"
            + "    \"aims\": \"https://uofa.net/vocab/aims#\",\n"
            + "    \"id\": \"@id\",\n"
            + "    \"type\": \"@type\"\n"
            + "  },\n"
            + "  \"id\": \"https://example.test/uofa-sufficient\",\n"
            + "  \"type\": \"UnitOfAssurance\",\n"
            + "  \"bindsClaim\": {\n"
            + "    \"id\": \"https://example.test/claim/policy\",\n"
            + "    \"type\": \"aims:AIPolicyAppropriatenessClaim\",\n"
            + "    \"hasSupportingEvidence\": [\n"
            + "      {\"id\": \"https://example.test/ev/policy\",  \"type\": \"aims:AIPolicy\"},\n"
            + "      {\"id\": \"https://example.test/ev/purpose\", \"type\": \"aims:OrganizationalPurposeStatement\"},\n"
            + "      {\"id\": \"https://example.test/ev/review\",  \"type\": \"aims:PolicyToPurposeReviewRecord\"}\n"
            + "    ]\n"
            + "  }\n"
            + "}\n");

        Path rules = repoRoot().resolve("packs/iso42001/rules/oos/oos_v0.1.rules");
        Model data = JsonLdLoader.load(pkg, null);
        List<Rule> ruleList = Rule.rulesFromURL("file:" + rules.toAbsolutePath());
        Map<String, OOSEngine.RuleMetadata> metadata =
            OOSEngine.CommentBlockParser.parse(rules);
        Rule policyRule = ruleList.stream()
            .filter(r -> "oos_aims_policy_appropriateness_warranted".equals(r.getName()))
            .findFirst()
            .orElseThrow();

        List<OOSEngine.OOSResult> results = OOSEngine.evaluateRule(
            policyRule, metadata.get(policyRule.getName()), data);
        assertEquals(0, results.size(),
            "Bundle carries AIPolicy, OrganizationalPurposeStatement AND "
            + "PolicyToPurposeReviewRecord, so the rule must clear it");
    }
}
