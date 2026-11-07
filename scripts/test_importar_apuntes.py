import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("importar_apuntes", Path(__file__).with_name("importar-apuntes.py"))
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)

FIGURE = '<p><span><span class="doc-image" role="figure"><img src="x" alt=""><span class="doc-image-caption"></span></span></span></p>'


class CaptionTests(unittest.TestCase):
    def test_adjacent_caption_retains_link_and_format(self):
        source = FIGURE + '<div><p><br></p><div><p><em>Texto <a href="https://example.com">fuente</a></em></p></div></div>'
        result = importer.transfer_image_captions(source)
        self.assertIn('<span class="doc-image-caption"><em>Texto <a href="https://example.com">fuente</a></em></span>', result)
        self.assertEqual(result.count("Texto"), 1)

    def test_unrelated_content_stops_search(self):
        for barrier in ('<p>Texto normal</p>', '<h3>Encabezado</h3>', '<p><img src="y"></p>', '<ul><li>Texto</li></ul>', '<p><em>Mixto</em> normal</p>'):
            with self.subTest(barrier=barrier):
                result = importer.transfer_image_captions(FIGURE + barrier + '<p><em>Ajeno</em></p>')
                self.assertNotIn('class="doc-image-caption"', result)
                self.assertEqual(result.count("Ajeno"), 1)

    def test_no_caption_stays_empty(self):
        self.assertNotIn('class="doc-image-caption"', importer.transfer_image_captions(FIGURE + "<p><br></p>"))

    def test_multiple_images_do_not_steal_caption(self):
        inner = FIGURE.removeprefix("<p>").removesuffix("</p>")
        result = importer.transfer_image_captions("<p>" + inner + inner + "</p><p><em>Ambiguo</em></p>")
        self.assertNotIn('class="doc-image-caption"', result)
        self.assertEqual(result.count("Ambiguo"), 1)


if __name__ == "__main__":
    unittest.main()
