/* Read Chinese Daily — offline cache.
 * 页面导航: 网络优先(避免 Cloudflare 的 .html→无后缀 308 重定向响应
 *          被缓存后导致导航失败),离线时回退缓存。
 * 静态资源: 缓存优先 + 后台刷新。永不缓存 redirected 响应。 */
const V = "rcd-v19";
const PRECACHE = ["./", "./assets/style.css", "./assets/reader.js"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== V).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || !req.url.startsWith(self.location.origin)) return;
  // 音频体积大(几十MB),不进 SW 缓存,交给浏览器 HTTP 缓存
  if (req.url.includes("/audio/")) return;

  if (req.mode === "navigate") {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res.ok && !res.redirected) {
          const c = await caches.open(V);
          c.put(req, res.clone());
        }
        return res;
      } catch (err) {
        const hit = await caches.match(req);
        if (hit && !hit.redirected) return hit;
        const home = await caches.match("./");
        return home || Response.error();
      }
    })());
    return;
  }

  e.respondWith(
    caches.match(req).then((hit) => {
      const net = fetch(req).then((res) => {
        if (res && res.ok && !res.redirected) {
          const copy = res.clone();
          caches.open(V).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
