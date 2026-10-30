const search = document.querySelector("#search");
const formatFilter = document.querySelector("#format-filter");
const groupFilter = document.querySelector("#group-filter");
const cards = [...document.querySelectorAll(".card")];
const count = document.querySelector("#results-count");
const empty = document.querySelector("#empty");

const topicSets = [
  [
    { label: "711 y monarquía visigoda", terms: ["711", "monarquia visigoda", "invasion musulmana"] },
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
    { label: "La Mesta", terms: ["asociacion de ganaderos", "mesta"] },
    { label: "Escuela de Traductores", terms: ["escuela de traductores"] },
  ],
  [
    { label: "Reyes Católicos", terms: ["reyes catolicos", "union dinastica", "monarcas a finales del siglo xv", "unidad religiosa"] },
    { label: "Carlos V y los Austrias", terms: ["casa de austria", "fue tambien emperador", "austrias mayores", "comunidades", "germanias"] },
    { label: "Expansión y política exterior", terms: ["expansion territorial", "politica exterior", "territorios se asentaba", "hegemonia espanola"] },
    { label: "Gobierno de los validos", terms: ["valido", "gobierno de los validos"] },
    { label: "Granada y la Reconquista", terms: ["toma de granada", "final de la reconquista"] },
    { label: "Felipe II y Lepanto", terms: ["batalla de lepanto", "monarquia hispanica en ese reinado"] },
  ],
  [
    { label: "Guerra de Sucesión", terms: ["guerra de sucesion", "borbones y austrias", "tratado"] },
    { label: "Dinastía borbónica", terms: ["casa de borbon", "nueva dinastia", "dinastia borbonica"] },
    { label: "Decretos de Nueva Planta", terms: ["nueva planta", "fueros de los territorios"] },
    { label: "Despotismo ilustrado", terms: ["despotismo ilustrado"] },
    { label: "Carlos III y Esquilache", terms: ["motin de esquilache"] },
    { label: "Reformas y Reales Fábricas", terms: ["reales fabricas", "reformas en la administracion", "reformas economicas"] },
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
