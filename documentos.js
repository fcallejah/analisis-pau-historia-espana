(() => {
  const search = document.querySelector("#document-search");
  const topicSearch = document.querySelector("#document-topic-search");
  const block = document.querySelector("#document-block");
  const topics = document.querySelector("#document-topics");
  const topicSort = document.querySelector("#document-topic-sort");
  const topicToggle = document.querySelector("#document-topic-toggle");
  const topicEmpty = document.querySelector("#document-topic-empty");
  const grid = document.querySelector("#document-grid");
  const count = document.querySelector("#document-count");
  const error = document.querySelector("#document-error");
  const retry = document.querySelector("#document-retry");
  const dialog = document.querySelector("#document-dialog");
  const content = document.querySelector("#document-dialog-content");
  const typeButtons = [...document.querySelectorAll("[data-type]")];
  const typeStorageKey = "pau-he.document-type";
  const typeNames = { texto: "Texto", imagen: "Imagen", grafico: "Gráfico o tabla" };
  let documents = [];
  let type = "all";
  try {
    const savedType = sessionStorage.getItem(typeStorageKey);
    if (["all", "texto", "imagen", "grafico"].includes(savedType)) type = savedType;
  } catch {
    type = "all";
  }
  function setType(value) {
    type = value;
    typeButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.type === type)));
    try {
      sessionStorage.setItem(typeStorageKey, type);
    } catch {
      // The selected filter remains usable if session storage is unavailable.
    }
  }
  let topic = "";
  let topicsExpanded = false;
  let opener = null;
  let pagePosition = null;
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
    const cardImage = document.image || document.tableImage;
    if (preview && (document.tableImage || cardImage?.kind === "table")) {
      box.classList.add("document-preview-table");
    }
    const fullImages = [document.image, document.tableImage]
      .filter((image, index, images) => image && images.findIndex((candidate) => candidate?.src === image.src) === index);
    const visibleImages = preview ? [cardImage].filter(Boolean) : fullImages;
    visibleImages.forEach((imageData) => {
      const figure = element("figure", undefined, "document-image-figure");
      const image = element("img");
      image.src = imageData.src;
      image.alt = imageData.alt;
      image.width = imageData.width;
      image.height = imageData.height;
      image.loading = preview ? "lazy" : "eager";
      image.addEventListener("error", () => {
        image.hidden = true;
        box.append(element("p", "No se pudo cargar la imagen. Consulta la recopilación enlazada en las apariciones.", "document-quality"));
      }, { once: true });
      if (imageData.crop) {
        const crop = imageData.crop;
        const frame = element("span", undefined, "doc-image-crop");
        frame.style.setProperty("--doc-frame-width", `${imageData.width * crop.width / crop.imageWidth}px`);
        frame.style.setProperty("--doc-frame-ratio", `${crop.width} / ${crop.height}`);
        frame.style.setProperty("--document-crop-aspect", crop.width / crop.height);
        frame.style.setProperty("--doc-img-width", `${100 * crop.imageWidth / crop.width}%`);
        frame.style.setProperty("--doc-img-height", `${100 * crop.imageHeight / crop.height}%`);
        frame.style.setProperty("--doc-img-left", `${100 * crop.left / crop.width}%`);
        frame.style.setProperty("--doc-img-top", `${100 * crop.top / crop.height}%`);
        frame.append(image);
        figure.append(frame);
      } else {
        figure.append(image);
      }
      if (!preview && imageData.caption) figure.append(element("figcaption", imageData.caption, "document-image-caption"));
      if (!preview && imageData.sourceUrl) {
        const attribution = link("Fuente de esta reproducción ↗", imageData.sourceUrl);
        attribution.className = "document-image-caption";
        figure.append(attribution);
      }
      if (!preview && imageData.originalSrc) {
        const original = link("Ver recorte del PDF original ↗", imageData.originalSrc);
        original.className = "document-image-caption document-original-link";
        figure.append(original);
      }
      box.append(figure);
    });
    if (visibleImages.length && !preview) {
      const zoom = element("button", "Ampliar imagen", "document-zoom");
      zoom.type = "button";
      zoom.setAttribute("aria-pressed", "false");
      zoom.addEventListener("click", () => {
        const expanded = box.classList.toggle("is-zoomed");
        zoom.setAttribute("aria-pressed", String(expanded));
        zoom.textContent = expanded ? "Ajustar a la pantalla" : "Ampliar imagen";
      });
      box.prepend(zoom);
    } else if (preview && cardImage) {
      const zoom = element("button", undefined, "document-preview-zoom");
      zoom.type = "button";
      zoom.setAttribute("aria-label", `Ampliar imagen: ${document.title}`);
      zoom.title = "Ampliar imagen";
      const icon = window.document.createElementNS("http://www.w3.org/2000/svg", "svg");
      icon.setAttribute("viewBox", "0 0 24 24");
      icon.setAttribute("aria-hidden", "true");
      icon.setAttribute("fill", "none");
      icon.setAttribute("stroke", "currentColor");
      icon.setAttribute("stroke-width", "2");
      const lens = window.document.createElementNS("http://www.w3.org/2000/svg", "circle");
      lens.setAttribute("cx", "10.5");
      lens.setAttribute("cy", "10.5");
      lens.setAttribute("r", "6.5");
      const handle = window.document.createElementNS("http://www.w3.org/2000/svg", "path");
      handle.setAttribute("d", "m16 16 5 5");
      icon.append(lens, handle);
      zoom.append(icon);
      zoom.addEventListener("click", () => open(document, zoom, true));
      box.append(zoom);
    }
    if (document.table && (!preview || !cardImage)) {
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
      if (preview) {
        box.append(table);
      } else {
        const details = element("details", undefined, "document-table-details");
        details.append(element("summary", "Leer la tabla en texto"));
        details.append(table);
        document.table.notes?.forEach((note) => details.append(element("p", note, "document-image-caption")));
        box.append(details);
      }
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
  function open(document, button, zoomImage = false) {
    pagePosition = { left: window.scrollX, top: window.scrollY };
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
      const exam = appearance.exam.replace(new RegExp(`^${appearance.year}\\s+`), "");
      const pendingRoute = appearance.route.endsWith("sin cotejar");
      const label = [appearance.year, exam, pendingRoute ? "" : appearance.route, `Documento ${appearance.document}`]
        .filter((part) => part !== "").join(" · ");
      item.append(element("span", label, "exam-pill"));
      item.append(link("Ver en la recopilación ↗", appearance.sourceUrl));
      if (pendingRoute) {
        const note = appearance.route.startsWith("Opción")
          ? "Opción A/B pendiente de comprobar en el PDF oficial."
          : "Itinerario pendiente de comprobar en el PDF oficial.";
        item.append(element("small", note, "document-appearance-note"));
      }
      appearances.append(item);
    });
    content.append(appearances, element("p", "Formato histórico, anterior a 2026–27. No es una predicción del examen nuevo.", "document-meta"));
    document.blocks.forEach((number) => content.append(link(`Ir a los apuntes del bloque ${number} →`, `apuntes/bloque-${number}.html`)));
    dialog.showModal();
    dialog.scrollTop = 0;
    if (zoomImage) content.querySelector(".document-zoom")?.click();
  }
  dialog.querySelector(".document-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    opener?.focus({ preventScroll: true });
    if (pagePosition) {
      window.scrollTo({ ...pagePosition, behavior: "instant" });
      pagePosition = null;
    }
  });
  const baseMatches = (document) => {
    const haystack = normalize([document.title, document.date, document.sourceCaption, ...document.tags,
      ...document.appearances.map((appearance) => `${appearance.year} ${appearance.exam}`)].join(" "));
    return (type === "all" || document.type === type)
      && (!block.value || document.blocks.includes(Number(block.value)))
      && normalize(search.value).trim().split(/\s+/).every((word) => haystack.includes(word));
  };
  function fitTopics() {
    const bubbles = [...topics.querySelectorAll(".document-topic-bubble")];
    const showAll = topicsExpanded || normalize(topicSearch.value).trim();
    bubbles.forEach((button, index) => {
      button.hidden = !showAll && index >= 8 && button.getAttribute("aria-pressed") !== "true";
    });
    topicToggle.hidden = Boolean(normalize(topicSearch.value).trim()) || bubbles.length <= 8;
    if (showAll || topicToggle.hidden) return;
    const rowCount = () => {
      let rows = 1;
      let previousRight = -Infinity;
      for (const button of topics.children) {
        if (button.hidden) continue;
        const bounds = button.getBoundingClientRect();
        if (bounds.left < previousRight - 1) rows += 1;
        previousRight = bounds.right;
      }
      return rows;
    };
    const rows = rowCount();
    for (const button of bubbles) {
      if (!button.hidden) continue;
      button.hidden = false;
      if (rowCount() > rows) {
        button.hidden = true;
        break;
      }
    }
    topicToggle.hidden = bubbles.every((button) => !button.hidden);
  }
  let topicWidth = 0;
  new ResizeObserver(([entry]) => {
    if (entry.contentRect.width === topicWidth) return;
    topicWidth = entry.contentRect.width;
    fitTopics();
  }).observe(topics);
  document.fonts.ready.then(fitTopics);
  function renderTopics() {
    const available = documents.filter(baseMatches);
    const tags = [...new Set(available.flatMap((document) => document.tags))];
    const statistics = new Map(tags.map((tag) => {
      const tagged = available.filter((document) => document.tags.includes(tag));
      const firstYear = Math.min(...tagged.map((document) => {
        const year = String(document.date).match(/\b(?:1[0-9]{3}|20[0-9]{2})\b/);
        return year ? Number(year[0]) : Number.MAX_SAFE_INTEGER;
      }));
      return [tag, {
        documents: tagged.length,
        appearances: tagged.reduce((total, document) => total + document.appearances.length, 0),
        firstYear,
      }];
    }));
    tags.sort((first, second) => {
      const firstStats = statistics.get(first);
      const secondStats = statistics.get(second);
      if (topicSort.value === "frequency") {
        return secondStats.appearances - firstStats.appearances
          || secondStats.documents - firstStats.documents
          || first.localeCompare(second, "es");
      }
      if (topicSort.value === "chronology") {
        return firstStats.firstYear - secondStats.firstYear || first.localeCompare(second, "es");
      }
      return first.localeCompare(second, "es");
    });
    if (topic && !tags.includes(topic)) topic = "";
    const query = normalize(topicSearch.value).trim();
    const matchingTags = tags.filter((tag) => normalize(tag).includes(query));
    topics.replaceChildren();
    topicEmpty.hidden = !query || matchingTags.length > 0;
    topicToggle.hidden = Boolean(query) || matchingTags.length <= 8;
    topicToggle.textContent = topicsExpanded ? "Ver menos ↑" : "Ver más ↓";
    topicToggle.setAttribute("aria-expanded", String(topicsExpanded));
    const allButton = element("button", `Todas las temáticas (${available.length})`);
    allButton.className = "document-topic-all";
    allButton.type = "button";
    allButton.setAttribute("aria-pressed", String(topic === ""));
    allButton.addEventListener("click", () => {
      topic = "";
      render();
      topics.firstElementChild.focus();
    });
    topics.append(allButton);
    const minCount = Math.min(...matchingTags.map((tag) => statistics.get(tag).appearances));
    const maxCount = Math.max(...matchingTags.map((tag) => statistics.get(tag).appearances));
    for (const tag of matchingTags) {
      const stats = statistics.get(tag);
      const button = element("button", `${tag} (${stats.appearances})`);
      button.classList.add("document-topic-bubble");
      const scale = maxCount === minCount ? 1
        : 0.94 + 0.56 * (Math.log1p(stats.appearances) - Math.log1p(minCount))
          / (Math.log1p(maxCount) - Math.log1p(minCount));
      button.style.setProperty("--topic-font-size", `${12 * scale}px`);
      button.style.setProperty("--topic-padding-y", `${6 * scale}px`);
      button.style.setProperty("--topic-padding-x", `${11 * scale}px`);
      button.title = `${stats.appearances} ${stats.appearances === 1 ? "aparición" : "apariciones"} en ${stats.documents} ${stats.documents === 1 ? "ficha" : "fichas"} del corpus`;
      button.setAttribute("aria-label", `${tag}: ${button.title}`);
      button.type = "button";
      button.setAttribute("aria-pressed", String(topic === tag));
      button.addEventListener("click", () => {
        topic = tag;
        render();
        [...topics.children].find((node) => node.textContent === button.textContent)?.focus();
      });
      topics.append(button);
    }
    topics.append(topicToggle);
    fitTopics();
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
      const notes = link("", `apuntes/bloque-${number}.html`);
      notes.setAttribute("aria-label", `Ver apuntes del bloque ${number}`);
      const sheet = window.document.createElementNS("http://www.w3.org/2000/svg", "svg");
      sheet.setAttribute("viewBox", "0 0 24 24");
      sheet.setAttribute("aria-hidden", "true");
      sheet.setAttribute("fill", "none");
      sheet.setAttribute("stroke", "currentColor");
      sheet.setAttribute("stroke-width", "1.7");
      sheet.setAttribute("stroke-linecap", "round");
      sheet.setAttribute("stroke-linejoin", "round");
      const lines = window.document.createElementNS("http://www.w3.org/2000/svg", "path");
      lines.setAttribute("d", "M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8l-5-5Zm0 0v5h5M8 12h8M8 16h8");
      sheet.append(lines);
      notes.append(sheet, element("span", "Ver apuntes"));
      heading.append(element("h2", `Bloque ${number} · ${blockName}`), notes);
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
  typeButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.type === type));
    button.addEventListener("click", () => {
      setType(button.dataset.type);
      render();
    });
  });
  topicSearch.addEventListener("input", () => {
    topic = "";
    renderTopics();
  });
  topicToggle.addEventListener("click", () => {
    topicsExpanded = !topicsExpanded;
    renderTopics();
    topicToggle.focus();
  });
  topicSort.addEventListener("change", renderTopics);
  search.addEventListener("input", render);
  block.addEventListener("change", render);
  document.querySelector("#document-reset").addEventListener("click", () => {
    search.value = "";
    block.value = "";
    setType("all");
    topic = "";
    topicSearch.value = "";
    topicsExpanded = false;
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
      const coverage = data.coverage;
      if (!coverage || !Array.isArray(coverage.sourceManifest)
        || coverage.sourceDocumentOccurrences !== coverage.sourceManifest.length) {
        throw new Error("El inventario de apariciones está incompleto");
      }
      const manifestKeys = coverage.sourceManifest.map((source) => source.key);
      const appearanceKeys = data.documents.flatMap((document) =>
        document.appearances.map((appearance) => appearance.sourceKey));
      if (manifestKeys.some((key) => !key) || appearanceKeys.some((key) => !key)
        || new Set(manifestKeys).size !== manifestKeys.length
        || appearanceKeys.length !== manifestKeys.length
        || new Set(appearanceKeys).size !== appearanceKeys.length
        || manifestKeys.some((key) => !appearanceKeys.includes(key))
        || coverage.sourceImageOccurrences !== coverage.sourceManifest.reduce(
          (total, source) => total + source.images.length, 0,
        )) {
        throw new Error("Las apariciones y las imágenes no coinciden con el inventario");
      }
      document.querySelector("#document-scope").textContent =
        `${data.documents.length} fichas · ${coverage.sourceDocumentOccurrences} apariciones documentales · `
        + `${coverage.sourceImageOccurrences} apariciones de imágenes. ${coverage.formatNote} `
        + "El recuento refleja solo la exportación disponible; las transcripciones y la cobertura deben cotejarse con los PDF oficiales.";
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
