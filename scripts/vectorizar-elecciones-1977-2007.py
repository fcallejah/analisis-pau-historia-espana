"""Rebuild the 2007 election diagram as an accessible semicircular SVG."""
from decimal import Decimal
from html import escape
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = "assets/documentos/elecciones-1977-diagrama-semicircular.svg"
DATA_SOURCE = (
    "https://es.wikipedia.org/wiki/"
    "Elecciones_generales_de_Espa%C3%B1a_de_1977"
)

ROWS = [
    ("UCD — Unión de Centro Democrático", "6 310 391", "34,44", "165"),
    ("PSOE — Partido Socialista Obrero Español", "5 371 866", "29,32", "118"),
    ("PCE — Partido Comunista de España", "1 709 890", "9,33", "20"),
    ("AP — Federación de Partidos de Alianza Popular", "1 504 771", "8,21", "16"),
    ("PSP-US — Partido Socialista Popular-Unidad Socialista", "816 582", "4,46", "6"),
    ("PDPC — Pacte Democràtic per Catalunya", "514 647", "2,81", "11"),
    ("PNV — Partido Nacionalista Vasco", "296 193", "1,62", "8"),
    ("FDC-EDC — Equipo de la Democracia Cristiana", "215 841", "1,18", "0"),
    ("DCC — Unió del Centre i la Democràcia Cristiana de Catalunya", "172 791", "0,94", "2"),
    ("EC-FED — Esquerra de Catalunya", "143 954", "0,79", "1"),
    ("FDI — Frente Democrático de Izquierdas", "122 608", "0,67", "0"),
    ("ASDCI — Alianza Socialista Democrática", "101 916", "0,56", "0"),
    ("AET — Agrupación Electoral de Trabajadores", "77 575", "0,42", "0"),
    ("AN18 — Alianza Nacional 18 de Julio", "67 336", "0,37", "0"),
    ("RSE — Reforma Social Española", "64 241", "0,35", "0"),
    ("EE — Euskadiko Ezkerra", "61 417", "0,34", "1"),
    ("CAI — Candidatura Aragonesa Independiente de Centro", "37 183", "0,20", "1"),
    ("INDEP — Candidatura Independiente de Centro", "29 834", "0,16", "1"),
    ("Otros partidos", "723 290", "2,97", "0"),
]

MAIN_PARTIES = (
    ("UCD", "UCD", "#26736f", (55, 190), "start", (238, 278)),
    ("PSOE", "PSOE", "#4f74a4", (455, 106), "middle", (455, 145)),
    ("PCE", "PCE", "#c56a53", (650, 78), "middle", (650, 116)),
    ("AP", "AP", "#c39437", (815, 150), "start", (805, 180)),
    ("PDPC", "PDC", "#8b78a8", (825, 244), "start", (810, 263)),
    ("PNV", "PNV", "#73986c", (825, 338), "start", (810, 357)),
)
OTHER_COLOR = "#bb718c"


def number(value):
    return int(value.replace(" ", ""))


def decimal(value):
    return Decimal(value.replace(",", "."))


def svg_point(cx, cy, radius, angle_degrees):
    angle = math.radians(angle_degrees)
    return cx + radius * math.cos(angle), cy - radius * math.sin(angle)


def annular_sector(cx, cy, outer, inner, start, end):
    x1, y1 = svg_point(cx, cy, outer, start)
    x2, y2 = svg_point(cx, cy, outer, end)
    x3, y3 = svg_point(cx, cy, inner, end)
    x4, y4 = svg_point(cx, cy, inner, start)
    return (
        f"M{x1:.2f},{y1:.2f} A{outer},{outer} 0 0 1 {x2:.2f},{y2:.2f} "
        f"L{x3:.2f},{y3:.2f} A{inner},{inner} 0 0 0 {x4:.2f},{y4:.2f} Z"
    )


def build_svg(record):
    rows_by_code = {row[0].split(" — ", 1)[0].split(" ")[0]: row for row in ROWS}
    main_codes = {item[0] for item in MAIN_PARTIES}
    other_rows = [row for row in ROWS if row[0].split(" — ", 1)[0].split(" ")[0] not in main_codes]
    other_votes = sum(number(row[1]) for row in other_rows)
    other_percent = sum((decimal(row[2]) for row in other_rows), Decimal(0))
    other_seats = sum(int(row[3]) for row in other_rows)
    total_percent = sum((decimal(row[2]) for row in ROWS), Decimal(0))
    segments = [
        {
            "code": label,
            "row": rows_by_code[code],
            "percent": decimal(rows_by_code[code][2]),
            "color": color,
            "position": position,
            "anchor": anchor,
            "line_end": line_end,
        }
        for code, label, color, position, anchor, line_end in MAIN_PARTIES
    ]
    segments.append({
        "code": "Otros*",
        "row": ("Otros*", f"{other_votes:,}".replace(",", " "), str(other_percent).replace(".", ","), str(other_seats)),
        "percent": other_percent,
        "color": OTHER_COLOR,
        "position": (825, 430),
        "anchor": "start",
        "line_end": (810, 449),
    })

    width, height = 1080, 760
    cx, cy, outer, inner = 500, 425, 248, 105
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Resultados electorales de 1977: votos y escaños</title>',
        '<desc id="desc">Diagrama semicircular de las elecciones del 15 de junio de 1977. Los segmentos representan porcentajes de votos; las etiquetas indican votos y escaños. Las candidaturas menores se reúnen en Otros.</desc>',
        f'<metadata>{escape(json.dumps({"method": "Redibujo vectorial semicircular; cifras numéricas actualizadas a partir de la tabla aportada por el usuario.", "original": record["image"]["src"], "originalSha256": hashlib.sha256((ROOT / record["image"]["src"]).read_bytes()).hexdigest(), "pdf": record["appearances"][0]["pdfUrl"], "pdfSha256": record["appearances"][0]["sourceSha256"], "dataSource": DATA_SOURCE, "page": record["appearances"][0]["officialPage"]}, ensure_ascii=False))}</metadata>',
        '<style>text{font-family:"Arial Narrow",Arial,sans-serif;fill:#25343b}.title{font-size:26px;font-weight:700;fill:#223e4b}.subtitle{font-size:16px;fill:#53666e}.party{font-size:20px;font-weight:700}.metric{font-size:15px}.seat{font-size:15px;font-weight:600}.year{font-size:23px;font-weight:700;fill:#53666e}.footnote{font-size:15px}.source{font-size:13px;fill:#59666b}.sector{stroke:#fff;stroke-width:2}.leader{fill:none;stroke:#59666b;stroke-width:1.5}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        '<text class="title" x="540" y="40" text-anchor="middle">Resultado de las elecciones de 1977 (15 de junio)</text>',
        '<text class="subtitle" x="540" y="69" text-anchor="middle">Los sectores representan votos; cada rótulo indica también los escaños obtenidos.</text>',
    ]

    angle = 180.0
    for segment in segments:
        fraction = float(segment["percent"] / total_percent)
        end = angle - 180 * fraction
        path = annular_sector(cx, cy, outer, inner, angle, end)
        output.append(
            f'<path class="sector" data-party="{escape(segment["code"])}" '
            f'data-vote-percent="{segment["percent"]}" fill="{segment["color"]}" d="{path}"/>'
        )
        middle = (angle + end) / 2
        start_point = svg_point(cx, cy, outer + 4, middle)
        end_point = segment["line_end"]
        line_path = f"M{start_point[0]:.1f},{start_point[1]:.1f} L{end_point[0]},{end_point[1]}"
        output.append(f'<path class="leader" d="{line_path}"/>')
        label_x, label_y = segment["position"]
        anchor = segment["anchor"]
        party, votes, percent, seats = segment["row"]
        output.extend([
            f'<text class="party" x="{label_x}" y="{label_y}" text-anchor="{anchor}">{escape(segment["code"])}</text>',
            f'<text class="metric" x="{label_x}" y="{label_y + 22}" text-anchor="{anchor}">{percent}% · {votes} votos</text>',
            f'<text class="seat" x="{label_x}" y="{label_y + 42}" text-anchor="{anchor}">{seats} escaños</text>',
        ])
        angle = end

    output.extend([
        f'<circle cx="{cx}" cy="{cy}" r="{inner - 1}" fill="#fff"/>',
        f'<text class="year" x="{cx}" y="{cy + 7}" text-anchor="middle">1977</text>',
        '<text class="footnote" x="540" y="598" text-anchor="middle">* Otros escaños: PSP-US 6 · DCC 2 · EC-FED 1 · EE 1 · CAI 1 · Candidatura Independiente 1.</text>',
        '<text class="footnote" x="540" y="625" text-anchor="middle">Las candidaturas menores se agrupan en Otros*; el detalle completo queda en la tabla accesible.</text>',
        '<text class="footnote" x="540" y="652" text-anchor="middle">Los porcentajes facilitados suman 99,14 %; los sectores se normalizan proporcionalmente para cerrar el semicírculo.</text>',
        f'<text class="source" x="540" y="710" text-anchor="middle">Cifras: tabla aportada por el usuario · Material: {escape(record["appearances"][0]["exam"])}, {escape(record["appearances"][0]["route"])}</text>',
        "</svg>",
    ])
    return "\n".join(output) + "\n", segments, other_rows, other_votes, other_percent, other_seats, total_percent


def main():
    path = ROOT / "data/documentos.json"
    corpus = json.loads(path.read_text(encoding="utf-8"))
    record = next(item for item in corpus["documents"] if item["id"] == "elecciones-1977-diagrama")
    svg, segments, other_rows, other_votes, other_percent, other_seats, total_percent = build_svg(record)
    (ROOT / OUTPUT).write_text(svg, encoding="utf-8")
    record["sourceCaption"] = (
        "Material de 2007, Examen 4, Bloque II · Opción B. "
        "Cifras actualizadas con la tabla de resultados aportada por el usuario."
    )
    record["quality"] = (
        "Diagrama semicircular redibujado a partir del material del examen. "
        "Los colores y la geometría son editoriales; se utilizan las cifras aportadas "
        "por el usuario en lugar de las cifras redondeadas impresas en el gráfico original. "
        "La tabla accesible conserva el detalle por candidatura y explica la agrupación «Otros*»."
    )
    record["image"] = {
        **record["image"],
        "src": OUTPUT,
        "width": 1080,
        "height": 760,
        "kind": "chart",
        "originalSrc": "assets/documentos/pdf-2007-4-4.png",
        "originalSha256": hashlib.sha256(
            (ROOT / "assets/documentos/pdf-2007-4-4.png").read_bytes()
        ).hexdigest(),
        "alt": (
            "Diagrama semicircular de los resultados de 1977; las etiquetas comparan votos "
            "y escaños de seis candidaturas y de Otros. Colores editoriales."
        ),
        "reproductionNote": (
            "Vectorización editorial con cifras aportadas por el usuario; la imagen original "
            "del examen se conserva para comparar las cifras redondeadas."
        ),
    }
    main_codes = {item[0] for item in MAIN_PARTIES}
    rows = [
        [party, votes, percent, int(seats)]
        for party, votes, percent, seats in ROWS
    ]
    breakdown = ", ".join(
        f'{row[0].split(" — ", 1)[0]} ({row[3]})' for row in other_rows
    )
    other_votes_formatted = f"{other_votes:,}".replace(",", ".")
    other_percent_formatted = str(other_percent).replace(".", ",")
    notes = [
        "Cifras numéricas transcritas de la tabla de resultados aportada por el usuario. "
        "Se omiten nombres de candidatos y observaciones de coalición, que no aparecen en el gráfico del examen.",
        f"Otros* agrupa {len(other_rows)} candidaturas: {breakdown}. "
        f"En conjunto suman {other_votes_formatted} votos, {other_percent_formatted} % y {other_seats} escaños.",
        f"Los porcentajes de todas las filas suman {str(total_percent).replace('.', ',')} %. "
        "Las cuñas del semicírculo se normalizan proporcionalmente para cerrar el trazado; "
        "las etiquetas conservan los porcentajes aportados.",
        f"Referencia de datos compartida por el usuario: {DATA_SOURCE}",
    ]
    record["table"] = {
        "caption": "Elecciones generales de 1977: votos, porcentajes y escaños",
        "headers": ["Partido o candidatura", "Votos", "Votos (%)", "Escaños"],
        "rows": rows,
        "notes": notes,
    }
    record["dataSourceUrl"] = DATA_SOURCE
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{OUTPUT}: {len(segments)} semicircle sectors, "
        f"{len(rows)} accessible rows, Others*={other_seats} seats"
    )


if __name__ == "__main__":
    main()
