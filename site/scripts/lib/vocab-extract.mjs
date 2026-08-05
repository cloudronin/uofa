// Gather everything the repo actually knows about each vocabulary term.
//
// The three namespaces are very unevenly documented, and the pages must not
// pretend otherwise:
//   vocab/aims#      127 terms, all labelled, 76 with comments  (iso42001 pack)
//   vocab/surrogate#  39 terms, all labelled, 25 with comments
//   vocab#           136 terms, 2 labelled (via the disposition pack), and
//                    66 with no label, comment, constraint or schema
//                    description of any kind
//
// For the bare core namespace the honest fallback is everything derivable:
// the JSON-LD mapping, SHACL constraints and their sh:message, the JSON Schema
// description where one exists, which context version introduced the term, and
// how often the shipped examples actually use it. That is not a definition and
// the page says so.

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

export const NAMESPACES = [
  { key: 'core', iri: 'https://uofa.net/vocab#', path: 'vocab', label: 'Core' },
  { key: 'aims', iri: 'https://uofa.net/vocab/aims#', path: 'vocab/aims', label: 'ISO 42001 (AIMS)' },
  { key: 'surrogate', iri: 'https://uofa.net/vocab/surrogate#', path: 'vocab/surrogate', label: 'Surrogate' },
];

// Only the single-line form is accepted. All 288 label/comment lines in the
// repo match it today; anything else throws rather than being silently dropped,
// because a quietly missing definition is worse than a failed build.
const LABEL_LINE = /^\s*rdfs:(label|comment)\s+"([^"]*)"\s*[;.]\s*$/;
const SUBJECT_LINE = /^\s*(uofa|uofa-aims|uofa-surr):([A-Za-z0-9_]+)\s+a\s+(rdfs:Class|rdf:Property)\s*[;.]/;

const PREFIX_TO_NS = {
  'uofa': 'https://uofa.net/vocab#',
  'uofa-aims': 'https://uofa.net/vocab/aims#',
  'uofa-surr': 'https://uofa.net/vocab/surrogate#',
};

/**
 * Pull rdfs:label / rdfs:comment / rdfs:subClassOf / owl:deprecated out of a
 * shapes file.
 * Deliberately narrow: it only reads the vocabulary declaration blocks, and
 * throws on any label or comment line it cannot parse.
 */
export function extractTtlTerms(ttl, sourceFile) {
  const terms = {};
  let current = null;
  const lines = ttl.split('\n');

  for (const [i, line] of lines.entries()) {
    // A line that starts a new subject ends the previous one.
    const subject = SUBJECT_LINE.exec(line);
    if (subject) {
      const [, prefix, name, kind] = subject;
      current = `${PREFIX_TO_NS[prefix]}${name}`;
      terms[current] = {
        iri: current,
        name,
        kind: kind === 'rdfs:Class' ? 'Class' : 'Property',
        sourceFile,
      };
      continue;
    }
    if (/^\s*$/.test(line)) { current = null; continue; }

    if (/rdfs:(label|comment)/.test(line)) {
      const m = LABEL_LINE.exec(line);
      if (!m) {
        throw new Error(
          `${sourceFile}:${i + 1}: unparseable rdfs term line. This extractor ` +
          `only accepts single-line double-quoted literals; refusing to guess.\n  ${line.trim()}`
        );
      }
      if (!current) continue;
      terms[current][m[1] === 'label' ? 'label' : 'comment'] = m[2];
      continue;
    }

    const sub = /^\s*rdfs:subClassOf\s+(uofa|uofa-aims|uofa-surr):([A-Za-z0-9_]+)\s*[;.]/.exec(line);
    if (sub && current) terms[current].subClassOf = `${PREFIX_TO_NS[sub[1]]}${sub[2]}`;

    // Only `owl:deprecated true` marks a term. `false` is the RDF default and
    // says nothing, so treat it as absent rather than as a second state.
    const dep = /^\s*owl:deprecated\s+(true|false)\s*[;.]/.exec(line);
    if (dep && current && dep[1] === 'true') terms[current].deprecated = true;
  }
  return terms;
}

/** rdfs metadata from every pack that declares any. */
export function collectTtlTerms(repoRoot) {
  const all = {};
  const packsDir = join(repoRoot, 'packs');
  for (const pack of readdirSync(packsDir, { withFileTypes: true })) {
    if (!pack.isDirectory()) continue;
    const shapesDir = join(packsDir, pack.name, 'shapes');
    let files = [];
    try { files = readdirSync(shapesDir).filter((f) => f.endsWith('.ttl')); } catch { continue; }
    for (const f of files) {
      const rel = `packs/${pack.name}/shapes/${f}`;
      Object.assign(all, extractTtlTerms(readFileSync(join(shapesDir, f), 'utf8'), rel));
    }
  }
  return all;
}

/**
 * SHACL constraints keyed by the term they constrain. sh:message is often the
 * closest thing to a usable one-line description a core term has.
 */
export function collectShaclConstraints(repoRoot) {
  const out = {};
  const packsDir = join(repoRoot, 'packs');
  for (const pack of readdirSync(packsDir, { withFileTypes: true })) {
    if (!pack.isDirectory()) continue;
    const shapesDir = join(packsDir, pack.name, 'shapes');
    let files = [];
    try { files = readdirSync(shapesDir).filter((f) => f.endsWith('.ttl')); } catch { continue; }

    for (const f of files) {
      const ttl = readFileSync(join(shapesDir, f), 'utf8');
      // Property shapes are bracketed blocks; split on sh:path and read forward.
      const blocks = ttl.split(/sh:path\s+/).slice(1);
      for (const block of blocks) {
        const head = /^(uofa|uofa-aims|uofa-surr):([A-Za-z0-9_]+)/.exec(block);
        if (!head) continue;
        const iri = `${PREFIX_TO_NS[head[1]]}${head[2]}`;
        // End the property shape at a line that is just a closing bracket.
        // Cutting at the first "]" instead would truncate inside a regex
        // character class: uofa:hash's sh:pattern contains [a-f0-9], which
        // silently swallowed both the pattern and the sh:message.
        const close = /^[ \t]*\]/m.exec(block);
        const upto = block.slice(0, close ? close.index : 400);
        const grab = (re) => { const m = re.exec(upto); return m ? m[1] : undefined; };
        const entry = {
          datatype: grab(/sh:datatype\s+([\w:]+)/),
          minCount: grab(/sh:minCount\s+(\d+)/),
          maxCount: grab(/sh:maxCount\s+(\d+)/),
          pattern: grab(/sh:pattern\s+"([^"]*)"/),
          message: grab(/sh:message\s+"([^"]*)"/),
          pack: pack.name,
        };
        if (Object.values(entry).some((v) => v !== undefined)) {
          (out[iri] ??= []).push(entry);
        }
      }
    }
  }
  return out;
}

/** Term descriptions from the JSON Schema, which nests them under oneOf/allOf. */
export function collectSchemaDescriptions(repoRoot) {
  const out = {};
  let schema;
  try {
    schema = JSON.parse(readFileSync(join(repoRoot, 'spec/schemas/uofa.schema.json'), 'utf8'));
  } catch { return out; }
  const walk = (node) => {
    if (Array.isArray(node)) return node.forEach(walk);
    if (node === null || typeof node !== 'object') return;
    if (node.properties && typeof node.properties === 'object') {
      for (const [term, def] of Object.entries(node.properties)) {
        if (def && typeof def.description === 'string' && !term.startsWith('@')) {
          out[term] ??= def.description;
        }
      }
    }
    for (const v of Object.values(node)) walk(v);
  };
  walk(schema);
  return out;
}

/**
 * Context term mappings, plus the earliest context version each term appears
 * in. "Added in v0.4" is real provenance nobody currently has anywhere.
 */
export function collectContextTerms(repoRoot) {
  const dir = join(repoRoot, 'spec/context');
  const versions = readdirSync(dir).filter((f) => /^v\d+\.\d+\.jsonld$/.test(f)).sort();
  const mapping = {};
  const since = {};
  for (const file of versions) {
    const version = file.replace('.jsonld', '');
    const ctx = JSON.parse(readFileSync(join(dir, file), 'utf8'))['@context'];
    for (const [term, value] of Object.entries(ctx)) {
      if (term.startsWith('@')) continue;
      const target = typeof value === 'string' ? value : value?.['@id'];
      if (typeof target !== 'string') continue;
      const iri = target.startsWith('uofa:')
        ? target.replace('uofa:', 'https://uofa.net/vocab#')
        : target;
      if (!iri.startsWith('https://uofa.net/vocab')) continue;
      since[iri] ??= version;
      mapping[iri] = {
        term,
        iri,
        idTyped: typeof value === 'object' && value?.['@type'] === '@id',
        latestVersion: version,
      };
    }
  }
  return { mapping, since, versions: versions.map((v) => v.replace('.jsonld', '')) };
}

/**
 * Merge every source into one record per term, grouped by namespace.
 * `usage` counts how often the shipped examples reference the term, which comes
 * from the instance walk so the vocabulary and identifier pages agree.
 */
export function buildVocabulary(repoRoot, usage = {}) {
  const ttl = collectTtlTerms(repoRoot);
  const shacl = collectShaclConstraints(repoRoot);
  const schemaDesc = collectSchemaDescriptions(repoRoot);
  const { mapping, since, versions } = collectContextTerms(repoRoot);

  const byNamespace = Object.fromEntries(NAMESPACES.map((n) => [n.key, []]));
  const iris = new Set([...Object.keys(ttl), ...Object.keys(mapping), ...Object.keys(shacl)]);

  for (const iri of iris) {
    const ns = NAMESPACES.find((n) => iri.startsWith(n.iri));
    if (!ns) continue;
    const name = iri.slice(ns.iri.length);
    if (!name || name.includes('/')) continue;
    const t = ttl[iri] ?? {};
    const ctx = mapping[iri];
    byNamespace[ns.key].push({
      iri,
      name,
      kind: t.kind ?? null,
      label: t.label ?? null,
      comment: t.comment ?? null,
      subClassOf: t.subClassOf ?? null,
      deprecated: t.deprecated ?? false,
      definedIn: t.sourceFile ?? null,
      jsonKey: ctx?.term ?? null,
      idTyped: ctx?.idTyped ?? false,
      since: since[iri] ?? null,
      schemaDescription: schemaDesc[ctx?.term] ?? schemaDesc[name] ?? null,
      constraints: shacl[iri] ?? [],
      usage: usage[iri] ?? 0,
    });
  }

  for (const key of Object.keys(byNamespace)) {
    byNamespace[key].sort((a, b) => a.name.localeCompare(b.name));
  }
  return { byNamespace, versions };
}
