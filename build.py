#!/usr/bin/env python3
"""
BUILD SCRIPT for Doug's Dharma Video Index
============================================
This script reads the data file (dougs_dharma_index.json) and the 
HTML template (template.html) and creates the final webpage (index.html).

HOW TO USE:
  1. Open Terminal
  2. Type: cd ~/dougs-dharma-index
  3. Type: python3 build.py
  4. The file "index.html" will be created/updated

After running this, you can:
  - Open index.html in your browser to preview
  - Upload to GitHub to publish (see the guide for instructions)
"""

import json
import sys
import os

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Building Doug's Dharma Video Index...")
print()

# Step 1: Read the data
try:
    with open('dougs_dharma_index.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  ✓ Loaded {len(data)} videos from dougs_dharma_index.json")
except FileNotFoundError:
    print("  ✗ ERROR: dougs_dharma_index.json not found!")
    print("    Make sure this file is in the same folder as build.py")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"  ✗ ERROR: dougs_dharma_index.json has a formatting error!")
    print(f"    {e}")
    print()
    print("  Common causes:")
    print("    - A missing comma between entries")
    print("    - A missing quotation mark")
    print("    - A stray character")
    print()
    print("  The error is near the line number shown above.")
    sys.exit(1)

# Step 2: Compact the data for embedding
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
print(f"  ✓ Compacted data ({len(compact_json)//1024} KB)")

# Step 3: Count stats
from collections import Counter
all_topics = set()
all_suttas = set()
for v in data:
    for t in v.get('topics', []):
        all_topics.add(t)
    for s in v.get('sutta_refs', []):
        all_suttas.add(s['sutta_id'])

# Step 4: Read the template
try:
    with open('template.html', 'r', encoding='utf-8') as f:
        html = f.read()
    print(f"  ✓ Loaded template.html")
except FileNotFoundError:
    print("  ✗ ERROR: template.html not found!")
    sys.exit(1)

# Step 5: Replace placeholders
html = html.replace('PLACEHOLDER_DATA', compact_json)
html = html.replace('PLACEHOLDER_VIDEO_COUNT', str(len(data)))
html = html.replace('PLACEHOLDER_TOPIC_COUNT', str(len(all_topics)))
html = html.replace('PLACEHOLDER_SUTTA_COUNT', str(len(all_suttas)))

# Find date range
dates = sorted([v['date'] for v in data if v.get('date')])
if dates:
    from datetime import datetime
    earliest = datetime.strptime(dates[0], '%Y-%m-%d').strftime('%B %Y')
    latest = datetime.strptime(dates[-1], '%Y-%m-%d').strftime('%B %Y')
    html = html.replace('PLACEHOLDER_DATE_RANGE', f'{earliest} – {latest}')

# Step 6: Write the output
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = len(html) // 1024
print(f"  ✓ Created index.html ({size_kb} KB)")
print()
print(f"  Stats: {len(data)} videos, {len(all_topics)} topics, {len(all_suttas)} suttas")
print(f"  Date range: {earliest} – {latest}")
print()
print("Done! You can now:")
print("  - Open index.html in your browser to preview")
print("  - Push to GitHub to publish (see the guide)")
