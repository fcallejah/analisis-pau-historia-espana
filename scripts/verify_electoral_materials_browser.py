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
                ("material propio", 23),
                ("resultados electorales 2015", 1),
                ("resultados referéndum 1980", 1),
                ("referéndum 2005", 2),
                ("elecciones europeas 2014", 1),
                ("elecciones andaluzas 1982", 1),
                ("elecciones generales 1982", 1),
                ("elecciones segunda república", 5),
                ("elecciones municipales 1931", 2),
                ("elecciones generales 1931", 1),
            ):
                search.fill(query)
                assert page.locator('.document-card[data-id^="propio-"]').count() == expected, query
            search.fill("")
            page.locator('[data-type="grafico"]').click()
            own_cards = page.locator('.document-card[data-id^="propio-"]')
            assert page.locator('[data-type="propio"]').count() == 0
            assert own_cards.count() == 23
            assert "23 materiales propios" in page.locator("#document-count").inner_text()
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
            assert dialog.locator(".study-chart-selector").count() == 0
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
            election_select = dialog.locator(".study-chart-selector select")
            election_labels = election_select.locator("option").all_text_contents()
            election_files = [
                "elecciones-1977-diagrama-semicircular.svg",
                "elecciones-generales-1979-semicirculo.svg",
                "elecciones-generales-1982-semicirculo.svg",
                "elecciones-generales-1986-semicirculo.svg",
                "elecciones-generales-1989-semicirculo.svg",
                "elecciones-generales-1993-semicirculo.svg",
                "elecciones-generales-1996-semicirculo.svg",
                "elecciones-generales-2000-semicirculo.svg",
                "elecciones-generales-2004-semicirculo.svg",
                "elecciones-generales-2008-semicirculo.svg",
                "elecciones-generales-2011-semicirculo.svg",
                "elecciones-generales-2015-semicirculo.svg",
            ]
            assert len(election_labels) == len(election_files) == 12
            assert election_labels[0] == "Resultado elecciones 1977 (15 de junio)"
            assert election_labels[1] == "Resultado elecciones 1979 (1 de marzo)"
            assert election_labels[-1] == "Resultado elecciones 2015 (20 de diciembre)*"
            assert dialog.locator(".study-chart-note").count() == 0
            assert not any(
                word in label.lower()
                for label in election_labels
                for word in ("andaluzas", "europeas", "referéndum")
            )
            selector_label = dialog.locator(".study-chart-selector")
            assert "Elección:" not in selector_label.inner_text()
            assert election_select.get_attribute("aria-label") == "Desplegable electoral"
            assert "Datos del Congreso: candidaturas con representación" not in dialog.inner_text()
            previous = dialog.get_by_role("button", name="Anterior elección")
            next_election = dialog.get_by_role("button", name="Próxima elección")
            assert not previous.is_disabled()
            assert not next_election.is_disabled()
            label_box = selector_label.bounding_box()
            select_box = election_select.bounding_box()
            assert abs(
                select_box["x"] + select_box["width"] / 2
                - label_box["x"] - label_box["width"] / 2
            ) < 2
            next_election.click()
            assert dialog.locator(".study-chart-selector select").input_value() == "2"
            assert dialog.locator(".study-election-chart").get_attribute("src").endswith(
                "elecciones-generales-1982-semicirculo.svg"
            )
            dialog.get_by_role("button", name="Anterior elección").click()
            assert dialog.locator(".study-chart-selector select").input_value() == "1"
            assert dialog.locator(".study-election-chart").get_attribute("src").endswith(
                "elecciones-generales-1979-semicirculo.svg"
            )
            for index, filename in enumerate(election_files):
                dialog.locator(".study-chart-selector select").select_option(str(index))
                page.wait_for_function(
                    """filename => {
                      const image = document.querySelector('#document-dialog .study-election-chart');
                      return image?.complete && image.naturalWidth > 0 && image.src.endsWith(filename);
                    }""",
                    arg=filename,
                )
                if index == 0:
                    assert dialog.get_by_role("button", name="Anterior elección").is_disabled()
                    error_note = dialog.locator(".document-error-note")
                    assert "UCD figura con 166 escaños" in error_note.inner_text()
                    assert error_note.evaluate(
                        "node => getComputedStyle(node).color"
                    ) == "rgb(180, 35, 24)"
                    source_link = dialog.locator(".document-collection-link")
                    assert source_link.inner_text() == "2007 · Examen 4 · Bloque II · Opción B"
                    assert source_link.get_attribute("href") == (
                        "https://drive.google.com/file/d/1pmWRafrxiqQ8zQcLkraSGoRxkCyvyFjC/view"
                    )
                if index == len(election_files) - 1:
                    assert dialog.get_by_role("button", name="Próxima elección").is_disabled()
            assert dialog.locator("h2").inner_text() == "Elecciones generales de 2015*"
            assert any(
                "turnismo PP–PSOE" in note
                for note in dialog.locator(".study-chart-note").all_inner_texts()
            )
            assert dialog.locator(".document-table caption").text_content() == "Congreso de los Diputados · 2015"
            assert dialog.locator(".document-reading-note").count() == 0
            for _ in range(len(election_files) + 2):
                if not dialog.evaluate("node => node.open"):
                    break
                current_route = page.evaluate("location.hash")
                dialog.get_by_role("button", name="Cerrar documento").click()
                page.wait_for_function(
                    "route => location.hash !== route", arg=current_route
                )
            assert not dialog.evaluate("node => node.open")
            page.locator('[data-id="propio-elecciones-andaluzas-1982"] .document-open').click()
            assert dialog.locator(".study-chart-selector").count() == 0
            assert dialog.locator(".study-election-chart").get_attribute("src").endswith(
                "elecciones-andaluzas-1982-semicirculo.svg"
            )
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-europeas-2014"] .document-open').click()
            assert dialog.locator(".study-chart-selector").count() == 0
            assert dialog.locator("h2").inner_text() == "Elecciones europeas de 2014 en España*"
            assert any(
                "fragmentación del voto" in note
                for note in dialog.locator(".study-chart-note").all_inner_texts()
            )
            assert dialog.locator(".study-election-chart").get_attribute("src").endswith(
                "elecciones-europeas-2014-semicirculo.svg"
            )
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1931"] .document-open').click()
            image = dialog.locator(".study-election-chart")
            assert image.get_attribute("src").endswith("elecciones-republica-1931-semicirculo.svg")
            assert "1931" in image.get_attribute("alt")
            svg = page.request.get(image.evaluate("node => node.src")).text()
            assert "Otros*" in svg
            select = dialog.locator(".study-chart-selector select")
            assert select.locator("option").all_text_contents() == [
                "1931 · 28 de junio",
                "1933 · 19 de noviembre y 3 de diciembre",
                "1936 · 16 de febrero y 1 de marzo",
            ]
            assert dialog.get_by_role("button", name="Anterior elección").is_disabled()
            dialog.get_by_role("button", name="Próxima elección").click()
            assert dialog.locator("h2").inner_text() == "Elecciones generales de 1933: Segunda República"
            assert dialog.locator(".study-election-chart").get_attribute("src").endswith(
                "elecciones-republica-1933-semicirculo.svg"
            )
            dialog.get_by_role("button", name="Próxima elección").click()
            assert dialog.locator("h2").inner_text() == "Elecciones generales de 1936: Segunda República"
            assert dialog.get_by_role("button", name="Próxima elección").is_disabled()
            dialog.locator(".study-chart-selector select").select_option("0")
            assert dialog.locator("h2").inner_text() == "Elecciones generales de 1931: Cortes Constituyentes"
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
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
            assert "El diagrama representa escaños, no votos." not in dialog.inner_text()
            assert dialog.get_by_role(
                "link", name="Elecciones generales de 1936 · distribución por bloques"
            ).get_attribute("href").endswith("Elecciones_generales_de_Espa%C3%B1a_de_1936")
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
            municipal = page.locator('[data-id="propio-elecciones-municipales-1931"]')
            municipal.locator(".document-open").click()
            assert [row.inner_text() for row in dialog.locator(".study-chart-row").all()] == [
                "Monárquicos\n30,54 %", "Republicanos y socialistas\n69,46 %"
            ]
            assert "capitales de provincia" in dialog.inner_text().lower()
            assert "se interpretaron como un plebiscito" in dialog.inner_text()
            assert "195.147 votos" in dialog.inner_text() and "443.945 votos" in dialog.inner_text()
            assert "no coinciden" not in dialog.inner_text() and "falta Ávila" not in dialog.inner_text()
            dialog.get_by_text("Ver tablas y notas de los datos").click()
            assert "1.104.159" in dialog.inner_text() and "715.911" in dialog.inner_text()
            assert dialog.get_by_role("link", name="Fuente de los votos en las capitales").count() == 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-municipales-1931-capitales"] .document-open').click()
            assert [row.inner_text() for row in dialog.locator(".study-chart-row").all()] == [
                "Monárquicos\n30,54 %", "Republicanos y socialistas\n69,46 %"
            ]
            assert "Porcentaje entre estas dos candidaturas" in dialog.inner_text()
            assert "no un referéndum" in dialog.inner_text()
            assert "no coinciden" not in dialog.inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.keyboard.press("Escape")
            page.locator('[data-id="propio-elecciones-generales-1982"] .document-open').click()
            assert dialog.locator(".study-chart-note").count() == 0
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
            assert len(dialog.locator(".study-chart-note").all_inner_texts()) == 1
            assert "Ampliación posterior al corte de 2012" in dialog.locator(
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
        assert page.locator('.document-card[data-id^="propio-"]').count() == 23
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
