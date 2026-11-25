# Update // v0.4.1

Extract the archive into the repository root, merging directories. Review changes before staging. Preserve `.git`, `LICENSE`, `SECURITY.md`, `.gitignore` and `wrangler.jsonc`. The archive includes the v0.4.0 theme update, the new catalogue, the README and the missing quality and formatting configuration. If local files have changed, merge rather than blindly replacing them.

## Maintenance

Edit `src/projects.json` for projects, `src/style.css` for visual styles, `src/site.js` for interactions, `src/theme.js` for theme setup and `tools/build.py` for HTML templates. Generated files in `public/` are not the source of truth. JSON is expanded and CSS rules are separated into readable blocks. EditorConfig and Prettier settings provide consistent formatting for supported source files. Do not format the generated output independently of the build.

## Checks

```powershell
py tools/build.py
py tools/check.py
py -m unittest discover -s tools -p 'test_*.py'
node --check public/assets/site.js
node --check public/assets/theme.js
```

`py tools/sync_github.py` compares public GitHub repositories without writing to the catalogue or creating commits. The generated report can be discarded after review. Changes to the catalogue should be regenerated and committed with a trusted signing identity.
