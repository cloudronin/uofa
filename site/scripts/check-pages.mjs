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
  ['Pillars C1/C2/C3 cards', (b) => /C1.*INTEGRITY/.test(b) && /C2.*COMPLETENESS/.test(b) && /C3.*QUALITY/.test(b)],
  ['DemoStrip Morrison header', (b) => /Morrison blood pump/.test(b)],
  ['Footer support email', (b) => /support@uofa\.net/.test(b)],
  ['Footer cite link', (b) => /href="\/cite\/"/.test(b)],
  ['Footer Apache-2.0 link', (b) => /Apache-2\.0/.test(b)],
]);

await checkSurface('S2 demo', '/demo/', [
  ['Stage 5 Morrison COU1 path', (b) => /morrison-cou1\.jsonld/.test(b)],
  ['Stage 6 Morrison COU2 path', (b) => /morrison-cou2\.jsonld/.test(b)],
  ['11 weakeners across 5 patterns', (b) => /11.*weakeners.*5.*patterns|5 patterns.*11/i.test(b)],
  ['18 weakeners on COU2', (b) => /18.*weakeners/.test(b)],
  ['COMPOUND-01 reference', (b) => /COMPOUND-01/.test(b)],
]);

await checkSurface('S3 feedback', '/feedback/', [
  ['mailto support@uofa.net', (b) => /mailto:support@uofa\.net/.test(b)],
  ['GitHub Discussions link', (b) => /github\.com\/cloudronin\/uofa\/discussions/.test(b)],
  ['Three CTAs (run / tell / shape)', (b) => /Run UofA.*own evidence/i.test(b) && /gaps/i.test(b)],
]);

await checkSurface('S4 catalog', '/reference/catalog/', [
  ['23 patterns mentioned', (b) => /23 patterns/i.test(b)],
  ['W-PROV-01 row present', (b) => /W-PROV-01/.test(b)],
  ['W-EP-04 row present', (b) => /W-EP-04/.test(b)],
  ['COMPOUND-01 row present', (b) => /COMPOUND-01/.test(b)],
  ['Auto-generated marker in body', (b) => /Generated from .{0,20}uofa catalog/i.test(b)],
]);

await checkSurface('S5 nafems-2026', '/research/nafems-2026/', [
  ['v0.7.x tag in reproduce block', (b) => /git checkout v0\.7\.\d+/.test(b)],
  ['Link to /demo/ page', (b) => /href="\/demo\/"/.test(b)],
  ['11 + 18 weakener call-outs', (b) => /11 weakeners across 5 patterns/.test(b) && /18 weakeners across 6 patterns/.test(b)],
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
