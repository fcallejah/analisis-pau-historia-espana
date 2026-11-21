"""Verify document deep links and sharing on the local site."""
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"


def verify_document_sharing():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": 375, "height": 812}, service_workers="block"
        )
        page = context.new_page()
        page.add_init_script("""Object.defineProperty(navigator, 'share', {
            configurable: true,
            value: undefined,
        });
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: {writeText: async (text) => { window.__copiedDocumentUrl = text; }},
        });""")
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")

        card = page.locator(".document-card:visible").first
        document_id = card.get_attribute("data-id")
        title = card.locator("h3").inner_text()
        card.locator(".document-open").click()
        page.wait_for_function("location.hash.startsWith('#documento=')")
        assert page.url.endswith(f"#documento={document_id}")

        share_button = page.get_by_role("button", name="Compartir documento")
        assert share_button.inner_text() == "Compartir"
        assert share_button.locator("svg path").count() == 2
        share_button.click()
        page.wait_for_function("window.__copiedDocumentUrl !== undefined")
        expected_url = page.evaluate("""identity => {
            const url = new URL('documentos.html', location.href);
            url.hash = `documento=${encodeURIComponent(identity)}`;
            return url.href;
        }""", document_id)
        assert page.evaluate("window.__copiedDocumentUrl") == expected_url
        toast = page.locator(".document-share-status")
        assert toast.inner_text() == "Enlace copiado al portapapeles."
        assert not toast.is_hidden()
        toast_box = toast.bounding_box()
        assert toast_box["x"] >= 0 and toast_box["x"] + toast_box["width"] <= 375
        page.wait_for_timeout(5200)
        assert toast.is_hidden()

        page.evaluate("""() => Object.defineProperty(navigator, 'share', {
            configurable: true,
            value: async (details) => { window.__sharedDocument = details; },
        })""")
        share_button.click()
        page.wait_for_function("window.__sharedDocument !== undefined")
        assert page.evaluate("window.__sharedDocument.url") == expected_url
        assert page.evaluate("window.__sharedDocument.title") == title

        page.locator(".document-close").click()
        page.wait_for_function("!document.querySelector('#document-dialog').open && !location.hash")
        page.locator(f'.document-card[data-id="{document_id}"] .document-open').click()
        page.evaluate("history.back()")
        page.wait_for_function("!document.querySelector('#document-dialog').open && !location.hash")
        page.evaluate("history.forward()")
        page.wait_for_function("document.querySelector('#document-dialog').open && location.hash")
        assert page.locator("#document-dialog-title").inner_text() == title

        page.evaluate("""identity => localStorage.setItem(
            'pau-he.documents.marks.v1',
            JSON.stringify({ [identity]: { favorite: true, review: false } }),
        )""", document_id)
        page.goto(f"{BASE}/mis-documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        page.locator(f'.document-card[data-id="{document_id}"] .document-open').click()
        personal_share_button = page.get_by_role("button", name="Compartir documento")
        assert personal_share_button.is_enabled()
        personal_share_button.click()
        page.wait_for_function("(expected) => window.__copiedDocumentUrl === expected", arg=expected_url)
        assert page.locator(".document-share-status").inner_text() == "Enlace copiado al portapapeles."
        page.locator(".document-close").click()
        context.close()

        direct_context = browser.new_context(service_workers="block")
        direct_page = direct_context.new_page()
        direct_page.goto(expected_url)
        direct_page.wait_for_function("document.querySelector('#document-dialog').open")
        assert direct_page.locator("#document-dialog-title").inner_text() == title
        direct_page.locator(".document-close").click()
        direct_page.wait_for_function("!document.querySelector('#document-dialog').open && !location.hash")
        direct_context.close()
        browser.close()


if __name__ == "__main__":
    verify_document_sharing()
    print("Document sharing links, native share, browser history and temporary toast verified.")
