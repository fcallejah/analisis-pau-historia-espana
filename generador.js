/* Banco de cuestiones: [enunciado, puntos clave, años PAU]. Mezcla los ejemplos de los apuntes
   del autor (sin años) con los enunciados literales de la PAU 2017-2026 del corpus
   (data/preguntas-cortas.json). Los puntos clave de las preguntas PAU de los bloques 1-3 se han
   redactado a partir de los apuntes; el bloque 4 no tiene soluciones hasta recibir sus apuntes. */
const FICHAS = {
 "1": [
  [
   "Defina el concepto de Paleolítico y explique las características fundamentales de la prehistoria en la península ibérica durante este período.",
   "cronología, economía depredadora, nomadismo, herramientas líticas, arte rupestre, enterramientos",
   ""
  ],
  [
   "¿Qué cueva cántabra es considerada una de las cumbres del arte del Paleolítico? Explique las diferencias entre el arte rupestre cantábrico y el arte rupestre levantino.",
   "Altamira; estilo cantábrico: Paleolítico, interior de cuevas, policromado, realismo, animales; estilo levantino: Mesolítico y Neolítico, abrigos rocosos, monocromo, esquematismo, figuras humanas.",
   ""
  ],
  [
   "Defina el concepto de Neolítico y explique las diferencias entre la economía depredadora y la economía productora.",
   "domesticación, agricultura, sedentarismo, división del trabajo, trueque, cerámica, megalitismo",
   ""
  ],
  [
   "Explique brevemente las diferencias entre la economía y la organización social del Paleolítico y el Neolítico.",
   "caza y recolección vs. agricultura y ganadería; nomadismo vs. sedentarismo; sociedad igualitaria vs. incipiente jerarquización social",
   ""
  ],
  [
   "¿En qué época se desarrolló el megalitismo? Explique en qué consistió la Edad de los Metales en la península ibérica y mencione algunos yacimientos representativos.",
   "Neolítico, Edad del Cobre, Edad del Bronce, Edad del Hierro; Los Millares, El Argar",
   ""
  ],
  [
   "¿A qué cultura pertenece la Dama de Baza? Explique las características generales de los pueblos autóctonos prerromanos de la península ibérica.",
   "íberos, celtas, celtíberos, tartésicos; organización social, economía, arte, lengua",
   ""
  ],
  [
   "¿Qué cultura prerromana se desarrolló en el valle del Guadalquivir? Describa brevemente las causas y el impacto de las colonizaciones fenicia y griega en la península ibérica.",
   "tartésica; comercio, escritura, olivo, moneda, arte, influencias culturales, avances tecnológicos",
   ""
  ],
  [
   "Explique qué pueblos colonizaron la península ibérica antes de la llegada de Roma y sus características principales.",
   "fenicios, griegos, cartagineses; asentamientos, actividades económicas, aportaciones culturales",
   ""
  ],
  [
   "¿Quiénes se enfrentaron en las guerras púnicas? Explique qué fue este conflicto y su importancia en la Edad Antigua de la península ibérica.",
   "Roma vs. Cartago; 264-146 a.C.; causas, desarrollo, consecuencias para la península",
   ""
  ],
  [
   "Explique en cuántas etapas se produjo la conquista romana de la península ibérica y qué territorios se ocuparon en cada una de ellas.",
   "218-19 a.C.; etapas: este y sur, centro, norte; resistencia de lusitanos, celtíberos, cántabros y astures",
   ""
  ],
  [
   "Defina el concepto de romanización y describa los instrumentos para llevarla a cabo.",
   "latín, derecho, religión, cristianismo, vías, ciudades, obras públicas, provincias",
   ""
  ],
  [
   "¿Qué dos grandes áreas culturales se dividían la península ibérica antes de la conquista romana? Explique las principales diferencias en el grado de desarrollo sociopolítico y económico entre ambas zonas.",
   "área ibérica vs. área celta; urbanización, escritura, moneda, economía agraria vs. ganadera",
   ""
  ],
  [
   "¿Qué nombre dieron los romanos a la península ibérica? Describa las características fundamentales de la economía de la Hispania romana.",
   "Hispania; economía esclavista y colonial; tríada mediterránea; minería (oro, plata, cobre); exportación de salazones/”garum”, aceite; moneda",
   ""
  ],
  [
   "¿Qué monarquía germánica se estableció en la península ibérica en el siglo VI? Explique brevemente las características principales de este reino y cuál fue su final.",
   "Visigodos; Toledo; debilidad por monarquía electiva; entrada de musulmanes en 711 y batalla de Guadalete",
   ""
  ],
  [
   "¿A qué monarquía perteneció el rey Leovigildo? Explique las características del proceso de unificación territorial, religioso y legislativo de este reino.",
   "monarquía visigoda; Leovigildo: unificación territorial; Recaredo: III, catolicismo; Recesvinto: Liber Iudiciorum; mezcla cultural con hispanorromanos y ruralización",
   ""
  ],
  [
   "¿Qué monarquía reinaba en la península en el 711? Describa las causas de la invasión musulmana.",
   "monarquía visigoda; 711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2017"
  ],
  [
   "¿Qué monarquía precedió a la invasión musulmana? Explique las causas de dicha invasión y su rápida expansión en la península.",
   "monarquía visigoda; 711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2019"
  ],
  [
   "¿Qué monarquía precedió a la invasión musulmana? Explique brevemente qué evolución política siguió el islam peninsular hasta los denominados reinos de taifas (711-1031).",
   "monarquía visigoda; emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2020, 2021, 2024"
  ],
  [
   "¿Qué monarquía precedió a la invasión musulmana? Explique brevemente las causas de la invasión musulmana y su rápida expansión por la península.",
   "monarquía visigoda; 711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2022"
  ],
  [
   "Indique y explique cuáles fueron las culturas autóctonas existentes en la península ibérica antes de la llegada de los romanos.",
   "íberos, celtas, celtíberos, tartésicos; organización social, economía, arte, lengua",
   "PAU 2026"
  ],
  [
   "¿Quiénes fueron los iberos? Cita algunas características de este conjunto de pueblos.",
   "pueblo prerromano del área ibérica (este y sur); urbanización, escritura, moneda, economía agraria; arte (Dama de Baza)",
   "PAU 2026"
  ],
  [
   "Define el concepto de romanización y describe los instrumentos para llevarla a cabo.",
   "latín, derecho, religión, cristianismo, vías, ciudades, obras públicas, provincias",
   "PAU 2026"
  ],
  [
   "¿Qué pueblo logró dominar la península ibérica tras la caída del Imperio romano de Occidente? Menciona los rasgos más relevantes de su organización política.",
   "visigodos; monarquía electiva con capital en Toledo; Leovigildo (unificación territorial); Recaredo (catolicismo); Recesvinto (Liber Iudiciorum); mezcla con hispanorromanos",
   "PAU 2026"
  ]
 ],
 "2": [
  [
   "¿En qué año se produjo la invasión musulmana de la península ibérica y en qué batalla fue derrotado el último rey visigodo? Explique brevemente las causas de la rápida ocupación y el nacimiento de al-Ándalus.",
   "711; batalla de Guadalete; Rodrigo; debilidad visigoda por luchas internas; concepto de al-Ándalus",
   ""
  ],
  [
   "¿Qué monarca proclamó el califato de Córdoba en el año 929? Describa brevemente la evolución política de al-Ándalus desde su creación hasta el siglo XI.",
   "Abderramán III; emirato dependiente de Damasco; emirato independiente de Córdoba; califato; cénit andalusí; fragmentación en reinos de taifas en 1031",
   ""
  ],
  [
   "¿Qué nombre recibían los cristianos que mantuvieron su religión en territorio musulmán a cambio de pagar impuestos? Explique brevemente la organización social de al-Ándalus.",
   "mozárabes; muladíes como hispanorromanos/visigodos conversos al islam; coexistencia de tres religiones",
   ""
  ],
  [
   "¿Qué caudillo militar musulmán destacó a finales del siglo X por sus devastadoras campañas de saqueo contra los reinos cristianos? Explique el final del califato y la llegada de los imperios norteafricanos.",
   "Almanzor; razias; debilidad andalusí; reinos de taifas; auxilio a almorávides y almohades",
   ""
  ],
  [
   "¿Qué reino musulmán logró sobrevivir en la península ibérica hasta 1492? Describa brevemente el legado cultural, científico y económico de al-Ándalus.",
   "reino nazarí de Granada; huerta y producción textil; matemáticas, filosofía, astronomía; preservación del saber clásico; toponimia; Alhambra y Mezquita",
   ""
  ],
  [
   "¿Qué victoria cristiana en el año 1212 supuso el principio del fin de la presencia musulmana en la Península? Explique el concepto de Reconquista y mencione el origen de los primeros núcleos de resistencia cristiana.",
   "Navas de Tolosa; justificación ideológica de recuperar la Hispania visigoda; reino asturleonés, Navarra, Aragón, condados catalanes",
   ""
  ],
  [
   "¿Qué nombre recibe el proceso de ocupación y colonización de las tierras conquistadas a los musulmanes por los reinos cristianos? Describa los principales modelos aplicados en este proceso según la zona.",
   "repoblación; presura en el norte; concejil en Duero/Ebro; órdenes militares en Mancha/Extremadura; repartimientos en el Guadalquivir",
   ""
  ],
  [
   "¿Qué institución fundó Alfonso X en 1273 para organizar a los pastores y ganaderos de Castilla? Explique la importancia de la ganadería y el comercio en los reinos cristianos.",
   "Honrado Concejo de la Mesta; trashumancia; supervivencia económica por la guerra; banca; expansión atlántica castellana y mediterránea aragonesa",
   ""
  ],
  [
   "¿Qué asambleas políticas nacidas en la Edad Media reunían al rey con representantes de la nobleza, el clero y las ciudades? Explique el desarrollo de las principales instituciones de gobierno cristianas.",
   "Cortes; antecedente en las Curias Regias; Cortes de León de 1188; creación de concejos o ayuntamientos",
   ""
  ],
  [
   "¿Qué rey fundó la Escuela de Traductores de Toledo y promulgó el código legislativo de las Siete Partidas? Explique brevemente las principales vías de desarrollo cultural en los reinos cristianos durante la Edad Media.",
   "Alfonso X; Escuela de Traductores de Toledo -intercambio entre árabe, hebreo, latín y castellano-; Siete Partidas -derecho romano unificado-; universidades como Salamanca; Camino de Santiago; arte románico, gótico y mudéjar",
   ""
  ],
  [
   "¿Qué personaje histórico adoptó el título de califa en Córdoba durante el siglo X? Describa el legado cultural y económico de al-Ándalus.",
   "Abderramán III en el año 929 (príncipe de los creyentes). Para la economía: cultivos de huerta, textil, cuero y comercio. Para la ciencia y cultura: idioma, toponimia, astronomía, medicina, matemáticas, filosofía, y la labor de preservación del saber griego, latino, persa e hindú. Para el arte: Mezquita de Córdoba, Alhambra de Granada o Alcazaba de Málaga",
   "PAU 2018, 2020"
  ],
  [
   "¿Qué nombre reciben los componentes de la minoría cristiana de al-Andalus? Explique las causas de la invasión musulmana y su rápida expansión en la península.",
   "Para la minoría cristiana: mozárabes (cristianos en territorio musulmán). Para las causas y expansión: crisis y debilidad del reino visigodo por luchas internas, año 711, batalla de Guadalete y derrota del rey Rodrigo",
   "PAU 2020"
  ],
  [
   "¿Dónde estuvo la capital de Al-Ándalus durante la época califal? Explique brevemente el origen y expansión de Al-Ándalus.",
   "Córdoba; 711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2017"
  ],
  [
   "¿Durante qué reinado se produjo el final de la Reconquista? Explique brevemente qué se entiende históricamente por Reconquista.",
   "reinado de los Reyes Católicos (1492); avance cristiano hacia el sur justificado como recuperación del antiguo reino visigodo (idea de Alfonso III de Asturias); desde Covadonga (722) hasta la toma de Granada (1492); Navas de Tolosa (1212) como punto de inflexión",
   "PAU 2017"
  ],
  [
   "¿Qué cronología, en siglos, abarca el proceso de Reconquista? Defina brevemente el concepto de repoblación.",
   "siglos VIII-XV (722-1492); ocupación de los territorios conquistados; presura (Duero y Miño, minifundios); repoblación concejil (Tajo y Ebro, fueros y cartas puebla); órdenes militares (La Mancha y Extremadura, latifundios); repartimientos (Guadalquivir)",
   "PAU 2017"
  ],
  [
   "¿Cómo se denominó la asociación de ganaderos de León y Castilla creada por Alfonso X el Sabio? Describa brevemente en qué consistía dicha asociación.",
   "Honrado Concejo de la Mesta; Honrado Concejo de la Mesta, creado por Alfonso X en 1273; asociación de pastores y ganaderos trashumantes de la Corona de Castilla; peso de la ganadería ovina",
   "PAU 2017, 2018"
  ],
  [
   "¿Dónde se situaron los primeros núcleos de resistencia cristiana al islam en España? Defina brevemente el concepto de Reconquista.",
   "norte peninsular: reino astur (Covadonga, Pelayo, cornisa cantábrica), reino de Pamplona (Navarra), Aragón y Marca Hispánica (condado de Barcelona); avance cristiano hacia el sur justificado como recuperación del antiguo reino visigodo (idea de Alfonso III de Asturias); desde Covadonga (722) hasta la toma de Granada (1492); Navas de Tolosa (1212) como punto de inflexión",
   "PAU 2017"
  ],
  [
   "¿Quién fue el primer califa omeya de Córdoba? Describa la evolución política del califato de Córdoba.",
   "Abderramán III (929); emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2017"
  ],
  [
   "¿Qué rey castellano impulsó la actividad cultural en la Edad Media a través de la Escuela de Traductores de Toledo? Describa brevemente la importancia de dicha institución.",
   "Alfonso X; Alfonso X; Escuela de Traductores de Toledo: intercambio cultural entre árabe, hebreo, latín y castellano; el castellano como lengua de traducción",
   "PAU 2018, 2019"
  ],
  [
   "¿Dónde se situaron geográficamente los primeros núcleos de resistencia cristiana al islam en España? Defina brevemente el concepto de Reconquista.",
   "norte peninsular: reino astur (Covadonga, Pelayo, cornisa cantábrica), reino de Pamplona (Navarra), Aragón y Marca Hispánica (condado de Barcelona); avance cristiano hacia el sur justificado como recuperación del antiguo reino visigodo (idea de Alfonso III de Asturias); desde Covadonga (722) hasta la toma de Granada (1492); Navas de Tolosa (1212) como punto de inflexión",
   "PAU 2018"
  ],
  [
   "¿Qué nombre reciben los componentes de la minoría cristiana de Al-Ándalus? Explica los rasgos principales de la sociedad hispano-musulmana.",
   "mozárabes; minoría musulmana gobernante; muladíes (cristianos convertidos al islam); mozárabes (cristianos que mantienen su religión pagando impuestos); minoría judía; coexistencia de tres religiones",
   "PAU 2018, 2019"
  ],
  [
   "¿Qué reino surgido a finales del siglo VIII se consolida como primer núcleo político relevante del proceso conocido como Reconquista? Defina brevemente dicho concepto.",
   "reino astur (Asturias); avance cristiano hacia el sur justificado como recuperación del antiguo reino visigodo (idea de Alfonso III de Asturias); desde Covadonga (722) hasta la toma de Granada (1492); Navas de Tolosa (1212) como punto de inflexión",
   "PAU 2019, 2020"
  ],
  [
   "¿Qué término acuñado por los cristianos define el enfrentamiento de larga duración que mantuvieron estos y musulmanes hasta 1492? Explique brevemente el ámbito territorial y carácter de cada sistema de repoblación, así como sus causas y consecuencias.",
   "Reconquista; ocupación de los territorios conquistados; presura (Duero y Miño, minifundios); repoblación concejil (Tajo y Ebro, fueros y cartas puebla); órdenes militares (La Mancha y Extremadura, latifundios); repartimientos (Guadalquivir)",
   "PAU 2019"
  ],
  [
   "¿Qué sector productivo aglutinó La Mesta? Indique en qué reinado se instauró y describa brevemente en qué consistía dicha asociación.",
   "ganadería ovina; Honrado Concejo de la Mesta, creado por Alfonso X en 1273; asociación de pastores y ganaderos trashumantes de la Corona de Castilla; peso de la ganadería ovina",
   "PAU 2019"
  ],
  [
   "¿Qué estamento o grupo social logra representación en las Cortes medievales, además de la alta nobleza y el clero? Explique el origen de las Cortes en los reinos cristianos y sus principales funciones.",
   "burguesía de las ciudades (tercer estamento); origen en las Curias Regias (nobles y eclesiásticos que asesoraban al rey); con los representantes de las ciudades pasan a ser Cortes; Cortes de León de 1188; asesoran al rey (consultivas en Castilla, pactistas en Aragón)",
   "PAU 2020, 2022"
  ],
  [
   "¿Qué asociación aglutinó a los ganaderos durante la Edad Media? Indique en qué reinado se instauró y describa brevemente en qué consistía dicha asociación.",
   "Mesta; Honrado Concejo de la Mesta, creado por Alfonso X en 1273; asociación de pastores y ganaderos trashumantes de la Corona de Castilla; peso de la ganadería ovina",
   "PAU 2020, 2021, 2023, 2024"
  ],
  [
   "¿Durante qué reinado se produjo la conquista del reino nazarí de Granada? Explique brevemente la política de unidad religiosa de dicho reinado.",
   "Reyes Católicos; Inquisición (1478); expulsión de los judíos (1492); conversiones forzosas de musulmanes (1502, moriscos); búsqueda de la unanimidad religiosa",
   "PAU 2021"
  ],
  [
   "¿Qué reino surgido a finales del siglo VIII en el norte peninsular se consolida como primer núcleo político relevante del proceso conocido como Reconquista? Explique brevemente dicho concepto.",
   "reino astur; avance cristiano hacia el sur justificado como recuperación del antiguo reino visigodo (idea de Alfonso III de Asturias); desde Covadonga (722) hasta la toma de Granada (1492); Navas de Tolosa (1212) como punto de inflexión",
   "PAU 2021"
  ],
  [
   "¿Qué estamento o grupo social logra representación en las Cortes medievales además de la alta nobleza y el clero? Explica el origen de las Cortes en los reinos cristianos y sus principales funciones.",
   "ciudades; origen en las Curias Regias (nobles y eclesiásticos que asesoraban al rey); con los representantes de las ciudades pasan a ser Cortes; Cortes de León de 1188; asesoran al rey (consultivas en Castilla, pactistas en Aragón)",
   "PAU 2021, 2023, 2026"
  ],
  [
   "¿Qué nombre dieron los musulmanes al territorio conquistado en la península ibérica a partir del año 711? Explique brevemente las causas de la invasión musulmana y su rápida expansión por la península.",
   "al-Ándalus; 711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2021, 2023, 2026"
  ],
  [
   "¿Qué título adoptó Abderramán III en Córdoba durante el siglo X? Describa el legado cultural y económico de Al-Ándalus.",
   "Abderramán III (califa); lengua y toponimia; cultivos de huerta, textil, cuero y comercio; astronomía, medicina, matemáticas y filosofía; preservación del saber griego, latino, persa e hindú; Mezquita de Córdoba, Alhambra, alcazaba de Málaga",
   "PAU 2021, 2022"
  ],
  [
   "¿Durante qué reinado se produjo la conquista del reino nazarí de Granada? Explique brevemente la expansión territorial realizada durante dicho reinado.",
   "Reyes Católicos; Granada (1492) y Navarra; Canarias y Melilla; Aragón hacia el Mediterráneo (Sicilia, Cerdeña, Nápoles); Castilla hacia el Atlántico y el norte de África; América (1492); alianzas matrimoniales",
   "PAU 2022, 2023, 2024, 2026"
  ],
  [
   "¿Qué nombre dieron los musulmanes al territorio conquistado en la península ibérica a partir del año 711? Explique brevemente qué evolución política siguió el islam peninsular hasta los denominados reinos de taifas (711-1031).",
   "al-Ándalus; emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2022, 2023"
  ],
  [
   "¿Qué nombre reciben los componentes de la minoría cristiana de Al-Ándalus? Explique los rasgos principales de la sociedad hispano-musulmana.",
   "mozárabes; minoría musulmana gobernante; muladíes (cristianos convertidos al islam); mozárabes (cristianos que mantienen su religión pagando impuestos); minoría judía; coexistencia de tres religiones",
   "PAU 2022"
  ],
  [
   "¿Dónde se situaron los primeros núcleos de resistencia al islam en España? Defina brevemente el concepto de repoblación.",
   "norte peninsular: reino astur (Covadonga, Pelayo, cornisa cantábrica), reino de Pamplona (Navarra), Aragón y Marca Hispánica (condado de Barcelona); ocupación de los territorios conquistados; presura (Duero y Miño, minifundios); repoblación concejil (Tajo y Ebro, fueros y cartas puebla); órdenes militares (La Mancha y Extremadura, latifundios); repartimientos (Guadalquivir)",
   "PAU 2022"
  ],
  [
   "¿Qué término acuñado por los cristianos define el enfrentamiento de larga duración que mantuvieron estos y los musulmanes hasta 1492? Explique brevemente el ámbito territorial y carácter de cada sistema de repoblación, así como sus causas y consecuencias.",
   "Reconquista; ocupación de los territorios conquistados; presura (Duero y Miño, minifundios); repoblación concejil (Tajo y Ebro, fueros y cartas puebla); órdenes militares (La Mancha y Extremadura, latifundios); repartimientos (Guadalquivir)",
   "PAU 2023"
  ],
  [
   "¿Quién ostentó por primera vez el título del califa en Córdoba durante el siglo X? Describa el legado cultural y económico de Al-Ándalus.",
   "Abderramán III (929); lengua y toponimia; cultivos de huerta, textil, cuero y comercio; astronomía, medicina, matemáticas y filosofía; preservación del saber griego, latino, persa e hindú; Mezquita de Córdoba, Alhambra, alcazaba de Málaga",
   "PAU 2023, 2024"
  ],
  [
   "¿Qué estamentos o grupos sociales tuvieron representación en las Cortes medievales? Explique el origen de las Cortes en los reinos cristianos y sus principales funciones.",
   "nobleza, clero y ciudades; origen en las Curias Regias (nobles y eclesiásticos que asesoraban al rey); con los representantes de las ciudades pasan a ser Cortes; Cortes de León de 1188; asesoran al rey (consultivas en Castilla, pactistas en Aragón)",
   "PAU 2024"
  ],
  [
   "¿Qué nombre dieron los musulmanes al territorio conquistado en la península ibérica a partir del año 711? Explique brevemente qué evolución política siguió el islam hasta los denominados reinos de taifas (1031).",
   "al-Ándalus; emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2024"
  ],
  [
   "¿Qué nombre dieron los musulmanes al territorio conquistado en la península ibérica a partir del año 711? Explique brevemente las etapas de la dominación musulmana en la península.",
   "al-Ándalus; emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2024"
  ],
  [
   "Establezca las diferencias entre un mozárabe y un mudéjar.",
   "mozárabe: cristiano bajo dominio musulmán que mantiene su religión pagando impuestos; mudéjar: musulmán bajo dominio cristiano que mantiene su religión pagando impuestos; muladíes y moriscos (1502) son los que cambian de religión",
   "PAU 2025"
  ],
  [
   "Precise brevemente cuáles fueron las etapas de la dominación musulmana en la península.",
   "emirato dependiente de Damasco (711-756); emirato independiente de Córdoba (756-929); califato de Córdoba (929-1031) con Abderramán III y el cénit andalusí; fragmentación en reinos de taifas (1031); después, almorávides, almohades y reino nazarí de Granada hasta 1492",
   "PAU 2025"
  ],
  [
   "¿Cuándo surge y qué es el Honrado Concejo de la Mesta?",
   "Alfonso X, 1273; Honrado Concejo de la Mesta, creado por Alfonso X en 1273; asociación de pastores y ganaderos trashumantes de la Corona de Castilla; peso de la ganadería ovina",
   "PAU 2026"
  ],
  [
   "¿Cuándo se produce la invasión de la península ibérica por parte de los musulmanes? ¿Qué factores explican la rapidez en la conquista?",
   "711; batalla de Guadalete; derrota de Rodrigo, último rey visigodo; debilidad del reino visigodo por sus luchas internas; nacimiento de al-Ándalus",
   "PAU 2026"
  ]
 ],
 "3": [
  [
   "¿Qué monarcas iniciaron a finales del siglo XV la unión dinástica de los reinos peninsulares? Explique brevemente en qué consistió dicha unión.",
   "Isabel I de Castilla y Fernando II de Aragón; matrimonio en 1469; unión dinástica pero no institucional; cada corona mantiene sus propias leyes, moneda, Cortes e instituciones; creación de la Monarquía Hispánica",
   ""
  ],
  [
   "¿Qué rey de la Monarquía Hispánica fue también emperador del Sacro Imperio Romano Germánico? Explique brevemente los conflictos políticos internos que se produjeron en su reinado.",
   "Carlos I de España y V de Alemania; revuelta de las Comunidades de Castilla -comuneros, oligarquías urbanas-; revuelta de las Germanías en Valencia y Mallorca -carácter social, artesanos contra nobleza-; ambas en 1520",
   ""
  ],
  [
   "¿Qué valido del rey Felipe IV propuso el proyecto de la Unión de Armas? Explique brevemente los principales hitos políticos y problemas económicos.",
   "el conde-duque de Olivares; vuelta a una política exterior agresiva -guerra de los Treinta Años-; grave crisis política de 1640 provocada por la centralización de la Unión de Armas -rebeliones de Cataluña y Portugal-; hundimiento económico causado por el inmenso gasto militar, suspensiones de pagos -bancarrotas-, subida de impuestos y devaluación con la moneda de vellón",
   ""
  ],
  [
   "¿En qué reinado tuvo lugar la derrota de la “Armada Invencible”? Explique brevemente las líneas maestras de la política exterior de este monarca.",
   "reinado de Felipe II; defensa a ultranza del catolicismo frente al protestantismo -Contrarreforma-; mantenimiento de la hegemonía hispánica; enfrentamientos con Francia -San Quintín-, Imperio otomano -Lepanto-, Inglaterra e independentistas de Flandes; logró la Unión Ibérica en 1580",
   ""
  ],
  [
   "¿Qué nombre reciben los monarcas del siglo XVII que delegaron las tareas de gobierno en validos? Explique brevemente en qué consistía la figura del valido.",
   "Austrias Menores -Felipe III, Felipe IV y Carlos II-; el valido o privado era un ministro de máxima confianza del rey, perteneciente a la alta nobleza, que actuaba como primer ministro y tomaba las principales decisiones políticas; ejemplos: duque de Lerma, conde-duque de Olivares",
   ""
  ],
  [
   "¿Durante qué reinado se produjo la expulsión de los moriscos? Explique brevemente las consecuencias demográficas y económicas de esta medida.",
   "reinado de Felipe III, año 1609; grave pérdida demográfica de unas 300 000 personas; duras consecuencias económicas especialmente para la agricultura de regadío en la Corona de Aragón -Valencia y Aragón- al perder gran parte de su mano de obra campesina",
   ""
  ],
  [
   "¿Qué valido del rey Felipe IV dirigió la política española durante la guerra de los Treinta Años? Explique brevemente en qué consistió su proyecto de la Unión de Armas.",
   "el Conde-Duque de Olivares; propuesta de 1626 para que todos los reinos de la Monarquía Hispánica, y no solo Castilla, aportaran hombres y dinero para la guerra en proporción a su riqueza y población; chocaba con los fueros de los distintos reinos y provocó la Crisis de 1640",
   ""
  ],
  [
   "¿Qué dos grandes rebeliones estallaron en 1640 contra la política centralizadora del conde-duque de Olivares? Explique brevemente el desenlace de ambas.",
   "la rebelión de Cataluña y la de Portugal; Cataluña acabó rindiéndose y reincorporándose a la Monarquía Hispánica conservando sus fueros; Portugal inició una larga guerra que culminaría con su independencia definitiva coronando a la casa de Braganza",
   ""
  ],
  [
   "¿Qué monarca fue el último representante de la dinastía de los Austrias en España? Explique brevemente el problema sucesorio que se generó a su muerte.",
   "Carlos II “el Hechizado”; muerte sin descendencia en 1700; testamento a favor de Felipe de Anjou -Borbón- frente a las reclamaciones del archiduque Carlos de Austria -Habsburgo-; provocó el estallido de la guerra de sucesión, con dimensión civil e internacional",
   ""
  ],
  [
   "¿Qué dos monarcas de la Casa de Austria reinaron tras los Reyes Católicos durante casi todo el siglo XVI? Explique brevemente las características de la hegemonía española en el mundo.",
   "Carlos I de España y su hijo Felipe II -Austrias Mayores-; creación del mayor imperio territorial de la época abarcando dominios en Europa, América, África y Asia; asunción de la defensa de la fe católica frente a los protestantes y el Imperio otomano; inmenso desgaste militar y financiero provocado por las continuas guerras de religión y hegemonía que derivó en sucesivas bancarrotas",
   "PAU 2017"
  ],
  [
   "¿Durante qué reinado se produjo el final de la Reconquista? Explique brevemente la política exterior de dicho reinado.",
   "reinado de los Reyes Católicos; expansión atlántica -América y Canarias- y mediterránea -Nápoles-; sistema de alianzas matrimoniales con Inglaterra, el papado y el Sacro Imperio Romano Germánico diseñado para aislar a Francia, su principal rival; establecimiento de embajadores permanentes en las cortes europeas, sentando las bases del Estado moderno",
   "PAU 2018, 2019, 2020"
  ],
  [
   "¿En qué reinado tuvo lugar la batalla de Lepanto? Explique brevemente la política exterior de la Monarquía Hispánica en ese reinado.",
   "reinado de Felipe II; política basada en el mantenimiento de la hegemonía hispánica y la defensa a ultranza del catolicismo -Contrarreforma-; freno a los turcos en el Mediterráneo -Lepanto en 1571-; enfrentamientos contra Inglaterra -Armada Invencible- y contra Francia -San Quintín-; rebelión protestante e independentista de los Países Bajos; logró la incorporación del reino de Portugal -Unión Ibérica en 1580-",
   "PAU 2018"
  ],
  [
   "¿Qué monarca del siglo XVI tiene que afrontar las sublevaciones de las “Comunidades” y las “Germanías”? Explique brevemente los conflictos políticos más relevantes de la etapa de los Austrias Mayores en la península ibérica.",
   "Carlos I; durante su reinado estallan las Comunidades en Castilla -revuelta de carácter político de las oligarquías urbanas contra el entorno extranjero del rey- y las Germanías en la Corona de Aragón -revuelta de carácter social de los artesanos contra la nobleza-; durante el reinado de Felipe II destacan la rebelión de los moriscos de las Alpujarras y las alteraciones de Aragón en defensa de sus fueros tras el caso de Antonio Pérez",
   "PAU 2019"
  ],
  [
   "¿Qué comunidades religiosas fueron expulsadas de Castilla y Aragón entre 1492 y 1502, respectivamente? Explique brevemente la política de unidad religiosa de los Reyes Católicos.",
   "expulsión de los judíos en 1492 y conversión forzosa de los musulmanes en 1502 -dando origen a los moriscos-; objetivo de utilizar la religión católica como instrumento para unificar política y socialmente los reinos de la monarquía; creación del Tribunal de la Santa Inquisición en 1478 para vigilar la ortodoxia y perseguir a los falsos conversos; generó graves pérdidas demográficas, económicas y culturales",
   "PAU 2019"
  ],
  [
   "¿En qué siglo se produce la toma de Granada por los Reyes Católicos? Describa brevemente por qué es importante en el mundo este acontecimiento.",
   "siglo XV (1492); fin de al-Ándalus y de la Reconquista; mismo año: Colón llega a América y se expulsa a los judíos",
   "PAU 2017"
  ],
  [
   "¿Qué reyes efectuaron la unión dinástica en España a finales del siglo XV? Explique brevemente la expansión territorial realizada por dichos monarcas.",
   "Isabel de Castilla y Fernando de Aragón (Reyes Católicos); matrimonio en 1469; unión dinástica (Isabel 1474, Fernando 1479); cada territorio conserva sus leyes e instituciones; nace la Monarquía Hispánica; Granada (1492) y Navarra; Canarias y Melilla; Aragón hacia el Mediterráneo (Sicilia, Cerdeña, Nápoles); Castilla hacia el Atlántico y el norte de África; América (1492); alianzas matrimoniales",
   "PAU 2017, 2021"
  ],
  [
   "Cite el nombre de algún valido Defina brevemente a qué se refiere el término “gobierno de los validos”.",
   "el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2017"
  ],
  [
   "¿Qué rey de España fue también emperador en Europa en la Edad Moderna? Describa brevemente en qué territorios se asentaba la monarquía española en ese reinado y qué pasó a la muerte del emperador.",
   "Carlos I; Castilla y América, Corona de Aragón y Mediterráneo, y herencia borgoñona y austríaca (Países Bajos, Flandes, Austria, título imperial); a su muerte Felipe II hereda todo salvo el Sacro Imperio y Austria",
   "PAU 2017"
  ],
  [
   "¿Qué rey de España fue también emperador en Europa en la Edad Moderna? Explique brevemente las características de la política exterior de dicho monarca.",
   "Carlos I; Universitas Christiana; enemigos: Francia, Imperio otomano y protestantismo; Paz de Augsburgo (1555); abdicación en 1556",
   "PAU 2018"
  ],
  [
   "¿Qué reyes efectuaron la unión dinástica entre las coronas de Castilla y Aragón a finales del siglo XV? Explique brevemente la expansión territorial realizada por dichos monarcas.",
   "Isabel de Castilla y Fernando de Aragón (Reyes Católicos); matrimonio en 1469; unión dinástica (Isabel 1474, Fernando 1479); cada territorio conserva sus leyes e instituciones; nace la Monarquía Hispánica; Granada (1492) y Navarra; Canarias y Melilla; Aragón hacia el Mediterráneo (Sicilia, Cerdeña, Nápoles); Castilla hacia el Atlántico y el norte de África; América (1492); alianzas matrimoniales",
   "PAU 2018"
  ],
  [
   "Cita uno de los validos del reinado de Felipe IV Explique en qué consiste la figura del valido y la importancia que tuvieron en el siglo XVII.",
   "conde-duque de Olivares; el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2018"
  ],
  [
   "¿Qué monarca del siglo XVI tiene que afrontar las sublevaciones de las “Comunidades” y las “Germanías”? Explique brevemente los conflictos políticos más relevantes de la etapa de los Austrias mayores (siglo XVI) en la península ibérica.",
   "Carlos I; con Carlos I, Comunidades de Castilla (1520, oligarquías urbanas) y Germanías en la Corona de Aragón (artesanos contra nobles); con Felipe II, rebelión de las Alpujarras (1568-1571) y alteraciones de Aragón (caso Antonio Pérez)",
   "PAU 2019, 2023, 2024"
  ],
  [
   "¿En qué reinado tuvo lugar la derrota de la “Armada Invencible”? Explique brevemente las diferencias de la política internacional de este monarca con la de su padre, Carlos I.",
   "Felipe II; defensa del catolicismo (Contrarreforma) y de la hegemonía hispánica; San Quintín (1557) y Lepanto (1571); Unión Ibérica con Portugal (1580); rebelión de Flandes; Armada Invencible (1588); bancarrotas; Carlos I: imperio europeo, Universitas Christiana y lucha contra Francia, otomanos y protestantes; Felipe II: imperio de base hispánica, capital en Madrid, Contrarreforma, Lepanto, Portugal (1580), Flandes y Armada Invencible",
   "PAU 2019, 2020, 2021, 2023"
  ],
  [
   "¿De qué monarca fue valido el Conde-Duque de Olivares? Explique brevemente al menos dos hechos relevantes ocurridos entre 1640 y 1659 que evidenciaron la decadencia de la monarquía hispánica.",
   "Felipe IV; crisis de 1640 (rebeliones de Cataluña y Portugal); Paz de Westfalia (1648, independencia de las Provincias Unidas); Paz de los Pirineos (1659, Francia gran potencia); bancarrotas",
   "PAU 2019, 2023"
  ],
  [
   "¿Qué monarcas iniciaron a finales del siglo XV la expansión atlántica? Explique brevemente su política de expansión hacia el Atlántico y de control del norte de África.",
   "Reyes Católicos; expansión atlántica (Canarias, América desde 1492, Tratado de Tordesillas en 1494) y control del norte de África (Melilla)",
   "PAU 2019"
  ],
  [
   "¿Qué monarca del siglo XVI tiene que afrontar las sublevaciones de las “Comunidades” y las “Germanías”? Explique brevemente los conflictos políticos más relevantes de la etapa de los Austrias mayores (siglo XVI) en la península.",
   "Carlos I; con Carlos I, Comunidades de Castilla (1520, oligarquías urbanas) y Germanías en la Corona de Aragón (artesanos contra nobles); con Felipe II, rebelión de las Alpujarras (1568-1571) y alteraciones de Aragón (caso Antonio Pérez)",
   "PAU 2020"
  ],
  [
   "¿De qué monarca fue valido el Conde-Duque de Olivares? Explique en qué consiste la figura del valido y la importancia que tuvieron en el siglo XVII.",
   "Felipe IV; el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2020"
  ],
  [
   "¿Qué rey de España fue también emperador en Europa en la Edad Moderna? Explique brevemente las características de la política exterior europea de dicho monarca.",
   "Carlos I; Universitas Christiana; enemigos: Francia, Imperio otomano y protestantismo; Paz de Augsburgo (1555); abdicación en 1556",
   "PAU 2020, 2024"
  ],
  [
   "¿Qué minoría social y religiosa fue expulsada de España en 1609? Explique brevemente la política de unidad religiosa realizada por los Reyes Católicos y la dinastía de los Austrias.",
   "moriscos (1609, Felipe III); Inquisición (1478); expulsión de los judíos (1492); conversiones forzosas de musulmanes (1502, moriscos); búsqueda de la unanimidad religiosa",
   "PAU 2020, 2022"
  ],
  [
   "¿Qué conflicto armado pone fin a la dinastía de los Austrias en España? Explique las causas de dicho conflicto.",
   "guerra de sucesión; Carlos II muere sin descendencia en 1700; testamento a favor de Felipe de Anjou (Borbón) frente al archiduque Carlos de Austria; guerra de sucesión (1701-1714), civil e internacional; fin de los Austrias y llegada de los Borbones",
   "PAU 2021, 2023, 2024, 2026"
  ],
  [
   "¿Qué monarca del siglo XVI tuvo que afrontar las sublevaciones de las “Comunidades” y las “Germanías”? Explique brevemente los conflictos políticos más relevantes de la etapa de los Austrias mayores (siglo XVI) en la península ibérica.",
   "Carlos I; con Carlos I, Comunidades de Castilla (1520, oligarquías urbanas) y Germanías en la Corona de Aragón (artesanos contra nobles); con Felipe II, rebelión de las Alpujarras (1568-1571) y alteraciones de Aragón (caso Antonio Pérez)",
   "PAU 2021"
  ],
  [
   "¿Por qué apelativo son conocidos los reyes Isabel I de Castilla y Fernando V de Aragón? Explique brevemente las características básicas de la monarquía autoritaria.",
   "Reyes Católicos; poder del rey reforzado; unión dinástica con instituciones propias en cada reino; Inquisición y unidad religiosa; expansión territorial y alianzas matrimoniales",
   "PAU 2021"
  ],
  [
   "¿Cómo se llama la figura política que se hizo cargo de las tareas de gobierno en lugar del rey durante el siglo XVII? Explique en qué consiste su figura y la importancia que tuvieron en dicho siglo.",
   "valido; el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2021"
  ],
  [
   "¿Qué reyes efectuaron la unión dinástica en España a finales del siglo XV? Explique brevemente la política de unidad religiosa de dicho reinado.",
   "Reyes Católicos; Inquisición (1478); expulsión de los judíos (1492); conversiones forzosas de musulmanes (1502, moriscos); búsqueda de la unanimidad religiosa",
   "PAU 2022"
  ],
  [
   "¿Por qué apelativo son conocidos los reyes Isabel I de Castilla y Fernando II de Aragón? Explique brevemente las características básicas de la monarquía autoritaria.",
   "Reyes Católicos; poder del rey reforzado; unión dinástica con instituciones propias en cada reino; Inquisición y unidad religiosa; expansión territorial y alianzas matrimoniales",
   "PAU 2022, 2023, 2026"
  ],
  [
   "¿Qué monarca del siglo XVI tuvo que afrontar la rebelión de las Alpujarras? Explique brevemente los conflictos políticos más relevantes de la etapa de los Austrias mayores (siglo XVI) en la península ibérica.",
   "Felipe II; con Carlos I, Comunidades de Castilla (1520, oligarquías urbanas) y Germanías en la Corona de Aragón (artesanos contra nobles); con Felipe II, rebelión de las Alpujarras (1568-1571) y alteraciones de Aragón (caso Antonio Pérez)",
   "PAU 2022, 2023, 2024"
  ],
  [
   "Cite el nombre de algún valido de los Austrias menores. Explique en qué consiste su figura y la importancia que tuvieron en el siglo XVII.",
   "duque de Lerma, conde-duque de Olivares; el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2022, 2024"
  ],
  [
   "¿Qué reyes españoles son conocidos por el apelativo de “católicos”? Explique brevemente las características básicas de la monarquía autoritaria.",
   "Reyes Católicos; poder del rey reforzado; unión dinástica con instituciones propias en cada reino; Inquisición y unidad religiosa; expansión territorial y alianzas matrimoniales",
   "PAU 2024"
  ],
  [
   "Explique brevemente las diferencias de la política internacional de Carlos I y Felipe II.",
   "Carlos I: imperio europeo, Universitas Christiana y lucha contra Francia, otomanos y protestantes; Felipe II: imperio de base hispánica, capital en Madrid, Contrarreforma, Lepanto, Portugal (1580), Flandes y Armada Invencible",
   "PAU 2025, 2026"
  ],
  [
   "Explique las razones del conflicto armado que puso fin a la dinastía de los Austrias en España y las consecuencias que tuvo.",
   "Carlos II muere sin descendencia en 1700; testamento a favor de Felipe de Anjou (Borbón) frente al archiduque Carlos de Austria; guerra de sucesión (1701-1714), civil e internacional; fin de los Austrias y llegada de los Borbones",
   "PAU 2025, 2026"
  ],
  [
   "Señale los dos monarcas de más amplio reinado en el siglo XVI y las diferencias en su política exterior.",
   "Carlos I y Felipe II; Carlos I: imperio europeo, Universitas Christiana y lucha contra Francia, otomanos y protestantes; Felipe II: imperio de base hispánica, capital en Madrid, Contrarreforma, Lepanto, Portugal (1580), Flandes y Armada Invencible",
   "PAU 2025, 2026"
  ],
  [
   "Explique la política de unidad religiosa de los Reyes Católicos.",
   "Inquisición (1478); expulsión de los judíos (1492); conversiones forzosas de musulmanes (1502, moriscos); búsqueda de la unanimidad religiosa",
   "PAU 2025"
  ],
  [
   "Explique brevemente los conflictos políticos más relevantes de la política interior de Carlos I.",
   "con Carlos I, Comunidades de Castilla (1520, oligarquías urbanas) y Germanías en la Corona de Aragón (artesanos contra nobles); con Felipe II, rebelión de las Alpujarras (1568-1571) y alteraciones de Aragón (caso Antonio Pérez)",
   "PAU 2025"
  ],
  [
   "Explique en qué consistió la figura del valido y la importancia que tuvo en el siglo XVII.",
   "el valido (o privado) es un ministro de máxima confianza del rey que actúa como primer ministro; Austrias Menores (Felipe III, Felipe IV, Carlos II); ejemplos: duque de Lerma, conde-duque de Olivares; contexto de decadencia política y económica",
   "PAU 2025"
  ],
  [
   "Explique la expansión territorial realizada durante el reinado de los Reyes Católicos.",
   "Granada (1492) y Navarra; Canarias y Melilla; Aragón hacia el Mediterráneo (Sicilia, Cerdeña, Nápoles); Castilla hacia el Atlántico y el norte de África; América (1492); alianzas matrimoniales",
   "PAU 2025"
  ]
 ],
 "4": [
  [
   "¿Con qué monarca comienza a reinar en España la Casa de Borbón a comienzos del siglo XVIII? Explique las causas de la guerra de sucesión española.",
   null,
   "PAU 2017"
  ],
  [
   "¿Con qué tratado se pone fin a la guerra de sucesión española? Explique brevemente las consecuencias de dicho tratado.",
   null,
   "PAU 2017"
  ],
  [
   "¿Qué dinastía reinaba en España cuando se promulgaron los decretos de Nueva Planta? Explique brevemente el contenido de los mismos y su importancia histórica.",
   null,
   "PAU 2017"
  ],
  [
   "¿A qué reinado corresponde el Motín de Esquilache? Defina el concepto de despotismo ilustrado.",
   null,
   "PAU 2017"
  ],
  [
   "¿Qué rey firmó los decretos de Nueva Planta? Explique brevemente en qué consistieron dichos decretos.",
   null,
   "PAU 2017, 2018, 2019"
  ],
  [
   "¿Con qué nombre se conoce la guerra entre Borbones y Austrias en su disputa por el trono de España? Describa brevemente por qué se produjo dicha guerra, qué países estuvieron implicados en ella y cuál fue su resultado.",
   null,
   "PAU 2017"
  ],
  [
   "¿Qué dinastía impulsó la creación de las reales fábricas en el siglo XVIII para el desarrollo industrial? Explique brevemente las reformas económicas emprendidas por los monarcas ilustrados.",
   null,
   "PAU 2018"
  ],
  [
   "¿Qué nueva dinastía comenzó a reinar en España a comienzos del siglo XVIII? Explique brevemente las causas de la guerra de sucesión española.",
   null,
   "PAU 2018"
  ],
  [
   "¿Qué tratado puso fin a la guerra de sucesión española? Explique brevemente las consecuencias de dicho tratado.",
   null,
   "PAU 2018, 2019, 2021"
  ],
  [
   "¿Qué nombre recibe la guerra entre Borbones y Austrias en su disputa por el trono de España? Describa brevemente por qué se produjo dicha guerra, qué países estuvieron implicados en ella y cuál fue su resultado.",
   null,
   "PAU 2018"
  ],
  [
   "¿Qué nueva dinastía comenzó a reinar en España con Felipe V? Explique brevemente qué es el despotismo ilustrado, rasgo definidor de esta dinastía en el siglo XVIII.",
   null,
   "PAU 2019"
  ],
  [
   "¿Qué nombre reciben los decretos que abolen los fueros de los territorios de la antigua Corona de Aragón? Explique brevemente las reformas en la Administración emprendidas bajo la dinastía borbónica a lo largo del siglo XVIII.",
   null,
   "PAU 2019"
  ],
  [
   "¿Cómo se conoce el modelo político del rey Carlos III? Explique brevemente las medidas reformistas llevadas a cabo durante su reinado.",
   null,
   "PAU 2019"
  ],
  [
   "¿Qué dinastía impulsó reformas en la agricultura en el siglo XVIII? Explique brevemente las medidas más relevantes emprendidas por los monarcas ilustrados.",
   null,
   "PAU 2019"
  ],
  [
   "¿Qué rey del siglo XVIII encarnó mejor el modelo del despotismo ilustrado en España? Explique brevemente las medidas reformistas llevadas a cabo durante su reinado.",
   null,
   "PAU 2020, 2021"
  ],
  [
   "¿Qué dinastía impulsó reformas en la agricultura en el siglo XVIII? Explique brevemente las medidas más relevantes emprendidas por los monarcas ilustrados para el desarrollo de esta actividad económica.",
   null,
   "PAU 2020, 2024"
  ],
  [
   "¿Qué monarca español firmó los tratados de Utrecht y Rastadt? Explique brevemente las consecuencias de dichos tratados para España.",
   null,
   "PAU 2020"
  ],
  [
   "¿Qué tratado puso fin a la guerra de sucesión española? Explique brevemente las causas de la guerra de sucesión española.",
   null,
   "PAU 2020"
  ],
  [
   "¿Qué dinastía reinaba en España durante el denominado siglo de las Luces? Explique el porqué de esta denominación y las características del movimiento ideológico y cultural al que hace referencia.",
   null,
   "PAU 2020"
  ],
  [
   "¿A qué dinastía perteneció el rey que firmó los decretos de Nueva Planta? Explique brevemente en qué consistieron dichos decretos.",
   null,
   "PAU 2020"
  ],
  [
   "¿A qué dinastía perteneció el rey Carlos III? Explique brevemente las medidas más relevantes emprendidas por los monarcas ilustrados para el desarrollo de la agricultura.",
   null,
   "PAU 2021"
  ],
  [
   "¿A qué dinastía perteneció el monarca español que firmó los tratados de Utrecht y Rastadt? Explique brevemente las causas de la guerra de sucesión española.",
   null,
   "PAU 2021, 2022"
  ],
  [
   "¿Qué nombre reciben los decretos que abolieron los fueros de los territorios de la antigua Corona de Aragón? Explique brevemente en qué consistieron dichos decretos.",
   null,
   "PAU 2021, 2022, 2024"
  ],
  [
   "¿Qué monarca español firmó los tratados de Utrecht y Rastadt? Explique brevemente las causas de la guerra que los originaron.",
   null,
   "PAU 2022, 2023"
  ],
  [
   "¿Tras qué conflicto armado iniciaron su reinado en España los Borbones a comienzos del siglo XVIII? Explique las consecuencias de dicho conflicto.",
   null,
   "PAU 2022, 2023"
  ],
  [
   "¿Qué tratados pusieron fin a la guerra de sucesión española? Explique brevemente las consecuencias de dicho tratado.",
   null,
   "PAU 2022"
  ],
  [
   "¿Qué dinastía reinaba en España durante el denominado siglo de las Luces? Explique el porqué de esta denominación y las características del movimiento ideológico y cultural al que hace referencia.",
   null,
   "PAU 2022"
  ],
  [
   "¿Qué nombre reciben los decretos que abolieron los fueros de los territorios de la antigua Corona de Aragón? Explique brevemente las causas de la guerra de sucesión española.",
   null,
   "PAU 2023"
  ],
  [
   "¿Cuál es el rey español más representativo del denominado siglo de las Luces? Explique el porqué de esta denominación y las características del movimiento ideológico y cultural al que hace referencia.",
   null,
   "PAU 2023"
  ],
  [
   "¿A qué dinastía perteneció el monarca español que firmó los tratados de Utrecht y Rastadt? Explique brevemente en qué consistieron dichos acuerdos.",
   null,
   "PAU 2023, 2024"
  ],
  [
   "¿Tras qué conflicto armado iniciaron su reinado en España los Borbones a comienzos del siglo XVIII? Explique las causas de dicho conflicto.",
   null,
   "PAU 2024"
  ],
  [
   "¿Con qué tratados concluyó la guerra que permitió la llegada de los Borbones a España a comienzos del siglo XVIII? Explique brevemente las causas de la guerra que los originaron.",
   null,
   "PAU 2024"
  ],
  [
   "Explique brevemente las medidas más relevantes emprendidas por los monarcas ilustrados para el desarrollo de la agricultura.",
   null,
   "PAU 2025"
  ],
  [
   "Explique las características del movimiento ideológico y cultural del conocido como el siglo de las Luces.",
   null,
   "PAU 2025"
  ],
  [
   "Explique brevemente por qué se hicieron y en qué consistieron los decretos que abolieron los fueros en la antigua Corona de Aragón a comienzos del siglo XVIII.",
   null,
   "PAU 2025"
  ],
  [
   "Explique brevemente cómo se llamaban, por qué se hicieron y en qué consistieron los decretos que abolieron los fueros en la antigua Corona de Aragón a comienzos del siglo XVIII.",
   null,
   "PAU 2026"
  ],
  [
   "¿Qué es el despotismo ilustrado? ¿Quién es considerado el principal monarca ilustrado de España y por qué?",
   null,
   "PAU 2026"
  ]
 ]
};


(() => {
  const root = document.getElementById("generador");
  if (!root) return;
  const out = root.querySelector("#gen-output");
  const status = root.querySelector("#gen-status");
  const buttons = root.querySelectorAll("[data-gen]");
  const shuffle = (a) => {
    const r = a.slice();
    for (let i = r.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [r[i], r[j]] = [r[j], r[i]]; }
    return r;
  };
  const all = Object.entries(FICHAS).flatMap(([b, list]) => list.map((f) => ({ b: Number(b), f })));
  const total = (mode) => (mode === "random" ? all.length : (FICHAS[mode] || []).length);
  const seen = new Set();
  const pick = (pool, n) => {
    let fresh = pool.filter((x) => !seen.has(x.f[0]));
    if (fresh.length < n) { pool.forEach((x) => seen.delete(x.f[0])); fresh = pool; }
    const chosen = shuffle(fresh).slice(0, n);
    chosen.forEach((x) => seen.add(x.f[0]));
    return chosen;
  };
  const render = (items, label) => {
    out.textContent = "";
    items.forEach((it, i) => {
      const art = document.createElement("article");
      art.className = "gen-q";
      const h = document.createElement("p");
      h.className = "gen-text";
      const num = document.createElement("strong");
      num.textContent = `${i + 1}. ${it.f[0]}`;
      h.append(num);
      const meta = document.createElement("small");
      meta.textContent = it.f[2] ? `Bloque ${it.b} · ${it.f[2]}` : `Bloque ${it.b}`;
      const exams = questionExamMap.get(questionKey(it.f[0]));
      if (exams) {
        meta.className = "gen-exams";
        meta.replaceChildren(document.createTextNode(`Bloque ${it.b} `), ...exams.map(examPill));
      }
      const det = document.createElement("details");
      det.className = "gen-sol";
      const sum = document.createElement("summary");
      sum.textContent = "Posible solución";
      const body = document.createElement("p");
      if (it.f[1]) {
        const b = document.createElement("strong");
        b.textContent = "Debe incluir: ";
        body.append(b, document.createTextNode(it.f[1].replace(/\.?$/, ".")));
      } else {
        body.textContent = "Todavía no hay solución: faltan los apuntes del bloque 4.";
      }
      det.append(sum, body);
      art.append(h, meta, det);
      appendErratum(art, it.f[0]);
      out.append(art);
    });
    status.textContent = `${label}: ${items.length} cuestiones generadas.`;
    const rb = root.querySelector("#gen-reset");
    const sel = root.querySelector('[data-gen][aria-pressed="true"]');
    sel.after(rb);
    rb.hidden = false;
    buttons.forEach((x) => { x.disabled = true; });
  };
  const generate = (mode) => {
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.gen === mode)));
    if (!total(mode)) {
      out.textContent = "";
      status.textContent = `Bloque ${mode}: todavía no hay cuestiones.`;
      return;
    }
    if (mode === "random") {
      render(pick(all, 4), "Aleatorio");
    } else {
      render(pick(all.filter((x) => x.b === Number(mode)), 4), `Bloque ${mode}`);
    }
  };
  buttons.forEach((b) => b.addEventListener("click", () => generate(b.dataset.gen)));
  const reset = root.querySelector("#gen-reset");
  const dialog = root.querySelector("#gen-dialog");
  const initial = status.textContent;
  const controls = reset.parentElement;
  reset.addEventListener("click", () => dialog.showModal());
  dialog.addEventListener("close", () => {
    if (dialog.returnValue !== "delete") return;
    out.textContent = "";
    status.textContent = initial;
    buttons.forEach((b) => { b.setAttribute("aria-pressed", "false"); b.disabled = false; });
    reset.hidden = true;
    controls.append(reset);
    root.querySelector("[data-gen]").focus();
  });
})();
