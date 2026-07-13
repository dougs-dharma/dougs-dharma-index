# Claude for Doug's Dharma — project memory
<!-- VERSION: 2026-06-01 · If a copy elsewhere shows an older date, replace it from this project. -->

Doug Smith ("Doug's Dharma") — Early Buddhism, secular practice. YouTube channel,
a book, a website at **dougsdharma.com**, and video content edited in Final Cut Pro.
Brand voice: quiet, warm, scholarly, restrained. Less is more. No AI-slop tropes,
no gratuitous gradients, no emoji.

## ALWAYS use the existing design system
Before designing ANY material for Doug (videos, decks, web pages, indexes, PDFs),
read these first and follow them — do not invent new colors, fonts, or styles:
- `assets/tokens.css` — the canonical design tokens (palette, type, spacing, scale)
- `Design System.html` — the full field manual (voice, palette, type, mark, components)
- `Video & Motion Style Notes.html` — video / Final Cut conventions (see below)

The online video index was once built WITHOUT these details — don't repeat that.
When in doubt, match the website (`Doug Smith Homepage.html`).

## Palette (from tokens.css — use these names)
- night `#122d48` (primary deep navy) · ink `#0b1c2c` (darkest type on light)
- stillwater `#7fa0a2` (dusty blue-grey, main secondary)
- parchment `#d7d2c8` (cream linework) · ivory `#efeae0` (warm page bg)
- smoke `#52585e` (muted body) · mist `#8a8f95` (captions)
- ember `#f06e32` (book-cover accent — USE SPARINGLY)
Backgrounds are warm ivory (light) or deep night navy (dark). Ember is an accent only.

## Typography system & the rule behind it
- Display / serif = **Gentium Book Plus** (fallback EB Garamond, Georgia) — things that SPEAK: titles, names, quotes.
- Body / sans = **Inter** (fallback system-ui) — running text.
- Mono = **JetBrains Mono** — labels/specimens, sparingly.
- THE RULE: **serif for things that speak; sans/mono, UPPERCASE + wide letter-spacing, for things that LABEL** (eyebrows, callouts, footers). Keeping this one rule consistent is what makes everything feel unified.

## Video / Final Cut Pro conventions
Final Cut uses fonts installed on the Mac. **Gentium Book Plus is now installed on
Doug's Mac** — so use it directly for serif roles (exact brand fidelity). Mac-native
fallbacks if ever on another machine:
- Serif role (names, section titles, quotes) → **Gentium Book Plus** (installed, use this),
  fallback **Charter** (ships w/ macOS), Iowan Old Style, Palatino, EB Garamond.
- Sans role (descriptors, labels) → **SF Pro** or **Avenir Next** (both native), or install Inter.
- Mono role (called-out term) → JetBrains Mono.

Role mapping for video:
- Lower-third NAME: Gentium Book Plus (Charter fallback), larger, regular. Current text: **"Doug Smith, Ph.D."**
  — name only, NO affiliation (deliberately moving away from "Online Dharma Institute").
- Section / segment titles: Gentium Book Plus (Charter fallback), title case, generous.
- Footers / called-out word or phrase: SF Pro / Avenir Next (or JetBrains Mono),
  UPPERCASE, small, WIDE letter-spacing. The letter-spacing matters more than the font.
- Longer quotes: Gentium Book Plus *Italic* (Charter Italic fallback), larger, comfortable leading.
Video tips: add a soft shadow / semi-opaque backing bar behind lower-third text for
legibility over footage; add tracking on small sans lines so they read in motion.

## Hosting (so I give correct instructions, not redesign)
Site is on GitHub Pages. GitHub account **dougs-dharma**, repo **dougsdharma-site**,
served at dougsdharma.com via a CNAME. Updates: edit `index.html` in the browser for
text; re-upload `index.html` for redesigns. The repo's `index.html` is the source of
truth — if Doug edited in the browser, re-sync (get his current file) before any redo.

## Data & build scripts (this repo)
- `dougs_dharma_index.json` is the **hand-maintained source of truth** (623 videos:
  title, date, youtube_url, summary, topics, sutta_refs, other_refs, related_videos).
- `build.py` regenerates the site derivatives (`index.html`, `videos.json`, `videos.md`,
  `llms.txt`, `sitemap.xml`, `robots.txt`) from that JSON. It is a clean UTF-8 passthrough.
- `rebuild_wiki_index.py` regenerates the **vault** file `Past Videos:Writings/Dougs Dharma
  Wiki Index.md` deterministically from the vault notes + this index. Run it after any
  frontmatter-enrichment pass or when videos are added:
  `python3 rebuild_wiki_index.py --notes-dir "<vault>/Past Videos:Writings"`
  (index defaults to the JSON next to the script). It drops the old editorial "Notable"
  field on purpose; themes/sources come from the index for linked notes.
- **Encoding caveat:** the source JSON previously carried double-encoded mojibake
  (`â€™`, `Åš`, and a 4-byte emoji `🙂` that a 2/3-byte-only fixer misses). It was cleaned
  2026-07; if you hand-edit the JSON, keep it valid UTF-8 and re-run `build.py`. A quick
  check: `python3 -c "import json,ftfy;[print(s) for x in json.load(open('dougs_dharma_index.json')) for s in x.values() if isinstance(s,str) and ftfy.fix_encoding(s)!=s]"` should print nothing.

## The vault (Obsidian) — where the video notes live
Doug's note vault is the connected **"Claude Folders"** folder; per-video outline notes are
in `Past Videos:Writings/` (~610 `.md` files, most with `video:`/`date:`/`url:`/`suttas:`/
`summary:` frontmatter joined to this index by the exact published `video:` title). Notes
were originally `.pages`/RTF conversions, so watch for conversion artifacts if new ones are
added: double-encoded mojibake, bare RTF codes (`'92`→’, `'93`→“, `'97`→—), dropped Pali
diacritics (`Pli`→Pāli, `jhna`→jhāna), and `Courier;`/`*HYPERLINK` junk. Cleaned 2026-07.
