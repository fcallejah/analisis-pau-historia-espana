"""Run against the local server on port 8765."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"
DATA = json.loads((Path(__file__).resolve().parent.parent / "data/documentos.json").read_text())


def check_text_card(page):
    card = page.locator('.document-card[data-document-type="texto"]').first
    opener = card.locator(".document-open")
    assert card.locator("button, a, [tabindex]").count() == 1
    assert card.locator(".document-read-more").inner_text() == "… Leer más"
    assert card.locator(".document-read-more").get_attribute("aria-hidden") == "true"
    assert card.locator(".document-read-more span").evaluate(
        "(node) => getComputedStyle(node).textDecorationLine"
    ) == "underline"
    assert card.locator("blockquote").evaluate("(node) => node.scrollHeight > node.clientHeight")
    for selector in ("blockquote", ".document-kind", "h3", ".document-meta",
                     ".document-card-topics", ".document-read-more"):
        target = card.locator(selector)
        target.scroll_into_view_if_needed()
        bounds = target.bounding_box()
        page.mouse.click(bounds["x"] + bounds["width"] / 2,
                         bounds["y"] + bounds["height"] / 2)
        assert page.locator("#document-dialog").is_visible(), selector
        assert page.locator(".document-full-source blockquote p").count() == 6
        assert page.locator(".document-read-more").count() == page.locator(
            '.document-card[data-document-type="texto"]'
        ).count()
        page.keyboard.press("Escape")
        assert opener.evaluate("(button) => button === document.activeElement")
    opener.focus()
    page.keyboard.press("Enter")
    assert page.locator("#document-dialog").is_visible()
    page.keyboard.press("Escape")
    assert card.evaluate("(node) => getComputedStyle(node).outlineWidth") == "2px"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block", reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector(".document-card")
        assert page.locator(".document-card").count() == len(DATA["documents"])
        assert page.locator("#document-block option").evaluate_all("(options) => options.map(option => option.value)") == ["", "5", "6", "7", "8", "9", "10", "11", "12"]
        page.locator('[data-type="imagen"]').click()
        assert page.locator(".document-card").count() == 2
        page.locator("#document-search").fill("GOYA")
        assert page.locator(".document-card").count() == 1
        opener = page.locator(".document-open")
        opener.click()
        assert page.locator("#document-dialog").is_visible()
        assert page.locator(".document-task").inner_text().count("De 0 a 2 puntos.") == 2
        assert "a) Analice el hecho histórico" in page.locator(".document-task").inner_text()
        assert "b) Explique el contexto histórico" in page.locator(".document-task").inner_text()
        page.locator(".document-zoom").click()
        assert page.locator(".document-full-source").get_attribute("class").endswith("is-zoomed")
        assert not page.locator(".document-guide").get_attribute("open")
        page.locator(".document-guide summary").click()
        assert page.locator(".document-guide h3").count() == 2
        assert page.locator(".document-guide h3").first.inner_text().startswith("a) ")
        assert page.locator(".document-guide h3").nth(1).inner_text().startswith("b) ")
        assert page.locator(".document-appearances li").count() == 1
        page.keyboard.press("Escape")
        assert not page.locator("#document-dialog").is_visible()
        assert opener.evaluate("(button) => button === document.activeElement")
        page.locator("#document-reset").click()
        page.locator("#document-search").fill("constitucion")
        assert page.locator(".document-card").count() == 5
        page.locator("#document-search").fill("")
        page.get_by_role("button", name="Representación política (1)", exact=True).click()
        assert page.locator(".document-card").count() == 1
        page.locator(".document-open").click()
        assert page.locator(".document-full-source tbody tr").count() == 13
        assert page.locator(".document-full-source tbody tr").first.inner_text() == "Eclesiásticos\t90"
        page.locator(".document-close").click()
        page.locator("#document-reset").click()
        page.select_option("#document-block", "10")
        page.locator(".document-open").click()
        paragraphs = page.locator(".document-full-source blockquote p").all_text_contents()
        assert "trabajadores de toda clase, que se organiza" in paragraphs[0]
        assert paragraphs[1] == "Los poderes de todos sus órganos emanan del pueblo."
        assert paragraphs[4] == "Artículo 2. Todos los españoles son iguales ante la ley."
        assert paragraphs[-1].endswith("legítima del Estado […].")
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "12")
        assert page.locator(".document-card").count() == 2
        page.get_by_role("button", name="Ver documento: El preámbulo de la Constitución de 1978", exact=True).click()
        paragraphs = page.locator(".document-full-source blockquote p").all_text_contents()
        assert "orden económico y social justo." in paragraphs[3]
        assert paragraphs[-1].endswith("pueblos de la Tierra.")
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "11")
        assert page.locator(".document-card").count() == 0
        assert page.locator("#document-empty").is_visible()
        page.locator("#document-reset").click()
        page.locator('[data-type="texto"]').click()
        for width in (320, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            check_text_card(page)
        page.locator(".document-open").first.click()
        assert page.locator(".document-full-source blockquote p").count() == 6
        page.locator(".document-close").click()
        page.goto(f"{BASE}/documentos.html?bloque=5")
        page.wait_for_selector(".document-card")
        assert page.locator("#document-block").input_value() == "5"
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        for width in (320, 375, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
            check_text_card(page)
            page.locator(".document-open").first.click()
            assert page.locator("#document-dialog").evaluate("(el) => el.scrollWidth <= el.clientWidth"), width
            page.locator(".document-close").click()
        assert not errors, errors
        context.close()

        # A document with several appearances remains one searchable card.
        multi = json.loads(json.dumps(DATA))
        multi["documents"][0]["appearances"].append({
            **multi["documents"][0]["appearances"][0], "id": "test-extra-appearance",
        })
        multi["documents"][0]["blocks"].append(6)
        multi_context = browser.new_context(service_workers="block")
        multi_page = multi_context.new_page()
        multi_page.route("**/data/documentos.json", lambda route: route.fulfill(json=multi))
        multi_page.goto(f"{BASE}/documentos.html")
        multi_page.wait_for_selector(".document-card")
        assert multi_page.locator(".document-card").count() == len(DATA["documents"])
        assert f"{len(DATA['documents']) + 1} apariciones" in multi_page.locator("#document-count").inner_text()
        multi_page.locator(".document-open").first.click()
        assert multi_page.locator(".document-appearances li").count() == 2
        multi_page.locator(".document-close").click()
        multi_page.select_option("#document-block", "6")
        assert multi_page.locator(".document-card").count() == 1
        assert multi_page.locator(".document-block-heading h2").inner_text().startswith("Bloque 6,")
        multi_context.close()

        failed = browser.new_context(service_workers="block")
        failed_page = failed.new_page()
        failed_page.route("**/data/documentos.json", lambda route: route.fulfill(status=503, body="Unavailable"))
        failed_page.goto(f"{BASE}/documentos.html")
        failed_page.locator("#document-error").wait_for(state="visible")
        assert "503" in failed_page.locator("#document-error").inner_text()
        assert failed_page.locator("#document-retry").is_visible()
        failed_page.unroute("**/data/documentos.json")
        failed_page.locator("#document-retry").click()
        failed_page.wait_for_selector(".document-card")
        assert not failed_page.locator("#document-error").is_visible()
        invalid = json.loads(json.dumps(DATA))
        invalid["documents"][0]["blocks"] = [4]
        failed_page.route("**/data/documentos.json", lambda route: route.fulfill(json=invalid))
        failed_page.reload()
        failed_page.locator("#document-error").wait_for(state="visible")
        assert "bloques 5–12" in failed_page.locator("#document-error").inner_text()
        assert failed_page.locator(".document-card").count() == 0
        failed.close()

        offline = browser.new_context()
        offline_page = offline.new_page()
        offline_page.goto(f"{BASE}/index.html")
        offline_page.evaluate("async () => { await navigator.serviceWorker.ready; }")
        offline_page.wait_for_function("navigator.serviceWorker.controller !== null")
        offline.set_offline(True)
        offline_page.goto(f"{BASE}/documentos.html")
        offline_page.wait_for_selector(".document-card")
        assert offline_page.locator(".document-card").count() == len(DATA["documents"])
        offline_page.locator(".document-preview img").evaluate_all("(images) => images.forEach(image => image.loading = 'eager')")
        offline_page.wait_for_function("Array.from(document.querySelectorAll('.document-preview img')).every(image => image.complete && image.naturalWidth > 0)")
        offline.close()
        browser.close()
    print("OK: banco por tipos, bloques 5–12, temáticas, búsqueda, a)/b), ampliación, apariciones, errores y sin conexión.")


if __name__ == "__main__":
    run()
