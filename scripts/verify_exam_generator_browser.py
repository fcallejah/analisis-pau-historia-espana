"""Verify the complete-exam generator against the local PAU banks."""
from playwright.sync_api import sync_playwright


URL = "http://localhost:8765/index.html"


def verify_exam(page, document_captions):
    paper = page.locator(".exam-paper")
    paper.wait_for(state="visible")
    instructions = paper.locator(".exam-paper-instructions")
    assert instructions.count() == 1
    assert instructions.locator("th").all_text_contents() == ["Instrucciones:"]
    assert instructions.locator("td").all_text_contents() == [
        "a) Duración: 1 hora y 30 minutos.",
        "b) Todas las cuestiones deben responderse en el papel entregado para la realización del examen y nunca en los folios que contienen los enunciados.",
        "c) Este examen está estructurado en bloques. Deberá responder a lo que se indica en cada bloque.",
        "d) La valoración de cada apartado se indica en este.",
        "e) La falta de adecuación a lo solicitado en el enunciado de las distintas preguntas, la coherencia, cohesión, corrección gramatical, léxica y ortográfica, así como su presentación de las respuestas dadas por el alumnado podrán reducir la puntuación del conjunto de los tres bloques hasta 1 punto.",
    ]
    assert instructions.evaluate(
        "node => { const style = getComputedStyle(node); const title = node.querySelector('.exam-paper-instructions-title'); const rows = [...node.querySelectorAll('tr')]; const cells = [...node.querySelectorAll('td')]; const firstCell = cells[0].getBoundingClientRect(); const heading = title.getBoundingClientRect(); return node.tagName === 'TABLE' && style.borderStyle === 'solid' && style.borderColor === 'rgb(17, 17, 17)' && style.backgroundColor === 'rgba(0, 0, 0, 0)' && style.borderCollapse === 'collapse' && style.fontWeight === '400' && title.rowSpan === 5 && getComputedStyle(title).fontWeight === '700' && getComputedStyle(title).paddingTop === '2px' && getComputedStyle(title).paddingRight === '24px' && getComputedStyle(cells[0]).paddingTop === '2px' && getComputedStyle(cells[0]).paddingLeft === '8px' && cells.every(cell => getComputedStyle(cell).fontWeight === '400' && Math.abs(cell.getBoundingClientRect().left - firstCell.left) < 1) && Math.abs(heading.top - firstCell.top) < 1 && rows.length === 5 && node.nextElementSibling.matches('.exam-block-intro'); }"
    )
    page.evaluate("() => document.fonts.ready.then(() => true)")
    assert paper.evaluate(
        "node => [...new Set([...node.querySelectorAll('*')].map(child => getComputedStyle(child).fontFamily))]"
    ) == ['"Arial Narrow", "Exam Condensed", Arial, sans-serif']
    assert paper.evaluate("node => getComputedStyle(node).boxShadow !== 'none'")
    assert paper.evaluate(
        "node => [...node.querySelectorAll('*')].every(child => { const size = getComputedStyle(child).fontSize; return size === (child.matches('.exam-paper-status') ? '10px' : child.matches('.exam-common .exam-part-title, .exam-route-title') || child.closest('.exam-paper-overline') ? '18px' : '16px'); })"
    )
    masthead = paper.locator(".exam-masthead")
    logo = masthead.get_by_role("img")
    logo.evaluate("img => img.decode()")
    center = masthead.get_by_text("CURSO 2026-2027", exact=True).bounding_box()
    assert masthead.locator("td").evaluate_all(
        "cells => cells.map(cell => [getComputedStyle(cell).borderLeftColor, getComputedStyle(cell).borderRightColor])"
    ) == [["rgb(34, 34, 34)", "rgba(0, 0, 0, 0)"], ["rgba(0, 0, 0, 0)", "rgba(0, 0, 0, 0)"], ["rgba(0, 0, 0, 0)", "rgb(34, 34, 34)"]]
    subject = masthead.get_by_role("heading", name="HISTORIA DE ESPAÑA").bounding_box()
    assert logo.bounding_box()["x"] + logo.bounding_box()["width"] <= center["x"]
    assert center["x"] + center["width"] <= subject["x"]
    assert masthead.bounding_box()["y"] + masthead.bounding_box()["height"] <= paper.locator(".exam-paper-status").bounding_box()["y"]
    assert paper.locator(".exam-paper-overline").evaluate(
        "node => getComputedStyle(node).fontSize === '18px' && getComputedStyle(node).whiteSpace === 'normal' && !node.querySelector('br') && node.textContent.replace(/\\s+/g, ' ').trim() === 'PRUEBA DE ACCESO A LA UNIVERSIDAD Y PRUEBA DE ADMISIÓN' && getComputedStyle(node).fontSize !== getComputedStyle(node.closest('.exam-masthead').querySelector('.exam-paper-course')).fontSize"
    )
    common_title = paper.locator(".exam-common-title")
    assert common_title.inner_text() == "COMÚN A AMBOS ITINERARIOS"
    block_intro = paper.locator(".exam-block-intro")
    assert block_intro.inner_text() == (
        "El examen consta de TRES BLOQUES (CUESTIONES, DOCUMENTO Y TEMA) "
        "que deberán responderse según lo indicado"
    )
    assert block_intro.evaluate(
        "node => getComputedStyle(node).textDecorationLine === 'underline' && node.nextElementSibling === node.parentElement.querySelector('.exam-common-title')"
    )
    assert common_title.evaluate(
        "node => getComputedStyle(node).fontSize === '18px' && getComputedStyle(node).letterSpacing === 'normal' && getComputedStyle(node).marginTop === '20px' && getComputedStyle(node).textAlign === 'center'"
    )
    status_box = paper.locator(".exam-paper-status").bounding_box()
    instruction_box = instructions.bounding_box()
    block_intro_box = block_intro.bounding_box()
    common_title_box = common_title.bounding_box()
    assert abs(instruction_box["y"] - status_box["y"] - status_box["height"] - 24) < 1
    assert abs(block_intro_box["y"] - instruction_box["y"] - instruction_box["height"] - 24) < 1
    assert abs(common_title_box["y"] - block_intro_box["y"] - block_intro_box["height"] - 20) < 1
    questions = paper.locator(".exam-short-question")
    assert questions.count() == 4
    assert questions.evaluate_all("nodes => nodes.map(node => Number(node.dataset.block))") == [1, 2, 3, 4]
    assert paper.locator(".exam-common .exam-part-title").inner_text() == (
        "I. CUESTIONES (hasta 3 puntos en total, de 0 a 1,5 puntos por pregunta respondida)"
    )
    assert paper.locator(".exam-common .exam-part-title").evaluate(
        "node => getComputedStyle(node).textAlign === 'center' && getComputedStyle(node).fontSize === '18px'"
    )
    assert paper.locator(".exam-common").evaluate(
        "node => { const style = getComputedStyle(node); return style.marginTop === '0px' && style.paddingTop === '0px' && getComputedStyle(node.querySelector('.exam-part-title')).marginTop === '0px'; }"
    )
    assert paper.locator(".exam-common .exam-instruction").evaluate(
        "node => getComputedStyle(node).textAlign"
    ) == "left"
    assert questions.locator("p").evaluate_all(
        "nodes => nodes.every(node => { const style = getComputedStyle(node); return style.fontWeight === '400' && style.lineHeight === '19.2px' && style.margin === '0px'; })"
    )
    assert questions.evaluate_all(
        "nodes => nodes.every(node => getComputedStyle(node, '::marker').fontWeight === '400' && getComputedStyle(node).paddingTop === '0px' && getComputedStyle(node).paddingBottom === '0px')"
    )
    common_instruction = paper.locator(".exam-common .exam-instruction")
    assert common_instruction.inner_text() == "Responda a DOS de las cuatro cuestiones planteadas:"
    assert common_instruction.locator("strong").all_text_contents() == ["DOS de las cuatro cuestiones"]
    assert paper.locator(".exam-common").evaluate(
        "node => { const style = getComputedStyle(node); return style.borderStyle === 'solid' && style.borderColor === 'rgb(17, 17, 17)'; }"
    )
    assert paper.locator(".exam-route").evaluate_all(
        "nodes => nodes.every(node => getComputedStyle(node).borderTopStyle === 'none')"
    )
    route_choice = paper.locator(".exam-route-choice")
    assert route_choice.text_content() == (
        "Elija\u00a0UNO\u00a0de los dos\u00a0ITINERARIOS y responda en ellos a lo que se le solicita "
        "en los apartados II. DOCUMENTOS y III. TEMAS:"
    )
    assert route_choice.evaluate("node => getComputedStyle(node).marginBottom === '20px'")
    assert route_choice.locator("strong").all_text_contents() == ["UNO", "ITINERARIOS"]
    assert route_choice.evaluate(
        "node => getComputedStyle(node).textDecorationLine === 'none' && getComputedStyle(node).borderStyle === 'none' && getComputedStyle(node).fontFamily === getComputedStyle(node.parentElement).fontFamily"
    )
    question_list = paper.locator(".exam-short-questions")
    assert question_list.evaluate("node => getComputedStyle(node).marginBottom === '0px'")
    assert question_list.evaluate(
        "node => getComputedStyle(node).marginLeft === '-4px' && getComputedStyle(node).paddingLeft === '12px' && [...node.children].every(item => getComputedStyle(item).paddingLeft === '0px' && getComputedStyle(item).paddingRight === '0px')"
    )
    assert paper.locator(".exam-common").evaluate(
        "node => Math.abs(node.querySelector('.exam-short-questions p').getBoundingClientRect().left - node.getBoundingClientRect().left - 21) < 1 && getComputedStyle(node.querySelector('.exam-short-questions p')).textAlign === 'left'"
    )
    assert route_choice.bounding_box()["y"] - question_list.bounding_box()["y"] - question_list.bounding_box()["height"] >= 29
    assert paper.locator(".exam-question-block, .exam-theme-unit, .exam-route-period, .exam-document-source, .exam-document-title").count() == 0
    assert paper.locator(".exam-document-prompts").count() == 0
    question_text = questions.locator("p").all_text_contents()
    assert len({text.strip() for text in question_text}) == 4

    routes = paper.locator(".exam-route")
    assert routes.count() == 2
    document_ids = []
    for route_index, route in enumerate(routes.all()):
        tables = route.locator(":scope > .exam-part-table")
        assert tables.count() == 1
        assert tables.nth(0).get_attribute("class") == "exam-part-table exam-document-part exam-theme-part"
        assert tables.locator(".exam-part-title").all_text_contents() == [
            "II. DOCUMENTO (hasta 4 puntos, de 0 a 2 puntos por pregunta respondida)",
            "III. TEMA (de 0 a 3 puntos)",
        ]
        assert tables.evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).borderTopStyle === 'solid' && getComputedStyle(node).borderTopColor === 'rgb(17, 17, 17)')"
        )
        assert tables.locator("tbody tr:not(:last-child) td").evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).borderBottomStyle === 'solid' && getComputedStyle(node).borderBottomColor === 'rgb(17, 17, 17)')"
        )
        assert tables.locator(".exam-document").evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).borderStyle === 'none')"
        )
        assert tables.locator(".exam-instruction").evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).textAlign === 'center')"
        )
        assert tables.evaluate_all(
            "nodes => nodes.every(table => [...table.querySelectorAll('.exam-part-title')].every(title => { const titleStyle = getComputedStyle(title); const instructionStyle = getComputedStyle(title.nextElementSibling); return titleStyle.fontFamily === instructionStyle.fontFamily && titleStyle.fontSize === instructionStyle.fontSize && titleStyle.fontWeight === instructionStyle.fontWeight && titleStyle.fontWeight === '700'; }))"
        )
        assert tables.evaluate_all(
            "nodes => nodes.every(table => [...table.querySelectorAll('.exam-part-title')].every(title => title.closest('td') === title.nextElementSibling.closest('td')))"
        )
        assert route.locator(":scope > .exam-route-title").count() == 1
        assert route.locator(".exam-route-title").evaluate(
            "node => getComputedStyle(node).letterSpacing === 'normal'"
        )
        if route_index == 0:
            assert route.evaluate(
                "node => getComputedStyle(node).marginTop === '0px' && getComputedStyle(node).paddingTop === '0px' && getComputedStyle(node.querySelector('.exam-route-title')).marginTop === '0px'"
            )
            assert route.locator(".exam-route-title").evaluate(
                "node => node.getBoundingClientRect().top - node.closest('.exam-paper').querySelector('.exam-route-choice').getBoundingClientRect().bottom === 20"
            )
        else:
            assert route.evaluate(
                "node => getComputedStyle(node).marginTop === '16px' && getComputedStyle(node).paddingTop === '0px'"
            )
        for heading in tables.locator(".exam-part-title").all():
            assert heading.evaluate("node => getComputedStyle(node).textAlign") == "center"
            heading_box = heading.bounding_box()
            table_box = heading.locator("xpath=ancestor::table").bounding_box()
            assert abs((heading_box["x"] + heading_box["width"] / 2) -
                       (table_box["x"] + table_box["width"] / 2)) < 1
        docs = route.locator(".exam-document")
        assert docs.count() == 2
        assert docs.evaluate_all(
            "nodes => nodes.every(node => { const style = getComputedStyle(node); return style.paddingLeft === '0px' && style.paddingRight === '0px' && style.marginLeft === '-12px' && style.marginRight === '-12px'; })"
        )
        assert tables.nth(0).locator("tbody tr").count() == 5
        assert tables.nth(0).evaluate(
            "node => { const firstCell = node.querySelector('tbody > tr:first-child td'); return getComputedStyle(node).marginTop === '0px' && getComputedStyle(firstCell).paddingTop === '0px' && getComputedStyle(firstCell.querySelector('.exam-part-title')).marginTop === '0px'; }"
        )
        assert docs.evaluate_all(
            "nodes => nodes[0].closest('tr') === nodes[1].closest('tr') && nodes[0].closest('td') !== nodes[1].closest('td') && nodes.every(node => node.closest('table') === node.closest('tr').closest('table'))"
        )
        final_instruction = tables.nth(0).locator(".exam-document-final-instruction")
        assert final_instruction.inner_text() == (
            "a) Analice el hecho histórico a que hace referencia el documento elegido.\n"
            "b) Explique el contexto histórico y las consecuencias de este acontecimiento."
        )
        assert final_instruction.evaluate(
            "node => node.closest('td').colSpan === 2 && getComputedStyle(node).textAlign === 'center' && getComputedStyle(node).fontWeight === '400' && getComputedStyle(node).lineHeight === '16px'"
        )
        assert final_instruction.evaluate(
            "node => node.closest('tr').nextElementSibling === node.closest('table').querySelectorAll('.exam-part-title')[1].closest('tr')"
        )
        assert tables.locator(".exam-document-criteria-row td").evaluate(
            "node => getComputedStyle(node).paddingTop === '0px' && getComputedStyle(node).paddingBottom === '8px'"
        )
        assert tables.locator(".exam-theme-heading-row td").evaluate(
            "node => { const heading = node.querySelector('.exam-part-title'); const instruction = node.querySelector('.exam-instruction'); return getComputedStyle(node).paddingTop === '0px' && getComputedStyle(heading).marginTop === '0px' && getComputedStyle(heading).marginBottom === '0px' && getComputedStyle(instruction).marginTop === '0px' && instruction.getBoundingClientRect().top === heading.getBoundingClientRect().bottom; }"
        )
        groups = docs.evaluate_all("nodes => nodes.map(node => node.dataset.group)")
        expected_document_group = "II" if route_index == 0 else "III"
        expected_theme_group = "III" if route_index == 0 else "II"
        assert groups == [expected_document_group, expected_document_group]
        document_ids.extend(docs.evaluate_all("nodes => nodes.map(node => node.dataset.documentId)"))
        for doc in docs.all():
            assert doc.evaluate(
                "node => { const children = [...node.children]; return children[0]?.matches('h4') && ['.exam-source-text', '.exam-image-container'].some(selector => children[1]?.matches(selector)) && getComputedStyle(children[0]).textAlign === 'left' && getComputedStyle(node.closest('td')).verticalAlign === 'top'; }"
            )
            record = document_captions[doc.get_attribute("data-document-id")]
            if doc.locator(".exam-source-text").count():
                assert doc.locator(".exam-source-text").evaluate("node => node.tagName === 'DIV'")
                assert doc.locator(".exam-source-text p").count() > 0
                assert doc.locator(".exam-source-text p").all_text_contents() == [
                    text for text in record["text"] if text.strip()
                ]
                assert doc.locator(".exam-source-text p").evaluate_all(
                    "nodes => nodes.every(node => getComputedStyle(node).margin === '0px')"
                )
                assert doc.evaluate(
                    "node => { const style = getComputedStyle(node); const card = node.getBoundingClientRect(); const cell = node.closest('td').getBoundingClientRect(); return node.classList.contains('exam-document-text') && style.marginLeft === '-12px' && style.marginRight === '-12px' && style.paddingLeft === '0px' && style.paddingRight === '0px' && node.querySelector('.exam-source-text').getBoundingClientRect().width === card.width && Math.abs(card.left - cell.left) < 1 && Math.abs(cell.right - card.right) < 1; }"
                )
                assert doc.locator(".exam-source-text").evaluate(
                    "node => { const style = getComputedStyle(node); return style.fontSize === '16px' && style.margin === '0px' && style.padding === '0px' && style.borderWidth === '0px' && style.backgroundColor === 'rgba(0, 0, 0, 0)'; }"
                )
                assert doc.locator(".exam-text-body").evaluate_all(
                    "nodes => nodes.every(node => getComputedStyle(node).textAlign === 'justify' && getComputedStyle(node).fontSize === '16px')"
                )
                assert doc.locator(".exam-text-attribution").evaluate_all(
                    "nodes => nodes.every(node => getComputedStyle(node).textAlign === 'right')"
                )
                assert doc.locator(".exam-text-heading").evaluate_all(
                    "nodes => nodes.every(node => ['left', 'center'].includes(getComputedStyle(node).textAlign))"
                )
            else:
                image = doc.locator(".exam-source-image")
                assert image.count() == 1
                assert image.evaluate("node => node.complete && node.naturalWidth > 0")
                if record["crop"]:
                    crop = record["crop"]
                    expected_aspect = (
                        record["width"] / record["height"]
                        * crop["width"] / crop["imageWidth"]
                        * crop["imageHeight"] / crop["height"]
                    )
                    frame = doc.locator(".exam-image-crop")
                    assert frame.count() == 1
                    assert abs(
                        frame.evaluate("node => Number(node.style.getPropertyValue('--exam-image-crop-aspect'))")
                        - expected_aspect
                    ) < 0.000001
                    assert image.evaluate(
                        "node => node.parentElement.classList.contains('exam-image-crop') && getComputedStyle(node).position === 'absolute' && getComputedStyle(node).objectFit === 'fill'"
                    )
                else:
                    assert doc.locator(".exam-image-crop").count() == 0
                assert image.evaluate(
                    "node => { const container = node.closest('.exam-image-container'); const media = node.parentElement.classList.contains('exam-image-crop') ? node.parentElement : node; const imageRect = media.getBoundingClientRect(); const containerRect = container.getBoundingClientRect(); const cellRect = container.closest('td').getBoundingClientRect(); return Math.abs(imageRect.left + imageRect.width / 2 - (containerRect.left + containerRect.width / 2)) < 1 && Math.abs(containerRect.left + containerRect.width / 2 - (cellRect.left + cellRect.width / 2)) < 1 && Math.abs(containerRect.left - cellRect.left) < 1 && Math.abs(cellRect.right - containerRect.right) < 1; }"
                )
                captions = doc.locator(".exam-image-caption")
                if record["examCaption"]:
                    assert captions.count() == 1
                    assert captions.inner_text() == record["examCaption"]
                    assert captions.evaluate(
                        "node => getComputedStyle(node).textAlign === 'center' && getComputedStyle(node).fontSize === '16px'"
                    )
                else:
                    assert captions.count() == 0
        themes = route.locator(".exam-theme")
        assert themes.count() == 2
        assert themes.evaluate_all("nodes => nodes.map(node => node.dataset.group)") == [expected_theme_group] * 2
        assert themes.evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).paddingBottom === '4px')"
        )
        assert tables.nth(0).locator("tbody tr:last-child td").evaluate(
            "node => getComputedStyle(node).verticalAlign === 'top' && getComputedStyle(node).paddingTop === '0px' && getComputedStyle(node).paddingBottom === '8px' && node.colSpan === 2"
        )
        assert route.locator(".exam-themes").evaluate(
            "node => getComputedStyle(node).margin === '0px'"
        )
        assert themes.locator("p").evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).fontSize === '16px' && getComputedStyle(node).lineHeight === '16px' && getComputedStyle(node).fontWeight === '400')"
        )
        assert themes.evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).lineHeight === '16px')"
        )
        assert themes.evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node, '::marker').fontWeight === '400')"
        )
        assert themes.evaluate_all(
            "nodes => nodes.every(node => getComputedStyle(node).paddingTop === '0px' && getComputedStyle(node).paddingBottom === '4px' && getComputedStyle(node.querySelector('p')).margin === '0px')"
        )
        assert all(text.strip().endswith(".") for text in themes.locator("p").all_text_contents())
    assert len(set(document_ids)) == 4
    button = page.get_by_role("button", name="Generar otro simulacro")
    assert button.is_enabled()
    assert page.locator("#exam-generate .exam-generate-icon").is_visible()
    save_top = page.locator("#exam-save-top")
    save_bottom = page.locator("#exam-save-bottom")
    assert save_top.is_visible() and save_top.is_enabled()
    assert save_bottom.is_visible() and save_bottom.is_enabled()
    assert save_top.evaluate(
        "node => node.parentElement.classList.contains('exam-generator-action-row') && node.previousElementSibling.id === 'exam-generate'"
    )
    generate_box = button.bounding_box()
    save_top_box = save_top.bounding_box()
    action_row_box = page.locator(".exam-generator-action-row").bounding_box()
    assert abs(generate_box["y"] - save_top_box["y"]) < 1
    assert save_top_box["x"] > generate_box["x"] + generate_box["width"]
    assert abs(action_row_box["x"] + action_row_box["width"] - save_top_box["x"] - save_top_box["width"]) < 1
    assert save_bottom.evaluate(
        "node => node.parentElement.id === 'exam-save-footer' && node.parentElement.previousElementSibling.id === 'exam-preview'"
    )
    paper_box = paper.bounding_box()
    save_bottom_box = save_bottom.bounding_box()
    assert save_bottom_box["y"] > paper_box["y"] + paper_box["height"]
    assert page.locator("#exam-preview").evaluate("node => node.scrollWidth <= node.clientWidth")


def exam_snapshot(page):
    return page.locator(".exam-paper").evaluate("""node => ({
      questions: [...node.querySelectorAll('.exam-short-question p')].map(item => item.textContent),
      documents: [...node.querySelectorAll('.exam-document')].map(item => item.dataset.documentId),
      themes: [...node.querySelectorAll('.exam-theme p')].map(item => item.textContent),
    })""")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1365, "height": 900}, service_workers="block")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL, wait_until="domcontentloaded")
    page.get_by_role("button", name="Preparar simulacro").wait_for(state="visible")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    assert page.locator("#exam-save-top").is_hidden()
    assert page.locator("#exam-save-footer").is_hidden()
    warning = page.locator(".exam-generator .alert-warn p").inner_text()
    assert warning == (
        "La selección es aleatoria y no predice el examen. "
        "La estructura sigue como referencia las orientaciones 2026–27."
    )
    document_captions = page.evaluate("""async () => {
      const data = await fetch("data/documentos.json").then(response => response.json());
      return Object.fromEntries(data.documents.map(record => [record.id, {
        type: record.type,
        examCaption: record.image?.examCaption?.text || record.examCaption?.text || "",
        crop: record.image?.crop || null,
        width: record.image?.width || 0,
        height: record.image?.height || 0,
        text: record.text || [],
      }]));
    }""")
    assert page.locator(".exam-generator-nav").get_attribute("href") == "#generador-examen"
    assert page.locator(".saved-nav-stack a").all_text_contents() == ["Mis preguntas cortas", "Mis documentos"]
    page.locator("#exam-generate").click()
    verify_exam(page, document_captions)
    desktop_overline_lines = page.locator(".exam-paper-overline").evaluate(
        "node => { const range = document.createRange(); range.selectNodeContents(node); return range.getClientRects().length; }"
    )
    original_exam = exam_snapshot(page)

    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    page.locator(".exam-paper").wait_for(state="visible")
    verify_exam(page, document_captions)
    assert exam_snapshot(page) == original_exam

    page.get_by_role("button", name="Generar otro simulacro").click()
    dialog = page.locator("#exam-confirm-dialog")
    dialog.wait_for(state="visible")
    dialog.get_by_role("button", name="Cancelar").click()
    dialog.wait_for(state="hidden")
    assert exam_snapshot(page) == original_exam

    for _ in range(5):
        page.get_by_role("button", name="Generar otro simulacro").click()
        dialog.wait_for(state="visible")
        dialog.get_by_role("button", name="Sí, generar otro").click()
        dialog.wait_for(state="hidden")
        verify_exam(page, document_captions)
    assert not errors, errors

    saved_exam = page.evaluate("() => JSON.parse(localStorage.getItem('pau-he-generated-exam-v1'))")
    saved_exam["routes"][0]["documentIds"] = ["general-valeriano-weyler", "goya-tres-de-mayo"]
    page.evaluate(
        "saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))",
        saved_exam,
    )
    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    verify_exam(page, document_captions)
    assert page.locator('[data-document-id="general-valeriano-weyler"] .exam-image-crop').count() == 1

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, service_workers="block")
    mobile.goto(URL, wait_until="domcontentloaded")
    mobile.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    mobile.locator("#exam-generate").click()
    verify_exam(mobile, document_captions)
    mobile_overline_lines = mobile.locator(".exam-paper-overline").evaluate(
        "node => { const range = document.createRange(); range.selectNodeContents(node); return range.getClientRects().length; }"
    )
    assert mobile_overline_lines > desktop_overline_lines
    assert mobile.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    page.evaluate("() => { window.__printCalls = 0; window.print = () => { window.__printCalls += 1; }; }")
    page.locator("#exam-save-top").click()
    page.locator("#exam-save-bottom").click()
    assert page.evaluate("window.__printCalls === 2")
    page.emulate_media(media="print")
    assert page.locator(".exam-paper").evaluate(
        "node => getComputedStyle(node).boxShadow === 'none' && getComputedStyle(node).maxWidth === 'none'"
    )
    assert page.locator("#exam-save-footer").evaluate("node => getComputedStyle(node).display === 'none'")
    assert page.locator(".site-header").evaluate("node => getComputedStyle(node).display === 'none'")
    page.emulate_media(media="screen")
    browser.close()

print("OK: cuatro cuestiones, dos itinerarios cruzados y vista adaptable.")
