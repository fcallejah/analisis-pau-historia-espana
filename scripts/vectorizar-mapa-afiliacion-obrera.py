"""Redraw the 2003 union-affiliation map over the user's provincial SVG source."""
import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
SOURCE_MAP = ROOT / "assets/documentos/espana-loc.svg"
SOURCE_SCAN = ROOT / "assets/documentos/pdf-2003-1-4.png"
OUTPUT = ROOT / "assets/documentos/mapa-afiliacion-obrera-1917-vector.svg"
SOURCE_MAP_URL = "https://commons.wikimedia.org/wiki/File:Espa%C3%B1a-loc.svg"
SOURCE_PDF_URL = "https://drive.google.com/file/d/1XDODoBqLulonuiXw0Z598p2YYRrF1DRd/view"

LABELS = [
    ("La Coruña", 329, 53), ("Lugo", 495, 87), ("Pontevedra", 319, 130),
    ("Ourense", 464, 147), ("Oviedo", 500, 25), ("Santander", 626, 38),
    ("Vizcaya", 691, 19), ("Guipúzcoa", 746, 28), ("Álava", 727, 91),
    ("Navarra", 779, 111), ("Logroño", 734, 146), ("León", 550, 117),
    ("Palencia", 602, 128), ("Burgos", 665, 122), ("Zamora", 532, 174),
    ("Valladolid", 593, 195), ("Soria", 727, 186), ("Segovia", 643, 218),
    ("Salamanca", 511, 245), ("Ávila", 632, 259), ("Madrid", 675, 277),
    ("Zaragoza", 788, 158), ("Huesca", 848, 139), ("Lérida", 913, 143),
    ("Barcelona", 994, 201), ("Tarragona", 895, 215),
    ("Guadalajara", 728, 246), ("Cuenca", 753, 311), ("Teruel", 819, 254),
    ("Castellón", 883, 294), ("Valencia", 896, 348), ("Alicante", 902, 415),
    ("Murcia", 779, 444), ("Cáceres", 529, 292), ("Toledo", 650, 317),
    ("Ciudad Real", 657, 364), ("Badajoz", 500, 369), ("Albacete", 744, 385),
    ("Córdoba", 603, 441), ("Jaén", 675, 422), ("Sevilla", 551, 503),
    ("Huelva", 473, 484), ("Granada", 676, 523), ("Almería", 742, 497),
    ("Málaga", 605, 567), ("Cádiz", 507, 554), ("Baleares", 1037, 319),
    ("Canarias", 139, 510), ("Gerona", 1015, 160),
]

LABEL_PLACEMENTS = {
    "Oviedo": (540, 25, "end"),
    "Santander": (650, 16, "middle"),
    "Vizcaya": (718, 16, "middle"),
    "Guipúzcoa": (756, 28, "start"),
    "León": (569, 90, "middle"),
    "Palencia": (628, 112, "middle"),
    "Burgos": (686, 108, "middle"),
    "Ourense": (500, 155, "start"),
    "Zamora": (548, 180, "middle"),
    "Navarra": (805, 107, "start"),
    "Soria": (730, 190, "end"),
    "Logroño": (735, 162, "end"),
    "Valladolid": (619, 175, "middle"),
    "Segovia": (673, 209, "middle"),
    "Salamanca": (554, 270, "middle"),
    "Ávila": (628, 290, "middle"),
    "Madrid": (703, 282, "middle"),
    "Cuenca": (790, 320, "start"),
    "Toledo": (671, 309, "middle"),
    "Ciudad Real": (692, 353, "middle"),
    "Albacete": (737, 359, "middle"),
    "Murcia": (810, 490, "start"),
    "Cádiz": (500, 560, "end"),
    "Málaga": (610, 590, "middle"),
    "Granada": (689, 545, "middle"),
    "Almería": (760, 530, "middle"),
    "Córdoba": (623, 404, "middle"),
    "Jaén": (725, 405, "start"),
    "Baleares": (1048, 356, "middle"),
    "Lérida": (938, 52, "middle"),
    "Gerona": (1126, 36, "end"),
}

BLUE = "#4e679d"
ORANGE = "#e87925"

# Centers and radii are traced from the original scan at its native 1142 × 602 size.
PIE_CHARTS = [
    (424, 52, 33), (573, 40, 30), (665, 62, 18), (718, 52, 26),
    (766, 56, 19), (489, 83, 9), (413, 126, 22), (483, 143, 10),
    (569, 113, 16), (633, 137, 10), (686, 135, 12), (736, 96, 6),
    (789, 107, 10),     (749, 131, 17), (743, 185, 10), (619, 194, 17),
    (554, 238, 15), (685, 263, 75), (766, 309, 9), (555, 316, 24),
    (831, 258, 10), (870, 157, 14), (821, 191, 31), (932, 164, 9),
    (1024, 153, 89), (923, 230, 15), (869, 286, 13), (857, 349, 33),
    (1048, 319, 20), (782, 385, 18), (692, 383, 18), (545, 398, 24),
    (623, 437, 25), (693, 441, 22), (805, 442, 26), (871, 417, 28),
    (489, 460, 20), (559, 476, 53), (543, 545, 18), (689, 502, 25),
    (625, 530, 23), (760, 495, 17), (167, 524, 12),
]
PIE_CHART_PROVINCES = {
    (424, 52): "La Coruña", (573, 40): "Oviedo", (665, 62): "Santander",
    (718, 52): "Vizcaya", (766, 56): "Guipúzcoa", (489, 83): "Lugo",
    (413, 126): "Pontevedra", (483, 143): "Ourense", (569, 113): "León",
    (633, 137): "Palencia", (686, 135): "Burgos", (736, 96): "Álava",
    (789, 107): "Navarra", (749, 131): "Logroño", (743, 185): "Soria",
    (619, 194): "Valladolid", (554, 238): "Salamanca", (685, 263): "Madrid",
    (766, 309): "Cuenca", (555, 316): "Cáceres", (831, 258): "Teruel",
    (870, 157): "Zaragoza", (821, 191): "Huesca", (932, 164): "Lérida",
    (1024, 153): "Barcelona", (923, 230): "Tarragona", (869, 286): "Castellón",
    (857, 349): "Valencia", (1048, 319): "Baleares", (782, 385): "Albacete",
    (692, 383): "Ciudad Real", (545, 398): "Badajoz", (623, 437): "Córdoba",
    (693, 441): "Jaén", (805, 442): "Murcia", (871, 417): "Alicante",
    (489, 460): "Huelva", (559, 476): "Sevilla", (543, 545): "Cádiz",
    (689, 502): "Granada", (625, 530): "Málaga", (760, 495): "Almería",
    (167, 524): "Canarias",
}
PIE_CHART_RELOCATIONS = {(932, 164): (938, 74)}

PIE_SECTOR_OVERRIDES = {
    (1024, 153): (112, 338),  # Small orange notch at the bottom of Barcelona.
    (869, 286): (280, 340),  # Small orange notch at the top of Castellón.
    (789, 107): (260, 20),   # Small blue sector at the top of Navarra.
    (555, 316): (260, 20),   # Small blue sector at the top of Cáceres.
}
PIE_SECTOR_ROTATIONS = {
    (923, 230): 180,  # Tarragona.
}

# Supplemental markers clarify provinces covered by oversized charts.
OVERLAPPING_LOCATIONS = [
    ("Ávila", 628, 258, 15), ("Segovia", 673, 222, 10),
    ("Guadalajara", 733, 247, 13), ("Toledo", 671, 305, 20),
    ("Gerona", 1104, 54, 13),
]
OVERLAPPING_PIES = [
    ("Gerona", 1104, 54, 9, 305, 340),
]
SMALL_PROVINCE_MARKERS = [("Zamora", 548, 198, 10)]
OVERLAPPING_PROVINCE_ANCHORS = {
    "Ávila": (628, 258), "Segovia": (673, 222),
    "Guadalajara": (733, 247), "Toledo": (671, 305),
    "Gerona": (1002, 151),
}

MAP_INTERACTION_SCRIPT = r"""
(() => {
  const initialize = () => {
  const root = document.documentElement;
  const view = window;
  const labels = [...root.querySelectorAll("#province-labels .province-label")];
  const rootMatrix = root.getScreenCTM();
  if (!rootMatrix) return;
  const nonProvincePathIds = new Set(["path263-main"]);
  const mapPaths = [...root.querySelectorAll("#provincial-map path")].filter(
    path => !nonProvincePathIds.has(path.id)
      && view.getComputedStyle(path).fill === "rgb(255, 255, 208)"
  );
  const islandPaths = [...root.querySelectorAll("#canary-inset path")].filter(
    path => view.getComputedStyle(path).fill === "rgb(255, 255, 208)"
  );
  const provinceReferenceOverrides = new Map([
    ["Cádiz", [530, 545]],
    ["Málaga", [610, 545]],
    ["Navarra", [790, 110]],
    ["Logroño", [740, 150]],
    ["Cuenca", [785, 310]],
    ["Albacete", [775, 375]],
    ["Huesca", [850, 115]],
    ["Zaragoza", [870, 165]],
    ["Teruel", [830, 260]],
    ["Tarragona", [930, 215]]
  ]);
  const provinceReferences = [];
  const addProvinceReference = (name, x, y) => {
    if (!provinceReferenceOverrides.has(name)) {
      provinceReferences.push({ name, x, y });
    }
  };
  for (const node of root.querySelectorAll(
    "[data-province][data-anchor-x][data-anchor-y]"
  )) {
    addProvinceReference(
      node.dataset.province,
      Number(node.dataset.anchorX),
      Number(node.dataset.anchorY)
    );
  }
  for (const node of root.querySelectorAll(
    "[data-province][data-center-x][data-center-y]"
  )) {
    addProvinceReference(
      node.dataset.province,
      Number(node.dataset.centerX),
      Number(node.dataset.centerY)
    );
  }
  for (const label of labels) {
    const box = label.getBBox();
    const point = new DOMPoint(box.x + box.width / 2, box.y + box.height / 2)
      .matrixTransform(label.getScreenCTM()).matrixTransform(rootMatrix.inverse());
    addProvinceReference(label.dataset.province, point.x, point.y);
  }
  for (const [name, [x, y]] of provinceReferenceOverrides) {
    provinceReferences.push({ name, x, y });
  }
  const nearestProvince = (x, y) => [...provinceReferences]
    .sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y))[0]?.name;
  const mark = (node, name, className, focusable = false) => {
    if (!name) return;
    node.dataset.province = name;
    node.classList.add(className);
    node.setAttribute("aria-label", `Seleccionar provincia ${name}`);
    node.setAttribute("role", "button");
    node.setAttribute("aria-pressed", "false");
    node.style.cursor = "pointer";
    if (focusable) node.setAttribute("tabindex", "0");
  };
  for (const path of mapPaths) {
    path.classList.add("province-area");
    path.setAttribute("aria-hidden", "true");
    path.style.cursor = "pointer";
    path.style.setProperty("pointer-events", "visiblePainted", "important");
  }
  for (const path of root.querySelectorAll("#provincial-map path")) {
    if (!mapPaths.includes(path)) {
      path.style.setProperty("pointer-events", "none", "important");
    }
  }
  for (const path of islandPaths) {
    mark(path, "Canarias", "province-area", true);
    path.style.setProperty("pointer-events", "visiblePainted", "important");
  }
  for (const path of root.querySelectorAll("#canary-inset path")) {
    if (!islandPaths.includes(path)) {
      path.style.setProperty("pointer-events", "none", "important");
    }
  }
  const provinceAt = (x, y) => nearestProvince(x, y);
  const chartHitTargets = [
    ...root.querySelectorAll("#affiliation-sectors circle"),
    ...root.querySelectorAll("#overlapping-location-sectors circle")
  ].map(node => ({
    name: node.dataset.province,
    x: Number(node.getAttribute("cx")),
    y: Number(node.getAttribute("cy")),
    radius: Number(node.getAttribute("r"))
  }));
  const smallestChartAt = (x, y) => chartHitTargets
    .filter(chart => Math.hypot(chart.x - x, chart.y - y) <= chart.radius)
    .sort((a, b) => a.radius - b.radius)[0]?.name;
  for (const node of root.querySelectorAll("#affiliation-sectors [data-center-x]")) {
    const name = node.dataset.province || provinceAt(
      Number(node.dataset.centerX), Number(node.dataset.centerY)
    );
    mark(node, name, "affiliation-chart");
    node.setAttribute("aria-hidden", "true");
  }
  for (const node of root.querySelectorAll("#affiliation-outlines circle")) {
    const name = node.dataset.province || provinceAt(
      Number(node.dataset.centerX), Number(node.dataset.centerY)
    );
    mark(node, name, "affiliation-outline", true);
  }
  for (const node of root.querySelectorAll("#overlapping-locations circle")) {
    mark(node, node.dataset.province, "overlap-location", true);
  }
  for (const node of root.querySelectorAll("#overlapping-location-sectors [data-province]")) {
    mark(node, node.dataset.province, "affiliation-chart");
    node.setAttribute("aria-hidden", "true");
  }
  for (const node of root.querySelectorAll("#province-markers circle")) {
    mark(node, node.dataset.province, "province-marker", true);
  }
  for (const label of labels) {
    mark(label, label.dataset.province, "province-label", true);
  }
  const selectable = [...root.querySelectorAll("[data-province]:not(.province-area)")];
  const select = name => {
    root.dataset.selectedProvince = name || "";
    for (const node of selectable) {
      const active = Boolean(name) && node.dataset.province === name;
      node.classList.toggle("is-selected", active);
      if (node.getAttribute("role") === "button") {
        node.setAttribute("aria-pressed", String(active));
      }
    }
    for (const path of islandPaths) {
      const active = Boolean(name) && name === "Canarias";
      path.classList.toggle("is-selected", active);
      path.setAttribute("aria-pressed", String(active));
    }
  };
  root.addEventListener("click", event => {
    const area = event.target.closest?.(".province-area");
    if (area) {
      if (area.closest("#canary-inset")) {
        select("Canarias");
      } else {
        const point = new DOMPoint(event.clientX, event.clientY)
          .matrixTransform(root.getScreenCTM().inverse());
        select(nearestProvince(point.x, point.y));
      }
      return;
    }
    const target = event.target.closest?.("[data-province]");
    if (target) {
      if (target.matches(".affiliation-chart, .affiliation-outline")) {
        const point = new DOMPoint(event.clientX, event.clientY)
          .matrixTransform(root.getScreenCTM().inverse());
        select(smallestChartAt(point.x, point.y) || target.dataset.province);
      } else {
        select(target.dataset.province);
      }
      return;
    }
    select("");
  });
  root.addEventListener("keydown", event => {
    if (event.key === "Escape") select("");
    if (event.key === "Enter" || event.key === " ") {
      const target = event.target.closest?.("[data-province]");
      if (target) {
        event.preventDefault();
        select(target.dataset.province);
      }
    }
  });
  };
  if (document.readyState === "complete") initialize();
  else window.addEventListener("load", initialize, { once: true });
})();
"""


def append(parent, tag, text=None, **attributes):
    child = ET.SubElement(parent, f"{{{SVG_NS}}}{tag}", {
        key.replace("_", "-"): str(value) for key, value in attributes.items()
    })
    child.text = text
    return child


def pie_sector_angles(scan_path):
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise SystemExit(
            "Instala opencv-python-headless y numpy para regenerar los trazados."
        ) from error

    image = cv2.imread(str(scan_path))
    if image is None:
        raise ValueError(f"No se pudo leer el mapa original: {scan_path}")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, np.array((88, 25, 30)), np.array((140, 255, 255))) > 0
    orange = cv2.inRange(hsv, np.array((4, 35, 40)), np.array((30, 255, 255))) > 0
    height, width = image.shape[:2]
    yy, xx = np.ogrid[:height, :width]
    charts = []

    for cx, cy, radius in PIE_CHARTS:
        distance = np.hypot(xx - cx, yy - cy)
        inside = (distance >= radius * 0.18) & (distance <= radius * 0.86)
        blue_pixels = blue & inside
        orange_pixels = orange & inside
        total = int(blue_pixels.sum() + orange_pixels.sum())
        blue_share = float(blue_pixels.sum() / total) if total else 0
        if blue_share < 0.02:
            charts.append((cx, cy, radius, 0, 0))
            continue
        if blue_share > 0.97:
            charts.append((cx, cy, radius, 0, 360))
            continue

        blue_angles = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360
        blue_bins = np.bincount(
            np.floor(blue_angles[blue_pixels]).astype(int), minlength=360
        )
        orange_bins = np.bincount(
            np.floor(blue_angles[orange_pixels]).astype(int), minlength=360
        )
        kernel = np.ones(7)
        smooth_blue = np.convolve(
            np.r_[blue_bins[-3:], blue_bins, blue_bins[:3]], kernel, mode="valid"
        )[:360]
        smooth_orange = np.convolve(
            np.r_[orange_bins[-3:], orange_bins, orange_bins[:3]], kernel, mode="valid"
        )[:360]
        colored = smooth_blue + smooth_orange
        blue_run = (smooth_blue > smooth_orange) & (colored > 0)
        doubled = np.r_[blue_run, blue_run]
        longest = (0, 0)
        for start in range(360):
            if doubled[start] and (start == 0 or not doubled[start - 1]):
                end = start
                while end < start + 360 and doubled[end]:
                    end += 1
                if end - start > longest[1]:
                    longest = (start, end - start)

        span = max(4, blue_share * 360)
        center = (longest[0] + longest[1] / 2) % 360
        charts.append((cx, cy, radius, (center - span / 2) % 360, span))
    return charts


def correct_chart_sectors(charts):
    corrected = []
    for cx, cy, radius, start, span in charts:
        key = (cx, cy)
        if key in PIE_SECTOR_OVERRIDES:
            start, span = PIE_SECTOR_OVERRIDES[key]
        else:
            start = (start + PIE_SECTOR_ROTATIONS.get(key, 0)) % 360
        corrected.append((cx, cy, radius, start, span))
    return corrected


def pie_wedge_path(cx, cy, radius, start_angle, span):
    import math

    def point(angle):
        radians = math.radians(angle)
        return cx + radius * math.cos(radians), cy + radius * math.sin(radians)

    start = point(start_angle)
    end = point(start_angle + span)
    large_arc = 1 if span > 180 else 0
    return (
        f"M {cx} {cy} L {start[0]:.2f} {start[1]:.2f} "
        f"A {radius} {radius} 0 {large_arc} 1 {end[0]:.2f} {end[1]:.2f} Z"
    )


def clone_layer(layer, suffix, omit_path_ids=()):
    cloned = copy.deepcopy(layer)
    for element in list(cloned):
        if element.get("id") in ("rect2920", "rect3290"):
            cloned.remove(element)
    for parent in cloned.iter():
        for element in list(parent):
            if element.get("id") in omit_path_ids:
                parent.remove(element)
    for element in cloned.iter():
        style = element.get("style", "")
        if "stroke-width:0.2" in style and "stroke-dasharray:none" in style:
            element.set("style", style.replace("stroke-dasharray:none", "stroke-dasharray:4,3"))
    identifiers = {}
    for element in cloned.iter():
        identifier = element.get("id")
        if identifier:
            identifiers[identifier] = f"{identifier}{suffix}"
            element.set("id", identifiers[identifier])
    for element in cloned.iter():
        for key, value in tuple(element.attrib.items()):
            for original, replacement in identifiers.items():
                value = value.replace(f"url(#{original})", f"url(#{replacement})")
                if value == f"#{original}":
                    value = f"#{replacement}"
            element.set(key, value)
    return cloned


def draw_legend(root):
    legend = append(
        root, "g", id="map-legend",
        aria_label="afiliados a la UGT en naranja; afiliados a la CNT en azul",
    )
    cx, cy, radius = 167, 364, 12
    append(legend, "circle", cx=cx, cy=cy, r=radius, fill=BLUE,
           stroke="#36454f", stroke_width=1)
    append(legend, "path",
           d=f"M {cx} {cy-radius} A {radius} {radius} 0 0 0 {cx} {cy+radius} L {cx} {cy-radius} Z",
           fill=ORANGE, stroke="#36454f", stroke_width=1, stroke_linejoin="round")
    append(legend, "line", x1=104, y1=cy, x2=cx-radius, y2=cy,
           stroke=ORANGE, stroke_width=2)
    append(legend, "line", x1=cx+radius, y1=cy, x2=230, y2=cy,
           stroke=BLUE, stroke_width=2)
    append(legend, "text", "afiliados", x=98, y=cy-3, text_anchor="end", font_size=16)
    append(legend, "text", "a la UGT", x=98, y=cy+9, text_anchor="end", font_size=16)
    append(legend, "text", "afiliados", x=236, y=cy-3, font_size=16)
    append(legend, "text", "a la CNT", x=236, y=cy+9, font_size=16)


def export(map_path=SOURCE_MAP, scan_path=SOURCE_SCAN, destination=OUTPUT):
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    ET.register_namespace("cc", "http://creativecommons.org/ns#")
    ET.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")

    source = ET.parse(map_path).getroot()
    definitions = source.find(f"{{{SVG_NS}}}defs")
    map_layer = source.find(f"{{{SVG_NS}}}g[@id='layer1']")
    if definitions is None or map_layer is None:
        raise ValueError("El SVG provincial no contiene las capas esperadas.")

    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": "1142", "height": "620", "viewBox": "0 0 1142 620",
        "role": "img", "aria-labelledby": "map-title map-description",
    })
    append(root, "title", "Afiliación obrera en España, 1917", id="map-title")
    append(
        root, "desc",
        "Redibujo vectorial del documento 2, opción B, del examen PAU de 2003. "
        "La cartografía provincial procede de España-loc.svg, de Miguillen, publicada "
        "en Wikimedia Commons bajo licencia CC BY-SA 3.0. Los círculos y sectores "
        "naranjas representan afiliación a la UGT y los azules a la CNT. Su geometría "
        "se reconstruye de forma aproximada desde el original, que no ofrece cifras exactas. "
        "Puede seleccionar una provincia, un círculo o un rótulo; pulse el fondo para "
        "quitar la selección o use Escape.",
        id="map-description",
    )
    append(
        root, "metadata",
        f"Fuente temática: {SOURCE_PDF_URL}; recorte: {scan_path.name}. "
        f"Cartografía: Miguillen, España-loc.svg, CC BY-SA 3.0 "
        f"(https://creativecommons.org/licenses/by-sa/3.0/): {SOURCE_MAP_URL}. "
        "Se reconstruyen círculos perfectos a partir de sus centros, radios y sectores "
        "visibles en el examen; el círculo de Soria se amplía ligeramente para facilitar "
        "su lectura. No se han inferido cifras absolutas.",
    )
    root.append(copy.deepcopy(definitions))
    defs = root.find(f"{{{SVG_NS}}}defs")
    mainland_clip = append(defs, "clipPath", id="mainland-clip")
    append(mainland_clip, "path",
           d="M0 0H2458V1767H0Z M0 1380H850V1767H0Z",
           fill_rule="evenodd", clip_rule="evenodd")
    canaries_clip = append(defs, "clipPath", id="canaries-clip")
    append(canaries_clip, "path", d="M0 1360H850V1767H0Z")
    append(root, "rect", x=0, y=0, width=1142, height=620, fill="#cbeaf1")
    mainland = append(root, "g", transform="translate(194 -35) scale(0.424 0.39)",
                      id="provincial-map")
    mainland_layer = append(mainland, "g", clip_path="url(#mainland-clip)")
    mainland_layer.append(clone_layer(map_layer, "-main"))
    canaries = append(root, "g", transform="translate(-34 -201) scale(0.46)",
                      id="canary-inset")
    canaries_layer = append(canaries, "g", clip_path="url(#canaries-clip)")
    canaries_layer.append(clone_layer(map_layer, "-canary", {"path3796"}))

    sectors = append(root, "g", id="affiliation-sectors")
    charts = correct_chart_sectors(pie_sector_angles(scan_path))
    for cx, cy, radius, start, span in charts:
        anchor_x, anchor_y = cx, cy
        province = PIE_CHART_PROVINCES[(anchor_x, anchor_y)]
        cx, cy = PIE_CHART_RELOCATIONS.get((anchor_x, anchor_y), (cx, cy))
        attributes = {
            "class": "affiliation-chart",
            "data_center_x": cx, "data_center_y": cy,
            "data_anchor_x": anchor_x, "data_anchor_y": anchor_y,
            "data_province": province,
            "fill": BLUE if span == 360 else ORANGE,
        }
        append(sectors, "circle", cx=cx, cy=cy, r=radius, **attributes)
        if 0 < span < 360:
            append(sectors, "path",
                   d=pie_wedge_path(cx, cy, radius, start, span),
                   **{"class": "affiliation-chart"},
                   data_center_x=cx, data_center_y=cy,
                   data_anchor_x=anchor_x, data_anchor_y=anchor_y,
                   data_province=province, fill=BLUE)

    outlines = append(root, "g", id="affiliation-outlines")
    for cx, cy, radius, _, _ in charts:
        anchor_x, anchor_y = cx, cy
        province = PIE_CHART_PROVINCES[(anchor_x, anchor_y)]
        cx, cy = PIE_CHART_RELOCATIONS.get((anchor_x, anchor_y), (cx, cy))
        attributes = {
            "class": "affiliation-outline",
            "data_center_x": cx, "data_center_y": cy,
            "data_anchor_x": anchor_x, "data_anchor_y": anchor_y,
            "data_province": province,
            "fill": "none", "stroke": "#fff", "stroke_width": 1.6,
        }
        append(outlines, "circle", cx=cx, cy=cy, r=radius, **attributes)
    markers = append(root, "g", id="province-markers")
    for name, cx, cy, radius in SMALL_PROVINCE_MARKERS:
        append(markers, "circle", cx=cx, cy=cy, r=radius, fill=ORANGE,
               stroke="#fff", stroke_width=1.6, data_province=name,
               data_anchor_x=cx, data_anchor_y=cy)
    overlap_sectors = append(root, "g", id="overlapping-location-sectors")
    for name, cx, cy, radius, start, span in OVERLAPPING_PIES:
        anchor_x, anchor_y = OVERLAPPING_PROVINCE_ANCHORS[name]
        append(overlap_sectors, "circle", cx=cx, cy=cy, r=radius,
               fill=ORANGE, data_province=name,
               data_anchor_x=anchor_x, data_anchor_y=anchor_y)
        append(overlap_sectors, "path",
               d=pie_wedge_path(cx, cy, radius, start, span), fill=BLUE,
               data_province=name, data_anchor_x=anchor_x, data_anchor_y=anchor_y)
    overlap_markers = append(root, "g", id="overlapping-locations")
    for name, cx, cy, radius in OVERLAPPING_LOCATIONS:
        anchor_x, anchor_y = OVERLAPPING_PROVINCE_ANCHORS[name]
        append(overlap_markers, "circle", cx=cx, cy=cy, r=radius, fill="none",
               stroke="#fff", stroke_width=3, data_province=name,
               data_anchor_x=anchor_x, data_anchor_y=anchor_y)
    draw_legend(root)

    append(
        root, "style",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#222;paint-order:stroke;"
        "stroke:#fff;stroke-width:3px;stroke-linejoin:round}.province-label{"
        "font-weight:700;user-select:text;-webkit-user-select:text;pointer-events:all}.province-area,"
        ".affiliation-chart,.affiliation-outline,.province-marker,.overlap-location{"
        "transition:filter .15s,fill .15s}.province-area.is-selected{"
        "fill:#ffe6a3!important;stroke:#d46b17!important;stroke-width:2px!important;"
        "filter:drop-shadow(0 0 4px #f4bc35)}.affiliation-outline.is-selected,"
        ".province-marker.is-selected,.overlap-location.is-selected{"
        "stroke:#ffd43b!important;stroke-width:5px!important;"
        "filter:drop-shadow(0 0 5px #f4bc35)}.province-label.is-selected{"
        "fill:#9d4c00!important;stroke-width:4px;"
        "filter:drop-shadow(0 0 3px #f4bc35)}.province-area:focus,"
        ".affiliation-outline:focus,.province-marker:focus,.overlap-location:focus,"
        ".province-label:focus{filter:drop-shadow(0 0 4px #174a72)}",
    )
    labels = append(root, "g", id="province-labels")
    for name, source_x, source_y in LABELS:
        x, y, anchor = LABEL_PLACEMENTS.get(
            name, (source_x, source_y,
                   "end" if source_x < 280 or 600 < source_x < 710 else "start")
        )
        label = append(
            labels, "text", name, x=x, y=y, text_anchor=anchor,
            font_size=12 if name == "Toledo" else 14,
            **{"class": "province-label"},
            data_province=name, data_source_x=source_x, data_source_y=source_y,
        )
        if name == "Toledo":
            label.set("textLength", "34")
            label.set("lengthAdjust", "spacingAndGlyphs")
        append(label, "title", name)

    append(root, "script", MAP_INTERACTION_SCRIPT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    print(f"{destination}: SVG con {len(charts)} sectores circulares y {len(LABELS)} etiquetas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=SOURCE_MAP)
    parser.add_argument("--scan", type=Path, default=SOURCE_SCAN)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    export(args.map, args.scan, args.output)
