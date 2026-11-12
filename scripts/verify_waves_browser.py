"""Verify seamless homepage wave loops against the local server on port 8765."""
from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(service_workers="block", reduced_motion="no-preference")
        page.goto("http://localhost:8765/")
        page.wait_for_selector(".hero-waves .wave", state="attached")
        results = page.evaluate("""async () => {
            const results = [];
            for (const wave of document.querySelectorAll('.hero-waves .wave')) {
                const image = new Image();
                const loaded = new Promise((resolve, reject) => {
                    image.onload = resolve;
                    image.onerror = reject;
                });
                image.src = 'data:image/svg+xml;charset=utf-8,' +
                    encodeURIComponent(new XMLSerializer().serializeToString(wave));
                await loaded;
                const canvas = document.createElement('canvas');
                canvas.width = 2400;
                canvas.height = 200;
                const context = canvas.getContext('2d');
                context.drawImage(image, 0, 0, 2400, 200);
                const first = context.getImageData(0, 0, 1200, 200).data;
                const second = context.getImageData(1200, 0, 1200, 200).data;
                let differences = 0;
                let visiblePixels = 0;
                for (let index = 3; index < first.length; index += 4) {
                    if (first[index] !== second[index]) differences++;
                    if (first[index]) visiblePixels++;
                }
                const animation = wave.getAnimations()[0];
                animation.pause();
                const timing = animation.effect.getTiming();
                animation.currentTime = timing.duration + timing.delay + 0.01;
                const start = new DOMMatrix(getComputedStyle(wave).transform).m41;
                animation.currentTime = 2 * timing.duration + timing.delay - 0.01;
                const end = new DOMMatrix(getComputedStyle(wave).transform).m41;
                results.push({
                    name: wave.getAttribute('class'), differences, visiblePixels,
                    distance: Math.abs(end - start),
                    halfWidth: wave.getBoundingClientRect().width / 2,
                    duration: timing.duration,
                });
            }
            return results;
        }""")
        assert len(results) == 3
        for result, duration in zip(results, (22000, 30000, 38000)):
            assert result["visiblePixels"] > 0, result
            assert result["differences"] <= 2, result  # Subpixel rasterization at curve edges.
            assert abs(result["distance"] - result["halfWidth"]) < 0.1, result
            assert result["duration"] == duration, result
        page.emulate_media(reduced_motion="reduce")
        assert page.locator(".hero-waves .wave").evaluate_all(
            "(waves) => waves.every(wave => getComputedStyle(wave).animationName === 'none')"
        )
        browser.close()
        print("OK: identical wave halves, seamless loop distance, original durations, reduced motion.")


if __name__ == "__main__":
    run()
