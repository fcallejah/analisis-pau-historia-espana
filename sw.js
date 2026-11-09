const CACHE = "pau-he-v168";
const CORE = [
  "./", "./index.html", "./styles.css", "./practice.css", "./app.js", "./generador.js",
  "./manifest.json", "./data/preguntas-cortas.json", "./assets/icon.svg",
  "./assets/icon-192.png", "./assets/icon-512.png", "./assets/apple-touch-icon.png",
  "./assets/favicon-32.png",
  "./assets/social-preview.png",
  "./assets/dle-logo.jpg",
  "./assets/apuntes/bloque-02-alhambra.jpg",
  "./assets/apuntes/bloque-06-amadeo-i.jpg",
  "./assets/apuntes/bloque-10-republica.jpg",
  "./apuntes.css", "./apuntes.js", "./imagenes-apuntes.js",
  "./anotaciones.js", "./videos-apuntes.js",
  "./nueva-planta.css", "./nueva-planta.js", "./assets/apuntes/nueva-planta.svg",
  "./organizacion-borbonica.css", "./organizacion-borbonica.js",
  ...Array.from({ length: 12 }, (_, i) => `./apuntes/bloque-${i + 1}.html`),
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
