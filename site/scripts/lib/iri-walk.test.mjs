// Unit tests for the identifier walk. Run: node --test site/scripts/lib/
//
// The corpus guard tests are the important ones. specs/calibration/packages/
// defines four ids that collide exactly with shipped example ids, including
// https://uofa.net/nagaraja/cou/cou1-noncannulated, which is printed on the
// Nagaraja handout. If discovery ever widened to specs/, the site would publish
// a page describing the wrong record at a real, cited identifier.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  ALLOWED_SEGMENTS, buildIndex, discoverPackages, iriToPath, resolveTerm, walkPackage,
} from './iri-walk.mjs';
import { inferType, shortPredicate, stubTwin } from './iri-render.mjs';

const REPO_ROOT = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../..');

test('discovery finds only shipped example packages', () => {
  const files = discoverPackages(REPO_ROOT).map((f) => f.slice(REPO_ROOT.length + 1));
  assert.equal(files.length, 11);
  for (const f of files) {
    assert.match(f, /^packs\/[^/]+\/examples\//, `${f} escaped packs/*/examples/`);
  }
  // The colliding corpora must never appear.
  for (const f of files) {
    assert.ok(!f.includes('specs/'), `${f} is calibration data`);
    assert.ok(!f.includes('dev/'), `${f} is adversarial output`);
    assert.ok(!f.includes('.claude/'), `${f} is a worktree duplicate`);
  }
});

test('starters using example.org are skipped by id-space, not by filename', () => {
  const idx = buildIndex(REPO_ROOT);
  assert.equal(idx.skipped.length, 2);
  for (const s of idx.skipped) assert.match(s, /starters\//);
  for (const id of idx.defined) assert.ok(id.startsWith('https://uofa.net/'));
});

test('index totals are stable', () => {
  const idx = buildIndex(REPO_ROOT);
  assert.equal(idx.defined.length, 128, 'described identifiers');
  assert.equal(idx.dangling.length, 44, 'referenced-only identifiers');
});

test('both IRIs printed on the Nagaraja handout are described', () => {
  const idx = buildIndex(REPO_ROOT);
  for (const id of [
    'https://uofa.net/nagaraja/cou/cou1-noncannulated',
    'https://uofa.net/nagaraja/decision/cou1-overall/offset/test-conditions',
  ]) {
    assert.ok(idx.byId[id], `${id} should be described`);
  }
});

test('inline nested nodes keep an edge back to their parent', () => {
  const idx = buildIndex(REPO_ROOT);
  const cou = idx.inbound['https://uofa.net/nagaraja/cou/cou1-noncannulated'];
  assert.ok(cou?.some((r) => r.subject === 'https://uofa.net/nagaraja/cou1'));
  assert.ok(cou?.some((r) => r.predicate.endsWith('#hasContextOfUse')));
});

test('cross-file references resolve to the defining package', () => {
  const idx = buildIndex(REPO_ROOT);
  const id = 'https://uofa.net/morrison/validation/mesh-convergence';
  assert.match(idx.byId[id].sourceFile, /morrison\/cou2\//);
  assert.ok(idx.inbound[id].some((r) => r.subject === 'https://uofa.net/morrison/cou1'));
});

test('vocabulary terms are never treated as instance identifiers', () => {
  const idx = buildIndex(REPO_ROOT);
  for (const id of [...idx.defined, ...idx.dangling]) {
    assert.ok(!id.includes('#'), `${id} is a vocabulary term, not instance data`);
  }
  assert.ok(Object.keys(idx.vocabRefs).length > 100, 'vocabulary usage is tracked');
});

test('blank nodes never become addressable', () => {
  const idx = buildIndex(REPO_ROOT);
  for (const id of [...idx.defined, ...idx.dangling]) {
    assert.ok(!id.includes('_:'), `${id} came from a blank node label`);
  }
  // ...but a reference made *from* a blank node is still recorded.
  const viaBlank = 'https://uofa.net/instances/hpt-blade-cht-cruise-steady-state/cou2/validation/creep-damage-prediction';
  assert.ok(idx.inbound[viaBlank].some((r) => r.subject.startsWith('_:')));
});

test('iriToPath rejects namespaces outside the allowlist', () => {
  assert.equal(iriToPath('https://uofa.net/nagaraja/cou1'), 'nagaraja/cou1');
  assert.throws(() => iriToPath('https://uofa.net/docs/architecture'), /ALLOWED_SEGMENTS/);
  assert.throws(() => iriToPath('https://uofa.net/nagaraja/../../etc'), /unsafe path/);
  assert.throws(() => iriToPath('https://example.org/foo'), /not a uofa\.net IRI/);
});

test('every generated path stays inside an allowed namespace', () => {
  const idx = buildIndex(REPO_ROOT);
  for (const id of [...idx.defined, ...idx.dangling]) {
    assert.ok(ALLOWED_SEGMENTS.includes(iriToPath(id).split('/')[0]));
  }
});

test('term resolution handles compact terms, prefixes and absolute IRIs', () => {
  const ctx = {
    '@vocab': 'https://uofa.net/vocab#',
    uofa: 'https://uofa.net/vocab#',
    prov: 'http://www.w3.org/ns/prov#',
    hasWeakener: { '@id': 'uofa:hasWeakener', '@type': '@id' },
    wasDerivedFrom: { '@id': 'prov:wasDerivedFrom', '@type': '@id' },
  };
  assert.equal(resolveTerm('hasWeakener', ctx), 'https://uofa.net/vocab#hasWeakener');
  assert.equal(resolveTerm('wasDerivedFrom', ctx), 'http://www.w3.org/ns/prov#wasDerivedFrom');
  assert.equal(resolveTerm('https://uofa.net/vocab#already', ctx), 'https://uofa.net/vocab#already');
  // Unknown terms fall through to @vocab rather than being dropped.
  assert.equal(resolveTerm('somethingNew', ctx), 'https://uofa.net/vocab#somethingNew');
  // A package with no context at all must still resolve keys to something.
  assert.equal(resolveTerm('https://uofa.net/vocab#x', null), 'https://uofa.net/vocab#x');
});

test('an id defined by two packages is a hard error', () => {
  const index = { byId: {}, inbound: {} };
  const mk = (sourceFile) => ({
    doc: { id: 'https://uofa.net/morrison/cou1', name: sourceFile },
    ctx: { '@vocab': 'https://uofa.net/vocab#' },
    sourceFile,
    index,
  });
  walkPackage(mk('a.jsonld'));
  assert.throws(() => walkPackage(mk('b.jsonld')), /defined in both/);
});

test('stub twins assert only @reverse, never an invented name', () => {
  const inbound = [{
    subject: 'https://uofa.net/nagaraja/cou1',
    predicate: 'https://uofa.net/vocab#hasValidationResult',
    sourceFile: 'packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld',
  }];
  const twin = stubTwin('https://uofa.net/nagaraja/validation/mesh-convergence', inbound);
  assert.equal(twin['uofa:descriptionStatus'], 'referenced-only');
  assert.equal(twin['uofa:inferredType'], 'uofa:ValidationResult');
  assert.deepEqual(Object.keys(twin['@reverse']), ['uofa:hasValidationResult']);
  // Nothing may name the thing.
  assert.ok(!('schema:name' in twin));
  assert.ok(!('name' in twin));
  assert.ok(!('label' in twin));
});

test('type inference stays silent when referrers disagree', () => {
  const p = (predicate) => ({ subject: 'x', predicate, sourceFile: 'f' });
  assert.equal(inferType([p('https://uofa.net/vocab#bindsModel')]), 'uofa:Model');
  assert.equal(
    inferType([p('https://uofa.net/vocab#bindsModel'), p('https://uofa.net/vocab#bindsDataset')]),
    null,
  );
  assert.equal(inferType([p('https://uofa.net/vocab#somethingUnmapped')]), null);
});

test('predicate shortening covers the namespaces in use', () => {
  assert.equal(shortPredicate('https://uofa.net/vocab#hasWeakener'), 'uofa:hasWeakener');
  assert.equal(shortPredicate('https://uofa.net/vocab/aims#assessor'), 'aims:assessor');
  assert.equal(shortPredicate('https://uofa.net/vocab/surrogate#parentCOU'), 'surr:parentCOU');
  assert.equal(shortPredicate('http://www.w3.org/ns/prov#wasDerivedFrom'), 'prov:wasDerivedFrom');
});
