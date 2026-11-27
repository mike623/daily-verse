# 晨光 · Daily Bible Verse (`EN` + `zh-TW`)

Bilingual daily scripture reflection site published automatically to GitHub Pages (`https://mike623.github.io/daily-verse/`) and served on [`https://verse.namike.me/`](https://verse.namike.me/) through a Cloudflare Worker reverse proxy.

## Structure

- `data/entries/YYYY-MM-DD.json` — Structured daily entry (verbatim Bible.com `EN` + `zh-TW` quotes, original-language word study, historical context, cross-references, daily habits & tensions, sourced workplace notes).
- `scripts/build_site.py` — Zero-dependency Python 3 generator that validates entries and outputs:
  - `YYYY/MM/DD/index.html` (canonical static page per day)
  - `index.html` (latest entry at site root)
  - `data/index.json` (archive search manifest)
- `assets/styles.css` & `assets/app.js` — Editorial broadsheet styling, dark/light theme toggle, study tabs, copy/share actions, and slide-over archive search.
- `design/mock/` — Approved v2 design mock (`index.html`), `DESIGN.md` spec, and preview screenshots.
- `design/logo/` — Dawn-Scripture logo mark, favicon, and PWA icon sources with the preview sheet.
- `skills/daily-verse-site-publishing/` — Agent skill describing the daily publishing, copy, and accessibility rules.
- `skills/humanizer/` — Third-party writing skill ([blader/humanizer](https://github.com/blader/humanizer), MIT, see its `LICENSE`) used for the copy pass.
- `worker/` — Cloudflare Worker (`daily-verse-proxy`) bound to `verse.namike.me` (`custom_domain: true`) forwarding requests to `https://mike623.github.io/daily-verse/`.

## Build & Proxy Deploy

```bash
python3 scripts/build_site.py
cd worker && wrangler deploy
```
