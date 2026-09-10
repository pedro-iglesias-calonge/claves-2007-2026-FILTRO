# Etapa 03 — Cliente LLM (Ollama): prueba de humo

Inicio: 2026-08-11 09:22:33
Fin: 2026-08-11 09:26:51
Modelo: `gpt-oss:20b` vía Ollama en `localhost:11434`, lotes de 25.

## Indicadores

- Nombres consultados (muestra): 50
- Veredictos ERROR (fallos del servidor o de parseo): 1

### Por veredicto del LLM

- INCLUIR: 4
- EXCLUIR: 39
- DUDOSO: 6
- ERROR: 1

### Razones de error

- Nombre 'ingenieria comercial mencion economia' ausente en la respuesta del LLM

Resultados en `prod/verificacion_llm_demo.csv`.
