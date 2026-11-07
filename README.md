# PAU Historia de España · Andalucía

✅ Accesible aquí https://fcallejah.github.io/analisis-pau-historia-espana/ ✅

Sitio estático e independiente para organizar recursos y, cuando se incorpore y revise un corpus suficiente, analizar preguntas cortas, temas, documentos e imágenes de los exámenes PAU de Historia de España en Andalucía.

## Estado inicial

La portada prioriza los apuntes y los accesos a preguntas y generador, sin carrusel de novedades. La barra de puntos navega por los doce bloques de apuntes y se sincroniza con los números y las flechas. Su indicador se rellena durante seis segundos antes de avanzar; al llegar al final vuelve al inicio. El avance automático se desactiva con la preferencia de reducir movimiento.

El carrusel admite arrastre con ratón y desplazamiento táctil. Los accesos numerados se centran en tres grupos indivisibles de cuatro bloques, que se distribuyen en las filas necesarias según el ancho.

El índice de estudio es breve y se divide en apuntes completos, preguntas cortas, imágenes y comentario de texto, y preguntas de desarrollo. Los apuntes de los bloques 1–3 y las preguntas cortas están disponibles; el banco de documentos y los temas de desarrollo indican que están pendientes. El índice conserva búsqueda y filtros, y enlaza también al generador. Se integra en un único anexo al final, después de las secciones de práctica: índice de materiales, estructura 3-4-3 y fuentes oficiales, en ese orden.

Esta versión ofrece una guía navegable del formato 2026–27, búsqueda en los contenidos publicados, filtros por tipo de contenido y agrupación, y enlaces a fuentes oficiales y al documento de recopilación. La caja de cuestiones cortas abre cuatro grupos con los enunciados resaltados en azul en el documento (114 enunciados únicos de 2017 a 2026, también en `data/preguntas-cortas.json`), clasificados por bloque; las repeticiones exactas se reúnen indicando las convocatorias cuando aparecen en la fuente. Al abrir cada bloque se genera una nube de temas: cada burbuja distingue preguntas distintas y exámenes del corpus; el tamaño y el orden reflejan el número de exámenes. Pulsar una burbuja filtra sus preguntas. Es una clasificación temática orientativa del corpus seleccionado, no una frecuencia de todos los exámenes celebrados ni una predicción. Esta es una instantánea estática: las nuevas marcas que se añadan al Google Doc deben importarse y clasificarse aquí manualmente. **Aún no contiene un corpus histórico completo revisado contra todos los originales**.

Según las orientaciones oficiales 2026–27, las cuestiones cortas (dos de cuatro) proceden de los bloques 1–4 de la Agrupación I, y el documento y el tema se organizan mediante dos itinerarios cruzados sobre las Agrupaciones II y III. Dado el cambio de estructura, los exámenes anteriores y los de 2026–27 en adelante deben analizarse por separado. Consulta la guía oficial para todos los detalles.

La cabecera muestra junto al título un carrusel horizontal de 12 tarjetas con los apuntes por bloque (del 1 al 12, con color por Agrupación I–III, flechas y chips de salto). Los títulos de las tarjetas y de sus páginas incluyen los períodos de las orientaciones; el bloque 8 conserva su referencia al siglo XIX sin añadir otro intervalo. Cada tarjeta muestra una imagen buscada en el navegador en Wikimedia Commons (API pública, término `data-q` de cada `.apunte-img`; se guarda en `localStorage`), con una breve descripción en pie de foto (`data-caption`) que enlaza a su ficha cuando viene de Commons (`data-pos` ajusta el encuadre, p. ej. `50% 80%` baja el recorte; `data-file` fija un fichero concreto; `data-src`, una URL directa); si no carga, queda un fondo de color. Revisa que la imagen elegida sea adecuada y cambia `data-q` si no. Cada tarjeta enlaza a una página estática en `apuntes/bloque-N.html`: los bloques 1–3 contienen los apuntes completos, y las páginas 4–12 indican expresamente que están pendientes. Los originales siguen enlazados desde las tarjetas y sus páginas. Se enlaza el PDF oficial de las orientaciones.

Los bloques 1–3 se actualizaron el 7 de noviembre de 2026 desde las exportaciones HTML de sus Google Docs: conservan texto, encabezados, listas, tablas, enlaces, notas e imágenes incrustadas, convertidas en archivos locales en `apuntes/imagenes/`; la negrita y la cursiva del original se trasladan a marcado semántico. El importador comprueba cada entrada del índice contra el texto del encabezado al que apunta en la fuente, y genera identificadores únicos y deterministas para los encabezados, conservando los antiguos como alias. Si una entrada es ambigua o no coincide, aborta la importación en lugar de adivinar. Las imágenes que el documento inserta dentro de un encabezado se colocan inmediatamente después para no desplazar su destino. Las notas exportadas se agrupan al final de cada página y sus referencias incluyen enlaces de ida y vuelta. Se descartan scripts, estilos de Google y atributos no necesarios; los enlaces de redirección se sustituyen por sus destinos. No se reproduce exactamente la tipografía, el color ni la maquetación de Google Docs.

El enlace al documento fuente aparece una vez al inicio de cada página. El importador utiliza como pie únicamente el párrafo en cursiva inmediatamente posterior a una imagen, incluso si hay párrafos vacíos entre ambos, y lo traslada junto a ella conservando enlaces y énfasis. No cruza texto, encabezados, listas ni otras imágenes para buscar un pie; si no hay una asociación clara, no añade ningún texto. Se conserva el texto alternativo de la imagen si el original lo proporciona.

La copia local es una instantánea. Para actualizar un bloque del 1 al 3, descarga la exportación HTML del documento correspondiente y ejecuta `python3 scripts/importar-apuntes.py 1 ruta/al-archivo.html` (o `2` o `3`); revisa los cambios y su correspondencia con el original. Las páginas comparten `apuntes.css` y `apuntes.js`, sin depender del código de portada, y sincronizan el tema con `pau-he.theme`. Los botones «Imprimir / guardar PDF», al principio y al final, abren el diálogo de impresión del navegador: allí se puede elegir una impresora o, si está disponible, guardar como PDF. La impresión conserva fuentes, imágenes y notas, con colores y diseño adaptados al papel. El service worker precarga las páginas y sus recursos comunes; las imágenes de los apuntes se guardan al visitarlas, por lo que pueden faltar sin conexión si no se han cargado antes.

El análisis de imágenes requiere los exámenes originales con sus imágenes; una transcripción de texto no basta para estudiar la recurrencia visual.

## Generador de cuestiones de práctica

Las burbujas distinguen **preguntas distintas** y **exámenes del corpus**: cada combinación de año y convocatoria se cuenta una sola vez dentro de un tema, aunque incluya varias preguntas relacionadas. Se ordenan por número de exámenes y después por número de preguntas. No representan todos los exámenes celebrados ni una probabilidad futura. Las convocatorias se destacan en píldoras. La errata "Fernando V de Aragón" de 2021 (reserva ordinaria) se conserva en el enunciado original y se acompaña de una nota roja: Fernando II de Aragón, también llamado Fernando V de Castilla.

Las píldoras mantienen el mismo fondo lila claro, texto morado y contorno morado fino, también en el generador. Las fechas y convocatorias permanecen visibles; el color no codifica frecuencias ni probabilidades futuras.

La barra superior muestra las 114 preguntas recopiladas, repartidas por bloque en sus píldoras (8, 35, 34 y 37), calculadas automáticamente a partir de los enunciados. Las burbujas de temas siguen mostrando exámenes distintos; las burbujas "Todos" muestran preguntas.

La sección "Generador" crea cuatro preguntas cortas del bloque 1, 2, 3 o 4, o mezcladas ("Aleatorio": una de cada bloque, ordenadas del 1 al 4, como en el modelo oficial 2026–27, donde las cuatro cuestiones son de bloques distintos), cada una con un desplegable "Posible solución". El banco (`FICHAS` en `generador.js`, entradas `[enunciado, "puntos clave", "PAU años"]`) combina los ejemplos de preguntas cortas de los apuntes del autor (bloques 1–3, sin año) con los enunciados literales de la PAU 2017–2026 del corpus (etiquetados con sus años). Los puntos clave de las preguntas PAU de los bloques 1–3 se han redactado a partir de los apuntes; el bloque 4 solo incluye preguntas PAU, sin solución hasta que se incorporen sus apuntes. Para ampliarlo, añade entradas al bloque correspondiente. Las soluciones son orientativas y no indican probabilidad de examen.

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

El favicon es una H cuadrada y la imagen Open Graph (`assets/social-preview.png`, 1200 × 630) muestra la H con "PAU 26-27" debajo para compartir en WhatsApp. La vista previa necesita la publicación en Pages y puede tardar en renovarse por la caché de WhatsApp.

1. Publica el contenido de este repositorio en GitHub.
2. En **Settings → Pages**, elige desplegar desde una rama.
3. Selecciona la rama `main` y la carpeta raíz (`/`), y guarda.

Los recursos locales usan rutas relativas, compatibles con la raíz del sitio y con la ruta de proyecto de Pages. La tipografía remota es opcional; se han definido alternativas de sistema.

## Próximos pasos del análisis

Importar el corpus recopilado y registrar para cada examen el año, formato, parte de la prueba, bloque o agrupación y fuente. Revisar las transcripciones frente a los originales, separar las series anteriores a 2026–27 de las del nuevo modelo e incorporar los originales de imagen y sus metadatos antes de publicar cualquier frecuencia o análisis visual.
