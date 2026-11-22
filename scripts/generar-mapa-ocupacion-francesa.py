#!/usr/bin/env python3
"""Generate the study map using the repository's attributed geographic bases."""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def tag(name):
    return f"{{{NS}}}{name}"


def copy_shape(shape, **attributes):
    result = deepcopy(shape)
    result.attrib.clear()
    result.attrib.update(attributes)
    for key in ("d", "points", "fill-rule"):
        if key in shape.attrib:
            result.set(key, shape.get(key))
    return result


base = ET.parse(ROOT / "assets/apuntes/nueva-planta.svg").getroot()
geo = next(element for element in base if element.get("class") == "map-geography")
root = ET.fromstring(f"""<svg xmlns="{NS}" width="1080" height="875" viewBox="0 75 1080 875" role="img" aria-labelledby="title description">
  <title id="title">La ocupación francesa y las plazas resistentes, 1808–1814</title>
  <desc id="description">Esquema de la guerra de la Independencia: el azul indica campañas francesas en distintos momentos y con control variable; el rojo señala plazas resistentes e islas no ocupadas. La España napoleónica se asocia a José I Bonaparte, rey de 1808 a 1813, y al Estatuto de Bayona, carta otorgada de 1808. Galicia y Asturias conocieron ocupaciones temporales. Se señalan Cádiz, la Isla de León, Tarifa, Alicante y Cartagena; Gibraltar era británico. Los barcos representan simbólicamente el predominio naval británico, que dificultó las incursiones y desembarcos franceses, sin indicar ubicaciones exactas. Un recuadro recuerda al duque de Wellington y los ejércitos aliados. También se mencionan las plazas norteafricanas y los territorios americanos y asiáticos, con la salvedad de las revoluciones y guerras de independencia en América.</desc>
  <metadata>Elaboración propia. Península y Baleares: INE 2018, geoBoundaries ESP-ADM2-93216281; Portugal y Francia: Natural Earth, dominio público. Canarias: adaptación de España-loc.svg, Miguillen, CC BY-SA 3.0, https://commons.wikimedia.org/wiki/File:Espa%C3%B1a-loc.svg . Geometría moderna simplificada; no representa fronteras históricas ni control simultáneo. Fuentes históricas: Instituto Geográfico Nacional, https://centrodedescargas.cnig.es/CentroDescargas/busquedaRedirigida.do?ruta=PUBLICACION_CNIG_DATOS_VARIOS/aneTematico/Espana_Guerra-de-la-Independencia.-Ocupacion-francesa_1808-1814_mapa_16797_spa.pdf ; Universidade de Vigo, https://portalcientifico.uvigo.gal/documentos/5f0b9a66299952638043304d ; Universidad de Murcia, https://publicaciones.um.es/publicaciones/public/obras/ficha.seam?numero=2998&amp;edicion=1 ; https://www.historyofwar.org/articles/siege_tarifa.html . Mapa derivado bajo CC BY-SA 3.0.</metadata>
  <style>
    text{{font-family:Arial,sans-serif;fill:#25353b}}
    .label{{font-size:16px;font-weight:700;paint-order:stroke;stroke:#f5f9fa;stroke-width:4px;stroke-linejoin:round}}
    .small{{font-size:15px;fill:#495c60}}
    .note{{font-size:15px;fill:#354d51}}
    .box-title{{font-size:18px;font-weight:700;fill:#274f4b}}
    .region{{font-size:17px;font-weight:700;fill:#234f77;paint-order:stroke;stroke:#f5f9fa;stroke-width:4px;stroke-linejoin:round}}
    .regime{{font-size:23px;font-weight:700;fill:#173c5b}}
    .regime-detail{{font-size:16px;fill:#173c5b}}
    .leader{{fill:none;stroke:#446a61;stroke-width:1.6}}
    .place{{fill:#ae3239;stroke:#fff;stroke-width:2.5}}
  </style>
  <defs>
    <g id="british-ship">
      <path d="M2 23H30L26 28H7Z" fill="#30465b"/>
      <path d="M15 3V23M15 7L4 20H15M18 9L27 20H18Z" fill="#fffdf3" stroke="#30465b" stroke-width="1.2"/>
      <path d="M16 3H24V8H16Z" fill="#b63f47"/>
    </g>
  </defs>
  <rect width="1080" height="950" rx="18" fill="#fbfaf6"/>
  <rect x="22" y="94" width="1036" height="580" rx="16" fill="#edf6f8" stroke="#d4e5e6"/>
  <g id="geography" transform="translate(30 102)"/>
  <g transform="translate(30 102)">
    <text class="region" x="125" y="87">Galicia</text>
    <text class="region" x="211" y="62">Asturias</text>
    <text class="small" x="137" y="111">ocupación temporal</text>
    <text class="small" x="214" y="84">incursiones y ocupaciones</text>
    <text class="small" x="135" y="285" transform="rotate(-85 135 285)">Portugal</text>
    <text class="small" x="553" y="26">Francia</text>
    <text class="label" x="657" y="290">Baleares</text>
    <text class="regime-detail" x="350" y="265" text-anchor="middle">José I Bonaparte (1808-1813)</text>
    <text class="regime-detail" x="350" y="292" text-anchor="middle">Estatuto de Bayona (carta otorgada)</text>
    <text class="regime" x="350" y="320" text-anchor="middle">España napoleónica</text>
    <circle class="place" cx="218" cy="474" r="6"/>
    <circle class="place" cx="222" cy="481" r="5"/>
    <path class="leader" d="M218 474L175 455H130 M222 481L175 455"/>
    <text class="label" x="20" y="459">Isla de León</text>
    <text class="small" x="20" y="480">(Cádiz y San Fernando)</text>
    <circle class="place" cx="252" cy="508" r="6"/>
    <path class="leader" d="M252 508L235 530H189"/>
    <text class="label" x="145" y="535">Tarifa</text>
    <circle class="place" cx="264.5" cy="500.4" r="6"/>
    <path class="leader" d="M264.5 500.4L286 530H298"/>
    <text class="label" x="302" y="535">Gibraltar (británico)</text>
    <circle class="place" cx="507" cy="368" r="6"/>
    <path class="leader" d="M507 368L524 352H530"/>
    <text class="label" x="533" y="356">Alicante</text>
    <circle class="place" cx="482" cy="415" r="6"/>
    <path class="leader" d="M482 415L504 430H511"/>
    <text class="label" x="514" y="435">Cartagena</text>
  </g>
  <g aria-label="Barcos británicos, símbolos sin ubicación exacta">
    <use href="#british-ship" transform="translate(320 100) scale(.8)"/>
    <use href="#british-ship" transform="translate(60 275) scale(.8)"/>
    <use href="#british-ship" transform="translate(48 380) scale(.8)"/>
    <use href="#british-ship" transform="translate(48 495) scale(.8)"/>
    <use href="#british-ship" transform="translate(410 579) scale(.8)"/>
    <use href="#british-ship" transform="translate(535 580) scale(.8)"/>
    <use href="#british-ship" transform="translate(604 480) scale(.8)"/>
    <use href="#british-ship" transform="translate(610 340) scale(.8)"/>
    <use href="#british-ship" transform="translate(710 450) scale(.8)"/>
  </g>
  <g transform="translate(593 560)">
    <rect width="228" height="96" rx="10" fill="#fffdf8" stroke="#c7d7de"/>
    <circle cx="23" cy="27" r="13" fill="#e1e9ed"/>
    <path d="M12 25Q23 19 34 25L31 20H15Z" fill="#35465b"/>
    <circle cx="23" cy="30" r="5" fill="#ba8973"/>
    <text class="box-title" x="43" y="29">Wellington</text>
    <text class="small" x="43" y="48">Ejércitos aliados:</text>
    <text class="small" x="43" y="66">británicos, portugueses</text>
    <text class="small" x="43" y="84">y españoles.</text>
  </g>
  <g transform="translate(838 126)">
    <rect x="0" y="24" width="22" height="22" rx="3" fill="#8bb4d3" stroke="#507c9e"/>
    <text class="note" x="32" y="30"><tspan x="32">Campañas y</tspan><tspan x="32" dy="19">ocupación francesa</tspan><tspan x="32" dy="19">en algún momento</tspan></text>
    <rect x="0" y="100" width="22" height="22" rx="3" fill="#df8884" stroke="#ad5d5a"/>
    <text class="note" x="32" y="107"><tspan x="32">Baleares: sin</tspan><tspan x="32" dy="19">ocupación francesa</tspan></text>
    <circle class="place" cx="11" cy="166" r="7"/>
    <text class="note" x="32" y="163"><tspan x="32">Plaza señalada</tspan><tspan x="32" dy="19">no tomada</tspan></text>
    <circle class="place" cx="11" cy="219" r="7"/>
    <text class="note" x="32" y="216"><tspan x="32">Gibraltar:</tspan><tspan x="32" dy="19">posesión británica</tspan></text>
    <use href="#british-ship" transform="translate(0 278) scale(.8)"/>
    <text class="note" x="32" y="295">Flota británica</text>
    <text class="note" x="0" y="331"><tspan x="0">Su predominio naval</tspan><tspan x="0" dy="20">dificultó incursiones y</tspan><tspan x="0" dy="20">desembarcos franceses.</tspan></text>
  </g>
  <text class="box-title" x="36" y="710">Fuera de la península</text>
  <rect x="25" y="725" width="296" height="175" rx="12" fill="#edf5ef" stroke="#c8ddce"/>
  <text class="box-title" x="43" y="755">Canarias</text>
  <g id="canarias" transform="translate(55 240) scale(1.35)"/>
  <use href="#british-ship" transform="translate(253 844) scale(.8)"/>
  <text class="note" x="43" y="865">Sin ocupación francesa.</text>
  <rect x="333" y="725" width="296" height="175" rx="12" fill="#edf5ef" stroke="#c8ddce"/>
  <text class="box-title" x="351" y="755">Plazas norteafricanas</text>
  <text class="note" x="351" y="785"><tspan x="351">Ceuta, Melilla y demás plazas</tspan><tspan x="351" dy="22">españolas: no ocupadas</tspan><tspan x="351" dy="22">por las tropas napoleónicas.</tspan></text>
  <rect x="641" y="725" width="414" height="175" rx="12" fill="#edf5ef" stroke="#c8ddce"/>
  <text class="box-title" x="659" y="755">América y Asia</text>
  <text class="note" x="659" y="785"><tspan x="659">Territorios de la monarquía no conquistados</tspan><tspan x="659" dy="22">por Napoleón; en América surgieron juntas</tspan><tspan x="659" dy="22">y guerras de independencia desde 1810.</tspan></text>
  <text class="small" x="31" y="929">Esquema propio aproximado</text>
</svg>""")
geography = root.find(".//*[@id='geography']")
mainland_paths = []
for element in geo:
    if element.tag == tag("path") and element.get("class") == "land":
        geography.append(copy_shape(element, fill="#e5e2d9", stroke="#9caaa8", **{"stroke-width": "1"}))
    elif element.tag == tag("g") and element.get("class") == "territory":
        islands = element.get("data-territory") == "mallorca"
        for path in element.findall(tag("path")):
            if islands:
                geography.append(copy_shape(path, fill="#df8884", stroke="#ad5d5a", **{"stroke-width": "0.8"}))
            else:
                mainland_paths.append(path.get("d"))
    elif element.get("data-peace") == "menorca":
        for path in element.findall(tag("path")):
            geography.append(copy_shape(path, fill="#df8884", stroke="#ad5d5a", **{"stroke-width": "0.8"}))

ET.SubElement(geography, tag("path"), {
    "d": " ".join(mainland_paths), "fill": "#8bb4d3", "fill-rule": "evenodd",
    "stroke": "#8bb4d3", "stroke-width": "1"
})

canarias = root.find(".//*[@id='canarias']")
islands = ET.parse(ROOT / "assets/documentos/mapa-desamortizacion-madoz-vector-2009.svg").getroot()
for polygon in islands.iter(tag("polygon")):
    if polygon.get("data-province") in ("Las Palmas", "Santa Cruz de Tenerife"):
        canarias.append(copy_shape(polygon, fill="#df8884", stroke="#ad5d5a", **{"stroke-width": "0.8"}))

output = ROOT / "assets/documentos/mapa-ocupacion-francesa-1808-1814.svg"
output.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
