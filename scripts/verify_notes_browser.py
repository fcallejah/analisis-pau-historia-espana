"""Browser regression checks; run against the local server on port 8765."""
import re
import unicodedata
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765"


def key(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if c.isalnum())


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        counts = []
        related_counts = []
        for block, total in ((1, 15), (2, 12), (3, 14), (4, 18)):
            page.goto(f"{BASE}/apuntes/bloque-{block}.html", wait_until="domcontentloaded")
            page.wait_for_selector(".example-solution", state="attached")
            page.wait_for_function("document.querySelector('.reading-content').dataset.relatedPractice === 'ready'")
            bank = page.evaluate("window.pauPracticeBank")
            if block == 4:
                assert all(points for _, points, number in bank if number == 4)
                mixed = next(points for prompt, points, number in bank if number == 4
                             and "decretos" in prompt.lower()
                             and "causas de la guerra de sucesión" in prompt)
                assert "Nueva Planta" in mixed and "Carlos II" in mixed
            examples = page.locator(".example-solution")
            assert examples.count() == total
            section = page.locator(".example-practice")
            assert section.count() == 1
            assert section.locator(".example-solution").count() == total
            if block != 4:
                assert "líneas cada una" in section.inner_text()
            else:
                assert page.locator(".reading-index a").count() == 10
                assert page.locator(".footnotes .footnote-back").count() == 20
                assert page.locator(".reading-content .doc-image img").count() == 5
                assert page.locator(".pending").count() == 0
                assert page.locator("#nueva-planta").count() == 1
                assert page.locator("#organizacion-borbonica").count() == 1
            assert "linear-gradient" in section.evaluate("n => getComputedStyle(n).backgroundImage")
            mapped = 0
            for index in range(total):
                details = examples.nth(index)
                prompt = details.evaluate("(n) => n.previousElementSibling.textContent")
                prompt = re.sub(r"^\s*\d+\.\s*", "", prompt)
                prompt = re.sub(r"\s*\(PAU\s+\d{4}(?:\s*(?:y|,|-)\s*\d{4})*\)\s*$", "", prompt)
                answers = {points for question, points, number in bank
                           if number == block and key(question) == key(prompt) and points}
                expected = next(iter(answers)) if len(answers) == 1 else None
                assert details.locator("summary").inner_text() == "Posible solución"
                if expected:
                    mapped += 1
                    assert details.locator("p").text_content() == "Debe incluir: " + re.sub(r"\.?$", ".", expected, count=1)
                    assert details.locator("strong").text_content() == "Debe incluir: "
                else:
                    assert details.get_attribute("data-solution-state") == "document", prompt
                    assert "Debe incluir" in details.locator("p").text_content(), prompt
                assert details.evaluate("""n => {
                    let next = n.nextElementSibling;
                    while (next?.matches('p') && !next.textContent.trim()) next = next.nextElementSibling;
                    return !next?.textContent.trim().startsWith('(Debe incluir');
                }""")
                assert details.get_attribute("open") is None
                assert not details.locator("p").is_visible()
                details.locator("summary").click()
                assert details.locator("p").is_visible()
                details.locator("summary").click()
            counts.append((block, mapped, total - mapped))
            if block == 4:
                assert mapped == 18
            related_mapped = 0
            related_pending = 0
            for item in page.locator(".related-question").all():
                prompt = item.locator(".related-question-text").inner_text()
                sub = item.locator(".related-question-sub")
                full = prompt + " " + (sub.inner_text() if sub.count() else "")
                answers = {points for question, points, number in bank
                           if number == block and key(question) == key(full) and points}
                expected = next(iter(answers)) if len(answers) == 1 else None
                answer = item.locator(".gen-sol p").text_content()
                if expected:
                    related_mapped += 1
                    assert answer == "Debe incluir: " + re.sub(r"\.?$", ".", expected, count=1)
                else:
                    related_pending += 1
                    assert "Solución pendiente" in answer
                assert item.locator("a").get_attribute("href").startswith("https://docs.google.com/")
            related_counts.append((block, related_mapped, related_pending))
            first = examples.first
            first.locator("summary").click()
            assert first.locator("p").is_visible()
            first.locator("summary").click()
            assert not first.locator("p").is_visible()
            page.evaluate("setupExampleSolutions(); setupRelatedPractice(); setupFootnotes()")
            assert examples.count() == total
            assert page.locator(".footnote-bubble").count() == 1
            assert page.evaluate("""async () => {
                const source = new DOMParser().parseFromString(await (await fetch(location.href)).text(), 'text/html');
                source.querySelectorAll('.np-map,.ob-chart').forEach(n => n.remove());
                const heading = [...source.querySelectorAll('h2,h3,h4,h5')].find(n => /ejemplos de preguntas/i.test(n.textContent));
                for (let node = heading.nextElementSibling; node && !node.matches('.footnotes');) {
                    const next = node.nextElementSibling;
                    if (node.matches('p') && /^\\(?\\s*Debe incluir(?:\\s*\\/\\s*Pistas)?\\s*:/i.test(node.textContent.trim())) node.remove();
                    node = next;
                }
                const copy = document.querySelector('.reading-content').cloneNode(true);
                copy.querySelectorAll('.np-map,.ob-chart').forEach(n => n.remove());
                copy.querySelectorAll('.gen-sol,.practice-status,.related-practice').forEach(n => n.remove());
                return copy.textContent === source.querySelector('.reading-content').textContent;
            }""")
            assert page.locator("#generador").count() == 0
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector(".example-solution", state="attached")
            assert examples.count() == total

        page.goto(f"{BASE}/apuntes/bloque-4.html", wait_until="domcontentloaded")
        page.set_viewport_size({"width": 375, "height": 667})
        citation = page.locator("#ftnt_ref3")
        citation.click()
        bubble = page.locator(".footnote-bubble")
        assert "La RAE reconoce tanto Rastadt como Rastatt" in bubble.inner_text()
        assert bubble.locator('a[href="https://x.com/RAEinforma/status/2120114348014084251"]').count() == 1
        bubble.locator(".footnote-close").click()
        long_note = page.locator("#ftnt_ref4")
        long_note.click()
        # A long citation must be readable regardless of the space near its reference.
        page.evaluate("""() => {
            const body=document.querySelector('.footnote-dialog-body');
            body.append(document.createTextNode(' Texto de prueba largo.'.repeat(100)));
        }""")
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        more = bubble.get_by_role("button", name="Leer completa")
        assert more.is_visible()
        assert bubble.evaluate("n=>n.classList.contains('has-more')")
        more.click()
        assert bubble.get_attribute("data-expanded") == "true"
        assert not more.is_visible()
        bounds = bubble.bounding_box()
        assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= 375
        assert bounds["y"] >= 0 and bounds["y"] + bounds["height"] <= 667
        body = bubble.locator(".footnote-dialog-body")
        body.evaluate("n=>n.scrollTop=n.scrollHeight")
        assert body.evaluate("n=>n.scrollTop+n.clientHeight>=n.scrollHeight-1")
        page.keyboard.press("Escape")
        assert not bubble.is_visible()
        assert long_note.evaluate("n=>n===document.activeElement")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
        page.locator('[data-gen="4"]').click()
        assert page.locator("#gen-output .gen-sol").count() == 4
        assert "pendiente" not in page.locator("#gen-output").inner_text().lower()
        page.locator("#gen-reset").click()
        page.locator(".gen-delete").click()
        page.locator('[data-gen="1"]').click()
        assert page.locator("#gen-output .gen-sol").count() == 4
        assert page.evaluate("""() => [...document.querySelectorAll('#gen-output .gen-q')].every(n => {
            const prompt = n.querySelector('.gen-text').textContent.replace(/^\\d+\\.\\s*/, '');
            return n.querySelector('.gen-sol').outerHTML === pauPractice.render(pauPractice.find(prompt, '', 1)).outerHTML;
        })""")
        generator_style = page.locator(".gen-sol summary").first.evaluate("""n => {
            const s = getComputedStyle(n); return [s.padding,s.borderRadius,s.font,s.borderColor];
        }""")
        page.goto(f"{BASE}/apuntes/bloque-1.html", wait_until="domcontentloaded")
        page.wait_for_selector(".example-solution", state="attached")
        assert generator_style == page.locator(".example-solution summary").first.evaluate("""n => {
            const s = getComputedStyle(n); return [s.padding,s.borderRadius,s.font,s.borderColor];
        }""")
        assert page.evaluate("""() => {
            const [question,,block] = pauPracticeBank.find(([,points]) => points);
            return pauPractice.find(question, 'Subpregunta que no existe', block) === null
                && pauPractice.find(question, '', 99) === null;
        }""")
        page.locator("#reading-search").fill("Solución pendiente")
        assert page.locator("#reading-search-results li").count() == 0
        page.locator("#reading-search-clear").click()

        for viewport in ({"width": 1280, "height": 900}, {"width": 375, "height": 667}):
            page.set_viewport_size(viewport)
            for top in (80, viewport["height"] // 2, viewport["height"] - 45):
                reference = page.locator(".footnote-ref").nth(2)
                reference.evaluate("""(n, top) => {
                    document.documentElement.style.scrollBehavior = 'auto';
                    window.scrollTo(0, window.scrollY + n.getBoundingClientRect().top - top);
                }""", top)
                before = page.evaluate("window.scrollY")
                reference.click()
                bubble = page.locator(".footnote-bubble")
                assert bubble.is_visible()
                assert page.evaluate("window.scrollY") == before
                bounds = bubble.bounding_box()
                ref_bounds = reference.bounding_box()
                assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= viewport["width"]
                assert bounds["y"] >= 0 and bounds["y"] + bounds["height"] <= viewport["height"]
                if bubble.get_attribute("data-side") == "below":
                    assert bounds["y"] >= ref_bounds["y"] + ref_bounds["height"]
                else:
                    assert bounds["y"] + bounds["height"] <= ref_bounds["y"]
                assert len(bubble.locator(".footnote-dialog-body").inner_text()) > 10
                assert not page.evaluate("!!document.querySelector('dialog:modal')")
                bubble.locator(".footnote-close").click()
                assert not bubble.is_visible()
                assert page.evaluate("window.scrollY") == before
                assert reference.evaluate("(n) => n === document.activeElement")
                reference.click()
                page.keyboard.press("Escape")
                assert not bubble.is_visible()
                assert page.evaluate("window.scrollY") == before
                assert reference.evaluate("(n) => n === document.activeElement")
                reference.click()
                page.locator(".reading-header").dispatch_event("click")
                assert not bubble.is_visible()
                assert page.evaluate("window.scrollY") == before
        linked_note = page.evaluate("""() => {
            const link = document.querySelector('.footnotes a[href^="http"]');
            const note = link?.closest('div');
            return note?.querySelector('.footnote-back')?.id;
        }""")
        assert linked_note
        linked_reference = page.locator(f'a.footnote-ref[href="#{linked_note}"]').first
        linked_reference.scroll_into_view_if_needed()
        linked_reference.click()
        source_links = page.locator(f'#{linked_note}').evaluate("""n =>
            [...n.parentElement.parentElement.querySelectorAll('a[href^="http"]')].map(a=>[a.textContent,a.href])
        """)
        cloned_links = page.locator(".footnote-bubble").evaluate("""n =>
            [...n.querySelectorAll('a[href^="http"]')].map(a=>[a.textContent,a.href])
        """)
        assert source_links == cloned_links
        page.keyboard.press("Escape")
        page.emulate_media(media="print")
        assert not page.locator(".example-solution").first.is_visible()
        assert page.locator(".footnotes").is_visible()
        page.emulate_media(media="screen")
        page.route("**/data/preguntas-cortas.json", lambda route: route.fulfill(status=503, body="Unavailable"))
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector(".practice-status[role=alert]")
        assert "práctica relacionada" in page.locator(".practice-status[role=alert]").inner_text()
        assert page.locator(".example-solution").count() == 15
        page.unroute("**/data/preguntas-cortas.json")
        page.route("**/generador.js*", lambda route: route.abort())
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector(".practice-status[role=alert]")
        assert "banco de soluciones" in page.locator(".practice-status[role=alert]").inner_text()
        assert not errors, errors
        context.close()
        native = browser.new_context(java_script_enabled=False, service_workers="block")
        native_page = native.new_page()
        native_page.goto(f"{BASE}/apuntes/bloque-1.html", wait_until="domcontentloaded")
        assert native_page.locator(".footnote-ref").first.get_attribute("href").startswith("#ftnt")
        assert native_page.locator(".footnotes").is_visible()
        assert native_page.locator(".footnote-bubble").count() == 0
        native.close()
        browser.close()
        print("Ejemplos (bloque, con solución, pendientes):", counts)
        print("Práctica relacionada (bloque, con solución, pendientes):", related_counts)
        print("OK: respuestas exactas, controles compartidos, reimportación/reinicio, errores y bocadillos.")


if __name__ == "__main__":
    run()
