// Render one HTML document per vocabulary namespace.
//
// Hash IRIs mean the server never sees the fragment: https://uofa.net/vocab#Foo
// is a request for /vocab/, and the browser scrolls to #Foo. So this is three
// documents with per-term anchors, not 300 routes.
//
// The core namespace has almost no authored definitions. The page says that in
// its own banner rather than dressing up derived metadata as documentation.

import { esc } from './iri-render.mjs';

const REPO_BLOB = 'https://github.com/cloudronin/uofa/blob/main';

function coverage(terms) {
  return {
    total: terms.length,
    labelled: terms.filter((t) => t.label).length,
    commented: terms.filter((t) => t.comment).length,
    constrained: terms.filter((t) => t.constraints.length).length,
    described: terms.filter((t) => t.schemaDescription).length,
    used: terms.filter((t) => t.usage > 0).length,
    deprecated: terms.filter((t) => t.deprecated).length,
    dropped: terms.filter((t) => t.lastVersion).length,
    domained: terms.filter((t) => t.domain).length,
    bare: terms.filter((t) => !t.label && !t.comment && !t.constraints.length && !t.schemaDescription).length,
  };
}

function renderConstraints(constraints) {
  // Several profiles can constrain the same term; the messages differ per
  // profile, so show them all rather than picking one arbitrarily.
  const seen = new Set();
  const rows = [];
  for (const c of constraints) {
    const bits = [];
    if (c.datatype) bits.push(`datatype <code>${esc(c.datatype)}</code>`);
    if (c.minCount) bits.push(`min ${esc(c.minCount)}`);
    if (c.maxCount) bits.push(`max ${esc(c.maxCount)}`);
    if (c.pattern) bits.push(`pattern <code>${esc(c.pattern)}</code>`);
    // An enumeration answers the reader's question outright, so it is worth
    // more than any other constraint kind on the page.
    if (c.in) bits.push(`one of <code>${esc(c.in)}</code>`);
    const key = bits.join('|') + (c.message ?? '');
    if (!bits.length && !c.message) continue;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push(`
        <li>${bits.join(', ')}${c.message ? `<span class="v-msg">${esc(c.message)}</span>` : ''}</li>`);
  }
  return rows.length ? `<ul class="v-constraints">${rows.join('')}\n      </ul>` : '';
}

// A cross-namespace term has no anchor on this page, so it is shown as plain
// text. Only same-namespace targets get a link.
function termRef(iri, namespaceIri) {
  if (!iri.startsWith('http')) return `<code>${esc(iri)}</code>`;
  const local = iri.split('#')[1] ?? iri;
  return iri.startsWith(namespaceIri)
    ? `<a href="#${esc(local)}"><code>${esc(local)}</code></a>`
    : `<code>${esc(local)}</code>`;
}

// "which class is this a property of" was the question the pages could not
// answer. Domain says it; range says what the value is. Absent means the
// repository has no evidence for one, not that the property is unconstrained --
// several are deliberately omitted because they are carried by more than one
// class and rdfs:domain would assert a false equivalence.
function renderSignature(t, namespaceIri) {
  const bits = [];
  if (t.domain) bits.push(`on ${termRef(t.domain, namespaceIri)}`);
  if (t.range) bits.push(`value ${termRef(t.range, namespaceIri)}`);
  return bits.length ? `<p class="v-sig">${bits.join(' &middot; ')}</p>` : '';
}

function renderTerm(t, namespaceIri) {
  const meta = [];
  if (t.kind) meta.push(esc(t.kind));
  if (t.deprecated) meta.push('<strong class="v-dep">deprecated</strong>');
  if (t.lastVersion) meta.push(`<strong class="v-dep">not in the current context</strong>`);
  if (t.jsonKey) meta.push(`JSON key <code>${esc(t.jsonKey)}</code>`);
  if (t.idTyped) meta.push('value is an IRI reference');
  if (t.since) {
    meta.push(t.lastVersion
      ? `<code>${esc(t.since)}</code> to <code>${esc(t.lastVersion)}</code>`
      : `since <code>${esc(t.since)}</code>`);
  }
  if (t.usage) meta.push(`used ${t.usage}&times; in the shipped examples`);

  const derived = !t.label && !t.comment;
  const body = [
    t.comment ? `<p class="v-comment">${esc(t.comment)}</p>` : '',
    !t.comment && t.schemaDescription
      ? `<p class="v-comment">${esc(t.schemaDescription)}
         <span class="v-provenance">from the JSON Schema</span></p>` : '',
    // Through termRef, because a parent is often in another namespace: the aims
    // and surrogate packs subclass core's ValidationResult, AssuranceClaim and
    // ProcessAttestation. Linking those to a same-page anchor produced seven
    // dead links across the two pack pages.
    t.subClassOf
      ? `<p class="v-sub">Subclass of ${termRef(t.subClassOf, namespaceIri)}</p>` : '',
    renderSignature(t, namespaceIri),
    renderConstraints(t.constraints),
    derived && !t.schemaDescription && !t.constraints.length
      ? `<p class="v-none">No definition, constraint, or schema description exists for this term in the repository.</p>` : '',
  ].filter(Boolean).join('\n      ');

  return `
    <div class="v-term${t.deprecated || t.lastVersion ? ' v-term-dep' : ''}" id="${esc(t.name)}">
      <h3><a href="#${esc(t.name)}">${esc(t.label ?? t.name)}</a>
        ${t.label ? `<span class="v-name"><code>${esc(t.name)}</code></span>` : ''}</h3>
      <p class="v-iri"><code>${esc(t.iri)}</code></p>
      ${meta.length ? `<p class="v-meta">${meta.join(' &middot; ')}</p>` : ''}
      ${body}
    </div>`;
}

export function renderVocabPage({ namespace, terms, versions }) {
  const c = coverage(terms);
  const isCore = namespace.key === 'core';

  // Say plainly how well documented this namespace is. A reader arriving from a
  // @vocab lookup deserves to know whether they are reading definitions or
  // derived metadata.
  // Driven by the counts, not by which namespace this is. The earlier version
  // keyed on isCore alone, so it would have kept calling the namespace
  // undocumented at full coverage. Three states, because "most terms defined
  // but not all" is the situation core is actually in and it deserves saying.
  const pct = c.total ? c.labelled / c.total : 0;
  const source = terms.find((t) => t.definedIn)?.definedIn ?? '';
  const sourceLink = source
    ? ` Definitions live in <a href="${REPO_BLOB}/${esc(source)}"><code>${esc(source)}</code></a>.`
    : '';

  // A deprecated term is defined, but it is not a term anyone should reach for.
  // Counting the two together would let "122 of 136 defined" quietly imply 122
  // usable terms, so the banner states them separately wherever any exist.
  const depNote = c.deprecated ? ` ${c.deprecated} of those are deprecated and
    should not be used in new packages.` : '';

  // Terms the newest context dropped are still listed, because their IRIs still
  // resolve and packages written against an older context still use them. The
  // page has to say they are no longer current rather than quietly omit them.
  const dropNote = c.dropped ? `
    <p>${c.dropped} terms below were removed in the current context release.
    They stay documented because their IRIs still resolve and packages pinned to
    an earlier context remain valid; they are simply not part of the vocabulary
    a new package should draw on.</p>` : '';

  const banner = pct === 1 ? `
  <div class="v-banner v-banner-ok">
    <p>All ${c.total} terms in this namespace carry an authored label, and
    ${c.commented} carry a description.${depNote}${sourceLink}</p>${dropNote}
  </div>` : pct >= 0.25 ? `
  <div class="v-banner v-banner-ok">
    <p><strong>${c.labelled} of ${c.total} terms are defined.</strong>${depNote}
    The rest show only what can be derived from the JSON-LD context, the SHACL
    shapes and the JSON Schema, and ${c.bare} have none of those either. Derived
    metadata says how a term is constrained, not what it means.${sourceLink}</p>${dropNote}
  </div>` : `
  <div class="v-banner">
    <p><strong>This namespace is largely undocumented.</strong> Of its
    ${c.total} terms, ${c.labelled} carry an authored definition. Everything
    else below is derived from the JSON-LD context, the SHACL shapes, and the
    JSON Schema, and ${c.bare} terms have none of those either. Derived metadata
    describes how a term is constrained, not what it means.</p>${dropNote}
  </div>`;

  const jsonld = JSON.stringify({
    '@context': {
      rdfs: 'http://www.w3.org/2000/01/rdf-schema#',
      owl: 'http://www.w3.org/2002/07/owl#',
    },
    '@graph': terms.map((t) => ({
      '@id': t.iri,
      ...(t.kind ? { '@type': t.kind === 'Class' ? 'rdfs:Class' : 'rdf:Property' } : {}),
      ...(t.label ? { 'rdfs:label': t.label } : {}),
      ...(t.comment ? { 'rdfs:comment': t.comment } : {}),
      ...(t.subClassOf ? { 'rdfs:subClassOf': { '@id': t.subClassOf } } : {}),
      ...(t.domain ? { 'rdfs:domain': { '@id': t.domain } } : {}),
      ...(t.range ? { 'rdfs:range': t.range.startsWith('xsd:')
        ? { '@id': t.range.replace('xsd:', 'http://www.w3.org/2001/XMLSchema#') }
        : { '@id': t.range } } : {}),
      ...(t.deprecated ? { 'owl:deprecated': true } : {}),
    })),
  }, null, 2);

  const index = terms.map((t) =>
    `<a href="#${esc(t.name)}"><code>${esc(t.name)}</code></a>`).join('\n      ');

  return `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(namespace.label)} vocabulary — UofA</title>
<meta name="description" content="The ${esc(namespace.label)} vocabulary used by UofA evidence packages: ${c.total} terms at ${esc(namespace.iri)}" />
<link rel="stylesheet" href="/_iri/iri.css" />
<link rel="alternate" type="application/ld+json" href="/${esc(namespace.path)}.json" />
<script type="application/ld+json">
${jsonld}
</script>
</head>
<body class="iri-vocab">
<header class="iri-top">
  <a class="iri-home" href="/">Unit of Assurance</a>
  <nav><a href="/reference/identifiers/">All identifiers</a></nav>
</header>
<main data-pagefind-body>
  <p class="iri-eyebrow">Vocabulary</p>
  <h1>${esc(namespace.label)}</h1>
  <p class="iri-id"><code>${esc(namespace.iri)}</code></p>
  <p class="iri-note">${c.total} terms. This is the namespace UofA packages
  expand their property names into. Every term below is addressable as
  <code>${esc(namespace.iri)}&lt;Term&gt;</code>.</p>
${banner}
  <section>
    <h2>Terms</h2>
    <p class="v-index">
      ${index}
    </p>
  </section>
  <section>
${terms.map((t) => renderTerm(t, namespace.iri)).join('\n')}
  </section>
  <section>
    <h2>Provenance</h2>
    <p class="iri-note">Generated from the JSON-LD context files
    (${versions.join(', ')}), the SHACL shapes under <code>packs/*/shapes/</code>,
    and the JSON Schema. Term coverage: ${c.labelled} labelled,
    ${c.commented} with a description, ${c.constrained} carrying SHACL
    constraints, ${c.used} used by the shipped example packages,
    ${c.domained} declaring the class they belong to.</p>
    <p class="iri-note">A property with no declared class is one the repository
    has no single answer for: either nothing uses it yet, or it is carried by
    several classes at once and <code>rdfs:domain</code> would assert that every
    carrier is the same kind of thing.</p>
  </section>
</main>
<footer class="iri-foot">
  <p>This page is generated from the repository. The shapes and context files
  are the authority.</p>
</footer>
</body>
</html>
`;
}

export function vocabTwin(namespace, terms) {
  return {
    '@context': {
      rdfs: 'http://www.w3.org/2000/01/rdf-schema#',
      rdf: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
      owl: 'http://www.w3.org/2002/07/owl#',
    },
    '@id': namespace.iri.replace(/#$/, ''),
    '@graph': terms.map((t) => ({
      '@id': t.iri,
      ...(t.kind ? { '@type': t.kind === 'Class' ? 'rdfs:Class' : 'rdf:Property' } : {}),
      ...(t.label ? { 'rdfs:label': t.label } : {}),
      ...(t.comment ? { 'rdfs:comment': t.comment } : {}),
      ...(t.subClassOf ? { 'rdfs:subClassOf': { '@id': t.subClassOf } } : {}),
      ...(t.domain ? { 'rdfs:domain': { '@id': t.domain } } : {}),
      ...(t.range ? { 'rdfs:range': t.range.startsWith('xsd:')
        ? { '@id': t.range.replace('xsd:', 'http://www.w3.org/2001/XMLSchema#') }
        : { '@id': t.range } } : {}),
      ...(t.deprecated ? { 'owl:deprecated': true } : {}),
      ...(t.since ? { 'uofa:sinceContextVersion': t.since } : {}),
    })),
  };
}

export { coverage };
