"""Tests de la generación de zonas grises para la revisión humana.

Cubren el seam puro de la etapa 06: la selección de los puntos frontera
(los `DUDOSO` de la clasificación), la etiqueta de origen de cada punto
(LLM, híbrido sonido/acústica, educación artística pura o ambiguo), y la
persistencia de `zonas_grises.csv` y del template `zonas_grises_revisadas.csv`
con las columnas de decisión humana vacías.
"""

import csv

from sies_musica.clasificador import (
    CATEGORIA_INTERPRETACION,
    METODO_LLM,
    VEREDICTO_DUDOSO,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ResultadoClasificacion,
)
from sies_musica.zonas_grises import (
    COLUMNAS_REVISADAS,
    COLUMNAS_ZONAS_GRISES,
    DECISION_EXCLUIR,
    DECISION_INCLUIR,
    ORIGEN_AMBIGUO,
    ORIGEN_EDUCACION_ARTISTICA,
    ORIGEN_HIBRIDO,
    ORIGEN_LLM,
    escribir_revision,
    escribir_zonas_grises,
    filas_zonas_grises,
    leer_originales,
    origen_de,
    por_origen,
    seleccionar_zonas_grises,
)


def _resultado(
    veredicto: str,
    categoria: str = "",
    metodo: str = "lexico",
    razon: str = "razon",
) -> ResultadoClasificacion:
    return {"veredicto": veredicto, "categoria": categoria, "metodo": metodo, "razon": razon}


def _clasificacion_con_dudosos() -> dict[str, ResultadoClasificacion]:
    return {
        "licenciatura en musica": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "danza": _resultado(VEREDICTO_EXCLUIR),
        "sonido": _resultado(VEREDICTO_DUDOSO, metodo=METODO_LLM, razon="Nombre genérico"),
        "educacion artistica": _resultado(
            VEREDICTO_DUDOSO, razon="Educación artística pura (sin mención de música)"
        ),
        "ingenieria en sonido y acustica": _resultado(
            VEREDICTO_DUDOSO, razon="Híbrido 'sonido y acústica'"
        ),
    }


# ------------------------------------------------------------ seleccionar zonas grises


def test_seleccion_solo_incluye_dudosos() -> None:
    clas = _clasificacion_con_dudosos()
    zonas = seleccionar_zonas_grises(clas)
    assert set(zonas) == {
        "sonido",
        "educacion artistica",
        "ingenieria en sonido y acustica",
    }


def test_seleccion_devuelve_ordenado() -> None:
    clas = _clasificacion_con_dudosos()
    zonas = seleccionar_zonas_grises(clas)
    assert zonas == sorted(zonas)


def test_seleccion_sin_dudosos_devuelve_vacio() -> None:
    clas = {
        "licenciatura en musica": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "danza": _resultado(VEREDICTO_EXCLUIR),
    }
    assert seleccionar_zonas_grises(clas) == []


# ------------------------------------------------------------- etiqueta de origen


def test_origen_dudoso_del_llm() -> None:
    resultado = _resultado(VEREDICTO_DUDOSO, metodo=METODO_LLM, razon="duda del modelo")
    assert origen_de(resultado) == ORIGEN_LLM


def test_origen_hibrido_sonido_acustica() -> None:
    resultado = _resultado(VEREDICTO_DUDOSO, razon="Híbrido 'sonido y acústica'")
    assert origen_de(resultado) == ORIGEN_HIBRIDO


def test_origen_educacion_artistica() -> None:
    resultado = _resultado(VEREDICTO_DUDOSO, razon="Educación artística pura")
    assert origen_de(resultado) == ORIGEN_EDUCACION_ARTISTICA


def test_origen_ambiguo_no_clasificable() -> None:
    resultado = _resultado(VEREDICTO_DUDOSO, razon="ambiguo")
    assert origen_de(resultado) == ORIGEN_AMBIGUO


def test_origen_llm_precede_a_reglas_lexicas() -> None:
    resultado = _resultado(
        VEREDICTO_DUDOSO, metodo=METODO_LLM, razon="Híbrido 'sonido y acústica'"
    )
    assert origen_de(resultado) == ORIGEN_LLM


# --------------------------------------------------------- filas de zonas grises


def test_filas_incluyen_origen_y_nombre_original() -> None:
    clas = _clasificacion_con_dudosos()
    originales = {"sonido": "SONIDO", "educacion artistica": "EDUCACION ARTISTICA"}
    filas = filas_zonas_grises(clas, originales)
    por_nombre = {f["nombre_normalizado"]: f for f in filas}
    assert por_nombre["sonido"]["nombre_original"] == "SONIDO"
    assert por_nombre["sonido"]["origen"] == ORIGEN_LLM
    assert por_nombre["sonido"]["metodo"] == METODO_LLM
    assert por_nombre["educacion artistica"]["origen"] == ORIGEN_EDUCACION_ARTISTICA


def test_filas_sin_originales_dejan_columna_vacia() -> None:
    clas = _clasificacion_con_dudosos()
    filas = filas_zonas_grises(clas)
    assert all(f["nombre_original"] == "" for f in filas)


def test_filas_ordenadas_por_nombre() -> None:
    clas = _clasificacion_con_dudosos()
    nombres = [f["nombre_normalizado"] for f in filas_zonas_grises(clas)]
    assert nombres == sorted(nombres)


def test_por_origen_cuenta_etiquetas() -> None:
    filas = filas_zonas_grises(_clasificacion_con_dudosos())
    conteo = por_origen(filas)
    assert conteo[ORIGEN_LLM] == 1
    assert conteo[ORIGEN_EDUCACION_ARTISTICA] == 1
    assert conteo[ORIGEN_HIBRIDO] == 1


# ---------------------------------------------------------------- persistencia


def test_escribir_zonas_grises_y_releer(tmp_path) -> None:
    ruta = tmp_path / "zonas_grises.csv"
    filas = filas_zonas_grises(_clasificacion_con_dudosos())
    escribir_zonas_grises(ruta, filas)
    with open(ruta, encoding="utf-8", newline="") as f:
        leidas = list(csv.DictReader(f))
    assert [c for c in leidas[0]] == COLUMNAS_ZONAS_GRISES
    assert {fila["nombre_normalizado"] for fila in leidas} == {
        f["nombre_normalizado"] for f in filas
    }
    assert all(fila["origen"] for fila in leidas)


def test_escribir_revision_agrega_decisiones_vacias(tmp_path) -> None:
    ruta = tmp_path / "zonas_grises_revisadas.csv"
    filas = filas_zonas_grises(_clasificacion_con_dudosos())
    creado = escribir_revision(ruta, filas)
    assert creado is True
    with open(ruta, encoding="utf-8", newline="") as f:
        leidas = list(csv.DictReader(f))
    assert [c for c in leidas[0]] == COLUMNAS_REVISADAS
    assert leidas[0]["decision_final"] == ""
    assert leidas[0]["categoria_final"] == ""
    assert all(f["decision_final"] == "" for f in leidas)


def test_escribir_revision_no_pisa_archivo_existente(tmp_path) -> None:
    ruta = tmp_path / "zonas_grises_revisadas.csv"
    filas = filas_zonas_grises(_clasificacion_con_dudosos())
    ruta.write_text(
        "nombre_normalizado,nombre_original,veredicto,categoria,metodo,razon,origen,"
        "decision_final,categoria_final\n"
        f"sonido,,DUDOSO,,llm,Nombre genérico,{ORIGEN_LLM},{DECISION_INCLUIR},"
        f"{CATEGORIA_INTERPRETACION}\n",
        encoding="utf-8",
    )
    contenido_previo = ruta.read_text(encoding="utf-8")
    creado = escribir_revision(ruta, filas)
    assert creado is False
    assert ruta.read_text(encoding="utf-8") == contenido_previo


def test_leer_originales(tmp_path) -> None:
    ruta = tmp_path / "parcial.csv"
    ruta.write_text(
        "nombre_normalizado,nombre_original\n"
        "sonido,SONIDO\n"
        "danza,DANZA\n",
        encoding="utf-8",
    )
    originales = leer_originales(ruta)
    assert originales == {"sonido": "SONIDO", "danza": "DANZA"}
