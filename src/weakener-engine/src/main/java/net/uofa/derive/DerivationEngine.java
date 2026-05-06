package net.uofa.derive;

import net.uofa.JsonLdLoader;

import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * UofA Derivation Pre-Pass Engine — SPARQL CONSTRUCT execution against the
 * loaded JSON-LD data graph.
 *
 * v0.1 implementation per UofA_Derivation_PrePass_Spec_v0_1.md §2.3.1.
 *
 * Algorithm:
 *   1. Load JSON-LD package into a Jena Model (via shared JsonLdLoader).
 *   2. For each CONSTRUCT file, parse out individual CONSTRUCT clauses
 *      (a single SPARQL file may carry multiple CONSTRUCT blocks).
 *   3. Execute each CONSTRUCT in declaration order against the data graph.
 *      Triples derived by clause N are merged back into the data graph
 *      before clause N+1 executes — enables multi-stage derivations
 *      (e.g., compute _auditAge first, then derive _auditOverdue against
 *      the materialized _auditAge predicate).
 *   4. Write the FULL enriched graph (original + derived) to the output
 *      path as N-Triples format. Downstream engines (WeakenerEngine,
 *      OOSEngine) read this enriched file when derivations are enabled.
 *
 * Design notes:
 *   - Output format is N-Triples (Lang.NTRIPLES) rather than JSON-LD
 *     because N-Triples is unambiguous, requires no @context, and
 *     round-trips through Jena cleanly. WeakenerEngine and OOSEngine use
 *     RDFDataMgr.read() which detects format by extension; ensure the
 *     output file uses .nt extension.
 *   - Backward compatibility: this engine is opt-in. Packs without a
 *     `derivations` config see no execution and no output drift. The
 *     check.py orchestration only invokes this engine when the active
 *     pack declares derivations.enabled: true.
 *   - Cumulative derivation: triples derived by an earlier CONSTRUCT in
 *     the same file are visible to later CONSTRUCTs (Jena Model.add() is
 *     immediate; no separate transaction layer needed).
 */
@Command(
    name = "uofa-derivation-engine",
    mixinStandardHelpOptions = true,
    version = "0.1.0",
    description = "Derivation pre-pass — SPARQL CONSTRUCT against JSON-LD package."
)
public class DerivationEngine implements Callable<Integer> {

    @Option(names = "--package", required = true,
            description = "Path to the UofA evidence package JSON-LD")
    Path packagePath;

    @Option(names = "--constructs", required = true,
            description = "SPARQL CONSTRUCT file(s). May be repeated.")
    List<Path> constructPaths;

    @Option(names = "--context", required = true,
            description = "Path to JSON-LD context file (e.g. spec/context/v0.5.jsonld)")
    Path contextPath;

    @Option(names = "--output", required = true,
            description = "Output path for enriched N-Triples graph (suffix .nt)")
    Path outputPath;

    @Option(names = "--derived-only", description = "Write only derived triples, not the merged graph.")
    boolean derivedOnly;

    @Option(names = "--verbose", description = "Verbose diagnostic output to stderr.")
    boolean verbose;

    /**
     * Splits a SPARQL file containing one or more CONSTRUCT blocks into
     * individual queries. Preserves PREFIX declarations by prepending the
     * file's prefix block (lines starting with "PREFIX") to each CONSTRUCT.
     *
     * The simple split heuristic looks for lines starting with the
     * CONSTRUCT keyword (case-insensitive, optionally indented). Comments
     * are passed through. This is sufficient for the iso42001 derivations
     * file structure but assumes "well-formed" SPARQL with each CONSTRUCT
     * starting on its own line.
     */
    static List<String> splitConstructs(String fileContent) {
        // Extract PREFIX declarations to prepend to each split query.
        StringBuilder prefixes = new StringBuilder();
        for (String line : fileContent.split("\n", -1)) {
            String trimmed = line.trim();
            if (trimmed.toUpperCase().startsWith("PREFIX ")) {
                prefixes.append(line).append("\n");
            }
        }

        // Split file into CONSTRUCT-headed blocks.
        Pattern constructStart = Pattern.compile(
            "(?im)^\\s*CONSTRUCT\\b"
        );
        Matcher m = constructStart.matcher(fileContent);
        List<Integer> starts = new ArrayList<>();
        while (m.find()) {
            starts.add(m.start());
        }

        List<String> queries = new ArrayList<>();
        for (int i = 0; i < starts.size(); i++) {
            int start = starts.get(i);
            int end = (i + 1 < starts.size()) ? starts.get(i + 1) : fileContent.length();
            String body = fileContent.substring(start, end);
            queries.add(prefixes.toString() + body);
        }
        return queries;
    }

    @Override
    public Integer call() throws Exception {
        // 1. Load the JSON-LD package into a Jena Model.
        Model dataGraph = JsonLdLoader.load(packagePath, contextPath);
        long originalSize = dataGraph.size();
        if (verbose) {
            System.err.println("DerivationEngine: loaded " + originalSize + " triples from "
                + packagePath);
        }

        // 2. Track derived triples separately for --derived-only and reporting.
        Model derived = ModelFactory.createDefaultModel();
        int constructCount = 0;
        long totalDerived = 0;

        // 3. Execute each CONSTRUCT in declaration order; merge results.
        for (Path file : constructPaths) {
            String content = Files.readString(file);
            List<String> queries = splitConstructs(content);
            if (verbose) {
                System.err.println("DerivationEngine: " + queries.size()
                    + " CONSTRUCT(s) in " + file);
            }
            for (String queryText : queries) {
                Query query;
                try {
                    query = QueryFactory.create(queryText);
                } catch (Exception e) {
                    System.err.println("DerivationEngine: parse error in " + file
                        + " (CONSTRUCT #" + (constructCount + 1) + "): " + e.getMessage());
                    return 2;
                }
                if (!query.isConstructType()) {
                    System.err.println("DerivationEngine: non-CONSTRUCT query found in "
                        + file + " — only CONSTRUCT queries are supported.");
                    return 2;
                }
                try (QueryExecution qe = QueryExecutionFactory.create(query, dataGraph)) {
                    Model result = qe.execConstruct();
                    derived.add(result);
                    dataGraph.add(result);  // cumulative: visible to later CONSTRUCTs
                    totalDerived += result.size();
                    constructCount++;
                    if (verbose) {
                        System.err.println("  CONSTRUCT #" + constructCount
                            + " materialized " + result.size() + " triple(s)");
                    }
                }
            }
        }

        // 4. Write output.
        Model toWrite = derivedOnly ? derived : dataGraph;
        try (OutputStream out = Files.newOutputStream(outputPath)) {
            RDFDataMgr.write(out, toWrite, Lang.NTRIPLES);
        }

        if (verbose) {
            System.err.println("DerivationEngine: wrote " + toWrite.size()
                + " triples to " + outputPath
                + (derivedOnly ? " (derived only)" : " (merged)"));
            System.err.println("DerivationEngine: " + constructCount + " CONSTRUCT(s) executed; "
                + totalDerived + " triple(s) derived total.");
        }

        return 0;
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new DerivationEngine()).execute(args);
        System.exit(exitCode);
    }
}
