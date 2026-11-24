"""Check generated HTML, SEO metadata, links and sitemap without dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
SITE = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
BASE = SITE['siteUrl'].rstrip('/')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.meta = {}
        self.canonicals = []
        self.h1 = 0
        self.title = ''
        self.in_title = False
        self.lang = ''
        self.in_ld = False
        self.ld = []
        self.ld_text = ''
        self.heading_levels = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'html':
            self.lang = attrs.get('lang')
        if re.fullmatch(r'h[1-6]', tag):
            self.heading_levels.append(int(tag[1]))
        if tag == 'h1':
            self.h1 += 1
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            key = attrs.get('name') or attrs.get('property')
            if key:
                self.meta[key] = attrs.get('content', '')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs.get('href', ''))
        if tag in ('a', 'link') and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag in ('script', 'img') and attrs.get('src'):
            self.links.append(attrs['src'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_ld = True
            self.ld_text = ''
        if tag == 'img':
            assert 'alt' in attrs, 'Image without alt'

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_ld:
            self.ld_text += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_ld:
            self.ld.append(json.loads(self.ld_text))
            self.in_ld = False


def page_url(file):
    rel = file.relative_to(PUBLIC).as_posix()
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel


def main():
    pages = {}
    for file in sorted(PUBLIC.rglob('*.html')):
        p = Page()
        p.feed(file.read_text(encoding='utf-8'))
        pages[page_url(file)] = p
    urls, titles, descriptions = set(), set(), set()
    link_count = 0
    for path, p in pages.items():
        assert p.lang == 'fr-CH' and p.h1 == 1, path
        assert len(set(p.ids)) == len(p.ids), f'Duplicate ID: {path}'
        assert p.title and p.meta.get('description'), path
        assert 'contenu' in p.ids, path
        assert all(b <= a + 1 for a, b in zip(p.heading_levels, p.heading_levels[1:])), f'Heading jump: {path}'
        if path == '/404.html':
            assert 'noindex' in p.meta['robots'] and not p.canonicals
        else:
            assert p.canonicals == [BASE + path], path
            assert p.meta['og:url'] == BASE + path, path
            assert p.title not in titles and p.meta['description'] not in descriptions, f'Duplicate metadata: {path}'
            assert p.ld and 'noindex' not in p.meta['robots'], path
            titles.add(p.title)
            descriptions.add(p.meta['description'])
            urls.add(BASE + path)
        for link in p.links + [p.meta['og:image'], p.meta['twitter:image']]:
            dest = urlsplit(link)
            if dest.netloc and dest.netloc != urlsplit(BASE).netloc:
                continue
            if dest.scheme and dest.scheme not in ('http', 'https'):
                continue
            target = unquote(dest.path) or path
            if target in pages:
                if dest.fragment:
                    assert dest.fragment in pages[target].ids, f'Broken fragment {path}: {link}'
            else:
                assert (PUBLIC / target.lstrip('/')).is_file(), f'Broken link {path}: {link}'
            link_count += 1
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = [entry.text for entry in ET.parse(PUBLIC / 'sitemap.xml').findall('s:url/s:loc', ns)]
    assert set(sitemap) == urls and len(sitemap) == len(urls), 'Sitemap mismatch'
    assert f'Sitemap: {BASE}/sitemap.xml' in (PUBLIC / 'robots.txt').read_text()
    project_count = len(json.loads((ROOT / 'src/projects.json').read_text(encoding='utf-8')))
    assert len([path for path in pages if path.startswith('/projets/') and path != '/projets/']) == project_count
    print(f'OK: {len(pages)} HTML pages, {len(urls)} indexable URLs, {project_count} projects, {link_count} internal link/asset references.')


if __name__ == '__main__':
    main()
