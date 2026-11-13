"""Verify the shared static footer on every page, including narrow screens."""
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "documentos.html", "mis-preguntas.html", "mis-documentos.html",
         *[path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "apuntes").glob("bloque-*.html"))]]
BASE = "http://127.0.0.1:8765"
VIDEO = "https://youtu.be/dGbyNi_Z25c"


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(service_workers="block")
        context.route("https://**", lambda route: route.abort())
        page = context.new_page()
        for path in PAGES:
            page.goto(f"{BASE}/{path}", wait_until="domcontentloaded")
            footer = page.locator("footer.site-footer")
            assert footer.count() == 1, path
            assert footer.locator(".credit").inner_text().startswith("Página web creada por")
            assert footer.locator('a[href="https://github.com/fcallejah"]').count() == 1
            assert footer.locator(".credit-place .ext-icon[aria-hidden=true] path").count() == 1
            assert footer.locator(".credit-emojis a").get_attribute("aria-label")
            assert footer.locator(".credit-emojis span").get_attribute("aria-hidden") == "true"
            for link in footer.locator(f'a[href="{VIDEO}"]').all():
                assert link.get_attribute("target") == "_blank", path
                assert set(link.get_attribute("rel").split()) >= {"noopener", "noreferrer"}, path
                assert link.get_attribute("title") == "Ver vídeo sobre Cuevas Bajas (se abre en nueva pestaña)"
            assert footer.locator(f'a[href="{VIDEO}"]').count() == 2, path
            assert footer.locator(".brand").evaluate("(a) => new URL(a.href).pathname").endswith("/index.html")
            assert footer.locator(".brand").evaluate("(a) => new URL(a.href).hash") == "#inicio"
            for width in (320, 375, 768, 1280):
                page.set_viewport_size({"width": width, "height": 900})
                for theme in ("light", "dark"):
                    page.evaluate("(theme) => document.documentElement.dataset.theme = theme", theme)
                    footer.scroll_into_view_if_needed()
                    assert page.evaluate("""() => {
                        const header = getComputedStyle(document.querySelector('.site-header .brand-icon'));
                        const footer = getComputedStyle(document.querySelector('.site-footer .brand-icon'));
                        return footer.fontFamily === header.fontFamily && footer.fontStyle === header.fontStyle
                            && footer.lineHeight === header.lineHeight
                            && footer.paddingTop === header.paddingTop && footer.paddingBottom === header.paddingBottom
                            && footer.placeItems === header.placeItems;
                    }"""), (path, width, theme, "H distinta a la cabecera")
                    geometry = footer.evaluate("""node => {
                        const credit = node.querySelector('.credit').getBoundingClientRect();
                        const brand = node.querySelector('.brand').getBoundingClientRect();
                        return {center:credit.left+credit.width/2, brandRight:brand.right,
                            viewportWidth:document.documentElement.getBoundingClientRect().width,
                            brandBottom:brand.bottom, creditTop:credit.top,
                            paddingRight:parseFloat(getComputedStyle(node).paddingRight),
                            overflow:[...node.querySelectorAll('a,.credit-part')].some(child => {
                                const box = child.getBoundingClientRect();
                                return box.left < -1 || box.right > document.documentElement.getBoundingClientRect().right+1;
                            })};
                    }""")
                    assert not geometry["overflow"], (path, width, theme, geometry)
                    if width < 1000:
                        assert abs(geometry["center"] - geometry["viewportWidth"] / 2) < 1, (path, width, theme, geometry)
                        assert geometry["creditTop"] >= geometry["brandBottom"], (path, width, theme, geometry)
                    elif path != "index.html":
                        assert abs(geometry["paddingRight"] - geometry["viewportWidth"] * .072) < 1, (path, geometry)
                        center = (geometry["brandRight"] + 24 + geometry["viewportWidth"] - geometry["paddingRight"]) / 2
                        assert abs(geometry["center"] - center) < 1, (path, width, theme, geometry)
            page.emulate_media(media="print")
            assert not footer.is_visible(), path
            page.emulate_media(media="screen")
        context.close()
        static = browser.new_context(java_script_enabled=False)
        static.route("https://**", lambda route: route.abort())
        for path in PAGES:
            static_page = static.new_page()
            static_page.goto(f"{BASE}/{path}", wait_until="domcontentloaded")
            assert static_page.locator("footer.site-footer").is_visible(), path
            static_page.close()
        static.close()
        browser.close()
    print(f"OK: pie estático en {len(PAGES)} páginas, cuatro anchos, claro/oscuro, enlaces e impresión.")


if __name__ == "__main__":
    run()
