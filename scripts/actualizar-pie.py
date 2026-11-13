"""Synchronize the static site footer without requiring JavaScript."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent


def footer_markup(home_url):
    return f'''<footer class="site-footer">
  <div class="footer-inner">
    <a class="brand" href="{home_url}"><span class="brand-icon" aria-hidden="true">H</span> PAU Andalucía <span class="muted">/</span> Historia de España</a>
    <p class="credit">
      <span class="credit-part">Página web creada por <a href="https://github.com/fcallejah" target="_blank" rel="noopener noreferrer">fcallejah</a></span>
      <span class="credit-part">con mucho cariño desde</span>
      <span class="credit-part credit-place"><a href="https://youtu.be/dGbyNi_Z25c" target="_blank" rel="noopener noreferrer" title="Ver vídeo sobre Cuevas Bajas (se abre en nueva pestaña)"><strong>Cuevas Bajas (Málaga)</strong><svg class="ext-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg></a></span>
      <span class="credit-part credit-emojis"><a href="https://youtu.be/dGbyNi_Z25c" target="_blank" rel="noopener noreferrer" title="Ver vídeo sobre Cuevas Bajas (se abre en nueva pestaña)" aria-label="Ver vídeo sobre Cuevas Bajas (se abre en nueva pestaña)"><span aria-hidden="true">🥕 💜 🫒 🏞️</span></a></span>
    </p>
  </div>
</footer>'''


def update_page(page, prefix="", home=False):
    if "</head>" not in page or "</body>" not in page:
        raise ValueError("La página no contiene un head y body completos")
    stylesheet = f'<link rel="stylesheet" href="{prefix}site-footer.css?v=2">'
    stylesheet_pattern = r'<link\b[^>]*href="[^"]*site-footer\.css[^"]*"[^>]*>'
    stylesheets = re.findall(stylesheet_pattern, page)
    if len(stylesheets) > 1:
        raise ValueError("La página contiene varias hojas de estilo del pie")
    if stylesheets:
        page = re.sub(stylesheet_pattern, stylesheet, page, count=1)
    else:
        page = page.replace("</head>", stylesheet + "\n</head>", 1)
    footer = footer_markup("#inicio" if home else f"{prefix}index.html#inicio")
    footer_pattern = r"<footer\b[^>]*>.*?</footer>"
    footers = re.findall(footer_pattern, page, flags=re.S)
    if len(footers) > 1:
        raise ValueError("La página contiene varios pies")
    if footers:
        return re.sub(footer_pattern, lambda match: footer, page, count=1, flags=re.S)
    return page.replace("</body>", footer + "\n</body>", 1)


def main():
    pages = [ROOT / "index.html", ROOT / "documentos.html", ROOT / "mis-preguntas.html", ROOT / "mis-documentos.html",
             *sorted((ROOT / "apuntes").glob("bloque-*.html"))]
    for path in pages:
        source = path.read_text(encoding="utf-8")
        updated = update_page(source, "../" if path.parent.name == "apuntes" else "",
                              home=path.name == "index.html")
        if source != updated:
            path.write_text(updated, encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
