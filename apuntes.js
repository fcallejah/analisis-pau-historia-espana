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
