const CACHE = "pau-he-v38";
const CORE = [
  "./", "./index.html", "./styles.css", "./app.js", "./generador.js",
  "./manifest.json", "./data/preguntas-cortas.json", "./assets/icon.svg",
  "./assets/icon-192.png", "./assets/icon-512.png", "./assets/apple-touch-icon.png",
  "./assets/favicon-32.png",
  "./assets/social-preview.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CORE)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((key) => key.startsWith("pau-he-") && key !== CACHE).map((key) => caches.delete(key)),
  )).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin
      || !url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  event.respondWith((async () => {
    try {
      const response = await fetch(event.request);
      if (response.ok) {
        const cache = await caches.open(CACHE);
        await cache.put(event.request, response.clone());
      }
      return response;
    } catch (error) {
      const cached = await caches.match(event.request, { ignoreSearch: true });
      if (cached) return cached;
      if (event.request.mode === "navigate") return caches.match("./index.html");
      throw error;
    }
  })());
});
