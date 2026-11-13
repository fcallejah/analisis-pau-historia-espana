"""Redraw the official Madoz map on the user's Wikimedia provincial template."""
import argparse
import hashlib
import io
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile


SVG = "http://www.w3.org/2000/svg"
SOURCE = (
    "https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/"
    "sguit/examanes_anios_anteriores/selectividad/sel_historia_espana.zip"
)
TEMPLATE_URL = "https://commons.wikimedia.org/wiki/File:Provincias_de_Espa%C3%B1a.svg"
TEMPLATE_SHA256 = "ef4a268e5ec73e915e6e663567a655d291cce2064aaaf951fba7d2e82ca3d062"
CROP = (93, 498, 326, 774)
PALETTE = {
    "70": ("#e9b8a7", "70 millones de reales", "Salmón"),
    "50": ("#f0bd76", "50 millones de reales", "Naranja pálido"),
    "40": ("#f4a62a", "40 millones de reales", "Naranja oscuro"),
    "30": ("#e2f0f6", "30 millones de reales", "Azul claro"),
    "10": ("#9cc5da", "10 millones de reales", "Azul celeste"),
    "5": ("#ad8aac", "5 millones de reales", "Púrpura"),
    "1": ("#d1d75e", "1 millón de reales", "Verde lima"),
    "none": ("#ffffff", "No se produce desamortización", "Blanco"),
}
# The template splits some provinces into several filled pieces and enclaves.
# Categories were read from the exam, not inferred from the alternative corpus map.
PROVINCES = [
    ("La Coruña", "10", "polygon22", 193, 72),
    ("Lugo", "5", "polygon324", 225, 77),
    ("Pontevedra", "1", "path54 path56 polygon856 polygon858 polygon860 polygon862 polygon864 polygon866", 191, 99),
    ("Ourense", "1", "polygon86", 219, 114),
    ("Asturias", "1", "polygon328 path330", 271, 65),
    ("Cantabria", "1", "path334", 324, 74),
    ("Vizcaya", "none", "path338 polygon50", 357, 68),
    ("Guipúzcoa", "none", "polygon26", 394, 75),
    ("Álava", "1", "polygon346", 361, 84),
    ("Navarra", "10", "polygon342", 395, 96),
    ("La Rioja", "5", "path94", 373, 111),
    ("León", "5", "path34 polygon36", 269, 100),
    ("Palencia", "10", "path46", 306, 105),
    ("Burgos", "10", "path40 path42 polygon764", 337, 114),
    ("Zamora", "10", "polygon130", 265, 128),
    ("Valladolid", "10", "polygon126", 306, 137),
    ("Soria", "1", "polygon150", 366, 138),
    ("Segovia", "10", "polygon166", 327, 151),
    ("Salamanca", "10", "polygon172", 261, 170),
    ("Ávila", "30", "polygon176", 294, 186),
    ("Madrid", "40", "path180 polygon188", 331, 183),
    ("Zaragoza", "10", "path76", 410, 141),
    ("Huesca", "10", "polygon350 polygon352", 446, 117),
    ("Lleida", "10", "polygon356 path358", 478, 123),
    ("Girona", "5", "polygon98 polygon110", 523, 112),
    ("Barcelona", "10", "path362 path364", 506, 132),
    ("Tarragona", "5", "polygon368", 468, 156),
    ("Guadalajara", "5", "polygon378", 372, 170),
    ("Cuenca", "5", "polygon382", 382, 207),
    ("Teruel", "10", "polygon372 polygon374", 420, 176),
    ("Castellón", "5", "polygon184", 448, 192),
    ("Valencia", "30", "polygon386 polygon210", 424, 225),
    ("Alicante", "10", "polygon394", 432, 263),
    ("Murcia", "5", "polygon276", 405, 288),
    ("Cáceres", "10", "polygon196 polygon198", 256, 212),
    ("Toledo", "40", "polygon200 polygon202", 310, 212),
    ("Ciudad Real", "40", "polygon230 polygon234", 330, 253),
    ("Badajoz", "30", "polygon238 polygon240", 254, 254),
    ("Albacete", "5", "polygon246", 387, 252),
    ("Córdoba", "30", "polygon280 polygon282", 297, 284),
    ("Jaén", "30", "polygon286", 341, 284),
    ("Sevilla", "70", "path294 path296", 272, 304),
    ("Huelva", "5", "polygon290", 229, 299),
    ("Granada", "30", "polygon300", 340, 313),
    ("Almería", "1", "polygon306", 376, 323),
    ("Málaga", "30", "polygon320", 304, 332),
    ("Cádiz", "50", "polygon398", 264, 337),
    ("Islas Baleares", "5", "polygon206 polygon218 polygon260 path272 polygon768", 542, 215),
    ("Santa Cruz de Tenerife", "1", "polygon798 polygon806 polygon810 polygon818", 47, 418),
    ("Las Palmas", "1", "polygon786 polygon790 polygon794 polygon802 polygon814", 136, 432),
]
NO_DATA = {"polygon776", "polygon782"}


def node(parent, tag, text=None, **attributes):
    child = ET.SubElement(parent, f"{{{SVG}}}{tag}", {
        key.replace("_", "-"): str(value) for key, value in attributes.items()
    })
    child.text = text
    return child


def export(archive, template, output):
    try:
        import pymupdf
    except ImportError as error:
        raise SystemExit("Instala PyMuPDF en el entorno de autoría para extraer el recorte oficial.") from error
    with ZipFile(archive) as historical:
        year_bytes = historical.read("sel_2009_historia_espana.zip")
    with ZipFile(io.BytesIO(year_bytes)) as year:
        pdf_bytes = year.read("historico06.pdf")
    original = output / "mapa-desamortizacion-madoz-oficial-2009.png"
    destination = output / "mapa-desamortizacion-madoz-vector-2009.svg"
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        pdf[0].get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=pymupdf.Rect(CROP), alpha=False).save(original)

    template_bytes = template.read_bytes()
    if hashlib.sha256(template_bytes).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("La plantilla no coincide con la versión revisada; coteja sus regiones antes de regenerar.")
    base = ET.fromstring(template_bytes)
    if base.get("viewBox") != "-0.003 0 644 458":
        raise ValueError("La plantilla ha cambiado de geometría; revisa las asignaciones provinciales.")
    ownership = {}
    for province, category, identifiers, _, _ in PROVINCES:
        for identifier in identifiers.split():
            if identifier in ownership:
                raise ValueError(f"Región provincial duplicada: {identifier}")
            ownership[identifier] = (province, category)
    root = ET.Element(f"{{{SVG}}}svg", {
        "width": "1288", "height": "1160", "viewBox": "0 56 644 580",
        "role": "img", "aria-labelledby": "map-title map-description",
    })
    node(root, "title", "Desamortización de Madoz: valor en remate de las fincas", id="map-title")
    node(root, "desc", "Redibujado didáctico del documento 2, opción A, Examen 6 de 2009. "
         "Geometría provincial moderna de Wikimedia Commons; colores sólidos según las ocho "
         "categorías del examen. No es un facsímil. Texto seleccionable, incluidas las provincias "
         "y la leyenda. Ceuta y Melilla no tienen categoría en la fuente.", id="map-description")
    node(root, "metadata",
         f"Fuente temática: {SOURCE}; sel_2009_historia_espana.zip/historico06.pdf; página 1; "
         f"SHA-256 del PDF: {hashlib.sha256(pdf_bytes).hexdigest()}; "
         f"Cartografía: {TEMPLATE_URL}; SHA-256 de la plantilla: {hashlib.sha256(template_bytes).hexdigest()}; "
         "Emilio Gómez Fernández, Javi C. S., Darz Mol y Lojwe. "
         "Adaptación: colores, eliminación de rótulos externos, texto seleccionable y leyenda. "
         "Licencia del mapa adaptado: CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/.")
    node(root, "style", "text{font-family:Arial,Helvetica,sans-serif;fill:#20272c;"
         "user-select:text;-webkit-user-select:text;cursor:text}"
         ".province-label{font-size:8px;text-anchor:middle;paint-order:stroke;"
         "stroke:#fff;stroke-width:1.6;stroke-linejoin:round;stroke-opacity:.55}")
    node(root, "rect", x=0, y=56, width=644, height=580, fill="#ffffff")
    geography = node(root, "g", transform="translate(0 56)", id="geography")
    seen = set()
    for shape in base.iter():
        kind = shape.tag.rsplit("}", 1)[-1]
        style = dict(item.split(":", 1) for item in shape.get("style", "").split(";") if ":" in item)
        if kind not in ("path", "polygon", "polyline") or not style or style.get("fill") == "#0099ff":
            continue
        identifier = shape.get("id")
        # These are white seam corrections between pieces, not province borders.
        if identifier in ("path122", "path170", "path228"):
            continue
        attrs = {key: value for key, value in shape.attrib.items()
                 if key in ("id", "d", "points", "transform")}
        fill = style.get("fill", "none")
        if fill == "#fff8e3":
            if identifier in NO_DATA:
                attrs["fill"] = "#f1f0eb"
            elif identifier in ownership:
                province, category = ownership[identifier]
                attrs.update(fill=PALETTE[category][0], **{
                    "data-province": province, "data-category": category,
                })
                seen.add(identifier)
            else:
                raise ValueError(f"Región sin categoría revisada: {identifier}")
        elif fill == "#f4e2ba":
            attrs["fill"] = "#f1f0eb"
        elif fill == "#d3ebfa":
            attrs["fill"] = "#ffffff"
        else:
            attrs["fill"] = fill
        if "stroke" in style and style["stroke"] != "none":
            attrs.update(stroke="#77858b", **{"stroke-width": "0.55", "stroke-linejoin": "round"})
            if "stroke-dasharray" in style:
                attrs["stroke-dasharray"] = style["stroke-dasharray"]
        ET.SubElement(geography, f"{{{SVG}}}{kind}", attrs)
    if seen != set(ownership):
        raise ValueError(f"Faltan regiones de la plantilla: {set(ownership) - seen}")
    labels = node(geography, "g", id="province-labels")
    for province, _, _, x, y in PROVINCES:
        label = node(labels, "text", None if province == "Santa Cruz de Tenerife" else province,
                     x=x, y=y, **{"class": "province-label"})
        if province == "Santa Cruz de Tenerife":
            node(label, "tspan", "Santa Cruz", x=x)
            node(label, "tspan", "de Tenerife", x=x, dy=10)
    for label, x, y in (("Ceuta", 293, 368), ("Melilla", 372, 387)):
        node(labels, "text", label, x=x, y=y, **{"class": "province-label"})
    node(root, "text", "Valor en remate de las fincas", x=322, y=538,
         text_anchor="middle", font_size=14, font_weight=700)
    legend = node(root, "g", id="map-legend")
    for index, (category, (color, label, _)) in enumerate(PALETTE.items()):
        x, y = 16 + 212 * (index // 3), 552 + 28 * (index % 3)
        node(legend, "rect", x=x, y=y, width=23, height=14, fill=color, stroke="#66747a",
             stroke_width=".65", **{"class": "legend-swatch", "data-category": category})
        if category == "none":
            label_node = node(legend, "text", "No se produce ", x=x + 32, y=y + 5, font_size=10.5)
            node(label_node, "tspan", "desamortización", x=x + 32, dy=12)
        else:
            node(legend, "text", label, x=x + 32, y=y + 11, font_size=10.5)
    ET.register_namespace("", SVG)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    print(f"{destination.name}: 50 provincias, 8 categorías, texto seleccionable.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "assets/documentos")
    args = parser.parse_args()
    export(args.archive, args.template, args.output)
