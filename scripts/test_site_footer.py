import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("actualizar_pie", ROOT / "scripts/actualizar-pie.py")
footer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(footer)


class FooterTests(unittest.TestCase):
    def test_existing_footer_is_replaced_without_changing_content(self):
        source = '<html><head></head><body><main>Apuntes</main><footer>Anterior</footer></body></html>'
        updated = footer.update_page(source, "../")
        self.assertIn("<main>Apuntes</main>", updated)
        self.assertNotIn("Anterior", updated)
        self.assertEqual(updated.count("<footer"), 1)
        self.assertIn('href="../index.html#inicio"', updated)
        self.assertIn('href="../site-footer.css?v=2"', updated)
        self.assertEqual(footer.update_page(updated, "../"), updated)

    def test_missing_footer_is_added_outside_dialog_and_main(self):
        source = '<html><head></head><body><main>Banco</main><dialog>Ficha</dialog></body></html>'
        updated = footer.update_page(source)
        self.assertGreater(updated.index("<footer"), updated.index("</dialog>"))
        self.assertIn('href="index.html#inicio"', updated)
        self.assertEqual(footer.update_page(updated), updated)

    def test_duplicate_footers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "varios pies"):
            footer.update_page("<head></head><body><footer>A</footer><footer>B</footer></body>")

    def test_all_fifteen_pages_are_synchronized(self):
        pages = [ROOT / "index.html", ROOT / "documentos.html", ROOT / "mis-preguntas.html",
                 *sorted((ROOT / "apuntes").glob("bloque-*.html"))]
        self.assertEqual(len(pages), 15)
        for path in pages:
            with self.subTest(page=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertEqual(
                    footer.update_page(source, "../" if path.parent.name == "apuntes" else "",
                                       home=path.name == "index.html"),
                    source,
                )
                self.assertEqual(source.count('<footer class="site-footer">'), 1)
                self.assertGreater(source.index('<footer class="site-footer">'), source.index("</main>"))


if __name__ == "__main__":
    unittest.main()
