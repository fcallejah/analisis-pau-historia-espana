(() => {
  const content = document.querySelector(".reading-content");
  const tools = document.querySelector(".reading-tools");
  if (!content || !tools) return;
  const block = document.querySelector(".reading-number").textContent.trim();
  const key = `pau-he.annotations.v1.${block}`;
  const colors = ["amarillo", "verde", "azul", "rosa", "violeta"];
  const excluded = ".np-map,.ob-chart,.gen-sol,.practice-status,.related-practice,.footnotes,.heading-alias,.reading-video";
  const bar = document.createElement("div");
  bar.className = "annotation-toolbar";
  bar.setAttribute("role", "group");
  bar.setAttribute("aria-label", "Subrayar y añadir notas al texto seleccionado");
  const label = document.createElement("strong");
  label.textContent = "Subrayar";
  bar.append(label);
  const status = document.createElement("p");
  status.className = "annotation-status";
  status.setAttribute("role", "status");
  status.textContent = "Selecciona texto de los apuntes y elige un color o añade una nota. Se guarda solo en este navegador.";
  const manager = document.createElement("details");
  manager.className = "annotation-manager";
  const summary = document.createElement("summary");
  summary.textContent = "Mis subrayados y notas";
  const list = document.createElement("ul");
  manager.append(summary, list);
  tools.append(bar, status, manager);
  const dialog = document.createElement("dialog");
  dialog.className = "annotation-dialog";
  dialog.setAttribute("aria-labelledby", "annotation-title");
  const title = document.createElement("h2");
  title.id = "annotation-title";
  title.textContent = "Nota personal";
  const close = document.createElement("button");
  close.type = "button";
  close.className = "annotation-close";
  close.textContent = "×";
  close.setAttribute("aria-label", "Cerrar nota personal");
  const quote = document.createElement("blockquote");
  const noteLabel = document.createElement("label");
  noteLabel.htmlFor = "annotation-note";
  noteLabel.textContent = "Tu nota";
  const textarea = document.createElement("textarea");
  textarea.id = "annotation-note";
  textarea.rows = 5;
  textarea.maxLength = 4000;
  const save = document.createElement("button");
  save.type = "button";
  save.textContent = "Guardar nota";
  const removeAnnotation = document.createElement("button");
  removeAnnotation.type = "button";
  removeAnnotation.className = "annotation-erase";
  removeAnnotation.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path class="gen-reset-line" stroke-width="1.8" d="M4 20h16"/><g transform="rotate(-42 12 10)"><rect x="8" y="3" width="8" height="14" rx="1.5" stroke-width="1.8"/><path stroke-width="1.5" d="M8.5 12h7"/></g></svg>';
  const error = document.createElement("p");
  error.setAttribute("role", "alert");
  dialog.append(title, close, quote, noteLabel, textarea, save, removeAnnotation, error);
  document.body.append(dialog);
  const previews = document.createElement("aside");
  previews.className = "annotation-previews";
  previews.setAttribute("aria-label", "Notas al margen");
  document.body.append(previews);
  let records = [];
  let selected = null;
  let editing = null;
  let sourceText = "";
  let available = true;
  const message = (text, alert = false) => {
    status.hidden = false;
    status.textContent = text;
    status.setAttribute("role", alert ? "alert" : "status");
  };
  function nodes() {
    const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => node.parentElement.closest(excluded)
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const result = [];
    let offset = 0;
    while (walker.nextNode()) {
      const node = walker.currentNode;
      result.push({ node, start: offset, end: offset + node.length });
      offset += node.length;
    }
    return result;
  }
  function persist(next) {
    if (!available) {
      message("No se puede guardar: revisa el error de las anotaciones antes de continuar.", true);
      return false;
    }
    try {
      localStorage.setItem(key, JSON.stringify({ text: sourceText, records: next }));
      records = next;
      return true;
    } catch (failure) {
      message(`No se pudieron guardar tus anotaciones: ${failure.message}.`, true);
      error.textContent = status.textContent;
      return false;
    }
  }
  function render() {
    content.querySelectorAll("mark[data-annotation]").forEach((mark) => {
      mark.replaceWith(...mark.childNodes);
    });
    content.normalize();
    for (const record of [...records].sort((a, b) => b.start - a.start)) {
      for (const segment of nodes().reverse()) {
        const start = Math.max(record.start, segment.start);
        const end = Math.min(record.end, segment.end);
        if (start >= end) continue;
        const range = document.createRange();
        range.setStart(segment.node, start - segment.start);
        range.setEnd(segment.node, end - segment.start);
        const mark = document.createElement("mark");
        mark.className = `annotation-mark annotation-${record.color}`;
        mark.dataset.annotation = record.id;
        if (record.note) mark.classList.add("annotation-with-note");
        mark.tabIndex = 0;
        mark.setAttribute("role", "button");
        mark.setAttribute("aria-label", record.note ? "Editar nota o eliminar subrayado" : "Editar subrayado");
        range.surroundContents(mark);
      }
    }
    list.replaceChildren();
    summary.textContent = `Mis subrayados y notas (${records.length})`;
    for (const record of records) {
      const item = document.createElement("li");
      const open = document.createElement("button");
      open.type = "button";
      open.textContent = `${record.note ? "Nota" : record.color}: ${record.quote.slice(0, 100)}`;
      open.addEventListener("click", () => {
        content.querySelector(`[data-annotation="${record.id}"]`)?.scrollIntoView({ block: "center" });
        showNote(record);
      });
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "annotation-erase";
      remove.append(removeAnnotation.firstElementChild.cloneNode(true));
      remove.title = "Eliminar subrayado y su nota, si la tiene";
      remove.setAttribute("aria-label", `Eliminar anotación: ${record.quote.slice(0, 60)}`);
      remove.addEventListener("click", () => {
        if (persist(records.filter((entry) => entry.id !== record.id))) {
          render();
          message("Anotación eliminada.");
        }
      });
      item.append(open, remove);
      list.append(item);
    }
    layoutPreviews();
  }
  function layoutPreviews() {
    previews.replaceChildren();
    const bounds = content.getBoundingClientRect();
    const width = Math.min(220, document.documentElement.clientWidth - bounds.right - 36);
    if (width < 170) return;
    let bottom = 0;
    for (const record of [...records].filter((entry) => entry.note).sort((a, b) => a.start - b.start)) {
      const mark = content.querySelector(`[data-annotation="${record.id}"]`);
      if (!mark) continue;
      const anchor = mark.getBoundingClientRect().top + window.scrollY;
      const top = Math.max(anchor, bottom + 12);
      const preview = document.createElement("button");
      preview.type = "button";
      preview.className = `annotation-preview annotation-${record.color}`;
      preview.textContent = record.note;
      preview.title = "Editar nota o eliminar subrayado";
      preview.style.left = `${bounds.right + 20}px`;
      preview.style.top = `${top}px`;
      preview.style.width = `${width}px`;
      preview.style.setProperty("--note-offset", `${top - anchor}px`);
      preview.addEventListener("click", () => showNote(record));
      previews.append(preview);
      bottom = top + preview.getBoundingClientRect().height;
    }
  }
  new ResizeObserver(layoutPreviews).observe(content);
  window.addEventListener("resize", layoutPreviews);
  window.addEventListener("load", layoutPreviews);
  function capture() {
    if (dialog.open) return;
    const selection = window.getSelection();
    if (!selection.rangeCount || selection.isCollapsed) {
      selected = null;
      bar.classList.remove("annotation-floating");
      return;
    }
    const range = selection.getRangeAt(0);
    if (!content.contains(range.startContainer) || !content.contains(range.endContainer)) {
      selected = null;
      bar.classList.remove("annotation-floating");
      return;
    }
    const segments = nodes();
    const start = segments.find((item) => item.node === range.startContainer);
    const end = segments.find((item) => item.node === range.endContainer);
    const crossesExcluded = [...content.querySelectorAll(excluded)].some((item) => {
      return item.textContent && range.intersectsNode(item);
    });
    if (!start || !end || crossesExcluded) {
      selected = null;
      bar.classList.remove("annotation-floating");
      message("Selecciona solo texto de los apuntes, sin esquemas, soluciones ni notas al pie.");
      return;
    }
    selected = {
      start: start.start + range.startOffset,
      end: end.start + range.endOffset,
    };
    selected.quote = sourceText.slice(selected.start, selected.end);
    if (!selected.quote.trim()) { selected = null; return; }
    bar.classList.add("annotation-floating");
    positionToolbar();
    message("Elige un color o pulsa «Añadir nota» para el texto seleccionado.");
  }
  function positionToolbar() {
    if (!bar.classList.contains("annotation-floating") || dialog.open) return;
    const selection = window.getSelection();
    if (!selection.rangeCount || selection.isCollapsed) return;
    const rects = [...selection.getRangeAt(0).getClientRects()];
    const anchor = rects[rects.length - 1];
    if (!anchor) return;
    const bounds = bar.getBoundingClientRect();
    const left = Math.max(8, Math.min(anchor.left, document.documentElement.clientWidth - bounds.width - 8));
    const below = anchor.bottom + 8;
    const top = below + bounds.height <= window.innerHeight - 8
      ? below : Math.max(8, anchor.top - bounds.height - 8);
    bar.style.left = `${left}px`;
    bar.style.top = `${Math.max(8, Math.min(top, window.innerHeight - bounds.height - 8))}px`;
  }
  window.addEventListener("resize", positionToolbar);
  window.addEventListener("scroll", positionToolbar, { passive: true });
  function newRecord(color) {
    if (!selected) {
      message("Selecciona primero el texto que quieres subrayar o comentar.");
      return null;
    }
    if (records.some((record) => record.start < selected.end && record.end > selected.start)) {
      message("Ese texto ya tiene una anotación. Edítala o elimínala desde «Mis subrayados y notas».");
      return null;
    }
    const id = [...crypto.getRandomValues(new Uint32Array(4))].map((value) => value.toString(16)).join("-");
    return { ...selected, id, color, note: "" };
  }
  function showNote(record) {
    editing = record;
    title.textContent = record.note ? "Nota personal" : "Texto subrayado";
    removeAnnotation.hidden = !records.some((entry) => entry.id === record.id);
    const removeLabel = record.note ? "Eliminar subrayado y nota" : "Eliminar subrayado";
    removeAnnotation.setAttribute("aria-label", removeLabel);
    removeAnnotation.title = removeLabel;
    quote.textContent = record.quote;
    textarea.value = record.note;
    error.textContent = "";
    dialog.showModal();
    textarea.focus();
  }
  colors.forEach((color) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `annotation-color annotation-${color}`;
    button.setAttribute("aria-label", `Subrayar en ${color}`);
    button.title = color;
    button.addEventListener("pointerdown", (event) => event.preventDefault());
    button.addEventListener("click", () => {
      const record = newRecord(color);
      if (record && persist([...records, record])) {
        render();
        selected = null;
        window.getSelection().removeAllRanges();
        bar.classList.remove("annotation-floating");
        message(`Subrayado ${color} guardado en este navegador.`);
      }
    });
    bar.append(button);
  });
  const addNote = document.createElement("button");
  addNote.type = "button";
  addNote.textContent = "Añadir nota";
  addNote.addEventListener("pointerdown", (event) => event.preventDefault());
  addNote.addEventListener("click", () => {
    const record = newRecord("amarillo");
    if (record) showNote(record);
  });
  bar.append(addNote);
  close.addEventListener("click", () => dialog.close());
  removeAnnotation.addEventListener("click", () => {
    if (editing && persist(records.filter((record) => record.id !== editing.id))) {
      dialog.close();
      render();
      message("Subrayado y su nota, si la había, eliminados. El texto original se conserva.");
    }
  });
  dialog.addEventListener("close", () => { editing = null; });
  save.addEventListener("click", () => {
    const note = textarea.value.trim();
    if (!note) { error.textContent = "Escribe una nota antes de guardarla."; return; }
    const updated = { ...editing, note };
    const next = records.filter((record) => record.id !== editing.id);
    if (persist([...next, updated])) {
      dialog.close();
      render();
      window.getSelection().removeAllRanges();
      bar.classList.remove("annotation-floating");
      message("Nota guardada en este navegador.");
    }
  });
  content.addEventListener("click", (event) => {
    const mark = event.target.closest("mark[data-annotation]");
    if (!mark || !window.getSelection().isCollapsed) return;
    showNote(records.find((record) => record.id === mark.dataset.annotation));
  });
  content.addEventListener("keydown", (event) => {
    const mark = event.target.closest("mark[data-annotation]");
    if (mark && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      showNote(records.find((record) => record.id === mark.dataset.annotation));
    }
  });
  sourceText = nodes().map((item) => item.node.textContent).join("");
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const stored = JSON.parse(raw);
      const caseOnlyChange = typeof stored.text === "string"
        && stored.text.length === sourceText.length
        && stored.text.toLocaleLowerCase("es") === sourceText.toLocaleLowerCase("es");
      if (stored.text !== sourceText && !caseOnlyChange) {
        const archiveKey = `${key}.archive.${crypto.randomUUID()}`;
        localStorage.setItem(archiveKey, raw);
        console.info("Anotaciones de la versión anterior archivadas en este navegador:", archiveKey);
      } else {
        if (!Array.isArray(stored.records) || !stored.records.every((record) =>
          Number.isInteger(record.start) && Number.isInteger(record.end)
          && record.start >= 0 && record.end > record.start && record.end <= sourceText.length
          && record.quote === stored.text.slice(record.start, record.end)
          && colors.includes(record.color) && typeof record.note === "string"
          && typeof record.id === "string" && /^[\w-]+$/.test(record.id)
        )) throw new Error("Los datos de las anotaciones no tienen un formato válido");
        records = stored.records;
        if (stored.text !== sourceText) {
          const updated = records.map((record) => ({
            ...record, quote: sourceText.slice(record.start, record.end),
          }));
          if (!persist(updated)) {
            available = false;
            return;
          }
          message("Tus subrayados y notas se han conservado tras corregir las mayúsculas de los apuntes.");
        }
        render();
      }
    }
  } catch (failure) {
    available = false;
    message(`No se pudieron recuperar las anotaciones: ${failure.message}.`, true);
  }
  document.addEventListener("selectionchange", capture);
  window.addEventListener("storage", (event) => {
    if (event.key === key) {
      available = false;
      message("Las anotaciones han cambiado en otra pestaña. Recarga antes de editarlas para no sobrescribirlas.", true);
    }
  });
})();
