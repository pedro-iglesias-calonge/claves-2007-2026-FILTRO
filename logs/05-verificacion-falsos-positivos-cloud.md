# Etapa 05 — Verificación de falsos positivos con LLM

Inicio: 2026-08-11 22:32:00
Fin: 2026-08-11 22:32:36
Modelo: `alias-fast` (Ministral-3-14B) vía Blablador (`api.blablador.fz-juelich.de`), lotes de 25.

## Indicadores

- Incluidos fronterizos consultados: 67
- Retirados de la inclusión (EXCLUIR del LLM): 12
- Marcados para zonas grises (DUDOSO del LLM): 6
- Veredictos ERROR (fallos de servidor o de parseo): 2

### Por veredicto del LLM

- INCLUIR: 47
- EXCLUIR: 12
- DUDOSO: 6
- ERROR: 2

### Retirados de la inclusión (método `llm`)

- diploma de postitulo en comunicacion y gestion cultural
- diploma de postitulo en gestion cultural
- diploma de postitulo en gestion cultural comunitaria y politicas culturales
- diplomado en gestion cultural
- diplomado en gestion cultural mencion administracion de organizaciones culturales
- diplomado en gestion cultural mencion educacion artistica o mediacion lectora
- diplomado en gestion cultural publica y privada
- diplomado en gestion cultural vinculado a la educacion
- diplomado en gestion y autogestion cultural
- magister en patrimonio y gestion cultural
- tecnico en arte y gestion cultural
- tecnico en artes y gestion cultural

### Marcados para zonas grises (método `llm`, sin re-consultar)

- diplomado gestion cultural del patrimonio
- gestion cultural
- magister en gestion cultural
- magister en gestion cultural aplicada
- sonido
- sonido profesional

### Razones de error

- Categoría fuera de las 9 del dominio para INCLUIR: 'Musicología e investigación'

Resultados en `prod/verificacion_falsos_positivos_cloud.csv`.
Clasificación actualizada en `prod/clasificacion_tras_falsos_positivos_cloud.csv`.
