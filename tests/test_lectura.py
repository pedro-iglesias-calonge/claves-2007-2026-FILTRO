"""Tests de la lectura robusta del CSV y del reporte de integridad."""

from pathlib import Path

import pytest

from sies_musica.lectura import (
    ENCODING,
    INDICE_ANIO,
    INDICE_CODIGO,
    INDICE_NOMBRE,
    leer_matricula,
    reporte_integridad,
)
from tests.conftest import _fila, escribir_csv, inyectar_byte_invalido


def test_leer_matricula_filas_y_columnas(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    assert df.shape == (4, 58)


def test_leer_matricula_anio_por_indice(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    assert df.iloc[0, INDICE_ANIO] == "MAT_2007"
    assert df.iloc[3, INDICE_ANIO] == "MAT_2026"


def test_leer_matricula_nombre_y_codigo_por_indice(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    assert df.iloc[0, INDICE_NOMBRE] == "Composición Musical"
    assert df.iloc[0, INDICE_CODIGO] == "A001"
    assert df.iloc[3, INDICE_NOMBRE] == "Ingeniería Comercial"


def test_leer_matricula_maneja_byte_invalido(tmp_path: Path):
    ruta = escribir_csv(tmp_path / "invalido.csv", [_fila("MAT_2020", "Ingeniería Comercial", "X001")])
    inyectar_byte_invalido(ruta)
    df = leer_matricula(ruta)
    assert df.shape[1] == 58
    assert len(df) == 1


def test_reporte_integridad_filas_columnas(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    reporte = reporte_integridad(df)
    assert reporte["filas"] == 4
    assert reporte["columnas"] == 58


def test_reporte_integridad_anios(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    reporte = reporte_integridad(df)
    assert reporte["anios"] == ["MAT_2007", "MAT_2026"]


def test_reporte_integridad_nombres_unicos_normalizados(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    reporte = reporte_integridad(df)
    assert reporte["nombres_unicos_normalizados"] == 3


def test_reporte_integridad_codigos_unicos(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    reporte = reporte_integridad(df)
    assert reporte["codigos_unicos"] == 4


def test_reporte_integridad_encoding(matricula_csv: Path):
    df = leer_matricula(matricula_csv)
    reporte = reporte_integridad(df)
    assert reporte["encoding"] == ENCODING
    assert reporte["bom_utf8"] is False
    assert reporte["cabecera_anio_ok"] is True


def test_reporte_integridad_codigos_vacios_se_ignoran(tmp_path: Path):
    fila_con_vacio = _fila("MAT_2010", "Música", "C001")
    fila_con_vacio[INDICE_CODIGO] = ""
    ruta = escribir_csv(tmp_path / "codigos.csv", [fila_con_vacio, _fila("MAT_2010", "Música", "C002")])
    df = leer_matricula(ruta)
    reporte = reporte_integridad(df)
    assert reporte["codigos_unicos"] == 1


def test_reporte_integridad_anios_solo_mat(tmp_path: Path):
    fila = _fila("MAT_2007", "Música", "C001")
    fila[0] = "2007"
    ruta = escribir_csv(tmp_path / "anios.csv", [fila, _fila("MAT_2026", "Piano", "C002")])
    df = leer_matricula(ruta)
    reporte = reporte_integridad(df)
    assert reporte["anios"] == ["MAT_2026"]


def test_reporte_integridad_byte_invalido_marca_reemplazo(tmp_path: Path):
    ruta = escribir_csv(tmp_path / "inv2.csv", [_fila("MAT_2020", "Ingeniería Comercial", "X001")])
    inyectar_byte_invalido(ruta)
    df = leer_matricula(ruta)
    reporte = reporte_integridad(df)
    assert reporte["bytes_no_decodificables"] == 1