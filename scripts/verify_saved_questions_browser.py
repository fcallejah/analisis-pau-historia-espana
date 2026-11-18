"""Verify independent personal question lists on the local server."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765"


def check_exam_pills(browser):
    with browser.new_context(service_workers="block") as context:
        page = context.new_page()
        page.add_init_script("Math.random = () => 0.5")
        page.goto(BASE, wait_until="domcontentloaded")
        page.locator(".block").first.locator("summary").first.click()
        linked = page.locator(".question-list a.exam-pill")
        sources = dict(linked.evaluate_all("nodes => nodes.map(n => [n.textContent, n.href])"))
        assert sources["2017 · Titular extraordinaria"].startswith("https://drive.google.com/file/d/")
        assert page.locator(".question-list span.exam-pill").count() == 0
        zip_sources = {label: href for label, href in sources.items() if label.endswith(" (ZIP)")}
        assert len(zip_sources) == 6
        assert all(href.endswith("/sel_2024_historia_espana.zip") for href in zip_sources.values())
        agriculture = page.locator(".question-list li").filter(has_text="impulsó reformas en la agricultura")
        reserva = agriculture.locator('a.exam-pill').filter(has_text="2024 · Reserva A (ZIP)")
        assert "Examen_Reserva-A_HISTORIA DE ESPAÑA.pdf" in reserva.get_attribute("title")
        page.locator('[data-gen="1"]').click()
        generated = page.locator('#gen-output a.exam-pill:not([title*="del modelo"])')
        assert generated.count() > 0
        assert all(sources[label] == href and target == ("" if label in zip_sources else "_blank")
                   for label, href, target in
                   generated.evaluate_all("nodes => nodes.map(n => [n.textContent, n.href, n.target])"))


def check_model_questions(browser):
    with browser.new_context(service_workers="block") as context:
        page = context.new_page()
        page.add_init_script("""let seed = 42;
            Math.random = () => ((seed = (1664525 * seed + 1013904223) >>> 0) / 4294967296);
        """)
        page.goto(BASE, wait_until="domcontentloaded")
        observed = page.evaluate("""() => {
            const result = {};
            for (const block of [1, 2, 3, 4]) {
                const button = document.querySelector(`[data-gen="${block}"]`);
                for (let attempt = 0; attempt < 30; attempt++) {
                    button.click();
                    document.querySelectorAll('#gen-output a[title*="del modelo"]').forEach(link => {
                        const prompt = link.closest('.gen-q').querySelector('.gen-text').textContent.replace(/^\\d+\\. /, '');
                        result[`${block}:${prompt}:${link.textContent}`] = link.href;
                    });
                    const dialog = document.querySelector('#gen-dialog');
                    dialog.returnValue = 'delete';
                    dialog.dispatchEvent(new Event('close'));
                }
            }
            return result;
        }""")
        assert {key.split(":")[-1][:4] for key in observed} == {
            "2017", "2018", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
        }
        assert len({key.rsplit(":", 1)[0] for key in observed}) == 11
        assert all(href.startswith("https://drive.google.com/file/d/") for href in observed.values())
        page.locator('[data-gen="random"]').click()
        assert [text.split()[1] for text in page.locator("#gen-output .gen-q small").all_text_contents()] == [
            "1", "2", "3", "4",
        ]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        check_exam_pills(browser)
        check_model_questions(browser)
        context = browser.new_context(service_workers="block")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE)
        page.locator(".block").first.locator("summary").first.click()
        question = page.locator(".question-list li").first
        question.locator(".question-marks").get_by_role("button", name="Favorita", exact=True).click()
        particle = page.locator(".favorite-particle")
        assert particle.count() == 1
        assert particle.evaluate("n=>getComputedStyle(n).animationDuration") == "0.7s"
        assert particle.locator("svg").evaluate("n=>getComputedStyle(n).fill") == "none"
        assert particle.evaluate("""n => {
            const frames = n.getAnimations()[0].effect.getKeyframes();
            return frames[0].opacity === '1' && frames.at(-1).opacity === '0'
                && frames[0].transform === 'translateY(-110%)' && frames.at(-1).transform === 'translateY(-270%)'
                && n.parentElement.matches('button');
        }""")
        particle.wait_for(state="detached")
        review = question.locator(".question-marks").get_by_role("button", name="Necesito repasar", exact=True)
        assert review.evaluate("n=>getComputedStyle(n).backgroundColor") == "rgb(255, 255, 255)"
        review.click()
        assert review.evaluate("n=>getComputedStyle(n).backgroundColor") == "rgb(214, 238, 122)"
        assert page.locator(".review-particle svg").count() == 1
        assert page.locator(".review-particle").evaluate("""n => {
            const icon = document.querySelector('.question-mark-review[aria-pressed=true] svg').getBoundingClientRect();
            const r = n.getBoundingClientRect();
            return Math.abs(r.left + r.width / 2 - icon.left - icon.width / 2) < 1
                && (icon.top + icon.height / 2 - r.top - r.height / 2) / icon.height >= 1.09
                && (icon.top + icon.height / 2 - r.top - r.height / 2) / icon.height <= 2.71;
        }""")
        page.locator(".review-particle").wait_for(state="detached")
        prompt = question.locator("p").first.inner_text().replace("\n", " ")
        page.goto(f"{BASE}/mis-preguntas.html")
        assert page.locator("[data-saved-list]").first.get_attribute("data-saved-list") == "all"
        assert page.locator(".saved-tab-icon svg").count() == 2
        assert page.locator(".saved-question").count() == 1
        assert page.locator(".saved-question>p").text_content() == prompt
        heading = page.locator("h1 em")
        assert heading.text_content() == "preguntas cortas"
        assert heading.evaluate("""node => {
            const s = getComputedStyle(node);
            return s.color === 'rgb(32, 35, 29)' && s.backgroundColor === 'rgb(214, 238, 122)'
                && parseFloat(s.webkitTextStrokeWidth) === 0 && s.textShadow === 'none';
        }""")
        page.locator("#saved-search").fill("sin coincidencia deliberada")
        assert page.locator(".saved-question").count() == 0
        assert page.locator("#saved-count").inner_text().startswith("0 preguntas")
        page.locator("#saved-reset").click()
        assert page.locator(".saved-question").count() == 1
        page.locator("#saved-search").fill(prompt.split()[0].upper())
        assert page.locator(".saved-question").count() == 1
        page.locator("#saved-reset").click()
        page.get_by_text("Posible solución", exact=True).click()
        assert page.locator(".gen-sol p").is_visible()
        page.locator('[data-saved-list="review"]').click()
        assert page.locator(".saved-question").count() == 1
        page.get_by_role("button", name="Necesito repasar", exact=True).click()
        assert page.locator(".saved-question").count() == 0
        page.locator('[data-saved-list="favorite"]').click()
        assert page.locator(".saved-question").count() == 1
        page.reload()
        assert page.locator(".saved-question").count() == 1
        page.emulate_media(reduced_motion="reduce")
        favorite = page.get_by_role("button", name="Favorita", exact=True)
        favorite.click()
        assert page.locator(".favorite-particle").count() == 0
        page.goto(BASE)
        page.locator(".block").first.locator("summary").first.click()
        page.locator(".question-list .question-mark-favorite").first.click()
        assert page.locator(".favorite-particle").count() == 0
        page.goto(f"{BASE}/mis-preguntas.html")
        page.emulate_media(reduced_motion="no-preference")
        page.select_option("#saved-block", "4")
        assert page.locator(".saved-question").count() == 0
        page.goto(f"{BASE}/apuntes/bloque-4.html")
        page.wait_for_selector(".related-question")
        assert page.locator(".practice-marks .question-marks").count() == 18
        item = page.locator(".related-question").first
        item.get_by_role("button", name="Favorita", exact=True).click()
        expected = item.locator(".related-question-text").text_content()
        # Duplicate occurrences in related sections share the same state.
        same = page.locator(".related-question").filter(has=page.get_by_text(expected, exact=True))
        for occurrence in same.all():
            assert occurrence.get_by_role("button", name="Favorita", exact=True).get_attribute("aria-pressed") == "true"
        page.goto(f"{BASE}/")
        page.locator('[data-gen="4"]').click()
        assert page.locator(".gen-q .question-marks").count() == 4
        page.locator(".gen-q").first.get_by_role("button", name="Necesito repasar", exact=True).click()
        page.goto(f"{BASE}/mis-preguntas.html")
        page.locator('[data-saved-list="review"]').click()
        assert page.locator(".saved-question").count() == 1
        second = context.new_page()
        second.goto(f"{BASE}/mis-preguntas.html")
        second.locator('[data-saved-list="review"]').click()
        page.get_by_role("button", name="Necesito repasar", exact=True).click()
        second.wait_for_function("document.querySelectorAll('.saved-question').length === 0")
        for width in (375, 768, 1440):
            page.set_viewport_size({"width": width, "height": 800})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        failing = browser.new_context(service_workers="block")
        failing.add_init_script("Storage.prototype.setItem=()=>{throw new Error('quota')}")
        failure = failing.new_page()
        failure.goto(BASE)
        failure.locator(".block").first.locator("summary").first.click()
        button = failure.locator(".question-list .question-marks button").first
        button.click()
        assert "No se pudieron guardar" in failure.locator(".saved-status").text_content()
        assert button.get_attribute("aria-pressed") == "false"
        invalid = browser.new_context(service_workers="block")
        invalid.add_init_script("localStorage.setItem('pau-he.questions.v1', '{roto')")
        broken = invalid.new_page()
        broken.goto(f"{BASE}/mis-preguntas.html")
        assert "No se pudieron leer" in broken.locator(".saved-status").text_content()
        assert broken.evaluate("localStorage.getItem('pau-he.questions.v1')") == "{roto"
        missing = browser.new_context(service_workers="block")
        missing.route("**/mis-preguntas.js*", lambda route: route.abort())
        fallback = missing.new_page()
        fallback.goto(f"{BASE}/apuntes/bloque-4.html")
        fallback.wait_for_function("document.querySelector('.reading-content').dataset.relatedPractice === 'ready'")
        assert fallback.locator(".example-solution").count() == 18
        assert fallback.locator(".related-question").count() == 21
        assert fallback.locator(".saved-questions-error").count() == 1
        fallback.locator(".related-question .gen-sol summary").first.click()
        assert fallback.locator(".related-question .gen-sol p").first.is_visible()
        offline = browser.new_context()
        cached = offline.new_page()
        cached.goto(BASE)
        cached.evaluate("navigator.serviceWorker.ready")
        cached.goto(f"{BASE}/mis-preguntas.html")
        offline.set_offline(True)
        cached.reload()
        assert cached.locator("h1").text_content() == "Mis preguntas cortas"
        assert cached.locator("[data-saved-list]").count() == 3
        assert not errors, errors
        browser.close()
    print("OK: listas independientes, soluciones, filtros, persistencia, duplicados, pestañas y errores.")


if __name__ == "__main__":
    run()
