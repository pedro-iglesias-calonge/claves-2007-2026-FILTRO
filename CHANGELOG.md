# Historial de cambios

Todas las fechas están en formato ISO 8601 (`AAAA-MM-DD`). Este proyecto sigue
el versionado semántico (SemVer).

## [1.0.0] - 2026-09-10

Primera versión pública del procedimiento y sus productos.

### Añadido

- Pipeline completo de filtrado en ocho etapas (`scripts/01` a `scripts/08`).
- Paquete `sies_musica/` con el clasificador léxico y semántico, la lectura
  robusta del CSV, el cliente LLM, la verificación y el ensamblado.
- Documentación metodológica (`metodologia/00` a `08`), paso a paso del procedimiento
  para el artículo académico.
- Registros de corrida por etapa (`logs/`).
- Productos finales: `prod/Musica_2007_2026_filtrado.csv` (2.664 filas, 58
  columnas, `cp1252`) y `prod/clasificacion_total.csv` (215 programas
  incluidos).
- Revisión humana de las 26 zonas grises (13 INCLUIR / 13 EXCLUIR) y la
  aplicación HTML de apoyo.
- Pruebas automatizadas con `pytest`.
- Metadatos académicos: `CITATION.cff`, licencias MIT y CC BY 4.0,
  `CONTRIBUTING.md`.
