"""Browser smoke tests of rendered documents, with local CSS/JS inlined for tests only.
Install with: pip install playwright; playwright install chromium.
HTTP routing, deployment headers and crawler behavior require a deployed-site test.
"""
import argparse
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PUBLIC = Path(__file__).resolve().parents[1] / 'public'
PROJECTS = json.loads((PUBLIC.parent / "src/projects.json").read_text(encoding="utf-8"))
CSS = (PUBLIC / 'assets/style.css').read_text(encoding='utf-8')
MAP = base64.b64encode((PUBLIC / 'assets/ambient-map.svg').read_bytes()).decode('ascii')
CSS = CSS.replace('./ambient-map.svg', f'data:image/svg+xml;base64,{MAP}')
JS = (PUBLIC / 'assets/site.js').read_text(encoding='utf-8')
THEME = (PUBLIC / 'assets/theme.js').read_text(encoding='utf-8')


def render(page, file, javascript=True):
    html = file.read_text(encoding='utf-8')
    html = html.replace('<link rel="stylesheet" href="/assets/style.css">', f'<style>{CSS}</style>')
    html = html.replace('<script src="/assets/site.js" defer></script>', '')
    html = html.replace('<script src="/assets/theme.js"></script>', '')
    for name in ('forest-terminal.svg', 'day-terminal.svg', 'rux-diagram.svg'):
        data = base64.b64encode((PUBLIC / 'assets' / name).read_bytes()).decode('ascii')
        html = html.replace(f'/assets/{name}', f'data:image/svg+xml;base64,{data}')
    if javascript:
        html = html.replace('</head>', f'<script>{THEME}</script></head>')
    if javascript:
        html = html.replace('</body>', f'<script>{JS}</script></body>')
    if file == PUBLIC / 'lab/index.html':
        lab_css = (PUBLIC / 'assets/lab.css').read_text(encoding='utf-8')
        lab_js = (PUBLIC / 'assets/lab.js').read_text(encoding='utf-8')
        html = html.replace('<link rel="stylesheet" href="/assets/lab.css">', f'<style>{lab_css}</style>')
        html = html.replace('<script src="/assets/lab.js" defer></script>', '')
        if javascript:
            html = html.replace('</body>', f'<script>{lab_js}</script></body>')
    page.set_content(html)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chromium', help='Optional Chromium executable path')
    parser.add_argument('--screenshot', help='Optional home screenshot output path')
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium)
        errors = []
        count = 0
        for theme in ('dark', 'light'):
            for width in (320, 375, 768, 1024, 1440):
                page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme=theme)
                page.on('pageerror', lambda error: errors.append(str(error)))
                for file in sorted(PUBLIC.rglob('*.html')):
                    render(page, file)
                    assert page.locator('h1').count() == 1, file
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (theme, width, file)
                    assert page.locator('#theme-select').input_value() == 'auto'
                    if file == PUBLIC / 'index.html':
                        assert page.locator(f'.art-{theme}').is_visible()
                page.close()
                count += len(list(PUBLIC.rglob('*.html')))
        page = browser.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        render(page, PUBLIC / 'projets/index.html')
        assert page.locator('.project:visible').count() == sum(p.get("section") != "apps" for p in PROJECTS)
        page.locator('[data-filter="security"]').click()
        assert page.locator('.project:visible').count() == sum(p["category"] == "security" and p.get("section") != "apps" for p in PROJECTS)
        page.locator('[data-filter="all"]').click()
        page.locator('#project-search').fill('parfum')
        assert page.locator('.project:visible').count() == 1
        page.locator('#project-search').fill('no-match-zzzz')
        assert page.locator('#empty').is_visible()
        page.close()
        page = browser.new_page(viewport={'width': 1440, 'height': 1250})
        page.on('pageerror', lambda error: errors.append(str(error)))
        render(page, PUBLIC / 'index.html')
        input_ = page.locator('#terminal-input')
        for command in ('help', 'whoami', '<img src=x onerror=alert(1)>'):
            input_.fill(command)
            input_.press('Enter')
        assert 'whoami' in page.locator('#terminal-output').inner_text()
        assert 'RufusTheDwarf' in page.locator('#terminal-output').inner_text()
        assert page.locator('#terminal-output img').count() == 0
        input_.press('ArrowUp')
        assert input_.input_value() == '<img src=x onerror=alert(1)>'
        input_.fill('clear')
        input_.press('Enter')
        assert page.locator('#terminal-output').inner_text() == ''
        # Isolated rendering exercises theme switching even when storage is blocked.
        page.select_option('#theme-select', 'light')
        assert page.locator('html').get_attribute('data-theme') == 'light'
        assert page.locator('.art-light').is_visible()
        assert not page.locator('.art-dark').is_visible()
        page.select_option('#theme-select', 'dark')
        assert page.locator('.art-dark').is_visible()
        page.select_option('#theme-select', 'auto')
        assert page.locator('html').get_attribute('data-theme') is None
        page.locator('#motion-toggle').click()
        assert page.locator('html').get_attribute('data-motion-paused') is not None
        assert page.locator('#motion-toggle').get_attribute('aria-pressed') == 'true'
        page.locator('#motion-toggle').click()
        assert page.locator('html').get_attribute('data-motion-paused') is None
        render(page, PUBLIC / 'apps/index.html')
        assert page.locator('a[href$="/RUX.exe"]').count() == 1
        assert page.locator('a[href="/apps/rux-netmap/"]').count() >= 1
        render(page, PUBLIC / 'index.html')
        assert page.title() == '/>Terminal'
        if args.screenshot:
            page.select_option('#theme-select', 'dark')
            page.locator('#theme-select').blur()
            page.screenshot(path=args.screenshot)
            page.select_option('#theme-select', 'light')
            target = Path(args.screenshot)
            page.locator('#theme-select').blur()
            page.screenshot(path=str(target.with_name(target.stem + '-light' + target.suffix)))
        nojs = browser.new_page(java_script_enabled=False)
        render(nojs, PUBLIC / 'projets/index.html', javascript=False)
        assert nojs.locator('.project:visible').count() == sum(p.get("section") != "apps" for p in PROJECTS)
        assert not nojs.locator('#project-controls').is_visible()
        assert not errors, errors
        browser.close()
        print(f'OK: {count} isolated page/viewport checks; search, filters, theme switching, terminal, history, safe text and catalogue without JS.')


if __name__ == '__main__':
    main()
