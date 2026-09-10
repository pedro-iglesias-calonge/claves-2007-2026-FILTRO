"""Ensamblado final que incorpora la revisión humana (seam puro, etapa 08).

Toma la clasificación automática (léxica + semántica + LLM, ya depurada tras
las pasadas de falsos negativos y positivos) y la fusiona con las decisiones
humanas registradas en ``prod/zonas_grises_revisadas.csv``: cada punto que el
humano decidió (INCLUIR con categoría, o EXCLUIR) sobrescribe el veredicto
automático. De ahí sale la clasificación total, que es la que manda.

El filtro reduce la matrícula completa a las filas de los programas incluidos:
porque el veredicto se aplica al nombre normalizado, se conservan todas las
filas del mismo programa (todos los años y todas las sedes), y el archivo
resultante conserva las 58 columnas originales en cp1252, como la base SIES.
"""

import csv
from pathlib import Path

import pandas as pd

from sies_musica.clasificador import (
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ResultadoClasificacion,
)
from sies_musica.lectura import ENCODING, INDICE_NOMBRE
from sies_musica.texto import normalizar_nombre
from sies_musica.zonas_grises import (
    DECISION_EXCLUIR,
    DECISION_INCLUIR,
)

METODO_HUMANO = "humano"
RAZON_DECISION_HUMANA = "Decisión humana en la revisión de zonas grises"


def leer_decisiones(ruta: Path) -> dict[str, dict[str, str]]:
    """Lee las decisiones humanas de ``zonas_grises_revisadas.csv``.

    Devuelve un dict por nombre normalizado con ``decision_final`` y
    ``categoria_final``, pero solo para los puntos que el humano decidió
    (decisión reconocida: INCLUIR o EXCLUIR). Una decisión vacía o mal escrita
    se ignora: el punto conserva su veredicto automático (DUDOSO) y, por lo
    tanto, no entra al filtro. Así el ensamblado falla cerrado — un punto sin
    decisión no se incluye por accidente.
    """
    decisiones: dict[str, dict[str, str]] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            decision = (fila.get("decision_final") or "").strip().upper()
            if decision not in (DECISION_INCLUIR, DECISION_EXCLUIR):
                continue
            decisiones[fila["nombre_normalizado"]] = {
                "decision_final": decision,
                "categoria_final": (fila.get("categoria_final") or "").strip(),
            }
    return decisiones


def fusionar_revision(
    clasificacion: dict[str, ResultadoClasificacion],
    decisiones: dict[str, dict[str, str]],
) -> dict[str, ResultadoClasificacion]:
    """Devuelve la clasificación total tras incorporar la revisión humana.

    Cada punto con decisión humana sobrescribe el veredicto automático:
    INCLUIR toma la categoría final decidida, el método ``humano`` y la razón
    de decisión humana; EXCLUIR queda excluido. El resto de los nombres se
    conserva intacto. No muta la clasificación de entrada.
    """
    fusionada: dict[str, ResultadoClasificacion] = {
        nombre: {
            "veredicto": res["veredicto"],
            "categoria": res["categoria"],
            "metodo": res["metodo"],
            "razon": res["razon"],
        }
        for nombre, res in clasificacion.items()
    }
    for nombre, decision in decisiones.items():
        if decision["decision_final"] == DECISION_INCLUIR:
            veredicto = VEREDICTO_INCLUIR
        else:
            veredicto = VEREDICTO_EXCLUIR
        fusionada[nombre] = {
            "veredicto": veredicto,
            "categoria": decision["categoria_final"],
            "metodo": METODO_HUMANO,
            "razon": RAZON_DECISION_HUMANA,
        }
    return fusionada


def seleccionar_incluidos(
    clasificacion: dict[str, ResultadoClasificacion],
) -> list[str]:
    """Nombres con veredicto final ``INCLUIR``, ordenados alfabéticamente."""
    return sorted(
        nombre
        for nombre, res in clasificacion.items()
        if res["veredicto"] == VEREDICTO_INCLUIR
    )


def filtrar_matricula(
    df: pd.DataFrame, incluidos: list[str] | set[str]
) -> pd.DataFrame:
    """Reduce la matrícula a las filas de los programas incluidos.

    El filtro compara por nombre normalizado, la regla de la cadena: el
    veredicto se aplica a todas las filas del programa, de modo que se
    conservan todos los años y todas las sedes (y se pierden los excluidos).
    """
    incluidos = set(incluidos)
    mascara = df.iloc[:, INDICE_NOMBRE].map(normalizar_nombre).isin(incluidos)
    return df.loc[mascara].copy()


def escribir_filtrado(ruta: Path, df: pd.DataFrame) -> None:
    """Escribe el archivo filtrado en el mismo formato de la base SIES.

    58 columnas originales, separador ``;``, encoding cp1252 y salto de línea
    CRLF: un subconjunto de filas del archivo maestro, legible por las mismas
    herramientas. Como la base solo cita los campos que lo necesitan, se
    replica ese formato (comillas mínimas). Se usa ``errors='replace'`` para
    que los pocos caracteres que cp1252 no puede codificar no aborten la
    escritura; el DF ya llega saneado de la lectura.
    """
    df.to_csv(
        ruta,
        sep=";",
        index=False,
        lineterminator="\r\n",
        encoding=ENCODING,
        errors="replace",
    )