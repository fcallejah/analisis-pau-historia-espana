"""Run against the local server on port 8765."""
import json
import re
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"
DATA = json.loads((Path(__file__).resolve().parent.parent / "data/documentos.json").read_text())
TEXT_DOCUMENT = next(document for document in DATA["documents"]
                     if document["id"] == "constitucion-1812-articulos-2008")
GOYA_DOCUMENT = next(document for document in DATA["documents"]
                     if document["id"] == "goya-tres-de-mayo")


def normalize(value):
    return "".join(character for character in unicodedata.normalize("NFD", value.lower())
                   if not unicodedata.combining(character))

def check_document_attributions(browser):
    records = {record["id"]: record for record in DATA["documents"]}
    for width in (1440, 375):
        context = browser.new_context(viewport={"width": width, "height": 1000}, service_workers="block")
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        for identifier, record in records.items():
            if record["type"] != "texto":
                continue
            page.locator(f'.document-card[data-id="{identifier}"] .document-open').click()
            check_collection_link(page, record)
            font = page.locator(".document-full-source blockquote").evaluate(
                "node => getComputedStyle(node).fontFamily")
            assert font.startswith('"PAU Caption"'), (identifier, font)
            assert page.locator(f'.document-card[data-id="{identifier}"] blockquote').evaluate(
                "node => getComputedStyle(node).fontFamily") == font
            paragraphs = page.locator(".document-full-source blockquote p")
            assert paragraphs.all_text_contents() == record["text"]
            count = record.get("attributionParagraphs", 0)
            for index, paragraph in enumerate(paragraphs.all()):
                style = paragraph.evaluate("""node => {
                    const s = getComputedStyle(node);
                    return {align:s.textAlign,last:s.textAlignLast,style:s.fontStyle};
                }""")
                if index >= len(record["text"]) - count:
                    assert style == {"align": "right", "last": "right", "style": "normal"}, (identifier, style)
                    emphasis = record.get("attributionEmphasis", []) if index == len(record["text"]) - 1 else []
                    assert paragraph.locator("em").all_text_contents() == emphasis, identifier
                    for part in paragraph.locator("em").all():
                        assert part.evaluate("node => getComputedStyle(node).fontStyle") == "italic"
                    if identifier == "ley-general-de-ferrocarriles":
                        assert paragraph.locator("em").all_text_contents() == ["Ley general de ferrocarriles"]
                    if identifier == "antonio-maura-critica-la-representacion-politica":
                        assert paragraph.locator("em").all_text_contents() == ["Antonio Maura"]
                    assert paragraph.evaluate("""node => {
                        const range = document.createRange();
                        range.selectNodeContents(node);
                        return Math.abs(range.getBoundingClientRect().right - node.getBoundingClientRect().right) < 1;
                    }""")
                else:
                    assert style == {"align": "justify", "last": "left", "style": "normal"}, (identifier, style)
            page.keyboard.press("Escape")
        context.close()

def check_collection_link(page, record):
    assert page.locator(".document-provenance, .document-quality").count() == 0
    collection = page.get_by_role("link", name="Ver en la recopilación", exact=True)
    assert collection.count() == 1
    appearance = next(item for item in record["appearances"]
                      if item["id"] == record["examCaption"]["appearanceId"]) if record.get("examCaption") else record["appearances"][0]
    assert collection.get_attribute("href") == appearance["sourceUrl"]
    assert collection.inner_text() == "Ver en la recopilación"
    icon = collection.locator("svg")
    assert icon.count() == 1 and icon.get_attribute("aria-hidden") == "true"
    assert icon.evaluate("(node) => node.getBoundingClientRect().width > 0 && node.getBoundingClientRect().height > 0")


def appearance_label(appearance):
    exam = re.sub(rf"^{appearance['year']}\s+", "", appearance["exam"])
    exam = re.sub(r"\s*\([^)]*\)\s*$", "", exam)
    return " · ".join(str(part) for part in (
        appearance["year"], exam,
        "" if appearance["route"].endswith("sin cotejar") else appearance["route"],
        f"Documento {appearance['document']}",
    ) if part != "")


def check_card_badges(page):
    badges = page.locator(".document-card").evaluate_all("""cards => Object.fromEntries(
        cards.map(card => [card.dataset.id,
            [...card.querySelectorAll('.document-exams .exam-pill')].map(pill => pill.textContent)])
    )""")
    for record in DATA["documents"]:
        assert badges[record["id"]] == [
            appearance_label(appearance) for appearance in record["appearances"]
        ], record["id"]

def check_fitted_media_and_people(browser):
    for width, height in ((1440, 1000), (768, 1024), (375, 812)):
        context = browser.new_context(viewport={"width": width, "height": height},
                                      service_workers="block", has_touch=True)
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector(".document-card")
        for record in DATA["documents"]:
            if not record.get("image") and not record.get("tableImage"):
                continue
            card = page.locator(f'.document-card[data-id="{record["id"]}"]')
            card.locator(".document-preview-zoom").tap()
            check_collection_link(page, record)
            box = page.locator(".document-full-source")
            assert not box.evaluate("(node) => node.classList.contains('is-zoomed')")
            for image in box.locator("img").all():
                image.evaluate("(node) => node.decode()")
                geometry = image.evaluate("""image => {
                    const r = image.getBoundingClientRect();
                    const visible = (image.closest('.doc-image-crop') || image).getBoundingClientRect();
                    return {ratio:r.width/r.height, natural:image.naturalWidth/image.naturalHeight,
                        height:visible.height, width:visible.width};
                }""")
                assert abs(geometry["ratio"] - geometry["natural"]) < 0.001, (record["id"], width, geometry)
                assert geometry["height"] <= height * .52 + 1, (record["id"], geometry)
                assert geometry["width"] <= box.evaluate("(node) => node.clientWidth"), record["id"]
            visible_images = [
                image for image in [
                    record.get("image"),
                    *(record.get("image", {}).get("additionalImages") or []),
                    record.get("tableImage"),
                ] if image
            ]
            data = next((image["annotations"] for image in visible_images if image.get("annotations")), None)
            if record.get("image", {}).get("filter"):
                assert box.locator("img").first.evaluate(
                    "(image) => getComputedStyle(image).filter"
                ) == record["image"]["filter"]
            feet = box.locator(".document-exam-caption")
            assert feet.count() == len(visible_images)
            for foot, image_data in zip(feet.all(), visible_images):
                caption = image_data.get("examCaption", record.get("examCaption"))
                assert foot.locator("p").inner_text() == (caption["text"] if caption else "(Sin descripción)")
                assert foot.locator("em").all_text_contents() == (caption.get("emphasis", []) if caption else [])
                assert foot.locator("small").count() == 0
                assert foot.evaluate("""node => {
                    const p = node.querySelector('p');
                    const style = getComputedStyle(p);
                    const media = node.closest('figure').querySelector('.document-person-stage, .doc-image-crop, img, object');
                    return parseFloat(style.fontSize) >= 18 && style.fontWeight === '400'
                        && style.fontStyle === 'normal' && style.fontFamily.startsWith('"PAU Caption"')
                        && node.getBoundingClientRect().top >= media.getBoundingClientRect().bottom - 1
                        && !!node.closest('.document-full-source');
                }"""), record["id"]
            toggle = box.locator(".document-person-toggle")
            assert toggle.count() == bool(data), record["id"]
            if data:
                assert toggle.get_attribute("aria-expanded") == "false"
                assert not box.locator(".document-person-overlay").is_visible()
                before = box.locator(".document-person-stage").bounding_box()
                toggle.tap()
                after = box.locator(".document-person-stage").bounding_box()
                assert abs(before["width"] - after["width"]) < 1 and abs(before["height"] - after["height"]) < 1
                assert toggle.inner_text() == "Ocultar personajes"
                assert box.locator(".document-person-overlay").is_visible()
                assert box.locator(".document-person-name").all_text_contents() == [
                    person["name"] for person in data["people"]
                ]
                margins = width == 1440 and data["layout"] == "margins"
                assert box.locator(".document-person-bubble").first.is_visible() == margins
                assert box.locator(".document-person-names").is_visible() != margins
                assert page.locator(".document-person-sources").count() == 0
                assert box.locator(".document-person-role").all_text_contents() == [
                    person["role"] for person in data["people"]
                ]
                for zoomed in (False, True):
                    if zoomed:
                        box.locator(".document-zoom").tap()
                    page.wait_for_timeout(60)
                    stage = box.locator(".document-person-stage")
                    geometry = stage.evaluate("""stage => {
                        const media = stage.querySelector('.doc-image-crop, img').getBoundingClientRect();
                        const r = stage.getBoundingClientRect();
                        const image = stage.querySelector('img');
                        const i = image.getBoundingClientRect();
                        return {aligned:Math.abs(r.width-media.width)<1 && Math.abs(r.height-media.height)<1,
                            ratio:i.width/i.height, natural:image.naturalWidth/image.naturalHeight};
                    }""")
                    assert geometry["aligned"], (record["id"], width, zoomed, geometry)
                    assert abs(geometry["ratio"] - geometry["natural"]) < .001
                    if margins:
                        assert box.locator(".document-person-lines path").first.evaluate("""path => {
                            const style = getComputedStyle(path);
                            const commands = path.getAttribute('d').match(/[A-Za-z]/g);
                            return style.stroke === 'rgb(229, 57, 53)' && parseFloat(style.strokeWidth) >= 2.5
                                && commands.every(command => ['M','H','Q','V'].includes(command))
                                && commands.includes('H') && (!commands.includes('Q') || commands.includes('V'));
                        }""")
                        assert stage.evaluate("""stage => {
                            const leader = stage.querySelector('.document-person-lines path');
                            const dot = stage.querySelector('.document-person-lines circle');
                            const start = leader.getPointAtLength(0);
                            return getComputedStyle(dot).fill === 'rgb(229, 57, 53)'
                                && dot.r.baseVal.value * 2 === 10
                                && dot.cx.baseVal.value === start.x
                                && dot.cy.baseVal.value === start.y;
                        }""")
                        assert stage.evaluate("""stage => {
                            const r = document.querySelector('#document-dialog').getBoundingClientRect();
                            const labels = [...stage.querySelectorAll('.document-person-bubble')]
                                .filter(b => !b.hidden).map(b => b.getBoundingClientRect());
                            return labels.every(label => label.right <= r.left || label.left >= r.right)
                                && labels.every((label, index) => labels.slice(index + 1).every(other =>
                                    label.right <= other.left || label.left >= other.right
                                    || label.bottom <= other.top || label.top >= other.bottom));
                        }"""), record["id"]
                toggle.tap()
                assert toggle.get_attribute("aria-expanded") == "false"
                assert not box.locator(".document-person-details").is_visible()
            page.locator(".document-close").tap()
        context.close()

def check_external_people(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    page.locator('.document-card[data-id="reunion-expresidentes-gobierno"] .document-open').click()
    page.locator(".document-person-stage img").evaluate("(image) => image.decode()")
    page.locator(".document-person-toggle").click()
    for width in (1440, 1280, 1100, 375, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        placement = "external" if width >= 1280 else "numbered"
        page.wait_for_function("""placement => {
            const figure = document.querySelector('.document-person-figure');
            if (figure.dataset.peoplePlacement !== placement) return false;
            if (placement === 'numbered') return !document.querySelector(':popover-open');
            const stage = figure.querySelector('.document-person-stage').getBoundingClientRect();
            const leader = figure.querySelector('.document-person-lines path');
            const point = leader.getPointAtLength(0).matrixTransform(leader.getScreenCTM());
            return Math.abs(point.x - stage.left - .1 * stage.width) < 1
                && Math.abs(point.y - stage.top - .48 * stage.height) < 1;
        }""", arg=placement)
        assert page.locator(".document-person-names").is_visible() == (placement == "numbered")
        if width == 1440:
            order = page.evaluate("""() => {
                const bubbles = [...document.querySelectorAll('.document-person-bubble')];
                const top = name => bubbles.find(bubble =>
                    bubble.querySelector('.document-person-label').textContent === name
                ).getBoundingClientRect().top;
                return top('José María Aznar') > top('Felipe González')
                    && top('Leopoldo Calvo-Sotelo') > top('Adolfo Suárez');
            }""")
            assert order
    leader = page.locator(".document-person-lines path").first
    before_y = leader.evaluate("path => path.getPointAtLength(0).y")
    delta = page.locator("#document-dialog").evaluate("""dialog => {
        const before = dialog.scrollTop;
        dialog.scrollTop += 80;
        return dialog.scrollTop - before;
    }""")
    assert delta > 0
    page.wait_for_function("expected => Math.abs(document.querySelector('.document-person-lines path').getPointAtLength(0).y - expected) < 1",
                           arg=before_y - delta)
    label = page.locator(".document-person-label").first.bounding_box()
    page.mouse.move(label["x"] + 1, label["y"] + label["height"] / 2)
    page.mouse.down()
    page.mouse.move(label["x"] + label["width"] - 1, label["y"] + label["height"] / 2, steps=10)
    page.mouse.up()
    assert "Felipe González" in page.evaluate("getSelection().toString()")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#document-dialog').open && !document.querySelector(':popover-open')")
    assert not errors, errors
    context.close()

    fallback = browser.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
    fallback.add_init_script("HTMLElement.prototype.showPopover = undefined")
    page = fallback.new_page()
    page.goto(f"{BASE}/documentos.html")
    page.locator('.document-card[data-id="reunion-expresidentes-gobierno"] .document-open').click()
    page.locator(".document-person-toggle").click()
    assert page.locator(".document-person-names").is_visible()
    assert not page.locator(".document-person-bubble").first.is_visible()
    fallback.close()


def search_matches(query):
    return [
        document for document in DATA["documents"]
        if all(normalize(word) in normalize(" ".join([
            document["title"], document["date"], document["sourceCaption"],
            *document["tags"],
            *(f"{appearance['year']} {appearance['exam']}" for appearance in document["appearances"]),
        ])) for word in normalize(query).split())
    ]


def topic_statistics():
    statistics = {}
    for document in DATA["documents"]:
        year = re.search(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", document["date"])
        for tag in document["tags"]:
            count, first_year = statistics.get(tag, (0, float("inf")))
            statistics[tag] = (
                count + len(document["appearances"]),
                min(first_year, int(year.group()) if year else float("inf")),
            )
    return statistics


def check_text_card(page):
    card = page.locator(f'.document-card[data-id="{TEXT_DOCUMENT["id"]}"]')
    opener = card.locator(".document-open")
    assert card.locator("button, a, [tabindex]").count() == 3
    assert card.locator(".document-open").count() == 1
    assert card.locator('button.question-mark-favorite[aria-pressed]').count() == 1
    assert card.locator('button.question-mark-review[aria-pressed]').count() == 1
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
        assert page.locator(".document-full-source blockquote p").count() == len(TEXT_DOCUMENT["text"])
        assert page.locator(".document-full-source blockquote").evaluate("""node => {
            const style = getComputedStyle(node);
            return style.textAlign === 'justify' && style.textAlignLast === 'left'
                && node.scrollWidth <= node.clientWidth;
        }""")
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


def check_dialog_scroll(page):
    original_viewport = page.viewport_size
    opener = page.locator('.document-card[data-id="franco-mola-cavalcanti-burgos"] .document-open')
    for width in (320, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        for close_method in ("button", "escape"):
            opener.scroll_into_view_if_needed()
            position = page.evaluate("({x:scrollX,y:scrollY})")
            opener.click()
            assert page.evaluate("getComputedStyle(document.documentElement).overflowY") == "hidden"
            page.mouse.move(width - 2, 200)
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(200)
            assert page.evaluate("({x:scrollX,y:scrollY})") == position
            bounds = page.locator("#document-dialog").bounding_box()
            page.mouse.move(bounds["x"] + 4, bounds["y"] + bounds["height"] / 2)
            page.mouse.wheel(0, 500)
            page.wait_for_function("document.querySelector('#document-dialog').scrollTop > 0")
            page.locator("#document-dialog").evaluate("(dialog) => dialog.scrollTop = dialog.scrollHeight")
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(200)
            assert page.evaluate("({x:scrollX,y:scrollY})") == position
            if close_method == "button":
                page.locator(".document-close").click()
            else:
                page.keyboard.press("Escape")
            assert page.evaluate("({x:scrollX,y:scrollY})") == position
            assert opener.evaluate("(button) => button === document.activeElement")
            assert page.evaluate("getComputedStyle(document.documentElement).overflowY") != "hidden"
            page.mouse.move(width - 2, 200)
            page.mouse.wheel(0, 300)
            page.wait_for_function("(previous) => scrollY > previous", arg=position["y"])
    page.set_viewport_size(original_viewport)


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
        check_card_badges(page)
        scope_text = page.locator("#document-scope").inner_text()
        assert str(len(DATA["documents"])) in scope_text
        assert f"{DATA['coverage']['sourceDocumentOccurrences']} apariciones documentales" in scope_text
        assert "2017–2024" in scope_text
        assert page.locator("#document-block option").evaluate_all("(options) => options.map(option => option.value)") == ["", "5", "6", "7", "8", "9", "10", "11", "12"]
        assert page.locator('#document-block option[value="7"]').inner_text() == "7 · La Restauración (1874–1902)"
        assert page.locator("#document-grid h2").all_text_contents() == [
            f"Bloque {option['value']} · {option['text'].split(' · ', 1)[1]}"
            for option in page.locator("#document-block option").evaluate_all(
                "(options) => options.filter(option => option.value).map(option => ({value:option.value,text:option.textContent}))"
            )
            if any(int(option["value"]) in document["blocks"] for document in DATA["documents"])
        ]
        check_dialog_scroll(page)
        page.locator('.document-card[data-id="mapa-desamortizacion-madoz"] .document-open').click()
        map_record = next(d for d in DATA["documents"] if d["id"] == "mapa-desamortizacion-madoz")
        assert page.locator("#document-dialog .document-exams .exam-pill").all_text_contents() == [
            appearance_label(appearance) for appearance in map_record["appearances"]
        ]
        assert page.locator(".document-original-link").get_attribute("href") == map_record["image"]["originalSrc"]
        assert page.locator(".document-corpus-link").get_attribute("href") == map_record["image"]["corpusSrc"]
        assert "leyenda distinta" in page.locator(".document-corpus-link").inner_text()
        assert "70 millones de reales" in page.locator("#document-dialog .document-table").text_content()
        assert "400 millones de reales" not in page.locator("#document-dialog .document-table").text_content()
        page.locator(".document-close").click()
        page.locator(
            '.document-card[data-id="fotografias-guerra-civil-entrega-fusiles-y-burgos-1936"] .document-open'
        ).click()
        paired_figures = page.locator("#document-dialog .document-image-figure")
        assert paired_figures.count() == 2
        assert "18 de julio de 1936" in paired_figures.nth(0).locator("figcaption").inner_text()
        assert "Burgos en agosto de 1936" in paired_figures.nth(1).locator("figcaption").inner_text()
        assert paired_figures.nth(1).locator(".document-person-toggle").inner_text() == "Revelar personajes"
        first_photo = paired_figures.nth(0).bounding_box()
        second_photo = paired_figures.nth(1).bounding_box()
        assert second_photo["x"] > first_photo["x"]
        assert abs(second_photo["y"] - first_photo["y"]) <= 2
        original_viewport = page.viewport_size
        page.set_viewport_size({"width": 320, "height": 900})
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        first_photo = paired_figures.nth(0).bounding_box()
        second_photo = paired_figures.nth(1).bounding_box()
        assert second_photo["y"] >= first_photo["y"] + first_photo["height"] - 2
        page.set_viewport_size(original_viewport)
        page.locator(".document-close").click()
        for selected_type in ("texto", "imagen", "grafico", "all"):
            page.locator(f'[data-type="{selected_type}"]').click()
            page.reload()
            page.wait_for_selector(".document-card")
            assert page.locator(f'[data-type="{selected_type}"]').get_attribute("aria-pressed") == "true"
            assert page.evaluate("sessionStorage.getItem('pau-he.document-type')") == selected_type
            expected_count = len(DATA["documents"]) if selected_type == "all" else sum(
                document["type"] == selected_type for document in DATA["documents"]
            )
            assert page.locator(".document-card").count() == expected_count
            heading = page.locator(".document-block-heading h2").first
            heading_geometry = heading.evaluate(
                "(node) => {"
                "const box=node.getBoundingClientRect();"
                "const row=node.parentElement.getBoundingClientRect();"
                "return {offset:Math.abs(box.left+box.width/2-row.left-row.width/2),"
                "radius:getComputedStyle(node).borderRadius};"
                "}"
            )
            assert heading_geometry["offset"] <= 2
            assert heading_geometry["radius"] != "0px"
            for notes in page.locator(".document-block-heading a").all():
                assert notes.inner_text() == "Ver apuntes"
                assert notes.get_attribute("aria-label").startswith("Ver apuntes del bloque ")
                assert notes.locator("svg").get_attribute("aria-hidden") == "true"
                assert notes.evaluate("(node) => getComputedStyle(node).borderStyle") == "solid"
                assert notes.evaluate("(node) => getComputedStyle(node).backgroundColor") == "rgb(214, 238, 122)"
                assert notes.evaluate(
                    "(node) => {const title=node.previousElementSibling.getBoundingClientRect();"
                    "const button=node.getBoundingClientRect();return button.left-title.right;}"
                ) <= 13
        original_viewport = page.viewport_size
        page.set_viewport_size({"width": 320, "height": 900})
        for heading in page.locator(".document-block-heading").all():
            assert heading.evaluate(
                "(node) => {const title=node.querySelector('h2').getBoundingClientRect();"
                "const button=node.querySelector('a').getBoundingClientRect();"
                "return button.left>=title.right && button.right<=innerWidth"
                " && Math.abs(button.top+button.height/2-title.top-title.height/2)<2;}"
            )
        page.set_viewport_size(original_viewport)
        compact_counts = []
        for width in (1280, 1920, 2560, 320, 1280):
            page.set_viewport_size({"width": width, "height": 900})
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            fit = page.locator("#document-topics").evaluate("""(topics) => {
                const rows = () => {
                    let count = 1;
                    let previousRight = -Infinity;
                    for (const button of topics.children) {
                        if (button.hidden) continue;
                        const bounds = button.getBoundingClientRect();
                        if (bounds.left < previousRight - 1) count++;
                        previousRight = bounds.right;
                    }
                    return count;
                };
                const before = rows();
                const next = topics.querySelector('.document-topic-bubble[hidden]');
                let after = before;
                if (next) {
                    next.hidden = false;
                    after = rows();
                    next.hidden = true;
                }
                const visible = topics.querySelectorAll('.document-topic-bubble:not([hidden])');
                const last = visible[visible.length - 1].getBoundingClientRect();
                const toggle = topics.querySelector('#document-topic-toggle').getBoundingClientRect();
                return {count:visible.length, more:Boolean(next), before, after,
                    alignment:Math.abs(last.bottom-toggle.bottom)};
            }""")
            compact_counts.append(fit["count"])
            if fit["more"]:
                assert fit["after"] > fit["before"], fit
                assert fit["alignment"] <= 2, fit
        assert max(compact_counts) > 8, compact_counts
        page.set_viewport_size(original_viewport)
        page.locator('[data-type="all"]').click()
        for width in (320, 1280, 2560):
            page.set_viewport_size({"width": width, "height": 900})
            for preview in page.locator(".document-preview:has(img)").all():
                preview.scroll_into_view_if_needed()
                geometry = preview.evaluate("""async (box) => {
                    const image = box.querySelector('img');
                    await image.decode();
                    const preview = box.getBoundingClientRect();
                    const figure = box.querySelector('figure').getBoundingClientRect();
                    const crop = box.querySelector('.doc-image-crop');
                    const bounds = (crop || image).getBoundingClientRect();
                    return {
                        id: box.closest('.document-card').dataset.id,
                        table: box.classList.contains('document-preview-table'),
                        horizontal: Math.abs(bounds.left+bounds.width/2-preview.left-preview.width/2),
                        vertical: Math.abs(bounds.top+bounds.height/2-preview.top-preview.height/2),
                        top: Math.abs(bounds.top-figure.top),
                        contained: bounds.top>=preview.top && bounds.bottom<=preview.bottom
                            && bounds.left>=preview.left && bounds.right<=preview.right,
                        ratio: bounds.width/bounds.height,
                    };
                }""")
                document = next(item for item in DATA["documents"] if item["id"] == geometry["id"])
                expected_table = bool(document.get("tableImage") or document.get("image", {}).get("kind") == "table")
                assert geometry["table"] == expected_table, (width, geometry)
                assert geometry["horizontal"] <= 1, (width, geometry)
                assert geometry["top" if expected_table else "vertical"] <= 1, (width, geometry)
                assert geometry["contained"], (width, geometry)
                crop = document.get("image", {}).get("crop")
                image_data = document.get("image") or document["tableImage"]
                ratio = image_data["width"] / image_data["height"]
                if crop:
                    ratio *= crop["width"] / crop["imageWidth"] * crop["imageHeight"] / crop["height"]
                assert abs(geometry["ratio"] - ratio) < 0.01, (width, geometry)
        page.set_viewport_size(original_viewport)
        for document in DATA["documents"]:
            crop = document.get("image", {}).get("crop")
            if not crop:
                continue
            page.locator(f'.document-card[data-id="{document["id"]}"] .document-open').click()
            for zoomed in (False, True):
                if zoomed:
                    page.locator(".document-zoom").click()
                frame = page.locator(".document-full-source .doc-image-crop")
                geometry = frame.evaluate("""frame => {
                    const bounds = frame.getBoundingClientRect();
                    const image = frame.querySelector('img').getBoundingClientRect();
                    return {ratio:bounds.width/bounds.height,
                        left:(image.left-bounds.left)/bounds.width,
                        top:(image.top-bounds.top)/bounds.height,
                        width:image.width/bounds.width,
                        height:image.height/bounds.height,
                        overflow:getComputedStyle(frame).overflow};
                }""")
                assert geometry["overflow"] == "hidden"
                for key, expected in {
                    "ratio": document["image"]["width"] / document["image"]["height"]
                        * crop["width"] / crop["imageWidth"] * crop["imageHeight"] / crop["height"],
                    "left": crop["left"] / crop["width"],
                    "top": crop["top"] / crop["height"],
                    "width": crop["imageWidth"] / crop["width"],
                    "height": crop["imageHeight"] / crop["height"],
                }.items():
                    assert abs(geometry[key] - expected) < 0.001, (document["id"], zoomed, key, geometry)
            page.locator(".document-close").click()
        casas_viejas = next(item for item in DATA["documents"] if item["id"] == "casas-viejas-detenciones-1933")
        page.locator('.document-card[data-id="casas-viejas-detenciones-1933"] .document-open').click()
        assert page.locator(".document-full-source img").evaluate(
            "(image) => [image.naturalWidth, image.naturalHeight]"
        ) == [940, 615]
        assert page.get_by_role("link", name="Fuente de esta reproducción", exact=True).get_attribute("href") == casas_viejas["image"]["sourceUrl"]
        assert page.locator(".document-reproduction-note").inner_text() == casas_viejas["image"]["reproductionNote"]
        page.locator(".document-close").click()
        page.locator('[data-type="imagen"]').click()
        assert page.locator(".document-card").count() == sum(document["type"] == "imagen" for document in DATA["documents"])
        page.locator("#document-search").fill("GOYA")
        assert page.locator(".document-card").count() == len(search_matches("GOYA"))
        opener = page.locator(f'.document-card[data-id="{GOYA_DOCUMENT["id"]}"] .document-open')
        preview_zoom = page.locator(f'.document-card[data-id="{GOYA_DOCUMENT["id"]}"] .document-preview-zoom')
        ratio = page.locator(f'.document-card[data-id="{GOYA_DOCUMENT["id"]}"] .document-preview img').evaluate(
            "(image) => Math.abs(image.getBoundingClientRect().width / image.getBoundingClientRect().height"
            " - image.naturalWidth / image.naturalHeight)"
        )
        assert ratio < 0.01
        assert preview_zoom.get_attribute("aria-label") == "Ampliar imagen: Los fusilamientos del 3 de mayo"
        preview_zoom.click()
        assert page.locator(".document-dialog").count() == 0
        assert page.locator("#document-dialog").is_visible()
        assert not page.locator(".document-full-source").evaluate("(node) => node.classList.contains('is-zoomed')")
        page.locator(".document-close").click()
        assert preview_zoom.evaluate("(button) => button === document.activeElement")
        opener.click()
        assert page.locator("#document-dialog").is_visible()
        assert page.locator(".document-task h3").inner_text() == "Enunciado de PAU · 4 puntos"
        assert page.locator(".document-task").get_attribute("aria-label") == "Enunciado de PAU · 4 puntos"
        for theme in ("light", "dark"):
            page.evaluate("(theme) => document.documentElement.dataset.theme = theme", theme)
            assert page.locator(".document-task").evaluate("""node => {
                const task = getComputedStyle(node);
                const source = getComputedStyle(document.querySelector('.document-full-source'));
                return task.backgroundColor === source.backgroundColor && task.borderColor === source.borderColor;
            }""")
        page.evaluate("document.documentElement.dataset.theme = 'light'")
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
        assert page.locator(".document-appearances").count() == 0
        assert "Formato histórico, anterior a 2026" not in page.locator("#document-dialog-content").inner_text()
        pills = page.locator("#document-dialog-content > .document-exams .exam-pill")
        assert pills.count() == len(GOYA_DOCUMENT["appearances"])
        assert pills.all_text_contents() == [
            " · ".join(part for part in (
                str(appearance["year"]),
                re.sub(rf"^{appearance['year']}\s+", "", appearance["exam"]),
                "" if appearance["route"].endswith("sin cotejar") else appearance["route"],
                f"Documento {appearance['document']}",
            ) if part)
            for appearance in GOYA_DOCUMENT["appearances"]
        ]
        assert pills.locator("a").count() == 0
        assert "DM Mono" in pills.first.evaluate("(node) => getComputedStyle(node).fontFamily")
        assert pills.first.evaluate("(node) => getComputedStyle(node).borderRadius") == "999px"
        for theme, border in (("light", "rgb(206, 192, 223)"), ("dark", "rgb(87, 71, 103)")):
            page.evaluate("(theme) => document.documentElement.dataset.theme = theme", theme)
            assert pills.first.evaluate("(node) => getComputedStyle(node).borderColor") == border
        page.evaluate("document.documentElement.dataset.theme = 'light'")
        page.keyboard.press("Escape")
        assert not page.locator("#document-dialog").is_visible()
        assert opener.evaluate("(button) => button === document.activeElement")
        page.locator("#document-reset").click()
        page.locator('[data-type="imagen"]').click()
        image_card = page.locator('.document-card[data-id="goya-tres-de-mayo"]')
        preview = image_card.locator(".document-preview")
        preview.scroll_into_view_if_needed()
        preview_bounds = preview.bounding_box()
        page.mouse.click(preview_bounds["x"] + preview_bounds["width"] / 2,
                        preview_bounds["y"] + preview_bounds["height"] / 2)
        assert page.locator("#document-dialog").is_visible()
        page.locator(".document-close").click()

        page.locator('[data-type="grafico"]').click()
        graph_card = page.locator('.document-card[data-id="resultados-electorales-restauracion-1881-1898"]')
        card_title = graph_card.locator("h3")
        card_title.scroll_into_view_if_needed()
        title_bounds = card_title.bounding_box()
        page.mouse.click(title_bounds["x"] + title_bounds["width"] / 2,
                        title_bounds["y"] + title_bounds["height"] / 2)
        assert page.locator("#document-dialog").is_visible()
        page.locator(".document-close").click()

        for document_id in (
            "resultados-electorales-restauracion-1881-1898",
            "bajas-espanolas-en-cuba-y-filipinas",
            "resultados-de-las-elecciones-generales-de-1982",
        ):
            document = next(item for item in DATA["documents"] if item["id"] == document_id)
            card = page.locator(f'.document-card[data-id="{document_id}"]')
            card.locator(".document-open").click()
            source = page.locator(".document-full-source")
            capture = document["tableImage"]
            image = source.locator(f'img[src$="{capture["src"].split("/")[-1]}"]')
            assert image.evaluate("(node) => [node.naturalWidth, node.naturalHeight]") == [
                capture["width"], capture["height"]
            ]
            check_collection_link(page, document)
            details = source.locator("details.document-table-details")
            assert details.locator("summary").inner_text() == "Leer la tabla en texto"
            details.locator("summary").click()
            assert details.locator("tbody tr").count() == len(document["table"]["rows"])
            assert details.locator("p").all_text_contents() == document["table"].get("notes", [])
            page.locator(".document-close").click()

        official_id = "elecciones-generales-1982-congreso-senado"
        official = next(item for item in DATA["documents"] if item["id"] == official_id)
        page.locator(f'.document-card[data-id="{official_id}"] .document-open').click()
        official_image = page.locator(".document-full-source img")
        assert official_image.evaluate("(node) => [node.naturalWidth, node.naturalHeight]") == [2084, 1418]
        check_collection_link(page, official)
        assert page.locator(".document-reproduction-note").inner_text() == official["image"]["reproductionNote"]
        assert page.get_by_role("link", name="Ver recorte del PDF original", exact=True).get_attribute("href") == official["image"]["originalSrc"]
        assert page.locator("#document-dialog-content > .document-exams .exam-pill").all_text_contents() == [
            appearance_label(appearance) for appearance in official["appearances"]
        ]
        official_details = page.locator(".document-table-details")
        official_details.locator("summary").click()
        assert official_details.locator("tbody tr").count() == len(official["table"]["rows"])
        page.locator(".document-close").click()

        desamortizaciones = next(item for item in DATA["documents"]
                                 if item["id"] == "grafico-desamortizaciones-siglo-xix")
        page.locator(f'.document-card[data-id="{desamortizaciones["id"]}"] .document-open').click()
        image = page.locator(".document-full-source img")
        assert image.evaluate("(node) => [node.naturalWidth, node.naturalHeight]") == [1492, 1088]
        check_collection_link(page, desamortizaciones)
        assert page.locator("#document-dialog-content > .document-exams .exam-pill").first.inner_text() == "2008 · Examen 6 · Opción A · Documento 2"
        page.locator(".document-close").click()
        page.locator("#document-reset").click()
        page.locator("#document-search").fill("constitucion")
        assert page.locator(".document-card").count() == len(search_matches("constitucion"))
        page.locator("#document-search").fill("")
        page.locator('[data-type="imagen"]').click()
        alignment = page.locator("#document-topic-toggle").evaluate(
            "(button) => {"
            "const bubbles=[...button.parentElement.querySelectorAll('.document-topic-bubble:not([hidden])')];"
            "const last=bubbles[bubbles.length-1].getBoundingClientRect();"
            "const current=button.getBoundingClientRect();"
            "return Math.abs(last.bottom-current.bottom);"
            "}"
        )
        assert alignment <= 2
        page.locator("#document-reset").click()
        assert page.evaluate("sessionStorage.getItem('pau-he.document-type')") == "all"
        topic_search = page.locator("#document-topic-search")
        topic_sort = page.locator("#document-topic-sort")
        topic_toggle = page.locator("#document-topic-toggle")
        all_topics = {tag for document in DATA["documents"] for tag in document["tags"]}
        topic_stats = topic_statistics()
        representation_count = topic_stats["Representación política"][0]
        representation_label = (
            f"Representación política: {representation_count} "
            f"{'aparición' if representation_count == 1 else 'apariciones'} en 1 ficha del corpus"
        )
        assert page.locator("#document-topics button").nth(1).inner_text().startswith("1808 (")
        assert topic_toggle.is_visible()
        assert topic_toggle.inner_text() == "Ver más ↓"
        reset_button = page.locator("#document-reset")
        assert reset_button.inner_text() == "Limpiar filtros"
        assert reset_button.locator("svg").get_attribute("aria-hidden") == "true"
        page.mouse.move(1, 1)
        assert reset_button.evaluate("(button) => getComputedStyle(button).backgroundColor") == "rgb(251, 228, 225)"
        reset_button.hover()
        assert reset_button.evaluate("(button) => getComputedStyle(button).backgroundColor") == "rgb(217, 83, 74)"
        assert page.locator(".document-topic-heading #document-reset").count() == 1
        assert page.locator(".document-results-bar #document-reset").count() == 0
        assert topic_toggle.evaluate("(button) => button.parentElement.id === 'document-topics'")
        assert topic_toggle.evaluate("(button) => button === button.parentElement.lastElementChild")
        assert page.locator("#document-topics button.document-topic-bubble:visible").count() >= 8
        topic_sort.select_option("frequency")
        most_frequent = max(topic_stats, key=lambda tag: topic_stats[tag][0])
        assert page.locator("#document-topics button").nth(1).inner_text().startswith(most_frequent)
        topic_toggle.click()
        assert topic_toggle.inner_text() == "Ver menos ↑"
        bubble_sizes = page.locator("#document-topics button.document-topic-bubble").evaluate_all(
            "(buttons) => buttons.map(button => ({"
            "count: Number(button.textContent.match(/\\((\\d+)\\)$/)[1]),"
            "size: parseFloat(getComputedStyle(button).fontSize)"
            "}))"
        )
        assert max(bubble_sizes, key=lambda bubble: bubble["count"])["size"] > min(
            bubble_sizes, key=lambda bubble: bubble["count"]
        )["size"]
        topic_sort.select_option("chronology")
        first_chronological = re.sub(
            r" \(\d+\)$", "", page.locator("#document-topics button").nth(1).inner_text(),
        )
        dated_topics = [first_year for _, first_year in topic_stats.values()
                        if first_year != float("inf")]
        assert topic_stats[first_chronological][1] == min(dated_topics)
        topic_sort.select_option("alphabetical")
        assert topic_toggle.get_attribute("aria-expanded") == "true"
        assert page.locator("#document-topics button").nth(1).inner_text().startswith("1808 (")
        assert page.locator("#document-topics button.document-topic-bubble").count() == len(all_topics)
        topic_search.fill("representacion")
        assert page.locator("#document-topics button.document-topic-bubble").count() == 1
        assert topic_toggle.is_hidden()
        topic_button = page.get_by_role(
            "button", name=representation_label, exact=True,
        )
        assert topic_button.is_visible()
        topic_search.fill("")
        page.get_by_role(
            "button", name=representation_label, exact=True,
        ).click()
        assert page.locator(".document-card").count() == 1
        page.locator(".document-open").click()
        accessible_table = page.locator(".document-table-details")
        accessible_table.locator("summary").click()
        assert accessible_table.locator("tbody tr").count() == 13
        assert accessible_table.locator("tbody tr").first.inner_text() == "Eclesiásticos\t90"
        page.locator(".document-close").click()
        page.locator("#document-reset").click()
        page.select_option("#document-block", "10")
        page.locator('.document-card[data-id="constitucion-1931-articulos-suplente-a"] .document-open').click()
        paragraphs = page.locator(".document-full-source blockquote p").all_text_contents()
        assert "trabajadores de toda clase, que se organiza" in paragraphs[0]
        assert paragraphs[1] == "Los poderes de todos sus órganos emanan del pueblo."
        assert paragraphs[4] == "Artículo 2. Todos los españoles son iguales ante la ley."
        assert paragraphs[-1].endswith("legítima del Estado […].")
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "12")
        assert page.locator(".document-card").count() == sum(12 in document["blocks"] for document in DATA["documents"])
        page.get_by_role("button", name="Ver documento: El preámbulo de la Constitución de 1978", exact=True).click()
        paragraphs = page.locator(".document-full-source blockquote p").all_text_contents()
        assert "orden económico y social justo." in paragraphs[3]
        assert paragraphs[-1].endswith("pueblos de la Tierra.")
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "11")
        assert page.locator(".document-card").count() == sum(11 in document["blocks"] for document in DATA["documents"])
        page.locator("#document-search").fill("no existe este documento")
        assert page.locator(".document-card").count() == 0
        assert page.locator("#document-empty").is_visible()
        page.locator("#document-reset").click()
        page.locator('[data-type="texto"]').click()
        for width in (320, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            check_text_card(page)
        page.locator(f'.document-card[data-id="{TEXT_DOCUMENT["id"]}"] .document-open').click()
        assert page.locator(".document-full-source blockquote p").count() == len(TEXT_DOCUMENT["text"])
        page.locator(".document-close").click()
        page.goto(f"{BASE}/documentos.html?bloque=5")
        page.wait_for_selector(".document-card")
        assert page.locator("#document-block").input_value() == "5"
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        for width in (320, 375, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
            assert page.locator(".document-card .document-exams .exam-pill").evaluate_all("""pills =>
                pills.every(pill => {
                    const box = pill.getBoundingClientRect();
                    const card = pill.closest('.document-card').getBoundingClientRect();
                    return box.left >= card.left && box.right <= card.right && pill.scrollWidth <= pill.clientWidth;
                })
            """), width
            check_text_card(page)
            page.locator(f'.document-card[data-id="{TEXT_DOCUMENT["id"]}"] .document-open').click()
            assert page.locator("#document-dialog").evaluate("(el) => el.scrollWidth <= el.clientWidth"), width
            page.locator(".document-close").click()
        check_fitted_media_and_people(browser)
        check_external_people(browser)
        check_document_attributions(browser)
        assert not errors, errors
        context.close()

        # A document with several appearances remains one searchable card.
        multi = json.loads(json.dumps(DATA))
        multi_target = next(document for document in multi["documents"]
                            if document["id"] == "bando-de-murat-tras-el-levantamiento-del-2-de-mayo")
        extra_source_key = "test-extra-source"
        multi_target["appearances"].append({
            **multi_target["appearances"][0],
            "id": "test-extra-appearance",
            "sourceKey": extra_source_key,
        })
        multi["coverage"]["sourceManifest"].append({
            **next(source for source in multi["coverage"]["sourceManifest"]
                   if source["key"] == multi_target["appearances"][0]["sourceKey"]),
            "key": extra_source_key,
            "images": [],
        })
        multi["coverage"]["sourceDocumentOccurrences"] += 1
        multi_target["blocks"].append(6)
        multi_context = browser.new_context(service_workers="block")
        multi_page = multi_context.new_page()
        multi_page.route("**/data/documentos.json", lambda route: route.fulfill(json=multi))
        multi_page.goto(f"{BASE}/documentos.html")
        multi_page.wait_for_selector(".document-card")
        assert multi_page.locator(".document-card").count() == len(DATA["documents"])
        assert multi_page.locator(
            f'.document-card[data-id="{multi_target["id"]}"] .document-exams .exam-pill'
        ).count() == 2
        total_appearances = sum(len(document["appearances"]) for document in DATA["documents"])
        assert f"{total_appearances + 1} apariciones" in multi_page.locator("#document-count").inner_text()
        multi_page.locator(f'.document-card[data-id="{multi_target["id"]}"] .document-open').click()
        assert multi_page.locator("#document-dialog-content > .document-exams li").count() == 2
        assert multi_page.locator("#document-dialog .document-exams .exam-pill").count() == 2
        multi_page.locator(".document-close").click()
        multi_page.select_option("#document-block", "6")
        assert multi_page.locator(".document-card").count() == sum(
            6 in document["blocks"] for document in DATA["documents"]
        ) + 1
        assert multi_page.locator(".document-block-heading h2").inner_text().startswith("Bloque 6 ·")
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
        assert offline_page.locator(".site-footer .credit").evaluate("(node) => getComputedStyle(node).fontSize") == "13px"
        offline_page.goto(f"{BASE}/apuntes/bloque-1.html")
        assert offline_page.locator(".site-footer").is_visible()
        assert offline_page.locator(".site-footer .credit").evaluate("(node) => getComputedStyle(node).fontSize") == "13px"
        offline.close()
        browser.close()
    print("OK: banco por tipos, bloques 5–12, temáticas, búsqueda, a)/b), ampliación, apariciones, errores y sin conexión.")


if __name__ == "__main__":
    run()
