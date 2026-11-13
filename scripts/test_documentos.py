"""Integrity checks for the reviewed document corpus."""
import json
import hashlib
import importlib.util
from pathlib import Path
import unittest
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("notes_image_tools", ROOT / "scripts/importar-apuntes.py")
notes_image_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes_image_tools)


def image_dimensions(path):
    if path.suffix == ".svg":
        root = ET.parse(path).getroot()
        return int(root.get("width")), int(root.get("height"))
    dimensions = notes_image_tools.image_dimensions(path.read_bytes())
    if dimensions is None:
        raise ValueError(f"Formato de imagen no compatible: {path}")
    return dimensions


class DocumentCorpusTests(unittest.TestCase):
    def test_desamortization_documents_belong_to_the_economy_block(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identifier in (
            "decreto-de-desamortizacion-de-mendizabal",
            "decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal",
            "exposicion-de-mendizabal-sobre-los-objetivos-de-la-desamortizacion",
            "grafico-desamortizaciones-siglo-xix",
            "mendizabal-explica-la-desamortizacion-de-1836",
            "mapa-desamortizacion-madoz",
        ):
            with self.subTest(document=identifier):
                self.assertEqual(records[identifier]["blocks"], [8])

    def test_attributions_do_not_replace_the_body_or_change_merged_wording(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for record in records.values():
            if "attributionParagraphs" in record:
                with self.subTest(document=record["id"]):
                    count = record["attributionParagraphs"]
                    self.assertIs(type(count), int)
                    self.assertGreater(count, 0)
                    self.assertLess(count, len(record["text"]))
        original = {
            "critica-del-sistema-electoral-de-la-restauracion": "3c8d44344a08216bbc920848b9fabffb1972cf3d4334427207cfd6cbbcd3b646",
            "la-segunda-republica-y-la-cuestion-agraria": "a5ea5441ee76b9e2e62d9b549f3bf23f7e5c4ea1f836e4bab2ea498732b30b73",
            "la-jefatura-del-estado-en-la-ley-organica-de-1967": "359d60d04ecc3c031ef4c221deac00757d2c5d8f4f6a9b78d3683b0d29949069",
            "investidura-de-jose-maria-aznar": "0531fab6d4196779c3ce169daf70e8c080f31cf480492206aec69fcd2392a75e",
        }
        for identifier, expected in original.items():
            record = records[identifier]
            self.assertEqual(record["attributionParagraphs"], 1)
            self.assertEqual(hashlib.sha256(" ".join(record["text"]).encode()).hexdigest(), expected)
        aznar = records["investidura-de-jose-maria-aznar"]["text"]
        self.assertTrue(aznar[-2].endswith("en nuestra vida pública"))
        self.assertTrue(aznar[-1].startswith("Discurso de D. Jose Maria Aznar"))
        constitution = records["constitucion-1812-articulos-2008"]["text"]
        self.assertTrue(constitution[-2].endswith("que establezcan las leyes."))
        self.assertEqual(constitution[-1], "Constitución Española de 1812")
        for identifier in (
            "napoleon-espanoles-bayona-1808",
            "decreto-unificacion-1937",
            "decreto-de-desamortizacion-de-mendizabal",
            "decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal",
            "manifiesto-manzanares-1854",
        ):
            self.assertNotIn("attributionParagraphs", records[identifier])

    def test_exam_headers_and_misplaced_treaty_tail_are_cleaned(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for record in records.values():
            if record["type"] == "texto":
                self.assertNotRegex(" ".join(record["text"]),
                                    r"ADMISI[ÓO]N|ANDALUCÍA, CEUTA|CURSO 202[45]-202[56]")
        decree = records["decreto-de-desamortizacion-de-mendizabal"]["text"]
        self.assertEqual(decree, records["decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal"]["text"])
        self.assertNotIn("Tratado", " ".join(decree))
        treaty = records["tratado-de-paris-y-perdida-del-imperio-colonial"]["text"]
        self.assertIn("veinte millones de dólares dentro de los tres meses después del canje", treaty[-2])
        self.assertIn("10 de diciembre de 1898", treaty[-1])
        sandhurst = records["manifiesto-de-sandhurst-llamamiento-a-la-restauracion"]["text"]
        self.assertTrue(any("Por mi parte, debo al infortunio" in paragraph for paragraph in sandhurst))
        self.assertTrue(sandhurst[-1].endswith("1874."))

    def test_franco_2025_continuation_is_recovered_from_its_own_pdf(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        text = records["franco-ante-las-cortes-sobre-democracia-y-partidos"]["text"]
        self.assertIn("del análisis crítico de las soluciones de gobierno", text[-2])
        self.assertTrue(text[-2].endswith("que constituyen a perfeccionar la marcha de la comunidad”."))
        self.assertEqual(text[-1], "Discurso de Franco ante las Cortes, 22 de noviembre de 1966.")

    def test_reflow_preserves_murat_text_and_article_boundaries(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        text = records["bando-de-murat-tras-el-levantamiento-del-2-de-mayo"]["text"]
        self.assertEqual(len(text), 8)
        for number, paragraph in enumerate(text[1:7], 1):
            self.assertTrue(paragraph.startswith(f"Art. {number}. "))
        self.assertEqual(hashlib.sha256(" ".join(text).encode()).hexdigest(),
                         "7c75e5c5a6722e82a94e62f87ceb0deac60f03dd5e717b2ca02c2c94e073ed4b")

    def test_prepared_people_have_sources_and_visible_crop_coordinates(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        for record in data["documents"]:
            annotations = record.get("image", {}).get("annotations")
            if not annotations:
                continue
            with self.subTest(document=record["id"]):
                self.assertIn(annotations["layout"], ("margins", "numbered"))
                self.assertTrue(annotations["note"])
                self.assertTrue(annotations["sources"])
                for source in annotations["sources"]:
                    self.assertTrue(source["title"])
                    self.assertEqual(urlparse(source["url"]).scheme, "https")
                self.assertTrue(annotations["people"])
                for person in annotations["people"]:
                    self.assertTrue(person["name"])
                    self.assertTrue(person["role"])
                    self.assertTrue(person["position"])
                    self.assertNotRegex(person["position"], r"espectador|quien mira|para los retratados")
                    self.assertTrue(0 <= person["x"] <= 1 and 0 <= person["y"] <= 1)
                    self.assertIn(person["side"], ("left", "right"))
        records = {d["id"]: d for d in data["documents"]}
        self.assertEqual(records["general-valeriano-weyler"]["blocks"], [7])
        self.assertEqual(records["militantes-pce-acto-multitudinario"]["blocks"], [12])
        for name in ("general-valeriano-weyler", "isabel-ii-jura-constitucion-1837", "azana-homenaje-coruna-franco"):
            self.assertTrue(records[name]["image"]["crop"])

    def test_alhucemas_names_share_the_car_instead_of_unverified_individual_positions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "primo-rivera-sanjurjo-alhucemas-1925")
        people = record["image"]["annotations"]["people"]
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["name"], "Miguel Primo de Rivera y José Sanjurjo")
        self.assertIn("sin distinguir", people[0]["position"])
        self.assertTrue(0.45 < people[0]["x"] < 0.60 and 0.55 < people[0]["y"] < 0.65)

    def test_emphasis_parts_are_ordered_literal_fragments(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        for record in data["documents"]:
            sources = []
            if "attributionEmphasis" in record:
                self.assertTrue(record.get("attributionParagraphs"))
                sources.append((record["text"][-1], record["attributionEmphasis"]))
            caption = record.get("examCaption", {})
            if "emphasis" in caption:
                sources.append((caption["text"], caption["emphasis"]))
            for text, phrases in sources:
                with self.subTest(document=record["id"]):
                    self.assertIsInstance(phrases, list)
                    position = 0
                    for phrase in phrases:
                        self.assertTrue(phrase.strip())
                        start = text.find(phrase, position)
                        self.assertGreaterEqual(start, position)
                        position = start + len(phrase)

    def test_literal_captions_reference_a_real_appearance_without_exam_instructions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        for record in data["documents"]:
            caption = record.get("examCaption")
            if not caption:
                continue
            with self.subTest(document=record["id"]):
                self.assertTrue(record.get("image") or record.get("tableImage"))
                self.assertTrue(caption["text"].strip())
                self.assertIn(caption["appearanceId"], [a["id"] for a in record["appearances"]])
                self.assertNotRegex(caption["text"], r"(?i)instrucciones:|a\) analice|b\) explique|transcripción de la recopilación")

    def test_2009_contains_all_four_documents_from_each_exam(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        appearances = [
            appearance for document in data["documents"]
            for appearance in document["appearances"] if appearance["year"] == 2009
        ]
        self.assertEqual(len(appearances), 24)
        for exam in range(1, 7):
            entries = [a for a in appearances if a["exam"] == f"2009 Examen {exam}"]
            self.assertEqual(sorted(a["sourceOrdinal"] for a in entries), [1, 2, 3, 4])
            self.assertEqual(sorted(a["document"] for a in entries), [1, 1, 2, 2])
        for identifier in ("decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal",
                           "constitucion-1931-articulos-suplente-a"):
            record = next(d for d in data["documents"] if d["id"] == identifier)
            self.assertTrue(any(a["year"] == 2009 and a.get("sameDocumentReviewed")
                                for a in record["appearances"]))

    def test_madoz_map_keeps_official_and_corpus_legends_separate(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "mapa-desamortizacion-madoz")
        for attribute in ("src", "originalSrc", "corpusSrc"):
            self.assertTrue((ROOT / record["image"][attribute]).is_file())
        self.assertIn("leyenda distinta", record["quality"])
        self.assertIn("Redibujado didáctico", record["quality"])
        self.assertTrue(record["image"]["selectable"])
        self.assertEqual([row[1] for row in record["table"]["rows"]], [
            "70 millones de reales", "50 millones de reales", "40 millones de reales",
            "30 millones de reales", "10 millones de reales", "5 millones de reales",
            "1 millón de reales", "No se produce desamortización",
        ])

    def test_madoz_redraw_has_eight_solid_categories_and_real_labels(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "mapa-desamortizacion-madoz")
        root = ET.parse(ROOT / record["image"]["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        background = root.find(f"{namespace}rect").get("fill")
        self.assertEqual(background, "#ffffff")
        for identifier in ("polygon6", "polygon8"):
            self.assertEqual(root.find(f".//*[@id='{identifier}']").get("fill"), background)
        self.assertEqual([n.text for n in root.findall(f"{namespace}text")],
                         ["Valor en remate de las fincas"])
        self.assertEqual((int(root.get("width")), int(root.get("height"))),
                         (record["image"]["width"], record["image"]["height"]))
        legend = root.find(f"{namespace}g[@id='map-legend']")
        self.assertEqual([" ".join("".join(n.itertext()).split()) for n in legend.findall(f"{namespace}text")],
                         [row[1] for row in record["table"]["rows"]])
        swatches = legend.findall(f"{namespace}rect")
        self.assertEqual(len(swatches), 8)
        columns = {}
        for swatch in swatches:
            columns.setdefault(float(swatch.get("x")), []).append(swatch.get("data-category"))
        self.assertEqual([columns[x] for x in sorted(columns)], [
            ["70", "50", "40"], ["30", "10", "5"], ["1", "none"],
        ])
        self.assertEqual(len({n.get("fill") for n in swatches}), 8)
        colors = {n.get("data-category"): n.get("fill") for n in swatches}
        provinces = {n.get("data-province") for n in root.iter() if n.get("data-province")}
        self.assertEqual(len(provinces), 50)
        for n in root.iter():
            if n.get("data-province"):
                self.assertEqual(n.get("fill"), colors[n.get("data-category")])
        labels = root.find(f".//{namespace}g[@id='province-labels']")
        self.assertEqual(len(labels.findall(f"{namespace}text")), 52)
        text = " ".join("".join(n.itertext()) for n in root.iter(f"{namespace}text"))
        for removed in ("FRANCIA", "PORTUGAL", "MARRUECOS", "ARGELIA", "OCÉANO", "MEDITERRÁNEO"):
            self.assertNotIn(removed, text.upper())
        self.assertIn("CC BY-SA 3.0", root.find(f"{namespace}metadata").text)

    def test_2009_transcriptions_restore_ocr_omissions_from_pdf(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {d["id"]: d for d in data["documents"]}
        decree = " ".join(records["decreto-unificacion-1937"]["text"])
        self.assertIn("Una acción de gobierno eficiente", decree)
        self.assertIn("todos los españoles", decree)
        transition = " ".join(records["garcia-cortazar-transicion-democracia"]["text"])
        self.assertIn("autorizaron la transición a la democracia", transition)
        self.assertIn("habían vaticinado", transition)
        self.assertNotIn("Vatinadocracia", transition)

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

    def test_assembly_continuation_is_recovered_from_its_own_corpus(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "la-asamblea-de-parlamentarios-de-barcelona")
        self.assertEqual(document["text"][:2], [
            "“La Asamblea adopta los siguientes acuerdos:",
            "Primero.",
        ])
        self.assertEqual(hashlib.sha256(" ".join(document["text"]).encode()).hexdigest(),
                         "86cefc60bf3b3d5a18e6725dfc28c36801c2b2663df1ff5d9cd1551a498db978")
        self.assertIn("esta misma aparición", document["quality"])
        self.assertIn("pendiente de cotejo con el PDF oficial", document["quality"])

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
            "general-valeriano-weyler": (467.92, 627.5, 467.92, 671.21, 0, 0),
            "isabel-ii-jura-constitucion-1837": (425, 355, 508, 434.32, -42, -41.26),
            "azana-homenaje-coruna-franco": (548.5, 362.12, 1068.6, 617.73, -520.1, -23.08),
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
