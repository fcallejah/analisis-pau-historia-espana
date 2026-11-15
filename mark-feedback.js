window.pauMarkFeedback = (button, flag) => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const icon = button.querySelector("svg");
  const bounds = icon.getBoundingClientRect();
  const buttonBounds = button.getBoundingClientRect();
  const particle = document.createElement("span");
  particle.className = `favorite-particle${flag === "review" ? " review-particle" : ""}`;
  particle.setAttribute("aria-hidden", "true");
  particle.append(icon.cloneNode(true));
  button.append(particle);
  particle.style.left = `${bounds.left - buttonBounds.left - button.clientLeft}px`;
  particle.style.top = `${bounds.top - buttonBounds.top - button.clientTop}px`;
  particle.style.width = `${bounds.width}px`;
  particle.style.height = `${bounds.height}px`;
  particle.addEventListener("animationend", () => particle.remove(), { once: true });
  setTimeout(() => particle.remove(), 1600);
};
