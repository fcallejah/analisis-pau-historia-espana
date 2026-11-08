const search = document.querySelector("#search");
const formatFilter = document.querySelector("#format-filter");
const groupFilter = document.querySelector("#group-filter");
const cards = [...document.querySelectorAll(".card")];
const count = document.querySelector("#results-count");
const empty = document.querySelector("#empty");

const topicSets = [
  [
    { label: "711 y monarquía visigoda", terms: ["711", "precedio a la invasion", "monarquia visigoda", "invasion musulmana"] },
    { label: "romanización", terms: ["romaniz"] },
    { label: "pueblos prerromanos", terms: ["iberos", "culturas autoctonas"] },
    { label: "reino visigodo", terms: ["imperio romano de occidente"] },
  ],
  [
    { label: '"Reconquista"', terms: ["reconquista", "nucleo politico relevante"] },
    { label: "al-Ándalus", terms: ["al andalus", "andalus"] },
    { label: "califato de Córdoba", terms: ["califato", "epoca califal", "califa omeya", "titulo de califa"] },
    { label: "siglo X", terms: ["siglo x"] },
    { label: "repoblación", terms: ["repoblacion"] },
    { label: "reinos cristianos", terms: ["reinos cristianos", "resistencia cristiana", "reino surgido a finales"] },
    { label: "sociedad andalusí", terms: ["minoria cristiana", "sociedad hispano musulmana"] },
    { label: "mozárabes", terms: ["minoria cristiana"] },
    { label: "la Mesta", terms: ["asociacion de ganaderos", "ganaderos", "mesta"] },
    { label: "Escuela de Traductores", terms: ["escuela de traductores"] },
    { label: "invasión musulmana", terms: ["invasion musulmana", "territorio conquistado", "dominacion musulmana", "invasion de la peninsula"] },
    { label: "cortes medievales", terms: ["cortes medievales"] },
    { label: "mudéjares y mozárabes", terms: ["mozarabe", "mudejar"] },
    { label: "reino nazarí", terms: ["nazari"] },
  ],
  [
    { label: "Reyes Católicos", terms: ["reyes catolicos", "union dinastica", "monarcas a finales del siglo xv", "unidad religiosa"] },
    { label: "Carlos V y los Austrias", terms: ["casa de austria", "fue tambien emperador", "austrias mayores", "comunidades", "germanias", "interior de carlos i"] },
    { label: "expansión y política exterior", terms: ["expansion territorial", "politica exterior", "territorios se asentaba", "hegemonia espanola"] },
    { label: "gobierno de los validos", terms: ["valido", "figura politica", "gobierno de los validos"] },
    { label: 'Granada y la "Reconquista"', terms: ["toma de granada", "final de la reconquista"] },
    { label: "Felipe II y Lepanto", terms: ["batalla de lepanto", "monarquia hispanica en ese reinado", "armada invencible", "carlos i y felipe ii", "dos monarcas de mas amplio reinado"] },
    { label: "monarquía autoritaria", terms: ["monarquia autoritaria", "apelativo"] },
    { label: "moriscos y expulsiones", terms: ["expulsad", "moriscos", "1609", "alpujarras"] },
    { label: "conflictos con los Austrias", terms: ["dinastia de los austria", "conflicto armado"] },
    { label: "expansión atlántica", terms: ["expansion atlantica"] },
  ],
  [
    { label: "guerra de sucesión", terms: ["guerra de sucesion", "borbones y austrias", "tratado", "iniciaron su reinado"] },
    { label: "dinastía borbónica", terms: ["casa de borbon", "nueva dinastia", "dinastia borbonica"] },
    { label: "Decretos de Nueva Planta", terms: ["nueva planta", "fueros de los territorios", "abolieron los fueros"] },
    { label: "despotismo ilustrado", terms: ["despotismo ilustrado"] },
    { label: "Carlos III y Esquilache", terms: ["motin de esquilache"] },
    { label: "reformas y reales fábricas", terms: ["reales fabricas", "reformas en la administracion", "reformas economicas", "agricultura"] },
    { label: "Siglo de las Luces", terms: ["siglo de las luces", "ilustrad"] },
    { label: "Carlos III", terms: ["carlos iii"] },
    { label: "Utrecht-Rastadt *", terms: ["utrecht", "tratado", "tratados"] },
  ],
];

function normalizeText(text) {
  return text.toLocaleLowerCase("es").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function examReferences(question) {
  if (question.dataset.exams) return JSON.parse(question.dataset.exams);
  return question.querySelector("small").textContent.split(";").map((exam) => exam.trim());
}

function uniqueExams(questions) {
  return new Set(questions.flatMap(examReferences)).size;
}

function appendErratum(container, text) {
  if (!text.includes("Fernando V de Aragón")) return;
  const note = document.createElement("p");
  note.className = "question-erratum";
  note.textContent = "* Errata del original (2021 · Reserva ordinaria): Fernando II de Aragón, también llamado Fernando V de Castilla, no Fernando V de Aragón.";
  const marker = document.createElement("sup");
  marker.className = "question-erratum";
  marker.textContent = "*";
  container.querySelector("p").append(marker);
  container.append(note);
}

function appendSpellingNote(container, text) {
  if (!text.includes("Rastadt")) return;
  const marker = document.createElement("sup");
  marker.className = "question-spelling";
  marker.textContent = "*";
  container.querySelector("p").append(marker);
  const note = document.createElement("p");
  note.className = "question-spelling";
  note.append(document.createTextNode('* Nota de grafía: los exámenes de PAU aquí recogidos emplean "Rastadt", forma tradicional que conservamos en los enunciados. También es válida la forma "Rastatt", grafía actual de la ciudad alemana donde se firmó el tratado de 1714 y que recomendamos usar en esta web. Puedes referirte a los tratados de Utrecht y Rastatt. '));
  const link = document.createElement("a");
  link.href = "https://www.schloss-rastatt.de/en/interesting-amusing/collections/the-treaty-of-rastatt";
  link.textContent = "Información del Palacio de Rastatt";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  note.append(link, document.createTextNode(". Es una recomendación de uso, no una errata del examen."));
  container.append(note);
}

function questionKey(text) {
  return normalizeText(text).replace(/[^\p{L}\p{N}]/gu, "");
}

function examPill(reference, index) {
  const pill = document.createElement("span");
  pill.className = "exam-pill";
  pill.dataset.frequency = String(Math.min(index, 4));
  pill.title = `Aparición ${index + 1} registrada en el corpus; no indica probabilidad futura`;
  pill.textContent = reference;
  return pill;
}

const questionExamMap = new Map();
document.querySelectorAll(".question-list li").forEach((question) => {
  const meta = question.querySelector("small");
  const references = examReferences(question);
  questionExamMap.set(questionKey(question.querySelector("p").textContent), references);
  meta.replaceChildren(...references.map(examPill));
  // Keep the source text available for counting even after decorating it.
  question.dataset.exams = JSON.stringify(references);
  appendErratum(question, question.querySelector("p").textContent);
  appendSpellingNote(question, question.querySelector("p").textContent);
});

document.querySelectorAll(".qt-blocks li").forEach((item, index) => {
  const questions = [...document.querySelectorAll(".block")[index].querySelectorAll(".question-list li")];
  item.querySelector("b").textContent = questions.length;
  item.setAttribute("aria-label", `Bloque ${index + 1}: ${questions.length} preguntas recopiladas`);
});

function renderTopicCloud(block, blockIndex) {
  const cloud = block.querySelector(".topic-cloud");
  const status = block.querySelector(".topic-status");
  const questions = [...block.querySelectorAll(".question-list li")];
  const topics = topicSets[blockIndex]
    .map((topic) => ({
      ...topic,
      matches: questions.filter((question) => {
        const text = normalizeText(question.querySelector("p").textContent);
        return topic.terms.some((term) => text.includes(term));
      }),
    }))
    .filter((topic) => topic.matches.length > 0)
    .map((topic) => ({ ...topic, exams: uniqueExams(topic.matches) }))
    .sort((a, b) => b.exams - a.exams || b.matches.length - a.matches.length || a.label.localeCompare(b.label, "es"));

  const clearButton = document.createElement("button");
  clearButton.className = "topic-bubble topic-all";
  clearButton.type = "button";
  clearButton.setAttribute("aria-pressed", "true");
  clearButton.innerHTML = `<span>Todos</span><small>${questions.length} ${questions.length === 1 ? "pregunta" : "preguntas"}</small>`;
  clearButton.addEventListener("click", () => selectTopic(null));
  cloud.append(clearButton);

  for (const topic of topics) {
    const bubble = document.createElement("button");
    bubble.className = "topic-bubble";
    bubble.type = "button";
    bubble.dataset.topic = topic.label;
    bubble.style.setProperty("--bubble-size", `${Math.min(150, 112 + topic.exams * 2)}px`);
    bubble.setAttribute("aria-pressed", "false");
    const examLabel = `${topic.exams} ${topic.exams === 1 ? "examen" : "exámenes"}`;
    bubble.setAttribute("aria-label", `${topic.label}: ${examLabel} del corpus`);
    bubble.innerHTML = `<span>${topic.label}</span><small>${examLabel}</small>`;
    bubble.addEventListener("click", () => {
      selectTopic(bubble.getAttribute("aria-pressed") === "true" ? null : topic.label);
    });
    cloud.append(bubble);
  }

  function selectTopic(label) {
    for (const question of questions) {
      const text = normalizeText(question.querySelector("p").textContent);
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
      ? `${visibleCount} preguntas distintas con "${label}", presentes en ${uniqueExams(questions.filter((question) => !question.hidden))} exámenes del corpus. Cada convocatoria se cuenta una sola vez; no es una probabilidad.`
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
    const formatMatches = formatFilter.value === "all" || card.dataset.format.split(" ").includes(formatFilter.value);
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

const apTrack = document.querySelector("#apuntes-track");
const apCards = [...apTrack.querySelectorAll(".apunte")];
const apChips = [...document.querySelectorAll(".apunte-chip")];
const apNav = [...document.querySelectorAll(".apuntes-nav")];
const apControls = document.querySelector(".apuntes-controls");
const apReduce = window.matchMedia("(prefers-reduced-motion: reduce)");
const apGap = document.createElement("li");
apGap.className = "apuntes-loop-gap";
apGap.setAttribute("aria-hidden", "true");
apGap.inert = true;
apTrack.append(apGap);
const apCopies = apCards.map((card) => {
  const copy = card.cloneNode(true);
  copy.classList.replace("apunte", "apunte-loop");
  copy.removeAttribute("aria-label");
  copy.setAttribute("aria-hidden", "true");
  copy.inert = true;
  for (const el of [copy, ...copy.querySelectorAll("*")]) {
    el.removeAttribute("id");
    el.removeAttribute("data-n");
  }
  apTrack.append(copy);
  return copy;
});
let apWrapping = false;
let apNormalizing = false;
const apLeft = (card) => card.offsetLeft - apCards[0].offsetLeft;
function apNormalize() {
  if (apNormalizing || apTrack.scrollLeft < apLeft(apCopies[0]) - 1) return;
  apNormalizing = true;
  apTrack.classList.add("is-looping");
  // The copies and canonical cards have identical geometry: this jump is not animated.
  const shift = apLeft(apCopies[0]);
  if (apDrag) apDrag.left -= shift;
  apTrack.scrollTo({ left: apTrack.scrollLeft - shift, behavior: "instant" });
  apWrapping = false;
  requestAnimationFrame(() => {
    apNormalizing = false;
    apTrack.classList.remove("is-looping");
    apSync();
  });
}
let apActive = -1;
const apDots = apCards.map((card, i) => {
  const dot = document.createElement("button");
  dot.type = "button";
  dot.className = "note-dot";
  dot.setAttribute("aria-label", `Ir al bloque ${i + 1}${card.classList.contains("is-soon") ? " (próximamente)" : ""}`);
  dot.append(document.createElement("span"));
  document.querySelector("#apuntes-dots").append(dot);
  return dot;
});
const apGo = (i) => {
  apWrapping = false;
  apTrack.classList.remove("is-looping");
  apTrack.scrollTo({ left: apLeft(apCards[i]), behavior: apReduce.matches ? "instant" : "smooth" });
};
const apCurrent = () => {
  const i = apCards.findIndex((c) => apLeft(c) + c.offsetWidth / 2 > apTrack.scrollLeft + 1);
  return i < 0 ? apCards.length - 1 : i;
};
function apSync() {
  if (apNormalizing) return;
  if (apTrack.scrollLeft >= apLeft(apCopies[0]) - 1) {
    apNormalize();
    return;
  }
  const i = Math.max(0, apCurrent());
  try { localStorage.setItem("pau-apuntes-pos", String(i)); } catch {}
  apChips.forEach((c, k) => {
    if (k === i) c.setAttribute("aria-current", "true");
    else c.removeAttribute("aria-current");
  });
  apDots.forEach((dot, k) => {
    if (k === i) dot.setAttribute("aria-current", "true");
    else dot.removeAttribute("aria-current");
  });
  if (i !== apActive) {
    apActive = i;
    const fill = apDots[i].firstElementChild;
    fill.style.animation = "none";
    void fill.offsetWidth;
    fill.style.animation = "";
  }
  apNav[0].disabled = i === 0;
  apNav[1].disabled = i === apCards.length - 1;
}
apChips.forEach((c, k) => c.addEventListener("click", () => apGo(k)));
apDots.forEach((dot, k) => dot.addEventListener("click", () => apGo(k)));
apDots.forEach((dot) => dot.firstElementChild.addEventListener("animationend", () => {
  if (apReduce.matches || dot.getAttribute("aria-current") !== "true") return;
  if (apWrapping || apDrag) return;
  if (apActive === apCards.length - 1) {
    apWrapping = true;
    apTrack.classList.add("is-looping");
    apTrack.scrollTo({ left: apLeft(apCopies[0]), behavior: "smooth" });
  } else apGo(apActive + 1);
}));
const apMotion = () => {
  apControls.dataset.paused = String(apReduce.matches);
  if (apReduce.matches && apWrapping) apGo(apActive);
};
apReduce.addEventListener("change", apMotion);
apMotion();
apNav.forEach((b) => b.addEventListener("click", () => apGo(Math.min(apCards.length - 1, Math.max(0, apCurrent() + Number(b.dataset.dir))))));
apTrack.addEventListener("scroll", () => requestAnimationFrame(apSync), { passive: true });
let apDrag = null;
let apSuppressClick = false;
apTrack.addEventListener("pointerdown", (event) => {
  if (event.pointerType !== "mouse" || event.button !== 0) return;
  apSuppressClick = false;
  apDrag = { id: event.pointerId, x: event.clientX, left: apTrack.scrollLeft, moved: false };
});
apTrack.addEventListener("pointermove", (event) => {
  if (!apDrag || event.pointerId !== apDrag.id) return;
  const delta = event.clientX - apDrag.x;
  if (!apDrag.moved && Math.abs(delta) < 6) return;
  if (!apDrag.moved) {
    apDrag.moved = true;
    apTrack.classList.add("is-dragging");
    apTrack.setPointerCapture(event.pointerId);
  }
  event.preventDefault();
  apTrack.scrollLeft = apDrag.left - delta;
});
const apEndDrag = (event) => {
  if (!apDrag || event.pointerId !== apDrag.id) return;
  const moved = apDrag.moved;
  apDrag = null;
  apTrack.classList.remove("is-dragging");
  if (apTrack.hasPointerCapture(event.pointerId)) apTrack.releasePointerCapture(event.pointerId);
  if (moved) {
    apSuppressClick = true;
    apGo(Math.max(0, apCurrent()));
  }
};
apTrack.addEventListener("pointerup", apEndDrag);
apTrack.addEventListener("pointercancel", apEndDrag);
apTrack.addEventListener("lostpointercapture", apEndDrag);
apTrack.addEventListener("pointerleave", (event) => {
  if (apDrag && !apDrag.moved) apEndDrag(event);
});
apTrack.addEventListener("dragstart", (event) => event.preventDefault());
apTrack.addEventListener("click", (event) => {
  if (!apSuppressClick || event.detail === 0) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  apSuppressClick = false;
}, true);
window.addEventListener("resize", () => {
  if (apWrapping) {
    apTrack.scrollTo({ left: apLeft(apCopies[0]), behavior: "instant" });
    apNormalize();
  }
  apSync();
});
apTrack.addEventListener("keydown", (e) => {
  if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
  e.preventDefault();
  apGo(Math.min(apCards.length - 1, Math.max(0, apCurrent() + (e.key === "ArrowRight" ? 1 : -1))));
});
try {
  const saved = Number(localStorage.getItem("pau-apuntes-pos"));
  if (saved > 0 && saved < apCards.length) apTrack.scrollTo({ left: apCards[saved].offsetLeft - apCards[0].offsetLeft, behavior: "instant" });
} catch {}
apSync();

const apImgObserver = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (!e.isIntersecting) return;
  apImgObserver.unobserve(e.target);
  window.pauLoadImage(e.target);
  const copyIndex = apCopies.indexOf(e.target.closest(".apunte-loop"));
  if (copyIndex >= 0) window.pauLoadImage(apCards[copyIndex].querySelector(".apunte-img"));
}), { root: apTrack, rootMargin: "0px 300px" });
document.querySelectorAll(".apunte-img").forEach((box) => apImgObserver.observe(box));

apCards.forEach((card) => card.addEventListener("click", (event) => {
  if (event.target.closest("a, button")) return;
  card.querySelector(".apunte-open")?.click();
}));

document.querySelectorAll('a[href="#inicio"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    e.preventDefault();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    history.replaceState(null, "", location.pathname + location.search);
  });
});

const toTop = document.querySelector(".to-top");
if (toTop) {
  const toggleToTop = () => { toTop.hidden = window.scrollY < 400; };
  window.addEventListener("scroll", toggleToTop, { passive: true });
  toggleToTop();
}

const phaseNav = document.querySelector(".phase-nav");
if (phaseNav) {
  const phases = [
    { id: "apuntes", number: 0, name: "Apuntes completos" },
    { id: "bloques-cuestiones", number: 1, name: "Preguntas cortas" },
    { id: "generador", number: 3, name: "Generador preguntas cortas" },
    { id: "fuentes", number: 4, name: "Formato examen" },
  ];
  const nextBtn = phaseNav.querySelector(".next-phase");
  const prevBtn = phaseNav.querySelector(".prev-phase");
  const stepEl = nextBtn.querySelector(".np-step");
  const nameEl = nextBtn.querySelector(".np-name");
  let current = -1;
  const MARGIN = 28;
  const anchorOf = (id) => {
    const el = document.getElementById(id);
    if (id === "apuntes") return el.querySelector(".apuntes-title") || el;
    const sec = el.closest("section") || el;
    return sec.querySelector(".eyebrow") || el;
  };
  const topOf = (id) => anchorOf(id).getBoundingClientRect().top + window.scrollY - MARGIN;
  const go = (i) => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: Math.max(0, Math.min(topOf(phases[i].id), max)), behavior: reduce ? "auto" : "smooth" });
  };
  const sync = () => {
    phaseNav.hidden = false;
    const y = window.scrollY + 40;
    current = -1;
    let best = -Infinity;
    phases.forEach((p, i) => { const t = topOf(p.id); if (t <= y + 1 && t > best) { best = t; current = i; } });
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) current = phases.length - 1;
    const next = (current + 1) % phases.length;
    stepEl.textContent = `Fase ${phases[next].number}`;
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
    const apply = () => {
      if (dark) root.dataset.theme = "dark"; else delete root.dataset.theme;
      paintTheme();
    };
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const zoomed = window.visualViewport && window.visualViewport.scale > 1;
    if (document.startViewTransition && !calm && !zoomed) document.startViewTransition(apply); else apply();
    try { localStorage.setItem("pau-he.theme", dark ? "dark" : "light"); } catch (e) {}
  });
  paintTheme();
}

if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch((error) => {
      console.error("No se pudo activar el modo sin conexión de PAU Historia:", error);
    });
  });
}

// Fase aleatoria de las olas en cada carga
document.querySelectorAll(".hero-waves .wave").forEach((w) => {
  const d = parseFloat(getComputedStyle(w).animationDuration) || 22;
  w.style.animationDelay = `-${(Math.random() * d).toFixed(2)}s`;
});
