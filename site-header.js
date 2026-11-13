(() => {
  const questionsLink = document.querySelector(".header-tools .saved-nav");
  if (questionsLink && !questionsLink.closest(".saved-nav-stack")) {
    const stack = document.createElement("div");
    stack.className = "saved-nav-stack";
    questionsLink.before(stack);
    stack.append(questionsLink);
    const documentsLink = document.createElement("a");
    documentsLink.href = new URL("mis-documentos.html", questionsLink.href).href;
    documentsLink.className = "saved-nav";
    documentsLink.textContent = "Mis documentos";
    if (new URL(documentsLink.href).pathname === location.pathname) {
      documentsLink.setAttribute("aria-current", "page");
    }
    stack.append(documentsLink);
    stack.closest("nav").setAttribute("aria-label", "Listas personales, diccionario y RAE");
  }
  const toggle = document.querySelector("#theme-toggle");
  if (!toggle) return;
  const root = document.documentElement;
  const paintTheme = () => {
    const dark = root.dataset.theme === "dark";
    toggle.setAttribute("aria-pressed", String(dark));
    toggle.setAttribute("aria-label", dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    toggle.title = dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
  };
  const setTheme = (dark) => {
    if (dark) root.dataset.theme = "dark";
    else delete root.dataset.theme;
    paintTheme();
  };
  toggle.addEventListener("click", () => {
    const dark = root.dataset.theme !== "dark";
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const zoomed = window.visualViewport && window.visualViewport.scale > 1;
    if (document.startViewTransition && !calm && !zoomed) {
      document.startViewTransition(() => setTheme(dark));
    } else setTheme(dark);
    try { localStorage.setItem("pau-he.theme", dark ? "dark" : "light"); } catch {}
  });
  window.addEventListener("storage", (event) => {
    if (event.key === "pau-he.theme") setTheme(event.newValue === "dark");
  });
  paintTheme();
})();
