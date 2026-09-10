"""Tests de la verificación de falsos negativos y positivos con el LLM.

Cubren las funciones puras del seam de verificación: selección de la red de
candidatos a falsos negativos, la muestra de control de excluidos, la selección
de los incluidos fronterizos, y la fusión de los veredictos del LLM en la
clasificación con método `llm`.
"""

from sies_musica.clasificador import (
    CATEGORIA_INTERPRETACION,
    METODO_LLM,
    VEREDICTO_DUDOSO,
    VEREDICTO_ERROR,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ResultadoClasificacion,
)
from sies_musica.verificacion import (
    aplicar_veredictos_llm,
    seleccionar_incluidos_fronterizos,
    seleccionar_muestra_control,
    seleccionar_red_candidatos,
)


def _resultado(
    veredicto: str,
    categoria: str = "",
    metodo: str = "lexico",
    razon: str = "razon",
) -> ResultadoClasificacion:
    return {"veredicto": veredicto, "categoria": categoria, "metodo": metodo, "razon": razon}


AREA_MUSICAL = "musica, canto o danza"
AREA_ARTES = "artes y licenciatura en artes"


def _clasificacion_base() -> dict[str, ResultadoClasificacion]:
    return {
        "licenciatura en musica": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "danza": _resultado(VEREDICTO_EXCLUIR),
        "pedagogia en artes visuales": _resultado(VEREDICTO_EXCLUIR),
        "canto popular": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "ingenieria civil": _resultado(VEREDICTO_EXCLUIR),
        "educacion artistica": _resultado(VEREDICTO_DUDOSO),
        "interpretacion en danza": _resultado(VEREDICTO_EXCLUIR),
    }


# ---------------------------------------------------------------- red candidatos


def test_red_incluye_nombre_en_area_musical_sin_keyword() -> None:
    clas = _clasificacion_base()
    areas = {
        "danza": {AREA_MUSICAL},
        "pedagogia en artes visuales": {AREA_ARTES},
        "licenciatura en musica": {AREA_MUSICAL},
        "ingenieria civil": {AREA_ARTES},
    }
    red = seleccionar_red_candidatos(clas, areas)
    assert "danza" in red
    assert "licenciatura en musica" not in red


def test_red_excluye_nombre_con_keyword_musical() -> None:
    clas = _clasificacion_base()
    areas = {"canto popular": {AREA_MUSICAL}, "interpretacion en danza": {AREA_MUSICAL}}
    red = seleccionar_red_candidatos(clas, areas)
    assert "canto popular" not in red
    assert "interpretacion en danza" in red


def test_red_excluye_fuera_de_area_musical() -> None:
    clas = _clasificacion_base()
    areas = {"ingenieria civil": {AREA_ARTES}}
    assert seleccionar_red_candidatos(clas, areas) == []


def test_red_devuelve_ordenado() -> None:
    clas = _clasificacion_base()
    areas = {
        "danza": {AREA_MUSICAL},
        "interpretacion en danza": {AREA_MUSICAL},
    }
    red = seleccionar_red_candidatos(clas, areas)
    assert red == sorted(red)


def test_red_excluye_nombres_ya_en_zona_gris() -> None:
    clas = _clasificacion_base()
    areas = {
        "educacion artistica": {AREA_MUSICAL},
        "danza": {AREA_MUSICAL},
    }
    red = seleccionar_red_candidatos(clas, areas)
    assert "educacion artistica" not in red
    assert "danza" in red


# ---------------------------------------------------------------- muestra control


def test_muestra_control_toma_excluidos_al_azar() -> None:
    clas = {
        "a": _resultado(VEREDICTO_EXCLUIR),
        "b": _resultado(VEREDICTO_EXCLUIR),
        "c": _resultado(VEREDICTO_EXCLUIR),
        "d": _resultado(VEREDICTO_EXCLUIR),
        "e": _resultado(VEREDICTO_INCLUIR),
        "f": _resultado(VEREDICTO_DUDOSO),
    }
    muestra = seleccionar_muestra_control(clas, tamano=3, semilla=2026)
    assert len(muestra) == 3
    assert all(clas[n]["veredicto"] == VEREDICTO_EXCLUIR for n in muestra)


def test_muestra_control_reproducible() -> None:
    clas = {f"p{i}": _resultado(VEREDICTO_EXCLUIR) for i in range(30)}
    assert seleccionar_muestra_control(clas, tamano=5, semilla=2026) == (
        seleccionar_muestra_control(clas, tamano=5, semilla=2026)
    )


def test_muestra_control_evita_red() -> None:
    clas = {
        "a": _resultado(VEREDICTO_EXCLUIR),
        "b": _resultado(VEREDICTO_EXCLUIR),
        "c": _resultado(VEREDICTO_EXCLUIR),
    }
    muestra = seleccionar_muestra_control(clas, tamano=3, semilla=2026, evitar={"a", "c"})
    assert muestra == ["b"]


def test_muestra_control_sin_excluidos_devuelve_vacio() -> None:
    clas = {"a": _resultado(VEREDICTO_INCLUIR)}
    assert seleccionar_muestra_control(clas, tamano=5) == []


# ---------------------------------------------------------- incluidos fronterizos


def test_fronterizos_son_incluidos_sin_core_musical() -> None:
    clas = _clasificacion_base()
    front = seleccionar_incluidos_fronterizos(clas)
    assert "canto popular" in front
    assert "licenciatura en musica" not in front


def test_fronterizos_excluye_no_incluidos() -> None:
    clas = _clasificacion_base()
    front = seleccionar_incluidos_fronterizos(clas)
    assert "danza" not in front
    assert "educacion artistica" not in front


def test_fronterizos_devuelve_ordenado() -> None:
    clas = _clasificacion_base()
    front = seleccionar_incluidos_fronterizos(clas)
    assert front == sorted(front)


# --------------------------------------------------------------- aplicar veredictos


def test_aplicar_incorpora_incluir_con_metodo_llm() -> None:
    clas = {"danza": _resultado(VEREDICTO_EXCLUIR)}
    veredictos = [
        {
            "nombre": "danza",
            "veredicto": VEREDICTO_INCLUIR,
            "categoria": CATEGORIA_INTERPRETACION,
            "metodo": METODO_LLM,
            "razon": "el LLM la considera musical",
        }
    ]
    fusionada = aplicar_veredictos_llm(clas, veredictos)
    assert fusionada["danza"]["veredicto"] == VEREDICTO_INCLUIR
    assert fusionada["danza"]["metodo"] == METODO_LLM
    assert fusionada["danza"]["categoria"] == CATEGORIA_INTERPRETACION


def test_aplicar_retira_excluir_de_la_inclusion() -> None:
    clas = {"canto popular": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION)}
    veredictos = [
        {
            "nombre": "canto popular",
            "veredicto": VEREDICTO_EXCLUIR,
            "categoria": "",
            "metodo": METODO_LLM,
            "razon": "no es programa musical",
        }
    ]
    fusionada = aplicar_veredictos_llm(clas, veredictos)
    assert fusionada["canto popular"]["veredicto"] == VEREDICTO_EXCLUIR
    assert fusionada["canto popular"]["metodo"] == METODO_LLM
    assert fusionada["canto popular"]["categoria"] == ""


def test_aplicar_marca_dudoso_para_zonas_grises() -> None:
    clas = {"canto popular": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION)}
    veredictos = [
        {
            "nombre": "canto popular",
            "veredicto": VEREDICTO_DUDOSO,
            "categoria": "",
            "metodo": METODO_LLM,
            "razon": "ambigüedad",
        }
    ]
    fusionada = aplicar_veredictos_llm(clas, veredictos)
    assert fusionada["canto popular"]["veredicto"] == VEREDICTO_DUDOSO
    assert fusionada["canto popular"]["metodo"] == METODO_LLM


def test_aplicar_no_toca_nombres_consultados() -> None:
    clas = {
        "licenciatura en musica": _resultado(VEREDICTO_INCLUIR, CATEGORIA_INTERPRETACION),
        "danza": _resultado(VEREDICTO_EXCLUIR),
    }
    veredictos = [
        {
            "nombre": "danza",
            "veredicto": VEREDICTO_INCLUIR,
            "categoria": CATEGORIA_INTERPRETACION,
            "metodo": METODO_LLM,
            "razon": "sí",
        }
    ]
    fusionada = aplicar_veredictos_llm(clas, veredictos)
    assert fusionada["licenciatura en musica"] == clas["licenciatura en musica"]


def test_aplicar_ignora_error_y_conserva_previa() -> None:
    clas = {"danza": _resultado(VEREDICTO_EXCLUIR)}
    veredictos = [
        {
            "nombre": "danza",
            "veredicto": VEREDICTO_ERROR,
            "categoria": "",
            "metodo": METODO_LLM,
            "razon": "sin respuesta del modelo",
        }
    ]
    fusionada = aplicar_veredictos_llm(clas, veredictos)
    assert fusionada["danza"] == clas["danza"]


def test_aplicar_no_muta_la_clasificacion_original() -> None:
    clas = {"danza": _resultado(VEREDICTO_EXCLUIR)}
    veredictos = [
        {
            "nombre": "danza",
            "veredicto": VEREDICTO_INCLUIR,
            "categoria": CATEGORIA_INTERPRETACION,
            "metodo": METODO_LLM,
            "razon": "sí",
        }
    ]
    aplicar_veredictos_llm(clas, veredictos)
    assert clas["danza"]["veredicto"] == VEREDICTO_EXCLUIR
