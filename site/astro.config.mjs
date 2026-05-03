// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import toml from 'toml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pyproject = toml.parse(
  readFileSync(resolve(__dirname, '../pyproject.toml'), 'utf-8')
);
const uofaVersion = pyproject.project.version;

// https://astro.build/config
export default defineConfig({
  site: 'https://uofa.net',
  vite: {
    define: {
      __UOFA_VERSION__: JSON.stringify(`v${uofaVersion}`),
    },
  },
  integrations: [
    starlight({
      title: 'UofA',
      description:
        'Machine-verifiable credibility evidence for regulated computational simulation.',
      logo: {
        src: './src/components/hex-shield.svg',
        replacesTitle: false,
      },
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/cloudronin/uofa',
        },
      ],
      customCss: ['./src/styles/custom.css'],
      // Dark-only — light mode is hidden via CSS in custom.css
      // (If light mode is later desired, remove the toggle hide and add light tokens.)
      head: [
        {
          tag: 'script',
          content: `
            // Lock dark theme on load (before paint)
            try {
              localStorage.setItem('starlight-theme', 'dark');
              document.documentElement.dataset.theme = 'dark';
            } catch (_) {}
          `,
        },
        {
          tag: 'meta',
          attrs: { name: 'theme-color', content: '#0c0d0e' },
        },
      ],
      sidebar: [
        {
          label: 'Get Started',
          items: [
            { label: 'Overview', link: '/start/' },
            { label: 'Live demo (Morrison)', link: '/demo/' },
            { label: 'Install', link: '/start/install/' },
            { label: 'Your first UofA', link: '/start/first-uofa/' },
            { label: 'Excel on-ramp', link: '/start/from-excel/' },
          ],
        },
        {
          label: 'Concepts',
          items: [
            { label: 'Overview', link: '/concepts/' },
            { label: 'What a UofA is', link: '/concepts/uofa/' },
            { label: 'C1 / C2 / C3', link: '/concepts/contributions/' },
            { label: 'Weakeners', link: '/concepts/weakeners/' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'Overview', link: '/reference/' },
            { label: 'CLI commands', link: '/reference/cli/' },
            { label: 'Weakener catalog', link: '/reference/catalog/' },
          ],
        },
        {
          label: 'Research',
          items: [
            { label: 'Overview', link: '/research/' },
            { label: 'NAFEMS 2026', link: '/research/nafems-2026/' },
            { label: 'Feedback', link: '/feedback/' },
          ],
        },
        {
          label: 'Project docs',
          collapsed: true,
          items: [
            { label: 'Onboarding', link: '/docs/onboarding/' },
            { label: 'Architecture', link: '/docs/architecture/' },
            { label: 'Design', link: '/docs/design/' },
            { label: 'Profiles', link: '/docs/profiles/' },
            { label: 'Repo layout', link: '/docs/repo-layout/' },
            { label: 'LLM configuration', link: '/docs/llm-config/' },
            { label: 'Security model', link: '/docs/security/' },
            { label: '--explain flag', link: '/docs/explain/' },
            { label: 'Adversarial generation', link: '/docs/adversarial/' },
          ],
        },
      ],
      components: {
        // Override the default home page hero with our terminal hero
        // (Starlight's splash template is used via the homepage frontmatter)
        //
        // Footer override appends the site-wide SiteFooter (license,
        // citation, contact, build SHA) below Starlight's prev/next nav
        // on every docs page. The splash homepage doesn't use this slot,
        // so it imports SiteFooter directly in index.mdx.
        Footer: './src/components/StarlightFooterWithSite.astro',
      },
      lastUpdated: false,
      pagination: true,
      editLink: {
        baseUrl:
          'https://github.com/cloudronin/uofa/edit/main/site/',
      },
    }),
  ],
});
