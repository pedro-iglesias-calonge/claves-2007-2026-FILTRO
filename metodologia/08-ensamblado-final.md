# Etapa 08 — El ensamblado final: el archivo que se puede usar

_Enfoque humanista: cada etapa anterior dejó un veredicto —la regla decidió, el modelo dudó, el humano resolvió. Esta etapa junta todas esas voces en un solo acto: construye la matrícula definitiva, con las mismas 58 columnas y el mismo encoding cp1252 que la base original, de modo que quien la reciba no necesite saber nada de lo que pasó antes para trabajar con ella. El producto deja de ser un resumen de decisiones y vuelve a ser, literalmente, un archivo de matrícula: solo que con la música adentro._

## Qué se hizo

Se escribió la **etapa de ensamblado**, el último tramo del pipeline, que toma tres insumos y produce dos entregables:

- Entran **la clasificación automática** (`prod/clasificacion_tras_falsos_positivos.csv`, de las etapas anteriores), **la decisión humana** sobre las 26 zonas grises (`prod/zonas_grises_revisadas.csv`) y **la matrícula completa** (`datos SIES/Matricula_2007_2026_WEB_10_07_2026.csv`, 280.160 filas).
- Sale **la clasificación final por nombre** (`prod/clasificacion_total.csv`): un veredicto único por programa, donde la decisión humana **reemplaza** la duda automática —*incluir* con su categoría, o *excluir* — y se registra con método `humano` y la razón `Decisión humana en la revisión de zonas grises`. Ningún `DUDOSO` sobrevive al ensamblado.
- Sale **el archivo histórico de matrícula musical** (`prod/Musica_2007_2026_filtrado.csv`): todas las filas, de todos los años y todas las sedes, de los programas incluidos, conservando **las 58 columnas originales**, el **encoding cp1252** (sin BOM, CRLF, comillas solo donde el formato lo exige). La persona que reciba este archivo puede abrirlo, filtrarlo o cruzarlo con otras fuentes sin mediar palabra.

La decisión humana se incorpora sobre el **nombre normalizado** (la misma unidad de decisión de todo el estudio): si el humano dijo *incluir* para un nombre, ese nombre entra con su categoría final; si dijo *excluir*, ese nombre deja la lista. El diseño no muta la clasificación de entrada: produce una copia enriquecida, y así cada veredicto puede trazarse sin reescribir lo ya escrito.

## Qué se descubrió

- **De 280.160 filas quedan 2.664**: la matrícula musical histórica es el ~1% de la matrícula total. Es un porcentaje pequeño y esperable, pero ahora está medido sobre una base completa de veinte años.
- **La lista final tiene 215 programas incluidos**, y **13 de ellos entran por decisión humana** (de 202 a 215). Las zonas grises no fueron una formalidad: movieron la frontera en un 6% de los incluidos.
- **La serie cubre los 20 años sin huecos**: el archivo final tiene filas de `MAT_2007` a `MAT_2026`, todos los años presentes. La música no tiene lagunas en la historia registrada.
- **El filtro conserva 49 instituciones** (284 combinaciones institución–curso): el archivo final no es una lista de nombres, es la matrícula real con toda su geografía de instituciones, carreras, sedes y años.
- **La decisión humana resolvió la frontera exacta donde la regla no se atreve**: los programas de *sonido* (ingenierías acústicas, técnicos de sonido) y de *educación artística pura* entraron o salieron según el juicio humano; en particular, los nombres `sonido` y `tecnico de nivel superior sonido y acustica` entraron sin categoría final, porque el humano incluyó sin precisarla. La clasificación total admite esa ligereza: la categoría queda en blanco pero el veredicto es soberano.

## Por qué importa para el resto del estudio

1. **El estudio se puede usar**: hasta aquí todo era clasificación; desde aquí hay un archivo de matrícula listo para cualquier análisis posterior sobre la música en Chile.
2. **La huella es idéntica a la fuente**: mismas columnas, mismo encoding, mismo separador, mismo salto de línea. Un cruce entre el archivo filtrado y la base original es directo, fila por fila.
3. **El veredicto final queda trazable**: cada nombre tiene su método (`lexico`, `semantico`, `llm` o `humano`) y su razón; quien quiera auditar la lista sabe por qué está cada programa, sin adivinar.
4. **El criterio y la humana conviven**: la clasificación final es la síntesis de toda la garantía del estudio — reglas, modelo y persona — con prelación explícita de la persona sobre el motor.
5. **El formato preserva la completitud**: los tests de integración verifican que toda fila del archivo final pertenezca a un nombre incluido y que ningún programa incluido haya perdido filas; el recorte no pierde ninguna historia.

## Registro

La lógica vive en `sies_musica/ensamblado.py` (lectura de las decisiones humanas, fusión con la clasificación, selección de incluidos, filtrado de la matrícula y escritura cp1252), y se prueba en `tests/test_ensamblado.py` con datos sintéticos y con la corrida real de integración. La corrida está en `scripts/08_ensamblado_final.py`. Resultados en `prod/clasificacion_total.csv` y `prod/Musica_2007_2026_filtrado.csv`. Log en `logs/08-ensamblado-final.md`. Con esta etapa se cierra el pipeline completo de los ocho momentos del estudio.