"""Utilidades de normalización de texto para nombres de carrera."""

import re
import unicodedata

_ESPACIOS_RE = re.compile(r"\s+")


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre de carrera: minúsculas, sin tildes, sin espacios sobrantes."""
    descompuesto = unicodedata.normalize("NFD", nombre)
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    sin_espacios = _ESPACIOS_RE.sub(" ", sin_tildes)
    return sin_espacios.strip().casefold()
