#!/usr/bin/env python3
"""Static site generator for the bilingual Daily Bible Verse site."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "data" / "entries"
INDEX_JSON_PATH = ROOT / "data" / "index.json"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WEEKDAYS_ZH = ("週一", "週二", "週三", "週四", "週五", "週六", "週日")
PLACEHOLDERS = (
    "示範預覽",
    "Sample Preview",
    "示範歸檔摘要",
    "Sample archive summary",
    "TODO",
    "TBD",
)
REQUIRED_STR_FIELDS = (
    "date",
    "chapterVerse",
    "refZh",
    "versionZh",
    "quoteZh",
    "linkZh",
    "refEn",
    "versionEn",
    "quoteEn",
    "linkEn",
    "snippet",
    "contextHeading",
)

FAVICON_DATA_URI = (
    "data:image/svg+xml,"
    "%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2024%2024%27%3E"
    "%3Crect%20width%3D%2724%27%20height%3D%2724%27%20rx%3D%275%27%20fill%3D%27%23161412%27%2F%3E"
    "%3Ccircle%20cx%3D%2712%27%20cy%3D%2713%27%20r%3D%274%27%20fill%3D%27%23C84B2A%27%2F%3E"
    "%3Cline%20x1%3D%274%27%20y1%3D%2717%27%20x2%3D%2720%27%20y2%3D%2717%27%20stroke%3D%27%23F6F1E7%27%20stroke-width%3D%271.5%27%20stroke-linecap%3D%27round%27%2F%3E"
    "%3C%2Fsvg%3E"
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require_non_empty_str(obj: dict, key: str, source: str) -> str:
    val = obj.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ValueError(f"{source}: missing or empty string field '{key}'")
    text = val.strip()
    for marker in PLACEHOLDERS:
        if marker in text:
            raise ValueError(f"{source}: placeholder text '{marker}' found in '{key}'")
    return text


def require_url(obj: dict, key: str, source: str) -> str:
    url = require_non_empty_str(obj, key, source)
    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValueError(f"{source}: '{key}' must start with http:// or https://")
    return url


def load_and_validate_entry(path: Path) -> dict:
    source = str(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: entry JSON must be an object")

    for field in REQUIRED_STR_FIELDS:
        require_non_empty_str(raw, field, source)

    date_str = raw["date"].strip()
    if not DATE_RE.match(date_str):
        raise ValueError(f"{source}: invalid date format '{date_str}', expected YYYY-MM-DD")
    if path.stem != date_str:
        raise ValueError(f"{source}: filename '{path.name}' must match date '{date_str}.json'")

    parsed_date = dt.date.fromisoformat(date_str)
    require_url(raw, "linkZh", source)
    require_url(raw, "linkEn", source)

    ctx_paras = raw.get("contextParagraphs")
    if not isinstance(ctx_paras, list) or not ctx_paras or not all(isinstance(p, str) and p.strip() for p in ctx_paras):
        raise ValueError(f"{source}: 'contextParagraphs' must be a non-empty list of strings")

    cross_refs = raw.get("crossRefs")
    if not isinstance(cross_refs, list) or not cross_refs:
        raise ValueError(f"{source}: 'crossRefs' must be a non-empty list")
    for idx, item in enumerate(cross_refs):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: crossRefs[{idx}] must be an object")
        require_non_empty_str(item, "ref", f"{source}:crossRefs[{idx}]")
        require_non_empty_str(item, "note", f"{source}:crossRefs[{idx}]")

    habits = raw.get("habits")
    if not isinstance(habits, list) or not habits:
        raise ValueError(f"{source}: 'habits' must be a non-empty list")
    for idx, item in enumerate(habits):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: habits[{idx}] must be an object")
        require_non_empty_str(item, "title", f"{source}:habits[{idx}]")
        require_non_empty_str(item, "body", f"{source}:habits[{idx}]")

    tensions = raw.get("tensions")
    if not isinstance(tensions, list) or not tensions:
        raise ValueError(f"{source}: 'tensions' must be a non-empty list")
    for idx, item in enumerate(tensions):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: tensions[{idx}] must be an object")
        require_non_empty_str(item, "title", f"{source}:tensions[{idx}]")
        require_non_empty_str(item, "body", f"{source}:tensions[{idx}]")

    workplace = raw.get("workplace")
    if not isinstance(workplace, list) or not workplace:
        raise ValueError(f"{source}: 'workplace' must be a non-empty list")
    for idx, item in enumerate(workplace):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: workplace[{idx}] must be an object")
        require_non_empty_str(item, "kicker", f"{source}:workplace[{idx}]")
        require_non_empty_str(item, "title", f"{source}:workplace[{idx}]")
        require_non_empty_str(item, "body", f"{source}:workplace[{idx}]")
        require_non_empty_str(item, "source", f"{source}:workplace[{idx}]")

    word_study = raw.get("wordStudy")
    normalized_ws = None
    if word_study is not None:
        if not isinstance(word_study, dict):
            raise ValueError(f"{source}: 'wordStudy' must be an object or null")
        lexeme = require_non_empty_str(word_study, "lexeme", f"{source}:wordStudy")
        translit = require_non_empty_str(word_study, "translit", f"{source}:wordStudy")
        gloss = require_non_empty_str(word_study, "gloss", f"{source}:wordStudy")
        ws_body = require_non_empty_str(word_study, "body", f"{source}:wordStudy")
        lang = (word_study.get("lang") or "he").strip() if isinstance(word_study.get("lang"), str) else "he"
        default_dir = "rtl" if lang == "he" else "ltr"
        direction = (word_study.get("dir") or default_dir).strip() if isinstance(word_study.get("dir"), str) else default_dir
        if direction not in ("rtl", "ltr"):
            direction = default_dir
        normalized_ws = {
            "lexeme": lexeme,
            "translit": translit,
            "gloss": gloss,
            "body": ws_body,
            "lang": lang,
            "dir": direction,
        }

    yyyy, mm, dd = date_str.split("-")
    weekday = raw.get("weekday")
    if isinstance(weekday, str) and weekday.strip():
        weekday_val = weekday.strip()
    else:
        weekday_val = WEEKDAYS_ZH[parsed_date.weekday()]

    return {
        "date": date_str,
        "dateDot": f"{yyyy}.{mm}.{dd}",
        "shortLabel": f"{mm}/{dd}",
        "weekday": weekday_val,
        "path": f"{yyyy}/{mm}/{dd}/",
        "chapterVerse": raw["chapterVerse"].strip(),
        "refZh": raw["refZh"].strip(),
        "versionZh": raw["versionZh"].strip(),
        "quoteZh": raw["quoteZh"].strip(),
        "linkZh": raw["linkZh"].strip(),
        "refEn": raw["refEn"].strip(),
        "versionEn": raw["versionEn"].strip(),
        "quoteEn": raw["quoteEn"].strip(),
        "linkEn": raw["linkEn"].strip(),
        "snippet": raw["snippet"].strip(),
        "wordStudy": normalized_ws,
        "contextHeading": raw["contextHeading"].strip(),
        "contextParagraphs": [p.strip() for p in ctx_paras],
        "crossRefs": [{"ref": c["ref"].strip(), "note": c["note"].strip()} for c in cross_refs],
        "habits": [{"title": h["title"].strip(), "body": h["body"].strip()} for h in habits],
        "tensions": [{"title": t["title"].strip(), "body": t["body"].strip()} for t in tensions],
        "workplace": [
            {
                "kicker": w["kicker"].strip(),
                "title": w["title"].strip(),
                "body": w["body"].strip(),
                "source": w["source"].strip(),
            }
            for w in workplace
        ],
    }


def render_word_study(ws: dict | None) -> str:
    if not ws:
        return ""
    return f"""
          <aside class="word-study" aria-label="原文詞彙筆記">
            <div class="word-study-top">
              <span class="word-study-tag">原文詞彙筆記</span>
              <div class="word-study-lexeme">
                <span class="word-study-hebrew" lang="{esc(ws['lang'])}" dir="{esc(ws['dir'])}">{esc(ws['lexeme'])}</span>
                <span class="word-study-translit" lang="en">{esc(ws['translit'])}</span>
              </div>
              <span class="word-study-gloss">{esc(ws['gloss'])}</span>
            </div>
            <p>{esc(ws['body'])}</p>
          </aside>"""


def render_page(
    entry: dict,
    older: dict | None,
    newer: dict | None,
    archive_manifest: list[dict],
    base: str,
) -> str:
    title = f"晨光 · Daily Verse — {entry['refZh']} · {entry['refEn']}"
    desc = f"{entry['dateDot']} {entry['refZh']} ({entry['versionZh']}) · {entry['refEn']} ({entry['versionEn']}) — {entry['snippet']}"
    watermark_class = "hero-watermark tabular is-long" if len(entry["chapterVerse"]) > 4 else "hero-watermark tabular"

    prev_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>'
    next_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>'

    if older:
        prev_control = f'<a class="day-btn" id="prevDayBtn" href="{esc(base + older["path"])}" aria-label="前一日 ({esc(older["shortLabel"])})" title="前一日 (←)">{prev_svg}</a>'
        footer_prev = f'<a class="footer-link" id="footerPrevBtn" href="{esc(base + older["path"])}">← 前一日 ({esc(older["shortLabel"])})</a>'
    else:
        prev_control = f'<span class="day-btn is-disabled" id="prevDayBtn" aria-disabled="true" title="已是最早收錄日">{prev_svg}</span>'
        footer_prev = '<span class="footer-link is-disabled" id="footerPrevBtn" aria-disabled="true">已是最早收錄日</span>'

    if newer:
        next_control = f'<a class="day-btn" id="nextDayBtn" href="{esc(base + newer["path"])}" aria-label="後一日 ({esc(newer["shortLabel"])})" title="後一日 (→)">{next_svg}</a>'
    else:
        next_control = f'<span class="day-btn is-disabled" id="nextDayBtn" aria-disabled="true" title="已是最新一日經文">{next_svg}</span>'

    ctx_html = "\n                ".join(f"<p>{esc(p)}</p>" for p in entry["contextParagraphs"])
    cross_refs_html = "\n                ".join(
        f"""<li class="crossref-item">
                  <span class="crossref-ref">{esc(c['ref'])}</span>
                  <span class="crossref-note">{esc(c['note'])}</span>
                </li>"""
        for c in entry["crossRefs"]
    )
    habits_html = "\n                ".join(
        f"""<li class="habit-item">
                  <span class="habit-index tabular">{i:02d}</span>
                  <div>
                    <h4 class="item-title">{esc(h['title'])}</h4>
                    <p class="item-body">{esc(h['body'])}</p>
                  </div>
                </li>"""
        for i, h in enumerate(entry["habits"], start=1)
    )
    tensions_html = "\n                ".join(
        f"""<li class="tension-item">
                  <h4 class="item-title">{esc(t['title'])}</h4>
                  <p class="item-body">{esc(t['body'])}</p>
                </li>"""
        for t in entry["tensions"]
    )
    workplace_html = "\n            ".join(
        f"""<article class="workplace-cell">
              <div>
                <span class="workplace-kicker">{esc(w['kicker'])}</span>
                <h3 class="item-title">{esc(w['title'])}</h3>
                <p class="item-body">{esc(w['body'])}</p>
              </div>
              <div class="workplace-source">{esc(w['source'])}</div>
            </article>"""
        for w in entry["workplace"]
    )

    archive_json = json.dumps(archive_manifest, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html
  lang="zh-Hant"
  data-theme="light"
  data-base="{esc(base)}"
  data-date="{esc(entry['date'])}"
  data-entry-path="{esc(entry['path'])}"
  data-ref-zh="{esc(entry['refZh'])}"
  data-ver-zh="{esc(entry['versionZh'])}"
  data-ref-en="{esc(entry['refEn'])}"
  data-ver-en="{esc(entry['versionEn'])}"
>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:type" content="website" />
  <link rel="icon" type="image/svg+xml" href="{FAVICON_DATA_URI}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Noto+Sans+TC:wght@400;500;600&family=Noto+Serif+TC:wght@400;500;600&family=Source+Sans+3:wght@400;500;600&display=swap"
    rel="stylesheet"
  />
  <link rel="stylesheet" href="{esc(base)}assets/styles.css" />
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a href="{esc(base)}" class="brand" id="brandHomeLink" title="回到最新一日經文">
        <span class="brand-mark" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 17h18"/>
            <path d="M7 17a5 5 0 0 1 10 0"/>
            <path d="M12 5v3M6.2 8.2l1.8 1.8M17.8 8.2L16 10"/>
          </svg>
        </span>
        <span class="brand-text">
          <span class="brand-zh">晨光</span>
          <span class="brand-en">Daily Verse</span>
        </span>
      </a>

      <nav class="day-nav" aria-label="每日經文切換">
        {prev_control}
        <span class="day-current tabular">
          <span class="date-full" id="currentDateFull">{esc(entry['dateDot'])}</span>
          <span class="date-short" id="currentDateShort">{esc(entry['shortLabel'])}</span>
        </span>
        {next_control}
      </nav>

      <div class="header-actions">
        <button type="button" class="ghost-icon-btn" id="openArchiveBtn" aria-haspopup="dialog" aria-controls="archiveDrawer" aria-label="開啟每日經文歸檔" title="經文歸檔 (A)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <path d="M16 2v4M8 2v4M3 10h18"/>
          </svg>
          <span class="archive-label">歸檔</span>
        </button>
        <button type="button" class="ghost-icon-btn ghost-icon-btn--square" id="themeToggleBtn" aria-label="切換淺色或深色閱讀模式" title="切換閱讀模式 (T)">
          <svg id="themeIconSun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="display:none;" aria-hidden="true">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          </svg>
          <svg id="themeIconMoon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
      </div>
    </div>
  </header>

  <main id="top">
    <article id="entryRoot" aria-live="polite">
      <section class="hero-stage" aria-label="今日雙語經文">
        <svg class="hero-motif" viewBox="0 0 300 220" fill="none" aria-hidden="true">
          <circle cx="228" cy="96" r="144" stroke="var(--hero-arc)" stroke-width="1"/>
          <circle cx="228" cy="96" r="102" stroke="var(--hero-arc)" stroke-width="1"/>
          <circle cx="228" cy="96" r="62" stroke="var(--hero-arc-warm)" stroke-width="1"/>
          <line x1="76" y1="96" x2="300" y2="96" stroke="var(--hero-arc)" stroke-width="1"/>
          <circle cx="228" cy="96" r="12" fill="var(--accent)"/>
        </svg>

        <div class="{watermark_class}" id="heroWatermark" aria-hidden="true">{esc(entry['chapterVerse'])}</div>

        <div class="hero-content">
          <div class="hero-kicker tabular" id="heroKicker">DAILY VERSE · {esc(entry['dateDot'])} · {esc(entry['weekday'])}</div>

          <blockquote class="hero-quote-zh" id="heroQuoteZh">{esc(entry['quoteZh'])}</blockquote>

          <div class="hero-dash" aria-hidden="true"></div>

          <blockquote class="hero-quote-en" id="heroQuoteEn" lang="en">{esc(entry['quoteEn'])}</blockquote>

          <div class="hero-footer">
            <h1 class="hero-ref-group">
              <a class="hero-ref-link" id="heroLinkZh" href="{esc(entry['linkZh'])}" target="_blank" rel="noopener noreferrer">
                <span id="heroRefZh">{esc(entry['refZh'])}</span>
                <span class="ref-ver" id="heroVerZh">{esc(entry['versionZh'])}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>
              </a>
              <span class="ref-sep" aria-hidden="true">·</span>
              <a class="hero-ref-link hero-ref-en" id="heroLinkEn" href="{esc(entry['linkEn'])}" target="_blank" rel="noopener noreferrer" lang="en">
                <span id="heroRefEn">{esc(entry['refEn'])}</span>
                <span class="ref-ver" id="heroVerEn">{esc(entry['versionEn'])}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>
              </a>
            </h1>

            <div class="hero-actions">
              <button type="button" class="hero-ghost-btn" id="copyVerseBtn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="9" y="9" width="13" height="13" rx="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                <span>複製經文</span>
              </button>
              <button type="button" class="hero-ghost-btn" id="copyLinkBtn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                <span>分享連結</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="study-sanctuary" id="studySanctuary" data-expanded="false" aria-label="經文默想與應用">
        <div class="study-tabs-bar">
          <div class="tab-list" role="tablist" aria-label="經文研讀分頁">
            <button type="button" class="study-tab" role="tab" id="tab-context" aria-controls="panel-context" aria-selected="true" data-tab="context">
              <span class="tab-num tabular">01</span>
              <span>經文脈絡</span>
            </button>
            <button type="button" class="study-tab" role="tab" id="tab-practice" aria-controls="panel-practice" aria-selected="false" data-tab="practice">
              <span class="tab-num tabular">02</span>
              <span>實踐與張力</span>
            </button>
            <button type="button" class="study-tab" role="tab" id="tab-workplace" aria-controls="panel-workplace" aria-selected="false" data-tab="workplace">
              <span class="tab-num tabular">03</span>
              <span>職場應用</span>
            </button>
          </div>

          <button type="button" class="expand-all-btn" id="expandAllBtn" aria-pressed="false">展開全文</button>
        </div>

        <section class="study-panel" id="panel-context" role="tabpanel" aria-labelledby="tab-context">
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular">01</span>
            <h2 class="panel-expanded-title">經文背景、脈絡與相似段落</h2>
          </div>{render_word_study(entry['wordStudy'])}

          <div class="context-split">
            <div>
              <h3 class="subsection-heading">{esc(entry['contextHeading'])}</h3>
              <div class="prose-column">
                {ctx_html}
              </div>
            </div>

            <div>
              <h3 class="subsection-heading">相似段落與跨卷對照</h3>
              <ul class="crossref-list">
                {cross_refs_html}
              </ul>
            </div>
          </div>
        </section>

        <section class="study-panel" id="panel-practice" role="tabpanel" aria-labelledby="tab-practice" hidden>
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular">02</span>
            <h2 class="panel-expanded-title">日常實踐方式與現實難處</h2>
          </div>

          <div class="practice-grid">
            <div>
              <h3 class="column-label">日常實踐 · 微習慣</h3>
              <ol class="habit-list">
                {habits_html}
              </ol>
            </div>

            <div class="tensions-panel">
              <h3 class="column-label">現實難處 · 真實張力</h3>
              <ul class="tension-list">
                {tensions_html}
              </ul>
            </div>
          </div>
        </section>

        <section class="study-panel" id="panel-workplace" role="tabpanel" aria-labelledby="tab-workplace" hidden>
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular">03</span>
            <h2 class="panel-expanded-title">他人如何把這節經文用在日常工作</h2>
          </div>

          <div class="workplace-grid">
            {workplace_html}
          </div>
        </section>
      </section>
    </article>
  </main>

  <footer class="site-footer">
    <div class="footer-links">
      {footer_prev}
      <button type="button" class="footer-link" id="footerArchiveBtn">瀏覽完整歸檔</button>
    </div>
    <span class="tabular">verse.namike.me · 每日雙語經文與默想</span>
  </footer>

  <div class="drawer-backdrop" id="drawerBackdrop" hidden></div>
  <aside class="archive-drawer" id="archiveDrawer" role="dialog" aria-modal="true" aria-labelledby="archiveDrawerTitle" hidden>
    <div class="drawer-header">
      <h2 class="drawer-title" id="archiveDrawerTitle">每日經文歸檔</h2>
      <button type="button" class="ghost-icon-btn ghost-icon-btn--square" id="closeArchiveBtn" aria-label="關閉歸檔視窗">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <div class="drawer-search-wrap">
      <label class="sr-only" for="archiveSearchInput">搜尋日期或經文出處</label>
      <input
        type="search"
        id="archiveSearchInput"
        class="drawer-search"
        placeholder="搜尋日期或經文（例如 {esc(entry['date'])}、{esc(entry['refZh'])}）"
        autocomplete="off"
      />
    </div>
    <div class="drawer-body" id="archiveBody">
      <div id="archiveGroups"></div>
      <p class="archive-empty" id="archiveEmpty" hidden>找不到符合條件的每日默想紀錄。</p>
    </div>
  </aside>

  <div class="toast" id="toastEl" role="status" aria-live="polite"></div>

  <script id="archiveFallback" type="application/json">{archive_json}</script>
  <script defer src="{esc(base)}assets/app.js"></script>
</body>
</html>
"""


def build() -> None:
    if not ENTRIES_DIR.exists():
        raise FileNotFoundError(f"Missing entries directory: {ENTRIES_DIR}")

    entry_files = sorted(ENTRIES_DIR.glob("*.json"))
    if not entry_files:
        raise RuntimeError(f"No entry JSON files found in {ENTRIES_DIR}")

    entries = [load_and_validate_entry(p) for p in entry_files]
    entries.sort(key=lambda e: e["date"], reverse=True)

    manifest = [
        {
            "date": e["date"],
            "dateDot": e["dateDot"],
            "shortLabel": e["shortLabel"],
            "weekday": e["weekday"],
            "refZh": e["refZh"],
            "refEn": e["refEn"],
            "snippet": e["snippet"],
            "path": e["path"],
        }
        for e in entries
    ]
    INDEX_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    built_paths: list[str] = []
    for idx, entry in enumerate(entries):
        older = entries[idx + 1] if idx + 1 < len(entries) else None
        newer = entries[idx - 1] if idx - 1 >= 0 else None

        day_dir = ROOT / entry["path"]
        day_dir.mkdir(parents=True, exist_ok=True)
        day_html = render_page(entry, older=older, newer=newer, archive_manifest=manifest, base="../../../")
        (day_dir / "index.html").write_text(day_html, encoding="utf-8")
        built_paths.append(entry["path"] + "index.html")

    latest = entries[0]
    latest_older = entries[1] if len(entries) > 1 else None
    root_html = render_page(latest, older=latest_older, newer=None, archive_manifest=manifest, base="./")
    (ROOT / "index.html").write_text(root_html, encoding="utf-8")

    print(f"Built {len(entries)} archive page(s) + root index.html (latest: {latest['date']} {latest['refZh']} / {latest['refEn']})")
    for rel in built_paths:
        print(f"  - {rel}")


if __name__ == "__main__":
    build()
