"""Exercise the local workspace with Chromium. No external services required."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_check import render, PUBLIC


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chromium')
    parser.add_argument('--screenshot')
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, color_scheme='light', accept_downloads=True)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: dialog.accept())
        render(page, PUBLIC / 'lab/index.html')
        assert page.locator('#workspace').is_visible()
        def command(value):
            page.locator('#shell-command').fill(value)
            page.locator('#shell-command').press('Enter')
        def app(value):
            page.locator('[data-app="' + value + '"]').click()
        command('mkdir test')
        command('cd test')
        command('echo bonjour > a.txt')
        command('cat a.txt')
        assert 'bonjour' in page.locator('#shell-output').inner_text()
        command('js console.log(6 * 7, self.origin)')
        page.wait_for_function("document.querySelector('#shell-output').textContent.includes('42 null')")
        page.wait_for_function("document.querySelector('#workspace-status').textContent.includes('terminé')")
        command('js try { indexedDB.open(\"x\"); } catch (e) { console.log(e.name); }')
        page.wait_for_function("document.querySelector('#shell-output').textContent.includes('SecurityError')")
        page.wait_for_function("document.querySelector('#workspace-status').textContent.includes('terminé')")
        command('cd /')
        app('notes')
        page.locator('#note-editor').fill('Une note <img src=x onerror=alert(1)>')
        page.locator('#save-note').click()
        app('shell')
        command('cat /notes.txt')
        assert 'Une note' in page.locator('#shell-output').inner_text()
        assert page.locator('#shell-output img').count() == 0
        app('files')
        row = page.locator('.file-row').filter(has_text='notes.txt')
        row.get_by_text('Corbeille').click()
        app('trash')
        page.get_by_role('button',name='Restaurer').click()
        app('files')
        assert page.locator('.file-row').filter(has_text='notes.txt').count() == 1
        app('code')
        page.locator('#code-path').fill('/hello.js')
        page.locator('#code-editor').fill('console.log("editor works", 3 ** 3);')
        page.locator('#run-code').click()
        page.wait_for_function("document.querySelector('#shell-output').textContent.includes('editor works 27')")
        page.wait_for_function("document.querySelector('#workspace-status').textContent.includes('terminé')")
        app('files')
        with page.expect_download() as dl:
            page.locator('#export-all').click()
        assert dl.value.suggested_filename == 'terminal-session.json'
        assert 'editor works' in Path(dl.value.path()).read_text()
        if args.screenshot:
            page.screenshot(path=args.screenshot)
        page.locator('#reset-session').click()
        app('files')
        assert page.locator('.file-row').filter(has_text='test/').count() == 0
        assert page.locator('.file-row').filter(has_text='notes.txt').count() == 1
        assert not errors, errors
        browser.close()
    print('OK: shell, shared files, editor, JS worker (opaque origin), storage isolation, trash, export and reset.')

if __name__ == '__main__':
    main()
