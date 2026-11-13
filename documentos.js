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
  const savedButtons = [...document.querySelectorAll("[data-document-saved]")];
  const savedOnly = document.body.dataset.documentLibrary === "saved";
  const typeStorageKey = savedOnly ? "pau-he.documents.saved-type" : "pau-he.document-type";
  const viewStorageKey = savedOnly ? "pau-he.documents.saved-view.v1" : "pau-he.documents.view.v1";
  const marksStorageKey = "pau-he.documents.marks.v1";
  const typeNames = { texto: "Texto", imagen: "Imagen", grafico: "Gráfico o tabla" };
  const imagePanUpdates = new WeakMap();
  const imagePanObserver = typeof ResizeObserver === "function"
    ? new ResizeObserver((entries) => entries.forEach(({ target }) => imagePanUpdates.get(target)?.()))
    : null;
  window.addEventListener("resize", () => {
    imagePanUpdates.get(content.querySelector(".document-full-source"))?.();
  });
  let documents = [];
  let type = "all";
  let savedFilter = "all";
  let marks = {};
  let viewWritable = true;
  let loaded = false;
  let restoring = true;
  let selectedId = null;
  let restoredView = null;
  const notices = new Map();
  function reportStorage(area, message, failed = false) {
    if (message) notices.set(area, { message, failed });
    else notices.delete(area);
    const text = [...notices.values()].map((notice) => notice.message).join(" ");
    for (const node of document.querySelectorAll(".document-storage-status")) {
      node.textContent = text;
      node.hidden = !text;
      node.setAttribute("role", [...notices.values()].some((notice) => notice.failed) ? "alert" : "status");
    }
  }
  const positionValid = (value) => value && [value.left, value.top]
    .every((number) => Number.isFinite(number) && number >= 0);
  function compatibleView(value) {
    if (!value || value.version !== 1) return value;
    // Earlier v1 snapshots predate saved filters and opener tracking.
    return {
      ...value,
      savedFilter: value.savedFilter === undefined ? "all" : value.savedFilter,
      dialog: value.dialog && {
        ...value.dialog,
        opener: value.dialog.opener === undefined ? "open" : value.dialog.opener,
      },
    };
  }
  function validView(value) {
    return value && value.version === 1 && typeof value.url === "string"
      && ["all", "texto", "imagen", "grafico"].includes(value.type)
      && ["all", "favorite", "review"].includes(value.savedFilter)
      && ["", "5", "6", "7", "8", "9", "10", "11", "12"].includes(value.block)
      && typeof value.search === "string" && typeof value.topic === "string"
      && typeof value.topicSearch === "string" && typeof value.expanded === "boolean"
      && ["alphabetical", "frequency", "chronology"].includes(value.sort)
      && positionValid(value.page)
      && (value.dialog === null || (value.dialog && typeof value.dialog.id === "string"
        && ["open", "zoom"].includes(value.dialog.opener)
        && positionValid(value.dialog.position) && positionValid(value.dialog.source)
        && typeof value.dialog.zoom === "boolean" && Array.isArray(value.dialog.details)
        && value.dialog.details.every((open) => typeof open === "boolean")));
  }
  try {
    const raw = sessionStorage.getItem(viewStorageKey);
    if (raw !== null) {
      const value = compatibleView(JSON.parse(raw));
      if (!validView(value)) throw new Error("Formato de vista no válido");
      if (value.url === location.href) restoredView = value;
    }
    const savedType = sessionStorage.getItem(typeStorageKey);
    if (["all", "texto", "imagen", "grafico"].includes(savedType)) type = savedType;
  } catch (error) {
    viewWritable = false;
    console.warn("No se pudo recuperar la posición de lectura guardada:", error);
  }
  function setType(value) {
    type = value;
    typeButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.type === type)));
  }
  let topic = "";
  let topicsExpanded = false;
  let opener = null;
  let pagePosition = null;
  function scrollPage(position) {
    const root = document.documentElement;
    const previous = root.style.scrollBehavior;
    root.style.scrollBehavior = "auto";
    window.scrollTo(position.left, position.top);
    root.style.scrollBehavior = previous;
  }
  function updateReaderCue() {
    dialog.classList.toggle("has-more-below",
      dialog.open && dialog.scrollHeight - dialog.clientHeight - dialog.scrollTop > 2);
  }
  const readerObserver = new ResizeObserver(updateReaderCue);
  readerObserver.observe(content);
  readerObserver.observe(dialog);
  dialog.addEventListener("scroll", updateReaderCue, { passive: true });
  function readMarks() {
    const raw = localStorage.getItem(marksStorageKey);
    if (raw === null) return {};
    const value = JSON.parse(raw);
    if (!value || Array.isArray(value) || typeof value !== "object"
      || !Object.entries(value).every(([id, item]) => id && item && typeof item === "object"
        && typeof item.favorite === "boolean" && typeof item.review === "boolean")) {
      throw new Error("Formato de marcas no válido");
    }
    return value;
  }
  try { marks = readMarks(); }
  catch {
    reportStorage("marks", "No se pudieron leer las marcas del banco. No se sobrescribirán datos inválidos.", true);
  }
  function saveView() {
    if (!loaded || restoring || !viewWritable) return;
    const box = content.querySelector(".document-full-source");
    const position = (node) => ({ left: node?.scrollLeft || 0, top: node?.scrollTop || 0 });
    const value = {
      version: 1, url: location.href, type, savedFilter, block: block.value,
      search: search.value, topic, topicSearch: topicSearch.value, sort: topicSort.value,
      expanded: topicsExpanded,
      page: dialog.open && pagePosition ? pagePosition : { left: scrollX, top: scrollY },
      dialog: dialog.open ? {
        id: selectedId, opener: opener?.matches(".document-preview-zoom") ? "zoom" : "open",
        position: position(dialog), source: position(box), zoom: !!box?.classList.contains("is-zoomed"),
        details: [...content.querySelectorAll("details")].map((node) => node.open),
      } : null,
    };
    try {
      const current = sessionStorage.getItem(viewStorageKey);
      if (current !== null && !validView(compatibleView(JSON.parse(current)))) throw new Error("Formato de vista no válido");
      sessionStorage.setItem(viewStorageKey, JSON.stringify(value));
      sessionStorage.setItem(typeStorageKey, type);
    } catch (error) {
      console.warn("No se pudo guardar la posición de lectura:", error);
    }
  }
  let saveFrame = 0;
  function scheduleSave() {
    if (restoring || !loaded || saveFrame) return;
    saveFrame = requestAnimationFrame(() => { saveFrame = 0; saveView(); });
  }
  window.addEventListener("scroll", scheduleSave, { passive: true });
  dialog.addEventListener("scroll", scheduleSave, { passive: true, capture: true });
  content.addEventListener("toggle", scheduleSave, true);
  content.addEventListener("click", scheduleSave);
  document.querySelector(".documents-filters").addEventListener("input", scheduleSave);
  document.querySelector(".documents-filters").addEventListener("change", scheduleSave);
  document.querySelector(".documents-filters").addEventListener("click", scheduleSave);
  window.addEventListener("pagehide", saveView);
  document.addEventListener("visibilitychange", () => { if (document.hidden) saveView(); });
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
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
  const sourceLink = (text, href) => {
    const node = link(text, href);
    node.append(" ");
    node.insertAdjacentHTML("beforeend", '<svg class="document-link-icon" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M7 7h10v10"/></svg>');
    return node;
  };
  const sourceParagraph = (text, emphasis = [], className) => {
    const node = element("p", undefined, className);
    let position = 0;
    for (const phrase of emphasis) {
      const start = text.indexOf(phrase, position);
      if (start < 0) throw new Error(`Fragmento en cursiva no encontrado: ${phrase}`);
      node.append(text.slice(position, start), element("em", phrase));
      position = start + phrase.length;
    }
    node.append(text.slice(position));
    return node;
  };
  function appearancePill(appearance, compact = false) {
    const exam = appearance.exam.replace(new RegExp(`^${appearance.year}\\s+`), "");
    const pendingRoute = appearance.route.endsWith("sin cotejar");
    const label = [
      appearance.year, compact ? exam.replace(/\s*\([^)]*\)\s*$/, "") : exam,
      pendingRoute ? "" : appearance.route, `Documento ${appearance.document}`,
    ].filter((part) => part !== "").join(" · ");
    const pill = element("span", label, "exam-pill");
    pill.title = [appearance.year, exam, appearance.route, `Documento ${appearance.document}`].join(" · ");
    return pill;
  }
  function appearanceBadges(record) {
    const list = element("ul", undefined, "document-exams");
    list.setAttribute("aria-label", "Apariciones en exámenes");
    record.appearances.forEach((appearance) => {
      const item = element("li");
      item.append(appearancePill(appearance, true));
      list.append(item);
    });
    return list;
  }
  const star = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9Z"/></svg>';
  const cap = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="m2 8 10-5 10 5-10 5Z M5 10v6q7 5 14 0v-6 M22 8v8"/><path d="M10 15a2 2 0 0 1 4 0c0 1-2 1-2 2 M12 19h.01"/></svg>';
  const peopleStages = new WeakMap();
  const activePeopleStages = new Set();
  let peopleFrame = 0;
  function croppedAspect(imageData) {
    const crop = imageData.crop;
    return imageData.width / imageData.height
      * crop.width / crop.imageWidth * crop.imageHeight / crop.height;
  }
  function closePeoplePopover(data) {
    if (data.overlay.hasAttribute("popover")) {
      if (data.overlay.matches(":popover-open")) data.overlay.hidePopover();
      data.overlay.removeAttribute("popover");
    }
    data.overlay.classList.remove("is-external");
    data.figure.dataset.peoplePlacement = "numbered";
  }
  function roundedLeaderPath(x, y, endX, endY) {
    const horizontal = endX - x;
    const vertical = endY - y;
    if (!vertical) return `M${x} ${y}H${endX}`;
    const radius = Math.min(12, Math.abs(horizontal) / 2, Math.abs(vertical) / 2);
    const bendX = endX - Math.sign(horizontal) * radius;
    const bendY = y + Math.sign(vertical) * radius;
    return `M${x} ${y}H${bendX}Q${endX} ${y} ${endX} ${bendY}V${endY}`;
  }
  function positionPeople(stage) {
    const data = peopleStages.get(stage);
    if (!data) return;
    const bounds = stage.getBoundingClientRect();
    const modal = dialog.getBoundingClientRect();
    const labelWidth = 116;
    const gap = 16;
    const clearance = labelWidth + gap + 12;
    const external = dialog.open && !data.overlay.hidden && data.layout === "margins"
      && bounds.width && bounds.height && typeof data.overlay.showPopover === "function"
      && modal.left >= clearance && window.innerWidth - modal.right >= clearance;
    if (!external) {
      closePeoplePopover(data);
      return;
    }
    data.figure.dataset.peoplePlacement = "external";
    data.overlay.classList.add("is-external");
    data.overlay.setAttribute("popover", "manual");
    if (!data.overlay.matches(":popover-open")) data.overlay.showPopover();
    data.svg.setAttribute("viewBox", `0 0 ${data.overlay.clientWidth} ${data.overlay.clientHeight}`);
    const source = stage.closest(".document-full-source").getBoundingClientRect();
    const labels = [];
    data.items.forEach(({ person, bubble, leader, dot }) => {
      const x = bounds.left + person.x * bounds.width;
      const y = bounds.top + person.y * bounds.height;
      const visible = x >= Math.max(source.left, modal.left) && x <= Math.min(source.right, modal.right)
        && y >= Math.max(source.top, modal.top) && y <= Math.min(source.bottom, modal.bottom);
      bubble.hidden = !visible;
      leader.style.display = visible ? "" : "none";
      dot.style.display = visible ? "" : "none";
      if (!visible) return;
      const height = bubble.getBoundingClientRect().height;
      const top = Math.max(12, Math.min(y - height / 2, window.innerHeight - height - 12));
      bubble.style.left = `${person.side === "left" ? modal.left - gap - labelWidth : modal.right + gap}px`;
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      labels.push({
        side: person.side, bubble, leader, x, y,
        endX: person.side === "left" ? modal.left - gap : modal.right + gap,
        height, top,
      });
    });
    for (const side of ["left", "right"]) {
      const column = labels.filter((label) => label.side === side).sort((a, b) => a.y - b.y);
      if (column.reduce((total, label) => total + label.height, 0)
        + Math.max(0, column.length - 1) * 8 > window.innerHeight - 24) {
        closePeoplePopover(data);
        return;
      }
      let bottom = 4;
      for (const label of column) {
        label.top = Math.max(label.top, bottom + 8);
        bottom = label.top + label.height;
      }
      let ceiling = window.innerHeight - 12;
      for (let index = column.length - 1; index >= 0; index--) {
        const label = column[index];
        label.top = Math.min(label.top, ceiling - label.height);
        label.bubble.style.top = `${label.top}px`;
        label.leader.setAttribute("d", roundedLeaderPath(
          label.x, label.y, label.endX, label.top + label.height / 2,
        ));
        ceiling = label.top - 8;
      }
    }
  }
  const peopleObserver = new ResizeObserver((entries) => {
    entries.forEach(({ target }) => positionPeople(target));
  });
  function schedulePeoplePosition() {
    if (peopleFrame || !activePeopleStages.size) return;
    peopleFrame = requestAnimationFrame(() => {
      peopleFrame = 0;
      activePeopleStages.forEach(positionPeople);
    });
  }
  function resetPeopleStages() {
    activePeopleStages.forEach((stage) => closePeoplePopover(peopleStages.get(stage)));
    activePeopleStages.clear();
    peopleObserver.disconnect();
    cancelAnimationFrame(peopleFrame);
    peopleFrame = 0;
  }
  window.addEventListener("resize", schedulePeoplePosition);
  dialog.addEventListener("scroll", schedulePeoplePosition, { passive: true, capture: true });
  function annotatePhoto(figure, imageData, identity) {
    const data = imageData.annotations;
    figure.classList.add("document-person-figure");
    figure.dataset.peopleLayout = data.layout;
    const crop = imageData.crop;
    const width = crop ? imageData.width * crop.width / crop.imageWidth : imageData.width;
    figure.style.setProperty("--person-natural-width", `${width}px`);
    figure.style.setProperty("--person-aspect", crop ? croppedAspect(imageData) : imageData.width / imageData.height);
    const media = figure.firstElementChild;
    const stage = element("div", undefined, "document-person-stage");
    media.replaceWith(stage);
    stage.append(media);
    const overlay = element("div", undefined, "document-person-overlay");
    overlay.id = `people-${identity}`;
    overlay.hidden = true;
    const svg = window.document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("document-person-lines");
    svg.setAttribute("aria-hidden", "true");
    const details = element("div", undefined, "document-person-details");
    details.id = `${overlay.id}-details`;
    details.hidden = true;
    const names = element("ol", undefined, "document-person-names");
    names.setAttribute("aria-label", "Personajes identificados");
    const items = data.people.map((person, index) => {
      const line = window.document.createElementNS("http://www.w3.org/2000/svg", "line");
      const dot = window.document.createElementNS("http://www.w3.org/2000/svg", "circle");
      const leader = window.document.createElementNS("http://www.w3.org/2000/svg", "path");
      dot.setAttribute("r", "5");
      svg.append(leader, dot);
      const point = element("span", String(index + 1), "document-person-point");
      point.setAttribute("aria-hidden", "true");
      point.style.left = `${person.x * 100}%`;
      point.style.top = `${person.y * 100}%`;
      const bubble = element("span", undefined, "document-person-bubble");
      bubble.append(element("span", person.name, "document-person-label"),
        element("span", person.role, "document-person-role"));
      bubble.dataset.side = person.side;
      bubble.style.top = `${person.y * 100}%`;
      const item = element("li");
      item.append(element("span", person.name, "document-person-name"), ` · ${person.role} · ${person.position}`);
      names.append(item);
      overlay.append(point, bubble);
      return { person, bubble, leader, dot };
    });
    overlay.prepend(svg);
    stage.append(overlay);
    details.append(names);
    const toggle = element("button", "Revelar personajes", "document-person-toggle");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", `${overlay.id} ${details.id}`);
    toggle.addEventListener("click", () => {
      const reveal = toggle.getAttribute("aria-expanded") !== "true";
      overlay.hidden = details.hidden = !reveal;
      toggle.setAttribute("aria-expanded", String(reveal));
      toggle.textContent = reveal ? "Ocultar personajes" : "Revelar personajes";
      positionPeople(stage);
    });
    figure.prepend(toggle);
    figure.append(details);
    peopleStages.set(stage, { svg, items, overlay, figure, layout: data.layout });
    activePeopleStages.add(stage);
    peopleObserver.observe(stage);
  }
  savedButtons.forEach((button) => {
    const label = element("span");
    label.append(...button.childNodes);
    button.append(label);
    if (button.dataset.documentSaved === "all") return;
    const icon = element("span", undefined, "saved-tab-icon");
    icon.innerHTML = button.dataset.documentSaved === "favorite" ? star : cap;
    button.prepend(icon);
  });
  const isMarked = (record) => !!(marks[record.id]?.favorite || marks[record.id]?.review);
  function refreshMarks() {
    document.querySelectorAll("[data-document-mark]").forEach((button) => {
      const flag = button.dataset.documentMark;
      const active = !!marks[button.dataset.documentId]?.[flag];
      button.setAttribute("aria-pressed", String(active));
      button.title = flag === "favorite"
        ? (active ? "Quitar de favoritos" : "Añadir a favoritos")
        : (active ? "Ya repasado: quitar de repaso" : "Necesito repasar");
    });
    savedButtons.forEach((button) => {
      const filter = button.dataset.documentSaved;
      button.setAttribute("aria-pressed", String(filter === savedFilter));
      const counter = button.querySelector("[data-document-saved-count]");
      if (counter) counter.textContent = documents.filter((record) =>
        isMarked(record) && (filter === "all" || marks[record.id]?.[filter])).length;
    });
  }
  function attachMarks(parent, record) {
    const controls = element("div", undefined, "question-marks");
    controls.setAttribute("role", "group");
    controls.setAttribute("aria-label", `Marcas: ${record.title}`);
    for (const [flag, icon, label] of [
      ["favorite", star, "Favorito"], ["review", cap, "Necesito repasar"],
    ]) {
      const button = element("button", undefined, `question-mark-${flag}`);
      button.type = "button";
      button.dataset.documentMark = flag;
      button.dataset.documentId = record.id;
      button.setAttribute("aria-label", `${label}: ${record.title}`);
      button.innerHTML = icon;
      if (flag === "review") button.append(element("span", label));
      button.addEventListener("click", () => {
        try {
          // Merge against the latest durable value, never an old tab's snapshot.
          const next = readMarks();
          const old = next[record.id];
          const value = { favorite: !!old?.favorite, review: !!old?.review };
          value[flag] = !value[flag];
          Object.defineProperty(next, record.id, { value, enumerable: true, configurable: true, writable: true });
          if (!value.favorite && !value.review) delete next[record.id];
          localStorage.setItem(marksStorageKey, JSON.stringify(next));
          marks = next;
          if (value[flag]) window.pauMarkFeedback(button, flag);
          updateMarkedResults();
          reportStorage("marks", "");
        } catch {
          reportStorage("marks", "No se pudieron guardar las marcas del banco. No se han modificado los datos guardados.", true);
        }
      });
      controls.append(button);
    }
    parent.append(controls);
  }
  function updateMarkedResults() {
    if (loaded && (savedOnly || savedFilter !== "all")) render();
    refreshMarks();
  }
  savedButtons.forEach((button) => button.addEventListener("click", () => {
    savedFilter = button.dataset.documentSaved;
    render();
  }));
  window.addEventListener("storage", (event) => {
    if (event.key !== marksStorageKey && event.key !== null) return;
    try {
      marks = readMarks();
      updateMarkedResults();
      reportStorage("marks", "Marcas del banco actualizadas desde otra pestaña.");
    } catch {
      reportStorage("marks", "No se pudieron actualizar las marcas del banco. No se sobrescribirán datos inválidos.", true);
    }
  });
  function source(document, preview = false) {
    const box = element("div", undefined, preview ? "document-preview" : "document-full-source");
    let panControls;
    const cardImage = document.image || document.tableImage;
    if (preview && (document.tableImage || cardImage?.kind === "table")) {
      box.classList.add("document-preview-table");
    }
    const fullImages = [document.image, ...(document.image?.additionalImages || []), document.tableImage]
      .filter((image, index, images) => image && images.findIndex((candidate) => candidate?.src === image.src) === index);
    const visibleImages = preview ? [cardImage].filter(Boolean) : fullImages;
    const imageGroup = !preview && visibleImages.length > 1
      ? element("div", undefined, "document-image-pair") : null;
    visibleImages.forEach((imageData, imageIndex) => {
      const figure = element("figure", undefined, "document-image-figure");
      const mediaWidth = imageData.crop
        ? imageData.width * imageData.crop.width / imageData.crop.imageWidth : imageData.width;
      figure.style.setProperty("--document-media-width", `${mediaWidth}px`);
      const selectable = !preview && imageData.selectable;
      const image = element(selectable ? "object" : "img");
      image.style.setProperty("--document-image-width", `${imageData.width}px`);
      image.style.setProperty("--document-image-aspect", imageData.width / imageData.height);
      if (selectable) {
        image.data = imageData.src;
        image.type = "image/svg+xml";
        image.className = "document-selectable-map";
        image.setAttribute("aria-label", imageData.alt);
        image.style.setProperty("--document-image-ratio", `${imageData.width} / ${imageData.height}`);
        image.append(sourceLink("Abrir mapa con texto seleccionable", imageData.src));
      } else {
        image.src = imageData.src;
        image.alt = imageData.alt;
        image.loading = preview ? "lazy" : "eager";
        if (imageData.filter) image.style.filter = imageData.filter;
      }
      image.width = imageData.width;
      image.height = imageData.height;
      image.addEventListener("error", () => {
        image.hidden = true;
        box.append(element("p", "No se pudo cargar la imagen. Consulta la recopilación enlazada en las apariciones.", "document-quality"));
      }, { once: true });
      if (imageData.crop) {
        const crop = imageData.crop;
        const frame = element("span", undefined, "doc-image-crop");
        frame.style.setProperty("--doc-frame-width", `${imageData.width * crop.width / crop.imageWidth}px`);
        frame.style.setProperty("--doc-frame-ratio", croppedAspect(imageData));
        frame.style.setProperty("--document-crop-aspect", croppedAspect(imageData));
        frame.style.setProperty("--doc-img-width", `${100 * crop.imageWidth / crop.width}%`);
        frame.style.setProperty("--doc-img-height", `${100 * crop.imageHeight / crop.height}%`);
        frame.style.setProperty("--doc-img-left", `${100 * crop.left / crop.width}%`);
        frame.style.setProperty("--doc-img-top", `${100 * crop.top / crop.height}%`);
        frame.append(image);
        figure.append(frame);
      } else {
        figure.append(image);
      }
      if (!preview && imageData.reproductionNote) {
        figure.append(element("p", imageData.reproductionNote, "document-reproduction-note"));
      }
      if (!preview) {
        const caption = imageData.examCaption || document.examCaption;
        const foot = element("figcaption", undefined, "document-exam-caption");
        foot.append(sourceParagraph(caption?.text || "(Sin descripción)", caption?.emphasis));
        figure.append(foot);
      }
      if (!preview && imageData.annotations) {
        annotatePhoto(figure, imageData, imageIndex ? `${document.id}-${imageIndex}` : document.id);
      }
      if (!preview && imageData.attribution) {
        const attribution = imageData.attribution;
        const credit = element("p", undefined, "document-image-caption");
        credit.append(link(attribution.text, attribution.url), " · ", link(attribution.license, attribution.licenseUrl));
        figure.append(credit);
      }
      if (!preview && imageData.sourceUrl) {
        const attribution = sourceLink("Fuente de esta reproducción", imageData.sourceUrl);
        attribution.className = "document-image-caption";
        figure.append(attribution);
      }
      if (!preview && imageData.originalSrc) {
        const original = sourceLink("Ver recorte del PDF original", imageData.originalSrc);
        original.className = "document-image-caption document-original-link";
        figure.append(original);
      }
      if (!preview && imageData.corpusSrc) {
        const corpus = sourceLink(imageData.corpusLabel || "Ver imagen de la recopilación (leyenda distinta)", imageData.corpusSrc);
        corpus.className = "document-image-caption document-corpus-link";
        figure.append(corpus);
      }
      (imageGroup || box).append(figure);
    });
    if (imageGroup) box.append(imageGroup);
    if (visibleImages.length && !preview) {
      panControls = element("label", undefined, "document-pan-controls");
      panControls.hidden = true;
      const pan = element("input", undefined, "document-pan-range");
      pan.type = "range";
      pan.min = "0";
      pan.max = "0";
      pan.step = "1";
      pan.value = "0";
      panControls.append(element("span", "Desplazar imagen ampliada"), pan);
      const updatePan = () => {
        const maximum = Math.max(0, box.scrollWidth - box.clientWidth);
        panControls.hidden = !box.classList.contains("is-zoomed") || maximum <= 1;
        pan.max = String(maximum);
        pan.value = String(Math.round(box.scrollLeft));
        pan.setAttribute("aria-valuetext", `${maximum ? Math.round(box.scrollLeft / maximum * 100) : 0} %`);
      };
      pan.addEventListener("input", () => { box.scrollLeft = Number(pan.value); });
      box.addEventListener("scroll", updatePan, { passive: true });
      box.querySelectorAll("img,object").forEach((image) => image.addEventListener("load", updatePan));
      imagePanUpdates.set(box, updatePan);
      imagePanObserver?.observe(box);
      const zoom = element("button", "Ampliar imagen", "document-zoom");
      zoom.type = "button";
      zoom.setAttribute("aria-pressed", "false");
      zoom.addEventListener("click", () => {
        const expanded = box.classList.toggle("is-zoomed");
        zoom.setAttribute("aria-pressed", String(expanded));
        zoom.textContent = expanded ? "Ajustar a la pantalla" : "Ampliar imagen";
        box.scrollLeft = expanded ? (box.scrollWidth - box.clientWidth) / 2 : 0;
        updatePan();
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
      zoom.addEventListener("click", () => open(document, zoom));
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
      const attributionStart = document.text.length - (document.attributionParagraphs || 0);
      (preview ? document.text.slice(0, 3) : document.text).forEach((paragraph, index) => {
        const emphasis = index === document.text.length - 1 ? document.attributionEmphasis : undefined;
        quote.append(sourceParagraph(paragraph, emphasis, index >= attributionStart ? "document-attribution" : undefined));
      });
      box.append(quote);
      if (preview) {
        const more = element("span", "… ", "document-read-more");
        more.setAttribute("aria-hidden", "true");
        more.append(element("span", "Leer más"));
        box.append(more);
      }
    }
    if (panControls) {
      const shell = element("div", undefined, "document-source-shell");
      shell.append(panControls, box);
      return shell;
    }
    return box;
  }
  function open(document, button) {
    pagePosition = { left: window.scrollX, top: window.scrollY };
    opener = button;
    selectedId = document.id;
    resetPeopleStages();
    imagePanObserver?.disconnect();
    content.replaceChildren();
    content.append(element("p", `${typeNames[document.type]} · Bloque ${document.blocks.join(" · ")}`, "document-kind"));
    const title = element("h2", document.title);
    title.id = "document-dialog-title";
    content.append(title);
    attachMarks(content, document);
    content.append(element("p", document.date, "document-meta"), appearanceBadges(document), source(document));
    const guide = element("details", undefined, "document-guide");
    guide.append(element("summary", "Claves para responder a) y b)"));
    guide.append(element("p", "Orientación didáctica propia; no es una solución oficial.", "document-meta"));
    document.commentary.forEach((section) => guide.append(element("h3", section.title), element("p", section.text)));
    const task = element("section", undefined, "document-task");
    task.setAttribute("aria-label", "Enunciado de PAU · 4 puntos");
    task.append(element("h3", "Enunciado de PAU · 4 puntos"));
    task.append(element("p", "a) Analice el hecho histórico a que hace referencia el documento elegido."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    task.append(element("p", "b) Explique el contexto histórico y las consecuencias de este acontecimiento."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    const guidance = document.type === "texto"
      ? "En textos, a) permite desarrollar naturaleza, ideas principales y secundarias y contexto inmediato; b) explica el proceso general, sus causas y consecuencias. La extensión puede estar más equilibrada."
      : "En imágenes y gráficos, a) es más breve y descriptivo: identifica los elementos y sitúalos en su contexto inmediato. Dedica mayor desarrollo a b): evolución general del momento, causas y consecuencias relacionadas con el documento.";
    task.append(element("p", `${guidance} Pauta docente: a) no debería superar media carilla. No es un límite oficial añadido al examen ni cambia la puntuación: ambos apartados valen lo mismo.`, "document-meta"));
    content.append(task, guide);
    const sourceAppearance = document.examCaption
      ? document.appearances.find((appearance) => appearance.id === document.examCaption.appearanceId)
      : document.appearances[0];
    const collectionLink = sourceLink("Ver en la recopilación", sourceAppearance.sourceUrl);
    collectionLink.className = "document-collection-link";
    const footer = element("p");
    footer.append(collectionLink);
    content.append(footer);
    document.blocks.forEach((number) => content.append(link(`Ir a los apuntes del bloque ${number} →`, `apuntes/bloque-${number}.html`)));
    dialog.showModal();
    dialog.scrollTop = 0;
    updateReaderCue();
    refreshMarks();
    saveView();
  }
  dialog.querySelector(".document-close").addEventListener("click", () => dialog.close());
  let backdropPressed = null;
  const outsideDialog = (event) => {
    const bounds = dialog.getBoundingClientRect();
    return event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
  };
  const trackBackdropPress = (event) => {
    backdropPressed = event.target === dialog && outsideDialog(event);
  };
  dialog.addEventListener("pointerdown", trackBackdropPress);
  dialog.addEventListener("mousedown", trackBackdropPress);
  dialog.addEventListener("pointercancel", () => { backdropPressed = false; });
  dialog.addEventListener("click", (event) => {
    // Click-only input can close; a drag that started inside must not.
    const closeFromBackdrop = backdropPressed !== false && event.target === dialog && outsideDialog(event);
    backdropPressed = null;
    if (closeFromBackdrop) dialog.close();
  });
  dialog.addEventListener("close", () => {
    backdropPressed = null;
    resetPeopleStages();
    imagePanObserver?.disconnect();
    updateReaderCue();
    (opener?.isConnected ? opener : savedButtons.find((button) =>
      button.dataset.documentSaved === savedFilter))?.focus({ preventScroll: true });
    if (pagePosition) {
      scrollPage(pagePosition);
      pagePosition = null;
    }
    selectedId = null;
    saveView();
  });
  const baseMatches = (document) => {
    const haystack = normalize([document.title, document.date, document.sourceCaption, ...document.tags,
      ...document.appearances.map((appearance) => `${appearance.year} ${appearance.exam}`)].join(" "));
    return (type === "all" || document.type === type)
      && (!savedOnly || isMarked(document))
      && (savedFilter === "all" || !!marks[document.id]?.[savedFilter])
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
    const focused = document.activeElement;
    const oldCard = focused.closest(".document-card");
    const oldCards = [...grid.querySelectorAll(".document-card")];
    const oldIndex = oldCards.indexOf(oldCard);
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
        body.append(appearanceBadges(document));
        body.append(element("p", document.tags.join(" · "), "document-card-topics"));
        const button = element("button", document.type === "texto" ? "Leer texto completo y practicar →" : "Ver documento y practicar →", "document-open");
        button.type = "button";
        button.setAttribute("aria-label", `Ver documento: ${document.title}`);
        button.addEventListener("click", () => open(document, button));
        body.append(button);
        attachMarks(body, document);
        card.append(body);
        cards.append(card);
      }
      section.append(heading, cards);
      grid.append(section);
    }
    refreshMarks();
    const cards = [...grid.querySelectorAll(".document-card")];
    if (opener && !opener.isConnected) {
      const card = cards.find((node) => node.dataset.id === selectedId);
      opener = card?.querySelector(opener.matches(".document-preview-zoom") ? ".document-preview-zoom" : ".document-open") || null;
    }
    if (oldCard && !dialog.open) {
      const card = cards.find((node) => node.dataset.id === oldCard.dataset.id)
        || cards[Math.min(oldIndex, cards.length - 1)];
      const selector = focused.dataset.documentMark
        ? `[data-document-mark="${focused.dataset.documentMark}"]`
        : focused.matches(".document-preview-zoom") ? ".document-preview-zoom" : ".document-open";
      (card?.querySelector(selector) || savedButtons.find((button) =>
        button.dataset.documentSaved === savedFilter))?.focus({ preventScroll: true });
    }
    saveView();
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
    savedFilter = "all";
    topicSort.value = "alphabetical";
    render();
  });
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(resolve));
  async function restoreView() {
    const saved = restoredView;
    if (!saved) { restoring = false; saveView(); return; }
    const record = saved.dialog && documents.find((item) =>
      item.id === saved.dialog.id && (!savedOnly || isMarked(item)));
    if (record) {
      const card = [...grid.querySelectorAll(".document-card")].find((node) => node.dataset.id === record.id);
      open(record, card?.querySelector(saved.dialog.opener === "zoom" ? ".document-preview-zoom" : ".document-open"));
      content.querySelectorAll("details").forEach((node, index) => {
        node.open = saved.dialog.details[index] || false;
      });
      const box = content.querySelector(".document-full-source");
      box?.classList.toggle("is-zoomed", saved.dialog.zoom);
      const zoom = box?.querySelector(".document-zoom");
      if (zoom) {
        zoom.setAttribute("aria-pressed", String(saved.dialog.zoom));
        zoom.textContent = saved.dialog.zoom ? "Ajustar a la pantalla" : "Ampliar imagen";
      }
    }
    const applyPositions = () => {
      scrollPage(saved.page);
      if (record && dialog.open) {
        pagePosition = { ...saved.page };
        content.querySelector(".document-full-source")?.scrollTo({ ...saved.dialog.source, behavior: "auto" });
        dialog.scrollTo({ ...saved.dialog.position, behavior: "auto" });
      }
    };
    applyPositions();
    // Keep the valid snapshot untouched until fonts and the full source settle.
    // Lazy card images have fixed preview heights and need not be downloaded.
    const media = [...content.querySelectorAll("img, object")].map((node) => {
      if (node.tagName === "IMG") return node.decode().catch(() => {});
      return new Promise((resolve) => {
        try { if (node.contentDocument?.readyState === "complete") return resolve(); } catch {}
        node.addEventListener("load", resolve, { once: true });
        node.addEventListener("error", resolve, { once: true });
      });
    });
    let interrupted = false;
    let finishInteraction;
    const interaction = new Promise((resolve) => { finishInteraction = resolve; });
    const interrupt = (event) => {
      if (!event.isTrusted) return;
      if (event.type === "keydown" && !["Escape", "Tab", "ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "].includes(event.key)) return;
      interrupted = true;
      restoring = false;
      document.documentElement.removeAttribute("data-document-restoring");
      finishInteraction();
    };
    for (const name of ["pointerdown", "wheel", "touchstart", "keydown"]) {
      window.addEventListener(name, interrupt, { passive: true, capture: true });
    }
    await Promise.race([
      Promise.all([document.fonts.ready, ...media]),
      interaction,
    ]);
    await nextFrame();
    fitTopics();
    await nextFrame();
    if (!interrupted) applyPositions();
    await nextFrame();
    for (const name of ["pointerdown", "wheel", "touchstart", "keydown"]) {
      window.removeEventListener(name, interrupt, true);
    }
    restoring = false;
    restoredView = null;
    updateReaderCue();
    saveView();
  }
  async function load() {
    grid.setAttribute("aria-busy", "true");
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
      const scope = document.querySelector("#document-scope");
      if (scope) {
        scope.textContent =
          `${data.documents.length} fichas · ${coverage.sourceDocumentOccurrences} apariciones documentales · `
          + `${coverage.sourceImageOccurrences} apariciones de imágenes. ${coverage.formatNote} `
          + "El recuento refleja solo la exportación disponible; las transcripciones y la cobertura deben cotejarse con los PDF oficiales.";
      }
      documents = data.documents;
      const requestedBlock = new URLSearchParams(location.search).get("bloque");
      if (restoredView) {
        setType(restoredView.type);
        savedFilter = restoredView.savedFilter;
        block.value = restoredView.block;
        search.value = restoredView.search;
        topic = restoredView.topic;
        topicSearch.value = restoredView.topicSearch;
        topicSort.value = restoredView.sort;
        topicsExpanded = restoredView.expanded;
      } else if (requestedBlock && block.querySelector(`option[value="${Number(requestedBlock)}"]`)) block.value = requestedBlock;
      loaded = true;
      render();
      await restoreView();
      grid.setAttribute("aria-busy", "false");
    } catch (failure) {
      grid.setAttribute("aria-busy", "false");
      count.textContent = "Banco no disponible";
      error.textContent = `No se pudo cargar el banco de documentos (${failure.message}). Puedes reintentarlo o consultar la recopilación al final de la página.`;
      error.hidden = false;
      retry.hidden = false;
      console.error("No se pudo cargar el banco de documentos:", failure);
    } finally {
      document.documentElement.removeAttribute("data-document-restoring");
      if (dialog.open && document.activeElement === document.body) {
        dialog.querySelector(".document-close").focus({ preventScroll: true });
      }
    }
  }
  retry.addEventListener("click", load);
  load();
})();
