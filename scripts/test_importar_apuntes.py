import importlib.util
import base64
import re
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("importar_apuntes", Path(__file__).with_name("importar-apuntes.py"))
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)

FIGURE = '<p><span><span class="doc-image" role="figure"><img src="x" alt=""><span class="doc-image-caption"></span></span></span></p>'


class CropTests(unittest.TestCase):
    def test_removes_import_notice_but_preserves_other_sources(self):
        notice = (
            '<p class="source-note">Texto e imágenes importados del '
            '<a href="https://docs.google.com/document/d/example/edit">documento original en Google Docs</a>. '
            'Las imágenes se reproducen tal como aparecen allí; consulta la fuente para su contexto y autoría.</p>'
        )
        other = '<p class="source-note">Créditos de la imagen.</p>'
        self.assertEqual(importer.remove_import_notice(notice + other), other)
        self.assertEqual(importer.remove_import_notice(other), other)

    def test_practice_capitals_only_changes_final_section(self):
        source = ('<p>Despotismo Ilustrado y Reales Fábricas</p>'
                  '<h3>Ejemplos de preguntas cortas del bloque 4</h3>'
                  '<p>¿Qué es el <strong>Despotismo Ilustrado</strong>?</p>'
                  '<p>Reales Fábricas</p>'
                  '<section class="footnotes"><p>Despotismo Ilustrado</p></section>')
        result = importer.normalize_practice_capitals(source)
        self.assertIn('<p>Despotismo Ilustrado y Reales Fábricas</p>', result)
        self.assertIn('<strong>despotismo ilustrado</strong>', result)
        self.assertIn('<p>reales fábricas</p>', result)
        self.assertIn('<section class="footnotes"><p>Despotismo Ilustrado', result)

    def test_society_video_replaces_image_and_link(self):
        source = ('<p>Texto anterior</p><p><span><span class="doc-image" role="figure">'
                  '<img src="imagenes/bloque-4-08.png" alt=""></span></span></p>'
                  '<p><span><u><a href="https://youtu.be/sPzE-fm-V-Y">Vídeo y enlace</a>'
                  '</u></span></p><h3>1.5 Tema siguiente</h3>')
        result = importer.embed_society_video(source)
        self.assertNotIn("bloque-4-08.png", result)
        self.assertNotIn("Vídeo y enlace", result)
        self.assertIn('data-video-id="sPzE-fm-V-Y"', result)
        self.assertNotIn("reading-video-load", result)
        self.assertNotIn("El reproductor conecta", result)
        self.assertIn("<p>Texto anterior</p>", result)
        self.assertIn("<h3>1.5 Tema siguiente</h3>", result)

    def test_latin_expression_quotes_preserve_emphasis(self):
        source = "<p>Defendió la <strong><em>Universitas Christiana</em></strong>.</p>"
        result = importer.quote_latin_expression(source)
        self.assertIn("<strong><em>«universitas christiana»</em></strong>", result)
        self.assertEqual(importer.quote_latin_expression(result), result)

    def test_rebuild_stale_index_preserves_body_and_preamble(self):
        source = ('<p><strong>ÍNDICE</strong></p><p><a href="#h.old">Etiqueta antigua 3</a></p>'
                  '<p>Preámbulo <a href="https://example.com">fuente</a></p>'
                  '<h3 id="h.real">Apartado actual</h3><p>Texto íntegro.</p>')
        rebuilt = importer.rebuild_source_index(source)
        self.assertNotIn("ÍNDICE", rebuilt)
        result = importer.map_heading_anchors(rebuilt, 4, page_numbers=False)
        self.assertNotIn("Etiqueta antigua", result)
        self.assertIn("Preámbulo", result)
        self.assertIn("Texto íntegro.", result)
        self.assertIn('href="#bloque-4-seccion-real"', result)

    def test_rebuild_index_rejects_mixed_content(self):
        with self.assertRaises(ValueError):
            importer.rebuild_source_index(
                '<p>Texto ajeno <a href="#h.a">Apartado</a></p><h3 id="h.a">Apartado</h3>'
            )

    def test_rebuild_keeps_terminal_heading_number(self):
        source = '<p><a href="#h.a">Antiguo 3</a></p><h3 id="h.a">Ejemplos del bloque 4</h3>'
        body = importer.map_heading_anchors(
            importer.rebuild_source_index(source), 4, page_numbers=False
        )
        nav, _ = importer.extract_native_index(body, 4, page_numbers=False)
        self.assertIn(">Ejemplos del bloque 4</a>", nav)

    def test_repoblaciones_export_geometry(self):
        viewport = {"overflow": "hidden", "width": "328.13px", "height": "359.85px"}
        image = {"width": "490.96px", "height": "697.43px", "margin-left": "-72.30px", "margin-top": "-79.01px"}
        style = importer.image_crop([viewport], image)
        values = dict(item.split(":", 1) for item in style.split(";"))
        self.assertEqual(values["--doc-frame-ratio"], "328.13 / 359.85")
        self.assertAlmostEqual(float(values["--doc-img-left"][:-1]), -72.30 / 328.13 * 100)
        self.assertAlmostEqual(float(values["--doc-img-top"][:-1]), -79.01 / 359.85 * 100)
        self.assertAlmostEqual(float(values["--doc-img-width"][:-1]), 490.96 / 328.13 * 100)
        self.assertAlmostEqual(float(values["--doc-img-height"][:-1]), 697.43 / 359.85 * 100)

    def test_no_crop_keeps_full_image(self):
        viewport = {"overflow": "hidden", "width": "200px", "height": "100px"}
        image = {"width": "200px", "height": "100px", "transform": "rotate(0.00rad) translateZ(0px)"}
        self.assertIsNone(importer.image_crop([viewport], image))
        self.assertIsNone(importer.image_crop([], image))

    def test_class_styles_inline_override_and_nested_wrapper(self):
        data = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + b"\0\0\0\x04\0\0\0\x02").decode()
        source = (
            '<style>.c1{overflow:hidden;width:200px;height:100px}.c2{width:400px;height:200px}</style>'
            '<body><p><span class="c1"><span><img class="c2" style="margin-left:-30px;'
            'margin-top:-10px" src="data:image/png;base64,' + data + '"></span></span></p>'
            '<p><em>Pie con <a href="https://example.com">fuente</a></em></p></body>'
        )
        parser = importer.Importer(1, source)
        parser.feed(source)
        result = importer.transfer_image_captions("".join(parser.result))
        self.assertIn('class="doc-image-crop"', result)
        self.assertIn("--doc-img-width:200%", result)
        self.assertIn("--doc-img-left:-15%", result)
        self.assertEqual(result.count("Pie con"), 1)
        self.assertIn('class="doc-image-caption"><em>Pie con', result)
        self.assertIn('href="https://example.com"', result)
        self.assertEqual(len(parser.images), 1)
        self.assertFalse(parser.source_styles)

    def test_rotation_is_sanitized_and_unknown_geometry_aborts(self):
        self.assertEqual(importer.crop_transform({"transform": "rotate(-15deg) translateZ(0px)"}), "rotate(-15deg)")
        for transform in ("url(https://example.com)", "translateZ(1px)", "matrix(1,0,0,1,0,0)", "rotate(nanrad)"):
            with self.subTest(transform=transform), self.assertRaises(ValueError):
                importer.crop_transform({"transform": transform})
        with self.assertRaises(ValueError):
            importer.image_crop([{"overflow": "hidden", "width": "100%", "height": "200px"}], {"width": "200px", "height": "300px"})


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


class NativeIndexTests(unittest.TestCase):
    def fixture(self):
        return (
            '<p><strong>ÍNDICE</strong></p>'
            '<p><a href="#bloque-1-seccion-a">Bloque 1</a><a href="#bloque-1-seccion-a"> 2</a></p>'
            '<p><a href="#bloque-1-seccion-b">1.2 Tema 5</a></p>'
            '<p><a href="#bloque-1-seccion-c">1.2.1 Subtema 6</a></p>'
            '<p><a href="#bloque-1-seccion-d">Ejemplos de preguntas cortas del bloque 1 8</a></p>'
            '<p><a href="https://example.com">Mapa original</a></p>'
            '<h2 id="bloque-1-seccion-a">Bloque 1</h2>'
            '<h3 id="bloque-1-seccion-b">1.2 Tema</h3><p>Texto educativo.</p>'
            '<h4 id="bloque-1-seccion-c">1.2.1 Subtema</h4>'
            '<h3 id="bloque-1-seccion-d">Ejemplos de preguntas cortas del bloque 1</h3>'
        )

    def test_hierarchy_links_and_original_preamble(self):
        source = self.fixture()
        nav, body = importer.extract_native_index(source, 1)
        self.assertEqual(body, source[source.index("<h2"):])
        self.assertIn('<a href="#bloque-1-seccion-b">1.2 Tema</a><ul>', nav)
        self.assertIn('aria-labelledby="reading-index-title"', nav)
        self.assertIn('<div class="reading-preamble"><p><a href="https://example.com">Mapa original</a></p></div>', nav)
        self.assertNotIn("> 2</a>", nav)
        self.assertEqual(nav.count('<a href="#'), 4)

    def test_missing_duplicate_mismatched_and_mixed_entries_abort(self):
        source = self.fixture()
        variants = [
            source.replace('href="#bloque-1-seccion-b"', 'href="#bloque-1-seccion-missing"'),
            source.replace("1.2 Tema 5", "Otro tema 5"),
            source.replace('<p><a href="#bloque-1-seccion-b">', '<p>Contenido adicional<a href="#bloque-1-seccion-b">'),
            source.replace('<h3 id="bloque-1-seccion-b">', '<h3 id="bloque-1-seccion-a">'),
            source.replace('<h4 id="bloque-1-seccion-c">', '<h5 id="bloque-1-seccion-c">'),
            source.replace('<p><a href="#bloque-1-seccion-c">1.2.1 Subtema 6</a></p>',
                           '<p><a href="#bloque-1-seccion-b">1.2 Tema 5</a></p>'),
            source.replace('<p><strong>ÍNDICE</strong></p>',
                           '<p><strong>ÍNDICE</strong></p><p>Texto original ajeno al índice.</p>'),
        ]
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                importer.extract_native_index(variant, 1)

    def test_current_pages_have_all_original_toc_targets(self):
        total = 0
        for block, count in ((1, 5), (2, 6), (3, 12)):
            parser = importer.Fragment()
            # Parse just the main fragment (the full document has scripts and metadata).
            page = (importer.ROOT / f"apuntes/bloque-{block}.html").read_text()
            main = re.search(r'<main\b[^>]*>(.*?)</main>', page, re.S)[1]
            main = re.sub(r'<section class="reading-tools".*?</section>', "", main, count=1, flags=re.S)
            parser.feed(main)
            index = next(node for node in importer.walk(parser.root) if node.has_class("reading-index"))
            article = next(node for node in importer.walk(parser.root) if node.has_class("reading-content"))
            links = [node for node in importer.walk(index) if node.tag == "a"]
            self.assertEqual(len(links), count)
            self.assertEqual(article.children[0].tag, "h2")
            headings = {dict(node.attrs).get("id"): node for node in importer.walk(article)
                        if node.tag in ("h2", "h3", "h4", "h5")}
            for link in links:
                target = dict(link.attrs)["href"][1:]
                self.assertIn(target, headings)
                self.assertEqual(" ".join(importer.element_text(link).split()),
                                 " ".join(importer.element_text(headings[target]).split()))
            self.assertEqual(sum(importer.element_text(link).startswith("1.2 ") for link in links), 1)
            total += count
        self.assertEqual(total, 23)


class PageShellTests(unittest.TestCase):
    def test_import_replacement_preserves_shared_reading_tools(self):
        page = (importer.ROOT / "apuntes/bloque-1.html").read_text()
        updated = importer.replace_imported_article(
            page,
            '<nav class="reading-index"><h2>Índice</h2></nav>',
            '<article class="reading-content"><h2>Texto actualizado</h2></article>',
        )
        self.assertIn('id="reading-search"', updated)
        self.assertIn('id="reading-size-up"', updated)
        self.assertIn('class="reading-illustration"', updated)
        self.assertIn("Texto actualizado", updated)
        self.assertEqual(updated.count('class="reading-tools"'), 1)

    def test_all_twelve_pages_have_the_shared_reading_shell(self):
        for block in range(1, 13):
            page = (importer.ROOT / f"apuntes/bloque-{block}.html").read_text()
            with self.subTest(block=block):
                self.assertIn('class="reading-tools"', page)
                self.assertIn('id="reading-font"', page)
                self.assertIn('id="notes-search"', page)


if __name__ == "__main__":
    unittest.main()
