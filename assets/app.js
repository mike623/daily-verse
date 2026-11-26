(function () {
  const rootEl = document.documentElement;
  const base = rootEl.dataset.base || './';
  const currentDate = rootEl.dataset.date || '';
  const entryPath = rootEl.dataset.entryPath || '';

  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIconSun = document.getElementById('themeIconSun');
  const themeIconMoon = document.getElementById('themeIconMoon');
  const themeColorMeta = document.getElementById('themeColorMeta');
  const installPwaBtn = document.getElementById('installPwaBtn');
  const toastEl = document.getElementById('toastEl');

  const studySanctuary = document.getElementById('studySanctuary');
  const tabButtons = Array.from(document.querySelectorAll('.study-tab'));
  const tabPanels = {
    context: document.getElementById('panel-context'),
    practice: document.getElementById('panel-practice'),
    workplace: document.getElementById('panel-workplace')
  };
  const expandAllBtn = document.getElementById('expandAllBtn');

  const archiveDrawer = document.getElementById('archiveDrawer');
  const drawerBackdrop = document.getElementById('drawerBackdrop');
  const openArchiveBtn = document.getElementById('openArchiveBtn');
  const footerArchiveBtn = document.getElementById('footerArchiveBtn');
  const closeArchiveBtn = document.getElementById('closeArchiveBtn');
  const archiveSearchInput = document.getElementById('archiveSearchInput');
  const archiveGroups = document.getElementById('archiveGroups');
  const archiveEmpty = document.getElementById('archiveEmpty');

  let activeTab = 'context';
  let isExpanded = false;
  let toastTimer = null;
  let archiveEntries = [];

  function showToast(msg) {
    if (!toastEl) return;
    toastEl.textContent = '';
    toastEl.classList.add('visible');
    setTimeout(() => {
      toastEl.textContent = msg;
    }, 50);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove('visible');
    }, 2200);
  }

  function applyTheme(theme) {
    rootEl.setAttribute('data-theme', theme);
    const isDark = theme === 'dark';
    if (themeIconSun) themeIconSun.style.display = isDark ? 'block' : 'none';
    if (themeIconMoon) themeIconMoon.style.display = isDark ? 'none' : 'block';
    if (themeColorMeta) themeColorMeta.setAttribute('content', isDark ? '#12110F' : '#F8F4EC');
    if (themeToggleBtn) {
      themeToggleBtn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      themeToggleBtn.setAttribute('aria-label', '深色模式');
    }
    try {
      localStorage.setItem('daily-verse-theme', theme);
    } catch (_) {}
  }

  (function initTheme() {
    const params = new URLSearchParams(window.location.search);
    const qTheme = params.get('theme');
    if (qTheme === 'dark' || qTheme === 'light') {
      applyTheme(qTheme);
      return;
    }
    let saved = null;
    try {
      saved = localStorage.getItem('daily-verse-theme');
    } catch (_) {}
    if (saved === 'dark' || saved === 'light') {
      applyTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
    } else {
      applyTheme('light');
    }
  })();

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const next = rootEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  }

  function syncStudyView() {
    if (!studySanctuary || !expandAllBtn) return;
    studySanctuary.setAttribute('data-expanded', isExpanded ? 'true' : 'false');
    expandAllBtn.textContent = isExpanded ? '分頁閱讀' : '展開全文';

    tabButtons.forEach((btn) => {
      const isCurrent = btn.getAttribute('data-tab') === activeTab;
      btn.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      btn.setAttribute('tabindex', isCurrent ? '0' : '-1');
    });

    Object.keys(tabPanels).forEach((key) => {
      const panel = tabPanels[key];
      if (panel) {
        panel.hidden = isExpanded ? false : key !== activeTab;
      }
    });
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      activeTab = btn.getAttribute('data-tab') || 'context';
      if (isExpanded) {
        isExpanded = false;
      }
      syncStudyView();
    });
  });

  const tabOrder = ['context', 'practice', 'workplace'];
  tabButtons.forEach((btn) => {
    btn.addEventListener('keydown', (ev) => {
      const idx = tabOrder.indexOf(btn.getAttribute('data-tab'));
      let nextIdx = null;
      if (ev.key === 'ArrowRight') nextIdx = (idx + 1) % tabOrder.length;
      else if (ev.key === 'ArrowLeft') nextIdx = (idx - 1 + tabOrder.length) % tabOrder.length;
      else if (ev.key === 'Home') nextIdx = 0;
      else if (ev.key === 'End') nextIdx = tabOrder.length - 1;
      if (nextIdx === null) return;
      ev.preventDefault();
      ev.stopPropagation();
      activeTab = tabOrder[nextIdx];
      isExpanded = false;
      syncStudyView();
      const target = tabButtons.find((b) => b.getAttribute('data-tab') === activeTab);
      if (target) target.focus();
    });
  });

  if (expandAllBtn) {
    expandAllBtn.addEventListener('click', () => {
      isExpanded = !isExpanded;
      syncStudyView();
    });
  }

  function formatMonthLabel(dateStr) {
    const parts = (dateStr || '').split('-');
    if (parts.length >= 2) {
      return `${parts[0]} 年 ${parts[1]} 月`;
    }
    return '過往經文';
  }

  function renderArchiveList(query) {
    if (!archiveGroups || !archiveEmpty) return;
    const q = (query || '').trim().toLowerCase();
    const filtered = archiveEntries.filter((item) => {
      if (!q) return true;
      return (
        (item.date || '').toLowerCase().includes(q) ||
        (item.refZh || '').toLowerCase().includes(q) ||
        (item.refEn || '').toLowerCase().includes(q) ||
        (item.snippet || '').toLowerCase().includes(q)
      );
    });

    archiveGroups.innerHTML = '';
    archiveEmpty.hidden = filtered.length > 0;
    const statusEl = document.getElementById('archiveStatus');
    if (statusEl && q) {
      statusEl.textContent = filtered.length ? `找到 ${filtered.length} 篇` : '找不到符合的日期或經文';
    } else if (statusEl) {
      statusEl.textContent = '';
    }
    if (filtered.length === 0) return;

    const groups = new Map();
    filtered.forEach((item) => {
      const monthKey = formatMonthLabel(item.date);
      if (!groups.has(monthKey)) {
        groups.set(monthKey, []);
      }
      groups.get(monthKey).push(item);
    });

    groups.forEach((items, monthLabel) => {
      const groupEl = document.createElement('section');
      groupEl.className = 'archive-group';

      const heading = document.createElement('h3');
      heading.className = 'archive-month';
      heading.textContent = monthLabel;
      groupEl.appendChild(heading);

      const ul = document.createElement('ul');
      ul.className = 'archive-list';

      items.forEach((item) => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.className = 'archive-entry-btn' + (item.date === currentDate ? ' is-active' : '');
        link.href = `${base}${item.path}`;
        if (item.date === currentDate) {
          link.setAttribute('aria-current', 'page');
        }

        const dateSpan = document.createElement('span');
        dateSpan.className = 'archive-date tabular';
        dateSpan.textContent = item.date;

        const refSpan = document.createElement('span');
        refSpan.className = 'archive-ref';
        refSpan.textContent = `${item.refZh} · ${item.refEn}`;

        const snippetSpan = document.createElement('span');
        snippetSpan.className = 'archive-snippet';
        snippetSpan.textContent = item.snippet;

        link.appendChild(dateSpan);
        link.appendChild(refSpan);
        link.appendChild(snippetSpan);
        li.appendChild(link);
        ul.appendChild(li);
      });

      groupEl.appendChild(ul);
      archiveGroups.appendChild(groupEl);
    });
  }

  function loadFallbackArchive() {
    const el = document.getElementById('archiveFallback');
    if (!el) return [];
    try {
      const parsed = JSON.parse(el.textContent || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  async function loadArchive() {
    archiveEntries = loadFallbackArchive();
    renderArchiveList(archiveSearchInput ? archiveSearchInput.value : '');
    if (window.location.protocol === 'file:') {
      return;
    }
    try {
      const res = await fetch(`${base}data/index.json`);
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data)) {
        archiveEntries = data;
        renderArchiveList(archiveSearchInput ? archiveSearchInput.value : '');
      }
    } catch (_) {}
  }

  const backgroundEls = Array.from(document.querySelectorAll('.skip-link, .site-header, main, .site-footer'));
  let drawerOpener = null;

  function setBackgroundInert(on) {
    backgroundEls.forEach((el) => {
      if (on) {
        el.setAttribute('inert', '');
        el.setAttribute('aria-hidden', 'true');
      } else {
        el.removeAttribute('inert');
        el.removeAttribute('aria-hidden');
      }
    });
  }

  function openDrawer() {
    if (!archiveDrawer || !drawerBackdrop) return;
    drawerOpener = document.activeElement;
    setBackgroundInert(true);
    archiveDrawer.hidden = false;
    drawerBackdrop.hidden = false;
    requestAnimationFrame(() => {
      archiveDrawer.classList.add('open');
      drawerBackdrop.classList.add('open');
      if (archiveSearchInput) archiveSearchInput.focus();
    });
  }

  function closeDrawer() {
    if (!archiveDrawer || !drawerBackdrop) return;
    archiveDrawer.classList.remove('open');
    drawerBackdrop.classList.remove('open');
    setBackgroundInert(false);
    const opener = drawerOpener && document.contains(drawerOpener) ? drawerOpener : openArchiveBtn;
    if (opener && typeof opener.focus === 'function') opener.focus();
    drawerOpener = null;
    setTimeout(() => {
      if (!archiveDrawer.classList.contains('open')) {
        archiveDrawer.hidden = true;
        drawerBackdrop.hidden = true;
      }
    }, 220);
  }

  async function copyText(text, label) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        showToast(label);
        return;
      }
    } catch (_) {}

    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast(label);
    } catch (_) {
      showToast('無法自動複製，請手動選取文字');
    } finally {
      document.body.removeChild(ta);
    }
  }

  function getCanonicalUrl() {
    if (!entryPath) {
      return window.location.href.split('#')[0];
    }
    try {
      return new URL(`${base}${entryPath}`, window.location.href).href;
    } catch (_) {
      return window.location.href.split('#')[0];
    }
  }

  const copyVerseBtn = document.getElementById('copyVerseBtn');
  if (copyVerseBtn) {
    copyVerseBtn.addEventListener('click', () => {
      const quoteZh = (document.getElementById('heroQuoteZh') || {}).textContent || '';
      const quoteEn = (document.getElementById('heroQuoteEn') || {}).textContent || '';
      const refZh = rootEl.dataset.refZh || '';
      const verZh = rootEl.dataset.verZh || '';
      const refEn = rootEl.dataset.refEn || '';
      const verEn = rootEl.dataset.verEn || '';
      const shareUrl = getCanonicalUrl();
      const payload = `${quoteZh}\n— ${refZh} (${verZh})\n\n${quoteEn}\n— ${refEn} (${verEn})\n\n${shareUrl}`;
      copyText(payload, '已複製中英經文與來源');
    });
  }

  const copyLinkBtn = document.getElementById('copyLinkBtn');
  if (copyLinkBtn) {
    copyLinkBtn.addEventListener('click', async () => {
      const shareUrl = getCanonicalUrl();
      const shareData = {
        title: document.title,
        url: shareUrl
      };
      if (
        typeof navigator.share === 'function' &&
        (!navigator.canShare || navigator.canShare(shareData))
      ) {
        try {
          await navigator.share(shareData);
          return;
        } catch (err) {
          if (err && err.name === 'AbortError') return;
        }
      }
      copyText(shareUrl, currentDate ? `已複製 ${currentDate} 的連結` : '已複製連結');
    });
  }

  if (openArchiveBtn) openArchiveBtn.addEventListener('click', openDrawer);
  if (footerArchiveBtn) footerArchiveBtn.addEventListener('click', openDrawer);
  if (closeArchiveBtn) closeArchiveBtn.addEventListener('click', closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);

  if (archiveSearchInput) {
    archiveSearchInput.addEventListener('input', (ev) => {
      renderArchiveList(ev.target.value);
    });
  }

  document.addEventListener('keydown', (ev) => {
    const drawerOpen = archiveDrawer && archiveDrawer.classList.contains('open');
    if (ev.key === 'Escape' && drawerOpen) {
      closeDrawer();
      return;
    }
    if (ev.key === 'Tab' && drawerOpen) {
      const focusables = Array.from(
        archiveDrawer.querySelectorAll('button, a[href], input, [tabindex]:not([tabindex="-1"])')
      ).filter((el) => !el.hidden && el.offsetParent !== null);
      if (focusables.length) {
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (ev.shiftKey && document.activeElement === first) {
          ev.preventDefault();
          last.focus();
        } else if (!ev.shiftKey && document.activeElement === last) {
          ev.preventDefault();
          first.focus();
        }
      }
      return;
    }
    // Arrow keys switch days only when nothing interactive has focus, so they never
    // fight screen-reader or form navigation. No single-letter shortcuts (WCAG 2.1.4).
    if (drawerOpen || ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    const activeEl = document.activeElement;
    if (activeEl && activeEl !== document.body && activeEl.id !== 'top') return;

    if (ev.key === 'ArrowLeft') {
      const prevEl = document.getElementById('prevDayBtn');
      if (prevEl && prevEl.tagName === 'A' && prevEl.getAttribute('href')) {
        window.location.href = prevEl.href;
      }
    } else if (ev.key === 'ArrowRight') {
      const nextEl = document.getElementById('nextDayBtn');
      if (nextEl && nextEl.tagName === 'A' && nextEl.getAttribute('href')) {
        window.location.href = nextEl.href;
      }
    }
  });

  const initParams = new URLSearchParams(window.location.search);
  const qTab = initParams.get('tab');
  if (qTab && tabPanels[qTab]) {
    activeTab = qTab;
  } else if (qTab === 'all') {
    isExpanded = true;
  }

  syncStudyView();
  loadArchive();

  let deferredInstallPrompt = null;
  const isStandalone =
    (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
    window.navigator.standalone === true;

  window.addEventListener('beforeinstallprompt', (ev) => {
    ev.preventDefault();
    deferredInstallPrompt = ev;
    if (installPwaBtn && !isStandalone) {
      installPwaBtn.hidden = false;
    }
  });

  if (installPwaBtn) {
    installPwaBtn.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      try {
        await deferredInstallPrompt.userChoice;
      } catch (_) {}
      deferredInstallPrompt = null;
      installPwaBtn.hidden = true;
    });
  }

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    if (installPwaBtn) installPwaBtn.hidden = true;
    showToast('已安裝「晨光」App');
  });

  if (
    'serviceWorker' in navigator &&
    (window.location.protocol === 'https:' || window.location.hostname === 'localhost')
  ) {
    window.addEventListener('load', () => {
      const swUrl = new URL(`${base}sw.js`, window.location.href).href;
      const swScope = new URL(base, window.location.href).pathname;
      navigator.serviceWorker.register(swUrl, { scope: swScope, updateViaCache: 'none' }).catch(() => {});
    });
  }
})();
