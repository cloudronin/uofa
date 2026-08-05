// The vocabulary, read from the CLI rather than parsed here.
//
// This replaced vocab-extract.mjs, which parsed the same Turtle with regexes.
// Two readers of one source drift, and the regex one was the fragile half: it
// had to cut each property shape at a line that is only a closing bracket,
// because stopping at the first "]" truncated inside uofa:hash's [a-f0-9]
// character class and silently swallowed both the pattern and the message. It
// also required ';' or '.' immediately after `a rdf:Property`, so the idiomatic
// way to mark a term deprecated would have dropped it from the site without
// erroring. `uofa vocab --site` reads the same files with rdflib and has
// neither failure mode.
//
// `usage` still comes from this side. It is counted by the instance-corpus walk
// the identifier pages already run, and duplicating that in Python would
// recreate exactly the second reader this change removes.

import { execFileSync } from 'node:child_process';

export const NAMESPACES = [
  { key: 'core', iri: 'https://uofa.net/vocab#', path: 'vocab', label: 'Core' },
  { key: 'aims', iri: 'https://uofa.net/vocab/aims#', path: 'vocab/aims', label: 'ISO 42001 (AIMS)' },
  { key: 'surrogate', iri: 'https://uofa.net/vocab/surrogate#', path: 'vocab/surrogate', label: 'Surrogate' },
];

/**
 * Every term, grouped by namespace, with usage counts merged in.
 *
 * Throws rather than degrading: a site built without the vocabulary would be
 * missing several hundred addressable terms and would look like it had simply
 * never had them.
 */
export function buildVocabulary(repoRoot, usage = {}) {
  let raw;
  try {
    raw = execFileSync('uofa', ['vocab', '--site'], {
      cwd: repoRoot,
      encoding: 'utf8',
      maxBuffer: 32 * 1024 * 1024,
    });
  } catch (err) {
    throw new Error(
      `could not read the vocabulary from the CLI (\`uofa vocab --site\` in ${repoRoot}). ` +
      `The site build needs the Python package installed: \`pip install -e .\`. ` +
      `Original error: ${err.message}`
    );
  }

  const payload = JSON.parse(raw);
  const byNamespace = {};
  for (const ns of NAMESPACES) {
    const terms = payload.byNamespace[ns.key] ?? [];
    // Ordering stays here rather than in the CLI: localeCompare is what the
    // rendered index and every anchor list have always used, and Python's
    // ASCII sort puts _evalOutsideEnvelope and the capitalised class names in
    // different places. Presentation order belongs to the presentation layer.
    byNamespace[ns.key] = terms
      .map((t) => ({ ...t, usage: usage[t.iri] ?? 0 }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }
  return { byNamespace, versions: payload.versions };
}
