---
name: Daily verse site publishing
description: "Publish a daily Bible verse page to the static daily-verse GitHub
  Pages site: fetch the verse, write the entry JSON, build, commit, push, and
  verify the live result, with accessibility checks. Use for the daily verse
  routine or any edit that ships to verse.namike.me."
---

## Procedure

1. **Sync before editing.** Commit or stash all local changes first, then run `git pull --rebase origin main`. A pull with unstaged changes fails with "cannot pull with rebase: You have unstaged changes", so the commit must come first.

2. **Fetch the source text live.** Open each translation's verse-of-the-day page with the browser tool, extract the date, verbatim verse text, reference and version, then close the tab. Do not use curl or plain HTTP, because these sources return 403. Never write a verse from memory. If a page cannot be loaded or extracted, report the failure with the error and stop.

3. **Find real sources.** Run web searches on the verse reference in each language. Record only sources you actually found, with their names and domains. Never invent a source, because an invented citation is worse than fewer citations.

4. **Write the entry JSON.** Copy the schema from the most recent file in `data/entries/`, and write `data/entries/YYYY-MM-DD.json` using the live date. Fill in the verbatim quotes, a permanent link to the exact verse in each translation, the context paragraphs, 3 to 5 cross-references, 3 habits, 3 tensions, and 4 workplace items. Attribute each workplace item only to a source verified in step 3. Never use the verse-of-the-day page as the verse link, because it changes every day and old pages would point to the wrong verse. The link format is `https://www.bible.com/<locale>/bible/<version id>/<USFM book>.<chapter>.<verse>.<version>`, with the version abbreviation URL-encoded. The build script generates it from the English reference and fails if a verse-of-the-day link would remain. For a new translation, open the verse on the site in the browser, read the version id from its URL, and add it to the script's version table.

5. **Keep copy honest and plain.** Apply these rules to all site text:
   - Summarize Bible passages only from the passage itself. Quote short verses in their own words rather than paraphrasing from memory, because wrong summaries are the most common error.
   - Present scholarly opinion as opinion, such as "scholars generally think", because stated theories read as fact.
   - Do not overstate grammar. A Greek tense or form does not prove a theological claim.
   - Do not promise outcomes, such as prosperity or guaranteed meaning.
   - Avoid long dashes, "not X but Y" contrasts, inflated words, and lists of three where fewer items say more.
   - Use the regional wording the user expects, for example 身分 and 信箱 for Taiwan Traditional Chinese.

6. **Edit the template and assets.** When you change `scripts/build_site.py`, the CSS, or the JS, follow the Page accessibility rules below. Keep the CSS that hides the skip link inline in the `build_site.py` template, not only in `assets/styles.css`, because a cached stylesheet with an old version string can make the link show.

7. **Build and validate.** Run `python3 scripts/build_site.py`. It validates the JSON and regenerates the dated page, the root `index.html`, and `data/index.json`. Fix any validation error before continuing.

8. **Commit and push.** If `git status --porcelain` shows changes, run `git add -A`, commit with the message `Publish daily verse: YYYY-MM-DD (<refEn>)` and the co-author trailer for the bot, then run `git push origin main`. Keep no CNAME file at the repo root, because the custom domain is proxied through a Cloudflare Worker.

9. **Poll the live URL.** GitHub Pages takes time to rebuild, so a 404 right after push is normal. Poll `https://verse.namike.me/` (with a cache-busting query string) every 20 seconds, up to about 8 tries. Check the dated page once the new text appears. Report the result only after it is live, or state clearly that it is still pending.

## Page accessibility

Apply these rules to every template, CSS, or JS change. Each rule states the reason it matters.

- **Skip link first.** Make a skip link to the verse the first focusable element, so keyboard and screen-reader users bypass the header.
- **One descriptive h1.** Put the date and verse reference in the h1, so screen-reader users know what the page is.
- **Tabs use arrow keys.** Build study tabs with roving tabindex, where Left and Right move between tabs and Home and End jump to the first and last. Keep decorative numbers out of speech.
- **Dialogs trap focus.** Make the past-verses panel a dialog that keeps focus inside while open, hides the rest of the page from assistive tech, closes on Esc, and returns focus to the button that opened it.
- **No single-letter shortcuts.** Do not add them, because screen readers pass those keys to the page and can open panels by accident.
- **Visible focus.** Keep focus outlines visible on every background, including dark cards, because a faint outline is invisible to keyboard users.
- **Readable contrast.** Meet WCAG contrast for all text, including muted grey and accent colors, because low-contrast text fails for many readers.
- **Reduced motion.** Turn off animations under `prefers-reduced-motion`, because motion can cause discomfort.
- **Announce status.** Put copy, share, and empty-state messages in a live region, so they are heard without moving focus.
- **Label states clearly.** Give toggles an `aria-pressed` state and a stable label, and say when a link opens in a new tab.

## Changing shared assets

When you change JS, CSS, or other cached assets, bump the cache name in `sw.js`, for example `daily-verse-v5` to `daily-verse-v6`. Without the bump, the PWA keeps serving the old files because the service worker caches them by name. After the push, confirm that the live HTML references the new stylesheet version and that the served stylesheet contains the new rules.

## Checks before reporting

- Confirm the build passed and the automated search finds no long dashes or inflated phrases in the new entry.
- Run axe-core on the local preview and on the live site, covering each day page (newest and oldest), light and dark themes, each study tab, the expanded view, and the open past-verses dialog. Require zero violations.
- Test the keyboard path: Left, Right, Home, and End move across tabs, and focus stays in the dialog and returns on Esc.
- Preview the page locally with a static server on a free port, check the tabs and mobile layout, then stop the server and remove its log file.
- Confirm the live page shows the new text.
- Separate in the report what was verified (build, axe-core, keyboard test, local preview, live text) from what was not (real screen reader such as VoiceOver or TalkBack, real device testing, checking Bible wording against a printed Bible).

## Reporting

State the publication status and both live links. Show both translations verbatim as blockquotes with bold references, then give a concise Traditional Chinese summary. Say which reviewer suggestions were applied and which were rejected, with a short reason for each rejection.
