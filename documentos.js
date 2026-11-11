(() => {
  const search = document.querySelector("#document-search");
  const block = document.querySelector("#document-block");
  const topics = document.querySelector("#document-topics");
  const grid = document.querySelector("#document-grid");
  const count = document.querySelector("#document-count");
  const error = document.querySelector("#document-error");
  const retry = document.querySelector("#document-retry");
  const dialog = document.querySelector("#document-dialog");
  const content = document.querySelector("#document-dialog-content");
  const typeNames = { texto: "Texto", imagen: "Imagen", grafico: "Gráfico o tabla" };
  let documents = [];
  let type = "all";
  let topic = "";
  let opener = null;
  const normalize = (value) => String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const link = (text, href) => {
    const node = element("a", text);
    node.href = href;
    return node;
  };
  function source(document, preview = false) {
    const box = element("div", undefined, preview ? "document-preview" : "document-full-source");
    if (document.image) {
      const image = element("img");
      image.src = document.image.src;
      image.alt = document.image.alt;
      image.width = document.image.width;
      image.height = document.image.height;
      image.loading = preview ? "lazy" : "eager";
      image.addEventListener("error", () => {
        image.hidden = true;
        box.append(element("p", "No se pudo cargar la imagen. Consulta la recopilación enlazada en las apariciones.", "document-quality"));
      }, { once: true });
      box.append(image);
      if (!preview) {
        const zoom = element("button", "Ampliar imagen", "document-zoom");
        zoom.type = "button";
        zoom.setAttribute("aria-pressed", "false");
        zoom.addEventListener("click", () => {
          const expanded = box.classList.toggle("is-zoomed");
          zoom.setAttribute("aria-pressed", String(expanded));
          zoom.textContent = expanded ? "Ajustar a la pantalla" : "Ampliar imagen";
        });
        box.prepend(zoom);
      }
    }
    if (document.table && (!preview || !document.image)) {
      const table = element("table", undefined, "document-table");
      table.append(element("caption", document.table.caption));
      const head = element("tr");
      document.table.headers.forEach((value) => {
        const cell = element("th", value);
        cell.scope = "col";
        head.append(cell);
      });
      const thead = element("thead");
      thead.append(head);
      table.append(thead);
      const body = element("tbody");
      document.table.rows.forEach((values) => {
        const row = element("tr");
        values.forEach((value, i) => {
          const cell = element(i === 0 ? "th" : "td", String(value));
          if (i === 0) cell.scope = "row";
          row.append(cell);
        });
        body.append(row);
      });
      table.append(body);
      box.append(table);
    } else if (!document.image && !document.table) {
      const quote = element("blockquote");
      (preview ? document.text.slice(0, 3) : document.text).forEach((paragraph) => quote.append(element("p", paragraph)));
      box.append(quote);
      if (preview) {
        const more = element("span", "… ", "document-read-more");
        more.setAttribute("aria-hidden", "true");
        more.append(element("span", "Leer más"));
        box.append(more);
      }
    }
    return box;
  }
  function open(document, button) {
    opener = button;
    content.replaceChildren();
    content.append(element("p", `${typeNames[document.type]} · Bloque ${document.blocks.join(" · ")}`, "document-kind"));
    const title = element("h2", document.title);
    title.id = "document-dialog-title";
    content.append(title, element("p", document.date, "document-meta"), source(document));
    content.append(element("p", document.sourceCaption, "document-source-caption"));
    content.append(element("p", document.quality, "document-quality"));
    const guide = element("details", undefined, "document-guide");
    guide.append(element("summary", "Claves para responder a) y b)"));
    guide.append(element("p", "Orientación didáctica propia; no es una solución oficial.", "document-meta"));
    document.commentary.forEach((section) => guide.append(element("h3", section.title), element("p", section.text)));
    const task = element("section", undefined, "document-task");
    task.setAttribute("aria-label", "Práctica del modelo 2026–27");
    task.append(element("h3", "Practica con el modelo 2026–27 · 4 puntos en total"));
    task.append(element("p", "a) Analice el hecho histórico a que hace referencia el documento elegido."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    task.append(element("p", "b) Explique el contexto histórico y las consecuencias de este acontecimiento."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    const guidance = document.type === "texto"
      ? "En textos, a) permite desarrollar naturaleza, ideas principales y secundarias y contexto inmediato; b) explica el proceso general, sus causas y consecuencias. La extensión puede estar más equilibrada."
      : "En imágenes y gráficos, a) es más breve y descriptivo: identifica los elementos y sitúalos en su contexto inmediato. Dedica mayor desarrollo a b): evolución general del momento, causas y consecuencias relacionadas con el documento.";
    task.append(element("p", `${guidance} Pauta docente: a) no debería superar media carilla. No es un límite oficial añadido al examen ni cambia la puntuación: ambos apartados valen lo mismo.`, "document-meta"));
    content.append(task, guide);
    content.append(element("h3", "Apariciones incorporadas"));
    const appearances = element("ul", undefined, "document-appearances");
    document.appearances.forEach((appearance) => {
      const item = element("li");
      item.append(element("span", `${appearance.year} · ${appearance.exam} · ${appearance.route} · Documento ${appearance.document}. `));
      item.append(link("Ver en la recopilación ↗", appearance.sourceUrl));
      appearances.append(item);
    });
    content.append(appearances, element("p", "Formato histórico, anterior a 2026–27. No es una predicción del examen nuevo.", "document-meta"));
    document.blocks.forEach((number) => content.append(link(`Ir a los apuntes del bloque ${number} →`, `apuntes/bloque-${number}.html`)));
    dialog.showModal();
    dialog.scrollTop = 0;
  }
  dialog.querySelector(".document-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => opener?.focus());
  const baseMatches = (document) => {
    const haystack = normalize([document.title, document.date, document.sourceCaption, ...document.tags,
      ...document.appearances.map((appearance) => `${appearance.year} ${appearance.exam}`)].join(" "));
    return (type === "all" || document.type === type)
      && (!block.value || document.blocks.includes(Number(block.value)))
      && normalize(search.value).trim().split(/\s+/).every((word) => haystack.includes(word));
  };
  function renderTopics() {
    const available = documents.filter(baseMatches);
    const tags = [...new Set(available.flatMap((document) => document.tags))].sort((a, b) => a.localeCompare(b, "es"));
    if (topic && !tags.includes(topic)) topic = "";
    topics.replaceChildren();
    for (const tag of ["", ...tags]) {
      const total = tag ? available.filter((document) => document.tags.includes(tag)).length : available.length;
      const button = element("button", `${tag || "Todas las temáticas"} (${total})`);
      button.type = "button";
      button.setAttribute("aria-pressed", String(topic === tag));
      button.addEventListener("click", () => {
        topic = tag;
        render();
        [...topics.children].find((node) => node.textContent === button.textContent)?.focus();
      });
      topics.append(button);
    }
  }
  function render() {
    renderTopics();
    const matches = documents.filter((document) => baseMatches(document) && (!topic || document.tags.includes(topic)));
    const appearances = matches.reduce((total, document) => total + document.appearances.length, 0);
    count.textContent = `${matches.length} ${matches.length === 1 ? "documento" : "documentos"} · ${appearances} ${appearances === 1 ? "aparición incorporada" : "apariciones incorporadas"}`;
    grid.replaceChildren();
    document.querySelector("#document-empty").hidden = matches.length > 0;
    const numbers = block.value ? [Number(block.value)]
      : [...new Set(matches.flatMap((document) => document.blocks))].sort((a, b) => a - b);
    const displayed = new Set();
    for (const number of numbers) {
      const group = matches.filter((document) => document.blocks.includes(number) && !displayed.has(document.id));
      if (!group.length) continue;
      const section = element("section");
      const heading = element("div", undefined, "document-block-heading");
      const blockName = block.querySelector(`option[value="${number}"]`).textContent.replace(/^\d+ · /, "");
      heading.append(element("h2", `Bloque ${number}, ${blockName}`), link("Ver apuntes →", `apuntes/bloque-${number}.html`));
      const cards = element("div", undefined, "document-card-grid");
      for (const document of group) {
        displayed.add(document.id);
        const card = element("article", undefined, "document-card");
        card.dataset.id = document.id;
        card.dataset.documentType = document.type;
        card.append(source(document, true));
        const body = element("div", undefined, "document-card-body");
        body.append(element("p", document.type === "texto" ? "Texto · vista previa" : typeNames[document.type], "document-kind"), element("h3", document.title));
        body.append(element("p", `${document.date} · ${document.appearances.length} ${document.appearances.length === 1 ? "aparición incorporada" : "apariciones incorporadas"}`, "document-meta"));
        body.append(element("p", document.tags.join(" · "), "document-card-topics"));
        const button = element("button", document.type === "texto" ? "Leer texto completo y practicar →" : "Ver documento y practicar →", "document-open");
        button.type = "button";
        button.setAttribute("aria-label", `Ver documento: ${document.title}`);
        button.addEventListener("click", () => open(document, button));
        body.append(button);
        card.append(body);
        cards.append(card);
      }
      section.append(heading, cards);
      grid.append(section);
    }
  }
  document.querySelectorAll("[data-type]").forEach((button) => button.addEventListener("click", () => {
    type = button.dataset.type;
    document.querySelectorAll("[data-type]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    render();
  }));
  search.addEventListener("input", render);
  block.addEventListener("change", render);
  document.querySelector("#document-reset").addEventListener("click", () => {
    search.value = "";
    block.value = "";
    type = "all";
    topic = "";
    document.querySelectorAll("[data-type]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.type === "all")));
    render();
  });
  async function load() {
    retry.hidden = true;
    error.hidden = true;
    count.textContent = "Cargando documentos…";
    try {
      const response = await fetch("data/documentos.json");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.documents) || !data.documents.length) throw new Error("El banco no contiene documentos");
      if (data.documents.some((document) => !Array.isArray(document.blocks) || !document.blocks.length
        || document.blocks.some((number) => !Number.isInteger(number) || number < 5 || number > 12))) {
        throw new Error("Los documentos deben pertenecer a los bloques 5–12");
      }
      documents = data.documents;
      const requestedBlock = new URLSearchParams(location.search).get("bloque");
      if (requestedBlock && block.querySelector(`option[value="${Number(requestedBlock)}"]`)) block.value = requestedBlock;
      render();
    } catch (failure) {
      count.textContent = "Banco no disponible";
      error.textContent = `No se pudo cargar el banco de documentos (${failure.message}). Puedes reintentarlo o consultar la recopilación al final de la página.`;
      error.hidden = false;
      retry.hidden = false;
      console.error("No se pudo cargar el banco de documentos:", failure);
    }
  }
  retry.addEventListener("click", load);
  load();
})();
