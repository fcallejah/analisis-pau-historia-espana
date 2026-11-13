"""Verify reader recovery and personal-list presentation in Chromium and WebKit."""
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"
VIEW = "pau-he.documents.view.v1"
LARGE = "primo-rivera-sanjurjo-alhucemas-1925"


def ready(page):
    page.wait_for_selector('#document-grid[aria-busy="false"]', state="attached")
    page.wait_for_function("!document.documentElement.hasAttribute('data-document-restoring')")


def open_card(page, identifier):
    page.locator(f'.document-card[data-id="{identifier}"] .document-open').click()
    for image in page.locator(".document-full-source img").all():
        image.evaluate("node => node.decode()")


def check_handwritten_title(page):
    page.evaluate("document.fonts.ready")
    word = page.locator("h1 .personal-library-mis")
    assert word.inner_text() == "Mis"
    assert word.evaluate("""node => {
        const style = getComputedStyle(node);
        const title = getComputedStyle(node.closest('h1'));
        const rest = node.nextElementSibling.getClientRects()[0];
        return style.fontFamily.startsWith('"Great Vibes"') && style.fontWeight === '400'
            && style.fontFamily !== title.fontFamily
            && node.getBoundingClientRect().right <= rest.left + 1
            && Array.from(document.fonts).some(face => face.family.replaceAll('"', '') === 'Great Vibes' && face.status === 'loaded');
    }""")


def centered(page):
    return page.locator(".document-full-source").evaluate("""box => {
        const media = box.querySelector('.document-person-stage').getBoundingClientRect();
        const r = box.getBoundingClientRect();
        return Math.abs(media.left + media.width / 2 - r.left - box.clientLeft - box.clientWidth / 2) < 2;
    }""")


def check(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    page.locator('[data-type="imagen"]').click()
    page.select_option("#document-block", "9")
    page.locator("#document-search").fill("Primo")
    open_card(page, LARGE)
    box = page.locator(".document-full-source")
    box.locator(".document-zoom").click()
    assert centered(page)
    box.evaluate("node => node.scrollLeft = (node.scrollWidth - node.clientWidth) * .7")
    dialog = page.locator("#document-dialog")
    dialog.evaluate("node => node.scrollTop = 320")
    page.wait_for_function("""key => {
        const saved = JSON.parse(sessionStorage.getItem(key));
        const dialog = document.querySelector('#document-dialog');
        const box = document.querySelector('.document-full-source');
        return saved?.dialog?.zoom && saved.dialog.position.top === dialog.scrollTop
            && saved.dialog.source.left === box.scrollLeft;
    }""", arg=VIEW)
    saved = page.evaluate("key => JSON.parse(sessionStorage.getItem(key))", VIEW)
    page.evaluate("""key => {
        const old = JSON.parse(sessionStorage.getItem(key));
        delete old.savedFilter;
        delete old.dialog.opener;
        sessionStorage.setItem(key, JSON.stringify(old));
    }""", VIEW)
    page.add_init_script("""
        const decode = HTMLImageElement.prototype.decode;
        HTMLImageElement.prototype.decode = async function() {
            await new Promise(resolve => setTimeout(resolve, 600));
            return decode.call(this);
        };
        window.readerFrames = [];
        function sample() {
            const dialog = document.querySelector('#document-dialog');
            const grid = document.querySelector('#document-grid');
            if (grid?.getAttribute('aria-busy') === 'false'
                && !document.documentElement.hasAttribute('data-document-restoring')) {
                readerFrames.push({open: dialog.open, top: dialog.scrollTop, pageTop: scrollY});
            }
            requestAnimationFrame(sample);
        }
        requestAnimationFrame(sample);
    """)
    page.reload()
    ready(page)
    page.wait_for_function("readerFrames.length >= 3")
    frames = page.evaluate("readerFrames")
    assert all(frame["open"] and abs(frame["top"] - saved["dialog"]["position"]["top"]) < 2
               and abs(frame["pageTop"] - saved["page"]["top"]) < 2 for frame in frames), frames
    assert page.locator("#document-block").input_value() == "9"
    assert page.locator("#document-search").input_value() == "Primo"
    assert LARGE == page.evaluate("key => JSON.parse(sessionStorage.getItem(key)).dialog.id", VIEW)
    assert abs(box.evaluate("node => node.scrollLeft") - saved["dialog"]["source"]["left"]) < 2
    assert not page.locator("#document-storage-status").is_visible()
    assert page.evaluate("history.scrollRestoration") == "manual"
    assert dialog.evaluate("node => node.classList.contains('has-more-below')")
    assert page.locator(".document-scroll-cue").evaluate("""node => {
        const r = node.getBoundingClientRect();
        const d = node.closest('dialog').getBoundingClientRect();
        return getComputedStyle(node).pointerEvents === 'none'
            && r.top >= d.top && r.bottom <= d.bottom + 1;
    }""")
    dialog.evaluate("node => node.scrollTop = node.scrollHeight")
    page.wait_for_function("!document.querySelector('#document-dialog').classList.contains('has-more-below')")
    assert page.locator(".document-scroll-cue").evaluate("node => getComputedStyle(node).opacity") == "0"
    page.keyboard.press("Escape")
    page.locator("#document-reset").click()
    for identifier in (LARGE, "retrato-ramon-maria-narvaez"):
        open_card(page, identifier)
        assert centered(page)
        box.locator(".document-zoom").click()
        assert centered(page), identifier
        box.locator(".document-zoom").click()
        assert centered(page), identifier
        page.keyboard.press("Escape")
    open_card(page, "azana-homenaje-coruna-franco")
    page.locator(".document-person-toggle").click()
    text = page.locator("#document-dialog-content").inner_text()
    assert "Presidente del Consejo de Ministros" in text
    assert "Ministro de la Gobernación" in text
    assert "espectador" not in text and "el pie del examen identifica" not in text.lower()
    assert page.locator(".document-provenance").count() == 0
    collection = page.get_by_role("link", name="Ver en la recopilación", exact=True)
    assert collection.count() == 1
    assert collection.locator('svg[aria-hidden="true"]').count() == 1
    mark = page.locator('#document-dialog [data-document-mark="favorite"]')
    mark.click()
    assert mark.get_attribute("aria-pressed") == "true"
    assert not page.locator("#document-dialog-storage-status").is_visible()
    background = page.evaluate("({left: scrollX, top: scrollY})")
    bounds = dialog.bounding_box()
    page.mouse.click(bounds["x"] + 5, bounds["y"] + 80)
    assert dialog.is_visible()
    page.mouse.move(bounds["x"] + 5, bounds["y"] + 80)
    page.mouse.down()
    page.mouse.move(1, bounds["y"] + 80)
    page.mouse.up()
    assert dialog.is_visible()
    if options.get("has_touch"):
        page.touchscreen.tap(1, 100)
    else:
        page.mouse.click(1, 100)
    page.wait_for_function("!document.querySelector('#document-dialog').open")
    assert page.evaluate("({left: scrollX, top: scrollY})") == background
    assert page.evaluate("document.activeElement.closest('.document-card')?.dataset.id") == "azana-homenaje-coruna-franco"
    open_card(page, "azana-homenaje-coruna-franco")
    bounds = dialog.bounding_box()
    dialog.dispatch_event("mousedown", {"clientX": bounds["x"] + 5, "clientY": bounds["y"] + 80})
    dialog.dispatch_event("click", {"clientX": 1, "clientY": 100})
    assert dialog.is_visible()
    dialog.dispatch_event("click", {"clientX": bounds["x"] + 5, "clientY": bounds["y"] + 80})
    assert dialog.is_visible()
    dialog.dispatch_event("click", {"clientX": 1, "clientY": 100})
    page.wait_for_function("!document.querySelector('#document-dialog').open")
    assert page.evaluate("({left: scrollX, top: scrollY})") == background
    for name in ("documentos.html", "mis-documentos.html"):
        page.goto(f"{BASE}/{name}")
        ready(page)
        if name == "mis-documentos.html":
            check_handwritten_title(page)
        assert page.locator(".document-types button svg").count() == 3
        assert page.locator("h1 em").evaluate("""node => {
            const s = getComputedStyle(node);
            const canvas = document.createElement('canvas');
            const c = canvas.getContext('2d');
            c.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
            const m = c.measureText(node.textContent);
            return s.backgroundClip === 'border-box' && s.color === 'rgb(32, 35, 29)'
                && s.backgroundImage.includes('linear-gradient')
                && parseFloat(s.paddingRight) >= Math.max(0, m.actualBoundingBoxRight - m.width) + 1;
        }""")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.goto(f"{BASE}/mis-preguntas.html")
    check_handwritten_title(page)
    assert page.locator("main").get_attribute("class") == "documents-main saved-questions-main"
    assert page.locator("h1 em").evaluate("""node => {
        const s = getComputedStyle(node);
        return s.backgroundColor === 'rgb(214, 238, 122)' && s.color === 'rgb(32, 35, 29)'
            && s.textShadow === 'none' && parseFloat(s.webkitTextStrokeWidth) === 0;
    }""")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    back = page.get_by_role("link", name="Volver a preguntas cortas", exact=True)
    assert back.get_attribute("href") == "index.html#bloques-cuestiones"
    if options.get("viewport", {}).get("width", 0) >= 1280:
        heading = page.locator("h1").bounding_box()
        target = back.bounding_box()
        assert target["x"] >= heading["x"] + heading["width"]
    back.click()
    page.wait_for_url(f"{BASE}/index.html#bloques-cuestiones")
    assert not errors, errors
    context.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        for engine, options in (
            (playwright.chromium, {"viewport": {"width": 1440, "height": 1000}}),
            (playwright.chromium, {"viewport": {"width": 375, "height": 812}}),
            (playwright.webkit, playwright.devices["iPad (gen 7)"]),
        ):
            browser = engine.launch()
            check(browser, options)
            browser.close()
    print("PASS: legacy recovery without visible jumps, centered zoom, reading cue, roles and personal-list headings")
