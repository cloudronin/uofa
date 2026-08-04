// Pure HTML/JSON emission for identifier pages. No I/O, no globals, so it can
// be exercised with `node --test`.
//
// Two page kinds:
//   renderNodePage — an identifier a package actually describes
//   renderStubPage — an identifier packages reference but nobody describes
//
// The stub is deliberately thin. These URLs sit in the uofa.net namespace and
// therefore look authoritative, so they must not assert anything the corpus
// does not actually say. The machine twin uses @reverse only: inventing a
// schema:name from a URL slug would fabricate a claim at an address that
// appears to speak for the project.

import { ORIGIN } from './iri-walk.mjs';

const REPO_BLOB = 'https://github.com/cloudronin/uofa/blob/main';

export const esc = (s) =>
  String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const VOCAB = 'https://uofa.net/vocab#';

/** uofa:hasWeakener for display; full IRI kept for the link. */
export const shortPredicate = (iri) =>
  iri.startsWith(VOCAB) ? `uofa:${iri.slice(VOCAB.length)}`
  : iri.startsWith('https://uofa.net/vocab/aims#') ? `aims:${iri.split('#')[1]}`
  : iri.startsWith('https://uofa.net/vocab/surrogate#') ? `surr:${iri.split('#')[1]}`
  : iri.replace('http://www.w3.org/ns/prov#', 'prov:')
       .replace('http://purl.org/dc/terms/', 'dct:')
       .replace('https://schema.org/', 'schema:');

const localPath = (iri) => '/' + iri.slice(ORIGIN.length).replace(/\/+$/, '') + '/';

const linkIri = (iri, known) => {
  if (typeof iri !== 'string' || !iri.startsWith(ORIGIN) || iri.includes('#')) {
    return `<code>${esc(iri)}</code>`;
  }
  const cls = known ? 'iri-link' : 'iri-link iri-link-stub';
  return `<a class="${cls}" href="${esc(localPath(iri))}"><code>${esc(iri)}</code></a>`;
};

// What a referring predicate implies about an undescribed identifier. Derived
// from how the corpus uses each property; kept small and explicit rather than
// guessed, and rendered as "inferred", never as fact.
const TYPE_FROM_PREDICATE = {
  [`${VOCAB}bindsRequirement`]: 'uofa:Requirement',
  [`${VOCAB}bindsClaim`]: 'uofa:AssuranceClaim',
  [`${VOCAB}bindsModel`]: 'uofa:Model',
  [`${VOCAB}bindsDataset`]: 'uofa:Dataset',
  [`${VOCAB}hasValidationResult`]: 'uofa:ValidationResult',
  [`${VOCAB}criteriaSet`]: 'uofa:AcceptanceCriteria',
  [`${VOCAB}comparedAgainst`]: 'uofa:Dataset',
  [`${VOCAB}actor`]: 'prov:Agent',
  'http://www.w3.org/ns/prov#wasAttributedTo': 'prov:Agent',
  'http://www.w3.org/ns/prov#wasGeneratedBy': 'prov:Activity',
};

export function inferType(inboundRefs) {
  const guesses = new Set(
    inboundRefs.map((r) => TYPE_FROM_PREDICATE[r.predicate]).filter(Boolean)
  );
  return guesses.size === 1 ? [...guesses][0] : null;
}

const humanise = (id) =>
  id.split('/').filter(Boolean).pop().replace(/[-_]/g, ' ')
    .replace(/^\w/, (c) => c.toUpperCase());

function shell({ title, description, bodyClass, main, jsonld, jsonTwin }) {
  return `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}" />
<link rel="stylesheet" href="/_iri/iri.css" />
<link rel="alternate" type="application/ld+json" href="${esc(jsonTwin)}" />
<script type="application/ld+json">
${jsonld}
</script>
</head>
<body class="${bodyClass}">
<header class="iri-top">
  <a class="iri-home" href="/">Unit of Assurance</a>
  <nav><a href="/reference/identifiers/">All identifiers</a></nav>
</header>
<main data-pagefind-body>
${main}
</main>
<footer class="iri-foot">
  <p>This page describes an identifier used inside UofA evidence packages. The
  record it comes from is the authority; this page is generated from it.</p>
</footer>
</body>
</html>
`;
}

/** Split a node's own keys into literal fields and outbound IRI references. */
function partition(node, resolve) {
  const literals = [];
  const refs = [];
  for (const [key, value] of Object.entries(node)) {
    if (key === 'id' || key === '@id' || key === '@context') continue;
    const predicate = resolve(key);
    const items = Array.isArray(value) ? value : [value];
    for (const item of items) {
      if (typeof item === 'string' && item.startsWith(ORIGIN) && !item.includes('#')) {
        refs.push({ predicate, value: item });
      } else if (item !== null && typeof item === 'object') {
        const nested = item.id ?? item['@id'];
        if (typeof nested === 'string' && nested.startsWith(ORIGIN)) {
          refs.push({ predicate, value: nested });
        } else {
          literals.push({ predicate, value: JSON.stringify(item), isJson: true });
        }
      } else {
        literals.push({ predicate, value: item });
      }
    }
  }
  return { literals, refs };
}

export function renderNodePage({ id, node, sourceFile, resolve, inbound, isKnown }) {
  const { literals, refs } = partition(node, resolve);
  const typeLabel = node.type ?? node['@type'] ?? null;

  const literalRows = literals.map(({ predicate, value, isJson }) => `
      <tr>
        <td class="k"><code>${esc(shortPredicate(predicate))}</code></td>
        <td class="v">${isJson ? `<pre>${esc(value)}</pre>` : esc(value)}</td>
      </tr>`).join('');

  const refRows = refs.map(({ predicate, value }) => `
      <tr>
        <td class="k"><code>${esc(shortPredicate(predicate))}</code></td>
        <td class="v">${linkIri(value, isKnown(value))}</td>
      </tr>`).join('');

  const inboundRows = (inbound ?? []).map((r) => `
      <tr>
        <td class="v">${linkIri(r.subject, isKnown(r.subject))}</td>
        <td class="k"><code>${esc(shortPredicate(r.predicate))}</code></td>
        <td class="k"><a href="${REPO_BLOB}/${esc(r.sourceFile)}">${esc(r.sourceFile.split('/').pop())}</a></td>
      </tr>`).join('');

  const verify = (node.hash || node.signature) ? `
  <section class="iri-verify">
    <h2>Integrity</h2>
    <p>This identifier names a signed package. Verify it yourself against the
    record in the repository.</p>
    <pre class="iri-cmd">uofa check --build ${esc(sourceFile)}</pre>
  </section>` : '';

  const main = `
  <p class="iri-eyebrow">${esc(typeLabel ? String(typeLabel) : 'Identifier')}</p>
  <h1>${esc(humanise(id))}</h1>
  <p class="iri-id"><code>${esc(id)}</code></p>
  <p class="iri-source">Described in
    <a href="${REPO_BLOB}/${esc(sourceFile)}"><code>${esc(sourceFile)}</code></a>
  </p>
${literalRows ? `
  <section>
    <h2>Fields</h2>
    <table class="iri-table"><tbody>${literalRows}
    </tbody></table>
  </section>` : ''}
${refRows ? `
  <section>
    <h2>References</h2>
    <table class="iri-table"><tbody>${refRows}
    </tbody></table>
  </section>` : ''}
${inboundRows ? `
  <section>
    <h2>Referenced by</h2>
    <p class="iri-note">Which records point at this identifier, and through which
    property. This relationship is not written down anywhere in the packages
    themselves; it is derived by indexing the whole corpus.</p>
    <table class="iri-table"><thead><tr><th>Record</th><th>Property</th><th>Source</th></tr></thead>
    <tbody>${inboundRows}
    </tbody></table>
  </section>` : ''}
${verify}
`;

  return shell({
    title: `${humanise(id)} — UofA identifier`,
    description: `The UofA package node ${id}, described from ${sourceFile}.`,
    bodyClass: 'iri-node',
    main,
    jsonld: JSON.stringify(node, null, 2),
    jsonTwin: localPath(id).replace(/\/$/, '') + '.json',
  });
}

/**
 * Machine twin for an undescribed identifier: @reverse and nothing else, so the
 * document asserts only what the corpus actually states about it.
 */
export const stubTwin = (id, inbound) => {
  const inferred = inferType(inbound);
  return {
    '@id': id,
    ...(inferred ? { 'uofa:inferredType': inferred } : {}),
    'uofa:descriptionStatus': 'referenced-only',
    '@reverse': inbound.reduce((acc, r) => {
      (acc[shortPredicate(r.predicate)] ??= []).push({ '@id': r.subject });
      return acc;
    }, {}),
  };
};

export function renderStubPage({ id, inbound, isKnown }) {
  const inferred = inferType(inbound);
  const rows = inbound.map((r) => `
      <tr>
        <td class="v">${linkIri(r.subject, isKnown(r.subject))}</td>
        <td class="k"><code>${esc(shortPredicate(r.predicate))}</code></td>
        <td class="k"><a href="${REPO_BLOB}/${esc(r.sourceFile)}">${esc(r.sourceFile.split('/').pop())}</a></td>
      </tr>`).join('');

  const main = `
  <p class="iri-eyebrow">Referenced only</p>
  <h1>${esc(humanise(id))}</h1>
  <p class="iri-id"><code>${esc(id)}</code></p>
  <div class="iri-banner">
    <p><strong>Referenced but not described.</strong> No package in this
    repository defines this identifier. Everything below is inferred from how
    other records refer to it.</p>
  </div>
${inferred ? `
  <section>
    <h2>Inferred type</h2>
    <p>The referring property implies <code>${esc(inferred)}</code>. That is an
    inference from usage, not a statement the record makes.</p>
  </section>` : ''}
  <section>
    <h2>Referenced by</h2>
    <table class="iri-table"><thead><tr><th>Record</th><th>Property</th><th>Source</th></tr></thead>
    <tbody>${rows}
    </tbody></table>
  </section>
`;

  return shell({
    title: `${humanise(id)} — referenced only`,
    description: `${id} is referenced by UofA packages but not described by any of them.`,
    bodyClass: 'iri-stub',
    main,
    jsonld: JSON.stringify(stubTwin(id, inbound), null, 2),
    jsonTwin: localPath(id).replace(/\/$/, '') + '.json',
  });
}
