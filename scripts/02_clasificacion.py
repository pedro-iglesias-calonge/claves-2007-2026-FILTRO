"""Etapa 02 — Motor de clasificación: filtro léxico y semántico sobre la base real.

Clasifica los 16.684 nombres únicos normalizados de la base y escribe la
clasificación parcial (veredicto, categoría, método y razón por nombre) en
``prod/``, con el resumen de la corrida en ``logs/``.
"""

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from sies_musica.clasificador import clasificar
from sies_musica.lectura import leer_matricula
from sies_musica.texto import normalizar_nombre

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BASE = RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_parcial.csv"
RUTA_LOG = RAIZ / "logs" / "02-clasificacion.md"

INDICE_NOMBRE = 19
INDICE_SUBAREA_1997 = 22
INDICE_AREA_GENERICA = 23
INDICE_SUBAREA_2013 = 25

COLUMNAS_SALIDA = [
    "nombre_normalizado",
    "nombre_original",
    "veredicto",
    "categoria",
    "metodo",
    "razon",
]


def _contexto_por_nombre(
    df: pd.DataFrame,
) -> tuple[dict[str, dict[str, list[str]]], dict[str, str]]:
    """Agrega, por nombre normalizado, las áreas y subáreas CINE de sus filas.

    Devuelve el contexto (áreas y subáreas únicas) y un nombre original de
    ejemplo por cada nombre normalizado.
    """
    contexto: dict[str, dict[str, list[str]]] = {}
    original: dict[str, str] = {}
    for _, fila in df.iterrows():
        nombre = normalizar_nombre(str(fila.iloc[INDICE_NOMBRE]))
        if not nombre.strip():
            continue
        if nombre not in contexto:
            contexto[nombre] = {"areas_genericas": [], "subareas_cine": []}
            original[nombre] = str(fila.iloc[INDICE_NOMBRE])
        area = str(fila.iloc[INDICE_AREA_GENERICA]).strip()
        if area and normalizar_nombre(area) not in contexto[nombre]["areas_genericas"]:
            contexto[nombre]["areas_genericas"].append(normalizar_nombre(area))
        for indice_subarea in (INDICE_SUBAREA_1997, INDICE_SUBAREA_2013):
            subarea = str(fila.iloc[indice_subarea]).strip()
            if subarea and normalizar_nombre(subarea) not in contexto[nombre]["subareas_cine"]:
                contexto[nombre]["subareas_cine"].append(normalizar_nombre(subarea))
    return contexto, original


def _a_markdown(
    total: int, por_veredicto: Counter, por_categoria: Counter, por_metodo: Counter
) -> str:
    filas = []
    filas.append("# Etapa 02 — Motor de clasificación (filtro léxico y semántico)")
    filas.append("")
    hoy = datetime.now()
    filas.append(f"Generado: {hoy.year}-{hoy.month:02d}-{hoy.day:02d}")
    filas.append(f"Archivo: `Matricula_2007_2026_WEB_10_07_2026.csv`")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"- Nombres únicos normalizados clasificados: {total}")
    filas.append("")
    filas.append("### Por veredicto")
    filas.append("")
    for veredicto in ("INCLUIR", "EXCLUIR", "DUDOSO"):
        filas.append(f"- {veredicto}: {por_veredicto[veredicto]}")
    filas.append("")
    filas.append("### Por categoría (solo INCLUIR)")
    filas.append("")
    for categoria, conteo in por_categoria.most_common():
        filas.append(f"- {categoria}: {conteo}")
    filas.append("")
    filas.append("### Por método")
    filas.append("")
    for metodo in ("lexico", "semantico"):
        filas.append(f"- {metodo}: {por_metodo[metodo]}")
    filas.append("")
    filas.append("Clasificación parcial en `prod/clasificacion_parcial.csv`.")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    df = leer_matricula(RUTA_BASE)
    contexto, original = _contexto_por_nombre(df)

    RUTA_CLASIFICACION.parent.mkdir(parents=True, exist_ok=True)
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)

    por_veredicto: Counter[str] = Counter()
    por_categoria: Counter[str] = Counter()
    por_metodo: Counter[str] = Counter()

    with open(RUTA_CLASIFICACION, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_SALIDA)
        writer.writeheader()
        for nombre, ctx in sorted(contexto.items()):
            resultado = clasificar(nombre, ctx)
            por_veredicto[resultado["veredicto"]] += 1
            por_metodo[resultado["metodo"]] += 1
            if resultado["veredicto"] == "INCLUIR":
                por_categoria[resultado["categoria"]] += 1
            writer.writerow(
                {
                    "nombre_normalizado": nombre,
                    "nombre_original": original[nombre],
                    "veredicto": resultado["veredicto"],
                    "categoria": resultado["categoria"],
                    "metodo": resultado["metodo"],
                    "razon": resultado["razon"],
                }
            )

    total = sum(por_veredicto.values())
    RUTA_LOG.write_text(
        _a_markdown(total, por_veredicto, por_categoria, por_metodo),
        encoding="utf-8",
    )
    print(RUTA_CLASIFICACION)
    print(RUTA_LOG)
    print(f"Total: {total} | INCLUIR: {por_veredicto['INCLUIR']} | "
          f"EXCLUIR: {por_veredicto['EXCLUIR']} | DUDOSO: {por_veredicto['DUDOSO']}")


if __name__ == "__main__":
    main()
