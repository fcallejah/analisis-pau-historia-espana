(() => {
  const search = document.querySelector("#document-search");
  const topicSearch = document.querySelector("#document-topic-search");
  const block = document.querySelector("#document-block");
  const examYear = document.querySelector("#document-year");
  const exam = document.querySelector("#document-exam");
  const examHint = document.querySelector("#document-exam-hint");
  const topics = document.querySelector("#document-topics");
  const topicSort = document.querySelector("#document-topic-sort");
  const topicToggle = document.querySelector("#document-topic-toggle");
  const topicEmpty = document.querySelector("#document-topic-empty");
  const unitSelect = document.querySelector("#document-unit");
  const frequencySort = document.querySelector("#document-frequency-sort");
  const moreFilters = document.querySelector(".document-more-filters");
  const activeFilters = document.querySelector("#document-active-filters");
  const searchOutside = document.createElement("p");
  const searchOutsideText = document.createElement("span");
  const searchOutsideButton = document.createElement("button");
  searchOutside.className = "document-search-outside";
  searchOutside.hidden = true;
  searchOutsideButton.type = "button";
  searchOutsideButton.textContent = "Buscar en todo el banco";
  searchOutside.append(searchOutsideText, " ", searchOutsideButton);
  activeFilters.after(searchOutside);
  const reset = document.querySelector("#document-reset");
  const grid = document.querySelector("#document-grid");
  const count = document.querySelector("#document-count");
  const error = document.querySelector("#document-error");
  const retry = document.querySelector("#document-retry");
  const dialog = document.querySelector("#document-dialog");
  const content = document.querySelector("#document-dialog-content");
  const previousDocument = dialog.querySelector(".document-previous");
  const nextDocument = dialog.querySelector(".document-next");
  const shareDocumentButton = dialog.querySelector(".document-share");
  const shareStatus = dialog.querySelector(".document-share-status");
  const cardShareStatus = document.createElement("p");
  cardShareStatus.className = "document-share-status";
  cardShareStatus.setAttribute("role", "status");
  cardShareStatus.setAttribute("aria-live", "polite");
  cardShareStatus.setAttribute("aria-atomic", "true");
  cardShareStatus.hidden = true;
  document.body.append(cardShareStatus);
  const readerStatus = dialog.querySelector(".document-reader-status");
  const typeButtons = [...document.querySelectorAll("[data-type]")];
  const savedButtons = [...document.querySelectorAll("[data-document-saved]")];
  const savedOnly = document.body.dataset.documentLibrary === "saved";
  const typeStorageKey = savedOnly ? "pau-he.documents.saved-type" : "pau-he.document-type";
  const viewStorageKey = savedOnly ? "pau-he.documents.saved-view.v1" : "pau-he.documents.view.v1";
  const filtersStorageKey = savedOnly ? "pau-he.documents.saved-filters.v1" : "pau-he.documents.filters.v1";
  const marksStorageKey = "pau-he.documents.marks.v1";
  const typeNames = { texto: "Texto", imagen: "Imagen", grafico: "Mapas y gráficos" };
  function syncPageZoom() {
    document.documentElement.toggleAttribute("data-page-zoomed", (window.visualViewport?.scale || 1) > 1.01);
    schedulePeoplePosition();
  }
  window.visualViewport?.addEventListener("resize", syncPageZoom);
  let documents = [];
  let thematicUnits = [];
  let selectedUnit = "";
  let frequencyOrder = false;
  let officialExams = new Map();
  let historicalVisible = false;
  const searchIndex = new Map();
  let type = "all";
  let savedFilter = "all";
  let marks = {};
  let viewWritable = true;
  let filtersWritable = true;
  let loaded = false;
  let restoring = true;
  let selectedId = null;
  let routePushedForDialog = false;
  let routeChangeFromHistory = false;
  let shareStatusTimer = 0;
  let activeShareStatus = shareStatus;
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
  const sameViewUrl = (url) => url.split("#")[0] === location.href.split("#")[0];
  const documentRouteId = () => new URLSearchParams(location.hash.slice(1)).get("documento");
  const shareableDocumentUrl = (id) => {
    const url = new URL("documentos.html", location.href);
    url.hash = `documento=${encodeURIComponent(id)}`;
    return url.href;
  };
  function setDocumentRoute(id, mode) {
    const url = new URL(location.href);
    url.hash = `documento=${encodeURIComponent(id)}`;
    if (mode === "push") {
      history.pushState(history.state, "", url);
      routePushedForDialog = true;
    } else {
      history.replaceState(history.state, "", url);
    }
  }
  function clearDocumentRoute() {
    if (!documentRouteId()) return;
    const url = new URL(location.href);
    url.hash = "";
    history.replaceState(history.state, "", url);
  }
  function compatibleView(value) {
    if (!value || value.version !== 1) return value;
    // Earlier v1 snapshots predate saved filters and opener tracking.
    return {
      ...value,
      type: value.type === "propio" ? "grafico" : value.type,
      year: value.year === undefined ? "" : value.year,
      exam: value.exam === undefined ? "" : value.exam,
      savedFilter: value.savedFilter === undefined ? "all" : value.savedFilter,
      historicalVisible: value.historicalVisible === undefined ? false : value.historicalVisible,
      unit: value.unit === undefined ? "" : value.unit,
      frequencyOrder: value.frequencyOrder === undefined ? false : value.frequencyOrder,
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
      && ["", "4", "5", "6", "7", "8", "9", "10", "11", "12"].includes(value.block)
      && (value.year === "" || typeof value.year === "string" && /^\d{4}$/.test(value.year)
        && Number(value.year) >= 2001 && Number(value.year) <= 2027)
      && typeof value.exam === "string" && (value.year !== "" || value.exam === "")
      && typeof value.search === "string" && typeof value.topic === "string"
      && typeof value.topicSearch === "string" && typeof value.expanded === "boolean"
      && typeof value.historicalVisible === "boolean"
      && typeof value.unit === "string" && typeof value.frequencyOrder === "boolean"
      && ["alphabetical", "frequency", "chronology"].includes(value.sort)
      && positionValid(value.page)
      && (value.dialog === null || (value.dialog && typeof value.dialog.id === "string"
        && ["open", "zoom"].includes(value.dialog.opener)
        && positionValid(value.dialog.position) && positionValid(value.dialog.source)
        && Array.isArray(value.dialog.details)
        && value.dialog.details.every((open) => typeof open === "boolean")
        && (value.dialog.selectionsGrouped === undefined || typeof value.dialog.selectionsGrouped === "boolean")));
  }
  try {
    const raw = sessionStorage.getItem(viewStorageKey);
    if (raw !== null) {
      const value = compatibleView(JSON.parse(raw));
      if (!validView(value)) throw new Error("Formato de vista no válido");
      if (sameViewUrl(value.url)) restoredView = value;
    }
    const savedType = sessionStorage.getItem(typeStorageKey);
    if (["all", "texto", "imagen", "grafico", "propio"].includes(savedType)) {
      type = savedType === "propio" ? "grafico" : savedType;
    }
  } catch (error) {
    viewWritable = false;
    console.warn("No se pudo recuperar la posición de lectura guardada:", error);
  }
  try {
    const raw = localStorage.getItem(filtersStorageKey);
    if (raw !== null) {
      const value = compatibleView(JSON.parse(raw));
      if (!validView(value)) throw new Error("Formato de filtros no válido");
      if (!restoredView && sameViewUrl(value.url)) {
        restoredView = { ...value, page: { left: 0, top: 0 }, dialog: null };
      }
    }
  } catch (error) {
    filtersWritable = false;
    console.warn("No se pudieron recuperar los filtros guardados:", error);
  }
  let initialDocumentId = documentRouteId();
  if (initialDocumentId && restoredView?.dialog) restoredView = { ...restoredView, dialog: null };
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
    if (!loaded || restoring) return;
    const box = content.querySelector(".document-full-source");
    const position = (node) => ({ left: node?.scrollLeft || 0, top: node?.scrollTop || 0 });
    const value = {
      version: 1, url: location.href, type, savedFilter, block: block.value,
      year: examYear.value, exam: exam.value,
      search: search.value, topic, topicSearch: topicSearch.value, sort: topicSort.value,
      expanded: topicsExpanded,
      historicalVisible,
      unit: selectedUnit, frequencyOrder,
      page: dialog.open && pagePosition ? pagePosition : { left: scrollX, top: scrollY },
      dialog: dialog.open ? {
        id: selectedId, opener: opener?.matches(".document-preview-zoom") ? "zoom" : "open",
        position: position(dialog), source: position(box),
        details: [...content.querySelectorAll("details")].map((node) => node.open),
        selectionsGrouped: true,
      } : null,
    };
    if (viewWritable) {
      try {
        const current = sessionStorage.getItem(viewStorageKey);
        if (current !== null && !validView(compatibleView(JSON.parse(current)))) throw new Error("Formato de vista no válido");
        sessionStorage.setItem(viewStorageKey, JSON.stringify(value));
        sessionStorage.setItem(typeStorageKey, type);
      } catch (error) {
        console.warn("No se pudo guardar la posición de lectura:", error);
      }
    }
    if (filtersWritable) {
      try {
        const current = localStorage.getItem(filtersStorageKey);
        if (current !== null && !validView(compatibleView(JSON.parse(current)))) throw new Error("Formato de filtros no válido");
        const filters = JSON.stringify({ ...value, page: { left: 0, top: 0 }, dialog: null });
        if (current !== filters) localStorage.setItem(filtersStorageKey, filters);
      } catch (error) {
        console.warn("No se pudieron guardar los filtros:", error);
      }
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
  // Search ignores accents, case and inner punctuation: 28-F = 28F, U.C.D. = UCD, 2.ª = 2a, 52.77 = 52,77.
  const compact = (value) => String(value).normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es")
    .replace(/(\p{N})[.,](?=\p{N})/gu, "$1")
    .replace(/([\p{L}\p{N}])[-\u2010-\u2015.·'’/](?=[\p{L}\p{N}])/gu, "$1");
  const searchAliases = [["28 de febrero", "28f"], ["23 de febrero", "23f"]];
  const hasTerm = (text, term) => new RegExp(`(?:^|[^\\p{L}\\p{N}])${term}(?![\\p{L}\\p{N}])`, "u").test(text);
  const indexText = (value) => {
    const text = compact(value);
    const aliases = searchAliases.filter((pair) => pair.some((term) => hasTerm(text, term))).flat();
    return `${normalize(value)} ${text} ${aliases.join(" ")}`;
  };
  const searchTerms = (value) => compact(value).split(/\s+/)
    .map((term) => term.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "")).filter(Boolean);
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
  const sourceText = (tag, text, emphasis = [], className) => {
    const node = element(tag, undefined, className);
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
  const sourceParagraph = (text, emphasis, className) => sourceText("p", text, emphasis, className);
  const examName = (appearance) => appearance.exam.replace(new RegExp(`^${appearance.year}\\s+`), "");
  function displayExamName(name, year) {
    const numbered = year === 2011 && name.match(/^(Ordinaria|Extraordinaria) examen (\d+)$/i);
    if (numbered) return `Examen ${numbered[2]} ${normalize(numbered[1])}`;
    const reserve = year === 2010 && name.match(/^(Titular|Extraordinaria) reserva ([AB])$/i);
    if (!reserve) return name;
    return `Reserva ${reserve[2].toUpperCase()} ${normalize(reserve[1]) === "titular" ? "ordinaria" : "extraordinaria"}`;
  }
  function appearancePill(appearance, compact = false) {
    const exam = displayExamName(examName(appearance), appearance.year);
    const shortExam = exam.replace(/\s*\([^)]*\)\s*$/, "");
    const words = (value) => normalize(value).match(/[\p{L}\p{N}]+/gu)?.join(" ") || "";
    const displayRoute = displayExamName(appearance.route, appearance.year);
    const route = ` ${words(shortExam)} `.includes(` ${words(displayRoute)} `) ? "" : displayRoute;
    const pendingRoute = appearance.route.endsWith("sin cotejar");
    const documentLabel = appearance.document === null ? "" : `Documento ${appearance.document}`;
    const label = [
      appearance.year, compact ? shortExam : exam,
      pendingRoute ? "" : route, documentLabel,
    ].filter((part) => part !== "").join(" · ");
    const pill = element("span", label, "exam-pill");
    const modelPage = appearance.sourceReviewStatus === "orientation-model" ? `p. ${appearance.officialPage}` : "";
    pill.title = [appearance.year, exam, route, documentLabel, modelPage].filter(Boolean).join(" · ");
    return pill;
  }
  function appearanceBadges(record, appearances = record.appearances) {
    const list = element("ul", undefined, "document-exams");
    list.setAttribute("aria-label", record.origin === "propio" ? "Procedencia" : "Apariciones en exámenes");
    if (record.origin === "propio") {
      const item = element("li");
      item.append(element("span", "Elaboración propia · puede caer", "exam-pill"));
      list.append(item);
      return list;
    }
    appearances.forEach((appearance) => {
      const item = element("li");
      const pill = appearancePill(appearance, true);
      const localPdf = appearance.sourceReviewStatus === "user-scan";
      const pdfUrl = localPdf && appearance.officialPage
        ? `${appearance.pdfUrl}#page=${appearance.officialPage}` : appearance.pdfUrl;
      const anchor = link("", pdfUrl);
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      const location = localPdf ? "el archivo local" : "Drive";
      anchor.setAttribute("aria-label", `Abrir PDF del examen en ${location} (otra pestaña): ${pill.title}`);
      anchor.title = `Abrir el PDF de este examen en ${location} (otra pestaña)`;
      anchor.append(pill);
      item.append(anchor);
      list.append(item);
    });
    return list;
  }
  const examLabel = (appearance) => examName(appearance).replace(/\s*\([^)]*\)\s*$/, "").trim();
  const examKey = (appearance) => normalize(examLabel(appearance)).replace(/\s+/g, " ");
  function examPriority(key) {
    if (key === "titular ordinaria") return 0;
    if (key === "titular extraordinaria") return 1;
    if (key === "modelo orientaciones pau") return 2;
    // En 2010, «Titular reserva A» equivale a «Reserva A ordinaria» en el orden.
    const reserve = key.match(/^(?:(titular|extraordinaria) )?reserva ([ab])(?: (ordinaria|extraordinaria))?$/);
    if (reserve) return (reserve[1] === "extraordinaria" || reserve[3] === "extraordinaria" ? 5 : 3)
      + (reserve[2] === "b" ? 1 : 0);
    if (key.startsWith("ordinaria examen ") || key === "suplente ordinaria") return 7;
    return 8;
  }
  const matchesExam = (appearance) => (!examYear.value || appearance.year === Number(examYear.value))
    && (!exam.value || examKey(appearance) === exam.value);
  const matchingAppearances = (record) => record.appearances.filter(matchesExam);
  function updateExamOptions(selected = "") {
    const withoutDocumentExercise = Number(examYear.value) >= 2017 && Number(examYear.value) <= 2024;
    const availability = officialExams.get(Number(examYear.value));
    const options = new Map();
    if (examYear.value) {
      documents.flatMap((record) => record.appearances).filter((appearance) =>
        appearance.year === Number(examYear.value)).forEach((appearance) => {
        options.set(examKey(appearance), displayExamName(examLabel(appearance), appearance.year));
      });
    }
    const placeholder = element("option", !examYear.value ? "Elige un año"
      : withoutDocumentExercise ? "Sin comentario de documento"
      : options.size ? "Todos los exámenes" : "Sin exámenes incorporados");
    placeholder.value = "";
    exam.replaceChildren(placeholder);
    const numberedOrder = ["examen 1", "examen 2", "modelo orientaciones pau"];
    const hasNumberedModel = numberedOrder.every((key) => options.has(key));
    const priority = (key) => {
      const position = hasNumberedModel ? numberedOrder.indexOf(key) : -1;
      return position < 0 ? examPriority(key) : position - numberedOrder.length;
    };
    [...options].sort((a, b) => priority(a[0]) - priority(b[0])
      || a[1].localeCompare(b[1], "es", { numeric: true })).forEach(([key, label]) => {
      const option = element("option", label);
      option.value = key;
      exam.append(option);
    });
    (availability?.unavailableExams || []).forEach((label, index) => {
      const option = element("option", label);
      option.value = `unavailable-${index + 1}`;
      option.disabled = true;
      exam.append(option);
    });
    exam.disabled = !options.size;
    exam.value = options.has(selected) ? selected : "";
    if (selected && !options.has(selected)) console.warn("El examen guardado ya no está incorporado; se muestran todos los del año.");
    exam.classList.toggle("is-format-warning", withoutDocumentExercise);
    examHint.classList.toggle("is-format-warning", withoutDocumentExercise);
    if (withoutDocumentExercise) exam.title = placeholder.textContent;
    else exam.removeAttribute("title");
    examHint.textContent = withoutDocumentExercise
      ? "Entre 2017-2024, ambos inclusive, el formato PAU era solo de cuestiones cortas y tema; no faltan comentarios de documentos porque no cayó ninguno."
      : availability?.year === 2006 || availability?.year === 2027 ? availability.note : "";
    examHint.hidden = !examHint.textContent;
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
  function roundedLeaderPath(points) {
    const corners = points.filter((point, index) => !index
      || point[0] !== points[index - 1][0] || point[1] !== points[index - 1][1]);
    let path = `M${corners[0].join(" ")}`;
    for (let index = 1; index < corners.length - 1; index++) {
      const [x, y] = corners[index];
      const [px, py] = corners[index - 1];
      const [nx, ny] = corners[index + 1];
      const before = Math.hypot(px - x, py - y);
      const after = Math.hypot(nx - x, ny - y);
      const radius = Math.min(6, before / 2, after / 2);
      path += `L${x + (px - x) * radius / before} ${y + (py - y) * radius / before}`
        + `Q${x} ${y} ${x + (nx - x) * radius / after} ${y + (ny - y) * radius / after}`;
    }
    return `${path}L${corners.at(-1).join(" ")}`;
  }
  function positionPeople(stage) {
    const data = peopleStages.get(stage);
    if (!data || data.overlay.hidden) return;
    const bounds = stage.getBoundingClientRect();
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    if (!width || !height) return;
    data.svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    const caption = data.figure.querySelector(".document-exam-caption").getBoundingClientRect();
    const callouts = data.callouts.getBoundingClientRect();
    const routes = data.items.filter(item => !item.bubble.hidden).map((item) => {
      const box = item.bubble.getBoundingClientRect();
      const x = item.person.x * width;
      const y = item.person.y * height;
      const vertical = Math.min(y, height - y) <= Math.min(x, width - x);
      const left = vertical ? box.left + box.width / 2 < callouts.left + callouts.width / 2 : x < width / 2;
      return { ...item, box, x, y, vertical, left };
    });
    const counts = [routes.filter(route => route.left).length, routes.filter(route => !route.left).length];
    const tracks = [0, 0];
    routes.forEach(({ bubble, leader, dot, box, x, y, vertical, left }) => {
      const side = left ? 0 : 1;
      const rank = tracks[side]++;
      const margin = 6 + rank * Math.min(6, 12 / Math.max(1, counts[side] - 1));
      const rail = left ? Math.min(caption.left, callouts.left, bounds.left) - bounds.left - margin
        : Math.max(caption.right, callouts.right, bounds.right) - bounds.left + margin;
      const lane = box.top - bounds.top - (bubble.offsetLeft < data.callouts.clientWidth / 2 ? 8 : 16);
      const points = [[x, y]];
      if (vertical) {
        const exit = y <= height / 2 ? -margin : height + margin;
        points.push([x, exit], [rail, exit]);
      } else {
        points.push([rail, y]);
      }
      points.push([rail, lane], [box.left + box.width / 2 - bounds.left, lane],
        [box.left + box.width / 2 - bounds.left, box.top - bounds.top]);
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      leader.setAttribute("d", roundedLeaderPath(points));
    });
  }
  const peopleObserver = new ResizeObserver((entries) => {
    entries.forEach(({ target }) => positionPeople(
      peopleStages.has(target) ? target : target.querySelector(".document-person-stage"),
    ));
  });
  function schedulePeoplePosition() {
    if (peopleFrame || !activePeopleStages.size) return;
    peopleFrame = requestAnimationFrame(() => {
      peopleFrame = 0;
      activePeopleStages.forEach(positionPeople);
    });
  }
  function resetPeopleStages() {
    activePeopleStages.clear();
    peopleObserver.disconnect();
    cancelAnimationFrame(peopleFrame);
    peopleFrame = 0;
  }
  window.addEventListener("resize", schedulePeoplePosition);
  syncPageZoom();
  dialog.addEventListener("scroll", schedulePeoplePosition, { passive: true, capture: true });
  function annotatePhoto(figure, imageData, identity) {
    const data = imageData.annotations;
    const symbols = Boolean(data.symbols);
    const showLabel = symbols ? "Revelar símbolos" : "Revelar personajes";
    const hideLabel = symbols ? "Ocultar símbolos" : "Ocultar personajes";
    figure.classList.add("document-person-figure");
    figure.dataset.peopleLayout = data.layout;
    const crop = imageData.crop;
    const width = crop ? imageData.width * crop.width / crop.imageWidth : imageData.width;
    figure.style.setProperty("--person-natural-width", `${width}px`);
    figure.style.setProperty("--person-aspect", crop ? croppedAspect(imageData) : imageData.width / imageData.height);
    const media = figure.firstElementChild;
    const canvas = element("div", undefined, "document-person-canvas");
    const stage = element("div", undefined, "document-person-stage");
    media.replaceWith(canvas);
    canvas.append(stage);
    stage.append(media);
    const overlay = element("div", undefined, "document-person-overlay");
    overlay.id = `people-${identity}`;
    overlay.hidden = true;
    const callouts = element("div", undefined, "document-person-callouts");
    callouts.id = `${overlay.id}-callouts`;
    callouts.hidden = true;
    const svg = window.document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("document-person-lines");
    svg.setAttribute("aria-hidden", "true");
    const details = element("div", undefined, "document-person-details");
    details.id = `${overlay.id}-details`;
    details.hidden = true;
    const names = element("ul", undefined, "document-person-names");
    names.setAttribute("aria-label", symbols ? "Símbolos identificados" : "Personajes identificados");
    const subjects = symbols ? data.symbols : data.people;
    const byRow = !symbols && subjects.some(person => person.row);
    const staged = !symbols && subjects.some(person => person.primary);
    const rows = new Map();
    const items = subjects.map((person) => {
      const dot = window.document.createElementNS("http://www.w3.org/2000/svg", "circle");
      const leader = window.document.createElementNS("http://www.w3.org/2000/svg", "path");
      dot.setAttribute("r", "5");
      svg.append(leader, dot);
      const bubble = element("span", undefined, "document-person-bubble");
      const nameTag = person.region || person.emphasis === "strong" ? "strong"
        : person.emphasis === "em" ? "em" : "span";
      const label = (className) => {
        if (nameTag === "span") return element("span", person.name, className);
        const node = element("span", undefined, className);
        node.append(element(nameTag, person.name));
        if (byRow && nameTag === "strong") node.append("*");
        if (person.region) node.append(` (${person.region})`);
        return node;
      };
      bubble.append(label("document-person-label"),
        element("span", person.role, "document-person-role"));
      bubble.dataset.side = person.side;
      const item = element("li");
      item.append(label("document-person-name"));
      if (person.context) {
        const note = element("p", person.context.text);
        const citation = link("Fuente", person.context.url);
        citation.setAttribute("aria-label", `Fuente sobre ${person.name}`);
        note.append(" ", citation);
        if (person.context.biographyUrl) note.append(" · ", link("Biografía", person.context.biographyUrl));
        item.append(note);
      }
      if (!byRow) {
        names.append(item);
      } else {
        if (!rows.has(person.row)) {
          const row = element("li");
          const list = element("ul");
          row.append(element("strong", `Fila ${person.row}`), list);
          names.append(row);
          rows.set(person.row, list);
        }
        rows.get(person.row).append(item);
      }
      return { person, bubble, leader, dot };
    });
    const sorted = [...items].sort((a, b) => a.person.x - b.person.x);
    const middle = Math.ceil(sorted.length / 2);
    const ordered = sorted.slice(0, middle).flatMap((item, index) =>
      sorted[middle + index] ? [item, sorted[middle + index]] : [item]);
    const colors = ["#e53935", "#f08986", "#d6ee7a", "#48632b", "#4b2e83", "#9c7bc5",
      "#bc6e3f", "#84431f", "#287bb0", "#173e6f", "#259f98", "#125c54",
      "#bd5092", "#75235a", "#d5a227", "#856113"];
    ordered.forEach(({ bubble, leader, dot }, index) => {
      const color = colors[index] || `hsl(${index * 137.508 % 360} 58% ${index % 2 ? 40 : 62}%)`;
      [bubble, leader, dot].forEach(node => node.style.setProperty("--person-color", color));
      callouts.append(bubble);
    });
    overlay.prepend(svg);
    stage.append(overlay);
    figure.querySelector(".document-exam-caption").after(callouts);
    const context = !byRow && data.context ? element("div", undefined, "document-person-context-panel") : null;
    if (context) {
      context.id = `${overlay.id}-context`;
      context.hidden = true;
      context.append(element("h3", data.contextTitle || "Qué muestra la fotografía"),
        element("p", data.context, "document-person-context"));
      if (data.sources?.length) {
        const sources = element("ul");
        data.sources.forEach(({ title, url }) => {
          const item = element("li");
          item.append(link(title, url));
          sources.append(item);
        });
        context.append(sources);
      }
      callouts.after(context);
    }
    if (byRow) {
      const legend = element("p");
      legend.append("De izquierda a derecha: ",
        element("strong", "Directorio Militar"), " (* junto al nombre y, cuando corresponde, la región entre paréntesis) y ",
        element("em", "Cuadrilátero"), ".");
      details.append(legend);
      if (data.context) details.append(element("p", data.context, "document-person-context"));
      callouts.after(details);
    }
    details.append(names);
    const toggle = element("button", showLabel, "document-person-toggle");
    toggle.type = "button";
    toggle.setAttribute("aria-controls", [overlay.id, callouts.id, details.id, context?.id].filter(Boolean).join(" "));
    const more = staged ? element("button", undefined, "document-person-more") : null;
    if (more) {
      more.type = "button";
      more.setAttribute("aria-controls", toggle.getAttribute("aria-controls"));
    }
    let revealed = false;
    let expanded = false;
    function updateReveal() {
      overlay.hidden = callouts.hidden = !revealed;
      details.hidden = !revealed || (staged && !expanded);
      if (context) context.hidden = details.hidden;
      if (byRow) {
        details.classList.toggle("document-person-details-by-row", expanded);
      }
      toggle.setAttribute("aria-expanded", String(revealed));
      toggle.textContent = revealed ? hideLabel : showLabel;
      if (more) {
        more.hidden = !revealed;
        more.setAttribute("aria-expanded", String(expanded));
        more.textContent = expanded ? "Ocultar personajes adicionales" : "Revelar más personajes";
        items.forEach(({ person, bubble, leader, dot }) => {
          bubble.hidden = !person.primary && !expanded;
          leader.style.display = dot.style.display = bubble.hidden ? "none" : "";
        });
      }
      positionPeople(stage);
    }
    toggle.addEventListener("click", () => {
      revealed = !revealed;
      expanded = false;
      updateReveal();
    });
    if (!byRow) figure.prepend(details);
    figure.prepend(toggle);
    if (more) {
      toggle.after(more);
      more.addEventListener("click", () => {
        expanded = !expanded;
        updateReveal();
      });
    }
    peopleStages.set(stage, { svg, items, overlay, figure, callouts });
    updateReveal();
    activePeopleStages.add(stage);
    peopleObserver.observe(stage);
    peopleObserver.observe(figure);
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
  const memberIds = (record) => record.memberIds || [record.id];
  const hasMark = (record, flag, values = marks) => memberIds(record).some((id) => values[id]?.[flag]);
  const isMarked = (record) => hasMark(record, "favorite") || hasMark(record, "review");
  function refreshMarks() {
    document.querySelectorAll("[data-document-mark]").forEach((button) => {
      const flag = button.dataset.documentMark;
      const record = documents.find((item) => item.id === button.dataset.documentId);
      const active = record ? hasMark(record, flag) : false;
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
        isMarked(record) && (filter === "all" || hasMark(record, filter))).length;
    });
    if (dialog.open) updateReaderNavigation();
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
          const value = { favorite: hasMark(record, "favorite", next), review: hasMark(record, "review", next) };
          value[flag] = !value[flag];
          memberIds(record).forEach((id) => { delete next[id]; });
          Object.defineProperty(next, record.id, { value, enumerable: true, configurable: true, writable: true });
          if (!value.favorite && !value.review) delete next[record.id];
          localStorage.setItem(marksStorageKey, JSON.stringify(next));
          marks = next;
          updateMarkedResults();
          if (value[flag]) {
            const target = button.isConnected ? button
              : grid.querySelector(`[data-document-id="${CSS.escape(record.id)}"][data-document-mark="${flag}"]`);
            if (target) window.pauMarkFeedback(target, flag);
          }
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
  function filterFocusTarget() {
    const button = savedButtons.find((button) => button.dataset.documentSaved === savedFilter);
    return button?.closest("details:not([open])") ? moreFilters.querySelector("summary") : button;
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
  function textContentSize(record) {
    const end = record.text.length - (record.attributionParagraphs || 0);
    return record.text.filter((_, index) =>
      index < end && !record.headingParagraphs?.includes(index))
      .join(" ").match(/[\p{L}\p{N}]+/gu)?.length || 0;
  }
  function groupTexts(records, groups = []) {
    if (!Array.isArray(groups)) throw new Error("Las agrupaciones de textos no son válidas");
    const byId = new Map(records.map((record) => [record.id, record]));
    const grouped = new Map();
    const secondary = new Set();
    const assigned = new Set();
    for (const ids of groups) {
      if (!Array.isArray(ids) || ids.length < 2 || new Set(ids).size !== ids.length || ids.some((id) =>
        !byId.has(id) || byId.get(id).type !== "texto" || assigned.has(id))) {
        throw new Error("Una agrupación de textos contiene selecciones repetidas, ausentes o incompatibles");
      }
      const versions = ids.map((id) => byId.get(id));
      const ranked = [...versions].sort((a, b) => textContentSize(b) - textContentSize(a));
      const canonical = versions[0];
      if (canonical.primaryTextId !== undefined && !ids.includes(canonical.primaryTextId)) {
        throw new Error("La selección principal no pertenece a su agrupación de textos");
      }
      const primary = canonical.primaryTextId === undefined ? ranked[0] : byId.get(canonical.primaryTextId);
      grouped.set(canonical.id, {
        ...primary,
        id: canonical.id,
        studyCompilation: canonical.studyCompilation,
        titleMarker: canonical.titleMarker,
        historicalNote: canonical.historicalNote,
        memberIds: ids,
        textVersions: [primary, ...ranked.filter((version) => version !== primary)],
        tags: [...new Set(versions.flatMap((record) => record.tags))],
        blocks: [...new Set(versions.flatMap((record) => record.blocks))],
        appearances: versions.flatMap((record) => record.appearances)
          .sort((a, b) => a.year - b.year || a.exam.localeCompare(b.exam, "es")),
      });
      ids.forEach((id, index) => {
        assigned.add(id);
        if (index) secondary.add(id);
      });
    }
    return records.filter((record) => !secondary.has(record.id)).map((record) => grouped.get(record.id) || record);
  }
  function readThematicUnits(curriculum, records) {
    if (!curriculum || curriculum.academicYear !== "2026-27"
      || !Array.isArray(curriculum.units) || curriculum.units.length !== 25) {
      throw new Error("Las unidades temáticas de las orientaciones 2026–27 no son válidas");
    }
    const byId = new Map(records.map((record) => [record.id, record]));
    const ids = new Set();
    const assigned = new Set();
    for (const unit of curriculum.units) {
      if (!unit || !["II", "III"].includes(unit.group) || !Number.isInteger(unit.number)
        || unit.number < 1 || unit.number > (unit.group === "II" ? 12 : 13)
        || unit.id !== `${unit.group.toLowerCase()}-${unit.number}` || ids.has(unit.id)
        || !Number.isInteger(unit.block) || unit.block < (unit.group === "II" ? 5 : 9)
        || unit.block > (unit.group === "II" ? 8 : 12)
        || typeof unit.title !== "string" || !unit.title.trim()
        || !Array.isArray(unit.documentIds)) {
        throw new Error("Una unidad temática tiene un identificador, bloque o título incompatible");
      }
      if (new Set(unit.documentIds).size !== unit.documentIds.length
        || unit.documentIds.some((id) => !byId.has(id) || !byId.get(id).blocks.includes(unit.block))) {
        throw new Error("Una unidad temática contiene documentos repetidos, ausentes o de otro bloque");
      }
      ids.add(unit.id);
      unit.documentIds.forEach((id) => assigned.add(id));
    }
    if (records.some((record) => record.blocks.some((number) => number >= 5) && !assigned.has(record.id))) {
      throw new Error("Hay documentos de los bloques 5–12 sin clasificar en las unidades temáticas");
    }
    return curriculum.units;
  }
  function searchableText(record) {
    const images = [record.image, ...(record.image?.additionalImages || []), record.tableImage].filter(Boolean);
    return [
      record.title, record.date, record.sourceCaption, record.quality, record.readingNote, ...record.tags,
      record.historicalNote,
      ...(record.origin === "propio" ? ["material propio", "resultados"] : []),
      ...(record.origin === "propio" && ["elections", "municipal-turnout", "municipal-votes"].includes(record.visualization)
        ? ["electorales"] : []),
      ...(record.text || []),
      ...(record.studyCompilation?.text || []),
      ...record.commentary.flatMap((section) => [section.title, section.text]),
      ...record.appearances.flatMap((appearance) => [
        appearance.year, appearance.exam, appearance.route, displayExamName(examLabel(appearance), appearance.year),
      ]),
      ...images.flatMap((image) => [
        image.alt, image.reproductionNote, image.editorialNote, image.examCaption?.text, image.examCaption?.note, image.attribution?.text,
        image.annotations?.note,
        ...(image.annotations?.people || []).flatMap((person) => [person.name, person.role, person.position]),
        ...(image.annotations?.symbols || []).flatMap((symbol) => [symbol.name, symbol.role, symbol.position]),
      ]),
      record.examCaption?.text, record.examCaption?.note, record.table?.caption,
      ...(record.table?.headers || []), ...(record.table?.rows.flat() || []), ...(record.table?.notes || []),
      ...(record.tables || []).flatMap((table) => [table.caption, ...table.headers, ...table.rows.flat(), ...(table.notes || [])]),
      ...(record.questions || []),
      ...(record.textVersions || []).map(searchableText),
    ].join(" ");
  }
  function textQuote(record, preview = false) {
    const quote = element("blockquote");
    if (record.textLayout === "verse-pair") quote.classList.add("document-verse-pair");
    const outerQuotePairs = { "“": "”", "«": "»", "\"": "\"", "‘": "’", "'": "'" };
    const numbered = /^\s*[«“"']*\d+[ºª]?\)\s/u;
    const starts = [...new Set([
      ...(record.paragraphStarts || record.text.map((_, index) => index)),
      ...record.text.flatMap((line, index) => numbered.test(line) ? [index] : []),
    ])].sort((a, b) => a - b);
    const attributionStart = record.text.length - (record.attributionParagraphs || 0);
    const paragraphs = starts.flatMap((start, index) => {
      const end = starts[index + 1] ?? record.text.length;
      const paragraph = record.text.slice(start, end).join(" ");
      const parts = numbered.test(paragraph) ? paragraph.split(/\s+(?=\d+[ºª]?\)\s)/u) : [paragraph];
      return parts.map((text, part) => ({
        start,
        text,
        emphasis: record.headingParagraphs?.includes(start) ? record.headingEmphasis?.[start]
          : start >= attributionStart
            ? record.attributionEmphasis?.filter((phrase) => text.includes(phrase)) : undefined,
        className: start >= attributionStart ? "document-attribution"
          : record.headingParagraphs?.includes(start)
            ? `document-source-heading${record.centerHeadings !== false ? " is-centered" : ""}` : undefined,
      }));
    });
    const sourceParagraphs = paragraphs.filter((paragraph) => paragraph.start < attributionStart);
    const firstSourceParagraph = sourceParagraphs.find((paragraph) =>
      !record.headingParagraphs?.includes(paragraph.start) || /^\s*[“«"‘']/u.test(paragraph.text));
    if (firstSourceParagraph) {
      const opener = firstSourceParagraph.text.match(/^\s*([“«"‘'])/u)?.[1];
      if (opener) {
        firstSourceParagraph.text = firstSourceParagraph.text.replace(
            new RegExp(`^(\\s*)${opener.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`),
            "$1",
        );
        const closer = outerQuotePairs[opener];
        const terminalQuote = new RegExp(
            `${closer.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?=[\\s.!?,;:…)]*$)`,
        );
        const lastSourceParagraph = sourceParagraphs[sourceParagraphs.length - 1];
        if (lastSourceParagraph?.text.match(terminalQuote)) {
            lastSourceParagraph.text = lastSourceParagraph.text.replace(terminalQuote, "");
        } else {
            const lastParagraph = paragraphs[paragraphs.length - 1];
            if (lastParagraph && lastParagraph !== lastSourceParagraph) {
              lastParagraph.text = lastParagraph.text.replace(terminalQuote, "");
            }
        }
      }
    }
    (preview ? paragraphs.slice(0, 3) : paragraphs).forEach((paragraph) => {
      quote.append(sourceParagraph(paragraph.text, paragraph.emphasis, paragraph.className));
    });
    return quote;
  }
  function versionSources(record) {
    const sources = element("div", undefined, "document-variant-sources");
    const count = record.appearances.length;
    sources.append(element("p",
      `Esta selección: ${count} ${count === 1 ? "aparición" : "apariciones"}, ya ${count === 1 ? "incluida" : "incluidas"} en el total.`),
      appearanceBadges(record, record.appearances));
    return sources;
  }
  function textSelections(record) {
    const selections = new Map();
    for (const version of record.textVersions || [record]) {
      const key = JSON.stringify([
        version.text.join(" ").replace(/\s+/g, " ").trim(),
        version.appearances.some((appearance) => appearance.sourceReviewStatus === "transcription-copy"),
      ]);
      const existing = selections.get(key);
      if (existing) existing.appearances.push(...version.appearances);
      else selections.set(key, { ...version, appearances: [...version.appearances] });
    }
    return [...selections.values()];
  }
  function studyBar(label, value, maximum, variant = "") {
    const row = element("div", undefined, "study-chart-row");
    const name = element("span", label, "study-chart-label");
    const track = element("span", undefined, "study-chart-track");
    track.setAttribute("aria-hidden", "true");
    const fill = element("span", undefined, `study-chart-fill ${variant}`);
    fill.style.width = `${Math.max(0, Math.min(100, value / maximum * 100))}%`;
    track.append(fill);
    row.append(name, track, element("strong", String(value).replace(".", ","), "study-chart-value"));
    return row;
  }
  function nationalElectionYear(record) {
    if (record.id === "elecciones-1977-diagrama") return 1977;
    const match = /^propio-elecciones-generales-(\d{4})$/.exec(record.id);
    const year = match ? Number(match[1]) : 0;
    return year >= 1979 && year <= 2015 ? year : null;
  }
  function isNationalElectionRecord(record) {
    return nationalElectionYear(record) !== null;
  }
  function isRepublicElectionRecord(record) {
    return /^propio-elecciones-generales-193[136]$/.test(record.id);
  }
  function nationalElectionCharts() {
    return documents.flatMap((record) => {
      const year = nationalElectionYear(record);
      if (year === null) return [];
      if (year === 1977) {
        if (!record.table || !record.image?.src) {
          throw new Error("Faltan los datos del gráfico electoral de 1977");
        }
        return [{
          record,
          table: record.table,
          year,
          label: record.table.chart?.heading || record.table.caption,
          src: record.image.src,
        }];
      }
      return (record.tables || []).map((table) => {
        if (!table.chart?.svg) throw new Error(`Falta el gráfico electoral de ${year}`);
        return {
          record,
          table,
          year,
          label: table.chart.selectorLabel || table.chart.heading || table.caption,
          src: `assets/documentos/${table.chart.svg}`,
        };
      });
    }).sort((a, b) => a.year - b.year);
  }
  function electionChartEntry(record, table) {
    const year = Number(record.date.match(/\d{4}/)?.[0] || table.caption.match(/\d{4}/)?.[0]);
    if (!table.chart?.svg || !year) {
      throw new Error(`Faltan los datos del gráfico electoral: ${table.caption}`);
    }
    return {
      record,
      table,
      year,
      label: table.chart.selectorLabel || table.chart.heading || table.caption,
      src: `assets/documentos/${table.chart.svg}`,
    };
  }
  function municipalVotesChart(table) {
    const votes = table.rows.map((row) => Number(row[1].replaceAll(".", "")));
    const total = votes.reduce((sum, value) => sum + value, 0);
    const group = element("section", undefined, "study-chart-referendum");
    group.append(element("h3", table.caption, "study-chart-title"));
    group.append(element("p", "Porcentaje entre estas dos candidaturas", "study-chart-note"));
    table.rows.forEach((row, index) => {
      const percentage = votes[index] / total * 100;
      const bar = studyBar(row[0], percentage, 100, index === 0 ? "is-monarchist" : "is-republican");
      bar.querySelector(".study-chart-value").textContent = `${percentage.toFixed(2).replace(".", ",")} %`;
      group.append(bar);
    });
    group.append(element("p", table.rows.map((row) => `${row[0]}: ${row[1]} votos`).join(" · "), "study-chart-note"));
    return group;
  }
  function studyChart(record, preview) {
    const section = element("section", undefined, "study-chart");
    const chart = element("div");
    if (record.visualization === "elections" || record.id === "elecciones-1977-diagrama") {
      if (!preview) chart.setAttribute("aria-live", "polite");
      const nationalSeries = isNationalElectionRecord(record);
      const republicSeries = isRepublicElectionRecord(record);
      const options = nationalSeries
        ? nationalElectionCharts()
        : republicSeries
          ? documents.filter(isRepublicElectionRecord)
            .flatMap((entry) => entry.tables.map((table) => electionChartEntry(entry, table)))
            .sort((a, b) => a.year - b.year)
        : (record.tables || []).map((table) => electionChartEntry(record, table));
      const selectedIndex = options.findIndex((option) => option.record.id === record.id);
      if (selectedIndex < 0) throw new Error(`No hay gráfico electoral para ${record.id}`);
      const renderElection = (option) => {
        const { table, year } = option;
        const image = element("img", undefined, "study-election-chart");
        image.src = option.src;
        image.alt = `Semicírculo de escaños${table.chart?.showVotes === false ? " por candidatura o bloque" : ` y votos por candidatura${table.chartGroups ? " y agrupación editorial" : ""}`} en las elecciones de ${year}. Datos completos en las tablas.`;
        if (preview) image.loading = "lazy";
        chart.replaceChildren(image);
        if (!preview && table.chart?.postCutoffNote) {
          chart.append(element("p", table.chart.postCutoffNote, "study-chart-note"));
        }
        if (!preview && option.record.errorNote) {
          chart.append(element("p", option.record.errorNote, "document-error-note"));
        }
        if (!preview) chart.append(sourceLink("Abrir gráfico SVG", image.src));
      };
      if (!preview && (nationalSeries || republicSeries)) {
        const selector = element("div", undefined, "study-chart-selector");
        const select = element("select");
        select.setAttribute("aria-label", "Desplegable electoral");
        options.forEach((entry, index) => {
          const option = element("option", entry.label);
          option.value = String(index);
          select.append(option);
        });
        select.value = String(selectedIndex);
        const previous = element("button", "←", "study-chart-nav");
        previous.type = "button";
        previous.setAttribute("aria-label", "Anterior elección");
        previous.title = "Anterior elección";
        previous.disabled = selectedIndex === 0;
        const next = element("button", "→", "study-chart-nav");
        next.type = "button";
        next.setAttribute("aria-label", "Próxima elección");
        next.title = "Próxima elección";
        next.disabled = selectedIndex === options.length - 1;
        const openElection = (index) => {
          const selected = options[index];
          if (!selected) throw new Error("La elección seleccionada no está disponible");
          open(selected.record, opener, "replace");
          updateReaderNavigation();
          dialog.querySelector(".study-chart-selector select")?.focus({ preventScroll: true });
        };
        select.addEventListener("change", () => openElection(Number(select.value)));
        previous.addEventListener("click", () => openElection(Number(select.value) - 1));
        next.addEventListener("click", () => openElection(Number(select.value) + 1));
        selector.append(previous, select, next);
        section.append(selector);
      }
      renderElection(options[selectedIndex]);
    } else if (record.visualization === "municipal-turnout") {
      const comparison = documents.find((item) => item.id === record.comparisonDocumentId);
      if (!comparison || comparison.visualization !== "municipal-votes") {
        throw new Error("Falta la comparación de votos de las elecciones municipales");
      }
      chart.append(municipalVotesChart(comparison.tables[0]));
      if (!preview) {
        chart.append(element("p", comparison.quality, "document-reading-note"));
        comparison.tables[0].notes.forEach((note) => chart.append(element("p", note, "document-reading-note")));
      }
    } else if (record.visualization === "municipal-votes") {
      chart.append(municipalVotesChart(record.tables[0]));
    } else {
      const table = record.tables[0];
      (preview ? table.rows.slice(0, 1) : table.rows).forEach((row) => {
        const group = element("section", undefined, "study-chart-referendum");
        group.append(element("h3", row[0], "study-chart-title"));
        const names = ["Participación · sobre censo", "Sí · sobre votantes", "No · sobre votantes"];
        names.forEach((name, index) => {
          const number = Number(row[index + 1].replace(",", "."));
          const bar = studyBar(name, number, 100, index === 2 ? "is-no" : index === 0 ? "is-turnout" : "is-yes");
          bar.querySelector(".study-chart-value").textContent = `${row[index + 1]} %`;
          group.append(bar);
        });
        if (!preview) {
          group.append(element("p", table.headers.slice(4).map((header, index) =>
            `${header.replace(" (%)", "")}: ${row[index + 4]} %`).join(" · ") + " · sobre votantes", "study-chart-note"));
        }
        chart.append(group);
      });
    }
    section.append(chart);
    return section;
  }
  function source(document, preview = false) {
    const box = element("div", undefined, preview ? "document-preview" : "document-full-source");
    if (!preview) {
      for (const note of new Set(matchingAppearances(document).map((appearance) => appearance.imageReviewNote).filter(Boolean))) {
        box.append(element("p", note, "document-reading-note"));
      }
    }
    if (!preview && document.origin === "propio") {
      if (document.quality && !isNationalElectionRecord(document)) {
        box.append(element("p", document.quality, "document-reading-note"));
      }
      if (document.readingNote) box.append(element("p", document.readingNote, "document-reading-note"));
    }
    const series1977 = document.id === "elecciones-1977-diagrama";
    if ((document.origin === "propio" && document.visualization !== "map") || series1977) {
      box.append(studyChart(document, preview));
    }
    const cardImage = document.image || document.tableImage;
    if (preview && (document.tableImage || cardImage?.kind === "table")) {
      box.classList.add("document-preview-table");
    }
    const fullImages = [document.image, ...(document.image?.additionalImages || []), document.tableImage]
      .filter((image, index, images) => image && images.findIndex((candidate) => candidate?.src === image.src) === index);
    const visibleImages = series1977
      ? fullImages.filter((image) => image.src !== document.image?.src)
      : fullImages;
    const imageGroup = visibleImages.length > 1
      ? element("div", undefined, preview ? "document-preview-pair" : "document-image-pair") : null;
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
        box.append(element("p", document.origin === "propio"
          ? "No se pudo cargar la imagen."
          : "No se pudo cargar la imagen. Consulta el PDF enlazado en las apariciones.", "document-quality"));
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
      if (!preview && imageData.editorialNote) {
        figure.append(element("p", imageData.editorialNote, "document-reading-note"));
      }
      if (!preview && !document.sharedImageCaption && !imageData.hideExamCaption) {
        const caption = imageData.examCaption || document.examCaption;
        const foot = element("figcaption", undefined, "document-exam-caption");
        foot.append(sourceParagraph(caption?.text || "(Sin descripción)", caption?.emphasis));
        if (caption?.note) {
          foot.append(sourceParagraph(caption.note, caption.noteEmphasis, "document-exam-footnote"));
        }
        figure.append(foot);
      }
      if (!preview && imageData.annotations) {
        annotatePhoto(figure, imageData, imageIndex ? `${document.id}-${imageIndex}` : document.id);
      }
      if (!preview && imageData.attribution) {
        const attribution = imageData.attribution;
        const details = element("details", undefined, "document-image-credits");
        details.append(element("summary", "Créditos de la imagen"));
        const credit = element("p", undefined, "document-image-caption");
        credit.append(link(attribution.text, attribution.url), " · ", link(attribution.license, attribution.licenseUrl));
        details.append(credit);
        figure.append(details);
      }
      if (!preview && !document.sharedImageCaption && imageData.sourceUrl) {
        const attribution = sourceLink("Fuente de esta reproducción", imageData.sourceUrl);
        attribution.className = "document-image-caption";
        figure.append(attribution);
      }
      if (!preview && imageData.openVector) {
        const enlarged = sourceLink("Abrir redibujo ampliable", imageData.src);
        enlarged.className = "document-image-caption document-vector-link";
        figure.append(enlarged);
      }
      if (!preview && imageIndex === 0 && document.dataSourceUrl) {
        const dataSource = sourceLink("Fuente de los datos", document.dataSourceUrl);
        dataSource.className = "document-image-caption";
        figure.append(dataSource);
      }
      if (!preview && !document.sharedImageCaption && imageData.originalSrc) {
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
    if (!preview && document.sharedImageCaption && imageGroup) {
      const caption = element("div", undefined, "document-exam-caption");
      caption.append(sourceParagraph(document.examCaption.text, document.examCaption.emphasis));
      box.append(caption);
      if (document.image.sourceUrl) {
        const attribution = sourceLink("Fuente de esta reproducción", document.image.sourceUrl);
        attribution.className = "document-image-caption";
        box.append(attribution);
      }
      if (document.image.originalSrc) {
        const original = sourceLink("Ver recorte del PDF original", document.image.originalSrc);
        original.className = "document-image-caption document-original-link";
        box.append(original);
      }
    }
    if (!preview && document.origin === "propio" && document.visualization === "map") {
      document.additionalSources?.forEach((item) => {
        const source = element("p", undefined, "document-image-caption");
        source.append(sourceLink(item.label, item.url));
        box.append(source);
      });
    }
    if (preview && cardImage) {
      const zoom = element("button", undefined, "document-preview-zoom");
      zoom.type = "button";
      zoom.setAttribute("aria-label", `Ver imagen: ${document.title}`);
      zoom.title = "Ver imagen";
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
    const tables = document.tables || (document.table ? [document.table] : []);
    if (tables.length && (!preview || !cardImage) && !(preview && document.origin === "propio")) {
      const ownDetails = document.origin === "propio" ? element("details", undefined, "document-table-details") : null;
      if (ownDetails) ownDetails.append(element("summary", "Ver tablas y notas de los datos"));
      for (const data of preview ? tables.slice(0, 1) : tables) {
        const table = element("table", undefined, "document-table");
        table.append(element("caption", data.caption));
        const head = element("tr");
        data.headers.forEach((value) => {
          const cell = element("th", value);
          cell.scope = "col";
          head.append(cell);
        });
        const thead = element("thead");
        thead.append(head);
        table.append(thead);
        const body = element("tbody");
        data.rows.forEach((values) => {
          const row = element("tr");
          values.forEach((value, i) => {
            const cell = element(i === 0 ? "th" : "td", String(value));
            if (i === 0) cell.scope = "row";
            row.append(cell);
          });
          body.append(row);
        });
        table.append(body);
        if (ownDetails) {
          ownDetails.append(table);
          data.notes?.forEach((note) => ownDetails.append(element("p", note, "document-image-caption")));
        } else if (preview) {
          box.append(table);
        } else {
          const details = element("details", undefined, "document-table-details");
          details.append(element("summary", "Leer la tabla en texto"));
          details.append(table);
          data.notes?.forEach((note) => details.append(element("p", note, "document-image-caption")));
          box.append(details);
        }
      }
      if (ownDetails) box.append(ownDetails);
      if (!preview && document.origin === "propio") {
        document.questions?.forEach((question) => box.append(element("p", question, "document-image-caption")));
        box.append(sourceLink("Fuente de los datos", document.dataSourceUrl));
        document.additionalSources?.forEach((item) => {
          const source = element("p", undefined, "document-image-caption");
          source.append(sourceLink(item.label, item.url));
          box.append(source);
        });
      }
    } else if (document.type === "imagen" && !document.image) {
      box.append(element("p", "La fotografía se puede ver en el PDF del modelo, en la página indicada.", "document-reading-note"));
    } else if (!document.image && !tables.length) {
      const selections = textSelections(document);
      const primary = document.studyCompilation || selections[0];
      const alternatives = document.studyCompilation ? selections : selections.slice(1);
      const titleIsSourceHeading = document.studyCompilation
        && primary.headingParagraphs?.includes(0) && primary.text[0] === primary.title;
      if (!preview && (document.studyCompilation || document.textVersions)) {
        const heading = element("p", undefined, "document-group-note document-group-heading");
        heading.append(element("span", "Recopilación", "document-group-label"));
        if (document.textVersions) {
          heading.append(element("span",
            "Han caído variaciones de este mismo texto; todas están al final.",
            "document-group-description"));
        } else {
          heading.append(element("span", "Texto reunido para estudiar.", "document-group-description"));
        }
        box.append(heading);
        if (document.studyCompilation && primary.showTitle !== false && !titleIsSourceHeading) {
          box.append(element("h3", primary.title));
        }
      }
      if (!preview && primary.readingNote) {
        box.append(element("p", primary.readingNote, "document-reading-note"));
      }
      box.append(textQuote(primary, preview));
      if (!preview && document.historicalNote) {
        box.append(element("p", `* ${document.historicalNote}`, "document-reading-note"));
      }
      if (!preview && document.studyCompilation) {
        box.append(sourceLink("Consultar el texto original de referencia", primary.sourceUrl));
      }
      if (!preview && document.textVersions) {
        const details = element("details", undefined, "document-text-versions");
        details.append(element("summary", "Ver selecciones y variantes por examen"));
        if (!document.studyCompilation) {
          details.append(element("h3", "Procedencia de la selección principal"), versionSources(primary));
        }
        alternatives.forEach((version, index) => {
          const section = element("section", undefined, "document-text-version");
          section.dataset.versionId = version.id;
          section.append(element("h3",
            `${document.studyCompilation ? "Selección del examen" : "Selección alternativa"} ${index + 1}`),
            versionSources(version));
          if (version.readingNote) section.append(element("p", version.readingNote, "document-reading-note"));
          section.append(element("p", version.quality, "document-quality"), textQuote(version));
          details.append(section);
        });
        box.append(details);
      }
      if (preview) {
        const more = element("span", "… ", "document-read-more");
        more.setAttribute("aria-hidden", "true");
        more.append(element("span", "Leer más"));
        box.append(more);
      }
    }
    return box;
  }
  function open(document, button, routeMode = "push") {
    if (!dialog.open) pagePosition = { left: window.scrollX, top: window.scrollY };
    opener = button;
    selectedId = document.id;
    if (routeMode !== "none" && documentRouteId() !== document.id) {
      setDocumentRoute(document.id, routeMode);
    } else if (routeMode === "none") {
      routePushedForDialog = false;
    }
    shareDocumentButton.disabled = false;
    setShareStatus("");
    resetPeopleStages();
    content.replaceChildren();
    content.append(element("p", `${typeNames[document.type]} · Bloque ${document.blocks.join(" · ")}`, "document-kind"));
    const title = sourceText("h2", document.title, document.titleEmphasis);
    if (document.titleMarker) title.append(element("sup", document.titleMarker));
    title.id = "document-dialog-title";
    content.append(title);
    attachMarks(content, document);
    const meta = element("p", document.date, "document-meta");
    const total = document.appearances.length;
    const filtered = matchingAppearances(document).length;
    if (document.origin === "propio") meta.append(" · Material de estudio · sin apariciones en la PAU todavía");
    else meta.append(" · ", element("strong", `${total} ${total === 1 ? "aparición" : "apariciones"} en total`));
    if (filtered !== total) meta.append(` · ${filtered} con los filtros actuales`);
    content.append(meta, appearanceBadges(document), source(document));
    if (document.textVersions && matchingAppearances(document).some((appearance) =>
      appearance.sourceReviewStatus === "transcription-copy" && !appearance.textReviewedByUser)) {
      content.append(element("p",
        "La selección de 2006 procede de una copia no original y está pendiente de cotejo con el examen original.",
        "document-reading-note"));
    }
    const guide = element("details", undefined, "document-guide");
    guide.append(element("summary", "Claves para responder a) y b)"));
    guide.append(element("p", "Orientación didáctica propia; no es una solución oficial.", "document-meta"));
    document.commentary.forEach((section) => guide.append(element("h3", section.title), element("p", section.text)));
    const selectedAppearances = matchingAppearances(document);
    const historicalModel = exam.value === "modelo orientaciones pau"
      && selectedAppearances.some((appearance) => appearance.sourceReviewStatus === "orientation-model");
    const historicalOnly = document.blocks.every((number) => number < 5);
    const task = element("section", undefined, "document-task");
    task.setAttribute("aria-label", document.origin === "propio" ? "Práctica orientativa" : "Enunciado de PAU · 4 puntos");
    task.append(element("h3", document.origin === "propio" ? "Práctica orientativa · formato PAU" : "Enunciado de PAU · 4 puntos"));
    task.append(element("p", "a) Analice el hecho histórico a que hace referencia el documento elegido."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    task.append(element("p", "b) Explique el contexto histórico y las consecuencias de este acontecimiento."));
    task.append(element("p", "De 0 a 2 puntos.", "document-meta"));
    const guidance = document.type === "texto"
      ? "En textos, a) permite desarrollar naturaleza, ideas principales y secundarias y contexto inmediato; b) explica el proceso general, sus causas y consecuencias. La extensión puede estar más equilibrada."
      : "En mapas, gráficos y tablas, a) es más breve y descriptivo: identifica los elementos y sitúalos en su contexto inmediato. Dedica mayor desarrollo a b): evolución general del momento, causas y consecuencias relacionadas con el documento.";
    task.append(element("p", `${guidance} Pauta docente: a) no debería superar media carilla. No es un límite oficial añadido al examen ni cambia la puntuación: ambos apartados valen lo mismo.`, "document-meta"));
    if (historicalModel) {
      content.append(element("p", "En este modelo histórico se pedía analizar el documento y justificar su relación con el tema (hasta 1,5 puntos por documento).", "document-meta"), guide);
    } else if (historicalOnly) {
      content.append(element("p", "Documento de un formato histórico. El bloque 4 corresponde a las cuestiones cortas y queda fuera del comentario de documento del modelo 2026–27.", "document-meta"), guide);
    } else {
      content.append(task, guide);
    }
    const sourceAppearance = historicalModel ? selectedAppearances[0] : document.examCaption
      ? document.appearances.find((appearance) => appearance.id === document.examCaption.appearanceId)
      : matchingAppearances(document)[0] || document.appearances[0];
    if (sourceAppearance) {
    const sourceLabel = sourceAppearance.sourceReviewStatus === "orientation-model"
      ? `Ver PDF del modelo · p. ${sourceAppearance.officialPage}`
      : document.id === "elecciones-1977-diagrama"
        ? "2007 · Examen 4 · Bloque II · Opción B"
        : sourceAppearance.sourceType === "pdf"
          ? sourceAppearance.sourceReviewStatus === "transcription-copy" ? "Ver copia PDF de origen" : "Ver PDF de origen"
          : "Ver en la recopilación";
    const collectionLink = sourceLink(sourceLabel, sourceAppearance.sourceUrl);
    collectionLink.className = "document-collection-link";
    const footer = element("p");
    footer.append(collectionLink);
    content.append(footer);
    }
    document.blocks.forEach((number) => content.append(link(`Ir a los apuntes del bloque ${number} →`, `apuntes/bloque-${number}.html`)));
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    updateReaderCue();
    refreshMarks();
    saveView();
  }
  function updateReaderNavigation() {
    const cards = visibleCards();
    const index = cards.findIndex((card) => card.dataset.id === selectedId);
    previousDocument.disabled = index <= 0;
    nextDocument.disabled = index < 0 || index >= cards.length - 1;
    readerStatus.textContent = index < 0
      ? "Este documento ya no figura en los filtros actuales."
      : `Documento ${index + 1} de ${cards.length}: ${content.querySelector("h2").textContent}`;
  }
  function navigateDocument(direction) {
    const cards = visibleCards();
    const index = cards.findIndex((card) => card.dataset.id === selectedId);
    const card = index >= 0 ? cards[index + direction] : null;
    if (!card) return;
    const record = documents.find((item) => item.id === card.dataset.id);
    open(record, card.querySelector(".document-open"), "replace");
    const button = direction < 0 ? previousDocument : nextDocument;
    const opposite = direction < 0 ? nextDocument : previousDocument;
    (button.disabled ? opposite.disabled ? dialog.querySelector(".document-close") : opposite : button)
      .focus({ preventScroll: true });
  }
  previousDocument.addEventListener("click", () => navigateDocument(-1));
  nextDocument.addEventListener("click", () => navigateDocument(1));
  previousDocument.setAttribute("aria-keyshortcuts", "ArrowLeft");
  nextDocument.setAttribute("aria-keyshortcuts", "ArrowRight");
  previousDocument.title = "Documento anterior (←)";
  nextDocument.title = "Documento siguiente (→)";
  dialog.addEventListener("keydown", (event) => {
    if (!dialog.open || event.defaultPrevented || event.isComposing
      || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey
      || !["ArrowLeft", "ArrowRight"].includes(event.key)
      || event.target.isContentEditable
      || event.target.closest("input, textarea, select, [role='slider'], [role='tab'], [role='radio']")) return;
    event.preventDefault();
    navigateDocument(event.key === "ArrowLeft" ? -1 : 1);
  });
  dialog.querySelector(".document-close").addEventListener("click", () => dialog.close());
  let backdropPressed = null;
  const outsideDialog = (event) => {
    const bounds = dialog.getBoundingClientRect();
    return event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
  };
  let swipeStart = null;
  const isPageZoomed = () => (window.visualViewport?.scale || 1) > 1.01;
  dialog.addEventListener("touchstart", (event) => {
    swipeStart = null;
    if (!dialog.open || event.touches.length !== 1 || isPageZoomed()
      || event.target.isContentEditable
      || event.target.closest("a, button, summary, input, textarea, select, object, iframe")) return;
    const touch = event.touches[0];
    if (outsideDialog(touch)) return;
    for (let node = event.target; node !== dialog; node = node.parentElement) {
      if (node.scrollWidth > node.clientWidth + 1 && /^(auto|scroll)$/.test(getComputedStyle(node).overflowX)) return;
    }
    swipeStart = { id: touch.identifier, x: touch.clientX, y: touch.clientY, documentId: selectedId };
  }, { passive: true });
  dialog.addEventListener("touchmove", (event) => {
    if (!swipeStart) return;
    const touch = event.touches[0];
    if (event.touches.length !== 1 || isPageZoomed()) {
      swipeStart = null;
      return;
    }
    const dy = Math.abs(touch.clientY - swipeStart.y);
    if (dy > 16 && dy >= Math.abs(touch.clientX - swipeStart.x)) swipeStart = null;
  }, { passive: true });
  dialog.addEventListener("touchcancel", () => { swipeStart = null; }, { passive: true });
  dialog.addEventListener("touchend", (event) => {
    const start = swipeStart;
    swipeStart = null;
    if (!start || !dialog.open || selectedId !== start.documentId || event.touches.length
      || isPageZoomed() || window.getSelection()?.isCollapsed === false) return;
    const touch = Array.from(event.changedTouches).find((point) => point.identifier === start.id);
    if (!touch) return;
    const dx = touch.clientX - start.x;
    const dy = touch.clientY - start.y;
    if (Math.abs(dx) >= 64 && Math.abs(dx) >= 1.5 * Math.abs(dy)) navigateDocument(dx < 0 ? 1 : -1);
  }, { passive: true });
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
    const closedFromHistory = routeChangeFromHistory;
    routeChangeFromHistory = false;
    if (!closedFromHistory && routePushedForDialog) {
      routePushedForDialog = false;
      history.back();
    } else {
      routePushedForDialog = false;
      if (!closedFromHistory) clearDocumentRoute();
    }
    backdropPressed = null;
    swipeStart = null;
    shareDocumentButton.disabled = true;
    setShareStatus("");
    resetPeopleStages();
    updateReaderCue();
    (opener?.isConnected ? opener : filterFocusTarget())?.focus({ preventScroll: true });
    if (pagePosition) {
      scrollPage(pagePosition);
      pagePosition = null;
    }
    selectedId = null;
    saveView();
  });
  async function copyDocumentLink(url) {
    let clipboardFailure = null;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        return;
      }
    } catch (failure) {
      clipboardFailure = failure;
    }
    const field = element("textarea");
    field.value = url;
    field.readOnly = true;
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.append(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    if (!copied) throw clipboardFailure || new Error("El navegador no permitió copiar el enlace.");
  }
  function setShareStatus(message, failed = false, target = shareStatus) {
    window.clearTimeout(shareStatusTimer);
    shareStatusTimer = 0;
    activeShareStatus.hidden = true;
    activeShareStatus = target;
    target.textContent = message;
    target.hidden = !message;
    target.setAttribute("role", failed ? "alert" : "status");
    if (message) {
      shareStatusTimer = window.setTimeout(() => {
        target.hidden = true;
        shareStatusTimer = 0;
      }, 5000);
    }
  }
  async function shareDocument(record, target = shareStatus) {
    if (!record) {
      setShareStatus("No se pudo identificar el documento para compartir.", true, target);
      console.error("No se pudo compartir: falta el documento seleccionado.");
      return;
    }
    const url = shareableDocumentUrl(record.id);
    try {
      if (navigator.share) {
        await navigator.share({ title: record.title, url });
        setShareStatus("Enlace compartido.", false, target);
      } else {
        await copyDocumentLink(url);
        setShareStatus("Enlace copiado al portapapeles.", false, target);
      }
    } catch (failure) {
      if (failure?.name === "AbortError") return;
      try {
        await copyDocumentLink(url);
        setShareStatus("No se pudo abrir la opción de compartir; enlace copiado al portapapeles.", false, target);
      } catch (copyFailure) {
        console.error("No se pudo compartir ni copiar el enlace del documento.", failure, copyFailure);
        setShareStatus("No se pudo compartir ni copiar el enlace del documento.", true, target);
      }
    }
  }
  shareDocumentButton.addEventListener("click", () => shareDocument(documents.find((item) => item.id === selectedId)));
  let cachedSearch = [null, []];
  const currentTerms = () => {
    if (cachedSearch[0] !== search.value) cachedSearch = [search.value, searchTerms(search.value)];
    return cachedSearch[1];
  };
  const matchesSearch = (document) => {
    const haystack = searchIndex.get(document.id);
    return (!savedOnly || isMarked(document)) && currentTerms().every((term) => haystack.includes(term));
  };
  const baseMatches = (document) => (type === "all" || document.type === type)
      && (savedFilter === "all" || hasMark(document, savedFilter))
      && (document.origin === "propio" ? !examYear.value && !exam.value : document.appearances.some(matchesExam))
      && (!block.value || document.blocks.includes(Number(block.value)))
      && matchesSearch(document);
  function fitTopics() {
    if (!moreFilters.open) return;
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
    if (!topicToggle.hidden) {
      for (const bubble of [...bubbles].reverse()) {
        if (bubble.hidden || bubble.getAttribute("aria-pressed") === "true") continue;
        const visible = bubbles.filter((button) => !button.hidden);
        const last = visible[visible.length - 1];
        if (visible.length <= 1
          || topicToggle.getBoundingClientRect().bottom - last.getBoundingClientRect().bottom <= 2) break;
        bubble.hidden = true;
      }
    }
  }
  let topicWidth = 0;
  new ResizeObserver(([entry]) => {
    if (entry.contentRect.width === topicWidth) return;
    topicWidth = entry.contentRect.width;
    requestAnimationFrame(fitTopics);
  }).observe(topics);
  document.fonts.ready.then(fitTopics);
  moreFilters.addEventListener("toggle", fitTopics);
  function renderTopics() {
    const available = documents.filter(baseMatches);
    const tags = [...new Set(available.flatMap((document) => document.tags))];
    if (topic && !tags.includes(topic)) {
      if (documents.some((document) => document.tags.includes(topic))) tags.push(topic);
      else topic = "";
    }
    const statistics = new Map(tags.map((tag) => {
      const tagged = available.filter((document) => document.tags.includes(tag));
      const firstYear = Math.min(...tagged.map((document) => {
        const year = String(document.date).match(/\b(?:1[0-9]{3}|20[0-9]{2})\b/);
        return year ? Number(year[0]) : Number.MAX_SAFE_INTEGER;
      }));
      return [tag, {
        documents: tagged.filter((record) => record.origin !== "propio").length,
        own: tagged.filter((record) => record.origin === "propio").length,
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
    const query = searchTerms(topicSearch.value);
    const matchingTags = tags.filter((tag) => {
      const text = indexText(tag);
      return query.every((term) => text.includes(term));
    });
    topics.replaceChildren();
    topicEmpty.hidden = !query.length || matchingTags.length > 0;
    topicToggle.hidden = Boolean(query.length) || matchingTags.length <= 8;
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
      button.title = `${stats.appearances} ${stats.appearances === 1 ? "aparición" : "apariciones"} en ${stats.documents} ${stats.documents === 1 ? "ficha" : "fichas"} del corpus`
        + (stats.own ? ` · ${stats.own} ${stats.own === 1 ? "material propio" : "materiales propios"}` : "");
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
  function renderUnits(available) {
    const all = element("option", "Todos los subbloques");
    all.value = "";
    unitSelect.replaceChildren(all);
    for (const number of [...new Set(thematicUnits.map((unit) => unit.block))]) {
      const units = thematicUnits.filter((unit) => unit.block === number);
      const group = element("optgroup");
      group.label = `Bloque ${number} · Agrupación ${units[0].group}`;
      for (const unit of units) {
        const total = available.filter((record) => unit.documentIds.includes(record.id))
          .reduce((sum, record) => sum + record.appearances.length, 0);
        const option = element("option", `${unit.number}. ${unit.title} (${total})`);
        option.value = unit.id;
        group.append(option);
      }
      unitSelect.append(group);
    }
    unitSelect.value = selectedUnit;
    unitSelect.title = thematicUnits.find((unit) => unit.id === selectedUnit)?.title || "Todas las unidades temáticas de las orientaciones 2026–27";
    frequencySort.setAttribute("aria-pressed", String(frequencyOrder));
  }
  function renderActiveFilters(unit) {
    const optionLabel = (select) => select.value && select.selectedOptions[0]?.textContent;
    const filters = [
      ["Búsqueda", search.value.trim(), () => { search.value = ""; }],
      ["Bloque", optionLabel(block), () => { block.value = ""; }],
      ["Tipo", type !== "all" && typeNames[type], () => setType("all")],
      ["Año", optionLabel(examYear), () => { examYear.value = ""; updateExamOptions(); }],
      ["Examen", optionLabel(exam), () => { exam.value = ""; }],
      ["Temática", topic, () => { topic = ""; }],
      ["Subbloque", unit && `${unit.number}. ${unit.title}`, () => { selectedUnit = ""; }],
      ["Marca", { favorite: "Favoritos", review: "Pendientes de repaso" }[savedFilter],
        () => { savedFilter = "all"; }],
    ].filter(([, value]) => value);
    activeFilters.replaceChildren();
    activeFilters.hidden = filters.length === 0;
    for (const [label, value, clear] of filters) {
      const item = element("li");
      const text = `${label}: ${value}`;
      const button = element("button");
      button.type = "button";
      button.dataset.filter = label;
      button.setAttribute("aria-label", `Quitar filtro: ${text}`);
      const cross = element("span", "×");
      cross.setAttribute("aria-hidden", "true");
      button.append(element("span", text), cross);
      button.addEventListener("click", () => {
        const index = filters.findIndex(([key]) => key === label);
        const preferred = [...filters.slice(index + 1), ...filters.slice(0, index).reverse()];
        clear();
        render();
        const remaining = [...activeFilters.querySelectorAll("button")];
        const next = preferred.map(([key]) => remaining.find((node) => node.dataset.filter === key)).find(Boolean);
        (next || reset).focus();
      });
      item.append(button);
      activeFilters.append(item);
    }
  }
  function render() {
    const focused = document.activeElement;
    const oldCard = focused.closest(".document-card");
    const oldCards = [...grid.querySelectorAll(".document-card")];
    const oldIndex = oldCards.indexOf(oldCard);
    renderTopics();
    const available = documents.filter((document) => baseMatches(document) && (!topic || document.tags.includes(topic)));
    renderUnits(available);
    const unit = thematicUnits.find((unit) => unit.id === selectedUnit);
    renderActiveFilters(unit);
    const matches = available.filter((record) => !unit || unit.documentIds.includes(record.id));
    const appearances = matches.reduce((total, document) => total + document.appearances.length, 0);
    const scope = examYear.value ? "en total" : appearances === 1 ? "incorporada" : "incorporadas";
    const ownCount = matches.filter((record) => record.origin === "propio").length;
    const examCount = matches.length - ownCount;
    count.textContent = `${examCount} ${examCount === 1 ? "documento" : "documentos"} · ${appearances} ${appearances === 1 ? "aparición" : "apariciones"} ${scope}`
      + (ownCount ? ` · ${ownCount} ${ownCount === 1 ? "material propio" : "materiales propios"}` : "");
    const outside = currentTerms().length ? documents.filter(matchesSearch).length - matches.length : 0;
    searchOutside.hidden = outside <= 0;
    if (outside > 0) {
      searchOutsideText.textContent = `${outside} ${outside === 1 ? "coincidencia más" : "coincidencias más"} con esta búsqueda ${outside === 1 ? "queda" : "quedan"} fuera de los filtros activos.`;
    }
    grid.replaceChildren();
    document.querySelector("#document-empty").hidden = matches.length > 0;
    const numbers = block.value ? [Number(block.value)]
      : [...new Set(matches.flatMap((document) => document.blocks))].sort((a, b) => a - b);
    const byFrequency = (a, b) => b.appearances.length - a.appearances.length
      || a.title.localeCompare(b.title, "es");
    const sections = frequencyOrder ? [
      {
        number: block.value && block.value !== "4" ? Number(block.value) : null,
        records: matches.filter((record) => record.blocks.some((number) => number >= 5)).sort(byFrequency),
      },
      {
        number: 4,
        records: matches.filter((record) => record.blocks.every((number) => number === 4)).sort(byFrequency),
      },
    ] : numbers.map((number) => ({
      number, records: matches.filter((record) => record.blocks.includes(number)),
    }));
    const displayed = new Set();
    for (const { number, records } of sections) {
      const group = records.filter((record) => !displayed.has(record.id));
      if (!group.length) continue;
      const section = element("section");
      const heading = element("div", undefined, "document-block-heading");
      if (number === null) {
        heading.append(element("h2", "Documentos · Más frecuentes primero"));
      } else {
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
      }
      const cards = element("div", undefined, "document-card-grid");
      if (number === 4) {
        heading.classList.add("has-history-toggle");
        cards.id = "document-block-4-cards";
        const toggle = element("button", undefined, "document-history-toggle");
        toggle.type = "button";
        toggle.setAttribute("aria-controls", cards.id);
        const syncToggle = () => {
          cards.hidden = !historicalVisible;
          toggle.setAttribute("aria-expanded", String(historicalVisible));
          const label = `${historicalVisible ? "Ocultar" : "Mostrar"} documentos históricos del bloque 4`;
          toggle.setAttribute("aria-label", label);
          toggle.title = label;
          toggle.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>'
            + (historicalVisible ? "" : '<path d="m3 3 18 18"/>') + "</svg>";
        };
        toggle.addEventListener("click", () => {
          historicalVisible = !historicalVisible;
          syncToggle();
          if (dialog.open) updateReaderNavigation();
          saveView();
        });
        syncToggle();
        heading.prepend(toggle);
        section.append(heading, element("p",
          "Archivo histórico · Fuera del comentario de documentos del modelo 2026–27.",
          "document-historical-notice"), cards);
      } else {
        section.append(heading, cards);
      }
      for (const document of group) {
        displayed.add(document.id);
        const card = element("article", undefined, "document-card");
        card.dataset.id = document.id;
        card.dataset.documentType = document.type;
        card.append(source(document, true));
        const body = element("div", undefined, "document-card-body");
        const kind = document.type === "texto" ? "Texto · vista previa" : typeNames[document.type];
        body.append(element("p", kind + (frequencyOrder ? ` · Bloque ${document.blocks.join(" · ")}` : ""), "document-kind"),
          sourceText("h3", document.title, document.titleEmphasis));
        const occurrences = document.appearances.length;
        body.append(element("p", document.origin === "propio" ? `${document.date} · Sin apariciones todavía`
          : `${document.date} · ${occurrences} ${occurrences === 1 ? "aparición incorporada" : "apariciones incorporadas"}`, "document-meta"));
        body.append(appearanceBadges(document));
        body.append(element("p", document.tags.join(" · "), "document-card-topics"));
        const button = element("button", document.type === "texto" ? "Leer texto completo y practicar →" : "Ver documento y practicar →", "document-open");
        button.type = "button";
        button.setAttribute("aria-label", `Ver documento: ${document.title}`);
        button.addEventListener("click", () => open(document, button));
        const actions = element("div", undefined, "document-card-actions");
        const share = element("button", undefined, "document-card-share");
        share.type = "button";
        share.setAttribute("aria-label", `Compartir documento: ${document.title}`);
        share.innerHTML = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3m0 0 4 4m-4-4L8 7"/><path d="M5 12v8h14v-8"/></svg><span>Compartir</span>';
        share.addEventListener("click", () => shareDocument(document, cardShareStatus));
        actions.append(button, share);
        body.append(actions);
        attachMarks(body, document);
        card.append(body);
        cards.append(card);
      }
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
      (card?.querySelector(selector) || filterFocusTarget())?.focus({ preventScroll: true });
    }
    saveView();
  }
  function visibleCards() {
    return [...grid.querySelectorAll(".document-card")].filter((card) => !card.closest("[hidden]"));
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
    render();
  });
  topicToggle.addEventListener("click", () => {
    topicsExpanded = !topicsExpanded;
    renderTopics();
    topicToggle.focus();
  });
  topicSort.addEventListener("change", renderTopics);
  unitSelect.addEventListener("change", () => { selectedUnit = unitSelect.value; render(); });
  frequencySort.addEventListener("click", () => { frequencyOrder = !frequencyOrder; render(); });
  search.addEventListener("input", render);
  block.addEventListener("change", render);
  examYear.addEventListener("change", () => { updateExamOptions(); render(); });
  exam.addEventListener("change", render);
  function clearFilters(keepSearch) {
    if (!keepSearch) search.value = "";
    block.value = "";
    examYear.value = "";
    updateExamOptions();
    setType("all");
    topic = "";
    topicSearch.value = "";
    savedFilter = "all";
    selectedUnit = "";
    if (keepSearch) return;
    topicsExpanded = false;
    historicalVisible = false;
    topicSort.value = "alphabetical";
    frequencyOrder = false;
  }
  reset.addEventListener("click", () => {
    clearFilters(false);
    render();
  });
  searchOutsideButton.addEventListener("click", () => {
    clearFilters(true);
    render();
    search.focus({ preventScroll: true });
  });
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(resolve));
  async function restoreView() {
    const saved = restoredView;
    if (!saved) { restoring = false; saveView(); return; }
    const record = saved.dialog && documents.find((item) =>
      memberIds(item).includes(saved.dialog.id) && (!savedOnly || isMarked(item)));
    if (record?.blocks.includes(4) && !historicalVisible) {
      historicalVisible = true;
      render();
    }
    if (record) {
      const card = [...grid.querySelectorAll(".document-card")].find((node) => node.dataset.id === record.id);
      open(record, card?.querySelector(saved.dialog.opener === "zoom" ? ".document-preview-zoom" : ".document-open"), "none");
      let details = saved.dialog.details;
      if (record.textVersions && !saved.dialog.selectionsGrouped) {
        details = [details.slice(0, -1).some(Boolean), details[details.length - 1] || false];
      }
      content.querySelectorAll("details").forEach((node, index) => {
        node.open = details[index] || false;
      });
      if (record.id !== saved.dialog.id) {
        const version = content.querySelector(`[data-version-id="${CSS.escape(saved.dialog.id)}"]`);
        if (version) version.closest("details").open = true;
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
      const ownResponse = await fetch("data/documentos-propios.json");
      if (!ownResponse.ok) throw new Error(`Material propio: HTTP ${ownResponse.status}`);
      const ownData = await ownResponse.json();
      if (!Array.isArray(data.documents) || !data.documents.length) throw new Error("El banco no contiene documentos");
      if (data.documents.some((record) => !Array.isArray(record.appearances)
        || record.appearances.some((appearance) =>
          typeof appearance.pdfUrl !== "string"
          || !(/^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]+\/view$/.test(appearance.pdfUrl)
            || appearance.sourceReviewStatus === "user-scan"
              && /^assets\/documentos\/[a-z0-9._-]+\.pdf$/.test(appearance.pdfUrl))))) {
        throw new Error("Falta un enlace válido al PDF de un examen");
      }
      if (data.documents.some((document) => !Array.isArray(document.blocks) || !document.blocks.length
        || document.blocks.some((number) => !Number.isInteger(number) || number < 4 || number > 12))) {
        throw new Error("Los documentos deben pertenecer a los bloques 4–12 (el bloque 4 es solo archivo histórico)");
      }
      if (data.documents.some((record) => record.paragraphStarts && (
        record.type !== "texto" || !Array.isArray(record.paragraphStarts) || record.paragraphStarts[0] !== 0
        || record.paragraphStarts.some((start, index, starts) =>
          !Number.isInteger(start) || start < 0 || start >= record.text.length
          || index > 0 && start <= starts[index - 1])))) {
        throw new Error("Los límites de párrafo de un texto no son válidos");
      }
      if (data.documents.some((record) => record.headingParagraphs !== undefined && (
        record.type !== "texto" || !Array.isArray(record.headingParagraphs)
        || record.headingParagraphs.some((index) => !Number.isInteger(index) || index < 0
          || index >= record.text.length || record.paragraphStarts && !record.paragraphStarts.includes(index))))) {
        throw new Error("Los encabezados de un texto no son válidos");
      }
      if (data.documents.some((record) => record.titleMarker !== undefined
        && (record.titleMarker !== "*" || typeof record.historicalNote !== "string"
          || !record.historicalNote.trim())
        || record.historicalNote !== undefined
          && (record.type !== "texto" || typeof record.historicalNote !== "string"
            || !record.historicalNote.trim() || record.titleMarker !== "*"))) {
        throw new Error("La nota histórica de un texto no es válida");
      }
      if (data.documents.some((record) => record.studyCompilation !== undefined && (
        record.type !== "texto" || !record.studyCompilation
        || !["title", "sourceUrl"].every((key) =>
          typeof record.studyCompilation[key] === "string" && record.studyCompilation[key].trim())
        || record.studyCompilation.showTitle !== undefined
          && typeof record.studyCompilation.showTitle !== "boolean"
        || record.studyCompilation.readingNote !== undefined
          && (typeof record.studyCompilation.readingNote !== "string"
            || !record.studyCompilation.readingNote.trim())
        || !Array.isArray(record.studyCompilation.text) || !record.studyCompilation.text.length
        || record.studyCompilation.text.some((line) => typeof line !== "string" || !line.trim())
        || !Number.isInteger(record.studyCompilation.attributionParagraphs)
        || record.studyCompilation.attributionParagraphs < 0
        || record.studyCompilation.attributionParagraphs >= record.studyCompilation.text.length))) {
        throw new Error("La recopilación de estudio de un texto no es válida");
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
      documents = groupTexts(data.documents, data.textGroups);
      thematicUnits = readThematicUnits(data.curriculum, documents);
      if (!Array.isArray(ownData.documents) || ownData.documents.some((record) =>
        !record.id || documents.some((item) => item.id === record.id)
        || !record.title || !record.date || !record.sourceCaption || !record.dataSourceUrl
        || !Array.isArray(record.blocks) || !record.blocks.length
        || !Array.isArray(record.tags) || !Array.isArray(record.commentary)
        || !Array.isArray(record.unitIds) || !record.unitIds.length
        || record.unitIds.some((id) => !thematicUnits.some((unit) => unit.id === id && record.blocks.includes(unit.block)))
        || !["elections", "referendums", "municipal-turnout", "municipal-votes", "map"].includes(record.visualization)
        || (record.visualization === "map"
          ? !record.image?.src || !record.image.alt || !(record.image.width > 0) || !(record.image.height > 0)
          : !Array.isArray(record.tables) || !record.tables.length
        || record.tables.some((table) => !table.caption || !Array.isArray(table.headers)
          || !table.headers.length || !Array.isArray(table.rows) || !table.rows.length
          || (record.visualization === "elections" && (
            !/ · \d{4}$/.test(table.caption)
            || (!table.chart && !/^Congreso de los Diputados · \d{4}$/.test(table.caption))
            || (table.chart && (!/^elecciones-[a-z]+-\d{4}-semicirculo\.svg$/.test(table.chart.svg)
              || !Number.isInteger(table.chart.seats) || table.chart.seats < 1 || table.chart.seats > 600))))
          || (record.visualization === "municipal-turnout" && (table.headers.length !== 4
            || table.rows.some((row) => row.length !== 4 || !/^\d+(?:,\d+)?$/.test(row[3])
              || Number(row[3].replace(",", ".")) > 100)))
          || (record.visualization === "municipal-votes" && (table.headers.length !== 2
            || table.rows.length !== 2 || table.rows.some((row) => !Array.isArray(row)
              || row.length !== 2 || typeof row[1] !== "string"
              || !/^(?:\d{1,3}(?:\.\d{3})+|\d+)$/.test(row[1]))
            || table.rows.every((row) => Number(row[1].replaceAll(".", "")) === 0)))
          || table.rows.some((row) => !Array.isArray(row) || row.length !== table.headers.length
            || (record.visualization === "elections"
              ? table.headers.length !== 4 || !(row[3] === "—" || /^\d+$/.test(row[3]) && Number(row[3]) <= 600)
              : record.visualization === "municipal-turnout"
                ? table.headers.length !== 4 || row.slice(1).some((value) =>
                  typeof value !== "string" || !/^(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?$/.test(value))
              : record.visualization === "municipal-votes"
                ? false
                : ![5, 6].includes(table.headers.length) || row.slice(1).some((value) =>
                typeof value !== "string" || !/^\d+(?:,\d+)?$/.test(value) || Number(value.replace(",", ".")) > 100))))))) {
        throw new Error("Los materiales propios no son válidos");
      }
      if (new Set(ownData.documents.map((record) => record.id)).size !== ownData.documents.length) {
        throw new Error("Hay materiales propios duplicados");
      }
      if (ownData.documents.some((record) => record.visualization === "municipal-turnout"
        && !ownData.documents.some((item) => item.id === record.comparisonDocumentId
          && item.visualization === "municipal-votes"))) {
        throw new Error("Falta la comparación de votos de las elecciones municipales");
      }
      for (const record of ownData.documents) {
        documents.push({ ...record, origin: "propio", type: "grafico", appearances: [] });
        for (const id of record.unitIds) thematicUnits.find((unit) => unit.id === id).documentIds.push(record.id);
      }
      officialExams = new Map((coverage.officialExamAvailability || []).map((entry) => [entry.year, entry]));
      searchIndex.clear();
      documents.forEach((record) => searchIndex.set(record.id, indexText(searchableText(record))));
      examYear.replaceChildren(element("option", "Todos los años"));
      examYear.firstElementChild.value = "";
      for (let year = 2001; year <= 2027; year++) {
        const option = element("option", String(year));
        option.value = String(year);
        examYear.append(option);
      }
      const scope = document.querySelector("#document-scope");
      if (scope) {
        const total = coverage.sourceDocumentOccurrences;
        const exams = new Set(documents.flatMap((record) =>
          record.appearances.map((appearance) => appearance.pdfUrl))).size;
        scope.textContent =
          `${total} ${total === 1 ? "documento recopilado" : "documentos recopilados"} · `
          + `${exams} ${exams === 1 ? "examen" : "exámenes"} · Desde 2000-01 hasta 2026-27, ambos inclusive.`;
      }
      const requestedBlock = new URLSearchParams(location.search).get("bloque");
      if (restoredView) {
        setType(restoredView.type);
        savedFilter = restoredView.savedFilter;
        block.value = restoredView.block;
        examYear.value = restoredView.year;
        updateExamOptions(restoredView.exam);
        search.value = restoredView.search;
        topic = restoredView.topic;
        topicSearch.value = restoredView.topicSearch;
        topicSort.value = restoredView.sort;
        topicsExpanded = restoredView.expanded;
        historicalVisible = restoredView.historicalVisible;
        if (restoredView.unit && !thematicUnits.some((unit) => unit.id === restoredView.unit)) {
          console.warn("El subbloque guardado ya no está disponible; se muestran todos.");
        } else {
          selectedUnit = restoredView.unit;
        }
        frequencyOrder = restoredView.frequencyOrder;
      } else {
        if (requestedBlock && block.querySelector(`option[value="${Number(requestedBlock)}"]`)) block.value = requestedBlock;
        updateExamOptions();
      }
      loaded = true;
      render();
      await restoreView();
      if (initialDocumentId) openDocumentFromRoute(initialDocumentId);
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
  function openDocumentFromRoute(id) {
    const record = documents.find((item) => item.id === id);
    if (!record) {
      if (dialog.open) {
        routePushedForDialog = false;
        routeChangeFromHistory = true;
        dialog.close();
      }
      error.textContent = "No se encontró el documento solicitado. Puede que la ficha haya cambiado.";
      error.hidden = false;
      clearDocumentRoute();
      return;
    }
    if (dialog.open && selectedId === id) return;
    const card = [...grid.querySelectorAll(".document-card")].find((item) => item.dataset.id === id);
    open(record, card?.querySelector(".document-open") || null, "none");
  }
  window.addEventListener("popstate", () => {
    const id = documentRouteId();
    if (!loaded) {
      initialDocumentId = id;
      if (initialDocumentId && restoredView?.dialog) restoredView = { ...restoredView, dialog: null };
      return;
    }
    if (id) {
      openDocumentFromRoute(id);
    } else if (dialog.open) {
      routeChangeFromHistory = true;
      dialog.close();
    } else {
      saveView();
    }
  });
  retry.addEventListener("click", load);
  load();
})();
