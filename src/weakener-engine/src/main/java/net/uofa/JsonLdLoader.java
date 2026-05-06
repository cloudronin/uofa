package net.uofa;

import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Shared JSON-LD loader for UofA evidence packages.
 *
 * Lifted from {@link WeakenerEngine} during T5a so the C3 weakener engine,
 * the OOS substrate test, and the production OOS engine all share one
 * implementation. Behaviour is otherwise unchanged from the original
 * inline loader at {@code WeakenerEngine.java:177}.
 *
 * The loader handles two shapes:
 *   1. Package's @context references an external URL; caller passes a local
 *      context file via {@code ctxPath}. The loader inlines the local
 *      context's @context object before parsing.
 *   2. ctxPath is null but the @context value is a relative path resolvable
 *      against the package's parent directory. The loader recurses with the
 *      resolved local path.
 */
public final class JsonLdLoader {

    private JsonLdLoader() {}

    /**
     * Load a UofA JSON-LD package into a Jena {@link Model}.
     *
     * @param jsonldPath path to the package JSON-LD file
     * @param ctxPath optional path to the local context file. When non-null
     *                and existing, its @context object is inlined into the
     *                package text before parsing. When null, the loader
     *                attempts to resolve the package's @context reference
     *                against the package's parent directory.
     * @return parsed RDF model
     * @throws Exception on file-IO or parse errors
     */
    public static Model load(Path jsonldPath, Path ctxPath) throws Exception {
        String content = Files.readString(jsonldPath);

        if (ctxPath != null && Files.exists(ctxPath)) {
            String ctxContent = Files.readString(ctxPath);
            int ctxStart = ctxContent.indexOf("{", ctxContent.indexOf("@context"));
            int depth = 0;
            int ctxEnd = ctxStart;
            for (int i = ctxStart; i < ctxContent.length(); i++) {
                if (ctxContent.charAt(i) == '{') depth++;
                if (ctxContent.charAt(i) == '}') depth--;
                if (depth == 0) { ctxEnd = i + 1; break; }
            }
            String ctxObject = ctxContent.substring(ctxStart, ctxEnd);
            content = content.replaceFirst(
                "\"@context\"\\s*:\\s*\"[^\"]+\"",
                "\"@context\": " + ctxObject.replace("$", "\\$")
            );
        } else {
            // Try resolving context relative to the input file
            int idx = content.indexOf("\"@context\"");
            if (idx >= 0) {
                char firstNonSpace = ' ';
                for (int i = idx + 10; i < content.length(); i++) {
                    char c = content.charAt(i);
                    if (c == ':') continue;
                    if (!Character.isWhitespace(c)) { firstNonSpace = c; break; }
                }
                if (firstNonSpace == '"') {
                    int strStart = content.indexOf("\"", idx + 11) + 1;
                    int strEnd = content.indexOf("\"", strStart);
                    String ref = content.substring(strStart, strEnd);
                    Path resolved = jsonldPath.getParent().resolve(ref);
                    if (Files.exists(resolved)) {
                        System.err.println("  Resolved @context: " + ref + " → " + resolved);
                        return load(jsonldPath, resolved);
                    }
                }
            }
        }

        Model model = ModelFactory.createDefaultModel();
        try (InputStream is = new ByteArrayInputStream(content.getBytes())) {
            RDFDataMgr.read(model, is, Lang.JSONLD);
        }
        return model;
    }
}
