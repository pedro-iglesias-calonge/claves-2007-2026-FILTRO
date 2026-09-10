# Etapa 01 — Conocimiento de la fuente

_Enfoque humanista: lo que se narra no es un tecnicismo, sino el primer gesto de honestidad del estudio: enterarse de qué es exactamente el material con el que se va a trabajar antes de tocarlo._

## Qué se hizo

Antes de buscar los programas musicales, se examinó el archivo que contiene la matrícula de Educación Superior de Chile entre 2007 y 2026. El propósito de esta etapa no fue todavía filtrar, sino **entender la fuente**: su idioma (la codificación de los caracteres), su estructura (cuántas columnas y filas) y sus señas de identidad (años cubiertos, cuántos nombres de carrera distintos existen y cuántos códigos de carrera distintos).

## Qué se descubrió

- **Idioma del archivo.** Los datos están escritos en codificación `cp1252` (un estándar de Windows en el que la letra Ñ tiene su propio marcador). Se confirmó que no hay un "marcador de inicio" (BOM) de codificación UTF-8, lo que descarta confusiones de lectura. Existen 5 símbolos aislados que la codificación no puede interpretar; para no perder ninguna fila, esos 5 símbolos se leen con un carácter de reemplazo y se deja constancia de ellos.
- **Estructura.** El archivo tiene **58 columnas** y **280.160 filas** de matrícula: una fila por combinación de año, institución, sede y carrera.
- **Tiempo cubierto.** Los 20 años están presentes, desde `MAT_2007` hasta `MAT_2026`.
- **Diversidad de la oferta.** Hay **16.684 nombres de carrera distintos** (normalizados: en minúsculas y sin tildes, para que "Composición Musical" y "composición musical" cuenten como una sola cosa) y **54.426 códigos de carrera distintos**. Que haya más códigos que nombres significa que el mismo nombre de carrera, correctamente escrito, puede corresponder a carreras de distintas instituciones con códigos propios.

## Por qué importa para el resto del estudio

Esta etapa fija las reglas del juego para todo lo que sigue:

1. La lectura se hace respetando el idioma del archivo (`cp1252`), para no corromper los nombres.
2. El acceso a los campos es por **posición de columna**, no por nombre, porque los nombres de las columnas llevan tildes y espacios que varían.
3. La **unidad de decisión** será el nombre de carrera normalizado: lo que se decida sobre un nombre se aplicará a todas sus filas (todos los años y todas las sedes que lo usan).
4. Queda registro permanente de estos indicadores en el log de la etapa, para que cualquier lector pueda confirmar que se trabajó sobre la fuente completa y sin alteraciones.

## Registro

Los indicadores numéricos exactos de esta verificación quedan en `logs/01-integridad.md`, y la rutina que los produce en `scripts/01_integridad.py` (apoyada en `sies_musica/lectura.py`). La verificación fue automatizada con pruebas que garantizan que la lectura respeta el idioma del archivo, que cuenta correctamente filas, columnas, años y unicidades, y que tolera los 5 símbolos no interpretables sin perder ninguna fila.