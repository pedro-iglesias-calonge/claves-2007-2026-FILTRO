"""Tests de unidad del motor de clasificación (tabla nombre → veredicto/categoría).

Cubren: incluyentes claros, excluyentes fuertes, híbridos que caen en zona gris
y desambiguación semántica por contexto (área genérica, subárea CINE).
"""

import pytest

from sies_musica.clasificador import (
    CATEGORIA_COMPOSICION,
    CATEGORIA_FORMACION,
    CATEGORIA_GESTION,
    CATEGORIA_INTERPRETACION,
    CATEGORIA_MUSICOTERAPIA,
    CATEGORIA_OTROS,
    CATEGORIA_PEDAGOGIA,
    CATEGORIA_PRODUCCION,
    CATEGORIA_TEORIA,
    VEREDICTO_DUDOSO,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ContextoClasificacion,
    clasificar,
)

CASOS_INCLUIR = [
    ("musica", CATEGORIA_FORMACION),
    ("licenciatura en musica", CATEGORIA_FORMACION),
    ("bachillerato en musica", CATEGORIA_FORMACION),
    ("pedagogia en musica", CATEGORIA_PEDAGOGIA),
    ("educacion musical", CATEGORIA_PEDAGOGIA),
    ("pedagogia en artes musicales", CATEGORIA_PEDAGOGIA),
    ("profesor de piano", CATEGORIA_PEDAGOGIA),
    ("profesor de violin", CATEGORIA_PEDAGOGIA),
    ("licenciatura en educacion y pedagogia en musica", CATEGORIA_PEDAGOGIA),
    ("didactica de la musica", CATEGORIA_PEDAGOGIA),
    ("composicion musical", CATEGORIA_COMPOSICION),
    ("composicion en jazz y musica popular", CATEGORIA_COMPOSICION),
    ("composicion y arreglos", CATEGORIA_COMPOSICION),
    ("especialista en arreglos instrumentales y composicion de musica popular", CATEGORIA_COMPOSICION),
    ("interpretacion musical", CATEGORIA_INTERPRETACION),
    ("interprete en teatro musical", CATEGORIA_INTERPRETACION),
    ("interprete musical superior en piano", CATEGORIA_INTERPRETACION),
    ("interprete musical superior en violin", CATEGORIA_INTERPRETACION),
    ("interprete musical superior en guitarra", CATEGORIA_INTERPRETACION),
    ("interprete musical superior en arpa", CATEGORIA_INTERPRETACION),
    ("interprete instrumental mencion instrumento popular", CATEGORIA_INTERPRETACION),
    ("interprete instrumental", CATEGORIA_INTERPRETACION),
    ("tecnico/a en interprete instrumental mencion (instrumento popular)", CATEGORIA_INTERPRETACION),
    ("direccion de orquestas juveniles e infantiles", CATEGORIA_INTERPRETACION),
    ("direccion coral", CATEGORIA_INTERPRETACION),
    ("diploma de postitulo en direccion orquestal", CATEGORIA_INTERPRETACION),
    ("direccion de agrupaciones musicales instrumentales", CATEGORIA_INTERPRETACION),
    ("interpretacion en canto", CATEGORIA_INTERPRETACION),
    ("canto popular", CATEGORIA_INTERPRETACION),
    ("interprete en jazz y musica popular", CATEGORIA_INTERPRETACION),
    ("musico mencion direccion y gestion en conjunto y bandas instrumentales juveniles", CATEGORIA_INTERPRETACION),
    ("teoria de la musica", CATEGORIA_TEORIA),
    ("magister en musicologia latinoamericana", CATEGORIA_TEORIA),
    ("licenciatura en artes mencion teoria de la musica", CATEGORIA_TEORIA),
    ("postitulo en investigacion musical", CATEGORIA_TEORIA),
    ("musica y sonido", CATEGORIA_PRODUCCION),
    ("musica y tecnologia en sonido", CATEGORIA_PRODUCCION),
    ("produccion musical", CATEGORIA_PRODUCCION),
    ("ingenieria en sonido", CATEGORIA_PRODUCCION),
    ("tecnico en sonido", CATEGORIA_PRODUCCION),
    ("tecnologia en sonido e iluminacion", CATEGORIA_PRODUCCION),
    ("licenciatura en artes mencion sonido", CATEGORIA_PRODUCCION),
    ("musicoterapia", CATEGORIA_MUSICOTERAPIA),
    ("terapias de arte mencion musicoterapia", CATEGORIA_MUSICOTERAPIA),
    ("postitulo en terapias de arte mencion musicoterapia", CATEGORIA_MUSICOTERAPIA),
    ("gestion cultural", CATEGORIA_GESTION),
    ("diplomado en gestion cultural", CATEGORIA_GESTION),
    ("tecnico en arte y gestion cultural", CATEGORIA_GESTION),
    ("diplomado emprendimiento e industrias de la musica", CATEGORIA_GESTION),
    ("taller de lutheria artistica", CATEGORIA_OTROS),
    ("musica electronica", CATEGORIA_OTROS),
    ("musica y tecnologia", CATEGORIA_OTROS),
    ("magister en artes musicales mencion cultura tradicional", CATEGORIA_OTROS),
    ("licenciatura en artes con mencion en composicion", CATEGORIA_COMPOSICION),
    ("etapa basica de la licenciatura en artes con mencion en composicion", CATEGORIA_COMPOSICION),
    ("licenciatura en artes musicales", CATEGORIA_FORMACION),
    ("interpretacion superior en musica antigua", CATEGORIA_INTERPRETACION),
    ("diplomado en interpretacion musical mencion guitarra", CATEGORIA_INTERPRETACION),
    ("magister en composicion para artes escenicas y medios audiovisuales", CATEGORIA_COMPOSICION),
    ("interpretacion y docencia musical", CATEGORIA_PEDAGOGIA),
    ("interprete en canto popular", CATEGORIA_INTERPRETACION),
    ("musica espanola", CATEGORIA_OTROS),
    ("canto en ingles", CATEGORIA_INTERPRETACION),
    ("interpretacion musical mencion ingles", CATEGORIA_INTERPRETACION),
    ("musica italiana", CATEGORIA_OTROS),
    ("musica de camara y orquesta", CATEGORIA_INTERPRETACION),
    ("musica y ultrasonido", CATEGORIA_PRODUCCION),
    ("musica, sonido y acustica", CATEGORIA_PRODUCCION),
    ("musical mencion sonido y acustica", CATEGORIA_PRODUCCION),
]

CASOS_EXCLUIR = [
    "interpretacion de enlace ingles-castellano",
    "interpretacion o traduccion ingles-espanol",
    "interpretacion profesional del ingles al espanol",
    "interpretacion simultanea y consecutiva ingles espanol",
    "interpretariado ingles-espanol",
    "traduccion e interpretariado bilingue",
    "tecnico en interpretacion de lengua de senas",
    "postitulo de interpretacion en lengua de senas chilena",
    "diplomado en lengua de senas chilena",
    "diplomado en interpretacion del patrimonio",
    "diplomado en interpretacion patrimonial",
    "diplomado de interpretacion simultanea",
    "interpretacion en danza",
    "interpretacion mencion danza",
    "danza",
    "danza y coreografia",
    "pedagogia en danza",
    "licenciatura en danza",
    "pet de danza",
    "coreografia y pedagogia en danza-teatro",
    "teatro",
    "teatro profesional",
    "licenciatura en teatro",
    "pedagogia en lengua castellana y comunicacion mencion teatro",
    "teatro mencion pedagogia e interprete",
    "cine",
    "licenciatura en cine",
    "comunicacion audiovisual",
    "realizador de cine y television",
    "animacion digital",
    "ingenieria acustica",
    "ingenieria civil acustica",
    "magister en acustica y vibraciones",
    "diplomado en acustica ambiental",
    "diplomado en acustica de la edificacion",
    "diplomado en acustica submarina",
    "diplomado en ultrasonido de partes blandas",
    "postitulo en ultrasonido",
    "pedagogia en artes visuales",
    "licenciatura en artes visuales",
    "licenciatura en artes plasticas",
    "licenciatura en artes",
    "programa especial de licenciatura en artes",
    "pedagogia y licenciatura en artes",
    "licenciatura en artes mencion danza",
    "licenciatura en artes mencion pintura",
    "licenciatura en artes escenicas",
    "licenciatura en artes culinarias",
    "licenciatura en artes digitales",
    "licenciatura en artes liberales",
    "arte terapia",
    "arteterapia",
    "diplomado dramaterapia",
    "psicoterapia",
    "terapia ocupacional",
    "kinesiterapia",
    "fisioterapia",
    "diplomado en danza movimiento en terapia",
    "diploma en habilitacion de vuelo por instrumentos y piloto comercial",
    "diplomado en instrumentos de evaluacion",
    "diplomado en aseguramiento de la calidad en el reprocesamiento y esterilizacion de instrumental quirurgico",
    "diplomado en higiene industrial, evaluacion instrumental de riesgos laborales",
    "diplomado en mediacion para el desarrollo del pensamiento: programa de enriquecimiento instrumental",
    "diplomado en tratamiento manual e instrumental de tejidos blandos",
    "instrumental quirurgico",
    "tecnico de nivel superior electrico instrumentista mantenedor plantas mineras",
    "tecnico de nivel superior electrico-instrumentista mantenedor plantas mineras",
    "tecnico en enfermeria mencion instrumentista quirurgico",
    "diploma de postitulo en analisis instrumental organico",
    "postitulo de especialidad de tecnologia medica en ultra sonido",
    "instructor en gimnasia jazz",
    "diplomado transformacion digital orquestando cultura negocio datos y tecnologia",
    "administracion de empresas",
    "ingenieria comercial",
    "diplomado en direccion de proyectos",
    "licenciatura en educacion y pedagogia en artes visuales",
    "pedagogia en arte",
    "pedagogia en artes manuales",
    "licenciatura en artes mencion artes visuales",
    "actuacion",
    "actuacion teatral",
    "ballet",
]

CASOS_DUDOSO = [
    "ingenieria civil en sonido y acustica",
    "ingenieria en sonido y acustica",
    "tecnico de nivel superior sonido y acustica",
    "tecnico universitario en sonido y acustica",
    "educacion artistica",
    "pedagogia en educacion artistica",
    "magister en educacion artistica",
    "postitulo en educacion artistica",
]

CONTEXTO_ARTES = {
    "areas_genericas": ["Artes y Licenciatura en Artes"],
    "subareas_cine": ["Artes"],
}
CONTEXTO_MUSICAL = {
    "areas_genericas": ["Música, Canto o Danza"],
    "subareas_cine": ["Artes"],
}
CONTEXTO_PEDAGOGIA_ARTES = {
    "areas_genericas": ["Pedagogía en Artes y Música"],
    "subareas_cine": ["Artes"],
}


@pytest.mark.parametrize("nombre,categoria", CASOS_INCLUIR)
def test_incluye(nombre: str, categoria: str) -> None:
    resultado = clasificar(nombre)
    assert resultado["veredicto"] == VEREDICTO_INCLUIR, resultado
    assert resultado["categoria"] == categoria, resultado


@pytest.mark.parametrize("nombre", CASOS_EXCLUIR)
def test_excluye(nombre: str) -> None:
    resultado = clasificar(nombre)
    assert resultado["veredicto"] == VEREDICTO_EXCLUIR, resultado
    assert resultado["categoria"] == "", resultado


@pytest.mark.parametrize("nombre", CASOS_DUDOSO)
def test_zona_gris(nombre: str) -> None:
    resultado = clasificar(nombre)
    assert resultado["veredicto"] == VEREDICTO_DUDOSO, resultado


def test_semantico_rescata_con_area_musical() -> None:
    resultado = clasificar("expresion y creacion artistica", CONTEXTO_MUSICAL)
    assert resultado["veredicto"] == VEREDICTO_INCLUIR, resultado
    assert resultado["categoria"] == CATEGORIA_OTROS, resultado
    assert resultado["metodo"] == "semantico", resultado


def test_semantico_excluye_sin_area_musical() -> None:
    resultado = clasificar("expresion y creacion artistica", CONTEXTO_ARTES)
    assert resultado["veredicto"] == VEREDICTO_EXCLUIR, resultado
    assert resultado["metodo"] == "semantico", resultado


def test_danza_en_area_musical_se_excluye() -> None:
    resultado = clasificar("danza", CONTEXTO_MUSICAL)
    assert resultado["veredicto"] == VEREDICTO_EXCLUIR, resultado


def test_educacion_artistica_pura_según_area() -> None:
    resultado = clasificar("educacion artistica", CONTEXTO_PEDAGOGIA_ARTES)
    assert resultado["veredicto"] == VEREDICTO_DUDOSO, resultado


def test_resultado_tiene_cuatro_claves() -> None:
    resultado = clasificar("musica")
    assert set(resultado.keys()) == {"veredicto", "categoria", "metodo", "razon"}
    assert isinstance(resultado["razon"], str)
    assert resultado["razon"]


def test_metodo_lexico_para_inclusiones() -> None:
    assert clasificar("composicion musical")["metodo"] == "lexico"
    assert clasificar("danza")["metodo"] == "lexico"


def test_acepta_nombre_con_tildes() -> None:
    resultado = clasificar("Composición Musical")
    assert resultado["veredicto"] == VEREDICTO_INCLUIR
    assert resultado["categoria"] == CATEGORIA_COMPOSICION


def test_acepta_contexto_con_tildes() -> None:
    contexto: ContextoClasificacion = {
        "areas_genericas": ["Pedagogía en Artes y Música"],
        "subareas_cine": ["Artes"],
    }
    resultado = clasificar("expresion y creacion artistica", contexto)
    assert resultado["veredicto"] == VEREDICTO_INCLUIR
