"""Etapa 03 — Cliente LLM (Ollama): prueba de humo contra el servidor real.

Demuestra el cliente reutilizable de ``sies_musica/cliente_llm.py``: consulta
en lotes de 25 con reporte de avance (%), parseo tri-valor con categoría y
razón, y manejo de fallos sin abortar. Usa una muestra de la clasificación
parcial (los DUDOSO + una muestra aleatoria de EXCLUIR como control): el
cliente nunca recibe los 16.684 nombres completos.
"""

import csv
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from sies_musica.clasificador import (
    VEREDICTO_DUDOSO,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
)
from sies_musica.cliente_llm import VEREDICTO_ERROR, consultar_nombres

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_parcial.csv"
RUTA_SALIDA = RAIZ / "prod" / "verificacion_llm_demo.csv"
RUTA_LOG = RAIZ / "logs" / "03-cliente-llm.md"

SEMILLA = 2026
TAMANO_MUESTRA_CONTROL = 40

COLUMNAS_SALIDA = [
    "nombre_normalizado",
    "veredicto",
    "categoria",
    "metodo",
    "razon",
]


def _leer_por_veredicto(ruta: Path) -> dict[str, list[str]]:
    por_veredicto: dict[str, list[str]] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            veredicto = fila["veredicto"]
            por_veredicto.setdefault(veredicto, []).append(fila["nombre_normalizado"])
    return por_veredicto


def _muestra() -> list[str]:
    """DUDOSO de la etapa 02 + muestra aleatoria reproducible de EXCLUIR."""
    por_veredicto = _leer_por_veredicto(RUTA_CLASIFICACION)
    dudosos = list(por_veredicto.get(VEREDICTO_DUDOSO, []))
    control = random.Random(SEMILLA).sample(
        por_veredicto.get(VEREDICTO_EXCLUIR, []), TAMANO_MUESTRA_CONTROL
    )
    return dudosos + control


def _a_markdown(
    total: int, por_veredicto: Counter, errores: list[str], fechas: tuple[str, str]
) -> str:
    inicio, fin = fechas
    filas = []
    filas.append("# Etapa 03 — Cliente LLM (Ollama): prueba de humo")
    filas.append("")
    filas.append(f"Inicio: {inicio}")
    filas.append(f"Fin: {fin}")
    filas.append("Modelo: `gpt-oss:20b` vía Ollama en `localhost:11434`, lotes de 25.")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"- Nombres consultados (muestra): {total}")
    filas.append(f"- Veredictos ERROR (fallos del servidor o de parseo): {por_veredicto[VEREDICTO_ERROR]}")
    filas.append("")
    filas.append("### Por veredicto del LLM")
    filas.append("")
    for veredicto in (
        VEREDICTO_INCLUIR,
        VEREDICTO_EXCLUIR,
        VEREDICTO_DUDOSO,
        VEREDICTO_ERROR,
    ):
        filas.append(f"- {veredicto}: {por_veredicto[veredicto]}")
    if errores:
        filas.append("")
        filas.append("### Razones de error")
        filas.append("")
        for razon in errores:
            filas.append(f"- {razon}")
    filas.append("")
    filas.append("Resultados en `prod/verificacion_llm_demo.csv`.")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    nombres = _muestra()
    total = len(nombres)
    print(f"Consultando {total} nombres al LLM local (gpt-oss:20b), lotes de 25...")

    def mostrar_avance(lote: int, total_lotes: int) -> None:
        porcentaje = lote * 100 // total_lotes
        print(f"  Lote {lote}/{total_lotes} ({porcentaje}%)")

    inicio = datetime.now()
    resultados = consultar_nombres(nombres, on_progreso=mostrar_avance)
    fin = datetime.now()

    por_veredicto: Counter[str] = Counter()
    errores: list[str] = []
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)

    with open(RUTA_SALIDA, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_SALIDA)
        writer.writeheader()
        for resultado in resultados:
            por_veredicto[resultado["veredicto"]] += 1
            if (
                resultado["veredicto"] == VEREDICTO_ERROR
                and resultado["razon"] not in errores
            ):
                errores.append(resultado["razon"])
            writer.writerow(
                {
                    "nombre_normalizado": resultado["nombre"],
                    "veredicto": resultado["veredicto"],
                    "categoria": resultado["categoria"],
                    "metodo": resultado["metodo"],
                    "razon": resultado["razon"],
                }
            )

    def _formato(fecha: datetime) -> str:
        return fecha.strftime("%Y-%m-%d %H:%M:%S")

    RUTA_LOG.write_text(
        _a_markdown(total, por_veredicto, errores, (_formato(inicio), _formato(fin))),
        encoding="utf-8",
    )
    print(RUTA_SALIDA)
    print(RUTA_LOG)
    print(f"Total: {total} | INCLUIR: {por_veredicto[VEREDICTO_INCLUIR]} | "
          f"EXCLUIR: {por_veredicto[VEREDICTO_EXCLUIR]} | "
          f"DUDOSO: {por_veredicto[VEREDICTO_DUDOSO]} | "
          f"ERROR: {por_veredicto[VEREDICTO_ERROR]}")


if __name__ == "__main__":
    main()
