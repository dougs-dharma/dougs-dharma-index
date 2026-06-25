#!/usr/bin/env python3
"""
Doug's Dharma Index — Build Script
===================================
Reads dougs_dharma_index.json and template.html,
generates index.html with embedded data and JSON-LD schema markup,
plus llms.txt, sitemap.xml for agent/search discoverability.
"""

import json
import sys
import os
import html as html_lib
from datetime import datetime
from urllib.parse import urlparse, parse_qs

SITE_URL = "https://dougs-dharma.github.io/dougs-dharma-index"


def youtube_id(url):
    """Extract the YouTube video id from a watch URL."""
    try:
        return parse_qs(urlparse(url).query).get('v', [''])[0]
    except Exception:
        return ''

print()
print("Doug's Dharma Index — Build Script")
print("=" * 40)
print()

# Step 1: Load JSON data
print("  Loading dougs_dharma_index.json...")
try:
    with open('dougs_dharma_index.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  Found {len(data)} videos.")
except FileNotFoundError:
    print("  ERROR: dougs_dharma_index.json not found!")
    print("  Make sure it's in the same folder as this script.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"  ERROR: JSON syntax error: {e}")
    print("  Open the file in VS Code and look for red underlines.")
    sys.exit(1)

# Step 2: Load template
print("  Loading template.html...")
try:
    with open('template.html', 'r', encoding='utf-8') as f:
        html = f.read()
except FileNotFoundError:
    print("  ERROR: template.html not found!")
    sys.exit(1)

if 'PLACEHOLDER_DATA' not in html:
    print("  ERROR: template.html is missing PLACEHOLDER_DATA!")
    sys.exit(1)

# Step 3: Compute stats
all_topics = set()
all_suttas = set()
for v in data:
    for t in v.get('topics', []):
        all_topics.add(t)
    for s in v.get('sutta_refs', []):
        all_suttas.add(s['sutta_id'])

# Step 3b: Build a normalized, public projection of each video.
# This is the single source for videos.json, videos.md, the llms.txt list,
# and the no-JS anchor fallback — all derived from `data`, so nothing drifts.
records = []
for v in data:
    vid = youtube_id(v.get('youtube_url', ''))
    canonical = f"https://www.youtube.com/watch?v={vid}" if vid else v.get('youtube_url', '')
    records.append({
        "id": vid,
        "title": v['title'],
        "url": canonical,
        "date": v.get('date', ''),
        "description": v.get('summary', ''),
        "topics": v.get('topics', []),
        "suttas": [s['sutta_id'] for s in v.get('sutta_refs', [])],
    })

# Reverse-chronological order (newest first) for the flat text/HTML listings.
# Records without a date sort to the end.
records_sorted = sorted(records, key=lambda r: (r['date'] != '', r['date']), reverse=True)

# Step 4: Create compact JSON for embedding
compact = []
for v in data:
    compact.append({
        't': v['title'],
        'd': v.get('date', ''),
        'u': v['youtube_url'],
        's': v.get('summary', ''),
        'tp': v.get('topics', []),
        'sr': [{'id': s['sutta_id'], 'url': s.get('url', ''), 'l': s.get('label', '') or ''}
               for s in v.get('sutta_refs', [])],
        'or': [{'type': r.get('type', ''), 'label': r.get('label', ''), 'url': r.get('url', '')}
               for r in v.get('other_refs', [])],
        'rv': [{'t': r['title'], 'u': r['url']}
               for r in v.get('related_videos', [])]
    })

compact_json = json.dumps(compact, separators=(',', ':'), ensure_ascii=False)

# Step 5: Generate JSON-LD schema.org markup (VideoObject for each video)
print("  Generating JSON-LD schema markup...")
schema_items = []
for v in data:
    vid = youtube_id(v.get('youtube_url', ''))
    # Schema.org wants uploadDate as ISO 8601 *with* a timezone. We only have
    # the calendar date, so anchor it at noon UTC — a representative time that
    # keeps the same calendar day in every timezone from UTC-11 to UTC+11.
    raw_date = v.get('date', '')
    upload_date = f"{raw_date}T12:00:00+00:00" if raw_date else ''
    # Schema.org VideoObject requires a non-empty description; an empty string
    # counts as "missing". Fall back to the title when no summary is set.
    description = (v.get('summary') or '').strip() or v['title']
    video_obj = {
        "@type": "VideoObject",
        "name": v['title'],
        "description": description,
        "uploadDate": upload_date,
        "url": v['youtube_url'],
        "embedUrl": v['youtube_url'].replace("watch?v=", "embed/"),
    }
    # Google needs a thumbnailUrl for VideoObject rich results; YouTube's
    # thumbnail path is derivable from the video id.
    if vid:
        video_obj["thumbnailUrl"] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    # Add topic keywords
    if v.get('topics'):
        video_obj["keywords"] = ", ".join(v['topics'])
    schema_items.append(video_obj)

schema_ld = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "Doug's Dharma Video Index",
    "description": "A searchable index of Doug's Dharma YouTube videos on early Buddhism, organized by topic, sutta reference, and scholar.",
    "url": SITE_URL,
    "numberOfItems": len(data),
    "itemListElement": [
        {
            "@type": "ListItem",
            "position": i + 1,
            "item": item
        }
        for i, item in enumerate(schema_items)
    ]
}

schema_json = json.dumps(schema_ld, ensure_ascii=False, separators=(',', ':'))
schema_tag = f'<script type="application/ld+json">{schema_json}</script>'

# Step 6: Replace placeholders in HTML
# Build the no-JS fallback: full list of videos as plain anchors (newest first).
print("  Building no-JavaScript fallback list...")
noscript_lines = ['        <section class="noscript-index">',
                  f'          <h2>All {len(records)} videos</h2>',
                  '          <ul>']
for r in records_sorted:
    title = html_lib.escape(r['title'])
    url = html_lib.escape(r['url'])
    date = html_lib.escape(r['date'])
    date_suffix = f' <time datetime="{date}">({date})</time>' if date else ''
    noscript_lines.append(f'            <li><a href="{url}">{title}</a>{date_suffix}</li>')
noscript_lines.append('          </ul>')
noscript_lines.append('        </section>')
noscript_html = '\n'.join(noscript_lines)

html = html.replace('PLACEHOLDER_NOSCRIPT', noscript_html)
html = html.replace('PLACEHOLDER_DATA', compact_json)
html = html.replace('PLACEHOLDER_VIDEO_COUNT', str(len(data)))
html = html.replace('PLACEHOLDER_TOPIC_COUNT', str(len(all_topics)))
html = html.replace('PLACEHOLDER_SUTTA_COUNT', str(len(all_suttas)))

dates = sorted([v['date'] for v in data if v.get('date')])
if dates:
    earliest = datetime.strptime(dates[0], '%Y-%m-%d').strftime('%B %Y')
    latest = datetime.strptime(dates[-1], '%Y-%m-%d').strftime('%B %Y')
    html = html.replace('PLACEHOLDER_DATE_RANGE', f'{earliest} \u2013 {latest}')

# Inject JSON-LD just before </head>
if '</head>' in html:
    html = html.replace('</head>', f'{schema_tag}\n</head>')
else:
    # Fallback: inject at end
    html += f'\n{schema_tag}'

# Step 7: Write index.html
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = len(html) // 1024
print(f"  Created index.html ({size_kb} KB)")

# Step 7b: Generate videos.json (standalone, machine-readable, stable path).
print("  Generating videos.json...")
videos_json = {
    "name": "Doug's Dharma Video Index",
    "description": "Machine-readable index of Doug's Dharma YouTube videos on early Buddhism.",
    "url": SITE_URL + "/",
    "source": SITE_URL + "/dougs_dharma_index.json",
    "generated": datetime.now().strftime('%Y-%m-%d'),
    "count": len(records),
    "videos": records,
}
with open('videos.json', 'w', encoding='utf-8') as f:
    json.dump(videos_json, f, ensure_ascii=False, indent=2)
print(f"  Created videos.json ({len(records)} videos)")

# Step 7c: Generate videos.md (flat, human- and LLM-readable, newest first).
print("  Generating videos.md...")
videos_md_lines = [
    "# Doug's Dharma — Complete Video Index",
    "",
    f"{len(records)} videos, newest first. Format: `Title — watch URL`.",
    f"Structured data: {SITE_URL}/videos.json",
    "",
]
for r in records_sorted:
    videos_md_lines.append(f"- {r['title']} — {r['url']}")
videos_md_lines.append("")
with open('videos.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(videos_md_lines))
print(f"  Created videos.md ({len(records)} videos)")

# Step 8: Generate llms.txt
print("  Generating llms.txt...")
topic_list = sorted(all_topics)
sutta_list = sorted(all_suttas)
llms_video_list = '\n'.join(f"- {r['title']} — {r['url']}" for r in records_sorted)

llms_txt = f"""# Doug's Dharma Video Index

> A searchable index of {len(data)} educational videos on early Buddhism
> by Doug Smith (Doug's Dharma YouTube channel).

## About

Doug's Dharma is a YouTube channel created in 2017 to introduce the
teachings of early Buddhism to a wide audience. Doug Smith holds a PhD
in Philosophy and has published scholarly works in Buddhist Studies.
This index covers videos from {earliest} to {latest}.

## Structured Data

The complete video index is available in several machine-readable forms:
- Normalized JSON (recommended): {SITE_URL}/videos.json
- Flat Markdown list: {SITE_URL}/videos.md
- Full source JSON (richest, with refs): {SITE_URL}/dougs_dharma_index.json
- Searchable web interface: {SITE_URL}/

Each video in videos.json contains:
- id (YouTube video id), title, url (canonical watch URL), date, description
- topics (from a controlled vocabulary of {len(all_topics)} terms)
- suttas (early Buddhist text references, e.g. "MN 10", "SN 56.11")

The source file (dougs_dharma_index.json) additionally includes sutta_refs
with SuttaCentral URLs, other_refs (books/articles), and related_videos.

## Topics Covered

{chr(10).join('- ' + t for t in topic_list)}

## Sutta References

This index references {len(all_suttas)} unique suttas from the Pali canon
and other early Buddhist texts. References use standard abbreviations
(DN, MN, SN, AN, etc.) and link to SuttaCentral.net translations.

## All Videos (newest first)

{llms_video_list}

## Links

- YouTube: https://www.youtube.com/@dougsdharma
- Website: https://www.dougsdharma.com
- Podcast: https://digginthedharma.com
- Online courses: https://onlinedharma.org
- Patreon: https://www.patreon.com/dougsseculardharma
"""

with open('llms.txt', 'w', encoding='utf-8') as f:
    f.write(llms_txt)
print("  Created llms.txt")

# Step 9: Generate sitemap.xml
print("  Generating sitemap.xml...")
now = datetime.now().strftime('%Y-%m-%d')

sitemap_urls = []
# Main index page
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""")

# Normalized JSON data file (stable public path)
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/videos.json</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

# Flat Markdown list
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/videos.md</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>""")

# Raw source JSON data file
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/dougs_dharma_index.json</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""")

# llms.txt
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/llms.txt</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>""")

sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_urls)}
</urlset>
"""

with open('sitemap.xml', 'w', encoding='utf-8') as f:
    f.write(sitemap_xml)
print("  Created sitemap.xml")

# Step 10: Generate robots.txt (points to sitemap)
print("  Generating robots.txt...")
robots_txt = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

with open('robots.txt', 'w', encoding='utf-8') as f:
    f.write(robots_txt)
print("  Created robots.txt")

# Summary
print()
print("=" * 40)
print(f"  Stats: {len(data)} videos, {len(all_topics)} topics, {len(all_suttas)} suttas")
print(f"  Date range: {earliest} \u2013 {latest}")
print()
print("  Files generated:")
print("    index.html       - searchable webpage (JSON-LD + no-JS anchor list)")
print("    videos.json      - normalized machine-readable index (stable path)")
print("    videos.md        - flat human/LLM-readable list (newest first)")
print("    llms.txt         - AI/agent discoverability file (full video list)")
print("    sitemap.xml      - search engine sitemap")
print("    robots.txt       - search engine instructions")
print()
print("  Public data files are served at:")
print(f"    {SITE_URL}/videos.json")
print(f"    {SITE_URL}/videos.md")
print(f"    {SITE_URL}/dougs_dharma_index.json")
print()
print("Done! You can now:")
print("  - Open index.html in your browser to preview")
print("  - Push to GitHub to publish (see the guide)")
