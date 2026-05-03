#!/usr/bin/env node
// Sync external markdown (repo root README, curated docs/*.md) into
// site/src/content/docs/ as Starlight pages. Runs at build time;
// outputs are gitignored.
//
// Edit the CONFIG map below to add or remove mirrored pages.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = resolve(__dirname, '..');
const REPO_ROOT = resolve(SITE_ROOT, '..');
const OUT_DIR = join(SITE_ROOT, 'src/content/docs');

const REPO_BLOB = 'https://github.com/cloudronin/uofa/blob/main';
const REPO_RAW = 'https://raw.githubusercontent.com/cloudronin/uofa/main';

const CONFIG = {
  'README.md':              { title: 'Project README',          slug: 'readme',              sidebarHidden: true },
  'docs/architecture.md':   { title: 'Architecture',            slug: 'docs/architecture'   },
  'docs/design.md':         { title: 'Design',                  slug: 'docs/design'         },
  'docs/onboarding.md':     { title: 'Onboarding',              slug: 'docs/onboarding'     },
  'docs/security.md':       { title: 'Security model',          slug: 'docs/security'       },
  'docs/profiles.md':       { title: 'Profiles',                slug: 'docs/profiles'       },
  'docs/llm-config.md':     { title: 'LLM configuration',       slug: 'docs/llm-config'     },
  'docs/explain.md':        { title: '--explain flag',          slug: 'docs/explain'        },
  'docs/adversarial.md':    { title: 'Adversarial generation',  slug: 'docs/adversarial'    },
  'docs/repo-layout.md':    { title: 'Repo layout',             slug: 'docs/repo-layout'    },
};

const SLUG_BY_PATH = Object.fromEntries(
  Object.entries(CONFIG).map(([p, m]) => [p, `/${m.slug}/`])
);

function stripFrontmatter(text) {
  return text.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
}

function escapeYaml(s) {
  return s.replace(/'/g, "''");
}

function normalizeRelative(url, sourceDir) {
  const cleaned = url.replace(/^\.\//, '');
  if (sourceDir === '.' || sourceDir === '') return cleaned;
  return join(sourceDir, cleaned).replace(/\\/g, '/');
}

function rewriteLinks(body, sourcePath) {
  const sourceDir = dirname(sourcePath);
  return body.replace(/(!?)(\[[^\]]*\])\(([^)\s]+)(\s+"[^"]*")?\)/g, (match, bang, label, url, title) => {
    if (/^([a-z]+:|#|mailto:)/i.test(url)) return match;
    const normalized = normalizeRelative(url, sourceDir);
    const [pathPart, ...rest] = normalized.split(/([#?])/);
    const tail = rest.join('');

    if (bang === '!') {
      return `${bang}${label}(${REPO_RAW}/${pathPart}${tail}${title ?? ''})`;
    }
    if (SLUG_BY_PATH[pathPart]) {
      return `${label}(${SLUG_BY_PATH[pathPart]}${tail}${title ?? ''})`;
    }
    return `${label}(${REPO_BLOB}/${pathPart}${tail}${title ?? ''})`;
  });
}

let written = 0;
let skipped = 0;
for (const [sourcePath, meta] of Object.entries(CONFIG)) {
  const absSource = join(REPO_ROOT, sourcePath);
  if (!existsSync(absSource)) {
    console.warn(`sync-readmes: missing source ${sourcePath} — skipped`);
    skipped++;
    continue;
  }

  const raw = readFileSync(absSource, 'utf8');
  const body = rewriteLinks(stripFrontmatter(raw), sourcePath);

  const sidebarYaml = meta.sidebarHidden ? '\nsidebar:\n  hidden: true' : '';
  const frontmatter =
    `---\n` +
    `title: '${escapeYaml(meta.title)}'\n` +
    `description: 'Mirrored from \`${sourcePath}\` in the uofa repo. Edits should be made there.'\n` +
    `editUrl: ${REPO_BLOB}/${sourcePath}` +
    sidebarYaml +
    `\n---\n\n`;

  const banner =
    `:::note[Mirrored page]\n` +
    `This page is mirrored from [\`${sourcePath}\`](${REPO_BLOB}/${sourcePath}) in the uofa repo. ` +
    `Edits made here are overwritten on the next build — edit the source instead.\n` +
    `:::\n\n`;

  const outPath = join(OUT_DIR, `${meta.slug}.md`);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, frontmatter + banner + body);
  written++;
}

console.log(`sync-readmes: wrote ${written} mirrored page(s); skipped ${skipped}`);
