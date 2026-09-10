"""Tests del ensamblado final que incorpora la revisión humana.

Cubren el seam puro de la etapa 08: la lectura de las decisiones humanas
desde ``zonas_grises_revisadas.csv``, la fusión de esas decisiones con la
clasificación automática (léxica + semántica + LLM) para obtener la
clasificación total, la selección de los nombres incluidos, y los invariantes
del archivo filtrado (mismas 58 columnas, encoding cp1252, inclusión completa
y sin filas espurias).
"""

import csv
from pathlib import Path

import pandas as pd
import pytest

from sies_musica.clasificador import (
    CATEGORIA_INTERPRETACION,
    CATEGORIA_PRODUCCION,
    VEREDICTO_DUDOSO,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ResultadoClasificacion,
)
from sies_musica.ensamblado import (
    DECISION_EXCLUIR,
    DECISION_INCLUIR,
    METODO_HUMANO,
    escribir_filtrado,
    filtrar_matricula,
    fusionar_revision,
    leer_decisiones,
    seleccionar_incluidos,
)
from sies_musica.lectura import ENCODING, INDICE_NOMBRE
from sies_musica.texto import normalizar_nombre
from tests.conftest import _fila, escribir_csv, inyectar_byte_invalido


def _resultado(
    veredicto: str,
    categoria: str = "",
    metodo: str = "lexico",
    razon: str = "razon",
) -> ResultadoClasificacion:
    return {"veredicto": veredicto, "categoria": categoria, "metodo": metodo, "razon": razon}


# ------------------------------------------------------------- leer decisiones


def test_leer_decisiones_registra_decision_y_categoria(tmp_path: Path) -> None:
    ruta = tmp_path / "revisadas.csv"
    ruta.write_text(
        "nombre_normalizado,nombre_original,veredicto,categoria,metodo,razon,origen,"
        "decision_final,categoria_final\n"
        f"sonido,SONIDO,DUDOSO,,llm,razon,origen,{DECISION_INCLUIR},"
        f"{CATEGORIA_PRODUCCION}\n",
        encoding="utf-8",
    )
    decisiones = leer_decisiones(ruta)
    assert decisiones["sonido"]["decision_final"] == DECISION_INCLUIR
    assert decisiones["sonido"]["categoria_final"] == CATEGORIA_PRODUCCION


def test_leer_decisiones_ignora_filas_sin_decision(tmp_path: Path) -> None:
    ruta = tmp_path / "revisadas.csv"
    ruta.write_text(
        "nombre_normalizado,nombre_original,veredicto,categoria,metodo,razon,origen,"
        "decision_final,categoria_final\n"
        "sonido,SONIDO,DUDOSO,,llm,razon,origen,,\n"
        f"danza,DANZA,DUDOSO,,llm,razon,origen,{DECISION_EXCLUIR},\n",
        encoding="utf-8",
    )
    decisiones = leer_decisiones(ruta)
    assert "sonido" not in decisiones
    assert decisiones["danza"]["decision_final"] == DECISION_EXCLUIR


def test_leer_decisiones_archivo_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "revisadas.csv"
    ruta.write_text(
        "nombre_normalizado,nombre_original,veredicto,categoria,metodo,razon,origen,"
        "decision_final,categoria_final\n",
        encoding="utf-8",
    )
    assert leer_decisiones(ruta) == {}


# ------------------------------------------------------- fusionar clasificacion


def _clasificacion_con_dudosos() -> dict[str, ResultadoClasificacion]:
    return {
        "licenciatura en musica": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "danza": _resultado(VEREDICTO_EXCLUIR),
        "sonido": _resultado(VEREDICTO_DUDOSO, metodo="llm", razon="Nombre genérico"),
        "educacion artistica": _resultado(VEREDICTO_DUDOSO),
    }


def test_fusionar_incluir_humano_sobrescribe_dudoso() -> None:
    clas = _clasificacion_con_dudosos()
    decisiones = {
        "sonido": {"decision_final": DECISION_INCLUIR, "categoria_final": CATEGORIA_PRODUCCION}
    }
    total = fusionar_revision(clas, decisiones)
    assert total["sonido"]["veredicto"] == VEREDICTO_INCLUIR
    assert total["sonido"]["categoria"] == CATEGORIA_PRODUCCION
    assert total["sonido"]["metodo"] == METODO_HUMANO


def test_fusionar_excluir_humano_sobrescribe_dudoso() -> None:
    clas = _clasificacion_con_dudosos()
    decisiones = {"sonido": {"decision_final": DECISION_EXCLUIR, "categoria_final": ""}}
    total = fusionar_revision(clas, decisiones)
    assert total["sonido"]["veredicto"] == VEREDICTO_EXCLUIR
    assert total["sonido"]["categoria"] == ""
    assert total["sonido"]["metodo"] == METODO_HUMANO


def test_fusionar_conserva_veredictos_automaticos() -> None:
    clas = _clasificacion_con_dudosos()
    decisiones = {
        "sonido": {"decision_final": DECISION_INCLUIR, "categoria_final": CATEGORIA_PRODUCCION}
    }
    total = fusionar_revision(clas, decisiones)
    assert total["licenciatura en musica"] == clas["licenciatura en musica"]
    assert total["danza"] == clas["danza"]
    assert total["educacion artistica"] == clas["educacion artistica"]


def test_fusionar_no_muta_la_clasificacion_original() -> None:
    clas = _clasificacion_con_dudosos()
    decisiones = {
        "sonido": {"decision_final": DECISION_INCLUIR, "categoria_final": CATEGORIA_PRODUCCION}
    }
    fusionar_revision(clas, decisiones)
    assert clas["sonido"]["veredicto"] == VEREDICTO_DUDOSO


def test_fusionar_sin_decisiones_devuelve_copia() -> None:
    clas = _clasificacion_con_dudosos()
    total = fusionar_revision(clas, {})
    assert total == clas
    assert total is not clas


# ---------------------------------------------------------- seleccionar incluidos


def test_seleccionar_incluidos_solo_incluir() -> None:
    clas = _clasificacion_con_dudosos()
    decisions = {"sonido": {"decision_final": DECISION_INCLUIR, "categoria_final": CATEGORIA_PRODUCCION}}
    total = fusionar_revision(clas, decisions)
    incluidos = seleccionar_incluidos(total)
    assert "sonido" in incluidos
    assert "licenciatura en musica" in incluidos
    assert "danza" not in incluidos
    assert "educacion artistica" not in incluidos


def test_seleccionar_incluidos_ordenado() -> None:
    clas = _clasificacion_con_dudosos()
    incluidos = seleccionar_incluidos(clas)
    assert incluidos == sorted(incluidos)


def test_seleccionar_incluidos_sin_dudoso_decidido() -> None:
    clas = _clasificacion_con_dudosos()
    decisiones = {"sonido": {"decision_final": DECISION_EXCLUIR, "categoria_final": ""}}
    total = fusionar_revision(clas, decisiones)
    assert seleccionar_incluidos(total) == ["licenciatura en musica"]


# ------------------------------------------------------- filtrar y escribir csv


def _clasificacion_total(incluir_sonido: bool = True) -> dict[str, ResultadoClasificacion]:
    clas = _clasificacion_con_dudosos()
    decisiones = {
        "sonido": {
            "decision_final": DECISION_INCLUIR if incluir_sonido else DECISION_EXCLUIR,
            "categoria_final": CATEGORIA_PRODUCCION if incluir_sonido else "",
        }
    }
    return fusionar_revision(clas, decisiones)


def _matricula_con_sonido(tmp_path: Path) -> pd.DataFrame:
    filas = [
        _fila("MAT_2007", "Licenciatura en Música", "A001"),
        _fila("MAT_2007", "Sonido", "A002"),
        _fila("MAT_2007", "Danza", "A003"),
        _fila("MAT_2026", "Sonido", "A004"),
    ]
    ruta = escribir_csv(tmp_path / "matricula.csv", filas)
    return pd.read_csv(
        ruta, sep=";", dtype=str, keep_default_na=False, encoding=ENCODING
    )


def test_filtrar_matricula_mantiene_las_filas_de_incluidos(tmp_path: Path) -> None:
    df = _matricula_con_sonido(tmp_path)
    clas = _clasificacion_total()
    filtrado = filtrar_matricula(df, seleccionar_incluidos(clas))
    assert len(filtrado) == 3  # Licenciatura en Música + 2 filas de Sonido
    nombres = set(filtrado.iloc[:, INDICE_NOMBRE])
    assert nombres == {"Licenciatura en Música", "Sonido"}
    assert filtrado.shape[1] == 58


def test_filtrar_matricula_excluye_si_decision_humana_excluye(tmp_path: Path) -> None:
    df = _matricula_con_sonido(tmp_path)
    clas = _clasificacion_total(incluir_sonido=False)
    filtrado = filtrar_matricula(df, seleccionar_incluidos(clas))
    assert len(filtrado) == 1
    assert filtrado.iloc[0, INDICE_NOMBRE] == "Licenciatura en Música"


def test_escribir_filtrado_preserva_58_columnas(tmp_path: Path) -> None:
    df = _matricula_con_sonido(tmp_path)
    clas = _clasificacion_total()
    filtrado = filtrar_matricula(df, seleccionar_incluidos(clas))
    ruta = tmp_path / "filtrado.csv"
    escribir_filtrado(ruta, filtrado)
    releido = pd.read_csv(
        ruta, sep=";", dtype=str, keep_default_na=False, encoding=ENCODING
    )
    assert releido.shape[1] == 58
    assert list(releido.columns) == list(df.columns)


def test_escribir_filtrado_encoding_cp1252(tmp_path: Path) -> None:
    df = _matricula_con_sonido(tmp_path)
    clas = _clasificacion_total()
    filtrado = filtrar_matricula(df, seleccionar_incluidos(clas))
    ruta = tmp_path / "filtrado.csv"
    escribir_filtrado(ruta, filtrado)
    bytes_ = ruta.read_bytes()
    assert not bytes_.startswith(b"\xef\xbb\xbf")
    texto = bytes_.decode(ENCODING)
    assert "Licenciatura en Música" in texto
    assert texto.split(";", 1)[0] == "AÑO"


def test_escribir_filtrado_no_agrega_indices(tmp_path: Path) -> None:
    df = _matricula_con_sonido(tmp_path)
    clas = _clasificacion_total()
    filtrado = filtrar_matricula(df, seleccionar_incluidos(clas))
    ruta = tmp_path / "filtrado.csv"
    escribir_filtrado(ruta, filtrado)
    with open(ruta, encoding=ENCODING, newline="") as f:
        primera = next(csv.reader(f, delimiter=";"))
    assert primera == list(df.columns)


def test_escribir_filtrado_maneja_byte_invalido(tmp_path: Path) -> None:
    """El archivo de salida se escribe en cp1252 incluso con bytes no decodificables."""
    ruta = inyectar_byte_invalido(
        escribir_csv(
            tmp_path / "invalido.csv",
            [_fila("MAT_2020", "Ingeniería Comercial", "X001")],
        )
    )
    df = pd.read_csv(
        ruta, sep=";", dtype=str, keep_default_na=False, encoding=ENCODING,
        encoding_errors="replace",
    )
    filtrado = filtrar_matricula(df, ["ingenieria comercial"])
    salida = tmp_path / "filtrado.csv"
    escribir_filtrado(salida, filtrado)
    salida.read_bytes().decode(ENCODING)


# ----------------------------------------------------- integración con datos reales

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BASE = RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
RUTA_FILTRADO = RAIZ / "prod" / "Musica_2007_2026_filtrado.csv"
RUTA_CLASIFICACION_TOTAL = RAIZ / "prod" / "clasificacion_total.csv"

INTEGRACION_DISPONIBLE = RUTA_BASE.exists() and RUTA_FILTRADO.exists()


@pytest.mark.skipif(
    not INTEGRACION_DISPONIBLE,
    reason="Requiere la base SIES y el filtrado de la etapa 08 en el repo",
)
def test_integracion_columnas_iguales_al_original() -> None:
    """Las 58 columnas del filtrado coinciden con las de la base original."""
    with open(RUTA_BASE, encoding=ENCODING, newline="") as f:
        columnas_base = next(csv.reader(f, delimiter=";"))
    with open(RUTA_FILTRADO, encoding=ENCODING, newline="") as f:
        columnas_filtrado = next(csv.reader(f, delimiter=";"))
    assert len(columnas_base) == 58
    assert columnas_filtrado == columnas_base


@pytest.mark.skipif(
    not INTEGRACION_DISPONIBLE,
    reason="Requiere la base SIES y el filtrado de la etapa 08 en el repo",
)
def test_integracion_encoding_cp1252_sin_bom() -> None:
    """El filtrado es cp1252, sin BOM, con salto de línea CRLF como la base."""
    bytes_ = RUTA_FILTRADO.read_bytes()
    assert not bytes_.startswith(b"\xef\xbb\xbf")
    bytes_.decode(ENCODING)
    assert b"\r\n" in bytes_


@pytest.mark.skipif(
    not INTEGRACION_DISPONIBLE,
    reason="Requiere la base SIES y el filtrado de la etapa 08 en el repo",
)
def test_integracion_toda_fila_corresponde_a_incluido() -> None:
    """Ninguna fila del filtrado pertenece a un programa no incluido."""
    incluidos = _nombres_incluidos()
    with open(RUTA_FILTRADO, encoding=ENCODING, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        nombres = {normalizar_nombre(fila[INDICE_NOMBRE]) for fila in reader}
    assert nombres <= incluidos


@pytest.mark.skipif(
    not INTEGRACION_DISPONIBLE,
    reason="Requiere la base SIES y el filtrado de la etapa 08 en el repo",
)
def test_integracion_ninguna_fila_de_incluido_falta() -> None:
    """Todas las filas de cada programa incluido están en el filtrado."""
    incluidos = _nombres_incluidos()
    contador_base = _contar_nombres(RUTA_BASE)
    contador_filtrado = _contar_nombres(RUTA_FILTRADO)
    for nombre in incluidos:
        assert contador_filtrado.get(nombre, 0) == contador_base.get(nombre, 0), nombre


def _nombres_incluidos() -> set[str]:
    """Nombres con veredicto final INCLUIR en la clasificación total."""
    incluidos: set[str] = set()
    with open(RUTA_CLASIFICACION_TOTAL, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["veredicto"] == VEREDICTO_INCLUIR:
                incluidos.add(fila["nombre_normalizado"])
    return incluidos


def _contar_nombres(ruta: Path) -> dict[str, int]:
    """Contador de filas por nombre normalizado en un CSV de matrícula."""
    conteo: dict[str, int] = {}
    with open(ruta, encoding=ENCODING, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for fila in reader:
            nombre = normalizar_nombre(fila[INDICE_NOMBRE])
            conteo[nombre] = conteo.get(nombre, 0) + 1
    return conteo