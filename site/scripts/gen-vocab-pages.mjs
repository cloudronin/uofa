#!/usr/bin/env node
// Publish the UofA vocabulary namespaces and JSON-LD context documents.
//
// https://uofa.net/vocab# is the @vocab of every package the project has ever
// produced, including packages on users' machines that will never be published,
// and it has always returned 404. That makes it a more fundamental gap than any
// individual instance identifier.
//
// Hash IRIs never reach the server, so this is three documents with per-term
// anchors rather than a route per term.
//
// Like gen-iri-pages.mjs this is a build dependency, not a check: skipping
// would silently produce a site missing several hundred addressable terms.

import { copyFileSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { buildIndex } from './lib/iri-walk.mjs';
import { buildVocabulary, NAMESPACES } from './lib/vocab-source.mjs';
import { coverage, renderVocabPage, vocabTwin } from './lib/vocab-render.mjs';
import { esc } from './lib/iri-render.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = resolve(__dirname, '..');
const REPO_ROOT = resolve(SITE_ROOT, '..');
const PUBLIC = join(SITE_ROOT, 'public');
const DOCS_PAGE = join(SITE_ROOT, 'src/content/docs/reference/vocabulary.md');

// Segments this script owns. Asserted against .gitignore for the same reason as
// the identifier segments: public/ also holds committed assets.
const SEGMENTS = ['vocab', 'context', 'schemas'];

function assertGitignored() {
  const gi = readFileSync(join(SITE_ROOT, '.gitignore'), 'utf8');
  // Both the directory and the sibling .json twin. Checking only the directory
  // let public/vocab.json slip through and show up as untracked.
  const required = [
    ...SEGMENTS.map((s) => `public/${s}/`),
    ...NAMESPACES.map((n) => `public/${n.path}.json`),
  ];
  const rules = gi.split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
  // A path counts as covered by an exact entry or by any parent directory
  // entry, so public/vocab/aims.json is satisfied by public/vocab/ while the
  // sibling public/vocab.json still needs its own line.
  const missing = required.filter(
    (entry) => !rules.some((r) => entry === r || (r.endsWith('/') && entry.startsWith(r)))
  );
  if (missing.length) {
    throw new Error(`site/.gitignore is missing entries for: ${missing.join(', ')}`);
  }
}

function assertNoRouteCollision() {
  const docs = readdirSync(join(SITE_ROOT, 'src/content/docs'), { withFileTypes: true })
    .map((e) => (e.isDirectory() ? e.name : e.name.replace(/\.(md|mdx)$/, '')));
  for (const seg of SEGMENTS) {
    if (docs.includes(seg)) throw new Error(`namespace "${seg}" collides with a docs route`);
  }
}

const write = (rel, contents) => {
  const abs = join(PUBLIC, rel);
  mkdirSync(dirname(abs), { recursive: true });
  writeFileSync(abs, contents);
};

/**
 * Serve the JSON-LD contexts from uofa.net. Note this does NOT retarget the
 * packages: shipped files pin raw.githubusercontent.com inside the canonicalised
 * content, so changing their @context would break every hash and signature.
 * These are an additional way to reach the same documents.
 */
function publishContexts() {
  const dir = join(REPO_ROOT, 'spec/context');
  const files = readdirSync(dir).filter((f) => /^v\d+\.\d+\.jsonld$/.test(f)).sort();
  for (const f of files) {
    const src = join(dir, f);
    copyFileSync(src, join(PUBLIC, 'context', f));
    // .json alongside .jsonld: GitHub Pages maps .json to application/json
    // reliably, whereas .jsonld is very likely to come back as
    // application/octet-stream, which conforming processors reject.
    copyFileSync(src, join(PUBLIC, 'context', f.replace('.jsonld', '.json')));
  }

  const rows = files.map((f) => {
    const v = f.replace('.jsonld', '');
    const ctx = JSON.parse(readFileSync(join(dir, f), 'utf8'))['@context'];
    const n = Object.keys(ctx).filter((k) => !k.startsWith('@')).length;
    return `      <tr><td><a href="/context/${esc(f)}"><code>${esc(v)}</code></a></td>
        <td>${n} terms</td>
        <td><a href="/context/${esc(f.replace('.jsonld', '.json'))}"><code>.json</code></a></td></tr>`;
  }).join('\n');

  write('context/index.html', `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>JSON-LD contexts — UofA</title>
<meta name="description" content="The JSON-LD context documents UofA evidence packages expand against." />
<link rel="stylesheet" href="/_iri/iri.css" />
</head>
<body class="iri-vocab">
<header class="iri-top">
  <a class="iri-home" href="/">Unit of Assurance</a>
  <nav><a href="/reference/identifiers/">All identifiers</a></nav>
</header>
<main data-pagefind-body>
  <p class="iri-eyebrow">Vocabulary</p>
  <h1>JSON-LD contexts</h1>
  <p class="iri-note">The context documents UofA packages expand their compact
  property names against. Each is served here in both <code>.jsonld</code> and
  <code>.json</code> form.</p>
  <div class="v-banner">
    <p><strong>Shipped packages do not point here.</strong> They pin
    <code>raw.githubusercontent.com</code>, and that URL is inside the
    canonicalised content that the package hash and signature cover. Retargeting
    it would invalidate every signature, so these copies are an additional route
    to the same documents rather than a replacement.</p>
  </div>
  <section>
    <h2>Versions</h2>
    <table class="iri-table">
      <thead><tr><th>Version</th><th>Terms</th><th>Also as</th></tr></thead>
      <tbody>
${rows}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Vocabularies</h2>
    <p class="iri-note">Every context declares
    <code>@vocab: https://uofa.net/vocab#</code>. The namespaces those terms
    expand into are documented at
    ${NAMESPACES.map((n) => `<a href="/${n.path}/"><code>${esc(n.iri)}</code></a>`).join(', ')}.</p>
  </section>
</main>
<footer class="iri-foot">
  <p>Copied from <code>spec/context/</code> in the repository at build time.</p>
</footer>
</body>
</html>
`);
  return files.length;
}

/**
 * Serve the generated JSON Schema from uofa.net at the URL it already claims.
 *
 * The destination is derived from the schema's own `$id` rather than hardcoded,
 * so the declared identity and the published location cannot disagree. If `$id`
 * carries a version segment (`/schemas/v0.5/uofa.schema.json`) the document goes
 * there and the unversioned path is also written as the current alias, giving
 * adopters something stable to pin. If `$id` is unversioned the single
 * unversioned path IS current.
 *
 * Unlike the contexts there is no .json twin to write: the file is already
 * .json, so GitHub Pages serves it as application/json without help.
 *
 * Publishing this is inert with respect to integrity. Nothing embeds the schema
 * URL inside a canonicalised package, so unlike @context it carries no risk to
 * any hash or signature.
 */
function publishSchemas() {
  const src = join(REPO_ROOT, 'spec/schemas/uofa.schema.json');
  const schema = JSON.parse(readFileSync(src, 'utf8'));
  const id = schema.$id;
  if (!id) throw new Error('spec/schemas/uofa.schema.json has no $id to publish under');

  const url = new URL(id);
  if (url.hostname !== 'uofa.net') {
    throw new Error(`schema $id points at ${url.hostname}, not uofa.net: ${id}`);
  }
  const segments = url.pathname.replace(/^\//, '').split('/');
  if (segments[0] !== 'schemas' || segments.some((s) => !s || s === '..')) {
    throw new Error(`schema $id path is not a plain /schemas/... route: ${id}`);
  }

  const written = [];
  const emit = (rel, from) => {
    const abs = join(PUBLIC, rel);
    mkdirSync(dirname(abs), { recursive: true });
    copyFileSync(from, abs);
    written.push(rel);
  };

  // The moving alias: whatever main currently generates.
  emit(segments.join('/'), src);

  // Frozen versions, named like the contexts (spec/schemas/vX.Y.json ->
  // /schemas/vX.Y.json) so a consumer can read a package's @context version and
  // pick the matching schema without a lookup table. Cut by `uofa schema
  // --freeze vX.Y` and never regenerated -- adopters pin these.
  const dir = join(REPO_ROOT, 'spec/schemas');
  const frozen = readdirSync(dir).filter((f) => /^v\d+\.\d+\.json$/.test(f)).sort();
  for (const f of frozen) {
    const abs = join(dir, f);
    // A frozen file whose $id does not match its own URL would publish a
    // document claiming to be something else. Caught here as well as in the
    // test, because the build is what actually puts it on the internet.
    const got = JSON.parse(readFileSync(abs, 'utf8')).$id;
    const want = `https://uofa.net/schemas/${f}`;
    if (got !== want) {
      throw new Error(`frozen schema ${f} declares $id ${got}, expected ${want}`);
    }
    emit(`schemas/${f}`, abs);
  }

  writeSchemaIndex(frozen, segments.join('/'));
  return written;
}

/** Landing page for /schemas/, mirroring the /context/ one. */
function writeSchemaIndex(frozen, currentRel) {
  const rows = frozen.map((f) => {
    const v = f.replace('.json', '');
    return `      <tr><td><a href="/schemas/${esc(f)}"><code>${esc(v)}</code></a></td>
        <td>frozen — safe to pin</td>
        <td><a href="/context/${esc(v)}.jsonld"><code>${esc(v)}</code> context</a></td></tr>`;
  }).join('\n');

  write('schemas/index.html', `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>JSON Schemas — UofA</title>
<link rel="stylesheet" href="/_iri/iri.css" />
</head>
<body>
<main class="iri-main">
  <h1>JSON Schemas</h1>
  <p class="iri-note">Generated from the SHACL shapes. Use these to validate UofA
  evidence packages in an editor or in CI — point your tooling at a URL below.
  Do <strong>not</strong> add <code>$schema</code> inside a package: the hash
  covers the JSON serialization, so an extra key invalidates the signature.</p>
  <section>
    <h2>Pin a version</h2>
    <p class="iri-note">Frozen versions never change. Match the version to the
    <code>@context</code> your package declares.</p>
    <table>
      <thead><tr><th>Schema</th><th>Status</th><th>Matching context</th></tr></thead>
      <tbody>
${rows || '      <tr><td colspan="3">none yet</td></tr>'}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Track current</h2>
    <p class="iri-note"><a href="/${esc(currentRel)}"><code>/${esc(currentRel)}</code></a>
    always serves what <code>main</code> generates. Convenient for development,
    but it moves — pin a version above if you need stability.</p>
  </section>
</main>
<footer class="iri-foot">
  <p>Generated from <code>spec/schemas/</code> in the repository at build time.</p>
</footer>
</body>
</html>
`);
}

function writeDocsPage(vocab) {
  const rows = NAMESPACES.map((ns) => {
    const c = coverage(vocab.byNamespace[ns.key]);
    return `| [${ns.label}](/${ns.path}/) | \`${ns.iri}\` | ${c.total} | ${c.labelled} | ${c.commented} |`;
  }).join('\n');

  const core = coverage(vocab.byNamespace.core);
  writeFileSync(DOCS_PAGE, `---
title: 'Vocabulary'
description: 'The RDF vocabularies UofA evidence packages expand their property names into, and how well documented each one is.'
---

:::note[Generated page]
Generated by \`site/scripts/gen-vocab-pages.mjs\` from \`spec/context/\`,
\`packs/*/shapes/\` and \`spec/schemas/\`. Edits here are overwritten on the next
build.
:::

UofA packages use compact property names that expand into these namespaces. Each
term is addressable, so \`https://uofa.net/vocab#hasWeakener\` resolves to its
entry.

| Namespace | IRI | Terms | Labelled | Described |
|---|---|---|---|---|
${rows}

The [JSON-LD contexts](/context/) that map compact names onto these namespaces
are served alongside them.

## Coverage is uneven

The ISO 42001 and surrogate namespaces carry authored labels and descriptions in
their pack shapes. The core namespace does not: of its ${core.total} terms,
${core.labelled} have an authored definition, ${core.constrained} carry SHACL
constraints that describe how they are validated, and ${core.bare} have neither.

Their pages show what can be derived from the context, the shapes and the JSON
Schema, and say plainly where nothing exists. Derived metadata tells you how a
term is constrained, not what it means. Writing definitions for the core terms
belongs in \`packs/core/shapes/\`, alongside the definitions the other packs
already carry, so that SHACL messages improve at the same time.
`);
}

function main() {
  assertGitignored();
  assertNoRouteCollision();

  // Usage counts come from the same walk the identifier pages use, so the two
  // sets of pages cannot disagree about how often a term appears.
  const usage = buildIndex(REPO_ROOT).vocabRefs;
  const vocab = buildVocabulary(REPO_ROOT, usage);

  for (const seg of SEGMENTS) rmSync(join(PUBLIC, seg), { recursive: true, force: true });
  mkdirSync(join(PUBLIC, 'context'), { recursive: true });

  const summary = [];
  for (const ns of NAMESPACES) {
    const terms = vocab.byNamespace[ns.key];
    if (!terms.length) throw new Error(`no terms found for ${ns.iri}`);
    write(join(ns.path, 'index.html'), renderVocabPage({ namespace: ns, terms, versions: vocab.versions }));
    write(`${ns.path}.json`, JSON.stringify(vocabTwin(ns, terms), null, 2) + '\n');
    const c = coverage(terms);
    summary.push(`${ns.key} ${c.total} terms (${c.labelled} labelled)`);
  }

  const contexts = publishContexts();
  const schemas = publishSchemas();
  writeDocsPage(vocab);

  console.log(
    `vocab-pages: ${summary.join(', ')}; ${contexts} context documents; ` +
    `schema at ${schemas.join(', ')}`
  );
}

try {
  main();
} catch (err) {
  console.error(`vocab-pages: ${err.message}`);
  process.exit(1);
}
