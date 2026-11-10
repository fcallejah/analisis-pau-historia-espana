"""Verify continuous carousel wrapping against the local server."""
from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (320, 375, 445, 768, 1024, 1440, 2560):
        page = browser.new_page(viewport={"width": width, "height": 900}, service_workers="block")
        page.goto("http://localhost:8765/")
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
