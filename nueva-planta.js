(() => {
  const root = document.querySelector(".np-map");
  if (!root) return;
  const territories = {
    castilla: {
      name: "Corona de Castilla",
      date: "Modelo de referencia para la centralización",
      before: "La Corona de Castilla contaba con sus propias instituciones y leyes. Los territorios vascos pertenecían a esta corona, pero conservaban regímenes forales específicos.",
      after: "Felipe V extendió buena parte del modelo político y administrativo castellano a los territorios de la Corona de Aragón. Nueva Planta no significa que todos los territorios pasaran a tener idénticas leyes ni que surgieran las provincias actuales.",
      subdivisions: "Idea clave: una corona reunía varios reinos y territorios históricos. Las líneas discontinuas sitúan las grandes divisiones de forma aproximada; no representan provincias ni pequeños distritos.",
    },
    aragon: {
      name: "Reino de Aragón",
      date: "29 de junio de 1707 · Nueva organización en 1711",
      before: "Tenía Cortes e instituciones propias dentro de la Corona de Aragón, así como un ordenamiento foral.",
      after: "El decreto de 1707 abolió sus fueros e instituciones. La reorganización de 1711 recuperó parte del derecho civil aragonés, sin restablecer las instituciones políticas anteriores.",
      subdivisions: "Idea clave: el reino de Aragón era uno de los territorios de la Corona de Aragón. Reino y corona no eran lo mismo.",
    },
    valencia: {
      name: "Reino de Valencia",
      date: "29 de junio de 1707",
      before: "Formaba parte de la Corona de Aragón y disponía de Cortes, instituciones y fueros propios.",
      after: "Tras la victoria borbónica en Almansa, se abolieron sus fueros e instituciones y se implantó el modelo castellano. A diferencia de Aragón, Cataluña y Mallorca, no se restituyó su derecho civil propio.",
      subdivisions: "Idea clave: pertenecer a la misma corona no significaba compartir todas las leyes e instituciones. Valencia tenía las suyas.",
    },
    cataluna: {
      name: "Principado de Cataluña",
      date: "16 de enero de 1716",
      before: "Dentro de la Corona de Aragón, conservaba sus constituciones e instituciones, entre ellas las Cortes y la Diputación del General.",
      after: "Se suprimieron sus instituciones políticas propias y se reorganizó el gobierno mediante un capitán general y una Real Audiencia. Se mantuvo parte del derecho privado catalán: la pérdida de instituciones no equivale a la desaparición de todo el derecho propio.",
      subdivisions: "Idea clave: Cataluña era un principado dentro de la Corona de Aragón, con instituciones propias; no un reino independiente de esa corona.",
    },
    mallorca: {
      name: "Mallorca, Ibiza y Formentera",
      date: "28 de noviembre de 1715",
      before: "Pertenecían al reino de Mallorca, integrado en la Corona de Aragón, con instituciones propias. Menorca también pertenecía a este reino antes de su ocupación británica.",
      after: "Nueva Planta reorganizó el gobierno del reino de Mallorca, suprimió sus instituciones políticas propias y mantuvo parte de su derecho privado. Menorca, cedida a Gran Bretaña en Utrecht, no quedó bajo esta reorganización borbónica.",
      subdivisions: "Idea clave: el reino de Mallorca pertenecía a la Corona de Aragón. La separación de Menorca se explica por Utrecht, no por Nueva Planta.",
    },
    navarra: {
      name: "Reino de Navarra",
      date: "Conservación del régimen foral",
      before: "Estaba incorporado a la monarquía y conservaba su condición de reino, sus Cortes y su régimen foral.",
      after: "Conservó sus fueros e instituciones propias. Su apoyo a Felipe V ayuda a explicar por qué no recibió la misma reforma que los territorios de la Corona de Aragón.",
      subdivisions: "Idea clave: Navarra conservó su condición de reino y su régimen foral dentro de la monarquía.",
    },
    vizcaya: {
      name: "Señorío de Vizcaya",
      date: "Conservación del régimen foral",
      before: "Pertenecía a la Corona de Castilla con fueros e instituciones propias. No formaba un reino separado.",
      after: "Conservó su régimen foral y sus instituciones. Nueva Planta no suprimió los fueros de todos los territorios de la monarquía.",
      subdivisions: "Idea clave: Vizcaya, Guipúzcoa y Álava pertenecían a la Corona de Castilla, pero tenían regímenes forales propios. No eran un único territorio bajo el Señorío de Vizcaya.",
    },
    guipuzcoa: {
      name: "Provincia de Guipúzcoa",
      date: "Conservación del régimen foral",
      before: "Pertenecía a la Corona de Castilla y tenía un régimen foral e instituciones propias.",
      after: "Conservó su régimen foral y sus instituciones, al igual que Vizcaya y Álava.",
      subdivisions: "Idea clave: Guipúzcoa tenía su propia organización foral; no era una subdivisión del Señorío de Vizcaya.",
    },
    alava: {
      name: "Provincia de Álava",
      date: "Conservación del régimen foral",
      before: "Pertenecía a la Corona de Castilla y conservaba fueros e instituciones propias.",
      after: "Conservó su régimen foral y sus instituciones, al igual que Vizcaya y Guipúzcoa.",
      subdivisions: "Idea clave: Álava tenía su propia organización foral; no era una subdivisión del Señorío de Vizcaya.",
    },
  };
  const stage = root.querySelector(".np-stage");
  const info = root.querySelector(".np-info");
  const controls = root.querySelector(".np-controls");
  const regions = root.querySelector(".np-region-buttons");
  const modeButtons = [...root.querySelectorAll("[data-np-mode]")];
  let mode = "before";
  let selected = "aragon";
  let svg;
  let zoom = 1;
  let view = { x: 0, y: 0 };
  const pointers = new Map();
  let gesture;
  let dragged = false;
  let peaceArrows;
  const peaceCallout = root.querySelector(".np-peace-callout");
  const updatePeaceArrows = () => {
    if (!svg || !peaceArrows) return;
    const bounds = svg.getBoundingClientRect();
    const box = svg.viewBox.baseVal;
    const toSvg = (x, y) => {
      return {
        x: box.x + (x - bounds.left) * box.width / bounds.width,
        y: box.y + (y - bounds.top) * box.height / bounds.height,
      };
    };
    const panel = peaceCallout.getBoundingClientRect();
    const gibraltar = svg.querySelector('[data-peace="gibraltar"] circle').getBBox();
    const menorca = svg.querySelector('[data-peace="menorca"] path').getBBox();
    const endpoints = [
      {
        path: peaceArrows.gibraltar,
        start: toSvg(panel.left, panel.top + panel.height * 0.78),
        target: { x: gibraltar.x + gibraltar.width / 2, y: gibraltar.y + gibraltar.height / 2 },
      },
      {
        path: peaceArrows.menorca,
        start: toSvg(panel.left + panel.width * 0.8, panel.top),
        target: { x: menorca.x + menorca.width / 2, y: menorca.y + menorca.height / 2 },
      },
    ];
    endpoints.forEach(({ path, start, target }) => {
      path.setAttribute("d", `M${start.x},${start.y} L${target.x},${target.y}`);
    });
  };
  const updateView = () => {
    view.x = Math.max(0, Math.min(800 - 800 / zoom, view.x));
    view.y = Math.max(0, Math.min(560 - 560 / zoom, view.y));
    svg.setAttribute("viewBox", `${view.x} ${view.y} ${800 / zoom} ${560 / zoom}`);
    root.querySelector(".np-zoom-level").textContent = `${Math.round(zoom * 100)} %`;
    root.querySelector("[data-np-zoom=in]").disabled = zoom >= 4;
    root.querySelector("[data-np-zoom=out]").disabled = zoom <= 1;
    updatePeaceArrows();
  };
  const setZoom = (value, center = { x: 0.5, y: 0.5 }) => {
    const next = Math.max(1, Math.min(4, value));
    view.x += center.x * (800 / zoom - 800 / next);
    view.y += center.y * (560 / zoom - 560 / next);
    zoom = next;
    if (zoom === 1) view = { x: 0, y: 0 };
    updateView();
  };
  const paint = () => {
    root.dataset.mode = mode;
    modeButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.npMode === mode)));
    root.querySelector(".np-mode-description").textContent = mode === "before"
      ? "Antes · Monarquía Hispánica (hacia 1700)"
      : "Después · Centralización borbónica (reino de España) · tras 1716";
    root.querySelector(".np-aragon-label").textContent = mode === "before"
      ? "Territorios de la Corona de Aragón"
      : "Aragón, Cataluña, Valencia y Mallorca: Felipe V abolió sus fueros e instituciones políticas mediante los Decretos de Nueva Planta (1707–1716), tras la guerra de sucesión española. Invocó el «derecho de conquista» para justificar la abolición en el decreto de 1707.";
    root.querySelector(".np-castile-label").textContent = mode === "before"
      ? "Corona de Castilla"
      : "Modelo de centralización borbónica";
    root.querySelector(".np-peace-context").textContent = mode === "before"
      ? "Contexto posterior al mapa de hacia 1700."
      : "Cesiones distintas de los Decretos de Nueva Planta.";
    svg.querySelector("#map-title").textContent = mode === "before"
      ? "Territorios antes de Nueva Planta (hacia 1700)"
      : "Territorios después de Nueva Planta (tras 1716)";
    svg.querySelector('[data-peace="menorca"] text').textContent = mode === "before" ? "Menorca" : "Menorca · 1713";
    svg.querySelector('[data-peace="gibraltar"] text').textContent = mode === "before" ? "Gibraltar" : "Gibraltar · 1713";
    [...svg.querySelectorAll("[data-territory]"), ...regions.querySelectorAll("[data-territory]")].forEach((element) => {
      element.setAttribute("aria-pressed", String(element.dataset.territory === selected));
    });
    info.hidden = selected === null;
    if (selected === null) return;
    const item = territories[selected];
    info.querySelector("h3").textContent = item.name;
    info.querySelector(".np-date").textContent = mode === "after" ? item.date : "Antes de los decretos";
    info.querySelector(".np-explanation").textContent = item[mode];
    info.querySelector(".np-subdivisions").textContent = item.subdivisions;
  };
  const select = (id) => {
    selected = selected === id ? null : id;
    paint();
  };
  const beginGesture = () => {
    const points = [...pointers.values()];
    gesture = { points, view: { ...view }, zoom };
  };
  const distance = (a, b) => Math.hypot(b.x - a.x, b.y - a.y);
  const load = async () => {
    try {
      const response = await fetch(stage.querySelector("img").getAttribute("src"));
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const parsed = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
      if (parsed.querySelector("parsererror") || parsed.documentElement.localName !== "svg") {
        throw new Error("El archivo del mapa no es un SVG válido");
      }
      svg = parsed.documentElement;
      svg.setAttribute("role", "group");
      svg.setAttribute("aria-label", "Mapa interactivo de Nueva Planta");
      const namespace = "http://www.w3.org/2000/svg";
      const connectorGroup = document.createElementNS(namespace, "g");
      connectorGroup.setAttribute("class", "np-peace-connectors");
      connectorGroup.setAttribute("aria-hidden", "true");
      const definitions = document.createElementNS(namespace, "defs");
      const arrowhead = document.createElementNS(namespace, "marker");
      arrowhead.setAttribute("id", "np-peace-arrowhead");
      arrowhead.setAttribute("viewBox", "0 0 10 10");
      arrowhead.setAttribute("refX", "9");
      arrowhead.setAttribute("refY", "5");
      arrowhead.setAttribute("markerWidth", "7");
      arrowhead.setAttribute("markerHeight", "7");
      arrowhead.setAttribute("orient", "auto");
      const arrowShape = document.createElementNS(namespace, "path");
      arrowShape.setAttribute("d", "M0 0 10 5 0 10z");
      arrowShape.setAttribute("fill", "#c20e18");
      arrowhead.append(arrowShape);
      definitions.append(arrowhead);
      const gibraltarArrow = document.createElementNS(namespace, "path");
      const menorcaArrow = document.createElementNS(namespace, "path");
      gibraltarArrow.setAttribute("class", "np-peace-arrow");
      menorcaArrow.setAttribute("class", "np-peace-arrow");
      gibraltarArrow.setAttribute("marker-end", "url(#np-peace-arrowhead)");
      menorcaArrow.setAttribute("marker-end", "url(#np-peace-arrowhead)");
      connectorGroup.append(gibraltarArrow, menorcaArrow);
      svg.append(definitions, connectorGroup);
      peaceArrows = { gibraltar: gibraltarArrow, menorca: menorcaArrow };
      stage.replaceChildren(svg, peaceCallout);
      window.addEventListener("resize", updatePeaceArrows, { passive: true });
      svg.querySelectorAll("[data-territory]").forEach((element) => {
        const id = element.dataset.territory;
        element.setAttribute("tabindex", "0");
        element.setAttribute("role", "button");
        element.setAttribute("aria-label", territories[id].name);
        element.setAttribute("aria-controls", "np-info");
        element.addEventListener("click", () => { if (!dragged) select(id); });
        element.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            select(id);
          }
        });
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.territory = id;
        button.textContent = territories[id].name;
        button.setAttribute("aria-controls", "np-info");
        button.addEventListener("click", () => select(id));
        regions.append(button);
      });
      modeButtons.forEach((button) => button.addEventListener("click", () => {
        mode = button.dataset.npMode;
        paint();
      }));
      root.querySelector("[data-np-zoom=in]").addEventListener("click", () => setZoom(zoom * 1.25));
      root.querySelector("[data-np-zoom=out]").addEventListener("click", () => setZoom(zoom / 1.25));
      root.querySelector("[data-np-zoom=reset]").addEventListener("click", () => {
        view = { x: 0, y: 0 };
        zoom = 1;
        updateView();
      });
      svg.addEventListener("wheel", (event) => {
        if (!event.ctrlKey) return;
        event.preventDefault();
        const rect = svg.getBoundingClientRect();
        setZoom(zoom * (event.deltaY < 0 ? 1.1 : 1 / 1.1), {
          x: (event.clientX - rect.left) / rect.width,
          y: (event.clientY - rect.top) / rect.height,
        });
      }, { passive: false });
      svg.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        if (!pointers.size) dragged = false;
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
        beginGesture();
      });
      svg.addEventListener("pointermove", (event) => {
        if (!pointers.has(event.pointerId)) return;
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
        const points = [...pointers.values()];
        const rect = svg.getBoundingClientRect();
        const midpoint = (values, coordinate) => values.reduce((sum, point) => sum + point[coordinate], 0) / values.length;
        const dx = midpoint(points, "x") - midpoint(gesture.points, "x");
        const dy = midpoint(points, "y") - midpoint(gesture.points, "y");
        if (Math.hypot(dx, dy) > 5 || points.length > 1) {
          dragged = true;
          svg.setPointerCapture(event.pointerId);
        }
        if (points.length === 2 && gesture.points.length === 2) {
          const initial = distance(...gesture.points);
          if (!initial) return;
          const next = Math.max(1, Math.min(4, gesture.zoom * distance(...points) / initial));
          const center = {
            x: ((gesture.points[0].x + gesture.points[1].x) / 2 - rect.left) / rect.width,
            y: ((gesture.points[0].y + gesture.points[1].y) / 2 - rect.top) / rect.height,
          };
          zoom = next;
          view.x = gesture.view.x + center.x * (800 / gesture.zoom - 800 / zoom) - dx * 800 / zoom / rect.width;
          view.y = gesture.view.y + center.y * (560 / gesture.zoom - 560 / zoom) - dy * 560 / zoom / rect.height;
        } else if (zoom > 1) {
          view.x = gesture.view.x - dx * 800 / zoom / rect.width;
          view.y = gesture.view.y - dy * 560 / zoom / rect.height;
        }
        if (zoom === 1) view = { x: 0, y: 0 };
        updateView();
      });
      const endPointer = (event) => {
        pointers.delete(event.pointerId);
        if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
        if (pointers.size) beginGesture();
      };
      svg.addEventListener("pointerup", endPointer);
      svg.addEventListener("pointercancel", endPointer);
      svg.addEventListener("pointerleave", (event) => {
        if (!svg.hasPointerCapture(event.pointerId)) endPointer(event);
      });
      controls.hidden = false;
      regions.hidden = false;
      info.hidden = false;
      paint();
      updateView();
    } catch (error) {
      const message = root.querySelector(".np-error");
      message.textContent = `No se pudo activar el mapa interactivo (${error.message}). Puedes consultar el esquema y el resumen histórico de debajo. Recarga la página para volver a intentarlo.`;
      message.hidden = false;
    }
  };
  const historicalSummary = root.querySelector("details");
  let summaryWasOpen = false;
  window.addEventListener("beforeprint", () => {
    summaryWasOpen = historicalSummary.open;
    historicalSummary.open = true;
    if (svg) {
      svg.setAttribute("viewBox", "0 0 800 560");
      updatePeaceArrows();
    }
  });
  window.addEventListener("afterprint", () => {
    historicalSummary.open = summaryWasOpen;
    if (svg) updateView();
  });
  load();
})();
