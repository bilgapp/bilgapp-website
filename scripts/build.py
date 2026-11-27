#!/usr/bin/env python3
"""Generate a portable, JavaScript-free static website from reviewed source files."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import posixpath
import shutil
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('operatorName', 'operatorAddress', 'operatorPhone', 'supportEmail')


def validated_config(config):
    date.fromisoformat(config['updatedDate'])
    for key, domain in [('appStoreUrl', 'apps.apple.com'), ('googlePlayUrl', 'play.google.com')]:
        if config[key]:
            parsed = urlparse(config[key])
            if parsed.scheme != 'https' or parsed.hostname != domain or parsed.username or parsed.password:
                raise ValueError(f'{key} must be an HTTPS {domain} URL')
    if config['supportEmail'] and not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', config['supportEmail']):
        raise ValueError('supportEmail must be a valid public email address')
    if config['siteUrl']:
        parsed = urlparse(config['siteUrl'])
        if parsed.scheme != 'https' or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError('siteUrl must be an HTTPS website base URL')
    return [key for key in REQUIRED if not config[key].strip()]


def build(release=False):
    config = json.loads((ROOT / 'config/site.json').read_text())
    missing = validated_config(config)
    if release and (missing or not config['siteUrl'] or 'will be confirmed' in config['hostingPrivacy']):
        raise ValueError('Publication details incomplete: provide operator contact, siteUrl, and hosting privacy information')
    output = ROOT / 'dist'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    shutil.copytree(ROOT / 'assets', output / 'assets', ignore=shutil.ignore_patterns('README.md', '.DS_Store', '__pycache__', '*.pyc'))
    shutil.copyfile(ROOT / 'src/styles.css', output / 'styles.css')
    # Wrangler reads exclusions from the root of the generated asset directory.
    shutil.copyfile(ROOT / '.assetsignore', output / '.assetsignore')
    layout = (ROOT / 'src/layout.html').read_text()
    legal = json.loads((ROOT / 'src/legal.json').read_text())
    root_url = config['siteUrl'].rstrip('/')
    draft = bool(missing)
    operator = '<dl class="contact-details">' + ''.join(
        f'<dt>{label}</dt><dd>{escape(config[key]) if config[key] else "To be supplied before publication"}</dd>'
        for key, label in [('operatorName', 'Operator'), ('operatorAddress', 'Postal address'), ('operatorPhone', 'Phone'), ('supportEmail', 'Support and privacy email')]
    ) + '</dl>'
    contact = f'<a href="mailto:{escape(config["supportEmail"], quote=True)}">Contact</a>' if config['supportEmail'] else ''

    def page(path, title, description, content, active='', company=False):
        assets = '../' * len(Path(path).parts) + 'assets/'
        root = posixpath.relpath('multiplying-panda', path or '.') + '/'
        template = (ROOT / 'src/company-layout.html').read_text() if company else layout
        metadata = '<meta name="robots" content="noindex, follow">' if not company or not root_url else ''
        if root_url:
            url = f'{root_url}/{path}'
            metadata += f'<link rel="canonical" href="{escape(url, quote=True)}">'
            metadata += f'<meta property="og:url" content="{escape(url, quote=True)}">'
            metadata += f'<meta property="og:image" content="{escape(root_url, quote=True)}/assets/app-icon.png">' if not company else ''
        metadata += f'<meta property="og:title" content="{escape(title, quote=True)}"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:type" content="website">'
        rendered = template.replace('{{content}}', content)
        replacements = {'title': escape(title), 'description': escape(description, quote=True), 'root': root, 'assets': assets, 'metadata': metadata, 'content': content, 'privacy-current': 'aria-current="page"' if active == 'privacy' else '', 'terms-current': 'aria-current="page"' if active == 'terms' else '', 'year': config['updatedDate'][:4], 'copyright': escape(config['operatorName'] or config['appName']), 'contact': contact}
        for key, value in replacements.items():
            rendered = rendered.replace('{{' + key + '}}', value)
        target = output / path
        target.mkdir(parents=True, exist_ok=True)
        (target / 'index.html').write_text(rendered)

    apple = '<svg viewBox="0 0 24 28" fill="currentColor" aria-hidden="true"><path d="M17.4 14.8c0-2.7 2.2-4.1 2.3-4.2-1.3-1.9-3.2-2.1-3.9-2.1-1.7-.2-3.3 1-4.2 1-.9 0-2.2-1-3.6-.9-1.8 0-3.5 1.1-4.4 2.7-1.9 3.3-.5 8.1 1.3 10.8.9 1.3 1.9 2.7 3.3 2.6 1.3-.1 1.8-.9 3.5-.9 1.6 0 2.1.9 3.6.9 1.5 0 2.4-1.3 3.3-2.6 1-1.4 1.4-2.8 1.5-2.9-.1 0-2.7-1-2.7-4.4ZM14.6 6.7c.7-.9 1.2-2.1 1.1-3.3-1.1 0-2.4.7-3.1 1.5-.7.8-1.3 2-1.1 3.2 1.2.1 2.4-.6 3.1-1.4Z"/></svg>'
    play = '<svg viewBox="0 0 28 30" aria-hidden="true"><path d="M3 2 18 15 3 28Z" fill="#3f9eea"/><path d="m3 2 18 10-3 3Z" fill="#5dae34"/><path d="m3 28 18-10-3-3Z" fill="#e5533d"/><path d="m18 15 3-3 5 3-5 3Z" fill="#ffc928"/></svg>'
    stores = ''
    for key, name, device, icon in [('appStoreUrl', 'App Store', 'For iPhone', apple), ('googlePlayUrl', 'Google Play', 'For Android phones', play)]:
        url = config[key]
        tag = 'a' if url else 'div'
        attrs = f' href="{escape(url, quote=True)}" rel="noopener"' if url else ' role="group"'
        status = '<span aria-hidden="true">↗</span>' if url else '<span class="store-status">Coming soon</span>'
        stores += f'<{tag} class="store-card"{attrs}>{icon}<span><small>{device}</small><strong>{name}</strong></span>{status}</{tag}>'
    home = (ROOT / 'src/home.html').read_text().replace('{{stores}}', stores)
    company = (ROOT / 'src/company.html').read_text()
    page('', 'Bilgapp — Thoughtful software development', 'Bilgapp is a software development company building practical mobile applications and web experiences with considered design and reliable engineering.', company, company=True)
    page('multiplying-panda/', 'Multiplying Panda — A little practice, every day', 'Short math practice, a friendly panda, and rewards for little milestones. Find Multiplying Panda for iPhone and Android, and read our privacy policy and terms.', home)
    for key, document in legal.items():
        path = 'multiplying-panda/privacy-policy/' if key == 'privacy' else 'multiplying-panda/terms/'
        toc = '<aside class="contents" aria-label="On this page"><p>On this page</p><ol>' + ''.join(f'<li><a href="#{sid}">{escape(title)}</a></li>' for sid, title, _ in document['sections']) + '</ol></aside>'
        sections = ''.join(f'<section id="{sid}"><h2>{escape(title)}</h2>{body.replace("{{operator}}", operator).replace("{{hostingPrivacy}}", escape(config["hostingPrivacy"]))}</section>' for sid, title, body in document['sections'])
        draft_notice = '<div class="draft-note"><strong>Draft for review.</strong> Operator contact details are pending. This policy must be completed before it is published as the app’s official policy.</div>' if draft else ''
        hero = f'<header class="legal-hero wrap"><p class="eyebrow">MULTIPLYING PANDA · LEGAL</p><h1>{escape(document["title"])}</h1><p class="intro">{escape(document["intro"])}</p><div class="document-meta"><span>Last updated: {date.fromisoformat(config["updatedDate"]).strftime("%d %B %Y")}</span><span>Applies to the app and this website</span></div>{draft_notice}</header>'
        page(path, f'{document["title"]} — Multiplying Panda', document['intro'], hero + '<div class="legal-layout wrap">' + toc + '<article class="legal-copy">' + sections + '</article></div>', key)
    (output / 'robots.txt').write_text('User-agent: *\n' + ('Disallow: /\n' if not root_url else f'Allow: /\nSitemap: {root_url}/sitemap.xml\n'))
    if root_url:
        # The app section is intentionally unlisted and omitted from discovery.
        (output / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>' + escape(root_url) + '/</loc></url></urlset>')
    print(f'Built 4 pages in {output}')
    if missing:
        print('Pending operator details: ' + ', '.join(missing))
    print('Missing store links show Coming soon; no destination is invented.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true', help='Require complete operator and hosting information')
    args = parser.parse_args()
    build(args.release)
