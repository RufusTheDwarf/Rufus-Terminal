# Validation // Terminal v0.5.0

## Executed checks

- `python tools/build.py`: 25 indexable pages and one custom 404 page.
- `python tools/check.py`: 26 HTML pages, 18 catalogue entries (17 projects and one application), 649 internal link and asset references.
- `node --check public/assets/site.js` and `node --check public/assets/theme.js`: passed.
- `python -m unittest discover -s tools -p 'test_*.py'`: three catalogue audit tests passed.
- `python tools/browser_check.py --chromium /usr/bin/chromium`: 260 isolated Chromium checks, covering 26 pages, five viewport widths (320, 375, 768, 1024 and 1440 px) and two themes. No horizontal overflow. Catalogue search and filters, theme switching, motion pause, terminal commands and history, safe text handling, application links and no-JavaScript catalogue passed.
- The screenshot test inlines the local map and illustration assets to render the actual stylesheet and document without a local HTTP server.

## Migration checks

The Worker is configured as `terminal`, with the canonical origin `https://terminal.rutsumello.workers.dev`. The build removes the former RUX project page and generates redirect rules for its replacement at `/apps/rux-netmap/`.

## Not verified end to end

Live Cloudflare deployment, redirects and security headers, persistence across real HTTP navigations, live GitHub Actions, Lighthouse scores, complete WCAG compliance, and search-engine indexing. Existing project descriptions are retained from v0.4.1; this update is not a fresh audit of every repository or release.
