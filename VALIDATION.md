# Validation // Rufus Terminal v0.4.1

Executed in the preparation environment:

- `python tools/build.py`: 24 indexable pages and one 404 page.
- `python tools/check.py`: 25 HTML pages, 18 project pages and 598 internal link/asset references checked.
- `node --check public/assets/site.js` and `node --check public/assets/theme.js`: passed.
- `python -m unittest discover -s tools -p 'test_*.py'`: three catalogue audit tests passed, including pagination and private-repository exclusion.
- `python tools/browser_check.py --chromium /usr/bin/chromium`: 250 isolated page/viewport/theme checks passed (25 pages, five widths, two themes). Search, filters, terminal, history, theme switching and catalogue without JavaScript passed.
- GitHub connector: 19 public repositories including the profile repository; 18 catalogue projects. The RUX v1.1.0 release lists `RUX.exe` and `RUX.exe.sha256`.

Not executed end-to-end: the scheduled workflow, live REST request from the local audit script, live Cloudflare routing, HTTP security headers, Lighthouse scores, full WCAG audit and search engine indexing. Existing project descriptions are retained; matching the repository list is not a new audit of every release or README.
