package net.uofa.oos;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link OOSEngine.CommentBlockParser}.
 *
 * The parser reads a Jena rules file as raw text and extracts the
 * {@code # key: value} comment block immediately preceding each rule
 * definition (per src/uofa_cli/oos/SCHEMA_NOTES.md §8 format).
 */
class CommentBlockParserTest {

    @Test
    void parsesAllFiveProductionRules(@TempDir Path tmp) throws Exception {
        // Use the actual production rule file as the integration anchor.
        Path repoRoot = Path.of("").toAbsolutePath();
        // Walk up to find the repo root marker.
        while (!Files.exists(repoRoot.resolve("packs/vv40/rules/oos/oos_v0.1.rules"))) {
            Path parent = repoRoot.getParent();
            if (parent == null) {
                fail("Could not locate repo root containing packs/vv40/rules/oos/oos_v0.1.rules");
            }
            repoRoot = parent;
        }
        Path rules = repoRoot.resolve("packs/vv40/rules/oos/oos_v0.1.rules");

        Map<String, OOSEngine.RuleMetadata> metadata =
            OOSEngine.CommentBlockParser.parse(rules);

        assertEquals(5, metadata.size(), "Expected 5 rule metadata blocks");
        assertTrue(metadata.containsKey("oos_modelform_adequacy_warranted"));
        assertTrue(metadata.containsKey("oos_tacit_knowledge_warranted"));
        assertTrue(metadata.containsKey("oos_behavioral_compliance_warranted"));
        assertTrue(metadata.containsKey("oos_jurisdictional_alignment_warranted"));
        assertTrue(metadata.containsKey("oos_clinical_arbitration_warranted"));

        // Spot-check field semantics on rule 1.
        OOSEngine.RuleMetadata m = metadata.get("oos_modelform_adequacy_warranted");
        assertEquals("cal-021", m.calibrationTarget);
        assertEquals(5, m.sufficiencyStartsAt);
        assertTrue(m.defeaterType.contains("model-form adequacy"));
        assertTrue(m.missingEvidence.contains("structured model-form comparison studies"));
    }

    @Test
    void parsesMinimalSingleRule(@TempDir Path tmp) throws Exception {
        Path rules = tmp.resolve("min.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.\n"
            + "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#>.\n"
            + "\n"
            + "# bundle_check_rule_name: r1\n"
            + "# calibration_target: cal-XXX\n"
            + "# defeater_type: a defeater type\n"
            + "# missing_evidence: an evidence phrase\n"
            + "# sufficiency_starts_at: 2\n"
            + "[r1:\n"
            + "    (?u uofa:bundleSufficient \"true\"^^xsd:boolean)\n"
            + "    <-\n"
            + "    (?u rdf:type uofa:UnitOfAssurance)\n"
            + "    (?u uofa:hasSupportingEvidence ?e)\n"
            + "]\n");
        Map<String, OOSEngine.RuleMetadata> meta = OOSEngine.CommentBlockParser.parse(rules);
        assertEquals(1, meta.size());
        OOSEngine.RuleMetadata m = meta.get("r1");
        assertNotNull(m);
        assertEquals(2, m.sufficiencyStartsAt);
        assertEquals("a defeater type", m.defeaterType);
        assertEquals("an evidence phrase", m.missingEvidence);
    }

    @Test
    void rejectsMissingSufficiencyStartsAt(@TempDir Path tmp) throws Exception {
        Path rules = tmp.resolve("bad.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "# bundle_check_rule_name: r1\n"
            + "# defeater_type: x\n"
            + "# missing_evidence: y\n"
            // no sufficiency_starts_at
            + "[r1: (?u uofa:p \"v\") <- (?u uofa:p \"v\") ]\n");
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> OOSEngine.CommentBlockParser.parse(rules));
        assertTrue(ex.getMessage().contains("sufficiency_starts_at"),
            "Expected error message to mention missing sufficiency_starts_at, got: " + ex.getMessage());
    }

    @Test
    void rejectsRuleNameMismatch(@TempDir Path tmp) throws Exception {
        Path rules = tmp.resolve("mismatch.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "# bundle_check_rule_name: r_DECLARED\n"
            + "# defeater_type: x\n"
            + "# missing_evidence: y\n"
            + "# sufficiency_starts_at: 2\n"
            + "[r_ACTUAL: (?u uofa:p \"v\") <- (?u uofa:p \"v\") (?u uofa:q \"v\") ]\n");
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> OOSEngine.CommentBlockParser.parse(rules));
        assertTrue(ex.getMessage().contains("does not match"),
            "Expected error message to mention rule name mismatch, got: " + ex.getMessage());
    }

    @Test
    void rejectsNonIntegerSufficiencyStartsAt(@TempDir Path tmp) throws Exception {
        Path rules = tmp.resolve("badnum.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "# defeater_type: x\n"
            + "# missing_evidence: y\n"
            + "# sufficiency_starts_at: not-a-number\n"
            + "[r1: (?u uofa:p \"v\") <- (?u uofa:p \"v\") ]\n");
        IllegalArgumentException ex = assertThrows(
            IllegalArgumentException.class,
            () -> OOSEngine.CommentBlockParser.parse(rules));
        assertTrue(ex.getMessage().contains("sufficiency_starts_at"));
    }

    @Test
    void prefixDeclarationResetsBlock(@TempDir Path tmp) throws Exception {
        // A kv line that appears BEFORE a @prefix declaration must NOT bleed
        // into the next rule's metadata.
        Path rules = tmp.resolve("reset.rules");
        Files.writeString(rules, ""
            + "# defeater_type: SHOULD-NOT-LEAK\n"
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "# defeater_type: real-defeater\n"
            + "# missing_evidence: real-evidence\n"
            + "# sufficiency_starts_at: 2\n"
            + "[r1: (?u uofa:p \"v\") <- (?u uofa:p \"v\") (?u uofa:q \"v\") ]\n");
        Map<String, OOSEngine.RuleMetadata> meta = OOSEngine.CommentBlockParser.parse(rules);
        assertEquals(1, meta.size());
        assertEquals("real-defeater", meta.get("r1").defeaterType);
    }

    @Test
    void rulesWithoutMetadataAreSkipped(@TempDir Path tmp) throws Exception {
        // Two rules, only one with a metadata block. The other has no
        // preceding kv block — it should NOT appear in the parsed map
        // (the runtime warns and skips).
        Path rules = tmp.resolve("partial.rules");
        Files.writeString(rules, ""
            + "@prefix uofa: <https://uofa.net/vocab#>.\n"
            + "[r_no_meta: (?u uofa:p \"v\") <- (?u uofa:p \"v\") ]\n"
            + "\n"
            + "# defeater_type: d\n"
            + "# missing_evidence: e\n"
            + "# sufficiency_starts_at: 2\n"
            + "[r_with_meta: (?u uofa:p \"v\") <- (?u uofa:p \"v\") (?u uofa:q \"v\") ]\n");
        Map<String, OOSEngine.RuleMetadata> meta = OOSEngine.CommentBlockParser.parse(rules);
        assertEquals(1, meta.size());
        assertTrue(meta.containsKey("r_with_meta"));
        assertFalse(meta.containsKey("r_no_meta"));
    }
}
