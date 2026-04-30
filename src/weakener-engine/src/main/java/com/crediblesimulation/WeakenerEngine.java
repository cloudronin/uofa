package com.crediblesimulation;

import org.apache.jena.rdf.model.*;
import org.apache.jena.reasoner.rulesys.GenericRuleReasoner;
import org.apache.jena.reasoner.rulesys.Rule;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.riot.Lang;
import org.apache.jena.vocabulary.RDF;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.Callable;

/**
 * UofA Weakener Detection Engine
 *
 * Loads a UofA JSON-LD evidence package, applies forward-chaining Jena rules
 * from the weakener pattern catalog, and outputs detected WeakenerAnnotation
 * triples as JSON-LD, Turtle, or a human-readable summary.
 *
 * Usage:
 *   java -jar uofa-weakener-engine.jar input.jsonld
 *   java -jar uofa-weakener-engine.jar input.jsonld --rules custom.rules
 *   java -jar uofa-weakener-engine.jar input.jsonld --context uofa_v0_3.jsonld
 *   java -jar uofa-weakener-engine.jar input.jsonld --format turtle
 *   java -jar uofa-weakener-engine.jar input.jsonld --summary
 */
@Command(
    name = "uofa-weakener-engine",
    mixinStandardHelpOptions = true,
    version = "0.1.0",
    description = "Detect credibility gaps in UofA evidence packages using Jena rule inference."
)
public class WeakenerEngine implements Callable<Integer> {

    private static final String UOFA_NS = "https://uofa.net/vocab#";
    private static final String PROV_NS = "http://www.w3.org/ns/prov#";

    @Parameters(index = "0", description = "Path to the UofA JSON-LD file")
    private Path inputFile;

    @Option(names = {"--rules", "-r"},
            description = "Path to .rules file (default: bundled uofa_weakener.rules)",
            defaultValue = "")
    private String rulesPath;

    @Option(names = {"--context", "-c"},
            description = "Path to external JSON-LD context file for resolving @context references")
    private Path contextFile;

    @Option(names = {"--format", "-f"},
            description = "Output format: summary, turtle, ntriples, jsonld (default: summary)",
            defaultValue = "summary")
    private String outputFormat;

    @Option(names = {"--output", "-o"},
            description = "Output file path (default: stdout)")
    private Path outputFile;

    @Option(names = {"--trace"},
            description = "Enable rule execution tracing")
    private boolean trace;

    @Option(names = {"--derivations"},
            description = "Enable derivation logging (shows WHY each weakener fired)")
    private boolean derivations;

    @Override
    public Integer call() throws Exception {

        // ── 1. Load the data graph ────────────────────────────────────
        System.err.println("Loading: " + inputFile);
        Model data = loadJsonLdWithContext(inputFile, contextFile);
        long rawTriples = data.size();
        System.err.println("  Data graph: " + rawTriples + " triples");

        // ── 2. Load rules ─────────────────────────────────────────────
        List<Rule> rules;
        if (rulesPath != null && !rulesPath.isEmpty()) {
            System.err.println("Loading rules: " + rulesPath);
            rules = Rule.rulesFromURL("file:" + rulesPath);
        } else {
            System.err.println("Loading bundled rules: uofa_weakener.rules");
            try (InputStream is = getClass().getResourceAsStream("/uofa_weakener.rules")) {
                if (is == null) {
                    System.err.println("ERROR: Bundled rules not found on classpath.");
                    return 1;
                }
                BufferedReader br = new BufferedReader(new InputStreamReader(is));
                rules = Rule.parseRules(Rule.rulesParserFromReader(br));
            }
        }
        System.err.println("  Loaded " + rules.size() + " rules");

        // ── 3. Create reasoner and inference model ────────────────────
        GenericRuleReasoner reasoner = new GenericRuleReasoner(rules);
        reasoner.setMode(GenericRuleReasoner.FORWARD_RETE);

        if (trace) {        
            reasoner.setParameter(org.apache.jena.vocabulary.ReasonerVocabulary.PROPtraceOn,Boolean.TRUE);
        }
        if (derivations) {
            reasoner.setDerivationLogging(true);
        }

        InfModel inf = ModelFactory.createInfModel(reasoner, data);

        // Force inference to run
        inf.prepare();

        long totalTriples = inf.size();
        long inferred = totalTriples - rawTriples;
        System.err.println("  Inferred " + inferred + " new triples (" + totalTriples + " total)");

        // ── 4. Extract WeakenerAnnotation results ─────────────────────
        Resource weakenerType = inf.createResource(UOFA_NS + "WeakenerAnnotation");
        Property patternIdProp = inf.createProperty(UOFA_NS, "patternId");
        Property severityProp = inf.createProperty(UOFA_NS, "severity");
        Property affectedProp = inf.createProperty(UOFA_NS, "affectedNode");
        Property hasWeakenerProp = inf.createProperty(UOFA_NS, "hasWeakener");

        // Collect all WeakenerAnnotation instances
        List<WeakenerResult> results = new ArrayList<>();
        StmtIterator it = inf.listStatements(null, RDF.type, weakenerType);
        while (it.hasNext()) {
            Resource ann = it.next().getSubject();
            String pid = getStringValue(inf, ann, patternIdProp);
            String sev = getStringValue(inf, ann, severityProp);
            String affected = getIriValue(inf, ann, affectedProp);

            // Find which UofA this weakener belongs to
            StmtIterator owners = inf.listStatements(null, hasWeakenerProp, ann);
            String owner = owners.hasNext() ? owners.next().getSubject().getURI() : "unknown";

            results.add(new WeakenerResult(pid, sev, affected, owner, ann.toString()));
        }

        // Sort by pattern ID for deterministic output
        results.sort(Comparator.comparing(r -> r.patternId));

        // ── 5. Output ─────────────────────────────────────────────────
        PrintStream out = (outputFile != null)
            ? new PrintStream(new FileOutputStream(outputFile.toFile()))
            : System.out;

        switch (outputFormat.toLowerCase()) {
            case "summary":
                printSummary(out, results, inputFile.getFileName().toString(), derivations ? inf : null);
                break;
            case "turtle":
                printDeductionsAsTurtle(inf, data, out);
                break;
            case "ntriples":
                printDeductionsAsNTriples(inf, data, out);
                break;
            case "jsonld":
                printDeductionsAsJsonLd(inf, data, out);
                break;
            default:
                System.err.println("Unknown format: " + outputFormat);
                return 1;
        }

        if (outputFile != null) out.close();
        return 0;
    }

    // ── JSON-LD loading with external context resolution ──────────────

    private Model loadJsonLdWithContext(Path jsonldPath, Path ctxPath) throws Exception {
        // Read the JSON-LD file
        String content = Files.readString(jsonldPath);

        // If context file is provided, inject it inline
        if (ctxPath != null && Files.exists(ctxPath)) {
            String ctxContent = Files.readString(ctxPath);
            // Extract the @context object from the context file
            // Simple approach: replace the string reference with the file contents
            // The context file has {"@context": {...}} structure
            int ctxStart = ctxContent.indexOf("{", ctxContent.indexOf("@context"));
            int depth = 0;
            int ctxEnd = ctxStart;
            for (int i = ctxStart; i < ctxContent.length(); i++) {
                if (ctxContent.charAt(i) == '{') depth++;
                if (ctxContent.charAt(i) == '}') depth--;
                if (depth == 0) { ctxEnd = i + 1; break; }
            }
            String ctxObject = ctxContent.substring(ctxStart, ctxEnd);

            // Replace the @context string reference with the inline object
            content = content.replaceFirst(
                "\"@context\"\\s*:\\s*\"[^\"]+\"",
                "\"@context\": " + ctxObject
            );
        } else {
            // Try resolving context relative to the input file
            // Parse the @context value from the JSON
            int idx = content.indexOf("\"@context\"");
            if (idx >= 0) {
                int valStart = content.indexOf("\"", idx + 10);
                // Check if it's a string (external ref) or object (inline)
                char firstNonSpace = ' ';
                for (int i = idx + 10; i < content.length(); i++) {
                    char c = content.charAt(i);
                    if (c == ':') continue;
                    if (!Character.isWhitespace(c)) { firstNonSpace = c; break; }
                }
                if (firstNonSpace == '"') {
                    // It's a string reference — try to find the file
                    int strStart = content.indexOf("\"", idx + 11) + 1;
                    int strEnd = content.indexOf("\"", strStart);
                    String ref = content.substring(strStart, strEnd);
                    Path resolved = jsonldPath.getParent().resolve(ref);
                    if (Files.exists(resolved)) {
                        System.err.println("  Resolved @context: " + ref + " → " + resolved);
                        return loadJsonLdWithContext(jsonldPath, resolved);
                    }
                }
            }
        }

        // Parse the (potentially modified) JSON-LD
        Model model = ModelFactory.createDefaultModel();
        try (InputStream is = new ByteArrayInputStream(content.getBytes())) {
            RDFDataMgr.read(model, is, Lang.JSONLD);
        }
        return model;
    }

    // ── Output formatters ─────────────────────────────────────────────

    private void printSummary(PrintStream out, List<WeakenerResult> results,
                              String filename, InfModel infForDerivations) {
        out.println("══════════════════════════════════════════════════════════════");
        out.println("  UofA Weakener Detection Report");
        out.println("  Input: " + filename);
        out.println("══════════════════════════════════════════════════════════════");
        out.println();

        // Count by severity
        Map<String, Integer> bySeverity = new LinkedHashMap<>();
        bySeverity.put("Critical", 0);
        bySeverity.put("High", 0);
        bySeverity.put("Medium", 0);
        bySeverity.put("Low", 0);

        Map<String, List<WeakenerResult>> byPattern = new LinkedHashMap<>();

        for (WeakenerResult r : results) {
            bySeverity.merge(r.severity, 1, Integer::sum);
            byPattern.computeIfAbsent(r.patternId, k -> new ArrayList<>()).add(r);
        }

        out.println("  SUMMARY: " + results.size() + " weakener(s) detected");
        out.println("  ─────────────────────────────────────────────────");
        for (var e : bySeverity.entrySet()) {
            if (e.getValue() > 0) {
                out.printf("    %-10s %d%n", e.getKey() + ":", e.getValue());
            }
        }
        out.println();

        // Detail by pattern
        for (var e : byPattern.entrySet()) {
            String pid = e.getKey();
            List<WeakenerResult> hits = e.getValue();
            String sev = hits.get(0).severity;
            boolean isCompound = pid.startsWith("COMPOUND");

            out.println("  " + (isCompound ? "⚡" : "⚠") + " " + pid + " [" + sev + "] — " + hits.size() + " hit(s)");
            for (WeakenerResult r : hits) {
                String shortAffected = r.affectedNode;
                if (shortAffected != null && shortAffected.contains("/")) {
                    shortAffected = shortAffected.substring(shortAffected.lastIndexOf("/") + 1);
                }
                out.println("      → affected: " + shortAffected);
            }
            out.println();
        }

        // Compound rules summary
        long compoundCount = results.stream()
            .filter(r -> r.patternId.startsWith("COMPOUND"))
            .count();
        if (compoundCount > 0) {
            out.println("  ─────────────────────────────────────────────────");
            out.println("  ⚡ " + compoundCount + " compound inference(s) — these require");
            out.println("    chained rule reasoning and cannot be detected");
            out.println("    by standalone SPARQL queries.");
        }

        out.println();
        out.println("══════════════════════════════════════════════════════════════");
    }

    private void printDeductionsAsTurtle(InfModel inf, Model raw, PrintStream out) {
        Model deductions = inf.getDeductionsModel();
        if (deductions != null) {
            deductions.setNsPrefix("uofa", UOFA_NS);
            deductions.setNsPrefix("prov", PROV_NS);
            RDFDataMgr.write(out, deductions, Lang.TURTLE);
        }
    }

    private void printDeductionsAsNTriples(InfModel inf, Model raw, PrintStream out) {
        Model deductions = inf.getDeductionsModel();
        if (deductions != null) {
            RDFDataMgr.write(out, deductions, Lang.NTRIPLES);
        }
    }

    private void printDeductionsAsJsonLd(InfModel inf, Model raw, PrintStream out) {
        Model deductions = inf.getDeductionsModel();
        if (deductions != null) {
            RDFDataMgr.write(out, deductions, Lang.JSONLD);
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────

    private String getStringValue(Model m, Resource r, Property p) {
        Statement s = m.getProperty(r, p);
        return (s != null) ? s.getObject().toString() : "unknown";
    }

    private String getIriValue(Model m, Resource r, Property p) {
        Statement s = m.getProperty(r, p);
        if (s != null && s.getObject().isResource()) {
            return s.getObject().asResource().getURI();
        }
        return (s != null) ? s.getObject().toString() : "unknown";
    }

    // ── Result container ─────────────────────────────────────────────

    static class WeakenerResult {
        final String patternId;
        final String severity;
        final String affectedNode;
        final String ownerUofA;
        final String annotationId;

        WeakenerResult(String pid, String sev, String affected, String owner, String annId) {
            this.patternId = pid;
            this.severity = sev;
            this.affectedNode = affected;
            this.ownerUofA = owner;
            this.annotationId = annId;
        }
    }

    // ── Entry point ──────────────────────────────────────────────────

    public static void main(String[] args) {
        int exitCode = new CommandLine(new WeakenerEngine()).execute(args);
        System.exit(exitCode);
    }
}
