# SIES — Programas de Música

Contexto: filtro de la base de matrícula SIES 2007–2026 (Chile, educación superior) para extraer los programas vinculados a la música, con precisión 100% (sin falsos positivos ni falsos negativos), priorizando la inclusión en las zonas ambiguas y delegando la decisión final a revisión humana.

## Language

**Programa**:
Unidad de oferta académica en la base SIES: fila identificada por su `NOMBRE CARRERA` (y desambiguada por `CÓDIGO CARRERA`). La clasificación se decide por el nombre único normalizado y se aplica a todas sus filas.
_Avoid_: carrera (ambiguo entre programa y nombre)

**Nombre normalizado**:
El `NOMBRE CARRERA` en minúsculas, sin tildes (p. ej. `composicion musical`). Es la unidad de decisión para clasificar.
_Avoid_: nombre original, nombre crudo

**Programa musical**:
Todo programa cuyo objeto de estudio es la música en cualquiera de sus dimensiones: docencia, composición, interpretación, teoría/investigación, formación general, producción de sonido, terapia o gestión.
_Avoid_: carrera de música (restringe a un subtipo)

**Interpretación (musical)**:
Dimensión que incluye instrumentos, canto, dirección de conjuntos (orquestas, coros, bandas) y teatro musical. Solo es musical si el nombre lo expresa explícitamente.
_Avoid_: ejecución (poco usado en los nombres), interpretación (ambigua por sí sola)

**Zona gris**:
Programa sin veredicto automático claro; va a revisión humana. La inclusión se prioriza provisionalmente sobre la exclusión.
_Avoid_: ambiguo (no señala el procedimiento), dubitativo

## Categorías

**Pedagogía en música**: formación docente musical. Excluye pedagogía en artes visuales, danza, teatro sin mención musical.

**Composición y arreglos**: composición musical y arreglos de música popular.

**Interpretación musical**: instrumentos, canto, dirección de conjuntos u orquestas/coros, teatro musical.

**Teoría, musicología e investigación**: teoría musical, musicología, investigación musical.

**Formación musical general**: licenciaturas y bachilleratos en música (no sólo una mención).

**Producción musical y sonido**: ingeniería/técnico en sonido, música y tecnología en sonido, producción musical. Incluye los híbridos "sonido y acústica" (el sonido se privilegia; la acústica técnica queda en zona gris).

**Musicoterapia**: musicoterapia y terapias de arte con mención musicoterapia. Excluye el resto de terapias (clínicas, psicoterapia).

**Gestión cultural**: gestión cultural, se incluye como categoría propia (toda la gestión cultural).

**Otros**: categoría de reserva para programas musicales inclasificables; se revisa en zonas grises.

## Procedimiento (acordado)

- **Clasificación por nombre único normalizado**; el veredicto se aplica a todas sus filas (años, sedes).
- **Zonas grises** (sin veredicto automático) van a `zonas_grises.csv` para revisión humana final, sin iterar.
- **LLM**: `alias-fast` (Ministral-3-14B) vía Blablador (`api.blablador.fz-juelich.de`), consultas por lote de 25 nombres, respuesta tri-valor `INCLUIR/EXCLUIR/DUDOSO` con categoría y razón, una sola pasada.
  - **Nota**: Se intentó inicialmente con `gpt-oss:20b` vía Ollama en local, pero falló (2 errores en 84 consultas de falsos negativos, tiempos 12× más largos). La corrida final se realizó exclusivamente con Blablador cloud, que fue más rápido (36 seg vs 7 min 50 seg por etapa) y más conservador: retiró 12 programas de gestión cultural que el modelo local mantuvo, y marcó 6 como dudosos en vez de 15.
- **Falsos negativos**: red de nombres de las dos áreas genéricas de música sin keyword + muestra de control aleatoria de ~50 excluidos (84 nombres consultados, 0 falsos negativos encontrados).
- **Falsos positivos**: incluidos fronterizos sin señal nuclear "música"/"musical" (67 nombres consultados, 12 retirados, 6 marcados como dudosos).
- **Salidas**: carpeta de productos finales (`*_filtrado.csv`, clasificación, zonas grises), carpeta de logs en MD, y carpeta de metodología (paso a paso para artículo académico).

_Avoid_: artes escénicas, artes visuales, danza, teatro, cine (dominios de exclusión: nunca musicales salvo mención explícita "musical")

## Exclusiones (reglas fuertes, sin LLM)

- Interpretación/traducción de **idiomas** o lengua de señas (p. ej. `interprete ingles-espanol`).
- **Artes visuales/plásticas**, **danza**, **teatro** puro, **cine/audiovisual**, **acústica técnica** (edificación, ambiental, submarina, vibraciones).
- **Terapias** no musicales (clínicas, psicoterapia, ultrasonido, ecografía).
- `licenciatura en artes` **sin mención**: se excluye.
- Tecnología médica en ultrasonido, "arte" en sentido retórico (p. ej. "el arte de la persuasión").