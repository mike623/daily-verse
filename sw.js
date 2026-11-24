const CACHE_NAME = 'daily-verse-v1';
const CORE_ASSETS = [
  './',
  './manifest.webmanifest',
  './assets/styles.css',
  './assets/app.js',
  './data/index.json',
  './assets/icons/favicon.svg',
  './assets/icons/icon-192.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const isNetworkFirst =
    request.mode === 'navigate' ||
    url.pathname.endsWith('/') ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('/data/index.json');

  if (isNetworkFirst) {
    event.respondWith(
      fetch(request)
        .then((res) => {
          if (res && res.ok && res.type === 'basic') {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return res;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          if (request.mode === 'navigate') {
            const fallback = await caches.match('./');
            if (fallback) return fallback;
          }
          return Response.error();
        })
    );
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);
      const networkPromise = fetch(request)
        .then((res) => {
          if (res && res.ok && res.type === 'basic') {
            cache.put(request, res.clone());
          }
          return res;
        })
        .catch(() => null);
      return cached || (await networkPromise) || Response.error();
    })
  );
});
