"""Check the Nueva Planta map against the local server on port 8765."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/apuntes/bloque-4.html"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL)
        page.locator(".np-stage svg").wait_for()
        regions = page.locator(".np-region-buttons button")
        assert regions.count() == 9
        assert page.locator(".np-map > details > ul > li").count() == 2
        assert "Utrecht-Rastatt" in page.locator(".np-map > details").text_content()
        assert page.locator(".np-stage [role=button]").count() == 9
        for link in page.locator(".np-source a").all():
            href = link.get_attribute("href")
            assert href.startswith("https://") or href.startswith("../assets/"), href
        assert "INE" in page.locator(".np-source").inner_text()
        assert page.locator(".np-stage [data-territory=castilla] path").get_attribute("d").count("L") > 300
        assert page.locator(".np-map").get_attribute("data-mode") == "before"
        assert "Monarquía Hispánica" in page.locator(".np-mode-description").inner_text()
        assert page.locator('[data-peace="menorca"] path').evaluate("n=>getComputedStyle(n).fill") == "rgb(227, 186, 76)"
        assert not page.locator(".np-peace-note").is_visible()
        assert not page.locator(".np-provinces-note").is_visible()
        assert page.locator(".historical-divisions").is_visible()
        assert page.locator(".historical-divisions path").count() > 10
        assert "Castilla la Nueva" in page.locator(".historical-divisions").text_content()
        page.locator(".np-stage [data-territory=valencia]").click()
        assert page.locator(".np-info h3").inner_text() == "Reino de Valencia"
        page.locator("[data-np-mode=after]").click()
        assert page.locator(".np-map").get_attribute("data-mode") == "after"
        assert "Centralización borbónica (reino de España)" in page.locator(".np-mode-description").inner_text()
        assert page.locator("#np-provinces").count() == 0
        assert page.locator("#referencia-provincial-ign").count() == 0
        assert page.locator("#provincias-1782").count() == 0
        assert page.locator(".centralized-outline").is_visible()
        for region in ("aragon", "cataluna", "valencia", "mallorca"):
            shape = page.locator(f'.np-stage [data-territory="{region}"] path')
            assert shape.evaluate("n=>getComputedStyle(n).stroke") == "rgb(214, 238, 122)"
            assert page.locator(f'.np-stage [data-territory="{region}"] text').first.is_visible()
            assert page.locator(f'.np-stage [data-territory="{region}"] text').first.evaluate("n=>getComputedStyle(n).fill") == "rgb(103, 58, 183)"
        assert page.locator(".np-aragon-label").is_visible()
        assert "Felipe V" in page.locator(".np-aragon-label").inner_text()
        assert "derecho de conquista" in page.locator(".np-aragon-label").inner_text()
        assert "guerra de sucesión española" in page.locator(".np-aragon-label").inner_text()
        assert "Parte del derecho civil" not in page.locator(".np-aragon-label").inner_text()
        assert "derrotar a los territorios" not in page.locator(".np-aragon-label").inner_text()
        assert page.locator(".np-peace-note").is_visible()
        assert page.locator(".np-provinces-note").is_visible()
        assert "1750" in page.locator(".np-provinces-note").inner_text()
        assert "22 provincias" in page.locator(".np-provinces-note").inner_text()
        assert page.locator(".np-provinces-note a").get_attribute("href") == "https://pares.cultura.gob.es/catastro/servlets/ServletController?accion=2&opcion=43"
        assert "Utrecht (1713)" in page.locator(".np-peace-note").inner_text()
        assert page.locator('[data-peace="menorca"] path').evaluate("n=>getComputedStyle(n).fill") == "rgb(229, 27, 35)"
        assert page.locator('[data-peace="gibraltar"] circle').evaluate("n=>getComputedStyle(n).fill") == "rgb(229, 27, 35)"
        assert page.locator(".np-date").inner_text() == "29 de junio de 1707"
        assert "no se restituyó" in page.locator(".np-explanation").inner_text()
        assert page.locator(".np-stage [data-territory=valencia] path").evaluate(
            "n => getComputedStyle(n).fill"
        ) == "rgb(214, 238, 122)"
        assert not page.locator(".historical-divisions").is_visible()
        assert page.locator(".unified-label").first.is_visible()
        assert page.locator(".np-stage [data-territory=valencia] path").evaluate(
            "n => getComputedStyle(n).strokeDasharray"
        ) == "none"
        for name, date in (("aragon", "1711"), ("cataluna", "1716"), ("mallorca", "1715")):
            page.locator(f".np-region-buttons [data-territory={name}]").click()
            assert date in page.locator(".np-date").inner_text()
        for name in ("navarra", "vizcaya", "guipuzcoa", "alava"):
            page.locator(f".np-region-buttons [data-territory={name}]").click()
            assert "Conserv" in page.locator(".np-explanation").inner_text()
            assert page.locator(".np-subdivisions").inner_text()
        page.locator(".np-stage [data-territory=cataluna]").focus()
        page.keyboard.press("Enter")
        assert "Cataluña" in page.locator(".np-info h3").inner_text()
        page.keyboard.press("Space")
        assert page.locator(".np-stage [data-territory=cataluna]").get_attribute("aria-pressed") == "false"
        assert not page.locator(".np-info").is_visible()
        assert page.locator('.np-region-buttons [aria-pressed="true"]').count() == 0
        page.keyboard.press("Enter")
        assert page.locator(".np-info").is_visible()
        page.locator(".np-region-buttons [data-territory=cataluna]").click()
        assert not page.locator(".np-info").is_visible()
        page.locator("[data-np-mode=before]").click()
        assert not page.locator(".np-info").is_visible()
        page.locator(".np-region-buttons [data-territory=cataluna]").click()
        page.locator("[data-np-mode=before]").click()
        assert page.locator(".historical-divisions").is_visible()
        assert not page.locator(".unified-label").first.is_visible()
        assert page.locator(".np-stage [data-territory=aragon] path").evaluate(
            "n => getComputedStyle(n).fill"
        ) == "rgb(227, 186, 76)"
        assert page.locator(".np-info h3").inner_text() == "Principado de Cataluña"
        for _ in range(8):
            if not page.locator("[data-np-zoom=in]").is_disabled():
                page.locator("[data-np-zoom=in]").click()
        assert page.locator(".np-zoom-level").inner_text() == "400 %"
        assert page.locator("[data-np-zoom=in]").is_disabled()
        stage = page.locator(".np-stage").bounding_box()
        page.mouse.move(stage["x"] + 80, stage["y"] + 80)
        page.mouse.down()
        page.mouse.move(stage["x"] + 160, stage["y"] + 160, steps=10)
        page.mouse.up()
        view = page.locator(".np-stage svg").get_attribute("viewBox")
        assert view != "300 210 200 140"
        page.evaluate("dispatchEvent(new Event('beforeprint'))")
        assert page.locator(".np-stage svg").get_attribute("viewBox") == "0 0 800 560"
        assert page.locator(".np-map details").get_attribute("open") is not None
        page.emulate_media(media="print")
        assert not page.locator(".np-controls").is_visible()
        assert page.locator(".np-map details ul").is_visible()
        page.evaluate("dispatchEvent(new Event('afterprint'))")
        assert page.locator(".np-stage svg").get_attribute("viewBox") == view
        page.emulate_media(media="screen")
        page.locator("[data-np-zoom=reset]").click()
        assert page.locator(".np-stage svg").get_attribute("viewBox") == "0 0 800 560"
        assert page.locator("[data-np-zoom=out]").is_disabled()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator(".np-region-buttons [data-territory=mallorca]").click()
        page.evaluate("document.documentElement.dataset.theme = 'dark'")
        assert "Mallorca" in page.locator(".np-info h3").inner_text()
        page.locator("[data-np-mode=after]").click()
        assert "Menorca" in page.locator(".np-explanation").inner_text()
        # Touch events verify pinch and restoration independently of mouse input.
        page.locator(".np-stage").scroll_into_view_if_needed()
        stage = page.locator(".np-stage").bounding_box()
        x, y = stage["x"] + stage["width"] / 2, stage["y"] + stage["height"] / 2
        client = context.new_cdp_session(page)
        for kind, gap in (("touchStart", 30), ("touchMove", 65)):
            client.send("Input.dispatchTouchEvent", {
                "type": kind,
                "touchPoints": [{"x": x - gap, "y": y, "id": 1}, {"x": x + gap, "y": y, "id": 2}],
            })
        client.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        assert page.locator(".np-zoom-level").inner_text() != "100 %"
        page.locator("[data-np-zoom=reset]").click()
        assert not errors, errors

        fallback = browser.new_context(java_script_enabled=False, service_workers="block")
        static = fallback.new_page()
        static.goto(URL)
        assert static.locator(".np-stage img").is_visible()
        assert static.locator(".np-stage img").evaluate("n => n.complete && n.naturalWidth > 0")
        static.locator(".np-map summary").click()
        assert "Utrecht-Rastatt" in static.locator(".np-map details").inner_text()

        broken = context.new_page()
        broken.route("**/nueva-planta.svg*", lambda route: route.abort())
        broken.goto(URL)
        broken.locator(".np-error").wait_for()
        assert "No se pudo activar" in broken.locator(".np-error").inner_text()
        assert not broken.locator(".np-controls").is_visible()
        browser.close()
    print("OK: comparativa, territorios, teclado, zoom/arrastre, móvil/pinch, impresión y alternativas.")


if __name__ == "__main__":
    run()
