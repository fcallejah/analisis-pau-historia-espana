"""Check local highlights, notes, Google Docs links and the ready video."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765"


def select_text(page, start=0, end=15):
    page.evaluate("""([start,end]) => {
        const parent = [...document.querySelectorAll('.reading-content > p')]
            .find(n => n.textContent.length > 100);
        parent.scrollIntoView({block:'center',behavior:'instant'});
        const nodes = [];
        const walker = document.createTreeWalker(parent, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) nodes.push(walker.currentNode);
        let offset = 0, first, last;
        for (const node of nodes) {
            if (!first && start < offset + node.length) first = [node,start-offset];
            if (!last && end <= offset + node.length) last = [node,end-offset];
            offset += node.length;
        }
        const range = document.createRange();
        range.setStart(...first); range.setEnd(...last);
        const selection = getSelection();
        selection.removeAllRanges(); selection.addRange(range);
    }""", [start, end])
    page.locator(".annotation-floating").wait_for()


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block")
        page = context.new_page()
        page.route("https://www.youtube-nocookie.com/**", lambda route: route.fulfill(body="<html>video</html>"))
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for block in range(1, 5):
            page.goto(f"{BASE}/apuntes/bloque-{block}.html")
            assert page.locator(".docs-button").count() == 1
            assert page.locator(".print-tools").first.locator(".docs-button").count() == 0
            assert page.locator(".print-tools").last.locator(".docs-button").count() == 1
            for link in page.locator(".docs-button").all():
                assert "docs.google.com/document/" in link.get_attribute("href")
                assert link.evaluate("n=>getComputedStyle(n).backgroundColor") == "rgb(214, 238, 122)"
            assert page.locator(".annotation-color").count() == 5
            assert not page.locator(".annotation-toolbar").is_visible()
        original = page.locator(".reading-content").text_content()
        assert page.locator(".example-practice .practice-status").count() == 0
        assert page.evaluate("""() => window.pauPracticeBank
            .filter(([, , block]) => block === 4)
            .every(([question, answer]) => !/Reales Fábricas|Despotismo Ilustrado|Motín de Esquilache|guerra de Sucesión española/.test(
                `${question} ${answer || ''}`))""")
        assert page.locator(".example-solution").count() == 18
        assert page.evaluate("""() => [...document.querySelectorAll('.example-solution')]
            .every(node => !/Reales Fábricas|Despotismo Ilustrado/.test(node.textContent))""")
        for i, color in enumerate(("amarillo", "verde", "azul", "rosa", "violeta")):
            select_text(page, i * 20, i * 20 + 15)
            page.get_by_role("button", name=f"Subrayar en {color}", exact=True).click()
            assert page.locator(f"mark.annotation-{color}").count() > 0
        assert page.locator(".reading-content").text_content() == original
        select_text(page, 150, 190)
        page.get_by_role("button", name="Añadir nota", exact=True).click()
        page.locator("#annotation-note").fill("Mi nota: <script>alert('no')</script>")
        page.get_by_role("button", name="Guardar nota", exact=True).click()
        assert page.locator("mark.annotation-with-note").count() > 0
        page.set_viewport_size({"width": 1440, "height": 900})
        page.locator(".annotation-preview").wait_for(state="visible")
        assert page.locator(".annotation-preview").text_content().startswith("Mi nota:")
        page.set_viewport_size({"width": 390, "height": 900})
        assert not page.locator(".annotation-preview").is_visible()
        page.set_viewport_size({"width": 1440, "height": 900})
        assert page.locator(".reading-content").text_content() == original
        page.evaluate("""() => {
            const key = 'pau-he.annotations.v1.4';
            const saved = JSON.parse(localStorage.getItem(key));
            saved.text = saved.text.toLocaleUpperCase('es');
            saved.records.forEach(record => record.quote = saved.text.slice(record.start, record.end));
            localStorage.setItem(key, JSON.stringify(saved));
        }""")
        page.reload()
        assert page.locator("mark.annotation-violeta").count() > 0
        page.evaluate("document.querySelector('.resume-dialog[open]')?.close()")
        assert "se han conservado" in page.locator(".annotation-status").text_content()
        page.locator("mark.annotation-with-note").first.click()
        assert page.locator("#annotation-note").input_value().startswith("Mi nota:")
        page.locator("#annotation-note").fill("Nota editada")
        page.get_by_role("button", name="Guardar nota", exact=True).click()
        page.locator("mark.annotation-with-note").first.click()
        assert page.locator("#annotation-note").input_value() == "Nota editada"
        page.get_by_role("button", name="Cerrar nota personal").click()
        assert not page.locator(".annotation-dialog").is_visible()
        page.locator(".annotation-manager summary").click()
        assert page.locator(".annotation-manager li").count() == 6
        assert page.locator(".annotation-manager .annotation-erase svg").count() == 6
        assert page.locator(".annotation-manager .annotation-erase").first.evaluate(
            "n=>getComputedStyle(n).backgroundColor") == "rgb(251, 228, 225)"
        page.locator(".annotation-manager li").first.get_by_role("button", name="Eliminar anotación:", exact=False).click()
        assert page.locator(".annotation-manager li").count() == 5
        page.locator("mark.annotation-azul").first.click()
        assert page.locator(".annotation-dialog").is_visible()
        assert page.locator(".annotation-dialog .annotation-erase svg").count() == 1
        page.get_by_role("button", name="Eliminar subrayado", exact=True).click()
        assert page.locator("mark.annotation-azul").count() == 0
        assert page.locator(".reading-content").text_content() == original
        page.reload()
        assert page.locator("mark.annotation-azul").count() == 0
        page.evaluate("document.querySelector('.resume-dialog[open]')?.close()")
        assert page.locator(".reading-video iframe").count() == 1
        assert page.locator(".reading-video-load").count() == 0
        assert page.locator(".reading-video iframe").get_attribute("src") == "https://www.youtube-nocookie.com/embed/sPzE-fm-V-Y"
        assert "autoplay" not in page.locator(".reading-video iframe").get_attribute("allow")
        assert page.locator(".reading-video").count() == 1
        assert page.locator('img[src*="bloque-4-08"]').count() == 0
        for width in (390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            select_text(page, 220, 250)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.locator(".annotation-floating").evaluate(
                """n=>{const r=n.getBoundingClientRect();
                    const rects=[...getSelection().getRangeAt(0).getClientRects()];
                    const anchor=rects[rects.length-1];
                    return r.left>=0&&r.right<=innerWidth&&r.height<=60
                        &&Math.abs(r.top-anchor.bottom-8)<2}"""
            )
        page.evaluate("getSelection().removeAllRanges()")
        page.locator(".annotation-toolbar").wait_for(state="hidden")
        page.goto(f"{BASE}/apuntes/bloque-3.html")
        assert page.locator("mark[data-annotation]").count() == 0
        assert not errors, errors
        blocked = browser.new_context(service_workers="block")
        blocked.add_init_script("Storage.prototype.setItem = () => { throw new Error('quota'); }")
        failure = blocked.new_page()
        failure.goto(f"{BASE}/apuntes/bloque-4.html")
        select_text(failure)
        failure.get_by_role("button", name="Subrayar en amarillo", exact=True).click()
        assert "No se pudieron guardar" in failure.locator(".annotation-status").text_content()
        assert failure.locator("mark[data-annotation]").count() == 0
        stale = browser.new_context(service_workers="block")
        stale.add_init_script("""if (!localStorage.getItem('pau-he.annotations.v1.4')) {
            localStorage.setItem('pau-he.annotations.v1.4',
                JSON.stringify({text:'otro texto',records:[]}));
        }""")
        older = stale.new_page()
        older.goto(f"{BASE}/apuntes/bloque-4.html")
        assert "Los apuntes han cambiado" not in older.locator(".annotation-status").text_content()
        assert older.evaluate("""JSON.parse(localStorage.getItem('pau-he.annotations.v1.4')).text""") == "otro texto"
        assert older.locator("mark[data-annotation]").count() == 0
        select_text(older)
        older.get_by_role("button", name="Subrayar en amarillo", exact=True).click()
        assert older.locator("mark.annotation-amarillo").count() > 0
        select_text(older, 30, 60)
        older.get_by_role("button", name="Añadir nota", exact=True).click()
        older.locator("#annotation-note").fill("Nota tras actualizar los apuntes")
        older.get_by_role("button", name="Guardar nota", exact=True).click()
        assert older.locator("mark.annotation-with-note").count() > 0
        assert older.evaluate("""() => Object.keys(localStorage)
            .filter(key => key.startsWith('pau-he.annotations.v1.4.archive.'))
            .some(key => JSON.parse(localStorage.getItem(key)).text === 'otro texto')""")
        older.reload()
        assert older.locator("mark.annotation-with-note").count() > 0
        assert older.locator("mark.annotation-amarillo").count() > 0
        browser.close()
    print("OK: cinco colores, notas, edición, persistencia, errores, enlaces y vídeo.")


if __name__ == "__main__":
    run()
