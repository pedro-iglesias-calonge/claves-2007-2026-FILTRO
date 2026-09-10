# Etapa 06 — Zonas grises para revisión humana

Inicio: 2026-08-11 23:14:01
Fin: 2026-08-11 23:14:01

## Indicadores

Puntos frontera hacia la revisión humana: 26

### Por origen

- DUDOSO del LLM: 16
- Híbrido 'sonido y acústica': 4
- Educación artística pura: 6
- Ambiguo no clasificable: 0

Clasificación de entrada: `prod/clasificacion_tras_falsos_positivos.csv`.
Template de revisión humana: ya existía: no se pisó para no perder decisiones humanas.

Resultados en `prod/zonas_grises.csv`.
Revisión humana en `prod/zonas_grises_revisadas.csv`.

## Aplicación HTML de revisión

Para la decisión humana se generó además `prod/revisar_zonas_grises.html`: una aplicación de un solo archivo (sin servidor) que lista los 26 puntos frontera con su **nombre normalizado e instituciones**, y permite decidir **INCLUIR** (con selector de las 9 categorías) o **EXCLUIR** por punto. El avance se guarda solo en el navegador, y el botón *Descargar CSV* exporta `prod/zonas_grises_revisadas.csv` en el formato del template (9 columnas, utf-8 sin BOM, sin pisar las decisiones ya anotadas al regenerar).

Generador: `scripts/07_generar_app_revision.py`.
