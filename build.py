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
from datetime import datetime

SITE_URL = "https://dougs-dharma.github.io/dougs-dharma-index"

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
    video_obj = {
        "@type": "VideoObject",
        "name": v['title'],
        "description": v.get('summary', ''),
        "uploadDate": v.get('date', ''),
        "url": v['youtube_url'],
        "embedUrl": v['youtube_url'].replace("watch?v=", "embed/"),
    }
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

# Step 8: Generate llms.txt
print("  Generating llms.txt...")
topic_list = sorted(all_topics)
sutta_list = sorted(all_suttas)

llms_txt = f"""# Doug's Dharma Video Index

> A searchable index of {len(data)} educational videos on early Buddhism
> by Doug Smith (Doug's Dharma YouTube channel).

## About

Doug's Dharma is a YouTube channel created in 2017 to introduce the
teachings of early Buddhism to a wide audience. Doug Smith holds a PhD
in Philosophy and has published scholarly works in Buddhist Studies.
This index covers videos from {earliest} to {latest}.

## Structured Data

The complete video index is available as machine-readable JSON:
- Full JSON: {SITE_URL}/dougs_dharma_index.json
- Searchable web interface: {SITE_URL}/

Each video entry in the JSON contains:
- title, date, youtube_url, summary
- topics (from a controlled vocabulary of {len(all_topics)} terms)
- sutta_refs (references to early Buddhist texts with SuttaCentral URLs)
- other_refs (books, articles, external resources)
- related_videos (links to other Doug's Dharma videos)

## Topics Covered

{chr(10).join('- ' + t for t in topic_list)}

## Sutta References

This index references {len(all_suttas)} unique suttas from the Pali canon
and other early Buddhist texts. References use standard abbreviations
(DN, MN, SN, AN, etc.) and link to SuttaCentral.net translations.

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

# Raw JSON data file
sitemap_urls.append(f"""  <url>
    <loc>{SITE_URL}/dougs_dharma_index.json</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
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
print("    index.html      - searchable webpage (with JSON-LD schema)")
print("    llms.txt         - AI/agent discoverability file")
print("    sitemap.xml      - search engine sitemap")
print("    robots.txt       - search engine instructions")
print()
print("  Your raw JSON is also served at:")
print(f"    {SITE_URL}/dougs_dharma_index.json")
print()
print("Done! You can now:")
print("  - Open index.html in your browser to preview")
print("  - Push to GitHub to publish (see the guide)")
