"""Verificación de falsos negativos y positivos con el LLM local (seam puro).

Etapas 04 y 05 de la metodología: dos pasadas de control sobre la
clasificación.

(a) Falsos negativos: red de candidatos = nombres de las áreas genéricas
    musicales que NO contienen keyword de música (tras dedupe contra los ya
    incluidos), más una muestra aleatoria de excluidos como control. Se
    consultan al LLM y los INCLUIR se incorporan a la clasificación con
    método ``llm``.

(b) Falsos positivos: los incluidos fronterizos (incluidos sin la señal
    nuclear 'música'/'musical') se consultan al LLM; los EXCLUIR se retiran
    de la inclusión y los DUDOSO quedan marcados para zonas grises.

Todo veredicto del LLM se registra con método ``llm`` y su razón.

Además de la lógica de selección y fusión, este módulo ofrece los helpers de
persistencia que comparten los scripts de las etapas 04 y 05: leer y escribir
la clasificación, escribir los veredictos del LLM y formatear fechas.
"""

import csv
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from sies_musica.clasificador import (
    AREAS_GENERICAS_MUSICALES,
    METODO_LLM,
    VEREDICTO_DUDOSO,
    VEREDICTO_ERROR,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    ResultadoClasificacion,
    tiene_core_musical,
    tiene_senal_musical,
)
from sies_musica.cliente_llm import ResultadoLLM

SEMILLA_CONTROL = 2026
TAMANO_MUESTRA_CONTROL = 50

COLUMNAS_VEREDICTOS = [
    "nombre_normalizado",
    "veredicto",
    "categoria",
    "metodo",
    "razon",
]

COLUMNAS_CLASIFICACION = [
    "nombre_normalizado",
    "veredicto",
    "categoria",
    "metodo",
    "razon",
]


def seleccionar_red_candidatos(
    clasificacion: dict[str, ResultadoClasificacion],
    areas_por_nombre: dict[str, set[str]],
) -> list[str]:
    """Red de candidatos a falsos negativos.

    Nombres en las áreas genéricas musicales que no contienen keyword de
    música y no están ya decididos (dedupe contra la clasificación actual):
    se excluyen los ya INCLUIR y los ya DUDOSO (zona gris, sin iterar).
    """
    red = []
    for nombre, areas in sorted(areas_por_nombre.items()):
        previo = clasificacion.get(nombre)
        if not (areas & AREAS_GENERICAS_MUSICALES):
            continue
        if tiene_senal_musical(nombre):
            continue
        if previo is not None and previo["veredicto"] in (
            VEREDICTO_INCLUIR,
            VEREDICTO_DUDOSO,
        ):
            continue
        red.append(nombre)
    return red


def seleccionar_muestra_control(
    clasificacion: dict[str, ResultadoClasificacion],
    tamano: int = TAMANO_MUESTRA_CONTROL,
    semilla: int = SEMILLA_CONTROL,
    evitar: set[str] | None = None,
) -> list[str]:
    """Muestra aleatoria reproducible de ~50 excluidos como control.

    Solo se toman nombres EXCLUIR que no estén ya en ``evitar`` (la red de
    candidatos), para no consultar dos veces el mismo nombre.
    """
    evitar = evitar or set()
    excluidos = sorted(
        nombre
        for nombre, r in clasificacion.items()
        if r["veredicto"] == VEREDICTO_EXCLUIR and nombre not in evitar
    )
    if not excluidos:
        return []
    return random.Random(semilla).sample(excluidos, min(tamano, len(excluidos)))


def seleccionar_incluidos_fronterizos(
    clasificacion: dict[str, ResultadoClasificacion],
) -> list[str]:
    """Incluidos fronterizos: INCLUIR sin la señal nuclear 'música'/'musical'.

    Son los candidatos a falsos positivos: su inclusión descansa en señales
    secundarias (canto, coro, sonido, instrumentos, gestión cultural, etc.).
    """
    return sorted(
        nombre
        for nombre, r in clasificacion.items()
        if r["veredicto"] == VEREDICTO_INCLUIR and not tiene_core_musical(nombre)
    )


def aplicar_veredictos_llm(
    clasificacion: dict[str, ResultadoClasificacion],
    veredictos_llm: list[ResultadoLLM],
) -> dict[str, ResultadoClasificacion]:
    """Fusiona los veredictos del LLM en la clasificación con método ``llm``.

    INCLUIR se incorpora (con su categoría), EXCLUIR se retira de la
    inclusión y DUDOSO queda marcado para zonas grises. Un ERROR conserva la
    clasificación previa. Devuelve una copia; no muta la entrada.
    """
    fusionada = dict(clasificacion)
    for v in veredictos_llm:
        if v["veredicto"] == VEREDICTO_ERROR:
            continue
        fusionada[v["nombre"]] = {
            "veredicto": v["veredicto"],
            "categoria": v["categoria"],
            "metodo": METODO_LLM,
            "razon": v["razon"],
        }
    return fusionada


def leer_clasificacion(ruta: Path) -> dict[str, ResultadoClasificacion]:
    """Lee un CSV de clasificación a un dict por nombre normalizado."""
    clasificacion: dict[str, ResultadoClasificacion] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            clasificacion[fila["nombre_normalizado"]] = {
                "veredicto": fila["veredicto"],
                "categoria": fila["categoria"],
                "metodo": fila["metodo"],
                "razon": fila["razon"],
            }
    return clasificacion


def escribir_clasificacion(
    ruta: Path, clasificacion: dict[str, ResultadoClasificacion]
) -> None:
    """Escribe la clasificación completa ordenada por nombre normalizado."""
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_CLASIFICACION)
        writer.writeheader()
        for nombre, res in sorted(clasificacion.items()):
            writer.writerow(
                {
                    "nombre_normalizado": nombre,
                    "veredicto": res["veredicto"],
                    "categoria": res["categoria"],
                    "metodo": res["metodo"],
                    "razon": res["razon"],
                }
            )


def escribir_veredictos_llm(
    ruta: Path,
    resultados: list[ResultadoLLM],
    tipos: dict[str, str] | None = None,
) -> list[str]:
    """Escribe los veredictos del LLM; devuelve las razones de error únicas.

    Si ``tipos`` se entrega (p. ej. 'red'/'control'), se agrega la columna
    ``tipo`` al archivo.
    """
    errores: list[str] = []
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        columnas = list(COLUMNAS_VEREDICTOS)
        if tipos is not None:
            columnas = ["tipo"] + columnas
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for resultado in resultados:
            if (
                resultado["veredicto"] == VEREDICTO_ERROR
                and resultado["razon"] not in errores
            ):
                errores.append(resultado["razon"])
            fila = {
                "nombre_normalizado": resultado["nombre"],
                "veredicto": resultado["veredicto"],
                "categoria": resultado["categoria"],
                "metodo": resultado["metodo"],
                "razon": resultado["razon"],
            }
            if tipos is not None:
                fila["tipo"] = tipos[resultado["nombre"]]
            writer.writerow(fila)
    return errores


def por_veredicto(resultados: list[ResultadoLLM]) -> Counter[str]:
    """Conteo de veredictos del LLM para el log de la etapa."""
    return Counter(r["veredicto"] for r in resultados)


def formato_fecha(fecha: datetime) -> str:
    """Formato de fecha usado en los logs de las etapas."""
    return fecha.strftime("%Y-%m-%d %H:%M:%S")
