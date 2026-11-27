#!/usr/bin/env python3
"""Static site generator for the bilingual Daily Bible Verse site."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from urllib.parse import quote
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

BOOK_CODES = {
    "genesis": "GEN", "exodus": "EXO", "leviticus": "LEV", "numbers": "NUM", "deuteronomy": "DEU",
    "joshua": "JOS", "judges": "JDG", "ruth": "RUT", "1 samuel": "1SA", "2 samuel": "2SA",
    "1 kings": "1KI", "2 kings": "2KI", "1 chronicles": "1CH", "2 chronicles": "2CH", "ezra": "EZR",
    "nehemiah": "NEH", "esther": "EST", "job": "JOB", "psalm": "PSA", "psalms": "PSA",
    "proverbs": "PRO", "ecclesiastes": "ECC", "song of songs": "SNG", "song of solomon": "SNG",
    "isaiah": "ISA", "jeremiah": "JER", "lamentations": "LAM", "ezekiel": "EZK", "daniel": "DAN",
    "hosea": "HOS", "joel": "JOL", "amos": "AMO", "obadiah": "OBA", "jonah": "JON", "micah": "MIC",
    "nahum": "NAM", "habakkuk": "HAB", "zephaniah": "ZEP", "haggai": "HAG", "zechariah": "ZEC",
    "malachi": "MAL", "matthew": "MAT", "mark": "MRK", "luke": "LUK", "john": "JHN", "acts": "ACT",
    "romans": "ROM", "1 corinthians": "1CO", "2 corinthians": "2CO", "galatians": "GAL",
    "ephesians": "EPH", "philippians": "PHP", "colossians": "COL", "1 thessalonians": "1TH",
    "2 thessalonians": "2TH", "1 timothy": "1TI", "2 timothy": "2TI", "titus": "TIT",
    "philemon": "PHM", "hebrews": "HEB", "james": "JAS", "1 peter": "1PE", "2 peter": "2PE",
    "1 john": "1JN", "2 john": "2JN", "3 john": "3JN", "jude": "JUD", "revelation": "REV",
}
# Life-application angles; each entry picks 3-5 that fit the verse.
LIFE_ANGLES = {
    "family": "家庭與關係",
    "inner": "內心與情緒",
    "body": "身體與休息",
    "money": "金錢與消費",
    "digital": "數位生活",
    "community": "群體與鄰舍",
    "suffering": "苦難與等候",
    "workplace": "職場",
}
EDITOR_SOURCE = "編者默想"

# Bible.com version ids, verified against live verse pages.
VERSION_IDS = {"NIV": 111, "CUNP-神": 46}
REF_RE = re.compile(r"^(.+?)\s+(\d+):(\d+)(?:\s*[-–]\s*(\d+))?$")


def bible_permalink(ref_en: str, version: str, locale: str) -> str | None:
    """Permanent bible.com link for one passage, e.g. /zh-TW/bible/46/ISA.26.3.CUNP-神."""
    m = REF_RE.match(ref_en.strip())
    vid = VERSION_IDS.get(version)
    if not m or vid is None:
        return None
    code = BOOK_CODES.get(m.group(1).strip().lower())
    if not code:
        return None
    verses = m.group(3) + (f"-{m.group(4)}" if m.group(4) else "")
    return f"https://www.bible.com/{locale}/bible/{vid}/{code}.{m.group(2)}.{verses}.{quote(version)}"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def asset_hash(rel_path: str) -> str:
    data = (ROOT / rel_path).read_bytes()
    return hashlib.sha256(data).hexdigest()[:8]


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
    link_zh = bible_permalink(raw["refEn"], raw["versionZh"].strip(), "zh-TW") or raw["linkZh"].strip()
    link_en = bible_permalink(raw["refEn"], raw["versionEn"].strip(), "en-GB") or raw["linkEn"].strip()
    if "verse-of-the-day" in link_zh or "verse-of-the-day" in link_en:
        raise ValueError(f"{source}: could not build a permanent bible.com link for '{raw['refEn']}'; add the book to BOOK_CODES or the version to VERSION_IDS")

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

    life_items: list[dict] = []
    life = raw.get("life")
    if life is not None:
        if not isinstance(life, list) or not 3 <= len(life) <= 5:
            raise ValueError(f"{source}: 'life' must be a list of 3-5 items")
        for idx, item in enumerate(life):
            where = f"{source}:life[{idx}]"
            if not isinstance(item, dict):
                raise ValueError(f"{where} must be an object")
            angle = require_non_empty_str(item, "angle", where)
            if angle not in LIFE_ANGLES:
                raise ValueError(f"{where}: unknown angle '{angle}', expected one of {sorted(LIFE_ANGLES)}")
            life_items.append({
                "angle": angle,
                "tag": LIFE_ANGLES[angle],
                "title": require_non_empty_str(item, "title", where),
                "body": require_non_empty_str(item, "body", where),
                "source": require_non_empty_str(item, "source", where),
            })
        if len({i["angle"] for i in life_items}) != len(life_items):
            raise ValueError(f"{source}: each 'life' angle may appear only once")
    else:
        # Legacy entries (before 2026-11-27) only have workplace cards.
        workplace = raw.get("workplace")
        if not isinstance(workplace, list) or not workplace:
            raise ValueError(f"{source}: needs a 'life' list (or legacy 'workplace' list)")
        for idx, item in enumerate(workplace):
            where = f"{source}:workplace[{idx}]"
            if not isinstance(item, dict):
                raise ValueError(f"{where} must be an object")
            kicker = require_non_empty_str(item, "kicker", where)
            life_items.append({
                "angle": "workplace",
                "tag": f"{LIFE_ANGLES['workplace']} · {kicker}",
                "title": require_non_empty_str(item, "title", where),
                "body": require_non_empty_str(item, "body", where),
                "source": require_non_empty_str(item, "source", where),
            })

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
        "path": f"verse/{yyyy}/{mm}/{dd}/",
        "chapterVerse": raw["chapterVerse"].strip(),
        "refZh": raw["refZh"].strip(),
        "versionZh": raw["versionZh"].strip(),
        "quoteZh": raw["quoteZh"].strip(),
        "linkZh": link_zh,
        "refEn": raw["refEn"].strip(),
        "versionEn": raw["versionEn"].strip(),
        "quoteEn": raw["quoteEn"].strip(),
        "linkEn": link_en,
        "snippet": raw["snippet"].strip(),
        "wordStudy": normalized_ws,
        "contextHeading": raw["contextHeading"].strip(),
        "contextParagraphs": [p.strip() for p in ctx_paras],
        "crossRefs": [{"ref": c["ref"].strip(), "note": c["note"].strip()} for c in cross_refs],
        "habits": [{"title": h["title"].strip(), "body": h["body"].strip()} for h in habits],
        "tensions": [{"title": t["title"].strip(), "body": t["body"].strip()} for t in tensions],
        "life": life_items,
    }


def render_word_study(ws: dict | None) -> str:
    if not ws:
        return ""
    return f"""
          <section class="word-study" aria-label="原文詞彙筆記">
            <div class="word-study-top">
              <span class="word-study-tag">原文詞彙筆記</span>
              <div class="word-study-lexeme">
                <span class="word-study-hebrew" lang="{esc(ws['lang'])}" dir="{esc(ws['dir'])}">{esc(ws['lexeme'])}</span>
                <span class="word-study-translit" lang="en">{esc(ws['translit'])}</span>
              </div>
              <span class="word-study-gloss">{esc(ws['gloss'])}</span>
            </div>
            <p>{esc(ws['body'])}</p>
          </section>"""


def render_page(
    entry: dict,
    older: dict | None,
    newer: dict | None,
    archive_manifest: list[dict],
    base: str,
) -> str:
    title = f"晨光 · Daily Verse｜{entry['refZh']} · {entry['refEn']}"
    desc = f"{entry['dateDot']} {entry['refZh']} ({entry['versionZh']}) · {entry['refEn']} ({entry['versionEn']})｜{entry['snippet']}"
    watermark_class = "hero-watermark tabular is-long" if len(entry["chapterVerse"]) > 4 else "hero-watermark tabular"
    styles_ver = asset_hash("assets/styles.css")
    app_ver = asset_hash("assets/app.js")
    favicon_ver = asset_hash("assets/icons/favicon.svg")
    apple_ver = asset_hash("assets/icons/apple-touch-icon.png")

    prev_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>'
    next_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>'

    if older:
        prev_control = f'<a class="day-btn" id="prevDayBtn" href="{esc(base + older["path"])}" aria-label="前一天（{esc(older["shortLabel"])}）" title="前一天">{prev_svg}</a>'
        footer_prev = f'<a class="footer-link" id="footerPrevBtn" href="{esc(base + older["path"])}">← 前一天（{esc(older["shortLabel"])}）</a>'
    else:
        prev_control = f'<span class="day-btn is-disabled" id="prevDayBtn" role="link" aria-disabled="true" aria-label="前一天：已是最早一篇" title="已是最早一篇">{prev_svg}</span>'
        footer_prev = '<span class="footer-link is-disabled" id="footerPrevBtn">已是最早一篇</span>'

    if newer:
        next_control = f'<a class="day-btn" id="nextDayBtn" href="{esc(base + newer["path"])}" aria-label="後一天（{esc(newer["shortLabel"])}）" title="後一天">{next_svg}</a>'
    else:
        next_control = f'<span class="day-btn is-disabled" id="nextDayBtn" role="link" aria-disabled="true" aria-label="後一天：已是最新一篇" title="已是最新一篇">{next_svg}</span>'

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
                  <span class="habit-index tabular" aria-hidden="true">{i:02d}</span>
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
    life_html = "\n            ".join(
        f"""<article class="workplace-cell" data-angle="{esc(w['angle'])}">
              <div>
                <span class="workplace-kicker">{esc(w['tag'])}</span>
                <h3 class="item-title">{esc(w['title'])}</h3>
                <p class="item-body">{esc(w['body'])}</p>
              </div>
              <div class="workplace-source">{esc(w['source'])}</div>
            </article>"""
        for w in entry["life"]
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:type" content="website" />
  <meta name="theme-color" id="themeColorMeta" content="#F8F4EC" />
  <meta name="mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="晨光" />
  <link rel="manifest" href="{esc(base)}manifest.webmanifest" />
  <link rel="icon" type="image/svg+xml" href="{esc(base)}assets/icons/favicon.svg?v={favicon_ver}" />
  <link rel="apple-touch-icon" sizes="180x180" href="{esc(base)}assets/icons/apple-touch-icon.png?v={apple_ver}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Noto+Sans+TC:wght@400;500;600&family=Noto+Serif+TC:wght@400;500;600&family=Source+Sans+3:wght@400;500;600&display=swap"
    rel="stylesheet"
  />
  <style>.skip-link{{position:absolute;left:12px;top:-48px;z-index:100}}.skip-link:focus{{top:12px}}</style>
  <link rel="stylesheet" href="{esc(base)}assets/styles.css?v={styles_ver}" />
</head>
<body>
  <a class="skip-link" href="#top">跳到今日經文</a>
  <header class="site-header">
    <div class="header-inner">
      <a href="{esc(base)}" class="brand" id="brandHomeLink" title="回到最新一篇" aria-label="晨光 Daily Verse，回到最新一篇">
        <span class="brand-mark" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
            <path d="M 5.2 14.3 A 8.8 8.8 0 0 1 22.8 14.3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <circle cx="14" cy="12.3" r="3.4" fill="var(--accent, #C84B2A)"/>
            <path d="M 3.4 17.7 C 7.4 16.7 11.2 17.6 14 19.7 C 16.8 17.6 20.6 16.7 24.6 17.7" stroke="currentColor" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M 7.2 21.4 C 9.8 20.9 12.1 21.4 14 22.7 C 15.9 21.4 18.2 20.9 20.8 21.4" stroke="currentColor" stroke-opacity="0.48" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="brand-text">
          <span class="brand-zh">晨光</span>
          <span class="brand-en" lang="en">Daily Verse</span>
        </span>
      </a>

      <nav class="day-nav" aria-label="每日經文切換">
        {prev_control}
        <span class="day-current tabular" aria-current="date">
          <span class="date-full" id="currentDateFull">{esc(entry['dateDot'])}</span>
          <span class="date-short" id="currentDateShort">{esc(entry['shortLabel'])}</span>
        </span>
        {next_control}
      </nav>

      <div class="header-actions">
        <button type="button" class="ghost-icon-btn" id="openArchiveBtn" aria-haspopup="dialog" aria-controls="archiveDrawer" aria-label="開啟過往經文" title="過往經文">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <path d="M16 2v4M8 2v4M3 10h18"/>
          </svg>
          <span class="archive-label" aria-hidden="true">過往經文</span>
        </button>
        <button type="button" class="ghost-icon-btn ghost-icon-btn--square" id="themeToggleBtn" aria-label="深色模式" aria-pressed="false" title="切換閱讀模式">
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

  <main id="top" tabindex="-1">
    <article id="entryRoot">
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
          <h1 class="sr-only">今日經文 {esc(entry['dateDot'])}：{esc(entry['refZh'])}</h1>
          <div class="hero-kicker tabular" id="heroKicker"><span lang="en">DAILY VERSE</span> · {esc(entry['dateDot'])} · {esc(entry['weekday'])}</div>

          <blockquote class="hero-quote-zh" id="heroQuoteZh">{esc(entry['quoteZh'])}</blockquote>

          <div class="hero-dash" aria-hidden="true"></div>

          <blockquote class="hero-quote-en" id="heroQuoteEn" lang="en">{esc(entry['quoteEn'])}</blockquote>

          <div class="hero-footer">
            <p class="hero-ref-group">
              <a class="hero-ref-link" id="heroLinkZh" href="{esc(entry['linkZh'])}" target="_blank" rel="noopener noreferrer">
                <span id="heroRefZh">{esc(entry['refZh'])}</span>
                <span class="ref-ver" id="heroVerZh">{esc(entry['versionZh'])}</span>
                <span class="sr-only">（在 Bible.com 新分頁開啟）</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>
              </a>
              <span class="ref-sep" aria-hidden="true">·</span>
              <a class="hero-ref-link hero-ref-en" id="heroLinkEn" href="{esc(entry['linkEn'])}" target="_blank" rel="noopener noreferrer" lang="en">
                <span id="heroRefEn">{esc(entry['refEn'])}</span>
                <span class="ref-ver" id="heroVerEn">{esc(entry['versionEn'])}</span>
                <span class="sr-only">(opens Bible.com in a new tab)</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>
              </a>
            </p>

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
            <button type="button" class="study-tab" role="tab" id="tab-context" aria-controls="panel-context" aria-selected="true" tabindex="0" data-tab="context">
              <span class="tab-num tabular" aria-hidden="true">01</span>
              <span>經文脈絡</span>
            </button>
            <button type="button" class="study-tab" role="tab" id="tab-practice" aria-controls="panel-practice" aria-selected="false" tabindex="-1" data-tab="practice">
              <span class="tab-num tabular" aria-hidden="true">02</span>
              <span>實踐與難處</span>
            </button>
            <button type="button" class="study-tab" role="tab" id="tab-workplace" aria-controls="panel-workplace" aria-selected="false" tabindex="-1" data-tab="workplace">
              <span class="tab-num tabular" aria-hidden="true">03</span>
              <span>生活應用</span>
            </button>
          </div>

          <button type="button" class="expand-all-btn" id="expandAllBtn" aria-controls="panel-context panel-practice panel-workplace">展開全文</button>
        </div>

        <section class="study-panel" id="panel-context" role="tabpanel" aria-labelledby="tab-context" tabindex="0">
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular" aria-hidden="true">01</span>
            <h2 class="panel-expanded-title">經文背景與相關經文</h2>
          </div>{render_word_study(entry['wordStudy'])}

          <div class="context-split">
            <div>
              <h3 class="subsection-heading">{esc(entry['contextHeading'])}</h3>
              <div class="prose-column">
                {ctx_html}
              </div>
            </div>

            <div>
              <h3 class="subsection-heading">相關經文</h3>
              <ul class="crossref-list">
                {cross_refs_html}
              </ul>
            </div>
          </div>
        </section>

        <section class="study-panel" id="panel-practice" role="tabpanel" aria-labelledby="tab-practice" tabindex="0" hidden>
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular" aria-hidden="true">02</span>
            <h2 class="panel-expanded-title">日常實踐與現實難處</h2>
          </div>

          <div class="practice-grid">
            <div>
              <h3 class="column-label">日常小習慣</h3>
              <ol class="habit-list">
                {habits_html}
              </ol>
            </div>

            <div class="tensions-panel">
              <h3 class="column-label">現實難處</h3>
              <ul class="tension-list">
                {tensions_html}
              </ul>
            </div>
          </div>
        </section>

        <section class="study-panel" id="panel-workplace" role="tabpanel" aria-labelledby="tab-workplace" tabindex="0" hidden>
          <div class="panel-expanded-head">
            <span class="panel-expanded-num tabular" aria-hidden="true">03</span>
            <h2 class="panel-expanded-title">把這節經文帶進生活</h2>
          </div>

          <div class="workplace-grid">
            {life_html}
          </div>
        </section>
      </section>
    </article>
  </main>

  <footer class="site-footer">
    <div class="footer-links">
      {footer_prev}
      <button type="button" class="footer-link" id="footerArchiveBtn">瀏覽過往經文</button>
      <button type="button" class="footer-link" id="installPwaBtn" hidden>安裝 App</button>
    </div>
    <span class="tabular">verse.namike.me · 每日雙語經文與默想</span>
  </footer>

  <div class="drawer-backdrop" id="drawerBackdrop" hidden></div>
  <div class="archive-drawer" id="archiveDrawer" role="dialog" aria-modal="true" aria-labelledby="archiveDrawerTitle" hidden>
    <div class="drawer-header">
      <h2 class="drawer-title" id="archiveDrawerTitle">過往經文</h2>
      <button type="button" class="ghost-icon-btn ghost-icon-btn--square" id="closeArchiveBtn" aria-label="關閉過往經文">
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
      <p class="sr-only" id="archiveStatus" role="status" aria-live="polite"></p>
      <p class="archive-empty" id="archiveEmpty" hidden>找不到符合的日期或經文。</p>
    </div>
  </div>

  <div class="toast" id="toastEl" role="status" aria-live="polite" aria-atomic="true"></div>

  <script id="archiveFallback" type="application/json">{archive_json}</script>
  <script defer src="{esc(base)}assets/app.js?v={app_ver}"></script>
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
        day_html = render_page(entry, older=older, newer=newer, archive_manifest=manifest, base="../../../../")
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
