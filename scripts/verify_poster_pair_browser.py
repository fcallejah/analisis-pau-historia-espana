"""Verify the 2016 posters remain proportional and equally tall."""
from playwright.sync_api import sync_playwright


URL = "http://localhost:8765/documentos.html#documento=carteles-guerra-civil-2016"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    for width, height in [(320, 700), (375, 812), (620, 800), (621, 800), (960, 800), (1440, 1000)]:
        page.set_viewport_size({"width": width, "height": height})
        page.goto(URL)
        images = page.locator("#document-dialog .document-equal-height-pair img")
        images.first.wait_for(state="visible")
        page.wait_for_function("""() => [...document.querySelectorAll(
            '#document-dialog .document-equal-height-pair img'
        )].length === 2 && [...document.querySelectorAll(
            '#document-dialog .document-equal-height-pair img'
        )].every(img => img.complete && img.naturalWidth)""")
        dimensions = images.evaluate_all("""images => images.map(img => {
            const rect = img.getBoundingClientRect();
            return {width: rect.width, height: rect.height, ratio: img.naturalWidth / img.naturalHeight};
        })""")
        assert abs(dimensions[0]["height"] - dimensions[1]["height"]) < 1, (width, dimensions)
        for image in dimensions:
            assert abs(image["width"] / image["height"] - image["ratio"]) < 0.001, (width, image)
        assert page.locator("#document-dialog .document-full-source").evaluate(
            "node => node.scrollWidth <= node.clientWidth"
        ), width
    browser.close()

print("OK: carteles proporcionales y de igual altura en escritorio y móvil.")
