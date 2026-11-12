"""Verify continuous carousel wrapping against the local server."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def check_notes_availability(browser):
    source = (Path(__file__).resolve().parent.parent / "app.js").read_text(encoding="utf-8")
    cases = (
        ([1, 2, 3, 4], "BLOQUES 1–4", "Consulta los apuntes de los bloques 1–4; los demás llegarán pronto."),
        ([1, 3, 4, 8], "BLOQUES 1, 3–4 y 8", "Consulta los apuntes de los bloques 1, 3–4 y 8; los demás llegarán pronto."),
        ([3], "BLOQUE 3", "Consulta los apuntes del bloque 3; los demás llegarán pronto."),
        ([], "PRÓXIMAMENTE", "Los apuntes de los bloques llegarán pronto."),
        (list(range(1, 13)), "BLOQUES 1–12", "Consulta los apuntes de todos los bloques."),
    )
    for ready, label, description in cases:
        page = browser.new_page(service_workers="block", reduced_motion="reduce")
        prepare = (
            "document.querySelectorAll('#apuntes-track > .apunte').forEach(card => "
            f"card.classList.toggle('is-soon', !{json.dumps(ready)}.includes(Number(card.dataset.n))));\n"
        )
        page.route("**/app.js?*", lambda route: route.fulfill(
            content_type="application/javascript", body=prepare + source))
        page.goto("http://localhost:8765/", wait_until="domcontentloaded")
        notes = page.locator('.study-cards [data-format="apuntes"]')
        assert notes.locator(".tag").inner_text() == label, ready
        assert notes.locator(".card-body p").inner_text() == description, ready
        assert page.locator(".study-cards .card-top > span:not(.tag)").count() == 0
        expected = "Los 12 bloques" if len(ready) == 12 else f"{len(ready)} de 12"
        assert page.locator("#apuntes-count").inner_text() == expected
        page.close()


def check_study_cards(page, width):
    notes = page.locator('.study-cards [data-format="apuntes"]')
    heading = page.locator(".study-structure-heading")
    structure = page.locator(".study-cards .score-card")
    for theme in ("light", "dark"):
        page.evaluate("(theme) => document.documentElement.dataset.theme = theme", theme)
        geometry = notes.evaluate("""node => {
            const box = node.getBoundingClientRect();
            const grid = node.parentElement.getBoundingClientRect();
            return {center:Math.abs(box.left+box.width/2-grid.left-grid.width/2),
                width:box.width, bottom:box.bottom};
        }""")
        assert geometry["center"] < 1, (width, theme, geometry)
        assert notes.evaluate("(node) => getComputedStyle(node).borderRadius") == "12px"
        watermark = notes.locator(".card-notes-watermark")
        assert watermark.get_attribute("aria-hidden") == "true"
        assert watermark.evaluate("(node) => getComputedStyle(node).pointerEvents") == "none"
        assert geometry["bottom"] <= heading.bounding_box()["y"]
        assert heading.bounding_box()["y"] + heading.bounding_box()["height"] <= structure.first.bounding_box()["y"]
        assert heading.locator("span").inner_text() == "+3 +4 +3"
        if width > 900:
            first, second = [node.bounding_box() for node in structure.all()[:2]]
            assert abs(geometry["width"] - (second["x"] - first["x"] + first["width"])) < 1
            assert len({round(node.bounding_box()["y"]) for node in structure.all()}) == 1
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.select_option("#format-filter", "apuntes")
    assert not heading.is_visible()
    page.select_option("#format-filter", "all")
    assert heading.is_visible()
    notes.hover()
    page.wait_for_function(
        "getComputedStyle(document.querySelector('.study-cards [data-format=apuntes]')).transform"
        " === 'matrix(1, 0, 0, 1, 0, -3)'"
    )
    notes_shadow = notes.evaluate("(node) => getComputedStyle(node).boxShadow")
    structure.first.hover()
    page.wait_for_function(
        "getComputedStyle(document.querySelector('.study-cards .score-card')).transform"
        " === 'matrix(1, 0, 0, 1, 0, -3)'"
    )
    assert structure.first.evaluate("(node) => getComputedStyle(node).boxShadow") == notes_shadow
    page.mouse.move(0, 0)


def check_footer(page, width):
    page.evaluate("window.scrollTo({top:document.documentElement.scrollHeight, behavior:'instant'})")
    page.wait_for_function("scrollY + innerHeight >= document.documentElement.scrollHeight - 1")
    page.wait_for_function(
        "Math.abs(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--phase-nav-width'))"
        " - document.querySelector('.phase-nav').getBoundingClientRect().width) < 1"
    )
    geometry = page.locator("footer").evaluate("""footer => {
        const brand = footer.querySelector('.brand').getBoundingClientRect();
        const credit = footer.querySelector('.credit').getBoundingClientRect();
        const nav = document.querySelector('.phase-nav').getBoundingClientRect();
        return {center:credit.left+credit.width/2, gapCenter:(brand.right+nav.left)/2,
            creditTop:credit.top, creditBottom:credit.bottom, brandBottom:brand.bottom,
            creditLeft:credit.left, creditRight:credit.right, brandRight:brand.right,
            navLeft:nav.left, navTop:nav.top};
    }""")
    if width >= 1000:
        assert abs(geometry["center"] - geometry["gapCenter"]) < 1, (width, geometry)
        assert geometry["creditLeft"] > geometry["brandRight"]
        assert geometry["creditRight"] < geometry["navLeft"]
    else:
        assert abs(geometry["center"] - width / 2) < 1, (width, geometry)
        assert geometry["creditTop"] > geometry["brandBottom"]
    assert geometry["creditBottom"] < geometry["navTop"], (width, geometry)
    assert page.locator("footer .credit").evaluate("(node) => getComputedStyle(node).textAlign") == "center"
    video_links = page.locator('footer a[href="https://youtu.be/dGbyNi_Z25c"]')
    assert video_links.count() == 2
    for link in video_links.all():
        assert link.get_attribute("target") == "_blank"
        assert {"noopener", "noreferrer"} <= set(link.get_attribute("rel").split())
        assert link.get_attribute("title") == "Ver vídeo sobre Cuevas Bajas (se abre en nueva pestaña)"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


with sync_playwright() as p:
    browser = p.chromium.launch()
    check_notes_availability(browser)
    for width in (320, 375, 445, 768, 1024, 1440, 2560):
        page = browser.new_page(viewport={"width": width, "height": 900}, service_workers="block")
        page.goto("http://localhost:8765/")
        check_study_cards(page, width)
        check_footer(page, width)
        page.locator("#apuntes-track").scroll_into_view_if_needed()
        assert page.locator(".apuntes-loop-gap[aria-hidden=true]").count() == 1
        assert page.evaluate("""() => {
            const last = document.querySelectorAll('#apuntes-track > .apunte')[11];
            const copy = document.querySelector('.apunte-loop');
            const gap = document.querySelector('.apuntes-loop-gap');
            const track = document.querySelector('#apuntes-track');
            return gap.offsetWidth >= track.clientWidth - 5
                && Math.abs(copy.offsetLeft-last.offsetLeft-last.offsetWidth-gap.offsetWidth-24)<2;
        }""")
        page.locator(".note-dot").nth(11).click()
        page.wait_for_function("document.querySelectorAll('.note-dot')[11].getAttribute('aria-current') === 'true'")
        page.wait_for_timeout(800)
        assert page.evaluate("""() => document.querySelector('.apuntes-controls').getBoundingClientRect().bottom
            <= document.querySelector('.hero-caption').getBoundingClientRect().top"""), width
        assert page.locator(".apunte-credit-toggle").count() == 0
        result = page.evaluate("""async () => {
            const track = document.querySelector('#apuntes-track');
            const cards = [...track.querySelectorAll(':scope > .apunte,:scope > .apunte-loop')];
            let interrupted = false;
            let controlsVisible = true;
            let previousLeft = track.scrollLeft;
            let backwards = false;
            const start = performance.now();
            document.querySelectorAll('.note-dot')[11].firstElementChild
                .dispatchEvent(new AnimationEvent('animationend'));
            while(performance.now()-start < 1400) {
                await new Promise(requestAnimationFrame);
                const copiesLeft = cards[12].offsetLeft - cards[0].offsetLeft;
                if (track.scrollLeft < previousLeft - 3 && track.scrollLeft > 3) backwards = true;
                previousLeft = track.scrollLeft;
                if (track.scrollLeft > 3 && track.scrollLeft < copiesLeft - 3
                    && track.classList.contains('is-looping')) interrupted = true;
                controlsVisible &&= getComputedStyle(document.querySelector('.apuntes-controls')).visibility === 'visible'
                    && track.getBoundingClientRect().height > 300
                    && cards.every(card => getComputedStyle(card).visibility === 'visible');
            }
            return {controlsVisible, backwards, interrupted, left: track.scrollLeft,
                first: document.querySelector('.note-dot').getAttribute('aria-current')};
        }""")
        assert result["controlsVisible"], result
        assert not result["backwards"], result
        assert result["first"] == "true", result
        assert not result["interrupted"], result
        assert result["left"] <= 3, result
        assert page.locator(".apunte-loop[aria-hidden=true]").count() == 12
        page.close()
    browser.close()
print("OK: paso suave del 12 al 1 con hueco amplio y controles visibles en siete anchos.")
