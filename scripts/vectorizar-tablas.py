"""Rebuild the reviewed PDF tables as accessible, self-contained SVGs."""
from base64 import b64encode
import hashlib
import json
from pathlib import Path
import textwrap
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
TABLES = {
    "porcentajes-restauracion": {
        "caption": "Resultados de la Restauración: porcentaje de escaños",
        "headers": ["años electorales que dan comienzo a nuevas Cortes", "Partido Conservador",
                    "Partido Liberal", "suma de Conservadores y Liberales", "total de la oposición extra-turno"],
        "widths": [260, 220, 220, 290, 250],
        "group": "porcentajes de los escaños",
        "rows": [
            ["1891", "65,6", "20,8", "86,4", "13,6"],
            ["1893", "15,2", "70,2", "85,5", "14,5"],
            ["1896", "69,5", "22,0", "91,5", "8,5"],
            ["1898", "21,0", "66,3", "87,3", "12,7"],
            ["1899", "58,7", "30,3", "89,0", "11,0"],
            ["1901", "21,7", "61,1", "82,8", "17,2"],
        ],
        "underlinedCells": [[0, 1], [1, 2], [3, 2], [4, 1], [5, 2]],
        "visibleNotes": 1,
        "notes": [
            "NOTA: Las cifras subrayadas indican que el partido está en el poder a la hora de presidir las elecciones.",
            "Subrayados de la fuente: 1891, Conservador; 1893, Liberal; 1898, Liberal; 1899, Conservador; 1901, Liberal. En 1896 no se añade un subrayado que no aparece en el original.",
            "Se conserva el 85,5 de la suma de 1893, aunque las dos cifras de la fuente suman 85,4.",
        ],
    },
    "conflictos-laborales-1963-1972": {
        "caption": "CAUSAS DE LOS CONFLICTOS LABORALES (1963-1972).",
        "headers": [""] + [str(year) for year in range(1963, 1973)],
        "widths": [340] + [104] * 10,
        "rows": [
            ["Político-Sociales", "16", "8", "9", "10", "10", "54", "132", "687", "115", "66"],
            ["Convenio Colectivo", "202", "62", "32", "21", "21", "-", "39", "516", "63", "298"],
            ["Valoración Rendimiento", "83", "71", "35", "23", "23", "17", "49", "38", "43", "42"],
            ["Solidaridad", "34", "28", "22", "-", "-", "103", "108", "93", "133", "156"],
            ["Mejoras Salariales", "216", "209", "62", "61", "61", "67", "73", "122", "168", "152"],
            ["Otras causas", "204", "51", "39", "28", "28", "58", "71", "79", "201", "179"],
        ],
        "notes": ["FUENTE: TEZANOS, J. F.: Estructura de clases en la España actual, 1975."],
    },
    "renta-europea-1940-1960": {
        "caption": "Renta per cápita en algunos países europeos (en dólares de 1970)",
        "headers": ["Países/Años", "1940", "1950", "1960"],
        "widths": [124, 156, 131, 135],
        "examLayout": {
            "size": (866, 412), "origin": (160, 82), "rowHeights": [50] * 5,
            "fontSizes": (22, 22, 19), "titleBaselines": (25, 51),
            "notePosition": (8, 376), "noteBreakBefore": "(1939-1975)",
        },
        "rows": [
            ["Alemania", "1.230", "1.363", "1.610"],
            ["España", "746", "694", "1.042"],
            ["Francia", "1.456", "1.575", "2.234"],
            ["Reino Unido", "1.715", "1.964", "2.442"],
        ],
        "notes": ["Fuente: José Luis GARCÍA DELGADO y Juan Carlos JIMÉNEZ, “La economía”, en VV.AA., La época de Franco (1939-1975), vol XLI de la Historia de España, Espasa-Calpe, Madrid. 1996, p.450."],
    },
    "produccion-hierro-1860-1869": {
        "caption": "Producción de hierro colado (media anual en miles de toneladas)",
        "headers": ["", "ESPAÑA", "FRANCIA", "GRAN BRETAÑA"],
        "widths": [240, 240, 240, 340],
        "rows": [
            ["1860-1864", "45", "1.065", "4.152"],
            ["1865-1869", "42", "1.262", "4.904"],
        ],
        "notes": ["Fuente: NADAL, J.: El fracaso de la Revolución Industrial en España, 1814-1913, 1975."],
    },
    "escanos-constituyentes-1931-porcentajes": {
        "caption": "Distribución de escaños en las constituyentes de Junio de 1931",
        "headers": ["Partidos", "Porcentaje de escaños"],
        "widths": [750, 330],
        "rows": [
            ["Socialistas", "25,6 %"], ["Radicales de Lerroux", "19,8 %"],
            ["Radical Socialistas", "13,2 %"], ["Acción Republicana de M. Azaña", "6,6 %"],
            ["Federales", "3,7 %"], ["Derechas (Agrarios, vascos y monárquicos", "13,2 %"],
            ["Progresistas de A. Zamora y Maura", "4,6 %"], ["Catalanes", "9,5 %"],
            ["Gallegos", "3,5 %"],
        ],
        "notes": ["Se conserva el rótulo de Derechas sin cerrar el paréntesis, tal como aparece en la fuente."],
        "visibleNotes": 0,
    },
    "divisas-emigrantes-1961-1975": {
        "caption": "DIVISAS APORTADAS POR LOS EMIGRANTES ESPAÑOLES. 1961-1975",
        "headers": ["Años", "Millones de dólares"],
        "widths": [80, 196],
        "examLayout": {
            "size": (299, 512), "origin": (8, 70),
            "rowHeights": [24] + [23] * 15,
            "fontSizes": (17, 18, 12), "titleWeight": 400,
            "titleLines": ["DIVISAS APORTADAS POR LOS", "EMIGRANTES ESPAÑOLES. 1961-", "1975"],
            "titleBaselines": (17, 40, 63), "notePosition": (11, 493),
            "rulesAfter": (0,), "verticalRules": False,
            "italicHeader": True, "firstColumnLeft": True,
            "noteEmphasis": ("La emigración española",),
        },
        "rows": [[str(year), value] for year, value in zip(
            range(1961, 1976),
            ["115", "148", "201", "240", "301", "346", "325", "324", "402", "469",
             "539", "570", "749", "654", "599"])],
        "notes": ["Fuente: Barrutieta, A.: La emigración española"],
    },
    "elecciones-1977-votos-escanos": {
        "caption": "Doc. 11. Resultados electorales del 15 de junio de 1977",
        "introduction": "Las primeras elecciones legislativas con garantías democráticas desde la Segunda República arrojaron en porcentajes los siguientes resultados para el Congreso:",
        "headers": ["Partido", "Votos", "Votos (en %)", "Escaños", "Escaños (en %)"],
        "widths": [210, 270, 240, 210, 270],
        "rows": [
            ["UCD", "6 309 517", "34,8", "165", "47,1"],
            ["PSOE", "5 240 464", "29,4", "118", "33,7"],
            ["PCE", "1 655 744", "9,3", "20", "5,7"],
            ["AP", "1 503 376", "8,4", "16", "4,6"],
            ["PSP", "804 382", "4,5", "6", "1,7"],
            ["CIU", "666 398", "3,7", "13", "3,1"],
            ["PNV", "304 244", "1,7", "8", "2,3"],
            ["Otros", "1 783 117", "8,2", "4", "1,1"],
        ],
        "notes": ["Se conserva el 3,1 de escaños de CIU y el resto de cifras de la reproducción original, sin recalcular porcentajes. «Doc. 11» es el rótulo interno de la imagen, no la posición del material en el examen."],
        "visibleNotes": 0,
    },
    "ayuda-economica-americana-1953-1957": {
        "caption": "AYUDA ECONÓMICA AMERICANA (en dólares)",
        "headers": ["Conceptos", "1953-1954", "1954-1955", "1955-1956", "1956-1957"],
        "widths": [180, 112, 112, 112, 112],
        "examLayout": {
            "size": (632, 451), "origin": (2, 71),
            "rowHeights": [42, 57, 44, 33, 50, 44, 33, 44],
            "fontSizes": (21, 19, 18), "titleBaselines": (28, 54),
            "notePosition": (16, 444), "rulesAfter": (0, 1, 4),
            "boldHeader": True, "boldLabels": (1, 2, 5),
        },
        "rows": [
            ["Ayuda programada", "85.000.000", "85.000.000", "85.000.000", "50.000.000"],
            ["Ayuda concedida", "84.634.153", "84.890.784", "84.890.784", "18.687.000"],
            ["Ayuda económica", "84.273.248", "84.550.557", "84.550.557", "18.500.000"],
            ["Ayuda técnica", "360.905", "340.227", "340.227", "187.000"],
            ["Excedentes agrícolas", "–", "56.300.000", "92.200.000", "59.300.000"],
            ["Ventas", "–", "47.700.000", "64.800.000", "59.300.000"],
            ["Donativos", "–", "8.600.000", "27.400.000", "–"],
        ],
        "indentedRows": [2, 3, 5, 6],
        "notes": ["Fuente: Historia de España, Instituto Gallach, Vol. XII, 1993."],
    },
}


def lines(text, width, size):
    return textwrap.wrap(text, max(8, int((width - 32) / (size * .57))),
                         break_long_words=False, break_on_hyphens=False) or [""]


def render(table, provenance):
    if table.get("examLayout"):
        return render_exam_table(table, provenance)
    widths = table["widths"]
    width = sum(widths) + 48
    title = lines(table["caption"], width - 48, 28)
    intro = lines(table["introduction"], width - 48, 21) if table.get("introduction") else []
    headers = [lines(label, column, 23) for label, column in zip(table["headers"], widths)]
    header_height = max(map(len, headers)) * 29 + 30
    group_height = 48 if table.get("group") else 0
    rows = [[lines(str(value), widths[col] - (20 if col == 0 and index in table.get("indentedRows", []) else 0), 23)
             for col, value in enumerate(row)] for index, row in enumerate(table["rows"])]
    heights = [max(52, max(map(len, row)) * 29 + 20) for row in rows]
    visible_notes = table.get("notes", [])
    notes = [lines(note, width - 48, 18)
             for note in visible_notes[:table.get("visibleNotes", len(visible_notes))]]
    top = 28 + len(title) * 34 + len(intro) * 28 + (18 if intro else 0) + 18
    height = top + group_height + header_height + sum(heights) + sum(len(note) * 24 + 12 for note in notes) + 30
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(table["caption"])}</title>',
        f'<desc id="desc">{escape("Redibujo vectorial de la tabla del PDF; cifras y subrayados conservados. " + " ".join(table.get("notes", [])))}</desc>',
        f'<metadata>{escape(json.dumps(provenance, ensure_ascii=False))}</metadata>',
        '<style>text{font-family:Arial,sans-serif;fill:#17324e}.title{font-size:28px;font-weight:700}.head{font-size:23px;font-weight:700}.cell{font-size:23px}.note{font-size:18px}.intro{font-size:21px}.on-dark{fill:#fff}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
    ]

    def text(content, x, y, css, anchor="start", underlined=False):
        decoration = ' text-decoration="underline"' if underlined else ""
        parts.append(f'<text class="{css}" x="{x}" y="{y}" text-anchor="{anchor}"{decoration}>{escape(content)}</text>')

    def cell(x, y, w, h, content, fill, css, centered=False, underlined=False, inset=0):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#7695b3" stroke-width="1"/>')
        baseline = y + (h - len(content) * 29) / 2 + 23
        for index, line in enumerate(content):
            text(line, x + w / 2 if centered else x + 16 + inset,
                 baseline + index * 29, css, "middle" if centered else "start", underlined)

    y = 44
    for line in title:
        text(line, 24, y, "title")
        y += 34
    for line in intro:
        text(line, 24, y + 8, "intro")
        y += 28
    y = top
    if group_height:
        cell(24, y, widths[0], group_height + header_height, headers[0], "#244968", "head on-dark", True)
        cell(24 + widths[0], y, sum(widths[1:]), group_height, [table["group"]], "#244968", "head on-dark", True)
        y += group_height
    x = 24
    for index, (column, label) in enumerate(zip(widths, headers)):
        if not (group_height and index == 0):
            cell(x, y, column, header_height, label, "#c8dded", "head", True)
        x += column
    y += header_height
    for index, (row, row_height) in enumerate(zip(rows, heights)):
        x = 24
        for column, (value, column_width) in enumerate(zip(row, widths)):
            parts.append(f'<g data-row="{index}" data-column="{column}">')
            cell(x, y, column_width, row_height, value, "#f5f9fc" if index % 2 == 0 else "#e2edf6",
                 "cell", column > 0, [index, column] in table.get("underlinedCells", []),
                 20 if column == 0 and index in table.get("indentedRows", []) else 0)
            parts.append("</g>")
            x += column_width
        y += row_height
    for note in notes:
        y += 24
        for line in note:
            text(line, 24, y, "note")
            y += 24
        y -= 12
    parts.append("</svg>")
    return "\n".join(parts) + "\n", width, height


def render_exam_table(table, provenance):
    layout = table["examLayout"]
    width, height = layout["size"]
    title_size, cell_size, note_size = layout["fontSizes"]
    baselines = layout["titleBaselines"]
    title_weight = layout.get("titleWeight", 700)
    if "titleLines" in layout:
        title_lines = layout["titleLines"]
        unit = None
    elif " (" in table["caption"]:
        title, unit = table["caption"].split(" (", 1)
        title_lines = [title]
    else:
        title_lines = [table["caption"]]
        unit = None
    font = b64encode((ROOT / "assets/fonts/RobotoCondensed-Regular.ttf").read_bytes()).decode("ascii")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(table["caption"])}</title>',
        f'<desc id="desc">{escape(table["notes"][0])}</desc>',
        f'<metadata>{escape(json.dumps(provenance, ensure_ascii=False))}</metadata>',
        '<style>@font-face{font-family:PAUCondensed;src:local("Arial Narrow"),local("ArialNarrow"),'
        f'url(data:font/ttf;base64,{font}) format("truetype")}}'
        'text{font-family:PAUCondensed,"Arial Narrow",sans-serif;fill:#000}'
        f'.title{{font-size:{title_size}px;font-weight:{title_weight}}}.cell{{font-size:{cell_size}px}}.note{{font-size:{note_size}px}}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
    ]
    for index, line in enumerate(title_lines):
        baseline = baselines[index] if index < len(baselines) else baselines[-1] + 24 * (index - len(baselines) + 1)
        parts.append(f'<text class="title" x="{width / 2:g}" y="{baseline}" text-anchor="middle">{escape(line)}</text>')
    if unit is not None:
        parts.append(f'<text class="title" x="{width / 2:g}" y="{baselines[1]}" text-anchor="middle">({escape(unit)}</text>')
    x0, y0 = layout["origin"]
    grid_width = sum(table["widths"])
    row_heights = layout["rowHeights"]
    grid_height = sum(row_heights)
    rows = [table["headers"], *table["rows"]]
    assert len(rows) == len(row_heights)
    parts.append(f'<g fill="none" stroke="#333"><rect x="{x0}" y="{y0}" width="{grid_width}" height="{grid_height}"/>')
    x = x0
    if layout.get("verticalRules", True):
        for column_width in table["widths"][:-1]:
            x += column_width
            parts.append(f'<path d="M{x} {y0}v{grid_height}"/>')
    y = y0
    for row, row_height in enumerate(row_heights[:-1]):
        y += row_height
        if row in layout.get("rulesAfter", range(len(rows) - 1)):
            parts.append(f'<path d="M{x0} {y}h{grid_width}"/>')
    parts.append("</g>")
    y = y0
    for row, (values, row_height) in enumerate(zip(rows, row_heights)):
        x = x0
        for column, (value, column_width) in enumerate(zip(values, table["widths"])):
            if row:
                parts.append(f'<g data-row="{row - 1}" data-column="{column}">')
            bold = (row == 0 and layout.get("boldHeader")) or (column == 0 and row in layout.get("boldLabels", ()))
            italic = row == 0 and layout.get("italicHeader")
            weight = ' font-weight="700"' if bold else ""
            style = ' font-style="italic"' if italic else ""
            left = column == 0 and layout.get("firstColumnLeft")
            anchor = "start" if left else "middle"
            cell_x = x + 7 if left else x + column_width / 2
            parts.append(f'<text class="cell" x="{cell_x:g}" y="{y + row_height / 2 + round(cell_size * .36):g}" '
                         f'text-anchor="{anchor}"{weight}{style}>{escape(value)}</text>')
            if row:
                parts.append("</g>")
            x += column_width
        y += row_height
    note = table["notes"][0]
    note_lines = [note]
    if "noteLines" in layout:
        note_lines = layout["noteLines"]
    elif "noteBreakBefore" in layout:
        first, marker, rest = note.partition(" " + layout["noteBreakBefore"])
        assert marker
        note_lines = [first, marker.lstrip() + rest]
    note_x, note_y = layout["notePosition"]
    for index, line in enumerate(note_lines):
        emphasis = layout.get("noteEmphasis", ())
        fragment = escape(line)
        for phrase in emphasis:
            if phrase in line:
                fragment = fragment.replace(
                    escape(phrase), f'<tspan font-style="italic">{escape(phrase)}</tspan>')
        parts.append(f'<text class="note" x="{note_x}" y="{note_y + index * (note_size + 4)}">{fragment}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n", width, height


def main():
    path = ROOT / "data/documentos.json"
    corpus = json.loads(path.read_text())
    records = {record["id"]: record for record in corpus["documents"]}
    for identity, table in TABLES.items():
        record = records[identity]
        assert record["type"] == "grafico"
        assert len(table["headers"]) == len(table["widths"])
        assert all(len(row) == len(table["headers"]) for row in table["rows"])
        image = record["image"]
        original = image.get("originalSrc", image["src"])
        original_hash = hashlib.sha256((ROOT / original).read_bytes()).hexdigest()
        appearance = record["appearances"][0]
        provenance = {
            "method": ("Tabla vectorial con diseño basado en el examen." if table.get("examLayout")
                       else "Redibujo manual, no extracción vectorial certificada del PDF."),
            "original": original, "originalSha256": original_hash,
            "pdf": appearance["pdfUrl"], "pdfSha256": appearance["sourceSha256"],
            "file": appearance["officialFile"], "page": appearance["officialPage"],
        }
        svg, width, height = render(table, provenance)
        source = f"assets/documentos/tabla-{identity}.svg"
        (ROOT / source).write_text(svg, encoding="utf-8")
        record["image"] = {
            **image, "src": source, "width": width, "height": height, "kind": "table",
            "originalSrc": original, "originalSha256": original_hash,
            "alt": f'{table["caption"]}. Tabla vectorial; los datos también están disponibles en texto.',
        }
        if table.get("examLayout"):
            record["image"].pop("reproductionNote", None)
            presentation = "Redibujo vectorial con fondo blanco y tipografía condensada, siguiendo el diseño del examen."
        else:
            record["image"]["reproductionNote"] = provenance["method"]
            presentation = "Redibujo vectorial manual con paleta azul oscuro y azul claro, sin recalcular ni corregir las cifras de la fuente."
        record["table"] = {key: value for key, value in table.items()
                           if key in ("caption", "headers", "rows", "notes", "underlinedCells")}
        record["quality"] = record["quality"].split(" La reproducción procede de este PDF;")[0].split(" Redibujo vectorial")[0] + (
            f" {presentation} Se conserva la reproducción original para comparar y una tabla de datos accesible.")
        print(f"{identity}: {width} × {height}, {len(table['rows'])} filas")
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
