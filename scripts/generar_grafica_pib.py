import json

data = [
    (1939, 90000, 3509, 583800), (1940, 96200, 3750, 624000),
    (1941, 95500, 3723, 619400), (1942, 100300, 3910, 650600),
    (1943, 102500, 3996, 664800), (1944, 106300, 4144, 689500),
    (1945, 98200, 3828, 637000), (1946, 105500, 4113, 684300),
    (1947, 105900, 4128, 686900), (1948, 104300, 4066, 676500),
    (1949, 103900, 4050, 673900), (1950, 107400, 4187, 696600),
    (1951, 118100, 4604, 766000), (1952, 126000, 4912, 817300),
    (1953, 125600, 4896, 814700), (1954, 134900, 5259, 875000),
    (1955, 140500, 5477, 911300), (1956, 149400, 5824, 969100),
    (1957, 154700, 6031, 1003400), (1958, 160500, 6257, 1041100),
    (1959, 156400, 6097, 1014500), (1960, 158500, 6179, 1028100),
    (1961, 175400, 6838, 1137700), (1962, 189900, 7403, 1231700),
    (1963, 204400, 7968, 1325800), (1964, 214800, 8374, 1393300),
    (1965, 225700, 8799, 1464000), (1966, 239500, 9337, 1553500),
    (1967, 247500, 9648, 1605400), (1968, 261400, 10190, 1695500),
    (1969, 282100, 10997, 1829800), (1970, 291200, 11352, 1888800),
    (1971, 301600, 11757, 1956300), (1972, 322900, 12588, 2094400),
    (1973, 345000, 13449, 2237800),
]

width, height = 760, 444
pad_left, pad_right = 80, 25
pad_top, pad_bottom = 60, 65
plot_w = width - pad_left - pad_right
plot_h = height - pad_top - pad_bottom

y_max = 350000

svg_parts = []
svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="PIB por habitante en España, 1939–1973. Serie original en pesetas constantes de 1980; equivalentes de 2026 en los tooltips.">
  <defs>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
      .title {{ font-size: 16px; font-weight: 700; fill: #1e3a8a; text-anchor: middle; }}
      .subtitle {{ font-size: 13px; font-weight: 400; fill: #1e3a8a; text-anchor: middle; }}
      .axis-label {{ font-size: 12px; fill: #374151; }}
      .year-label {{ font-size: 11px; fill: #374151; }}
      .source {{ font-size: 11px; fill: #4b5563; }}
      .point {{ cursor: crosshair; outline: none; }}
      .hit {{ fill: transparent; stroke: transparent; }}
      .tooltip {{ visibility: hidden; pointer-events: none; }}
      .point:focus .tooltip, .point.is-pressed .tooltip {{ visibility: visible; }}
      @media (hover: hover) {{ .point:hover .tooltip {{ visibility: visible; }} }}
      .tooltip rect {{ fill: #1f2937; stroke: #fff; stroke-width: 1; rx: 5; }}
      .tooltip text {{ fill: #fff; font-size: 11px; font-weight: 600; }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" fill="#fff" />

  <!-- Título -->
  <text x="{width/2}" y="28" class="title">PIB POR HABITANTE, 1939–1973</text>
  <text x="{width/2}" y="46" class="subtitle">Serie original en ptas. constantes de 1980 · equivalentes de 2026 al posar el cursor</text>

  <!-- Fondo área gráfico con color similar al examen -->
  <rect x="{pad_left}" y="{pad_top}" width="{plot_w}" height="{plot_h}" fill="#fef08a" fill-opacity="0.55" stroke="#facc15" stroke-width="1.5" />''')

# Líneas de cuadrícula horizontal
for val in range(0, y_max + 1, 50000):
    y = pad_top + plot_h - (val / y_max) * plot_h
    svg_parts.append(f'''  <line x1="{pad_left}" y1="{y:.1f}" x2="{pad_left + plot_w}" y2="{y:.1f}" stroke="#ffffff" stroke-width="1.5" />''')
    # Etiqueta eje Y
    label = f"{val:,.0f}".replace(",", ".")
    svg_parts.append(f'''  <text x="{pad_left - 8}" y="{y + 4:.1f}" class="axis-label" text-anchor="end">{label}</text>''')
    # Marca eje Y
    svg_parts.append(f'''  <line x1="{pad_left - 4}" y1="{y:.1f}" x2="{pad_left}" y2="{y:.1f}" stroke="#ca8a04" stroke-width="1" />''')

# Puntos y eje X
points = []
num_years = len(data)
for i, (yr, val, euros_2026, pesetas_2026) in enumerate(data):
    x = pad_left + (i / (num_years - 1)) * plot_w
    y = pad_top + plot_h - (val / y_max) * plot_h
    points.append(f"{x:.1f},{y:.1f}")

    # Marcas eje X cada 2 años como el examen (1939, 1941, ..., 1973)
    if (yr - data[0][0]) % 6 == 0 or yr == data[-1][0]:
        svg_parts.append(f'''  <line x1="{x:.1f}" y1="{pad_top + plot_h}" x2="{x:.1f}" y2="{pad_top + plot_h + 5}" stroke="#ca8a04" stroke-width="1" />''')
        year_label = f"{yr}*" if yr == data[0][0] else str(yr)
        svg_parts.append(f'''  <text x="{x:.1f}" y="{pad_top + plot_h + 18}" class="year-label" text-anchor="end" transform="rotate(-45, {x:.1f}, {pad_top + plot_h + 18})">{year_label}</text>''')

# Curva roja
points_str = " ".join(points)
svg_parts.append(f'''  <polyline fill="none" stroke="#dc2626" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{points_str}" />''')

# Interactive points include a larger invisible hit target for touch screens.
for i, (yr, val, euros_2026, pesetas_2026) in enumerate(data):
    x = pad_left + (i / (num_years - 1)) * plot_w
    y = pad_top + plot_h - (val / y_max) * plot_h
    label = f"{val:,.0f}".replace(",", ".")
    euro_label = f"{euros_2026:,.0f}".replace(",", ".")
    peseta_label = f"{pesetas_2026:,.0f}".replace(",", ".")
    display_year = f"{yr}*" if yr == data[0][0] else str(yr)
    tooltip_width, tooltip_height = 260, 76
    tooltip_x = min(max(pad_left, x - tooltip_width / 2), width - pad_right - tooltip_width)
    tooltip_y = y - tooltip_height - 8
    if tooltip_y < pad_top + 4:
        tooltip_y = min(y + 8, pad_top + plot_h - tooltip_height - 4)
    aria_label = (
        f"{display_year}: serie original, {label} pesetas constantes de 1980; "
        f"{euro_label} euros de 2026; {peseta_label} pesetas de 2026"
    )
    svg_parts.append(f'''  <g class="point" data-year="{yr}" data-original-pesetas-1980="{val}" data-euros-2026="{euros_2026}" data-pesetas-2026="{pesetas_2026}" tabindex="0" role="graphics-symbol" aria-label="{aria_label}">
    <title>{aria_label}</title>
      <circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="8" />
    <circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#dc2626" stroke="#fff" stroke-width="1" />
    <g class="tooltip" transform="translate({tooltip_x:.1f} {tooltip_y:.1f})">
      <rect width="{tooltip_width}" height="{tooltip_height}" />
      <text x="8" y="17">{display_year}</text>
      <text x="8" y="34">Serie original: {label} ptas.</text>
      <text x="8" y="51">Euros de 2026: {euro_label} €</text>
      <text x="8" y="68">Pesetas de 2026: {peseta_label}</text>
    </g>
  </g>''')

# Touch devices show a tooltip only while the point is pressed; mouse hover and
# keyboard focus remain available without requiring JavaScript.
svg_parts.append('''  <script><![CDATA[
    const chart = document.documentElement;
    let pressedPoint;
    chart.addEventListener("pointerdown", event => {
      if (event.pointerType === "mouse") return;
      pressedPoint = event.target.closest(".point");
      pressedPoint?.classList.add("is-pressed");
    });
    const releasePoint = () => {
      pressedPoint?.classList.remove("is-pressed");
      pressedPoint = undefined;
    };
    chart.addEventListener("pointerup", releasePoint);
    chart.addEventListener("pointercancel", releasePoint);
  ]]></script>''')

# Fuente abajo
svg_parts.append(f'''  <text x="{pad_left}" y="{height - 27}" class="source" font-style="normal">Fuente: Prados de la Escosura, <tspan font-style="italic">Spain\'s Gross Domestic Product</tspan> (1995).</text>''')
svg_parts.append(f'''  <text x="{pad_left}" y="{height - 8}" class="source">* El examen original indica 1931; la serie de la gráfica comienza en 1939.</text>''')
svg_parts.append("</svg>")

svg_content = "\n".join(svg_parts) + "\n"
with open("assets/documentos/grafica-pib-habitante-1939-1973.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("SVG generado con éxito")
