"""Generate election semicircles from the JEC-based study tables."""
import json
import math
import re
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/documentos-propios.json"
OUTPUT = ROOT / "assets/documentos"
COLORS = (
    "#315a29", "#c6464f", "#2d4d73", "#d1a243", "#8b1e3f",
    "#4f805a", "#7d5da5", "#c7703a", "#347f89", "#8a6e53",
    "#b34978", "#7b882e", "#6d647e", "#bf8b6a", "#527ca1",
    "#b1a13d", "#8c5252", "#42735f", "#6c7889",
)
OTHER_COLOR = "#92979f"


def point(cx, cy, radius, angle):
    angle = math.radians(angle)
    return cx + radius * math.cos(angle), cy - radius * math.sin(angle)


def sector(cx, cy, outer, inner, start, end):
    x1, y1 = point(cx, cy, outer, start)
    x2, y2 = point(cx, cy, outer, end)
    x3, y3 = point(cx, cy, inner, end)
    x4, y4 = point(cx, cy, inner, start)
    return (f"M{x1:.2f},{y1:.2f} A{outer},{outer} 0 0 1 {x2:.2f},{y2:.2f} "
            f"L{x3:.2f},{y3:.2f} A{inner},{inner} 0 0 0 {x4:.2f},{y4:.2f} Z")


def colors_for(rows):
    recognizable = (
        ("Frente Popular", "#ff0000"),
        ("Frente Nacional Contrarrevolucionario", "#0000ff"),
        ("Centro y nacionalistas", "#3cb371"),
        ("PSOE, PSC", "#c6464f"),
        ("PSOE + PSC", "#c6464f"),
        ("Unión de Centro Democrático", "#315a29"),
        ("Partido Socialista Obrero Español", "#c6464f"),
        ("Partido socialista Obrero Español", "#c6464f"),
        ("Partido Popular (PP)", "#2d4d73"),
        ("Alianza Popular", "#2d4d73"),
        ("Partido Comunista de España", "#8b1e3f"),
        ("Partit dels Socialistes de Catalunya", "#b34978"),
        ("Partido Socialista de Catalunya", "#b34978"),
        ("Convergencia i Unió", "#d1a243"),
        ("Convergència i Unió", "#d1a243"),
        ("Ciudadanos-Partido", "#c7703a"),
        ("Podemos", "#7d5da5"),
    )
    preferred = [
        OTHER_COLOR if row[0] == "Otros*" else
        next((color for prefix, color in recognizable if row[0].startswith(prefix)), None)
        for row in rows
    ]
    reserved = set(preferred) - {None}
    available = iter(color for color in COLORS if color not in reserved)
    used = set()
    result = []
    for color in preferred:
        if color is None or color in used:
            color = next(available)
        used.add(color)
        result.append(color)
    return result


def grouped_rows(table):
    rows = [row for row in table["rows"] if row[0].strip() != "Total"
            and row[3].isdigit() and int(row[3]) > 0]
    for group in table.get("chartGroups", []):
        members = group["members"]
        selected = [row for row in rows if row[0] in members]
        if len(selected) != len(members) or len(set(members)) != len(members):
            raise ValueError(f"{table['caption']}: agrupación electoral no válida")
        rows = [row for row in rows if row[0] not in members]
        votes = (sum(int(row[1].replace(".", "")) for row in selected)
                 if table.get("chart", {}).get("showVotes", True) else None)
        seats = sum(int(row[3]) for row in selected)
        rows.append([group["label"], f"{votes:,}".replace(",", ".") if votes is not None else "—",
                     "", str(seats)])
    return rows


def render(year, table, source):
    config = table.get("chart", {})
    seats = config.get("seats", 350)
    majority = config.get("majority", 176)
    show_votes = config.get("showVotes", True)
    heading = config.get("heading", f"Congreso · {year}")
    title = config.get("title", f"Elecciones generales de {year}: escaños en el Congreso")
    center = config.get("center", "350 escaños")
    rows = grouped_rows(table)
    rows.sort(key=lambda row: -int(row[3]))
    if sum(int(row[3]) for row in rows) != seats or len(rows) > len(COLORS):
        raise ValueError(f"{year}: candidaturas o suma de escaños no válidas")
    diagram_labels = {
        group["label"]: group.get("diagramLabel", group["label"])
        for group in table.get("chartGroups", [])
    }
    labels = []
    for row in rows:
        label = diagram_labels.get(row[0], row[0])
        lines = textwrap.wrap(label, width=30, break_long_words=False, break_on_hyphens=False)
        suffix = f'· {row[3]} {"escaño" if row[3] == "1" else "escaños"}'
        if len(lines[-1]) + 1 + len(suffix) <= 30:
            lines[-1] += " " + suffix
        else:
            lines.append(suffix)
        labels.append(lines)
    colors = colors_for(rows)
    width = 760
    cx, cy, outer, inner = 230, 370, 185, 78
    legend_height = sum(
        max(52 if show_votes else 36, len(lines) * 18 + (18 if show_votes else 0) + 16)
        for lines in labels
    )
    footer_y = max(515, 112 + legend_height + 12)
    height = footer_y + 30
    result = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="desc">Diagrama semicircular proporcional a los {seats} escaños, con las candidaturas y sus porcentajes de representación a la derecha.'
        + (' Las candidaturas y coaliciones señaladas se agrupan; el desglose completo aparece en la tabla.' if table.get("chartGroups") else '')
        + (f' La línea discontinua marca la mitad; la mayoría absoluta requiere {majority} escaños.' if majority else ' Se representan únicamente los escaños asignados a España.')
        + '</desc>',
        f'<metadata>{escape(json.dumps({"source": source, "year": year}, ensure_ascii=False))}</metadata>',
        '<style>text{font-family:"Arial Narrow",Arial,sans-serif;fill:#25343b}.title{font-size:22px;font-weight:700;fill:#223e4b}.subtitle{font-size:13px}.party{font-size:15px;font-weight:700}.share{font-size:13px;font-weight:600}.metric{font-size:12px;fill:#53666e}.center-seat{font-size:18px;font-weight:700;fill:#53666e}.center-note{font-size:12px;fill:#53666e}.footnote{font-size:12px}.sector{stroke:#fff;stroke-width:2}</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        f'<text class="title" x="380" y="32" text-anchor="middle">{escape(heading)}</text>',
        f'<text class="subtitle" x="380" y="51" text-anchor="middle">{escape(config.get("subtitle", "Escaños por candidatura"))}</text>',
    ]
    angle = 180.0
    for row, color in zip(rows, colors):
        end = angle - 180 * int(row[3]) / seats
        result.append(f'<path class="sector" data-party="{escape(row[0], quote=True)}" '
                      f'data-seats="{row[3]}" data-seat-percent="{100 * int(row[3]) / seats:.3f}" '
                      f'fill="{color}" d="{sector(cx, cy, outer, inner, angle, end)}"/>')
        angle = end
    if majority:
        result.append(f'<line x1="{cx}" y1="{cy - outer}" x2="{cx}" y2="{cy - inner}" '
                      'stroke="#fff" stroke-width="2" stroke-dasharray="5 4"/>')
    result.append(f'<circle cx="{cx}" cy="{cy}" r="{inner - 1}" fill="#fff"/>')
    result.append(f'<text class="center-seat" x="{cx}" y="{cy - 37}" text-anchor="middle">{seats}</text>')
    result.append(f'<text class="center-note" x="{cx}" y="{cy - 21}" text-anchor="middle">escaños</text>')
    center_note = f"{majority} para la mayoría absoluta" if majority else config.get(
        "centerNote", "Asignados a España"
    )
    result.append(f'<text class="center-note" x="{cx}" y="{cy - 5}" text-anchor="middle">{escape(center_note)}</text>')
    y = 112
    for row, color, lines in zip(rows, colors, labels):
        result.append(f'<rect x="430" y="{y - 12}" width="14" height="14" rx="2" fill="{color}"/>')
        for index, line in enumerate(lines):
            line_y = y + index * 18
            result.append(f'<text class="party" x="454" y="{line_y}">{escape(line)}</text>')
            if index == 0:
                share = f"{100 * int(row[3]) / seats:.1f}".replace(".", ",")
                result.append(f'<text class="share" x="744" y="{line_y}" text-anchor="end">{share} %</text>')
        if show_votes:
            votes_y = y + len(lines) * 18
            result.append(f'<text class="metric" x="454" y="{votes_y}">{escape(row[1])} votos</text>')
        y += max(52 if show_votes else 36, len(lines) * 18 + (18 if show_votes else 0) + 16)
    footnote = config.get(
        "footnote",
        "«Otros*» agrupa candidaturas con escaño; no es un grupo parlamentario."
        if table.get("chartGroups") else "Colores editoriales; no indican grupos parlamentarios."
    )
    result.append(f'<text class="footnote" x="380" y="{footer_y}" text-anchor="middle">{escape(footnote)}</text>')
    result.append("</svg>")
    return "\n".join(result) + "\n"


def main():
    documents = json.loads(DATA.read_text(encoding="utf-8"))["documents"]
    charts = {}
    for record in documents:
        if record["visualization"] != "elections":
            continue
        for table in record["tables"]:
            match = re.search(r" · (\d{4})$", table["caption"])
            if not match:
                raise ValueError(f"Fecha electoral no válida: {table['caption']}")
            year = int(match.group(1))
            filename = table.get("chart", {}).get("svg", f"elecciones-generales-{year}-semicirculo.svg")
            if not re.fullmatch(r"elecciones-[a-z]+-\d{4}-semicirculo\.svg", filename):
                raise ValueError(f"Nombre de gráfico no válido: {filename}")
            if filename in charts and charts[filename][1]["rows"] != table["rows"]:
                raise ValueError(f"{year}: resultados repetidos distintos")
            charts[filename] = (year, table, record["dataSourceUrl"])
    for filename, (year, table, source) in sorted(charts.items()):
        (OUTPUT / filename).write_text(
            render(year, table, source), encoding="utf-8"
        )
    print(f"{len(charts)} semicírculos electorales generados.")


if __name__ == "__main__":
    main()
