# Registro de corridas — SIES Música 2007-2026

Carpeta de **logs**: el registro duro de cada corrida (script → resultados → marcado). Cada log lista el script que lo generó, los veredictos por etapa, y las rutas de los resultados en `prod/`.

Cada corrida se corresponde con un script de `scripts/` y una etapa documentada en lenguaje humano en `metodologia/`. El mapa completo está en `../metodologia/00-sintesis.md`.

## Índice de corridas

| Etapa | Log | Contenido |
|-------|-----|-----------|
| 01 | `01-integridad.md` | Verificación de integridad de la matrícula: filas, columnas, años, nombres y códigos únicos, bytes no decodificables. |
| 02 | `02-clasificacion.md` | Clasificación léxica + semántica (parcial): INCLUIR / EXCLUIR / DUDOSO por método y categoría. |
| 03 | `03-cliente-llm.md` | Prueba del cliente LLM (smoke test de 50 nombres, gpt-oss:20b local). |
| 04 | `04-verificacion-falsos-negativos.md` | Verificación de falsos negativos (LLM local): red de candidatos + control. |
| 04 | `04-verificacion-falsos-negativos-cloud.md` | La misma corrida en la nube (`alias-fast` / Blablador). |
| 05 | `05-verificacion-falsos-positivos.md` | Verificación de falsos positivos (LLM local): incluidos fronterizos. |
| 05 | `05-verificacion-falsos-positivos-cloud.md` | La misma corrida en la nube. |
| 06 | `06-zonas-grises.md` | Generación de zonas grises para la revisión humana (26 puntos). |
| 07 | `07-revision-humana.md` | Revisión humana de las zonas grises y sus decisiones (13 INCLUIR / 13 EXCLUIR). |
| 08 | `08-ensamblado-final.md` | Ensamblado final: clasificación total y matrícula filtrada `prod/Musica_2007_2026_filtrado.csv`. |

## Convenciones

- Los logs usan encoding **utf-8**.
- Las rutas a `prod/` se anotan **relativas a la raíz del repo** (p. ej. `prod/clasificacion_parcial.csv`), con separadores `/`.
- Cada log registra **Inicio** y **Fin** de la corrida, salvo la revisión humana (etapa 07), que es un proceso manual.