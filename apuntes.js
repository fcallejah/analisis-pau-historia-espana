const toggle = document.querySelector("#theme-toggle");
const root = document.documentElement;
function paintTheme() {
  const dark = root.dataset.theme === "dark";
  toggle.setAttribute("aria-pressed", String(dark));
  toggle.textContent = dark ? "Modo claro" : "Modo oscuro";
}
toggle.addEventListener("click", () => {
  const dark = root.dataset.theme !== "dark";
  if (dark) root.dataset.theme = "dark"; else delete root.dataset.theme;
  try { localStorage.setItem("pau-he.theme", dark ? "dark" : "light"); } catch {}
  paintTheme();
});
window.addEventListener("storage", (event) => {
  if (event.key !== "pau-he.theme") return;
  if (event.newValue === "dark") root.dataset.theme = "dark"; else delete root.dataset.theme;
  paintTheme();
});
paintTheme();

document.querySelectorAll(".print-button").forEach((button) => {
  button.addEventListener("click", () => window.print());
});

async function loadIllustration() {
  const box = document.querySelector(".reading-illustration");
  if (!box) return;
  try {
    // The main cards remain the single source for images, framing and attribution.
    const response = await fetch("../index.html");
    if (!response.ok) throw new Error("Índice no disponible");
    const index = new DOMParser().parseFromString(await response.text(), "text/html");
    const source = index.querySelector(`.apunte[data-n="${box.dataset.block}"] .apunte-img`);
    if (!source) throw new Error("Fuente no disponible");
    Object.assign(box.dataset, source.dataset);
    await window.pauLoadImage(box);
  } catch {
    box.dataset.imageState = "error";
    const caption = document.createElement("figcaption");
    caption.textContent = "Imagen contextual no disponible. Consulta la imagen y su fuente en el índice de bloques.";
    box.append(caption);
  }
}
loadIllustration();
