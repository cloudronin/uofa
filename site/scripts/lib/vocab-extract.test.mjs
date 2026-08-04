// Unit tests for vocabulary extraction.
//
// The extractor reads Turtle with targeted patterns rather than a full parser.
// That is only defensible because it refuses to guess: the tests below pin both
// the happy path and the refusal.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildVocabulary, collectContextTerms, collectShaclConstraints,
  extractTtlTerms, NAMESPACES,
} from './vocab-extract.mjs';
import { coverage } from './vocab-render.mjs';
import { buildIndex } from './iri-walk.mjs';

const REPO_ROOT = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../..');

test('extracts labels, comments and subclasses from a vocabulary block', () => {
  const ttl = `
uofa-aims:AIPolicy a rdfs:Class ;
    rdfs:label "AI Policy" ;
    rdfs:comment "ISO 42001 clause 5.2 AI policy artifact." .

uofa-aims:AIMSObjectiveStatement a rdfs:Class ;
    rdfs:subClassOf uofa-aims:AIMSObjective ;
    rdfs:label "AIMS Objective Statement" .
`;
  const terms = extractTtlTerms(ttl, 'test.ttl');
  const policy = terms['https://uofa.net/vocab/aims#AIPolicy'];
  assert.equal(policy.label, 'AI Policy');
  assert.equal(policy.kind, 'Class');
  assert.match(policy.comment, /clause 5\.2/);
  assert.equal(
    terms['https://uofa.net/vocab/aims#AIMSObjectiveStatement'].subClassOf,
    'https://uofa.net/vocab/aims#AIMSObjective',
  );
});

test('refuses to guess at a term line it cannot parse', () => {
  // A multi-line literal is exactly the case a regex would silently mangle.
  const ttl = `
uofa:Thing a rdfs:Class ;
    rdfs:comment """spans
    several lines""" .
`;
  assert.throws(() => extractTtlTerms(ttl, 'bad.ttl'), /refusing to guess/);
});

test('a property shape ending inside a regex character class is not truncated', () => {
  // uofa:hash's sh:pattern contains [a-f0-9]. Cutting the block at the first
  // "]" swallowed both the pattern and the message, and did so silently.
  const c = collectShaclConstraints(REPO_ROOT);
  const hash = c['https://uofa.net/vocab#hash'];
  assert.ok(hash?.length, 'uofa:hash should carry constraints');
  assert.ok(hash.some((x) => x.pattern?.includes('a-f0-9')), 'pattern survives');
  assert.ok(hash.some((x) => /hexdigest/.test(x.message ?? '')), 'message survives');
});

test('context extraction records the version a term first appeared in', () => {
  const { mapping, since, versions } = collectContextTerms(REPO_ROOT);
  assert.deepEqual(versions, ['v0.1', 'v0.2', 'v0.3', 'v0.4', 'v0.5', 'v0.6']);
  assert.equal(since['https://uofa.net/vocab#hash'], 'v0.1');
  assert.equal(mapping['https://uofa.net/vocab#hasWeakener'].idTyped, true);
  // A later addition should not be backdated to v0.1.
  assert.notEqual(since['https://uofa.net/vocab#hasOffsetRationale'], 'v0.1');
});

test('namespace coverage matches what the repo actually contains', () => {
  const vocab = buildVocabulary(REPO_ROOT, buildIndex(REPO_ROOT).vocabRefs);
  const core = coverage(vocab.byNamespace.core);
  const aims = coverage(vocab.byNamespace.aims);
  const surr = coverage(vocab.byNamespace.surrogate);

  assert.equal(core.total, 136);
  assert.equal(core.labelled, 2, 'core is almost entirely unlabelled');
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
  // vocab#  is a prefix of vocab/aims# only if compared naively; make sure the
  // core bucket did not swallow the sub-namespaces.
  const coreNames = vocab.byNamespace.core.map((t) => t.iri);
  assert.ok(!coreNames.some((i) => i.includes('/aims#') || i.includes('/surrogate#')));
});

test('usage counts come from the shipped examples', () => {
  const usage = buildIndex(REPO_ROOT).vocabRefs;
  const vocab = buildVocabulary(REPO_ROOT, usage);
  const used = vocab.byNamespace.core.filter((t) => t.usage > 0);
  assert.ok(used.length > 20, 'core terms are used by the examples');
  const hasWeakener = vocab.byNamespace.core.find((t) => t.name === 'hasWeakener');
  assert.ok(hasWeakener.usage > 0);
});
