"""Verify the redrawn map and real mouse selection inside its SVG document."""
from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:8765"


def select_label(page, selector, expected):
    svg = page.locator(".document-selectable-map")
    svg.evaluate("""(object, selector) => {
        const label = object.contentDocument.querySelector(selector);
        const dialog = object.closest('dialog');
        dialog.scrollTop += object.getBoundingClientRect().top
            + label.getBoundingClientRect().y - dialog.getBoundingClientRect().top - 180;
    }""", selector)
    bounds = svg.evaluate("""(object, selector) => {
        const frame = object.getBoundingClientRect();
        const label = object.contentDocument.querySelector(selector).getBoundingClientRect();
        return {x: frame.x + label.x, y: frame.y + label.y,
            width: label.width, height: label.height};
    }""", selector)
    page.mouse.move(bounds["x"] + 1, bounds["y"] + bounds["height"] / 2)
    page.mouse.down()
    page.mouse.move(bounds["x"] + bounds["width"] - 1,
                    bounds["y"] + bounds["height"] / 2, steps=25)
    page.mouse.up()
    assert svg.evaluate("o => o.contentDocument.defaultView.getSelection().toString()") == expected


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block", reduced_motion="reduce",
                                      viewport={"width": 1280, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/documentos.html?bloque=8")
        page.locator('.document-card[data-id="mapa-desamortizacion-madoz"] .document-open').click()
        page.wait_for_function(
            "document.querySelector('.document-selectable-map')?.contentDocument?.querySelector('#map-legend')"
        )
        svg = page.locator(".document-selectable-map")
        assert page.locator(".document-reproduction-note").count() == 0
        assert page.get_by_role("link", name="Créditos del mapa", exact=True).get_attribute("href") == "creditos-mapa.html"
        assert svg.evaluate("""object => {
            const doc = object.contentDocument;
            const background = doc.defaultView.getComputedStyle(doc.querySelector('svg > rect')).fill;
            return background === 'rgb(255, 255, 255)' && ['polygon6', 'polygon8'].every(id =>
                doc.defaultView.getComputedStyle(doc.getElementById(id)).fill === background);
        }""")
        assert svg.get_attribute("type") == "image/svg+xml"
        assert svg.evaluate("o => o.contentDocument.querySelectorAll('#map-legend rect').length") == 8
        layout = svg.evaluate("""object => {
            const svg = object.contentDocument.documentElement;
            const legend = svg.querySelector('#map-legend');
            const columns = new Map();
            legend.querySelectorAll('rect').forEach(rect => {
                const x = rect.x.baseVal.value;
                if (!columns.has(x)) columns.set(x, []);
                columns.get(x).push(rect.dataset.category);
            });
            return {
                columns: [...columns.entries()].sort((a,b) => a[0]-b[0]).map(([,categories]) => categories),
                contained: [...legend.querySelectorAll('text')].every(label => {
                    const box = label.getBBox();
                    return box.x >= 0 && box.x + box.width <= svg.viewBox.baseVal.width;
                }),
            };
        }""")
        assert layout["columns"] == [["70", "50", "40"], ["30", "10", "5"], ["1", "none"]], layout
        assert layout["contained"], layout
        assert svg.evaluate("o => o.contentDocument.querySelectorAll('#province-labels text').length") == 52
        select_label(page, "#map-legend text", "70 millones de reales")
        select_label(page, "#province-labels text:nth-child(42)", "Sevilla")
        for width in (320, 768, 1280):
            page.set_viewport_size({"width": width, "height": 1000})
            page.locator(".document-zoom").scroll_into_view_if_needed()
            geometry = svg.evaluate("""object => {
                const bounds = object.getBoundingClientRect();
                const frame = object.closest('.document-full-source').getBoundingClientRect();
                return {width:bounds.width,height:bounds.height,
                    contained:bounds.left>=frame.left && bounds.right<=frame.right};
            }""")
            assert geometry["contained"], (width, geometry)
            assert abs(geometry["height"] / geometry["width"] - 1160 / 1288) < .01
            page.locator(".document-zoom").click()
            assert svg.evaluate("o => o.getBoundingClientRect().width") == 1288
            page.locator(".document-zoom").click()
        page.locator(".document-zoom").click()
        page.locator(".document-table-details summary").click()
        page.locator(".document-full-source").evaluate("node => node.scrollLeft = 160")
        page.locator("#document-dialog").evaluate("node => node.scrollTop = 470")
        page.wait_for_timeout(100)
        saved = page.evaluate("JSON.parse(sessionStorage.getItem('pau-he.documents.view.v1'))")
        assert saved["dialog"]["source"]["left"] == 160
        page.reload()
        page.wait_for_selector('#document-grid[aria-busy="false"]', state="attached")
        svg = page.locator(".document-selectable-map")
        page.wait_for_function(
            "document.querySelector('.document-selectable-map')?.contentDocument?.querySelector('#map-legend')"
        )
        assert page.locator(".document-table-details").evaluate("node => node.open")
        assert svg.evaluate("o => o.getBoundingClientRect().width") == 1288
        assert page.locator(".document-full-source").evaluate("node => node.scrollLeft") == saved["dialog"]["source"]["left"]
        assert abs(page.locator("#document-dialog").evaluate("node => node.scrollTop")
                   - saved["dialog"]["position"]["top"]) < 2
        assert not errors, errors
        offline = browser.new_context(reduced_motion="reduce")
        offline_page = offline.new_page()
        offline_page.goto(f"{BASE}/index.html")
        offline_page.evaluate("async () => { await navigator.serviceWorker.ready; }")
        offline_page.wait_for_function("navigator.serviceWorker.controller !== null")
        offline.set_offline(True)
        offline_page.goto(f"{BASE}/documentos.html?bloque=8")
        offline_page.locator('.document-card[data-id="mapa-desamortizacion-madoz"] .document-open').click()
        offline_page.wait_for_function(
            "document.querySelector('.document-selectable-map')?.contentDocument?.querySelector('#map-legend')"
        )
        select_label(offline_page, "#map-legend text", "70 millones de reales")
        offline.close()
        browser.close()
    print("OK: mapa limpio, ocho categorías y selección real de leyenda y provincia.")


if __name__ == "__main__":
    run()
