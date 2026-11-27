#!/usr/bin/env python3
"""Check built pages, routes and both configured/unconfigured install states."""
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import shutil
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.h1 = self.main = 0
        self.feed(text)
        assert '{{' not in text, 'Unresolved template value'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'main':
            self.main += 1
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate ID'
            self.ids.add(attrs['id'])
        if tag == 'html':
            assert attrs.get('lang') == 'en'
        if tag == 'img':
            assert 'alt' in attrs, 'Missing image alt text'
        for key in ['href', 'src']:
            if attrs.get(key):
                self.links.append(attrs[key])


def crawl(folder):
    folder = folder.resolve()
    pages = {path: Page(path.read_text()) for path in folder.rglob('*.html')}
    assert len(pages) == 4
    for path, page in pages.items():
        assert page.h1 == 1 and page.main == 1, f'Invalid landmarks: {path}'
        for link in page.links:
            assert '\\' not in link
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                assert parsed.scheme in ('https', 'mailto'), link
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if target.is_dir():
                target /= 'index.html'
            assert target.is_file(), f'Broken local link: {path}: {link}'
            if parsed.fragment:
                assert target in pages and parsed.fragment in pages[target].ids, f'Broken anchor: {link}'
    return len(pages)


def main():
    assert (ROOT / 'dist/index.html').exists(), 'Run scripts/build.py first'
    count = crawl(ROOT / 'dist')
    company = (ROOT / 'dist/index.html').read_text()
    assert 'Bilgapp' in company
    assert 'multiplying-panda' not in company.lower() and 'multiplying panda' not in company.lower(), 'App must not be linked or advertised from the company homepage'
    for path in ['multiplying-panda/index.html', 'multiplying-panda/privacy-policy/index.html', 'multiplying-panda/terms/index.html']:
        assert 'noindex' in (ROOT / 'dist' / path).read_text(), 'Unlisted app pages should stay out of search results'
    spec = importlib.util.spec_from_file_location('site_build', ROOT / 'scripts/build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    config = json.loads((ROOT / 'config/site.json').read_text())
    builder.validated_config(config)
    for url in ['http://apps.apple.com/app/id1', 'https://apps.apple.com.example.org/app/id1', 'https://apps.apple.com@evil.example/app/id1', 'javascript:alert(1)']:
        try:
            builder.validated_config({**config, 'appStoreUrl': url})
        except ValueError:
            pass
        else:
            raise AssertionError(f'Unsafe store URL accepted: {url}')
    with tempfile.TemporaryDirectory(prefix='panda-site-check-') as directory:
        fixture = Path(directory)
        for name in ['scripts', 'src', 'assets', 'config']:
            shutil.copytree(ROOT / name, fixture / name)
        # Synthetic release configuration exists only in this disposable test.
        ready = {**config, 'siteUrl': 'https://example.invalid/panda', 'operatorName': 'Test operator', 'operatorAddress': 'Test address', 'operatorPhone': '+1 555 0100', 'supportEmail': 'test@example.invalid', 'hostingPrivacy': 'Synthetic test hosting statement.', 'appStoreUrl': 'https://apps.apple.com/app/id123456789', 'googlePlayUrl': 'https://play.google.com/store/apps/details?id=test.example.panda'}
        (fixture / 'config/site.json').write_text(json.dumps(ready))
        subprocess.run(['python3', str(fixture / 'scripts/build.py'), '--release'], check=True, capture_output=True)
        crawl(fixture / 'dist')
        home = (fixture / 'dist/multiplying-panda/index.html').read_text()
        assert ready['appStoreUrl'] in home and ready['googlePlayUrl'] in home
        assert 'Coming soon' not in home and 'noindex' in home
        assert 'noindex' not in (fixture / 'dist/index.html').read_text()
        assert 'https://example.invalid/panda/' in (fixture / 'dist/sitemap.xml').read_text()
        assert 'multiplying-panda' not in (fixture / 'dist/sitemap.xml').read_text()
        ready['operatorName'] = ''
        (fixture / 'config/site.json').write_text(json.dumps(ready))
        result = subprocess.run(['python3', str(fixture / 'scripts/build.py'), '--release'], capture_output=True)
        assert result.returncode != 0, 'Incomplete policy published without required operator details'
    print(f'PASS: {count} pages, all local links and anchors, image alt text, safe store URLs, company/app separation, configured downloads, release metadata, and incomplete-policy guard.')


if __name__ == '__main__':
    main()
