"""Motor de clasificación de programas musicales (seam puro).

Recibe un nombre normalizado de programa, con contexto auxiliar opcional
(área genérica, subárea CINE), y devuelve ``{veredicto, categoría, método,
razón}``. Implementa las reglas acordadas del filtro léxico (inclusiones y
exclusiones fuertes) y el filtro semántico por columnas auxiliares.
"""

import re
from typing import TypedDict

from sies_musica.texto import normalizar_nombre

VEREDICTO_INCLUIR = "INCLUIR"
VEREDICTO_EXCLUIR = "EXCLUIR"
VEREDICTO_DUDOSO = "DUDOSO"
VEREDICTO_ERROR = "ERROR"

METODO_LEXICO = "lexico"
METODO_SEMANTICO = "semantico"
METODO_LLM = "llm"

ORIGEN_HIBRIDO_SONIDO_ACUSTICA = "Híbrido 'sonido y acústica'"
ORIGEN_EDUCACION_ARTISTICA = "Educación artística pura"

CATEGORIA_PEDAGOGIA = "Pedagogía en música"
CATEGORIA_COMPOSICION = "Composición y arreglos"
CATEGORIA_INTERPRETACION = "Interpretación musical"
CATEGORIA_TEORIA = "Teoría, musicología e investigación"
CATEGORIA_FORMACION = "Formación musical general"
CATEGORIA_PRODUCCION = "Producción musical y sonido"
CATEGORIA_MUSICOTERAPIA = "Musicoterapia"
CATEGORIA_GESTION = "Gestión cultural"
CATEGORIA_OTROS = "Otros"

AREAS_GENERICAS_MUSICALES = frozenset(
    {"musica, canto o danza", "pedagogia en artes y musica"}
)

_INSTRUMENTOS = (
    "piano",
    "violin",
    "viola",
    "violonchelo",
    "violoncello",
    "guitarra",
    "flauta",
    "saxofon",
    "saxo",
    "trompeta",
    "trombon",
    "tuba",
    "corno",
    "fagot",
    "oboe",
    "clarinete",
    "arpa",
    "percusion",
    "contrabajo",
    "bajo electrico",
)

_DIRECCION_MUSICAL = (
    "direccion de orquestas",
    "direccion coral",
    "direccion orquestal",
    "direccion de conjuntos",
    "direccion de agrupaciones",
    "direccion musical",
)

_ORQUESTA = ("orquesta", "orquestas", "orquestal", "orquestacion")

_SEÑALES_POSITIVAS = (
    "musicoterap",
    "gestion cultural",
    "industrias de la musica",
    "musica",
    "musical",
    "musico",
    "musicolog",
    "canto",
    "cantante",
    "cantor",
    "coral",
    "coro",
    "coros",
    "composicion",
    "compositor",
    "arreglos",
    "arreglista",
    "sonido",
    "sonora",
    "produccion musical",
    "grabacion",
    "lutheria",
    "luthier",
) + _ORQUESTA + _DIRECCION_MUSICAL + _INSTRUMENTOS

_PISTAS_INTERPRETACION = (
    "interpretacion",
    "interprete",
    "canto",
    "cantante",
    "cantor",
    "instrumental",
    "instrumentista",
    "coral",
    "coro",
    "coros",
    "teatro musical",
) + _ORQUESTA + _DIRECCION_MUSICAL + _INSTRUMENTOS

_PISTAS_PEDAGOGIA = (
    "pedagog",
    "profesor",
    "didactica",
    "docencia",
)

_PISTAS_COMPOSICION = (
    "composicion",
    "compositor",
    "arreglo",
)

_PISTAS_TEORIA = (
    "teoria",
    "musicolog",
    "investigacion",
)

_PISTAS_PRODUCCION = (
    "sonido",
    "sonora",
    "produccion",
    "grabacion",
)

_MARCADORES_IDIOMAS = (
    "ingles",
    "espanol",
    "castellano",
    "frances",
    "aleman",
    "portugues",
    "italiano",
    "japones",
    "mandarin",
    "idioma",
    "idiomas",
    "bilingue",
    "bilingues",
    "simultanea",
    "consecutiva",
    "lengua de senas",
    "lengua extranjera",
    "lengua castellana",
    "lengua indigena",
    "traduccion",
    "interpretariado",
    "de contacto",
    "de enlace",
)

_ARTES_VISUALES = (
    "artes visuales",
    "artes plasticas",
    "artes escenicas",
    "artes dramaticas",
    "pintura",
    "escultura",
    "grabado",
    "dibujo",
    "fotografia",
    "diseno",
)

_ARTE_PALABRA_RE = re.compile(r"\barte\b|\bartes\b")

_MUSICO_RE = re.compile(r"\bmusico\b")


class ContextoClasificacion(TypedDict, total=False):
    areas_genericas: list[str]
    subareas_cine: list[str]


class ResultadoClasificacion(TypedDict):
    veredicto: str
    categoria: str
    metodo: str
    razon: str


def _coincide_pistas(nombre: str, pistas: tuple[str, ...]) -> bool:
    """True si el nombre contiene alguna pista léxica dada.

    La metáfora verbal "orquestando" (orquestar un proceso) no cuenta como
    señal musical, así que se descartan las palabras de orquesta para ese caso.
    """
    if "orquestando" in nombre:
        pistas = tuple(p for p in pistas if p not in _ORQUESTA)
    return any(p in nombre for p in pistas)


def tiene_core_musical(nombre: str) -> bool:
    """Señal nuclear: la palabra 'música'/'musical' en el nombre.

    Los programas con 'música'/'musical' se incluyen automáticamente, incluso
    si además contienen señales de dominio excluido (acústica, ultrasonido).
    """
    return "musica" in nombre or "musical" in nombre


def tiene_senal_musical(nombre: str) -> bool:
    return _coincide_pistas(nombre, _SEÑALES_POSITIVAS)


def _es_musicoterapia(nombre: str) -> bool:
    return (
        "musicoterap" in nombre
        or "musico-terapia" in nombre
        or "musico terapia" in nombre
    )


def _es_gestion(nombre: str) -> bool:
    return (
        "gestion cultural" in nombre
        or "industrias de la musica" in nombre
        or ("gestion" in nombre and "musica" in nombre)
        or ("emprendimiento" in nombre and "musica" in nombre)
    )


def _es_idiomas(nombre: str) -> bool:
    """Interpretación/traducción de idiomas o lengua de señas.

    Solo se considera exclusión de idiomas cuando hay contexto de
    interpretación/traducción (o estudio de lengua de señas); una palabra de
    idioma como adjetivo ("musica espanola") no basta para excluir.
    """
    if "lengua de senas" in nombre:
        return True
    contexto_interpretacion = any(
        p in nombre for p in ("interpretacion", "interprete", "traduccion", "interpretariado")
    )
    if not contexto_interpretacion:
        return False
    return any(m in nombre for m in _MARCADORES_IDIOMAS)


def _es_interpretacion_o_traduccion(nombre: str) -> bool:
    return any(p in nombre for p in ("interpretacion", "interprete", "traduccion"))


def _es_interprete_instrumental(nombre: str) -> bool:
    """Interprete/instrumentista musical (no quirúrgico ni industrial)."""
    return ("interprete" in nombre or "interpretacion" in nombre) and (
        "instrumental" in nombre or "instrumentista" in nombre
    )


def _es_artes_visuales(nombre: str) -> bool:
    return any(s in nombre for s in _ARTES_VISUALES)


def _es_arte_sin_mencion(nombre: str) -> bool:
    return bool(_ARTE_PALABRA_RE.search(nombre))


def _es_pedagogia(nombre: str) -> bool:
    if any(p in nombre for p in _PISTAS_PEDAGOGIA):
        return True
    return ("educacion" in nombre) and ("musica" in nombre or "musical" in nombre)


def _es_composicion(nombre: str) -> bool:
    return any(c in nombre for c in _PISTAS_COMPOSICION)


def _es_categoria_interpretacion(nombre: str) -> bool:
    return _coincide_pistas(nombre, _PISTAS_INTERPRETACION) or bool(
        _MUSICO_RE.search(nombre)
    )


def _es_teoria(nombre: str) -> bool:
    return any(t in nombre for t in _PISTAS_TEORIA)


def _es_produccion(nombre: str) -> bool:
    return any(p in nombre for p in _PISTAS_PRODUCCION)


def _categoria(nombre: str) -> str:
    if _es_musicoterapia(nombre):
        return CATEGORIA_MUSICOTERAPIA
    if _es_gestion(nombre):
        return CATEGORIA_GESTION
    if _es_pedagogia(nombre):
        return CATEGORIA_PEDAGOGIA
    if _es_composicion(nombre):
        return CATEGORIA_COMPOSICION
    if _es_categoria_interpretacion(nombre) or _es_interprete_instrumental(nombre):
        return CATEGORIA_INTERPRETACION
    if _es_teoria(nombre):
        return CATEGORIA_TEORIA
    if _es_produccion(nombre):
        return CATEGORIA_PRODUCCION
    if (
        "licenciatura" in nombre
        or "bachiller" in nombre
        or nombre in ("musica", "musical")
    ):
        return CATEGORIA_FORMACION
    return CATEGORIA_OTROS


def _resultado(
    veredicto: str, categoria: str, metodo: str, razon: str
) -> ResultadoClasificacion:
    return {
        "veredicto": veredicto,
        "categoria": categoria,
        "metodo": metodo,
        "razon": razon,
    }


def _excluir(razon: str) -> ResultadoClasificacion:
    """Resultado de exclusión léxica: sin categoría, método léxico."""
    return _resultado(VEREDICTO_EXCLUIR, "", METODO_LEXICO, razon)


def _filtro_semantico(
    nombre: str, contexto: ContextoClasificacion | None
) -> ResultadoClasificacion | None:
    if contexto is None:
        return None
    areas = {normalizar_nombre(a) for a in contexto.get("areas_genericas", []) if a}
    subareas = {normalizar_nombre(s) for s in contexto.get("subareas_cine", []) if s}
    if areas & AREAS_GENERICAS_MUSICALES:
        return _resultado(
            VEREDICTO_INCLUIR,
            CATEGORIA_OTROS,
            METODO_SEMANTICO,
            "Área genérica musical (Música, Canto o Danza / Pedagogía en Artes y Música)",
        )
    if "artes" in subareas:
        return _resultado(
            VEREDICTO_EXCLUIR,
            "",
            METODO_SEMANTICO,
            "Subárea CINE Artes sin señal musical en el nombre",
        )
    return None


def clasificar(
    nombre: str, contexto: ContextoClasificacion | None = None
) -> ResultadoClasificacion:
    """Clasifica un nombre normalizado de programa en un veredicto musical."""
    nombre = normalizar_nombre(nombre)

    if _es_musicoterapia(nombre):
        return _resultado(
            VEREDICTO_INCLUIR,
            CATEGORIA_MUSICOTERAPIA,
            METODO_LEXICO,
            "Musicoterapia (o terapias de arte con mención en musicoterapia)",
        )

    if _es_gestion(nombre):
        return _resultado(
            VEREDICTO_INCLUIR,
            CATEGORIA_GESTION,
            METODO_LEXICO,
            "Gestión cultural",
        )

    if tiene_core_musical(nombre):
        return _resultado(
            VEREDICTO_INCLUIR,
            _categoria(nombre),
            METODO_LEXICO,
            "Nombre con 'música'/'musical' (se incluye automáticamente)",
        )

    if "ultrasonido" in nombre or "ultra sonido" in nombre:
        return _excluir("Ultrasonido médico (no es música ni sonido musical)")

    if "sonido" in nombre and "acustica" in nombre:
        return _resultado(
            VEREDICTO_DUDOSO,
            "",
            METODO_LEXICO,
            f"{ORIGEN_HIBRIDO_SONIDO_ACUSTICA}: se privilegia el sonido "
            "pero la acústica técnica queda en zona gris",
        )

    if tiene_senal_musical(nombre):
        return _resultado(
            VEREDICTO_INCLUIR,
            _categoria(nombre),
            METODO_LEXICO,
            "Señal léxica de música en el nombre",
        )

    if _es_interprete_instrumental(nombre):
        return _resultado(
            VEREDICTO_INCLUIR,
            CATEGORIA_INTERPRETACION,
            METODO_LEXICO,
            "Intérprete instrumental (intérprete de instrumento musical)",
        )

    if _es_idiomas(nombre):
        return _excluir("Interpretación/traducción de idiomas o lengua de señas")

    if _es_interpretacion_o_traduccion(nombre):
        return _excluir("Interpretación/traducción sin contexto musical explícito")

    if "danza" in nombre or "coreografia" in nombre or "ballet" in nombre:
        return _excluir("Danza (dominio artístico no musical)")

    if "teatro" in nombre or "actuacion" in nombre:
        return _excluir("Teatro puro (sin mención de música)")

    if "cine" in nombre or "audiovisual" in nombre or "videojuego" in nombre:
        return _excluir("Cine/audiovisual (se vincula a la videografía, no a la música)")

    if "acustica" in nombre:
        return _excluir("Acústica técnica (edificación, ambiental, submarina, vibraciones)")

    if "terapia" in nombre:
        return _excluir("Terapia no musical")

    if _es_artes_visuales(nombre):
        return _excluir("Artes visuales/plásticas")

    if "licenciatura en artes" in nombre:
        return _excluir("Licenciatura en artes sin mención musical explícita")

    if _es_arte_sin_mencion(nombre):
        return _excluir("Arte sin mención musical explícita")

    if "educacion artistica" in nombre:
        return _resultado(
            VEREDICTO_DUDOSO,
            "",
            METODO_LEXICO,
            f"{ORIGEN_EDUCACION_ARTISTICA} (sin mención de música)",
        )

    resultado = _filtro_semantico(nombre, contexto)
    if resultado is not None:
        return resultado

    return _excluir("Sin señal léxica de música ni contexto musical")
