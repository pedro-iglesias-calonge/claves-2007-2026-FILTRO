# Síntesis — Procedimiento completo, paso a paso

## Qué es este documento

Es la **síntesis del procedimiento completo**. Cada etapa tiene su documento detallado en esta carpeta (`01` a `08`); aquí se resumen en orden, de modo que el lector comprenda **qué se hizo, en qué orden y por qué**, y pueda reconstruir el método con las instrucciones que cada etapa declara. Al final hay una tabla que vincula cada etapa con su script y su registro de corrida.

## Punto de partida

La Base de Datos de Matrícula del SIES contiene **280.160 filas** de matrícula de educación superior chilena entre 2007 y 2026, cada una con 58 campos (institución, carrera, sede, año, condiciones de ingreso, etc.). Esas filas corresponden a **16.684 programas distintos**, según la deduplicación por nombre normalizado. El objetivo es conservar únicamente los programas vinculados con la música, en un archivo que mantenga exactamente el formato de la fuente.

El procedimiento distingue tres formas de decisión:

- **Reglas (léxicas y semánticas):** instrucciones explícitas que la máquina aplica de forma determinista.
- **Verificación asistida por un modelo de lenguaje (LLM):** un modelo local y su réplica en la nube emiten un veredicto sobre los casos frontera.
- **Revisión humana:** la persona a cargo resuelve los casos que ni las reglas ni el modelo resuelven.

Las tres formas se aplican en orden: las reglas deciden la mayor parte; el LLM revisa los bordes; la persona cierra los casos restantes. Cada decisión queda **registrada con su método y su razón**, lo que permite auditar el procedimiento de principio a fin.

## Paso 1 — Integridad de los datos

Antes de clasificar se verifica que el archivo esté completo y sea legible: se cuentan filas y columnas, se confirma la presencia de los 20 años (`MAT_2007` a `MAT_2026`), se identifican los nombres y códigos únicos y se detectan 5 símbolos que el formato de texto no puede decodificar, los cuales se aíslan para que no alteren el resto de los datos.

- **Resultado**: un archivo verificado sobre el que se puede trabajar.
- **Procedimiento**: leer el archivo, contar filas y columnas, confirmar los años, detectar los símbolos no decodificables y dejar constancia.
- **Detalle**: `01-verificacion-datos.md`.

## Paso 2 — Filtro léxico

Se aplica un filtro léxico sobre el nombre del programa. Si el nombre contiene una señal musical directa, el programa se incluye; si contiene una señal de exclusión fuerte, se excluye. El motor reconoce señales directas (música, musical, composición, canto, instrumentos, producción musical, musicoterapia, gestión cultural) y aplica exclusiones fuertes contra las señales que no bastan por sí solas para calificar a un programa como musical (idiomas, danza, teatro, cine, acústica técnica, "licenciatura en artes" sin mención).

- **Resultado**: la base clara del universo — **217 programas incluidos** entre los 16.684 — y **10 dudosos** en la zona gris (los híbridos "sonido y acústica" y la "educación artística" sin mención) que el filtro no resuelve.
- **Procedimiento**: tomar cada nombre, buscar las señales de música, buscar las exclusiones y devolver veredicto (`INCLUIR`/`EXCLUIR`/`DUDOSO`), categoría y razón.
- **Detalle**: `02-filtro-lexico.md`.

## Paso 3 — Filtro semántico

Los programas cuyo nombre no contiene una señal léxica se evalúan por el **contexto** que la base entrega: el área genérica de la carrera y su subárea en la clasificación internacional de la educación (CINE). Si el contexto es claramente musical (áreas "Música, Canto o Danza" o "Pedagogía en Artes y Música"), el programa se incluye aunque su nombre no lo diga; si cae en la subárea *Artes* sin otra señal, se excluye con su razón.

- **Resultado**: **160 nombres** de la subárea *Artes* examinados por contexto y excluidos con fundamento; ningún programa musical queda fuera por ausencia de la palabra en su nombre.
- **Procedimiento**: reunir todas las apariciones del mismo nombre, revisar su área y subárea, desambiguar por mención musical y registrar la razón.
- **Detalle**: `03-filtro-semantico.md`.

## Paso 4 — Cliente del modelo de lenguaje

Antes de solicitar veredictos se construyó y probó el **cliente** que consulta al modelo de lenguaje (local, `gpt-oss:20b` vía Ollama, y su réplica en la nube `alias-fast`). Se comprobó que el cliente consulta por lotes, recibe respuestas estructuradas y **no aborta** si algún caso falla: registra el error y continúa, de modo que un fallo aislado no invalida el resto de la consulta.

- **Resultado**: un cliente probado (primera corrida de 50 nombres) antes de usarlo sobre los conjuntos frontera.
- **Detalle**: `04-cliente-llm.md`.

## Paso 5 — Verificación de falsos negativos

La pregunta de esta etapa es **"¿quedaron programas musicales fuera?"** Se construyó una red de candidatos: nombres de las áreas genéricas musicales que el filtro léxico no alcanzó a incluir, más una muestra de control aleatoria del resto. El modelo emitió un veredicto sobre **84 nombres** (34 de la red + 50 de control) y cada veredicto quedó registrado. La réplica en la nube confirmó el mismo resultado.

- **Resultado**: sin falsos negativos por ausencia del nombre; la clasificación queda en 217 incluir / 16.456 excluir / 11 dudosos.
- **Detalle**: `05-verificacion-falsos-negativos.md`.

## Paso 6 — Verificación de falsos positivos

La pregunta es la inversa: **"¿se incluyeron programas que no son música?"** Se tomaron los 67 incluidos fronterizos (aquellos cuya inclusión depende de señales secundarias y no de la palabra "música") y el modelo emitió un veredicto sobre cada uno. En la corrida local el modelo confirmó 52, marcó **15 como dudosos** para la revisión humana (principalmente de gestión cultural y los programas de *sonido*) y no retiró ninguno: la clasificación quedó en **202 incluidos, 16.456 excluidos y 26 dudosos**. La réplica en la nube fue más estricta con la gestión cultural: retiró 12 y dejó 6 dudosos, lo que confirma que esa frontera es la más sensible del procedimiento.

- **Resultado**: una inclusión más restrictiva — 202 incluidos, 16.456 excluidos, 26 dudosos — con la frontera de la gestión cultural delimitada.
- **Detalle**: `06-verificacion-falsos-positivos.md`.

## Paso 7 — Revisión humana

Las **26 dudas** que ni las reglas ni el modelo resolvieron (16 del modelo, 6 de educación artística pura, 4 híbridos "sonido y acústica") se entregan a la persona en una ficha y en una aplicación HTML para que decida caso por caso: *incluir* (con categoría) o *excluir*. La decisión humana es **definitiva**: no se vuelve a consultar al modelo, y todas las decisiones quedan en un archivo que la etapa siguiente lee.

- **Resultado**: 13 programas incluidos y 13 excluidos por decisión humana; cada decisión queda registrada.
- **Detalle**: `07-revision-humana.md`.

## Paso 8 — Ensamblado final

La etapa final integra la clasificación automática, la decisión humana y la matrícula completa, y produce dos entregables: **la clasificación final por programa** (donde la decisión humana reemplaza la duda y ninguna queda sin resolver) y **el archivo histórico de matrícula musical** (`Musica_2007_2026_filtrado.csv`), que conserva las 58 columnas originales y el mismo formato de la base.

- **Resultado**: de 280.160 filas quedan **2.664** (el ~1 % de la matrícula total en veinte años): **215 programas** incluidos, 13 de ellos por decisión humana; 49 instituciones (284 combinaciones institución–curso); los 20 años presentes; y todas las filas de los programas incluidos.
- **Detalle**: `08-ensamblado-final.md`.

## Verificación del método

Para que el método sea reproducible debe responder, con evidencia, tres preguntas:

1. **¿Quedaron fuera programas musicales?** → lo responden el paso 3 (contexto) y el paso 5 (falsos negativos con el modelo), construidos para no perder ninguno.
2. **¿Se incluyeron programas no musicales?** → lo responden el paso 2 (exclusiones fuertes) y el paso 6 (falsos positivos con el modelo), más el paso 7 (revisión humana) en la frontera final.
3. **¿Cada decisión tiene una razón?** → cada programa de la clasificación final registra su método (`lexico`, `semantico`, `llm` o `humano`) y su razón en lenguaje claro.

## Tabla de trazabilidad: etapa → script → log

Cada etapa tiene su documento en `metodologia/`, su script de corrida en `scripts/` y su registro de evidencias en `logs/`. El índice de corridas está en `logs/README.md`.

| Paso | Documento | Script | Log |
|------|-----------|--------|-----|
| 1. Integridad | `01-verificacion-datos.md` | `scripts/01_integridad.py` | `logs/01-integridad.md` |
| 2. Léxico | `02-filtro-lexico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 3. Semántico | `03-filtro-semantico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 4. Cliente del modelo | `04-cliente-llm.md` | `scripts/03_cliente_llm.py` | `logs/03-cliente-llm.md` |
| 5. Falsos negativos | `05-verificacion-falsos-negativos.md` | `scripts/04_verificacion_falsos_negativos.py` | `logs/04-verificacion-falsos-negativos.md` y `-cloud.md` |
| 6. Falsos positivos | `06-verificacion-falsos-positivos.md` | `scripts/05_verificacion_falsos_positivos.py` | `logs/05-verificacion-falsos-positivos.md` y `-cloud.md` |
| 7. Revisión humana | `07-revision-humana.md` | `scripts/06_generar_zonas_grises.py`, `07_generar_app_revision.py` | `logs/06-zonas-grises.md` y `07-revision-humana.md` |
| 8. Ensamblado | `08-ensamblado-final.md` | `scripts/08_ensamblado_final.py` | `logs/08-ensamblado-final.md` |

## Síntesis de resultados

El procedimiento no es una búsqueda por palabras: combina tres métodos de decisión —reglas, verificación con un modelo de lenguaje y revisión humana— y registra para cada decisión su nombre, método y razón. De 280.160 filas quedan 2.664; de 16.684 programas quedan 215; y los 20 años del registro quedan íntegros. Cualquiera puede reconstruir este método leyendo los documentos `01` a `08` en orden, sin necesidad de abrir el código para confiar en el resultado.
