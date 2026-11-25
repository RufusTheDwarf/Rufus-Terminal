# Validation // Terminal v0.7.0

## Executed checks

- Python generator and static checker: 28 HTML pages, 27 indexable URLs, 18 catalogue entries (17 projects and one application), 762 internal link and asset references.
- JavaScript syntax: workspace, shared site and theme scripts.
- Existing catalogue sync unit tests: 3 passed.
- Chromium isolated document checks: 280 page/viewport combinations, both themes, widths 320, 375, 768, 1024 and 1440 px. Search, filters, theme switching, navigation terminal, history and no-JavaScript catalogue.
- Workspace Chromium test: shell commands, folder and text-file creation, shared notepad/editor, actual JavaScript execution, opaque worker origin, IndexedDB denied, safe text rendering, trash restoration, JSON export and session reset.

## Scope and limitations

This is a cumulative update of the v0.6.0 archive. The remote tree returned by GitHub at preparation time was `f51ea7a632c88fc7a5e035770f87215476867939`, with the v0.5.0 source version; no remote modification was made. Check for local changes before extraction. Existing public project records were retained except for Terminal's own description and version.

The local environment blocks HTTP navigation and external DNS. Python runtime loading, micropip package installation, real Wikipedia searches, live Cloudflare headers and redirects, cross-page storage, deployment, live CI and Lighthouse metrics are not verified end to end. The workspace is a browser application with virtual files, not a complete Linux OS. See docs/WORKSPACE.md for the integration checks and limitations.
