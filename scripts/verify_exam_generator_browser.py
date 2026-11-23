"""Verify the complete-exam generator against the local PAU banks."""
from io import BytesIO

from playwright.sync_api import sync_playwright
from pypdf import PdfReader


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
    assert masthead.locator("td").nth(1).evaluate(
        "node => { const cell = node.getBoundingClientRect(); const text = node.querySelector('.exam-paper-course').getBoundingClientRect(); return Math.abs((cell.left + cell.right) / 2 - (text.left + text.right) / 2 - 4) < 1; }"
    )
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
    assert paper.evaluate("""node => {
      const rect = selector => node.querySelector(selector).getBoundingClientRect();
      const status = rect('.exam-paper-status');
      const instructions = rect('.exam-paper-instructions');
      const intro = rect('.exam-block-intro');
      const title = rect('.exam-common-title');
      return Math.abs(instructions.top - status.bottom - 24) < 1
        && Math.abs(intro.top - instructions.bottom - 24) < 1
        && Math.abs(title.top - intro.bottom - 20) < 1;
    }""")
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
        "node => getComputedStyle(node).marginLeft === '0px' && getComputedStyle(node).paddingLeft === '12px' && [...node.children].every(item => getComputedStyle(item).paddingLeft === '0px' && getComputedStyle(item).paddingRight === '0px')"
    )
    assert paper.locator(".exam-common").evaluate(
        "node => Math.abs(node.querySelector('.exam-short-questions p').getBoundingClientRect().left - node.getBoundingClientRect().left - 25) < 1 && getComputedStyle(node.querySelector('.exam-short-questions p')).textAlign === 'left'"
    )
    assert paper.evaluate("""node => {
      const questions = node.querySelector('.exam-short-questions').getBoundingClientRect();
      const choice = node.querySelector('.exam-route-choice').getBoundingClientRect();
      return choice.top - questions.bottom >= 29;
    }""")
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
            "nodes => nodes.every(node => { const style = getComputedStyle(node); const cell = node.closest('td'); return style.paddingLeft === '0px' && style.paddingRight === '0px' && style.marginLeft === '-6px' && style.marginRight === '-6px' && style.marginTop === '0px' && getComputedStyle(cell).paddingTop === '0px' && Math.abs(node.getBoundingClientRect().top - cell.getBoundingClientRect().top) < 1; })"
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
                "node => { const children = [...node.children]; return children[0]?.matches('h4') && ['.exam-source-text', '.exam-image-container', '.exam-image-pair'].some(selector => children[1]?.matches(selector)) && getComputedStyle(children[0]).textAlign === 'left' && getComputedStyle(node.closest('td')).verticalAlign === 'top'; }"
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
                    "node => { const style = getComputedStyle(node); const card = node.getBoundingClientRect(); const cell = node.closest('td').getBoundingClientRect(); return node.classList.contains('exam-document-text') && style.marginLeft === '-6px' && style.marginRight === '-6px' && style.paddingLeft === '0px' && style.paddingRight === '0px' && node.querySelector('.exam-source-text').getBoundingClientRect().width === card.width && Math.abs(card.left - cell.left - 6) < 1 && Math.abs(cell.right - card.right - 6) < 1; }"
                )
                assert doc.locator(".exam-source-text").evaluate(
                    "node => { const style = getComputedStyle(node); return style.fontSize === '16px' && style.margin === '0px' && style.padding === '0px' && style.borderWidth === '0px' && style.backgroundColor === 'rgba(0, 0, 0, 0)'; }"
                )
                assert doc.locator(".exam-text-body").evaluate_all(
                    "nodes => nodes.every(node => getComputedStyle(node).textAlign === (node.parentElement.classList.contains('exam-verse-pair') ? 'center' : 'justify') && getComputedStyle(node).fontSize === '16px')"
                )
                assert doc.locator(".exam-text-attribution").evaluate_all(
                    "nodes => nodes.every(node => getComputedStyle(node).textAlign === 'right')"
                )
                assert doc.locator(".exam-text-heading").evaluate_all(
                    "nodes => nodes.every(node => ['left', 'center'].includes(getComputedStyle(node).textAlign))"
                )
            else:
                if record["imageLayout"] == "pair":
                    assert doc.locator(".exam-image-pair .exam-source-image").count() == len(record["images"])
                    assert doc.locator(".exam-image-pair .exam-source-image").evaluate_all(
                        "nodes => nodes.every(node => node.complete && node.naturalWidth > 0)"
                    )
                    continue
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
                        "node => { const rect = node.getBoundingClientRect(); return Math.abs(rect.width / rect.height - node.naturalWidth / node.naturalHeight) < 0.01; }"
                    )
                assert image.evaluate(
                    "node => { const container = node.closest('.exam-image-container'); const media = node.parentElement.classList.contains('exam-image-crop') ? node.parentElement : node; const imageRect = media.getBoundingClientRect(); const containerRect = container.getBoundingClientRect(); const headingRect = container.previousElementSibling.getBoundingClientRect(); const cellRect = container.closest('td').getBoundingClientRect(); return Math.abs(imageRect.top - containerRect.top) < 1 && Math.abs(containerRect.top - headingRect.bottom - 10) < 1 && Math.abs(imageRect.left + imageRect.width / 2 - (containerRect.left + containerRect.width / 2)) < 1 && Math.abs(containerRect.left + containerRect.width / 2 - (cellRect.left + cellRect.width / 2)) < 1 && Math.abs(containerRect.left - cellRect.left - 6) < 1 && Math.abs(cellRect.right - containerRect.right - 6) < 1; }"
                )
                captions = doc.locator(".exam-image-caption")
                if record["examCaption"]:
                    assert captions.count() == 1
                    assert captions.inner_text() == record["examCaption"].replace("*", "")
                    assert "*" not in captions.inner_text()
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
    button = page.locator("#exam-generate")
    bottom_button = page.locator("#exam-generate-bottom")
    assert button.is_enabled()
    assert bottom_button.is_visible() and bottom_button.is_enabled()
    assert bottom_button.inner_text() == button.inner_text() == "Generar otro simulacro"
    assert bottom_button.locator(".exam-generate-icon").is_visible()
    assert page.locator("#exam-generate .exam-generate-icon").is_visible()
    save_top = page.locator("#exam-save-top")
    save_bottom = page.locator("#exam-save-bottom")
    assert save_top.is_visible() and save_top.is_enabled()
    assert save_bottom.is_visible() and save_bottom.is_enabled()
    assert save_top.inner_text() == save_bottom.inner_text() == "Guardar como PDF"
    assert save_top.locator(".exam-save-icon").is_visible() and save_bottom.locator(".exam-save-icon").is_visible()
    assert save_top.evaluate("node => getComputedStyle(node).backgroundColor") == "rgb(75, 46, 131)"
    assert save_bottom.evaluate("node => getComputedStyle(node).backgroundColor") == "rgb(75, 46, 131)"
    assert save_top.evaluate(
        "node => node.parentElement.classList.contains('exam-generator-action-row') && node.previousElementSibling.id === 'exam-generate'"
    )
    generate_box = button.bounding_box()
    save_top_box = save_top.bounding_box()
    assert abs(generate_box["y"] - save_top_box["y"]) < 1
    assert save_top_box["x"] > generate_box["x"] + generate_box["width"]
    assert 0 < save_top_box["x"] - generate_box["x"] - generate_box["width"] <= 12
    assert save_bottom.evaluate(
        "node => node.previousElementSibling.id === 'exam-generate-bottom' && node.parentElement.id === 'exam-save-footer' && node.parentElement.previousElementSibling.id === 'exam-preview'"
    )
    bottom_generate_box = bottom_button.bounding_box()
    bottom_save_box = save_bottom.bounding_box()
    assert abs(bottom_generate_box["y"] - bottom_save_box["y"]) < 1
    assert 0 < bottom_save_box["x"] - bottom_generate_box["x"] - bottom_generate_box["width"] <= 12
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


def verify_text_image_alignment(page):
    assert page.locator(".exam-route").first.evaluate("""route => {
      const paragraph = route.querySelector('.exam-source-text p');
      const image = route.querySelector('.exam-image-container');
      const marker = document.createElement('span');
      marker.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
      paragraph.prepend(marker);
      const baseline = marker.getBoundingClientRect().top;
      marker.remove();
      const style = getComputedStyle(paragraph);
      const canvas = document.createElement('canvas').getContext('2d');
      canvas.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
      const ascent = canvas.measureText(paragraph.textContent.slice(0, 12)).actualBoundingBoxAscent;
      return Math.abs(image.getBoundingClientRect().top - (baseline - ascent)) < 2;
    }""")


def verify_print_image_sizing(browser, pdf=False):
    page = browser.new_page(viewport={"width": 1365, "height": 900}, service_workers="block")
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    page.locator("#exam-generate").click()
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('pau-he-generated-exam-v1'))")
    saved["questions"] = page.evaluate("""() => [1, 2, 3, 4].map(block => ({
      block,
      prompt: window.pauPracticeBank.filter(entry => entry[2] === block && entry[0].trim())
        .map(entry => entry[0]).sort((a, b) => a.length - b.length)[0]
    }))""")
    saved["routes"][0]["documentIds"] = ["caricatura-se-colocan-reyes-1869", "fernando-vii-vicente-lopez"]
    saved["routes"][1]["documentIds"] = ["maximo-febrero-1976", "constitucion-1931-articulos-suplente-a"]

    def restore():
        page.evaluate("saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))", saved)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
        page.evaluate("""async () => {
          await document.fonts.ready;
          await Promise.all([...document.querySelectorAll('.exam-paper img')].map(image => image.decode()));
        }""")

    def image_sizes():
        return page.locator(".exam-route").first.locator(".exam-document").evaluate_all("""cards =>
          cards.map(card => {
            const rect = card.querySelector('.exam-image-crop, .exam-source-image').getBoundingClientRect();
            return [rect.width, rect.height];
          })
        """)

    restore()
    assert page.locator(".exam-route").nth(1).locator(".exam-print-matched-image").count() == 0
    screen_sizes = image_sizes()
    assert screen_sizes[1][1] > screen_sizes[0][1] * 1.5
    page.emulate_media(media="print")
    matched = image_sizes()
    assert abs(matched[0][1] - matched[1][1]) < 1
    assert abs(matched[1][0] / matched[1][1] - 1415 / 1920) < .01
    if pdf:
        reader = PdfReader(BytesIO(page.pdf(prefer_css_page_size=True)))
        pages = [p for p in reader.pages if "Subasta de reyes" in p.extract_text()
                 and "Fernando VII, «el Deseado»" in p.extract_text()]
        assert len(pages) == 1
        image_calls = []
        pages[0].extract_text(visitor_operand_before=lambda op, args, cm, tm: image_calls.append(args[0]) if op == b"Do" else None)
        assert len(image_calls) >= 2
    page.emulate_media(media="screen")
    assert image_sizes() == screen_sizes
    page.set_viewport_size({"width": 390, "height": 844})
    mobile_sizes = image_sizes()
    page.locator(".exam-route").first.locator(".exam-document-row").evaluate("node => node.scrollLeft = node.scrollWidth")
    page.emulate_media(media="print")
    mobile_print = image_sizes()
    assert abs(mobile_print[0][1] - mobile_print[1][1]) < 1
    page.emulate_media(media="screen")
    assert image_sizes() == mobile_sizes
    page.set_viewport_size({"width": 1365, "height": 900})

    saved["routes"][0]["documentIds"] = ["duelo-a-garrotazos-goya", "portada-constitucion-1812"]
    page.set_viewport_size({"width": 794, "height": 900})
    restore()
    page.emulate_media(media="print")
    cards = page.locator(".exam-route").first.locator(".exam-document")
    matched = image_sizes()
    cards.evaluate_all("nodes => nodes.forEach(node => node.classList.remove('exam-print-matched-image'))")
    original = image_sizes()
    assert matched[1][1] >= 120 - 1 and matched[1][1] >= original[1][1] * .45 - 1
    assert abs(matched[1][1] - original[1][1] * .45) < 1
    assert matched[1][1] < original[1][1] and matched[0][1] <= original[0][1] + 1
    page.emulate_media(media="screen")

    saved["routes"][0]["documentIds"] = ["mural-constitucion-1812-cadiz", "portada-constitucion-1812"]
    restore()
    page.emulate_media(media="print")
    sizes = image_sizes()
    assert abs(sizes[0][1] - sizes[1][1]) < 2 or sizes[1][1] >= 120 - 1
    assert page.locator('[data-document-id="mural-constitucion-1812-cadiz"] .exam-image-crop').count() == 1
    page.close()


def verify_paired_sources(browser, pdf=False):
    page = browser.new_page(viewport={"width": 1365, "height": 900}, service_workers="block")
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    page.locator("#exam-generate").click()
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('pau-he-generated-exam-v1'))")
    saved["routes"][0]["documentIds"] = ["espartero-narvaez-retratos-2016", "goya-tres-de-mayo"]
    saved["routes"][1]["documentIds"] = ["canciones-guerra-civil", "fotografias-guerra-civil-entrega-fusiles-y-burgos-1936"]

    def restore():
        page.evaluate("saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))", saved)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
        page.evaluate("""async () => {
          await document.fonts.ready;
          await Promise.all([...document.querySelectorAll('.exam-paper img')].map(image => image.decode()));
        }""")

    def check_pair(document_id):
        pair = page.locator(f'[data-document-id="{document_id}"] .exam-image-pair')
        assert pair.locator(".exam-image-item").count() == 2
        assert pair.locator("img").evaluate_all("images => images.every(image => image.complete && image.naturalWidth > 0)")
        assert pair.locator(".exam-image-item").evaluate_all("""items => {
          const a = items[0].getBoundingClientRect(), b = items[1].getBoundingClientRect();
          return Math.abs(a.top - b.top) < 1 && a.right <= b.left + 1;
        }""")
        return pair

    restore()
    songs = page.locator('[data-document-id="canciones-guerra-civil"] .exam-verse-pair')
    assert songs.locator("p").count() == 2
    assert songs.locator("p").evaluate_all("""nodes => {
      const a = nodes[0].getBoundingClientRect(), b = nodes[1].getBoundingClientRect();
      return Math.abs(a.top - b.top) < 1 && a.right <= b.left;
    }""")
    check_pair("espartero-narvaez-retratos-2016")
    photos = check_pair("fotografias-guerra-civil-entrega-fusiles-y-burgos-1936")
    assert photos.locator(".exam-image-caption").count() == 2
    assert page.locator('[data-document-id="goya-tres-de-mayo"] .exam-source-image').count() == 1

    page.set_viewport_size({"width": 390, "height": 844})
    assert songs.locator("p").evaluate_all("""nodes => {
      const a = nodes[0].getBoundingClientRect(), b = nodes[1].getBoundingClientRect();
      return b.top - a.bottom >= 24 && Math.abs(a.left - b.left) < 1;
    }""")
    check_pair("espartero-narvaez-retratos-2016")
    check_pair("fotografias-guerra-civil-entrega-fusiles-y-burgos-1936")
    page.locator(".exam-document-row").evaluate_all("rows => rows.forEach(row => row.scrollLeft = row.scrollWidth)")
    page.emulate_media(media="print")
    assert songs.locator("p").evaluate_all("""nodes => {
      const a = nodes[0].getBoundingClientRect(), b = nodes[1].getBoundingClientRect();
      return Math.abs(a.top - b.top) < 1 && a.right <= b.left;
    }""")
    check_pair("fotografias-guerra-civil-entrega-fusiles-y-burgos-1936")
    if pdf:
        assert page.pdf(prefer_css_page_size=True).startswith(b"%PDF-")
    page.emulate_media(media="screen")

    saved["routes"][1]["documentIds"][0] = "carteles-guerra-civil-2016"
    restore()
    check_pair("carteles-guerra-civil-2016")
    assert page.locator('[data-document-id="carteles-guerra-civil-2016"] > .exam-image-caption').count() == 1
    page.close()


def verify_mobile_document_scroll(browser, touch_protocol=False):
    page = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True,
                            service_workers="block", reduced_motion="reduce")
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    page.locator("#exam-generate").click()
    rows = page.locator(".exam-document-row")
    assert rows.count() == 2
    centered = """nodes => nodes.every(node => {
      const divider = node.cells[1].getBoundingClientRect().left;
      const viewport = node.getBoundingClientRect();
      return Math.abs(divider - (viewport.left + viewport.width / 2)) < 2;
    })"""
    assert rows.evaluate_all(centered)
    for width in (320, 390, 620):
        page.set_viewport_size({"width": width, "height": 844})
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
        assert rows.count() == 2 and rows.evaluate_all(centered)
    page.set_viewport_size({"width": 621, "height": 844})
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_function("""() => [...document.querySelectorAll('.exam-document-row')].every(node =>
      Math.abs(node.cells[1].getBoundingClientRect().left -
        (node.getBoundingClientRect().left + node.getBoundingClientRect().width / 2)) < 2)
    """)
    page.locator("#exam-generate").click()
    page.locator("#exam-confirm-dialog").get_by_role("button", name="Sí, generar otro").click()
    assert rows.evaluate_all(centered)
    page.evaluate("""async () => {
      await document.fonts.ready;
      await Promise.all([...document.querySelectorAll('.exam-paper img')].map(image => image.decode()));
    }""")
    page.emulate_media(media="print")
    print_geometry = rows.evaluate_all("""nodes => nodes.map(node =>
      [...node.cells].map(cell => {
        const rect = cell.getBoundingClientRect();
        return [rect.x, rect.y, rect.width, rect.height, cell.innerText];
      })
    )""")
    page.emulate_media(media="screen")
    for width in (320, 390, 620):
        page.set_viewport_size({"width": width, "height": 844})
        for row in rows.all():
            assert row.evaluate("""node => {
              const cells = [...node.cells];
              return getComputedStyle(node).overflowX === 'auto' &&
                cells.length === 2 && cells.every(cell => cell.clientWidth >= node.clientWidth * 0.84) &&
                node.scrollWidth > node.clientWidth * 1.6 &&
                getComputedStyle(cells[0].querySelector('h4')).fontSize === '16px';
            }""")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.set_viewport_size({"width": 621, "height": 844})
    assert rows.evaluate_all("nodes => nodes.every(node => getComputedStyle(node).display === 'table-row' && node.scrollWidth === node.clientWidth)")
    page.set_viewport_size({"width": 390, "height": 844})

    for row in rows.all():
        row.evaluate("node => window.scrollTo(0, node.getBoundingClientRect().top + scrollY - 120)")
        page.wait_for_timeout(500)
        box = row.bounding_box()
        if touch_protocol:
            session = page.context.new_cdp_session(page)
            for direction in (1, -1):
                row.evaluate("node => node.scrollLeft = (node.scrollWidth - node.clientWidth) / 2")
                page.wait_for_timeout(200)
                start = row.evaluate("node => node.scrollLeft")
                x, y = box["x"] + box["width"] * (0.25 if direction == 1 else 0.75), box["y"] + 50
                assert row.evaluate("(node, point) => node.contains(document.elementFromPoint(point.x, point.y))", {"x": x, "y": y})
                session.send("Input.synthesizeScrollGesture", {
                    "x": x, "y": y, "xDistance": direction * 150, "yDistance": 0,
                    "speed": 400, "gestureSourceType": "touch",
                })
                page.wait_for_timeout(500)
                end = row.evaluate("node => node.scrollLeft")
                assert direction * (start - end) > 10, (direction, start, end, box, row.get_attribute("aria-label"))
            session.detach()
            row.evaluate("node => node.scrollLeft = (node.scrollWidth - node.clientWidth) / 2")
            page.wait_for_timeout(200)
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + 50)
        page.mouse.wheel(300, 0)
        page.wait_for_function("(node) => node.scrollLeft >= node.scrollWidth - node.clientWidth - 1", arg=row.element_handle())
        assert row.evaluate("""node => {
          const last = node.cells[1].getBoundingClientRect();
          const viewport = node.getBoundingClientRect();
          return last.left >= viewport.left - 1 && last.right <= viewport.right + 1;
        }""")
        row.focus()
        for _ in range(8):
            page.keyboard.press("ArrowLeft")
            page.wait_for_timeout(80)
        page.wait_for_function("(node) => node.scrollLeft <= 1", arg=row.element_handle())

        if touch_protocol:
            session = page.context.new_cdp_session(page)
            x, y = box["x"] + box["width"] * 0.8, box["y"] + 50
            session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
            for distance in (20, 50, 100, 150, 200):
                session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x - distance, "y": y}]})
                page.wait_for_timeout(30)
            session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            page.wait_for_function("(node) => node.scrollLeft > 10", arg=row.element_handle())
            session.detach()
        else:
            row.evaluate("node => node.scrollLeft = node.scrollWidth")

    if touch_protocol:
        page.wait_for_timeout(800)
        row = rows.first
        row.evaluate("node => window.scrollTo(0, node.getBoundingClientRect().top + scrollY + 10)")
        box = row.bounding_box()
        x, y = box["x"] + box["width"] / 2, min(300, box["y"] + box["height"] - 20)
        assert row.evaluate("(node, point) => node.contains(document.elementFromPoint(point.x, point.y))", {"x": x, "y": y})
        before = page.evaluate("scrollY")
        left = row.evaluate("node => node.scrollLeft")
        session = page.context.new_cdp_session(page)
        session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        for distance in (20, 50, 100):
            session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y - distance}]})
            page.wait_for_timeout(30)
        session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_function("before => scrollY > before + 10", arg=before)
        assert abs(row.evaluate("node => node.scrollLeft") - left) < 2
        session.detach()

    page.emulate_media(media="print")
    assert rows.evaluate_all("""nodes => nodes.map(node =>
      [...node.cells].map(cell => {
        const rect = cell.getBoundingClientRect();
        return [rect.x, rect.y, rect.width, rect.height, cell.innerText];
      })
    )""") == print_geometry
    assert rows.evaluate_all("""nodes => nodes.every(node => {
      const cells = [...node.cells];
      const table = node.closest('table');
      const left = cells[0].getBoundingClientRect(), right = cells[1].getBoundingClientRect();
      return getComputedStyle(table).display === 'table' &&
        getComputedStyle(node).display === 'table-row' &&
        getComputedStyle(node).overflowX === 'visible' &&
        Math.abs(left.right - right.left) < 1 &&
        Math.abs(left.width - right.width) < 1 &&
        Math.abs(left.width + right.width - table.getBoundingClientRect().width) < 2;
    })""")
    if touch_protocol:
        assert page.pdf(prefer_css_page_size=True).startswith(b"%PDF-")
    page.close()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1365, "height": 900}, service_workers="block", reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL, wait_until="domcontentloaded")
    page.get_by_role("button", name="Preparar simulacro").wait_for(state="visible")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    generator = page.locator("#generador-examen")
    assert "rgb(232, 242, 208)" in generator.evaluate("node => getComputedStyle(node).backgroundImage")
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    assert "rgb(40, 50, 34)" in generator.evaluate("node => getComputedStyle(node).backgroundImage")
    page.evaluate("delete document.documentElement.dataset.theme")
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
        imageLayout: record.imageLayout || "",
        images: [record.image, ...(record.image?.additionalImages || [])].filter(Boolean).map(image => image.src),
        examCaption: record.image?.examCaption?.text || record.examCaption?.text || "",
        crop: record.image?.crop || null,
        width: record.image?.width || 0,
        height: record.image?.height || 0,
        text: record.text || [],
      }]));
    }""")
    assert page.locator(".exam-generator-nav").get_attribute("href") == "#generador-examen"
    assert page.locator(".saved-nav-stack a").all_text_contents() == ["Mis preguntas cortas", "Mis documentos"]
    assert page.locator(".exam-generator-nav").bounding_box()["x"] < page.locator(".saved-nav-stack").bounding_box()["x"]
    for theme in ("light", "dark"):
        page.evaluate("theme => theme === 'dark' ? document.documentElement.dataset.theme = 'dark' : delete document.documentElement.dataset.theme", theme)
        primary = page.locator(".exam-generator-nav").evaluate("node => getComputedStyle(node).backgroundColor")
        secondary = page.locator(".saved-nav-stack a").first.evaluate("node => getComputedStyle(node).backgroundColor")
        assert primary == "rgb(214, 238, 122)"
        assert secondary == ("rgb(249, 248, 244)" if theme == "light" else "rgb(41, 45, 47)")
    page.evaluate("delete document.documentElement.dataset.theme")
    page.locator("#exam-generate").click()
    verify_exam(page, document_captions)
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    assert page.locator(".exam-paper").evaluate("""node =>
      [node, ...node.querySelectorAll('.exam-masthead, .exam-common, .exam-part-table')]
        .every(element => getComputedStyle(element).backgroundColor === 'rgb(255, 255, 255)')
    """)
    page.evaluate("delete document.documentElement.dataset.theme")
    desktop_overline_lines = page.locator(".exam-paper-overline").evaluate(
        "node => { const range = document.createRange(); range.selectNodeContents(node); return range.getClientRects().length; }"
    )
    original_exam = exam_snapshot(page)

    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    page.locator(".exam-paper").wait_for(state="visible")
    verify_exam(page, document_captions)
    assert exam_snapshot(page) == original_exam

    page.locator("#exam-generate-bottom").click()
    dialog = page.locator("#exam-confirm-dialog")
    dialog.wait_for(state="visible")
    dialog.get_by_role("button", name="Cancelar").click()
    dialog.wait_for(state="hidden")
    assert exam_snapshot(page) == original_exam

    for index in range(5):
        page.locator("#exam-generate-bottom" if index == 0 else "#exam-generate").click()
        dialog.wait_for(state="visible")
        dialog.get_by_role("button", name="Sí, generar otro").click()
        dialog.wait_for(state="hidden")
        verify_exam(page, document_captions)
        if index == 0:
            assert exam_snapshot(page) != original_exam
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

    saved_exam["routes"][0]["documentIds"] = ["goya-tres-de-mayo", "portada-constitucion-1812"]
    page.evaluate(
        "saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))",
        saved_exam,
    )
    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    verify_exam(page, document_captions)
    assert page.locator('[data-document-id="portada-constitucion-1812"] .exam-source-image').count() == 1

    saved_exam["routes"][0]["documentIds"] = ["bando-de-murat-tras-el-levantamiento-del-2-de-mayo", "goya-tres-de-mayo"]
    page.evaluate(
        "saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))",
        saved_exam,
    )
    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    verify_exam(page, document_captions)
    verify_text_image_alignment(page)

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, service_workers="block", reduced_motion="reduce")
    mobile.goto(URL, wait_until="domcontentloaded")
    mobile.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    for width in (320, 375, 401, 430, 620):
        mobile.set_viewport_size({"width": width, "height": 844})
        brand = mobile.locator(".site-header > .brand").bounding_box()
        saved = mobile.locator(".saved-nav-stack").bounding_box()
        contact = mobile.locator(".site-header .contact-tool").bounding_box()
        exam = mobile.locator(".exam-generator-nav").bounding_box()
        assert brand["x"] + brand["width"] <= saved["x"]
        assert mobile.locator(".site-header .brand-text").evaluate(
            "node => node.getBoundingClientRect().height <= parseFloat(getComputedStyle(node).lineHeight) * 3 + 1"
        )
        assert exam["y"] >= saved["y"] + saved["height"]
        assert abs(exam["x"] - saved["x"]) < 1
        assert abs(exam["x"] + exam["width"] - contact["x"] - contact["width"]) < 1
        top = min(saved["y"], contact["y"])
        bottom = exam["y"] + exam["height"]
        assert abs(brand["y"] + brand["height"] / 2 - (top + bottom) / 2) < 1
        if width <= 430:
            for item, icon in zip(
                mobile.locator(".saved-nav-stack a").all(),
                (mobile.locator('.header-tool[href="https://dle.rae.es"]'), mobile.locator('.header-tool[href="https://x.com/RAEinforma"]')),
            ):
                saved_box, icon_box = item.bounding_box(), icon.bounding_box()
                assert abs(saved_box["y"] - icon_box["y"]) < 1
                assert abs(saved_box["height"] - icon_box["height"]) < 1
        assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth")
        x_icon = mobile.locator(".site-header .x-logo").bounding_box()
        moon = mobile.locator(".site-header .icon-moon").bounding_box()
        assert (x_icon["width"], x_icon["height"]) == (moon["width"], moon["height"])
    mobile.set_viewport_size({"width": 390, "height": 844})
    mobile.locator("#exam-generate").click()
    verify_exam(mobile, document_captions)
    mobile_overline_lines = mobile.locator(".exam-paper-overline").evaluate(
        "node => { const range = document.createRange(); range.selectNodeContents(node); return range.getClientRects().length; }"
    )
    assert mobile_overline_lines > desktop_overline_lines
    assert mobile.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    mobile.evaluate(
        "saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))",
        saved_exam,
    )
    mobile.reload(wait_until="domcontentloaded")
    mobile.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    verify_exam(mobile, document_captions)
    verify_text_image_alignment(mobile)
    saved_exam["routes"][1]["documentIds"] = ["maximo-febrero-1976", "franco-hitler-hendaya-1940"]
    page.evaluate(
        "saved => localStorage.setItem('pau-he-generated-exam-v1', JSON.stringify(saved))",
        saved_exam,
    )
    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#exam-generate').disabled")
    verify_exam(page, document_captions)
    assert page.locator('[data-document-id="maximo-febrero-1976"] .exam-image-caption').inner_text() == (
        "Chiste de Máximo aparecido en El País, febrero de 1976"
    )
    page.evaluate("() => { window.__printCalls = 0; window.print = () => { window.__printCalls += 1; }; }")
    page.locator("#exam-save-top").click()
    page.locator("#exam-save-bottom").click()
    assert page.evaluate("window.__printCalls === 2")
    page.locator(".exam-paper").evaluate(
        "node => { window.__examScreenFonts = [...node.querySelectorAll('*')].map(child => getComputedStyle(child).fontSize); }"
    )
    page.emulate_media(media="print")
    assert page.locator(".exam-paper").evaluate(
        "node => getComputedStyle(node).boxShadow === 'none' && getComputedStyle(node).maxWidth === 'none'"
    )
    assert page.locator(".exam-paper").evaluate("""node =>
      [...node.querySelectorAll('*')].every((child, index) => {
        const screenSize = parseFloat(window.__examScreenFonts[index]);
        const expected = screenSize === 10 ? 12 : screenSize * 0.75;
        return Math.abs(parseFloat(getComputedStyle(child).fontSize) - expected) < 0.01;
      })
    """)
    assert page.locator("#exam-save-footer").evaluate("node => getComputedStyle(node).display === 'none'")
    assert page.locator(".site-header").evaluate("node => getComputedStyle(node).display === 'none'")
    assert generator.evaluate("node => getComputedStyle(node).backgroundImage === 'none'")
    assert page.pdf(prefer_css_page_size=True).startswith(b"%PDF-")
    page.emulate_media(media="screen")
    verify_print_image_sizing(browser, pdf=True)
    verify_paired_sources(browser, pdf=True)
    verify_mobile_document_scroll(browser, touch_protocol=True)
    browser.close()
    browser = playwright.webkit.launch()
    verify_print_image_sizing(browser)
    verify_paired_sources(browser)
    verify_mobile_document_scroll(browser)
    browser.close()

print("OK: cuatro cuestiones, dos itinerarios cruzados y vista adaptable.")
