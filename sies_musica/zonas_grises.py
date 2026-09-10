"""Zonas grises para la revisión humana (seam puro, etapa 06).

A partir de la clasificación final (tras las pasadas de falsos negativos y
positivos), reúne los puntos frontera — los que quedaron ``DUDOSO`` — en
``prod/zonas_grises.csv``, cada uno con su veredicto, método, razón y una
etiqueta de origen. El mismo listado sirve de base para
``prod/zonas_grises_revisadas.csv``: un template que agrega las columnas
``decision_final`` y ``categoria_final`` vacías para que el humano registre su
decisión por punto (INCLUIR con categoría, o EXCLUIR). Como la decisión humana
no itera sobre el LLM, ``escribir_revision`` no pisa un archivo ya existente
para no perder decisiones en marcha.

La etiqueta de origen explica por qué cayó cada punto a la zona gris: un
``DUDOSO`` del LLM (método ``llm``), un híbrido "sonido y acústica", una
educación artística pura (sin mención de música) o un ambiguo no clasificable.
"""

import csv
from collections import Counter
from pathlib import Path

from sies_musica.clasificador import (
    METODO_LLM,
    ORIGEN_EDUCACION_ARTISTICA as RAZON_EDUCACION_ARTISTICA,
    ORIGEN_HIBRIDO_SONIDO_ACUSTICA as RAZON_HIBRIDO_SONIDO_ACUSTICA,
    VEREDICTO_DUDOSO,
    ResultadoClasificacion,
)

ORIGEN_LLM = "DUDOSO del LLM"
ORIGEN_HIBRIDO = RAZON_HIBRIDO_SONIDO_ACUSTICA
ORIGEN_EDUCACION_ARTISTICA = RAZON_EDUCACION_ARTISTICA
ORIGEN_AMBIGUO = "Ambiguo no clasificable"

DECISION_INCLUIR = "INCLUIR"
DECISION_EXCLUIR = "EXCLUIR"

COLUMNAS_ZONAS_GRISES = [
    "nombre_normalizado",
    "nombre_original",
    "veredicto",
    "categoria",
    "metodo",
    "razon",
    "origen",
]

COLUMNAS_REVISADAS = COLUMNAS_ZONAS_GRISES + ["decision_final", "categoria_final"]


def seleccionar_zonas_grises(
    clasificacion: dict[str, ResultadoClasificacion],
) -> list[str]:
    """Nombres con veredicto ``DUDOSO``, ordenados: son los puntos frontera."""
    return sorted(
        nombre
        for nombre, res in clasificacion.items()
        if res["veredicto"] == VEREDICTO_DUDOSO
    )


def origen_de(resultado: ResultadoClasificacion) -> str:
    """Etiqueta de por qué un punto cayó en zona gris.

    El ``DUDOSO`` del LLM (método ``llm``) tiene prioridad; luego se leen las
    razones léxicas que genera el clasificador (híbrido "sonido y acústica" y
    educación artística pura) y, si ninguna aplica, se marca como ambiguo.
    Así la etiqueta no duplica las reglas del motor: si cambia una regla en
    ``clasificador``, el origen se actualiza solo.
    """
    if resultado["metodo"] == METODO_LLM:
        return ORIGEN_LLM
    if resultado["razon"].startswith(RAZON_HIBRIDO_SONIDO_ACUSTICA):
        return ORIGEN_HIBRIDO
    if resultado["razon"].startswith(RAZON_EDUCACION_ARTISTICA):
        return ORIGEN_EDUCACION_ARTISTICA
    return ORIGEN_AMBIGUO


def filas_zonas_grises(
    clasificacion: dict[str, ResultadoClasificacion],
    originales: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Filas de las zonas grises para escribir el CSV.

    ``originales`` mapea nombre_normalizado → nombre_original (para que el
    humano revise con el nombre real del programa); si se omite, la columna
    queda vacía.
    """
    originales = originales or {}
    filas: list[dict[str, str]] = []
    for nombre in seleccionar_zonas_grises(clasificacion):
        res = clasificacion[nombre]
        filas.append(
            {
                "nombre_normalizado": nombre,
                "nombre_original": originales.get(nombre, ""),
                "veredicto": res["veredicto"],
                "categoria": res["categoria"],
                "metodo": res["metodo"],
                "razon": res["razon"],
                "origen": origen_de(res),
            }
        )
    return filas


def por_origen(filas: list[dict[str, str]]) -> Counter[str]:
    """Conteo de puntos por origen, para el log de la etapa."""
    return Counter(fila["origen"] for fila in filas)


def leer_originales(ruta: Path) -> dict[str, str]:
    """Mapa nombre_normalizado → nombre_original desde la clasificación parcial.

    Si la columna ``nombre_original`` no existe (clasificación sin nombres
    originales), devuelve un dict vacío.
    """
    originales: dict[str, str] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            originales[fila["nombre_normalizado"]] = fila.get("nombre_original", "")
    return originales


def escribir_zonas_grises(ruta: Path, filas: list[dict[str, str]]) -> None:
    """Escribe ``zonas_grises.csv`` en utf-8 con las columnas acordadas."""
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_ZONAS_GRISES)
        writer.writeheader()
        writer.writerows(filas)


def escribir_revision(ruta: Path, filas: list[dict[str, str]]) -> bool:
    """Escribe el template de revisión humana solo si no existe.

    Agrega las columnas ``decision_final`` y ``categoria_final`` vacías. Si el
    archivo ya existe (el humano ya está decidiendo), no lo pisa y devuelve
    ``False``.
    """
    if ruta.exists():
        return False
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_REVISADAS)
        writer.writeheader()
        for fila in filas:
            revisada = dict(fila)
            revisada["decision_final"] = ""
            revisada["categoria_final"] = ""
            writer.writerow(revisada)
    return True
