// Pure functions for discovering shipped UofA example packages and walking them
// into an addressable node index. No I/O beyond reading the files it is handed,
// no rendering. Kept separate from gen-iri-pages.mjs so it can be unit tested
// with `node --test`.
//
// The corpus guard in discoverPackages() is load-bearing, not defensive
// decoration: specs/calibration/packages/ contains four ids that collide
// exactly with shipped example ids, one of which
// (https://uofa.net/nagaraja/cou/cou1-noncannulated) is printed on the Nagaraja
// handout. Indexing anything outside packs/*/examples/ would publish a page for
// the wrong record at a real, cited identifier.

import { readFileSync, readdirSync, realpathSync, statSync } from 'node:fs';
import { basename, join, relative, sep } from 'node:path';

export const ORIGIN = 'https://uofa.net/';

// Every top-level path segment the shipped corpus is allowed to publish under.
// A new segment appearing here means a new namespace is going live, which
// should be a deliberate decision, so the generator fails rather than guesses.
export const ALLOWED_SEGMENTS = [
  'morrison', 'morrison-v09', 'nagaraja', 'iso42001', 'surrogate', 'instances',
  'org', 'criteria',
];

// Paths that must never be indexed. specs/ and dev/ reuse the same IRI space
// with different content; .claude/worktrees holds a full duplicate pack tree.
const FORBIDDEN = ['/specs/', '/dev/', '/build/', '/.claude/', '/tests/', '/node_modules/'];

// Shipped example files carrying uofa.net ids. The two starters/ files use
// example.org and drop out on their own via the id-space check below.
//
// 11 -> 13: the `morrison-v09` siblings. They restate Morrison's content under
// the v0.9 decision model, and they publish under their OWN segment because an
// IRI names one thing: they were briefly copied with the originals' ids intact,
// which would have put two different documents at `uofa.net/morrison/cou1` and
// let a reader resolving the IRI the praxis record cites land on the sibling
// instead. The originals are byte-frozen; the siblings carry the new model.
export const EXPECTED_PACKAGE_COUNT = 13;

function walkDir(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) walkDir(p, out);
    else if (entry.name.endsWith('.jsonld')) out.push(p);
  }
  return out;
}

/**
 * Find the shipped example packages, refusing anything outside packs/<pack>/examples/.
 * Returns absolute paths, sorted.
 */
export function discoverPackages(repoRoot) {
  const packsDir = join(repoRoot, 'packs');
  const found = [];
  for (const pack of readdirSync(packsDir, { withFileTypes: true })) {
    if (!pack.isDirectory()) continue;
    const examples = join(packsDir, pack.name, 'examples');
    try {
      if (!statSync(examples).isDirectory()) continue;
    } catch {
      continue;
    }
    found.push(...walkDir(examples));
  }

  const safe = [];
  for (const file of found.sort()) {
    // realpath first: a symlink into specs/ would otherwise pass a string check.
    // spec/schemas/uofa_shacl.ttl -> packs/core/shapes/ proves symlinks are used here.
    const real = realpathSync(file);
    const rel = relative(repoRoot, real).split(sep).join('/');
    if (!/^packs\/[^/]+\/examples\//.test(rel)) {
      throw new Error(`refusing ${rel}: resolves outside packs/<pack>/examples/`);
    }
    const probe = `/${rel}`;
    for (const bad of FORBIDDEN) {
      if (probe.includes(bad)) throw new Error(`refusing ${rel}: contains ${bad}`);
    }
    safe.push(real);
  }

  if (safe.length !== EXPECTED_PACKAGE_COUNT) {
    throw new Error(
      `expected ${EXPECTED_PACKAGE_COUNT} example packages, found ${safe.length}. ` +
      `If an example was added or removed, update EXPECTED_PACKAGE_COUNT deliberately.`
    );
  }
  return safe;
}

/**
 * Resolve a package's @context to a local file under spec/context/.
 * Shipped packages reference it either by relative path or by the
 * raw.githubusercontent.com URL; both map by basename. Never fetches.
 * Returns null when the package declares no context (the pre-expanded NASA pair).
 */
export function loadContext(contextValue, repoRoot) {
  if (contextValue === undefined || contextValue === null) return null;
  if (typeof contextValue !== 'string') {
    throw new Error(`unsupported inline @context (${typeof contextValue})`);
  }
  const name = basename(contextValue);
  if (!/^v\d+\.\d+\.jsonld$/.test(name)) {
    throw new Error(`cannot map @context ${contextValue} to spec/context/`);
  }
  const local = join(repoRoot, 'spec/context', name);
  return JSON.parse(readFileSync(local, 'utf8'))['@context'];
}

/** Expand a context prefix like "uofa:hasWeakener" to a full IRI. */
function expandPrefixed(value, ctx) {
  const colon = value.indexOf(':');
  if (colon < 0) return value;
  const prefix = value.slice(0, colon);
  const rest = value.slice(colon + 1);
  const mapped = ctx?.[prefix];
  if (typeof mapped === 'string' && /^https?:/.test(mapped)) return mapped + rest;
  return value;
}

/**
 * Map a JSON key to its absolute property IRI.
 * Keys are compact terms (vv40, iso42001, surrogate) or already-absolute IRIs
 * (the pre-expanded NASA pair). Unknown terms fall through to @vocab.
 */
export function resolveTerm(key, ctx) {
  if (/^https?:\/\//.test(key)) return key;
  const entry = ctx?.[key];
  const target = typeof entry === 'string' ? entry : entry?.['@id'];
  if (typeof target === 'string') return expandPrefixed(target, ctx);
  const vocab = ctx?.['@vocab'];
  return typeof vocab === 'string' ? vocab + key : key;
}

const isUofaIri = (v) => typeof v === 'string' && v.startsWith(ORIGIN);

// A uofa.net IRI carrying a fragment is a vocabulary term (vocab#,
// vocab/aims#, vocab/surrogate#), not instance data. Those are described by the
// vocabulary pages, so they must not be counted as instance references or they
// would turn into 33 spurious "dangling node" stubs.
const isInstanceIri = (v) => isUofaIri(v) && !v.includes('#');

/**
 * Walk one package, accumulating into the shared index.
 *
 * A dict is a *node definition* when it carries a uofa.net id AND at least one
 * other key. A dict carrying only an id, or a bare string in an @id-typed
 * position, is a *reference*. Blank nodes (_:bN) are deliberately never
 * addressable: their labels are file-scoped and unstable across
 * re-serialisation, so minting URLs from them would create identifiers that
 * break the next time any tool round-trips the file.
 */
export function walkPackage({ doc, ctx, sourceFile, index }) {
  const { byId, inbound } = index;

  const addInbound = (object, subject, predicate) => {
    if (!isInstanceIri(object)) return;
    (inbound[object] ??= []).push({ subject, predicate, sourceFile });
  };

  const vocabRefs = index.vocabRefs ??= {};
  const noteVocabUse = (term) => {
    if (isUofaIri(term) && term.includes('#')) vocabRefs[term] = (vocabRefs[term] ?? 0) + 1;
  };

  // Class names appear as compact `type` values ("UnitOfAssurance"), which
  // JSON-LD resolves against @vocab. Counting only expanded IRIs reported zero
  // usage for every core class, including CredibilityFactor at 39 occurrences,
  // which is exactly backwards for judging which terms matter most.
  const noteTypeUse = (value) => {
    if (typeof value !== 'string') return;
    if (value.includes('//') || value.includes(':')) return noteVocabUse(value);
    const vocab = ctx?.['@vocab'];
    if (typeof vocab === 'string') noteVocabUse(vocab + value);
  };

  const visit = (node, subjectId, viaPredicate) => {
    if (Array.isArray(node)) {
      for (const item of node) visit(item, subjectId, viaPredicate);
      return;
    }
    if (node === null || typeof node !== 'object') return;

    const rawId = node.id ?? node['@id'];
    const own = isInstanceIri(rawId) ? rawId : null;
    // Blank nodes are never addressable — their labels are file-scoped and
    // change whenever a tool re-serialises the document, so minting URLs from
    // them would create identifiers that break on the next regeneration. But
    // they can still be the subject of a reference (the pre-expanded NASA pair
    // reaches three real IRIs only from blank nodes), so carry the label
    // through as a subject and let the renderer show it as unlinked.
    const blank = typeof rawId === 'string' && rawId.startsWith('_:') ? rawId : null;
    const otherKeys = Object.keys(node).filter((k) => k !== 'id' && k !== '@id');

    // A nested node written inline still stands in a relationship to its
    // parent. Without this edge a context of use, decision record, or
    // credibility factor would have no link back to the package that contains
    // it, which is the single most useful hop on these pages.
    if (own && subjectId && viaPredicate) {
      addInbound(own, subjectId, viaPredicate);
    }

    if (own && otherKeys.length > 0) {
      const existing = byId[own];
      if (existing && existing.sourceFile !== sourceFile) {
        // No collisions exist today. If one appears, two packages disagree
        // about what an identifier means and we must not silently pick one.
        throw new Error(
          `id ${own} defined in both ${existing.sourceFile} and ${sourceFile}`
        );
      }
      byId[own] ??= { id: own, node, sourceFile, ctx };
    }

    const parentId = own ?? blank ?? subjectId;
    for (const [key, value] of Object.entries(node)) {
      if (key === 'id' || key === '@id' || key === '@context') continue;
      if (key === 'type' || key === '@type') {
        (Array.isArray(value) ? value : [value]).forEach(noteTypeUse);
        continue;
      }
      const predicate = resolveTerm(key, ctx);
      noteVocabUse(predicate);

      const consider = (v) => {
        if (typeof v === 'string') {
          // Any uofa.net string in a value position is a reference, whatever
          // the context says. The pre-expanded NASA pair has no context at all,
          // so @type-based detection would miss its references entirely.
          addInbound(v, parentId, predicate);
          noteVocabUse(v);
          return;
        }
        visit(v, parentId, predicate);
      };

      if (Array.isArray(value)) value.forEach(consider);
      else consider(value);
    }
  };

  visit(doc, null, null);
}

/** IRI -> repo-relative output path, e.g. .../nagaraja/cou1 -> nagaraja/cou1 */
export function iriToPath(iri) {
  if (!isUofaIri(iri)) throw new Error(`not a uofa.net IRI: ${iri}`);
  const path = iri.slice(ORIGIN.length).replace(/#.*$/, '').replace(/\/+$/, '');
  const segments = path.split('/');
  if (segments.some((s) => s === '' || s === '.' || s === '..')) {
    throw new Error(`unsafe path in IRI: ${iri}`);
  }
  if (!ALLOWED_SEGMENTS.includes(segments[0])) {
    throw new Error(
      `IRI ${iri} uses top-level segment "${segments[0]}", which is not in ` +
      `ALLOWED_SEGMENTS. Publishing a new namespace should be deliberate.`
    );
  }
  return segments.join('/');
}

/** Build the full index across every shipped package. */
export function buildIndex(repoRoot) {
  const files = discoverPackages(repoRoot);
  const index = { byId: {}, inbound: {} };
  const skipped = [];

  for (const file of files) {
    const doc = JSON.parse(readFileSync(file, 'utf8'));
    const rel = relative(repoRoot, file).split(sep).join('/');
    const topId = doc.id ?? doc['@id'];
    // starters/ use example.org ids; skipping by id-space is more robust than
    // a filename denylist.
    if (!isUofaIri(topId) && !doc['@graph']) {
      skipped.push(rel);
      continue;
    }
    const ctx = loadContext(doc['@context'], repoRoot);
    walkPackage({ doc, ctx, sourceFile: rel, index });
  }

  const defined = Object.keys(index.byId).sort();
  const dangling = Object.keys(index.inbound).filter((i) => !index.byId[i]).sort();
  return { ...index, files, skipped, defined, dangling };
}
