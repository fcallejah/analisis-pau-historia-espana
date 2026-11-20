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


def shade_1977_congress_table():
    target = ROOT / "assets/documentos/tabla-congreso-1977.svg"
    content = target.read_text(encoding="utf-8")
    old_css = (
        '.grid[x="24"]{fill:#f1f5f2}.grid[x="904"]{fill:#f7efdf}'
        '.grid[y="78"]{fill:#e2ece8}.cell'
    )
    new_css = '.grid[y="78"]{fill:#e2ece8}.grid.row-stripe{fill:#dce8e2}.cell'
    if old_css in content:
        content = content.replace(old_css, new_css, 1)
        old_description = (
            "Tabla cotejada con el PDF del examen. Se conservan las denominaciones y cifras; "
            "el color suave de las columnas es editorial."
        )
        new_description = (
            "Tabla cotejada con el PDF del examen. Se conservan las denominaciones y cifras; "
            "se añaden bandas horizontales verdes alternas."
        )
        if content.count(old_description) != 1:
            raise ValueError("Could not locate the 1977 table description")
        content = content.replace(old_description, new_description, 1)
        for row in range(0, 11, 2):
            y = 120 + row * 36
            for x, width in ((24, 880), (904, 180)):
                original = (
                    f'<rect class="grid" x="{x}" y="{y}" width="{width}" height="36"/>'
                )
                striped = (
                    f'<rect class="grid row-stripe" data-stripe-row="{row}" '
                    f'x="{x}" y="{y}" width="{width}" height="36"/>'
                )
                if content.count(original) != 1:
                    raise ValueError(f"Could not locate 1977 table row {row}, column {x}")
                content = content.replace(original, striped, 1)
        target.write_text(content, encoding="utf-8")
    elif '.grid.row-stripe{fill:#dce8e2}' in content and content.count(
        'class="grid row-stripe"'
    ) == 12:
        return
    else:
        raise ValueError("The 1977 table does not match the expected source format")
    print(f"{target.name}: added alternating row shading")


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
    if 'id="election-table-row-stripes"' in content:
        raise ValueError("The official SVG unexpectedly contains editorial row stripes")
    stripes = "".join(
        f'<rect class="row-stripe" data-stripe-row="{row}" x="0" y="{28.48 + row * 12:.2f}" '
        'width="436" height="12" fill="#dce8e2" />'
        for row in range(0, 15, 2)
    )
    overlays = f'<g id="election-table-row-stripes" aria-hidden="true">{stripes}</g>'
    old_description = (
        '<desc id="description">Extracción vectorial del PDF oficial de 2008, Examen 3, Opción B, '
        'documento 1. Se conservan los trazados, glifos y datos originales; no es una reconstrucción.</desc>'
    )
    new_description = (
        '<desc id="description">Tabla extraída del PDF oficial de 2008, Examen 3, Opción B, documento 1. '
        'Se añaden bandas horizontales alternas de tono gris verdoso; se conservan las cifras y '
        'el trazado original.</desc>'
    )
    if content.count(old_description) != 1:
        raise ValueError("Could not locate the official SVG description")
    content = content.replace(old_description, new_description, 1)
    target.write_text(content.replace(background, background + "\n" + overlays, 1),
                      encoding="utf-8")
    print(f"{target.name}: added alternating row shading")


if __name__ == "__main__":
    colorize_cadiz_chart()
    shade_1977_congress_table()
    shade_1982_election_table()
