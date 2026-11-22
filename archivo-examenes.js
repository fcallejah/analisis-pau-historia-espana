(() => {
  const archive = document.getElementById("archivo-orientaciones");
  const dialog = document.getElementById("archive-dialog");
  const title = document.getElementById("archive-dialog-title");
  const content = dialog.querySelector(".archive-dialog-content");
  const left = dialog.querySelector(".archive-left");
  const right = dialog.querySelector(".archive-right");
  const courses = [archive.querySelector(".orientation-current"), ...archive.querySelectorAll(".orientation-courses > li > *")];
  const orientations = new Map();
  let documentsPromise;
  let openSequence = 0;
  let currentYear;
  let touchStart;

  function loadDocuments() {
    if (!documentsPromise) {
      documentsPromise = fetch("data/documentos.json").then((response) => {
        if (!response.ok) throw new Error(`Error ${response.status}`);
        return response.json();
      }).then((data) => {
        if (!Array.isArray(data.documents)) throw new Error("El banco de documentos no tiene el formato esperado.");
        return data.documents;
      }).catch((error) => {
        documentsPromise = null;
        throw error;
      });
    }
    return documentsPromise;
  }

  function addHeading(text) {
    const heading = document.createElement("h4");
    heading.textContent = text;
    content.append(heading);
  }

  function addList(items) {
    const list = document.createElement("ul");
    items.forEach(({ label, url }) => {
      const item = document.createElement("li");
      const element = document.createElement(url ? "a" : "span");
      element.textContent = label;
      if (url) {
        element.href = url;
        element.target = "_blank";
        element.rel = "noopener noreferrer";
      }
      item.append(element);
      list.append(item);
    });
    content.append(list);
  }

  function addNote(text) {
    const note = document.createElement("p");
    note.textContent = text;
    content.append(note);
  }

  function getExams(documents, year) {
    const exams = new Map();
    if (year >= 2017 && year <= 2026) {
      for (const [reference, id] of shortExamDriveIds) {
        if (!reference.startsWith(`${year} · `) || reference.endsWith("· Modelo PAU")) continue;
        exams.set(`https://drive.google.com/file/d/${id}/view`, reference.slice(7));
      }
    }
    for (const record of documents) {
      for (const appearance of record.appearances || []) {
        if (appearance.year !== year || !appearance.pdfUrl || !appearance.exam) continue;
        if (/modelo orientaciones/i.test(appearance.exam)) continue;
        if (year >= 2017 && year <= 2026) continue;
        const label = appearance.exam
          .replace(new RegExp(`^${year}\\s+`), "")
          .replace(" (numeración del corpus)", "");
        if (!exams.has(appearance.pdfUrl)) exams.set(appearance.pdfUrl, label);
      }
    }
    return [...exams].map(([url, label]) => ({
      url,
      label: `${label}${year === 2001 || year === 2006 ? " · reconstruido" : ""}`,
    })).sort((a, b) => a.label.localeCompare(b.label, "es", { numeric: true }));
  }

  async function openCourse(year) {
    const sequence = ++openSequence;
    currentYear = year;
    const orientationUrl = orientations.get(year);
    left.disabled = !orientations.has(year + 1);
    right.disabled = !orientations.has(year - 1);
    left.textContent = left.disabled ? "← Sin curso" : `← ${year}–${year + 1}`;
    right.textContent = right.disabled ? "Sin curso →" : `${year - 2}–${year - 1} →`;
    title.textContent = `Curso ${year - 1}–${String(year).slice(-2)}`;
    content.replaceChildren();
    addHeading("Orientaciones");
    addList([{ label: orientationUrl ? "Orientaciones del curso" : "Orientaciones no localizadas", url: orientationUrl }]);
    addHeading("Exámenes");
    addNote("Cargando exámenes…");
    if (!dialog.open) dialog.showModal();
    try {
      const documents = await loadDocuments();
      if (!dialog.open || sequence !== openSequence) return;
      content.lastElementChild.remove();
      const exams = getExams(documents, year);
      const placeholders = Array.from({ length: Math.max(0, 6 - exams.length) }, () => ({
        label: year === 2027 ? "Examen pendiente" : "Examen no localizado",
      }));
      addList([...exams, ...placeholders]);
      if (year === 2027) addNote("Los exámenes de esta convocatoria aún no están disponibles.");
      if (year === 2001) addNote("Reconstrucciones para lectura a partir del escaneo; incluyen criterios de 2001–02 como referencia.");
      if (year === 2006) addNote("Reconstrucciones no oficiales, pendientes de cotejo con los originales.");
      if ([2014, 2016, 2018, 2026].includes(year)) addNote("La colección de exámenes disponibles para este curso está incompleta.");
    } catch (error) {
      if (!dialog.open || sequence !== openSequence) return;
      content.lastElementChild.textContent = `No se pudieron cargar los exámenes (${error.message}). Cierra y vuelve a abrir el curso para reintentar.`;
    }
  }

  function navigate(offset) {
    const year = currentYear + offset;
    if (orientations.has(year)) openCourse(year);
  }

  left.addEventListener("click", () => navigate(1));
  right.addEventListener("click", () => navigate(-1));
  dialog.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      navigate(event.key === "ArrowLeft" ? 1 : -1);
    }
  });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) {
      dialog.close();
    }
  });
  dialog.addEventListener("touchstart", (event) => {
    touchStart = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  dialog.addEventListener("touchend", (event) => {
    if (!touchStart || event.changedTouches.length !== 1) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) >= 60 && Math.abs(dx) > Math.abs(dy) * 1.5) navigate(dx < 0 ? 1 : -1);
  }, { passive: true });
  dialog.addEventListener("touchcancel", () => { touchStart = null; });

  courses.forEach((element) => {
    const match = element.textContent.match(/(20\d{2})[–-](\d{2})/);
    if (!match) return;
    const year = Number(match[1]) + 1;
    const orientationUrl = element.tagName === "A" ? element.getAttribute("href") : null;
    orientations.set(year, orientationUrl);
    const button = document.createElement("button");
    button.type = "button";
    button.className = element.classList.contains("orientation-current") ? "orientation-current" : "";
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-label", `Abrir histórico del curso ${match[0]}`);
    if (button.className) {
      const label = document.createElement("span");
      label.textContent = "CURSO VIGENTE";
      const course = document.createElement("strong");
      course.textContent = match[0];
      button.append(label, course);
    } else {
      button.textContent = match[0];
    }
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("class", "ext-icon");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("fill", "none");
    icon.setAttribute("stroke", "currentColor");
    icon.setAttribute("stroke-width", "2");
    icon.setAttribute("aria-hidden", "true");
    const arrow = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arrow.setAttribute("d", "m6 9 6 6 6-6");
    icon.append(arrow);
    if (button.className) button.querySelector("strong").append(icon);
    else button.append(icon);
    button.addEventListener("click", () => openCourse(year));
    element.replaceWith(button);
  });
})();
