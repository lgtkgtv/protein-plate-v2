/* ProteinPlate service worker.
 *
 * Lives at the site root (docs/sw.js -> /<repo>/sw.js) so its scope covers the
 * whole site. All cached URLs are relative to this file, so the same worker
 * works whether the site is served at "/" or under a project subpath.
 *
 * Strategy:
 *   - install: precache the app shell (core navigations + icons + manifest)
 *   - navigations: network-first (fresh when online) -> cache -> home fallback
 *   - other GETs (CSS/JS/images): cache-first, fill the cache on miss
 * Bump VERSION to roll the cache when the app shell changes.
 */
const VERSION = "v3";
const CACHE = "proteinplate-" + VERSION;

const CORE = [
  "./",
  "./the-plate/",
  "./recipes/",
  "./ingredients/",
  "./meal-plan/",
  "./grocery-list/",
  "./keto/",
  "./about/",
  "./manifest.json",
  "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting())
      .catch(() => {})   // never let a missing URL block install entirely
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function putInCache(request, response) {
  if (response && response.ok && response.type === "basic") {
    const copy = response.clone();
    caches.open(CACHE).then((cache) => cache.put(request, copy));
  }
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => { putInCache(request, response); return response; })
        .catch(() => caches.match(request).then((hit) => hit || caches.match("./")))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((hit) =>
      hit || fetch(request).then((response) => {
        putInCache(request, response);
        return response;
      }).catch(() => hit))
  );
});
