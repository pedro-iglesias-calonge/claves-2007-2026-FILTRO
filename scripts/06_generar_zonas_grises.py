"""Etapa 06 — Generación de zonas grises para la revisión humana.

Sin red y sin LLM: a partir de la clasificación final (tras las pasadas de
falsos negativos y positivos), reúne los puntos frontera — los que quedaron
``DUDOSO`` (del LLM, híbridos "sonido y acústica", educación artística pura o
ambiguos) — en ``prod/zonas_grises.csv``, cada uno con su veredicto, método,
razón y una etiqueta de origen.

Además genera ``prod/zonas_grises_revisadas.csv``: un template con las mismas
filas más las columnas ``decision_final`` y ``categoria_final`` vacías, para
que el humano registre su decisión por punto. Como esa decisión no itera sobre
el LLM y no se debe perder, el template no se pisa si ya existe (el script
avisa por consola y en el log).

Con ``--clasificacion`` y ``--parcial`` se puede apuntar a otra clasificación
(p. ej. la réplica ``_cloud``) y a otra fuente de nombres originales.
"""

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

from sies_musica.verificacion import formato_fecha, leer_clasificacion
from sies_musica.zonas_grises import (
    ORIGEN_AMBIGUO,
    ORIGEN_EDUCACION_ARTISTICA,
    ORIGEN_HIBRIDO,
    ORIGEN_LLM,
    escribir_revision,
    escribir_zonas_grises,
    filas_zonas_grises,
    leer_originales,
    por_origen,
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_tras_falsos_positivos.csv"
RUTA_PARTIAL = RAIZ / "prod" / "clasificacion_parcial.csv"
RUTA_ZONAS = RAIZ / "prod" / "zonas_grises.csv"
RUTA_REVISION = RAIZ / "prod" / "zonas_grises_revisadas.csv"
RUTA_LOG = RAIZ / "logs" / "06-zonas-grises.md"


def _relativizar(ruta: Path) -> str:
    """Ruta para el log: relativa a la raíz del repo, con separadores `/`."""
    try:
        return str(ruta.resolve().relative_to(RAIZ)).replace("\\", "/")
    except ValueError:
        return str(ruta.resolve()).replace("\\", "/")


def a_markdown(
    conteo_por_origen: Counter[str],
    fechas: tuple[str, str],
    ruta_clasificacion: Path,
    ruta_zonas: Path,
    ruta_revision: Path,
    template_creado: bool,
) -> str:
    inicio, fin = fechas
    filas = []
    filas.append("# Etapa 06 — Zonas grises para revisión humana")
    filas.append("")
    filas.append(f"Inicio: {inicio}")
    filas.append(f"Fin: {fin}")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"Puntos frontera hacia la revisión humana: {sum(conteo_por_origen.values())}")
    filas.append("")
    filas.append("### Por origen")
    filas.append("")
    for origen in (ORIGEN_LLM, ORIGEN_HIBRIDO, ORIGEN_EDUCACION_ARTISTICA, ORIGEN_AMBIGUO):
        filas.append(f"- {origen}: {conteo_por_origen[origen]}")
    filas.append("")
    filas.append(f"Clasificación de entrada: `{_relativizar(ruta_clasificacion)}`.")
    estado_revision = "creado (la revisión humana está por decidir)" if template_creado else (
        "ya existía: no se pisó para no perder decisiones humanas"
    )
    filas.append(f"Template de revisión humana: {estado_revision}.")
    filas.append("")
    filas.append(f"Resultados en `{_relativizar(ruta_zonas)}`.")
    filas.append(f"Revisión humana en `{_relativizar(ruta_revision)}`.")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Etapa 06 — zonas grises para revisión humana.")
    parser.add_argument(
        "--clasificacion",
        type=Path,
        default=RUTA_CLASIFICACION,
        help=f"Clasificación final de la etapa 05 (por defecto {RUTA_CLASIFICACION}).",
    )
    parser.add_argument(
        "--parcial",
        type=Path,
        default=RUTA_PARTIAL,
        help=f"Clasificación parcial con nombres originales (por defecto {RUTA_PARTIAL}).",
    )
    args = parser.parse_args()

    ruta_clasificacion = args.clasificacion.resolve()
    ruta_parcial = args.parcial.resolve()

    inicio = datetime.now()
    clasificacion = leer_clasificacion(ruta_clasificacion)
    print(f"Cargados {len(clasificacion)} nombres desde {ruta_clasificacion.name}.")

    originales = leer_originales(ruta_parcial) if ruta_parcial.exists() else {}
    filas = filas_zonas_grises(clasificacion, originales)
    conteo_por_origen = por_origen(filas)

    RUTA_ZONAS.parent.mkdir(parents=True, exist_ok=True)
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)

    escribir_zonas_grises(RUTA_ZONAS, filas)
    template_creado = escribir_revision(RUTA_REVISION, filas)
    fin = datetime.now()

    ruta_log_markdown = a_markdown(
        conteo_por_origen,
        (formato_fecha(inicio), formato_fecha(fin)),
        ruta_clasificacion,
        RUTA_ZONAS,
        RUTA_REVISION,
        template_creado,
    )
    RUTA_LOG.write_text(ruta_log_markdown, encoding="utf-8")

    print(RUTA_ZONAS)
    print(RUTA_REVISION)
    print(RUTA_LOG)
    if not template_creado:
        print(
            f"AVISO: {RUTA_REVISION.name} ya existía; no se pisó para no perder decisiones humanas."
        )
    print(
        f"Total: {len(filas)} | LLM: {conteo_por_origen[ORIGEN_LLM]} | "
        f"Híbridos: {conteo_por_origen[ORIGEN_HIBRIDO]} | "
        f"Ed. artística: {conteo_por_origen[ORIGEN_EDUCACION_ARTISTICA]} | "
        f"Ambiguos: {conteo_por_origen[ORIGEN_AMBIGUO]}"
    )


if __name__ == "__main__":
    main()