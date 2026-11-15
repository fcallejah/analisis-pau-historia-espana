"""Rebuild the layout of the map supplied in the 2012 exam 6 corpus in color.

The coast is the user-selected Commons SVG, unchanged. Historical curves follow
the supplied scan, adjusted to the geographic positions of its named cities.
"""
import argparse
import copy
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "assets/documentos/mapa-primera-guerra-carlista-vector.svg"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

CITY_DATA = [
    ("A Coruña", 94, 36, -8.4, 43.36, 0, -23, "end", "liberal"),
    ("Santiago de|Compostela", 87, 56, -8.54, 42.88, 15, 31, "start", "liberal"),
    ("Gijón", 180, 36, -5.66, 43.54, 0, -13, "middle", "liberal"),
    ("León", 181, 74, -5.57, 42.60, -12, 25, "end", "liberal"),
    ("Bilbao", 263, 46, -2.94, 43.26, -27, -27, "end", "liberal"),
    ("San Sebastián", 297, 47, -1.98, 43.32, 23, -24, "start", "liberal"),
    ("Amurrio", 257, 54, -3.0, 43.05, -35, 20, "end", "carlista"),
    ("Vergara", 278, 58, -2.42, 43.12, 8, 11, "start", "paz"),
    ("Estella", 251, 68, -2.03, 42.67, -10, -6, "end", "carlista"),
    ("Pamplona", 292, 74, -1.64, 42.82, 24, 15, "start", "carlista"),
    ("Logroño", 278, 81, -2.45, 42.47, -12, 24, "end", "liberal"),
    ("Huesca", 342, 96, -0.41, 42.14, 15, -20, "start", "liberal"),
    ("Zaragoza", 322, 115, -0.89, 41.65, -15, 23, "end", "carlista"),
    ("Berga", 408, 97, 1.85, 42.10, 15, -9, "start", "carlista"),
    ("Barcelona", 416, 122, 2.17, 41.39, 14, 12, "start", "liberal"),
    ("Cantavieja", 354, 135, -0.41, 40.53, 0, -24, "middle", "carlista"),
    ("Morella", 354, 151, -0.10, 40.62, 0, 38, "middle", "carlista"),
    ("Madrid", 251, 160, -3.70, 40.42, -15, -12, "end", "liberal"),
    ("Arganda", 249, 173, -3.44, 40.30, -10, 32, "end", "liberal"),
    ("Cuenca", 281, 179, -2.14, 40.07, 10, 27, "start", "liberal"),
    ("Valencia", 341, 199, -0.38, 39.47, 17, 8, "start", "liberal"),
    ("Cáceres", 146, 191, -6.37, 39.48, -14, -12, "end", "liberal"),
    ("Badajoz", 125, 226, -6.97, 38.88, -10, 26, "end", "liberal"),
    ("Córdoba", 200, 262, -4.78, 37.89, -18, 25, "end", "liberal"),
    ("Jaén", 233, 268, -3.79, 37.77, 12, 25, "start", "liberal"),
    ("Sevilla", 156, 279, -5.98, 37.39, -13, -9, "end", "liberal"),
    ("Huelva", 131, 290, -6.94, 37.26, -7, 27, "end", "liberal"),
    ("Granada", 239, 293, -3.6, 37.18, 14, 20, "start", "liberal"),
    ("Murcia", 311, 264, -1.13, 37.98, -14, -10, "end", "liberal"),
    ("Alicante", 337, 249, -0.48, 38.35, 12, 6, "start", "liberal"),
    ("Cartagena", 325, 280, -0.98, 37.6, 15, 24, "start", "liberal"),
]

ARROW_LENGTH = 22
CITY_DISPLAY_OFFSETS = {"Morella": (0, 27)}


def project(lon, lat):
    return ((lon + 9.9) * 1183.5554 / 14.7, (44.4 - lat) * 1015.8372 / 9.7)


def city_point(name, lon, lat):
    x, y = project(lon, lat)
    # Match Morella's schematic placement in the scan, retaining its real latitude.
    dx, dy = CITY_DISPLAY_OFFSETS.get(name, (0, 0))
    return x + dx, y + dy


def scan_point(x, y):
    # Smoothly adjust scan coordinates to the unchanged geographic base. Named
    # cities anchor the adjustment; intermediate historical curves are approximate.
    def affine(x, y):
        west = project(-8.4, 43.36)[0]
        north = project(-5.66, 43.54)[1]
        return (west + (x - 94) * (project(2.17, 41.39)[0] - west) / (416 - 94),
                north + (y - 36) * (project(-3.6, 37.18)[1] - north) / (293 - 36))
    base_x, base_y = affine(x, y)
    total = delta_x = delta_y = 0
    for _, sx, sy, lon, lat, *_ in CITY_DATA:
        px, py = project(lon, lat)
        distance = (x - sx) ** 2 + (y - sy) ** 2
        if distance < 1e-10:
            return px, py
        weight = 1 / distance ** 2
        ax, ay = affine(sx, sy)
        total += weight
        delta_x += weight * (px - ax)
        delta_y += weight * (py - ay)
    return base_x + delta_x / total, base_y + delta_y / total


def geographic_curve(path):
    def replace(match):
        x, y = project(float(match[1]), float(match[2]))
        return f"{x:.2f} {y:.2f}"
    number = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
    return re.sub(f"({number})\\s+({number})", replace, path)


def smooth_routes(paths):
    groups = []
    straight_segments = set()
    for path in paths:
        tokens = re.findall(r"[MCL]|-?\d+(?:\.\d+)?", path)
        current = scan_point(float(tokens[1]), float(tokens[2]))
        index = 3
        segments = []
        while index < len(tokens):
            command = tokens[index]
            count = 6 if command == "C" else 2
            numbers = list(map(float, tokens[index + 1:index + 1 + count]))
            points = [scan_point(*numbers[i:i + 2]) for i in range(0, count, 2)]
            if command == "L":
                end = points[0]
                points = [
                    tuple(a + (b - a) * ratio for a, b in zip(current, end))
                    for ratio in (1 / 3, 2 / 3, 1)
                ]
            segment = [current, *points]
            if command == "L":
                straight_segments.add(id(segment))
            segments.append(segment)
            current = points[-1]
            index += count + 1
        groups.append(segments)
    segments = [segment for group in groups for segment in group]
    # Keep cubic tangents aligned after moving the scan onto the geographic base.
    for before, after in zip(segments, segments[1:]):
        join = before[-1]
        if math.dist(join, after[0]) > .01:
            continue
        if id(after) in straight_segments:
            direction = tuple(b - a for a, b in zip(after[0], after[-1]))
        elif id(before) in straight_segments:
            direction = tuple(b - a for a, b in zip(before[0], before[-1]))
        else:
            direction = tuple(b - a for a, b in zip(before[2], after[1]))
        length = math.hypot(*direction)
        if not length:
            continue
        left, right = math.dist(before[2], join), math.dist(after[1], join)
        before[2] = tuple(p - d * left / length for p, d in zip(join, direction))
        after[1] = tuple(p + d * right / length for p, d in zip(join, direction))
    for group in groups:
        end = group[-1][-1]
        direction = tuple(b - a for a, b in zip(group[-1][2], end))
        length = math.hypot(*direction)
        direction = tuple(value / length for value in direction)
        base = tuple(p - value * ARROW_LENGTH for p, value in zip(end, direction))
        # The triangle replaces a straight tail: both base midpoint and tip are
        # on the route, and the next curve leaves the tip with the same tangent.
        while len(group) > 1 and math.dist(group[-1][0], end) < ARROW_LENGTH + 4:
            group.pop()
        last = group[-1]
        handle = min(math.dist(last[0], base) / 3, math.dist(last[2], end))
        last[2] = tuple(p - value * handle for p, value in zip(base, direction))
        last[3] = base
        start = group[0][0]
        yield f"M{start[0]:.4f} {start[1]:.4f}" + "".join(
            "C" + " ".join(f"{x:.4f} {y:.4f}" for x, y in segment[1:]) for segment in group
        ) + f"L{end[0]:.4f} {end[1]:.4f}"


def add(parent, name, text=None, **attributes):
    node = ET.SubElement(parent, f"{{{NS}}}{name}", {
        key.replace("_", "-"): str(value) for key, value in attributes.items()
    })
    node.text = text
    return node


def build(source):
    base = ET.parse(source).getroot()
    root = ET.Element(f"{{{NS}}}svg", {
        "width": "1184", "height": "1190", "viewBox": "0 -30 1184 1190",
        "role": "img", "aria-labelledby": "map-title map-description",
    })
    add(root, "title", "Principales focos y expediciones carlistas (1833–1840)", id="map-title")
    add(root, "desc", (
        "Reconstrucción vectorial a color del mapa de la recopilación, "
        "2012, examen 6, documento 1. Conserva la disposición del mapa, sus rótulos "
        "y las siete categorías de la leyenda: zonas controladas por los carlistas, "
        "área de influencia, ciudades carlistas y liberales, expediciones de Gómez "
        "y de don Carlos y paz de Vergara. Base de la península ibérica de "
        "NordNordWest y Sting, conservada sin modificar su geometría. Verde para la influencia, ocre "
        "para los contornos huecos de los focos de control, rojo para Gómez y verde oscuro para don Carlos. "
        "Pamplona y Zaragoza llevan círculos blancos como en la referencia aportada. "
        "Morella se coloca esquemáticamente debajo de Cantavieja, como en el escaneo, "
        "aunque su latitud real es ligeramente mayor. "
        "Los contornos y recorridos se han redibujado manualmente."
    ), id="map-description")
    add(root, "metadata", (
        "Fuente visual: assets/documentos/mapa-primera-guerra-carlista-2012-bn.png, "
        "imagen aportada en la recopilación del usuario: "
        "https://docs.google.com/document/d/1tLvTDk_3AdV7w-eoBB3InnzbTVsWmPbK_VL1z8dkyOk/"
        "edit#heading=h.xt7pfpw2sian. Revisado visualmente con la referencia ampliada "
        "aportada por el usuario; se omite la franja horizontal de fotocopia situada "
        "sobre Zaragoza, que no es un límite territorial ni una ruta. "
        "Influencia trazada con curvas continuas: Galicia cubierta, con entrantes "
        "que dejan fuera las ciudades liberales de León y Huesca. Logroño se representa "
        "como único hueco cerrado ampliado con forma de ojo y bordes suaves; "
        "esta área llega a la costa al norte de Barcelona. "
        "La prolongación verde del Maestrazgo cubre la mitad del tramo litoral anterior. "
        "El área sobre Madrid se retrae al norte y su borde queda más cerca de Cuenca. "
        "Gómez regresa directamente a Amurrio mediante una curva suave, sin pasar por Arganda "
        "ni desviarse a Logroño; su tramo occidental se abre entre Badajoz y el recorrido de ida. "
        "El giro de Cáceres es una curva simple sin bucles ni cruces. "
        "Don Carlos inicia su recorrido en el punto de Estella y pasa por Cantavieja. "
        "El rótulo de Estella se sitúa próximo a su ciudad. Morella se desplaza 27 unidades hacia abajo "
        "para conservar el orden esquemático del escaneo, sin alterar su latitud geográfica en los datos. "
        "Elipses de contorno grueso sin relleno; el foco del norte excluye Logroño. "
        "Reconstrucción manual, no facsímil certificado; "
        "pendiente de cotejo con el PDF oficial. Se preserva la simbología del original, "
        "sin corregirla silenciosamente. Colores de la anterior versión didáctica. "
        "Base: NordNordWest y Sting, Iberian Peninsula location map, "
        "https://commons.wikimedia.org/wiki/File:Iberian_Peninsula_location_map.svg. "
        "CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/. "
        "Adaptación: áreas, elipses, ciudades del examen, curvas, símbolos, colores y leyenda. "
        "Se conserva la geometría geográfica original, sin provincias."
    ))
    add(root, "style", (
        "text{fill:#20353c;font-family:Arial,Helvetica,sans-serif}"
        ".city-label{font-size:22px;font-weight:600;paint-order:stroke;"
        "stroke:#fff;stroke-width:4;stroke-linejoin:round}"
        ".legend-label{font-size:11px}"
        ".coast{fill:none;stroke:#7c817b;stroke-width:.7;stroke-linecap:round;stroke-linejoin:round}"
        ".route{fill:none;stroke:#111;stroke-width:1.55;stroke-linecap:round;stroke-linejoin:round}"
    ))
    defs = add(root, "defs")
    clip = add(defs, "clipPath", id="map-frame")
    add(clip, "rect", x="12", y="52", width="1160", height="830")
    marker = add(defs, "marker", id="arrow-gomez", viewBox="0 0 10 8",
                 refX="10", refY="4", markerWidth=ARROW_LENGTH, markerHeight=ARROW_LENGTH * .8,
                 markerUnits="userSpaceOnUse", orient="auto")
    add(marker, "path", d="M0 0L10 4L0 8Z", fill="#b64032")
    marker = add(defs, "marker", id="arrow-real", viewBox="0 0 10 8",
                 refX="10", refY="4", markerWidth=ARROW_LENGTH, markerHeight=ARROW_LENGTH * .8,
                 markerUnits="userSpaceOnUse", orient="auto")
    add(marker, "path", d="M0 0L10 4L0 8Z", fill="#28725d")
    add(root, "rect", x="0", y="-30", width="1184", height="1190", fill="#fff")
    cartography = add(root, "g", id="cartografia", clip_path="url(#map-frame)")
    for child in base:
        if child.tag.rsplit("}", 1)[-1] in ("rect", "polygon", "path", "polyline"):
            layer = copy.deepcopy(child)
            style = layer.get("style", "").replace("#c6ecff", "#e8f3f6")
            style = style.replace("#fefee9", "#faf7ed").replace("#e0e0e0", "#eee9dd")
            style = style.replace("#646464", "#7c817b").replace("2.40939999", "1.6")
            layer.set("style", style)
            cartography.append(layer)
    land_clip = add(defs, "clipPath", id="peninsular-spain")
    land = copy.deepcopy(next(node for node in base if node.get("id") == "polygon115"))
    land.attrib.pop("id", None)
    land.attrib.pop("style", None)
    land_clip.append(land)
    influence = add(cartography, "g", id="influencia", clip_path="url(#peninsular-spain)")
    add(influence, "path", fill="#c4d698", fill_rule="evenodd", d=geographic_curve(
        "M-10 44.5C-6 44.6 0 44.6 4 44.5 "
        "C4 43.5 4 42.4 4 41.75C3.3 41.6 2.9 41.6 2.55 41.58 "
        "C2.25 41.65 1.8 41.9 1.45 41.85 "
        "C1 41.78 .25 41.82 -.04 42.01 "
        "C-.12 42.13 -.12 42.30 -.30 42.36C-.48 42.42 -.72 42.36 -.78 42.16 "
        "C-.79 41.93 -.96 41.78 -1.22 41.5 "
        "C-1.05 41.25 -.7 41.1 -.3 40.98C.1 40.9 .95 40.85 1.05 40.6 "
        "C1.05 40.5919 .5 40.5838 .05 40.5838 "
        "C.04 39.72 -1.2 40.3 -1.8 40.5C-2.5 40.60 -2.95 40.98 -3.45 41.10 "
        "C-3.85 41.15 -3.9 41.0 -4.35 41.0C-4.85 41.0 -5.6 41.1 -5.85 41.1 "
        "C-6.15 41.5 -5.42 42.1 -5.32 42.33 "
        "C-5.18 42.54 -5.2 42.78 -5.42 42.82C-5.62 42.87 -5.9 42.77 -5.92 42.61 "
        "C-6 42.3 -6.1 42.12 -6.5 42.04C-7.25 41.7 -8.7 41.55 -10 41.6Z "
        "M-3.17 42.42C-3.17 42.48 -3.00 42.55 -2.84 42.59 "
        "C-2.68 42.63 -2.51 42.65 -2.34 42.62 "
        "C-2.10 42.58 -1.77 42.49 -1.77 42.42 "
        "C-1.77 42.35 -2.10 42.24 -2.34 42.20 "
        "C-2.51 42.17 -2.68 42.18 -2.84 42.23 "
        "C-3.00 42.28 -3.17 42.36 -3.17 42.42Z"
    ))
    control = add(cartography, "g", id="focos", fill="none",
                  stroke="#b17c32", stroke_width="6")
    positions = {name.replace("|", " "): city_point(name, lon, lat) for name, _, _, lon, lat, *_ in CITY_DATA}
    for name, cities, padding_x, padding_y, angle in (
        ("norte", ("Bilbao", "San Sebastián", "Amurrio", "Vergara", "Estella", "Pamplona"), 55, 11, 0),
        ("cataluna", ("Berga",), 51, 40, 37),
        ("maestrazgo", ("Cantavieja", "Morella"), 80, 80, -15),
    ):
        xs, ys = zip(*(positions[city] for city in cities))
        center_x, center_y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        rx, ry = (max(xs) - min(xs)) / 2 + padding_x, (max(ys) - min(ys)) / 2 + padding_y
        add(control, "ellipse", id=f"control-{name}", cx=center_x, cy=center_y,
            rx=rx, ry=ry,
            transform=f"rotate({angle} {center_x} {center_y})")
    expeditions = add(cartography, "g", id="expediciones")
    gomez = add(expeditions, "g", id="ruta-gomez", style="stroke:#b64032;stroke-width:3.8", **{"class": "route"})
    for curve in smooth_routes((
        "M257 54C240 65 220 70 202 69",
        "M202 69C174 71 204 48 194 43C172 42 150 43 129 39C115 36 104 33 94 36L87 52",
        "M87 52C82 68 126 78 158 73L181 71",
        "M181 71C198 77 186 93 196 104",
        "M196 104C201 115 211 114 221 116C237 118 244 124 251 131",
        "M251 131C264 137 287 141 298 145C305 151 302 163 307 174C313 190 320 205 313 217C311 222 307 224 299 224",
        "M299 224C284 220 275 227 269 239L257 246",
        "M257 246C253 253 249 263 241 267C225 274 208 267 199 263C191 259 186 250 181 241",
        "M181 241C172 223 162 212 151 205C151.9707 197.1054 150.4592 190.9053 146 191C141.3782 190.9063 138.3062 205.4790 140 224",
        "M140 224C144 244 153 266 168 281C178 298 193 310 190 315L184 317",
        "M184 317C168 324 154 311 161 300L174 292",
        "M174 292C197 282 214 287 226 273L235 257",
        "M235 257C245 243 251 231 253 211L253 199",
        "M253 199C266.9079 148.3482 248.0184 102.5695 257 54",
    )):
        add(gomez, "path", d=curve, marker_end="url(#arrow-gomez)")
    royal = add(expeditions, "g", id="ruta-real", style="stroke:#28725d;stroke-width:3.8", **{"class": "route"})
    for curve in smooth_routes((
        "M251 68C290.0169 81.2915 298.4737 84.6175 310 87L333 92",
        "M333 92C346 95 360 94 365 109C369 117 367 122 362 128",
        "M362 128C362 132 358 134 354 135",
        "M354 135C342 143 323 151 306 160L285 160",
        "M285 160C272 161 261 160 251 160",
    )):
        add(royal, "path", d=curve, stroke_dasharray="10 7", marker_end="url(#arrow-real)")
    city_group = add(cartography, "g", id="ciudades")
    for name, _, _, lon, lat, dx, dy, anchor, kind in CITY_DATA:
        x, y = positions[name.replace("|", " ")]
        group = add(city_group, "g", data_city=name.replace("|", " "), data_kind=kind,
                    data_lon=lon, data_lat=lat)
        if kind == "paz":
            peace(group, x, y, scale=2)
        else:
            add(group, "circle", cx=x, cy=y, r="5.8",
                fill="#fff" if kind == "carlista" else "#111",
                stroke="#24353c" if kind == "carlista" else "#fff", stroke_width="2")
        text = add(group, "text", x=x + dx, y=y + dy, text_anchor=anchor, **{"class": "city-label"})
        for index, line in enumerate(name.split("|")):
            add(text, "tspan", line, x=x + dx, dy="0" if index == 0 else "24")
    legend = add(root, "g", id="leyenda", transform="translate(0 20) scale(2.34)")
    add(legend, "path", d="M8 373H498", fill="none", stroke="#111", stroke_width="1.5")
    add(legend, "rect", x="15", y="378", width="30", height="33", fill="#c4d698", stroke="#56442b")
    add(legend, "ellipse", cx="30", cy="386", rx="12.5", ry="6.3", fill="none", stroke="#b17c32", stroke_width="2.5")
    add(legend, "text", "zonas controladas por los carlistas", x="52", y="389", **{"class": "legend-label"})
    add(legend, "text", "área de influencia carlista", x="52", y="406", **{"class": "legend-label"})
    for y, label, fill in ((420, "ciudades carlistas", "#fff"), (437, "ciudades liberales", "#111")):
        add(legend, "circle", cx="30", cy=y-3, r="3.6" if fill == "#fff" else "2.9",
            fill=fill, stroke="#111", stroke_width=".8")
        add(legend, "text", label, x="52", y=y, **{"class": "legend-label"})
    for name, color in (("gomez", "#b64032"), ("real", "#28725d")):
        marker = add(defs, "marker", id=f"legend-arrow-{name}", viewBox="0 0 10 8",
                     refX="10", refY="4", markerWidth="8", markerHeight="6.4",
                     markerUnits="userSpaceOnUse", orient="auto")
        add(marker, "path", d="M0 0L10 4L0 8Z", fill=color)
    add(legend, "path", d="M277 390H307", fill="none", stroke="#b64032", stroke_width="1.2", marker_end="url(#legend-arrow-gomez)")
    text = add(legend, "text", x="318", y="394", **{"class": "legend-label"})
    add(text, "tspan", "expedición del general", x="318")
    add(text, "tspan", " Miguel Gómez", x="318", dy="11")
    add(legend, "path", d="M277 420H307", fill="none", stroke="#28725d", stroke_width="1.2",
        stroke_dasharray="3 3", marker_end="url(#legend-arrow-real)")
    add(legend, "text", "expedición de Don Carlos (1837)", x="318", y="423", **{"class": "legend-label"})
    peace(legend, 292, 438)
    add(legend, "text", "Paz de Vergara (1839)", x="318", y="441", **{"class": "legend-label"})
    add(root, "rect", x="12", y="52", width="1160", height="1025", fill="none", stroke="#7c817b", stroke_width="1.5")
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(TARGET, encoding="utf-8", xml_declaration=True)


def peace(parent, x, y, scale=1):
    add(parent, "circle", cx=x, cy=y, r=4 * scale, fill="#fff", stroke="#111", stroke_width=scale)
    add(parent, "path", d=f"M{x} {y-2.8*scale}l{2.5*scale} {4.8*scale}h{-5*scale}Z", fill="#111")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="User-selected Iberian_Peninsula_location_map.svg from Commons")
    build(parser.parse_args().base)
