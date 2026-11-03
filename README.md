# PAU Historia de España · Andalucía

✅ Accesible aquí https://fcallejah.github.io/analisis-pau-historia-espana/ ✅

Sitio estático e independiente para organizar recursos y, cuando se incorpore y revise un corpus suficiente, analizar preguntas cortas, temas, documentos e imágenes de los exámenes PAU de Historia de España en Andalucía.

## Estado inicial

Esta primera versión ofrece una guía navegable del formato 2026–27, búsqueda en los contenidos publicados, filtros por tipo de contenido y agrupación, y enlaces a fuentes oficiales y al documento de recopilación. La caja de cuestiones cortas abre cuatro grupos con los enunciados resaltados en azul en el documento (114 enunciados únicos de 2017 a 2026, también en `data/preguntas-cortas.json`), clasificados por bloque; las repeticiones exactas se reúnen indicando las convocatorias cuando aparecen en la fuente. Al abrir cada bloque se genera una nube de temas: el tamaño y cifra de cada burbuja indican cuántos enunciados únicos de esa selección se relacionan con el tema; pulsar una burbuja filtra sus preguntas. Es una clasificación temática orientativa, no una estadística de exámenes ni una predicción. La exportación consultada contiene preguntas marcadas de exámenes de 2017–2019. Esta es una instantánea estática: las nuevas marcas que se añadan al Google Doc deben importarse y clasificarse aquí manualmente. **Aún no contiene un corpus histórico completo revisado contra todos los originales ni resultados estadísticos**.

Según las orientaciones oficiales 2026–27, las cuestiones cortas (dos de cuatro) proceden de los bloques 1–4 de la Agrupación I, y el documento y el tema se organizan mediante dos itinerarios cruzados sobre las Agrupaciones II y III. Dado el cambio de estructura, los exámenes anteriores y los de 2026–27 en adelante deben analizarse por separado. Consulta la guía oficial para todos los detalles.

La cabecera muestra junto al título, en abanico, las seis páginas de las orientaciones oficiales; son capturas WebP del PDF de la Junta de Andalucía (`assets/orientaciones/`), enlazado como fuente.

El análisis de imágenes requiere los exámenes originales con sus imágenes; una transcripción de texto no basta para estudiar la recurrencia visual.

## Generador de cuestiones de práctica

La sección «Generador» crea cuatro cuestiones cortas del bloque 1, 2 o 3, o mezcladas («Aleatorio»), cada una con un desplegable «Posible solución». El banco (`FICHAS` en `generador.js`) reproduce los ejemplos de preguntas cortas de los apuntes del autor para los bloques 1–3 (41 en total; las marcadas con año son PAU reales). El bloque 4 está pendiente de sus apuntes. Para ampliarlo, añade `[enunciado, "puntos clave"]` al bloque correspondiente. Las soluciones son orientativas y no indican probabilidad de examen.

## Fuentes

- [Orientaciones oficiales de Historia de España 2026–27 (PDF)](https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/sguit/examanes_anios_anteriores/selectividad/sel_2026-2027-Orientaciones_historia_espana.pdf)
- [Archivo oficial SGUIT de exámenes anteriores](https://www.juntadeandalucia.es/economiaconocimientoempresasyuniversidad/sguit/?q=grados&d=g_b_examenes_anteriores.php)
- [Documento del corpus de exámenes](https://docs.google.com/document/d/1tLvTDk_3AdV7w-eoBB3InnzbTVsWmPbK_VL1z8dkyOk/edit?usp=sharing)
- [Noticia de la Junta: convocatoria extraordinaria adelantada a julio (2021)](https://www.juntadeandalucia.es/organismos/universidadindustriaenergiaeinnovacion/servicios/actualidad/noticias/detalle/246746.html)

## Ejecutar localmente

No necesita dependencias ni compilación. Abre `index.html` en un navegador o sirve la carpeta con cualquier servidor estático local.

## Publicar en GitHub Pages

1. Publica el contenido de este repositorio en GitHub.
2. En **Settings → Pages**, elige desplegar desde una rama.
3. Selecciona la rama `main` y la carpeta raíz (`/`), y guarda.

Los recursos locales usan rutas relativas, compatibles con la raíz del sitio y con la ruta de proyecto de Pages. La tipografía remota es opcional; se han definido alternativas de sistema.

## Próximos pasos del análisis

Importar el corpus recopilado y registrar para cada examen el año, formato, parte de la prueba, bloque o agrupación y fuente. Revisar las transcripciones frente a los originales, separar las series anteriores a 2026–27 de las del nuevo modelo e incorporar los originales de imagen y sus metadatos antes de publicar cualquier frecuencia o análisis visual.
