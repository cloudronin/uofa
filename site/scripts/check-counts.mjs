#!/usr/bin/env node
// Snapshot test for bundled-example weakener counts.
//
// Runs `uofa rules <file> --format json` for each example listed in
// snapshots/example-counts.json and compares total firings, pattern count,
// and severity breakdown. Drift fails the build with a clear diff.
//
// Skip behavior: if `uofa` is not on PATH (e.g. local dev without install),
// the script prints a warning and exits 0 so `npm run build` still works
// for non-content edits. CI always has uofa installed (see deploy-site.yml).

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = resolve(__dirname, '..');
const REPO_ROOT = resolve(SITE_ROOT, '..');
const SNAPSHOT_PATH = resolve(REPO_ROOT, 'snapshots/example-counts.json');

const snapshot = JSON.parse(readFileSync(SNAPSHOT_PATH, 'utf-8'));

function uofaAvailable() {
  try {
    execFileSync('uofa', ['--version'], { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

if (!uofaAvailable()) {
  console.warn(
    'check-counts: `uofa` CLI not found on PATH; skipping snapshot test. ' +
    'Run `pip install -e ..` to enable, or rely on CI to enforce.'
  );
  process.exit(0);
}

let failed = 0;
let checked = 0;
const diffs = [];

for (const [exampleId, expected] of Object.entries(snapshot)) {
  if (exampleId.startsWith('$')) continue;
  checked += 1;
  const args = ['--pack', expected.pack, 'rules', expected.file, '--format', 'json'];
  let out;
  try {
    out = execFileSync('uofa', args, { cwd: REPO_ROOT, encoding: 'utf-8' });
  } catch (err) {
    console.error(`check-counts: ${exampleId}: command failed`);
    if (err.stdout) console.error('  stdout:', err.stdout.toString().slice(0, 500));
    if (err.stderr) console.error('  stderr:', err.stderr.toString().slice(0, 500));
    failed += 1;
    continue;
  }
  let actual;
  try {
    actual = JSON.parse(out);
  } catch (err) {
    console.error(`check-counts: ${exampleId}: stdout was not JSON: ${err.message}`);
    failed += 1;
    continue;
  }
  const actualTotal = actual.summary.total_firings;
  const actualPatterns = actual.summary.patterns;
  const actualCompound = actual.firings
    .filter((f) => /^COMPOUND-/.test(f.patternId))
    .reduce((acc, f) => acc + f.hits, 0);
  if (
    actualTotal !== expected.total ||
    actualPatterns !== expected.patterns ||
    actualCompound !== expected.compound_hits
  ) {
    diffs.push(
      `  ${exampleId} (${expected.file})\n` +
      `    expected:  total=${expected.total}, patterns=${expected.patterns}, compound=${expected.compound_hits}\n` +
      `    actual:    total=${actualTotal}, patterns=${actualPatterns}, compound=${actualCompound}`
    );
    failed += 1;
  }
}

if (failed > 0) {
  console.error(
    `\ncheck-counts: SNAPSHOT DRIFT in ${failed}/${checked} example(s):\n` +
    diffs.join('\n\n') +
    '\n\nIf the new counts are intentional, update snapshots/example-counts.json and re-run.'
  );
  process.exit(1);
}

console.log(`check-counts: all ${checked} example snapshot(s) match.`);
