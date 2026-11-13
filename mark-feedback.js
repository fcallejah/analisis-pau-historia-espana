window.pauMarkFeedback = (button, flag) => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const icon = button.querySelector("svg");
  const bounds = icon.getBoundingClientRect();
  const particle = document.createElement("span");
  particle.className = `favorite-particle${flag === "review" ? " review-particle" : ""}`;
  particle.setAttribute("aria-hidden", "true");
  particle.append(icon.cloneNode(true));
  particle.style.left = `${bounds.left + bounds.width / 2}px`;
  particle.style.top = `${bounds.top + bounds.height / 2}px`;
  (button.closest("dialog[open]") || document.body).append(particle);
  particle.addEventListener("animationend", () => particle.remove(), { once: true });
  setTimeout(() => particle.remove(), 1600);
};
