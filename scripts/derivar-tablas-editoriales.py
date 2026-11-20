"""Create color-treated derivatives while keeping extracted SGUIT SVGs intact."""
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SVG = "http://www.w3.org/2000/svg"
CADIZ_BAR_COLORS = [
    "#d4bd87", "#8fb8c8", "#8fb8c8", "#9aacc2", "#c6c2b9", "#ab9abb",
    "#d2a28f", "#9aacc2", "#a4b67f", "#ab9abb", "#ab9abb", "#ab9abb", "#ab9abb",
]
CADIZ_LEADERS = [
    (58.15, 34.13, 96.31),
    (46.62, 47.85, 160.08),
    (57.70, 59.39, 174.28),
    (39.63, 72.04, 209.72),
    (111.51, 85.65, 231.03),
    (117.64, 97.24, 245.47),
    (34.12, 109.90, 252.67),
    (38.12, 122.51, 273.55),
    (61.66, 135.10, 280.52),
    (46.10, 147.76, 294.81),
    (51.17, 161.43, 301.39),
    (40.87, 173.02, 301.39),
    (39.63, 185.56, 301.39),
]


def colorize_cadiz_chart():
    source = ROOT / "assets/documentos/miembros-cortes-cadiz-oficial-2008.svg"
    target = ROOT / "assets/documentos/miembros-cortes-cadiz-color-2008.svg"
    root = ET.parse(source).getroot()
    bars = [element for element in root.iter() if element.get("fill") == "#999a99"]
    expected_bars = len(CADIZ_BAR_COLORS) * 2
    if len(bars) != expected_bars:
        raise ValueError(f"Expected {expected_bars} original chart fills, found {len(bars)}")
    for index, bar in enumerate(bars):
        bar.set("fill", CADIZ_BAR_COLORS[index // 2])

    description = root.find(f"{{{SVG}}}desc")
    if description is not None:
        description.text = (
            "Extracción vectorial del PDF oficial de 2008, Examen 2, Opción A, documento 2. "
            "Se conservan las categorías y cifras originales; se añaden colores editoriales y "
            "líneas de puntos para relacionar cada ocupación con su cifra."
        )
    leaders = ET.SubElement(root, f"{{{SVG}}}g", {
        "id": "cadiz-chart-leaders",
        "aria-hidden": "true",
        "fill": "none",
        "stroke": "#46575e",
        "stroke-width": "0.7",
        "stroke-dasharray": "0.01 1.7",
        "stroke-linecap": "round",
        "opacity": "0.75",
    })
    for start, y, end in CADIZ_LEADERS:
        ET.SubElement(leaders, f"{{{SVG}}}path", {
            "class": "leader",
            "d": f"M{start:.2f},{y:.2f}H{end:.2f}",
        })

    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    target.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    print(f"{target.name}: recolored {len(bars)} fills and added {len(CADIZ_LEADERS)} dotted leaders")


def shade_1982_election_table():
    source = ROOT / "assets/documentos/resultados-elecciones-generales-1982-oficial-2008.svg"
    target = ROOT / "assets/documentos/resultados-elecciones-generales-1982-sombreado-editorial.svg"
    content = source.read_text(encoding="utf-8")
    background = '<rect width="436.0" height="264.0" fill="#fff" />'
    if content.count(background) != 1:
        raise ValueError("Could not locate the single white background in the official SVG")
    overlays = """\
<rect x="190" y="9" width="125" height="184" rx="2" fill="#a6c4d2" fill-opacity="0.34" aria-hidden="true" />
<rect x="316" y="9" width="117" height="184" rx="2" fill="#e3c18b" fill-opacity="0.34" aria-hidden="true" />"""
    target.write_text(content.replace(background, background + "\n" + overlays, 1),
                      encoding="utf-8")
    print(f"{target.name}: added editorial vote and seat column shading")


if __name__ == "__main__":
    colorize_cadiz_chart()
    shade_1982_election_table()
