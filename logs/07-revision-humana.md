# Etapa 07 — Revisión humana de zonas grises

Revisión: 2026-08-11, tras la etapa 06 (generación de zonas grises) y antes del ensamblado final (etapa 08).

## Indicadores

Puntos frontera revisados por una persona: 26

### Por origen

- DUDOSO del LLM: 16
- Educación artística pura: 6
- Híbrido 'sonido y acústica': 4
- Ambiguo no clasificable: 0

### Por decisión humana

- INCLUIR: 13
- EXCLUIR: 13

### Categoría asignada al incluir

- Pedagogía en música: 5
- Producción musical y sonido: 4
- Gestión cultural: 2
- Sin categoría: 2

## Cómo se decidió

Los 26 puntos se revisaron con la aplicación `prod/revisar_zonas_grises.html`: cada punto muestra su **nombre normalizado** y sus **instituciones**; la persona decide **INCLUIR** (con selector de las 9 categorías) o **EXCLUIR**, y el avance se exporta al CSV de decisiones.

Decisiones registradas en `prod/zonas_grises_revisadas.csv` (9 columnas, utf-8 sin BOM, no se pisan las decisiones al regenerar).

## En el ensamblado

Cada decisión humana se aplica a la clasificación final con la razón `Decisión humana en la revisión de zonas grises` y método `humano` (etapa 08).

Generador de la aplicación: `scripts/07_generar_app_revision.py`.
