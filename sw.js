/* Read Chinese Daily — offline cache (stale-while-revalidate). */
const V = "rcd-v1";

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) =>
    c.addAll(["./index.html", "./about.html", "./words.html", "./wordbook.html",
              "./assets/style.css", "./assets/reader.js"])));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== V).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || !e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const net = fetch(e.request).then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(V).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
