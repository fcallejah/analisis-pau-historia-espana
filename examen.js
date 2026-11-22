(() => {
  const button = document.getElementById("exam-generate");
  if (!button) return;
  const status = document.getElementById("exam-generator-status");
  const error = document.getElementById("exam-generator-error");
  const preview = document.getElementById("exam-preview");
  const generateButtons = [...document.querySelectorAll(".exam-generate")];
  const saveButtons = [...document.querySelectorAll(".exam-save-pdf")];
  const saveFooter = document.getElementById("exam-save-footer");
  const headerTemplate = document.getElementById("exam-paper-header-template");
  const confirmDialog = document.getElementById("exam-confirm-dialog");
  const storageKey = "pau-he-generated-exam-v1";
  const normalize = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es").replace(/[^\p{L}\p{N}]+/gu, "");
  const shuffle = (items) => {
    const result = items.slice();
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  };
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  let curriculum;
  let records;
  let questions;
  let activeExam = null;

  function setButtonState(label, canRegenerate, disabled) {
    generateButtons.forEach((generateButton) => {
      generateButton.querySelector(".exam-generate-label").textContent = label;
      generateButton.querySelector(".exam-generate-icon").toggleAttribute("hidden", !canRegenerate);
      generateButton.disabled = disabled;
    });
    const hasExam = Boolean(activeExam);
    saveButtons.forEach((saveButton) => { saveButton.hidden = !hasExam; });
    saveFooter.hidden = !hasExam;
  }

  function saveExamAsPdf() {
    if (!activeExam) return;
    window.print();
  }

  function showNotice(message) {
    error.replaceChildren(make("p", "", message));
    error.hidden = false;
  }

  function showError(message) {
    error.replaceChildren(make("p", "", message));
    const retry = make("button", "exam-retry", "Reintentar");
    retry.type = "button";
    retry.addEventListener("click", load);
    error.append(retry);
    error.hidden = false;
    status.textContent = "No se pudo preparar el generador.";
    setButtonState(activeExam ? "Generar otro simulacro" : "Preparar simulacro", Boolean(activeExam), !activeExam);
  }

  async function load() {
    error.hidden = true;
    status.textContent = "Cargando las preguntas y los documentos disponibles…";
    generateButtons.forEach((generateButton) => { generateButton.disabled = true; });
    try {
      if (!Array.isArray(window.pauPracticeBank) || window.pauPracticeBank.length === 0) {
        throw new Error("No está disponible el banco de preguntas cortas.");
      }
      questions = [1, 2, 3, 4].map((block) => {
        const byPrompt = new Map();
        window.pauPracticeBank.forEach(([prompt, , number]) => {
          if (number === block && typeof prompt === "string" && prompt.trim()) byPrompt.set(normalize(prompt), prompt);
        });
        const bank = [...byPrompt.values()];
        if (!bank.length) throw new Error(`El banco no contiene preguntas para el bloque ${block}.`);
        return { block, bank };
      });
      const response = await fetch("data/documentos.json");
      if (!response.ok) throw new Error(`No se pudo cargar el banco de documentos (${response.status}).`);
      const data = await response.json();
      curriculum = data.curriculum?.units;
      records = new Map(data.documents?.map((record) => [record.id, record]));
      if (!Array.isArray(curriculum) || records.size === 0) {
        throw new Error("El banco de documentos no contiene agrupaciones y fichas utilizables.");
      }
      ["II", "III"].forEach((group) => {
        if (!getDocuments(group).length || !curriculum.some((unit) => unit.group === group)) {
          throw new Error(`No hay documentos suficientes para la Agrupación ${group}.`);
        }
      });
      if (!curriculum.some((unit) => unit.group === "II") || !curriculum.some((unit) => unit.group === "III")) {
        throw new Error("No se han encontrado temas de las Agrupaciones II y III.");
      }
      const restored = restoreStoredExam();
      if (restored.exam) {
        activeExam = restored.exam;
        renderExam(activeExam);
        setButtonState("Generar otro simulacro", true, false);
        status.textContent = "Se ha recuperado el último simulacro guardado.";
      } else {
        setButtonState("Preparar simulacro", false, false);
        status.textContent = "Listo para generar un simulacro aleatorio.";
      }
      if (restored.message) showNotice(restored.message);
    } catch (reason) {
      showError(reason instanceof Error ? reason.message : "Error desconocido al cargar los bancos.");
    }
  }

  function getDocuments(group) {
    const ids = new Set(curriculum.filter((unit) => unit.group === group)
      .flatMap((unit) => unit.documentIds || []));
    return [...ids].map((id) => records.get(id)).filter((record) => {
      if (!record) return false;
      if (record.type === "texto") return examSourceParagraphs(record).length > 0;
      return record.type === "imagen" && Boolean(record.image?.src);
    });
  }

  function makeQuestionList(selectedQuestions) {
    const list = make("ol", "exam-short-questions");
    selectedQuestions.forEach(({ block, prompt }) => {
      const item = make("li", "exam-short-question");
      item.dataset.block = String(block);
      item.append(make("p", "", prompt));
      list.append(item);
    });
    return list;
  }

  function examSourceParagraphs(record) {
    if (!Array.isArray(record.text) || !record.appearances?.length) return [];
    return record.text.flatMap((text, index) =>
      typeof text === "string" && text.trim() ? [{ text, index }] : []);
  }

  function makeDocumentCard(record, group, index) {
    const card = make("article", record.type === "texto" ? "exam-document exam-document-text" : "exam-document");
    card.dataset.documentId = record.id;
    card.dataset.group = group;
    const heading = make("h4", "", `Documento ${index + 1}`);
    card.append(heading);
    if (record.type === "texto") {
      const text = make("div", "exam-source-text");
      const attributionStart = record.text.length - (record.attributionParagraphs || 0);
      examSourceParagraphs(record).forEach(({ text: paragraph, index: paragraphIndex }) => {
        const attribution = paragraphIndex >= attributionStart;
        const heading = record.headingParagraphs?.includes(paragraphIndex);
        const className = attribution
          ? "exam-text-attribution"
          : heading
            ? `exam-text-heading${record.centerHeadings === false ? "" : " is-centered"}`
            : "exam-text-body";
        text.append(make("p", className, paragraph));
      });
      card.append(text);
    } else {
      const image = make("img", "exam-source-image");
      const imageData = record.image;
      image.src = imageData.src;
      image.alt = imageData.alt || record.title;
      image.loading = "eager";
      image.width = imageData.width;
      image.height = imageData.height;
      if (imageData.filter) image.style.filter = imageData.filter;
      const imageContainer = make("div", "exam-image-container");
      let cropFrame = null;
      const crop = imageData.crop;
      if (crop) {
        const cropAspect = imageData.width / imageData.height
          * crop.width / crop.imageWidth * crop.imageHeight / crop.height;
        cropFrame = make("span", "exam-image-crop");
        cropFrame.style.setProperty("--exam-image-crop-aspect", cropAspect);
        cropFrame.style.setProperty("--exam-image-crop-max-width", `${480 * cropAspect}px`);
        cropFrame.style.setProperty("--exam-image-crop-mobile-max-width", `${360 * cropAspect}px`);
        image.style.setProperty("--exam-crop-image-width", `${100 * crop.imageWidth / crop.width}%`);
        image.style.setProperty("--exam-crop-image-height", `${100 * crop.imageHeight / crop.height}%`);
        image.style.setProperty("--exam-crop-image-left", `${100 * crop.left / crop.width}%`);
        image.style.setProperty("--exam-crop-image-top", `${100 * crop.top / crop.height}%`);
        cropFrame.append(image);
      }
      image.addEventListener("error", () => {
        image.hidden = true;
        imageContainer.hidden = true;
        card.append(make("p", "exam-image-error", "No se pudo cargar esta imagen del banco de documentos."));
      }, { once: true });
      imageContainer.append(cropFrame || image);
      card.append(imageContainer);
      const caption = record.image.examCaption?.text || record.examCaption?.text;
      if (caption) card.append(make("p", "exam-image-caption", caption.replace(/\*/g, "")));
    }
    return card;
  }

  function makeThemeList(themes) {
    const list = make("ol", "exam-themes");
    themes.forEach((unit) => {
      const item = make("li", "exam-theme");
      item.dataset.group = unit.group;
      const title = unit.title.trim();
      item.append(make("p", "", /[.!?…]$/.test(title) ? title : `${title}.`));
      list.append(item);
    });
    return list;
  }

  function makePartTable(title, instruction, content, className = "") {
    const table = make("table", `exam-part-table ${className}`.trim());
    const body = make("tbody");
    const rows = Array.isArray(content)
      ? content.map((row) => Array.isArray(row) ? row : [row])
      : [[content]];
    const columnCount = Math.max(1, ...rows.map((row) => row.length));
    const headingRow = make("tr");
    const headingCell = make("td");
    headingCell.colSpan = columnCount;
    headingCell.append(
      make("h4", "exam-part-title", title),
      make("p", "exam-instruction", instruction),
    );
    headingRow.append(headingCell);
    body.append(headingRow);
    rows.forEach((rowContent) => {
      const contentRow = make("tr");
      rowContent.forEach((cellContent) => {
        const contentCell = make("td");
        if (rowContent.length === 1 && columnCount > 1) contentCell.colSpan = columnCount;
        contentCell.append(cellContent);
        contentRow.append(contentCell);
      });
      body.append(contentRow);
    });
    table.append(body);
    return table;
  }

  function makeExamInstructions() {
    const box = make("table", "exam-paper-instructions");
    box.setAttribute("aria-label", "Instrucciones del examen");
    const body = make("tbody");
    const instructions = [
      "a) Duración: 1 hora y 30 minutos.",
      "b) Todas las cuestiones deben responderse en el papel entregado para la realización del examen y nunca en los folios que contienen los enunciados.",
      "c) Este examen está estructurado en bloques. Deberá responder a lo que se indica en cada bloque.",
      "d) La valoración de cada apartado se indica en este.",
      "e) La falta de adecuación a lo solicitado en el enunciado de las distintas preguntas, la coherencia, cohesión, corrección gramatical, léxica y ortográfica, así como su presentación de las respuestas dadas por el alumnado podrán reducir la puntuación del conjunto de los tres bloques hasta 1 punto.",
    ];
    const firstRow = make("tr");
    const heading = make("th", "exam-paper-instructions-title", "Instrucciones:");
    heading.rowSpan = instructions.length;
    heading.scope = "rowgroup";
    firstRow.append(heading, make("td", "exam-paper-instruction", instructions[0]));
    body.append(firstRow);
    instructions.slice(1).forEach((instruction) => {
      const row = make("tr");
      row.append(make("td", "exam-paper-instruction", instruction));
      body.append(row);
    });
    box.append(body);
    return box;
  }

  function makeRoute(route, routeDocuments, documentGroup, themes) {
    const section = make("section", "exam-route");
    section.dataset.route = route;
    section.append(make("h3", "exam-route-title", `ITINERARIO ${route}`));
    const documentColumns = routeDocuments.map((record, index) =>
      makeDocumentCard(record, documentGroup, index));
    const documentCriteria = make("p", "exam-document-final-instruction");
    documentCriteria.append(
      "a) Analice el hecho histórico a que hace referencia el documento elegido.",
      make("br"),
      "b) Explique el contexto histórico y las consecuencias de este acontecimiento."
    );
    const documentTable = makePartTable(
      "II. DOCUMENTO (hasta 4 puntos, de 0 a 2 puntos por pregunta respondida)",
      "Responda los enunciados de UNO de los dos documentos siguientes:",
      [documentColumns, [documentCriteria]],
      "exam-document-part",
    );
    const themeTable = makePartTable(
      "III. TEMA (de 0 a 3 puntos)",
      "Responda a UNO de los dos siguientes temas:",
      makeThemeList(themes),
      "exam-theme-part",
    );
    const routeTable = make("table", "exam-part-table exam-document-part exam-theme-part");
    const routeBody = make("tbody");
    const documentRows = [...documentTable.querySelectorAll("tbody > tr")];
    documentRows.at(-1).classList.add("exam-document-criteria-row");
    const themeRows = [...themeTable.querySelectorAll("tbody > tr")];
    themeRows[0].classList.add("exam-theme-heading-row");
    documentRows.forEach((row) => routeBody.append(row));
    themeRows.forEach((row) => {
      row.querySelector("td").colSpan = 2;
      routeBody.append(row);
    });
    routeTable.append(routeBody);
    section.append(routeTable);
    return section;
  }

  function hydrateExam(saved) {
    if (!saved || saved.version !== 1 || !Array.isArray(saved.questions) || !Array.isArray(saved.routes)
        || saved.questions.length !== 4 || saved.routes.length !== 2) {
      throw new Error("El simulacro guardado tiene un formato no válido.");
    }
    const selectedQuestions = saved.questions.map((entry, index) => {
      const expectedBlock = index + 1;
      if (!entry || entry.block !== expectedBlock || typeof entry.prompt !== "string"
          || !questions[index].bank.includes(entry.prompt)) {
        throw new Error("El simulacro guardado ya no coincide con el banco de preguntas.");
      }
      return { block: expectedBlock, prompt: entry.prompt };
    });
    const specifications = [
      { route: "A", documentGroup: "II", themeGroup: "III" },
      { route: "B", documentGroup: "III", themeGroup: "II" },
    ];
    const usedDocuments = new Set();
    const routes = specifications.map((specification, index) => {
      const entry = saved.routes[index];
      if (!entry || entry.route !== specification.route
          || entry.documentGroup !== specification.documentGroup
          || entry.themeGroup !== specification.themeGroup
          || !Array.isArray(entry.documentIds) || entry.documentIds.length !== 2
          || !Array.isArray(entry.themeIds) || entry.themeIds.length !== 2) {
        throw new Error("El simulacro guardado ya no coincide con los itinerarios disponibles.");
      }
      const availableDocuments = new Map(getDocuments(specification.documentGroup).map((record) => [record.id, record]));
      const documents = entry.documentIds.map((id) => {
        const record = availableDocuments.get(id);
        if (typeof id !== "string" || !record || usedDocuments.has(id)) {
          throw new Error("Un documento del simulacro guardado ya no está disponible.");
        }
        usedDocuments.add(id);
        return record;
      });
      const availableThemes = new Map(curriculum
        .filter((unit) => unit.group === specification.themeGroup)
        .map((unit) => [unit.id, unit]));
      const themes = entry.themeIds.map((id) => availableThemes.get(id));
      if (themes.some((unit) => !unit) || new Set(entry.themeIds).size !== 2) {
        throw new Error("Un tema del simulacro guardado ya no está disponible.");
      }
      return { ...specification, documents, themes };
    });
    return { version: 1, questions: selectedQuestions, routes };
  }

  function restoreStoredExam() {
    let raw;
    try {
      raw = localStorage.getItem(storageKey);
    } catch (reason) {
      return { exam: null, message: "El navegador no permite acceder al almacenamiento local; el simulacro no se conservará al recargar." };
    }
    if (!raw) return { exam: null, message: "" };
    try {
      return { exam: hydrateExam(JSON.parse(raw)), message: "" };
    } catch (reason) {
      try {
        localStorage.removeItem(storageKey);
      } catch (storageReason) {
        return { exam: null, message: "No se pudo recuperar ni descartar el simulacro guardado; el almacenamiento local no está disponible." };
      }
      return { exam: null, message: "El simulacro guardado ya no coincide con los materiales disponibles y se ha descartado." };
    }
  }

  function persistExam(exam) {
    const saved = {
      version: 1,
      questions: exam.questions,
      routes: exam.routes.map(({ route, documentGroup, themeGroup, documents: routeDocuments, themes: routeThemes }) => ({
        route,
        documentGroup,
        themeGroup,
        documentIds: routeDocuments.map((record) => record.id),
        themeIds: routeThemes.map((unit) => unit.id),
      })),
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(saved));
      return "";
    } catch (reason) {
      return "El simulacro se generó, pero el navegador no pudo guardarlo; no se conservará al recargar.";
    }
  }

  function selectExam() {
    const selectedQuestions = questions.map(({ block, bank }) => ({ block, prompt: shuffle(bank)[0] }));
    const pools = { II: shuffle(getDocuments("II")), III: shuffle(getDocuments("III")) };
    const themes = {
      II: shuffle(curriculum.filter((unit) => unit.group === "II")),
      III: shuffle(curriculum.filter((unit) => unit.group === "III")),
    };
    const usedDocuments = new Set();
    const specifications = [
      { route: "A", documentGroup: "II", themeGroup: "III" },
      { route: "B", documentGroup: "III", themeGroup: "II" },
    ];
    const routes = specifications.map(({ route, documentGroup, themeGroup }) => {
      const routeDocuments = pools[documentGroup].filter((record) => !usedDocuments.has(record.id)).slice(0, 2);
      if (routeDocuments.length < 2) throw new Error(`No quedan dos documentos distintos para la Agrupación ${documentGroup}.`);
      routeDocuments.forEach((record) => usedDocuments.add(record.id));
      const routeThemes = themes[themeGroup].splice(0, 2);
      if (routeThemes.length < 2) throw new Error(`No quedan dos temas para la Agrupación ${themeGroup}.`);
      return { route, documentGroup, themeGroup, documents: routeDocuments, themes: routeThemes };
    });
    return { version: 1, questions: selectedQuestions, routes };
  }

  function renderExam(exam) {
    const paper = make("article", "exam-paper");
    paper.setAttribute("aria-label", "Simulacro de examen completo");
    paper.append(headerTemplate.content.cloneNode(true));
    paper.append(makeExamInstructions());
    paper.append(make("p", "exam-block-intro", "El examen consta de TRES BLOQUES (CUESTIONES, DOCUMENTO Y TEMA) que deberán responderse según lo indicado"));
    paper.append(make("h3", "exam-route-title exam-common-title", "COMÚN A AMBOS ITINERARIOS"));
    const common = make("section", "exam-common");
    const commonInstruction = make("p", "exam-instruction");
    commonInstruction.append(
      "Responda a ",
      make("strong", "", "DOS de las cuatro cuestiones"),
      " planteadas:",
    );
    common.append(
      make("h3", "exam-part-title", "I. CUESTIONES (hasta 3 puntos en total, de 0 a 1,5 puntos por pregunta respondida)"),
      commonInstruction,
      makeQuestionList(exam.questions),
    );
    paper.append(common);
    const routeChoice = make("p", "exam-route-choice");
    routeChoice.append(
      "Elija\u00a0",
      make("strong", "", "UNO"),
      "\u00a0de los dos\u00a0",
      make("strong", "", "ITINERARIOS"),
      " y responda en ellos a lo que se le solicita en los apartados II. DOCUMENTOS y III. TEMAS:"
    );
    paper.append(routeChoice);
    exam.routes.forEach(({ route, documents: routeDocuments, documentGroup, themes }) =>
      paper.append(makeRoute(route, routeDocuments, documentGroup, themes)));
    preview.replaceChildren(paper);
  }

  function generate() {
    if (button.disabled) return;
    setButtonState("Preparando simulacro…", false, true);
    error.hidden = true;
    try {
      const nextExam = selectExam();
      renderExam(nextExam);
      activeExam = nextExam;
      const storageWarning = persistExam(activeExam);
      setButtonState("Generar otro simulacro", true, false);
      status.textContent = storageWarning
        ? "Simulacro generado, pero no se conservará al recargar."
        : "Simulacro generado y guardado en este navegador.";
      if (storageWarning) showNotice(storageWarning);
    } catch (reason) {
      showError(reason instanceof Error ? reason.message : "No se pudo generar el simulacro.");
    }
  }

  generateButtons.forEach((generateButton) => generateButton.addEventListener("click", () => {
    if (activeExam) confirmDialog.showModal();
    else generate();
  }));
  saveButtons.forEach((saveButton) => saveButton.addEventListener("click", saveExamAsPdf));
  confirmDialog.addEventListener("submit", (event) => {
    if (event.submitter?.value !== "regenerate") return;
    event.preventDefault();
    confirmDialog.close("regenerate");
    generate();
  });

  load();
})();
