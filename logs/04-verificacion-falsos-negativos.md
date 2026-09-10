# Etapa 04 — Verificación de falsos negativos con LLM

Inicio: 2026-08-11 19:43:53
Fin: 2026-08-11 19:50:16
Modelo: `gpt-oss:20b` vía Ollama en `localhost:11434`, lotes de 25.

## Indicadores

- Nombres consultados: 84
  - Red de candidatos (áreas musicales sin keyword, dedupe): 34
  - Muestra aleatoria de control (excluidos): 50
- Nombres incorporados a la clasificación (INCLUIR del LLM): 0
- Veredictos ERROR (fallos de servidor o de parseo): 2

### Por veredicto del LLM

- INCLUIR: 0
- EXCLUIR: 81
- DUDOSO: 1
- ERROR: 2

### Razones de error

- Nombre 'programa especial de titulacion pedagogia media en artes visuales' ausente en la respuesta del LLM
- Nombre 'tecnologia en administracion de empresas mencion marketing' ausente en la respuesta del LLM

Resultados en `prod/verificacion_falsos_negativos.csv`.
Clasificación actualizada en `prod/clasificacion_tras_falsos_negativos.csv`.
