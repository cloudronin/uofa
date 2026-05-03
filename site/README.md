# uofa-site

Source for [uofa.net](https://uofa.net), the documentation site for the [Unit of Assurance](https://github.com/cloudronin/uofa) tool.

Built with [Astro](https://astro.build) and [Starlight](https://starlight.astro.build). Deployed to GitHub Pages.

## Local development

```bash
npm install
npm run dev
```

The dev server runs at `http://localhost:4321`. Changes to `src/` hot-reload.

## Build

```bash
npm run build
```

Produces a static site in `dist/`.

## Project structure

```
uofa-site/
├── astro.config.mjs            # Starlight config: nav, sidebar, social links
├── public/
│   ├── CNAME                   # uofa.net (for GitHub Pages custom domain)
│   └── favicon.svg             # Hex shield favicon
├── src/
│   ├── components/
│   │   ├── hex-shield.svg      # Logo used in the Starlight header
│   │   ├── Hero.astro          # Homepage hero with terminal block
│   │   ├── Pillars.astro       # 4-card grid (C1, C2, C3, Standards)
│   │   └── DemoStrip.astro     # Morrison demo strip
│   ├── content/
│   │   ├── docs/
│   │   │   ├── index.mdx       # Homepage (uses splash template)
│   │   │   ├── start/          # Get Started section
│   │   │   ├── concepts/       # Concepts section
│   │   │   ├── reference/      # Reference section
│   │   │   └── research/       # Research section
│   │   └── content.config.ts
│   └── styles/
│       └── custom.css          # Theme overrides — design tokens, fonts, components
└── .github/
    └── workflows/
        └── deploy.yml          # GitHub Pages deployment
```

## Adding a page

Drop a markdown file under `src/content/docs/<section>/<page>.md`:

```markdown
---
title: Page title
description: One-sentence description for SEO and metadata.
---

Page content in Markdown.
```

Then add the page to the `sidebar` array in `astro.config.mjs`:

```js
{
  label: 'Concepts',
  items: [
    // ...
    { label: 'New page', link: '/concepts/new-page/' },
  ],
}
```

## Editing the homepage

The homepage is `src/content/docs/index.mdx`. It uses Starlight's `splash` template and embeds three custom Astro components: `Hero`, `Pillars`, and `DemoStrip`. Edit the components under `src/components/` to change hero copy, card text, or terminal output.

## Theme

The dark theme is locked. The Starlight light/dark toggle is hidden via CSS in `src/styles/custom.css`. To re-enable a light mode, remove the `starlight-theme-select { display: none }` rule and add light-mode token values under `:root[data-theme='light']`.

Design tokens are at the top of `custom.css`:

```css
--uofa-bg:           #0c0d0e;     /* warm near-black */
--uofa-accent:       #d4a35a;     /* refined amber / brass / wax seal */
--uofa-text:         #e8e6e1;     /* warm off-white */
```

Fonts are loaded from Google Fonts: Fraunces (display serif), IBM Plex Sans (body), IBM Plex Mono (code).

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site and deploys to GitHub Pages.

For the custom `uofa.net` domain to work, the repository's GitHub Pages settings must point at the deployed environment, and the DNS for `uofa.net` must have a CNAME record pointing at `<owner>.github.io`. The `public/CNAME` file is checked into the repo so GitHub Pages preserves the custom domain across deployments.

## License

Site content: CC0 1.0. Code: MIT.
