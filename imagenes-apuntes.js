(() => {
  const cache = (() => { try { return JSON.parse(localStorage.getItem("pau-apuntes-img") || "{}"); } catch { return {}; } })();
  const requests = new Map();
  async function resolve(box) {
    if (box.dataset.src) return { url: box.dataset.src, page: box.dataset.link || box.dataset.src };
    if (box.dataset.file) {
      const file = encodeURIComponent(box.dataset.file);
      return { url: `https://commons.wikimedia.org/wiki/Special:FilePath/${file}?width=500`, page: `https://commons.wikimedia.org/wiki/File:${file}`, credit: "Wikimedia Commons" };
    }
    const q = box.dataset.q;
    if (!q) throw new Error("Falta la fuente de la imagen");
    if (cache[q]) return cache[q];
    if (!requests.has(q)) requests.set(q, (async () => {
      const api = "https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*&generator=search&gsrnamespace=6&gsrlimit=1"
        + `&gsrsearch=${encodeURIComponent(`${q} filetype:bitmap`)}&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=500`;
      const response = await fetch(api);
      if (!response.ok) throw new Error("Fuente no disponible");
      const data = await response.json();
      const info = Object.values(data.query?.pages || {})[0]?.imageinfo?.[0];
      if (!info?.thumburl) throw new Error("Imagen no disponible");
      const meta = info.extmetadata || {};
      const text = (key) => (meta[key]?.value || "").replace(/<[^>]*>/g, "").trim();
      const result = { url: info.thumburl, page: info.descriptionurl, credit: text("Artist") || "Autor desconocido", license: text("LicenseShortName") };
      cache[q] = result;
      try { localStorage.setItem("pau-apuntes-img", JSON.stringify(cache)); } catch {}
      return result;
    })());
    return requests.get(q);
  }
  window.pauLoadImage = async (box) => {
    if (box.dataset.imageState) return;
    box.dataset.imageState = "loading";
    const illustration = box.classList.contains("reading-illustration");
    const caption = document.createElement(illustration ? "figcaption" : "span");
    caption.className = illustration ? "reading-illustration-caption" : "apunte-cap";
    const fail = () => {
      box.dataset.imageState = "error";
      const notice = document.createElement("span");
      notice.textContent = " · Imagen externa no disponible; requiere conexión y acceso a la fuente.";
      caption.append(notice);
      if (!caption.isConnected) box.append(caption);
    };
    try {
      const data = await resolve(box);
      const label = document.createElement(data.page ? "a" : "span");
      if (data.page) {
        label.href = data.page;
        label.target = "_blank";
        label.rel = "noopener noreferrer";
        label.title = [data.credit, data.license].filter(Boolean).join(" · ");
      }
      label.textContent = box.dataset.caption || "Wikimedia Commons";
      caption.append(label);
      if (illustration && (data.credit || data.license)) {
        caption.append(document.createTextNode(` · ${[data.credit, data.license].filter(Boolean).join(" · ")}`));
      }
      const img = new Image();
      img.alt = illustration ? box.dataset.caption || "Imagen contextual del bloque" : "";
      img.referrerPolicy = "no-referrer";
      if (box.dataset.pos) img.style.objectPosition = box.dataset.pos;
      img.addEventListener("load", () => {
        box.dataset.imageState = "loaded";
        box.prepend(img);
        if (!caption.isConnected) box.append(caption);
      }, { once: true });
      img.addEventListener("error", fail, { once: true });
      img.src = data.url;
      if (illustration) box.append(caption);
    } catch {
      caption.textContent = box.dataset.caption || "Imagen contextual del bloque";
      if (box.dataset.file || box.dataset.q) {
        const source = document.createElement("a");
        source.href = box.dataset.file
          ? `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(box.dataset.file)}`
          : `https://commons.wikimedia.org/w/index.php?search=${encodeURIComponent(box.dataset.q)}&title=Special:MediaSearch&type=image`;
        source.textContent = " · Consultar fuente en Wikimedia Commons";
        source.target = "_blank";
        source.rel = "noopener noreferrer";
        caption.append(source);
      }
      fail();
    }
  };
})();
