# Etapa 04 — Verificación de falsos negativos con LLM

Inicio: 2026-08-11 22:30:39
Fin: 2026-08-11 22:31:12
Modelo: `alias-fast` (Ministral-3-14B) vía Blablador (`api.blablador.fz-juelich.de`), lotes de 25.

## Indicadores

- Nombres consultados: 84
  - Red de candidatos (áreas musicales sin keyword, dedupe): 34
  - Muestra aleatoria de control (excluidos): 50
- Nombres incorporados a la clasificación (INCLUIR del LLM): 0
- Veredictos ERROR (fallos de servidor o de parseo): 0

### Por veredicto del LLM

- INCLUIR: 0
- EXCLUIR: 84
- DUDOSO: 0
- ERROR: 0

Resultados en `prod/verificacion_falsos_negativos_cloud.csv`.
Clasificación actualizada en `prod/clasificacion_tras_falsos_negativos_cloud.csv`.
