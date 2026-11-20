"""Rebuild the 2002 social-composition pie chart as an accessible SVG."""
import hashlib
import json
from base64 import b64encode
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
IDENTITY = "sociedad-espanola-1860"
SOURCE = "assets/documentos/pdf-2002-4-2.png"
OUTPUT = "assets/documentos/grafico-sociedad-espanola-1860.svg"
COLORS = {
    "Nobleza y clero": ("#c58b36", "#f7efdf"),
    "Burguesía alta": ("#b75d4e", "#f5e9e6"),
    "Clases medias": ("#54877d", "#e7f0ed"),
    "Clases bajas": ("#596d8b", "#e9edf3"),
}
VALUES = [
    ("Nobleza y clero", 16),
    ("Burguesía alta", 3),
    ("Clases medias", 10),
    ("Clases bajas", 71),
]
WIDTH, HEIGHT = 593, 419
CX, CY, RADIUS = 309, 231, 167


def sector_path(start_angle, percentage):
    import math

    end_angle = start_angle + percentage * 3.6

    def point(angle):
        radians = math.radians(angle)
        return CX + RADIUS * math.cos(radians), CY + RADIUS * math.sin(radians)

    start = point(start_angle)
    end = point(end_angle)
    large_arc = int(percentage > 50)
    return (
        f"M {CX} {CY} L {start[0]:.3f} {start[1]:.3f} "
        f"A {RADIUS} {RADIUS} 0 {large_arc} 1 {end[0]:.3f} {end[1]:.3f} Z"
    )


def build_svg(provenance):
    font = b64encode((ROOT / "assets/fonts/RobotoCondensed-Regular.ttf").read_bytes()).decode("ascii")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        'viewBox="0 28 593 419" role="img" aria-labelledby="title description">',
        '<title id="title">Composición de la sociedad española hacia 1860</title>',
        '<desc id="description">Gráfico circular con cuatro grupos sociales: nobleza y clero, '
        '16 %; burguesía alta, 3 %; clases medias, 10 %; clases bajas, 71 %.</desc>',
        f'<metadata>{escape(json.dumps(provenance, ensure_ascii=False))}</metadata>',
        '<style>@font-face{font-family:PAUCondensed;src:local("Arial Narrow"),'
        'local("ArialNarrow"),'
        f'url(data:font/ttf;base64,{font}) format("truetype")}}'
        'text{font-family:PAUCondensed,"Arial Narrow",sans-serif;fill:#202a33}'
        '.category{font-size:17px}'
        '.percentage{font-size:18px;font-weight:600}'
        '.sector{stroke:#fff;stroke-width:2;stroke-linejoin:round}'
        '</style>',
        '<rect x="0" y="28" width="593" height="419" fill="#fff"/>',
        '<rect x="8" y="28" width="576" height="411" fill="none" stroke="#b8b8b8"/>',
    ]

    angle = -90
    for label, percentage in VALUES:
        color, _ = COLORS[label]
        parts.append(
            f'<path class="sector" d="{sector_path(angle, percentage)}" '
            f'fill="{color}" data-category="{escape(label)}" '
            f'data-percentage="{percentage}"><title>{escape(label)}: {percentage} %</title></path>'
        )
        angle += percentage * 3.6
    parts.append(
        f'<circle cx="{CX}" cy="{CY}" r="{RADIUS}" fill="none" '
        'stroke="#26313b" stroke-width="2"/>'
    )

    labels = [
        ("Nobleza y clero", "Nobleza", "y clero", 331, 87, 102, 55),
        ("Burguesía alta", "Burguesía", "alta", 464, 69, 102, 55),
        ("Clases medias", "Clases", "medias", 482, 227, 80, 57),
        ("Clases bajas", "Clases", "bajas", 239, 302, 81, 66),
    ]
    for label, first, second, x, y, width, height in labels:
        color, tint = COLORS[label]
        parts.extend([
            f'<g data-category-label="{escape(label)}">',
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="2" fill="{tint}" stroke="{color}" stroke-width="1.5"/>',
            f'<text class="category" x="{x + width / 2}" y="{y + 22}" '
            f'text-anchor="middle">{escape(first)}</text>',
            f'<text class="category" x="{x + width / 2}" y="{y + 43}" '
            f'text-anchor="middle">{escape(second)}</text>',
            '</g>',
        ])

    for label, text, x, y, anchor in (
        ("Nobleza y clero", "16%", 397, 72, "start"),
        ("Burguesía alta", "3%", 477, 148, "start"),
        ("Clases medias", "10%", 484, 219, "start"),
        ("Clases bajas", "71%", 141, 355, "start"),
    ):
        parts.append(
            f'<text class="percentage" x="{x}" y="{y}" text-anchor="{anchor}" '
            f'data-category-percentage="{escape(label)}">{text}</text>'
        )
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main():
    corpus_path = ROOT / "data/documentos.json"
    corpus = json.loads(corpus_path.read_text())
    record = next(item for item in corpus["documents"] if item["id"] == IDENTITY)
    appearance = record["appearances"][0]
    original_path = ROOT / SOURCE
    original_hash = hashlib.sha256(original_path.read_bytes()).hexdigest()
    provenance = {
        "method": "Redibujo vectorial del gráfico original; porcentajes y categorías conservados.",
        "original": SOURCE,
        "originalSha256": original_hash,
        "pdf": appearance["pdfUrl"],
        "pdfSha256": appearance["sourceSha256"],
        "file": appearance["officialFile"],
        "page": appearance["officialPage"],
    }
    (ROOT / OUTPUT).write_text(build_svg(provenance), encoding="utf-8")
    record["image"] = {
        **record["image"],
        "src": OUTPUT,
        "width": WIDTH,
        "height": HEIGHT,
        "alt": "Gráfico circular de la composición social hacia 1860, redibujado en vector "
               "con colores editoriales para distinguir sus cuatro grupos.",
        "kind": "chart",
        "originalSrc": SOURCE,
        "originalSha256": original_hash,
    }
    record["image"].pop("reproductionNote", None)
    record["examCaption"] = {
        "text": "Composición de la sociedad española hacia 1860",
        "appearanceId": appearance["id"],
    }
    record["quality"] = (
        "Fuente directa: PDF del examen aportado. Se conserva el material de esa selección, "
        "sin completarlo con otra versión ni atribuirlo a Google Docs. Redibujo vectorial con "
        "colores editoriales; categorías y porcentajes conservados sin cambios."
    )
    record["table"] = {
        "caption": "Composición de la sociedad española hacia 1860 (porcentajes)",
        "headers": ["Grupo social", "Porcentaje"],
        "rows": [[label, str(percentage)] for label, percentage in VALUES],
        "notes": [],
    }
    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{OUTPUT}: gráfico vectorial de {len(VALUES)} grupos sociales.")


if __name__ == "__main__":
    main()
