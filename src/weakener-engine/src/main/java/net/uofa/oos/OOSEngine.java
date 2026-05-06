package net.uofa.oos;

import net.uofa.JsonLdLoader;

import org.apache.jena.graph.Node;
import org.apache.jena.graph.NodeFactory;
import org.apache.jena.graph.Triple;
import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.reasoner.TriplePattern;
import org.apache.jena.reasoner.rulesys.ClauseEntry;
import org.apache.jena.reasoner.rulesys.Rule;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * UofA Productive-OOS Engine — path-two LHS-decomposition over Jena rule body.
 *
 * v0.1 implementation per UofA_OOS_Productionization_Spec_v0_3.md §2.1 and
 * src/uofa_cli/oos/SCHEMA_NOTES.md §8.
 *
 * Algorithm:
 *   1. Load JSON-LD package into a Jena Model (via shared JsonLdLoader).
 *   2. Load Jena backward rules from one or more rule files.
 *   3. Parse each rule's preceding `# key: value` comment block to extract
 *      metadata (defeater_type, missing_evidence, sufficiency_starts_at).
 *   4. For each rule:
 *      a. Split body into discriminator (clauses 1..sufficiencyStartsAt-1)
 *         and sufficiency (clauses sufficiencyStartsAt..end).
 *      b. SPARQL SELECT over discriminator clauses → candidate bindings
 *         (each binding identifies a UofA + claim that the rule applies to).
 *         Empty result → silently skip rule (doesn't apply to this package).
 *      c. For each candidate binding, walk sufficiency clauses sequentially
 *         with binding propagation. The first clause whose substituted
 *         pattern returns zero matches against the data graph is the
 *         missing sub-goal; emit one OOSResult per failure.
 *      d. If all sufficiency clauses succeed for a binding → no firing
 *         (proof complete = bundle is sufficient for that claim).
 *   5. Serialize results as a JSON array per the v0.1 evidence_gap schema
 *      (2 required fields + path_two_metadata).
 */
@Command(
    name = "uofa-oos-engine",
    mixinStandardHelpOptions = true,
    version = "0.1.0",
    description = "OOS bundle-sufficiency engine — path-two LHS decomposition over Jena rule body."
)
public class OOSEngine implements Callable<Integer> {

    static final String VERDICT = "OUT-OF-SCOPE";

    @Option(names = "--package", required = true,
            description = "Path to the UofA evidence package JSON-LD")
    Path packagePath;

    @Option(names = "--rules", required = true,
            description = "Path to OOS rules file (Jena backward syntax). May be repeated.")
    List<Path> rulesPaths;

    @Option(names = "--context", required = true,
            description = "Path to JSON-LD context file (e.g. spec/context/v0.5.jsonld)")
    Path contextPath;

    @Option(names = "--output", required = true,
            description = "Output path for JSON results array")
    Path outputPath;

    @Option(names = "--verbose", description = "Verbose diagnostic output to stderr")
    boolean verbose;

    private final ObjectMapper json =
        new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);

    @Override
    public Integer call() throws Exception {
        Model data = JsonLdLoader.load(packagePath, contextPath);
        if (verbose) {
            System.err.println("Loaded " + data.size() + " triples from " + packagePath);
        }

        List<Rule> allRules = new ArrayList<>();
        Map<String, RuleMetadata> allMetadata = new LinkedHashMap<>();
        for (Path rp : rulesPaths) {
            List<Rule> parsed = Rule.rulesFromURL("file:" + rp.toAbsolutePath());
            allRules.addAll(parsed);
            allMetadata.putAll(CommentBlockParser.parse(rp));
            if (verbose) {
                System.err.println("Loaded " + parsed.size() + " rule(s) from " + rp);
            }
        }

        List<OOSResult> results = new ArrayList<>();
        for (Rule rule : allRules) {
            RuleMetadata meta = allMetadata.get(rule.getName());
            if (meta == null) {
                System.err.println("WARNING: rule " + rule.getName()
                    + " has no comment-block metadata; skipping.");
                continue;
            }
            try {
                results.addAll(evaluateRule(rule, meta, data));
            } catch (Exception e) {
                System.err.println("ERROR evaluating rule " + rule.getName()
                    + ": " + e.getMessage());
                if (verbose) e.printStackTrace(System.err);
            }
        }

        writeResults(results);
        if (verbose) {
            System.err.println("Wrote " + results.size() + " OOS result(s) to " + outputPath);
        }
        return 0;
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Rule evaluation
    // ────────────────────────────────────────────────────────────────────────

    static List<OOSResult> evaluateRule(Rule rule, RuleMetadata meta, Model data) {
        ClauseEntry[] body = rule.getBody();
        int sufStart = meta.sufficiencyStartsAt - 1;  // 1-based comment → 0-based array
        if (sufStart < 1 || sufStart >= body.length) {
            throw new IllegalArgumentException(
                "Invalid sufficiency_starts_at=" + meta.sufficiencyStartsAt
                + " for rule '" + rule.getName() + "' with " + body.length
                + " body clauses (must be in [2.." + body.length + "])");
        }
        ClauseEntry[] discriminator = Arrays.copyOfRange(body, 0, sufStart);
        ClauseEntry[] sufficiency = Arrays.copyOfRange(body, sufStart, body.length);

        List<Map<String, Node>> candidates = sparqlSelectBindings(discriminator, data);
        if (candidates.isEmpty()) return Collections.emptyList();

        List<OOSResult> firings = new ArrayList<>();
        for (Map<String, Node> binding : candidates) {
            FailureEvidence failure = walkSufficiency(sufficiency, binding, data);
            if (failure != null) {
                firings.add(new OOSResult(rule.getName(), meta, binding, failure));
            }
        }
        return firings;
    }

    /**
     * Walk sufficiency clauses sequentially. Returns the first clause that
     * fails (no matching triples in the data graph given current bindings),
     * or null if all clauses succeed (proof complete).
     */
    static FailureEvidence walkSufficiency(
            ClauseEntry[] sufficiency,
            Map<String, Node> seedBindings,
            Model data) {
        Map<String, Node> bindings = new HashMap<>(seedBindings);
        for (ClauseEntry ce : sufficiency) {
            if (!(ce instanceof TriplePattern)) {
                // Functor / builtin clauses are not supported in v0.1.
                throw new IllegalStateException(
                    "Non-TriplePattern clause in sufficiency body: " + ce);
            }
            TriplePattern tp = (TriplePattern) ce;
            Node s = resolve(tp.getSubject(), bindings);
            Node p = resolve(tp.getPredicate(), bindings);
            Node o = resolve(tp.getObject(), bindings);

            // Find any matching triple in the data graph.
            // Wildcards (Node.ANY) for unbound variables.
            Node sQ = s.isVariable() ? Node.ANY : s;
            Node pQ = p.isVariable() ? Node.ANY : p;
            Node oQ = o.isVariable() ? Node.ANY : o;

            org.apache.jena.util.iterator.ExtendedIterator<Triple> it =
                data.getGraph().find(sQ, pQ, oQ);
            try {
                if (!it.hasNext()) {
                    return new FailureEvidence(tp, bindings);
                }
                Triple match = it.next();
                if (s.isVariable()) bindings.putIfAbsent(varName(tp.getSubject()), match.getSubject());
                if (o.isVariable()) bindings.putIfAbsent(varName(tp.getObject()), match.getObject());
            } finally {
                it.close();
            }
        }
        return null;  // all sufficiency clauses satisfied
    }

    private static Node resolve(Node n, Map<String, Node> bindings) {
        if (n.isVariable()) {
            Node bound = bindings.get(varName(n));
            return bound != null ? bound : n;
        }
        return n;
    }

    private static String varName(Node n) {
        // Jena's Node_Variable.getName() may include the "?" prefix in some
        // versions / construction paths; strip defensively so we always work
        // with the bare name (matches the SPARQL ResultSet variable names).
        String name = n.getName();
        return name.startsWith("?") ? name.substring(1) : name;
    }

    // ────────────────────────────────────────────────────────────────────────
    //  SPARQL helpers (discriminator phase)
    // ────────────────────────────────────────────────────────────────────────

    /**
     * SPARQL SELECT * over a chain of TriplePattern clauses. Returns one
     * Map per result row, mapping variable name → bound Node.
     */
    static List<Map<String, Node>> sparqlSelectBindings(
            ClauseEntry[] clauses, Model data) {
        StringBuilder sparql = new StringBuilder("SELECT * WHERE {\n");
        for (ClauseEntry ce : clauses) {
            if (!(ce instanceof TriplePattern)) {
                throw new IllegalStateException(
                    "Non-TriplePattern clause in discriminator body: " + ce);
            }
            TriplePattern tp = (TriplePattern) ce;
            sparql.append("  ")
                  .append(nodeToSparql(tp.getSubject())).append(' ')
                  .append(nodeToSparql(tp.getPredicate())).append(' ')
                  .append(nodeToSparql(tp.getObject())).append(" .\n");
        }
        sparql.append("}");
        Query query = QueryFactory.create(sparql.toString());

        List<Map<String, Node>> rows = new ArrayList<>();
        try (QueryExecution qe = QueryExecutionFactory.create(query, data)) {
            ResultSet rs = qe.execSelect();
            List<String> vars = rs.getResultVars();
            while (rs.hasNext()) {
                QuerySolution sol = rs.next();
                Map<String, Node> row = new LinkedHashMap<>();
                for (String v : vars) {
                    RDFNode n = sol.get(v);
                    if (n != null) row.put(v, n.asNode());
                }
                rows.add(row);
            }
        }
        return rows;
    }

    static String nodeToSparql(Node n) {
        if (n.isVariable()) return "?" + varName(n);
        if (n.isURI()) return "<" + n.getURI() + ">";
        if (n.isLiteral()) {
            String lex = n.getLiteralLexicalForm()
                .replace("\\", "\\\\")
                .replace("\"", "\\\"");
            String dt = n.getLiteralDatatypeURI();
            if (dt != null && !dt.isEmpty()
                    && !"http://www.w3.org/2001/XMLSchema#string".equals(dt)) {
                return "\"" + lex + "\"^^<" + dt + ">";
            }
            return "\"" + lex + "\"";
        }
        if (n.isBlank()) return "_:" + n.getBlankNodeLabel();
        return n.toString();
    }

    // ────────────────────────────────────────────────────────────────────────
    //  JSON output
    // ────────────────────────────────────────────────────────────────────────

    void writeResults(List<OOSResult> results) throws Exception {
        ArrayNode arr = json.createArrayNode();
        for (OOSResult r : results) arr.add(toJson(r));
        Files.writeString(outputPath, json.writeValueAsString(arr) + "\n");
    }

    ObjectNode toJson(OOSResult r) {
        ObjectNode top = json.createObjectNode();
        top.put("rule_name", r.ruleName);
        top.put("verdict", VERDICT);

        // claim_bindings: include only URI/literal bindings. Blank-node
        // bindings (e.g. ?prov pointing at a JSON-LD blank node) are internal
        // discriminator-chain artifacts, get fresh IRIs per Jena parse, and
        // would make the output non-deterministic.
        ObjectNode bindings = top.putObject("claim_bindings");
        for (Map.Entry<String, Node> e : r.binding.entrySet()) {
            Node v = e.getValue();
            if (v.isBlank()) continue;
            bindings.put(e.getKey(), nodeAsString(v));
        }

        top.put("missing_subgoal",
            renderTriplePattern(r.failure.failingClause, r.failure.bindings));

        ObjectNode gap = top.putObject("evidence_gap");
        gap.put("missing_evidence_type", r.metadata.missingEvidence);
        gap.put("would_support_defeater_evaluation", r.metadata.defeaterType);

        ObjectNode meta = gap.putObject("path_two_metadata");
        Node claimNode = r.binding.get("claim");
        meta.put("claim_under_evaluation",
            claimNode != null ? nodeAsString(claimNode) : "(unbound)");
        meta.put("failed_subgoal_clause",
            renderTriplePattern(r.failure.failingClause, r.failure.bindings));
        meta.put("bundle_check_rule_name", r.ruleName);
        return top;
    }

    static String renderTriplePattern(TriplePattern tp, Map<String, Node> bindings) {
        return "(" + renderNode(tp.getSubject(), bindings) + " "
            + renderNode(tp.getPredicate(), bindings) + " "
            + renderNode(tp.getObject(), bindings) + ")";
    }

    static String renderNode(Node n, Map<String, Node> bindings) {
        if (n.isVariable()) {
            String bare = varName(n);
            Node bound = bindings.get(bare);
            if (bound != null) return "?" + bare + "=" + nodeAsString(bound);
            return "?" + bare;
        }
        return nodeAsString(n);
    }

    static String nodeAsString(Node n) {
        if (n.isURI()) return "<" + n.getURI() + ">";
        if (n.isLiteral()) {
            String lex = n.getLiteralLexicalForm();
            String dt = n.getLiteralDatatypeURI();
            if (dt != null && !dt.isEmpty()
                    && !"http://www.w3.org/2001/XMLSchema#string".equals(dt)) {
                return "\"" + lex + "\"^^<" + dt + ">";
            }
            return "\"" + lex + "\"";
        }
        if (n.isBlank()) return "_:" + n.getBlankNodeLabel();
        return n.toString();
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Data classes
    // ────────────────────────────────────────────────────────────────────────

    /** Comment-block metadata for one rule. */
    static final class RuleMetadata {
        final String ruleName;
        final String calibrationTarget;
        final String defeaterType;
        final String missingEvidence;
        final int sufficiencyStartsAt;

        RuleMetadata(String ruleName, String calibrationTarget,
                     String defeaterType, String missingEvidence,
                     int sufficiencyStartsAt) {
            this.ruleName = ruleName;
            this.calibrationTarget = calibrationTarget;
            this.defeaterType = defeaterType;
            this.missingEvidence = missingEvidence;
            this.sufficiencyStartsAt = sufficiencyStartsAt;
        }
    }

    /** A clause that failed during sufficiency-walk, plus the bindings at
     *  the point of failure (used to render the resolved missing sub-goal). */
    static final class FailureEvidence {
        final TriplePattern failingClause;
        final Map<String, Node> bindings;

        FailureEvidence(TriplePattern failingClause, Map<String, Node> bindings) {
            this.failingClause = failingClause;
            this.bindings = new LinkedHashMap<>(bindings);
        }
    }

    /** One OOS verdict — a rule that fired against a particular binding. */
    static final class OOSResult {
        final String ruleName;
        final RuleMetadata metadata;
        final Map<String, Node> binding;
        final FailureEvidence failure;

        OOSResult(String ruleName, RuleMetadata metadata,
                  Map<String, Node> binding, FailureEvidence failure) {
            this.ruleName = ruleName;
            this.metadata = metadata;
            this.binding = new LinkedHashMap<>(binding);
            this.failure = failure;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Comment-block parser
    // ────────────────────────────────────────────────────────────────────────

    static final class CommentBlockParser {
        private static final Pattern KV_LINE =
            Pattern.compile("^#\\s*(\\w+)\\s*:\\s*(.+?)\\s*$");
        private static final Pattern RULE_START =
            Pattern.compile("^\\[\\s*(\\w+)\\s*:");
        private static final Pattern PREFIX_LINE =
            Pattern.compile("^\\s*@(prefix|base)\\b");
        private static final Pattern COMMENT_LINE =
            Pattern.compile("^\\s*#");

        static Map<String, RuleMetadata> parse(Path rulesPath) throws Exception {
            String content = Files.readString(rulesPath);
            Map<String, RuleMetadata> result = new LinkedHashMap<>();
            Map<String, String> currentBlock = new LinkedHashMap<>();

            for (String rawLine : content.split("\n")) {
                String line = rawLine.trim();
                Matcher kv = KV_LINE.matcher(rawLine);
                Matcher rs = RULE_START.matcher(line);
                if (kv.matches()) {
                    currentBlock.put(kv.group(1), kv.group(2));
                } else if (rs.find()) {
                    String ruleName = rs.group(1);
                    if (!currentBlock.isEmpty()) {
                        result.put(ruleName, fromMap(ruleName, currentBlock));
                        currentBlock.clear();
                    }
                } else if (line.isEmpty() || COMMENT_LINE.matcher(line).find()) {
                    // passive: blank lines and non-kv comments don't reset
                } else if (PREFIX_LINE.matcher(line).find()) {
                    currentBlock.clear();
                }
                // any other line (rule body content) we ignore
            }
            return result;
        }

        static RuleMetadata fromMap(String ruleName, Map<String, String> kv) {
            String calTarget = kv.getOrDefault("calibration_target", "");
            String defeater = kv.getOrDefault("defeater_type", "");
            String missing = kv.getOrDefault("missing_evidence", "");
            String sufStartStr = kv.get("sufficiency_starts_at");
            if (sufStartStr == null) {
                throw new IllegalArgumentException(
                    "Rule '" + ruleName + "' missing required comment key "
                    + "`sufficiency_starts_at`");
            }
            int sufStart;
            try {
                sufStart = Integer.parseInt(sufStartStr.trim());
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException(
                    "Rule '" + ruleName + "' has non-integer sufficiency_starts_at='"
                    + sufStartStr + "'");
            }
            // Optional sanity: bundle_check_rule_name (when present) matches rule name
            String declaredName = kv.get("bundle_check_rule_name");
            if (declaredName != null && !declaredName.equals(ruleName)) {
                throw new IllegalArgumentException(
                    "Rule '" + ruleName + "' has comment bundle_check_rule_name='"
                    + declaredName + "' which does not match the rule's [name:] anchor");
            }
            return new RuleMetadata(ruleName, calTarget, defeater, missing, sufStart);
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    //  Entry point
    // ────────────────────────────────────────────────────────────────────────

    public static void main(String[] args) {
        int exitCode = new CommandLine(new OOSEngine()).execute(args);
        System.exit(exitCode);
    }
}
