"""Run against the local server on port 8765."""
import json
import re
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE = "http://localhost:8765"
RAW_DATA = json.loads((Path(__file__).resolve().parent.parent / "data/documentos.json").read_text())
OWN_DATA = json.loads((Path(__file__).resolve().parent.parent / "data/documentos-propios.json").read_text())


def text_content_size(record):
    end = len(record["text"]) - record.get("attributionParagraphs", 0)
    body = " ".join(line for index, line in enumerate(record["text"])
                    if index < end and index not in record.get("headingParagraphs", []))
    return len(re.findall(r"[^\W_]+", body))


def ordered_versions(records, identities):
    ranked = sorted((records[identity] for identity in identities), key=text_content_size, reverse=True)
    primary = records[records[identities[0]]["primaryTextId"]] if "primaryTextId" in records[identities[0]] else ranked[0]
    return [primary] + [version for version in ranked if version["id"] != primary["id"]]


def grouped_records(data):
    records = {record["id"]: record for record in data["documents"]}
    secondary = set()
    replacements = {}
    for identities in data.get("textGroups", []):
        canonical = records[identities[0]]
        versions = ordered_versions(records, identities)
        primary = versions[0]
        replacements[identities[0]] = {
            **primary, "id": canonical["id"], "memberIds": identities, "textVersions": versions,
            **({"studyCompilation": canonical["studyCompilation"]} if "studyCompilation" in canonical else {}),
            **({"titleMarker": canonical["titleMarker"]} if "titleMarker" in canonical else {}),
            **({"historicalNote": canonical["historicalNote"]} if "historicalNote" in canonical else {}),
            "tags": list(dict.fromkeys(tag for version in versions for tag in version["tags"])),
            "blocks": list(dict.fromkeys(block for version in versions for block in version["blocks"])),
            "appearances": sorted((appearance for version in versions for appearance in version["appearances"]),
                                  key=lambda appearance: (appearance["year"], appearance["exam"])),
        }
        secondary.update(identities[1:])
    return [replacements.get(record["id"], record) for record in data["documents"] if record["id"] not in secondary]


DATA = {**RAW_DATA, "documents": grouped_records(RAW_DATA), "textGroups": []}


def reading_paragraphs(record, *, use_compilation=True):
    if use_compilation:
        record = record.get("studyCompilation") or record
    numbered = re.compile(r"""^\s*[«“"']*\d+[ºª]?\)\s""")
    starts = sorted(set(record.get("paragraphStarts", range(len(record["text"])))) |
                    {index for index, line in enumerate(record["text"]) if numbered.match(line)})
    paragraphs = []
    indices = []
    for start, end in zip(starts, starts[1:] + [len(record["text"])]):
        paragraph = " ".join(record["text"][start:end])
        parts = re.split(r"\s+(?=\d+[ºª]?\)\s)", paragraph) if numbered.match(paragraph) else [paragraph]
        paragraphs.extend(parts)
        indices.extend([start] * len(parts))
    attribution_start = len(record["text"]) - record.get("attributionParagraphs", 0)
    source = [i for i, index in enumerate(indices) if index < attribution_start]
    first = next((i for i in source if indices[i] not in record.get("headingParagraphs", [])
                  or re.match(r"""^\s*[“«"‘']""", paragraphs[i])), None)
    if first is not None:
        opener = re.match(r"""^(\s*)([“«"‘'])""", paragraphs[first])
        if opener:
            paragraphs[first] = opener.group(1) + paragraphs[first][opener.end():]
            closer = {"“": "”", "«": "»", '"': '"', "‘": "’", "'": "'"}[opener.group(2)]
            terminal = re.compile(re.escape(closer) + r"(?=[\s.!?,;:…)]*$)")
            last_source = source[-1]
            target = last_source if terminal.search(paragraphs[last_source]) else len(paragraphs) - 1
            paragraphs[target] = terminal.sub("", paragraphs[target], count=1)
    return paragraphs

TEXT_DOCUMENT = next(document for document in DATA["documents"]
                     if document["id"] == "constitucion-1812-articulos-2008")
GOYA_DOCUMENT = next(document for document in DATA["documents"]
                     if document["id"] == "goya-tres-de-mayo")


def normalize(value):
    return "".join(character for character in unicodedata.normalize("NFD", value.lower())
                   if not unicodedata.combining(character))

def reveal_historical(page):
    toggle = page.locator(".document-history-toggle")
    if toggle.count() and toggle.get_attribute("aria-expanded") == "false":
        toggle.click()


def check_numbered_paragraphs(browser):
    fixture = json.loads(json.dumps(RAW_DATA))
    record = next(item for item in fixture["documents"]
                  if item["id"] == "bando-de-murat-tras-el-levantamiento-del-2-de-mayo")
    record.update({
        "text": ["Introducción: véase el apartado 2) del texto.", "2) Segundo apartado",
                 "con su continuación.", "3º) Tercer apartado. 11º) Undécimo apartado.",
                 "4ª) Cuarto apartado.", "Referencia final"],
        "paragraphStarts": [0, 5], "attributionParagraphs": 1,
        "primaryTextId": record["id"],
    })
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    page.route("**/data/documentos.json", lambda route: route.fulfill(json=fixture))
    page.goto(f"{BASE}/documentos.html")
    card = page.locator(f'.document-card[data-id="{record["id"]}"]')
    card.wait_for()
    assert card.locator("blockquote p").all_text_contents() == [
        "Introducción: véase el apartado 2) del texto.", "2) Segundo apartado con su continuación.",
        "3º) Tercer apartado.",
    ]
    card.locator(".document-open").click()
    paragraphs = page.locator(".document-full-source > blockquote p")
    assert paragraphs.all_text_contents() == [
        "Introducción: véase el apartado 2) del texto.", "2) Segundo apartado con su continuación.",
        "3º) Tercer apartado.", "11º) Undécimo apartado.", "4ª) Cuarto apartado.", "Referencia final",
    ]
    assert paragraphs.last.get_attribute("class") == "document-attribution"
    assert " ".join(paragraphs.all_text_contents()) == " ".join(record["text"])
    context.close()


def check_outer_quotes_with_heading(browser):
    fixture = json.loads(json.dumps(RAW_DATA))
    record = next(item for item in fixture["documents"]
                  if item["id"] == "bando-de-murat-tras-el-levantamiento-del-2-de-mayo")
    record.update({
        "text": ["Encabezado original", "“Primera frase con «cita interior».",
                 "Última frase”.", "Autor"],
        "headingParagraphs": [0], "attributionParagraphs": 1,
        "primaryTextId": record["id"],
    })
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    page.route("**/data/documentos.json", lambda route: route.fulfill(json=fixture))
    page.goto(f"{BASE}/documentos.html")
    card = page.locator(f'.document-card[data-id="{record["id"]}"]')
    card.wait_for()
    assert card.locator("blockquote p").all_text_contents() == [
        "Encabezado original", "Primera frase con «cita interior».", "Última frase.",
    ]
    card.locator(".document-open").click()
    assert page.locator(".document-full-source > blockquote p").all_text_contents() == [
        "Encabezado original", "Primera frase con «cita interior».", "Última frase.", "Autor",
    ]
    context.close()


def check_reader_navigation(browser):
    records = {record["id"]: record for record in DATA["documents"]}
    for width in (1440, 375):
        context = browser.new_context(viewport={"width": width, "height": 900},
                                      service_workers="block", reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        first_ids = page.locator(".document-card:visible").evaluate_all(
            "(cards)=>cards.slice(0,2).map(card=>card.dataset.id)")
        page.locator(".document-open:visible").first.click()
        assert page.locator(".document-previous").is_disabled()
        page.locator(".document-next").click()
        assert page.locator("#document-dialog-title").inner_text() == records[first_ids[1]]["title"]
        page.keyboard.press("ArrowLeft")
        assert page.locator("#document-dialog-title").inner_text() == records[first_ids[0]]["title"]
        page.keyboard.press("ArrowLeft")
        assert page.locator("#document-dialog-title").inner_text() == records[first_ids[0]]["title"]
        for key in ("Shift+ArrowRight", "Alt+ArrowRight", "Control+ArrowRight", "Meta+ArrowRight"):
            page.keyboard.press(key)
            assert page.locator("#document-dialog-title").inner_text() == records[first_ids[0]]["title"]
        for markup in ('<input>', '<textarea></textarea>', '<select><option>A</option><option>B</option></select>',
                       '<div contenteditable="true"><span>Texto editable</span></div>'):
            page.locator("#document-dialog-content").evaluate("""(node, markup) => {
                node.insertAdjacentHTML('beforeend', markup);
                node.lastElementChild.focus();
            }""", markup)
            page.keyboard.press("ArrowRight")
            assert page.locator("#document-dialog-title").inner_text() == records[first_ids[0]]["title"]
            page.locator("#document-dialog-content > :last-child").evaluate("node => node.remove()")
        page.locator(".document-close").focus()
        page.keyboard.press("ArrowRight")
        assert page.locator("#document-dialog-title").inner_text() == records[first_ids[1]]["title"]
        page.keyboard.press("Escape")

        page.select_option("#document-year", "2008")
        page.select_option("#document-exam", "examen 1")
        identities = page.locator(".document-card").evaluate_all("(cards)=>cards.map(card=>card.dataset.id)")
        assert len(identities) == 4
        page.locator(".document-open").first.click()
        position = page.evaluate("scrollY")
        for index, identity in enumerate(identities):
            assert page.locator("#document-dialog-title").inner_text() == records[identity]["title"]
            assert page.locator(".document-previous").is_disabled() == (index == 0)
            assert page.locator(".document-next").is_disabled() == (index == len(identities) - 1)
            assert page.locator(".document-reader-status").inner_text().startswith(
                f"Documento {index + 1} de {len(identities)}:")
            buttons = page.locator(".document-reader-controls button")
            bounds = [button.bounding_box() for button in buttons.all()]
            assert bounds[0]["x"] < bounds[1]["x"] < bounds[2]["x"]
            assert bounds[0]["x"] >= 0 and bounds[2]["x"] + bounds[2]["width"] <= width
            if index < len(identities) - 1:
                page.keyboard.press("ArrowRight")
        page.keyboard.press("ArrowRight")
        assert page.locator("#document-dialog-title").inner_text() == records[identities[-1]]["title"]
        page.locator(".document-previous").click()
        page.reload()
        page.wait_for_selector("#document-dialog[open]")
        assert page.locator("#document-dialog-title").inner_text() == records[identities[-2]]["title"]
        for identity in reversed(identities[:-2]):
            page.locator(".document-previous").click()
            assert page.locator("#document-dialog-title").inner_text() == records[identity]["title"]
        page.locator(".document-close").click()
        page.wait_for_function(
            "identity=>document.activeElement?.closest('.document-card')?.dataset.id===identity", arg=identities[0])
        assert page.locator(f'.document-card[data-id="{identities[0]}"] .document-open').evaluate(
            "node=>node===document.activeElement")
        assert abs(page.evaluate("scrollY") - position) < 2
        page.locator("#document-reset").click()
        page.select_option("#document-year", "2013")
        page.locator("#document-search").fill("Esquilache")
        reveal_historical(page)
        assert page.locator(".document-card").count() == 1
        page.locator(".document-open").click()
        assert page.locator(".document-previous").is_disabled()
        assert page.locator(".document-next").is_disabled()
        page.keyboard.press("Escape")

        page.locator("#document-reset").click()
        for identity in first_ids:
            page.locator(f'.document-card[data-id="{identity}"] [data-document-mark="favorite"]').click()
        page.goto(f"{BASE}/mis-documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert page.locator(".document-card").count() == 2
        page.locator(".document-open").first.click()
        page.keyboard.press("ArrowRight")
        assert page.locator("#document-dialog-title").inner_text() == records[first_ids[1]]["title"]
        page.locator('#document-dialog [data-document-mark="favorite"]').click()
        assert page.locator(".document-card").count() == 1
        assert page.locator(".document-previous").is_disabled()
        assert page.locator(".document-next").is_disabled()
        assert "ya no figura" in page.locator(".document-reader-status").inner_text()
        page.locator(".document-close").click()
        assert not errors, errors
        context.close()


def check_text_content_ranking(browser):
    fixture = json.loads(json.dumps(RAW_DATA))
    records = {record["id"]: record for record in fixture["documents"]}
    shortest = records["manifiesto-de-sandhurst"]
    shortest["text"] = ["Encabezado extenso " * 300] + shortest["text"] + ["Referencia extensa " * 300]
    shortest["headingParagraphs"] = [0]
    shortest["attributionParagraphs"] = 1
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    page.route("**/data/documentos.json", lambda route: route.fulfill(json=fixture))
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    page.locator('.document-card[data-id="manifiesto-de-sandhurst-llamamiento-a-la-restauracion"] .document-open').click()
    group = next(group for group in fixture["textGroups"]
                 if group[0] == "manifiesto-de-sandhurst-llamamiento-a-la-restauracion")
    versions = ordered_versions(records, group)
    complete = versions[0]
    assert complete["id"] != shortest["id"]
    assert page.locator(".document-full-source > blockquote p").all_text_contents() == reading_paragraphs(complete)
    page.locator(".document-text-versions > summary").click()
    assert page.locator(".document-text-version").evaluate_all(
        "nodes=>nodes.map(node=>node.dataset.versionId)") == [version["id"] for version in versions[1:]]
    legacy = page.evaluate("JSON.parse(sessionStorage.getItem('pau-he.documents.view.v1'))")
    legacy["dialog"].pop("selectionsGrouped", None)
    legacy["dialog"]["details"] = [False, True, False, True]
    page.add_init_script(
        f"sessionStorage.setItem('pau-he.documents.view.v1', {json.dumps(json.dumps(legacy))})")
    page.reload()
    page.wait_for_selector("#document-dialog[open]", state="attached")
    page.wait_for_function("!document.documentElement.hasAttribute('data-document-restoring')")
    assert page.locator(".document-text-versions").evaluate("node=>node.open")
    assert page.locator(".document-guide").evaluate("node=>node.open")
    context.close()


def check_grouped_texts_and_exam_filters(browser):
    raw_records = {record["id"]: record for record in RAW_DATA["documents"]}
    context = browser.new_context(service_workers="block", reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    reveal_historical(page)
    expected_ids = {record["id"] for record in DATA["documents"] + OWN_DATA["documents"]}
    assert set(page.locator(".document-card").evaluate_all(
        "cards => cards.map(card => card.dataset.id)")) == expected_ids
    assert page.locator(".document-card").count() == len(expected_ids)
    for identities in RAW_DATA["textGroups"]:
        canonical = raw_records[identities[0]]
        versions = ordered_versions(raw_records, identities)
        primary = versions[0]
        for identity in identities[1:]:
            assert page.locator(f'.document-card[data-id="{identity}"]').count() == 0
        page.locator(f'.document-card[data-id="{canonical["id"]}"] .document-open').click()
        assert page.locator(".document-full-source > blockquote p").all_text_contents() == reading_paragraphs(
            canonical.get("studyCompilation") or primary)
        expected_sources = [appearance["pdfUrl"] for identity in identities for appearance in raw_records[identity]["appearances"]]
        assert sorted(page.locator("#document-dialog-content > .document-exams a").evaluate_all(
            "(links)=>links.map(link=>link.href)")) == sorted(expected_sources)
        selections = {}
        for version in versions:
            text = (" ".join(" ".join(version["text"]).split()),
                    any(a.get("sourceReviewStatus") == "transcription-copy" for a in version["appearances"]))
            if text in selections:
                selections[text]["appearances"].extend(version["appearances"])
            else:
                selections[text] = {**version, "appearances": list(version["appearances"])}
        main, *alternatives = selections.values()
        if canonical.get("studyCompilation"):
            alternatives = [main, *alternatives]
        variants = page.locator(".document-text-versions")
        assert variants.count() == 1
        assert not variants.evaluate("(node)=>node.open")
        total = sum(len(raw_records[identity]["appearances"]) for identity in identities)
        assert page.locator("#document-dialog-content > .document-meta strong").inner_text() == (
            f'{total} {"aparición" if total == 1 else "apariciones"} en total')
        main_sources = variants.locator(":scope > .document-variant-sources")
        assert not main_sources.is_visible()
        variants.locator(":scope > summary").click()
        if canonical.get("studyCompilation"):
            assert main_sources.count() == 0
        else:
            assert main_sources.locator(".exam-pill").all_text_contents() == [
                appearance_label(appearance) for appearance in main["appearances"]]
            assert main_sources.locator("a").evaluate_all("(links)=>links.map(link=>link.href)") == [
                appearance["pdfUrl"] for appearance in main["appearances"]]
        assert page.locator(".document-text-version").count() == len(alternatives)
        assert page.locator(".document-text-version").evaluate_all(
            "(nodes)=>nodes.map(node=>node.dataset.versionId)") == [version["id"] for version in alternatives]
        for version in alternatives:
            identity = version["id"]
            details = page.locator(f'.document-text-version[data-version-id="{identity}"]')
            assert details.is_visible()
            assert details.locator("blockquote p").all_text_contents() == reading_paragraphs(version, use_compilation=False)
            assert details.locator(".exam-pill").all_text_contents() == [
                appearance_label(appearance) for appearance in version["appearances"]]
            assert details.locator("blockquote p:not(.document-attribution):not(.document-source-heading)").evaluate_all(
                "(paragraphs)=>paragraphs.every(p=>getComputedStyle(p).textAlign==='justify')")
        page.locator(".document-close").click()

    def exam_key(appearance):
        label = re.sub(rf"^{appearance['year']}\s+", "", appearance["exam"])
        return " ".join(normalize(re.sub(r"\s*\([^)]*\)\s*$", "", label)).split())

    years = page.locator("#document-year option").evaluate_all("(options)=>options.map(option=>option.value)")
    assert years == [""] + [str(year) for year in range(2001, 2028)]
    for year in range(2001, 2028):
        page.select_option("#document-year", str(year))
        options = page.locator("#document-exam option:not(:disabled)").evaluate_all("(options)=>options.map(option=>option.value)")
        expected_exams = {exam_key(appearance) for record in DATA["documents"] for appearance in record["appearances"]
                          if appearance["year"] == year}
        assert set(options[1:]) == expected_exams, (year, options, expected_exams)
        numbered_model = ("examen 1", "examen 2", "modelo orientaciones pau")
        priority = (list(numbered_model) if set(numbered_model) <= expected_exams else
                    [key for key in ("titular ordinaria", "titular extraordinaria", "modelo orientaciones pau")
                     if key in expected_exams])
        assert options[1:1 + len(priority)] == priority, (year, options)
        assert page.locator("#document-exam").is_disabled() == (not expected_exams)
        missing = next((entry.get("unavailableExams", []) for entry in RAW_DATA["coverage"]["officialExamAvailability"]
                        if entry["year"] == year), [])
        assert page.locator("#document-exam option:disabled").all_text_contents() == missing
        for selected in options:
            if expected_exams:
                page.select_option("#document-exam", selected)
            expected = {record["id"]: record["appearances"] for record in DATA["documents"]
                        if any(appearance["year"] == year and (not selected or exam_key(appearance) == selected)
                               for appearance in record["appearances"])}
            actual = page.locator(".document-card").evaluate_all("""cards=>Object.fromEntries(cards.map(card=>[
                card.dataset.id,[...card.querySelectorAll('.exam-pill')].map(pill=>pill.textContent)]))""")
            assert actual == {identity: [appearance_label(appearance) for appearance in appearances]
                              for identity, appearances in expected.items()}, (year, selected)
            if year == 2001 and selected == options[1]:
                assert len(actual) == 4
                hrefs = page.locator(".document-exams a").evaluate_all(
                    "(nodes)=>nodes.map(node=>node.href).filter(url=>url.includes('/assets/documentos/2000-2001-examen-1.pdf'))"
                )
                assert len(hrefs) == 4
                assert {url.rsplit('#', 1)[-1] for url in hrefs} == {"page=1", "page=2"}
                assert all(url.split('#', 1)[0].endswith("/assets/documentos/2000-2001-examen-1.pdf")
                           for url in hrefs)
            metadata = page.locator(".document-card").evaluate_all("""cards=>Object.fromEntries(cards.map(card=>[
                card.dataset.id,card.querySelector('.document-meta').textContent]))""")
            for identity, appearances in expected.items():
                label = "aparición incorporada" if len(appearances) == 1 else "apariciones incorporadas"
                assert f"{len(appearances)} {label}" in metadata[identity], (year, selected, identity)
            total = sum(len(appearances) for appearances in expected.values())
            assert page.locator("#document-count").inner_text() == (
                f'{len(expected)} {"documento" if len(expected) == 1 else "documentos"} · '
                f'{total} {"aparición" if total == 1 else "apariciones"} en total')
        if year == 2017:
            assert "no faltan comentarios de documentos porque no cayó ninguno" in page.locator("#document-exam-hint").inner_text()

    page.select_option("#document-year", "2012")
    page.select_option("#document-exam", "examen 4")
    page.select_option("#document-block", "5")
    page.locator("#document-search").fill("constitución")
    page.locator('[data-type="texto"]').click()
    card = page.locator('.document-card[data-id="constitucion-1812-articulos-2008"]')
    assert card.count() == 1
    card.locator(".document-open").click()
    assert page.locator(".document-full-source > blockquote p").all_text_contents() == reading_paragraphs(
        TEXT_DOCUMENT)
    details = page.locator('.document-text-version[data-version-id="constitucion-cadiz-articulos-1812"]')
    page.locator(".document-text-versions > summary").click()
    assert details.locator("blockquote p").first.inner_text().startswith("Art. 1.")
    assert all("2012" in text for text in details.locator(".exam-pill").all_text_contents())
    page.reload()
    page.wait_for_selector("#document-dialog[open]", state="attached")
    assert page.locator("#document-year").input_value() == "2012"
    assert page.locator("#document-exam").input_value() == "examen 4"
    assert page.locator("#document-search").input_value() == "constitución"
    page.locator(".document-close").click()
    for width in (320, 375, 768, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert page.locator("#document-year,#document-exam,#document-block").evaluate_all(
            "(controls)=>controls.every(el=>el.getBoundingClientRect().right<=innerWidth)"), width
    page.locator("#document-reset").click()
    assert page.locator("#document-year").input_value() == ""
    assert page.locator("#document-exam").is_disabled()
    assert set(page.locator(".document-card").evaluate_all(
        "cards => cards.map(card => card.dataset.id)")) == expected_ids
    assert page.locator(".document-card").count() == len(expected_ids)

    canonical, alias = RAW_DATA["textGroups"][5][:2]
    page.evaluate("""({canonical,alias})=>localStorage.setItem('pau-he.documents.marks.v1',JSON.stringify({
        [canonical]:{favorite:false,review:true},[alias]:{favorite:true,review:false}}))""",
                  {"canonical": canonical, "alias": alias})
    page.goto(f"{BASE}/mis-documentos.html")
    saved_card = page.locator(f'.document-card[data-id="{canonical}"]')
    saved_card.wait_for()
    assert page.locator(".document-card").count() == 1
    for flag in ("favorite", "review"):
        assert saved_card.locator(f'[data-document-mark="{flag}"]').get_attribute("aria-pressed") == "true"
    saved_card.locator('[data-document-mark="favorite"]').click()
    marks = page.evaluate("JSON.parse(localStorage.getItem('pau-he.documents.marks.v1'))")
    assert alias not in marks and marks[canonical] == {"favorite": False, "review": True}
    page.select_option("#document-year", "2026")
    assert saved_card.count() == 1
    saved_card.locator(".document-open").click()
    page.reload()
    page.wait_for_selector("#document-dialog[open]", state="attached")
    assert page.locator("#document-year").input_value() == "2026"
    page.locator(".document-close").click()
    canonical, alias = RAW_DATA["textGroups"][0][:2]
    page.evaluate("""({alias})=>{
        const key='pau-he.documents.view.v1';
        const state=JSON.parse(sessionStorage.getItem(key));
        delete state.year;
        delete state.exam;
        state.dialog={id:alias,position:{left:0,top:0},source:{left:0,top:0},details:[]};
        sessionStorage.setItem(key,JSON.stringify(state));
    }""", {"alias": alias})
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-dialog[open]", state="attached")
    assert page.locator("#document-year").input_value() == ""
    assert page.locator("#document-exam").is_disabled()
    assert page.locator('#document-dialog [data-document-mark="favorite"]').get_attribute("data-document-id") == canonical
    assert page.locator(f'.document-text-version[data-version-id="{alias}"]').evaluate(
        "(node)=>node.closest('details').open")
    assert not errors, errors
    context.close()


def check_document_attributions(browser):
    records = {record["id"]: record for record in DATA["documents"]}
    for width in (1440, 375):
        context = browser.new_context(viewport={"width": width, "height": 1000}, service_workers="block")
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        reveal_historical(page)
        for identifier, record in records.items():
            if record["type"] != "texto":
                continue
            page.locator(f'.document-card[data-id="{identifier}"] .document-open').click()
            check_collection_link(page, record)
            font = page.locator(".document-full-source > blockquote").evaluate(
                "node => getComputedStyle(node).fontFamily")
            assert font.startswith('"PAU Caption"'), (identifier, font)
            assert page.locator(f'.document-card[data-id="{identifier}"] blockquote').evaluate(
                "node => getComputedStyle(node).fontFamily") == font
            paragraphs = page.locator(".document-full-source > blockquote p")
            assert paragraphs.all_text_contents() == reading_paragraphs(record)
            if record.get("studyCompilation") or record.get("textVersions"):
                collection = page.locator(".document-group-heading")
                assert collection.locator(".document-group-label").inner_text() == "Recopilación"
                assert collection.evaluate(
                    "node => getComputedStyle(node).borderInlineStartColor === 'rgb(167, 207, 50)'"
                )
            if identifier == "napoleon-espanoles-bayona-1808":
                assert paragraphs.last.get_attribute("class") == "document-attribution"
                assert paragraphs.last.inner_text() == "Dado en nuestro palacio imperial y real de Bayona a 25 de mayo de 1808."
            if identifier == "decreto-cortes-soberania-isla-leon-1810":
                assert page.locator("#document-dialog-title sup").inner_text() == "*"
                note = page.locator(".document-full-source > .document-reading-note")
                assert note.inner_text().startswith("* La Isla de León corresponde a la actual ciudad de San Fernando")
                assert "escuadra británica" in note.inner_text()
                assert "balance of power" in note.inner_text()
                assert paragraphs.first.inner_text() == "PRIMER DECRETO DE LAS CORTES REUNIDAS EN LA ISLA DE LEÓN (CÁDIZ)"
                assert paragraphs.first.evaluate("""node => {
                    const style = getComputedStyle(node);
                    return style.textAlign === 'center' && Number(style.fontWeight) >= 700;
                }""")
                page.locator(".document-text-versions > summary").click()
                heading = page.locator('.document-text-version[data-version-id="decreto-cortes-soberania-isla-leon-1810-pdf-2005-3-1"] blockquote p').first
                assert heading.evaluate("""node => {
                    const style = getComputedStyle(node);
                    return style.textAlign === 'center' && Number(style.fontWeight) >= 700;
                }""")
                reference = page.locator('.document-text-version[data-version-id="decreto-cortes-soberania-isla-leon-1810-pdf-2007-1-1"] blockquote p').last
                assert reference.evaluate("node => getComputedStyle(node).textAlign") == "right"
            content = record.get("studyCompilation") or record
            starts = content.get("paragraphStarts", list(range(len(content["text"]))))
            attribution_start = len(content["text"]) - content.get("attributionParagraphs", 0)
            for index, paragraph in enumerate(paragraphs.all()):
                style = paragraph.evaluate("""node => {
                    const s = getComputedStyle(node);
                    return {align:s.textAlign,last:s.textAlignLast,style:s.fontStyle};
                }""")
                if starts[index] >= attribution_start:
                    assert style == {"align": "right", "last": "right", "style": "normal"}, (identifier, style)
                    emphasis = content.get("attributionEmphasis", []) if index == len(starts) - 1 else []
                    assert paragraph.locator("em").all_text_contents() == emphasis, identifier
                    for part in paragraph.locator("em").all():
                        assert part.evaluate("node => getComputedStyle(node).fontStyle") == "italic"
                    if identifier == "ley-general-de-ferrocarriles":
                        assert paragraph.locator("em").count() == 0
                    if identifier == "antonio-maura-critica-la-representacion-politica":
                        assert paragraph.locator("em").count() == 0
                    if identifier == "critica-del-sistema-electoral-de-la-restauracion":
                        assert paragraph.locator("em").all_text_contents() == ["Antología de artículos"]
                    if identifier == "la-segunda-republica-y-la-cuestion-agraria":
                        assert paragraph.locator("em").all_text_contents() == ["Causas de la guerra de España"]
                    assert paragraph.evaluate("""node => {
                        const range = document.createRange();
                        range.selectNodeContents(node);
                        return Math.abs(range.getBoundingClientRect().right - node.getBoundingClientRect().right) < 1;
                    }""")
                else:
                    heading = starts[index] in content.get("headingParagraphs", [])
                    align = ("center" if content.get("textLayout") == "verse-pair" else
                             ("center" if content.get("centerHeadings") is not False else "left") if heading else "justify")
                    assert style == {"align": align, "last": "center" if align == "center" else "left",
                                     "style": "normal"}, (identifier, style)
                    emphasis = content.get("headingEmphasis", {}).get(str(starts[index]), []) if heading else []
                    assert paragraph.locator("em").all_text_contents() == emphasis, identifier
                    if heading:
                        assert paragraph.evaluate("node=>getComputedStyle(node).fontWeight") == "700"
            page.keyboard.press("Escape")
        context.close()


def check_full_content_search(browser):
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    expected = {record["id"] for record in DATA["documents"] if any(
        "suñer" in person["name"].lower() for person in record.get("image", {}).get("annotations", {}).get("people", []))}
    assert expected
    results = []
    for query in ("Súñer", "SUÑER", "suner", "súñ"):
        page.locator("#document-search").fill(query)
        identities = set(page.locator(".document-card").evaluate_all("(cards)=>cards.map(card=>card.dataset.id)"))
        assert expected <= identities, query
        results.append(identities)
    assert results[0] == results[1] == results[2]
    assert results[0] <= results[3]
    assert not page.locator("#document-dialog").is_visible()
    page.locator("#document-search").fill("Suñer")
    page.select_option("#document-block", "5")
    assert page.locator(".document-card").count() == 0
    page.locator("#document-reset").click()
    for query, identity in (
        ("conservar y proteger por leyes sabias", "constitucion-1812-articulos-2008"),
        ("máxima recompensa", "alegoria-victoria-franco-1939"),
        ("Nork-Town", "manifiesto-de-sandhurst-llamamiento-a-la-restauracion"),
    ):
        page.locator("#document-search").fill(query)
        assert page.locator(f'.document-card[data-id="{identity}"]').count() == 1, query
    context.close()

    fixture = json.loads(json.dumps(RAW_DATA))
    photo = next(record for record in fixture["documents"] if record["id"] == "goya-tres-de-mayo")
    photo["commentary"][0]["text"] += " Comentariobuscable."
    photo["examCaption"] = {"text": "Piedefotobuscable", "appearanceId": photo["appearances"][0]["id"]}
    photo["image"]["annotations"] = {
        "layout": "margins", "note": "Notabuscable", "sources": [{"title": "Fuente", "url": fixture["source"]}],
        "symbols": [{"name": "Simbolobuscable", "role": "Significadobuscable", "position": "Posicionbuscable",
                     "x": .5, "y": .5, "side": "left"}],
    }
    photo["image"]["additionalImages"] = [{
        **photo["image"], "annotations": {
            **photo["image"]["annotations"],
            "symbols": [{"name": "Segundaimagenbuscable", "role": "Detalle", "position": "Centro",
                         "x": .5, "y": .5, "side": "right"}],
        },
    }]
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    page.route("**/data/documentos.json", lambda route: route.fulfill(json=fixture))
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    for query in ("comentariobusc", "piedefoto", "simbolobusc", "significadobusc", "posicionbusc",
                  "notabusc", "segundaimagenbusc"):
        page.locator("#document-search").fill(query)
        assert page.locator(".document-card").count() == 1, query
        assert page.locator(".document-card").get_attribute("data-id") == photo["id"]
    assert not errors, errors
    context.close()

def check_collection_link(page, record):
    assert page.locator(".document-provenance, .document-full-source > .document-quality").count() == 0
    appearance = next(item for item in record["appearances"]
                      if item["id"] == record["examCaption"]["appearanceId"]) if record.get("examCaption") else record["appearances"][0]
    label = ("Ver copia PDF de origen" if appearance.get("sourceReviewStatus") == "transcription-copy"
             else "Ver PDF de origen") if appearance.get("sourceType") == "pdf" else "Ver en la recopilación"
    collection = page.get_by_role("link", name=label, exact=True)
    assert collection.count() == 1
    assert collection.get_attribute("href") == appearance["sourceUrl"]
    assert collection.inner_text().strip() == label
    icon = collection.locator("svg")
    assert icon.count() == 1 and icon.get_attribute("aria-hidden") == "true"
    assert icon.evaluate("(node) => node.getBoundingClientRect().width > 0 && node.getBoundingClientRect().height > 0")


def appearance_label(appearance):
    exam = re.sub(rf"^{appearance['year']}\s+", "", appearance["exam"])
    exam = re.sub(r"\s*\([^)]*\)\s*$", "", exam)
    if appearance["year"] == 2011:
        exam = re.sub(r"^(Ordinaria|Extraordinaria) examen (\d+)$",
                      lambda match: f"Examen {match[2]} {match[1].lower()}", exam)
    if appearance["year"] == 2010:
        for letter in "AB":
            if exam == f"Titular reserva {letter}":
                exam = f"Reserva {letter} ordinaria"
            elif exam == f"Extraordinaria reserva {letter}":
                exam = f"Reserva {letter} extraordinaria"
    original_exam = re.sub(rf"^{appearance['year']}\s+", "", appearance["exam"])
    exam_words = " ".join(re.findall(r"\w+", normalize(exam)))
    route_words = " ".join(re.findall(r"\w+", normalize(appearance["route"])))
    return " · ".join(str(part) for part in (
        appearance["year"], exam,
        "" if (appearance["route"].endswith("sin cotejar") or appearance["route"] == original_exam
               or f" {route_words} " in f" {exam_words} ") else appearance["route"],
        "" if appearance["document"] is None else f"Documento {appearance['document']}",
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


def check_badges_without_repeated_exam_fields(browser):
    examples = [
        ("2012 Examen 2", "Examen 2", "2012 · Examen 2 · Documento 1"),
        ("2012 Examen 2", "  EXAMEN  2 ", "2012 · Examen 2 · Documento 1"),
        ("2012 Ordinaria examen 2", "Examen 2", "2012 · Ordinaria examen 2 · Documento 1"),
        ("2012 Examen 2", "Opción B", "2012 · Examen 2 · Opción B · Documento 1"),
    ]
    for exam, route, expected in examples:
        fixture = json.loads(json.dumps(DATA))
        record = fixture["documents"][0]
        record["appearances"] = [{**record["appearances"][0], "year": 2012, "exam": exam,
                                  "route": route, "document": 1}]
        context = browser.new_context(service_workers="block")
        page = context.new_page()
        page.route("**/data/documentos.json", lambda request: request.fulfill(json=fixture))
        page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
        card = page.locator(f'.document-card[data-id="{record["id"]}"]')
        pill = card.locator(".exam-pill")
        assert pill.inner_text() == expected, (exam, route)
        assert pill.get_attribute("title") == expected, (exam, route)
        card.locator(".document-open").click()
        assert page.locator("#document-dialog .exam-pill").inner_text() == expected
        assert page.locator('script[src="documentos.js?v=105"]').count() == 1
        assert page.locator('link[href="documentos.css?v=74"]').count() == 1
        context.close()

def check_image_credits(browser):
    for width in (1440, 375):
        context = browser.new_context(viewport={"width": width, "height": 900}, service_workers="block")
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        reveal_historical(page)
        for identity in ("motin-esquilache-1766", "acorazado-maine-1898", "mapa-primera-guerra-carlista-2012"):
            record = next(record for record in DATA["documents"] if record["id"] == identity)
            page.locator(f'.document-card[data-id="{identity}"] .document-open').click()
            details = page.locator("#document-dialog .document-image-credits")
            credit = details.locator("p")
            assert not details.evaluate("node => node.open")
            assert not credit.is_visible()
            summary = details.locator("summary")
            assert summary.inner_text() == "Créditos de la imagen"
            summary.focus()
            page.keyboard.press("Enter")
            assert credit.is_visible()
            attribution = record["image"]["attribution"]
            assert details.get_by_role("link", name=attribution["text"], exact=True).get_attribute("href") == attribution["url"]
            assert details.get_by_role("link", name=attribution["license"], exact=True).get_attribute("href") == attribution["licenseUrl"]
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.keyboard.press("Escape")
        page.locator('.document-card[data-id="cartel-ayuda-republica-francia"] .document-open').click()
        assert page.locator("#document-dialog .document-full-source img").get_attribute("src") == "assets/documentos/cartel-ayuda-republica-pares.jpg"
        assert page.locator("#document-dialog .document-full-source img").evaluate("node => node.style.filter") == "saturate(0.7) contrast(0.9) brightness(1.04)"
        assert page.locator("#document-dialog .document-reproduction-note").count() == 0
        page.keyboard.press("Escape")
        cover = page.locator('.document-card[data-id="portada-constitucion-1812"]')
        assert cover.locator(".document-preview img").evaluate("node => getComputedStyle(node).filter") == "none"
        cover.locator(".document-open").click()
        image = page.locator(".document-full-source img")
        assert image.get_attribute("src") == "assets/documentos/portada-constitucion-1812.png"
        assert image.evaluate("node => getComputedStyle(node).filter") == "none"
        page.keyboard.press("Escape")
        page.select_option("#document-year", "2015")
        page.select_option("#document-exam", "examen 4")
        page.locator('.document-card[data-id="goya-tres-de-mayo"] .document-open').click()
        assert page.locator(".document-exam-caption").inner_text() == "Francisco de Goya, Los fusilamientos (Museo del Prado)"
        assert page.get_by_role("link", name="Ver en la recopilación", exact=True).get_attribute("href").endswith("#heading=h.lxhnexopmiob")
        page.keyboard.press("Escape")
        page.locator("#document-reset").click()
        page.select_option("#document-block", "5")
        page.locator('.document-card[data-id="juramento-cortes-constituyentes-isla-leon-1810"] .document-open').click()
        caption = page.locator(".document-exam-caption")
        assert caption.inner_text() == (
            "Juramento de las Cortes Constituyentes en la Iglesia Mayor Parroquial de la Real Isla de León, "
            "24 de Septiembre de 1810. (Óleo sobre lienzo de Casado del Alisal, conservado en el Salón de Plenos "
            "del Congreso de los Diputados, Madrid)."
        )
        assert caption.evaluate("node => node.scrollWidth <= node.clientWidth")
        context.close()


def check_fitted_media_and_people(browser):
    for width, height in ((1440, 1000), (768, 1024), (375, 812)):
        context = browser.new_context(viewport={"width": width, "height": height},
                                      service_workers="block", has_touch=True)
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        reveal_historical(page)
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
                caption_text = foot.locator("p").first
                assert caption_text.inner_text() == (caption["text"] if caption else "(Sin descripción)")
                assert caption_text.locator("em").all_text_contents() == (
                    caption.get("emphasis", []) if caption else [])
                note = caption.get("note") if caption else None
                footnote = foot.locator(".document-exam-footnote")
                assert footnote.count() == int(bool(note))
                if note:
                    assert footnote.inner_text() == note
                    assert footnote.locator("em").all_text_contents() == caption.get("noteEmphasis", [])
                    assert footnote.evaluate("node => getComputedStyle(node).color") in (
                        "rgb(178, 58, 48)", "rgb(255, 170, 160)")
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
                assert toggle.inner_text() == ("Ocultar símbolos" if "symbols" in data else "Ocultar personajes")
                assert box.locator(".document-person-overlay").is_visible()
                assert box.locator(".document-person-name").all_text_contents() == [
                    person["name"] for person in data.get("symbols", data.get("people"))
                ]
                margins = width == 1440
                assert box.locator(".document-person-bubble").first.is_visible()
                assert box.locator(".document-person-names").is_visible()
                assert box.locator(".document-person-point").count() == 0
                assert page.locator(".document-person-sources").count() == 0
                assert sorted(box.locator(".document-person-role").all_text_contents()) == sorted(
                    person["role"] for person in data.get("symbols", data.get("people"))
                )
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
                assert geometry["aligned"], (record["id"], width, geometry)
                assert abs(geometry["ratio"] - geometry["natural"]) < .001
                if margins:
                    assert box.locator(".document-person-lines path").first.evaluate("""path => {
                            const style = getComputedStyle(path);
                            const commands = path.getAttribute('d').match(/[A-DF-Za-df-z]/g);
                            return parseFloat(style.strokeWidth) >= 2.5
                                && commands.every(command => ['M','L','Q'].includes(command))
                                && commands.includes('L') && commands.includes('Q');
                    }""")
                    assert stage.evaluate("""stage => {
                            const leader = stage.querySelector('.document-person-lines path');
                            const dot = stage.querySelector('.document-person-lines circle');
                            const start = leader.getPointAtLength(0);
                            return getComputedStyle(dot).fill === getComputedStyle(leader).stroke
                                && dot.r.baseVal.value * 2 === 10
                                && dot.cx.baseVal.value === start.x
                                && dot.cy.baseVal.value === start.y;
                    }""")
                    assert stage.evaluate("""stage => {
                            const figure = stage.closest('figure');
                            const caption = figure.querySelector('.document-exam-caption').getBoundingClientRect();
                            const labels = [...figure.querySelectorAll('.document-person-bubble')]
                                .filter(b => !b.hidden).map(b => b.getBoundingClientRect());
                            return labels.every(label => label.top >= caption.bottom)
                                && labels.every((label, index) => labels.slice(index + 1).every(other =>
                                    label.right <= other.left || label.left >= other.right
                                    || label.bottom <= other.top || label.top >= other.bottom));
                    }"""), record["id"]
                toggle.tap()
                assert toggle.get_attribute("aria-expanded") == "false"
                assert not box.locator(".document-person-details").is_visible()
            page.locator(".document-close").tap()
        context.close()

def check_below_caption_people(browser):
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
        page.wait_for_function("""() => {
            const figure = document.querySelector('.document-person-figure');
            const caption = figure.querySelector('.document-exam-caption').getBoundingClientRect();
            if (![...figure.querySelectorAll('.document-person-bubble')]
                .every(b => b.getBoundingClientRect().top >= caption.bottom)) return false;
            const stage = figure.querySelector('.document-person-stage').getBoundingClientRect();
            const leader = figure.querySelector('.document-person-lines path');
            const point = leader.getPointAtLength(0).matrixTransform(leader.getScreenCTM());
            return Math.abs(point.x - stage.left - .1 * stage.width) < 1
                && Math.abs(point.y - stage.top - .48 * stage.height) < 1;
        }""")
        assert page.locator(".document-person-names").is_visible()
        assert page.locator(":popover-open").count() == 0
    leader = page.locator(".document-person-lines path").first
    before_y = leader.evaluate("path => path.getPointAtLength(0).y")
    delta = page.locator("#document-dialog").evaluate("""dialog => {
        const before = dialog.scrollTop;
        dialog.scrollTop += 80;
        return dialog.scrollTop - before;
    }""")
    assert delta > 0
    page.wait_for_function("expected => Math.abs(document.querySelector('.document-person-lines path').getPointAtLength(0).y - expected) < 1",
                           arg=before_y)
    page.locator(".document-person-label").first.scroll_into_view_if_needed()
    label = page.locator(".document-person-label").first.bounding_box()
    page.mouse.move(label["x"] + 1, label["y"] + label["height"] / 2)
    page.mouse.down()
    page.mouse.move(label["x"] + label["width"] - 1, label["y"] + label["height"] / 2, steps=10)
    page.mouse.up()
    assert page.locator(".document-person-label").first.inner_text() in page.evaluate("getSelection().toString()")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#document-dialog').open && !document.querySelector(':popover-open')")
    assert not errors, errors
    context.close()


def check_extended_annotation_palette(browser):
    corpus = json.loads(json.dumps(DATA))
    record = next(item for item in corpus["documents"] if item["id"] == "alegoria-victoria-franco-1939")
    symbols = record["image"]["annotations"]["symbols"]
    for index in range(17 - len(symbols)):
        symbol = dict(symbols[0], name=f"Símbolo de prueba {index + 1}", x=.1 + index * .08, y=.5)
        symbols.append(symbol)
    context = browser.new_context(viewport={"width": 375, "height": 1000}, service_workers="block")
    page = context.new_page()
    page.route("**/data/documentos.json*", lambda route: route.fulfill(json=corpus))
    page.goto(f"{BASE}/documentos.html")
    page.locator(f'.document-card[data-id="{record["id"]}"] .document-open').click()
    page.locator(".document-person-toggle").click()
    assert page.locator(".document-person-figure").evaluate("""figure => {
        const colors = [...figure.querySelectorAll('.document-person-bubble')]
            .map(b => getComputedStyle(b).borderTopColor);
        const paths = [...figure.querySelectorAll('path')].map(p => getComputedStyle(p).stroke);
        const dots = [...figure.querySelectorAll('circle')].map(p => getComputedStyle(p).fill);
        return colors.length === 17 && new Set(colors).size === 17
            && paths.length === 17 && dots.length === 17
            && colors.every(color => paths.includes(color) && dots.includes(color));
    }""")
    context.close()


def search_matches(query):
    def content(record):
        images = [image for image in [record.get("image"), record.get("tableImage")] if image]
        images += record.get("image", {}).get("additionalImages", [])
        fields = [record["title"], record["date"], record["sourceCaption"], record["quality"], *record["tags"],
                  *record.get("text", []), record.get("examCaption", {}).get("text", "")]
        fields += [str(value) for appearance in record["appearances"] for value in (appearance["year"], appearance["exam"], appearance["route"])]
        fields += [section[key] for section in record["commentary"] for key in ("title", "text")]
        for image in images:
            fields += [image.get(key, "") for key in ("alt", "reproductionNote")]
            fields += [image.get("examCaption", {}).get("text", ""), image.get("attribution", {}).get("text", "")]
            annotations = image.get("annotations", {})
            fields += [annotations.get("note", "")]
            fields += [item[key] for item in annotations.get("people", []) + annotations.get("symbols", [])
                       for key in ("name", "role", "position")]
        table = record.get("table", {})
        fields += [table.get("caption", ""), *table.get("headers", []), *table.get("notes", [])]
        fields += [str(cell) for row in table.get("rows", []) for cell in row]
        fields += [content(version) for version in record.get("textVersions", [])]
        fields += record.get("studyCompilation", {}).get("text", []) if record.get("studyCompilation") else []
        return " ".join(fields)
    return [
        document for document in DATA["documents"]
        if all(normalize(word) in normalize(content(document)) for word in normalize(query).split())
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
    assert card.locator("button, [tabindex]").count() == 4
    assert card.locator(".document-exams a").count() == len(TEXT_DOCUMENT["appearances"])
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
        assert page.locator(".document-full-source > blockquote p").count() == len(reading_paragraphs(TEXT_DOCUMENT))
        assert page.locator(".document-full-source > blockquote").evaluate("""node => {
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


def check_carlist_map_and_pavia(browser):
    for width in (1440, 768, 320):
        context = browser.new_context(viewport={"width": width, "height": 1000},
                                      service_workers="block")
        page = context.new_page()
        page.set_default_timeout(10000)
        page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
        page.locator('.document-card[data-id="mapa-primera-guerra-carlista-2012"] .document-open').click()
        page.wait_for_function("""() => document.querySelector('.document-selectable-map')
            ?.contentDocument?.querySelector('#ciudades')""")
        map_object = page.locator(".document-selectable-map")
        issues = map_object.evaluate("""async object => {
            const doc = object.contentDocument;
            await doc.fonts.ready;
            const labels = [...doc.querySelectorAll('.city-label')].map(node =>
                ({name: node.textContent.trim(), box: node.getBBox(), parent: node.parentElement}));
            const circles = [...doc.querySelectorAll('#ciudades circle')];
            const intersects = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x
                && a.y < b.y + b.height && a.y + a.height > b.y;
            const problems = [];
            const influence = doc.querySelector('#influencia path');
            const projected = (lon, lat) => new DOMPoint(
                (lon + 9.9) * 1183.5554 / 14.7, (44.4 - lat) * 1015.8372 / 9.7);
            for (const name of ['León', 'Huesca', 'Logroño', 'Madrid', 'Barcelona']) {
                const city = doc.querySelector(`[data-city="${name}"] circle`);
                for (let step = 0; step < 32; step++) {
                    const angle = step * 2 * Math.PI / 32;
                    if (influence.isPointInFill(new DOMPoint(city.cx.baseVal.value + 8 * Math.cos(angle),
                        city.cy.baseVal.value + 8 * Math.sin(angle)))) {
                        problems.push(`${name}: ciudad incluida en el verde`);
                        break;
                    }
                }
            }
            for (const [name, lon, lat] of [
                ['A Coruña', -8.4, 43.36], ['Santiago', -8.54, 42.88],
                ['Lugo', -7.56, 43.01], ['Ourense', -7.86, 42.34], ['Tui', -8.64, 42.05],
                ['Costa al norte de Barcelona', 2.8, 41.75],
                ['Litoral reducido del Maestrazgo', .65, 40.75],
                ['Encima del entrante suave de Huesca', -.41, 42.43],
                ['Norte de Logroño', -2.45, 42.7], ['Sur de Logroño', -2.45, 42.1],
                ['Oeste de Logroño', -3.25, 42.47], ['Este de Logroño', -1.65, 42.47]
            ]) if (!influence.isPointInFill(projected(lon, lat))) problems.push(`${name}: falta sombreado verde`);
            for (const [name, lon, lat] of [
                ['Litoral retirado del Maestrazgo', .4, 40.4],
                ['Bolsa retirada sobre Madrid', -4.35, 40.75],
                ['Hueco ampliado de Logroño', -3.04, 42.43]
            ]) if (influence.isPointInFill(projected(lon, lat))) problems.push(`${name}: sobra sombreado verde`);
            const oldCoast = influence.cloneNode();
            const curve = pairs => 'C' + pairs.map(([lon, lat]) => {
                const p = projected(lon, lat); return `${p.x.toFixed(2)} ${p.y.toFixed(2)}`;
            }).join(' ');
            oldCoast.setAttribute('d', influence.getAttribute('d').replace(
                curve([[1.05, 40.5919], [.5, 40.5838], [.05, 40.5838]]),
                curve([[1.05, 40.35], [.5, 40.08], [.05, 40.08]])).replace(
                curve([[.04, 39.72], [-1.2, 40.3], [-1.8, 40.5]]),
                curve([[-.4, 40.1], [-1.2, 40.3], [-1.8, 40.5]])));
            oldCoast.setAttribute('opacity', '0');
            doc.documentElement.append(oldCoast);
            let before = 0, after = 0;
            const coast = doc.querySelector('#peninsular-spain polygon');
            for (let distance = 0; distance < coast.getTotalLength(); distance += .25) {
                const p = coast.getPointAtLength(distance);
                const lon = p.x * 14.7 / 1183.5554 - 9.9;
                const lat = 44.4 - p.y * 9.7 / 1015.8372;
                if (lon <= 0 || lon >= 2 || lat <= 39.8 || lat >= 41.1) continue;
                before += oldCoast.isPointInFill(p);
                after += influence.isPointInFill(p);
            }
            oldCoast.remove();
            if (!before || Math.abs(after / before - .5) > .01)
                problems.push(`Litoral verde: ${after}/${before}, no está reducido a la mitad`);
            const edge = [...Array(Math.ceil(influence.getTotalLength()))].map((_, index) =>
                influence.getPointAtLength(index));
            const distanceToEdge = name => {
                const city = doc.querySelector(`[data-city="${name}"] circle`);
                return Math.min(...edge.map(p => Math.hypot(
                    p.x - city.cx.baseVal.value, p.y - city.cy.baseVal.value)));
            };
            if (distanceToEdge('Cuenca') >= distanceToEdge('Madrid'))
                problems.push('El borde verde no queda más cerca de Cuenca que de Madrid');
            const estella = doc.querySelector('[data-city="Estella"] circle');
            const estellaLabel = doc.querySelector('[data-city="Estella"] text').getBBox();
            if (estella.cx.baseVal.value - estellaLabel.x - estellaLabel.width > 14)
                problems.push('El rótulo de Estella queda alejado de la ciudad');
            const royal = doc.querySelector('#ruta-real path');
            const origin = royal.getPointAtLength(0), next = royal.getPointAtLength(5);
            if (Math.hypot(origin.x - estella.cx.baseVal.value, origin.y - estella.cy.baseVal.value) > .02
                || next.x <= origin.x || next.y < origin.y)
                problems.push('El inicio de don Carlos no sale limpiamente del punto de Estella');
            const caceres = doc.querySelector('[data-city="Cáceres"] circle');
            const bend = [...doc.querySelectorAll('#ruta-gomez path')].find(path => {
                const box = path.getBBox();
                return caceres.cx.baseVal.value >= box.x - .1 && caceres.cx.baseVal.value <= box.x + box.width + .1
                    && caceres.cy.baseVal.value >= box.y - .1 && caceres.cy.baseVal.value <= box.y + box.height + .1;
            });
            if (!bend) problems.push('No se encuentra el giro de Cáceres');
            else {
                const length = bend.getTotalLength();
                const points = Array.from({length: Math.ceil(length * 2) + 1},
                    (_, i) => bend.getPointAtLength(Math.min(i / 2, length)));
                const cross = (a, b, c) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
                let tangled = false;
                for (let i = 0; i < points.length - 1 && !tangled; i++)
                    for (let j = i + 2; j < points.length - 1; j++)
                        if (cross(points[i], points[i + 1], points[j]) * cross(points[i], points[i + 1], points[j + 1]) < 0
                            && cross(points[j], points[j + 1], points[i]) * cross(points[j], points[j + 1], points[i + 1]) < 0) {
                            tangled = true; break;
                        }
                if (tangled) problems.push('El giro de Cáceres contiene un cruce');
                if (Math.min(...points.map(p => p.y)) < caceres.cy.baseVal.value - .1)
                    problems.push('El giro de Cáceres forma un bucle por encima de la ciudad');
            }
            const morella = doc.querySelector('[data-city="Morella"] circle');
            for (let i = 0; i < 32; i++) {
                if (!influence.isPointInFill(new DOMPoint(morella.cx.baseVal.value + 7 * Math.cos(i * Math.PI / 16),
                    morella.cy.baseVal.value + 7 * Math.sin(i * Math.PI / 16)))) {
                    problems.push('El punto de Morella queda fuera del verde');
                    break;
                }
            }
            for (const [region, names] of [
                ['norte', ['Estella']],
                ['maestrazgo', ['Cantavieja', 'Morella']]
            ]) {
                const ellipse = doc.getElementById(`control-${region}`);
                const inverse = ellipse.getCTM().inverse();
                for (const name of names) {
                    const text = doc.querySelector(`[data-city="${name}"] .city-label`);
                    const box = text.getBBox();
                    for (const x of [box.x, box.x + box.width])
                        for (const y of [box.y, box.y + box.height]) {
                            const point = new DOMPoint(x, y).matrixTransform(text.getCTM()).matrixTransform(inverse);
                            const distance = ((point.x - ellipse.cx.baseVal.value) / ellipse.rx.baseVal.value) ** 2
                                + ((point.y - ellipse.cy.baseVal.value) / ellipse.ry.baseVal.value) ** 2;
                            if (distance > 1) problems.push(`${name}: texto fuera de la elipse`);
                        }
                }
            }
            for (const [index, label] of labels.entries()) {
                const r = label.box;
                if (r.x < 12 || r.x + r.width > 1172 || r.y < 52 || r.y + r.height > 882)
                    problems.push(`Rótulo recortado: ${label.name}`);
                for (const other of labels.slice(index + 1))
                    if (intersects(r, other.box)) problems.push(`${label.name} / ${other.name}`);
                for (const circle of circles)
                    if (circle.parentElement !== label.parent && intersects(r, circle.getBBox()))
                        problems.push(`${label.name} oculta ${circle.parentElement.dataset.city}`);
            }
            return problems;
        }""")
        assert not issues, (width, issues)
        assert map_object.evaluate("""object => {
            const r = object.getBoundingClientRect();
            return r.width <= object.closest('.document-full-source').clientWidth
                && r.height <= innerHeight * .52 + 1;
        }""")
        page.locator(".document-table-details summary").click()
        assert page.locator(".document-table tbody tr").count() == 7
        assert page.locator(".document-zoom").count() == 0
        page.locator(".document-close").click()
        page.locator('.document-card[data-id="disolucion-cortes-general-pavia-1874"] .document-open').click()
        image = page.locator(".document-full-source img")
        image.evaluate("image => image.decode()")
        geometry = image.evaluate("""image => {
            const r = image.getBoundingClientRect();
            return {width: image.naturalWidth, height: image.naturalHeight, ratio: r.width/r.height,
                fits: r.width <= image.closest('.document-full-source').clientWidth};
        }""")
        assert (geometry["width"], geometry["height"]) == (4000, 2824)
        assert geometry["fits"] and abs(geometry["ratio"] - 4000 / 2824) < .001
        assert page.locator(".document-exam-caption p").inner_text() == "El general Pavía disuelve las Cortes en 1874"
        context.close()


def check_symbols_and_map_classification(browser):
    record = next(item for item in DATA["documents"] if item["id"] == "alegoria-victoria-franco-1939")
    symbols = record["image"]["annotations"]["symbols"]
    for width in (375, 768, 1440):
        context = browser.new_context(viewport={"width": width, "height": 1000}, service_workers="block")
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
        page.locator('[data-type="grafico"]').click()
        assert page.locator('.document-card[data-id="mapa-primera-guerra-carlista-2012"]').count() == 1
        assert page.locator(f'.document-card[data-id="{record["id"]}"]').count() == 0
        page.locator('[data-type="imagen"]').click()
        assert page.locator('.document-card[data-id="mapa-primera-guerra-carlista-2012"]').count() == 0
        page.locator(f'.document-card[data-id="{record["id"]}"] .document-open').click()
        assert page.get_by_role("button", name="Revelar símbolos", exact=True).count() == 1
        toggle = page.locator(".document-person-toggle")
        assert toggle.get_attribute("aria-expanded") == "false"
        assert not page.locator(".document-person-overlay").is_visible()
        toggle.focus()
        page.keyboard.press("Enter")
        assert toggle.inner_text() == "Ocultar símbolos"
        assert toggle.get_attribute("aria-expanded") == "true"
        assert sorted(page.locator(".document-person-label").all_text_contents()) == sorted(item["name"] for item in symbols)
        assert page.locator(".document-person-names").get_attribute("aria-label") == "Símbolos identificados"
        page.wait_for_timeout(80)
        assert page.locator(".document-person-stage").evaluate("""(stage, symbols) => {
                const bounds = stage.getBoundingClientRect();
                const points = [...stage.querySelectorAll('.document-person-lines circle')];
                const paths = [...stage.querySelectorAll('.document-person-lines path')];
                return points.length === symbols.length && paths.length === symbols.length
                    && points.some(point => point.style.display !== 'none')
                    && points.every((point, index) => {
                        if (point.style.display === 'none') return true;
                        const pixel = new DOMPoint(point.cx.baseVal.value, point.cy.baseVal.value)
                            .matrixTransform(point.getScreenCTM());
                        return Math.abs(pixel.x - bounds.left - symbols[index].x * bounds.width) < 1
                            && Math.abs(pixel.y - bounds.top - symbols[index].y * bounds.height) < 1;
                    }) && paths.every(path => {
                        const style = getComputedStyle(path);
                        return style.strokeDasharray !== 'none';
                    });
        }""", symbols), width
        toggle.click()
        assert toggle.inner_text() == "Revelar símbolos"
        assert toggle.get_attribute("aria-expanded") == "false"
        assert not page.locator(".document-person-overlay").is_visible()
        context.close()


def check_constitution_people(browser):
    record = next(item for item in DATA["documents"] if item["id"] == "comision-redactora-constitucion-1978")
    people = record["image"]["annotations"]["people"]
    expected_order = [
        "Manuel Fraga Iribarne", "Miquel Roca i Junyent", "Miguel Herrero y Rodríguez de Miñón",
        "José Pedro Pérez-Llorca Rodrigo", "Gabriel Cisneros Laborda",
        "Gregorio Peces-Barba Martínez", "Jordi Solé Tura",
    ]
    for width in (320, 375, 768, 1440):
        context = browser.new_context(viewport={"width": width, "height": 1000}, service_workers="block")
        page = context.new_page()
        page.goto(f"{BASE}/documentos.html")
        page.locator(f'.document-card[data-id="{record["id"]}"] .document-open').click()
        page.locator(".document-person-stage img").evaluate("image => image.decode()")
        stage = page.locator(".document-person-stage")
        before = stage.bounding_box()
        toggle = page.get_by_role("button", name="Revelar personajes", exact=True)
        toggle.click()
        page.wait_for_timeout(80)
        after = stage.bounding_box()
        assert abs(before["width"] - after["width"]) < 1 and abs(before["height"] - after["height"]) < 1
        assert sorted(page.locator(".document-person-label").all_text_contents()) == sorted(person["name"] for person in people)
        assert sorted(page.locator(".document-person-role").all_text_contents()) == sorted(person["role"] for person in people)
        order = page.locator(".document-person-figure").evaluate("""figure => {
            const bubbles = [...figure.querySelectorAll('.document-person-bubble')];
            return [...figure.querySelectorAll('circle')]
                .sort((a, b) => a.cx.baseVal.value - b.cx.baseVal.value)
                .map(dot => bubbles.find(b => getComputedStyle(b).borderTopColor === getComputedStyle(dot).fill)
                    .querySelector('.document-person-label').textContent);
        }""")
        assert order == expected_order, (width, order)
        result = page.locator(".document-person-figure").evaluate("""figure => {
            const paths = [...figure.querySelectorAll('path')];
            const dots = [...figure.querySelectorAll('circle')].map(dot => {
                const matrix = dot.getScreenCTM();
                const point = new DOMPoint(dot.cx.baseVal.value, dot.cy.baseVal.value).matrixTransform(matrix);
                return {x:point.x, y:point.y, r:dot.r.baseVal.value * matrix.a};
            });
            const caption = figure.querySelector('.document-exam-caption').getBoundingClientRect();
            const labels = [...figure.querySelectorAll('.document-person-bubble')].map(b => b.getBoundingClientRect());
            return {
                seven: paths.length === 7 && dots.length === 7 && labels.length === 7,
                colors: new Set(paths.map(path => getComputedStyle(path).stroke)).size === 7,
                belowCaption: labels.every(b => b.top >= caption.bottom),
                distinctPoints: dots.every((dot, i) => dots.slice(i + 1).every(other =>
                    Math.hypot(dot.x - other.x, dot.y - other.y) > dot.r + other.r + 1)),
                clearLeaders: paths.every((path, index) => {
                    const matrix = path.getScreenCTM();
                    for (let distance = 0; distance < path.getTotalLength(); distance += 2) {
                        const point = path.getPointAtLength(distance).matrixTransform(matrix);
                        if (dots.some((dot, other) => other !== index
                            && Math.hypot(point.x - dot.x, point.y - dot.y) < dot.r + 2)) return false;
                        if ([caption, ...labels].some(b => point.x > b.left + 2 && point.x < b.right - 2
                            && point.y > b.top + 2 && point.y < b.bottom - 2)) return false;
                    }
                    return true;
                }),
            };
        }""")
        assert all(result.values()), (width, result)
        page.get_by_role("button", name="Ocultar personajes", exact=True).click()
        assert not page.locator(".document-person-callouts").is_visible()
        context.close()


def check_reader_updates(browser, mobile_device):
    pair_id = "fotografias-guerra-civil-entrega-fusiles-y-burgos-1936"
    for width in (320, 412, 768, 1180, 1440):
        context = browser.new_context(viewport={"width": width, "height": 1000}, service_workers="block")
        page = context.new_page()
        page.set_default_timeout(10000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        check_card_badges(page)
        pair = page.locator(f'.document-card[data-id="{pair_id}"] .document-preview')
        pair.scroll_into_view_if_needed()
        assert pair.locator("img").count() == 2
        pair.locator("img").evaluate_all("images => Promise.all(images.map(image => image.decode()))")
        assert pair.evaluate("""box => {
            const r = box.getBoundingClientRect();
            const images = [...box.querySelectorAll('img')].map(image =>
                (image.closest('.doc-image-crop') || image).getBoundingClientRect());
            return images.every(i => i.width > 0 && i.height > 0 && i.left >= r.left && i.right <= r.right
                && i.top >= r.top && i.bottom <= r.bottom)
                && images[0].right <= images[1].left;
        }"""), width
        for record in DATA["documents"]:
            images = [record.get("image"), *(record.get("image", {}).get("additionalImages") or [])]
            if not any(image and image.get("annotations") for image in images):
                continue
            page.locator(f'.document-card[data-id="{record["id"]}"] .document-open').click()
            for toggle in page.locator(".document-person-toggle").all():
                toggle.click()
                page.wait_for_timeout(80)
            assert page.locator(".document-person-point").count() == 0
            for stage in page.locator(".document-person-stage").all():
                stage.scroll_into_view_if_needed()
                page.wait_for_timeout(80)
                result = stage.evaluate("""stage => {
                    const r = stage.getBoundingClientRect();
                    const figure = stage.closest('figure');
                    const toggle = figure.querySelector('.document-person-toggle').getBoundingClientRect();
                    const labels = [...figure.querySelectorAll('.document-person-bubble')].filter(b => !b.hidden)
                        .map(b => b.getBoundingClientRect());
                    const caption = figure.querySelector('.document-exam-caption').getBoundingClientRect();
                    const image = stage.querySelector('img');
                    const paths = [...stage.querySelectorAll('path')].filter(p => p.style.display !== 'none');
                    const clearLines = paths.every(path => {
                        const matrix = path.getScreenCTM();
                        const length = path.getTotalLength();
                        for (let distance = 0; distance < length; distance += 2) {
                            const point = path.getPointAtLength(distance).matrixTransform(matrix);
                            if ([...labels, caption].some(b => point.x > b.left + 2 && point.x < b.right - 2
                                && point.y > b.top + 2 && point.y < b.bottom - 2)) return false;
                        }
                        return true;
                    });
                    return {
                        count: labels.length,
                        aligned: Math.abs(image.getBoundingClientRect().width / image.getBoundingClientRect().height
                            - image.naturalWidth / image.naturalHeight) < .001,
                        belowCaption: labels.every(b => b.top >= caption.bottom + 16),
                        separated: labels.every((a, i) => labels.slice(i + 1).every(b =>
                            a.right <= b.left + 1 || a.left >= b.right - 1 || a.bottom <= b.top + 1 || a.top >= b.bottom - 1)),
                        shortestExit: paths.every(path => {
                            const values = path.getAttribute('d').match(/-?[\\d.]+/g).slice(0, 4).map(Number);
                            const [x, y, nextX] = values;
                            const vertical = Math.min(y, r.height - y) <= Math.min(x, r.width - x);
                            return vertical === (Math.abs(nextX - x) < .01);
                        }),
                        twoColumns: labels.length === 1 || new Set(labels.map(b => Math.round(b.left))).size === 2,
                        outsideImage: labels.every(b => b.top >= r.bottom),
                        lines: paths.length === labels.length && paths.every(p => {
                            const s = getComputedStyle(p);
                            return s.strokeDasharray !== 'none'
                                && p.getAttribute('d').match(/[A-DF-Za-df-z]/g).every(c => ['M','L','Q'].includes(c));
                        }),
                        matchingColors: paths.every(path => {
                            const color = getComputedStyle(path).stroke;
                            return [...figure.querySelectorAll('.document-person-bubble')]
                                .some(b => getComputedStyle(b).borderTopColor === color)
                                && [...stage.querySelectorAll('circle')].some(dot => getComputedStyle(dot).fill === color);
                        }),
                        distinctColors: new Set(paths.map(p => getComputedStyle(p).stroke)).size === paths.length,
                        noDisconnectedLabels: getComputedStyle(figure.querySelector('.document-person-details')).clipPath === 'inset(50%)',
                        clearLines,
                    };
                }""")
                assert result["count"] > 0 and all(value for key, value in result.items() if key != "count"), (
                    width, record["id"], result)
            assert page.locator(".document-zoom").count() == 0
            assert page.locator(".document-person-point").count() == 0
            for toggle in page.locator(".document-person-toggle").all():
                toggle.click()
            assert not page.locator(".document-person-overlay").first.is_visible()
            page.locator(".document-close").click()
        assert not errors, errors
        context.close()

    check_touch_reader_zoom(browser, mobile_device)
    check_anchored_feedback(browser, mobile_device)


def check_touch_reader_zoom(browser, mobile_device):
    for identifier in ("mapa-primera-guerra-carlista-2012", "disolucion-cortes-general-pavia-1874"):
        context = browser.new_context(**mobile_device, service_workers="block")
        page = context.new_page()
        page.set_default_timeout(10000)
        cdp = context.new_cdp_session(page)
        page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
        page.locator(f'.document-card[data-id="{identifier}"] .document-open').click()
        assert page.locator(".document-zoom").count() == 0
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(800)
        assert page.locator("#document-dialog").evaluate(
            "node => getComputedStyle(node).overscrollBehavior") == "contain"
        cdp.send("Input.synthesizePinchGesture", {
            "x": 200, "y": 600, "scaleFactor": 3, "relativeSpeed": 400, "gestureSourceType": "touch",
        })
        page.wait_for_function("document.documentElement.hasAttribute('data-page-zoomed')")
        before = page.evaluate("({x: visualViewport.offsetLeft, w: visualViewport.width, h: visualViewport.height})")
        assert page.locator(".document-full-source").evaluate(
            "node => getComputedStyle(node).overscrollBehavior") == "auto"
        cdp.send("Input.synthesizeScrollGesture", {
            "x": before["w"] / 2, "y": before["h"] / 2, "xDistance": -60, "yDistance": 0,
            "speed": 800, "preventFling": True, "gestureSourceType": "touch",
        })
        page.wait_for_timeout(150)
        assert page.evaluate("visualViewport.offsetLeft") > before["x"] + 20, identifier
        cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})
        page.wait_for_function("!document.documentElement.hasAttribute('data-page-zoomed')")
        assert page.locator("#document-dialog").evaluate(
            "node => getComputedStyle(node).overscrollBehavior") == "contain"
        context.close()


def check_anchored_feedback(browser, mobile_device):
    pair_id = "fotografias-guerra-civil-entrega-fusiles-y-burgos-1936"
    context = browser.new_context(**mobile_device, service_workers="block")
    page = context.new_page()
    cdp = context.new_cdp_session(page)
    page.goto(f"{BASE}/documentos.html", wait_until="domcontentloaded")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    for in_dialog in (False, True):
        if in_dialog:
            cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})
            page.locator(f'.document-card[data-id="{pair_id}"] .document-open').click()
        for scale in (1, 5):
            cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": scale})
            for flag in ("favorite", "review"):
                selector = "#document-dialog" if in_dialog else f'.document-card[data-id="{pair_id}"]'
                button = page.locator(f'{selector} [data-document-mark="{flag}"]')
                button.evaluate("(button, flag) => window.pauMarkFeedback(button, flag)", flag)
                result = button.evaluate("""button => {
                    const particle = button.querySelector('.favorite-particle');
                    const animation = particle.getAnimations()[0];
                    animation.pause();
                    const offset = () => {
                        const a = particle.getBoundingClientRect(), b = button.querySelector('svg').getBoundingClientRect();
                        return {x: (a.left + a.width / 2 - b.left - b.width / 2) / b.width,
                            y: (a.top + a.height / 2 - b.top - b.height / 2) / b.height,
                            ratio: a.width / b.width};
                    };
                    const positions = [0, 350, 680].map(time => { animation.currentTime = time; return offset(); });
                    const aligned = positions.every(p => Math.abs(p.x) < .02 && Math.abs(p.ratio - 1) < .02)
                        && Math.abs(positions[0].y + 1.1) < .02
                        && positions[2].y < positions[1].y && positions[1].y < positions[0].y
                        && positions[2].y >= -2.71;
                    const dialog = button.closest('dialog');
                    if (dialog) dialog.scrollTop += 60;
                    else window.scrollBy(0, 60);
                    const follows = Math.abs(offset().y - positions[2].y) < .02;
                    const anchored = particle.parentElement === button && getComputedStyle(particle).position === 'absolute';
                    particle.remove();
                    return aligned && follows && anchored;
                }""")
                assert result, (in_dialog, scale, flag)
    context.close()


def check_reader_swipe(browser, device, *, chromium=False):
    context = browser.new_context(**device, service_workers="block")
    page = context.new_page()
    page.goto(f"{BASE}/documentos.html")
    page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
    page.select_option("#document-year", "2008")
    page.select_option("#document-exam", "examen 1")
    page.locator(".document-open").first.click()
    status = page.locator(".document-reader-status")
    client = context.new_cdp_session(page) if chromium else None

    def swipe(dx, dy):
        bounds = page.locator("#document-dialog-title").bounding_box()
        x = round(bounds["x"] + bounds["width"] / 2 - dx / 2)
        y = round(bounds["y"] + bounds["height"] / 2)
        if client:
            for step in range(9):
                client.send("Input.dispatchTouchEvent", {
                    "type": "touchMove" if step else "touchStart",
                    "touchPoints": [{"x": round(x + dx * step / 8), "y": round(y + dy * step / 8)}],
                })
            client.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else:
            page.evaluate("""({x, y, dx, dy}) => {
                const target = document.elementFromPoint(x, y);
                for (const [type, step] of [['touchstart', 0], ['touchmove', .5], ['touchend', 1]]) {
                    const touch = {identifier: 0, clientX: x + step * dx, clientY: y + step * dy};
                    const event = new Event(type, {bubbles: true});
                    Object.defineProperties(event, {
                        touches: {value: type === 'touchend' ? [] : [touch]},
                        changedTouches: {value: [touch]},
                    });
                    target.dispatchEvent(event);
                }
            }""", dict(x=x, y=y, dx=dx, dy=dy))

    for dx, dy, expected in ((120, 0, 1), (-35, 0, 1), (10, 110, 1),
                             (-120, 5, 2), (-120, 0, 3), (-120, 0, 4),
                             (-120, 0, 4), (120, 0, 3)):
        swipe(dx, dy)
        assert status.inner_text().startswith(f"Documento {expected} de 4:"), (dx, dy, status.inner_text())
    context.close()


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(service_workers="block", reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/documentos.html")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert page.locator(".document-card").count() == len(DATA["documents"])
        check_card_badges(page)
        scope_text = page.locator("#document-scope").inner_text()
        exams = len({appearance["pdfUrl"] for record in DATA["documents"] for appearance in record["appearances"]})
        assert scope_text == (
            f"{DATA['coverage']['sourceDocumentOccurrences']} documentos recopilados · "
            f"{exams} exámenes · Desde 2000-01 hasta 2026-27, ambos inclusive.")
        assert "2017–2024" in page.locator("#cobertura").inner_text()
        assert page.locator("#document-block option").evaluate_all("(options) => options.map(option => option.value)") == ["", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        page.select_option("#document-block", "4")
        reveal_historical(page)
        page.locator('.document-card[data-id="motin-esquilache-1766"] .document-open').click()
        assert page.locator(".document-task").count() == 0
        assert "fuera del comentario de documento del modelo 2026–27" in page.locator("#document-dialog-content").inner_text()
        assert "2013 · Reserva B extraordinaria · Opción A · Documento 2" in page.locator("#document-dialog .exam-pill").all_text_contents()
        page.locator(".document-close").click()
        page.reload()
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert page.locator("#document-block").input_value() == "4"
        page.select_option("#document-block", "")
        assert page.locator('#document-block option[value="7"]').inner_text() == "7 · La Restauración (1874–1902)"
        assert page.locator("#document-grid h2").all_text_contents() == [
            f"Bloque {option['value']} · {option['text'].split(' · ', 1)[1]}"
            for option in page.locator("#document-block option").evaluate_all(
                "(options) => options.filter(option => option.value).map(option => ({value:option.value,text:option.textContent}))"
            )
            if any(int(option["value"]) in document["blocks"] for document in DATA["documents"])
        ]
        check_dialog_scroll(page)
        check_reader_navigation(browser)
        check_reader_swipe(browser, p.devices["Pixel 7"], chromium=True)
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
            page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
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
            if "has-history-toggle" in (heading.get_attribute("class") or ""):
                continue
            assert heading.evaluate(
                "(node) => {const title=node.querySelector('h2').getBoundingClientRect();"
                "const button=node.querySelector('a').getBoundingClientRect();"
                "return button.left>=title.right && button.right<=innerWidth"
                " && Math.abs(button.top+button.height/2-title.top-title.height/2)<2;}"
            )
        page.set_viewport_size(original_viewport)
        page.locator(".document-more-filters summary").click()
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
                geometries = preview.evaluate("""async (box) => {
                    const preview = box.getBoundingClientRect();
                    return Promise.all([...box.querySelectorAll('figure')].map(async node => {
                        const image = node.querySelector('img');
                        await image.decode();
                        const figure = node.getBoundingClientRect();
                        const crop = node.querySelector('.doc-image-crop');
                        const bounds = (crop || image).getBoundingClientRect();
                        return {
                            id: box.closest('.document-card').dataset.id,
                            src: image.getAttribute('src'),
                            table: box.classList.contains('document-preview-table'),
                            horizontal: Math.abs(bounds.left+bounds.width/2-figure.left-figure.width/2),
                            vertical: Math.abs(bounds.top+bounds.height/2-preview.top-preview.height/2),
                            top: Math.abs(bounds.top-figure.top),
                            contained: bounds.top>=preview.top && bounds.bottom<=preview.bottom
                                && bounds.left>=preview.left && bounds.right<=preview.right,
                            ratio: bounds.width/bounds.height,
                        };
                    }));
                }""")
                for geometry in geometries:
                    document = next(item for item in DATA["documents"] if item["id"] == geometry["id"])
                    expected_table = bool(document.get("tableImage") or document.get("image", {}).get("kind") == "table")
                    assert geometry["table"] == expected_table, (width, geometry)
                    assert geometry["horizontal"] <= 1, (width, geometry)
                    assert geometry["top" if expected_table else "vertical"] <= 1, (width, geometry)
                    assert geometry["contained"], (width, geometry)
                    image_data = next(image for image in [
                        document.get("image"), *document.get("image", {}).get("additionalImages", []),
                        document.get("tableImage"),
                    ] if image and image["src"] == geometry["src"])
                    crop = image_data.get("crop")
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
                assert abs(geometry[key] - expected) < 0.001, (document["id"], key, geometry)
            page.locator(".document-close").click()
        casas_viejas = next(item for item in DATA["documents"] if item["id"] == "casas-viejas-detenciones-1933")
        page.locator('.document-card[data-id="casas-viejas-detenciones-1933"] .document-open').click()
        assert page.locator(".document-full-source img").evaluate(
            "(image) => [image.naturalWidth, image.naturalHeight]"
        ) == [771, 567]
        assert page.locator(".document-full-source img").get_attribute("src") == casas_viejas["image"]["src"]
        assert page.locator(".document-full-source img").evaluate("(image) => getComputedStyle(image).filter") == "grayscale(1)"
        assert page.get_by_role("link", name="Ver recorte del PDF original", exact=True).get_attribute("href") == casas_viejas["image"]["originalSrc"]
        assert page.get_by_role("link", name="Ver reproducción anterior de El Debate", exact=True).get_attribute("href") == casas_viejas["image"]["corpusSrc"]
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
        assert preview_zoom.get_attribute("aria-label") == "Ver imagen: Los fusilamientos del 3 de mayo"
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
        assert page.locator(".document-zoom").count() == 0
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
        assert official_image.evaluate("(node) => [node.naturalWidth, node.naturalHeight]") == [2084, 1460]
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
        page.mouse.move(1, 1)
        assert reset_button.evaluate("(button) => getComputedStyle(button).backgroundColor") == "rgb(251, 228, 225)"
        reset_button.hover()
        assert reset_button.evaluate("(button) => getComputedStyle(button).backgroundColor") == "rgb(217, 83, 74)"
        assert page.locator(".document-results-bar #document-reset").count() == 1
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
        paragraphs = page.locator(".document-full-source > blockquote p").all_text_contents()
        assert "trabajadores de toda clase, que se organiza" in paragraphs[0]
        assert paragraphs[1] == "Los poderes de todos sus órganos emanan del pueblo."
        assert paragraphs[4] == "Artículo 2. Todos los españoles son iguales ante la ley."
        assert paragraphs[-1].endswith("legítima del Estado [...].")
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "12")
        assert page.locator(".document-card").count() == sum(12 in document["blocks"] for document in DATA["documents"])
        page.get_by_role("button", name="Ver documento: El preámbulo de la Constitución de 1978", exact=True).click()
        paragraphs = page.locator(".document-full-source > blockquote p").all_text_contents()
        assert "orden económico y social justo." in paragraphs[2]
        assert paragraphs[-2] == "En consecuencia, las Cortes aprueban y el pueblo español ratifica la siguiente CONSTITUCIÓN."
        assert paragraphs[-1] == "Constitución de 1978, Preámbulo"
        assert len(paragraphs) == 9
        page.locator(".document-close").click()
        page.select_option("#document-block", "11")
        assert page.locator(".document-card").count() == sum(11 in document["blocks"] for document in DATA["documents"])
        page.locator("#document-search").fill("zzsincoincidenciaszz")
        assert page.locator(".document-card").count() == 0
        assert page.locator("#document-empty").is_visible()
        page.locator("#document-reset").click()
        page.locator('[data-type="texto"]').click()
        for width in (320, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            check_text_card(page)
        page.locator(f'.document-card[data-id="{TEXT_DOCUMENT["id"]}"] .document-open').click()
        assert page.locator(".document-full-source > blockquote p").count() == len(reading_paragraphs(TEXT_DOCUMENT))
        page.locator(".document-close").click()
        page.goto(f"{BASE}/documentos.html?bloque=5")
        page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
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
        check_carlist_map_and_pavia(browser)
        check_symbols_and_map_classification(browser)
        check_constitution_people(browser)
        check_reader_updates(browser, p.devices["Pixel 7"])
        check_badges_without_repeated_exam_fields(browser)
        check_image_credits(browser)
        check_fitted_media_and_people(browser)
        check_below_caption_people(browser)
        check_extended_annotation_palette(browser)
        check_document_attributions(browser)
        check_numbered_paragraphs(browser)
        check_outer_quotes_with_heading(browser)
        check_grouped_texts_and_exam_filters(browser)
        check_text_content_ranking(browser)
        check_full_content_search(browser)
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
        expected_appearances = len(multi_target["appearances"])
        multi_target["blocks"].append(6)
        multi_context = browser.new_context(service_workers="block")
        multi_page = multi_context.new_page()
        multi_page.route("**/data/documentos.json", lambda route: route.fulfill(json=multi))
        multi_page.goto(f"{BASE}/documentos.html")
        multi_page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert multi_page.locator(".document-card").count() == len(DATA["documents"])
        assert multi_page.locator(
            f'.document-card[data-id="{multi_target["id"]}"] .document-exams .exam-pill'
        ).count() == expected_appearances
        total_appearances = sum(len(document["appearances"]) for document in DATA["documents"])
        assert f"{total_appearances + 1} apariciones" in multi_page.locator("#document-count").inner_text()
        multi_page.locator(f'.document-card[data-id="{multi_target["id"]}"] .document-open').click()
        assert multi_page.locator("#document-dialog-content > .document-exams li").count() == expected_appearances
        assert multi_page.locator("#document-dialog-content > .document-exams .exam-pill").count() == expected_appearances
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
        failed_page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert not failed_page.locator("#document-error").is_visible()
        invalid = json.loads(json.dumps(DATA))
        invalid["documents"][0]["blocks"] = [3]
        failed_page.route("**/data/documentos.json", lambda route: route.fulfill(json=invalid))
        failed_page.reload()
        failed_page.locator("#document-error").wait_for(state="visible")
        assert "bloques 4–12" in failed_page.locator("#document-error").inner_text()
        assert failed_page.locator(".document-card").count() == 0
        for pdf_url in (None, "https://drive.google.com/drive/folders/no-es-un-pdf"):
            invalid_pdf = json.loads(json.dumps(RAW_DATA))
            appearance = invalid_pdf["documents"][0]["appearances"][0]
            if pdf_url is None:
                del appearance["pdfUrl"]
            else:
                appearance["pdfUrl"] = pdf_url
            failed_page.unroute("**/data/documentos.json")
            failed_page.route("**/data/documentos.json", lambda route: route.fulfill(json=invalid_pdf))
            failed_page.reload()
            failed_page.locator("#document-error").wait_for(state="visible")
            assert "PDF de un examen en Drive" in failed_page.locator("#document-error").inner_text()
            assert failed_page.locator(".document-card").count() == 0
        failed.close()

        offline = browser.new_context()
        offline_page = offline.new_page()
        offline_page.goto(f"{BASE}/index.html")
        offline_page.evaluate("async () => { await navigator.serviceWorker.ready; }")
        offline_page.wait_for_function("navigator.serviceWorker.controller !== null")
        offline.set_offline(True)
        offline_page.goto(f"{BASE}/documentos.html")
        offline_page.wait_for_selector("#document-grid[aria-busy=false]", state="attached")
        assert offline_page.locator(".document-card").count() == len(DATA["documents"])
        offline_page.locator(".document-preview img").evaluate_all("(images) => images.forEach(image => image.loading = 'eager')")
        offline_page.wait_for_function("Array.from(document.querySelectorAll('.document-preview img')).every(image => image.complete && image.naturalWidth > 0)")
        assert offline_page.locator(".site-footer .credit").evaluate("(node) => getComputedStyle(node).fontSize") == "13px"
        offline_page.goto(f"{BASE}/apuntes/bloque-1.html")
        assert offline_page.locator(".site-footer").is_visible()
        assert offline_page.locator(".site-footer .credit").evaluate("(node) => getComputedStyle(node).fontSize") == "13px"
        offline.close()
        browser.close()
    print("OK: banco por tipos, bloques 4–12 (4 solo histórico), temáticas, búsqueda, a)/b), ampliación, apariciones, errores y sin conexión.")


if __name__ == "__main__":
    run()
