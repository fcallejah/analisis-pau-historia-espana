"""Export the five vector originals from SGUIT's historical exam archive."""
import argparse
import hashlib
import io
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

try:
    import pymupdf
except ImportError as error:
    raise SystemExit("Falta PyMuPDF. Instálalo en un entorno virtual: pip install PyMuPDF") from error


SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
SOURCE = (
    "https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/"
    "sguit/examanes_anios_anteriores/selectividad/sel_historia_espana.zip"
)
EXPORTS = (
    ("miembros-cortes-cadiz-oficial-2008.svg", 2, 0, (161, 511, 474, 705),
     "Miembros de las Cortes de Cádiz", "Opción A, documento 2"),
    ("grafico-desamortizaciones-siglo-xix-oficial-2008.svg", 6, 0, (111, 476, 484, 748),
     "Desamortización eclesiástica y civil (en millones de reales de vellón)", "Opción A, documento 2"),
    ("resultados-electorales-restauracion-1881-1898-oficial-2008.svg", 1, 0, (185, 507, 413, 733),
     "Resultados electorales, 1881–1898 (en número de escaños)", "Opción A, documento 2"),
    ("bajas-espanolas-en-cuba-y-filipinas-oficial-2008.svg", 4, 0, (78, 322, 514, 464),
     "Muertos en Cuba y Filipinas (1895–1898)", "Opción A, documento 1"),
    ("resultados-elecciones-generales-1982-oficial-2008.svg", 3, 1, (78, 302, 514, 566),
     "Elecciones Generales de 28 de octubre de 1982: distribución de votos y escaños en el Congreso",
     "Opción B, documento 1"),
)


def validate_text_crop(page, clip):
    for x0, y0, x1, y1, word, *_ in page.get_text("words"):
        center = pymupdf.Point((x0 + x1) / 2, (y0 + y1) / 2)
        # Adjacent text outside the graphic is not part of the selected crop.
        if clip.contains(center) and not clip.contains(pymupdf.Rect(x0, y0, x1, y1)):
            raise ValueError(f"El recorte corta la palabra «{word}» del PDF")


def export(archive, output):
    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", XLINK)
    with ZipFile(archive) as historical:
        year_bytes = historical.read("sel_2008_historia_espana.zip")
    with ZipFile(io.BytesIO(year_bytes)) as year:
        for filename, exam, page_number, bounds, title, option in EXPORTS:
            pdf_name = f"Texto Histórico {exam} - Examen y criterios de corrección.pdf"
            original = year.read(pdf_name)
            with pymupdf.open(stream=original, filetype="pdf") as source:
                page = source[page_number]
                clip = pymupdf.Rect(bounds)
                validate_text_crop(page, clip)
                if any(clip.intersects(image["bbox"]) for image in page.get_image_info()):
                    raise ValueError(f"{pdf_name}: el recorte contiene una imagen, no solo vectores")
                with pymupdf.open() as cropped:
                    target = cropped.new_page(width=clip.width, height=clip.height)
                    target.show_pdf_page(target.rect, source, page_number, clip=clip)
                    root = ET.fromstring(target.get_svg_image(text_as_path=True))
            # The PDF form retains out-of-frame logo resources; none intersects the crop.
            for parent in root.iter():
                for child in list(parent):
                    if child.tag == f"{{{SVG}}}image":
                        parent.remove(child)
            root.set("width", str(round(clip.width * 4)))
            root.set("height", str(round(clip.height * 4)))
            root.set("role", "img")
            root.set("aria-labelledby", "title description")
            ET.SubElement(root, f"{{{SVG}}}title", id="title").text = title
            ET.SubElement(root, f"{{{SVG}}}desc", id="description").text = (
                f"Extracción vectorial del PDF oficial de 2008, Examen {exam}, {option}. "
                "Se conservan los trazados, glifos y datos originales; no es una reconstrucción."
            )
            ET.SubElement(root, f"{{{SVG}}}metadata").text = (
                f"Fuente: {SOURCE}; archivo: sel_2008_historia_espana.zip/{pdf_name}; "
                f"página: {page_number + 1}; recorte PDF: {bounds}; "
                f"SHA-256 del PDF: {hashlib.sha256(original).hexdigest()}"
            )
            background = ET.Element(f"{{{SVG}}}rect", {
                "width": str(clip.width), "height": str(clip.height), "fill": "#fff",
            })
            root.insert(0, background)
            destination = output / filename
            ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
            print(destination.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Paquete oficial sel_historia_espana.zip")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent.parent / "assets/documentos")
    args = parser.parse_args()
    export(args.archive, args.output)
