# dougs-dharma-index

A searchable index of every video on the **Doug's Dharma** YouTube channel
(early Buddhism, secular practice). Static site on GitHub Pages:

➡️ https://dougs-dharma.github.io/dougs-dharma-index/

The interactive page renders client-side, but the same dataset is also published
as plain, fetchable files so AI agents and no-JavaScript fetchers get the full
content — not an empty shell.

## How it's built

Single source of truth → one build step → all outputs. Nothing is hand-edited
downstream, so nothing drifts.

```
dougs_dharma_index.json   (source of truth — edit this)
        │
   python3 build.py
        │
        ├── index.html        searchable UI + JSON-LD + <noscript> anchor list
        ├── videos.json       normalized machine-readable index  (stable path)
        ├── videos.md         flat list, newest first
        ├── llms.txt          agent-facing overview + full video list
        ├── topics/           crawlable page per topic  (+ hub at topics/)
        ├── suttas/           crawlable page per sutta  (+ hub at suttas/)
        ├── sitemap.xml
        └── robots.txt
```

To rebuild after editing `dougs_dharma_index.json`:

```sh
python3 build.py
```

(Or double-click `update_and_build.command`.) Then commit and push to publish.

## Browse pages (`topics/`, `suttas/`)

The interactive page is a single URL, so topic and sutta searches had nothing
for Google to rank. [`build_pages.py`](build_pages.py) generates a static,
crawlable page for each one from the same source data:

- `topics/<slug>.html` and `suttas/<slug>.html` — one per entry with **3 or
  more** videos (`MIN_FOR_PAGE` in `build_pages.py`).
- Entries below that threshold are listed inline on the hub pages
  (`topics/`, `suttas/`) instead, so nothing is orphaned and we don't publish
  hundreds of near-empty pages that search engines treat as thin content.
- Every page carries its own `<title>`, meta description, canonical URL,
  Open Graph tags, and `BreadcrumbList` + `ItemList` JSON-LD.
- All of them are linked from the main page footer and listed in `sitemap.xml`.

**These regenerate completely on every build.** New topics and suttas get pages
automatically once they reach the threshold; renamed or merged topics do *not*
leave stale pages behind, because the generator clears `topics/*.html` and
`suttas/*.html` before writing. Styling lives in
[`assets/pages.css`](assets/pages.css).

## Files for agents & simple fetchers

| File | What it is |
|------|------------|
| [`videos.json`](videos.json) | Normalized, machine-readable index. **Start here.** |
| [`videos.md`](videos.md) | Flat Markdown list, one line per video, newest first. |
| [`llms.txt`](llms.txt) | Plain-text overview ([llms.txt convention](https://llmstxt.org)) with the full video list. |
| [`dougs_dharma_index.json`](dougs_dharma_index.json) | Full source data (richest — includes sutta URLs, book/article refs, related videos). |

These are linked from the page `<head>` (`<link rel="alternate">`) and the footer.

> **Paths:** the site is served from a GitHub Pages *project* subpath
> (`/dougs-dharma-index/`), so links use **relative** paths (`videos.json`),
> which resolve correctly under that subpath. The fully-qualified URL of the
> JSON is `https://dougs-dharma.github.io/dougs-dharma-index/videos.json`.

### `videos.json` schema

```jsonc
{
  "name": "Doug's Dharma Video Index",
  "description": "...",
  "url": "https://dougs-dharma.github.io/dougs-dharma-index/",
  "source": ".../dougs_dharma_index.json",  // richer source file
  "generated": "2026-06-19",                 // build date (YYYY-MM-DD)
  "count": 622,
  "videos": [
    {
      "id": "6WtRetCi_Oc",                                       // YouTube video id
      "title": "Why the Buddha Rejected Prayer (Mostly)",        // full title
      "url": "https://www.youtube.com/watch?v=6WtRetCi_Oc",      // canonical watch URL
      "date": "2026-06-15",                                      // publish date (YYYY-MM-DD)
      "description": "Prayer is a nearly universal human ...",   // summary
      "topics": ["prayer", "suttas/early texts"],                // topic tags
      "suttas": ["AN 5.43", "SN 42.6", "AN 5.48"]                // early-text references
    }
    // ... one object per video
  ]
}
```

Field notes:
- `id` / `url` are derived from the source `youtube_url`; `url` is always the
  canonical `https://www.youtube.com/watch?v=<id>` form.
- `topics` come from a controlled vocabulary used across the site.
- `suttas` are the sutta ids only (e.g. `"MN 10"`). For sutta **URLs**
  (SuttaCentral) and other reference types, use `dougs_dharma_index.json`.
- `videos` preserves the source order (newest first); `videos.md` and the
  `llms.txt` list are explicitly sorted reverse-chronologically.

The page also embeds the same data as schema.org `VideoObject` JSON-LD for
search engines.
