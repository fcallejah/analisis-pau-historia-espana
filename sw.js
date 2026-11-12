const CACHE = "pau-he-v243";
const CORE = [
  "./", "./index.html", "./styles.css", "./site-header.css", "./site-header.js", "./practice.css", "./app.js", "./generador.js",
  "./site-footer.css",
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
  "./mis-preguntas.html", "./mis-preguntas.js",
  "./documentos.html", "./documentos.css", "./documentos.js", "./data/documentos.json",
  "./assets/documentos/goya-tres-de-mayo.png", "./assets/documentos/portada-constitucion-1812.png",
  "./assets/documentos/miembros-cortes-cadiz.png",
  "./assets/documentos/miembros-cortes-cadiz-oficial-2008.svg",
  "./assets/documentos/amadeo-i-ante-cadaver-prim.png",
  "./assets/documentos/grafico-desamortizaciones-siglo-xix.png",
  "./assets/documentos/grafico-desamortizaciones-siglo-xix-oficial-2008.png",
  "./assets/documentos/grafico-desamortizaciones-siglo-xix-oficial-2008.svg",
  "./assets/documentos/resultados-electorales-restauracion-1881-1898-oficial-2008.svg",
  "./assets/documentos/bajas-espanolas-en-cuba-y-filipinas-oficial-2008.svg",
  "./assets/documentos/resultados-elecciones-generales-1982-oficial-2008.svg",
  "./assets/documentos/elecciones-generales-1982-congreso-senado-vector.svg",
  "./assets/documentos/tabla-elecciones-restauracion-1881-1898.png",
  "./assets/documentos/tabla-bajas-cuba-filipinas.png",
  "./assets/documentos/tabla-resultados-elecciones-1982.png",
  "./assets/documentos/retrato-ramon-maria-narvaez.png",
  "./assets/documentos/caricatura-se-colocan-reyes-1869.png",
  "./assets/documentos/resultados-electorales-restauracion-1881-1898.png",
  "./assets/documentos/entrada-alfonso-xii-madrid-1875.png",
  "./assets/documentos/acorazado-maine-1898.png",
  "./assets/documentos/huelga-general-1917-fotografia.png",
  "./assets/documentos/primo-rivera-visita-tropas-marruecos.png",
  "./assets/documentos/detenidos-revolucion-asturias-1934.png",
  "./assets/documentos/casas-viejas-detenciones-1933.png",
  "./assets/documentos/casas-viejas-detenciones-1933-eldebate.png",
  "./assets/documentos/reparto-armas-madrid-1936.png",
  "./assets/documentos/franco-mola-cavalcanti-burgos.png",
  "./assets/documentos/cartel-ejercito-popular-republica.png",
  "./assets/documentos/militantes-pce-acto-multitudinario.png",
  "./assets/documentos/cartel-falange.png",
  "./assets/documentos/franco-hitler-hendaya-1940.png",
  "./assets/documentos/exaltacion-franco.png",
  "./assets/documentos/elecciones-generales-1982-congreso-senado.png",
  "./assets/documentos/elecciones-generales-1982-congreso-senado-oficial-2026.png",
  "./assets/documentos/reunion-expresidentes-gobierno.png",
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
