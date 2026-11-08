(() => {
  const root = document.querySelector("#organizacion-borbonica");
  if (!root) return;
  const buttons = [...root.querySelectorAll("[data-ob-mode]")];
  const views = [...root.querySelectorAll(".ob-view")];
  const status = root.querySelector(".ob-status");
  const definitions = {
    "Rey y sistema polisinodial": ["Forma de gobierno de la Monarquía Hispánica basada en múltiples consejos que asesoraban al rey. En el bloque 3 se explica con más detalle, con ejemplos como el Consejo de Indias y el gobierno de Felipe II.", false],
    "Rey y secretarías de Estado y del Despacho": ["Los secretarios de despacho se encargaban de los grandes asuntos del gobierno: Estado, Guerra, Gracia y Justicia, Marina e Indias, y Hacienda.", false],
    "Consejos y Cortes": ["Los consejos asesoraban al monarca; las Cortes eran asambleas de representación estamental, no parlamentos democráticos. Nueva Planta suprimió las instituciones propias de los territorios afectados.", true],
    "Coordinación del gobierno": ["La Junta Suprema de Estado era una reunión formal y regular de los secretarios de despacho para coordinar el gobierno, antecedente del Consejo de Ministros.", false],
    "Virreinatos peninsulares": ["Territorios en los que un virrey representaba al monarca y ejercía funciones de gobierno. Navarra conservó esta institución bajo los Borbones.", true],
    "Virreinatos italianos": ["Territorios italianos de la monarquía gobernados por un virrey, representante del rey. Nápoles, Sicilia y Cerdeña contaron con esta forma de gobierno.", true],
    "Virreinatos americanos": ["Grandes demarcaciones americanas gobernadas por un virrey en nombre del monarca. En el bloque 3 se explican con más detalle, con ejemplos como Nueva España y Perú y su administración local basada en cabildos.", true],
    "Corregimientos y municipios": ["El corregimiento era una demarcación bajo un corregidor, representante de la autoridad real. Los concejos o cabildos eran órganos de gobierno local.", true],
    "Corregimientos": ["Demarcaciones gobernadas por corregidores, representantes del rey con funciones de gobierno y justicia local. El modelo castellano se extendió a los territorios reorganizados por Nueva Planta.", true],
    "Capitanías generales": ["Demarcaciones encabezadas por capitanes generales, con poder militar y funciones de gobierno. Sustituyeron a los virreinatos en los territorios reorganizados por Nueva Planta.", true],
    "Intendencias": ["Demarcaciones administradas por intendentes, agentes del poder real con funciones fiscales, económicas y de abastecimiento militar.", true],
    "Chancillerías": ["Tribunales superiores de justicia de la Corona de Castilla.", true],
    "Audiencias": ["Tribunales superiores de justicia con jurisdicción sobre un territorio. En América también participaron en el gobierno.", true],
    "Audiencias y cabildos": ["Las audiencias eran tribunales superiores de justicia; los cabildos gobernaban las ciudades.", true],
    "Comercio americano": ["La Casa de Contratación administraba el tráfico de viajeros y comerciantes con América y organizaba el comercio y la navegación. En el bloque 3 se explica con más detalle, con ejemplos como el monopolio comercial del puerto de Sevilla.", false],
  };
  views.forEach((view) => {
    const before = view.dataset.obView === "before";
    view.querySelectorAll("details").forEach((detail) => {
      const summary = detail.querySelector("summary");
      const label = summary.textContent.trim();
      const entry = definitions[label];
      if (!entry) throw new Error(`Definición del esquema no disponible: ${label}`);
      let [text, supplement] = entry;
      if (before && label === "Chancillerías") {
        text += " En el bloque 3 se explican con más detalle, con ejemplos como la Real Chancillería de Granada y la administración judicial de Felipe II.";
      }
      if (before && label === "Audiencias y cabildos") {
        text += " En el bloque 3 se explican con más detalle los cabildos, como órganos de administración local de Nueva España y Perú.";
      }
      if (!before && label === "Virreinatos americanos") {
        text = "Grandes demarcaciones gobernadas por virreyes en nombre del rey. Bajo los Borbones continuaron Nueva España y Perú y se añadieron Nueva Granada y el Río de la Plata.";
      }
      if (!before && label === "Comercio americano") {
        text = "La Casa de Contratación centralizaba el comercio y la navegación con América. Pasó de Sevilla a Cádiz en 1717; los decretos de libre comercio de 1765 y 1778 abrieron el tráfico a más puertos.";
        supplement = true;
      }
      const wrapper = document.createElement("div");
      wrapper.className = "ob-item";
      const info = document.createElement("button");
      info.type = "button";
      info.className = "ob-info";
      info.textContent = "i";
      info.setAttribute("aria-label", `Definición: ${label}`);
      info.dataset.noteTitle = label;
      info.dataset.noteText = text;
      info.dataset.noteSource = before ? "bloque-3.html" : "bloque-4.html#bloque-4-seccion-k963oqg9s413";
      info.dataset.noteSourceLabel = `Bloque ${before ? 3 : 4} · ${supplement ? "contexto complementario a los apuntes" : "definición adaptada de los apuntes"}`;
      detail.before(wrapper);
      wrapper.append(detail, info);
    });
  });
  function select(mode) {
    root.querySelector('.ob-info[aria-expanded="true"]')?.click();
    buttons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.obMode === mode));
    });
    views.forEach((view) => { view.hidden = view.dataset.obView !== mode; });
    status.textContent = mode === "before"
      ? "Antes · Monarquía Hispánica de los Austrias (siglos XVI–XVII)"
      : "Después · Reformas borbónicas a lo largo del siglo XVIII";
  }
  buttons.forEach((button) => button.addEventListener("click", () => select(button.dataset.obMode)));
  root.querySelector(".ob-controls").hidden = false;
  select("before");
  let printOpened = [];
  window.addEventListener("beforeprint", () => {
    printOpened = [...root.querySelectorAll(".ob-view:not([hidden]) details:not([open])")];
    printOpened.forEach((detail) => { detail.open = true; });
  });
  window.addEventListener("afterprint", () => {
    printOpened.forEach((detail) => { detail.open = false; });
    printOpened = [];
  });
})();
