"""Verify document view recovery and independent marks against localhost:8765."""
import json
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"
URL = f"{BASE}/documentos.html"
VIEW = "pau-he.documents.view.v1"
MARKS = "pau-he.documents.marks.v1"
TEXT = "constitucion-1812-articulos-2008"
IMAGE = "goya-tres-de-mayo"


def ready(page):
    page.wait_for_selector('#document-grid[aria-busy="false"]', state="attached")


def snapshot(page):
    return page.evaluate("(key) => JSON.parse(sessionStorage.getItem(key))", VIEW)


def card(page, identity=TEXT):
    return page.locator(f'.document-card[data-id="{identity}"]')


def mark(page, flag, identity=TEXT, in_dialog=False):
    host = page.locator("#document-dialog") if in_dialog else card(page, identity)
    return host.locator(f'[data-document-mark="{flag}"]')


def reload(page):
    page.reload()
    ready(page)


def close_dialog(page):
    page.keyboard.press("Escape")
    page.wait_for_function("""(key) =>
        !document.querySelector('#document-dialog').open
        && JSON.parse(sessionStorage.getItem(key)).dialog === null""", arg=VIEW)


def assert_position(actual, expected):
    assert abs(actual["top"] - expected["top"]) <= 2, (actual, expected)
    assert abs(actual["left"] - expected["left"]) <= 2, (actual, expected)


def position(page):
    return page.evaluate("({left: scrollX, top: scrollY})")


def check_mark_feedback(browser):
    context = browser.new_context(service_workers="block", reduced_motion="no-preference")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL)
    ready(page)
    mark(page, "favorite").click()
    particle = page.locator(".favorite-particle")
    assert particle.count() == 1
    assert particle.evaluate("node => getComputedStyle(node).animationDuration") == "0.7s"
    particle.wait_for(state="detached")
    mark(page, "favorite").click()
    assert particle.count() == 0
    mark(page, "review").click()
    assert page.locator(".review-particle svg").count() == 1
    particle.wait_for(state="detached")
    card(page).locator(".document-open").click()
    mark(page, "favorite", in_dialog=True).click()
    assert particle.evaluate("node => node.parentElement.matches('dialog[open]')")
    assert particle.evaluate("""node => {
        const icon = document.querySelector('#document-dialog [data-document-mark="favorite"] svg')
            .getBoundingClientRect();
        return Math.abs(parseFloat(node.style.left) - icon.left - icon.width / 2) < 1
            && Math.abs(parseFloat(node.style.top) - icon.top - icon.height / 2) < 1;
    }""")
    particle.wait_for(state="detached")
    close_dialog(page)
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    page.locator('[data-document-saved="review"]').click()
    mark(page, "favorite").click()
    old_button = mark(page, "favorite").element_handle()
    bounds = mark(page, "favorite").locator("svg").bounding_box()
    mark(page, "favorite").click()
    assert not old_button.evaluate("node => node.isConnected")
    assert particle.count() == 1
    coordinates = particle.evaluate("node => ({left:parseFloat(node.style.left),top:parseFloat(node.style.top)})")
    assert abs(coordinates["left"] - bounds["x"] - bounds["width"] / 2) < 1
    assert abs(coordinates["top"] - bounds["y"] - bounds["height"] / 2) < 1
    particle.wait_for(state="detached")
    mark(page, "favorite").click()
    page.emulate_media(reduced_motion="reduce")
    mark(page, "favorite").click()
    assert mark(page, "favorite").get_attribute("aria-pressed") == "true"
    assert particle.count() == 0
    mark(page, "favorite").click()
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate("""key => {
        const original = Storage.prototype.setItem;
        Storage.prototype.setItem = function(name, value) {
            if (name === key) throw new DOMException('Denied', 'SecurityError');
            return original.call(this, name, value);
        };
    }""", MARKS)
    mark(page, "favorite").click()
    assert mark(page, "favorite").get_attribute("aria-pressed") == "false"
    assert page.locator("#document-storage-status").get_attribute("role") == "alert"
    assert particle.count() == 0
    assert not errors, errors
    context.close()


def check_horizontal_zoom(browser):
    for width, height in ((1440, 1000), (375, 812)):
        context = browser.new_context(viewport={"width": width, "height": height},
                                      service_workers="block", reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL)
        ready(page)
        card(page, "primo-rivera-sanjurjo-alhucemas-1925").locator(".document-open").click()
        box = page.locator(".document-full-source")
        image = box.locator(".document-person-stage img")
        image.evaluate("node => node.decode()")
        pan = page.get_by_role("slider", name="Desplazar imagen ampliada")
        assert not pan.is_visible()
        background = position(page)
        box.locator(".document-zoom").click()
        pan.wait_for(state="visible")
        assert float(pan.get_attribute("max")) > 0
        pan.press("End")
        page.wait_for_function("""() => {
            const box = document.querySelector('.document-full-source');
            const range = document.querySelector('.document-pan-range');
            return box.scrollLeft > 0 && Math.abs(box.scrollLeft - Number(range.max)) < 1;
        }""")
        assert position(page) == background
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert image.evaluate("""node => {
            const rect = node.getBoundingClientRect();
            return Math.abs(rect.width / rect.height - node.naturalWidth / node.naturalHeight) < .001;
        }""")
        assert pan.evaluate("""node => {
            const range = node.getBoundingClientRect();
            const dialog = document.querySelector('#document-dialog').getBoundingClientRect();
            return range.left >= dialog.left && range.right <= dialog.right;
        }""")
        page.locator("#document-dialog").evaluate("node => node.scrollTop = 500")
        assert position(page) == background
        assert pan.evaluate("""node => {
            const bar = node.closest('label').getBoundingClientRect();
            const close = document.querySelector('.document-close').getBoundingClientRect();
            return bar.top >= close.bottom && bar.bottom <= innerHeight;
        }""")
        page.wait_for_function("""key => {
            const saved = JSON.parse(sessionStorage.getItem(key));
            const box = document.querySelector('.document-full-source');
            return saved.dialog?.zoom && saved.dialog.source.left === box.scrollLeft
                && saved.dialog.position.top === document.querySelector('#document-dialog').scrollTop;
        }""", arg=VIEW)
        reload(page)
        pan.wait_for(state="visible")
        page.wait_for_function("""() => {
            const box = document.querySelector('.document-full-source');
            const range = document.querySelector('.document-pan-range');
            return box.scrollLeft > 0 && Math.abs(box.scrollLeft - Number(range.value)) < 1;
        }""")
        pan.press("Home")
        page.wait_for_function("document.querySelector('.document-full-source').scrollLeft === 0")
        box.locator(".document-zoom").click()
        assert not pan.is_visible()
        assert box.evaluate("node => node.scrollLeft") == 0
        assert not errors, errors
        context.close()


def check_saved_library(browser):
    context = browser.new_context(service_workers="block", reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL)
    ready(page)
    assert page.locator(".document-saved-filters .saved-tab-icon svg").count() == 2
    mark(page, "favorite").click()
    mark(page, "review").click()
    mark(page, "review", IMAGE).click()
    map_id = "mapa-desamortizacion-madoz"
    mark(page, "favorite", map_id).click()
    page.locator('[data-type="texto"]').click()
    page.locator("#document-search").fill("constitucion")
    page.get_by_role("link", name="Mis documentos", exact=True).click()
    ready(page)
    bank_view = snapshot(page)
    assert page.locator("h1").inner_text() == "Mis documentos"
    assert page.locator('.saved-nav[aria-current="page"]').inner_text() == "Mis documentos"
    assert page.locator(".document-card").count() == 3
    assert page.locator(".document-saved-filters .saved-tab-icon svg").count() == 2
    counters = page.locator("[data-document-saved-count]")
    assert counters.all_text_contents() == ["3", "2", "2"]
    page.locator('[data-document-saved="favorite"]').click()
    assert page.locator(".document-card").count() == 2
    assert card(page, IMAGE).count() == 0
    page.locator('[data-document-saved="review"]').click()
    assert page.locator(".document-card").count() == 2
    assert page.locator('[data-document-saved="review"]').evaluate(
        "node => getComputedStyle(node).backgroundColor") == "rgb(214, 238, 122)"
    mark(page, "review").click()
    assert card(page).count() == 0
    assert counters.all_text_contents() == ["3", "2", "1"]
    mark(page, "review", IMAGE).click()
    assert page.locator("#document-empty").is_visible()
    assert counters.all_text_contents() == ["2", "2", "0"]
    page.locator('[data-document-saved="all"]').click()
    assert card(page).count() == 1
    card(page, map_id).locator(".document-open").click()
    mark(page, "favorite", map_id, in_dialog=True).click()
    assert card(page, map_id).count() == 0
    page.keyboard.press("Escape")
    page.wait_for_function(
        "document.activeElement === document.querySelector('[data-document-saved=\"all\"]')"
    )
    assert counters.all_text_contents() == ["1", "1", "0"]
    page.locator("#document-search").fill("goya")
    reload(page)
    assert page.locator("#document-empty").is_visible()
    assert page.locator("#document-search").input_value() == "goya"
    assert snapshot(page) == bank_view
    page.locator("#document-reset").click()
    assert page.locator(".document-card").count() == 1
    card(page).locator(".document-open").click()
    reload(page)
    assert page.locator("#document-dialog").is_visible()
    page.keyboard.press("Escape")

    bank = context.new_page()
    bank.goto(URL)
    ready(bank)
    mark(bank, "favorite", IMAGE).click()
    card(page, IMAGE).wait_for(state="visible")
    assert counters.all_text_contents() == ["2", "2", "0"]
    mark(bank, "favorite").click()
    card(page).wait_for(state="detached")
    assert counters.all_text_contents() == ["1", "1", "0"]
    assert not errors, errors
    context.close()

    context = browser.new_context(service_workers="block")
    page = context.new_page()
    for path in ("index.html", "apuntes/bloque-4.html", "mis-preguntas.html",
                 "documentos.html", "mis-documentos.html"):
        page.goto(f"{BASE}/{path}")
        page.wait_for_selector(".saved-nav-stack")
        for width in (320, 375, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            for dark in (False, True):
                page.evaluate("dark => document.documentElement.dataset.theme = dark ? 'dark' : ''", dark)
                assert page.evaluate("""() => {
                    const stack = document.querySelector('.saved-nav-stack');
                    const [questions, documents] = [...stack.children].map(node => node.getBoundingClientRect());
                    const dictionary = document.querySelector('.header-tools .header-tool').getBoundingClientRect();
                    const group = stack.getBoundingClientRect();
                    return Math.abs(questions.x-documents.x) < 1
                        && Math.abs(questions.width-documents.width) < 1
                        && questions.bottom <= documents.top
                        && group.right < dictionary.left
                        && Math.abs(group.y+group.height/2-dictionary.y-dictionary.height/2) < 1
                        && document.documentElement.scrollWidth <= innerWidth;
                }"""), (path, width, dark)
        link = page.get_by_role("link", name="Mis documentos", exact=True)
        assert link.get_attribute("href") == f"{BASE}/mis-documentos.html"
    context.close()

    offline = browser.new_context(reduced_motion="reduce")
    page = offline.new_page()
    page.goto(f"{BASE}/index.html")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    page.evaluate("([key,id]) => localStorage.setItem(key, JSON.stringify({[id]:{favorite:true,review:false}}))",
                  [MARKS, IMAGE])
    offline.set_offline(True)
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    assert page.locator(".document-card").count() == 1
    assert card(page, IMAGE).is_visible()
    assert page.locator("[data-document-saved-count]").all_text_contents() == ["1", "1", "0"]
    assert page.locator(".saved-nav-stack a").count() == 2
    offline.close()


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block", viewport={"width": 1280, "height": 720})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL)
        ready(page)
        page.locator('[data-type="texto"]').click()
        page.locator("#document-block").select_option("5")
        page.locator("#document-search").fill("constitucion")
        page.locator("#document-topic-sort").select_option("frequency")
        page.locator("#document-topic-search").fill("constit")
        page.locator(".document-topic-bubble").first.click()
        before = page.locator(".document-card").evaluate_all("(nodes) => nodes.map(n => n.dataset.id)")
        saved = snapshot(page)
        reload(page)
        assert page.locator("#document-search").input_value() == "constitucion"
        assert page.locator("#document-topic-search").input_value() == "constit"
        assert page.locator("#document-topic-sort").input_value() == "frequency"
        assert page.locator("#document-block").input_value() == "5"
        assert page.locator('[data-type="texto"]').get_attribute("aria-pressed") == "true"
        assert snapshot(page)["topic"] == saved["topic"]
        assert page.locator(".document-card").evaluate_all("(nodes) => nodes.map(n => n.dataset.id)") == before
        page.locator("#document-search").fill("sin-resultados-xyz")
        reload(page)
        assert page.locator("#document-empty").is_visible()
        assert page.locator("#document-search").input_value() == "sin-resultados-xyz"
        assert page.locator(".document-card").count() == 0

        page.locator("#document-reset").click()
        page.locator("#document-topic-toggle").click()
        reload(page)
        assert page.locator("#document-topic-toggle").get_attribute("aria-expanded") == "true"
        card(page, IMAGE).scroll_into_view_if_needed()
        background = position(page)
        assert background["top"] > 500
        reload(page)
        assert_position(position(page), background)
        page.goto(f"{BASE}/apuntes/bloque-6.html")
        page.go_back()
        ready(page)
        assert_position(position(page), background)

        card(page).locator(".document-open").click()
        page.locator(".document-guide summary").click()
        page.locator("#document-dialog").evaluate("(node) => node.scrollTop = 530")
        page.wait_for_timeout(100)
        state = snapshot(page)
        assert state["dialog"]["position"]["top"] > 0
        reload(page)
        assert page.locator("#document-dialog").is_visible()
        assert page.locator(".document-guide").evaluate("(node) => node.open")
        assert page.locator(".document-full-source blockquote").is_visible()
        assert abs(page.locator("#document-dialog").evaluate("(node) => node.scrollTop") - state["dialog"]["position"]["top"]) < 2
        assert_position(position(page), state["page"])
        close_dialog(page)
        assert_position(position(page), state["page"])
        assert card(page).locator(".document-open").evaluate("(node) => node === document.activeElement")
        reload(page)
        assert not page.locator("#document-dialog").is_visible()
        assert_position(position(page), state["page"])
        card(page).locator(".document-open").click()
        page.locator(".document-guide summary").click()
        page.locator("#document-dialog").evaluate("(node) => node.scrollTop = 500")
        page.wait_for_timeout(100)
        page.locator('#document-dialog a[href="apuntes/bloque-5.html"]').click()
        notes_state = snapshot(page)
        page.go_back()
        ready(page)
        assert page.locator("#document-dialog").is_visible()
        assert page.locator(".document-guide").evaluate("(node) => node.open")
        assert abs(page.locator("#document-dialog").evaluate("(node) => node.scrollTop") - notes_state["dialog"]["position"]["top"]) < 2
        close_dialog(page)

        # A fresh explicit URL wins; reload of that URL retains later selections.
        page.goto(f"{URL}?bloque=8")
        ready(page)
        assert page.locator("#document-block").input_value() == "8"
        page.locator("#document-block").select_option("6")
        reload(page)
        assert page.locator("#document-block").input_value() == "6"
        page.goto(f"{URL}?bloque=11")
        ready(page)
        assert page.locator("#document-block").input_value() == "11"
        page.locator("#document-reset").click()

        # New controls must intercept the stretched card target, support keyboard,
        # and update both the card and the open document without replacing focus.
        mark(page, "favorite").focus()
        page.keyboard.press("Space")
        assert not page.locator("#document-dialog").is_visible()
        assert mark(page, "favorite").get_attribute("aria-pressed") == "true"
        assert mark(page, "favorite").evaluate("(node) => node === document.activeElement")
        mark(page, "review").click()
        assert not page.locator("#document-dialog").is_visible()
        card(page).locator(".document-open").click()
        assert mark(page, "favorite", in_dialog=True).get_attribute("aria-pressed") == "true"
        assert mark(page, "review", in_dialog=True).get_attribute("aria-pressed") == "true"
        mark(page, "review", in_dialog=True).click()
        assert mark(page, "review", in_dialog=True).evaluate("(node) => node === document.activeElement")
        assert mark(page, "review").get_attribute("aria-pressed") == "false"
        mark(page, "review", in_dialog=True).click()
        reload(page)
        assert mark(page, "review", in_dialog=True).get_attribute("aria-pressed") == "true"
        close_dialog(page)
        page.locator('[data-document-saved="favorite"]').click()
        assert page.locator(".document-card").count() == 1
        assert card(page).is_visible()
        reload(page)
        assert page.locator('[data-document-saved="favorite"]').get_attribute("aria-pressed") == "true"
        page.locator('[data-document-saved="review"]').click()
        assert page.locator(".document-card").count() == 1
        assert page.locator('[data-document-saved="review"]').evaluate(
            "node => getComputedStyle(node).backgroundColor") == "rgb(214, 238, 122)"
        mark(page, "review").click()
        assert page.locator(".document-card").count() == 0
        assert page.locator('[data-document-saved="review"]').evaluate("(node) => node === document.activeElement")
        page.locator('[data-document-saved="all"]').click()
        assert page.evaluate("localStorage.getItem('pau-he.questions.v1')") is None

        second = context.new_page()
        second.goto(URL)
        ready(second)
        mark(second, "review", IMAGE).click()
        page.wait_for_function(
            "(id) => document.querySelector(`.document-card[data-id='${id}'] [data-document-mark=review]`).getAttribute('aria-pressed') === 'true'",
            arg=IMAGE,
        )
        mark(page, "favorite").focus()
        mark(second, "favorite", IMAGE).click()
        page.wait_for_function(
            "(id) => document.querySelector(`.document-card[data-id='${id}'] [data-document-mark=favorite]`).getAttribute('aria-pressed') === 'true'",
            arg=IMAGE,
        )
        assert mark(page, "favorite").evaluate("(node) => node === document.activeElement")
        mark(page, "favorite").click()
        durable = page.evaluate("(key) => JSON.parse(localStorage.getItem(key))", MARKS)
        assert durable[IMAGE] == {"favorite": True, "review": True}
        assert TEXT not in durable
        page.locator('[data-document-saved="review"]').click()
        card(page, IMAGE).locator(".document-open").click()
        mark(second, "review", IMAGE).click()
        page.wait_for_function("document.querySelectorAll('.document-card').length === 0")
        assert page.locator("#document-dialog").is_visible()
        assert mark(page, "review", IMAGE, True).get_attribute("aria-pressed") == "false"
        close_dialog(page)
        page.wait_for_function("document.activeElement?.dataset.documentSaved === 'review'")
        page.locator("#document-reset").click()

        # Zoom, horizontal overflow, and source details survive without relying on img.
        card(page, IMAGE).locator(".document-preview-zoom").click()
        page.locator(".document-zoom").click()
        page.locator(".document-full-source img").evaluate("(node) => node.decode()")
        page.locator(".document-full-source").evaluate("(node) => node.scrollLeft = 120")
        page.locator("#document-dialog").evaluate("(node) => node.scrollTop = 180")
        page.wait_for_timeout(100)
        state = snapshot(page)
        assert state["dialog"]["zoom"]
        assert state["dialog"]["source"]["left"] > 0
        reload(page)
        assert page.locator(".document-full-source").evaluate("(node) => node.classList.contains('is-zoomed')")
        assert page.locator(".document-full-source").evaluate("(node) => node.scrollLeft") == state["dialog"]["source"]["left"]
        assert abs(page.locator("#document-dialog").evaluate("(node) => node.scrollTop") - state["dialog"]["position"]["top"]) < 2
        close_dialog(page)
        assert card(page, IMAGE).locator(".document-preview-zoom").evaluate("(node) => node === document.activeElement")
        table_id = "resultados-electorales-restauracion-1881-1898"
        card(page, table_id).locator(".document-open").click()
        page.locator(".document-table-details summary").click()
        reload(page)
        assert page.locator(".document-table-details").evaluate("(node) => node.open")
        close_dialog(page)

        # A failed write must not optimistically unmark an already saved item.
        original_marks = page.evaluate("(key) => localStorage.getItem(key)", MARKS)
        page.evaluate("""(key) => {
            const original = Storage.prototype.setItem;
            Storage.prototype.setItem = function(name, value) {
                if (name === key) throw new DOMException('Full', 'QuotaExceededError');
                return original.call(this, name, value);
            };
        }""", MARKS)
        assert mark(page, "favorite", IMAGE).get_attribute("aria-pressed") == "true"
        mark(page, "favorite", IMAGE).click()
        assert mark(page, "favorite", IMAGE).get_attribute("aria-pressed") == "true"
        assert page.evaluate("(key) => localStorage.getItem(key)", MARKS) == original_marks
        assert page.locator("#document-storage-status").get_attribute("role") == "alert"
        second.close()
        assert not errors, errors
        context.close()

        # Slow sources must not replace the good snapshot while restoring.
        slow = browser.new_context(service_workers="block")
        page = slow.new_page()
        page.goto(URL)
        ready(page)
        card(page, IMAGE).locator(".document-preview-zoom").click()
        page.locator(".document-zoom").click()
        page.locator("#document-dialog").evaluate("(node) => node.scrollTop = 400")
        page.wait_for_timeout(100)
        state = snapshot(page)
        page.add_init_script("""
            const decode = HTMLImageElement.prototype.decode;
            HTMLImageElement.prototype.decode = async function() {
                await new Promise(resolve => setTimeout(resolve, 3500));
                return decode.call(this);
            };
        """)
        page.reload()
        page.wait_for_selector("#document-dialog[open]", state="attached")
        page.wait_for_timeout(3100)
        assert snapshot(page) == state
        ready(page)
        assert abs(page.locator("#document-dialog").evaluate("(node) => node.scrollTop") - state["dialog"]["position"]["top"]) < 2
        slow.close()

        font_context = browser.new_context(service_workers="block")
        page = font_context.new_page()
        page.goto(URL)
        ready(page)
        card(page).locator(".document-open").click()
        page.locator("#document-dialog").evaluate("(node) => node.scrollTop = 550")
        page.wait_for_timeout(100)
        state = snapshot(page)
        page.add_init_script("""
            const ready = document.fonts.ready.then(() =>
                new Promise(resolve => setTimeout(resolve, 800)));
            Object.defineProperty(document.fonts, 'ready', { get: () => ready });
        """)
        page.reload()
        page.wait_for_selector("#document-dialog[open]", state="attached")
        assert snapshot(page) == state
        ready(page)
        assert abs(page.locator("#document-dialog").evaluate("(node) => node.scrollTop") - state["dialog"]["position"]["top"]) < 2
        font_context.close()

        for invalid in ("{broken", "[]", '{"x":{"favorite":"yes","review":false}}'):
            isolated = browser.new_context(service_workers="block")
            page = isolated.new_page()
            page.goto(URL)
            ready(page)
            page.evaluate("([key,value]) => localStorage.setItem(key,value)", [MARKS, invalid])
            reload(page)
            assert page.locator("#document-storage-status").get_attribute("role") == "alert"
            mark(page, "favorite").click()
            assert mark(page, "favorite").get_attribute("aria-pressed") == "false"
            assert page.evaluate("(key) => localStorage.getItem(key)", MARKS) == invalid
            isolated.close()

        for invalid in ("{broken", '{"version":1}'):
            isolated = browser.new_context(service_workers="block")
            page = isolated.new_page()
            warnings = []
            page.on("console", lambda message: warnings.append(message.text) if message.type == "warning" else None)
            page.goto(URL)
            ready(page)
            page.evaluate("([key,value]) => sessionStorage.setItem(key,value)", [VIEW, invalid])
            reload(page)
            page.locator("#document-search").fill("goya")
            page.wait_for_timeout(100)
            assert not page.locator("#document-storage-status").is_visible()
            assert any("posición de lectura" in message for message in warnings)
            assert page.evaluate("(key) => sessionStorage.getItem(key)", VIEW) == invalid
            isolated.close()

        for method in ("getItem", "setItem"):
            isolated = browser.new_context(service_workers="block")
            isolated.add_init_script(f"""
                const original = Storage.prototype.{method};
                Storage.prototype.{method} = function(key, ...args) {{
                    if (key.startsWith('pau-he.documents.')) throw new DOMException('Denied', 'SecurityError');
                    return original.call(this, key, ...args);
                }};
            """)
            page = isolated.new_page()
            page.goto(URL)
            ready(page)
            mark(page, "favorite").click()
            assert mark(page, "favorite").get_attribute("aria-pressed") == "false"
            assert page.locator("#document-storage-status").get_attribute("role") == "alert"
            card(page).locator(".document-open").click()
            mark(page, "favorite", in_dialog=True).click()
            assert page.locator("#document-dialog-storage-status").is_visible()
            assert "No se pudieron guardar" in page.locator("#document-dialog-storage-status").inner_text()
            isolated.close()
        check_saved_library(browser)
        check_mark_feedback(browser)
        check_horizontal_zoom(browser)
        browser.close()
        print("PASS: view recovery, marks, animations, horizontal zoom, saved library, mobile, offline, storage errors")


if __name__ == "__main__":
    run()
