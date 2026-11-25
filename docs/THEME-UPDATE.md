# Retro Glass / Sage Day (v0.4.0)

Merge this update into the root of the existing Rufus-Terminal v0.3.0 repository. Do not delete the existing directories or replace them wholesale: merge folders and overwrite matching files. The archive contains generated HTML for all pages, theme assets, editable sources, the shared generator, and the updated browser checker. It intentionally excludes README.md, LICENSE, SECURITY.md, .git, workflows, project data, sitemap, robots.txt and Cloudflare configuration, which remain unchanged.

## Preview and update

```powershell
py tools/build.py
py tools/check.py
py -m http.server 8000 --directory public
```

Open http://localhost:8000/ in your browser. The theme selector offers Auto (system setting), Sombre (forest green glass), and Clair (cream and sage green). Manual choices are saved in localStorage when available. Without JavaScript the system preference is used and the content is still accessible.

The updated SVG artwork is decorative. Both themes use local assets, no external fonts, no animated scanlines, no tracker, and no extra production dependencies. The shared social preview card remains unchanged.

## Source files

- `src/style.css`: palettes, layout and glass styling.
- `src/theme.js`: early saved-theme initialization.
- `src/site.js`: theme selection and existing interactions.
- `src/forest-terminal.svg`, `src/day-terminal.svg`: custom artwork.
- `tools/build.py`: shared templates; copies assets into `public/assets/`.
- `site.json`: site version.

The generated files in `public/` can be deployed directly. Rebuild after editing sources. If you have modified the generator or catalogue locally since v0.3.0, review and merge your changes instead of blindly overwriting.

## Verification

```powershell
node --check public/assets/site.js
node --check public/assets/theme.js
py tools/check.py
# Optional browser checks (requires Playwright and Chromium):
py tools/browser_check.py
```

Then review `git diff`, commit with your usual signing key, and push. Verify the deployed Cloudflare site, storage persistence across page loads, actual HTTP headers and Lighthouse separately.
