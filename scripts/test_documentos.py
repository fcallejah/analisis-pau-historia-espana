"""Integrity checks for the reviewed document corpus."""
import json
import hashlib
import importlib.util
import math
from decimal import Decimal
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
map_spec = importlib.util.spec_from_file_location(
    "affiliation_map_tools", ROOT / "scripts/vectorizar-mapa-afiliacion-obrera.py"
)
map_tools = importlib.util.module_from_spec(map_spec)
map_spec.loader.exec_module(map_tools)


def image_dimensions(path):
    if path.suffix == ".svg":
        root = ET.parse(path).getroot()
        return int(root.get("width")), int(root.get("height"))
    dimensions = notes_image_tools.image_dimensions(path.read_bytes())
    if dimensions is None:
        raise ValueError(f"Formato de imagen no compatible: {path}")
    return dimensions


class DocumentCorpusTests(unittest.TestCase):
    def test_electoral_study_materials_do_not_enter_exam_corpus(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        own = json.loads((ROOT / "data/documentos-propios.json").read_text())["documents"]
        records = {record["id"]: record for record in own}
        self.assertEqual(len(records), 21)
        self.assertFalse(set(records) & {record["id"] for record in data["documents"]})
        self.assertTrue(all("appearances" not in record for record in own))
        general_years = {1931, 1933, 1936, 1979, 1982, 1986, 1989, 1993,
                         1996, 2000, 2004, 2008, 2011, 2015}
        general = [record for record in own if record["id"].startswith("propio-elecciones-generales-")]
        self.assertEqual({int(record["date"]) for record in general}, general_years)
        self.assertTrue(all(len(record["tables"]) == 1 for record in general))
        for record in general:
            year = int(record["date"])
            table = record["tables"][0]
            self.assertEqual(int(table["caption"][-4:]), year)
            total = next(row for row in table["rows"] if row[0].strip() == "Total")
            seats = sum(int(row[3]) for row in table["rows"] if row[3] != "—" and row is not total)
            self.assertEqual((total[3], seats), (str(table["chart"]["seats"]), table["chart"]["seats"]))
        self.assertEqual(records["propio-elecciones-generales-1931"]["unitIds"], ["iii-4"])
        self.assertEqual(records["propio-elecciones-generales-1933"]["unitIds"], ["iii-5"])
        self.assertEqual(records["propio-elecciones-generales-1936"]["unitIds"], ["iii-5"])
        self.assertEqual(records["propio-elecciones-generales-1982"]["unitIds"], ["iii-11"])
        self.assertEqual(records["propio-elecciones-generales-1986"]["unitIds"], ["iii-12"])
        self.assertEqual(records["propio-elecciones-generales-1996"]["unitIds"], ["iii-13"])
        municipal = records["propio-elecciones-municipales-1931"]
        self.assertEqual(municipal["visualization"], "municipal-turnout")
        self.assertEqual(municipal["tables"][0]["rows"][0][1:], ["1.104.159", "715.911", "64,84"])
        self.assertIn("no aporta aquí un resultado nacional", municipal["tables"][0]["notes"][0])
        self.assertEqual(municipal["dataSourceUrl"], "https://ine.es/inebaseweb/pdfDispacher.do?td=96303")
        self.assertNotIn("propio-elecciones-1979-1982", records)
        self.assertNotIn("propio-elecciones-segunda-republica", records)
        refs = records["propio-referendums-1976-2005"]["tables"][0]["rows"]
        self.assertEqual(refs[0][0], "15-12-1976 · Reforma Política")
        self.assertEqual(refs[-1][1:], ["41,77", "76,30", "16,93", "5,91", "0,86"])
        andalusia = records["propio-referendum-andalucia-1980"]["tables"][0]
        self.assertEqual(andalusia["rows"][0][1:], ["64,19", "86,94", "5,36", "7,04", "0,67"])
        self.assertIn("rechazada", " ".join(andalusia["notes"]))
        self.assertIn("fuentes secundarias", records["propio-referendums-franquismo"]["sourceCaption"])
        europe = records["propio-referendum-europa-2005"]
        self.assertEqual(europe["unitIds"], ["iii-13"])
        self.assertEqual(europe["tables"][0]["rows"][0][1:], ["41,77", "76,30", "16,93", "5,91", "0,86"])
        self.assertIn("81,84 %", europe["tables"][0]["notes"][0])
        self.assertIn("Fraga", " ".join(section["text"] for section in records["propio-referendums-1976-2005"]["commentary"]))

    def test_electoral_semicircles_match_all_jec_study_tables(self):
        own = json.loads((ROOT / "data/documentos-propios.json").read_text())["documents"]
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        expected_titles = {
            "elecciones-generales-1979-semicirculo.svg": "Resultado elecciones 1979 (1 de marzo)",
            "elecciones-generales-1982-semicirculo.svg": "Resultado elecciones 1982 (28 de octubre)",
            "elecciones-andaluzas-1982-semicirculo.svg": "Resultado elecciones andaluzas 1982 (23 de mayo)",
            "elecciones-generales-1986-semicirculo.svg": "Resultado elecciones 1986 (22 de junio)",
            "elecciones-generales-1989-semicirculo.svg": "Resultado elecciones 1989 (29 de octubre)",
            "elecciones-generales-1993-semicirculo.svg": "Resultado elecciones 1993 (6 de junio)",
            "elecciones-generales-1996-semicirculo.svg": "Resultado elecciones 1996 (3 de marzo)",
            "elecciones-generales-2000-semicirculo.svg": "Resultado elecciones 2000 (12 de marzo)",
            "elecciones-generales-2004-semicirculo.svg": "Resultado elecciones 2004 (14 de marzo)",
            "elecciones-generales-2008-semicirculo.svg": "Resultado elecciones 2008 (9 de marzo)",
            "elecciones-generales-2011-semicirculo.svg": "Resultado elecciones 2011 (20 de noviembre)",
            "elecciones-europeas-2014-semicirculo.svg": "Resultado elecciones europeas 2014 (25 de mayo)",
            "elecciones-generales-2015-semicirculo.svg": "Resultado elecciones 2015 (20 de diciembre)",
        }
        years = set()
        for record in own:
            if record["visualization"] != "elections":
                continue
            for table in record["tables"]:
                year = int(table["caption"][-4:])
                years.add(year)
                chart = table.get("chart", {})
                path = "assets/documentos/" + chart.get("svg", f"elecciones-generales-{year}-semicirculo.svg")
                svg = ET.parse(ROOT / path).getroot()
                self.assertEqual(svg.get("width"), "760")
                if chart.get("svg") in expected_titles:
                    expected_title = expected_titles[chart["svg"]]
                    self.assertEqual(svg.find("svg:title", namespace).text, expected_title)
                    self.assertEqual(
                        svg.find("svg:text[@class='title']", namespace).text, expected_title
                    )
                sectors = svg.findall("svg:path[@class='sector']", namespace)
                visible_party_labels = " ".join(
                    node.text or "" for node in svg.findall(".//svg:text[@class='party']", namespace)
                )
                expected = {row[0]: int(row[3]) for row in table["rows"]
                            if row[0].strip() != "Total" and row[3].isdigit() and int(row[3]) > 0}
                for group in table.get("chartGroups", []):
                    expected[group["label"]] = sum(expected.pop(name) for name in group["members"])
                    if group["label"] in ("PSOE + PSC", "PSOE, PSC y PSOE-Nueva Canarias"):
                        self.assertTrue(group.get("diagramLabel"))
                    if group.get("diagramLabel"):
                        self.assertIn(group["diagramLabel"], visible_party_labels)
                coalition_totals = {
                    1982: {"PSOE + PSC": 202},
                    1986: {"PSOE + PSC": 184},
                    1989: {"PSOE + PSC": 175, "Partido Popular (PP) y coaliciones": 107},
                    1993: {"PSOE + PSC": 159, "Partido Popular (PP) y coaliciones": 141},
                    1996: {"PSOE + PSC": 141, "Partido Popular (PP) y coaliciones": 156},
                    2004: {"Partido Popular (PP) y coaliciones": 148},
                    2008: {"PSOE + PSC": 169, "Partido Popular (PP) y coaliciones": 154},
                    2011: {"PSOE + PSC": 110, "Partido Popular (PP) y coaliciones": 186},
                    2015: {"Partido Popular (PP) y coaliciones": 123},
                }
                if record["id"].startswith("propio-elecciones-generales-"):
                    for label, seats in coalition_totals.get(year, {}).items():
                        self.assertEqual(expected[label], seats)
                        sector = next(sector for sector in sectors if sector.get("data-party") == label)
                        expected_color = "#c6464f" if label == "PSOE + PSC" else "#2d4d73"
                        self.assertEqual(sector.get("fill"), expected_color)
                if year == 2015:
                    self.assertEqual(expected["PSOE, PSC y PSOE-Nueva Canarias"], 90)
                    self.assertEqual(expected["Podemos y confluencias"], 69)
                self.assertEqual({sector.get("data-party"): int(sector.get("data-seats"))
                                  for sector in sectors}, expected)
                self.assertEqual(sum(expected.values()), chart.get("seats", 350))
                self.assertEqual(len(sectors), len(expected))
                self.assertEqual(len({sector.get("fill") for sector in sectors}), len(sectors))
                self.assertTrue(all(float(sector.get("data-seat-percent")) > 0 for sector in sectors))
                if "Otros*" in expected:
                    other = next(sector for sector in sectors if sector.get("data-party") == "Otros*")
                    self.assertEqual(other.get("fill"), "#92979f")
                if year == 1936:
                    self.assertEqual(
                        {sector.get("data-party"): sector.get("fill") for sector in sectors},
                        {
                            "Frente Popular": "#ff0000",
                            "Frente Nacional Contrarrevolucionario": "#0000ff",
                            "Centro y nacionalistas": "#3cb371",
                        },
                    )
                self.assertEqual(json.loads(svg.find("svg:metadata", namespace).text)["source"],
                                 record["dataSourceUrl"])
                self.assertIn(f'"./{path}"', (ROOT / "sw.js").read_text())
                text = " ".join(svg.itertext())
                for name, count in expected.items():
                    self.assertIn(f"{count} {'escaño' if count == 1 else 'escaños'}", text)
                if year == 2015:
                    self.assertIn("5.212.711 votos", text)
                    self.assertIn("5.545.315 votos", text)
                if chart.get("majority") is None and chart:
                    self.assertNotIn("mayoría absoluta", text)
                    self.assertIn("Asignados a España", text)
                elif chart:
                    self.assertIn(f"{chart['majority']} para la mayoría absoluta", text)
        self.assertEqual(years, {1931, 1933, 1936, 1979, 1982, 1986, 1989, 1993, 1996, 2000, 2004, 2008, 2011, 2014, 2015})
        self.assertIn(".study-chart-fill.is-turnout{background:#59636d}", (ROOT / "documentos.css").read_text())

    def test_requested_2002_and_2003_source_captions(self):
        records = {record["id"]: record for record in
                   json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        self.assertEqual(records["produccion-hierro-1860-1869"]["examCaption"]["text"],
                         "Producción de hierro colado\n(media anual en miles de toneladas)")
        assembly = records["la-asamblea-de-parlamentarios-de-barcelona-pdf-2003-1-3"]
        self.assertEqual(assembly["text"][-1], "Barcelona, 19 de julio de 1917")
        self.assertEqual(assembly["attributionParagraphs"], 2)
        self.assertNotIn("reproductionNote", records["afiliacion-obrera-1917"]["image"])
        self.assertEqual(records["prim-busca-regimen-caricatura"]["image"]["filter"], "brightness(1.15)")

    def test_1936_map_caption_preserves_2004_exam(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(record for record in data["documents"] if record["id"] == "mapa-espana-julio-1936")
        self.assertEqual(record["image"]["examCaption"]["text"],
                         "División de España tras el fallido golpe de Estado de 17-19 julio de 1936")
        self.assertTrue(any(appearance["id"] == "fuente-pdf-2004-3-4" for appearance in record["appearances"]))

    def test_2014_juan_carlos_caption_uses_correct_capitalization(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"]
                      if d["id"] == "presidentes-monarquia-juan-carlos-2014")
        self.assertEqual(
            record["examCaption"]["text"],
            "Cuatro de los seis presidentes del Gobierno en la monarquía de Juan Carlos I",
        )

    def test_2003_cortes_caption_uses_correct_treatment_and_institution_case(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"]
                      if any(a["id"] == "fuente-pdf-2003-4-4" for a in d["appearances"]))
        self.assertEqual(
            record["examCaption"]["text"],
            "Apertura por su majestad Juan Carlos I de las Cortes legislativas. Mayo de 1979",
        )

    def test_pdf_import_preserves_the_original_corpus_and_counts_only_available_materials(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        original = []
        imported = []
        for record in data["documents"]:
            previous = [a for a in record["appearances"] if a["year"] >= 2008
                        and a.get("sourceReviewStatus") != "orientation-model"]
            if previous:
                original.append({key: previous if key == "appearances" else value
                                 for key, value in record.items() if key not in ("primaryTextId", "memberIds")
                                 and not (record["id"] == "casas-viejas-detenciones-1933"
                                          and key in ("image", "quality", "sourceCaption"))
                                 and not (record["id"] in ("mural-constitucion-1812-cadiz", "prim-busca-regimen-caricatura",
                                                          "directorio-civil-alfonso-xiii-1925", "reparto-armas-madrid-1936",
                                                          "miembros-cortes-cadiz", "mapa-desamortizacion-madoz",
                                                          "composicion-congreso-elecciones-febrero-1936",
                                                          "composicion-congreso-elecciones-1977")
                                          and key in ("image", "quality"))
                                 and not (record["id"] in ("constitucion-1812-articulos-2008",
                                                          "el-fuero-de-los-espanoles-y-los-limites-de-los-derechos",
                                                          "manifiesto-de-sandhurst-llamamiento-a-la-restauracion",
                                                          "constitucion-1978-articulos-suplente-a")
                                          and key == "studyCompilation")
                                 and not (record["id"] == "elecciones-cortes-1931"
                                          and key in ("date", "image", "quality", "table", "examCaption"))
                                 and not (record["id"] == "resultados-de-las-elecciones-generales-de-1982"
                                          and key in ("quality", "tableImage"))})
            imported.extend(a for a in record["appearances"] if a["year"] <= 2007)
        digest = hashlib.sha256(json.dumps(
            original, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(len(original), 178)
        self.assertEqual(digest, "ecc1ebb3f230949be089602824bd75d6d96ae8be2f323633a87fdf604940433f")
        self.assertEqual(len(imported), 135)
        self.assertEqual(len({a["pdfUrl"] for a in imported}), 36)
        self.assertEqual(data["coverage"]["sourceHeadingCount"], 101)
        self.assertEqual(data["coverage"]["sourceDocumentOccurrences"], 419)
        pending = data["coverage"]["pdfImport"]["pendingMaterials"]
        keys = {a["sourceKey"] for a in imported}
        self.assertEqual(len(pending), 9)
        self.assertFalse(keys.intersection(a["key"] for a in pending))
        for year in range(2002, 2008):
            selected = [a for a in imported if a["year"] == year]
            self.assertEqual(len(selected), 15 if year == 2006 else 24)
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
            if not copied or record["type"] != "texto":
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
                if group[0] == "manifiesto-persas-1814":
                    self.assertEqual(primary["id"], "manifiesto-persas-1814-pdf-2006-5-1")
                    self.assertIn("no original", primary["readingNote"])
                else:
                    self.assertTrue(all(a["year"] != 2006 for a in primary["appearances"]))
        songs = records["canciones-guerra-civil"]["text"]
        self.assertIn("¿Para qué tantos humos", songs[0])
        self.assertNotIn("Cuando se enteró", songs[0])
        self.assertIn("Canción republicana", songs[0])
        self.assertIn("Cuando se enteró", songs[1])
        self.assertIn("Canción falangista", songs[1])
        cavalry = records["huelga-1917-caballeria"]
        self.assertNotEqual(cavalry["image"]["src"], records["huelga-general-1917-fotografia"]["image"]["src"])

    def test_2006_divisas_table_appearance_is_counted_without_claiming_an_original_copy(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "divisas-emigrantes-1961-1975")
        appearance = next(a for a in record["appearances"] if a["year"] == 2006)
        self.assertEqual((appearance["exam"], appearance["route"], appearance["document"]),
                         ("2006 Examen 6", "Bloque II · Opción B", None))
        self.assertEqual(appearance["sourceReviewStatus"], "transcription-copy")
        self.assertEqual(len(record["appearances"]), 2)
        self.assertEqual(record["image"]["src"],
                         "assets/documentos/tabla-divisas-emigrantes-1961-1975.svg")
        self.assertTrue((ROOT / record["image"]["originalSrc"]).is_file())
        self.assertEqual(record["table"]["rows"][-1], ["1975", "599"])

    def test_document_omissions_use_square_brackets_and_three_dots(self):
        data = (ROOT / "data/documentos.json").read_text()
        self.assertIn("[...]", data)
        self.assertNotRegex(data, r"\(\s*(?:\.{3}|\u2026)\s*\)|\[\s*\u2026\s*\]")

    def test_junta_democratica_2002_principles_have_separate_paragraphs(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "junta-democratica-1974")
        self.assertEqual(record["text"][0], "“La Junta Democrática propugna:")
        self.assertEqual([paragraph.split(".", 1)[0] for paragraph in record["text"][1:-1]],
                         ["1", "2", "3", "4", "5", "6", "7", "9", "10"])
        self.assertEqual(record["attributionParagraphs"], 1)
        self.assertEqual(record["text"][-1], "Resoluciones de la Junta Democrática. (Julio de 1974).")
        self.assertEqual(hashlib.sha256(" ".join(record["text"]).encode()).hexdigest(),
                         "f3f239b273f8de308d063119ff3ea8398583a23cece8e37f66dc58e1af93c174")

    def test_war_songs_preserve_pdf_verses_and_words_in_separate_columns(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "canciones-guerra-civil")
        self.assertEqual(record["textLayout"], "verse-pair")
        self.assertEqual(len(record["text"]), 2)
        for song, label in zip(record["text"], ("Canción republicana", "Canción falangista.")):
            self.assertEqual(len(song.splitlines()), 17)
            self.assertTrue(song.endswith("\n\n" + label))
        self.assertTrue(record["text"][0].startswith("¿Para qué tantos humos,\ntantos faroles,"))
        self.assertTrue(record["text"][1].startswith("Cuando se enteró mi madre\nde que yo era de las JONS"))
        self.assertEqual(hashlib.sha256(" ".join(" ".join(record["text"]).split()).encode()).hexdigest(),
                         "31ad7ebf9c1f7a714878d319736aa2dbb6accf8f8f5192bb7b2bdd0e2300ba78")

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
            "la-jefatura-del-estado-en-la-ley-organica-de-1967": "1efcb01a4b887b2b2a0d17dfbc0950d3bfe94c6f68e85cd31f41252b90abb640",
            "investidura-de-jose-maria-aznar": "54bdcfd555029f9268470862069bec50259330dd4fb41fff19547296a493ac88",
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
            "decreto-unificacion-1937",
            "decreto-de-desamortizacion-de-mendizabal",
            "decreto-de-venta-de-bienes-eclesiasticos-de-mendizabal",
            "manifiesto-manzanares-1854",
        ):
            self.assertNotIn("attributionParagraphs", records[identifier])
        napoleon = records["napoleon-espanoles-bayona-1808"]
        self.assertEqual(napoleon["attributionParagraphs"], 1)
        self.assertEqual(napoleon["text"][-1],
                         "Dado en nuestro palacio imperial y real de Bayona a 25 de mayo de 1808.")

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

    def test_sandhurst_2025_recovers_the_exam_excerpt_under_the_full_reference_text(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        exam = records["manifiesto-de-sandhurst"]
        self.assertIn("Cuantos me han escrito", exam["text"][1])
        self.assertIn("las cosas de la España moderna", exam["text"][-1])
        self.assertTrue(exam["text"][-1].endswith("verdaderamente liberal”."))
        self.assertNotIn("Deseo que con todos", " ".join(exam["text"]))
        self.assertEqual([(a["exam"], a["route"], a["document"]) for a in exam["appearances"]],
                         [("2025 Titular extraordinaria", "Itinerario A", 2)])
        group = next(group for group in data["textGroups"] if exam["id"] in group)
        compilation = records[group[0]]["studyCompilation"]
        self.assertIn("las cosas de la Europa moderna", " ".join(compilation["text"]))
        self.assertEqual(sum(len(records[identity]["appearances"]) for identity in group), 5)

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
                if record["id"] != "apertura-cortes-1979":
                    self.assertTrue(annotations["sources"])
                for source in annotations.get("sources", []):
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

    def test_apertura_cortes_uses_the_three_user_supplied_identifications(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        image = records["apertura-cortes-1979"]["image"]
        self.assertEqual(image["src"], "assets/documentos/pdf-2003-4-4.png")
        annotations = image["annotations"]
        self.assertIn("indicados por el usuario", annotations["note"])
        self.assertNotIn("Las posiciones señaladas", annotations["context"])
        self.assertNotIn("sources", annotations)
        people = annotations["people"]
        self.assertEqual([person["name"] for person in people],
                         ["Juan Carlos I", "Sofía de Grecia", "Felipe de Borbón"])
        self.assertIn("actual Felipe VI", people[2]["role"])
        self.assertTrue(people[0]["x"] < people[1]["x"] < people[2]["x"])
        self.assertTrue(people[0]["y"] < people[1]["y"])
        note = people[0]["context"]
        self.assertIn("1969 sucesor en la jefatura del Estado a título de rey", note["text"])
        self.assertIn("abdicó en junio de 2014", note["text"])
        self.assertIn("agosto de 2020, seis años después", note["text"])
        self.assertIn("marzo de 2022", note["text"])
        self.assertIn("archivó las diligencias", note["text"])
        self.assertNotIn("exilio", note["text"])
        self.assertEqual(urlparse(note["url"]).netloc, "www.rtve.es")

    def test_republican_ministry_highlights_the_four_successive_presidents(self):
        records = {d["id"]: d for d in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        image = records["primer-gobierno-republica-1873"]["image"]
        annotations = image["annotations"]
        self.assertIn("ministros", annotations["context"])
        people = annotations["people"]
        self.assertEqual([person["name"] for person in people],
                         ["Estanislao Figueras", "Francisco Pi y Margall", "Nicolás Salmerón", "Emilio Castelar"])
        for person in people:
            self.assertTrue(person["context"]["text"])
            self.assertEqual(urlparse(person["context"]["url"]).scheme, "https")
        self.assertIn("no está acreditada", people[0]["context"]["text"])
        self.assertIn("cuestionan esa explicación", people[2]["context"]["text"])
        self.assertIn("3 de enero de 1874", people[3]["context"]["text"])
        self.assertIn("Francisco Serrano", people[3]["context"]["text"])
        self.assertIn("etapa parlamentaria", people[3]["context"]["text"])

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
        self.assertEqual(record["image"]["attribution"]["license"], "CC BY-SA 3.0")
        self.assertIn("Eldelcarro", record["image"]["attribution"]["text"])
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
                         "51bafe0aead39ac6865e217bae30b5c2126647eba525314f18128be598a2cc87")
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
        for identifier in ("acorazado-maine-1898", "no-pasaran-sitio-madrid"):
            self.assertTrue(records[identifier]["image"]["filter"])
        cover = records["portada-constitucion-1812"]["image"]
        self.assertNotIn("filter", cover)
        self.assertEqual(hashlib.sha256((ROOT / cover["src"]).read_bytes()).hexdigest(),
                         "0f045a05232f1bd97edc1f2196a45e3714e0c22aa77c6954cc768dda1cfa7204")

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
            if "titleEmphasis" in record:
                sources.append((record["title"], record["titleEmphasis"]))
            if "attributionEmphasis" in record:
                self.assertTrue(record.get("attributionParagraphs"))
                sources.append((" ".join(record["text"][-record["attributionParagraphs"]:]),
                                record["attributionEmphasis"]))
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
        self.assertIsNone(root.find(f".//*[@id='path1259']"))
        self.assertFalse(any(node.get("stroke-dasharray") not in (None, "none")
                             for node in root.iter()))
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
                         "52e3ce539c6e7b5bd708245afa2cbbe222fd6ac427d66f85a380672ca9605462")
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
        self.assertEqual(len(paragraphs), 20)
        articles = [p for p in paragraphs if p.startswith("Art. ")]
        self.assertEqual([int(re.match(r"Art\. (\d+)\.", p)[1]) for p in articles],
                         [1, 2, 3, 4, 14, 15, 16, 17, 287, 371])
        self.assertEqual([paragraphs[i] for i in compilation["headingParagraphs"]], [
            "CONSTITUCIÓN POLÍTICA DE LA MONARQUÍA ESPAÑOLA",
            "TÍTULO I. DE LA NACIÓN ESPAÑOLA Y DE LOS ESPAÑOLES",
            "CAPÍTULO I", "De la Nación Española",
        ])
        self.assertTrue(compilation["centerHeadings"])
        self.assertEqual([(paragraphs[i - 1].split(".")[1].strip(),
                           paragraphs[i + 1].split(".")[1].strip())
                          for i, p in enumerate(paragraphs) if p == "[...]"],
                         [("4", "14"), ("17", "287"), ("287", "371")])
        introduction = records["constitucion-1812-articulos-2008-pdf-2003-1-1"]["text"]
        self.assertEqual(paragraphs[0], introduction[0].removeprefix(
            "CONSTITUCIÓN DE CÁDIZ DE 1812 ").replace("SEPTIMO", "SÉPTIMO"))
        self.assertEqual(paragraphs[2], introduction[1].removeprefix(
            "CONSTITUCIÓN POLÍTICA DE LA MONARQUÍA ESPAÑOLA "))
        selected = records["constitucion-1812-articulos-2008-2015-lxhnexopmiob-2"]["text"]
        tokens = lambda text: re.findall(r"\w+", text.casefold())
        self.assertEqual([tokens(p) for p in articles[:8]], [tokens(p) for p in selected[:8]])
        self.assertEqual(articles[8], record["text"][4])
        self.assertEqual(articles[9], record["text"][5].replace("tiene libertad", "tienen libertad"))
        group = next(group for group in data["textGroups"] if group[0] == record["id"])
        appearances = [a for identity in group for a in records[identity]["appearances"]]
        self.assertEqual(sorted(a["year"] for a in appearances),
                         [2003, 2004, 2006, 2007, 2008, 2010, 2012, 2012, 2015, 2016])
        model = records["constitucion-1812-articulos-1-4-modelo"]
        self.assertEqual({a["year"] for a in model["appearances"]}, {2010, 2012})
        self.assertEqual([p.split(". ")[1] for p in model["text"][1:]], ["1", "2", "3", "4"])
        self.assertNotIn("appearances", compilation)
        self.assertIn("No es el texto íntegro", compilation["readingNote"])
        self.assertIn("tiene libertad", record["text"][5])

    def test_1978_compilation_combines_introduction_and_requested_articles(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        record = records["constitucion-1978-articulos-suplente-a"]
        compilation = record["studyCompilation"]
        paragraphs = compilation["text"]
        self.assertEqual(compilation["title"], "Constitución de 1978")
        self.assertEqual(paragraphs[0], compilation["title"])
        self.assertEqual(paragraphs[1], record["text"][0])
        self.assertEqual([paragraphs[index] for index in compilation["headingParagraphs"]],
                         ["Constitución de 1978", "Artículo 1", "Artículo 2", "Artículo 3",
                          "Artículo 6", "Artículo 7"])
        self.assertEqual([re.match(r"\d\.\d", paragraph)[0] for paragraph in paragraphs
                          if re.match(r"\d\.\d", paragraph)], ["1.1", "1.2", "1.3", "3.1", "3.2", "3.3"])
        self.assertEqual([index for index, paragraph in enumerate(paragraphs) if paragraph == "[...]"],
                         [2, 13])
        selection_2005 = records[f"{record['id']}-pdf-2005-4-3"]["text"]
        self.assertEqual(paragraphs[10:13], [selection_2005[5].removeprefix("Art. "), *selection_2005[6:8]])
        selection_2004 = records[f"{record['id']}-pdf-2004-6-3"]["text"]
        self.assertEqual(paragraphs[15], selection_2004[3].removeprefix("Artículo 6. "))
        self.assertEqual(paragraphs[17], selection_2004[4].removeprefix("Artículo 7. "))
        self.assertIn("Derecho,", paragraphs[4])
        self.assertIn("pueblo español,", paragraphs[5])
        self.assertIn("de derechos,", selection_2004[0])
        self.assertFalse(selection_2004[0].startswith("Don Juan Carlos"))
        self.assertEqual(compilation["attributionParagraphs"], 1)
        self.assertNotIn("readingNote", compilation)
        self.assertNotIn("appearances", compilation)
        group = next(group for group in data["textGroups"] if group[0] == record["id"])
        self.assertEqual(sorted(a["year"] for identity in group for a in records[identity]["appearances"]),
                         [2004, 2005, 2025])

    def test_four_digit_numbers_use_no_thousands_point(self):
        grouped_four_digits = re.compile(r"(?<![0-9.])[1-9]\.[0-9]{3}(?![0-9.])")

        def strings(value, path):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from strings(child, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from strings(child, f"{path}[{index}]")
            elif isinstance(value, str):
                yield path, value

        for path in sorted((ROOT / "data").glob("*.json")):
            data = json.loads(path.read_text())
            for location, value in strings(data, str(path)):
                self.assertIsNone(grouped_four_digits.search(value), f"{location}: {value}")

        for path in sorted((ROOT / "assets/documentos").glob("*.svg")):
            root = ET.parse(path).getroot()
            for node in root.iter():
                if node.tag.rsplit("}", 1)[-1] in ("text", "title", "desc", "tspan"):
                    value = "".join(node.itertext())
                    self.assertIsNone(grouped_four_digits.search(value), f"{path}: {value}")
                for attribute in ("aria-label", "alt", "title"):
                    value = node.get(attribute, "")
                    self.assertIsNone(grouped_four_digits.search(value), f"{path}: {value}")

        records = {record["id"]: record for record in
                   json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        constitution = records["constitucion-1978-gobierno-97-98-101"]
        self.assertEqual(constitution["text"][0], "CONSTITUCIÓN ESPAÑOLA DE 1978")
        self.assertIn("Se normaliza la escritura del año", constitution["quality"])

    def test_suarez_context_is_added_to_2011_pactos_moncloa_image(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"]
                      if item["id"] == "firmantes-pactos-moncloa-1977")
        self.assertIn("primer presidente democrático tras la dictadura (1976–1981)",
                      record["commentary"][0]["text"])

    def test_tejero_annotation_identifies_the_failed_23f_coup(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"]
                      if item["id"] == "fotografia-tejero-golpe-23f-1981")
        role = record["image"]["annotations"]["people"][0]["role"]
        self.assertIn("lideró el fallido golpe de Estado", role)
        self.assertIn("23 de febrero de 1981 (23F)", role)

    def test_fuero_compilation_covers_corpus_articles_without_replacing_exam_variants(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        identity = "el-fuero-de-los-espanoles-y-los-limites-de-los-derechos"
        compilation = records[identity]["studyCompilation"]
        group = next(group for group in data["textGroups"] if group[0] == identity)
        examined = {
            int(number) for member in group for paragraph in records[member]["text"]
            for number in re.findall(r"\b(?:Art\.|Artículo)\s+(\d+)", paragraph)
        }
        selected = [int(p.split()[1].rstrip(".")) for p in compilation["text"] if p.startswith("Art. ")]
        self.assertEqual(selected, sorted(examined))
        self.assertIn("No se permitirán otras ceremonias", " ".join(compilation["text"]))
        exam = records[f"{identity}-pdf-2002-3-3"]
        self.assertEqual([a["exam"] for a in exam["appearances"]], ["2002 Examen 3"])
        self.assertIn("protección de la libertad religiosa", " ".join(exam["text"]))
        self.assertNotIn("appearances", compilation)

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

    def test_cortazar_prefers_complete_2003_selection_with_heading_and_book_emphasis(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        canonical = records["garcia-cortazar-transicion-democracia"]
        record = records[canonical["primaryTextId"]]
        self.assertEqual(record["id"], "garcia-cortazar-transicion-democracia-pdf-2003-4-3")
        self.assertEqual(record["headingParagraphs"], [0])
        self.assertTrue(record["centerHeadings"])
        self.assertEqual(record["text"][0].strip("“”"), "Cuando España dio ejemplo")
        self.assertTrue(record["text"][1].startswith("Algunos fueron"))
        for version in (canonical, record):
            self.assertEqual(version["attributionEmphasis"], ["Álbum de la Historia de España"])
        self.assertTrue(canonical["text"][0].startswith("[...] Franco"))

    def test_artwork_and_book_titles_have_partial_italics_without_italicizing_authors(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identity, title in (
            ("goya-carga-mamelucos", "La carga de los mamelucos"),
            ("goya-tres-de-mayo", "Los fusilamientos del 3 de mayo"),
            ("rendicion-bailen-casado-alisal", "La rendición de Bailén"),
            ("guernica-picasso", "Guernica"),
            ("clarin-regenta-turno", "La Regenta"),
            ("hemingway-guerra-civil", "Por quien doblan las campanas"),
        ):
            with self.subTest(document=identity):
                self.assertEqual(records[identity]["titleEmphasis"], [title])
        caption = records["goya-carga-mamelucos"]["examCaption"]
        self.assertEqual(caption["emphasis"], ["La carga de los Mamelucos"])
        self.assertTrue(caption["text"].startswith("Francisco de Goya (1814):"))
        self.assertNotIn("GOYA", caption["text"])
        for identity, title in (
            ("caricatura-turno-partidos", "L'Esquella de la Torratxa"),
            ("sagasta-embudo-electoral", "La Carcajada"),
            ("maximo-febrero-1976", "El País"),
        ):
            self.assertEqual(records[identity]["examCaption"]["emphasis"], [title])

    def test_azana_religious_speech_has_two_body_paragraphs_in_every_selection(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = [r for r in data["documents"] if r["id"].startswith("azana-espana-ha-dejado-de-ser-catolica")]
        self.assertTrue(records)
        for record in records:
            with self.subTest(document=record["id"]):
                starts = record.get("paragraphStarts", list(range(len(record["text"]))))
                body_end = len(record["text"]) - record["attributionParagraphs"]
                body_starts = [start for start in starts if start < body_end]
                self.assertEqual(len(body_starts), 2)
                self.assertTrue(record["text"][body_starts[1]].startswith("Yo no puedo admitir"))
                self.assertTrue(record["text"][-1].startswith("Discurso de"))

    def test_blanco_white_heading_italicizes_only_the_work_title(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        for identity in ("blanco-white-1808", "blanco-white-1808-pdf-2006-1-1"):
            record = records[identity]
            with self.subTest(document=identity):
                self.assertEqual(record["headingParagraphs"], [0])
                self.assertTrue(record["centerHeadings"])
                self.assertEqual(record["headingEmphasis"]["0"], ["Escritos"])
                self.assertIn("José María Blanco White", record["text"][0])
                self.assertIn("1808", record["text"][0])
                self.assertTrue(record["text"][1].startswith("“Los diferentes hechos"))

    def test_book_titles_in_multiple_attribution_paragraphs_are_emphasized(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/documentos.json").read_text())["documents"]}
        galdos = records["perez-galdos-sobre-las-elecciones-de-la-restauracion-pdf-2003-4-1"]
        self.assertEqual(galdos["attributionParagraphs"], 2)
        self.assertIn("antología de artículos", galdos["attributionEmphasis"])
        self.assertIn("Partidos y programas", galdos["attributionEmphasis"])
        for identity, title in (
            ("serrano-suner-estado", "Entre Hendaya y Gibraltar"),
            ("herr-estatuto-real", "Ensayo histórico de la España contemporánea"),
            ("clarin-regenta-turno", "La Regenta"),
            ("tunon-lara-republica-1931", "Tres claves de la Segunda República"),
            ("hemingway-guerra-civil", "Por quien doblan las campanas"),
        ):
            with self.subTest(document=identity):
                self.assertIn(title, records[identity]["attributionEmphasis"])

    def test_suarez_source_uses_the_corpus_bibliographic_format(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"]
                      if d["id"] == "suarez-ley-reforma-politica-1976")
        self.assertEqual(record["text"][-1],
                         "Prego, V.: Así se hizo la transición. Barcelona, Plaza & Janés, 1995.")
        self.assertEqual(record["attributionEmphasis"], ["Así se hizo la transición"])

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

        election_table = documents["resultados-de-las-elecciones-generales-de-1982"]["tableImage"]
        styled = ET.parse(ROOT / election_table["src"]).getroot()
        stripes = styled.findall(".//{http://www.w3.org/2000/svg}rect[@class='row-stripe']")
        self.assertEqual([stripe.get("data-stripe-row") for stripe in stripes],
                         ["0", "2", "4", "6", "8", "10", "12", "14"])
        self.assertTrue(all(
            stripe.get("fill") == "#dce8e2" and stripe.get("x") == "0"
            and stripe.get("width") == "436" for stripe in stripes
        ))
        self.assertNotIn('id="election-table-row-stripes"',
                         (ROOT / documents["resultados-de-las-elecciones-generales-de-1982"]
                          ["tableImage"]["originalSrc"]).read_text())

        official = documents["elecciones-generales-1982-congreso-senado"]
        self.assertIn("-vector.svg", official["image"]["src"])
        self.assertIn("Redibujado vectorial", official["quality"])
        self.assertTrue((ROOT / official["image"]["originalSrc"]).is_file())
        self.assertIn("PDF oficial", official["quality"])
        self.assertEqual((official["image"]["width"], official["image"]["height"]), (2084, 1460))

        desamortizaciones = documents["grafico-desamortizaciones-siglo-xix"]
        self.assertIn("PDF oficial de 2008", desamortizaciones["sourceCaption"])
        self.assertIn("Extracción vectorial", desamortizaciones["quality"])
        self.assertEqual((desamortizaciones["image"]["width"], desamortizaciones["image"]["height"]), (1492, 1088))
        self.assertEqual(desamortizaciones["appearances"][0]["route"], "Opción A")

    def test_affiliation_map_uses_vector_cartography_and_keeps_original(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "afiliacion-obrera-1917")
        image = record["image"]
        self.assertEqual(image["src"], "assets/documentos/mapa-afiliacion-obrera-1917-vector.svg")
        self.assertEqual(
            image["examCaption"]["text"],
            "Distribución de la afiliación obrera en España en 1917.\n"
            "Fuente: Artola, M. (dir.): Enciclopedia de Historia de España: vol. VI.",
        )
        self.assertEqual(image["examCaption"]["emphasis"], ["Enciclopedia de Historia de España: vol. VI"])
        self.assertNotIn("reproductionNote", image)
        self.assertIn(f'"./{image["src"]}"', (ROOT / "sw.js").read_text())
        self.assertTrue(image["selectable"])
        self.assertTrue((ROOT / image["originalSrc"]).is_file())
        self.assertEqual(image["attribution"]["license"], "CC BY-SA 3.0")
        self.assertEqual(image["attribution"]["licenseUrl"], "https://creativecommons.org/licenses/by-sa/3.0/")
        self.assertIn("Miguillen", image["attribution"]["text"])
        self.assertIn("cifras absolutas", record["quality"])
        root = ET.parse(ROOT / image["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertIsNotNone(root.find(f"{namespace}title"))
        metadata = root.find(f"{namespace}metadata")
        self.assertIsNotNone(metadata)
        self.assertIn("https://creativecommons.org/licenses/by-sa/3.0/", metadata.text)
        self.assertEqual(len(root.findall(f".//{namespace}g[@id='province-labels']/{namespace}text")), 49)
        self.assertEqual(len(root.findall(f".//{namespace}g[@id='affiliation-outlines']/{namespace}circle")), 43)
        self.assertEqual(len(root.findall(f".//{namespace}g[@id='overlapping-locations']/{namespace}circle")), 5)
        canary_inset = root.find(f".//{namespace}g[@id='canary-inset']")
        self.assertIsNotNone(canary_inset)
        self.assertIsNone(canary_inset.find(f".//*[@id='path3796-canary']"))
        source_map = ET.parse(ROOT / "assets/documentos/espana-loc.svg").getroot()
        self.assertIsNotNone(source_map.find(f".//*[@id='path3796']"))
        legend = root.find(f".//{namespace}g[@id='map-legend']")
        self.assertEqual(len(legend.findall(f"{namespace}circle")), 1)
        self.assertEqual(len(legend.findall(f"{namespace}path")), 1)
        self.assertEqual(len(legend.findall(f"{namespace}line")), 2)
        self.assertEqual(len(legend.findall(f"{namespace}rect")), 0)
        self.assertEqual([node.text for node in legend.findall(f"{namespace}text")],
                         ["afiliados", "a la UGT", "afiliados", "a la CNT"])
        self.assertEqual(
            {node.get("font-size") for node in legend.findall(f"{namespace}text")},
            {"16"},
        )
        self.assertEqual(
            legend.get("aria-label"),
            "afiliados a la UGT en naranja; afiliados a la CNT en azul",
        )
        legend_circle = legend.find(f"{namespace}circle")
        self.assertEqual((legend_circle.get("cx"), legend_circle.get("cy")), ("167", "364"))
        self.assertEqual(legend_circle.get("fill"), "#4e679d")
        legend_left_sector = legend.find(f"{namespace}path")
        self.assertEqual(legend_left_sector.get("fill"), "#e87925")
        legend_lines = legend.findall(f"{namespace}line")
        self.assertEqual([node.get("stroke") for node in legend_lines], ["#e87925", "#4e679d"])
        city_real = next(node for node in root.findall(f".//{namespace}g[@id='province-labels']/{namespace}text")
                         if node.text == "Ciudad Real")
        self.assertEqual(legend_circle.get("cy"), "364")
        canary_chart = next(
            node for node in root.findall(f".//{namespace}g[@id='affiliation-sectors']/{namespace}circle")
            if node.get("cx") == "167" and node.get("cy") == "524"
        )
        self.assertEqual(legend_circle.get("cx"), canary_chart.get("cx"))
        city_labels = root.findall(f".//{namespace}g[@id='province-labels']/{namespace}text")
        self.assertTrue(all(
            float(label.get("font-size")) >= 14
            for label in city_labels if label.text != "Toledo"
        ))
        labels_by_name = {label.text: label for label in city_labels}
        self.assertEqual(
            (labels_by_name["Ourense"].get("x"), labels_by_name["Ourense"].get("y"),
             labels_by_name["Ourense"].get("text-anchor")),
            ("500", "155", "start"),
        )
        self.assertEqual(
            (labels_by_name["Zamora"].get("x"), labels_by_name["Zamora"].get("y"),
             labels_by_name["Zamora"].get("text-anchor")),
            ("548", "180", "middle"),
        )
        expected_label_positions = {
            "Oviedo": ("540", "25", "end"),
            "Santander": ("650", "16", "middle"),
            "Vizcaya": ("718", "16", "middle"),
            "Guipúzcoa": ("756", "28", "start"),
            "León": ("569", "90", "middle"),
            "Palencia": ("628", "112", "middle"),
            "Burgos": ("686", "108", "middle"),
            "Navarra": ("805", "107", "start"),
            "Soria": ("730", "190", "end"),
            "Logroño": ("735", "162", "end"),
            "Lérida": ("938", "52", "middle"),
            "Gerona": ("1126", "36", "end"),
            "Valladolid": ("619", "175", "middle"),
            "Segovia": ("673", "209", "middle"),
            "Salamanca": ("554", "270", "middle"),
            "Ávila": ("628", "290", "middle"),
            "Madrid": ("703", "282", "middle"),
            "Cuenca": ("790", "320", "start"),
            "Toledo": ("671", "309", "middle"),
            "Ciudad Real": ("692", "353", "middle"),
            "Albacete": ("737", "359", "middle"),
            "Murcia": ("810", "490", "start"),
            "Cádiz": ("500", "560", "end"),
            "Málaga": ("610", "590", "middle"),
            "Granada": ("689", "545", "middle"),
            "Almería": ("760", "530", "middle"),
            "Baleares": ("1048", "356", "middle"),
            "Córdoba": ("623", "404", "middle"),
            "Jaén": ("725", "405", "start"),
        }
        for name, position in expected_label_positions.items():
            label = labels_by_name[name]
            self.assertEqual(
                (label.get("x"), label.get("y"), label.get("text-anchor")),
                position,
            )
        toledo_label = labels_by_name["Toledo"]
        self.assertEqual(toledo_label.get("font-size"), "12")
        self.assertEqual(toledo_label.get("textLength"), "34")
        self.assertEqual(toledo_label.get("lengthAdjust"), "spacingAndGlyphs")
        provincial_map = root.find(f".//{namespace}g[@id='provincial-map']")
        province_styles = [element.get("style", "") for element in provincial_map.iter()]
        self.assertTrue(any(
            "stroke-width:0.2" in style and "stroke-dasharray:4,3" in style
            for style in province_styles
        ))
        self.assertTrue(any(
            "stroke-width:2" in style and "stroke-dasharray:none" in style
            for style in province_styles
        ))
        sectors = root.find(f".//{namespace}g[@id='affiliation-sectors']")
        self.assertEqual(len(sectors.findall(f"{namespace}circle")), 43)
        vizcaya_circle = next(
            circle for circle in sectors.findall(f"{namespace}circle")
            if circle.get("cx") == "718" and circle.get("cy") == "52"
        )
        self.assertEqual(vizcaya_circle.get("r"), "26")
        self.assertGreater(len(sectors.findall(f"{namespace}path")), 20)
        self.assertFalse(root.findall(f".//{namespace}g[@id='affiliation-sectors']/{namespace}polygon"))
        self.assertFalse(root.findall(f".//{namespace}image"))
        sector_paths = sectors.findall(f"{namespace}path")
        for cx, cy, radius, start, span in (
            (1024, 153, 89, 112, 338),
            (869, 286, 13, 280, 340),
            (789, 107, 10, 260, 20),
            (555, 316, 24, 260, 20),
        ):
            expected_path = map_tools.pie_wedge_path(cx, cy, radius, start, span)
            self.assertIn(expected_path, [path.get("d") for path in sector_paths])
        soria_chart = next(
            chart for chart in sectors.findall(f"{namespace}circle")
            if chart.get("cx") == "743" and chart.get("cy") == "185"
        )
        self.assertEqual(soria_chart.get("r"), "10")
        zamora_marker = root.find(
            f".//{namespace}g[@id='province-markers']/{namespace}circle"
        )
        self.assertEqual(
            (zamora_marker.get("data-province"), zamora_marker.get("cx"),
             zamora_marker.get("cy"), zamora_marker.get("r")),
            ("Zamora", "548", "198", "10"),
        )
        self.assertEqual(zamora_marker.get("r"), soria_chart.get("r"))
        lleida_chart = next(
            chart for chart in sectors.findall(f"{namespace}circle")
            if chart.get("data-province") == "Lérida"
        )
        self.assertEqual((lleida_chart.get("cx"), lleida_chart.get("cy")), ("938", "74"))
        rotated_tarragona = map_tools.correct_chart_sectors(
            [(923, 230, 15, 20, 250)]
        )
        self.assertEqual(rotated_tarragona, [(923, 230, 15, 200, 250)])
        overlapping_pies = root.find(f".//{namespace}g[@id='overlapping-location-sectors']")
        gerona_pie = overlapping_pies.find(f"{namespace}circle")
        self.assertEqual(
            (gerona_pie.get("cx"), gerona_pie.get("cy"), gerona_pie.get("r"),
             gerona_pie.get("fill"), gerona_pie.get("data-province")),
            ("1104", "54", "9", "#e87925", "Gerona"),
        )
        self.assertEqual(
            overlapping_pies.find(f"{namespace}path").get("d"),
            map_tools.pie_wedge_path(1104, 54, 9, 305, 340),
        )
        script = root.find(f"{namespace}script")
        self.assertIn("provinceReferenceOverrides", script.text)
        self.assertIn('["Cádiz", [530, 545]]', script.text)
        self.assertIn('["Málaga", [610, 545]]', script.text)
        self.assertIn('["Navarra", [790, 110]]', script.text)
        self.assertIn('["Logroño", [740, 150]]', script.text)
        self.assertIn('["Cuenca", [785, 310]]', script.text)
        self.assertIn('["Albacete", [775, 375]]', script.text)
        self.assertIn('["Huesca", [850, 115]]', script.text)
        self.assertIn('["Zaragoza", [870, 165]]', script.text)
        self.assertIn('["Teruel", [830, 260]]', script.text)
        self.assertIn('["Tarragona", [930, 215]]', script.text)
        self.assertIn("event.clientX", script.text)
        self.assertIn("root.getScreenCTM().inverse()", script.text)
        self.assertIn("nearestProvince(point.x, point.y)", script.text)
        self.assertIn("smallestChartAt(point.x, point.y)", script.text)
        self.assertIn("pointer-events:all", root.find(f"{namespace}style").text)
        self.assertNotIn("select(area.dataset.province)", script.text)
        self.assertIn('area.closest("#canary-inset")', script.text)
        self.assertIn('new Set(["path263-main"])', script.text)
        self.assertIn('mark(path, "Canarias", "province-area", true)', script.text)
        self.assertIn("Escape", script.text)
        self.assertTrue(all(label.get("data-province") for label in city_labels))

    def test_labor_conflicts_table_matches_the_exam_layout(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(
            item for item in data["documents"]
            if item["id"] == "conflictos-laborales-1963-1972"
        )
        image = record["image"]
        self.assertEqual((image["width"], image["height"]), (882, 227))
        root = ET.parse(ROOT / image["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertEqual((int(root.get("width")), int(root.get("height"))), (882, 227))
        self.assertIn("PAUCondensed", root.find(f"{namespace}style").text)
        self.assertEqual(
            root.find(f"{namespace}rect").get("fill"),
            "#fff",
        )
        border = root.find(f".//{namespace}g/{namespace}rect")
        self.assertEqual(
            (border.get("x"), border.get("y"), border.get("width")),
            ("8", "8", "866"),
        )
        self.assertTrue(math.isclose(float(border.get("height")), 188, abs_tol=0.01))
        title = root.find(f".//{namespace}text[@class='title']")
        self.assertEqual((title.get("x"), title.get("y")), ("441", "27"))
        rules = [path.get("d") for path in root.findall(f".//{namespace}g/{namespace}path")]
        self.assertIn("M8 32h866", rules)
        self.assertIn("M214 32v163.999998", rules)
        note = root.find(f".//{namespace}text[@class='note']")
        self.assertEqual(
            note.find(f"{namespace}tspan").text,
            "Estructura de clases en la España actual",
        )
        self.assertEqual(
            record["table"]["rows"][0],
            ["Político-Sociales", "16", "8", "9", "10", "10", "54", "132", "687", "115", "66"],
        )

    def test_graph_document_category_uses_the_current_label(self):
        source = (ROOT / "documentos.js").read_text()
        self.assertIn('grafico: "Mapas y gráficos"', source)
        self.assertNotIn("Mapa, gráfico o tabla", source)

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
                  if d.get("table") and d.get("image", {}).get("kind") == "table"
                  and all(a.get("sourceType") == "pdf" for a in d["appearances"])}
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

    def test_2002_iron_production_table_matches_the_exam_layout(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "produccion-hierro-1860-1869")
        namespace = "{http://www.w3.org/2000/svg}"
        root = ET.parse(ROOT / document["image"]["src"]).getroot()
        self.assertEqual((root.get("width"), root.get("height")), ("768", "255"))
        title = root.findall(f"{namespace}text[@class='title']")
        self.assertEqual([node.text for node in title], [
            "Producción de hierro colado",
            "(media anual en miles de toneladas)",
        ])
        self.assertTrue(all(node.get("x") == "384" and node.get("text-anchor") == "middle"
                            for node in title))
        grid = root.find(f"{namespace}g[@fill='none']")
        border = grid.find(f"{namespace}rect")
        self.assertEqual(
            (border.get("x"), border.get("y"), border.get("width"), border.get("height")),
            ("8", "51", "752", "144"),
        )
        self.assertEqual(grid.get("stroke"), "#555")
        self.assertEqual(
            [node.get("d") for node in grid.findall(f"{namespace}path")],
            ["M196 51v144", "M370 51v144", "M540 51v144",
             "M8 99h752", "M8 147h752"],
        )
        note = root.find(f"{namespace}text[@class='note']")
        self.assertEqual(
            (note.get("x"), note.get("y"), note.get("text-anchor")),
            ("384", "238", "middle"),
        )
        emphasis = note.find(f"{namespace}tspan")
        self.assertEqual(emphasis.text, "El fracaso de la Revolución Industrial en España, 1814-1913")
        self.assertEqual(emphasis.get("font-style"), "italic")
        for row_index, row in enumerate(document["table"]["rows"]):
            for column_index, value in enumerate(row):
                cell = root.find(f".//*[@data-row='{row_index}'][@data-column='{column_index}']")
                self.assertIsNotNone(cell)
                self.assertEqual(" ".join(" ".join(cell.itertext()).split()), value)

    def test_2002_social_composition_chart_is_vectorized_with_editorial_colors(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "sociedad-espanola-1860")
        image = document["image"]
        namespace = "{http://www.w3.org/2000/svg}"
        root = ET.parse(ROOT / image["src"]).getroot()
        self.assertEqual((image["kind"], image["width"], image["height"]),
                         ("chart", 593, 419))
        self.assertEqual((root.get("width"), root.get("height")), ("593", "419"))
        title = root.find(f"{namespace}text[@class='title']")
        self.assertIsNone(title)
        self.assertEqual(document["examCaption"]["text"], "Composición de la sociedad española hacia 1860")
        reference = ET.parse(ROOT / "assets/documentos/tabla-congreso-1936.svg").getroot()
        self.assertIn("font-family:Arial,sans-serif;fill:#382f3e",
                      reference.find(f"{namespace}style").text)
        sectors = root.findall(f"{namespace}path[@class='sector']")
        self.assertEqual(
            [(node.get("data-category"), node.get("data-percentage")) for node in sectors],
            [("Nobleza y clero", "16"), ("Burguesía alta", "3"),
             ("Clases medias", "10"), ("Clases bajas", "71")],
        )
        self.assertEqual(len({node.get("fill") for node in sectors}), 4)
        self.assertEqual(
            document["table"]["rows"],
            [["Nobleza y clero", "16"], ["Burguesía alta", "3"],
             ["Clases medias", "10"], ["Clases bajas", "71"]],
        )
        self.assertNotIn("reproductionNote", image)

    def test_montecristi_footers_spell_out_the_date(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = [r for r in data["documents"] if r["title"] == "Manifiesto de Montecristi"]
        self.assertEqual(len(records), 4)
        for record in records:
            with self.subTest(document=record["id"]):
                body = " ".join(record["text"][:-record["attributionParagraphs"]])
                footer = " ".join(record["text"][-record["attributionParagraphs"]:])
                self.assertIn("Montecristi, Santo Domingo, 25 de marzo de 1895", footer)
                self.assertIn("Firmado por José Martí y Máximo Gómez", footer)
                self.assertNotIn("Montecristi, Santo Domingo", body)

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
        self.assertEqual(persas["text"][0], "“SEÑOR")
        self.assertEqual(persas["headingParagraphs"], [0])
        self.assertFalse(persas["centerHeadings"])
        self.assertEqual(persas["attributionEmphasis"], ["Manifiesto de los Persas"])
        self.assertTrue(persas["appearances"][0]["textReviewedByUser"])
        self.assertIn("confirmado como correcto por el usuario", persas["readingNote"])
        self.assertNotIn("pendiente", persas["readingNote"])
        self.assertEqual([paragraph.split(".", 1)[0] for paragraph in persas["text"][1:-1]],
                         ["1", "7", "8", "134", "143"])

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

    def test_mapa_guerra_independencia_reproduction_preserves_exam_source(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(d for d in data["documents"] if d["id"] == "mapa-guerra-independencia-1808-1814")
        image = record["image"]
        self.assertEqual(image_dimensions(ROOT / image["src"]), (910, 762))
        self.assertEqual((image["width"], image["height"]), (910, 762))
        self.assertEqual(image["src"], "assets/documentos/pdf-2003-1-2.png")
        self.assertEqual(image["sourceUrl"],
                         "https://drive.google.com/file/d/1XDODoBqLulonuiXw0Z598p2YYRrF1DRd/view")
        self.assertEqual(record["examCaption"]["text"],
                         "España durante la guerra de la Independencia (1808-1814)")
        self.assertEqual(len(record["appearances"]), 1)
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2003-1-2")
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

    def test_maximo_caption_marks_el_pais_and_explains_the_date_anachronism(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "maximo-febrero-1976")
        caption = record["examCaption"]
        self.assertEqual(caption["text"], "Chiste de Máximo aparecido en El País*, febrero de 1976")
        self.assertEqual(caption["emphasis"], ["El País"])
        self.assertEqual(
            caption["note"],
            "* El periódico El País no existía aún en febrero de 1976: su primer número se publicó el 4 de mayo de ese año. "
            "Durante ese mes sí circulaban otros periódicos de tirada nacional, como ABC y La Vanguardia.",
        )
        self.assertEqual(caption["noteEmphasis"], ["El País", "ABC", "La Vanguardia"])
        self.assertEqual(record["appearances"][0]["id"], "fuente-pdf-2005-4-4")

    def test_pib_chart_tooltips_show_original_values_and_2026_equivalents(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "pib-habitante-1931-1973")
        self.assertNotIn("1939–1973*", record["title"])
        self.assertIn("1939*–1973", record["image"]["alt"])
        self.assertIn("pesetas constantes de 1980", record["quality"])
        self.assertIn("equivalentes en euros y pesetas de 2026", record["image"]["alt"])
        self.assertTrue(record["image"]["selectable"])
        self.assertEqual(record["image"]["examCaption"], {
            "text": "Fuente: Prados de la Escosura, Spain's Gross Domestic Product (1995)",
            "emphasis": ["Spain's Gross Domestic Product"],
        })
        svg = ET.parse(ROOT / record["image"]["src"]).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(
            [label.text for label in svg.findall(".//svg:text[@class='year-label']", namespace)],
            ["1939*"] + [str(year) for year in range(1941, 1974, 2)],
        )
        points = svg.findall(".//svg:g[@class='point']", namespace)
        self.assertEqual(len(points), 35)
        first = points[0]
        self.assertEqual(
            (first.get("data-year"), first.get("data-original-pesetas-1980"),
             first.get("data-euros-2026"), first.get("data-pesetas-2026")),
            ("1939", "90000", "3509", "583800"),
        )
        self.assertEqual(
            [node.text for node in first.findall(".//svg:g[@class='tooltip']/svg:text", namespace)],
            ["1939*", "Serie original: 90.000 ptas.",
             "Euros de 2026: 3509 €", "Pesetas de 2026: 583.800"],
        )
        tooltip_text = "".join(first.find(".//svg:g[@class='tooltip']", namespace).itertext())
        self.assertNotIn("base 1980", tooltip_text)
        year_1940 = next(point for point in points if point.get("data-year") == "1940")
        self.assertIn("96.200", year_1940.get("aria-label"))
        self.assertIn("3750 euros de 2026", year_1940.get("aria-label"))
        year_1970 = next(point for point in points if point.get("data-year") == "1970")
        self.assertEqual(year_1970.get("data-original-pesetas-1980"), "291200")
        self.assertIn("13.449 euros de 2026", points[-1].get("aria-label"))
        self.assertIn("pointerdown", svg.find("svg:script", namespace).text)
        self.assertIn("pointerup", svg.find("svg:script", namespace).text)
        self.assertIn("1931", "".join(svg.itertext()))
        self.assertIn("1939", "".join(svg.itertext()))
        self.assertIn("*Errata: el examen original indica en el título 1931, pero los datos comienzan en 1939",
                      "".join(svg.itertext()))
        self.assertNotIn("Prados de la Escosura", "".join(svg.itertext()))

    def test_divisas_table_matches_exam_layout_and_italicizes_book_title(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "divisas-emigrantes-1961-1975")
        self.assertEqual((record["image"]["width"], record["image"]["height"]), (480, 492))
        self.assertIn("sombreado verde editorial", record["image"]["reproductionNote"])
        self.assertEqual(record["image"]["originalSrc"], "assets/documentos/pdf-2003-6-4.png")
        self.assertEqual(len(record["table"]["rows"]), 15)
        svg = ET.parse(ROOT / record["image"]["src"]).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        stripes = svg.findall(".//svg:rect[@class='row-stripe']", namespace)
        self.assertEqual(len(stripes), 30)
        self.assertEqual([stripe.get("fill") for stripe in stripes[:4]],
                         ["#f5f7f5", "#dce8e2", "#fff", "#e7f0ec"])
        self.assertEqual([(stripe.get("data-stripe-row"), stripe.get("data-stripe-column"))
                          for stripe in stripes[:2]], [("0", "0"), ("0", "1")])
        title_line = svg.find(".//svg:text[@class='title']", namespace)
        self.assertIsNotNone(title_line)
        self.assertEqual((title_line.get("x"), title_line.get("text-anchor")), ("235", "middle"))
        title = svg.find(".//svg:tspan", namespace)
        self.assertIsNotNone(title)
        self.assertEqual(title.get("font-style"), "italic")
        self.assertEqual(title.text, "La emigración española")

    def test_2007_election_diagram_uses_exam_grouping_and_ministry_ucd_votes(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        record = next(item for item in data["documents"] if item["id"] == "elecciones-1977-diagrama")
        image = record["image"]
        self.assertEqual(image["width"], 760)
        self.assertNotIn("reproductionNote", image)
        self.assertEqual(len(record["table"]["rows"]), 7)
        svg = (ROOT / image["src"]).read_text()
        self.assertEqual(svg.count('<path class="sector"'), 7)
        self.assertIn('data-party="Otros*"', svg)
        svg_root = ET.fromstring(svg)
        self.assertEqual(image["height"], int(svg_root.get("height")))
        ucd_sector = svg_root.find(
            ".//{http://www.w3.org/2000/svg}path[@data-party='UCD']")
        self.assertEqual((ucd_sector.get("data-seats"), ucd_sector.get("data-seat-percent")),
                         ("166", "47.429"))
        self.assertEqual(ucd_sector.get("fill"), "#315a29")
        divider = svg_root.find(".//{http://www.w3.org/2000/svg}line[@class='majority-divider']")
        self.assertIsNotNone(divider)
        self.assertEqual(
            (divider.get("x1"), divider.get("y1"), divider.get("x2"), divider.get("y2")),
            ("230", "185", "230", "292"),
        )
        self.assertTrue(divider.get("stroke-dasharray"))
        center = [
            node.text for node in svg_root.iter("{http://www.w3.org/2000/svg}text")
            if node.get("class") in ("center-seat", "center-majority")
        ]
        self.assertEqual(center, ["350", "escaños", "176 para la mayoría"])
        self.assertEqual(
            svg_root.find("{http://www.w3.org/2000/svg}title").text,
            "Resultado elecciones 1977 (15 de junio)",
        )
        self.assertEqual(
            svg_root.find(".//{http://www.w3.org/2000/svg}text[@class='title']").text,
            "Resultado elecciones 1977 (15 de junio)",
        )
        self.assertIsNone(svg_root.find(".//{http://www.w3.org/2000/svg}text[@class='subtitle']"))
        visible_party_labels = " ".join(
            node.text or "" for node in svg_root.iter("{http://www.w3.org/2000/svg}text")
            if node.get("class") == "party"
        )
        for label in (
            "Unión de Centro Democrático (UCD)",
            "Partido Socialista Obrero Español (PSOE)",
            "Partit dels Socialistes de Catalunya (PSC-PSOE)",
            "Partido Comunista de España (PCE)",
            "Partit Socialista Unificat de Catalunya (PSUC)",
            "Alianza Popular (AP)",
            "Pacte Democràtic per Catalunya (PDC)",
            "Partido Nacionalista Vasco (PNV)",
        ):
            self.assertIn(label, visible_party_labels)
        self.assertIn("Otros*", visible_party_labels)
        footnotes = [
            node.text for node in svg_root.iter("{http://www.w3.org/2000/svg}text")
            if node.get("class") == "footnote"
        ]
        self.assertEqual(footnotes, [])
        description = svg_root.find("{http://www.w3.org/2000/svg}desc").text
        self.assertNotIn("Ministerio del Interior", description)
        self.assertNotIn("JEC", description)
        self.assertNotIn("Escaños (%) = escaños", svg)
        self.assertNotIn("Porcentajes de voto recalculados a una décima", svg)
        self.assertEqual(record["table"]["headers"][-2:], ["Escaños", "Escaños (%)"])
        self.assertEqual(record["table"]["rows"][0][1:], ["6 310 391", 166, "47,4"])
        self.assertEqual(record["table"]["caption"], "Resultado elecciones 1977 (15 de junio)")
        self.assertEqual(sum(row[2] for row in record["table"]["rows"]), 350)
        self.assertEqual(sum(int(row[1].replace(" ", "")) for row in record["table"]["rows"]),
                         16904704)
        self.assertIn("6 310 391 votos", svg)
        metadata = json.loads(svg_root.find("{http://www.w3.org/2000/svg}metadata").text)
        self.assertIn("infoelectoral.interior.gob.es", metadata["ministrySource"])
        notes = " ".join(record["table"]["notes"])
        self.assertIn("Ministerio del Interior", notes)
        self.assertIn("6 310 391", notes)
        self.assertIn("no es un grupo parlamentario", notes)
        self.assertIn("1 261 933 votos", svg)
        self.assertNotIn("Votos (%)", record["table"]["headers"])

    def test_1977_tables_use_the_declared_sources_and_exam_grouping(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        records = {record["id"]: record for record in data["documents"]}
        record = records["elecciones-1977-votos-escanos"]
        caption = "Resultado elecciones 1977 (15 de junio)"
        self.assertEqual(record["image"]["examCaption"]["text"], caption)
        self.assertNotIn("tipografía", record["quality"])
        svg = ET.parse(ROOT / record["image"]["src"]).getroot()
        self.assertEqual(
            svg.find("{http://www.w3.org/2000/svg}text[@class='title']").text,
            "Resultado elecciones 1977 (15 de junio)",
        )
        self.assertNotIn("Doc. 11", "".join(svg.itertext()))
        table = record["table"]
        self.assertEqual(table["caption"], caption)
        rows = {row[0]: row for row in table["rows"]}
        self.assertEqual(rows["UCD"], ["UCD", "6 310 391", "166", "47,4"])
        self.assertEqual(rows["PSOE + PSC"], ["PSOE + PSC", "5 338 107", "118", "33,7"])
        self.assertEqual(rows["PCE + PSUC"], ["PCE + PSUC", "1 711 906", "20", "5,7"])
        self.assertEqual(rows["Otros"], ["Otros", "445 179", "5", "1,4"])
        self.assertEqual(sum(int(row[2]) for row in table["rows"]), 350)
        self.assertEqual(sum(int(row[1].replace(" ", "")) for row in table["rows"]), 16904704)
        original_table = records["composicion-congreso-elecciones-1977"]["table"]
        self.assertEqual(sum(row[1] for row in original_table["rows"]), 350)
        table_record = records["composicion-congreso-elecciones-1977"]
        table_svg = ET.parse(ROOT / table_record["image"]["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        stripes = table_svg.findall(f".//{namespace}rect[@class='grid row-stripe']")
        self.assertEqual([stripe.get("data-stripe-row") for stripe in stripes],
                         ["0", "0", "2", "2", "4", "4", "6", "6", "8", "8", "10", "10"])
        self.assertIn(".grid.row-stripe{fill:#dce8e2}",
                      table_svg.find(f"{namespace}style").text)
        self.assertIn("Ministerio del Interior", " ".join(table["notes"]))
        for identity in ("elecciones-1977-votos-escanos", "elecciones-1977-diagrama",
                         "composicion-congreso-elecciones-1977"):
            self.assertIn("juntaelectoralcentral.es", records[identity]["dataSourceUrl"])

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
        manifest = [item for item in data["coverage"]["sourceManifest"]
                    if not item["key"].startswith("modelo-orientaciones-")]
        years = [item for item in manifest if item["year"] in (2010, 2011, 2012)]
        self.assertEqual(len(years), 72)
        self.assertEqual(len({item["heading"] for item in years}), 18)
        self.assertEqual(sum(len(item["images"]) for item in years), 20)
        self.assertEqual(len([item for item in manifest if item["year"] >= 2008]), 260)
        self.assertEqual(data["coverage"]["sourceImageOccurrences"], 171)
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
        self.assertEqual(len(appearances), 36)
        manifest = {entry["key"]: entry for entry in data["coverage"]["sourceManifest"]}
        for year, first_page in ((2010, 4), (2012, 3), (2013, 2), (2014, 2), (2015, 2), (2016, 2)):
            selected = [(r, a) for r, a in appearances if a["year"] == year]
            self.assertEqual(len(selected), 4)
            self.assertEqual({(a["route"], a["document"], a["officialPage"]) for _, a in selected}, {
                ("Opción A", 1, first_page), ("Opción A", 2, first_page),
                ("Opción B", 1, first_page + 1), ("Opción B", 2, first_page + 1),
            })
            self.assertEqual(len({a["pdfUrl"] for _, a in selected}), 1)
            for record, appearance in selected:
                self.assertEqual(appearance["sourceUrl"], appearance["pdfUrl"])
                self.assertEqual(manifest[appearance["sourceKey"]]["assignedTo"], record["id"])
                self.assertEqual(bool(appearance["sourceImages"]), record["type"] != "texto")
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
        root = ET.parse(ROOT / record["image"]["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        title = root.find(f"{namespace}text[@class='title']")
        self.assertIn("las elecciones a Cortes (junio de 1931)", title.text)
        self.assertEqual((title.get("x"), title.get("text-anchor")), ("450", "middle"))
        source = root.find(f"{namespace}text[@class='source']")
        self.assertEqual((source.get("x"), source.get("text-anchor")), ("450", "middle"))
        self.assertEqual(record["image"]["caption"], "Sin descripción.")
        self.assertNotIn("reproductionNote", record["image"])
        rendered = " ".join(root.itertext())
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
        namespace = "{http://www.w3.org/2000/svg}"
        stripes = root.findall(f".//{namespace}rect[@data-stripe-row]")
        self.assertEqual([stripe.get("data-stripe-row") for stripe in stripes],
                         ["0", "2", "4", "6", "8"])
        self.assertEqual([stripe.get("y") for stripe in stripes],
                         ["140", "236", "332", "428", "524"])
        cells = {
            (int(node.get("x")), int(node.get("y"))): node.text
            for node in root.iter(f"{namespace}text")
        }
        for index, row in enumerate(document["table"]["rows"]):
            y = 618 if index == 9 else 180 + 48 * index
            for x, value in zip((50, 490, 532, 960), row):
                with self.subTest(row=index, column=x):
                    if value != "":
                        self.assertEqual(cells[(x, y)], str(value))
                    else:
                        self.assertNotIn((x, y), cells)

    def test_1931_constituent_seats_chart_matches_the_original_typography(self):
        data = json.loads((ROOT / "data/documentos.json").read_text())
        document = next(item for item in data["documents"]
                        if item["id"] == "escanos-constituyentes-1931-porcentajes")
        image = document["image"]
        root = ET.parse(ROOT / image["src"]).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        title = root.find(f"{namespace}text[@class='title']")
        style = root.find(f"{namespace}style").text

        self.assertEqual(document["date"], "junio de 1931")
        self.assertEqual((image["width"], image["height"]), (882, 347))
        self.assertEqual(title.text, "Distribución de escaños en las constituyentes de junio de 1931")
        self.assertEqual((title.get("x"), title.get("text-anchor")), ("441", "middle"))
        self.assertIn("font-family:PAUCondensed", style)
        self.assertIn("font-weight:400", style)
        self.assertIsNone(root.find(f"{namespace}text[@class='note']"))
        self.assertNotIn("reproductionNote", image)
        self.assertNotIn("Redibujo", document["quality"])
        self.assertIn("cifras confirmadas por el usuario", document["quality"])

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
        root = ET.parse(ROOT / chart["image"]["src"]).getroot()
        leaders = root.find(".//*[@id='cadiz-chart-leaders']")
        self.assertIsNotNone(leaders)
        self.assertEqual(len(leaders), 13)
        self.assertEqual(leaders.get("stroke-dasharray"), "0.01 1.7")
        bars = [node for node in root.iter() if node.get("fill") in {
            "#d4bd87", "#8fb8c8", "#9aacc2", "#c6c2b9", "#ab9abb", "#d2a28f", "#a4b67f",
        }]
        self.assertEqual(len(bars), 26)
        self.assertEqual(len({node.get("fill") for node in bars}), 7)

    def test_1936_congress_table_uses_alternating_editorial_row_colors(self):
        root = ET.parse(ROOT / "assets/documentos/tabla-congreso-1936.svg").getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        style = root.find(f"{namespace}style").text
        self.assertIn(".grid:nth-of-type(4n+3),.grid:nth-of-type(4n+4){fill:#f2edf5}", style)
        self.assertIn(".grid:nth-of-type(4n+1),.grid:nth-of-type(4n+2){fill:#e8f0f3}", style)
        title = root.find(f"{namespace}text[@class='title']")
        self.assertEqual((title.get("x"), title.get("text-anchor")), ("454", "middle"))
        self.assertIn(".title{font-family:Arial,sans-serif", style)


if __name__ == "__main__":
    unittest.main()
