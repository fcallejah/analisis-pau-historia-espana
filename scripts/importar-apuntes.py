#!/usr/bin/env python3
"""Importar una exportación HTML de Google Docs a una página de apuntes existente."""
import argparse
import base64
import html
from html.parser import HTMLParser
import math
from pathlib import Path
import re
import struct
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
IDS = {
    1: "1PCWQjf98RERoyJZAeyGZvtj_D-XBf7gk0eYm--c5zuU",
    2: "12x5AA4RtX49xiCZl54-n0F3wEzqcaTwsmnOLgbEYBa8",
    3: "1RXepFknYtgNzC_-RVXBJhwNQS4dSjx-Ri1aZ0h4ldIo",
    4: "1q5P0YTBWItBwZWhsJG7l3sTrCQsAVTX4JzYtw9SFLTU",
}
ALLOWED = {
    "p", "div", "span", "h1", "h2", "h3", "h4", "ul", "ol", "li",
    "table", "tbody", "thead", "tr", "td", "th", "a", "sup", "sub",
    "strong", "em", "b", "i", "u", "br", "hr",
}
VOID = {"br", "hr"}
HEADINGS = {"h1": "h2", "h2": "h3", "h3": "h4", "h4": "h5"}


def image_dimensions(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 0xff:
                break
            while offset < len(data) and data[offset] == 0xff:
                offset += 1
            if offset >= len(data):
                break
            marker = data[offset]
            offset += 1
            if marker in (0x01, *range(0xd0, 0xd9)):
                continue
            if offset + 2 > len(data):
                break
            length = int.from_bytes(data[offset:offset + 2], "big")
            if length < 2 or offset + length > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 7:
                height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
                return width, height
            offset += length
    return None


class HeadingIndex(HTMLParser):
    """Validate TOC labels against the explicitly linked body headings."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.started = False
        self.heading = None
        self.headings = {}
        self.paragraph = None
        self.link = None
        self.entries = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in ("h2", "h3", "h4", "h5"):
            self.started = True
            if attrs.get("id", "").startswith("h."):
                name = attrs["id"]
                if name in self.headings:
                    raise ValueError(f"Encabezado duplicado: {name}")
                self.heading = [name, []]
        if not self.started and tag == "p":
            self.paragraph = []
        if self.paragraph is not None and tag == "a" and attrs.get("href", "").startswith("#h."):
            self.link = [attrs["href"][1:], []]

    def handle_data(self, text):
        if self.heading is not None:
            self.heading[1].append(text)
        if self.link is not None:
            self.link[1].append(text)

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "h4", "h5") and self.heading is not None:
            self.headings[self.heading[0]] = "".join(self.heading[1])
            self.heading = None
        if tag == "a" and self.link is not None:
            self.paragraph.append((self.link[0], "".join(self.link[1])))
            self.link = None
        if tag == "p" and self.paragraph is not None:
            if self.paragraph:
                self.entries.append(self.paragraph)
            self.paragraph = None


def map_heading_anchors(content, block, page_numbers=True):
    index = HeadingIndex()
    index.feed(content)
    if not index.entries or not index.headings:
        raise ValueError("No se encontró el índice o sus encabezados")
    normalize = lambda value: " ".join(value.split())
    for parts in index.entries:
        targets = {target for target, _ in parts}
        if len(targets) != 1:
            raise ValueError(f"Entrada del índice ambigua: {parts}")
        target = next(iter(targets))
        label = "".join(text for _, text in parts)
        if page_numbers:
            label = re.sub(r"\s+\d+\s*$", "", label)
        if target not in index.headings or normalize(label) != normalize(index.headings[target]):
            raise ValueError(f"Entrada del índice sin encabezado coincidente: {label!r} ({target})")
    mapping = {old: f"bloque-{block}-seccion-{old[2:]}" for old in index.headings}
    for old, new in mapping.items():
        if f'id="{new}"' in content:
            raise ValueError(f"Identificador de encabezado duplicado: {new}")
        # Retain old fragments as aliases for existing bookmarks.
        pattern = rf'(<h[2-5]\b[^>]*\bid="){re.escape(old)}("[^>]*>)'
        content, count = re.subn(pattern, rf'\g<1>{new}\g<2><span id="{old}" class="heading-alias"></span>', content)
        if count != 1:
            raise ValueError(f"Encabezado ambiguo: {old}")
        content = content.replace(f'href="#{old}"', f'href="#{new}"')
    return content


def rebuild_source_index(content):
    first_heading = re.search(r"<h[2-5]\b", content)
    if not first_heading:
        raise ValueError("No se encontraron encabezados para reconstruir el índice")
    prefix, body = content[:first_heading.start()], content[first_heading.start():]
    parser = Fragment()
    parser.feed(prefix)
    preserved = []
    for node in parser.root.children:
        if not isinstance(node, Element):
            preserved.append(html.escape(node))
            continue
        links = [item for item in walk(node) if item.tag == "a" and
                 dict(item.attrs).get("href", "").startswith("#h.")]
        if links:
            label = "".join(element_text(link) for link in links)
            if node.tag != "p" or " ".join(element_text(node).split()) != " ".join(label.split()):
                raise ValueError("Entrada del índice mezclada con contenido: no se puede reconstruir")
        elif node.tag == "p" and element_text(node).strip().upper() == "ÍNDICE":
            continue
        else:
            preserved.append(node.render())
    index = HeadingIndex()
    index.feed(body)
    entries = "".join(
        f'<p><a href="#{html.escape(target, quote=True)}">{html.escape(label)}</a></p>'
        for target, label in index.headings.items() if label.strip()
    )
    if not entries:
        raise ValueError("No se encontraron encabezados con texto")
    return entries + "".join(preserved) + body


def separate_heading_images(content):
    def move(match):
        heading = match.group(0)
        images = re.findall(r'<span><span class="doc-image".*?</span></span></span>(?=</h[2-5]>)', heading, re.S)
        if heading.count('class="doc-image"') != len(images):
            raise ValueError("Imagen de encabezado con estructura inesperada")
        for image in images:
            heading = heading.replace(image, "", 1)
        return heading + "".join(images)
    return re.sub(r'<h([2-5])\b[^>]*>.*?</h\1>', move, content, flags=re.S)


class Element:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, list(attrs), parent, []

    def has_class(self, name):
        return name in dict(self.attrs).get("class", "").split()

    def render(self):
        props = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in self.attrs)
        opening = f"<{self.tag}{props}>"
        if self.tag in ("img", "br", "hr"):
            return opening
        return opening + "".join(child.render() if isinstance(child, Element) else html.escape(child) for child in self.children) + f"</{self.tag}>"


class Fragment(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("root")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in ("img", "br", "hr"):
            self.current = node

    def handle_endtag(self, tag):
        if self.current.tag != tag:
            raise ValueError(f"Estructura inesperada en imágenes: {tag}")
        self.current = self.current.parent

    def handle_data(self, text):
        self.current.children.append(text)


def walk(node):
    yield node
    for child in node.children:
        if isinstance(child, Element):
            yield from walk(child)


def element_text(node):
    return "".join(element_text(child) if isinstance(child, Element) else child for child in node.children)


def extract_native_index(content, block, page_numbers=True):
    first_heading = re.search(r'<h[2-5]\b', content)
    if not first_heading:
        raise ValueError("No se encontró el comienzo del texto")
    prefix, body = content[:first_heading.start()], content[first_heading.start():]
    parser = Fragment()
    parser.feed(prefix)
    if parser.current is not parser.root:
        raise ValueError("Índice con estructura ambigua")
    headings = Fragment()
    headings.feed(body)
    targets = {}
    order = {}
    for node in walk(headings.root):
        if node.tag in ("h2", "h3", "h4", "h5") and dict(node.attrs).get("id", "").startswith(f"bloque-{block}-seccion-"):
            target = dict(node.attrs)["id"]
            if target in targets:
                raise ValueError("Destino del índice duplicado")
            order[target] = len(order)
            targets[target] = (int(node.tag[1]), " ".join(element_text(node).split()))
    entries = []
    last = -1
    for i, node in enumerate(parser.root.children):
        if not isinstance(node, Element):
            if node.strip():
                raise ValueError("Texto inesperado antes del índice")
            continue
        links = [item for item in walk(node) if item.tag == "a" and
                 dict(item.attrs).get("href", "").startswith(f"#bloque-{block}-seccion-")]
        if not links:
            continue
        if node.tag != "p":
            raise ValueError("Entrada de índice con estructura no compatible")
        destinations = {dict(link.attrs)["href"][1:] for link in links}
        if len(destinations) != 1:
            raise ValueError("Entrada de índice ambigua")
        target = next(iter(destinations))
        label = "".join(element_text(link) for link in links)
        if page_numbers:
            label = re.sub(r"\s+\d+\s*$", "", label)
        label = " ".join(label.split())
        if target not in targets or label != targets[target][1]:
            raise ValueError(f"Entrada de índice sin encabezado coincidente: {label}")
        visible = element_text(node)
        if page_numbers:
            visible = re.sub(r"\s+\d+\s*$", "", visible)
        visible = " ".join(visible.split())
        if visible != label:
            raise ValueError("Contenido original mezclado con una entrada del índice")
        if any(entry[0] == target for entry in entries) or entries and order[target] <= order[entries[-1][0]]:
            raise ValueError("Entradas del índice duplicadas o desordenadas")
        entries.append((target, *targets[target]))
        last = i
    if not entries:
        raise ValueError("No se encontró el índice original")
    for i, node in enumerate(parser.root.children[:last + 1]):
        if isinstance(node, Element):
            text = " ".join(element_text(node).split())
            if text and not any(item.tag == "a" for item in walk(node)) and text != "ÍNDICE":
                raise ValueError("Contenido original mezclado con el índice")
            if any(item.tag == "img" for item in walk(node)):
                raise ValueError("Imagen original mezclada con el índice")
            if any(item.tag == "a" and not dict(item.attrs).get("href", "").startswith(f"#bloque-{block}-seccion-")
                   for item in walk(node)):
                raise ValueError("Enlace original mezclado con el índice")
    listing = Element("ul")
    stack = [(entries[0][1] - 1, listing)]
    previous = None
    for target, level, label in entries:
        if level < entries[0][1]:
            raise ValueError("Jerarquía de índice ambigua")
        while level <= stack[-1][0]:
            stack.pop()
        if level > stack[-1][0] + 1:
            if previous is None or level != stack[-1][0] + 2:
                raise ValueError("Jerarquía de índice ambigua")
            nested = Element("ul")
            previous.children.append(nested)
            stack.append((level - 1, nested))
        item = Element("li")
        link = Element("a", [("href", "#" + target)])
        link.children.append(label)
        item.children.append(link)
        stack[-1][1].children.append(item)
        previous = item
    nav = f'<nav class="reading-index" aria-labelledby="reading-index-title"><h2 id="reading-index-title">Índice del bloque</h2>{listing.render()}</nav>'
    # Material after the last TOC entry (e.g. original map links) is not part of the TOC.
    remainder = "".join(node.render() if isinstance(node, Element) else html.escape(node)
                        for node in parser.root.children[last + 1:])
    if any(isinstance(node, Element) and (element_text(node).strip() or any(item.tag == "img" for item in walk(node)))
           for node in parser.root.children[last + 1:]):
        nav += f'<div class="reading-preamble">{remainder}</div>'
    return nav, body


def caption_text_is_italic(node):
    found = False
    def visit(element, italic=False):
        nonlocal found
        italic = (italic or element.tag in ("em", "i")) and not element.has_class("doc-normal-style")
        for child in element.children:
            if isinstance(child, Element):
                if child.tag in ("img", "hr"):
                    return False
                if not visit(child, italic):
                    return False
            elif child.strip():
                found = True
                if not italic:
                    return False
        return True
    return visit(node) and found


def following_caption(container):
    def candidate(item):
        if isinstance(item, str):
            return None if not item.strip() else False
        if item.tag == "p":
            if caption_text_is_italic(item):
                return item
            if not any(node.tag in ("img", "hr") or
                       any(isinstance(c, str) and c.strip() for c in node.children)
                       for node in walk(item)):
                return None
            return False
        if item.tag in ("div", "span"):
            for child in item.children:
                result = candidate(child)
                if result is not None:
                    return result
            return None
        return False

    current = container
    while current.parent:
        siblings = current.parent.children
        for item in siblings[siblings.index(current) + 1:]:
            result = candidate(item)
            if result is not None:
                return result or None
        if current.parent.tag not in ("div", "span", "root"):
            return None
        current = current.parent
    return None


def transfer_image_captions(content):
    parser = Fragment()
    parser.feed(content)
    if parser.current is not parser.root:
        raise ValueError("Fragmento incompleto")
    figures = [node for node in walk(parser.root) if node.has_class("doc-image")]
    for figure in figures:
        caption = next(node for node in figure.children if isinstance(node, Element) and node.has_class("doc-image-caption"))
        ancestor = figure
        while ancestor.parent and ancestor.tag not in ("p", "li", "td", "th", "h2", "h3", "h4", "h5"):
            ancestor = ancestor.parent
        if ancestor.tag == "p":
            figures_in_paragraph = [n for n in walk(ancestor) if n.has_class("doc-image")]
            if len(figures_in_paragraph) != 1:
                figure.children.remove(caption)
                continue
            after = False
            trailing = False
            for node in walk(ancestor):
                if node is figure:
                    after = True
                elif after and node not in list(walk(figure)):
                    if node.tag in ("img", "hr") or any(isinstance(c, str) and c.strip() for c in node.children):
                        trailing = True
            if trailing:
                figure.children.remove(caption)
                continue
            container = ancestor
        elif ancestor.tag in ("li", "td", "th", "h2", "h3", "h4", "h5"):
            figure.children.remove(caption)
            continue
        else:
            container = figure
            while container.parent and container.parent.tag == "span":
                container = container.parent
        found = following_caption(container)
        if found is None:
            figure.children.remove(caption)
            continue
        caption.children = found.children
        for child in caption.children:
            if isinstance(child, Element):
                child.parent = caption
        found.parent.children.remove(found)
    return "".join(child.render() if isinstance(child, Element) else html.escape(child) for child in parser.root.children)


def css_rules(document):
    styles = re.findall(r"<style[^>]*>(.*?)</style>", document, re.S | re.I)
    rules = []
    for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", "\n".join(styles)):
        selector = selector.strip()
        if not re.fullmatch(r"\.c\d+", selector):
            continue
        props = {}
        for declaration in declarations.split(";"):
            key, sep, value = declaration.partition(":")
            if sep and key.strip() in (
                "font-weight", "font-style", "text-decoration", "width", "height",
                "overflow", "overflow-x", "overflow-y", "margin-left", "margin-top",
                "transform", "-webkit-transform",
            ):
                props[key.strip()] = value.strip().lower()
        rules.append((selector[1:], props))
    return rules


def source_image_style(attrs, rules):
    properties = {}
    classes = attrs.get("class", "").split()
    for name, declarations in rules:
        if name in classes:
            properties.update(declarations)
    for declaration in attrs.get("style", "").split(";"):
        key, sep, value = declaration.partition(":")
        if sep:
            properties[key.strip().lower()] = value.strip().lower()
    for dimension in ("width", "height"):
        if dimension not in properties and re.fullmatch(r"\d+(?:\.\d+)?", attrs.get(dimension, "")):
            properties[dimension] = attrs[dimension] + "px"
    return properties


def crop_transform(style):
    value = style.get("transform", style.get("-webkit-transform", "none")).lower()
    if value == "none":
        return "none"
    tokens = re.findall(r"(rotate|translatez)\(([^()]*)\)", value)
    if not tokens or re.sub(r"(?:rotate|translatez)\([^()]*\)", "", value).strip():
        raise ValueError(f"Transformación de imagen no compatible: {value}")
    rotations = []
    for kind, argument in tokens:
        if kind == "translatez":
            if not re.fullmatch(r"[+-]?0(?:\.0+)?(?:px)?", argument):
                raise ValueError(f"Transformación de imagen no compatible: {value}")
        else:
            match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)(rad|deg|turn)", argument)
            if not match or not math.isfinite(float(match[1])):
                raise ValueError(f"Rotación de imagen no compatible: {value}")
            if float(match[1]) != 0:
                rotations.append(f"rotate({argument})")
    return " ".join(rotations) or "none"


def image_crop(styles, image):
    viewport = next((style for style in reversed(styles)
                     if style.get("overflow") in ("hidden", "clip") or
                     style.get("overflow-x") in ("hidden", "clip") or
                     style.get("overflow-y") in ("hidden", "clip")), None)
    if viewport is None:
        return None
    if viewport.get("overflow") not in ("hidden", "clip") and not all(
        viewport.get(f"overflow-{axis}") in ("hidden", "clip") for axis in ("x", "y")
    ):
        raise ValueError("Recorte de imagen en un solo eje no compatible")

    def pixels(style, key, default=None):
        value = style.get(key, default)
        match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)(?:px)?", value or "")
        if not match or not math.isfinite(float(match[1])):
            raise ValueError(f"Falta una medida de recorte en píxeles: {key}={value}")
        return float(match[1])

    width, height = (pixels(viewport, key) for key in ("width", "height"))
    image_width, image_height = (pixels(image, key) for key in ("width", "height"))
    left, top = (pixels(image, key, "0") for key in ("margin-left", "margin-top"))
    if min(width, height, image_width, image_height) <= 0:
        raise ValueError("Las dimensiones del recorte deben ser positivas")
    frame_transform, transform = crop_transform(viewport), crop_transform(image)
    if (image_width <= width and image_height <= height and left == top == 0
            and frame_transform == transform == "none"):
        return None
    # Percentages retain the export's geometry while the viewport scales uniformly on mobile.
    values = {
        "--doc-frame-width": f"{width:.8g}px",
        "--doc-frame-ratio": f"{width:.8g} / {height:.8g}",
        "--doc-img-width": f"{image_width / width * 100:.10g}%",
        "--doc-img-height": f"{image_height / height * 100:.10g}%",
        "--doc-img-left": f"{left / width * 100:.10g}%",
        "--doc-img-top": f"{top / height * 100:.10g}%",
    }
    if frame_transform != "none":
        values["--doc-frame-transform"] = frame_transform
    if transform != "none":
        values["--doc-img-transform"] = transform
    return ";".join(f"{key}:{value}" for key, value in values.items())


class Importer(HTMLParser):
    def __init__(self, number, document):
        super().__init__(convert_charrefs=True)
        self.number = number
        self.docid = IDS[number]
        self.rules = css_rules(document)
        self.body = False
        self.result = []
        self.stack = []
        self.source_styles = []
        self.images = {}

    def handle_starttag(self, tag, attributes):
        if tag == "body":
            self.body = True
            return
        if not self.body:
            return
        attrs = dict(attributes)
        source_style = source_image_style(attrs, self.rules)
        if tag == "img":
            match = re.fullmatch(r"data:image/(png|jpeg|gif|webp);base64,(.*)", attrs.get("src", ""), re.S)
            if not match:
                raise ValueError(f"Imagen no incrustada en el bloque {self.number}")
            extension = {"jpeg": "jpg"}.get(match.group(1), match.group(1))
            number = len(self.images) + 1
            name = f"bloque-{self.number}-{number:02d}.{extension}"
            data = base64.b64decode(match.group(2), validate=True)
            self.images[name] = data
            alt = attrs.get("alt", "").strip()
            label = f' aria-label="{html.escape(alt, quote=True)}"' if alt else ""
            size = image_dimensions(data)
            dimensions = f' width="{size[0]}" height="{size[1]}"' if size else ""
            crop = image_crop(self.source_styles, source_style)
            crop_start = f'<span class="doc-image-crop" style="{html.escape(crop, quote=True)}">' if crop else ""
            crop_end = "</span>" if crop else ""
            self.result.append(
                f'<span class="doc-image" role="figure"{label}>'
                f'{crop_start}'
                f'<img src="imagenes/{name}" alt="{html.escape(alt, quote=True)}"{dimensions} loading="lazy">'
                f'{crop_end}'
                f'<span class="doc-image-caption"></span></span>'
            )
            return
        if tag not in ALLOWED:
            raise ValueError(f"Etiqueta inesperada: {tag}")
        parent_weight, parent_italic = self.stack[-1][1:3] if self.stack else (False, False)
        weight, italic = parent_weight, parent_italic
        if tag in HEADINGS or tag in ("b", "strong"):
            weight = True
        if tag in ("i", "em"):
            italic = True
        classes = set(attrs.get("class", "").split())
        properties = {}
        for name, declarations in self.rules:
            if name in classes:
                properties.update(declarations)
        if "font-weight" in properties:
            value = properties["font-weight"]
            weight = value in ("bold", "bolder") or value.isdigit() and int(value) >= 600
        if "font-style" in properties:
            italic = properties["font-style"] in ("italic", "oblique")
        mapped = HEADINGS.get(tag, tag)
        # Native headings and explicit semantic elements already carry these styles.
        native_weight = parent_weight or tag in HEADINGS or tag in ("b", "strong")
        native_italic = parent_italic or tag in ("i", "em")
        resets = []
        if native_weight and not weight:
            resets.append("doc-normal-weight")
        if native_italic and not italic:
            resets.append("doc-normal-style")
        safe = []
        if attrs.get("id"):
            safe.append(("id", attrs["id"]))
        if tag == "a":
            reference = re.fullmatch(r"ftnt_ref(\d+)", attrs.get("id", ""))
            note = re.fullmatch(r"ftnt(\d+)", attrs.get("id", ""))
            if reference and attrs.get("href") == f"#ftnt{reference.group(1)}":
                safe.append(("class", "footnote-ref"))
                safe.append(("aria-label", f"Ir a la nota {reference.group(1)}"))
            elif note and attrs.get("href") == f"#ftnt_ref{note.group(1)}":
                safe.append(("class", "footnote-back"))
                safe.append(("aria-label", f"Volver a la referencia de la nota {note.group(1)}"))
        if resets:
            safe.append(("class", " ".join(resets)))
        if tag == "a" and attrs.get("href"):
            href = attrs["href"]
            parsed = urlparse(href)
            if parsed.hostname == "www.google.com" and parsed.path == "/url":
                href = parse_qs(parsed.query).get("q", [""])[0]
            if href.startswith("#") or urlparse(href).scheme in ("http", "https", "mailto"):
                safe.append(("href", href))
        if tag in ("td", "th"):
            for key in ("colspan", "rowspan"):
                if attrs.get(key, "").isdigit():
                    safe.append((key, attrs[key]))
        props = "".join(f' {key}="{html.escape(value, quote=True)}"' for key, value in safe)
        self.result.append(f"<{mapped}{props}>")
        wrappers = []
        if weight and not native_weight:
            wrappers.append("strong")
        if italic and not native_italic:
            wrappers.append("em")
        if "underline" in properties.get("text-decoration", "").split() and tag != "u":
            wrappers.append("u")
        self.result.extend(f"<{wrapper}>" for wrapper in wrappers)
        if tag not in VOID:
            self.stack.append((mapped, weight, italic, wrappers))
            self.source_styles.append(source_style)

    def handle_endtag(self, tag):
        if tag == "body":
            self.body = False
        elif self.body and tag in ALLOWED and tag not in VOID:
            mapped, _, _, wrappers = self.stack.pop()
            self.source_styles.pop()
            if mapped != HEADINGS.get(tag, tag):
                raise ValueError(f"Anidamiento inesperado: {tag}")
            self.result.extend(f"</{wrapper}>" for wrapper in reversed(wrappers))
            self.result.append(f"</{mapped}>")

    def handle_data(self, data):
        if self.body:
            self.result.append(html.escape(data))


def replace_imported_article(page, native_index, article):
    page = re.sub(r'<nav class="reading-index".*?</nav>(?:<div class="reading-preamble">.*?</div>(?=\s*<article))?\s*', "", page, count=1, flags=re.S)
    updated, count = re.subn(
        r'<article class="reading-content".*?</article>',
        lambda _: article,
        page,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("No se encontró el artículo de destino")
    updated, count = re.subn(
        r'(<figure class="reading-illustration"[^>]*>.*?</figure>)',
        lambda match: match[1] + "\n" + native_index,
        updated, count=1, flags=re.S,
    )
    if count != 1:
        raise ValueError("No se encontró la ilustración anterior al índice")
    return updated


BLOCK_FOUR_SCHEMES = (
    ("np-map", "bloque-4-04.png", r'<section class="np-map".*?</section>'),
    ("ob-chart", "bloque-4-05.png",
     r'<section class="ob-chart".*?<p class="ob-source">.*?</p>\s*</section>'),
)


def place_block_four_schemes(page):
    for class_name, filename, pattern in BLOCK_FOUR_SCHEMES:
        matches = list(re.finditer(pattern, page, re.S))
        if len(matches) != 1:
            raise ValueError(f"Esquema ausente o duplicado: {class_name}")
        scheme = matches[0][0]
        page = page[:matches[0].start()] + page[matches[0].end():]
        image = rf'<p><span><span class="doc-image"[^>]*><img src="imagenes/{re.escape(filename)}"[^>]*>.*?</p>'
        targets = list(re.finditer(image, page, re.S))
        if len(targets) != 1:
            raise ValueError(f"Imagen de destino ausente o duplicada: {filename}")
        caption = re.search(r'<span class="doc-image-caption">(.*)</span></span></span></p>$',
                            targets[0][0], re.S)
        replacement = scheme + (f'<p class="source-note">{caption[1]}</p>' if caption else "")
        page = page[:targets[0].start()] + replacement + page[targets[0].end():]
    return page


def quote_latin_expression(body):
    return re.sub(r'(?<![«"“])\buniversitas christiana\b(?![»"”])',
                  "«universitas christiana»", body, flags=re.I)


def normalize_practice_capitals(body):
    parser = Fragment()
    parser.feed(body)
    practice = False
    def normalize(node):
        for index, child in enumerate(node.children):
            if isinstance(child, Element):
                normalize(child)
            else:
                node.children[index] = re.sub(
                    r"\b(despotismo ilustrado|reales fábricas|motín)\b",
                    lambda match: match[0].lower(), child, flags=re.I,
                )
    for node in parser.root.children:
        if not isinstance(node, Element):
            continue
        if node.has_class("footnotes"):
            break
        if node.tag in ("h2", "h3", "h4", "h5") and "Ejemplos de preguntas cortas" in element_text(node):
            practice = True
        if practice:
            normalize(node)
    return "".join(node.render() if isinstance(node, Element) else html.escape(node)
                   for node in parser.root.children)


def embed_society_video(body):
    pattern = (r'<p><span><span class="doc-image"[^>]*><img src="imagenes/bloque-4-08.png"[^>]*>'
               r'.*?</p>\s*<p><span><u><a href="https://youtu.be/sPzE-fm-V-Y">.*?</a></u></span></p>')
    replacement = (
        '<figure class="reading-video" aria-label="Vídeo sobre la Sociedad Económica de Amigos del País de Málaga">'
        '<div class="reading-video-player" data-video-id="sPzE-fm-V-Y">'
        '</div><figcaption><a href="https://youtu.be/sPzE-fm-V-Y" target="_blank" rel="noopener noreferrer">'
        'Ver en YouTube</a></figcaption></figure>'
    )
    updated, count = re.subn(pattern, replacement, body, count=1, flags=re.S)
    if count != 1:
        raise ValueError("No se encontró la imagen y enlace del vídeo de la Sociedad Económica")
    return updated


def remove_import_notice(page):
    return re.sub(
        r'<p class="source-note">Texto e imágenes importados del .*?'
        r'Las imágenes se reproducen tal como aparecen allí; consulta la fuente para su contexto y autoría\.</p>',
        "", page, flags=re.S,
    )


def ensure_docs_button(page, block):
    footer = page.index('<button type="button" class="print-button" id="print-notes-bottom"')
    if 'class="docs-button"' in page[footer:]:
        return page
    end = page.index("</button>", footer) + len("</button>")
    link = (
        f'<a class="docs-button" href="https://docs.google.com/document/d/{IDS[block]}/edit" '
        'target="_blank" rel="noopener noreferrer">Ver en Google Docs</a>'
    )
    return page[:end] + link + page[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("block", type=int, choices=sorted(IDS))
    parser.add_argument("export", type=Path, help="exportación HTML descargada del documento correspondiente")
    parser.add_argument("--rebuild-index", action="store_true",
                        help="reconstruir un índice desactualizado usando los encabezados reales, sin cambiar el texto")
    args = parser.parse_args()
    document = args.export.read_text(encoding="utf-8")
    importer = Importer(args.block, document)
    importer.feed(document)
    if not importer.images or not importer.result or importer.stack:
        raise ValueError("Exportación incompleta o estructura inesperada")
    page_path = ROOT / f"apuntes/bloque-{args.block}.html"
    page = page_path.read_text(encoding="utf-8")
    body = transfer_image_captions(separate_heading_images("".join(importer.result)))
    if args.rebuild_index:
        body = rebuild_source_index(body)
        print("Índice reconstruido a partir de los encabezados reales del documento.")
    body = map_heading_anchors(body, args.block, page_numbers=not args.rebuild_index)
    native_index, body = extract_native_index(body, args.block, page_numbers=not args.rebuild_index)
    ids = re.findall(r'\bid="([^"]+)"', body)
    if len(ids) != len(set(ids)):
        raise ValueError("El documento contiene identificadores duplicados")
    references = set(re.findall(r'\bid="ftnt_ref(\d+)"', body))
    notes = set(re.findall(r'\bid="ftnt(\d+)"', body))
    if not references or references != notes:
        raise ValueError("Las referencias y notas no coinciden")
    for number in references:
        if not re.search(rf'<a\b[^>]*id="ftnt_ref{number}"[^>]*href="#ftnt{number}"', body):
            raise ValueError(f"Referencia inválida: {number}")
        if not re.search(rf'<a\b[^>]*id="ftnt{number}"[^>]*href="#ftnt_ref{number}"', body):
            raise ValueError(f"Retorno de nota inválido: {number}")
    marker = re.search(r'<div><p[^>]*><a id="ftnt1"(?=[ >])', body)
    if not marker:
        raise ValueError("No se encontró el inicio de las notas")
    body = body[:marker.start()] + '<section class="footnotes" aria-labelledby="footnotes-title"><h2 id="footnotes-title">Notas y referencias</h2>' + body[marker.start():] + "</section>"
    body = quote_latin_expression(normalize_practice_capitals(body))
    if args.block == 4:
        body = body.replace("Reales Fábricas", "reales fábricas")
    if args.block == 4 and "https://youtu.be/sPzE-fm-V-Y" in body:
        body = embed_society_video(body)
    article = '<article class="reading-content" aria-label="Texto del documento original">' + body + "</article>"
    # The shared reading tools and contextual illustration remain outside the replaceable article.
    if args.block == 4:
        schemes = []
        for class_name, _, pattern in BLOCK_FOUR_SCHEMES:
            matches = re.findall(pattern, page, re.S)
            if len(matches) != 1:
                raise ValueError(f"Esquema ausente o duplicado: {class_name}")
            schemes.append(matches[0])
            page = re.sub(pattern, "", page, count=1, flags=re.S)
        article = "".join(schemes) + article
    updated = ensure_docs_button(
        remove_import_notice(replace_imported_article(page, native_index, article)), args.block)
    if args.block == 4:
        updated = place_block_four_schemes(updated)
    image_dir = ROOT / "apuntes/imagenes"
    for name, data in importer.images.items():
        destination = image_dir / name
        if not destination.exists() or destination.read_bytes() != data:
            destination.write_bytes(data)
    page_path.write_text(updated, encoding="utf-8")
    stale = set(image_dir.glob(f"bloque-{args.block}-*")) - {image_dir / name for name in importer.images}
    for path in stale:
        path.unlink()
    print(f"Bloque {args.block}: {len(references)} notas, {len(importer.images)} imágenes importadas; {len(stale)} imágenes antiguas retiradas.")


if __name__ == "__main__":
    main()
