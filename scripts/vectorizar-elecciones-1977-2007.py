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
    ("UCD", "#5e8fb6"),
    ("PSOE", "#c6464f"),
    ("PCE", "#8b1e3f"),
    ("AP", "#2d4d73"),
    ("PDPC", "#d1a243"),
    ("PNV", "#4f805a"),
)
OTHER_COLOR = "#92979f"


def number(value):
    return int(value.replace(" ", ""))


def decimal(value):
    return Decimal(value.replace(",", "."))


def format_percent(value, places=1):
    return f"{value:.{places}f}".replace(".", ",")


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
    other_vote_percent = sum((decimal(row[2]) for row in other_rows), Decimal(0))
    other_seats = sum(int(row[3]) for row in other_rows)
    total_vote_percent = sum((decimal(row[2]) for row in ROWS), Decimal(0))
    total_seats = sum(int(row[3]) for row in ROWS)
    if total_seats != 350:
        raise ValueError(f"Expected 350 reported seats, found {total_seats}")
    segments = [
        {
            "code": code,
            "row": rows_by_code[code],
            "votes": rows_by_code[code][1],
            "vote_percent": rows_by_code[code][2],
            "seats": int(rows_by_code[code][3]),
            "seat_percent": Decimal(rows_by_code[code][3]) * 100 / Decimal(total_seats),
            "color": color,
        }
        for code, color in MAIN_PARTIES
    ]
    segments.append({
        "code": "Otros*",
        "row": ("Otros*", f"{other_votes:,}".replace(",", " "), str(other_vote_percent).replace(".", ","), str(other_seats)),
        "votes": f"{other_votes:,}".replace(",", " "),
        "vote_percent": str(other_vote_percent).replace(".", ","),
        "seats": other_seats,
        "seat_percent": Decimal(other_seats) * 100 / Decimal(total_seats),
        "color": OTHER_COLOR,
    })

    width, height = 760, 640
    cx, cy, outer, inner = 230, 370, 185, 78
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Elecciones de 1977: distribución proporcional de escaños</title>',
        '<desc id="desc">Diagrama semicircular de las elecciones del 15 de junio de 1977. Los sectores son proporcionales a los escaños obtenidos sobre un total de 350. La leyenda muestra los escaños, su porcentaje, los votos y el porcentaje de votos. Las candidaturas menores se agrupan como Otros.</desc>',
        f'<metadata>{escape(json.dumps({"method": "Redibujo vectorial semicircular con sectores proporcionales a escaños; paleta editorial, no presente en el original.", "original": record["image"]["src"], "originalSha256": hashlib.sha256((ROOT / record["image"]["src"]).read_bytes()).hexdigest(), "pdf": record["appearances"][0]["pdfUrl"], "pdfSha256": record["appearances"][0]["sourceSha256"], "dataSource": DATA_SOURCE, "page": record["appearances"][0]["officialPage"]}, ensure_ascii=False))}</metadata>',
        '<style>text{font-family:"Arial Narrow",Arial,sans-serif;fill:#25343b}.title{font-size:22px;font-weight:700;fill:#223e4b}.subtitle{font-size:13px;fill:#53666e}.party{font-size:15px;font-weight:700}.share{font-size:13px;font-weight:600}.metric{font-size:12px;fill:#53666e}.year{font-size:22px;font-weight:700;fill:#53666e}.center-seat{font-size:11px;fill:#53666e}.footnote{font-size:12px}.source{font-size:11px;fill:#59666b}.sector{stroke:#fff;stroke-width:2}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        '<text class="title" x="380" y="32" text-anchor="middle">Elecciones generales de 1977 (15 de junio)</text>',
        '<text class="subtitle" x="380" y="55" text-anchor="middle">Sectores proporcionales a escaños; el voto también se indica.</text>',
    ]

    angle = 180.0
    for index, segment in enumerate(segments):
        fraction = segment["seats"] / total_seats
        end = angle - 180 * fraction
        path = annular_sector(cx, cy, outer, inner, angle, end)
        output.append(
            f'<path class="sector" data-party="{escape(segment["code"])}" '
            f'data-seats="{segment["seats"]}" data-seat-percent="{segment["seat_percent"]:.3f}" '
            f'fill="{segment["color"]}" d="{path}"/>'
        )
        row_y = 112 + index * 52
        vote_percent = segment["vote_percent"]
        output.extend([
            f'<rect x="430" y="{row_y - 12}" width="14" height="14" rx="2" fill="{segment["color"]}"/>',
            f'<text class="party" x="454" y="{row_y}">{escape(segment["code"])}</text>',
            f'<text class="share" x="744" y="{row_y}" text-anchor="end">'
            f'{segment["seats"]} escaños · {format_percent(segment["seat_percent"])} %</text>',
            f'<text class="metric" x="454" y="{row_y + 18}">'
            f'{escape(vote_percent)} % de votos · {escape(segment["votes"])} votos</text>',
        ])
        angle = end

    other_seat_details = " · ".join(
        f'{row[0].split(" — ", 1)[0]} {row[3]}' for row in other_rows if int(row[3])
    )
    output.extend([
        f'<circle cx="{cx}" cy="{cy}" r="{inner - 1}" fill="#fff"/>',
        f'<text class="year" x="{cx}" y="{cy - 22}" text-anchor="middle">1977</text>',
        f'<text class="center-seat" x="{cx}" y="{cy - 5}" text-anchor="middle">{total_seats} escaños</text>',
        f'<text class="footnote" x="380" y="520" text-anchor="middle">* Otros agrupa candidaturas menores; sus {other_seats} escaños: {escape(other_seat_details)}.</text>',
        '<text class="footnote" x="380" y="542" text-anchor="middle">Escaños (%) = escaños / 350; colores editoriales, no reproducidos del examen.</text>',
        f'<text class="footnote" x="380" y="564" text-anchor="middle">Los porcentajes de votos se conservan como en la tabla (suman {format_percent(total_vote_percent, 2)} %).</text>',
        f'<text class="source" x="380" y="606" text-anchor="middle">Cifras: tabla aportada por el usuario · Material: {escape(record["appearances"][0]["exam"])}, {escape(record["appearances"][0]["route"])}</text>',
        "</svg>",
    ])
    return (
        "\n".join(output) + "\n", segments, other_rows, other_votes, other_vote_percent,
        other_seats, total_vote_percent, total_seats,
    )


def main():
    path = ROOT / "data/documentos.json"
    corpus = json.loads(path.read_text(encoding="utf-8"))
    record = next(item for item in corpus["documents"] if item["id"] == "elecciones-1977-diagrama")
    (
        svg, segments, other_rows, other_votes, other_vote_percent,
        other_seats, total_vote_percent, total_seats,
    ) = build_svg(record)
    (ROOT / OUTPUT).write_text(svg, encoding="utf-8")
    record["sourceCaption"] = (
        "Material de 2007, Examen 4, Bloque II · Opción B. "
        "Cifras actualizadas con la tabla de resultados aportada por el usuario."
    )
    record["quality"] = (
        "Diagrama semicircular redibujado a partir del material del examen. "
        "Los sectores son proporcionales a los 350 escaños, no a los votos. Los colores son editoriales, "
        "inspirados en asociaciones cromáticas de los partidos y no atribuidos al gráfico original. "
        "Las cifras se transcriben de la tabla aportada por el usuario; la tabla accesible detalla "
        "las candidaturas agrupadas en «Otros*» y calcula el porcentaje de escaños."
    )
    record["image"] = {
        **record["image"],
        "src": OUTPUT,
        "width": 760,
        "height": 640,
        "kind": "chart",
        "originalSrc": "assets/documentos/pdf-2007-4-4.png",
        "originalSha256": hashlib.sha256(
            (ROOT / "assets/documentos/pdf-2007-4-4.png").read_bytes()
        ).hexdigest(),
        "alt": (
            "Diagrama semicircular de los resultados de 1977, proporcional a los 350 escaños: "
            "la UCD obtuvo 165, el 47,1 %. La leyenda muestra votos y escaños por candidatura."
        ),
        "reproductionNote": (
            "Sectores proporcionales a escaños; el reparto de votos y las cifras proceden de la "
            "tabla aportada por el usuario. Colores editoriales, no reproducidos del examen."
        ),
    }
    rows = [
        [
            party, votes, percent, int(seats),
            format_percent(Decimal(seats) * 100 / Decimal(total_seats)),
        ]
        for party, votes, percent, seats in ROWS
    ]
    breakdown = ", ".join(
        f'{row[0].split(" — ", 1)[0]} ({row[3]})' for row in other_rows
    )
    other_votes_formatted = f"{other_votes:,}".replace(",", ".")
    other_percent_formatted = format_percent(other_vote_percent, 2)
    notes = [
        "Votos, porcentajes de voto y escaños se transcriben de la tabla de resultados aportada por el usuario. "
        "El porcentaje de escaños se calcula a partir de los 350 escaños y se redondea a una décima.",
        f"Otros* agrupa {len(other_rows)} candidaturas: {breakdown}. "
        f"En conjunto suman {other_votes_formatted} votos, {other_percent_formatted} % y {other_seats} escaños.",
        f"Los porcentajes de votos aportados suman {format_percent(total_vote_percent, 2)} % y se conservan sin cambios. "
        "Las cuñas representan los escaños, no los votos.",
        f"Referencia de datos compartida por el usuario: {DATA_SOURCE}",
    ]
    record["table"] = {
        "caption": "Elecciones generales de 1977: votos y distribución de escaños",
        "headers": ["Partido o candidatura", "Votos", "Votos (%)", "Escaños", "Escaños (%)"],
        "rows": rows,
        "notes": notes,
    }
    record["dataSourceUrl"] = DATA_SOURCE
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{OUTPUT}: {len(segments)} semicircle sectors, "
        f"{len(rows)} accessible rows, UCD=165/{total_seats} seats, Others*={other_seats} seats"
    )


if __name__ == "__main__":
    main()
