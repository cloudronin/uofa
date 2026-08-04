#!/usr/bin/env node
// Sanity check for production uofa.net.
//
// Hits each S1–S5 surface from the cross-browser test spec, verifies HTTP
// 200, asserts known content markers are present, and checks the footer
// build SHA matches the latest commit on main. This is the "infrastructure
// passes" gate the user runs before walking the manual visual matrix in
// site/tests/cross-browser-checklist.md.
//
// Usage: node site/scripts/check-pages.mjs [--base https://uofa.net]
//
// Exit code: 0 if every check passes; 1 on any failure.

import { execFileSync } from 'node:child_process';

const args = process.argv.slice(2);
const baseIdx = args.indexOf('--base');
const BASE = baseIdx >= 0 ? args[baseIdx + 1] : 'https://uofa.net';

const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

const results = { passed: 0, failed: 0, items: [] };

function record(ok, label, detail = '') {
  results.items.push({ ok, label, detail });
  results[ok ? 'passed' : 'failed'] += 1;
  const icon = ok ? `${GREEN}✓${RESET}` : `${RED}✗${RESET}`;
  const tail = detail ? ` ${DIM}${detail}${RESET}` : '';
  console.log(`  ${icon} ${label}${tail}`);
}

async function fetchPage(path) {
  const url = `${BASE}${path}`;
  try {
    const res = await fetch(url, { redirect: 'follow' });
    const body = await res.text();
    return { ok: true, status: res.status, body, url };
  } catch (err) {
    return { ok: false, error: err.message, url };
  }
}

function expectedFooterSha() {
  try {
    const sha = execFileSync('gh', ['api', 'repos/cloudronin/uofa/commits/main', '-q', '.sha'], {
      encoding: 'utf-8',
    }).trim();
    return sha.slice(0, 7);
  } catch {
    return null;
  }
}

async function checkSurface(id, path, contentChecks) {
  console.log(`\n${id} — ${BASE}${path}`);
  const r = await fetchPage(path);
  if (!r.ok) return record(false, `fetch`, r.error);
  record(r.status === 200, `HTTP 200`, `got ${r.status}`);
  if (r.status !== 200) return;
  for (const [label, predicate] of contentChecks) {
    const ok = predicate(r.body);
    record(ok, label);
  }
  return r.body;
}

console.log(`Sanity check against ${BASE}`);

const s1Body = await checkSurface('S1 splash', '/', [
  ['Hero contains v0.7.x version badge', (b) => /v0\.7\.\d+/.test(b)],
  ['Hero NAFEMS banner present', (b) => /Live Wed May 27 at NAFEMS/i.test(b)],
  ['Three Hero CTA buttons', (b) => (b.match(/uofa-btn/g) || []).length >= 3],
  ['Hero terminal shows real uofa demo command (not blade-fatigue)', (b) =>
    /uofa demo/.test(b) && !/blade-fatigue/.test(b)],
  ['Hero terminal shows C1/C2/C3 pipeline output', (b) =>
    /C1.{0,80}Integrity/i.test(b) && /C2.{0,80}SHACL/i.test(b) && /C3.{0,80}Quality gates/i.test(b)],
  ['Pillars C1/C2/C3 cards', (b) => /C1.*INTEGRITY/.test(b) && /C2.*COMPLETENESS/.test(b) && /C3.*QUALITY/.test(b)],
  ['DemoStrip Morrison header', (b) => /Morrison blood pump/.test(b)],
  ['Footer support email', (b) => /support@uofa\.net/.test(b)],
  ['Footer cite link', (b) => /href="\/cite\/"/.test(b)],
  ['Footer Apache-2.0 link', (b) => /Apache-2\.0/.test(b)],
]);

await checkSurface('S2 demo', '/demo/', [
  ['Morrison COU1 jsonld path present', (b) => /morrison-cou1\.jsonld/.test(b)],
  ['Morrison COU2 jsonld path present', (b) => /morrison-cou2\.jsonld/.test(b)],
  ['11 weakeners across 5 patterns', (b) => /11.*weakeners.*5.*patterns|5 patterns.*11/i.test(b)],
  ['18 weakeners on COU2', (b) => /18.*weakeners/.test(b)],
  ['COMPOUND-01 reference', (b) => /COMPOUND-01/.test(b)],
]);

await checkSurface('S3 feedback', '/feedback/', [
  ['mailto support@uofa.net', (b) => /mailto:support@uofa\.net/.test(b)],
  ['GitHub Discussions link', (b) => /github\.com\/cloudronin\/uofa\/discussions/.test(b)],
  ['Three CTAs (run / tell / shape)', (b) => /Run UofA.*own evidence/i.test(b) && /gaps/i.test(b)],
  ['Section 1 uses extract-first flow (uofa extract present)', (b) =>
    /uofa extract path\/to\/your\/evidence-folder/.test(b) && !/uofa init my-assessment/.test(b)],
  ['Google Form link present', (b) => /1FAIpQLScrl-EuVA9B0Pg8w66MIjcpdekmKmHPMfAxC-6oki7UnurNUA/.test(b)],
]);

await checkSurface('S4 catalog', '/reference/catalog/', [
  ['29 patterns across 2 packs', (b) => /29 patterns/i.test(b) && /2 packs?/i.test(b)],
  ['core pack section header', (b) => /Pack:.{0,5}core.{0,30}23 pattern/i.test(b)],
  ['nasa-7009b pack section header', (b) => /Pack:.{0,5}nasa-7009b.{0,30}6 pattern/i.test(b)],
  ['W-PROV-01 row present', (b) => /W-PROV-01/.test(b)],
  ['W-EP-04 row present', (b) => /W-EP-04/.test(b)],
  ['W-NASA-01 row present (aerospace pack)', (b) => /W-NASA-01/.test(b)],
  ['COMPOUND-01 row present', (b) => /COMPOUND-01/.test(b)],
  ['Auto-generated marker in body', (b) => /Generated from .{0,20}uofa catalog/i.test(b)],
]);

await checkSurface('S5 nafems-2026', '/research/nafems-2026/', [
  ['v0.7.x tag in reproduce block', (b) => /git checkout v0\.7\.\d+/.test(b)],
  ['Link to /demo/ page', (b) => /href="\/demo\/"/.test(b)],
  ['11 + 18 weakener call-outs', (b) => /11 weakeners across 5 patterns/.test(b) && /18 weakeners across 6 patterns/.test(b)],
]);

// S6 — identifier resolution. Sampled rather than exhaustive: 172 pages is too
// many to fetch on every run, so this covers one of each shape that could break
// independently. `node scripts/gen-iri-pages.mjs --check` is the exhaustive
// guard, and it runs at build time.
async function checkJson(label, path, checks) {
  console.log(`\n${label} — ${BASE}${path}`);
  const r = await fetchPage(path);
  if (!r.ok) return record(false, 'fetch', r.error);
  record(r.status === 200, 'HTTP 200', `got ${r.status}`);
  if (r.status !== 200) return;
  let parsed;
  try {
    parsed = JSON.parse(r.body);
    record(true, 'parses as JSON');
  } catch (err) {
    return record(false, 'parses as JSON', err.message);
  }
  for (const [l, p] of checks) record(p(parsed), l);
}

// The bare IRI is what a reader actually pastes. GitHub Pages answers it with a
// 301 to the trailing-slash form; assert that rather than only the canonical URL.
async function checkBareIri(path) {
  console.log(`\nS6 bare IRI — ${BASE}${path}`);
  try {
    const res = await fetch(`${BASE}${path}`, { redirect: 'manual' });
    record(res.status === 301 || res.status === 200, 'resolves without a trailing slash', `got ${res.status}`);
  } catch (err) {
    record(false, 'fetch', err.message);
  }
}

const IRI_HTML = [
  ['S6 described node (vv40 convention)', '/nagaraja/cou/cou1-noncannulated/',
    'https://uofa.net/nagaraja/cou/cou1-noncannulated'],
  ['S6 nested node', '/morrison/cou1/factor/model-form/',
    'https://uofa.net/morrison/cou1/factor/model-form'],
  ['S6 flat convention (iso42001)', '/iso42001/hybrid/cou2/',
    'https://uofa.net/iso42001/hybrid/cou2'],
  ['S6 cross-file node', '/morrison/validation/mesh-convergence/',
    'https://uofa.net/morrison/validation/mesh-convergence'],
];

for (const [label, path, iri] of IRI_HTML) {
  await checkSurface(label, path, [
    ['prints its own IRI', (b) => b.includes(iri)],
    ['carries inline JSON-LD', (b) => /<script type="application\/ld\+json">/.test(b)],
    ['inline JSON-LD parses and matches the IRI', (b) => {
      const m = b.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
      if (!m) return false;
      try {
        const j = JSON.parse(m[1]);
        return (j.id ?? j['@id']) === iri;
      } catch { return false; }
    }],
    ['links its machine-readable twin', (b) => /<link rel="alternate" type="application\/ld\+json"/.test(b)],
    ['is search-indexable', (b) => b.includes('data-pagefind-body')],
    ['links back to the defining record on GitHub', (b) => /github\.com\/cloudronin\/uofa\/blob\/main\/packs\//.test(b)],
  ]);
}

await checkSurface('S6 referenced-only stub', '/nagaraja/validation/mesh-convergence/', [
  ['marked referenced but not described', (b) => /Referenced but not described/.test(b)],
  ['names the referring record', (b) => b.includes('https://uofa.net/nagaraja/cou1')],
  ['does not claim to describe the thing', (b) => !/Described in/.test(b)],
]);

await checkJson('S6 twin (described)', '/nagaraja/cou/cou1-noncannulated.json', [
  ['@id matches the IRI', (j) => (j.id ?? j['@id']) === 'https://uofa.net/nagaraja/cou/cou1-noncannulated'],
]);

await checkJson('S6 twin (stub)', '/nagaraja/validation/mesh-convergence.json', [
  ['status is referenced-only', (j) => j['uofa:descriptionStatus'] === 'referenced-only'],
  ['uses @reverse', (j) => typeof j['@reverse'] === 'object'],
  ['invents no name for the thing', (j) =>
    !('name' in j) && !('schema:name' in j) && !('label' in j) && !('rdfs:label' in j)],
]);

await checkBareIri('/nagaraja/cou/cou1-noncannulated');

await checkSurface('S6 identifier index', '/reference/identifiers/', [
  ['lists the Nagaraja COU', (b) => b.includes('https://uofa.net/nagaraja/cou/cou1-noncannulated')],
  ['distinguishes referenced-only entries', (b) => /referenced only/.test(b)],
]);

// S7 — vocabulary and contexts. https://uofa.net/vocab# is the @vocab of every
// package the project has produced, so it returning 404 was a more fundamental
// gap than any single instance identifier.
await checkSurface('S7 core vocabulary', '/vocab/', [
  ['declares its namespace IRI', (b) => b.includes('https://uofa.net/vocab#')],
  ['anchors a term (hasWeakener)', (b) => /id="hasWeakener"/.test(b)],
  ['anchors a term (hash)', (b) => /id="hash"/.test(b)],
  ['admits the namespace is largely undocumented', (b) => /largely undocumented/i.test(b)],
  ['says so per-term where nothing exists', (b) => /No definition, constraint, or schema description/.test(b)],
  ['surfaces SHACL constraints as derived metadata', (b) => /hexdigest/.test(b)],
  ['is search-indexable', (b) => b.includes('data-pagefind-body')],
]);

await checkSurface('S7 aims vocabulary', '/vocab/aims/', [
  ['declares its namespace IRI', (b) => b.includes('https://uofa.net/vocab/aims#')],
  ['carries authored labels', (b) => /AI Policy/.test(b)],
  ['carries authored descriptions', (b) => /clause 5\.2/.test(b)],
  ['does not claim to be undocumented', (b) => !/largely undocumented/i.test(b)],
]);

await checkSurface('S7 surrogate vocabulary', '/vocab/surrogate/', [
  ['declares its namespace IRI', (b) => b.includes('https://uofa.net/vocab/surrogate#')],
  ['carries authored labels', (b) => /rdfs|label|Surrogate/i.test(b)],
]);

await checkJson('S7 vocabulary twin', '/vocab.json', [
  ['is an RDF graph', (j) => Array.isArray(j['@graph'])],
  ['covers the core namespace', (j) => j['@graph'].every((t) => t['@id'].startsWith('https://uofa.net/vocab#'))],
  ['has terms', (j) => j['@graph'].length > 100],
]);

await checkSurface('S7 contexts index', '/context/', [
  ['lists the context versions', (b) => /v0\.5/.test(b) && /v0\.6/.test(b)],
  ['warns against retargeting shipped packages', (b) => /invalidate every signature/i.test(b)],
]);

await checkJson('S7 context document', '/context/v0.5.json', [
  ['declares @vocab', (j) => j['@context']['@vocab'] === 'https://uofa.net/vocab#'],
  ['carries terms', (j) => Object.keys(j['@context']).length > 100],
]);

await checkSurface('extra /cite', '/cite/', [
  ['BibTeX entry present', (b) => /vettrivel_uofa_2026/.test(b)],
  ['NAFEMS conference reference', (b) => /NAFEMS Americas Conference/.test(b)],
]);

await checkSurface('extra /readme', '/readme/', [
  ['README mirrored content present', (b) => /Unit of Assurance|UofA/.test(b)],
  ['Mirrored-page note', (b) => /Mirrored page|edit the source instead/i.test(b)],
]);

console.log('\nFooter SHA freshness:');
const expectedSha = expectedFooterSha();
if (!expectedSha) {
  record(false, 'gh api lookup of latest main commit', 'gh CLI unavailable or unauthenticated');
} else if (s1Body) {
  const m = s1Body.match(/cloudronin\/uofa\/commit\/([0-9a-f]{7,40})/);
  const renderedSha = m ? m[1].slice(0, 7) : null;
  if (!renderedSha) {
    record(false, 'footer SHA link found in /', 'no commit link in body');
  } else {
    record(
      renderedSha === expectedSha,
      `footer SHA ${renderedSha} matches latest main ${expectedSha}`,
    );
  }
}

console.log(
  `\n${results.failed === 0 ? GREEN : RED}` +
  `${results.passed} passed, ${results.failed} failed${RESET}`
);

process.exit(results.failed === 0 ? 0 : 1);
