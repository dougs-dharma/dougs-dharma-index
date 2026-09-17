#!/usr/bin/env python3
"""
Doug's Dharma Index — Browse page generator
===========================================
Generates static, crawlable HTML pages from the same source of truth
(dougs_dharma_index.json), so topic and sutta queries have real URLs
for search engines to rank. Called from build.py.

Output:
    topics/index.html          hub listing every topic
    topics/<slug>.html         one page per topic with >= MIN_FOR_PAGE videos
    suttas/index.html          hub listing every sutta
    suttas/<slug>.html         one page per sutta with >= MIN_FOR_PAGE videos

Topics/suttas below the threshold are listed inline on the hub page instead,
so nothing is orphaned and we don't publish hundreds of thin pages.
"""

import os
import re
import json
import html as html_lib
from collections import defaultdict

# Below this many videos, an entry is folded into the hub page rather than
# getting its own URL (avoids thin / doorway pages).
MIN_FOR_PAGE = 3

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&'
         'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')


def slugify(s):
    """URL-safe slug: 'AN 3.65' -> 'an-3-65', 'suttas/early texts' -> 'suttas-early-texts'."""
    s = re.sub(r'[^a-z0-9]+', '-', s.lower())
    return s.strip('-') or 'item'


def build_slug_map(names):
    """Slug for each name, disambiguating any collisions deterministically."""
    out, taken = {}, {}
    for name in sorted(names):
        base = slugify(name)
        slug = base
        if base in taken:
            taken[base] += 1
            slug = f'{base}-{taken[base]}'
        else:
            taken[base] = 1
        out[name] = slug
    return out


def esc(s):
    return html_lib.escape(s or '')


def display(name):
    """Capitalise the first letter for headings only — slugs and data matching
    still use the source spelling. Proper names ('Analayo') are unaffected."""
    return name[:1].upper() + name[1:] if name else name


def truncate(s, n=155):
    s = ' '.join((s or '').split())
    return s if len(s) <= n else s[:n - 1].rsplit(' ', 1)[0] + '…'


def page_shell(title, description, canonical, depth, crumb, heading, lede,
               body, site_url, extra_ld=None):
    """One page of the browse section. `depth` is how many dirs deep (for ../)."""
    up = '../' * depth
    ld = [{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             **({"item": u} if u else {})}
            for i, (n, u) in enumerate(crumb)
        ],
    }]
    if extra_ld:
        ld.append(extra_ld)
    ld_tags = '\n'.join(
        f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>'
        for x in ld)

    crumb_html = '<span>/</span>'.join(
        (f'<a href="{up}{u_rel}">{esc(n)}</a>' if u_rel else f'{esc(n)}')
        for n, u_rel in [(n, r) for n, r in crumb_rel(crumb, site_url)])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="theme-color" content="#122d48">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Doug's Dharma">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="https://dougsdharma.com/assets/doug-portrait-mandala.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="https://dougsdharma.com/assets/logo-mark.png">
<link rel="alternate" type="application/json" href="{up}videos.json" title="Doug's Dharma video index (JSON)">
<link rel="alternate" type="text/plain" href="{up}llms.txt" title="Doug's Dharma video index (llms.txt)">
{FONTS}
<link rel="stylesheet" href="{up}assets/pages.css">
{ld_tags}
</head>
<body>
<header class="page">
  <div class="wrap">
    <nav class="crumb">{crumb_html}</nav>
    <a class="brandline" href="{up}index.html">
      <img src="https://dougsdharma.com/assets/logo-mark.png" alt="" onerror="this.style.display='none'">
      <span>Doug's Dharma</span>
    </a>
    <h1>{esc(heading)}</h1>
    <p class="lede">{esc(lede)}</p>
  </div>
</header>
<main>
  <div class="wrap">
{body}
  </div>
</main>
<footer class="page">
  <div class="wrap foot-inner">
    <div>
      <div class="eyebrow" style="color:var(--fg-inv-3)">Doug's Dharma</div>
      <p style="margin:8px 0 0">An index of the YouTube channel on early Buddhism.</p>
    </div>
    <div class="foot-links">
      <a href="{up}index.html">Full searchable index</a>
      <a href="{up}topics/">Browse by topic</a>
      <a href="{up}suttas/">Browse by sutta</a>
      <a href="{up}videos.json">Video data (JSON)</a>
      <a href="{up}llms.txt">llms.txt (for AI agents)</a>
      <a href="https://www.youtube.com/@DougsDharma">YouTube channel</a>
    </div>
  </div>
</footer>
</body>
</html>
"""


def crumb_rel(crumb, site_url):
    """Yield (name, relative-href-or-None) for breadcrumb rendering."""
    for name, url in crumb:
        if not url:
            yield name, None
        else:
            yield name, url[len(site_url) + 1:] if url.startswith(site_url) else url


def video_list_html(videos, indent='    '):
    rows = []
    for v in videos:
        date = esc(v.get('date', ''))
        rows.append(
            f'{indent}  <li>'
            f'<a class="t" href="{esc(v["url"])}">{esc(v["title"])}</a>'
            + (f'<span class="meta"><time datetime="{date}">{date}</time></span>' if date else '')
            + (f'<p>{esc(truncate(v.get("description", ""), 240))}</p>' if v.get('description') else '')
            + '</li>')
    return f'{indent}<ul class="videos">\n' + '\n'.join(rows) + f'\n{indent}</ul>'


def generate(records, data, site_url):
    """
    records: normalized video dicts (id/title/url/date/description/topics/suttas)
    data:    raw source records (used for SuttaCentral URLs)
    Returns a list of site-relative paths for the sitemap.
    """
    by_date = sorted(records, key=lambda r: (r['date'] != '', r['date']), reverse=True)

    topics = defaultdict(list)
    suttas = defaultdict(list)
    for r in by_date:
        for t in r['topics']:
            topics[t].append(r)
        for s in r['suttas']:
            suttas[s].append(r)

    # SuttaCentral URL + label per sutta id, from the source file.
    sutta_meta = {}
    for v in data:
        for s in v.get('sutta_refs', []):
            sid = s['sutta_id']
            if sid not in sutta_meta and s.get('url'):
                sutta_meta[sid] = {'url': s['url'], 'label': s.get('label') or ''}

    written = []

    for kind, mapping, hub_title, hub_lede in (
        ('topics', topics, 'Browse by Topic',
         'Every topic covered on the channel, with the videos that treat it.'),
        ('suttas', suttas, 'Browse by Sutta',
         'Early Buddhist texts cited across the channel, with the videos that discuss them.'),
    ):
        os.makedirs(kind, exist_ok=True)
        # Clear previously generated pages first. Without this, a renamed or
        # merged topic (or one that drops below MIN_FOR_PAGE) would leave a
        # stale orphan page published forever.
        for stale in os.listdir(kind):
            if stale.endswith('.html'):
                os.remove(os.path.join(kind, stale))
        slugs = build_slug_map(mapping.keys())
        big = {k: v for k, v in mapping.items() if len(v) >= MIN_FOR_PAGE}
        small = {k: v for k, v in mapping.items() if len(v) < MIN_FOR_PAGE}

        # ---- individual pages ----
        for name, vids in sorted(big.items()):
            slug = slugs[name]
            rel = f'{kind}/{slug}.html'
            canonical = f'{site_url}/{rel}'
            if kind == 'topics':
                title = f"{display(name)} — Doug's Dharma videos on early Buddhism"
                lede = f'{len(vids)} videos tagged “{name}”.'
                desc = truncate(f'{len(vids)} Doug\'s Dharma videos on {name} — '
                                f'early Buddhism explained, with sutta references.')
                refbar = ''
            else:
                meta = sutta_meta.get(name, {})
                label = meta.get('label') or ''
                title = f"{name}{' — ' + label if label else ''} — Doug's Dharma videos"
                lede = f'{len(vids)} videos discussing {name}' + (f' ({label})' if label else '') + '.'
                desc = truncate(f'{len(vids)} Doug\'s Dharma videos discussing {name}'
                                + (f', {label}' if label else '') + ' — early Buddhism explained.')
                refbar = (f'    <p class="refbar">Read {esc(name)} at '
                          f'<a href="{esc(meta["url"])}">SuttaCentral</a>.</p>\n') if meta.get('url') else ''

            item_ld = {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": title,
                "numberOfItems": len(vids),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "url": v['url'], "name": v['title']}
                    for i, v in enumerate(vids)
                ],
            }
            body = refbar + video_list_html(vids)
            crumb = [("Index", f'{site_url}/index.html'),
                     (hub_title, f'{site_url}/{kind}/'),
                     (display(name), None)]
            html = page_shell(title, desc, canonical, 1, crumb, display(name), lede,
                              body, site_url, extra_ld=item_ld)
            with open(rel, 'w', encoding='utf-8') as f:
                f.write(html)
            written.append(rel)

        # ---- hub page ----
        parts = []
        if big:
            parts.append('    <div class="group">')
            parts.append(f'      <h2>{esc(hub_title.replace("Browse by ", ""))}s with 3 or more videos</h2>')
            parts.append('      <div class="taglist">')
            for name, vids in sorted(big.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                parts.append(f'        <a href="{slugs[name]}.html">{esc(display(name))}'
                             f'<span class="n">{len(vids)}</span></a>')
            parts.append('      </div>')
            parts.append('    </div>')
        if small:
            parts.append('    <div class="group">')
            parts.append('      <h2>Also mentioned</h2>')
            for name, vids in sorted(small.items()):
                parts.append('      <div class="inline-entry">')
                parts.append(f'        <h3>{esc(display(name))}</h3>')
                parts.append('        <ul>')
                for v in vids:
                    parts.append(f'          <li><a href="{esc(v["url"])}">{esc(v["title"])}</a></li>')
                parts.append('        </ul>')
                parts.append('      </div>')
            parts.append('    </div>')

        hub_rel = f'{kind}/index.html'
        hub_desc = truncate(f'{len(mapping)} '
                            + ('topics' if kind == 'topics' else 'early Buddhist texts')
                            + " covered across Doug's Dharma videos on early Buddhism.")
        hub_html = page_shell(
            f"{hub_title} — Doug's Dharma Video Index", hub_desc,
            f'{site_url}/{kind}/', 1,
            [("Index", f'{site_url}/index.html'), (hub_title, None)],
            hub_title,
            f'{len(mapping)} ' + ('topics' if kind == 'topics' else 'texts')
            + f' across {len(records)} videos. {hub_lede}',
            '\n'.join(parts), site_url)
        with open(hub_rel, 'w', encoding='utf-8') as f:
            f.write(hub_html)
        written.append(f'{kind}/')

    return written
