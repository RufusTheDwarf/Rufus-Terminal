# Terminal v0.5.0 // Installation

This cumulative update targets the public repository tree `5a6c49ce9c51d921ea894efd7353bee683d4e459`.

1. Check `git status` and save any local changes before extracting the archive into the repository root. Merge folders and replace the files supplied in the archive. Keep the existing `.git`, `LICENSE` and `SECURITY.md`.
2. Run `py tools/build.py`. This step is required because extraction alone cannot delete the previous generated `public/projets/rux-netmap/index.html` file.
3. Run `py tools/check.py` and preview with `py -m http.server 8000 --directory public`. The Python preview does not implement Cloudflare-specific redirects or security headers.
4. Review `git status` and `git diff`, then create a signed commit and push it.
5. Verify the Worker named `terminal`, Git integration, the canonical URL, and HTTP redirects in Cloudflare.

The new site origin is `https://terminal.rutsumello.workers.dev`. If the old Worker is still reachable, configure a permanent redirect from that Worker to the new origin, preserving paths and query strings. The `_redirects` file in this update handles the RUX path migration on the new origin only. Submit the new sitemap after the deployment has been verified.

## Editing styles

Edit `src/style.css`, not the generated copy at `public/assets/style.css`. The stylesheet is separated into documented sections: palette, accessibility, ambient background, navigation, homepage, content, catalogue and optical surfaces, followed by responsive rules. Run the build after changing source assets or CSS. The background animation respects reduced motion and can be paused from the navigation.
