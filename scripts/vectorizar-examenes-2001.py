"""Redibujar tres materiales del escaneo PAU de 2001 sin modificar sus fuentes."""
import hashlib
import importlib.util
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets/documentos"
SVG = "http://www.w3.org/2000/svg"
spec = importlib.util.spec_from_file_location("election_chart", ROOT / "scripts/vectorizar-elecciones-1977-2007.py")
election_chart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(election_chart)
TEMPLATE = ASSETS / "base-mapa-provincias-commons.svg"
TEMPLATE_SHA256 = "86dd9753814a0238d4ce9502bb80cd5500aab16e272365d4d99ed84ab06f4be8"
TEMPLATE_URL = "https://commons.wikimedia.org/wiki/File:Blank_Spain_Map_(Provinces).svg"


def monarquia():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="760" viewBox="0 0 1000 760" role="img" aria-labelledby="title desc">
<title id="title">Funcionamiento de la monarquía absoluta</title>
<desc id="desc">Redibujo del esquema del examen 2 de 2001. Consejos y Cortes se relacionan con el rey; de él parten las secretarías y la administración provincial.</desc>
<metadata>Redibujo vectorial del documento 2, opción A, examen 2 de 2001, a partir del escaneo aportado. No es un facsímil.</metadata>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 Z" fill="#e2aa32"/></marker></defs>
<style>text{font-family:Arial,sans-serif;fill:#283536}.title{font-size:26px;font-weight:700;fill:#334b59}.head{font-size:22px;font-weight:700}.label{font-size:22px}.small{font-size:20px}.box{stroke:#c8caba;stroke-width:1.5}.link{fill:none;stroke:#e2aa32;stroke-width:7;marker-end:url(#arrow)}</style>
<rect width="1000" height="760" fill="#fffef5"/>
<text class="title" x="500" y="58" text-anchor="middle">FUNCIONAMIENTO DE LA MONARQUÍA ABSOLUTA</text>
<rect x="95" y="90" width="245" height="76" rx="3" fill="#e7e99d"/>
<text class="head" x="217" y="137" text-anchor="middle">INSTITUCIONES</text>
<rect x="625" y="90" width="285" height="76" rx="3" fill="#e7e99d"/>
<text class="head" x="767" y="137" text-anchor="middle">ÓRGANOS EJECUTIVOS</text>
<text class="small" x="50" y="304" transform="rotate(-90 50 304)" text-anchor="middle">Asesoran</text>
<text class="small" x="50" y="585" transform="rotate(-90 50 585)" text-anchor="middle">Representan</text>
<rect x="116" y="218" width="165" height="54" rx="3" fill="#e7e99d"/><text class="head" x="198" y="253" text-anchor="middle">Consejos</text>
<rect x="116" y="544" width="165" height="54" rx="3" fill="#e7e99d"/><text class="head" x="198" y="579" text-anchor="middle">Cortes</text>
<rect x="342" y="359" width="100" height="86" rx="3" fill="#f3c64c"/><text class="head" x="392" y="410" text-anchor="middle">REY</text>
<path class="link" d="M282 266 L337 356"/><text class="small" x="253" y="320">aconsejan</text>
<path class="link" d="M282 547 L337 448"/><text class="small" x="251" y="515">controlan</text>
<path class="link" d="M443 379 L508 308"/><path class="link" d="M443 425 L508 568"/>
<rect class="box" x="514" y="255" width="265" height="225" fill="#fffef7"/>
<line x1="514" y1="300" x2="779" y2="300" stroke="#c8caba"/>
<text class="head" x="646" y="284" text-anchor="middle">Secretarios</text>
<text class="label" x="531" y="336">• Estado</text><text class="label" x="531" y="370">• Asuntos extranjeros</text><text class="label" x="531" y="404">• Justicia</text><text class="label" x="531" y="438">• Guerra</text><text class="label" x="531" y="472">• Hacienda</text>
<rect x="785" y="347" width="190" height="80" fill="#b9e8bf"/><text class="small" x="880" y="379" text-anchor="middle"><tspan x="880">Administración</tspan><tspan x="880" dy="27">Central</tspan></text>
<rect class="box" x="514" y="559" width="265" height="162" fill="#fffef7"/>
<text class="small" x="531" y="590">• Capitanes generales</text><text class="small" x="531" y="625">• Audiencias</text><text class="small" x="531" y="660">• Corregidores</text><text class="small" x="531" y="695">• Intendentes</text>
<rect x="785" y="600" width="190" height="80" fill="#b9e8bf"/><text class="small" x="880" y="632" text-anchor="middle"><tspan x="880">Administración</tspan><tspan x="880" dy="27">Provincial</tspan></text>
</svg>
"""


# The shapes and labels are transcribed from the photographed exam; the positions
# are approximate because the contemporary provincial template is not the exam map.
SYMBOLS = [
    ("A Coruña", 164, 71, 50), ("Lugo", 214, 102, 10),
    ("Pontevedra", 148, 145, 1), ("Ourense", 188, 156, 5),
    ("Oviedo", 308, 72, 10), ("Santander", 425, 76, 10),
    ("Vizcaya", 475, 89, 10), ("Guipúzcoa", 531, 72, 1),
    ("Navarra", 529, 105, 50), ("León", 302, 142, 50),
    ("Burgos", 382, 178, 100), ("Palencia", 415, 134, 50),
    ("Logroño", 490, 136, 50), ("Soria", 500, 211, 10),
    ("Zaragoza", 578, 200, 200), ("Huesca", 607, 158, 50),
    ("Lérida", 667, 201, 50), ("Gerona", 805, 160, 50),
    ("Barcelona", 762, 235, 100), ("Tarragona", 706, 236, 50),
    ("Zamora", 285, 204, 100), ("Valladolid", 356, 201, 100),
    ("Salamanca", 296, 284, 200), ("Ávila", 354, 283, 50),
    ("Segovia", 385, 257, 50), ("Madrid", 431, 321, 300),
    ("Guadalajara", 449, 283, 50), ("Toledo", 412, 369, 200),
    ("Teruel", 566, 302, 50), ("Cuenca", 505, 364, 50),
    ("Castellón", 638, 355, 50), ("Valencia", 637, 410, 200),
    ("Baleares", 815, 380, 50), ("Cáceres", 265, 397, 100),
    ("Badajoz", 227, 444, 100), ("Ciudad Real", 415, 445, 10),
    ("Alicante", 627, 490, 50), ("Murcia", 592, 525, 50),
    ("Huelva", 220, 582, 50), ("Sevilla", 281, 565, 400),
    ("Córdoba", 364, 530, 200), ("Jaén", 421, 542, 100),
    ("Granada", 437, 590, 100), ("Cádiz", 260, 646, 100),
    ("Málaga", 380, 625, 50), ("Almería", 507, 614, 10),
    ("Canarias", 866, 630, 50),
]
STYLES = {
    400: ("#f4db28", 104), 300: ("#96724d", 87),
    200: ("#a897ca", 77), 100: ("#a4aa4a", 65),
    50: ("#eb854b", 47), 10: ("#dc126c", 30),
    5: ("#bd65bd", 21), 1: ("#d5a5db", 14),
}
LABEL_OFFSETS = {
    "Pontevedra": (-4, -10), "Ourense": (6, 12), "Santander": (-10, -10),
    "Vizcaya": (0, 10), "Guipúzcoa": (5, -12), "Navarra": (10, 11),
    "Palencia": (-3, -11), "Burgos": (3, 10), "Logroño": (-8, 11),
    "Zamora": (-8, -11), "Valladolid": (4, 10), "Salamanca": (-7, 0),
    "Ávila": (-4, 10), "Segovia": (0, -11), "Madrid": (0, 0),
    "Guadalajara": (5, -12), "Soria": (8, 2), "Huesca": (0, -11),
    "Zaragoza": (-3, 9), "Lérida": (0, -10), "Tarragona": (-8, 10),
    "Barcelona": (7, -9), "Castellón": (7, -9), "Valencia": (0, 3),
    "Córdoba": (0, -10), "Jaén": (8, 10), "Sevilla": (0, 2),
    "Granada": (0, 10), "Málaga": (-4, 11), "Almería": (12, 4),
}


def el(parent, tag, text=None, **attrs):
    child = ET.SubElement(parent, f"{{{SVG}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})
    child.text = text
    return child


def mapa():
    template = TEMPLATE.read_bytes()
    if hashlib.sha256(template).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("La plantilla cartográfica no coincide con la versión revisada.")
    base = ET.fromstring(template)
    root = ET.Element(f"{{{SVG}}}svg", {"width": "1200", "height": "790", "viewBox": "0 0 1200 790",
                                     "role": "img", "aria-labelledby": "title desc"})
    el(root, "title", "Desamortización de Mendizábal", id="title")
    el(root, "desc", "Redibujo del mapa del examen 4 de 2001. Cuadrados de colores y tamaños representan magnitudes en millones de reales; su posición sobre una cartografía provincial moderna es aproximada.", id="desc")
    el(root, "metadata", f"Cartografía adaptada de Blank Spain Map (Provinces), Javitomad: {TEMPLATE_URL}. "
       "Licencia CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/. "
       "Adaptación: recoloreado, ampliación y superposición de símbolos, etiquetas y leyenda a partir del examen 4 de 2001. No es un facsímil.")
    el(root, "style", "text{font-family:Arial,Helvetica,sans-serif;fill:#26343a}.title{font-size:24px;font-weight:700}.province{font-size:7.7px;font-weight:700;paint-order:stroke;stroke:#fff;stroke-width:2px;stroke-linejoin:round}.legend{font-size:16px}.legend-note{font-size:13px}.symbol{stroke:#554f44;stroke-width:.7;fill-opacity:.86}")
    el(root, "rect", x=0, y=0, width=1200, height=790, fill="#ffffff")
    el(root, "text", "Desamortización de Mendizábal", x=600, y=35, text_anchor="middle", **{"class": "title"})
    geo = el(root, "g", id="geography", transform="translate(22 48) scale(1.7)")
    for child in base:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "defs":
            geo.append(child)
        elif tag == "path":
            style = child.get("style", "").replace("#d3d3d3", "#e7ebe7").replace("#ffffff", "#839394")
            child.set("style", style)
            geo.append(child)

    boxes = el(geo, "g", id="symbols")
    labels = el(geo, "g", id="province-labels")
    for name, sx, sy, amount in SYMBOLS:
        if name == "Canarias":
            x, y = 105, 361
        else:
            x = 178 + (sx - 164) * 0.52
            y = 22 + (sy - 71) * 0.50
        color, size = STYLES[amount]
        side = size * .37
        el(boxes, "rect", x=f"{x-side/2:.2f}", y=f"{y-side/2:.2f}",
           width=f"{side:.2f}", height=f"{side:.2f}", fill=color,
           **{"class": "symbol", "data-province": name})
        dx, dy = LABEL_OFFSETS.get(name, (0, 2))
        el(labels, "text", name, x=f"{x+dx:.2f}", y=f"{y+dy:.2f}", text_anchor="middle", **{"class": "province"})
    legend = el(root, "g", id="legend", transform="translate(945 438)")
    el(legend, "text", "Millones de reales", x=0, y=0, **{"class": "legend", "font-weight": "700"})
    el(legend, "text", "Símbolos reducidos", x=0, y=20, **{"class": "legend-note"})
    for i, (amount, (color, size)) in enumerate(STYLES.items()):
        y = 43 + i * 34
        side = size * .25
        el(legend, "rect", x=0, y=y, width=f"{side:.2f}", height=f"{side:.2f}",
           fill=color, stroke="#554f44", stroke_width=".7", **{"data-reference": amount})
        el(legend, "text", f"{amount} {'millón' if amount == 1 else 'millones'}", x=38, y=y+16, **{"class": "legend"})
    ET.register_namespace("", SVG)
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


PARTIES = [
    ("Partido Progresista", 159, "#e9b625"),
    ("Partido Demócrata", 20, "#e887b8"),
    ("Unión Liberal (unionistas)", 69, "#4fa6d5"),
    ("Partido Republicano Federal", 69, "#9acd32"),
    ("Republicanos unitarios", 2, "#d84b36"),
    ("Carlistas", 18, "#697fae"),
    ("Isabelinos (liberales moderados)", 14, "#527a2a"),
]


def asamblea():
    total = sum(seats for _, seats, _ in PARTIES)
    if total != 351:
        raise ValueError("La suma de los escaños debe coincidir con los datos del examen.")
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="520" viewBox="0 0 760 520" role="img" aria-labelledby="title desc">',
        '<title id="title">Resultado elecciones 1869 (15-18 de enero)</title>',
        '<desc id="desc">Semicírculo proporcional a 351 diputados, con los siete grupos y colores adaptados del gráfico del examen 6 de 2001.</desc>',
        '<metadata>Redibujo vectorial a partir del escaneo de 2001, examen 6, opción A, documento 2; 351 diputados según los valores impresos y colores intensificados. No es un facsímil.</metadata>',
        '<style>text{font-family:Arial,sans-serif;fill:#25343b}.title{font-size:22px;font-weight:700;fill:#223e4b}.subtitle{font-size:13px}.party{font-size:14px;font-weight:700}.share{font-size:13px;font-weight:600}.center{font-size:18px;font-weight:700}.note{font-size:12px}.sector{stroke:#fff;stroke-width:2}</style>',
        '<rect width="760" height="520" fill="#fff"/>',
        '<text class="title" x="380" y="32" text-anchor="middle">Resultado elecciones 1869 (15-18 de enero)</text>',
        '<text class="subtitle" x="380" y="54" text-anchor="middle">Número de diputados</text>',
    ]
    angle = 180.0
    for name, seats, color in PARTIES:
        end = angle - 180 * seats / total
        out.append(f'<path class="sector" data-party="{escape(name, quote=True)}" data-seats="{seats}" '
                   f'data-seat-percent="{100 * seats / total:.3f}" fill="{color}" '
                   f'd="{election_chart.annular_sector(220, 345, 175, 74, angle, end)}"/>')
        angle = end
    out += ['<line x1="220" y1="170" x2="220" y2="271" stroke="#fff" stroke-width="2" stroke-dasharray="5 4"/>',
            '<text class="center" x="220" y="310" text-anchor="middle">351*</text>',
            '<text class="note" x="220" y="329" text-anchor="middle">diputados</text>',
            '<text class="note" x="220" y="345" text-anchor="middle">176 para la mayoría</text>']
    for i, (name, seats, color) in enumerate(PARTIES):
        y = 112 + i * 48
        pct = f"{100 * seats / total:.1f}".replace(".", ",")
        out.extend([f'<rect x="420" y="{y-13}" width="14" height="14" rx="2" fill="{color}"/>',
                    f'<text class="party" x="445" y="{y}">{escape(name)} · {seats}</text>',
                    f'<text class="share" x="745" y="{y}" text-anchor="end">{pct} %</text>'])
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    for filename, render in (
        ("2001-monarquia-absoluta-vector.svg", monarquia),
        ("2001-mendizabal-mapa-vector.svg", mapa),
        ("2001-asamblea-1869-semicirculo.svg", asamblea),
    ):
        (ASSETS / filename).write_text(render(), encoding="utf-8")
        print(filename)
