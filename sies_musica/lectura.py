"""Lectura robusta del CSV de matrícula y verificación de integridad.

El archivo SIES usa encoding cp1252, separador `;`, cabecera presente y
acceso a columnas por índice (el acceso por nombre falla por desajuste de
acentos). El encoding tiene bytes no decodificables (0x90) que se leen con
`encoding_errors='replace'`.
"""

from pathlib import Path
from typing import TypedDict

import pandas as pd

from sies_musica.texto import normalizar_nombre

ENCODING = "cp1252"
INDICE_ANIO = 0
INDICE_NOMBRE = 19
INDICE_CODIGO = 34


class ReporteIntegridad(TypedDict):
    encoding: str
    bom_utf8: bool
    bytes_no_decodificables: int
    cabecera_anio_ok: bool
    filas: int
    columnas: int
    anios: list[str]
    nombres_unicos_normalizados: int
    codigos_unicos: int


def leer_matricula(ruta: str | Path) -> pd.DataFrame:
    """Lee el CSV de matrícula SIES (cp1252, `;`, cabecera presente).

    Verifica el encoding contra los bytes del archivo y guarda el resultado
    en ``df.attrs["encoding"]`` para que lo use el reporte de integridad.
    """
    ruta = Path(ruta)
    raw = ruta.read_bytes()
    decodificado = raw.decode(ENCODING, errors="replace")
    df = pd.read_csv(
        ruta,
        sep=";",
        encoding=ENCODING,
        encoding_errors="replace",
        dtype=str,
        keep_default_na=False,
    )
    df.attrs["encoding"] = {
        "encoding": ENCODING,
        "bom_utf8": raw.startswith(b"\xef\xbb\xbf"),
        "bytes_no_decodificables": decodificado.count("\ufffd"),
        "cabecera_anio_ok": decodificado.split(";")[0] == "AÑO",
    }
    return df


def reporte_integridad(df: pd.DataFrame) -> ReporteIntegridad:
    """Resume la integridad de la base: filas, columnas, años, unicidad y encoding."""
    nombres = df.iloc[:, INDICE_NOMBRE]
    codigos = df.iloc[:, INDICE_CODIGO]
    anios = sorted(
        {str(a) for a in df.iloc[:, INDICE_ANIO].unique() if str(a).startswith("MAT_")}
    )
    nombres_normalizados = [
        normalizar_nombre(str(n)) for n in nombres if str(n).strip()
    ]
    return {
        "encoding": df.attrs["encoding"]["encoding"],
        "bom_utf8": df.attrs["encoding"]["bom_utf8"],
        "bytes_no_decodificables": df.attrs["encoding"]["bytes_no_decodificables"],
        "cabecera_anio_ok": df.attrs["encoding"]["cabecera_anio_ok"],
        "filas": len(df),
        "columnas": df.shape[1],
        "anios": anios,
        "nombres_unicos_normalizados": len(set(nombres_normalizados)),
        "codigos_unicos": int((codigos[codigos.str.strip() != ""]).nunique()),
    }