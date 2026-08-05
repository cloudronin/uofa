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
import { coverage, renderVocabPage } from './vocab-render.mjs';
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

test('domain and range are read, including xsd datatype ranges', () => {
  const ttl = `
uofa:achievedLevel a rdf:Property ;
    rdfs:label "achieved level" ;
    rdfs:domain uofa:CredibilityFactor ;
    rdfs:range xsd:integer ;
    rdfs:comment "The level reached." .

uofa:hasContextOfUse a rdf:Property ;
    rdfs:label "has context of use" ;
    rdfs:domain uofa:UnitOfAssurance ;
    rdfs:range uofa:ContextOfUse .

uofa:rationale a rdf:Property ;
    rdfs:label "rationale" ;
    rdfs:comment "Carried by more than one class, so no domain." .
`;
  const terms = extractTtlTerms(ttl, 'test.ttl');
  const achieved = terms['https://uofa.net/vocab#achievedLevel'];
  assert.equal(achieved.domain, 'https://uofa.net/vocab#CredibilityFactor');
  // A datatype range is not an IRI in these namespaces; it stays prefixed.
  assert.equal(achieved.range, 'xsd:integer');
  assert.equal(
    terms['https://uofa.net/vocab#hasContextOfUse'].range,
    'https://uofa.net/vocab#ContextOfUse',
  );
  // Omission is meaningful: it is how a multi-class property is recorded.
  assert.equal(terms['https://uofa.net/vocab#rationale'].domain, undefined);
});

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
  // The renderer turns a same-namespace domain/range into an anchor link. A
  // typo, or a class that was never declared, becomes a dead link on the
  // published page rather than an error here.
  const vocab = buildVocabulary(REPO_ROOT, {});
  for (const ns of NAMESPACES) {
    const declared = new Set(vocab.byNamespace[ns.key].map((t) => t.iri));
    for (const t of vocab.byNamespace[ns.key]) {
      for (const key of ['domain', 'range', 'subClassOf']) {
        const v = t[key];
        if (!v || !v.startsWith('http')) continue;   // xsd:, schema:, ... are external
        // A cross-namespace target is fine and is rendered as plain text; what
        // must never happen is an anchor link to a term that has no anchor.
        if (!v.startsWith(ns.iri)) continue;
        assert.ok(
          declared.has(v),
          `${t.name} declares ${key} ${v}, which is not a declared term`,
        );
      }
    }
  }
});

test('every in-page anchor on a rendered vocabulary page resolves', () => {
  // The extractor cannot see this: it is a rendering bug. Linking a parent or a
  // domain to "#Name" is only correct when that term is on the same page, and
  // the pack pages subclass core terms that are not. This caught seven dead
  // links to ValidationResult, AssuranceClaim, ProcessAttestation and Model.
  const { byNamespace, versions } = buildVocabulary(REPO_ROOT, {});
  for (const namespace of NAMESPACES) {
    const html = renderVocabPage({ namespace, terms: byNamespace[namespace.key], versions });
    const ids = new Set([...html.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]));
    const hrefs = [...html.matchAll(/href="#([^"]+)"/g)].map((m) => m[1]);
    const dead = [...new Set(hrefs.filter((h) => !ids.has(h)))];
    assert.deepEqual(dead, [], `${namespace.key} page links to missing anchors`);
  }
});

test('owl:deprecated is read, and only when it is true', () => {
  const ttl = `
uofa:gone a rdf:Property ;
    rdfs:label "gone" ;
    owl:deprecated true .

uofa:here a rdf:Property ;
    rdfs:label "here" ;
    owl:deprecated false .

uofa:silent a rdf:Property ;
    rdfs:label "silent" .
`;
  const terms = extractTtlTerms(ttl, 'test.ttl');
  assert.equal(terms['https://uofa.net/vocab#gone'].deprecated, true);
  // false is the RDF default and carries no information, so it must not
  // register as a distinct state the renderer then has to interpret.
  assert.equal(terms['https://uofa.net/vocab#here'].deprecated, undefined);
  assert.equal(terms['https://uofa.net/vocab#silent'].deprecated, undefined);
});

test('a deprecated term declared the compact way would vanish, so it is not', () => {
  // SUBJECT_LINE wants ';' or '.' straight after rdf:Property. The idiomatic
  // Turtle below is the shape that silently drops a term from the published
  // vocabulary rather than erroring, which is why §A.19 does not use it.
  const compact = `
uofa:gone a rdf:Property, owl:DeprecatedProperty ;
    rdfs:label "gone" .
`;
  assert.equal(Object.keys(extractTtlTerms(compact, 'test.ttl')).length, 0);

  // And the form §A.19 actually uses survives.
  const spelled = `
uofa:gone a rdf:Property ;
    rdfs:label "gone" ;
    owl:deprecated true .
`;
  assert.equal(Object.keys(extractTtlTerms(spelled, 'test.ttl')).length, 1);
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
  // Batches A to D, plus the five v0.6 reasoning relations picked up in §A.19.
  // The 14 still unlabelled are group 3e, which exist in the context files and
  // nowhere else, so only the author can define them. Bump this deliberately
  // per batch so coverage stays a reviewed number, not drift.
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
