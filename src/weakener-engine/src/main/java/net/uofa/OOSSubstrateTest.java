package net.uofa;

import org.apache.jena.rdf.model.*;
import org.apache.jena.reasoner.Derivation;
import org.apache.jena.reasoner.TriplePattern;
import org.apache.jena.reasoner.rulesys.ClauseEntry;
import org.apache.jena.reasoner.rulesys.GenericRuleReasoner;
import org.apache.jena.reasoner.rulesys.Rule;
import org.apache.jena.reasoner.rulesys.RuleDerivation;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.vocabulary.RDF;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import java.io.*;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.Callable;

/**
 * UofA OOS Backward-Chaining Substrate Validation Test
 *
 * Runs the four-property substrate test specified in
 * UofA_OOS_Substrate_Validation_Test_v0_1.md (PRD §2):
 *   A — hybrid mode loads cleanly
 *   B — backward rule fires on goal query
 *   C — structured failure information returnable (native + LHS-decomp diagnostic)
 *   D — C3 forward rules continue producing the same firings
 *
 * Emits a single JSON report to --report-path. Exit code 0 if the test ran to
 * completion (regardless of property pass/fail); non-zero only on harness errors.
 */
@Command(
    name = "uofa-substrate-test",
    mixinStandardHelpOptions = true,
    version = "0.1.0",
    description = "OOS backward-chaining substrate validation test (Jena hybrid mode)."
)
public class OOSSubstrateTest implements Callable<Integer> {

    private static final String UOFA_NS = "https://uofa.net/vocab#";
    private static final String JENA_VERSION = "5.3.0";
    private static final String TEST_ID = "substrate_validation_v0.1";

    @Option(names = "--cal-021-path", required = true,
            description = "Path to cal-021 JSONLD calibration package")
    private Path cal021Path;

    @Option(names = "--c3-rules-path", required = true,
            description = "Path to C3 forward rules file (uofa_weakener.rules)")
    private Path c3RulesPath;

    @Option(names = "--oos-rule-path", required = true,
            description = "Path to OOS backward rule file (oos_backward_v0.1.rules)")
    private Path oosRulePath;

    @Option(names = "--vocab-path", required = true,
            description = "Path to OOS vocab additions (oos_substrate_test.ttl)")
    private Path vocabPath;

    @Option(names = "--context-path", required = true,
            description = "Path to JSONLD context file (spec/context/v0.5.jsonld)")
    private Path contextPath;

    @Option(names = "--report-path", required = true,
            description = "Output path for JSON test report")
    private Path reportPath;

    @Option(names = "--claim-iri", defaultValue = "https://uofa.net/calibration/oos-021/claim",
            description = "IRI of the claim node in cal-021 to add ModelFormAdequacyClaim typing to")
    private String claimIri;

    @Option(names = "--mode", defaultValue = "full",
            description = "Test mode: full | forward-only-baseline | a1-parse-only")
    private String mode;

    @Option(names = "--verbose", description = "Enable Jena rule tracing (noisy)")
    private boolean verbose;

    private final ObjectMapper json = new ObjectMapper()
            .enable(SerializationFeature.INDENT_OUTPUT);

    @Override
    public Integer call() throws Exception {
        long startMs = System.currentTimeMillis();
        ObjectNode report = json.createObjectNode();
        report.put("test_id", TEST_ID);
        report.put("test_date", Instant.now().toString());
        report.put("jena_version", JENA_VERSION);
        report.put("package_under_test", cal021Path.toString());
        report.put("rule_under_test", oosRulePath.toString());
        report.put("mode", mode);

        try {
            switch (mode) {
                case "a1-parse-only":
                    runA1ParseOnly(report);
                    break;
                case "forward-only-baseline":
                    runForwardOnlyBaseline(report);
                    break;
                case "full":
                default:
                    runFull(report);
                    break;
            }
        } catch (Throwable t) {
            ObjectNode err = report.putObject("harness_error");
            err.put("type", t.getClass().getName());
            err.put("message", String.valueOf(t.getMessage()));
            err.put("stack", stackToString(t));
            report.put("overall_pass", false);
            report.put("outcome_classification", "HARNESS_ERROR");
        }

        report.put("elapsed_seconds", (System.currentTimeMillis() - startMs) / 1000.0);
        Files.writeString(reportPath, json.writeValueAsString(report));
        System.err.println("Report written: " + reportPath);
        return 0;
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Mode dispatchers
    // ────────────────────────────────────────────────────────────────────────

    private void runA1ParseOnly(ObjectNode report) {
        ObjectNode a1 = report.putObject("property_a1_standalone_parse");
        try {
            List<Rule> oosRules = Rule.rulesFromURL("file:" + oosRulePath.toAbsolutePath());
            a1.put("passed", true);
            a1.put("rules_parsed", oosRules.size());
            a1.put("first_rule_name", oosRules.isEmpty() ? null : oosRules.get(0).getName());
        } catch (Throwable t) {
            a1.put("passed", false);
            a1.put("error_type", t.getClass().getName());
            a1.put("error_message", String.valueOf(t.getMessage()));
        }
    }

    private void runForwardOnlyBaseline(ObjectNode report) throws Exception {
        Model data = JsonLdLoader.load(cal021Path, contextPath);
        List<Rule> c3Rules = Rule.rulesFromURL("file:" + c3RulesPath.toAbsolutePath());

        InfModel inf = buildReasoner(c3Rules, GenericRuleReasoner.FORWARD_RETE, false).bind(data.getGraph()) instanceof InfModel
                ? null : null; // unused branch
        // Build inference model the standard way
        GenericRuleReasoner reasoner = new GenericRuleReasoner(c3Rules);
        reasoner.setMode(GenericRuleReasoner.FORWARD_RETE);
        InfModel infModel = ModelFactory.createInfModel(reasoner, data);
        infModel.prepare();

        List<Firing> baseline = extractFirings(infModel);
        ArrayNode arr = report.putArray("forward_only_baseline_firings");
        for (Firing f : baseline) arr.add(firingToJson(f));
        report.put("baseline_count", baseline.size());
    }

    private void runFull(ObjectNode report) throws Exception {
        // ── Load shared inputs ─────────────────────────────────────────────
        Model originalData = JsonLdLoader.load(cal021Path, contextPath);
        Model vocabModel = ModelFactory.createDefaultModel();
        vocabModel.read(vocabPath.toUri().toString(), null, "TTL");
        // Vocab triples merged into the data graph so RDFS class/subclass info
        // is available to the reasoner. Substrate-test scope only — production
        // packages do not include this vocab.
        originalData.add(vocabModel);

        List<Rule> c3Rules = Rule.rulesFromURL("file:" + c3RulesPath.toAbsolutePath());

        // ── Property A.1: standalone OOS rule parse ────────────────────────
        ObjectNode a1 = report.putObject("property_a1_standalone_parse");
        List<Rule> oosRules;
        try {
            oosRules = Rule.rulesFromURL("file:" + oosRulePath.toAbsolutePath());
            a1.put("passed", true);
            a1.put("rules_parsed", oosRules.size());
            a1.put("first_rule_name", oosRules.isEmpty() ? null : oosRules.get(0).getName());
            if (oosRules.isEmpty()) {
                a1.put("passed", false);
                a1.put("error_message", "OOS rules file parsed but contained zero rules");
                report.put("overall_pass", false);
                report.put("outcome_classification", "3");
                return;
            }
        } catch (Throwable t) {
            a1.put("passed", false);
            a1.put("error_type", t.getClass().getName());
            a1.put("error_message", String.valueOf(t.getMessage()));
            report.put("overall_pass", false);
            report.put("outcome_classification", "3");
            return;
        }

        // ── Run 1: forward-only baseline (Property D baseline) ─────────────
        Model run1Data = ModelFactory.createDefaultModel().add(originalData);
        addModelFormAdequacyTyping(run1Data);
        List<Firing> baselineFirings;
        try {
            GenericRuleReasoner r1 = new GenericRuleReasoner(c3Rules);
            r1.setMode(GenericRuleReasoner.FORWARD_RETE);
            InfModel inf1 = ModelFactory.createInfModel(r1, run1Data);
            inf1.prepare();
            baselineFirings = extractFirings(inf1);
        } catch (Throwable t) {
            ObjectNode err = report.putObject("baseline_run_error");
            err.put("type", t.getClass().getName());
            err.put("message", String.valueOf(t.getMessage()));
            report.put("overall_pass", false);
            report.put("outcome_classification", "HARNESS_ERROR");
            return;
        }

        // ── Run 2: hybrid mode with C3 + OOS rules ─────────────────────────
        ObjectNode propA = report.putObject("property_a");
        Model run2Data = ModelFactory.createDefaultModel().add(originalData);
        addModelFormAdequacyTyping(run2Data);

        List<Rule> combinedRules = new ArrayList<>();
        combinedRules.addAll(c3Rules);
        combinedRules.addAll(oosRules);

        InfModel inf2;
        GenericRuleReasoner r2;
        try {
            r2 = new GenericRuleReasoner(combinedRules);
            r2.setMode(GenericRuleReasoner.HYBRID);
            r2.setDerivationLogging(true);
            if (verbose) {
                r2.setParameter(
                    org.apache.jena.vocabulary.ReasonerVocabulary.PROPtraceOn,
                    Boolean.TRUE);
            }
            inf2 = ModelFactory.createInfModel(r2, run2Data);
            inf2.prepare();
            propA.put("passed", true);
            propA.put("details", "Hybrid mode reasoner instantiated and prepared without exception.");
            propA.put("c3_rule_count", c3Rules.size());
            propA.put("oos_rule_count", oosRules.size());
        } catch (Throwable t) {
            propA.put("passed", false);
            propA.put("error_type", t.getClass().getName());
            propA.put("error_message", String.valueOf(t.getMessage()));
            report.put("overall_pass", false);
            report.put("outcome_classification", "3");
            return;
        }

        // ── Property B: backward goal query ────────────────────────────────
        Resource claimRes = inf2.createResource(claimIri);
        Property bundleSufficient = inf2.createProperty(UOFA_NS, "bundleSufficient");

        ObjectNode propB = report.putObject("property_b");
        Statement provedStmt = null;
        boolean iteratorExecuted = false;
        boolean proofSuccess = false;
        try {
            StmtIterator goalIter = inf2.listStatements(claimRes, bundleSufficient, (RDFNode) null);
            iteratorExecuted = true;
            if (goalIter.hasNext()) {
                provedStmt = goalIter.next();
                proofSuccess = true;
            }
            goalIter.close();
            propB.put("passed", true);
            propB.put("proof_outcome", proofSuccess ? "success" : "failure");
            propB.put("details",
                "Backward chain executed via inf.listStatements; "
                + (proofSuccess ? "proof succeeded with at least one binding."
                                : "proof failed (empty StmtIterator)."));
            if (proofSuccess) {
                propB.put("proved_object", provedStmt.getObject().toString());
            }
        } catch (Throwable t) {
            propB.put("passed", false);
            propB.put("error_type", t.getClass().getName());
            propB.put("error_message", String.valueOf(t.getMessage()));
            propB.put("iterator_executed", iteratorExecuted);
        }

        // ── Property C: native trace + LHS-decomp diagnostic ───────────────
        ObjectNode propC = report.putObject("property_c");

        // ── C native ──
        ObjectNode cNative = propC.putObject("native");
        try {
            if (proofSuccess && provedStmt != null) {
                Iterator<Derivation> derivs = inf2.getDerivation(provedStmt);
                if (derivs != null && derivs.hasNext()) {
                    ArrayNode dArr = cNative.putArray("derivations");
                    while (derivs.hasNext()) {
                        Derivation d = derivs.next();
                        ObjectNode dObj = json.createObjectNode();
                        dObj.put("class", d.getClass().getName());
                        if (d instanceof RuleDerivation) {
                            RuleDerivation rd = (RuleDerivation) d;
                            dObj.put("rule_name", rd.getRule() != null ? rd.getRule().getName() : null);
                            ArrayNode matches = dObj.putArray("matches");
                            if (rd.getMatches() != null) {
                                for (Object m : rd.getMatches()) matches.add(String.valueOf(m));
                            }
                        }
                        StringWriter sw = new StringWriter();
                        d.printTrace(new PrintWriter(sw), true);
                        dObj.put("trace_text", sw.toString());
                        dArr.add(dObj);
                    }
                    cNative.put("passed", true);
                    cNative.put("details", "Native getDerivation returned RuleDerivation objects for the successful proof.");
                } else {
                    cNative.put("passed", false);
                    cNative.put("details", "Proof succeeded but inf.getDerivation returned null/empty — derivation not retained for backward proofs in this Jena version.");
                }
            } else {
                cNative.put("passed", false);
                cNative.put("details", "Proof failed (empty iterator). Jena GenericRuleReasoner does not expose a structured failure trace for failed backward proofs — getDerivation only operates on successfully derived statements.");
                cNative.put("attempted_api", "inf.getDerivation(statement)");
            }
        } catch (Throwable t) {
            cNative.put("passed", false);
            cNative.put("error_type", t.getClass().getName());
            cNative.put("error_message", String.valueOf(t.getMessage()));
        }

        // ── C LHS-decomposition diagnostic ──
        ObjectNode cDiag = propC.putObject("lhs_decomposition_diagnostic");
        try {
            Rule oosRule = oosRules.get(0);
            ClauseEntry[] body = oosRule.getBody();
            ArrayNode clauseResults = cDiag.putArray("clauses");

            // Bind ?claim to claimIri throughout decomposition
            Map<String, Resource> bindings = new HashMap<>();
            // The OOS rule uses ?claim; identify it from variable nodes in body
            // Pre-bind explicitly via the configured claim IRI
            String firstUnsatisfiedClause = null;
            String firstUnsatisfiedRendered = null;
            int firstUnsatisfiedIdx = -1;

            for (int i = 0; i < body.length; i++) {
                ClauseEntry clause = body[i];
                ObjectNode cObj = json.createObjectNode();
                cObj.put("index", i);
                cObj.put("clause_text", clause.toString());

                if (!(clause instanceof TriplePattern)) {
                    cObj.put("evaluated", false);
                    cObj.put("note", "Non-TriplePattern clause (functor/builtin) — not evaluated by LHS decomposition.");
                    clauseResults.add(cObj);
                    continue;
                }
                TriplePattern tp = (TriplePattern) clause;

                // Resolve subject/predicate/object using current bindings
                Resource s = resolveResource(run2Data, tp.getSubject(), bindings, claimIri);
                Property p = resolveProperty(run2Data, tp.getPredicate());
                RDFNode o = resolveObject(run2Data, tp.getObject(), bindings);

                StmtIterator it = run2Data.listStatements(s, p, o);
                boolean satisfied = it.hasNext();

                cObj.put("subject_bound", s != null ? s.toString() : "?(unbound)");
                cObj.put("predicate_bound", p != null ? p.toString() : "?(unbound)");
                cObj.put("object_bound", o != null ? o.toString() : "?(unbound)");
                cObj.put("satisfied", satisfied);

                if (satisfied) {
                    // Capture binding from first match if there are unbound vars
                    Statement match = it.next();
                    captureBindings(tp, match, bindings);
                    cObj.put("first_match", match.toString());
                } else if (firstUnsatisfiedIdx == -1) {
                    firstUnsatisfiedIdx = i;
                    firstUnsatisfiedClause = clause.toString();
                    firstUnsatisfiedRendered = renderTriplePattern(tp, bindings, claimIri);
                }
                it.close();
                clauseResults.add(cObj);
            }

            if (firstUnsatisfiedIdx >= 0) {
                cDiag.put("passed", true);
                cDiag.put("missing_subgoal_index", firstUnsatisfiedIdx);
                cDiag.put("missing_subgoal", firstUnsatisfiedClause);
                cDiag.put("missing_subgoal_resolved", firstUnsatisfiedRendered);
                cDiag.put("details", "LHS decomposition identified the first unsatisfied body clause via direct listStatements queries. This produces structured failure attribution by hand-coding what the Jena backward chain would not expose natively.");
            } else {
                cDiag.put("passed", false);
                cDiag.put("details", "All body clauses satisfied — the rule should have proved successfully. If property B reported failure, this indicates a discrepancy worth investigating.");
            }
        } catch (Throwable t) {
            cDiag.put("passed", false);
            cDiag.put("error_type", t.getClass().getName());
            cDiag.put("error_message", String.valueOf(t.getMessage()));
        }

        // ── Property D: weakener firing comparison ─────────────────────────
        ObjectNode propD = report.putObject("property_d");
        try {
            List<Firing> withOOSFirings = extractFirings(inf2);
            Set<Firing> baseSet = new HashSet<>(baselineFirings);
            Set<Firing> withSet = new HashSet<>(withOOSFirings);
            Set<Firing> only_in_baseline = new LinkedHashSet<>(baseSet);
            only_in_baseline.removeAll(withSet);
            Set<Firing> only_in_with = new LinkedHashSet<>(withSet);
            only_in_with.removeAll(baseSet);

            boolean dPassed = only_in_baseline.isEmpty() && only_in_with.isEmpty();
            propD.put("passed", dPassed);
            propD.put("baseline_count", baselineFirings.size());
            propD.put("with_oos_count", withOOSFirings.size());

            ArrayNode baseArr = propD.putArray("weakener_firings_baseline");
            for (Firing f : baselineFirings) baseArr.add(firingToJson(f));
            ArrayNode withArr = propD.putArray("weakener_firings_with_oos_rule");
            for (Firing f : withOOSFirings) withArr.add(firingToJson(f));

            ArrayNode diffOnlyBase = propD.putArray("only_in_baseline");
            for (Firing f : only_in_baseline) diffOnlyBase.add(firingToJson(f));
            ArrayNode diffOnlyWith = propD.putArray("only_in_with_oos");
            for (Firing f : only_in_with) diffOnlyWith.add(firingToJson(f));

            propD.put("details", dPassed
                ? "Forward weakener firings unchanged when OOS rule loaded alongside C3."
                : "Forward weakener firings DIFFER between baseline and hybrid runs — see diff arrays.");
        } catch (Throwable t) {
            propD.put("passed", false);
            propD.put("error_type", t.getClass().getName());
            propD.put("error_message", String.valueOf(t.getMessage()));
        }

        // ── Outcome classification ─────────────────────────────────────────
        boolean aPass = propA.get("passed").asBoolean(false);
        boolean bPass = propB.get("passed").asBoolean(false);
        boolean cNativePass = cNative.get("passed").asBoolean(false);
        boolean cDiagPass = cDiag.get("passed").asBoolean(false);
        boolean dPass = propD.get("passed").asBoolean(false);

        boolean overall = aPass && bPass && cNativePass && dPass;
        report.put("overall_pass", overall);

        String outcome;
        if (!aPass) {
            outcome = "3";
        } else if (aPass && bPass && cNativePass && dPass) {
            outcome = "1";
        } else {
            outcome = "2";
        }
        report.put("outcome_classification", outcome);
        report.put("disposition_input", dispositionInput(outcome, cDiagPass));
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Helpers
    // ────────────────────────────────────────────────────────────────────────

    private GenericRuleReasoner buildReasoner(List<Rule> rules, GenericRuleReasoner.RuleMode mode, boolean withDerivationLogging) {
        // Helper retained for potential future use; currently unused branch in baseline run.
        GenericRuleReasoner r = new GenericRuleReasoner(rules);
        r.setMode(mode);
        if (withDerivationLogging) r.setDerivationLogging(true);
        return r;
    }

    private void addModelFormAdequacyTyping(Model data) {
        Resource claim = data.createResource(claimIri);
        Resource modelFormAdequacyClaim = data.createResource(UOFA_NS + "ModelFormAdequacyClaim");
        data.add(claim, RDF.type, modelFormAdequacyClaim);
        // Note: we deliberately do NOT add hasSupportingEvidence here — its
        // absence is exactly what should cause the OOS backward proof to fail
        // and the LHS decomposition to identify the missing sub-goal.
    }

    private List<Firing> extractFirings(InfModel inf) {
        Resource weakenerType = inf.createResource(UOFA_NS + "WeakenerAnnotation");
        Property patternIdProp = inf.createProperty(UOFA_NS, "patternId");
        Property affectedProp = inf.createProperty(UOFA_NS, "affectedNode");
        Property hasWeakenerProp = inf.createProperty(UOFA_NS, "hasWeakener");

        List<Firing> firings = new ArrayList<>();
        StmtIterator it = inf.listStatements(null, RDF.type, weakenerType);
        while (it.hasNext()) {
            Resource ann = it.next().getSubject();
            String pid = stringValue(inf, ann, patternIdProp);
            String affected = iriValue(inf, ann, affectedProp);

            StmtIterator owners = inf.listStatements(null, hasWeakenerProp, ann);
            String owner = owners.hasNext() ? owners.next().getSubject().getURI() : "unknown";
            owners.close();

            firings.add(new Firing(pid, affected, owner));
        }
        it.close();
        // Canonical sort for deterministic output
        firings.sort(Comparator
            .comparing((Firing f) -> f.patternId)
            .thenComparing(f -> f.affectedNode)
            .thenComparing(f -> f.owner));
        // Deduplicate (hybrid mode can produce duplicate solutions per Plan agent note)
        LinkedHashSet<Firing> dedup = new LinkedHashSet<>(firings);
        return new ArrayList<>(dedup);
    }

    private ObjectNode firingToJson(Firing f) {
        ObjectNode n = json.createObjectNode();
        n.put("patternId", f.patternId);
        n.put("affectedNode", f.affectedNode);
        n.put("owner", f.owner);
        return n;
    }

    private String stringValue(Model m, Resource r, Property p) {
        Statement s = m.getProperty(r, p);
        return (s != null) ? s.getObject().toString() : "unknown";
    }

    private String iriValue(Model m, Resource r, Property p) {
        Statement s = m.getProperty(r, p);
        if (s != null && s.getObject().isResource()) {
            return s.getObject().asResource().getURI();
        }
        return (s != null) ? s.getObject().toString() : "unknown";
    }

    private Resource resolveResource(Model m, org.apache.jena.graph.Node node,
                                      Map<String, Resource> bindings, String claimDefault) {
        if (node.isVariable()) {
            String varName = node.getName();
            Resource bound = bindings.get(varName);
            if (bound != null) return bound;
            // Special-case: ?claim binds to the configured claim IRI
            if ("claim".equals(varName)) {
                Resource r = m.createResource(claimDefault);
                bindings.put(varName, r);
                return r;
            }
            return null; // unbound
        }
        if (node.isURI()) return m.createResource(node.getURI());
        return null;
    }

    private Property resolveProperty(Model m, org.apache.jena.graph.Node node) {
        if (node.isURI()) return m.createProperty(node.getURI());
        return null;
    }

    private RDFNode resolveObject(Model m, org.apache.jena.graph.Node node,
                                   Map<String, Resource> bindings) {
        if (node.isVariable()) {
            String varName = node.getName();
            Resource bound = bindings.get(varName);
            return bound; // null for unbound
        }
        if (node.isURI()) return m.createResource(node.getURI());
        if (node.isLiteral()) {
            return m.createTypedLiteral(node.getLiteralLexicalForm(),
                                         node.getLiteralDatatype());
        }
        return null;
    }

    private void captureBindings(TriplePattern tp, Statement match,
                                  Map<String, Resource> bindings) {
        if (tp.getSubject().isVariable() && match.getSubject().isResource()) {
            bindings.putIfAbsent(tp.getSubject().getName(), match.getSubject());
        }
        if (tp.getObject().isVariable() && match.getObject().isResource()) {
            bindings.putIfAbsent(tp.getObject().getName(), match.getObject().asResource());
        }
    }

    private String renderTriplePattern(TriplePattern tp, Map<String, Resource> bindings,
                                        String claimDefault) {
        return String.format("(%s %s %s)",
            renderNode(tp.getSubject(), bindings, claimDefault),
            renderNode(tp.getPredicate(), bindings, claimDefault),
            renderNode(tp.getObject(), bindings, claimDefault));
    }

    private String renderNode(org.apache.jena.graph.Node node,
                               Map<String, Resource> bindings, String claimDefault) {
        if (node.isVariable()) {
            String n = node.getName();
            // Jena variable getName() may or may not include the leading "?";
            // strip it if present so we don't render "??claim".
            String bare = n.startsWith("?") ? n.substring(1) : n;
            Resource b = bindings.get(n);
            if (b == null) b = bindings.get(bare);
            if (b != null) return "?" + bare + "=" + b;
            if ("claim".equals(bare)) return "?" + bare + "=" + claimDefault;
            return "?" + bare;
        }
        if (node.isURI()) return "<" + node.getURI() + ">";
        if (node.isLiteral()) return "\"" + node.getLiteralLexicalForm() + "\"";
        return node.toString();
    }

    private String dispositionInput(String outcome, boolean cDiagPass) {
        switch (outcome) {
            case "1":
                return "Substrate works; path one is engineering-feasible. Disposition decision pending separate session.";
            case "2":
                return "Hybrid mode mechanically works but Property C native fails or Property D regresses. Disposition: fall back to path two (SPARQL goal-driven queries in Python). "
                    + (cDiagPass
                        ? "LHS-decomposition diagnostic confirms structured failure attribution is implementable in path two."
                        : "LHS-decomposition diagnostic also failed — path two implementation will need its own design pass.");
            case "3":
                return "Hybrid mode does not load cleanly. Recovery: try simpler rule, try different Jena version, or fall back to path two.";
            default:
                return "Inconclusive.";
        }
    }

    private String stackToString(Throwable t) {
        StringWriter sw = new StringWriter();
        t.printStackTrace(new PrintWriter(sw));
        return sw.toString();
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Result containers
    // ────────────────────────────────────────────────────────────────────────

    static class Firing {
        final String patternId;
        final String affectedNode;
        final String owner;

        Firing(String patternId, String affectedNode, String owner) {
            this.patternId = patternId;
            this.affectedNode = affectedNode;
            this.owner = owner;
        }

        @Override
        public boolean equals(Object o) {
            if (!(o instanceof Firing)) return false;
            Firing f = (Firing) o;
            return Objects.equals(patternId, f.patternId)
                && Objects.equals(affectedNode, f.affectedNode)
                && Objects.equals(owner, f.owner);
        }

        @Override
        public int hashCode() {
            return Objects.hash(patternId, affectedNode, owner);
        }
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new OOSSubstrateTest()).execute(args);
        System.exit(exitCode);
    }
}
