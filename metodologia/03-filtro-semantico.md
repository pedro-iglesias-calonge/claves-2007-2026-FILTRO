# Etapa 03 — El filtro semántico: cuando el nombre se explica con contexto

_Enfoque humanista: hay nombres que no se dicen a sí mismos. Un programa llamado "educación artística" no aclara si su alma es la música, la pintura o la danza. Para entenderlo hay que mirar dónde está parado dentro de la base: su área y su subárea._

## Qué se hizo

Se construyó un **filtro semántico** (sin modelos de lenguaje, con reglas sobre los datos) que rescata o descarta programas cuyo nombre no porta una señal léxica de música. Para ello usa las columnas auxiliares que la base entrega para cada programa:

- **ÁREA CARRERA GENÉRICA**, con dos valores que anuncian el mundo musical: *"Música, Canto o Danza"* y *"Pedagogía en Artes y Música"*.
- **Subárea CINE** (la clasificación internacional de la educación), cuando su valor es *Artes*.

La lógica es de **desambiguación por mención**: si el contexto musical confirma un programa cuyo nombre no lo dice, se incluye; si el contexto es solo "Artes" sin señal musical, se excluye; si el nombre es un arte general sin mención, queda en zona gris.

El motor agrega el contexto **por nombre único normalizado**: como un mismo nombre de carrera puede aparecer en muchas filas (años, sedes), se reúnen las áreas y subáreas de todas sus apariciones antes de decidir. Así el veredicto es uno solo por nombre y se aplica a todas sus filas (dedupe).

## Qué se descubrió

Al aplicar el filtro semántico a los 16.684 nombres únicos:

- **160 nombres** que no tenían señal léxica de música pero viven en la subárea CINE *Artes* fueron examinados por contexto. Todos resultaron ser de otras artes (actuación, animación, diseño, etc.) y se **excluyeron** con razón fundada en el contexto: *"subárea CINE Artes sin señal musical en el nombre"*.
- Los nombres de las **áreas musicales** ya habían sido capturados por el filtro léxico: todos los programas con área *"Música, Canto o Danza"* o *"Pedagogía en Artes y Música"* que no pasaron el filtro léxico eran de danza o artes visuales (exclusiones fuertes correctas) o de educación artística (zona gris).
- La zona gris de la etapa léxica **no se decide en esta etapa**: los híbridos "sonido y acústica" y la "educación artística" pura siguen siendo candidatos a revisión humana.

## Por qué importa para el resto del estudio

1. El filtro semántico cierra el universo **sin falsos negativos por silencio del nombre**: ningún programa musical queda fuera solo porque su nombre no diga "música".
2. También evita **falsos positivos**: un nombre en la subárea *Artes* no es, por estar ahí, un programa musical.
3. La decisión queda **auditable**: cada nombre excluido por contexto tiene su razón registrada.
4. Solo quedan para revisión humana los casos que ni la palabra ni el contexto resuelven: los candidatos de la zona gris.

## Registro

El filtro semántico vive en `sies_musica/clasificador.py` (función `clasificar` con contexto opcional), se prueba en `tests/test_clasificador.py`, y la corrida completa con agregación por nombre está en `scripts/02_clasificacion.py`, con resultados en `prod/clasificacion_parcial.csv` y `logs/02-clasificacion.md`.
