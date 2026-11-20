"""Rebuild the 2007 election diagram as an accessible semicircular SVG."""
import hashlib
import json
import math
import textwrap
from decimal import Decimal
from html import escape
from pathlib import Path

from elecciones_1977 import (
    EXAM_OTHER_SEATS,
    EXAM_UCD_SEATS,
    MINISTRY_SOURCE,
    MINISTRY_UCD_VOTES,
    RESULTS,
    SOURCE,
    seats_percent,
    votes_text,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = "assets/documentos/elecciones-1977-diagrama-semicircular.svg"

MAIN_PARTIES = (
    ("UCD", "Unión de Centro Democrático (UCD)", "#315a29"),
    ("PSOE", "Partido Socialista Obrero Español (PSOE) + Partit dels Socialistes de Catalunya (PSC-PSOE)", "#c6464f"),
    ("PCE", "Partido Comunista de España (PCE) + Partit Socialista Unificat de Catalunya (PSUC)", "#8b1e3f"),
    ("AP", "Alianza Popular (AP)", "#2d4d73"),
    ("PDC", "Pacte Democràtic per Catalunya (PDC)", "#d1a243"),
    ("PNV", "Partido Nacionalista Vasco (PNV)", "#4f805a"),
)
OTHER_COLOR = "#92979f"


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
    rows_by_code = {row[0]: row for row in RESULTS}
    original_src = record["image"].get("originalSrc", record["image"]["src"])
    original_path = ROOT / original_src
    main_codes = {item[0] for item in MAIN_PARTIES}
    other_rows = [row for row in RESULTS if row[0] not in main_codes]
    other_votes = sum(row[2] for row in other_rows)
    other_seats = EXAM_OTHER_SEATS
    total_seats = sum(row[3] for row in RESULTS)
    if total_seats != 350:
        raise ValueError(f"Expected 350 source seats, found {total_seats}")
    segments = [
        {
            "code": code,
            "row": rows_by_code[code],
            "votes": votes_text(
                MINISTRY_UCD_VOTES if code == "UCD" else rows_by_code[code][2]
            ),
            "seats": EXAM_UCD_SEATS if code == "UCD" else rows_by_code[code][3],
            "seat_percent": Decimal(
                EXAM_UCD_SEATS if code == "UCD" else rows_by_code[code][3]
            ) * 100 / Decimal(total_seats),
            "label": label,
            "color": color,
        }
        for code, label, color in MAIN_PARTIES
    ]
    segments.append({
        "code": "Otros*",
        "label": "Otros*",
        "votes": votes_text(other_votes),
        "seats": other_seats,
        "seat_percent": Decimal(other_seats) * 100 / Decimal(total_seats),
        "color": OTHER_COLOR,
    })
    if sum(segment["seats"] for segment in segments) != total_seats:
        raise ValueError("The exam's grouped seat totals must sum to 350")

    width = 760
    cx, cy, outer, inner = 230, 370, 185, 78
    labels = []
    for segment in segments:
        lines = textwrap.wrap(segment["label"], width=30, break_long_words=False, break_on_hyphens=False)
        suffix = f'· {segment["seats"]} {"escaño" if segment["seats"] == 1 else "escaños"}'
        if len(lines[-1]) + 1 + len(suffix) <= 30:
            lines[-1] += " " + suffix
        else:
            lines.append(suffix)
        labels.append(lines)
    row_heights = [max(52, len(lines) * 18 + 34) for lines in labels]
    footer_y = max(515, 112 + sum(row_heights) + 12)
    height = footer_y + 30
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Resultado elecciones 1977 (15 de junio)</title>',
        '<desc id="desc">Diagrama semicircular de votos y escaños. La Unión de Centro Democrático (UCD) se presenta con 166 escaños y «Otros*» con 11, según la agrupación del material del examen; los votos de UCD corresponden a la cifra consolidada del Ministerio del Interior y las demás candidaturas al resumen de la JEC. «Otros*» no es un grupo parlamentario.</desc>',
        f'<metadata>{escape(json.dumps({"method": "Redibujo vectorial proporcional a escaños, con la agrupación del material del examen; votos de UCD según el Ministerio del Interior y resto según la JEC.", "original": original_src, "originalSha256": hashlib.sha256(original_path.read_bytes()).hexdigest(), "pdf": record["appearances"][0]["pdfUrl"], "pdfSha256": record["appearances"][0]["sourceSha256"], "dataSource": SOURCE, "ministrySource": MINISTRY_SOURCE, "page": record["appearances"][0]["officialPage"]}, ensure_ascii=False))}</metadata>',
        '<style>text{font-family:"Arial Narrow",Arial,sans-serif;fill:#25343b}.title{font-size:22px;font-weight:700;fill:#223e4b}.party{font-size:14px;font-weight:700}.share{font-size:13px;font-weight:600}.metric{font-size:12px;fill:#53666e}.center-seat{font-size:18px;font-weight:700;fill:#53666e}.center-majority{font-size:12px;fill:#53666e}.footnote{font-size:12px}.sector{stroke:#fff;stroke-width:2}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        '<text class="title" x="380" y="32" text-anchor="middle">Resultado elecciones 1977 (15 de junio)</text>',
    ]

    angle = 180.0
    y = 112
    for segment, lines, row_height in zip(segments, labels, row_heights):
        fraction = segment["seats"] / total_seats
        end = angle - 180 * fraction
        path = annular_sector(cx, cy, outer, inner, angle, end)
        output.append(
            f'<path class="sector" data-party="{escape(segment["code"])}" '
            f'data-seats="{segment["seats"]}" data-seat-percent="{segment["seat_percent"]:.3f}" '
            f'fill="{segment["color"]}" d="{path}"/>'
        )
        output.append(
            f'<rect x="430" y="{y - 12}" width="14" height="14" rx="2" fill="{segment["color"]}"/>'
        )
        for line_index, line in enumerate(lines):
            line_y = y + line_index * 18
            output.append(f'<text class="party" x="454" y="{line_y}">{escape(line)}</text>')
            if line_index == 0:
                output.append(
                    f'<text class="share" x="744" y="{line_y}" text-anchor="end">'
                    f'{seats_percent(segment["seats"])} %</text>'
                )
        output.append(
            f'<text class="metric" x="454" y="{y + len(lines) * 18}">'
            f'{escape(segment["votes"])} votos</text>'
        )
        y += row_height
        angle = end

    output.extend([
        f'<line class="majority-divider" x1="{cx}" y1="{cy - outer}" x2="{cx}" y2="{cy - inner}" stroke="#fff" stroke-width="2" stroke-dasharray="5 4"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{inner - 1}" fill="#fff"/>',
        f'<text class="center-seat" x="{cx}" y="{cy - 37}" text-anchor="middle">{total_seats}</text>',
        f'<text class="center-majority" x="{cx}" y="{cy - 21}" text-anchor="middle">escaños</text>',
        f'<text class="center-majority" x="{cx}" y="{cy - 5}" text-anchor="middle">176 para la mayoría</text>',
        f'<text class="footnote" x="380" y="{footer_y}" text-anchor="middle">Agrupación del examen: Unión de Centro Democrático (UCD), 166 escaños; Otros*, 11.</text>',
        f'<text class="footnote" x="380" y="{footer_y + 20}" text-anchor="middle">Votos de Unión de Centro Democrático (UCD): Ministerio del Interior; demás votos: JEC.</text>',
        "</svg>",
    ])
    return "\n".join(output) + "\n", segments, other_rows, other_votes, other_seats, total_seats, height


def main():
    path = ROOT / "data/documentos.json"
    corpus = json.loads(path.read_text(encoding="utf-8"))
    record = next(item for item in corpus["documents"] if item["id"] == "elecciones-1977-diagrama")
    svg, segments, other_rows, other_votes, other_seats, total_seats, image_height = build_svg(record)
    (ROOT / OUTPUT).write_text(svg, encoding="utf-8")
    record["sourceCaption"] = (
        "Material de 2007, Examen 4, Bloque II · Opción B. "
        "Votos de UCD según el Ministerio del Interior; demás candidaturas contrastadas con la JEC."
    )
    record["quality"] = (
        "Diagrama semicircular redibujado a partir del material del examen. "
        "Los sectores son proporcionales a los 350 escaños. La agrupación electoral del material del examen "
        "presenta UCD con 166 escaños y Otros* con 11. La cifra consolidada de votos de UCD es 6 310 391, "
        "publicada por el Ministerio del Interior; las demás cifras de votos proceden del resumen de la JEC. "
        "«Otros*» agrupa candidaturas electorales y no es un grupo parlamentario."
    )
    image = dict(record["image"])
    image.pop("reproductionNote", None)
    record["image"] = {
        **image,
        "src": OUTPUT,
        "width": 760,
        "height": image_height,
        "kind": "chart",
        "originalSrc": "assets/documentos/pdf-2007-4-4.png",
        "originalSha256": hashlib.sha256(
            (ROOT / "assets/documentos/pdf-2007-4-4.png").read_bytes()
        ).hexdigest(),
        "alt": (
            "Resultado elecciones 1977 (15 de junio): diagrama de votos y escaños; "
            "Unión de Centro Democrático (UCD) figura con 166 escaños según el agrupamiento del examen."
        ),
    }
    rows = [
        [segment["code"], segment["votes"], segment["seats"], seats_percent(segment["seats"])]
        for segment in segments
    ]
    notes = [
        "La cifra de votos de UCD se actualiza a 6 310 391 según el Ministerio del Interior; los demás votos se mantienen según el resumen de la JEC.",
        "El reparto visible sigue la agrupación del material del examen: UCD suma 166 escaños y Otros* 11. Otros* agrupa candidaturas electorales; no es un grupo parlamentario.",
        "PSOE incluye PSC-PSOE; PCE incluye PSUC. El resumen de resultados de la JEC enlazado permite consultar el desglose original por candidatura.",
        f"Fuente: Junta Electoral Central, resumen de resultados, página 5: {SOURCE}",
        f"Fuente del voto de UCD: Ministerio del Interior, Infoelectoral: {MINISTRY_SOURCE}",
    ]
    record["table"] = {
        "caption": "Resultado elecciones 1977 (15 de junio)",
        "headers": ["Partido o candidatura con escaño", "Votos", "Escaños", "Escaños (%)"],
        "rows": rows,
        "notes": notes,
    }
    record["dataSourceUrl"] = SOURCE
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{OUTPUT}: {len(segments)} semicircle sectors, "
        f"{len(rows)} accessible rows, UCD={EXAM_UCD_SEATS}/{total_seats} seats, "
        f"Others*={other_seats} seats"
    )


if __name__ == "__main__":
    main()
