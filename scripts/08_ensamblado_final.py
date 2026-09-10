"""Etapa 08 — Ensamblado final incorporando la revisión humana.

Sin red y sin LLM: toma la clasificación automática (léxica + semántica +
LLM, ya depurada tras las pasadas de falsos negativos y positivos) y la
fusiona con las decisiones humanas de ``prod/zonas_grises_revisadas.csv``.
De la clasificación total resultante:

- escribe ``prod/clasificacion_total.csv`` (veredicto final por nombre con
  categoría, método y razón, ordenado);
- reduce ``datos SIES/.../Matricula_2007_2026_WEB_10_07_2026.csv`` a las
  filas de los programas incluidos (todos los años, todas las sedes), en
  ``prod/Musica_2007_2026_filtrado.csv``, conservando las 58 columnas
  originales y el encoding cp1252.

Con ``--clasificacion``, ``--revision`` y ``--matricula`` se puede apuntar a
otras fuentes (p. ej. los réplicas ``_cloud``).
"""

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

from sies_musica.ensamblado import (
    RAZON_DECISION_HUMANA,
    escribir_filtrado,
    filtrar_matricula,
    fusionar_revision,
    leer_decisiones,
    seleccionar_incluidos,
)
from sies_musica.lectura import leer_matricula
from sies_musica.verificacion import (
    escribir_clasificacion,
    formato_fecha,
    leer_clasificacion,
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_tras_falsos_positivos.csv"
RUTA_REVISION = RAIZ / "prod" / "zonas_grises_revisadas.csv"
RUTA_MATRICULA = RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
RUTA_CLASIFICACION_TOTAL = RAIZ / "prod" / "clasificacion_total.csv"
RUTA_FILTRADO = RAIZ / "prod" / "Musica_2007_2026_filtrado.csv"
RUTA_LOG = RAIZ / "logs" / "08-ensamblado-final.md"


def _relativizar(ruta: Path) -> str:
    """Ruta para el log: relativa a la raíz del repo, con separadores `/`."""
    try:
        return str(ruta.resolve().relative_to(RAIZ)).replace("\\", "/")
    except ValueError:
        return str(ruta.resolve()).replace("\\", "/")


def a_markdown(
    fechas: tuple[str, str],
    por_veredicto: Counter[str],
    decisiones_humanas: Counter[str],
    ruta_clasificacion: Path,
    ruta_revision: Path,
    ruta_matricula: Path,
    ruta_clasificacion_total: Path,
    matriz_shape: tuple[int, int],
    ruta_filtrado: Path,
    filtrado_shape: tuple[int, int],
) -> str:
    inicio, fin = fechas
    filas = []
    filas.append("# Etapa 08 — Ensamblado final")
    filas.append("")
    filas.append(f"Inicio: {inicio}")
    filas.append(f"Fin: {fin}")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"Programas en la clasificación total: {sum(por_veredicto.values())}")
    filas.append("")
    filas.append("### Por veredicto final")
    filas.append("")
    for veredicto in ("INCLUIR", "EXCLUIR", "DUDOSO"):
        filas.append(f"- {veredicto}: {por_veredicto[veredicto]}")
    filas.append("")
    filas.append("### Decisiones humanas aplicadas")
    filas.append("")
    for decision in ("INCLUIR", "EXCLUIR"):
        filas.append(f"- {decision}: {decisiones_humanas[decision]}")
    filas.append("")
    filas.append(f"Clasificación de entrada: `{_relativizar(ruta_clasificacion)}`.")
    filas.append(f"Revisión humana: `{_relativizar(ruta_revision)}`.")
    filas.append(f"Clasificación total: `{_relativizar(ruta_clasificacion_total)}`.")
    filas.append("")
    filas.append("### Archivo filtrado")
    filas.append("")
    filas.append(
        f"Matrícula de entrada: `{_relativizar(ruta_matricula)}` "
        f"({matriz_shape[0]:,} filas × {matriz_shape[1]} columnas)."
    )
    filas.append(
        f"Matrícula filtrada: `{_relativizar(ruta_filtrado)}` "
        f"({filtrado_shape[0]:,} filas × {filtrado_shape[1]} columnas)."
    )
    filas.append(
        "Conserva las 58 columnas de la base original y el encoding cp1252 "
        "(sin BOM, salto de línea CRLF, comillas solo donde el formato lo exige)."
    )
    filas.append("")
    filas.append(
        "La decisión humana suma la razón: "
        f"`{RAZON_DECISION_HUMANA}` con método `humano` en la clasificación total."
    )
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Etapa 08 — ensamblado final.")
    parser.add_argument(
        "--clasificacion",
        type=Path,
        default=RUTA_CLASIFICACION,
        help=f"Clasificación de la etapa 05 (por defecto {RUTA_CLASIFICACION}).",
    )
    parser.add_argument(
        "--revision",
        type=Path,
        default=RUTA_REVISION,
        help=f"Decisiones humanas (por defecto {RUTA_REVISION}).",
    )
    parser.add_argument(
        "--matricula",
        type=Path,
        default=RUTA_MATRICULA,
        help=f"Base de matrícula SIES (por defecto {RUTA_MATRICULA}).",
    )
    args = parser.parse_args()

    ruta_clasificacion = args.clasificacion.resolve()
    ruta_revision = args.revision.resolve()
    ruta_matricula = args.matricula.resolve()

    inicio = datetime.now()

    clasificacion = leer_clasificacion(ruta_clasificacion)
    print(f"Cargados {len(clasificacion)} programas desde {ruta_clasificacion.name}.")

    decisiones = leer_decisiones(ruta_revision)
    print(f"Aplicadas {len(decisiones)} decisiones humanas desde {ruta_revision.name}.")

    clasificacion_total = fusionar_revision(clasificacion, decisiones)
    incluidos = seleccionar_incluidos(clasificacion_total)
    por_veredicto = Counter(res["veredicto"] for res in clasificacion_total.values())
    decisiones_humanas = Counter(
        d["decision_final"] for d in decisiones.values()
    )

    RUTA_CLASIFICACION_TOTAL.parent.mkdir(parents=True, exist_ok=True)
    RUTA_FILTRADO.parent.mkdir(parents=True, exist_ok=True)
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)

    escribir_clasificacion(RUTA_CLASIFICACION_TOTAL, clasificacion_total)
    print(f"Escrita clasificación total: {RUTA_CLASIFICACION_TOTAL.name}.")

    print(f"Leyendo matrícula completa desde {ruta_matricula.name}...")
    matriz = leer_matricula(ruta_matricula)
    filtrado = filtrar_matricula(matriz, incluidos)
    escribir_filtrado(RUTA_FILTRADO, filtrado)
    fin = datetime.now()

    print(f"Matrícula: {len(matriz):,} filas -> filtrado {len(filtrado):,} filas.")

    ruta_log_markdown = a_markdown(
        (formato_fecha(inicio), formato_fecha(fin)),
        por_veredicto,
        decisiones_humanas,
        ruta_clasificacion,
        ruta_revision,
        ruta_matricula,
        RUTA_CLASIFICACION_TOTAL,
        (len(matriz), matriz.shape[1]),
        RUTA_FILTRADO,
        (len(filtrado), filtrado.shape[1]),
    )
    RUTA_LOG.write_text(ruta_log_markdown, encoding="utf-8")

    print(RUTA_CLASIFICACION_TOTAL)
    print(RUTA_FILTRADO)
    print(RUTA_LOG)
    print(
        f"Total: {sum(por_veredicto.values())} | "
        f"INCLUIR: {por_veredicto['INCLUIR']} | "
        f"EXCLUIR: {por_veredicto['EXCLUIR']} | "
        f"DUDOSO: {por_veredicto['DUDOSO']} | "
        f"Incluidos: {len(incluidos)}"
    )


if __name__ == "__main__":
    main()