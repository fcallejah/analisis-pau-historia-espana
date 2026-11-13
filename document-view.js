(() => {
  const root = document.documentElement;
  const key = location.pathname.endsWith("/mis-documentos.html")
    ? "pau-he.documents.saved-view.v1" : "pau-he.documents.view.v1";
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  try {
    const saved = JSON.parse(sessionStorage.getItem(key));
    if (saved?.version === 1 && saved.url === location.href) {
      root.setAttribute("data-document-restoring", "");
    }
  } catch (error) {
    console.warn("No se pudo preparar la recuperación de la lectura:", error);
  }
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) root.removeAttribute("data-document-restoring");
  });
  window.addEventListener("error", (event) => {
    if (event.target === window || (event.target instanceof HTMLScriptElement
      && event.target.src.includes("/documentos.js"))) {
      root.removeAttribute("data-document-restoring");
    }
  }, true);
})();
