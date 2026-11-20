"""Create color-treated derivatives while keeping extracted SGUIT SVGs intact."""
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def colorize_cadiz_chart():
    source = ROOT / "assets/documentos/miembros-cortes-cadiz-oficial-2008.svg"
    target = ROOT / "assets/documentos/miembros-cortes-cadiz-color-2008.svg"
    content = source.read_text(encoding="utf-8")
    gray_bars = content.count("#999a99")
    if gray_bars != 26:
        raise ValueError(f"Expected 26 original gray chart fills, found {gray_bars}")
    target.write_text(content.replace("#999a99", "#54877d"), encoding="utf-8")
    print(f"{target.name}: recolored {gray_bars} original fills")


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
