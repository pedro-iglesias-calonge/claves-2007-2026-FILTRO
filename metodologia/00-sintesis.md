# Síntesis — El procedimiento completo, paso a paso

_Enfoque humanista: esto no es un manual de programación. Es la historia de cómo se construyó una lista de programas musicales en veinte años de matrícula chilena, contada para quien trabaja en pedagogía o en música. Las palabras "regla", "modelo" e "humano" no son jerga: son los tres actores que se turnan en cada decisión. Aquí están juntos, en orden, en un solo relato._

## Qué es este documento

Es el **mapa del estudio completo**. Cada etapa del procedimiento tiene su propio documento detallado en esta carpeta (del `01` al `08`); aquí se los reúne en un relato único y en orden, de modo que un lector sin formación técnica entienda **qué se hizo, en qué orden, y por qué**, y pueda reconstruir el método con las instrucciones que cada etapa ya declara. Al final hay una tabla-puente entre esta narración y los registros técnicos, para quien quiera ir al detalle.

## El punto de partida

Chile registra, año a año, toda la matrícula de la educación superior. La base que abre este estudio contiene **280.160 filas de matrícula entre los años 2007 y 2026**, cada una con 58 datos (institución, carrera, sede, año, condiciones de ingreso, y más). Esos 280.160 registros describen **16.684 programas distintos** (el dedupe por nombre normalizado). El objetivo es quedarse solo con los programas cuyo corazón es la música, en un archivo que conserve exactamente el mismo formato de la fuente para que cualquiera pueda usarlo después.

Para lograr eso se distinguieron tres formas de decidir:

- **La regla**: instrucciones escritas a mano (léxico y contexto) que la máquina aplica igual siempre.
- **El modelo**: un colaborador externo (un gran modelo de lenguaje, local y en la nube) que opina en lenguaje natural donde la regla duda.
- **El humano**: la persona a cargo del estudio, que resuelve en última instancia los pocos casos que ni la regla ni el modelo se atreven a decidir.

Ninguno decide solo. La regla decide primero y rápido; el modelo corrige en los bordes; el humano cierra. Y cada decisión queda **registrada con su razón**, para que el estudio sea auditable de principio a fin.

## Paso 1 — Revisar la mercancía: integridad de los datos

Antes de clasificar hay que confiar en el archivo. Se verificó que la base esté completa y legible: se contaron las filas y columnas, se confirmó que están presentes los 20 años prometidos (`MAT_2007` a `MAT_2026`), se identificaron los nombres y códigos únicos, y se detectaron 5 símbolos que el formato de texto no pudo descifrar, aislándolos para que no contaminen el resto.

- **Qué logra**: un archivo verificado sobre el que vale la pena trabajar.
- **Paso a paso**: leer el archivo, contar, confirmar años, detectar símbolos raros, dejar constancia.
- **Detalle**: `01-verificacion-datos.md`.

## Paso 2 — La primera escucha: el filtro léxico

En esta etapa se escucha **la palabra del nombre**. Si un programa se llama a sí mismo musicalmente, entra; si se llama con palabras que engañan, sale. El motor reconoce las señales directas (música, musical, composición, canto, los instrumentos, producción musical, musicoterapia, gestión cultural) y aplica **exclusiones fuertes** contra las trampas (idiomas, danza, teatro, cine, acústica técnica, "licenciatura en artes" sin mención).

- **Qué logra**: la base clara del universo — **217 programas incluidos** entre los 16.684 — y deja **10 dudosos** en la zona gris (los híbridos "sonido y acústica" y la "educación artística" pura) que ni la palabra decide.
- **Paso a paso**: tomar cada nombre, buscar las señales de música, buscar las exclusiones, devolver veredicto (incluir/excluir/dudoso), categoría y razón.
- **Detalle**: `02-filtro-lexico.md`.

## Paso 3 — La segunda escucha: el filtro semántico

Hay programas que no se dicen a sí mismos. Para ellos se usó el **contexto** que la base entrega junto al nombre: el área genérica de la carrera y su subárea en la clasificación internacional de la educación. Si el contexto es claramente musical (áreas "Música, Canto o Danza" o "Pedagogía en Artes y Música"), el programa entra aunque su nombre no lo diga; si cae en la subárea *Artes* sin otra señal, se excluye con su razón.

- **Qué logra**: **160 nombres** de la subárea *Artes* examinados por contexto y excluidos con fundamento; ningún programa musical queda fuera por el silencio de su nombre.
- **Paso a paso**: unir todas las apariciones del mismo nombre, mirar su área y subárea, desambiguar por mención musical, registrar la razón.
- **Detalle**: `03-filtro-semantico.md`.

## Paso 4 — Preparar al colaborador: el cliente del modelo

Antes de pedir opiniones, se construyó y probó el **puente** que habla con el modelo de lenguaje (local, `gpt-oss:20b` vía Ollama, y su réplica en la nube `alias-fast`). Se comprobó que el puente consulta por lotes, recibe respuestas en forma de ficha, y —clave humanista— **no aborta** si algún caso falla: registra el error y sigue, para que una opinión fallida no tire al suelo las demás.

- **Qué logra**: un colaborador confiable y probado (primera corrida de 50 nombres) antes de usarlo en masa.
- **Detalle**: `04-cliente-llm.md`.

## Paso 5 — No quedarse corto: verificación de falsos negativos

La pregunta de esta etapa es **"¿nos estamos dejando programas afuera?"** Se armó una red de candidatos: nombres en las áreas genéricas musicales que la palabra no alcanzó a incluir, más una muestra de control del resto. El modelo opinó sobre **84 nombres** (34 de la red + 50 de control), y todo veredicto quedó registrado. La nube, además, confirmó lo mismo en una segunda corrida.

- **Qué logra**: sin falsos negativos por silencio del nombre; la clasificación queda en 217 incluir / 16.456 excluir / 11 dudosos.
- **Detalle**: `05-verificacion-falsos-negativos.md`.

## Paso 6 — No pasarse de largo: verificación de falsos positivos

Ahora la pregunta es la inversa: **"¿se colaron programas que no son música?"** Se tomaron los 67 incluidos fronterizos (aquellos cuya inclusión descansa en señales secundarias y no en la palabra "música") y el modelo opinó sobre cada uno. El modelo local confirmó 52, marcó **15 como dudosos** para la revisión humana (sobre todo de gestión cultural y los programas de *sonido*) y no retiró ninguno: la clasificación quedó en **202 incluidos, 16.456 excluidos y 26 dudosos**. La réplica en la nube fue más estricta con la gestión cultural: retiró 12 y dejó 6 dudosos, confirmando que esa frontera es la más sensible del estudio.

- **Qué logra**: una inclusión más austera y honesta — 202 incluidos, 16.456 excluidos, 26 dudosos — con la frontera más sensible (gestión cultural) bien delimitada.
- **Detalle**: `06-verificacion-falsos-positivos.md`.

## Paso 7 — La palabra final: revisión humana

Es el paso que vuelve humano el estudio. Las **26 dudas** que ni la regla ni el modelo resolvieron (16 dudas del modelo, 6 de educación artística pura, 4 híbridos de sonido y acústica) se entregan a la persona en una ficha —y en una aplicación sencilla— para que decida una por una: *incluir* (con categoría) o *excluir*. La decisión humana es **soberana**: no vuelve a preguntar al modelo, y todas las decisiones quedan en un archivo que la etapa siguiente sabrá leer.

- **Qué logra**: 13 programas entran y 13 salen por juicio humano; cada decisión queda registrada.
- **Detalle**: `07-revision-humana.md`.

## Paso 8 — El ensamblado: construir el archivo que se puede usar

La etapa final junta todas las voces. Toma la clasificación automática, la decisión humana y la matrícula completa, y produce dos entregables: **la clasificación final por programa** (donde la decisión humana reemplaza la duda y ninguna queda sin resolver) y **el archivo histórico de matrícula musical** (`Musica_2007_2026_filtrado.csv`), que conserva las 58 columnas originales y el mismo formato de la base, para que quien lo reciba no necesite saber nada del camino recorrido.

- **Qué logra**: de 280.160 filas quedan **2.664** (el ~1% de la matrícula total en veinte años): **215 programas** incluidos, 13 de ellos por decisión humana; 49 instituciones (284 combinaciones institución–curso); los 20 años presentes; y todas las filas de los incluidos, historia por historia, sin una pérdida.
- **Detalle**: `08-ensamblado-final.md`.

## Cómo verificar el método si usted lo controla bien

El relato de arriba es solo la mitad del asunto. Para que el método sea creíble debe poder contestar, con pruebas, tres preguntas:

1. **¿Quedaron fuera programas musicales?** → lo contestan el paso 3 (contexto) y el paso 5 (falsos negativos con el modelo), que se construyeron ex profeso para no perder ninguno.
2. **¿Se colaron programas no musicales?** → lo contestan el paso 2 (exclusiones fuertes) y el paso 6 (falsos positivos con el modelo), más el paso 7 (revisión humana) en la frontera final.
3. **¿La decisión de cada programa tiene razón?** → sí: cada programa de la clasificación final carga su método (`lexico`, `semantico`, `llm` o `humano`) y su razón en lenguaje claro.

## Tabla-puente: de la narración al registro

Para quien quiera aproximarse al material técnico, cada momento tiene su documento narrativo, su script de corrida y su log de evidencias. El índice de corridas está en `logs/README.md`.

| Paso | Narración | Corrida | Log |
|------|-----------|---------|-----|
| 1. Integridad | `01-verificacion-datos.md` | `scripts/01_integridad.py` | `logs/01-integridad.md` |
| 2. Léxico | `02-filtro-lexico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 3. Semántico | `03-filtro-semantico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 4. Cliente del modelo | `04-cliente-llm.md` | `scripts/03_cliente_llm.py` | `logs/03-cliente-llm.md` |
| 5. Falsos negativos | `05-verificacion-falsos-negativos.md` | `scripts/04_verificacion_falsos_negativos.py` | `logs/04-verificacion-falsos-negativos.md` y `-cloud.md` |
| 6. Falsos positivos | `06-verificacion-falsos-positivos.md` | `scripts/05_verificacion_falsos_positivos.py` | `logs/05-verificacion-falsos-positivos.md` y `-cloud.md` |
| 7. Revisión humana | `07-revision-humana.md` | `scripts/06_generar_zonas_grises.py`, `07_generar_app_revision.py` | `logs/06-zonas-grises.md` y `07-revision-humana.md` |
| 8. Ensamblado | `08-ensamblado-final.md` | `scripts/08_ensamblado_final.py` | `logs/08-ensamblado-final.md` |

## Lo que el lector no técnico debe llevarse

El estudio no es "una búsqueda por palabras": es un **procedimiento en tres turnos** — la regla clasifica, el modelo corrige los bordes, el humano decide el final — donde **cada decisión tiene nombre, método y razón**. De 280.160 filas quedan 2.664, de 16.684 programas quedan 215, y los 20 años del registro quedan íntegros. Cualquiera puede reconstruir este método leyendo los documentos `01` al `08` en orden; ninguno requiere abrir el código para confiar en el resultado.