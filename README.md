# 晨光 · Daily Bible Verse (`EN` + `zh-TW`)

Bilingual daily scripture reflection site published automatically to GitHub Pages (served via Cloudflare at `verse.namike.me`).

## Structure

- `data/entries/YYYY-MM-DD.json` — Structured daily entry (verbatim Bible.com `EN` + `zh-TW` quotes, original-language word study, historical context, cross-references, daily habits & tensions, sourced workplace notes).
- `scripts/build_site.py` — Zero-dependency Python 3 generator that validates entries and outputs:
  - `YYYY/MM/DD/index.html` (canonical static page per day)
  - `index.html` (latest entry at site root)
  - `data/index.json` (archive search manifest)
- `assets/styles.css` & `assets/app.js` — Editorial broadsheet styling, dark/light theme toggle, study tabs, copy/share actions, and slide-over archive search.

## Build

```bash
python3 scripts/build_site.py
```
