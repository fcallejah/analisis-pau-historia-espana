"""Integrity checks for the reviewed document corpus."""
import json
from pathlib import Path
import struct
import unittest
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent


def image_dimensions(path):
    if path.suffix == ".svg":
        root = ET.parse(path).getroot()
        return int(root.get("width")), int(root.get("height"))
    return struct.unpack(">II", path.read_bytes()[16:24])


class DocumentCorpusTests(unittest.TestCase):
    def test_source_manifest_is_fully_assigned(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        coverage = data["coverage"]
        manifest = coverage["sourceManifest"]
        source_keys = [source["key"] for source in manifest]
        appearance_keys = [
            appearance.get("sourceKey")
            for document in data["documents"]
            for appearance in document["appearances"]
        ]
        self.assertEqual(len(manifest), coverage["sourceDocumentOccurrences"])
        self.assertEqual(len(source_keys), len(set(source_keys)))
        self.assertEqual(set(source_keys), set(appearance_keys))
        self.assertEqual(len(appearance_keys), len(set(appearance_keys)))
        self.assertEqual(
            sum(len(source["images"]) for source in manifest),
            coverage["sourceImageOccurrences"],
        )
        self.assertEqual(coverage["yearsWithDifferentShortQuestionAndTopicFormat"],
                         list(range(2017, 2025)))

    def test_assembly_excerpt_is_not_reconstructed(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "la-asamblea-de-parlamentarios-de-barcelona")
        self.assertEqual(document["text"], [
            "“La Asamblea adopta los siguientes acuerdos:",
            "Primero.",
        ])
        self.assertIn("fragmento incompleto", document["quality"])

    def test_document_identities_sources_and_assets(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        ids = set()
        appearances = set()
        for document in data["documents"]:
            with self.subTest(document=document["id"]):
                self.assertNotIn(document["id"], ids)
                ids.add(document["id"])
                self.assertIn(document["type"], ("texto", "imagen", "grafico"))
                self.assertTrue(document["blocks"])
                self.assertTrue(all(isinstance(block, int) and 5 <= block <= 12 for block in document["blocks"]))
                self.assertTrue(document["tags"])
                self.assertTrue(document["quality"])
                self.assertTrue(document["appearances"])
                self.assertEqual(len(document["commentary"]), 2)
                self.assertTrue(document["commentary"][0]["title"].startswith("a) "))
                self.assertTrue(document["commentary"][1]["title"].startswith("b) "))
                for appearance in document["appearances"]:
                    self.assertNotIn(appearance["id"], appearances)
                    appearances.add(appearance["id"])
                    parsed = urlparse(appearance["sourceUrl"])
                    self.assertEqual(parsed.scheme, "https")
                    self.assertEqual(parsed.hostname, "docs.google.com")
                    self.assertTrue(parsed.fragment.startswith("heading="))
                if "image" in document:
                    image = document["image"]
                    path = ROOT / image["src"]
                    self.assertTrue(path.is_file())
                    dimensions = image_dimensions(path)
                    self.assertEqual(dimensions, (image["width"], image["height"]))
                    self.assertTrue(image["alt"])
                if "tableImage" in document:
                    image = document["tableImage"]
                    path = ROOT / image["src"]
                    self.assertTrue(path.is_file())
                    dimensions = image_dimensions(path)
                    self.assertEqual(dimensions, (image["width"], image["height"]))
                    self.assertTrue(image["alt"])
                    self.assertTrue(image["caption"])
                    self.assertIn("table", document)
                if document["type"] == "texto":
                    self.assertTrue(document["text"])
                if "table" in document:
                    table = document["table"]
                    self.assertTrue(all(len(row) == len(table["headers"]) for row in table["rows"]))

    def test_image_crops_match_google_docs_viewports(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        crops = {
            document["id"]: document["image"]["crop"]
            for document in data["documents"] if document.get("image", {}).get("crop")
        }
        source_geometry = {
            "retrato-ramon-maria-narvaez": (362, 352, 514, 800, -92, -96),
            "entrada-alfonso-xii-madrid-1875": (549.51, 364.57, 639.86, 454.92, -45.7, -45.79),
            "primo-rivera-visita-tropas-marruecos": (309, 461, 602, 753, -97, -223),
            "reparto-armas-madrid-1936": (401.34, 315.5, 453.3, 315.5, 0, 0),
            "exaltacion-franco": (207.11, 315.99, 521.67, 315.99, -162.05, 0),
        }
        self.assertEqual(set(crops), set(source_geometry))
        for document_id, geometry in source_geometry.items():
            with self.subTest(document=document_id):
                self.assertEqual(crops[document_id], dict(zip(
                    ("width", "height", "imageWidth", "imageHeight", "left", "top"), geometry,
                )))

    def test_vectors_keep_source_provenance(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        documents = {document["id"]: document for document in data["documents"]}
        for document_id in (
            "resultados-electorales-restauracion-1881-1898",
            "bajas-espanolas-en-cuba-y-filipinas",
            "resultados-de-las-elecciones-generales-de-1982",
        ):
            with self.subTest(document=document_id):
                capture = documents[document_id]["tableImage"]
                self.assertIn("SVG extraído del PDF oficial de 2008", capture["caption"])
                self.assertTrue(capture["src"].endswith(".svg"))
                self.assertIn("sel_historia_espana.zip", capture["sourceUrl"])

        official = documents["elecciones-generales-1982-congreso-senado"]
        self.assertIn("-vector.svg", official["image"]["src"])
        self.assertIn("Redibujado vectorial", official["quality"])
        self.assertTrue((ROOT / official["image"]["originalSrc"]).is_file())
        self.assertIn("PDF oficial", official["quality"])
        self.assertEqual((official["image"]["width"], official["image"]["height"]), (2084, 1418))

        desamortizaciones = documents["grafico-desamortizaciones-siglo-xix"]
        self.assertIn("PDF oficial de 2008", desamortizaciones["sourceCaption"])
        self.assertIn("Extracción vectorial", desamortizaciones["quality"])
        self.assertEqual((desamortizaciones["image"]["width"], desamortizaciones["image"]["height"]), (1492, 1088))
        self.assertEqual(desamortizaciones["appearances"][0]["route"], "Opción A")

    def test_all_charts_are_self_contained_vectors(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        namespace = "{http://www.w3.org/2000/svg}"
        for document in data["documents"]:
            if document["type"] != "grafico":
                continue
            with self.subTest(document=document["id"]):
                image = document.get("image") or document["tableImage"]
                path = ROOT / image["src"]
                self.assertEqual(path.suffix, ".svg")
                root = ET.parse(path).getroot()
                self.assertIsNotNone(root.find(f"{namespace}title"))
                self.assertIsNotNone(root.find(f"{namespace}desc"))
                ids = {node.get("id") for node in root.iter() if node.get("id")}
                for node in root.iter():
                    self.assertNotIn(node.tag, [
                        f"{namespace}image", f"{namespace}script", f"{namespace}foreignObject",
                    ])
                    for attribute, value in node.attrib.items():
                        if attribute.endswith("href"):
                            self.assertTrue(value.startswith("#"))
                            self.assertIn(value[1:], ids)
                metadata = root.find(f"{namespace}metadata").text
                if "redibujado" not in document["quality"].lower():
                    self.assertIn("SHA-256 del PDF:", metadata)

    def test_redrawn_table_matches_its_accessible_cells(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "elecciones-generales-1982-congreso-senado")
        root = ET.parse(ROOT / document["image"]["src"]).getroot()
        cells = {
            (int(node.get("x")), int(node.get("y"))): node.text
            for node in root.iter("{http://www.w3.org/2000/svg}text")
        }
        for index, row in enumerate(document["table"]["rows"]):
            y = 618 if index == 9 else 180 + 48 * index
            for x, value in zip((50, 490, 532, 960), row):
                with self.subTest(row=index, column=x):
                    if value != "":
                        self.assertEqual(cells[(x, y)], str(value))
                    else:
                        self.assertNotIn((x, y), cells)

    def test_1982_transcription_keeps_original_totals_and_notes(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "resultados-de-las-elecciones-generales-de-1982")
        self.assertEqual(document["table"]["rows"][-3:], [
            ["Total", "20.088.600", "", "", ""],
            ["Otros***", "863.000", "4,12", "350", ""],
            ["Total votos a candidaturas", "20.951.600", "", "", ""],
        ])
        self.assertEqual(len(document["table"]["notes"]), 4)
        self.assertIn("sin corregirla", document["quality"])

    def test_cadiz_transcription_matches_the_reviewed_chart(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        chart = next(document for document in data["documents"] if document["id"] == "miembros-cortes-cadiz")
        self.assertEqual(dict(chart["table"]["rows"]), {
            "Eclesiásticos": 90, "Abogados": 56, "Funcionarios": 49, "Militares": 30,
            "Sin profesión determinada": 20, "Catedráticos de universidad": 15,
            "Nobles": 14, "Marinos": 9, "Comerciantes": 8, "Escritores": 2,
            "Arquitectos": 1, "Bachiller": 1, "Médicos": 1,
        })


if __name__ == "__main__":
    unittest.main()
