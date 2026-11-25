# Design decisions // v0.6.0

The external reviews supplied by the maintainer were treated as suggestions, not as a replacement for the established visual brief.

- Keep the forest and cream-sage themes, retro SVG illustrations, full-width layout and the interactive terminal.
- Use one glass surface, the terminal. Navigation, application showcase and project directory no longer use blur.
- Keep a single slow topographic animation on the homepage. No aurora animation or animated grain. Honor reduced-motion preferences and the manual pause control.
- Replace repeated project cards with a directory of entries. Keep RUX separate as a featured application with its dedicated page and download links.
- Use compact skill rows, an asymmetric hero, restrained headings and a combined resources section.
- Remove decorative status labels and generic slogans from the homepage. Use real version information, links and factual first-person copy without inventing personal anecdotes.
- Keep the existing static site generator, URLs, sitemap, metadata, security settings and catalogue audit workflow.

Extract the archive into the repository root, merge directories, rebuild with `python tools/build.py`, then run `python tools/check.py`. Review the diff before committing with your existing trusted signing identity. The update contains the restored hidden configuration files; the inspected remote tree did not contain the GitHub workflows.
