"""Fixtures para los tests de lectura e integridad."""

import csv
from pathlib import Path

import pytest

from sies_musica.lectura import INDICE_CODIGO, INDICE_NOMBRE

# Cabecera real del CSV SIES (58 columnas), con acentos legibles (cp1252).
CABECERA = [
    "AÑO",
    "TOTAL MATRÍCULA",
    "TOTAL MATRÍCULA MUJERES",
    "TOTAL MATRÍCULA HOMBRES",
    "TOTAL MATRÍCULA NO BINARIOS O INDEFINIDOS",
    "TOTAL MATRÍCULA PRIMER AÑO",
    "TOTAL MATRÍCULA MUJERES PRIMER AÑO",
    "TOTAL MATRÍCULA HOMBRES PRIMER AÑO",
    "TOTAL MATRÍCULA NO BINARIOS O INDEFINIDOS PRIMER AÑO",
    "CLASIFICACIÓN INSTITUCIÓN NIVEL 1",
    "CLASIFICACIÓN INSTITUCIÓN NIVEL 2",
    "CLASIFICACIÓN INSTITUCIÓN NIVEL 3",
    "CÓDIGO DE INSTITUCIÓN",
    "NOMBRE INSTITUCIÓN",
    "ACREDITACIÓN INSTITUCIONAL",
    "REGIÓN",
    "PROVINCIA",
    "COMUNA",
    "NOMBRE SEDE",
    "NOMBRE CARRERA",
    "ÁREA DEL CONOCIMIENTO",
    "CINE-F 1997 ÁREA",
    "CINE-F 1997 SUBAREA",
    "ÁREA CARRERA GENÉRICA",
    "CINE-F 2013 ÁREA",
    "CINE-F 2013 SUBAREA",
    "NIVEL GLOBAL",
    "CARRERA CLASIFICACIÓN NIVEL 1",
    "CARRERA CLASIFICACIÓN NIVEL 2",
    "MODALIDAD",
    "JORNADA",
    "TIPO DE PLAN DE LA CARRERA",
    "DURACIÓN ESTUDIO CARRERA",
    "DURACIÓN TOTAL DE CARRERA",
    "CÓDIGO CARRERA",
    "ACREDITACIÓN CARRERA",
    "TOTAL RANGO DE EDAD",
    "RANGO DE EDAD 15 A 19 AÑOS",
    "RANGO DE EDAD 20 A 24 AÑOS",
    "RANGO DE EDAD 25 A 29 AÑOS",
    "RANGO DE EDAD 30 A 34 AÑOS",
    "RANGO DE EDAD 35 A 39 AÑOS",
    "RANGO DE EDAD 40 Y MÁS AÑOS",
    "RANGO DE EDAD SIN INFORMACIÓN",
    " PROMEDIO EDAD CARRERA      ",
    " PROMEDIO EDAD MUJER      ",
    " PROMEDIO EDAD HOMBRE      ",
    " PROMEDIO EDAD NO BINARIO ",
    "TES MUNICIPAL + SERVICIO LOCAL EDUCACION",
    "TES PARTICULAR SUBVENCIONADO",
    "TES PARTICULAR PAGADO",
    "TES CORP. DE ADMINISTRACIÓN DELEGADA",
    "TOTAL TES",
    "% COBERTURA TES",
    "TIPO ESTABLECIMIENTO HC",
    "TIPO ESTABLECIMIENTO TP",
    "CLAS_EST ADULTO",
    "CLAS_EST JOVEN",
]

IDX_NOMBRE = INDICE_NOMBRE
IDX_CODIGO = INDICE_CODIGO


def _fila(
    anio: str, nombre: str, codigo: str, subarea: str = "", area: str = ""
) -> list[str]:
    fila = [""] * len(CABECERA)
    fila[0] = anio
    fila[IDX_NOMBRE] = nombre
    fila[IDX_CODIGO] = codigo
    fila[22] = subarea
    fila[23] = area
    return fila


def escribir_csv(path: Path, filas: list[str]) -> Path:
    """Escribe un CSV cp1252 de 58 columnas con la cabecera real."""
    with open(path, "w", encoding="cp1252", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(CABECERA)
        for fila in filas:
            writer.writerow(fila)
    return path


def inyectar_byte_invalido(path: Path) -> Path:
    """Reemplaza el byte de 'í' en 'Ingeniería' por el byte cp1252 inválido 0x90."""
    contenido = path.read_bytes()
    path.write_bytes(contenido.replace(b"Ingenier\xeda", b"Ingenier\x90a"))
    return path


@pytest.fixture
def matricula_csv(tmp_path: Path) -> Path:
    """CSV de prueba con 4 filas de matrícula en cp1252."""
    filas = [
        _fila("MAT_2007", "Composición Musical", "A001", "Artes", "Música, Canto o Danza"),
        _fila("MAT_2007", "Pedagogía en Música", "A002", "Artes", "Pedagogía en Artes y Música"),
        _fila("MAT_2026", "Composición Musical", "A003", "Artes", "Música, Canto o Danza"),
        _fila("MAT_2026", "Ingeniería Comercial", "A004"),
    ]
    return escribir_csv(tmp_path / "matricula.csv", filas)