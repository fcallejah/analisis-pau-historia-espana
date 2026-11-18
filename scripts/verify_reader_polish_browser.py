"""Verify reader recovery and personal-list presentation in Chromium and WebKit."""
from playwright.sync_api import sync_playwright
from verify_documents_browser import DATA, check_collection_link, grouped_records


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


def check_compact_bank_header(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for path in ("documentos.html", "mis-documentos.html"):
        page.goto(f"{BASE}/{path}")
        ready(page)
        if path == "documentos.html":
            assert page.locator("#document-scope").inner_text() == (
                "394 documentos recopilados · 101 exámenes · Desde 2001-02 hasta 2026-27, ambos inclusive.")
            assert page.locator(".documents-lead, .document-saving-hint, .document-topic-hint").count() == 0
            assert page.locator("#document-topic-label").text_content() == "Explora por temática"
            assert "no implica que todos sus exámenes estén incorporados" in page.locator("#cobertura").inner_text()
        assert page.locator("#document-exam-hint").is_hidden()
        assert page.locator("#document-exam-hint").inner_text() == ""
        reset = page.get_by_role("button", name="Limpiar filtros", exact=True)
        assert reset.locator('svg[aria-hidden="true"] rect').is_visible()
        for name in ("Año de examen", "Examen", "Bloque"):
            select = page.get_by_role("combobox", name=name, exact=True)
            assert select.is_visible()
            label = page.locator(f'label[for="{select.get_attribute("id")}"]')
            assert abs(label.bounding_box()["height"] - select.bounding_box()["height"]) < 1
        exams = page.get_by_role("group", name="Por examen")
        label = exams.locator("#document-exam-label")
        year_box = exams.locator("#document-year").bounding_box()
        label_box = label.bounding_box()
        assert label_box["x"] + label_box["width"] < year_box["x"]
        assert abs(label_box["y"] + label_box["height"] / 2 - year_box["y"] - year_box["height"] / 2) <= 1
        assert int(label.evaluate("node => getComputedStyle(node).fontWeight")) >= 700
        if page.evaluate("window.innerWidth >= 1200"):
            types = page.get_by_role("group", name="Tipo de documento").bounding_box()
            exam_box = exams.bounding_box()
            toolbar = page.locator(".document-filter-toolbar").bounding_box()
            assert types["x"] + types["width"] < exam_box["x"]
            assert abs(types["y"] + types["height"] / 2 - exam_box["y"] - exam_box["height"] / 2) <= 1
            assert abs(exam_box["x"] + exam_box["width"] - toolbar["x"] - toolbar["width"]) <= 1
        page.select_option("#document-year", "2027")
        page.select_option("#document-exam", "modelo orientaciones pau")
        assert page.locator("#document-exam-hint").is_visible()
        page.select_option("#document-year", "2014")
        assert page.locator("#document-exam-hint").is_hidden()
        assert page.locator("#document-exam-hint").inner_text() == ""
        assert page.locator('#document-exam option:disabled').all_text_contents() == ["Reserva ? - No existe"]
        page.select_option("#document-year", "2017")
        assert "no faltan comentarios de documentos porque no cayó ninguno" in page.locator(
            "#document-exam-hint").inner_text()
        assert page.locator("#document-exam-hint").is_visible()
        page.select_option("#document-year", "")
        assert page.locator("#document-exam-hint").is_hidden()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert not errors, errors
    context.close()


def check_local_pdf_import(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    for year in range(2002, 2008):
        page.select_option("#document-year", str(year))
        assert page.locator("#document-exam option").count() == 7
        assert page.locator(".document-card").count() > 0
        assert "Documento null" not in page.locator("#document-grid").inner_text()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.select_option("#document-year", "2006")
    assert "copias no originales" in page.locator("#document-exam-hint").inner_text()
    assert all(kind.startswith("Texto") for kind in page.locator(".document-card .document-kind").all_text_contents())
    open_card(page, "hemingway-guerra-civil")
    assert "copia no original" in page.locator(".document-full-source .document-reading-note").inner_text()
    assert page.get_by_role("link", name="Ver copia PDF de origen", exact=True).get_attribute(
        "href").startswith("https://drive.google.com/file/d/")
    page.reload()
    ready(page)
    assert page.locator("#document-year").input_value() == "2006"
    assert page.locator("#document-dialog").is_visible()
    page.locator(".document-close").click()
    page.select_option("#document-year", "2007")
    page.select_option("#document-exam", "examen 1")
    open_card(page, "huelga-1917-caballeria")
    assert page.locator(".document-full-source img").evaluate("img=>img.naturalWidth>0")
    assert "Bloque II · Opción A" in page.locator("#document-dialog-content > .document-exams").inner_text()
    assert "Documento" not in page.locator("#document-dialog-content > .document-exams").inner_text()
    assert page.get_by_role("link", name="Ver PDF de origen", exact=True).get_attribute(
        "href").startswith("https://drive.google.com/file/d/")
    page.locator(".document-close").click()
    page.locator("#document-reset").click()
    page.select_option("#document-year", "2004")
    open_card(page, "canciones-guerra-civil")
    paragraphs = page.locator(".document-full-source > blockquote p").all_text_contents()
    assert "¿Para qué tantos humos" in paragraphs[0] and "Canción republicana" in paragraphs[0]
    assert "Cuando se enteró" in paragraphs[1] and "Canción falangista" in paragraphs[1]
    assert "Cuando se enteró" not in paragraphs[0]
    page.locator(".document-close").click()
    page.locator("#document-reset").click()
    page.select_option("#document-year", "2006")
    page.select_option("#document-exam", "examen 1")
    open_card(page, "el-fuero-de-los-espanoles-y-los-limites-de-los-derechos")
    assert "copia no original" in page.locator("#document-dialog-content > .document-reading-note").inner_text()
    page.locator(".document-text-versions > summary").click()
    copied = page.locator('[data-version-id="el-fuero-de-los-espanoles-y-los-limites-de-los-derechos-pdf-2006-1-4"]')
    assert copied.is_visible()
    assert " ".join(copied.locator("blockquote").inner_text().split()) == " ".join(page.locator(
        ".document-full-source > blockquote").inner_text().split())
    assert "2007" in page.locator(".document-text-versions > .document-variant-sources").inner_text()
    assert "copia no original" in copied.locator(".document-reading-note").inner_text()
    assert page.locator(".document-full-source > .document-reading-note").count() == 0
    assert not errors, errors
    context.close()


def check_pdf_source_polish(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    page.select_option("#document-year", "2002")
    page.select_option("#document-exam", "examen 1")
    open_card(page, "serrano-suner-estado")
    footer = page.locator(".document-full-source .document-attribution")
    assert footer.inner_text().startswith("Fuente: Ramón SERRANO SUÑER")
    assert footer.evaluate("p=>getComputedStyle(p).textAlign") == "right"
    assert footer.evaluate("p=>getComputedStyle(p).textAlignLast") == "right"
    assert page.locator(".document-full-source > blockquote p").first.evaluate(
        "p=>getComputedStyle(p).textAlign") == "justify"
    page.locator(".document-close").click()
    page.locator("#document-reset").click()
    corpus = page.request.get(f"{BASE}/data/documentos.json").json()
    tables = [record for record in corpus["documents"] if record.get("table")
              and all(a.get("sourceType") == "pdf" for a in record["appearances"])]
    assert len(tables) == 8
    vector_page = context.new_page()
    for record in tables:
        identity = record["id"]
        open_card(page, identity)
        assert page.locator(".document-full-source img").get_attribute("src").endswith(".svg")
        assert page.locator(".document-original-link").get_attribute("href") == record["image"]["originalSrc"]
        page.locator(".document-table-details > summary").click()
        actual = page.locator(".document-table tbody tr").evaluate_all(
            "rows=>rows.map(row=>[...row.cells].map(cell=>cell.textContent))")
        assert actual == record["table"]["rows"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert page.locator("#document-dialog").evaluate("dialog=>dialog.scrollWidth<=dialog.clientWidth+1")
        vector_page.goto(f'{BASE}/{record["image"]["src"]}')
        overflow = vector_page.evaluate("""() => {
            const svg=document.querySelector('svg'), view=svg.viewBox.baseVal;
            return [...svg.querySelectorAll('text')].filter(node=>{
                const b=node.getBBox();
                return b.x<0 || b.y<0 || b.x+b.width>view.width || b.y+b.height>view.height;
            }).map(node=>node.textContent);
        }""")
        assert not overflow, (identity, overflow)
        clipped = vector_page.evaluate("""() => [...document.querySelectorAll('g[data-row]')].filter(group=>{
            const cell=group.querySelector('rect').getBBox();
            return [...group.querySelectorAll('text')].some(node=>{
                const b=node.getBBox();
                return b.x<cell.x || b.x+b.width>cell.x+cell.width || b.y<cell.y || b.y+b.height>cell.y+cell.height;
            });
        }).map(group=>group.textContent)""")
        assert not clipped, (identity, clipped)
        page.locator(".document-close").click()
    for identity, path in (("guernica-picasso", "guernica-reina-sofia.jpg"),
                           ("primera-peseta-1869", "peseta-1869-fuenterrebollo.jpg")):
        open_card(page, identity)
        assert page.locator(".document-full-source img").get_attribute("src").endswith(path)
        assert page.locator(".document-original-link").is_visible()
        page.locator(".document-close").click()
    assert not errors, errors
    context.close()


def check_curriculum_frequencies(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    corpus = page.request.get(f"{BASE}/data/documentos.json").json()
    records = {record["id"]: record for record in corpus["documents"]}
    counts = {identity: len(record["appearances"]) for identity, record in records.items()}
    for group in corpus["textGroups"]:
        counts[group[0]] = sum(len(records[identity]["appearances"]) for identity in group)
    baseline = page.locator(".document-card").evaluate_all("cards=>cards.map(card=>card.dataset.id)")
    treaty = "tratado-de-paris-y-perdida-del-imperio-colonial"
    murat = "bando-de-murat-tras-el-levantamiento-del-2-de-mayo"
    unit_select = page.get_by_role("combobox", name="Subbloque de las orientaciones 2026–27", exact=True)
    sort = page.locator("#document-frequency-sort")
    assert unit_select.locator("optgroup").count() == 8
    assert unit_select.locator("option").count() == 26
    more = page.locator(".document-more-filters summary")
    more.click()
    for theme in ("light", "dark"):
        page.evaluate("theme=>document.documentElement.dataset.theme=theme", theme)
        assert page.locator(".document-filter-divider").count() == 1
        assert page.locator(".document-filter-divider").evaluate_all("""nodes=>nodes.every(node=>{
            const s=getComputedStyle(node);
            return s.height==='1px' && s.borderTopWidth==='0px' && s.backgroundImage.includes('linear-gradient');
        })""")
        for property in ("height", "padding", "borderRadius", "backgroundColor", "color", "font"):
            assert unit_select.evaluate("(node,property)=>getComputedStyle(node)[property]", property) == page.locator(
                "#document-year").evaluate("(node,property)=>getComputedStyle(node)[property]", property)
        assert page.locator(".document-results-bar #document-frequency-sort").count() == 1
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    more.click()
    sort.click()
    assert sort.get_attribute("aria-pressed") == "true"
    ranked = page.locator(".document-card:visible").evaluate_all("cards=>cards.map(card=>card.dataset.id)")
    assert [counts[identity] for identity in ranked] == sorted((counts[identity] for identity in ranked), reverse=True)
    assert counts[ranked[0]] == max(counts[identity] for identity in ranked)
    assert ranked.index(murat) >= sum(counts[identity] > counts[murat] for identity in ranked)
    assert f"Bloque {records[ranked[0]]['blocks'][0]}" in page.locator(
        ".document-card:visible").first.locator(".document-kind").text_content()
    for unit in corpus["curriculum"]["units"]:
        total = sum(counts[identity] for identity in unit["documentIds"])
        assert unit_select.locator(f'option[value="{unit["id"]}"]').inner_text().endswith(f"({total})")
    for unit in corpus["curriculum"]["units"]:
        unit_select.select_option(unit["id"])
        actual = page.locator(".document-card").evaluate_all("cards=>cards.map(card=>card.dataset.id)")
        assert set(actual) == set(unit["documentIds"]), unit["id"]
        assert len(actual) == len(set(actual))
        assert [counts[identity] for identity in actual] == sorted((counts[identity] for identity in actual), reverse=True)
        assert page.locator("#document-empty").is_visible() == (not actual)
    unit_select.select_option("ii-10")
    page.select_option("#document-year", "2025")
    page.select_option("#document-exam", "modelo orientaciones pau")
    assert page.locator(".document-card").count() == 1
    assert page.locator(".document-card .exam-pill").count() == counts[treaty]
    page.locator('.document-card [data-document-mark="favorite"]').click()
    open_card(page, treaty)
    page.wait_for_function(
        "JSON.parse(sessionStorage.getItem('pau-he.documents.view.v1')).unit==='ii-10'")
    page.reload()
    ready(page)
    assert page.input_value("#document-unit") == "ii-10" and sort.get_attribute("aria-pressed") == "true"
    assert page.locator("#document-year").input_value() == "2025"
    assert page.locator("#document-dialog").is_visible()
    assert page.locator("#document-dialog-content > .document-exams a").count() == counts[treaty]
    page.locator(".document-close").click()
    page.locator("#document-reset").click()
    assert page.input_value("#document-unit") == "" and sort.get_attribute("aria-pressed") == "false"
    assert page.locator(".document-card").evaluate_all("cards=>cards.map(card=>card.dataset.id)") == baseline
    page.add_init_script("""if (location.pathname.endsWith('/documentos.html')) {
        const key='pau-he.documents.view.v1', view=JSON.parse(sessionStorage.getItem(key));
        if (view) {
            delete view.unit;
            delete view.frequencyOrder;
            sessionStorage.setItem(key,JSON.stringify(view));
        }
    }""")
    page.reload()
    ready(page)
    assert page.input_value("#document-unit") == "" and sort.get_attribute("aria-pressed") == "false"
    assert not page.locator("#document-storage-status").is_visible()
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    unit_select.select_option("ii-10")
    sort.click()
    assert page.locator(".document-card").count() == 1
    assert page.locator(".document-card").get_attribute("data-id") == treaty
    assert page.locator(".document-card .exam-pill").count() == counts[treaty]
    page.reload()
    ready(page)
    assert page.input_value("#document-unit") == "ii-10" and sort.get_attribute("aria-pressed") == "true"
    assert not errors, errors
    context.close()


def check_orientation_models(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    records = {record["id"]: record for record in grouped_records(
        page.request.get(f"{BASE}/data/documentos.json").json())}
    assert "3 apariciones incorporadas" in page.locator(
        '.document-card[data-id="portada-constitucion-1812"] .document-meta').inner_text()
    assert "2 apariciones incorporadas" in page.locator(
        '.document-card[data-id="huelga-general-1917-fotografia"] .document-meta').inner_text()
    for year, pdf in (
        (2025, "1xnyJ3ZVFoIbyiME-PoWajjj7-eN64n8j"),
        (2026, "1YP4IJzY79cz01vqPXlET3D4oBWIU8oP0"),
        (2027, "1namjFwbxIfKvrgxFEKi5VWmSuj5wOFxa"),
    ):
        page.select_option("#document-year", str(year))
        if year != 2027:
            assert page.locator("#document-exam option").all_text_contents()[1:4] == [
                "Titular ordinaria", "Titular extraordinaria", "Modelo orientaciones PAU",
            ]
        page.select_option("#document-exam", "modelo orientaciones pau")
        cards = page.locator(".document-card:visible")
        assert cards.count() == 4
        assert cards.locator(f'.document-exams a[href="https://drive.google.com/file/d/{pdf}/view"]').count() == 4
        assert cards.locator(".document-exams a").count() > 4
        expected = sum(len(records[identity]["appearances"])
                       for identity in cards.evaluate_all("cards=>cards.map(card=>card.dataset.id)"))
        assert cards.locator(".document-exams a").count() == expected
        for card in cards.all():
            sources = card.locator(".document-exams a").evaluate_all("links=>links.map(link=>link.href)")
            total = len(sources)
            label = "aparición incorporada" if total == 1 else "apariciones incorporadas"
            assert f"{total} {label}" in card.locator(".document-meta").inner_text()
            open_card(page, card.get_attribute("data-id"))
            assert page.locator("#document-dialog-content > .document-exams a").evaluate_all(
                "links=>links.map(link=>link.href)") == sources
            meta = page.locator("#document-dialog-content > .document-meta").inner_text()
            label = "aparición" if total == 1 else "apariciones"
            assert f"{total} {label} en total" in meta
            if total > 1:
                assert "1 con los filtros actuales" in meta
            page.locator(".document-close").click()
    open_card(page, "franco-ante-las-cortes-sobre-democracia-y-partidos")
    assert "5 apariciones en total" in page.locator("#document-dialog-content > .document-meta").inner_text()
    page.wait_for_function(
        "JSON.parse(sessionStorage.getItem('pau-he.documents.view.v1')).year==='2027'")
    page.reload()
    ready(page)
    assert page.locator("#document-year").input_value() == "2027"
    assert page.locator("#document-exam").input_value() == "modelo orientaciones pau"
    assert page.locator("#document-dialog").is_visible()
    assert page.locator("#document-dialog-content > .document-exams a").count() == 5
    assert "5 apariciones en total" in page.locator("#document-dialog-content > .document-meta").inner_text()
    assert page.locator(".document-card:visible").count() == 4
    assert not page.locator("#document-storage-status").is_visible()
    assert not errors, errors
    context.close()


def check_docs_reproductions(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    cases = (
        ("retrato-ramon-maria-narvaez", [(514, 800)], [(362, 352, -92, -96)]),
        ("abrazo-vergara-1839", [(1200, 752)], []),
        ("espartero-narvaez-retratos-2016", [(1609, 2048), (514, 800)], [(362, 511, -92, -78)]),
    )
    for identifier, dimensions, crops in cases:
        open_card(page, identifier)
        source = page.locator(".document-full-source")
        images = source.locator("img")
        assert images.count() == len(dimensions)
        assert source.locator(".document-reproduction-note").count() == 0
        assert source.locator(".document-exam-caption").count() == len(dimensions)
        assert source.locator(".document-original-link").count() == len(dimensions)
        for image, expected in zip(images.all(), dimensions):
            assert image.evaluate("node=>[node.naturalWidth,node.naturalHeight]") == list(expected)
            assert image.evaluate("node=>getComputedStyle(node).filter") == "none"
            if identifier != "abrazo-vergara-1839":
                colored = image.evaluate("""node => {
                    const canvas = document.createElement('canvas');
                    canvas.width = canvas.height = 64;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(node, 0, 0, 64, 64);
                    const pixels = ctx.getImageData(0, 0, 64, 64).data;
                    let count = 0;
                    for (let i = 0; i < pixels.length; i += 4) {
                        if (Math.max(...pixels.slice(i, i + 3)) - Math.min(...pixels.slice(i, i + 3)) > 20) count++;
                    }
                    return count / (64 * 64);
                }""")
                assert colored > 0.25, (identifier, colored)
        frames = source.locator(".doc-image-crop")
        assert frames.count() == len(crops)
        for frame, (width, height, left, top) in zip(frames.all(), crops):
            actual = frame.evaluate("""node => {
                const frame = node.getBoundingClientRect(), image = node.querySelector('img').getBoundingClientRect();
                return [frame.width / frame.height, (image.left - frame.left) / frame.width,
                    (image.top - frame.top) / frame.height];
            }""")
            for measured, expected in zip(actual, (width / height, left / width, top / height)):
                assert abs(measured - expected) < 0.01, (identifier, actual)
        assert page.locator("#document-dialog").evaluate("node=>node.scrollWidth<=node.clientWidth")
        page.keyboard.press("Escape")
    context.close()


def check_text_selection_presentation(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    record = next(record for record in grouped_records(page.request.get(f"{BASE}/data/documentos.json").json())
                  if record["id"] == "constitucion-1978-preambulo-suplente-b")
    total = len(record["appearances"])
    card = page.locator('.document-card[data-id="constitucion-1978-preambulo-suplente-b"]')
    assert f"{total} apariciones incorporadas" in card.locator(".document-meta").inner_text()
    card.locator(".document-open").click()
    assert page.locator("#document-dialog-content > .document-meta strong").inner_text() == f"{total} apariciones en total"
    quote = page.locator(".document-full-source > blockquote")
    assert "En consecuencia, las Cortes aprueban" in quote.inner_text()
    main_text = quote.inner_text()
    versions = page.locator(".document-text-versions")
    assert versions.count() == 1
    assert not versions.evaluate("node=>node.open")
    assert not versions.locator(".document-variant-sources").first.is_visible()
    versions.locator(":scope > summary").click()
    assert versions.locator(":scope > .document-variant-sources .exam-pill").count() == 1
    assert versions.locator(".document-text-version").count() == 2
    alternative = versions.locator('[data-version-id="constitucion-1978-preambulo-suplente-b"]')
    assert alternative.locator(".exam-pill").count() == 4
    assert "En consecuencia, las Cortes aprueban" not in alternative.locator("blockquote").inner_text()
    page.wait_for_function(
        "JSON.parse(sessionStorage.getItem('pau-he.documents.view.v1')).dialog.details[0]===true")
    page.reload()
    ready(page)
    assert versions.evaluate("node=>node.open")
    assert quote.inner_text() == main_text
    page.locator(".document-close").click()
    page.select_option("#document-year", "2025")
    assert card.locator(".document-exams a").count() == total
    assert f"{total} apariciones incorporadas" in card.locator(".document-meta").inner_text()
    card.locator(".document-open").click()
    assert quote.inner_text() == main_text
    meta = page.locator("#document-dialog-content > .document-meta")
    assert f"{total} apariciones en total" in meta.inner_text()
    assert "1 con los filtros actuales" in meta.inner_text()
    assert page.locator("#document-dialog-content > .document-exams a").count() == total
    assert not versions.evaluate("node=>node.open")
    page.reload()
    ready(page)
    assert page.locator("#document-year").input_value() == "2025"
    assert quote.inner_text() == main_text
    assert card.locator(".document-exams a").count() == total
    assert page.locator("#document-dialog-content > .document-exams a").count() == total
    page.locator('#document-dialog [data-document-mark="favorite"]').click()
    page.locator(".document-close").click()
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    assert page.locator(".document-card").count() == 1
    assert card.locator(".document-exams a").count() == total
    card.locator(".document-open").click()
    assert quote.inner_text() == main_text
    assert f"{total} apariciones en total" in page.locator("#document-dialog-content > .document-meta").inner_text()
    for theme in ("light", "dark"):
        page.evaluate("theme=>document.documentElement.dataset.theme=theme", theme)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        versions.locator(":scope > summary").click()
        assert page.locator("#document-dialog").evaluate("node=>node.scrollWidth<=node.clientWidth")
    assert not errors, errors
    context.close()


def check_exam_pdf_links(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    context.route("https://drive.google.com/file/d/**", lambda route: route.fulfill(
        content_type="text/html", body="<title>PDF de examen</title><p>PDF de examen</p>"))
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    card = page.locator(".document-card:visible").first
    record = next(item for item in DATA["documents"] if item["id"] == card.get_attribute("data-id"))
    pill = card.locator(".document-exams a").first
    pdf_url = pill.get_attribute("href")
    assert pdf_url.startswith("https://drive.google.com/file/d/")
    assert pill.get_attribute("rel") == "noopener noreferrer"
    assert "otra pestaña" in pill.get_attribute("aria-label")
    assert page.locator(".document-card .document-exams .exam-pill").evaluate_all(
        "pills=>pills.every(pill=>pill.parentElement.matches('a[target=\"_blank\"]'))")
    with page.expect_popup() as opened:
        pill.click()
    popup = opened.value
    popup.wait_for_load_state()
    assert popup.url == pdf_url
    popup.close()
    assert not page.locator("#document-dialog").is_visible()
    pill.focus()
    with page.expect_popup() as opened:
        pill.press("Enter")
    popup = opened.value
    popup.wait_for_load_state()
    assert popup.url == pdf_url
    popup.close()
    card.locator('[data-document-mark="favorite"]').click()
    card.locator(".document-open").click()
    assert page.locator("#document-dialog-content > .document-exams a").first.get_attribute("href") == pdf_url
    check_collection_link(page, record)
    page.locator(".document-close").click()
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    assert page.locator(".document-card .document-exams a").first.get_attribute("href") == pdf_url
    for theme in ("light", "dark"):
        page.evaluate("theme=>document.documentElement.dataset.theme=theme", theme)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert not errors, errors
    context.close()


def check_historical_archive(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    toggle = page.locator(".document-history-toggle")
    archive = page.locator("#document-block-4-cards")
    assert toggle.get_attribute("aria-label") == "Mostrar documentos históricos del bloque 4"
    assert toggle.get_attribute("aria-expanded") == "false"
    assert not archive.is_visible()
    assert archive.locator(".document-card").count() == 4
    assert page.locator(".document-historical-notice").is_visible()
    for width in (320, 375, 810, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        bounds = toggle.bounding_box()
        title = page.locator(".has-history-toggle h2").bounding_box()
        assert bounds["width"] >= 44 and bounds["height"] >= 44
        assert bounds["x"] + bounds["width"] <= title["x"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    first = page.locator(".document-card:visible").first
    first_title = first.locator("h3").inner_text()
    visible_count = page.locator(".document-card:visible").count()
    first.locator(".document-open").click()
    assert page.locator("#document-dialog-title").inner_text() == first_title
    assert page.locator(".document-previous").is_disabled()
    assert f"de {visible_count}:" in page.locator(".document-reader-status").inner_text()
    page.evaluate("""() => {
        window.historicalReaderClosed = false;
        document.querySelector('#document-dialog').addEventListener('close', () => {
            window.historicalReaderClosed = true;
        }, {once: true});
    }""")
    page.keyboard.press("Escape")
    page.wait_for_function("window.historicalReaderClosed && !document.querySelector('#document-dialog').open && document.activeElement?.classList.contains('document-open')")
    toggle.focus()
    page.keyboard.press("Enter")
    assert archive.is_visible()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert toggle.get_attribute("aria-label") == "Ocultar documentos históricos del bloque 4"
    assert toggle.evaluate("node=>node===document.activeElement")
    page.reload()
    ready(page)
    assert archive.is_visible()
    page.select_option("#document-block", "4")
    assert archive.is_visible()
    page.locator("#document-reset").click()
    assert not archive.is_visible()
    page.locator("#document-search").fill("Jovellanos")
    assert not archive.is_visible()
    assert "1 documento" in page.locator("#document-count").inner_text()
    toggle.click()
    assert archive.locator(".document-card:visible").count() == 1
    archive.locator('[data-document-mark="favorite"]').click()
    archive.locator(".document-open").click()
    page.evaluate("""key=>{
        const view=JSON.parse(sessionStorage.getItem(key));
        delete view.historicalVisible;
        sessionStorage.setItem(key,JSON.stringify(view));
    }""", VIEW)
    page.reload()
    ready(page)
    assert page.locator("#document-dialog").is_visible()
    assert archive.is_visible()
    page.keyboard.press("Escape")
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    assert not archive.is_visible()
    toggle.click()
    assert archive.is_visible()
    assert archive.locator('[data-document-mark="favorite"]').get_attribute("aria-pressed") == "true"
    toggle.click()
    assert not archive.is_visible()
    assert page.locator("#document-count").inner_text().startswith("1 documento")
    assert not errors, errors
    context.close()


def check_1812_compilation_and_2004_reproductions(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    records = {r["id"]: r for r in page.request.get(f"{BASE}/data/documentos.json").json()["documents"]}
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    identity = "constitucion-1812-articulos-2008"
    expected = records[identity]["studyCompilation"]["text"]
    page.select_option("#document-year", "2012")
    page.select_option("#document-exam", "examen 4")
    open_card(page, identity)
    quote = page.locator(".document-full-source > blockquote")
    assert quote.locator("p").all_text_contents() == expected
    assert page.get_by_role("heading", name="Recopilación completa de fragmentos para estudiar").is_visible()
    headings = quote.locator(".document-source-heading")
    assert headings.all_text_contents() == [
        "CONSTITUCIÓN POLÍTICA DE LA MONARQUÍA ESPAÑOLA",
        "TÍTULO I. DE LA NACIÓN ESPAÑOLA Y DE LOS ESPAÑOLES",
        "CAPÍTULO I", "De la Nación Española",
    ]
    assert headings.evaluate_all("""nodes => nodes.every(node => {
        const style = getComputedStyle(node);
        return style.textAlign === 'center' && Number(style.fontWeight) >= 700;
    })""")
    assert quote.locator("p").all_text_contents().count("[…]") == 3
    assert "No es el texto íntegro" in page.locator(".document-full-source > .document-reading-note").inner_text()
    assert "8 apariciones en total" in page.locator("#document-dialog-content > .document-meta").inner_text()
    versions = page.locator(".document-text-versions")
    versions.locator("summary").click()
    assert versions.locator(".document-text-version").count() == 8
    assert versions.locator(":scope > .document-variant-sources").count() == 0
    page.reload()
    ready(page)
    assert quote.locator("p").all_text_contents() == expected
    assert versions.evaluate("node=>node.open")
    page.locator('#document-dialog [data-document-mark="favorite"]').click()
    page.keyboard.press("Escape")
    page.goto(f"{BASE}/mis-documentos.html")
    ready(page)
    open_card(page, identity)
    assert quote.locator("p").all_text_contents() == expected
    page.keyboard.press("Escape")
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    page.locator("#document-reset").click()
    open_card(page, "constitucion-1869")
    paragraphs = page.locator(".document-full-source > blockquote > p")
    assert paragraphs.first.inner_text() == "Constitución Española de 1 de junio de 1869."
    assert paragraphs.first.evaluate("""n=>{
        const s=getComputedStyle(n);
        return s.textAlign==='center' && s.textAlignLast==='center' && Number(s.fontWeight)>=700;
    }""")
    assert paragraphs.nth(1).inner_text().startswith("“LA NACIÓN ESPAÑOLA")
    assert paragraphs.nth(1).evaluate("n=>getComputedStyle(n).textAlign==='justify'")
    page.keyboard.press("Escape")
    for identity, year, exam in (("fernando-vii-jura-1820", "2004", "examen 1"),
                                ("goya-carga-mamelucos", "2004", "examen 2"),
                                ("asamblea-estudiantes-barcelona-1966", "2004", "examen 2"),
                                ("primer-gobierno-republica-1873", "2004", "examen 3"),
                                ("sagasta-embudo-electoral", "2004", "examen 4"),
                                ("alegoria-republica-1931", "2004", "examen 5"),
                                ("mural-constitucion-1812-cadiz", "2004", "examen 5"),
                                ("prim-busca-regimen-caricatura", "2005", "examen 4"),
                                ("prim-busca-regimen-caricatura", "2014", "titular ordinaria"),
                                ("proclamacion-republica-fotografia", "2005", "examen 6"),
                                ("directorio-civil-alfonso-xiii-1925", "2005", "examen 1"),
                                ("directorio-civil-alfonso-xiii-1925", "2007", "examen 6"),
                                ("directorio-civil-alfonso-xiii-1925", "2016", "titular extraordinaria"),
                                ("huelga-1917-caballeria", "2007", "examen 1"),
                                ("camino-exilio-1939", "2007", "examen 5"),
                                ("cartel-ayuda-republica-francia", "2007", "examen 6")):
        page.select_option("#document-year", year)
        page.select_option("#document-exam", exam)
        record = records[identity]
        data = record["image"]
        open_card(page, identity)
        image = page.locator(".document-full-source .document-image-figure img")
        assert image.get_attribute("src") == data["src"]
        assert image.evaluate("n=>[n.naturalWidth,n.naturalHeight]") == [data["width"], data["height"]]
        assert image.evaluate("n=>getComputedStyle(n).filter") == "none"
        caption = record["examCaption"]["text"] if "examCaption" in record else "(Sin descripción)"
        assert page.locator(".document-full-source .document-exam-caption").inner_text() == caption
        if "reproductionNote" in data:
            assert page.locator(".document-full-source .document-reproduction-note").inner_text() == data["reproductionNote"]
        assert page.get_by_role("link", name="Ver recorte del PDF original", exact=True).get_attribute("href") == data["originalSrc"]
        if "crop" in data:
            assert image.evaluate("""(n,c)=>{
                const r=n.getBoundingClientRect(),f=n.parentElement.getBoundingClientRect();
                const aspect=n.naturalWidth/n.naturalHeight*c.width/c.imageWidth*c.imageHeight/c.height;
                return Math.abs(f.width/f.height-aspect)<0.002
                    && Math.abs(r.width/r.height-n.naturalWidth/n.naturalHeight)<0.002
                    && Math.abs((f.top-r.top)/f.height+c.top/c.height)<0.002
                    && Math.abs((f.left-r.left)/f.width+c.left/c.width)<0.002;
            }""", data["crop"])
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
        page.keyboard.press("Escape")
    page.select_option("#document-exam", "")
    for year in ("2005", "2014"):
        page.select_option("#document-year", year)
        open_card(page, "mural-constitucion-1812-cadiz")
        assert page.locator(".document-full-source img").get_attribute("src") == records["mural-constitucion-1812-cadiz"]["image"]["src"]
        page.keyboard.press("Escape")
    assert not errors, errors
    context.close()


def check_pablo_iglesias_marker(browser, options):
    context = browser.new_context(service_workers="block", reduced_motion="reduce", **options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/documentos.html")
    ready(page)
    page.select_option("#document-year", "2004")
    page.select_option("#document-exam", "examen 6")
    identity = "pablo-iglesias-primero-mayo"
    assert "primero de mayo" in page.locator(f'.document-card[data-id="{identity}"]').inner_text()
    open_card(page, identity)
    assert "primero de mayo" in page.locator("#document-dialog-title").inner_text()
    assert "primero de mayo" in page.locator(".document-exam-caption").inner_text()
    image = page.locator(".document-person-stage img")
    assert image.evaluate("n=>[n.naturalWidth,n.naturalHeight]") == [1080, 1350]
    assert image.evaluate("n=>getComputedStyle(n).filter") == "none"
    stage = page.locator(".document-person-stage")
    before = stage.bounding_box()
    toggle = page.locator(".document-person-toggle")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert not page.locator(".document-person-overlay").is_visible()
    toggle.focus()
    page.keyboard.press("Enter")
    assert toggle.get_attribute("aria-expanded") == "true"
    assert page.locator(".document-person-label").all_text_contents() == ["Pablo Iglesias"]
    assert page.locator(".document-person-role").all_text_contents() == ["Fundador del PSOE"]
    page.wait_for_function("""() => {
        const stage=document.querySelector('.document-person-stage'),r=stage.getBoundingClientRect();
        const dot=stage.querySelector('circle');
        if (!dot?.getScreenCTM()) return false;
        const pixel=new DOMPoint(dot.cx.baseVal.value,dot.cy.baseVal.value).matrixTransform(dot.getScreenCTM());
        const x=(pixel.x-r.left)/r.width*1080,y=(pixel.y-r.top)/r.height*1350;
        return x>=480 && x<=500 && y>=1080 && y<=1110;
    }""")
    after = stage.bounding_box()
    assert abs(before["width"] - after["width"]) < 1
    assert abs(before["height"] - after["height"]) < 1
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
    assert page.get_by_role("link", name="Ver recorte del PDF original", exact=True).get_attribute("href") == "assets/documentos/pdf-2004-6-2.png"
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "false"
    assert not page.locator(".document-person-overlay").is_visible()
    assert not errors, errors
    context.close()


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
    assert box.locator(".document-zoom").count() == 0
    assert centered(page)
    box.evaluate("node => node.scrollLeft = (node.scrollWidth - node.clientWidth) * .7")
    dialog = page.locator("#document-dialog")
    dialog.evaluate("node => node.scrollTop = 320")
    page.wait_for_function("""key => {
        const saved = JSON.parse(sessionStorage.getItem(key));
        const dialog = document.querySelector('#document-dialog');
        const box = document.querySelector('.document-full-source');
        return saved?.dialog && saved.dialog.position.top === dialog.scrollTop
            && saved.dialog.source.left === box.scrollLeft;
    }""", arg=VIEW)
    saved = page.evaluate("key => JSON.parse(sessionStorage.getItem(key))", VIEW)
    page.evaluate("""key => {
        const old = JSON.parse(sessionStorage.getItem(key));
        delete old.savedFilter;
        delete old.dialog.opener;
        old.dialog.zoom = true;
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
        assert box.locator(".document-zoom").count() == 0
        assert dialog.locator(".document-reader-controls button").count() == 3
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
        for theme, expected in (("light", "rgb(178, 58, 48)"), ("dark", "rgb(255, 170, 160)")):
            page.evaluate("theme=>document.documentElement.dataset.theme=theme", theme)
            for year in range(2017, 2025):
                page.select_option("#document-year", str(year))
                exam = page.locator("#document-exam")
                assert exam.is_disabled()
                assert exam.locator("option:checked").inner_text() == "Sin comentario de documento"
                assert exam.evaluate("node=>getComputedStyle(node).color") == expected
                assert exam.evaluate("node=>getComputedStyle(node).webkitTextFillColor") == expected
                assert page.locator("#document-exam-hint").evaluate("node=>getComputedStyle(node).color") == expected
                assert page.locator("#document-exam-hint").inner_text() == (
                    "Entre 2017-2024, ambos inclusive, el formato PAU era solo de cuestiones cortas y tema; "
                    "no faltan comentarios de documentos porque no cayó ninguno."
                )
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            for year, count in ((2025, 7), (2026, 5), (2014, 5), (2016, 5)):
                page.select_option("#document-year", str(year))
                assert page.locator("#document-exam option:not(:disabled)").count() == count + 1
                assert page.locator("#document-exam option").count() == (8 if year >= 2025 else 7)
                if year in (2014, 2016):
                    label = "Reserva ? - No existe" if year == 2014 else "Suplente ? - No existe"
                    assert page.locator("#document-exam option:disabled").all_text_contents() == [label]
                assert "is-format-warning" not in (page.locator("#document-exam").get_attribute("class") or "")
                assert not page.locator("#document-exam").is_disabled()
                assert page.locator("#document-exam option").nth(1).inner_text() == "Titular ordinaria"
                assert page.locator("#document-exam option").nth(2).inner_text() == "Titular extraordinaria"
        page.evaluate("document.documentElement.dataset.theme='light'")
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


def check_exam_order(browser, options):
    context = browser.new_context(service_workers="block", **options)
    page = context.new_page()
    titulars = ["Titular ordinaria", "Titular extraordinaria"]
    expected = {
        "2003": [f"Examen {i}" for i in range(1, 7)],
        "2010": titulars + ["Reserva A ordinaria", "Reserva B ordinaria",
                            "Reserva A extraordinaria", "Reserva B extraordinaria"],
        "2011": [f"Examen {i} {session}" for session in ("ordinaria", "extraordinaria") for i in range(1, 4)],
        "2013": titulars + ["Reserva A ordinaria", "Reserva B ordinaria",
                            "Reserva A extraordinaria", "Reserva B extraordinaria"],
        "2014": titulars + ["Reserva A", "Reserva B", "Examen ?"],
        "2016": titulars + ["Reserva A 2", "Reserva B 3", "Suplente extraordinaria"],
        "2025": titulars + ["Modelo orientaciones PAU", "Suplente 1 A", "Suplente 1 B", "Suplente 2 A", "Suplente 2 B"],
        "2026": titulars + ["Modelo orientaciones PAU", "Suplente ordinaria", "Suplente extraordinaria"],
    }
    for path in ("documentos.html", "mis-documentos.html"):
        page.goto(f"{BASE}/{path}")
        ready(page)
        for year, labels in expected.items():
            page.select_option("#document-year", year)
            assert page.locator("#document-exam option:enabled").all_text_contents() == [
                "Todos los exámenes", *labels,
            ], (path, year)
        page.select_option("#document-year", "2010")
        page.select_option("#document-exam", "extraordinaria reserva a")
        page.reload()
        ready(page)
        assert page.locator("#document-exam").input_value() == "extraordinaria reserva a"
        assert page.locator("#document-exam option:checked").inner_text() == "Reserva A extraordinaria"
        if path == "documentos.html":
            cards = page.locator(".document-card:visible")
            assert cards.count() > 0
            for card in cards.all():
                labels = card.locator(".exam-pill").all_text_contents()
                assert any(label.startswith("2010 · Reserva A extraordinaria") for label in labels)
                assert all("Extraordinaria reserva A" not in label for label in labels)
            page.select_option("#document-year", "2011")
            page.select_option("#document-exam", "ordinaria examen 2")
            assert page.locator("#document-exam option:checked").inner_text() == "Examen 2 ordinaria"
            pills = cards.locator(".exam-pill").all_text_contents()
            assert any(label.startswith("2011 · Examen 2 ordinaria") for label in pills)
            assert all("Ordinaria examen 2" not in label for label in pills)
    context.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        for engine, options in (
            (playwright.chromium, {"viewport": {"width": 1440, "height": 1000}}),
            (playwright.chromium, {"viewport": {"width": 375, "height": 812}}),
            (playwright.webkit, playwright.devices["iPad (gen 7)"]),
        ):
            browser = engine.launch()
            check_compact_bank_header(browser, options)
            check_local_pdf_import(browser, options)
            check_pdf_source_polish(browser, options)
            check_curriculum_frequencies(browser, options)
            check_orientation_models(browser, options)
            check_docs_reproductions(browser, options)
            check_text_selection_presentation(browser, options)
            check_1812_compilation_and_2004_reproductions(browser, options)
            check_pablo_iglesias_marker(browser, options)
            check_exam_pdf_links(browser, options)
            check_historical_archive(browser, options)
            check_exam_order(browser, options)
            check(browser, options)
            browser.close()
    print("PASS: legacy recovery without visible jumps, centered reproductions, reader controls, reading cue, roles and personal-list headings")
