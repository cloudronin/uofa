#!/usr/bin/env node
// Generate a resolvable web page for every identifier the shipped UofA example
// packages define or reference, so that `https://uofa.net/nagaraja/cou1` and
// friends stop returning 404.
//
// Output goes to site/public/<iri-path>/index.html plus a sibling .json twin.
// public/ rather than an Astro route on purpose: Starlight injects a root
// `[...slug]` catch-all, so a route-based catch-all would shadow every docs
// page. Do NOT "simplify" this into src/pages/[...slug].astro.
//
// This is a build DEPENDENCY, not a check. It does not degrade gracefully when
// something is missing, because skipping would produce a different site (172
// URLs in CI, zero locally) rather than a missing assertion. Contrast
// check-counts.mjs, which may skip precisely because the site is byte-identical
// either way.
//
// Usage:
//   node scripts/gen-iri-pages.mjs            generate
//   node scripts/gen-iri-pages.mjs --check    verify the manifest is current

import {
  existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync,
} from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  ALLOWED_SEGMENTS, buildIndex, iriToPath, resolveTerm,
} from './lib/iri-walk.mjs';
import { renderNodePage, renderStubPage, stubTwin } from './lib/iri-render.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = resolve(__dirname, '..');
const REPO_ROOT = resolve(SITE_ROOT, '..');
const PUBLIC = join(SITE_ROOT, 'public');
const MANIFEST = join(REPO_ROOT, 'snapshots/iri-pages.json');
const DOCS_PAGE = join(SITE_ROOT, 'src/content/docs/reference/identifiers.md');

const checkOnly = process.argv.includes('--check');

/**
 * Fail if a namespace we publish would collide with an existing site route.
 * Reserved names are derived at runtime from the docs collection and the
 * committed public/ assets, so the guard cannot go stale as pages are added.
 */
function assertNoRouteCollision() {
  const docs = readdirSync(join(SITE_ROOT, 'src/content/docs'), { withFileTypes: true })
    .map((e) => (e.isDirectory() ? e.name : e.name.replace(/\.(md|mdx)$/, '')));
  const committed = readdirSync(PUBLIC, { withFileTypes: true })
    .map((e) => e.name)
    .filter((n) => n !== '_iri' && !ALLOWED_SEGMENTS.includes(n));
  const reserved = new Set([...docs, ...committed]);
  for (const seg of ALLOWED_SEGMENTS) {
    if (reserved.has(seg)) {
      throw new Error(
        `namespace "${seg}" collides with an existing site route or asset. ` +
        `Publishing it would shadow ${seg}.`
      );
    }
  }
  return reserved;
}

/** Every published segment must be gitignored, or generated output gets committed. */
function assertGitignored() {
  const gi = readFileSync(join(SITE_ROOT, '.gitignore'), 'utf8');
  const missing = ALLOWED_SEGMENTS.filter((s) => !gi.includes(`public/${s}/`));
  if (missing.length) {
    throw new Error(
      `site/.gitignore is missing entries for: ${missing.join(', ')}. ` +
      `Generated pages would be committed into public/.`
    );
  }
}

function write(relPath, contents) {
  const abs = join(PUBLIC, relPath);
  mkdirSync(dirname(abs), { recursive: true });
  writeFileSync(abs, contents);
}

function main() {
  assertGitignored();
  assertNoRouteCollision();

  const index = buildIndex(REPO_ROOT);
  const { byId, inbound, defined, dangling, files, skipped } = index;
  const isKnown = (iri) => Object.hasOwn(byId, iri);

  // Clear previously generated trees so a removed id cannot linger as a stale
  // page at a live URL.
  if (!checkOnly) {
    for (const seg of ALLOWED_SEGMENTS) rmSync(join(PUBLIC, seg), { recursive: true, force: true });
  }

  const urls = [];

  for (const id of defined) {
    const { node, sourceFile, ctx } = byId[id];
    const path = iriToPath(id);
    const html = renderNodePage({
      id, node, sourceFile,
      resolve: (key) => resolveTerm(key, ctx),
      inbound: inbound[id] ?? [],
      isKnown,
    });
    if (!checkOnly) {
      write(join(path, 'index.html'), html);
      write(`${path}.json`, JSON.stringify(node, null, 2) + '\n');
    }
    urls.push(`/${path}/`);
  }

  for (const id of dangling) {
    const refs = inbound[id] ?? [];
    const path = iriToPath(id);
    const html = renderStubPage({ id, inbound: refs, isKnown });
    if (!checkOnly) {
      write(join(path, 'index.html'), html);
      write(`${path}.json`, JSON.stringify(stubTwin(id, refs), null, 2) + '\n');
    }
    urls.push(`/${path}/`);
  }

  urls.sort();

  // Drift guard, mirroring snapshots/example-counts.json: the expected URL list
  // is committed, so a package change shows up as a reviewable diff.
  const manifest = { total: urls.length, defined: defined.length, stubs: dangling.length, urls };
  if (checkOnly) {
    if (!existsSync(MANIFEST)) throw new Error(`missing ${MANIFEST}; run without --check first`);
    const prev = JSON.parse(readFileSync(MANIFEST, 'utf8'));
    const added = urls.filter((u) => !prev.urls.includes(u));
    const removed = prev.urls.filter((u) => !urls.includes(u));
    if (added.length || removed.length) {
      console.error(`iri-pages: manifest drift\n  added:   ${added.join('\n           ')}\n  removed: ${removed.join('\n           ')}`);
      process.exit(1);
    }
    console.log(`iri-pages: manifest current (${urls.length} URLs)`);
    return;
  }

  mkdirSync(dirname(MANIFEST), { recursive: true });
  writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + '\n');

  writeDocsPage({ byId, defined, dangling });

  if (urls.length !== defined.length + dangling.length) {
    throw new Error(`emitted ${urls.length} URLs for ${defined.length + dangling.length} identifiers`);
  }
  console.log(
    `iri-pages: ${defined.length} described + ${dangling.length} referenced-only ` +
    `= ${urls.length} pages from ${files.length - skipped.length} packages`
  );
}

/** A real Starlight page, so the tree appears in the sidebar, nav and search. */
function writeDocsPage({ byId, defined, dangling }) {
  const groups = {};
  for (const id of [...defined, ...dangling]) {
    const seg = id.replace('https://uofa.net/', '').split('/')[0];
    (groups[seg] ??= []).push(id);
  }
  const body = Object.entries(groups).sort().map(([seg, ids]) => {
    const rows = ids.sort().map((id) => {
      const path = '/' + id.replace('https://uofa.net/', '') + '/';
      const kind = byId[id] ? 'described' : 'referenced only';
      return `| [\`${id}\`](${path}) | ${kind} |`;
    }).join('\n');
    return `## ${seg}\n\n| Identifier | Status |\n|---|---|\n${rows}\n`;
  }).join('\n');

  const frontmatter = `---
title: 'Published identifiers'
description: 'Every identifier the shipped UofA example packages define or reference, and where each one resolves.'
sidebar:
  hidden: false
---

:::note[Generated page]
Generated by \`site/scripts/gen-iri-pages.mjs\` from the packages under
\`packs/*/examples/\`. Edits here are overwritten on the next build.
:::

UofA packages identify their parts with \`https://uofa.net/\` IRIs. Those are
identifiers first and addresses second, but every one listed here now resolves
to a page describing what the record says about it.

Identifiers marked **referenced only** are named by a package through a property
such as \`bindsModel\` or \`hasValidationResult\`, but no package in this
repository describes them. Their pages say so plainly rather than inventing a
description.

`;
  mkdirSync(dirname(DOCS_PAGE), { recursive: true });
  writeFileSync(DOCS_PAGE, frontmatter + body);
}

try {
  main();
} catch (err) {
  console.error(`iri-pages: ${err.message}`);
  process.exit(1);
}
