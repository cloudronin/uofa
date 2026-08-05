// Invariants about the published vocabulary, whoever parsed it.
//
// This replaced vocab-extract.test.mjs when the regex Turtle reader was removed
// in favour of `uofa vocab --site`. Eight of its tests exercised that reader's
// internals -- what it did with a line it could not parse, whether it truncated
// inside a character class -- and went with it; the ones that still mattered
// moved to tests/test_vocab_index.py, which tests the reader that now exists.
//
// What remains here is everything that is about the vocabulary as the site
// consumes it, plus the rendering invariants no Python test can see.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { buildVocabulary, NAMESPACES } from './vocab-source.mjs';
import { coverage, renderVocabPage } from './vocab-render.mjs';
import { buildIndex } from './iri-walk.mjs';

const REPO_ROOT = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../..');

test('no core property claims a domain outside the core namespace', () => {
  // A core term pointing at uofa-aims: or uofa-surr: would make core depend on
  // a pack. documentReference and sourceReference are the two that tempt it.
  const vocab = buildVocabulary(REPO_ROOT, {});
  for (const t of vocab.byNamespace.core) {
    for (const key of ['domain', 'range']) {
      const v = t[key];
      if (!v || !v.startsWith('http')) continue;   // xsd:, schema:, ... are external
      assert.ok(
        v.startsWith('https://uofa.net/vocab#'),
        `core term ${t.name} declares ${key} ${v}, which inverts pack layering`,
      );
    }
  }
});

test('every declared domain and range names a term that exists', () => {
  const vocab = buildVocabulary(REPO_ROOT, {});
  for (const ns of NAMESPACES) {
    const declared = new Set(vocab.byNamespace[ns.key].map((t) => t.iri));
    for (const t of vocab.byNamespace[ns.key]) {
      for (const key of ['domain', 'range', 'subClassOf']) {
        const v = t[key];
        if (!v || !v.startsWith('http')) continue;
        // Cross-namespace targets render as plain text; only same-namespace
        // ones become anchors, and only those can dangle.
        if (!v.startsWith(ns.iri)) continue;
        assert.ok(declared.has(v), `${t.name} declares ${key} ${v}, which is not a declared term`);
      }
    }
  }
});

test('every in-page anchor on a rendered vocabulary page resolves', () => {
  // A rendering invariant: no Python test can see it, because it is about what
  // the template does with the data rather than what the data says. This caught
  // seven dead links to ValidationResult, AssuranceClaim, ProcessAttestation
  // and Model, from linking a cross-namespace parent to a same-page anchor.
  const { byNamespace, versions } = buildVocabulary(REPO_ROOT, {});
  for (const namespace of NAMESPACES) {
    const html = renderVocabPage({ namespace, terms: byNamespace[namespace.key], versions });
    const ids = new Set([...html.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]));
    const hrefs = [...html.matchAll(/href="#([^"]+)"/g)].map((m) => m[1]);
    const dead = [...new Set(hrefs.filter((h) => !ids.has(h)))];
    assert.deepEqual(dead, [], `${namespace.key} page links to missing anchors`);
  }
});

test('terms the current context dropped are marked, not deleted', () => {
  // The v0.7 cleanup removed 19 terms that nothing referenced. They must stay
  // listed: their IRIs resolve on uofa.net, and a package pinned to v0.5 still
  // uses them.
  const core = buildVocabulary(REPO_ROOT, {}).byNamespace.core;
  const dropped = core.filter((t) => t.lastVersion);

  assert.equal(dropped.length, 19, 'the v0.7 cleanup dropped 19 core terms');
  for (const t of dropped) {
    assert.equal(t.lastVersion, 'v0.6', `${t.name} should last appear in v0.6`);
    assert.ok(t.iri.startsWith('https://uofa.net/vocab#'));
  }
  assert.equal(core.find((t) => t.name === 'hasContextOfUse').lastVersion, null);
});

test('namespace coverage matches what the repo actually contains', () => {
  const vocab = buildVocabulary(REPO_ROOT, buildIndex(REPO_ROOT).vocabRefs);
  const core = coverage(vocab.byNamespace.core);
  const aims = coverage(vocab.byNamespace.aims);
  const surr = coverage(vocab.byNamespace.surrogate);

  assert.equal(core.total, 136);
  // Batches A to D, plus the five v0.6 reasoning relations in §A.19. The 14
  // still unlabelled exist in the context files and nowhere else, so only the
  // author can define them. Bump deliberately, so coverage stays a reviewed
  // number rather than drift.
  assert.equal(core.labelled, 122, 'everything but the 14 author-only terms');
  assert.equal(core.deprecated, 5, 'the v0.6 reasoning relations, used by nothing');
  assert.equal(aims.total, 127);
  assert.equal(aims.labelled, 127, 'every aims term is labelled');
  assert.equal(surr.total, 39);
  assert.equal(surr.labelled, 39);
});

test('terms never leak across namespace boundaries', () => {
  const vocab = buildVocabulary(REPO_ROOT, {});
  for (const ns of NAMESPACES) {
    for (const t of vocab.byNamespace[ns.key]) {
      assert.ok(t.iri.startsWith(ns.iri), `${t.iri} filed under ${ns.key}`);
      assert.ok(!t.name.includes('/'), `${t.name} is not a bare term name`);
    }
  }
  // vocab# is a prefix of vocab/aims# only if compared naively; make sure the
  // core bucket did not swallow the sub-namespaces.
  const coreNames = vocab.byNamespace.core.map((t) => t.iri);
  assert.ok(!coreNames.some((i) => i.includes('/aims#') || i.includes('/surrogate#')));
});

test('usage counts come from the shipped examples', () => {
  // usage is still computed here, from the instance walk the identifier pages
  // already run. Counting it again in Python would recreate the second reader
  // this file's predecessor was deleted to remove.
  const usage = buildIndex(REPO_ROOT).vocabRefs;
  const vocab = buildVocabulary(REPO_ROOT, usage);
  const used = vocab.byNamespace.core.filter((t) => t.usage > 0);
  assert.ok(used.length > 40, `expected the examples to exercise many core terms, got ${used.length}`);

  const cou = vocab.byNamespace.core.find((t) => t.name === 'hasContextOfUse');
  assert.ok(cou.usage > 0, 'hasContextOfUse is used by every shipped package');
});

test('the CLI is the only reader: no Turtle is parsed here', () => {
  // The point of the change. If a regex Turtle reader reappears in the site
  // build, two readers of one source start drifting again -- and the last one
  // silently truncated inside a character class and required a specific
  // punctuation after `a rdf:Property`.
  // Reading a .ttl is the signal. Emitting an rdfs: key is not -- vocab-render
  // writes rdfs:label into the JSON-LD twin, which is output, not parsing.
  const dir = resolve(fileURLToPath(new URL('.', import.meta.url)));
  for (const f of readdirSync(dir).filter((n) => n.endsWith('.mjs') && !n.includes('.test.'))) {
    const src = readFileSync(resolve(dir, f), 'utf8');
    assert.ok(!/\.ttl['"`]/.test(src) && !/endsWith\(['"]\.ttl/.test(src),
      `${f} reads Turtle directly; the CLI should be the only reader`);
  }
});
