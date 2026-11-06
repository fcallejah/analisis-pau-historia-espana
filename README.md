# PAU Historia de España · Andalucía

✅ Accesible aquí https://fcallejah.github.io/analisis-pau-historia-espana/ ✅

Sitio estático e independiente para organizar recursos y, cuando se incorpore y revise un corpus suficiente, analizar preguntas cortas, temas, documentos e imágenes de los exámenes PAU de Historia de España en Andalucía.

## Estado inicial

Esta versión ofrece una guía navegable del formato 2026–27, búsqueda en los contenidos publicados, filtros por tipo de contenido y agrupación, y enlaces a fuentes oficiales y al documento de recopilación. La caja de cuestiones cortas abre cuatro grupos con los enunciados resaltados en azul en el documento (114 enunciados únicos de 2017 a 2026, también en `data/preguntas-cortas.json`), clasificados por bloque; las repeticiones exactas se reúnen indicando las convocatorias cuando aparecen en la fuente. Al abrir cada bloque se genera una nube de temas: cada burbuja distingue preguntas distintas y exámenes del corpus; el tamaño y el orden reflejan el número de exámenes. Pulsar una burbuja filtra sus preguntas. Es una clasificación temática orientativa del corpus seleccionado, no una frecuencia de todos los exámenes celebrados ni una predicción. Esta es una instantánea estática: las nuevas marcas que se añadan al Google Doc deben importarse y clasificarse aquí manualmente. **Aún no contiene un corpus histórico completo revisado contra todos los originales**.

Según las orientaciones oficiales 2026–27, las cuestiones cortas (dos de cuatro) proceden de los bloques 1–4 de la Agrupación I, y el documento y el tema se organizan mediante dos itinerarios cruzados sobre las Agrupaciones II y III. Dado el cambio de estructura, los exámenes anteriores y los de 2026–27 en adelante deben analizarse por separado. Consulta la guía oficial para todos los detalles.

La cabecera muestra junto al título, en abanico, las seis páginas de las orientaciones oficiales; son capturas WebP del PDF de la Junta de Andalucía (`assets/orientaciones/`), enlazado como fuente.

El análisis de imágenes requiere los exámenes originales con sus imágenes; una transcripción de texto no basta para estudiar la recurrencia visual.

## Generador de cuestiones de práctica

Las burbujas distinguen **preguntas distintas** y **exámenes del corpus**: cada combinación de año y convocatoria se cuenta una sola vez dentro de un tema, aunque incluya varias preguntas relacionadas. Se ordenan por número de exámenes y después por número de preguntas. No representan todos los exámenes celebrados ni una probabilidad futura. Las convocatorias se destacan en píldoras. La errata «Fernando V de Aragón» de 2021 (reserva ordinaria) se conserva en el enunciado original y se acompaña de una nota roja: Fernando II de Aragón, también llamado Fernando V de Castilla.

Las píldoras mantienen el mismo fondo lila claro, texto morado y contorno morado fino, también en el generador. Las fechas y convocatorias permanecen visibles; el color no codifica frecuencias ni probabilidades futuras.

La barra superior muestra las 114 preguntas recopiladas, repartidas por bloque en sus píldoras (8, 35, 34 y 37), calculadas automáticamente a partir de los enunciados. Las burbujas de temas siguen mostrando exámenes distintos; las burbujas «Todos» muestran preguntas.

La sección «Generador» crea cuatro preguntas cortas del bloque 1, 2, 3 o 4, o mezcladas («Aleatorio»), cada una con un desplegable «Posible solución». El banco (`FICHAS` en `generador.js`, entradas `[enunciado, "puntos clave", "PAU años"]`) combina los ejemplos de preguntas cortas de los apuntes del autor (bloques 1–3, sin año) con los enunciados literales de la PAU 2017–2026 del corpus (etiquetados con sus años). Los puntos clave de las preguntas PAU de los bloques 1–3 se han redactado a partir de los apuntes; el bloque 4 solo incluye preguntas PAU, sin solución hasta que se incorporen sus apuntes. Para ampliarlo, añade entradas al bloque correspondiente. Las soluciones son orientativas y no indican probabilidad de examen.

## Fuentes

- [Orientaciones oficiales de Historia de España 2026–27 (PDF)](https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/sguit/examanes_anios_anteriores/selectividad/sel_2026-2027-Orientaciones_historia_espana.pdf)
- [Archivo oficial SGUIT de exámenes anteriores](https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/sguit/?q=grados&d=g_b_examenes_anteriores.php)
- [Documento del corpus de exámenes](https://docs.google.com/document/d/1tLvTDk_3AdV7w-eoBB3InnzbTVsWmPbK_VL1z8dkyOk/edit?usp=sharing)
- [Noticia de la Junta: fechas de la PAU 2027 (1, 2 y 3 de junio)](https://www.juntadeandalucia.es/organismos/universidadindustriaenergiaeinnovacion/servicios/actualidad/noticias/detalle/688960.html)

## Ejecutar localmente

No necesita dependencias ni compilación. Abre `index.html` en un navegador o sirve la carpeta con cualquier servidor estático local.

## Publicar en GitHub Pages

### Instalar y usar sin conexión

El sitio incluye `manifest.json` e iconos instalables. En Android, abre la web en Chrome y usa **Instalar aplicación** o **Añadir a pantalla de inicio**. En iPhone/iPad, abre Safari y usa **Compartir → Añadir a pantalla de inicio**. No es una aplicación nativa: es la misma web en una ventana independiente.

El service worker (`sw.js`) requiere HTTPS (GitHub Pages) o localhost. Tras una primera carga completa, conserva la interfaz, los bancos de preguntas y las seis imágenes de orientaciones para usarlos sin conexión. Los PDF oficiales, Google Docs y otros enlaces externos siguen necesitando internet. Las visitas con conexión recuperan las versiones nuevas; al cambiar los recursos precargados, aumenta la versión `CACHE` del service worker. Una actualización instalada se activa cuando se cierran las pestañas de la versión anterior.

El favicon es una H cuadrada y la imagen Open Graph (`assets/social-preview.png`, 1200 × 630) muestra la H con «PAU 26-27» debajo para compartir en WhatsApp. La vista previa necesita la publicación en Pages y puede tardar en renovarse por la caché de WhatsApp.

1. Publica el contenido de este repositorio en GitHub.
2. En **Settings → Pages**, elige desplegar desde una rama.
3. Selecciona la rama `main` y la carpeta raíz (`/`), y guarda.

Los recursos locales usan rutas relativas, compatibles con la raíz del sitio y con la ruta de proyecto de Pages. La tipografía remota es opcional; se han definido alternativas de sistema.

## Próximos pasos del análisis

Importar el corpus recopilado y registrar para cada examen el año, formato, parte de la prueba, bloque o agrupación y fuente. Revisar las transcripciones frente a los originales, separar las series anteriores a 2026–27 de las del nuevo modelo e incorporar los originales de imagen y sus metadatos antes de publicar cualquier frecuencia o análisis visual.
