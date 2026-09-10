"""Etapa 04 — Verificación de falsos negativos con el LLM.

Consulta al LLM la red de candidatos (nombres de las áreas genéricas
musicales que NO contienen keyword de música, tras dedupe contra los ya
incluidos y los ya en zona gris) más una muestra aleatoria de ~50 excluidos
como control. Los INCLUIR del LLM se incorporan a la clasificación con método
``llm`` y su razón. Todo veredicto del LLM queda registrado.

Por defecto usa el LLM local (Ollama, ``gpt-oss:20b``). Con ``--cloud`` usa el
LLM en la nube de Blablador (``alias-fast``) leyendo la clave de API de la
variable ``SIES_BLABLADOR_API_KEY`` o del archivo ``.env``, y guarda las
salidas con sufijo ``_cloud``.
"""

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from sies_musica.clasificador import VEREDICTO_ERROR, VEREDICTO_INCLUIR
from sies_musica.cliente_llm import (
    consultar_nombres,
    consultar_nombres_cloud,
    leer_clave_api,
)
from sies_musica.lectura import leer_matricula
from sies_musica.texto import normalizar_nombre
from sies_musica.verificacion import (
    aplicar_veredictos_llm,
    escribir_clasificacion,
    escribir_veredictos_llm,
    formato_fecha,
    leer_clasificacion,
    por_veredicto,
    seleccionar_muestra_control,
    seleccionar_red_candidatos,
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BASE = RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_parcial.csv"
RUTA_SALIDA_VEREDICTOS = RAIZ / "prod" / "verificacion_falsos_negativos.csv"
RUTA_SALIDA_CLASIFICACION = RAIZ / "prod" / "clasificacion_tras_falsos_negativos.csv"
RUTA_LOG = RAIZ / "logs" / "04-verificacion-falsos-negativos.md"

RUTAS_CLOUD = {
    "veredictos": RAIZ / "prod" / "verificacion_falsos_negativos_cloud.csv",
    "clasificacion": RAIZ / "prod" / "clasificacion_tras_falsos_negativos_cloud.csv",
    "log": RAIZ / "logs" / "04-verificacion-falsos-negativos-cloud.md",
}

PROVEEDOR_LOCAL = "`gpt-oss:20b` vía Ollama en `localhost:11434`"
PROVEEDOR_CLOUD = "`alias-fast` (Ministral-3-14B) vía Blablador (`api.blablador.fz-juelich.de`)"

INDICE_NOMBRE = 19
INDICE_AREA_GENERICA = 23


def _relativizar(ruta: Path) -> str:
    """Ruta para el log: relativa a la raíz del repo, con separadores `/`."""
    try:
        return str(ruta.resolve().relative_to(RAIZ)).replace("\\", "/")
    except ValueError:
        return str(ruta.resolve()).replace("\\", "/")


def _areas_por_nombre(df: pd.DataFrame) -> dict[str, set[str]]:
    """Reúne las áreas genéricas (normalizadas) de cada nombre normalizado."""
    areas: dict[str, set[str]] = {}
    for _, fila in df.iterrows():
        nombre = normalizar_nombre(str(fila.iloc[INDICE_NOMBRE]))
        if not nombre.strip():
            continue
        area = normalizar_nombre(str(fila.iloc[INDICE_AREA_GENERICA]))
        if area.strip():
            areas.setdefault(nombre, set()).add(area)
    return areas


def a_markdown(
    red: list[str],
    control: list[str],
    por_veredicto: Counter,
    incorporados: list[str],
    errores: list[str],
    fechas: tuple[str, str],
    proveedor: str,
    ruta_veredictos: Path,
    ruta_clasificacion: Path,
) -> str:
    inicio, fin = fechas
    filas = []
    filas.append("# Etapa 04 — Verificación de falsos negativos con LLM")
    filas.append("")
    filas.append(f"Inicio: {inicio}")
    filas.append(f"Fin: {fin}")
    filas.append(f"Modelo: {proveedor}, lotes de 25.")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"- Nombres consultados: {len(red) + len(control)}")
    filas.append(f"  - Red de candidatos (áreas musicales sin keyword, dedupe): {len(red)}")
    filas.append(f"  - Muestra aleatoria de control (excluidos): {len(control)}")
    filas.append(f"- Nombres incorporados a la clasificación (INCLUIR del LLM): {len(incorporados)}")
    filas.append(f"- Veredictos ERROR (fallos de servidor o de parseo): {por_veredicto[VEREDICTO_ERROR]}")
    filas.append("")
    filas.append("### Por veredicto del LLM")
    filas.append("")
    for veredicto in ("INCLUIR", "EXCLUIR", "DUDOSO", "ERROR"):
        filas.append(f"- {veredicto}: {por_veredicto[veredicto]}")
    if incorporados:
        filas.append("")
        filas.append("### Incorporados a la clasificación (método `llm`)")
        filas.append("")
        for nombre in incorporados:
            filas.append(f"- {nombre}")
    if errores:
        filas.append("")
        filas.append("### Razones de error")
        filas.append("")
        for razon in errores:
            filas.append(f"- {razon}")
    filas.append("")
    filas.append(f"Resultados en `{_relativizar(ruta_veredictos)}`.")
    filas.append(f"Clasificación actualizada en `{_relativizar(ruta_clasificacion)}`.")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Etapa 04 — falsos negativos con LLM.")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Usa el LLM en la nube de Blablador en vez del local (Ollama).",
    )
    args = parser.parse_args()
    cloud = args.cloud

    clasificacion = leer_clasificacion(RUTA_CLASIFICACION)
    print(f"Cargados {len(clasificacion)} nombres de la clasificación parcial.")
    df = leer_matricula(RUTA_BASE)
    areas_por_nombre = _areas_por_nombre(df)
    print(f"Áreas genéricas reunidas para {len(areas_por_nombre)} nombres de la base.")

    red = seleccionar_red_candidatos(clasificacion, areas_por_nombre)
    control = seleccionar_muestra_control(clasificacion, evitar=set(red))
    nombres = red + control
    total = len(nombres)

    ruta_veredictos = RUTAS_CLOUD["veredictos"] if cloud else RUTA_SALIDA_VEREDICTOS
    ruta_clasificacion = RUTAS_CLOUD["clasificacion"] if cloud else RUTA_SALIDA_CLASIFICACION
    ruta_log = RUTAS_CLOUD["log"] if cloud else RUTA_LOG
    proveedor = PROVEEDOR_CLOUD if cloud else PROVEEDOR_LOCAL

    def mostrar_avance(lote: int, total_lotes: int) -> None:
        porcentaje = lote * 100 // total_lotes
        print(f"  Lote {lote}/{total_lotes} ({porcentaje}%)")

    inicio = datetime.now()
    if cloud:
        api_key = leer_clave_api(RAIZ / ".env")
        print(f"Consultando {total} nombres al LLM en la nube (alias-fast), lotes de 25...")
        resultados = consultar_nombres_cloud(
            nombres, api_key=api_key, on_progreso=mostrar_avance
        )
    else:
        print(f"Consultando {total} nombres al LLM local (gpt-oss:20b), lotes de 25...")
        resultados = consultar_nombres(nombres, on_progreso=mostrar_avance)
    fin = datetime.now()

    ruta_veredictos.parent.mkdir(parents=True, exist_ok=True)
    ruta_log.parent.mkdir(parents=True, exist_ok=True)

    red_set = set(red)
    errores = escribir_veredictos_llm(
        ruta_veredictos,
        resultados,
        tipos={r["nombre"]: "red" if r["nombre"] in red_set else "control" for r in resultados},
    )

    actualizada = aplicar_veredictos_llm(clasificacion, resultados)
    incorporados = sorted(
        nombre
        for nombre in nombres
        if actualizada[nombre]["veredicto"] == VEREDICTO_INCLUIR
        and clasificacion[nombre]["veredicto"] != VEREDICTO_INCLUIR
    )
    escribir_clasificacion(ruta_clasificacion, actualizada)

    contador = por_veredicto(resultados)
    ruta_log.write_text(
        a_markdown(
            red,
            control,
            contador,
            incorporados,
            errores,
            (formato_fecha(inicio), formato_fecha(fin)),
            proveedor,
            ruta_veredictos,
            ruta_clasificacion,
        ),
        encoding="utf-8",
    )
    print(ruta_veredictos)
    print(ruta_clasificacion)
    print(ruta_log)
    print(f"Total: {total} | INCLUIR: {contador[VEREDICTO_INCLUIR]} | "
          f"EXCLUIR: {contador['EXCLUIR']} | "
          f"DUDOSO: {contador['DUDOSO']} | "
          f"ERROR: {contador[VEREDICTO_ERROR]} | "
          f"Incorporados: {len(incorporados)}")


if __name__ == "__main__":
    main()