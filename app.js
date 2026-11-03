const search = document.querySelector("#search");
const formatFilter = document.querySelector("#format-filter");
const groupFilter = document.querySelector("#group-filter");
const cards = [...document.querySelectorAll(".card")];
const count = document.querySelector("#results-count");
const empty = document.querySelector("#empty");

const topicSets = [
  [
    { label: "711 y monarquía visigoda", terms: ["711", "precedio a la invasion", "monarquia visigoda", "invasion musulmana"] },
    { label: "Romanización", terms: ["romaniz"] },
    { label: "Pueblos prerromanos", terms: ["iberos", "culturas autoctonas"] },
    { label: "Reino visigodo", terms: ["imperio romano de occidente"] },
  ],
  [
    { label: "Reconquista", terms: ["reconquista", "nucleo politico relevante"] },
    { label: "Al-Ándalus", terms: ["al andalus", "andalus"] },
    { label: "Califato de Córdoba", terms: ["califato", "epoca califal", "califa omeya", "titulo de califa"] },
    { label: "Siglo X", terms: ["siglo x"] },
    { label: "Repoblación", terms: ["repoblacion"] },
    { label: "Reinos cristianos", terms: ["reinos cristianos", "resistencia cristiana", "reino surgido a finales"] },
    { label: "Sociedad andalusí", terms: ["minoria cristiana", "sociedad hispano musulmana"] },
    { label: "Mozárabes", terms: ["minoria cristiana"] },
    { label: "La Mesta", terms: ["asociacion de ganaderos", "ganaderos", "mesta"] },
    { label: "Escuela de Traductores", terms: ["escuela de traductores"] },
    { label: "Invasión musulmana", terms: ["invasion musulmana", "territorio conquistado", "dominacion musulmana", "invasion de la peninsula"] },
    { label: "Cortes medievales", terms: ["cortes medievales"] },
    { label: "Mudéjares y mozárabes", terms: ["mozarabe", "mudejar"] },
    { label: "Reino nazarí", terms: ["nazari"] },
  ],
  [
    { label: "Reyes Católicos", terms: ["reyes catolicos", "union dinastica", "monarcas a finales del siglo xv", "unidad religiosa"] },
    { label: "Carlos V y los Austrias", terms: ["casa de austria", "fue tambien emperador", "austrias mayores", "comunidades", "germanias", "interior de carlos i"] },
    { label: "Expansión y política exterior", terms: ["expansion territorial", "politica exterior", "territorios se asentaba", "hegemonia espanola"] },
    { label: "Gobierno de los validos", terms: ["valido", "figura politica", "gobierno de los validos"] },
    { label: "Granada y la Reconquista", terms: ["toma de granada", "final de la reconquista"] },
    { label: "Felipe II y Lepanto", terms: ["batalla de lepanto", "monarquia hispanica en ese reinado", "armada invencible", "carlos i y felipe ii", "dos monarcas de mas amplio reinado"] },
    { label: "Monarquía autoritaria", terms: ["monarquia autoritaria", "apelativo"] },
    { label: "Moriscos y expulsiones", terms: ["expulsad", "moriscos", "1609", "alpujarras"] },
    { label: "Conflictos con los Austrias", terms: ["dinastia de los austria", "conflicto armado"] },
    { label: "Expansión atlántica", terms: ["expansion atlantica"] },
  ],
  [
    { label: "Guerra de Sucesión", terms: ["guerra de sucesion", "borbones y austrias", "tratado", "iniciaron su reinado"] },
    { label: "Dinastía borbónica", terms: ["casa de borbon", "nueva dinastia", "dinastia borbonica"] },
    { label: "Decretos de Nueva Planta", terms: ["nueva planta", "fueros de los territorios", "abolieron los fueros"] },
    { label: "Despotismo ilustrado", terms: ["despotismo ilustrado"] },
    { label: "Carlos III y Esquilache", terms: ["motin de esquilache"] },
    { label: "Reformas y Reales Fábricas", terms: ["reales fabricas", "reformas en la administracion", "reformas economicas", "agricultura"] },
    { label: "Siglo de las Luces", terms: ["siglo de las luces", "ilustrad"] },
    { label: "Carlos III", terms: ["carlos iii"] },
    { label: "Utrecht y Rastadt", terms: ["utrecht", "tratado", "tratados"] },
  ],
];

function normalizeText(text) {
  return text.toLocaleLowerCase("es").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function renderTopicCloud(block, blockIndex) {
  const cloud = block.querySelector(".topic-cloud");
  const status = block.querySelector(".topic-status");
  const questions = [...block.querySelectorAll(".question-list li")];
  const topics = topicSets[blockIndex]
    .map((topic) => ({
      ...topic,
      matches: questions.filter((question) => {
        const text = normalizeText(question.textContent);
        return topic.terms.some((term) => text.includes(term));
      }),
    }))
    .filter((topic) => topic.matches.length > 0)
    .sort((a, b) => b.matches.length - a.matches.length || a.label.localeCompare(b.label, "es"));

  const clearButton = document.createElement("button");
  clearButton.className = "topic-bubble topic-all";
  clearButton.type = "button";
  clearButton.setAttribute("aria-pressed", "true");
  clearButton.innerHTML = `<span>Todos</span><small>${questions.length}</small>`;
  clearButton.addEventListener("click", () => selectTopic(null));
  cloud.append(clearButton);

  for (const topic of topics) {
    const bubble = document.createElement("button");
    bubble.className = "topic-bubble";
    bubble.type = "button";
    bubble.dataset.topic = topic.label;
    bubble.style.setProperty("--bubble-size", `${Math.min(112, 58 + topic.matches.length * 9)}px`);
    bubble.setAttribute("aria-pressed", "false");
    bubble.setAttribute("aria-label", `${topic.label}: ${topic.matches.length} ${topic.matches.length === 1 ? "pregunta relacionada" : "preguntas relacionadas"}`);
    bubble.innerHTML = `<span>${topic.label}</span><small>${topic.matches.length}</small>`;
    bubble.addEventListener("click", () => {
      selectTopic(bubble.getAttribute("aria-pressed") === "true" ? null : topic.label);
    });
    cloud.append(bubble);
  }

  function selectTopic(label) {
    for (const question of questions) {
      const text = normalizeText(question.textContent);
      const topic = topics.find((item) => item.label === label);
      question.hidden = Boolean(topic && !topic.terms.some((term) => text.includes(term)));
    }

    for (const bubble of cloud.querySelectorAll(".topic-bubble")) {
      bubble.setAttribute("aria-pressed", String(
        bubble.classList.contains("topic-all") ? label === null : bubble.dataset.topic === label,
      ));
    }

    const visibleCount = questions.filter((question) => !question.hidden).length;
    status.textContent = label
      ? `${visibleCount} ${visibleCount === 1 ? "pregunta relacionada" : "preguntas relacionadas"} con «${label}».`
      : `${questions.length} ${questions.length === 1 ? "pregunta marcada" : "preguntas marcadas"} en este bloque.`;
  }

  selectTopic(null);
}

document.querySelectorAll(".block").forEach((block, index) => {
  block.addEventListener("toggle", () => {
    if (block.open && !block.dataset.cloudReady) {
      renderTopicCloud(block, index);
      block.dataset.cloudReady = "true";
    }
  });
});

function updateResults() {
  const query = search.value.trim().toLocaleLowerCase("es");
  let visible = 0;

  for (const card of cards) {
    const textMatches = !query
      || card.textContent.toLocaleLowerCase("es").includes(query)
      || card.dataset.search.includes(query);
    const formatMatches = formatFilter.value === "all" || card.dataset.format === formatFilter.value;
    const groups = card.dataset.groups.split(" ").filter(Boolean);
    const groupMatches = groupFilter.value === "all" || groups.includes(groupFilter.value);
    card.hidden = !(textMatches && formatMatches && groupMatches);
    if (!card.hidden) visible += 1;
  }

  count.textContent = `${visible} ${visible === 1 ? "contenido" : "contenidos"}`;
  empty.hidden = visible !== 0;
}

search.addEventListener("input", updateResults);
formatFilter.addEventListener("change", updateResults);
groupFilter.addEventListener("change", updateResults);
document.querySelector("#reset").addEventListener("click", () => {
  search.value = "";
  formatFilter.value = "all";
  groupFilter.value = "all";
  updateResults();
  search.focus();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    search.focus();
  }
});

updateResults();

const fan = document.querySelector("#fan");
const fanToggle = document.querySelector("#fan-toggle");
const fanPages = [...document.querySelectorAll(".fan-page")];

function setFan(open) {
  fan.dataset.open = String(open);
  fanToggle.setAttribute("aria-expanded", String(open));
  fanToggle.classList.toggle("is-open", open);
  fanToggle.querySelector(".ft-icon").textContent = open ? "×" : "+";
  fanToggle.querySelector(".ft-text b").textContent = open ? "Cerrar" : "Abrir";
  if (!open) fanPages.forEach((page) => page.setAttribute("aria-pressed", "false"));
}

fanToggle.addEventListener("click", () => setFan(fan.dataset.open !== "true"));
fanPages.forEach((page) => page.addEventListener("click", () => {
  if (fan.dataset.open !== "true") return setFan(true);
  const wasActive = page.getAttribute("aria-pressed") === "true";
  fanPages.forEach((item) => item.setAttribute("aria-pressed", "false"));
  page.setAttribute("aria-pressed", String(!wasActive));
}));
new IntersectionObserver((entries, observer) => {
  if (entries.some((entry) => entry.isIntersecting)) {
    setFan(true);
    observer.disconnect();
  }
}, { threshold: 0.45 }).observe(fan);

const toTop = document.querySelector(".to-top");
if (toTop) {
  const toggleToTop = () => { toTop.hidden = window.scrollY < 400; };
  window.addEventListener("scroll", toggleToTop, { passive: true });
  toggleToTop();
}

const phaseNav = document.querySelector(".phase-nav");
if (phaseNav) {
  const phases = [
    { id: "alineacion", name: "Alineación 3-4-3" },
    { id: "bloques-cuestiones", name: "Preguntas cortas" },
    { id: "generador", name: "Generador" },
    { id: "fuentes", name: "Fuentes" },
  ];
  const nextBtn = phaseNav.querySelector(".next-phase");
  const prevBtn = phaseNav.querySelector(".prev-phase");
  const stepEl = nextBtn.querySelector(".np-step");
  const nameEl = nextBtn.querySelector(".np-name");
  let current = -1;
  const topOf = (id) => document.getElementById(id).getBoundingClientRect().top + window.scrollY;
  const go = (i) => document.getElementById(phases[i].id).scrollIntoView({ behavior: "smooth", block: "start" });
  const sync = () => {
    phaseNav.hidden = false;
    const y = window.scrollY + window.innerHeight * 0.4;
    current = -1;
    let best = -Infinity;
    phases.forEach((p, i) => { const t = topOf(p.id); if (t <= y && t > best) { best = t; current = i; } });
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) current = phases.length - 1;
    const next = (current + 1) % phases.length;
    stepEl.textContent = `Fase ${next + 1}`;
    nameEl.textContent = phases[next].name;
    prevBtn.disabled = current <= 0;
  };
  nextBtn.addEventListener("click", () => go((current + 1) % phases.length));
  prevBtn.addEventListener("click", () => { if (current > 0) go(current - 1); });
  window.addEventListener("scroll", sync, { passive: true });
  window.addEventListener("resize", sync);
  sync();
}

const themeToggle = document.getElementById("theme-toggle");
if (themeToggle) {
  const root = document.documentElement;
  const paintTheme = () => {
    const dark = root.dataset.theme === "dark";
    themeToggle.setAttribute("aria-pressed", String(dark));
    themeToggle.setAttribute("aria-label", dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
  };
  themeToggle.addEventListener("click", () => {
    const dark = root.dataset.theme !== "dark";
    if (dark) root.dataset.theme = "dark"; else delete root.dataset.theme;
    try { localStorage.setItem("pau-he.theme", dark ? "dark" : "light"); } catch (e) {}
    paintTheme();
  });
  paintTheme();
}
