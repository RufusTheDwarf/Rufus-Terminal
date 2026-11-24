"""Browser smoke tests of rendered documents, with local CSS/JS inlined for tests only.
Install with: pip install playwright; playwright install chromium.
HTTP routing, deployment headers and crawler behavior require a deployed-site test.
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

PUBLIC = Path(__file__).resolve().parents[1] / 'public'
CSS = (PUBLIC / 'assets/style.css').read_text(encoding='utf-8')
JS = (PUBLIC / 'assets/site.js').read_text(encoding='utf-8')


def render(page, file, javascript=True):
    html = file.read_text(encoding='utf-8')
    html = html.replace('<link rel="stylesheet" href="/assets/style.css">', f'<style>{CSS}</style>')
    html = html.replace('<script src="/assets/site.js" defer></script>', '')
    if javascript:
        html = html.replace('</body>', f'<script>{JS}</script></body>')
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
        for width in (320, 375, 768, 1024, 1440):
            for file in sorted(PUBLIC.rglob('*.html')):
                page = browser.new_page(viewport={'width': width, 'height': 900})
                page.on('pageerror', lambda error: errors.append(str(error)))
                render(page, file)
                assert page.locator('h1').count() == 1, file
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, file)
                page.close()
                count += 1
        page = browser.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        render(page, PUBLIC / 'projets/index.html')
        assert page.locator('.project:visible').count() == 16
        page.locator('[data-filter="security"]').click()
        assert page.locator('.project:visible').count() == 3
        page.locator('[data-filter="all"]').click()
        page.locator('#project-search').fill('parfum')
        assert page.locator('.project:visible').count() == 1
        page.locator('#project-search').fill('no-match-zzzz')
        assert page.locator('#empty').is_visible()
        page.close()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
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
        assert not errors, errors
        if args.screenshot:
            page.screenshot(path=args.screenshot)
        nojs = browser.new_page(java_script_enabled=False)
        render(nojs, PUBLIC / 'projets/index.html', javascript=False)
        assert nojs.locator('.project:visible').count() == 16
        assert not nojs.locator('#project-controls').is_visible()
        browser.close()
        print(f'OK: {count} isolated page/viewport checks; search, filters, terminal, history, safe text and catalogue without JS.')


if __name__ == '__main__':
    main()
