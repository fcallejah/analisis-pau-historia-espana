(() => {
  const key = "pau-he.questions.v1";
  const normalize = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es").replace(/[^\p{L}\p{N}]+/gu, "");
  const identity = (question) => `${question.block}:${normalize(question.prompt)}`;
  let saved = {};
  let available = true;
  const status = document.createElement("p");
  status.className = "saved-status";
  status.setAttribute("role", "status");
  document.body.append(status);
  let noticeTimer;
  function report(text, error = false) {
    clearTimeout(noticeTimer);
    status.setAttribute("role", error ? "alert" : "status");
    status.textContent = text;
    if (!error) noticeTimer = setTimeout(() => { status.textContent = ""; }, 8000);
  }
  function read() {
    const raw = localStorage.getItem(key);
    if (!raw) return {};
    const value = JSON.parse(raw);
    if (!value || Array.isArray(value) || typeof value !== "object"
        || !Object.entries(value).every(([id, item]) => item
          && typeof item.prompt === "string" && Number.isInteger(item.block)
          && item.block >= 1 && item.block <= 4 && id === identity(item)
          && typeof item.favorite === "boolean" && typeof item.review === "boolean"
          && (item.answer === null || typeof item.answer === "string")
          && typeof item.source === "string")) {
      throw new Error("Formato de preguntas guardadas no válido");
    }
    return value;
  }
  try {
    saved = read();
    if (document.querySelector("#saved-questions") && localStorage.getItem("pau-he.theme") === "dark") {
      document.documentElement.dataset.theme = "dark";
    }
  } catch (error) {
    available = false;
    report(`No se pudieron leer tus preguntas: ${error.message}. No se sobrescribirán los datos.`, true);
  }
  const star = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9Z"/></svg>';
  const cap = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="m2 8 10-5 10 5-10 5Z M5 10v6q7 5 14 0v-6 M22 8v8"/><path d="M10 15a2 2 0 0 1 4 0c0 1-2 1-2 2 M12 19h.01"/></svg>';
  const controls = new Set();
  function celebrate(button, flag) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const icon = button.querySelector("svg");
    const bounds = icon.getBoundingClientRect();
    const particle = document.createElement("span");
    particle.className = `favorite-particle${flag === "review" ? " review-particle" : ""}`;
    particle.setAttribute("aria-hidden", "true");
    particle.append(icon.cloneNode(true));
    particle.style.left = `${bounds.left + bounds.width / 2}px`;
    particle.style.top = `${bounds.top + bounds.height / 2}px`;
    document.body.append(particle);
    particle.addEventListener("animationend", () => particle.remove(), { once: true });
    setTimeout(() => particle.remove(), 1600);
  }
  function refresh() {
    for (const entry of controls) {
      if (!entry.node.isConnected && entry.connected) { controls.delete(entry); continue; }
      entry.connected ||= entry.node.isConnected;
      const state = saved[entry.id];
      entry.favorite.setAttribute("aria-pressed", String(!!state?.favorite));
      entry.review.setAttribute("aria-pressed", String(!!state?.review));
      entry.favorite.title = state?.favorite ? "Quitar de favoritas" : "Añadir a favoritas";
      entry.review.title = state?.review ? "Ya repasada: quitar de repaso" : "Necesito repasar";
    }
  }
  function attach(parent, question) {
    const id = identity(question);
    const node = document.createElement("div");
    node.className = "question-marks";
    const favorite = document.createElement("button");
    const review = document.createElement("button");
    for (const [button, flag, icon, label] of [
      [favorite, "favorite", star, "Favorita"],
      [review, "review", cap, "Necesito repasar"],
    ]) {
      button.type = "button";
      button.className = `question-mark-${flag}`;
      button.innerHTML = icon;
      if (flag === "favorite") {
        button.setAttribute("aria-label", label);
      } else {
        const text = document.createElement("span");
        text.textContent = label;
        button.append(text);
      }
      button.addEventListener("click", () => {
        if (!available) { report("No se puede guardar: revisa el aviso de almacenamiento.", true); return; }
        try {
          // Read immediately before writing to preserve changes from other tabs.
          const next = read();
          const old = next[id];
          next[id] = { ...question, answer: question.answer || old?.answer || null,
            source: /20\d{2}/.test(question.source) ? question.source : (old?.source || question.source || ""),
            favorite: old?.favorite || false, review: old?.review || false };
          next[id][flag] = !next[id][flag];
          if (!next[id].favorite && !next[id].review) delete next[id];
          localStorage.setItem(key, JSON.stringify(next));
          saved = next;
          if (next[id]?.[flag]) celebrate(button, flag);
          refresh();
          renderList();
          report("Preguntas actualizadas. Se guardan solo en este navegador.");
        } catch (error) {
          report(`No se pudieron guardar tus preguntas: ${error.message}.`, true);
        }
      });
      node.append(button);
    }
    parent.append(node);
    controls.add({ node, id, favorite, review });
    refresh();
  }
  window.pauSavedQuestions = { attach };
  const host = document.querySelector("#saved-questions");
  let active = "all";
  const filter = document.querySelector("#saved-block");
  function renderList() {
    if (!host) return;
    const focused = document.activeElement;
    const oldIndex = [...host.querySelectorAll("button")].indexOf(focused);
    host.replaceChildren();
    const items = Object.values(saved).filter((item) => (active === "all" || item[active])
      && (!filter.value || item.block === Number(filter.value)));
    document.querySelectorAll("[data-saved-list]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.savedList === active));
      button.querySelector("span:not(.saved-tab-icon)").textContent = Object.values(saved).filter((item) => button.dataset.savedList === "all" || item[button.dataset.savedList]).length;
    });
    if (!items.length) {
      const empty = document.createElement("p");
      empty.textContent = active === "all"
        ? "No tienes preguntas guardadas con este filtro. Márcalas con la estrella o el birrete."
        : active === "favorite"
        ? "No tienes preguntas favoritas con este filtro. Márcalas con la estrella."
        : "No tienes preguntas pendientes con este filtro. Márcalas con el birrete.";
      host.append(empty);
    }
    for (const item of items) {
      const article = document.createElement("article");
      article.className = "saved-question";
      const meta = document.createElement("small");
      meta.textContent = `Bloque ${item.block}${item.source ? ` · ${item.source}` : ""}`;
      const prompt = document.createElement("p");
      prompt.textContent = item.prompt;
      const answer = window.pauPractice.find(item.prompt, "", item.block) || item.answer;
      article.append(meta, prompt, window.pauPractice.render(answer));
      host.append(article);
      attach(article, item);
    }
    refresh();
    if (oldIndex >= 0) {
      const buttons = host.querySelectorAll("button");
      (buttons[Math.min(oldIndex, buttons.length - 1)] || document.querySelector(`[data-saved-list="${active}"]`)).focus();
    }
  }
  if (host) {
    document.querySelectorAll("[data-saved-list]").forEach((button) => {
      if (button.dataset.savedList !== "all") {
        const icon = document.createElement("span");
        icon.className = "saved-tab-icon";
        icon.innerHTML = button.dataset.savedList === "favorite" ? star : cap;
        button.prepend(icon);
      }
      button.addEventListener("click", () => { active = button.dataset.savedList; renderList(); });
    });
    filter.addEventListener("change", renderList);
    window.addEventListener("DOMContentLoaded", renderList);
  }
  window.addEventListener("storage", (event) => {
    if (event.key !== key && event.key !== null) return;
    try { saved = read(); available = true; refresh(); renderList(); }
    catch (error) { available = false; report(`No se pudieron actualizar tus preguntas: ${error.message}.`, true); }
  });
})();
