"""Integrity checks for the reviewed document corpus."""
import json
import hashlib
import importlib.util
import math
from pathlib import Path
import re
import unicodedata
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
    def test_pdf_import_preserves_the_original_corpus_and_counts_only_available_materials(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        original = []
        imported = []
        for record in data["documents"]:
            previous = [a for a in record["appearances"] if a["year"] >= 2008]
            if previous:
                original.append({key: previous if key == "appearances" else value
                                 for key, value in record.items() if key not in ("primaryTextId", "memberIds")
                                 and not (record["id"] == "casas-viejas-detenciones-1933"
                                          and key in ("image", "quality", "sourceCaption"))
                                 and not (record["id"] in ("mural-constitucion-1812-cadiz", "prim-busca-regimen-caricatura",
                                                          "directorio-civil-alfonso-xiii-1925", "reparto-armas-madrid-1936")
                                          and key in ("image", "quality"))
                                 and not (record["id"] == "constitucion-1812-articulos-2008"
                                          and key == "studyCompilation")})
            imported.extend(a for a in record["appearances"] if a["year"] <= 2007)
        digest = hashlib.sha256(json.dumps(
            original, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(len(original), 178)
        self.assertEqual(digest, "c6f5dfb6bb4e65acc8dd9f16d32ea21a7f6ca24032c3554a39644e8a02f8c871")
        self.assertEqual(len(imported), 134)
        self.assertEqual(len({a["pdfUrl"] for a in imported}), 36)
        self.assertEqual(data["coverage"]["sourceHeadingCount"], 95)
        self.assertEqual(data["coverage"]["sourceDocumentOccurrences"], 394)
        pending = data["coverage"]["pdfImport"]["pendingMaterials"]
        keys = {a["sourceKey"] for a in imported}
        self.assertEqual(len(pending), 10)
        self.assertFalse(keys.intersection(a["key"] for a in pending))
        for year in range(2002, 2008):
            selected = [a for a in imported if a["year"] == year]
            self.assertEqual(len(selected), 14 if year == 2006 else 24)
            self.assertEqual(len({a["pdfUrl"] for a in selected}), 6)
            for appearance in selected:
                self.assertEqual(appearance["sourceType"], "pdf")
                self.assertEqual(appearance["sourceUrl"], appearance["pdfUrl"])
                self.assertRegex(appearance["sourceSha256"], r"^[0-9a-f]{64}$")
                self.assertFalse(Path(appearance["officialFile"]).is_absolute())
                self.assertIn(appearance["sourceOrdinal"], range(1, 5))
                if year >= 2006:
                    self.assertIsNone(appearance["document"])
                    self.assertRegex(appearance["route"], r"^Bloque II? · Opción [AB]$")

    def test_2006_copies_do_not_replace_or_degrade_original_transcriptions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        for record in records.values():
            copied = [a for a in record["appearances"] if a["year"] == 2006]
            if not copied:
                continue
            with self.subTest(document=record["id"]):
                self.assertEqual(record["type"], "texto")
                self.assertEqual(copied, record["appearances"])
                self.assertTrue(all(a["sourceReviewStatus"] == "transcription-copy" for a in copied))
                self.assertIn("no original", record["readingNote"])
                self.assertNotIn("image", record)
        for group in data["textGroups"]:
            if any(a["year"] == 2006 for identity in group for a in records[identity]["appearances"]):
                primary = records[records[group[0]]["primaryTextId"]]
                self.assertTrue(all(a["year"] != 2006 for a in primary["appearances"]))
        songs = records["canciones-guerra-civil"]["text"]
        self.assertIn("¿Para qué tantos humos", songs[0])
        self.assertNotIn("Cuando se enteró", songs[0])
        self.assertIn("Canción republicana", songs[0])
        self.assertIn("Cuando se enteró", songs[1])
        self.assertIn("Canción falangista", songs[1])
        cavalry = records["huelga-1917-caballeria"]
        self.assertNotEqual(cavalry["image"]["src"], records["huelga-general-1917-fotografia"]["image"]["src"])

    def test_curriculum_units_cover_grouped_documents_without_reclassifying_the_archive(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        groups = {group[0]: group for group in data["textGroups"]}
        secondary = {identity for group in data["textGroups"] for identity in group[1:]}
        units = data["curriculum"]["units"]
        self.assertEqual({unit["id"] for unit in units},
                         {f"ii-{number}" for number in range(1, 13)}
                         | {f"iii-{number}" for number in range(1, 14)})
        expected = {identity for identity, record in records.items()
                    if identity not in secondary and any(block >= 5 for block in record["blocks"])}
        assigned = set()
        for unit in units:
            self.assertEqual(len(unit["documentIds"]), len(set(unit["documentIds"])))
            for identity in unit["documentIds"]:
                with self.subTest(unit=unit["id"], document=identity):
                    self.assertIn(identity, expected)
                    for member in groups.get(identity, [identity]):
                        self.assertIn(unit["block"], records[member]["blocks"])
                assigned.add(identity)
        self.assertEqual(assigned, expected)
        colonial = next(unit for unit in units if unit["id"] == "ii-10")
        for identity in ("tratado-de-paris-y-perdida-del-imperio-colonial",
                         "debate-parlamentario-desastre-1899", "manifiesto-montecristi-1895"):
            self.assertIn(identity, colonial["documentIds"])
            for member in groups[identity]:
                self.assertEqual(records[member]["blocks"], [7])

    def test_ordinal_enumerations_do_not_use_the_letter_o(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        for record in data["documents"]:
            for paragraph in record.get("text", []):
                with self.subTest(document=record["id"], paragraph=paragraph):
                    self.assertNotRegex(paragraph, r"\b\d+[oOaA][.)]|\b\d+°[.)]")

    def test_desamortization_documents_belong_to_the_economy_block(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identifier in (
            "decreto-de-desamortizacion-de-mendizabal",
            "decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal",
            "exposicion-de-mendizabal-sobre-los-objetivos-de-la-desamortizacion",
            "grafico-desamortizaciones-siglo-xix",
            "mendizabal-explica-la-desamortizacion-de-1836",
            "mapa-desamortizacion-madoz",
            "desamortizacion-eclesiastica-civil-1834-1856",
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
            "investidura-de-jose-maria-aznar": "e8e302b1ed57a98dc86ea9b8e3151153159bde2f56ed09dfdb709b15d5b1f5a3",
        }
        for identifier, expected in original.items():
            record = records[identifier]
            self.assertEqual(record["attributionParagraphs"], 1)
            self.assertEqual(hashlib.sha256(" ".join(record["text"]).encode()).hexdigest(), expected)
        aznar = records["investidura-de-jose-maria-aznar"]["text"]
        self.assertTrue(aznar[-2].endswith("en nuestra vida pública."))
        self.assertTrue(aznar[-1].startswith("Discurso de D. José María Aznar"))
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
        self.assertTrue(any("veinte millones de dólares dentro de los tres meses después del canje" in paragraph
                            for paragraph in treaty))
        self.assertTrue(any("durante el término de diez años" in paragraph for paragraph in treaty))
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

    def test_prepared_annotations_have_sources_and_visible_crop_coordinates(self):
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
                items = annotations.get("symbols", annotations.get("people"))
                self.assertTrue(items)
                for person in items:
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

    def test_alhucemas_people_have_separate_callouts_on_the_official_exam_crop(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "primo-rivera-sanjurjo-alhucemas-1925")
        people = record["image"]["annotations"]["people"]
        self.assertEqual([person["name"] for person in people], ["Miguel Primo de Rivera", "José Sanjurjo"])
        self.assertEqual(record["sourceCaption"], "2009 Examen 5, opción B, documento 2.")
        self.assertEqual(record["image"]["width"], 1700)
        self.assertEqual(record["image"]["height"], 1128)
        self.assertTrue((ROOT / record["image"]["src"]).is_file())
        self.assertTrue(all(person["position"].startswith("En la parte trasera del coche principal") for person in people))
        self.assertTrue(all(0.36 < person["x"] < 0.45 and 0.5 < person["y"] < 0.57 for person in people))
        self.assertLess(people[0]["x"], people[1]["x"])

    def test_esquilache_is_a_historical_block_four_document_with_supplied_reproduction(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "motin-esquilache-1766")
        self.assertEqual(record["blocks"], [4])
        self.assertEqual(image_dimensions(ROOT / record["image"]["src"]), (2488, 1370))
        self.assertIn("CC BY-SA 3.0", record["image"]["reproductionNote"])
        self.assertIn("fuera del comentario", record["quality"])
        self.assertEqual(len(record["appearances"]), 2)
        appearance = record["appearances"][0]
        self.assertEqual((appearance["year"], appearance["exam"], appearance["route"], appearance["document"]),
                         (2013, "2013 Reserva B extraordinaria", "Opción A", 2))
        self.assertIn("h.6w2urkb44k1", appearance["sourceUrl"])

    def test_vergara_uses_the_larger_docs_reproduction_and_keeps_the_exam_crop(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "abrazo-vergara-1839")
        self.assertEqual(record["blocks"], [6])
        self.assertEqual(image_dimensions(ROOT / record["image"]["src"]), (1200, 752))
        self.assertEqual(image_dimensions(ROOT / record["image"]["originalSrc"]), (640, 358))
        self.assertNotIn("crop", record["image"])
        self.assertEqual(hashlib.sha256((ROOT / record["image"]["originalSrc"]).read_bytes()).hexdigest(),
                         "5e2da3ea230417079456da9e0d0b8e57fb2f38ca5aecf2af9c619aa5adfaf299")
        self.assertIn("sin reescalado", record["quality"])
        appearance = record["appearances"][0]
        self.assertEqual((appearance["year"], appearance["route"], appearance["document"]), (2014, "Opción A", 1))
        self.assertEqual(appearance["officialFile"], "sel_2014_historia_espana.zip/sel_2014_texto_historico/reserva b.pdf")
        self.assertEqual(appearance["officialPage"], 1)
        self.assertEqual(record["image"]["sourceUrl"], appearance["sourceUrl"])

    def test_text_groups_preserve_separate_selections_and_all_occurrences(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        assigned = set()
        for group in data["textGroups"]:
            self.assertGreaterEqual(len(group), 2)
            for identity in group:
                self.assertNotIn(identity, assigned)
                self.assertEqual(records[identity]["type"], "texto")
                self.assertTrue(records[identity]["text"])
                self.assertTrue(records[identity]["appearances"])
                assigned.add(identity)
        self.assertIn(["antonio-maura-critica-la-representacion-politica",
                       "antonio-maura-sobre-el-sistema-electoral"], data["textGroups"])
        self.assertFalse(any("constitucion-1978-preambulo-suplente-b" in group
                             and "constitucion-1978-gobierno-97-98-101" in group
                             for group in data["textGroups"]))

    def test_reading_paragraphs_join_scan_lines_but_keep_articles_and_attributions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        for record in records.values():
            for heading in record.get("headingParagraphs", []):
                self.assertIs(type(heading), int)
                self.assertGreaterEqual(heading, 0)
                self.assertLess(heading, len(record["text"]))
                self.assertIn(heading, record.get("paragraphStarts", range(len(record["text"]))))
            if "paragraphStarts" not in record:
                continue
            starts = record["paragraphStarts"]
            self.assertEqual(starts[0], 0)
            self.assertEqual(starts, sorted(set(starts)))
            self.assertLess(starts[-1], len(record["text"]))
            self.assertIn(len(record["text"]) - record["attributionParagraphs"], starts)
            paragraphs = [" ".join(record["text"][start:end])
                          for start, end in zip(starts, starts[1:] + [len(record["text"])])]
            self.assertEqual(" ".join(paragraphs), " ".join(record["text"]))
        directorio = records["constitucion-directorio-militar-1923"]
        self.assertEqual(hashlib.sha256(" ".join(directorio["text"]).encode()).hexdigest(),
                         "dcebd9af07774a88d7ce4a151cfdffca601dfcfff12fac992bcf0141863f4e25")
        constitution = records["constitucion-cadiz-articulos-1812"]
        paragraphs = [" ".join(constitution["text"][start:end]) for start, end in zip(
            constitution["paragraphStarts"], constitution["paragraphStarts"][1:] + [len(constitution["text"])])]
        self.assertTrue(paragraphs[1].endswith("ninguna familia ni persona."))
        self.assertTrue(paragraphs[2].startswith("Art. 3."))

    def test_2012_carlist_map_has_a_vector_and_preserves_the_monochrome_source(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {document["id"]: document for document in data["documents"]}
        carlist_map = records["mapa-primera-guerra-carlista-2012"]
        self.assertEqual(carlist_map["type"], "grafico")
        image_path = ROOT / carlist_map["image"]["src"]
        self.assertEqual(carlist_map["blocks"], [6])
        self.assertEqual(image_dimensions(image_path), (1184, 1190))
        self.assertTrue(carlist_map["image"]["selectable"])
        self.assertIn("focos y expediciones", carlist_map["image"]["examCaption"]["text"])
        original = ROOT / carlist_map["image"]["corpusSrc"]
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                         "2b224bf713d3fa6a2363b5f2f67eb1420eea5feb7c92c8f9976f524876b801f3")
        self.assertIn("blanco y negro", carlist_map["quality"])
        self.assertIn("no es una reproducción del examen", carlist_map["quality"])
        self.assertEqual(len(carlist_map["table"]["rows"]), 7)
        root = ET.parse(image_path).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertIsNotNone(root.find(f"{namespace}title"))
        self.assertIsNotNone(root.find(f"{namespace}desc"))
        self.assertIsNotNone(root.find(f".//*[@id='focos']"))
        self.assertIsNotNone(root.find(f".//*[@id='expediciones']"))
        self.assertFalse(root.findall(f".//{namespace}image"))
        labels = {"".join(node.itertext()).strip() for node in root.iter(f"{namespace}text")}
        self.assertIn("Estella", labels)
        self.assertIn("Arganda", labels)
        self.assertIn("mapa-primera-guerra-carlista-2012-bn.png", root.find(f"{namespace}metadata").text)
        self.assertIn("Iberian_Peninsula_location_map.svg", root.find(f"{namespace}metadata").text)
        self.assertIn("CC BY-SA 3.0", root.find(f"{namespace}metadata").text)
        base_geometry = root.find(".//*[@id='polygon115']")
        self.assertEqual(hashlib.sha256(base_geometry.get("points").encode()).hexdigest(),
                         "3778538f4bc468586fdefca531f2d4036ada8eb61c46b275047c773ff7ca6be1")
        self.assertIn(2012, data["coverage"]["sourceYearsWithDocumentComment"])
        alhucemas = records["primo-rivera-sanjurjo-alhucemas-1925"]
        self.assertTrue(any(appearance["year"] == 2012 for appearance in alhucemas["appearances"]))
        self.assertTrue((ROOT / alhucemas["image"]["corpusSrc"]).is_file())

    def test_carlist_map_legend_matches_curved_routes_and_city_symbols(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "mapa-primera-guerra-carlista-2012")
        root = ET.parse(ROOT / record["image"]["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        legend = root.find(".//*[@id='leyenda']")
        labels = {" ".join("".join(node.itertext()).split()) for node in legend.iter(f"{namespace}text")}
        for label, _ in record["table"]["rows"]:
            self.assertIn(label, labels)
        self.assertIsNotNone(root.find(".//*[@id='influencia']"))
        for city, color in (("Estella", "#fff"), ("Cantavieja", "#fff"), ("Zaragoza", "#fff"),
                            ("Madrid", "#111"), ("Pamplona", "#fff")):
            circle = root.find(f".//*[@data-city='{city}']/{namespace}circle")
            self.assertEqual(circle.get("fill"), color)
        for name in ("gomez", "real"):
            marker = root.find(f".//*[@id='arrow-{name}']")
            self.assertGreaterEqual(float(marker.get("markerWidth")), 8)
            self.assertEqual(marker.find(f"{namespace}path").get("fill"), "#b64032" if name == "gomez" else "#28725d")
            route = root.find(f".//*[@id='ruta-{name}']")
            arrows = [node for node in route if node.get("marker-end")]
            self.assertGreater(len(arrows), 2)
            for path in arrows:
                self.assertIn("C", path.get("d"))
                self.assertEqual(path.get("marker-end"), f"url(#arrow-{name})")
                self.assertEqual(bool(path.get("stroke-dasharray")), name == "real")
        self.assertEqual(len(root.findall(f".//*[@id='focos']/{namespace}ellipse")), 3)
        self.assertFalse(root.findall(f".//{namespace}textPath"))
        cities = {node.get("data-city") for node in root.findall(".//*[@data-city]")}
        self.assertEqual(cities, {
            "A Coruña", "Santiago de Compostela", "Gijón", "León", "Bilbao", "San Sebastián",
            "Amurrio", "Vergara", "Estella", "Pamplona", "Logroño", "Huesca", "Zaragoza",
            "Berga", "Barcelona", "Cantavieja", "Morella", "Madrid", "Arganda", "Cuenca",
            "Valencia", "Cáceres", "Badajoz", "Córdoba", "Jaén", "Sevilla", "Huelva",
            "Granada", "Murcia", "Alicante", "Cartagena",
        })
        texts = " ".join("".join(node.itertext()) for node in root.iter(f"{namespace}text"))
        self.assertNotRegex(texts.casefold(), r"océano|mediterráneo|francia|portugal|arcos|almadén")
        focus = root.find(".//*[@id='focos']")
        self.assertEqual(focus.get("fill"), "none")
        self.assertGreaterEqual(float(focus.get("stroke-width")), 5)
        legend_ellipse = root.find(f".//*[@id='leyenda']/{namespace}ellipse")
        self.assertEqual(legend_ellipse.get("fill"), "none")
        self.assertEqual(legend_ellipse.get("stroke"), focus.get("stroke"))
        for area in root.findall(f".//*[@id='influencia']/{namespace}path"):
            self.assertEqual(area.get("fill"), "#c4d698")
        self.assertIn("stroke:#b64032", root.find(".//*[@id='ruta-gomez']").get("style"))
        self.assertIn("stroke:#28725d", root.find(".//*[@id='ruta-real']").get("style"))

    def test_carlist_arrow_bases_and_tips_are_aligned_with_both_route_sides(self):
        root = ET.parse(ROOT / "assets/documentos/mapa-primera-guerra-carlista-vector.svg").getroot()

        def coordinates(path):
            tokens = re.findall(r"[MCL]|-?\d+(?:\.\d+)?", path.get("d"))
            start = tuple(map(float, tokens[1:3]))
            segments = []
            index = 3
            while index < len(tokens):
                count = 6 if tokens[index] == "C" else 2
                values = list(map(float, tokens[index + 1:index + 1 + count]))
                segments.append([tuple(values[i:i + 2]) for i in range(0, count, 2)])
                index += count + 1
            return start, segments

        for name in ("gomez", "real"):
            marker = root.find(f".//*[@id='arrow-{name}']")
            self.assertEqual(float(marker.get("refX")), 10)
            self.assertEqual(float(marker.get("refY")), 4)
            self.assertAlmostEqual(float(marker.get("markerHeight")) / float(marker.get("markerWidth")), .8)
            routes = list(root.find(f".//*[@id='ruta-{name}']"))
            for index, path in enumerate(routes):
                _, segments = coordinates(path)
                base, tip = segments[-2][-1], segments[-1][-1]
                length = math.dist(base, tip)
                self.assertAlmostEqual(length, float(marker.get("markerWidth")), delta=.02)
                ux, uy = ((tip[i] - base[i]) / length for i in range(2))
                incoming = segments[-2][-2]
                self.assertAlmostEqual((base[0] - incoming[0]) * uy - (base[1] - incoming[1]) * ux, 0, delta=.02)
                if index + 1 < len(routes):
                    start, following = coordinates(routes[index + 1])
                    self.assertLess(math.dist(start, tip), .02)
                    outgoing = following[0][0]
                    self.assertAlmostEqual((outgoing[0] - tip[0]) * uy - (outgoing[1] - tip[1]) * ux, 0, delta=.02)

        gomez = list(root.find(".//*[@id='ruta-gomez']"))
        start, return_curve = coordinates(gomez[-1])
        end = return_curve[-1][-1]
        amurrio = root.find(".//*[@data-city='Amurrio']/{http://www.w3.org/2000/svg}circle")
        self.assertLess(math.dist(end, (float(amurrio.get("cx")), float(amurrio.get("cy")))), .02)
        sampled = []
        current = start
        for segment in return_curve:
            for step in range(33):
                t = step / 32
                if len(segment) == 3:
                    weights = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3)
                    point = tuple(sum(weight * p[i] for weight, p in zip(weights, [current, *segment])) for i in range(2))
                else:
                    point = tuple(current[i] + (segment[-1][i] - current[i]) * t for i in range(2))
                sampled.append(point)
            current = segment[-1]
        offsets = [abs((point[0] - start[0]) * (end[1] - start[1])
                       - (point[1] - start[1]) * (end[0] - start[0])) / math.dist(start, end)
                   for point in sampled]
        self.assertGreater(max(offsets), 2)
        self.assertLess(max(offsets), 16)
        cantavieja = root.find(".//*[@data-city='Cantavieja']/{http://www.w3.org/2000/svg}circle")
        city_point = (float(cantavieja.get("cx")), float(cantavieja.get("cy")))
        self.assertTrue(any(math.dist(coordinates(path)[1][-1][-1], city_point) < .02 for path in routes))
        morella = root.find(".//*[@data-city='Morella']/{http://www.w3.org/2000/svg}circle")
        self.assertGreater(float(morella.get("cy")), city_point[1])

    def test_carlist_control_ellipses_enclose_the_correct_city_markers(self):
        root = ET.parse(ROOT / "assets/documentos/mapa-primera-guerra-carlista-vector.svg").getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        for region, expected in (
            ("norte", {"Bilbao", "San Sebastián", "Amurrio", "Vergara", "Estella", "Pamplona"}),
            ("cataluna", {"Berga"}),
            ("maestrazgo", {"Cantavieja", "Morella"}),
        ):
            ellipse = root.find(f".//*[@id='control-{region}']")
            cx, cy, rx, ry = (float(ellipse.get(key)) for key in ("cx", "cy", "rx", "ry"))
            angle = math.radians(float(ellipse.get("transform").split("(")[1].split()[0]))
            cosine, sine = math.cos(angle), math.sin(angle)

            def contains(x, y):
                dx, dy = x - cx, y - cy
                return ((cosine * dx + sine * dy) / rx) ** 2 + ((-sine * dx + cosine * dy) / ry) ** 2 <= 1

            for city in root.findall(".//*[@data-city]"):
                name = city.get("data-city")
                circle = city.find(f"{namespace}circle")
                x, y = float(circle.get("cx")), float(circle.get("cy"))
                with self.subTest(region=region, city=name):
                    self.assertEqual(contains(x, y), name in expected)
                    if name in expected:
                        radius = float(circle.get("r")) + 1
                        for step in range(32):
                            theta = step * math.tau / 32
                            self.assertTrue(contains(x + radius * math.cos(theta), y + radius * math.sin(theta)))

        areas = root.findall(f".//*[@id='influencia']/{namespace}path")
        self.assertEqual(len(areas), 1, "La influencia carlista debe formar una sola zona verde continua")
        self.assertEqual(areas[0].get("d").upper().count("M"), 2, "Un contorno exterior y un único enclave sin sombreado")
        self.assertEqual(areas[0].get("fill-rule"), "evenodd")

    def test_pavia_uses_the_supplied_high_resolution_reproduction(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "disolucion-cortes-general-pavia-1874")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (4000, 2824))
        self.assertEqual((image["width"], image["height"]), (4000, 2824))
        self.assertEqual(record["examCaption"]["appearanceId"], "fuente-h.a4tcharkltvm-2")

    def test_narvaez_uses_the_docs_color_crop_and_keeps_the_original_exam_image(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "retrato-ramon-maria-narvaez")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (514, 800))
        self.assertEqual((image["width"], image["height"]), (514, 800))
        self.assertEqual(image["crop"], {
            "width": 362, "height": 352, "imageWidth": 514, "imageHeight": 800,
            "left": -92, "top": -96,
        })
        self.assertEqual(image_dimensions(ROOT / image["originalSrc"]), (363, 350))
        self.assertEqual(image["sourceUrl"], record["appearances"][0]["sourceUrl"])
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "e6b37510d9b5bb207fed400208f80a245be0178de6fb589dd3989d7e0f53a868")
        self.assertEqual(record["appearances"][0]["officialPage"], 1)
        self.assertEqual(record["appearances"][0]["route"], "Opción A")
        self.assertEqual(record["appearances"][0]["exam"], "2008 Examen 5")
        self.assertEqual(record["appearances"][0]["document"], 2)

    def test_colonial_losses_and_maine_are_in_restoration_block_and_images_are_toned(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {d["id"]: d for d in data["documents"]}
        for identifier in ("bajas-espanolas-en-cuba-y-filipinas", "acorazado-maine-1898"):
            self.assertEqual(records[identifier]["blocks"], [7])
            self.assertIn("Restauración borbónica", records[identifier]["tags"])
        for identifier in ("portada-constitucion-1812", "acorazado-maine-1898", "no-pasaran-sitio-madrid"):
            self.assertTrue(records[identifier]["image"]["filter"])

    def test_casares_quiroga_role_includes_the_1936_coup_context(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "azana-homenaje-coruna-franco")
        role = next(p["role"] for p in record["image"]["annotations"]["people"]
                    if p["name"] == "Santiago Casares Quiroga")
        self.assertIn("presidente del Consejo de Ministros", role)
        self.assertIn("17 de julio de 1936", role)

    def test_emphasis_parts_are_ordered_literal_fragments(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        for record in data["documents"]:
            sources = []
            if "attributionEmphasis" in record:
                self.assertTrue(record.get("attributionParagraphs"))
                sources.append((record["text"][-1], record["attributionEmphasis"]))
            for index, phrases in record.get("headingEmphasis", {}).items():
                self.assertIn(int(index), record["headingParagraphs"])
                sources.append((record["text"][int(index)], phrases))
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

    def test_pdf_links_keep_each_exam_distinct_across_documents(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        by_source = {}
        by_pdf = {}
        for record in data["documents"]:
            for appearance in record["appearances"]:
                source = appearance["sourceUrl"]
                pdf = appearance["pdfUrl"]
                with self.subTest(source=source, document=record["id"]):
                    self.assertEqual(by_source.setdefault(source, pdf), pdf)
                    self.assertEqual(by_pdf.setdefault(pdf, source), source)
        expected = {
            "h.5qiyxceviwuz": "1fES0P1sntR-fPBHW1xuzjl5aMN_kCvyD",
            "h.6cr2y5ox1qsc": "1CJFlJpA0RbpdDK6pAWYyRfVABCEGOyU2",
            "h.7bxjd4xweowb": "19Ls3qdqeF8IRwGMAmov5uZ-PWPmAWuqi",
            "h.tyo9mvypmp5d": "1Qijo6zDs1l_wZqK0SZAv5uz9c-hgaIuh",
        }
        for heading, identifier in expected.items():
            source = f"{data['source']}#heading={heading}"
            self.assertEqual(by_source[source], f"https://drive.google.com/file/d/{identifier}/view")

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
                self.assertTrue(all(isinstance(block, int) and 4 <= block <= 12 for block in document["blocks"]))
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
                    if appearance.get("sourceType") == "pdf":
                        self.assertEqual(parsed.hostname, "drive.google.com")
                        self.assertEqual(appearance["sourceUrl"], appearance["pdfUrl"])
                    else:
                        self.assertEqual(parsed.hostname, "docs.google.com")
                        self.assertTrue(parsed.fragment.startswith("heading="))
                    self.assertRegex(
                        appearance["pdfUrl"],
                        r"^https://drive\.google\.com/file/d/[A-Za-z0-9_-]+/view$",
                    )
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

    def test_image_crops_match_reviewed_source_viewports(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        crops = {
            document["id"]: document["image"]["crop"]
            for document in data["documents"] if document.get("image", {}).get("crop")
        }
        paired_crop = crops.pop("fotografias-guerra-civil-entrega-fusiles-y-burgos-1936")
        self.assertEqual(paired_crop, crops["reparto-armas-madrid-1936"])
        source_geometry = {
            "retrato-ramon-maria-narvaez": (362, 352, 514, 800, -92, -96),
            "entrada-alfonso-xii-madrid-1875": (549.51, 364.57, 639.86, 454.92, -45.7, -45.79),
            "primo-rivera-visita-tropas-marruecos": (309, 461, 602, 753, -97, -223),
            "reparto-armas-madrid-1936": (401.34, 315.5, 453.3, 315.5, 0, 0),
            "exaltacion-franco": (207.11, 315.99, 521.67, 315.99, -162.05, 0),
            "general-valeriano-weyler": (467.92, 627.5, 467.92, 671.21, 0, 0),
            "isabel-ii-jura-constitucion-1837": (425, 355, 508, 434.32, -42, -41.26),
            "azana-homenaje-coruna-franco": (548.5, 362.12, 1068.6, 617.73, -520.1, -23.08),
            "nuncio-antoniutti-1956": (864, 644, 878, 658, -5, -8),
            "casas-viejas-detenciones-1933": (490, 432, 771, 567, -112, -128),
            "mural-constitucion-1812-cadiz": (2887, 1516, 2917, 1612, 0, -50),
            "fernando-vii-jura-1820": (588, 444, 700, 545, -56, -24),
            "prim-busca-regimen-caricatura": (1270, 975, 1300, 1094, -15, -9),
            "directorio-civil-alfonso-xiii-1925": (411.15, 392.41, 705.16, 436.92, -85.51, -44.51),
            "huelga-1917-caballeria": (792, 608, 1300, 865, -368, 0),
            "camino-exilio-1939": (761, 401, 1175, 933, -114, -311),
        }
        self.assertEqual(set(crops), set(source_geometry))
        for document_id, geometry in source_geometry.items():
            with self.subTest(document=document_id):
                self.assertEqual(crops[document_id], dict(zip(
                    ("width", "height", "imageWidth", "imageHeight", "left", "top"), geometry,
                )))

    def test_cadiz_reproduction_keeps_three_exams_and_the_original_pdf_image(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "mural-constitucion-1812-cadiz")
        self.assertEqual(sorted((a["year"], a["exam"]) for a in record["appearances"]),
                         [(2004, "2004 Examen 5"), (2005, "2005 Examen 3"), (2014, "2014 Reserva A")])
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (2917, 1612))
        original = ROOT / image["originalSrc"]
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                         "1d55899e1aae582a4db9dec5d56f6a942482f38da2d7928a4c785bbe48f1dfb5")
        crop = image["crop"]
        old_width, old_height = image_dimensions(original)
        self.assertAlmostEqual(crop["width"] / crop["height"], old_width / old_height, places=3)
        self.assertEqual(record["examCaption"]["text"], "Pintura mural titulada “Constitución de 1812 en Cádiz”")

    def test_1812_study_compilation_unifies_requested_passages_without_extra_occurrences(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {r["id"]: r for r in data["documents"]}
        record = records["constitucion-1812-articulos-2008"]
        compilation = record["studyCompilation"]
        paragraphs = compilation["text"]
        self.assertEqual(len(paragraphs), 13)
        self.assertEqual([int(re.match(r"Art\. (\d+)\.", p)[1]) for p in paragraphs[2:-1]],
                         [1, 2, 3, 4, 14, 15, 16, 17, 287, 371])
        introduction = records["constitucion-1812-articulos-2008-pdf-2003-1-1"]["text"]
        self.assertEqual(paragraphs[0], introduction[0].removeprefix(
            "CONSTITUCIÓN DE CÁDIZ DE 1812 ").replace("SEPTIMO", "SÉPTIMO"))
        self.assertEqual(paragraphs[1], introduction[1].removeprefix(
            "CONSTITUCIÓN POLÍTICA DE LA MONARQUÍA ESPAÑOLA "))
        selected = records["constitucion-1812-articulos-2008-2015-lxhnexopmiob-2"]["text"]
        tokens = lambda text: re.findall(r"\w+", text.casefold())
        self.assertEqual([tokens(p) for p in paragraphs[2:10]], [tokens(p) for p in selected[:8]])
        self.assertEqual(paragraphs[10], record["text"][4])
        self.assertEqual(paragraphs[11], record["text"][5].replace("tiene libertad", "tienen libertad"))
        group = next(group for group in data["textGroups"] if group[0] == record["id"])
        appearances = [a for identity in group for a in records[identity]["appearances"]]
        self.assertEqual(sorted(a["year"] for a in appearances), [2003, 2004, 2006, 2007, 2008, 2012, 2015, 2016])
        self.assertNotIn("appearances", compilation)
        self.assertIn("No es el texto íntegro", compilation["readingNote"])
        self.assertIn("tiene libertad", record["text"][5])

    def test_2004_reproductions_keep_originals_and_wikimedia_colors(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identity, dimensions, original_hash in (
            ("fernando-vii-jura-1820", (700, 545), "9bab52ba50d7fd747294487d252e42fcff84b1131fec0b57440a560787b20e12"),
            ("goya-carga-mamelucos", (3051, 2359), "37b4110ef5dc1f14923d5a0b084889eb917c5be729ced4f932c5e76917385224"),
            ("primer-gobierno-republica-1873", (1226, 1658), "3166eef2d8b5dbc7606c16989632e27d6f0057386dce3f25c740cde2db179a0d"),
            ("sagasta-embudo-electoral", (1181, 821), "22763cd246f42810613d43205ab328acf9573f4deee2f2c6ac7b2ba62df349b8"),
            ("alegoria-republica-1931", (1018, 1397), "67c9af49c7d9a53d49a5ecb67adad444d703f200d35d15ec00c68ddb9a92febc"),
            ("asamblea-estudiantes-barcelona-1966", (1000, 643), "5b0cfae3f28b9485e4a3184e1ac04eca718e4bd388a8735bd12eb8aded5e967e"),
        ):
            record = records[identity]
            image = record["image"]
            self.assertEqual(image_dimensions(ROOT / image["src"]), dimensions)
            self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(), original_hash)
            self.assertNotIn("filter", image)
            self.assertEqual(len(record["appearances"]), 1)
            self.assertEqual(record["appearances"][0]["year"], 2004)
            self.assertEqual(record["examCaption"]["appearanceId"], record["appearances"][0]["id"])
        self.assertNotIn("crop", records["goya-carga-mamelucos"]["image"])
        self.assertEqual(hashlib.sha256((ROOT / records["goya-carga-mamelucos"]["image"]["src"]).read_bytes()).hexdigest(),
                         "6d82144a93c8f9164b0ea31cbb3c88e2cb6175e56e9ea9b9d7398d33178403de")
        self.assertEqual(hashlib.sha256((ROOT / records["primer-gobierno-republica-1873"]["image"]["src"]).read_bytes()).hexdigest(),
                         "95d185802c1fa2b012bd718c5c1ceff7cc4b096d5a0a27cbd6031e426217d28f")
        self.assertEqual(hashlib.sha256((ROOT / records["sagasta-embudo-electoral"]["image"]["src"]).read_bytes()).hexdigest(),
                         "a4e45b6ff9b09b049e3882d51539b51c5f226e1fcb588bf6b0ba0a8acd12ef37")
        self.assertEqual(hashlib.sha256((ROOT / records["alegoria-republica-1931"]["image"]["src"]).read_bytes()).hexdigest(),
                         "bfb7011f51061ec80b419ac64c7b75babcadbef3e20e647cc9693bf43db23944")
        self.assertEqual(hashlib.sha256((ROOT / records["asamblea-estudiantes-barcelona-1966"]["image"]["src"]).read_bytes()).hexdigest(),
                         "cf154b9b3106fdb6f35eefe63bea8e55205f92f58a958bcee5f6e69aecf0abc5")

    def test_prim_crop_keeps_both_exams_and_the_full_attachment(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(r for r in data["documents"] if r["id"] == "prim-busca-regimen-caricatura")
        self.assertEqual(sorted((a["year"], a["exam"], a["route"], a["document"]) for a in record["appearances"]),
                         [(2005, "2005 Examen 4", "Opción A", 2),
                          (2014, "2014 Titular ordinaria", "Opción A", 1)])
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (1300, 1094))
        self.assertEqual(hashlib.sha256((ROOT / image["src"]).read_bytes()).hexdigest(),
                         "2fad165cf9568f87155d53630abf9df447289f256473d8c3663e1615cafee17d")
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "432bec6fb53127e6084beb13759d5f601998fcb4ff6dcec31589cf29af33f4dd")
        self.assertLessEqual(image["crop"]["height"] - image["crop"]["top"], 1004)
        self.assertEqual(record["examCaption"]["appearanceId"], "fuente-h-rwb4cqu1e7m5-1")

    def test_directorio_uses_the_2016_docs_photo_without_losing_its_three_exams(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(r for r in data["documents"] if r["id"] == "directorio-civil-alfonso-xiii-1925")
        self.assertEqual(sorted((a["year"], a["exam"]) for a in record["appearances"]),
                         [(2005, "2005 Examen 1"), (2007, "2007 Examen 6"), (2016, "2016 Titular extraordinaria")])
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (700, 435))
        self.assertEqual(image["sourceUrl"], next(a["sourceUrl"] for a in record["appearances"] if a["year"] == 2016))
        self.assertEqual(hashlib.sha256((ROOT / image["src"]).read_bytes()).hexdigest(),
                         "abaf37665d377d456e85a3cf04793067eecec669c90001bcb4647df63a75c1b8")
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "abe22b4a399078889e504480d72b43d1a0ed67feca170193c3834683ac830228")

    def test_single_fusiles_photo_keeps_the_larger_copy_and_excludes_double_photos(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {r["id"]: r for r in data["documents"]}
        single = records["reparto-armas-madrid-1936"]
        double = records["fotografias-guerra-civil-entrega-fusiles-y-burgos-1936"]
        self.assertEqual(sorted(a["year"] for a in single["appearances"]), [2005, 2025])
        self.assertEqual(sorted(a["year"] for a in double["appearances"]), [2010, 2011, 2012, 2013])
        self.assertFalse({a["sourceKey"] for a in single["appearances"]} & {a["sourceKey"] for a in double["appearances"]})
        self.assertNotIn("additionalImages", single["image"])
        self.assertEqual(len(double["image"]["additionalImages"]), 1)
        self.assertEqual(image_dimensions(ROOT / single["image"]["src"]), (640, 445))
        self.assertEqual(hashlib.sha256((ROOT / single["image"]["src"]).read_bytes()).hexdigest(),
                         "3d2215144e14afb953e45a138c5dee516d4a53945b0c9254b41f4009fb5e1f11")

    def test_2005_republic_photo_uses_the_museum_original_without_altering_it(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(r for r in data["documents"] if r["id"] == "proclamacion-republica-fotografia")
        appearance, = record["appearances"]
        self.assertEqual((appearance["year"], appearance["exam"], appearance["route"], appearance["document"]),
                         (2005, "2005 Examen 6", "Opción B", 2))
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (1440, 1100))
        self.assertEqual(hashlib.sha256((ROOT / image["src"]).read_bytes()).hexdigest(),
                         "d431d3f21c14499f4474f2c760b3a966afa992298be3eb26e24cb814388906d9")
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "4d70efc38dd403153ab0cc7cc435bdf871e62f0d1ae9885bd383b9c9fb86f788")

    def test_2007_replacements_preserve_sources_exams_and_unaltered_image_files(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {r["id"]: r for r in data["documents"]}
        for identity, exam, route, dimensions, image_hash, original_hash in (
            ("huelga-1917-caballeria", "2007 Examen 1", "Bloque II · Opción A", (1300, 865),
             "24d382241acb544134aa1e4eac200fd379e622958a7039dfb8539564fb8e9d05",
             "b213e5242147754f0929986089660e96be1676f5a8680a697f92474bec5084b0"),
            ("camino-exilio-1939", "2007 Examen 5", "Bloque II · Opción B", (1175, 933),
             "d95f070b2cee32606a845b065bcbf51badcf49d3ac988c631e0e95ae35465ebe",
             "d6df1cd96ed9cd91c8147645c068fc3d1da3b14e96a3ec6abf63fd0450973849"),
            ("cartel-ayuda-republica-francia", "2007 Examen 6", "Bloque II · Opción B", (912, 1004),
             "58ef6323d93d728a4be09c16f21a2c3a6e0faa8e491c84b44162ae18c2265681",
             "1101f6e2750e6656511b27dc7cb77403d856b5aca6cfe4958f647a88fde436e9"),
        ):
            with self.subTest(document=identity):
                record = records[identity]
                appearance, = record["appearances"]
                self.assertEqual((appearance["year"], appearance["exam"], appearance["route"]), (2007, exam, route))
                image = record["image"]
                self.assertEqual(image_dimensions(ROOT / image["src"]), dimensions)
                self.assertEqual(hashlib.sha256((ROOT / image["src"]).read_bytes()).hexdigest(), image_hash)
                self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(), original_hash)
        cavalry = records["huelga-1917-caballeria"]["image"]
        self.assertLessEqual(cavalry["crop"]["height"] - cavalry["crop"]["top"], 775)
        poster = records["cartel-ayuda-republica-francia"]["image"]
        self.assertIn("no incluye la franja inferior", poster["reproductionNote"])

    def test_pablo_iglesias_marker_points_to_the_indicated_hands_and_lowercase_date(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(r for r in data["documents"] if r["id"] == "pablo-iglesias-primero-mayo")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (1080, 1350))
        self.assertEqual(hashlib.sha256((ROOT / image["src"]).read_bytes()).hexdigest(),
                         "c67100298d3745854dc6a6afb935809c9efe2bd68d3e14ca95763a64cc9f50f6")
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "40b2b75cfa1d90a739800d0bd7c2c17b9c010874b9d8be9a82fa2b7d65e3755f")
        person, = image["annotations"]["people"]
        self.assertEqual(person["name"], "Pablo Iglesias")
        self.assertTrue(480 <= person["x"] * image["width"] <= 500)
        self.assertTrue(1080 <= person["y"] * image["height"] <= 1110)
        appearance, = record["appearances"]
        self.assertEqual((appearance["year"], appearance["exam"], appearance["route"], appearance["document"]),
                         (2004, "2004 Examen 6", "Opción A", 2))
        for text in (record["title"], record["tags"][0], image["alt"], record["examCaption"]["text"]):
            self.assertIn("primero de mayo", text)
            self.assertNotIn("Primero de Mayo", text)

    def test_1869_heading_is_separate_and_centered_without_changing_its_words(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        record = records["constitucion-1869"]
        self.assertEqual(record["headingParagraphs"], [0])
        self.assertTrue(record["centerHeadings"])
        self.assertEqual(record["text"][0], "Constitución Española de 1 de junio de 1869.")
        self.assertTrue(record["text"][1].startswith("“LA NACIÓN ESPAÑOLA y en su nombre las Cortes"))
        self.assertTrue(record["text"][2].startswith("Art.17."))

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

    def test_vector_charts_remain_self_contained(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        namespace = "{http://www.w3.org/2000/svg}"
        for document in data["documents"]:
            if document["type"] != "grafico":
                continue
            if not document.get("table") and all(a.get("sourceType") == "pdf" for a in document["appearances"]):
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
                metadata = root.find(f"{namespace}metadata")
                if "PDF oficial de 2008" in document.get("sourceCaption", ""):
                    self.assertIsNotNone(metadata)
                    self.assertIn("SHA-256 del PDF:", metadata.text)

    def test_pdf_tables_preserve_original_cells_underlines_and_reproductions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        namespace = "{http://www.w3.org/2000/svg}"
        tables = {d["id"]: d for d in data["documents"]
                  if d.get("table") and all(a.get("sourceType") == "pdf" for a in d["appearances"])}
        self.assertEqual(len(tables), 8)
        for identity, document in tables.items():
            with self.subTest(document=identity):
                image, table = document["image"], document["table"]
                self.assertEqual(image["kind"], "table")
                self.assertTrue(image["src"].endswith(".svg"))
                original_hash = hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest()
                self.assertEqual(image["originalSha256"], original_hash)
                root = ET.parse(ROOT / image["src"]).getroot()
                metadata = json.loads(root.find(f"{namespace}metadata").text)
                self.assertEqual(metadata["originalSha256"], original_hash)
                self.assertEqual(metadata["pdfSha256"], document["appearances"][0]["sourceSha256"])
                for row_index, row in enumerate(table["rows"]):
                    for column_index, value in enumerate(row):
                        cell = root.find(f".//*[@data-row='{row_index}'][@data-column='{column_index}']")
                        self.assertIsNotNone(cell)
                        self.assertEqual(" ".join(" ".join(cell.itertext()).split()), value)
                        underlined = cell.findall(f"{namespace}text[@text-decoration='underline']")
                        self.assertEqual(bool(underlined), [row_index, column_index] in table.get("underlinedCells", []))
        restoration = tables["porcentajes-restauracion"]["table"]
        self.assertEqual(restoration["rows"][1], ["1893", "15,2", "70,2", "85,5", "14,5"])
        self.assertEqual(restoration["underlinedCells"], [[0, 1], [1, 2], [3, 2], [4, 1], [5, 2]])
        self.assertEqual(tables["elecciones-1977-votos-escanos"]["table"]["rows"][5][-1], "3,1")

    def test_new_source_footers_use_existing_attribution_metadata(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {d["id"]: d for d in data["documents"]}
        serrano = records["serrano-suner-estado"]
        self.assertEqual(serrano["attributionParagraphs"], 1)
        self.assertTrue(serrano["text"][-1].startswith("Fuente: Ramón SERRANO SUÑER"))
        for identity in ("perez-galdos-sobre-las-elecciones-de-la-restauracion-pdf-2003-4-1",
                         "sevilla-guzman-reforma-agraria"):
            self.assertEqual(records[identity]["attributionParagraphs"], 2)
        persas = records["manifiesto-persas-1814-pdf-2006-5-1"]
        self.assertEqual(persas["attributionParagraphs"], 1)
        self.assertEqual(persas["text"][-1], "Manifiesto de los Persas. Madrid, 12 de abril de 1814")

    def test_requested_art_and_coin_reproductions_do_not_add_occurrences(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identity, host, dimensions in (
                ("guernica-picasso", "recursos.museoreinasofia.es", (1440, 652)),
                ("primera-peseta-1869", "www.fuenterrebollo.com", (1220, 617))):
            record = records[identity]
            image = record["image"]
            self.assertEqual(urlparse(image["sourceUrl"]).hostname, host)
            self.assertEqual(image_dimensions(ROOT / image["src"]), dimensions)
            self.assertTrue((ROOT / image["originalSrc"]).is_file())
            self.assertEqual(len(record["appearances"]), 1)

    def test_pablo_iglesias_reproduction_preserves_exam_source(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "pablo-iglesias-retrato")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (994, 1406))
        self.assertEqual((image["width"], image["height"]), (994, 1406))
        self.assertNotIn("reproductionNote", image)
        self.assertEqual(image["sourceUrl"],
                         "https://fpabloiglesias.es/wp-content/uploads/hemeroteca/"
                         "ElSocialista/ES-online%20066%202017-05-03.pdf#page=14")
        self.assertNotIn("crop", image)
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "04542e735eb06163f7af5f874c80edf609eecd1f269d8ce2e7d506ad83bd8d21")
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2002-5-2")
        self.assertEqual(record["examCaption"]["appearanceId"], record["appearances"][0]["id"])

    def test_arciniega_original_crop_preserves_photo_and_caption(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "nuncio-antoniutti-1956")
        self.assertEqual(record["title"], "El nuncio Antoniutti y el coronel Arciniega")
        self.assertFalse(any("según el examen" in tag for tag in record["tags"]))
        image = record["image"]
        self.assertEqual(image["src"], image["originalSrc"])
        self.assertEqual(image_dimensions(ROOT / image["src"]), (878, 658))
        self.assertEqual((image["width"], image["height"]), (878, 658))
        self.assertEqual(image["filter"], "grayscale(1)")
        self.assertEqual(image["crop"], {
            "width": 864, "height": 644, "imageWidth": 878, "imageHeight": 658,
            "left": -5, "top": -8,
        })
        self.assertNotIn("reproductionNote", image)
        self.assertEqual(image["sourceUrl"], record["appearances"][0]["pdfUrl"])
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "5d4a385cdaf2f76ccec3b6719b20f36f36f24399bfbe53d23577bb1a7e57fcf9")
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2002-3-4")
        self.assertIn("Arciniega, 1956.", record["examCaption"]["text"])

    def test_espartero_caricature_preserves_exam_and_caption(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "espartero-librecambismo-1842")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (1600, 976))
        self.assertEqual((image["width"], image["height"]), (1600, 976))
        self.assertEqual(image["sourceUrl"], "https://x.com/Arcdelahistori/status/1256908613152432128")
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "316ee7e0cd45b6585fc1dc41ded35409907feb024c3274b5f018e1451a1946cd")
        self.assertEqual(record["examCaption"]["text"],
                         'Caricatura aparecida en "El Republicano" (1842). '
                         'Espartero cobra de los ingleses por sus medidas librecambistas.')
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2003-2-2")
        self.assertEqual(record["examCaption"]["appearanceId"], record["appearances"][0]["id"])

    def test_esquella_caricature_preserves_exam_and_caption(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "caricatura-turno-partidos")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (1084, 1600))
        self.assertEqual((image["width"], image["height"]), (1084, 1600))
        self.assertNotIn("sourceUrl", image)
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "99def11809b3680822e9a9c9781e8c6f53ca21ebe17431b30acd735557d8c9a6")
        self.assertEqual(record["examCaption"]["text"],
                         'Caricatura publicada en la revista "L\'Esquella de la Torratxa".')
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2003-4-2")
        self.assertEqual(record["examCaption"]["appearanceId"], record["appearances"][0]["id"])

    def test_baler_reproduction_keeps_the_exam_description(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "baler-ultimos-filipinas")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (800, 571))
        self.assertEqual((image["width"], image["height"]), (800, 571))
        self.assertEqual(hashlib.sha256((ROOT / image["originalSrc"]).read_bytes()).hexdigest(),
                         "23b670c3447c20daa635a4f32c7b3424aee2c794c3ba738021da7a5733dfe70d")
        self.assertEqual(record["examCaption"]["text"],
                         "Los últimos de Filipinas: La guarnición española de Baler se rindió a los "
                         "independentistas el 2 de junio de 1899, después de 337 días de asedio. "
                         "La guerra había terminado mucho antes.")
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2003-6-2")
        self.assertEqual(record["examCaption"]["appearanceId"], record["appearances"][0]["id"])

    def test_casas_viejas_groups_three_exams_and_keeps_previous_identity(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        self.assertNotIn("casas-viejas-fotografia-2003", records)
        record = records["casas-viejas-detenciones-1933"]
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (771, 567))
        self.assertEqual((image["width"], image["height"]), (771, 567))
        self.assertEqual(image["filter"], "grayscale(1)")
        crop = image["crop"]
        self.assertEqual((crop["width"], crop["height"], -crop["left"], -crop["top"]),
                         (490, 432, 112, 128))
        self.assertLessEqual(-crop["left"] + crop["width"], image["width"])
        self.assertLessEqual(-crop["top"] + crop["height"], image["height"])
        self.assertEqual(image["originalSrc"], "assets/documentos/pdf-2003-5-4.png")
        self.assertTrue((ROOT / image["corpusSrc"]).is_file())
        self.assertNotIn("reproductionNote", image)
        self.assertEqual(record["memberIds"],
                         ["casas-viejas-detenciones-1933", "casas-viejas-fotografia-2003"])
        self.assertEqual([appearance["year"] for appearance in record["appearances"]], [2003, 2008, 2013])
        imported = record["appearances"][0]
        self.assertEqual(imported["sourceKey"], "pdf-2003-5:4")
        self.assertEqual(imported["pdfUrl"],
                         "https://drive.google.com/file/d/18b2s_IvufghxXpIENyxBZD7zhq5Ve_ms/view")
        source = next(source for source in data["coverage"]["sourceManifest"]
                      if source["key"] == imported["sourceKey"])
        self.assertEqual(source["assignedTo"], record["id"])
        self.assertEqual(source["images"], imported["sourceImages"])

    def test_new_corpus_tables_match_their_accessible_data_and_occurrences(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        documents = {document["id"]: document for document in data["documents"]}
        expected = {
            "desamortizacion-eclesiastica-civil-1834-1856": 4,
            "resultados-electorales-restauracion-1876-1886": 3,
            "composicion-congreso-elecciones-febrero-1936": 1,
            "composicion-congreso-elecciones-1977": 1,
        }
        for identifier, appearances in expected.items():
            with self.subTest(document=identifier):
                document = documents[identifier]
                self.assertEqual(document["type"], "grafico")
                self.assertEqual(len([a for a in document["appearances"] if a["year"] >= 2008]), appearances)
                self.assertEqual(document["image"]["kind"], "table")
                self.assertTrue((ROOT / document["image"]["src"]).is_file())
                self.assertEqual((ROOT / document["image"]["src"]).suffix, ".svg")
                self.assertTrue(document["table"]["rows"])

        restoration = documents["resultados-electorales-restauracion-1876-1886"]
        self.assertEqual(
            [appearance["year"] for appearance in restoration["appearances"] if appearance["year"] >= 2008],
            [2010, 2012, 2014],
        )
        desamortization = documents["desamortizacion-eclesiastica-civil-1834-1856"]
        original = desamortization["image"]["corpusSrc"]
        self.assertTrue((ROOT / original).is_file())
        self.assertEqual(
            (image_dimensions(ROOT / original)),
            (700, 435),
        )
        self.assertEqual(
            documents["composicion-congreso-elecciones-1977"]["table"]["rows"][-1],
            ["EE – Euskadiko Ezquerra", 1],
        )
        senate_table = documents["elecciones-generales-1982-congreso-senado"]
        self.assertIn(
            "h.wkz78yy8to0h:3",
            [appearance["sourceKey"] for appearance in senate_table["appearances"]],
        )
        namespace = "{http://www.w3.org/2000/svg}"
        for identifier in expected:
            document = documents[identifier]
            rendered = {
                self._normalize_table_text(node.text.strip())
                for node in ET.parse(ROOT / document["image"]["src"]).iter(f"{namespace}text")
                if node.text and node.text.strip()
            }
            table = document["table"]
            values = table["headers"] + [
                str(value) for row in table["rows"] for value in row
            ]
            for value in values:
                with self.subTest(document=identifier, value=value):
                    self.assertIn(self._normalize_table_text(value), rendered)

    def test_2010_through_2012_corpus_coverage_and_source_images(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        manifest = data["coverage"]["sourceManifest"]
        years = [item for item in manifest if item["year"] in (2010, 2011, 2012)]
        self.assertEqual(len(years), 72)
        self.assertEqual(len({item["heading"] for item in years}), 18)
        self.assertEqual(sum(len(item["images"]) for item in years), 20)
        self.assertEqual(len([item for item in manifest if item["year"] >= 2008]), 260)
        self.assertEqual(data["coverage"]["sourceImageOccurrences"], 163)
        image_ids = [image_id for item in manifest if item["year"] >= 2008 for image_id in item["images"]]
        self.assertEqual(sorted(image_ids), list(range(1, 103)))
        self.assertEqual(len(image_ids), len(set(image_ids)))
        self.assertIn(
            "fotografias-guerra-civil-entrega-fusiles-y-burgos-1936",
            {item["assignedTo"] for item in years},
        )

    def test_no_pasaran_keeps_three_distinct_exam_appearances(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "no-pasaran-sitio-madrid")
        self.assertEqual([(a["year"], a["route"], a["document"]) for a in record["appearances"]],
                         [(2009, "Opción B", 2), (2014, "Opción B", 1), (2015, "Opción B", 1)])
        self.assertEqual([a["sourceKey"] for a in record["appearances"]],
                         ["h.y1u3euanbxcl:4", "h.yjixy43rc4v8:3", "h.nprbq3qsjt1l:3"])
        self.assertIn("Examen ?", record["appearances"][1]["exam"])
        self.assertIn("sin certificar una numeración", record["quality"])
        for appearance in record["appearances"]:
            self.assertEqual(appearance["officialPage"], 2)
            self.assertTrue(appearance["officialFile"].endswith(".pdf"))

    def test_2009_accents_are_corrected_without_hiding_original_pdf_errata(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        aznar = " ".join(records["investidura-de-jose-maria-aznar"]["text"])
        self.assertIn("político", aznar)
        self.assertIn("período", aznar)
        self.assertIn("José María", aznar)
        self.assertIn("al funcionamientos", aznar)
        constitution = records["constitucion-1978-gobierno-97-98-101"]
        self.assertIn("Artículo 98", " ".join(constitution["text"]))
        self.assertIn("Artículo 101", " ".join(constitution["text"]))
        self.assertIn("disminución o fallecimiento", " ".join(constitution["text"]))
        self.assertIn("dimisión", constitution["readingNote"])

    def test_paired_war_photos_keep_separate_captions_and_local_images(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"]
                      if item["id"] == "fotografias-guerra-civil-entrega-fusiles-y-burgos-1936")
        images = [record["image"], *record["image"]["additionalImages"]]
        self.assertEqual(len(images), 2)
        self.assertIn("18 de julio de 1936", images[0]["examCaption"]["text"])
        self.assertIn("Burgos en agosto de 1936", images[1]["examCaption"]["text"])
        for image in images:
            self.assertTrue((ROOT / image["src"]).is_file())
        self.assertEqual(
            [appearance["sourceKey"] for appearance in record["appearances"]],
            ["h.ap6vdvuofbyh:4", "h.d40v7ql2zdxq:4", "h.s6w9kjl20asd:3", "h.r47y1233hkke:4"],
        )

    def test_completed_exam_years_preserve_four_distinct_documents_per_exam(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        appearances = [appearance for record in data["documents"] for appearance in record["appearances"]]
        availability = {entry["year"]: entry for entry in data["coverage"]["officialExamAvailability"]}
        for year, count in {2013: 6, 2014: 5, 2015: 6, 2016: 5, 2025: 6, 2026: 4}.items():
            with self.subTest(year=year):
                selected = [a for a in appearances if a["year"] == year
                            and not a["exam"].endswith("Modelo orientaciones PAU")]
                headings = {a["sourceKey"].split(":")[0] for a in selected}
                self.assertEqual(len(headings), count)
                self.assertEqual(len(selected), count * 4)
                self.assertEqual(availability[year]["exams"], count + (year in (2025, 2026)))
                self.assertEqual(count + len(availability[year].get("unavailableExams", [])), 6)
                for heading in headings:
                    exam = [a for a in selected if a["sourceKey"].startswith(heading + ":")]
                    self.assertEqual({a["sourceOrdinal"] for a in exam}, {1, 2, 3, 4})
                    if year < 2017:
                        self.assertEqual({(a["route"], a["document"]) for a in exam},
                                         {("Opción A", 1), ("Opción A", 2), ("Opción B", 1), ("Opción B", 2)})
                        self.assertTrue(all(a["officialPage"] in (1, 2) and a["officialFile"].endswith(".pdf") for a in exam))
        expected = {"h.5qiyxceviwuz": "2025 Suplente 1 A", "h.6cr2y5ox1qsc": "2025 Suplente 1 B",
                    "h.7bxjd4xweowb": "2025 Suplente 2 A", "h.tyo9mvypmp5d": "2025 Suplente 2 B",
                    "h.vu325nx5299w": "2025 Titular ordinaria", "h.tvlhtdubp2jf": "2025 Titular extraordinaria",
                    "h.rehqimt904hq": "2025 Modelo orientaciones PAU"}
        self.assertEqual({a["sourceKey"].split(":")[0]: a["exam"] for a in appearances if a["year"] == 2025}, expected)

    def test_orientation_models_contribute_four_documents_each_to_frequencies(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        appearances = [(record, appearance) for record in data["documents"]
                       for appearance in record["appearances"]
                       if appearance["exam"].endswith("Modelo orientaciones PAU")]
        self.assertEqual(len(appearances), 12)
        manifest = {entry["key"]: entry for entry in data["coverage"]["sourceManifest"]}
        for year, heading, pdf in (
            (2025, "h.rehqimt904hq", "1xnyJ3ZVFoIbyiME-PoWajjj7-eN64n8j"),
            (2026, "h.u5qgselcamwj", "1YP4IJzY79cz01vqPXlET3D4oBWIU8oP0"),
            (2027, "h.qkign2j8bncv", "1namjFwbxIfKvrgxFEKi5VWmSuj5wOFxa"),
        ):
            selected = [(r, a) for r, a in appearances if a["year"] == year]
            self.assertEqual(len(selected), 4)
            self.assertEqual({(a["route"], a["document"]) for _, a in selected}, {
                ("Itinerario A", 1), ("Itinerario A", 2), ("Itinerario B", 1), ("Itinerario B", 2),
            })
            self.assertEqual(sum(r["type"] != "texto" for r, _ in selected), 2)
            for record, appearance in selected:
                self.assertEqual(appearance["pdfUrl"], f"https://drive.google.com/file/d/{pdf}/view")
                self.assertEqual(appearance["sourceUrl"], f"{data['source']}#heading={heading}")
                self.assertEqual(manifest[appearance["sourceKey"]]["assignedTo"], record["id"])
        records = {record["id"]: record for record in data["documents"]}
        self.assertEqual(len(records["portada-constitucion-1812"]["appearances"]), 3)
        self.assertEqual(len(records["huelga-general-1917-fotografia"]["appearances"]), 2)
        photo = records["franco-saludo-catedral-modelo-2025"]
        self.assertNotEqual(photo["image"]["src"], records["franco-mola-cavalcanti-burgos"]["image"]["src"])
        self.assertEqual(len(photo["appearances"]), 1)

    def test_new_reproductions_do_not_merge_different_compositions(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        for new, old in [
            ("prim-busca-regimen-caricatura", "caricatura-se-colocan-reyes-1869"),
            ("mural-constitucion-1812-cadiz", "juramento-cortes-constituyentes-isla-leon-1810"),
            ("presidentes-monarquia-juan-carlos-2014", "reunion-expresidentes-gobierno"),
            ("carteles-guerra-civil-2016", "cartel-falange"),
            ("directorio-civil-alfonso-xiii-1925", "primo-rivera-directorio-civil-fotografia-1925"),
        ]:
            with self.subTest(document=new):
                image = records[new]["image"]
                self.assertTrue((ROOT / image["src"]).is_file())
                self.assertNotEqual(image["src"], records[old].get("image", {}).get("src"))
        portraits = records["espartero-narvaez-retratos-2016"]["image"]
        self.assertEqual(portraits["examCaption"]["text"], "General Baldomero Espartero")
        self.assertEqual(portraits["additionalImages"][0]["examCaption"]["text"], "General Ramón María Narváez")
        for image in [portraits, *portraits["additionalImages"]]:
            self.assertEqual(image_dimensions(ROOT / image["src"]), (image["width"], image["height"]))
            self.assertTrue((ROOT / image["originalSrc"]).is_file())
            self.assertEqual(image["sourceUrl"], records["espartero-narvaez-retratos-2016"]["appearances"][0]["sourceUrl"])
        self.assertEqual(image_dimensions(ROOT / portraits["src"]), (1609, 2048))
        narvaez = portraits["additionalImages"][0]
        self.assertEqual(narvaez["src"], records["retrato-ramon-maria-narvaez"]["image"]["src"])
        self.assertEqual(narvaez["crop"], {
            "width": 362, "height": 511, "imageWidth": 514, "imageHeight": 800,
            "left": -92, "top": -78,
        })
        visits = records["primo-rivera-visita-tropas-marruecos"]["appearances"]
        self.assertEqual([a["year"] for a in visits if a["year"] >= 2008], [2008, 2011, 2013])
        self.assertEqual([a["sourceKey"] for a in visits if a["year"] < 2008], ["pdf-2004-1:4"])

    def test_1931_election_table_preserves_its_official_figures_and_parties(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "elecciones-cortes-1931")
        rows = record["table"]["rows"]
        self.assertEqual([row[2:] for row in rows], [["279", "2.881.056"], ["119", "1.165.692"], ["41", "657.872"]])
        rendered = " ".join(ET.parse(ROOT / record["image"]["src"]).getroot().itertext())
        for row in rows:
            for value in [row[0], *row[1].split("; "), *row[2:]]:
                self.assertIn(value, rendered)

    @staticmethod
    def _normalize_table_text(value):
        normalized = unicodedata.normalize("NFKD", str(value).casefold())
        normalized = "".join(character for character in normalized
                             if not unicodedata.combining(character))
        return " ".join(normalized.replace("–", "-").replace("—", "-").split())

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
