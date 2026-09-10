"""Etapa 05 — Verificación de falsos positivos con el LLM.

Consulta al LLM los incluidos fronterizos (incluidos cuyo nombre no porta la
palabra clave central "música"/"musical" y cuya inclusión descansa en señales
secundarias). Los EXCLUIR del LLM se retiran de la inclusión y los DUDOSO se
marcan para las zonas grises, sin re-consultar. Todo veredicto del LLM queda
registrado con método ``llm`` y su razón.

Por defecto usa el LLM local (Ollama, ``gpt-oss:20b``). Con ``--cloud`` usa el
LLM en la nube de Blablador (``alias-fast``) leyendo la clave de API de la
variable ``SIES_BLABLADOR_API_KEY`` o del archivo ``.env``, y guarda las
salidas con sufijo ``_cloud``.
"""

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

from sies_musica.clasificador import (
    VEREDICTO_DUDOSO,
    VEREDICTO_ERROR,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
)
from sies_musica.cliente_llm import (
    consultar_nombres,
    consultar_nombres_cloud,
    leer_clave_api,
)
from sies_musica.verificacion import (
    aplicar_veredictos_llm,
    escribir_clasificacion,
    escribir_veredictos_llm,
    formato_fecha,
    leer_clasificacion,
    por_veredicto,
    seleccionar_incluidos_fronterizos,
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CLASIFICACION = RAIZ / "prod" / "clasificacion_tras_falsos_negativos.csv"
RUTA_SALIDA_VEREDICTOS = RAIZ / "prod" / "verificacion_falsos_positivos.csv"
RUTA_SALIDA_CLASIFICACION = RAIZ / "prod" / "clasificacion_tras_falsos_positivos.csv"
RUTA_LOG = RAIZ / "logs" / "05-verificacion-falsos-positivos.md"

RUTAS_CLOUD = {
    "clasificacion_entrada": RAIZ / "prod" / "clasificacion_tras_falsos_negativos_cloud.csv",
    "veredictos": RAIZ / "prod" / "verificacion_falsos_positivos_cloud.csv",
    "clasificacion": RAIZ / "prod" / "clasificacion_tras_falsos_positivos_cloud.csv",
    "log": RAIZ / "logs" / "05-verificacion-falsos-positivos-cloud.md",
}

PROVEEDOR_LOCAL = "`gpt-oss:20b` vía Ollama en `localhost:11434`"
PROVEEDOR_CLOUD = "`alias-fast` (Ministral-3-14B) vía Blablador (`api.blablador.fz-juelich.de`)"


def _relativizar(ruta: Path) -> str:
    """Ruta para el log: relativa a la raíz del repo, con separadores `/`."""
    try:
        return str(ruta.resolve().relative_to(RAIZ)).replace("\\", "/")
    except ValueError:
        return str(ruta.resolve()).replace("\\", "/")


def a_markdown(
    fronterizos: list[str],
    por_veredicto: Counter,
    retirados: list[str],
    dudosos: list[str],
    errores: list[str],
    fechas: tuple[str, str],
    proveedor: str,
    ruta_veredictos: Path,
    ruta_clasificacion: Path,
) -> str:
    inicio, fin = fechas
    filas = []
    filas.append("# Etapa 05 — Verificación de falsos positivos con LLM")
    filas.append("")
    filas.append(f"Inicio: {inicio}")
    filas.append(f"Fin: {fin}")
    filas.append(f"Modelo: {proveedor}, lotes de 25.")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"- Incluidos fronterizos consultados: {len(fronterizos)}")
    filas.append(f"- Retirados de la inclusión (EXCLUIR del LLM): {len(retirados)}")
    filas.append(f"- Marcados para zonas grises (DUDOSO del LLM): {len(dudosos)}")
    filas.append(f"- Veredictos ERROR (fallos de servidor o de parseo): {por_veredicto[VEREDICTO_ERROR]}")
    filas.append("")
    filas.append("### Por veredicto del LLM")
    filas.append("")
    for veredicto in (VEREDICTO_INCLUIR, VEREDICTO_EXCLUIR, VEREDICTO_DUDOSO, VEREDICTO_ERROR):
        filas.append(f"- {veredicto}: {por_veredicto[veredicto]}")
    if retirados:
        filas.append("")
        filas.append("### Retirados de la inclusión (método `llm`)")
        filas.append("")
        for nombre in retirados:
            filas.append(f"- {nombre}")
    if dudosos:
        filas.append("")
        filas.append("### Marcados para zonas grises (método `llm`, sin re-consultar)")
        filas.append("")
        for nombre in dudosos:
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
    parser = argparse.ArgumentParser(description="Etapa 05 — falsos positivos con LLM.")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Usa el LLM en la nube de Blablador en vez del local (Ollama).",
    )
    args = parser.parse_args()
    cloud = args.cloud

    ruta_clasificacion_entrada = (
        RUTAS_CLOUD["clasificacion_entrada"] if cloud else RUTA_CLASIFICACION
    )
    ruta_veredictos = RUTAS_CLOUD["veredictos"] if cloud else RUTA_SALIDA_VEREDICTOS
    ruta_clasificacion = RUTAS_CLOUD["clasificacion"] if cloud else RUTA_SALIDA_CLASIFICACION
    ruta_log = RUTAS_CLOUD["log"] if cloud else RUTA_LOG
    proveedor = PROVEEDOR_CLOUD if cloud else PROVEEDOR_LOCAL

    clasificacion = leer_clasificacion(ruta_clasificacion_entrada)
    print(f"Cargados {len(clasificacion)} nombres tras la etapa de falsos negativos.")

    fronterizos = seleccionar_incluidos_fronterizos(clasificacion)
    total = len(fronterizos)
    print(f"Consultando {total} incluidos fronterizos al LLM, lotes de 25...")

    def mostrar_avance(lote: int, total_lotes: int) -> None:
        porcentaje = lote * 100 // total_lotes
        print(f"  Lote {lote}/{total_lotes} ({porcentaje}%)")

    inicio = datetime.now()
    if cloud:
        api_key = leer_clave_api(RAIZ / ".env")
        resultados = consultar_nombres_cloud(
            fronterizos, api_key=api_key, on_progreso=mostrar_avance
        )
    else:
        resultados = consultar_nombres(fronterizos, on_progreso=mostrar_avance)
    fin = datetime.now()

    ruta_veredictos.parent.mkdir(parents=True, exist_ok=True)
    ruta_log.parent.mkdir(parents=True, exist_ok=True)

    errores = escribir_veredictos_llm(ruta_veredictos, resultados)

    actualizada = aplicar_veredictos_llm(clasificacion, resultados)
    retirados = sorted(
        nombre
        for nombre in fronterizos
        if clasificacion[nombre]["veredicto"] == VEREDICTO_INCLUIR
        and actualizada[nombre]["veredicto"] == VEREDICTO_EXCLUIR
    )
    dudosos = sorted(
        nombre
        for nombre in fronterizos
        if actualizada[nombre]["veredicto"] == VEREDICTO_DUDOSO
    )
    escribir_clasificacion(ruta_clasificacion, actualizada)

    contador = por_veredicto(resultados)
    ruta_log.write_text(
        a_markdown(
            fronterizos,
            contador,
            retirados,
            dudosos,
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
          f"EXCLUIR: {contador[VEREDICTO_EXCLUIR]} | "
          f"DUDOSO: {contador[VEREDICTO_DUDOSO]} | "
          f"ERROR: {contador[VEREDICTO_ERROR]} | "
          f"Retirados: {len(retirados)} | Dudosos: {len(dudosos)}")


if __name__ == "__main__":
    main()