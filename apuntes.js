const toggle = document.querySelector("#theme-toggle");
const root = document.documentElement;
const readStored = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
const writeStored = (key, value) => { try { localStorage.setItem(key, value); } catch {} };

function paintTheme() {
  if (!toggle) return;
  const dark = root.dataset.theme === "dark";
  toggle.setAttribute("aria-pressed", String(dark));
  toggle.textContent = dark ? "Modo claro" : "Modo oscuro";
}

toggle?.addEventListener("click", () => {
  const dark = root.dataset.theme !== "dark";
  if (dark) root.dataset.theme = "dark"; else delete root.dataset.theme;
  writeStored("pau-he.theme", dark ? "dark" : "light");
  paintTheme();
});
window.addEventListener("storage", (event) => {
  if (event.key === "pau-he.theme") {
    if (event.newValue === "dark") root.dataset.theme = "dark"; else delete root.dataset.theme;
    paintTheme();
  }
});
paintTheme();

document.querySelectorAll(".print-button").forEach((button) => {
  button.addEventListener("click", () => window.print());
});

let printSolutions = [];
window.addEventListener("beforeprint", () => {
  printSolutions = [...document.querySelectorAll(".example-solution:not([open])")];
  printSolutions.forEach((solution) => { solution.open = true; });
});
window.addEventListener("afterprint", () => {
  printSolutions.forEach((solution) => { solution.open = false; });
  printSolutions = [];
});

function setupReadingPreferences() {
  const decrease = document.querySelector("#reading-size-down");
  const increase = document.querySelector("#reading-size-up");
  const output = document.querySelector("#reading-size");
  const font = document.querySelector("#reading-font");
  if (!decrease || !increase || !output || !font) return;

  const storedScale = readStored("pau-he.reading-size");
  let scale = storedScale === null ? 100 : Number(storedScale);
  if (!Number.isFinite(scale)) scale = 100;
  scale = Math.max(85, Math.min(130, Math.round(scale / 5) * 5));
  const storedFont = readStored("pau-he.reading-font");
  const fonts = ["serif", "sans", "arial", "times"];
  font.value = fonts.includes(storedFont) ? storedFont : "serif";

  const applyScale = () => {
    root.style.setProperty("--reading-scale", String(scale / 100));
    output.value = `${scale} %`;
    output.textContent = `${scale} %`;
    decrease.disabled = scale <= 85;
    increase.disabled = scale >= 130;
  };
  decrease.addEventListener("click", () => {
    scale = Math.max(85, scale - 5);
    writeStored("pau-he.reading-size", String(scale));
    applyScale();
  });
  increase.addEventListener("click", () => {
    scale = Math.min(130, scale + 5);
    writeStored("pau-he.reading-size", String(scale));
    applyScale();
  });
  font.addEventListener("change", () => {
    writeStored("pau-he.reading-font", font.value);
    root.dataset.readingFont = font.value;
  });
  root.dataset.readingFont = font.value;
  applyScale();
}

function normalizeText(text) {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
}

function setupSearch() {
  const content = document.querySelector(".reading-content");
  const form = document.querySelector("#notes-search");
  const input = document.querySelector("#reading-search");
  const results = document.querySelector("#reading-search-results");
  const status = document.querySelector("#reading-search-status");
  const clear = document.querySelector("#reading-search-clear");
  if (!content || !form || !input || !results || !status || !clear) {
    form?.setAttribute("hidden", "");
    return;
  }

  const selector = "p,h2,h3,h4,h5,li,td,th";
  let serial = 0;
  const showResults = () => {
    const term = normalizeText(input.value.trim());
    results.replaceChildren();
    if (!term) {
      status.textContent = "";
      return;
    }
    const matches = [...content.querySelectorAll(selector)].filter((element) => {
      if (element.closest(".gen-sol,.practice-status,.related-practice")) return false;
      if ([...element.querySelectorAll(selector)].length) return false;
      return normalizeText(element.textContent).includes(term);
    });
    const shown = matches.slice(0, 80);
    shown.forEach((element) => {
      if (!element.id) element.id = `reading-find-${++serial}`;
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "reading-search-result";
      button.textContent = element.textContent.trim().replace(/\s+/g, " ").slice(0, 240);
      button.addEventListener("click", () => {
        element.tabIndex = -1;
        element.focus({ preventScroll: true });
        element.scrollIntoView({ block: "start" });
        element.classList.add("search-match-focus");
        window.setTimeout(() => element.classList.remove("search-match-focus"), 1800);
      });
      item.append(button);
      results.append(item);
    });
    status.textContent = matches.length
      ? `${matches.length} coincidencia${matches.length === 1 ? "" : "s"}${matches.length > shown.length ? `; se muestran ${shown.length}` : ""}.`
      : "No se encontraron coincidencias.";
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    showResults();
  });
  input.addEventListener("input", showResults);
  clear.addEventListener("click", () => {
    input.value = "";
    results.replaceChildren();
    status.textContent = "";
    input.focus();
  });
}

function setupFootnotes() {
  const content = document.querySelector(".reading-content");
  if (!content || document.querySelector(".footnote-bubble")) return;
  const dialog = document.createElement("div");
  dialog.className = "footnote-bubble";
  dialog.id = "footnote-bubble";
  dialog.hidden = true;
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "false");
  dialog.setAttribute("aria-labelledby", "footnote-dialog-title");
  const title = document.createElement("h2");
  title.id = "footnote-dialog-title";
  const body = document.createElement("div");
  body.className = "footnote-dialog-body";
  body.id = "footnote-dialog-body";
  const more = document.createElement("button");
  more.type = "button";
  more.className = "footnote-more";
  more.textContent = "Leer completa →";
  more.setAttribute("aria-controls", body.id);
  more.setAttribute("aria-expanded", "false");
  more.hidden = true;
  const close = document.createElement("button");
  close.type = "button";
  close.className = "footnote-close";
  close.setAttribute("aria-label", "Cerrar nota");
  close.textContent = "×";
  dialog.append(title, body, more, close);
  document.body.append(dialog);
  let trigger = null;
  const updateOverflow = () => {
    const clipped = body.scrollHeight > body.clientHeight + 1;
    more.hidden = dialog.dataset.expanded === "true" || !clipped;
    dialog.classList.toggle("has-more", clipped && body.scrollTop + body.clientHeight < body.scrollHeight - 1);
  };
  const resetPreview = () => {
    delete dialog.dataset.expanded;
    more.setAttribute("aria-expanded", "false");
    more.hidden = true;
    body.scrollTop = 0;
  };
  const hide = () => {
    if (dialog.hidden) return;
    dialog.hidden = true;
    body.replaceChildren();
    trigger?.setAttribute("aria-expanded", "false");
    trigger?.focus({ preventScroll: true });
  };
  const position = () => {
    if (dialog.hidden || !trigger) return;
    const rect = trigger.getBoundingClientRect();
    const gap = 10;
    const margin = 12;
    if (dialog.dataset.expanded === "true") {
      dialog.style.width = `${Math.min(640, window.innerWidth - margin * 2)}px`;
      dialog.style.maxHeight = `${window.innerHeight - margin * 2}px`;
      dialog.style.left = `${(window.innerWidth - dialog.getBoundingClientRect().width) / 2}px`;
      dialog.style.top = `${Math.max(margin, (window.innerHeight - dialog.getBoundingClientRect().height) / 2)}px`;
      updateOverflow();
      return;
    }
    const width = Math.min(420, window.innerWidth - margin * 2);
    const left = Math.max(margin, Math.min(rect.left - 16, window.innerWidth - width - margin));
    dialog.style.width = `${width}px`;
    const below = window.innerHeight - rect.bottom - gap - margin;
    const above = rect.top - gap - margin;
    dialog.style.maxHeight = `${Math.min(360, window.innerHeight - margin * 2)}px`;
    const desiredHeight = dialog.getBoundingClientRect().height;
    dialog.dataset.side = below >= Math.min(desiredHeight, 160) || below >= above ? "below" : "above";
    const available = dialog.dataset.side === "below" ? below : above;
    dialog.style.maxHeight = `${Math.max(60, Math.min(360, available))}px`;
    dialog.style.left = `${left}px`;
    const height = dialog.getBoundingClientRect().height;
    dialog.style.top = `${Math.max(margin, dialog.dataset.side === "below" ? rect.bottom + gap : rect.top - gap - height)}px`;
    dialog.style.setProperty("--arrow-left", `${Math.max(18, Math.min(width - 18, rect.left + rect.width / 2 - left))}px`);
    updateOverflow();
  };
  more.addEventListener("click", () => {
    dialog.dataset.expanded = "true";
    more.setAttribute("aria-expanded", "true");
    more.hidden = true;
    position();
    body.tabIndex = 0;
    body.focus({ preventScroll: true });
  });
  body.addEventListener("scroll", updateOverflow, { passive: true });
  close.addEventListener("click", hide);
  content.querySelectorAll("a.footnote-ref,button[data-note-text]").forEach((link) => {
    link.setAttribute("aria-controls", dialog.id);
    link.setAttribute("aria-expanded", "false");
    link.setAttribute("aria-haspopup", "dialog");
  });
  content.addEventListener("click", (event) => {
    const link = event.target.closest("a.footnote-ref,button[data-note-text]");
    if (!link || !content.contains(link)) return;
    const target = link.matches("a") ? document.getElementById(decodeURIComponent(link.hash.slice(1))) : null;
    if (!link.dataset.noteText && (!target || !target.closest(".footnotes"))) return;
    event.preventDefault();
    if (link === trigger && !dialog.hidden) { hide(); return; }
    trigger?.setAttribute("aria-expanded", "false");
    trigger = link;
    resetPreview();
    trigger.setAttribute("aria-expanded", "true");
    if (link.dataset.noteText) {
      title.textContent = link.dataset.noteTitle;
      const definition = document.createElement("p");
      definition.textContent = link.dataset.noteText;
      const source = document.createElement("a");
      source.href = link.dataset.noteSource;
      source.textContent = link.dataset.noteSourceLabel;
      body.replaceChildren(definition, source);
      dialog.hidden = false;
      position();
      close.focus({ preventScroll: true });
      return;
    }
    title.textContent = `Nota ${target.id.replace("ftnt", "")}`;
    const paragraph = target.closest("p");
    const container = paragraph?.parentElement;
    const note = container && container.querySelectorAll(".footnote-back").length === 1
      ? container : (paragraph || target);
    const clone = note.cloneNode(true);
    clone.removeAttribute("id");
    clone.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
    clone.querySelectorAll('a[href^="#ftnt_ref"]').forEach((backlink) => {
      backlink.removeAttribute("href");
      backlink.removeAttribute("aria-label");
    });
    body.replaceChildren(clone);
    dialog.hidden = false;
    position();
    close.focus({ preventScroll: true });
  });
  document.addEventListener("click", (event) => {
    if (!dialog.hidden && !dialog.contains(event.target)
        && !event.target.closest("a.footnote-ref,button[data-note-text]")) hide();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !dialog.hidden) { event.preventDefault(); hide(); }
  });
  window.addEventListener("resize", position);
  window.addEventListener("scroll", position, { passive: true });
}

function setupReadingPosition() {
  const content = document.querySelector(".reading-content");
  const block = document.querySelector(".reading-number")?.textContent.trim();
  if (!content || !block || window.location.hash) return;
  const key = `pau-he.reading-position.v1.${block}`;
  let saved = Number(readStored(key));
  if (!Number.isFinite(saved) || saved < 100) saved = 0;

  history.scrollRestoration = "manual";
  let writeTimer = 0;
  const storePosition = () => {
    if (window.location.hash) return;
    window.clearTimeout(writeTimer);
    writeTimer = window.setTimeout(() => writeStored(key, String(Math.round(window.scrollY))), 250);
  };
  window.addEventListener("scroll", storePosition, { passive: true });
  window.addEventListener("pagehide", () => {
    window.clearTimeout(writeTimer);
    if (!window.location.hash) writeStored(key, String(Math.round(window.scrollY)));
  });
  if (!saved) return;
  if (typeof HTMLDialogElement === "undefined"
      || typeof HTMLDialogElement.prototype.showModal !== "function") return;

  const dialog = document.createElement("dialog");
  dialog.className = "resume-dialog";
  dialog.setAttribute("aria-labelledby", "resume-dialog-title");
  const heading = document.createElement("h2");
  heading.id = "resume-dialog-title";
  heading.textContent = "¿Cómo quieres continuar?";
  const message = document.createElement("p");
  message.textContent = "Hay una posición de lectura guardada en este bloque.";
  const actions = document.createElement("div");
  actions.className = "resume-actions";
  const resume = document.createElement("button");
  resume.type = "button";
  resume.textContent = "Continuar donde lo dejé";
  const restart = document.createElement("button");
  restart.type = "button";
  restart.textContent = "Empezar desde el principio";
  actions.append(resume, restart);
  dialog.append(heading, message, actions);
  document.body.append(dialog);
  resume.addEventListener("click", () => {
    dialog.close();
    window.scrollTo({ top: saved, behavior: "auto" });
  });
  restart.addEventListener("click", () => {
    writeStored(key, "0");
    dialog.close();
    window.scrollTo({ top: 0, behavior: "auto" });
  });
  dialog.showModal();
  resume.focus();
}

const PRACTICE_TAGS = {
  1: [
    { match: /edad antigua/i, tags: ["Culturas prerromanas", "Hispania antigua", "Íberos", "Romanización"] },
    { match: /inicio de la edad media/i, tags: ["Dominación musulmana", "Invasión musulmana"] },
  ],
  2: [
    { match: /hegemonía y declive/i, tags: ["al-Ándalus", "Califato de Córdoba", "Invasión musulmana"] },
    { match: /economía, política y cultura de al-ándalus/i, tags: ["Mozárabes", "Mudéjares", "Unidad religiosa"] },
    { match: /reinos cristianos, de la resistencia/i, tags: ["Núcleos de resistencia cristiana", "Repoblación", "\"Reconquista\"", "Reino nazarí de Granada"] },
    { match: /economía, política y cultura de los reinos cristianos/i, tags: ["La Mesta", "Escuela de Traductores de Toledo", "Cortes medievales"] },
  ],
  3: [
    { match: /reyes católicos/i, tags: ["Reyes Católicos", "Monarquía Hispánica", "Unión dinástica", "Expansión atlántica", "Monarquía autoritaria", "Unidad religiosa", "Reino nazarí de Granada"] },
    { match: /austrias mayores/i, tags: ["Carlos I", "Felipe II", "Casa de Austria", "Siglo XVI", "Comunidades y Germanías", "Rebelión de las Alpujarras"] },
    { match: /carlos i de españa/i, tags: ["Carlos I", "Comunidades y Germanías"] },
    { match: /felipe ii/i, tags: ["Felipe II", "Rebelión de las Alpujarras"] },
    { match: /austrias menores/i, tags: ["Validos", "Felipe IV", "Siglo XVII", "Moriscos"] },
    { match: /felipe iv/i, tags: ["Validos", "Felipe IV", "Siglo XVII"] },
  ],
  4: [
    { match: /guerra de sucesión/i, tags: ["Guerra de Sucesión", "Tratados de Utrecht y Rastadt"] },
    { match: /decretos de nueva planta/i, tags: ["Decretos de Nueva Planta"] },
    { match: /reforma de la administración/i, tags: ["Reformismo borbónico"] },
    { match: /motín de esquilache/i, tags: ["Motín de Esquilache"] },
    { match: /segunda etapa de carlos iii/i, tags: ["Reformas económicas"] },
    { match: /despotismo ilustrado/i, tags: ["Despotismo Ilustrado", "Carlos III"] },
  ],
};

function practiceStatus(parent, message, error = false) {
  const status = document.createElement("p");
  status.className = "practice-status";
  status.setAttribute("role", error ? "alert" : "status");
  status.textContent = message;
  parent.append(status);
  return status;
}

function practiceAvailable(content) {
  if (Array.isArray(window.pauPracticeBank) && window.pauPracticeBank.length
      && typeof window.pauPractice?.find === "function"
      && typeof window.pauPractice?.render === "function") return true;
  if (!content.querySelector(".practice-status[role=alert]")) {
    practiceStatus(content, "No se pudo cargar el banco de soluciones existente. Recarga la página para volver a intentarlo.", true);
  }
  return false;
}

function attachQuestionMarks(parent, question) {
  if (typeof window.pauSavedQuestions?.attach === "function") {
    window.pauSavedQuestions.attach(parent, question);
    return;
  }
  const content = document.querySelector(".reading-content");
  if (!content.querySelector(".saved-questions-error")) {
    const warning = practiceStatus(content, "No se pudieron cargar las marcas personales. Las preguntas y sus soluciones siguen disponibles. Recarga para recuperar Favoritas y Para repasar.", true);
    warning.classList.add("saved-questions-error");
  }
}

function setupExampleSolutions() {
  const content = document.querySelector(".reading-content");
  const block = Number(document.querySelector(".reading-number")?.textContent.trim());
  if (!content || !practiceAvailable(content)) return;
  const headings = [...content.querySelectorAll("h2,h3,h4,h5")].filter((heading) => !heading.closest(".np-map,.ob-chart"));
  headings.filter((heading) => /ejemplos de preguntas cortas del bloque/i.test(heading.textContent))
    .forEach((heading) => {
      if (heading.dataset.solutionsReady) return;
      const rank = Number(heading.tagName.slice(1));
      const repeatedTitle = document.querySelector(".reading-title h1")?.textContent.trim();
      const endsPractice = (node) => node.matches(".footnotes,hr")
        || (/^H[1-6]$/.test(node.tagName) && Number(node.tagName.slice(1)) <= rank
          && node !== heading && node.textContent.trim() !== repeatedTitle);
      for (let node = heading.nextElementSibling; node; node = node.nextElementSibling) {
        if (endsPractice(node)) break;
        const prompts = node.matches("p,li") ? [node] : [...node.querySelectorAll("p,li")];
        prompts.filter((prompt) => !prompt.querySelector("p,li")).forEach((prompt) => {
          const copy = prompt.cloneNode(true);
          copy.querySelectorAll(".footnote-ref").forEach((reference) => reference.remove());
          const text = copy.textContent.trim();
          if (!/^\d+\.\s/.test(text) && !prompt.matches("ol > li")) return;
          const question = text.replace(/^\d+\.\s*/, "").replace(/\s*\(PAU\s+\d{4}(?:\s*(?:y|,|-)\s*\d{4})*\)\s*$/i, "");
          let hint = prompt.nextElementSibling;
          while (hint?.matches("p") && !hint.textContent.trim()) hint = hint.nextElementSibling;
          const sourceHint = hint?.matches("p")
            && /^\(?\s*Debe incluir(?:\s*\/\s*Pistas)?\s*:/i.test(hint.textContent.trim())
            ? hint : null;
          const answer = window.pauPractice.find(question, "", block);
          const details = window.pauPractice.render(answer);
          details.classList.add("example-solution");
          details.dataset.solutionState = answer ? "mapped" : sourceHint ? "document" : "pending";
          if (sourceHint) {
            if (answer) {
              sourceHint.remove();
            } else {
              details.querySelector("p").replaceWith(sourceHint);
            }
          }
          prompt.after(details);
          const marks = document.createElement("div");
          marks.className = "practice-marks";
          details.after(marks);
          attachQuestionMarks(marks, {
            prompt: question, block, answer: answer || (sourceHint ? details.querySelector("p").textContent.replace(/^Debe incluir(?:\s*\/\s*Pistas)?\s*:\s*/i, "") : null),
            source: "Ejemplo de los apuntes",
          });
        });
      }
      heading.dataset.solutionsReady = "true";
      const section = document.createElement("section");
      section.className = "example-practice";
      section.setAttribute("aria-labelledby", heading.id);
      let start = heading.previousElementSibling;
      if (!start?.matches("p") || !/líneas cada una/i.test(start.textContent)) start = heading;
      start.before(section);
      for (let node = start; node;) {
        if (endsPractice(node)) break;
        const next = node.nextElementSibling;
        section.append(node);
        node = next;
      }
    });
}

function setupRelatedPractice() {
  const content = document.querySelector(".reading-content");
  const block = Number(document.querySelector(".reading-number")?.textContent.trim());
  const rules = PRACTICE_TAGS[block];
  if (!content || !rules || content.dataset.relatedPractice || !practiceAvailable(content)) return;
  content.dataset.relatedPractice = "loading";
  const sourceUrl = "https://docs.google.com/document/d/1tLvTDk_3AdV7w-eoBB3InnzbTVsWmPbK_VL1z8dkyOk/edit?usp=sharing";
  const headings = [...content.querySelectorAll("h2,h3,h4,h5")].filter((heading) => !heading.closest(".np-map,.ob-chart"));
  const articleTitle = headings.find((heading) => heading.tagName === "H2");

  fetch("../data/preguntas-cortas.json")
    .then((response) => {
      if (!response.ok) throw new Error("Banco de preguntas no disponible");
      return response.json();
    })
    .then((questions) => {
      headings.forEach((heading) => {
        const label = heading.textContent.trim();
        if (heading === articleTitle || !label || label === document.querySelector(".reading-title h1")?.textContent.trim()
            || /ejemplos de preguntas|notas y referencias/i.test(label)) return;
        const rule = rules.find((item) => item.match.test(label));
        const relevant = rule
          ? questions.filter((question) => question.bloque === block && question.tags.some((tag) => rule.tags.includes(tag))).slice(0, 4)
          : [];
        const panel = document.createElement("aside");
        panel.className = "related-practice";
        const headingText = document.createElement("h4");
        headingText.textContent = relevant.length ? "Preguntas cortas PAU 2017-2026" : "Más práctica";
        panel.append(headingText);
        if (!relevant.length) {
          const note = document.createElement("p");
          note.className = "related-practice-note";
          note.textContent = "No hay una coincidencia temática suficientemente precisa en el banco para esta sección.";
          panel.append(note);
        }

        if (relevant.length) {
          relevant.forEach((question) => {
            const item = document.createElement("article");
            item.className = "related-question";
            const prompt = document.createElement("p");
            prompt.className = "related-question-text";
            prompt.textContent = question.pregunta;
            item.append(prompt);
            if (question.subpregunta) {
              const sub = document.createElement("p");
              sub.className = "related-question-sub";
              sub.textContent = question.subpregunta;
              item.append(sub);
            }
            const source = document.createElement("a");
            source.href = sourceUrl;
            source.target = "_blank";
            source.rel = "noopener noreferrer";
            source.textContent = `Fuente: corpus recopilado · ${question.convocatoria}`;
            item.append(source);
            const answer = window.pauPractice.find(question.pregunta, question.subpregunta || "", block);
            const details = window.pauPractice.render(answer);
            details.dataset.solutionState = answer ? "mapped" : "pending";
            item.append(details);
            panel.append(item);
            attachQuestionMarks(item, {
              prompt: `${question.pregunta} ${question.subpregunta || ""}`.trim(),
              block, answer: answer || null, source: question.convocatoria,
            });
          });
        } else {
          const links = document.createElement("p");
          links.className = "related-practice-links";
          const questionsLink = document.createElement("a");
          questionsLink.href = "../index.html#bloques-cuestiones";
          questionsLink.textContent = "Ver el banco de preguntas";
          const generatorLink = document.createElement("a");
          generatorLink.href = "../index.html#generador";
          generatorLink.textContent = "Abrir el generador";
          links.append(questionsLink, document.createTextNode(" · "), generatorLink);
          panel.append(links);
        }
        heading.after(panel);
      });
      content.dataset.relatedPractice = "ready";
    })
    .catch((error) => {
      content.dataset.relatedPractice = "error";
      practiceStatus(content, `No se pudo cargar la práctica relacionada: ${error.message}. Recarga la página para volver a intentarlo.`, true);
    });
}

async function loadIllustration() {
  const box = document.querySelector(".reading-illustration");
  if (!box) return;
  try {
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

setupReadingPreferences();
setupSearch();
setupFootnotes();
setupReadingPosition();
setupExampleSolutions();
setupRelatedPractice();
loadIllustration();
