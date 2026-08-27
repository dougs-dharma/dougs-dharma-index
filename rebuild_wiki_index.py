#!/usr/bin/env python3
"""
Doug's Dharma — Wiki Index rebuilder
====================================
Regenerates "Dougs Dharma Wiki Index.md" (a compressed, alphabetical reference
index of every video-outline note) deterministically from two inputs:

  1. the note files in the Obsidian vault folder "Past Videos:Writings", and
  2. this repo's dougs_dharma_index.json (authoritative titles / topics /
     sutta_refs / other_refs per video).

For each note it emits:
  ### <note filename>
  **Core claim:**  first substantive outline line (boilerplate + section
                   labels + title-repeats stripped)
  **Key themes:**  the video's concept topics (people routed to Sources)
  **Sources:**     sutta collections (DN/MN/SN/AN/...) + scholars, from the
                   linked index record; body-scanned fallback if unlinked.

There is deliberately NO "Notable" field (it was an un-reproducible editorial
judgment in the original April-2026 LLM compilation).

Usage:
  python3 rebuild_wiki_index.py \
      --notes-dir "/path/to/Claude Folders/Past Videos:Writings" \
      [--index dougs_dharma_index.json]     # defaults to file next to this script
      [--out   "<notes-dir>/Dougs Dharma Wiki Index.md"]

Re-run this after any enrichment pass or when new videos are added; it fully
overwrites the Wiki Index from current state.
"""
import os, re, json, argparse, unicodedata
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NOTES = "/Users/douglass/Desktop/Claude Folders/Past Videos:Writings"
WIKI_NAME = "Dougs Dharma Wiki Index.md"

HON = re.compile(r'^(Ajahn|Bhikkhu|Bhikkhuni|Ven|Venerable|Sister|Sayadaw|Lama|Dr|Prof)\b', re.I)
EXTRA_PEOPLE = {"Analayo", "Bodhipaksa", "Dalai Lama", "Ledi Sayadaw", "Nagarjuna",
                "Nyanaponika Thera", "Piya Tan", "Sheng Yen", "Epicurus",
                "Socrates", "Plato"}
COLL = re.compile(r'\b(DN|MN|SN|AN|Dhp|Ud|Iti|Snp|Sn|Thag|Thig|Vin|Kp|Pv|Vv|Ja|Mil)\b')
MARKER = re.compile(r'^\s*(?:\([0-9A-Za-z]+\)|[0-9A-Za-z][.)])\s*')
BOILER = re.compile(r'^(keep\s+(it\s+)?positive|name at intro|video notes|subscribe|teaser|please put|'
                    r'strong intro|interesting[,\s].*fun|make it (fun|funny)|'
                    r'page(\s*\d+)?$|script\s*/?\s*outline$|slide\s*notes?$|show\s*notes?\s*\d*$|'
                    r'opening$|closing$|outro$|body$|intro$|'
                    r'\(?final\)?\.?$|\d+$)', re.I)


def is_person(t):
    return ',' in t or HON.search(t) or t in EXTRA_PEOPLE


def person_short(t):
    return t.split(',')[0].strip() if ',' in t else t


def tnorm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'\b(notes|script|copy)\b', '', s.lower())
    return re.sub(r'[^a-z0-9]', '', s)


def frontmatter(t):
    if t.startswith('---'):
        p = t.split('---', 2)
        if len(p) >= 3:
            return p[1], p[2]
    return '', t


def get_video(fm):
    m = re.search(r'^video:\s*(.+)$', fm, re.M)
    if not m:
        return None
    v = m.group(1).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].replace(v[0]*2, v[0])
    return v


def topic_tags(fm):
    return [re.sub(r'.*topic/', '', x) for x in re.findall(r'topic/[^\s]+', fm)]


def core_claim(body, title_key):
    picked = []
    for raw in body.split('\n'):
        s = MARKER.sub('', raw.lstrip('#').strip()).strip()
        if not s or BOILER.match(s) or tnorm(s) == title_key:
            continue
        picked.append(s)
        if sum(len(x) for x in picked) > 110:
            break
    claim = re.sub(r'\s+', ' ', ' '.join(picked)).strip()
    if len(claim) > 170:
        claim = claim[:167].rsplit(' ', 1)[0] + '…'
    return claim


def main():
    ap = argparse.ArgumentParser(description="Rebuild Doug's Dharma Wiki Index.")
    ap.add_argument('--notes-dir', default=DEFAULT_NOTES,
                    help='Vault folder holding the video-outline notes.')
    ap.add_argument('--index', default=os.path.join(HERE, 'dougs_dharma_index.json'),
                    help='Path to dougs_dharma_index.json (default: next to this script).')
    ap.add_argument('--out', default=None,
                    help='Output path (default: "<notes-dir>/%s").' % WIKI_NAME)
    args = ap.parse_args()
    out = args.out or os.path.join(args.notes_dir, WIKI_NAME)

    d = json.load(open(args.index, encoding='utf-8'))
    by_title = {v['title']: v for v in d}

    files = sorted([f for f in os.listdir(args.notes_dir)
                    if f.endswith('.md') and f != WIKI_NAME], key=lambda s: s.lower())
    entries, linked = [], 0
    for f in files:
        fm, body = frontmatter(open(os.path.join(args.notes_dir, f), encoding='utf-8').read())
        rec = by_title.get(get_video(fm))
        claim = core_claim(body, tnorm(f[:-3]))
        if rec:
            linked += 1
            themes = [t for t in rec.get('topics', []) if not is_person(t)]
            people = [person_short(t) for t in rec.get('topics', []) if is_person(t)]
            colls = sorted({re.match(r'[A-Za-z]+', s['sutta_id']).group(0)
                            for s in rec.get('sutta_refs', []) if re.match(r'[A-Za-z]+', s['sutta_id'])})
            sources = colls + people
        else:
            themes = topic_tags(fm)
            sources = sorted(set(COLL.findall(body)))
        themes = list(dict.fromkeys(themes))
        sources = list(dict.fromkeys(s for s in sources if s))
        e = [f"### {f[:-3]}"]
        if claim:
            e.append(f"**Core claim:** {claim}")
        if themes:
            e.append(f"**Key themes:** {', '.join(themes)}")
        if sources:
            e.append(f"**Sources:** {', '.join(sources)}")
        entries.append('\n'.join(e))

    head = ("---\ntags:\n  - status/reference\n  - topic/channel\n---\n"
            "# Doug's Dharma Wiki Index\n\n"
            f"*A compressed reference index of {len(files)} video outlines, papers, and writings by "
            "Douglass Smith. Each entry lists the core claim, key themes, and sources cited. Themes and "
            "sources are drawn from the published video index where a note is linked to a video.*\n\n"
            f"*Reconstructed {date.today().isoformat()} from the current notes and index.*\n\n---\n\n")
    open(out, 'w', encoding='utf-8').write(head + '\n\n'.join(entries) + '\n')
    print(f"Wrote {out}\n  entries: {len(entries)} | linked to index: {linked} | fallback: {len(entries)-linked}")


if __name__ == '__main__':
    main()
