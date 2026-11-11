(() => {
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
