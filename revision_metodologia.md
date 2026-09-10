# Revisión Metodológica — Filtrado de Programas Musicales SIES 2007-2026

## (i) Filtrado de programas musicales

El propósito de esta fase fue identificar, extraer y documentar los programas de educación superior vinculados con la música en Chile durante el período 2007-2026, a partir de la Base de Datos de Matrícula del SIES. El objetivo fue construir un conjunto de datos histórico, auditable y reproducible. Como resultado, se generó una base que conservó la estructura de la fuente original e incluyó únicamente registros correspondientes a programas vinculados con la música. El proceso redujo la base inicial de 280.160 a 2.664 registros, equivalentes al 0,95% del total original.

El procedimiento se desarrolló mediante las siguientes etapas:

### 1. Verificación de integridad de los datos

**Propósito:** Asegurar la calidad y completitud de la base SIES antes del procesamiento.

**Procedimiento:**
- Se verificó la integridad estructural de la base SIES correspondiente al período 2007-2026: 280.160 registros, 58 columnas y datos completos para los 20 años del período analizado.
- Se identificaron 16.684 programas únicos a partir de la normalización de sus nombres (minúsculas, sin tildes).
- Se detectaron 5 símbolos no decodificables en el encoding cp1252, los cuales fueron aislados y registrados para su tratamiento posterior.

**Prueba de validación:** La verificación confirmó la ausencia de valores nulos en las columnas críticas (código de carrera, nombre de carrera, año de matrícula) y la consistencia temporal de las series históricas. El encoding fue estandarizado a UTF-8 manteniendo la fidelidad de los caracteres especiales.

### 2. Filtro léxico mediante reglas explícitas

**Propósito:** Clasificar programas mediante un sistema determinista de inclusión y exclusión basado en señales léxicas.

**Procedimiento:**
- Se construyó un léxico de 69 conceptos asociados con programas vinculados con la música. Entre los términos de inclusión se consideraron "música", "musical", "formación musical", nombres de instrumentos (piano, violín, guitarra, saxofón, entre otros 20), canto, composición, arreglos, sonido, grabación, producción musical, orquesta, coro, dirección musical y musicoterapia.
- Se establecieron criterios de exclusión con 47 conceptos, entre ellos: interpretación/traducción de idiomas, danza, teatro, cine, audiovisuales, artes visuales/plásticas, acústica técnica (edificación, ambiental, submarina) y terapias no musicales.
- Se aplicó una regla de prioridad: la presencia de "música" o "musical" en el nombre de la carrera sobreescribe señales de exclusión (p. ej., "música y acústica" se incluye).

**Resultados intermedios:** 217 programas incluidos, 16.457 excluidos y 10 casos inicialmente clasificados como dudosos (hibridos "sonido y acústica", educación artística sin mención musical).

**Prueba de validación:** Se ejecutó un conjunto de pruebas unitarias sobre 50 casos de referencia conocidos (25 musicales y 25 no musicales), obteniendo un 100% de precisión en la clasificación léxica. Los casos dudosos fueron marcados automáticamente para revisión semántica.

### 3. Filtro semántico basado en el contexto de la base

**Propósito:** Desambiguar programas cuyos nombres no contienen señales léxicas explícitas pero cuya clasificación puede inferirse del contexto institucional.

**Procedimiento:**
- Se examinaron 160 programas ubicados en áreas genéricas registradas en la base, tales como "Música, Canto o Danza" y "Pedagogía en Artes y Música".
- Se utilizó la clasificación CINE-F (Campo de Formación) como criterio complementario: los programas en el área "Artes" sin señal musical explícita en el nombre fueron excluidos.
- Los programas en áreas genéricas musicales fueron incluidos en la categoría "Otros" para posterior revisión.

**Resultados intermedios:** De los 160 nombres revisados, 145 fueron incluidos por contexto semántico y 15 excluidos por corresponder a artes visuales o escénicas puras.

**Prueba de validación:** Una muestra aleatoria del 10% (16 casos) fue revisada manualmente, confirmando la correcta aplicación del criterio semántico en todos los casos.

### 4. Verificación asistida de falsos negativos y positivos

**Propósito:** Auditar la clasificación léxica y semántica mediante un modelo de lenguaje para detectar errores sistemáticos antes de la revisión humana.

**Procedimiento:**
- Se empleó un modelo de lenguaje de gran escala (Ministral-3-14B, Blablador, 2025) accesado vía API cloud para garantizar tiempos de procesamiento y consistencia en las respuestas.
- **Verificación de falsos negativos:** Se revisaron 84 nombres compuestos por (a) una red de 34 candidatos de áreas musicales sin palabra clave y (b) una muestra aleatoria de control de 50 programas excluidos. El modelo recibió instrucciones tri-valor (INCLUIR/EXCLUIR/DUDOSO) con categoría obligatoria y razón breve.
- **Verificación de falsos positivos:** Se revisaron 67 programas incluidos considerados fronterizos por no contener los términos "música" o "musical" explícitamente (p. ej., "intérprete instrumental", "gestión cultural", nombres de instrumentos aislados).

**Resultados de la auditoría:**
- **Falsos negativos:** El modelo no identificó ningún programa musical omitido entre los 84 casos examinados (0% de falsos negativos en la muestra).
- **Falsos positivos:** El modelo sugirió retirar 12 programas sin referencia musical explícita (principalmente diplomados y técnicos en gestión cultural), los cuales fueron re-clasificados como EXCLUIR. Asimismo, identificó 6 casos dudosos que fueron transferidos a la zona gris.
- **Tasa de error del modelo:** 2 de 67 consultas (3%) retornaron errores de parseo por categorías fuera del esquema estándar; estos casos fueron mantenidos en la clasificación original y marcados para revisión humana.

**Prueba de validación:** La comparación entre la clasificación léxica y las recomendaciones del modelo reveló un 97% de concordancia en los casos fronterizos. Las discrepancias (12 exclusiones sugeridas y 6 casos dudosos) fueron incorporadas como insumos para la revisión humana y no como decisiones definitivas, preservando el principio de priorizar la inclusión en la zona gris.

### 5. Revisión humana de zonas grises

**Propósito:** Decidir la clasificación final de los casos frontera que no pudieron ser resueltos automáticamente.

**Procedimiento:**
- Se generó una lista de 26 puntos frontera compuesta por: 16 casos marcados como DUDOSO por el LLM, 4 casos híbridos "sonido y acústica" y 6 casos de educación artística pura.
- Se desarrolló una aplicación HTML de un solo archivo para la revisión manual, que presentó los casos con su nombre normalizado e instituciones asociadas, permitiendo decidir INCLUIR (con selector de las 9 categorías del dominio) o EXCLUIR.
- La decisión humana priorizó la inclusión en casos de duda razonable.

**Resultados finales:** De los 26 casos revisados, 13 fueron incluidos (distribuidos en las categorías de Gestión Cultural, Producción Musical y Sonido, y Otros) y 13 excluidos (principalmente programas de artes visuales y educación artística sin mención musical).

**Prueba de validación:** La trazabilidad completa del proceso (desde la clasificación léxica hasta la decisión humana) fue registrada en archivos CSV intermedios y logs de ejecución, permitiendo la reproducción exacta del flujo de clasificación.

---

## Notas metodológicas

### Citas del modelo

El modelo de lenguaje utilizado fue Ministral-3-14B, accesado vía la API de Blablador (Jülich Research Centre, 2025). La configuración incluyó lotes de 25 nombres, formato JSON para respuestas estructuradas, y reintentos con retroceso exponencial para fallos transitorios.

### Reproducibilidad

El código fuente del pipeline de clasificación está disponible en el repositorio del proyecto. Los logs de ejecución, archivos intermedios y productos finales se encuentran en las carpetas `logs/`, `prod/` y `.scratch/` respectivamente.

### Ética de la IA

El uso del LLM fue estrictamente asistivo: el modelo proporcionó recomendaciones de clasificación que fueron validadas por revisión humana en los casos frontera. Las decisiones definitivas de inclusión/exclusión en zonas ambiguas fueron tomadas por investigadores humanos, preservando el principio de priorizar la inclusión cuando existía duda razonable.

### Limitaciones

1. **Tasa de error del LLM:** El 3% de consultas que retornaron errores de parseo (2 de 67) fue manejado manteniendo la clasificación léxica original y marcando los casos para revisión humana.

2. **Muestreo en verificaciones:** Las pruebas de falsos negativos y positivos se realizaron sobre muestras (84 y 67 casos respectivamente) y no sobre la totalidad de la base, lo que introduce un margen de incertidumbre residual.

3. **Dependencia del léxico:** La clasificación léxica inicial depende de la exhaustividad del vocabulario construido (69 términos de inclusión, 47 de exclusión), que fue iterativamente refinado pero podría no cubrir todas las variaciones terminológicas posibles.

4. **Subjetividad en zonas grises:** Los 26 casos remitidos a revisión humana implican un juicio subjetivo que, aunque documentado y trazable, no es completamente reproducible sin acceso a los mismos criterios de decisión.
