"""Check the political comparison against the local server on port 8765."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/apuntes/bloque-4.html"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(service_workers="block")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL)
        assert page.locator("#ob-before").is_visible()
        assert not page.locator("#ob-after").is_visible()
        assert page.locator(".ob-view p").count() == 0
        assert page.locator(".ob-view details").count() == page.locator(".ob-view details > ul").count()
        councils = page.locator("#ob-before details").first.locator("li").all_text_contents()
        assert len(councils) == 14
        for name in ("Consejo de Castilla", "Consejo de Aragón", "Consejo Real de Navarra",
                     "Consejo de Indias", "Consejo de Italia", "Consejo de Flandes y de Borgoña",
                     "Consejo de Portugal", "Consejo de Estado", "Consejo de Guerra",
                     "Consejo de Hacienda", "Consejo de la Suprema y General Inquisición",
                     "Consejo de Órdenes", "Consejo de Cruzada", "Cámara de Castilla"):
            assert name in councils
        assert page.locator("#ob-before .ob-sovereign").evaluate(
            "n=>getComputedStyle(n).backgroundColor"
        ) == "rgb(75, 46, 131)"
        for mode in ("after", "before", "after"):
            button = page.locator(f'[data-ob-mode="{mode}"]')
            button.click()
            assert button.get_attribute("aria-pressed") == "true"
            assert page.locator(f"#ob-{mode}").is_visible()
            assert page.locator(f"#ob-{mode} .ob-info").count() == page.locator(f"#ob-{mode} details").count()
            for info in page.locator(f"#ob-{mode} .ob-info").all():
                detail = info.locator("..").locator("details")
                was_open = detail.get_attribute("open")
                info.click()
                assert page.locator(".footnote-bubble").is_visible()
                assert detail.get_attribute("open") == was_open
                assert page.locator(".footnote-dialog-body a").get_attribute("href").startswith(
                    f"bloque-{3 if mode == 'before' else 4}.html"
                )
                page.locator(".footnote-close").click()
                assert not page.locator(".footnote-bubble").is_visible()
                assert info.evaluate("n=>n===document.activeElement")
            for detail in page.locator(f"#ob-{mode} details").all():
                detail.locator("summary").focus()
                page.keyboard.press("Enter")
                assert detail.get_attribute("open") is not None
                page.keyboard.press("Enter")
                assert detail.get_attribute("open") is None
        assert page.locator("#ob-after .ob-sovereign").evaluate(
            "n=>getComputedStyle(n).backgroundColor"
        ) == "rgb(214, 238, 122)"
        assert "1787" in page.locator("#ob-after").text_content()
        assert "Nueva España" in page.locator("#ob-after").text_content()
        assert "Río de la Plata" in page.locator("#ob-after").text_content()
        page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
        assert page.locator("#ob-after details:not([open])").count() == 0
        page.evaluate("window.dispatchEvent(new Event('afterprint'))")
        assert page.locator("#ob-after details[open]").count() == 0
        for width in (390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.locator("#ob-after .ob-branches").evaluate(
                "n=>getComputedStyle(n).gridTemplateColumns.split(' ').length"
            ) == (1 if width == 390 else 2)
        assert not errors, errors
        fallback = browser.new_page(java_script_enabled=False)
        fallback.goto(URL)
        assert fallback.locator("#ob-before").is_visible()
        assert fallback.locator("#ob-after").is_visible()
        fallback.locator("#ob-after summary").first.click()
        assert fallback.locator("#ob-after details[open]").count() == 1
        offline = browser.new_context()
        cached = offline.new_page()
        cached.goto(URL)
        cached.evaluate("navigator.serviceWorker.register('../sw.js')")
        cached.evaluate("navigator.serviceWorker.ready")
        cached.wait_for_function("navigator.serviceWorker.controller !== null")
        offline.set_offline(True)
        cached.reload()
        cached.locator('[data-ob-mode="after"]').click()
        assert cached.locator("#ob-after").is_visible()
        assert cached.locator("#ob-after .ob-branches").evaluate(
            "n=>getComputedStyle(n).display"
        ) == "grid"
        browser.close()
    print("OK: comparación, teclado, móvil, impresión, sin JavaScript y offline.")


if __name__ == "__main__":
    run()
