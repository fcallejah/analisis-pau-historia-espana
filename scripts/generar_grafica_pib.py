import json

data = [
    (1939, 90000), (1940, 94000), (1941, 93500), (1942, 98000), (1943, 101500),
    (1944, 105000), (1945, 96500), (1946, 100000), (1947, 101000), (1948, 99500),
    (1949, 99000), (1950, 103500), (1951, 112000), (1952, 119500), (1953, 120500),
    (1954, 127000), (1955, 133500), (1956, 142000), (1957, 147000), (1958, 152500),
    (1959, 149000), (1960, 151500), (1961, 168000), (1962, 183000), (1963, 199000),
    (1964, 210500), (1965, 222000), (1966, 236500), (1967, 245000), (1968, 259000),
    (1969, 280000), (1970, 290500), (1971, 301500), (1972, 323000), (1973, 345000)
]

width, height = 760, 444
pad_left, pad_right = 80, 25
pad_top, pad_bottom = 60, 65
plot_w = width - pad_left - pad_right
plot_h = height - pad_top - pad_bottom

y_max = 350000

svg_parts = []
svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="PIB por habitante en España, 1939–1973">
  <defs>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
      .title {{ font-size: 16px; font-weight: 700; fill: #1e3a8a; text-anchor: middle; }}
      .subtitle {{ font-size: 13px; font-weight: 400; fill: #1e3a8a; text-anchor: middle; }}
      .axis-label {{ font-size: 12px; fill: #374151; }}
      .year-label {{ font-size: 11px; fill: #374151; }}
      .source {{ font-size: 11px; font-style: italic; fill: #4b5563; }}
      .point {{ cursor: crosshair; outline: none; }}
      .hit {{ fill: transparent; stroke: transparent; }}
      .tooltip {{ visibility: hidden; pointer-events: none; }}
      .point:focus .tooltip, .point.is-pressed .tooltip {{ visibility: visible; }}
      @media (hover: hover) {{ .point:hover .tooltip {{ visibility: visible; }} }}
      .tooltip rect {{ fill: #1f2937; stroke: #fff; stroke-width: 1; rx: 5; }}
      .tooltip text {{ fill: #fff; font-size: 12px; font-weight: 600; }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" fill="#fff" />

  <!-- Título -->
  <text x="{width/2}" y="28" class="title">PIB POR HABITANTE, 1939–1973*</text>
  <text x="{width/2}" y="46" class="subtitle">(en ptas. de 1980)</text>

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
for i, (yr, val) in enumerate(data):
    x = pad_left + (i / (num_years - 1)) * plot_w
    y = pad_top + plot_h - (val / y_max) * plot_h
    points.append(f"{x:.1f},{y:.1f}")

    # Marcas eje X cada 2 años como el examen (1939, 1941, ..., 1973)
    if (yr - data[0][0]) % 6 == 0 or yr == data[-1][0]:
        svg_parts.append(f'''  <line x1="{x:.1f}" y1="{pad_top + plot_h}" x2="{x:.1f}" y2="{pad_top + plot_h + 5}" stroke="#ca8a04" stroke-width="1" />''')
        svg_parts.append(f'''  <text x="{x:.1f}" y="{pad_top + plot_h + 18}" class="year-label" text-anchor="end" transform="rotate(-45, {x:.1f}, {pad_top + plot_h + 18})">{yr}</text>''')

# Curva roja
points_str = " ".join(points)
svg_parts.append(f'''  <polyline fill="none" stroke="#dc2626" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{points_str}" />''')

# Interactive points include a larger invisible hit target for touch screens.
for i, (yr, val) in enumerate(data):
    x = pad_left + (i / (num_years - 1)) * plot_w
    y = pad_top + plot_h - (val / y_max) * plot_h
    label = f"{val:,.0f}".replace(",", ".")
    tooltip_x = min(max(pad_left, x - 65), width - 150)
    tooltip_y = max(pad_top + 4, y - 42)
    svg_parts.append(f'''  <g class="point" tabindex="0" role="graphics-symbol" aria-label="{yr}: aproximadamente {label} pesetas constantes de 1980">
    <title>{yr}: aproximadamente {label} pesetas constantes de 1980</title>
      <circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="8" />
    <circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#dc2626" stroke="#fff" stroke-width="1" />
    <g class="tooltip" transform="translate({tooltip_x:.1f} {tooltip_y:.1f})">
      <rect width="142" height="32" />
      <text x="8" y="21">{yr} · ~{label} ptas.</text>
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
svg_parts.append(f'''  <text x="{pad_left}" y="{height - 27}" class="source">Fuente: Prados de la Escosura, Spain\'s Gross Domestic Product (1995).</text>''')
svg_parts.append(f'''  <text x="{pad_left}" y="{height - 8}" class="source">* El examen original indica 1931; la serie de la gráfica comienza en 1939.</text>''')
svg_parts.append("</svg>")

svg_content = "\n".join(svg_parts) + "\n"
with open("assets/documentos/grafica-pib-habitante-1939-1973.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("SVG generado con éxito")
