import importlib.util
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec("pymupdf"), "Pruebas opcionales: requieren PyMuPDF")
class TextCropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "exportar_graficos", Path(__file__).with_name("exportar-graficos.py"))
        cls.exporter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.exporter)

    def setUp(self):
        self.pdf = self.exporter.pymupdf.open()
        self.page = self.pdf.new_page()
        self.page.insert_text((20, 40), "Resultados electorales (en escanos)")

    def tearDown(self):
        self.pdf.close()

    def test_complete_title_is_accepted(self):
        self.exporter.validate_text_crop(self.page, self.page.rect)

    def test_clipped_end_of_title_is_rejected(self):
        x0, y0, x1, y1, *_ = self.page.get_text("words")[-1]
        clip = self.exporter.pymupdf.Rect(0, 0, x1 - 1, self.page.rect.height)
        with self.assertRaisesRegex(ValueError, "escanos"):
            self.exporter.validate_text_crop(self.page, clip)

    def test_adjacent_text_centered_outside_crop_is_excluded(self):
        x0, y0, x1, y1, *_ = self.page.get_text("words")[0]
        clip = self.exporter.pymupdf.Rect(0, (y0 + y1) / 2 + 1,
                                        self.page.rect.width, self.page.rect.height)
        self.exporter.validate_text_crop(self.page, clip)


if __name__ == "__main__":
    unittest.main()
