"""Verify editorial election graphics against a running local preview."""
import os

from playwright.sync_api import sync_playwright


BASE = os.environ.get("PAU_TEST_BASE", "http://localhost:8765")


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width in (375, 820):
            context = browser.new_context(
                viewport={"width": width, "height": 1000}, service_workers="block"
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{BASE}/documentos.html")
            search = page.locator("#document-search")
            for query, expected in (
                ("material propio", 21),
                ("resultados electorales 2015", 1),
                ("resultados referéndum 1980", 1),
                ("referéndum 2005", 2),
                ("elecciones europeas 2014", 1),
                ("elecciones andaluzas 1982", 1),
                ("elecciones generales 1982", 1),
                ("elecciones segunda república", 4),
                ("elecciones municipales 1931", 1),
                ("elecciones generales 1931", 1),
            ):
                search.fill(query)
                assert page.locator('.document-card[data-id^="propio-"]').count() == expected, query
            search.fill("")
            page.locator('[data-type="grafico"]').click()
            own_cards = page.locator('.document-card[data-id^="propio-"]')
            assert page.locator('[data-type="propio"]').count() == 0
            assert own_cards.count() == 21
            assert "21 materiales propios" in page.locator("#document-count").inner_text()
            for card in own_cards.all():
                assert card.locator(".document-kind").inner_text() == "MAPAS Y GRÁFICOS"
                assert card.locator(".exam-pill").inner_text() == "Elaboración propia · puede caer"
                assert card.locator(".exam-pill").evaluate("node => node.tagName") == "SPAN"
            for kind in ("texto", "imagen"):
                page.locator(f'[data-type="{kind}"]').click()
                assert page.locator('.document-card[data-id^="propio-"]').count() == 0
            page.locator('[data-type="grafico"]').click()
            page.locator("#document-unit").select_option("iii-13")
            assert page.locator('[data-id="propio-referendum-europa-2005"]').count() == 1
            assert page.locator('[data-id="propio-elecciones-europeas-2014"]').count() == 1
            page.locator("#document-unit").select_option("")
            card = page.locator('[data-id="propio-referendum-andalucia-1980"]')
            card.locator(".document-open").click()
            dialog = page.locator("#document-dialog")
            assert dialog.locator(".document-kind").inner_text() == "MAPAS Y GRÁFICOS · BLOQUE 12"
            assert dialog.locator(".exam-pill").inner_text() == "Elaboración propia · puede caer"
            rows = dialog.locator(".study-chart-row")
            assert rows.count() == 3
            assert [row.inner_text() for row in rows.all()] == [
                "Participación · sobre censo\n64,19 %",
                "Sí · sobre votantes\n86,94 %",
                "No · sobre votantes\n5,36 %",
            ]
            assert dialog.locator(".study-chart-fill.is-yes").evaluate(
                "node => node.style.width"
            ) == "86.94%"
            assert "Blanco: 7,04 %" in dialog.inner_text()
            assert "rechazada" in dialog.inner_text()
            assert dialog.get_by_text("Fuente de los datos", exact=True).count() == 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1979"] .document-open').click()
            election_option = dialog.locator(".study-chart-selector option").first
            assert election_option.inner_text() == "Resultado elecciones 1979 (1 de marzo)"
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1931"] .document-open').click()
            image = dialog.locator(".study-election-chart")
            assert image.get_attribute("src").endswith("elecciones-republica-1931-semicirculo.svg")
            assert "1931" in image.get_attribute("alt")
            assert "otros*" in dialog.inner_text().lower()
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1933"] .document-open').click()
            image = dialog.locator(".study-election-chart")
            assert image.get_attribute("src").endswith("elecciones-republica-1933-semicirculo.svg")
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1936"] .document-open').click()
            image = dialog.locator(".study-election-chart")
            assert image.get_attribute("src").endswith("elecciones-republica-1936-semicirculo.svg")
            page.wait_for_function("""() => {
                const image = document.querySelector('#document-dialog .study-election-chart');
                return image?.complete && image.naturalWidth > 0;
            }""")
            assert "escaños, no votos" in dialog.inner_text()
            assert "Fuente secundaria, no oficial" in dialog.inner_text()
            assert dialog.get_by_role(
                "link", name="Elecciones generales de 1936 · distribución por bloques"
            ).get_attribute("href").endswith("Elecciones_generales_de_Espa%C3%B1a_de_1936")
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
            municipal = page.locator('[data-id="propio-elecciones-municipales-1931"]')
            municipal.locator(".document-open").click()
            assert dialog.locator(".study-chart-row").count() == 1
            assert dialog.locator(".study-chart-row").inner_text() == (
                "Participación · sobre electores\n64,84 %"
            )
            assert "capitales de provincia" in dialog.inner_text()
            assert "no es un resultado nacional" in dialog.inner_text().lower()
            assert dialog.locator(".study-chart-fill.is-turnout").evaluate(
                "node => getComputedStyle(node).backgroundColor"
            ) == "rgb(89, 99, 109)"
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1982"] .document-open').click()
            assert "PSOE + PSC" in dialog.locator(".study-chart-note").inner_text()
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-2015"] .document-open').click()
            image = dialog.locator(".study-election-chart")
            assert image.get_attribute("src").endswith("elecciones-generales-2015-semicirculo.svg")
            page.wait_for_function("""() => {
                const image = document.querySelector('#document-dialog .study-election-chart');
                return image?.complete && image.naturalWidth > 0;
            }""")
            assert image.evaluate("node => node.complete && node.naturalWidth > 0")
            assert dialog.get_by_role("link", name="Abrir gráfico SVG").get_attribute("href").endswith(
                "elecciones-generales-2015-semicirculo.svg"
            )
            assert "PSOE, PSC y PSOE-Nueva Canarias" in dialog.inner_text()
            assert "Podemos y confluencias" in dialog.inner_text()
            assert "Partido Popular (PP) y coaliciones" in dialog.locator(
                ".study-chart-note"
            ).inner_text()
            dialog.get_by_text("Ver tablas y notas de los datos").click()
            assert dialog.locator(".document-table").count() == 1
            page.keyboard.press("Escape")
            for identity, filename in (
                ("propio-elecciones-andaluzas-1982", "elecciones-andaluzas-1982-semicirculo.svg"),
                ("propio-elecciones-europeas-2014", "elecciones-europeas-2014-semicirculo.svg"),
            ):
                page.locator(f'[data-id="{identity}"] .document-open').click()
                image = dialog.locator(".study-election-chart")
                assert image.get_attribute("src").endswith(filename)
                page.wait_for_function("""() => {
                    const image = document.querySelector('#document-dialog .study-election-chart');
                    return image?.complete && image.naturalWidth > 0;
                }""")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.keyboard.press("Escape")
            page.locator('[data-id="propio-referendum-europa-2005"] .document-open').click()
            assert "41,77 %" in dialog.inner_text()
            assert "76,30 %" in dialog.inner_text()
            assert "81,84 %" in dialog.inner_text()
            assert dialog.locator(".study-chart-row").count() == 3
            page.keyboard.press("Escape")
            page.locator("#document-year").select_option("2003")
            assert page.locator('.document-card[data-id^="propio-"]').count() == 0
            assert not errors, errors
            context.close()
        context = browser.new_context(service_workers="block")
        page = context.new_page()
        page.add_init_script("sessionStorage.setItem('pau-he.document-type', 'propio')")
        page.goto(f"{BASE}/documentos.html")
        assert page.locator('[data-type="grafico"]').get_attribute("aria-pressed") == "true"
        assert page.locator('.document-card[data-id^="propio-"]').count() == 21
        page.locator('[data-id="propio-referendum-andalucia-1980"] [data-document-mark="favorite"]').click()
        page.goto(f"{BASE}/mis-documentos.html")
        page.locator('[data-type="grafico"]').click()
        card = page.locator('[data-id="propio-referendum-andalucia-1980"]')
        assert card.count() == 1
        assert card.locator(".exam-pill").inner_text() == "Elaboración propia · puede caer"
        assert page.locator('[data-type="propio"]').count() == 0
        context.close()
        browser.close()
    print("Materiales electorales: filtros, gráficos, fuentes y tablas verificados.")


if __name__ == "__main__":
    run()
