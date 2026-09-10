# Etapa 05 — Verificación de falsos positivos con LLM

Inicio: 2026-08-11 19:50:19
Fin: 2026-08-11 19:58:09
Modelo: `gpt-oss:20b` vía Ollama en `localhost:11434`, lotes de 25.

## Indicadores

- Incluidos fronterizos consultados: 67
- Retirados de la inclusión (EXCLUIR del LLM): 0
- Marcados para zonas grises (DUDOSO del LLM): 15
- Veredictos ERROR (fallos de servidor o de parseo): 0

### Por veredicto del LLM

- INCLUIR: 52
- EXCLUIR: 0
- DUDOSO: 15
- ERROR: 0

### Marcados para zonas grises (método `llm`, sin re-consultar)

- diploma de postitulo en comunicacion y gestion cultural
- diploma de postitulo en gestion cultural
- diploma de postitulo en gestion cultural comunitaria y politicas culturales
- diplomado en gestion cultural
- diplomado en gestion cultural mencion administracion de organizaciones culturales
- diplomado en gestion cultural mencion educacion artistica o mediacion lectora
- diplomado en gestion cultural publica y privada
- diplomado en gestion cultural vinculado a la educacion
- diplomado en gestion y autogestion cultural
- diplomado gestion cultural del patrimonio
- magister en patrimonio y gestion cultural
- sonido
- tecnico en arte y gestion cultural
- tecnico en artes y gestion cultural
- tecnologia en sonido e iluminacion

Resultados en `prod/verificacion_falsos_positivos.csv`.
Clasificación actualizada en `prod/clasificacion_tras_falsos_positivos.csv`.
