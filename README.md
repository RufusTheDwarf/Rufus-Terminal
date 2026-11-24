# Rufus Terminal

**v0.3.0 — Build. Learn. Share. Improve.**

Personal developer portfolio by [RufusTheDwarf](https://github.com/RufusTheDwarf).
A static, multi-page website presenting infrastructure, networking, security,
software development, databases, games and technical documentation.

## Quick start (Windows)

The `public/` directory is already generated and can be deployed as-is. No Node.js,
Python or dependencies are required in production. Do not deploy `public/index.html`
alone: the other pages and shared assets are required.

To preview locally with Python 3.10 or later:

```powershell
py -m http.server 8000 --directory public
```

Open <http://localhost:8000/>. Use Ctrl+C to stop the server.
The simple Python server does not reproduce Cloudflare-specific headers or 404 behavior.

## Structure

```text
public/                    # Ready-to-deploy static output
  index.html
  a-propos/index.html
  projets/index.html
  projets/<slug>/index.html
  jeux/index.html
  guides/index.html
  devlog/index.html
  assets/style.css
  assets/site.js
  assets/social-card.png
  favicon.svg
  favicon.ico
  apple-touch-icon.png
  404.html
  robots.txt
  sitemap.xml
  _headers
src/                       # Editable source files
  projects.json
  style.css
  site.js
tools/                     # Build and checks
  build.py
  check.py
  browser_check.py
site.json                  # Canonical origin and project identity
wrangler.jsonc             # Cloudflare Workers static assets
lighthouserc.json          # Lighthouse CI targets
.github/workflows/quality.yml
```

## Editing and regenerating

- Project descriptions and relationships: `src/projects.json`.
- Shared layout, homepage, sections and metadata: `tools/build.py`.
- Styles and interactions: `src/style.css`, `src/site.js`.
- Canonical URL and version: `site.json`.
- Social card and favicon are original static assets in `public/`.

After editing, regenerate and check:

```powershell
py tools/build.py
py tools/check.py
node --check public/assets/site.js
```

The site is generated with the Python standard library. The generated HTML is formatted
and committed for direct Cloudflare deployment. Avoid editing generated output directly;
the next build will overwrite those changes. If a project is removed, explicitly remove
its old generated folder from `public/projets/`, then rerun the checker.
The catalogue is editorial, not a live GitHub API feed: add new entries deliberately,
including accurate status, links and content. Do not expose private repositories.

## Cloudflare Workers

Keep the existing Worker name and static assets directory. The supplied `wrangler.jsonc`
uses folder-index routing and custom 404 handling. If your deployment uses a different
name, domain or compatibility date, merge the configuration rather than overwriting it.
For Git integration, keep the existing deployment command. For manual deployment with
Wrangler installed and authenticated, use `npx wrangler deploy` from the repository root.

The existing URL is assumed to be the canonical origin:
`https://rufus-terminal-preview.rutsumello.workers.dev`.
If it is only a temporary preview, set `siteUrl` in `site.json` to the real public origin
before publishing or submitting a sitemap, then rerun `py tools/build.py`.
Avoid indexing equivalent preview and production sites.

## SEO and accessibility

- Unique titles, descriptions and canonical URLs for all 22 indexable pages.
- XML sitemap and robots.txt, real project URLs, breadcrumbs and internal links.
- ProfilePage, Person, WebSite, WebPage and BreadcrumbList structured data.
- Open Graph and Twitter/X image metadata, local favicon assets.
- Semantic HTML, keyboard focus, skip link, no-JS content, fluid layout.
- Shared local CSS and JavaScript; no third-party runtime requests.
- Security headers for Cloudflare static assets, including CSP.

After deployment, verify actual HTTP statuses (including a nonexistent route), response
headers, canonical URLs and sitemap. Register the canonical site in Google Search
Console and Bing Webmaster Tools, submit the sitemap and check indexing. Verify live
performance with PageSpeed Insights. Lighthouse CI targets are goals, not measured
scores; the workflow has not run in GitHub Actions yet. Static technical SEO does not
guarantee indexing or ranking. Publish useful original technical content and maintain links.

References:
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.cloudflare.com/workers/static-assets/routing/static-site-generation/
- https://developers.cloudflare.com/workers/static-assets/headers/
- https://github.com/GoogleChrome/lighthouse-ci

## Local validation

`tools/check.py` checks generated pages, unique metadata, sitemap, heading hierarchy,
IDs, JSON-LD syntax and internal links. `tools/browser_check.py` optionally tests
Chromium rendering and client-side interactions using isolated documents. Install
Playwright only for this development check:

```powershell
py -m pip install playwright
py -m playwright install chromium
py tools/browser_check.py
```

The browser test inlines local assets for the test only; it does not prove HTTP routing,
CSP enforcement or live crawler behavior. GitHub Actions is configured for validation
and Lighthouse measurement. Before deployment, review the changes and keep your existing
LICENSE, SECURITY.md and Git history. Use the existing trusted commit signing identity.
