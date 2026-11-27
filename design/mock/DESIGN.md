# Daily Bible Verse & Reflection — v2 Design Spec (`*.namike.me`)

Design specification for a pure-static, bilingual (`EN` + `zh-TW`) daily devotional site hosted on GitHub Pages behind Cloudflare (`*.namike.me`). Designed for seekers exploring Christianity: warm, calm, contemplative, editorial, and free of visual noise.

---

## 1. What Changed from v1 → v2

User feedback on v1: *"need more simplicity and eyecatch"*.

1. **Above-the-Fold Eye-Catch (Archival Gallery Broadsheet Stage):**
   - Replaced v1's flat beige 50/50 split with one sculptural **deep-obsidian Hero Broadsheet Stage** (`#161412` on Light `#F8F4EC`; `#1C1915` with copper hairline on Dark `#12110F`) so the daily scripture commands immediate attention.
   - Stacked the bilingual verses into a clear typographic hierarchy: large Traditional Chinese CUNP-神 centerpiece (`clamp(1.48rem, 3vw, 2.18rem)`), separated by a `40px × 2px` rule from the English NIV verse (`clamp(1.04rem, 1.48vw, 1.22rem)`).
   - Added two quiet editorial focal accents inside the hero stage: a top-right **Dawn Horizon** geometric SVG (concentric `1px` arcs + horizon line + vermilion rising-sun disc) and a low-opacity italic `Newsreader` chapter:verse watermark (`1:8`) in the lower-right.
2. **Radical Simplicity (Minimal Chrome + Tabbed Study Sanctuary):**
   - Collapsed the 2-row mobile header and pill steppers into a **single-row borderless header** (`64px` desktop / `56px` mobile) across all viewports.
   - Removed duplicate reference titles and the boxed utility bar/keyboard-hint row; consolidated Bible.com attribution links and `複製經文` / `分享連結` into a single hairline footer inside the hero stage.
   - Replaced the long 3-section vertical scroll wall with an underline-tabbed **Study Sanctuary** (`01 經文脈絡` · `02 實踐與張力` · `03 職場應用`) plus a quiet `展開全文` toggle (and auto-expansion in `@media print`), cutting initial page height by more than half while preserving every word of static semantic HTML in the DOM.

---

## 2. Visual Craft Guardrails

- **Color discipline:** Zero Tailwind indigo (`#6366f1` / `#4f46e5`), zero multi-stop hero gradients, zero pure `#000000` or `#FFFFFF` surfaces.
- **Iconography:** Zero emoji icons in UI/headings; use `1.6px` stroke monoline SVGs inheriting `currentColor`.
- **Surfaces:** Flat recessed surfaces with `1px` hairline borders; zero rounded cards with thick colored left borders.
- **Typography:** Never use `text-align: justify` on body copy (prevents CJK/Latin spacing rivers).
- **Accent restraint:** Cap visible `--accent` uses to **≤ 2 per viewport** (the hero Dawn Horizon sun disc + the active study tab underline).

---

## 3. Color Tokens

Define all colors as CSS custom properties on `:root` and `[data-theme="dark"]` (falling back to `prefers-color-scheme: dark` when no user choice is saved in `localStorage`).

### Canvas & Study Tokens

| Role | Token | Light (`Alabaster & Ink`) | Dark (`Candlelight Obsidian`) | Purpose |
|---|---|---|---|---|
| Page background | `--bg` | `#F8F4EC` | `#12110F` | Primary gallery canvas |
| Recessed surface | `--surface` | `#EFE8DB` | `#1B1815` | Word study box, tensions panel, hover fills |
| Elevated surface | `--surface-elevated` | `#FBF8F2` | `#211D19` | Archive slide-over drawer |
| Primary ink | `--fg` | `#1A1714` | `#F5EFE4` | Headings, active tabs, scripture labels |
| Secondary ink | `--fg-secondary` | `#48423B` | `#C8C0B4` | Long-form zh-TW prose |
| Muted metadata | `--muted` | `#72685E` | `#988E82` | Inactive tabs, attributions, timestamps |
| Hairline border | `--border` | `rgba(26, 23, 20, 0.11)` | `rgba(245, 239, 228, 0.11)` | Section dividers, matrix rules |
| Strong hairline | `--border-strong` | `rgba(26, 23, 20, 0.22)` | `rgba(245, 239, 228, 0.24)` | Focus rings, input & link underlines |
| Single accent | `--accent` | `#C84B2A` | `#E07852` | Hero sun disc, active tab underline, active archive date |
| Soft accent tint | `--accent-soft` | `rgba(200, 75, 42, 0.08)` | `rgba(224, 120, 82, 0.14)` | Active archive item tint |

### Hero Broadsheet Stage Tokens

| Role | Token | Light | Dark |
|---|---|---|---|
| Stage canvas | `--hero-bg` | `#161412` | `#1C1915` |
| Stage ring border | `--hero-stage-ring` | `rgba(22, 20, 18, 0.10)` | `rgba(224, 120, 82, 0.26)` |
| Primary verse ink | `--hero-fg` | `#F6F1E7` | `#F5EFE4` |
| Secondary verse ink | `--hero-fg-muted` | `rgba(246, 241, 231, 0.76)` | `rgba(245, 239, 228, 0.78)` |
| Kicker / version ink | `--hero-fg-subtle` | `rgba(246, 241, 231, 0.54)` | `rgba(245, 239, 228, 0.54)` |
| Dawn arc stroke | `--hero-arc` | `rgba(246, 241, 231, 0.11)` | `rgba(224, 120, 82, 0.15)` |
| Inner dawn arc | `--hero-arc-warm` | `rgba(200, 75, 42, 0.42)` | `rgba(224, 120, 82, 0.45)` |
| Chapter watermark | `--hero-numeral` | `rgba(246, 241, 231, 0.055)` | `rgba(245, 239, 228, 0.05)` |

---

## 4. Typography Pairing & Scale (EN + zh-TW)

Load Google Fonts (`display=swap`) with tuned macOS/iOS/Windows CJK fallbacks:

```css
--font-serif: 'Newsreader', 'Noto Serif TC', 'Iowan Old Style', 'Songti TC', 'Georgia', serif;
--font-sans:  'Source Sans 3', 'Noto Sans TC', 'PingFang TC', 'Hiragino Sans CNS', sans-serif;
--font-mono:  'JetBrains Mono', ui-monospace, 'SFMono-Regular', monospace;
```

| Role | Font Stack | Size | Line Height | Tracking | Weight |
|---|---|---|---|---|---|
| Hero Verse (zh-TW) | `--font-serif` | `clamp(1.48rem, 3vw, 2.18rem)` | `1.68` | `0.02em` | `500` |
| Hero Verse (EN) | `--font-serif` | `clamp(1.04rem, 1.48vw, 1.22rem)` | `1.64` | `-0.005em` | `400` |
| Chapter Watermark | `Newsreader` italic | `clamp(6rem, 13.5vw, 10.5rem)` | `0.82` | `-0.04em` | `400` |
| Prose Body (zh-TW) | `--font-sans` | `16.5px` (`max-width: 66ch`) | `1.86` | `0.01em` | `400` |
| Study Tabs / UI Labels | `--font-sans` | `13px–14.5px` | `1.4` | `0.015em` | `500` |
| Kickers / Dates / Numbers | `--font-mono` | `11px–12.5px` | `1.4` | `0.08em` | `500` |

- Apply `font-variant-numeric: tabular-nums` to all dates (`2026.11.24`), tab indices (`01`–`03`), watermarks (`1:8`), and archive rows.

---

## 5. Layout Hierarchy & Responsive Behavior

- **Outer Container:** `max-width: 960px`, horizontal gutters `clamp(16px, 4vw, 40px)`.
- **Single-Row Header (`64px` desktop / `56px` mobile):**
  - Left: Minimal dawn-horizon SVG mark + `晨光` (`Daily Verse` hidden `< 520px`).
  - Center: Borderless inline date stepper `‹ 2026.11.24 ›` (`‹ 11/24 ›` `< 520px`).
  - Right: Borderless `歸檔` trigger (icon-only `< 520px` with `aria-label`) + Sun/Moon theme toggle.
- **Hero Broadsheet Stage (`18px` radius desktop / `14px` mobile):**
  - Top-right Dawn Horizon SVG (`pointer-events: none`, scaled to `165px` on mobile) + lower-right ghosted chapter:verse watermark.
  - Eyebrow kicker → commanding zh-TW quote → `40px × 2px` rule → EN quote → bottom hairline bar with `<h1 class="hero-ref-group">` (Bible.com attribution links for `CUNP-神` & `NIV`) and `複製經文` / `分享連結` ghost buttons.
- **Tabbed Study Sanctuary:**
  - Underline tab bar (`role="tablist"`): `01 經文脈絡` (active default) · `02 實踐與張力` · `03 職場應用`, paired with a right-aligned `展開全文` / `分頁閱讀` toggle.
  - All 3 `role="tabpanel"` sections stay rendered in static HTML inside the page so search crawlers, screen readers, and `@media print` access every word without JavaScript hydration dependencies.
- **Quiet Footer:** Previous day shortcut, `瀏覽完整歸檔` trigger, and `verse.namike.me` edition label.

---

## 6. Interactive Features & Shortcuts

- **Slide-Over Archive Drawer (`width: min(440px, 100vw)`):** Live search across ISO date, Chinese/English scripture reference, and summary snippet, highlighting the active entry in `--accent`.
- **Copy & Share Ergonomics:** Copies formatted bilingual quotes + canonical link with `aria-live="polite"` toast feedback and `textarea` fallback.
- **Keyboard Shortcuts (Desktop):** `←` / `→` switch days, `1` / `2` / `3` switch study tabs, `A` toggles Archive drawer, `T` toggles Light/Dark theme, `Escape` closes drawer (ignored inside inputs).

---

## 7. GitHub Pages Static Architecture (`*.namike.me`)

Zero build step required (compatible with a daily routine commit):

```text
/
├── index.html                  # Latest day entry + inline semantic study panels
├── assets/
│   ├── styles.css              # Design tokens + broadsheet & tabbed layout
│   └── app.js                  # Tabs, expand-all, theme toggle, copy/share, archive drawer
├── data/
│   ├── index.json              # Archive manifest: [{ date, refZh, refEn, snippet, path }]
│   └── entries/
│       └── 2026-11-24.json     # Structured bilingual devotional JSON per day
└── 2026/11/24/
    └── index.html              # Static pre-rendered page per day for Cloudflare edge caching
```
