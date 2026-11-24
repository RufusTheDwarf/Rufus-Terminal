# Validation v0.3.0

Executed in the preparation environment:

- `python tools/build.py`: 22 indexable pages and one 404 page.
- `python tools/check.py`: 23 HTML pages, 16 project pages and 521 internal link/asset references checked.
- `node --check public/assets/site.js`: passed.
- `python tools/browser_check.py --chromium /usr/bin/chromium`: 115 isolated Chromium page/viewport checks (23 pages × 5 widths: 320, 375, 768, 1024, 1440 px), no horizontal overflow. Search, filters, terminal help/whoami/clear, command history, safe text rendering and no-JS catalogue passed.

Not measured or not tested end-to-end: live HTTP routing and CSP headers (local HTTP navigation blocked in the preparation environment), Lighthouse scores, full WCAG compliance, live Google/Bing indexing, deployment and external link availability. GitHub Actions and the Cloudflare configuration are supplied but not executed remotely.
