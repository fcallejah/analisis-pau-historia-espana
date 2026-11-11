"""Integrity checks for the reviewed document corpus."""
import json
from pathlib import Path
import struct
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent


class DocumentCorpusTests(unittest.TestCase):
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
                    dimensions = struct.unpack(">II", path.read_bytes()[16:24])
                    self.assertEqual(dimensions, (image["width"], image["height"]))
                    self.assertTrue(image["alt"])
                if document["type"] == "texto":
                    self.assertTrue(document["text"])
                if "table" in document:
                    table = document["table"]
                    self.assertTrue(all(len(row) == len(table["headers"]) for row in table["rows"]))

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
