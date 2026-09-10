"""Cliente reutilizable para el LLM local (Ollama).

Consulta por lotes de 25 nombres normalizados, una sola pasada, y parsea la
respuesta tri-valor ``INCLUIR/EXCLUIR/DUDOSO`` con categoría y razón (JSON).
Maneja fallos (servidor no disponible, respuestas malformadas) sin abortar el
lote: cada nombre recibe un veredicto y los que no se pudieron resolver
reciben ``VEREDICTO_ERROR`` con la razón del fallo. El cliente solo recibe el
conjunto de nombres que el pipeline le pase (frontera o muestras), nunca la
base completa.
"""

import json
import os
import re
import time
import urllib.request
from typing import Any, Callable, TypedDict

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
    METODO_LLM,
    VEREDICTO_DUDOSO,
    VEREDICTO_ERROR,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
)
from sies_musica.texto import normalizar_nombre

TAMANO_LOTE = 25
MODELO_DEFECTO = "gpt-oss:20b"
HOST_DEFECTO = "localhost"
PUERTO_DEFECTO = 11434
TIEMPO_ESPERA_DEFECTO = 180.0

URL_API = "http://{host}:{puerto}/api/chat"

URL_API_CLOUD = "https://api.blablador.fz-juelich.de/v1/chat/completions"
MODELO_CLOUD_DEFECTO = "alias-fast"
PAUSA_ENTRE_LOTES_CLOUD = 1.0
REINTENTOS_CLOUD_DEFECTO = 3
RETROCESO_CLOUD_INICIAL = 5.0
CLAVE_API_ENV = "SIES_BLABLADOR_API_KEY"

VEREDICTOS_VALIDOS = frozenset({VEREDICTO_INCLUIR, VEREDICTO_EXCLUIR, VEREDICTO_DUDOSO})

_CATEGORIAS = (
    CATEGORIA_PEDAGOGIA,
    CATEGORIA_COMPOSICION,
    CATEGORIA_INTERPRETACION,
    CATEGORIA_TEORIA,
    CATEGORIA_FORMACION,
    CATEGORIA_PRODUCCION,
    CATEGORIA_MUSICOTERAPIA,
    CATEGORIA_GESTION,
    CATEGORIA_OTROS,
)
_CATEGORIAS_VALIDAS = frozenset(_CATEGORIAS)

_PROMPT_SISTEMA = (
    "Eres un asistente que ayuda a construir una base de datos de programas de "
    "educación superior musicales de Chile. Recibirás una lista de nombres de "
    "programas de educación superior. Para cada uno decide si pertenece al "
    "universo musical: todo programa cuyo objeto de estudio es la música en "
    "cualquiera de sus dimensiones (docencia, composición, interpretación, "
    "teoría e investigación, formación general, producción de sonido, "
    "musicoterapia o gestión cultural). "
    "Responde exclusivamente con JSON válido, sin texto adicional."
)

_FENCE_RE = re.compile(r"^\s*```(?:json)?(.*?)```\s*$", re.DOTALL)


class ResultadoLLM(TypedDict):
    nombre: str
    veredicto: str
    categoria: str
    metodo: str
    razon: str


Transportador = Callable[[str, bytes, float], str]


def _resultado(
    nombre: str, veredicto: str, categoria: str, razon: str
) -> ResultadoLLM:
    return {
        "nombre": nombre,
        "veredicto": veredicto,
        "categoria": categoria,
        "metodo": METODO_LLM,
        "razon": razon or "Sin razón entregada por el LLM",
    }


def _error(nombre: str, razon: str) -> ResultadoLLM:
    return _resultado(nombre, VEREDICTO_ERROR, "", razon)


def _sin_cercas(texto: str) -> str:
    coincidencia = _FENCE_RE.search(texto)
    return coincidencia.group(1) if coincidencia else texto


def _extraer_json(texto: str) -> Any:
    """Devuelve el primer objeto JSON contenido en el texto, o levanta ValueError."""
    limpio = _sin_cercas(texto).strip()
    try:
        return json.loads(limpio)
    except json.JSONDecodeError:
        pass
    decodificador = json.JSONDecoder()
    for indice, caracter in enumerate(limpio):
        if caracter not in "{[":
            continue
        try:
            return decodificador.raw_decode(limpio, indice)[0]
        except json.JSONDecodeError:
            continue
    raise ValueError("La respuesta no contiene JSON válido")


def _contenido_de_envelope(objeto: Any) -> str | None:
    """Si el texto es un envelope de respuesta, extrae el contenido del asistente.

    Soporta el envelope de Ollama (/api/chat): ``{"message": {"content": ...}}``
    y el de la API de OpenAI (/v1/chat/completions)::
        {"choices": [{"message": {"role": "assistant", "content": ...}}]}
    """
    if not isinstance(objeto, dict):
        return None
    mensaje = objeto.get("message")
    if not isinstance(mensaje, dict):
        opciones = objeto.get("choices")
        if isinstance(opciones, list) and opciones:
            primero = opciones[0]
            if isinstance(primero, dict):
                mensaje = primero.get("message")
    if isinstance(mensaje, dict):
        contenido = mensaje.get("content")
        if isinstance(contenido, str):
            return contenido
    return None


def parsear_respuesta(texto: str, nombres: list[str]) -> list[ResultadoLLM]:
    """Convierte la respuesta cruda del LLM en un resultado por nombre.

    El texto puede venir con cercas de código, con texto antes del JSON, como
    lista desnuda o como envelope de Ollama. Los nombres consultados que no
    aparezcan en la respuesta (o con veredicto inválido) se marcan con
    ``VEREDICTO_ERROR`` sin abortar el resto del lote. El orden de salida es el
    del parámetro ``nombres``.
    """
    claves = [normalizar_nombre(n) for n in nombres]
    try:
        objeto = _extraer_json(texto)
    except ValueError as exc:
        return [_error(clave, f"Respuesta del LLM malformada: {exc}") for clave in claves]

    contenido = _contenido_de_envelope(objeto)
    if contenido is not None:
        return parsear_respuesta(contenido, nombres)

    if isinstance(objeto, dict) and "resultados" in objeto:
        items = objeto["resultados"]
    elif isinstance(objeto, list):
        items = objeto
    else:
        return [
            _error(clave, "La respuesta del LLM no trae el campo 'resultados'")
            for clave in claves
        ]

    consultados = set(claves)
    por_nombre: dict[str, ResultadoLLM] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        nombre_item = item.get("nombre")
        if not isinstance(nombre_item, str):
            continue
        clave = normalizar_nombre(nombre_item)
        if clave in por_nombre or clave not in consultados:
            continue
        veredicto = item.get("veredicto")
        if veredicto not in VEREDICTOS_VALIDOS:
            por_nombre[clave] = _error(
                clave, f"Veredicto desconocido del LLM: {veredicto!r}"
            )
            continue
        categoria = item.get("categoria")
        razon = item.get("razon")
        if not isinstance(categoria, str):
            categoria = ""
        if not isinstance(razon, str):
            razon = ""
        if veredicto == VEREDICTO_INCLUIR and categoria not in _CATEGORIAS_VALIDAS:
            por_nombre[clave] = _error(
                clave,
                f"Categoría fuera de las 9 del dominio para INCLUIR: {categoria!r}",
            )
            continue
        por_nombre[clave] = _resultado(clave, veredicto, categoria, razon)

    return [
        por_nombre[clave]
        if clave in por_nombre
        else _error(clave, f"Nombre '{clave}' ausente en la respuesta del LLM")
        for clave in claves
    ]


def partir_en_lotes(
    nombres: list[str], tamano: int = TAMANO_LOTE
) -> list[list[str]]:
    """Divide una lista de nombres en lotes de a lo más ``tamano``."""
    if tamano <= 0:
        return []
    return [nombres[i : i + tamano] for i in range(0, len(nombres), tamano)]


def _prompt_usuario(nombres: list[str]) -> str:
    lista = json.dumps(nombres, ensure_ascii=False)
    categorias = ", ".join(_CATEGORIAS)
    return (
        "Clasifica cada uno de los siguientes nombres de programa con un "
        "veredicto: INCLUIR (es musical), EXCLUIR (no es musical) o DUDOSO "
        "(no se puede decidir con certeza y requiere revisión humana). "
        f"Categorías posibles (solo para INCLUIR): {categorias}. "
        "Incluye además una razón breve en español. "
        'Responde en este formato JSON: {"resultados": [{"nombre": "...", '
        '"veredicto": "INCLUIR|EXCLUIR|DUDOSO", "categoria": "...", '
        '"razon": "..."}]}. Debes devolver un objeto por cada nombre de la '
        "lista, sin omitir ninguno.\n"
        f"Nombres: {lista}"
    )


def _cuerpo_consulta(modelo: str, nombres: list[str]) -> bytes:
    payload = {
        "model": modelo,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": _PROMPT_SISTEMA},
            {"role": "user", "content": _prompt_usuario(nombres)},
        ],
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _transporte_urllib(url: str, cuerpo: bytes, timeout: float) -> str:
    """Transporte por defecto: POST a la API de Ollama y devuelve el cuerpo crudo."""
    request = urllib.request.Request(
        url, data=cuerpo, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as respuesta:
        bytes_crudo: bytes = respuesta.read()
        return bytes_crudo.decode("utf-8")


def _consultar_lote(
    lote: list[str],
    url: str,
    modelo: str,
    tiempo_espera: float,
    transportador: Transportador,
) -> list[ResultadoLLM]:
    cuerpo = _cuerpo_consulta(modelo, lote)
    try:
        respuesta = transportador(url, cuerpo, tiempo_espera)
    except Exception as exc:  # servidor caído, timeout, HTTP error...
        return [
            _error(nombre, f"Fallo del servidor LLM al consultar el lote: {exc}")
            for nombre in lote
        ]
    return parsear_respuesta(respuesta, lote)


def _cuerpo_consulta_cloud(modelo: str, nombres: list[str]) -> bytes:
    """Cuerpo para la API de OpenAI (Blablador): sin el campo ``format``."""
    payload = {
        "model": modelo,
        "stream": False,
        "messages": [
            {"role": "system", "content": _PROMPT_SISTEMA},
            {"role": "user", "content": _prompt_usuario(nombres)},
        ],
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _transporte_cloud(api_key: str) -> Transportador:
    """Transporte para la API de Blablador con autenticación Bearer."""

    def transporte(url: str, cuerpo: bytes, timeout: float) -> str:
        request = urllib.request.Request(
            url,
            data=cuerpo,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as respuesta:
            bytes_crudo: bytes = respuesta.read()
            return bytes_crudo.decode("utf-8")

    return transporte


def leer_clave_api(ruta_env: os.PathLike[str] | str | None = None) -> str:
    """Devuelve la clave de API de Blablador desde el entorno o un archivo .env.

    Busca primero la variable ``SIES_BLABLADOR_API_KEY`` en el entorno y, si no
    existe, la lee de un archivo ``.env`` (formato ``CLAVE=VALOR``). Levanta
    ``RuntimeError`` si no se encuentra en ninguno de los dos. Nunca imprime ni
    registra la clave.
    """
    clave = os.environ.get(CLAVE_API_ENV)
    if clave:
        return clave
    if ruta_env is None:
        ruta_env = ".env"
    ruta = os.fspath(ruta_env)
    if not os.path.isfile(ruta):
        raise RuntimeError(
            f"No se encontró {CLAVE_API_ENV} en el entorno ni en '{ruta}'. "
            "Crea un archivo .env con la clave de Blablador (ver docs)."
        )
    prefijo = CLAVE_API_ENV + "="
    with open(ruta, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea.startswith(prefijo):
                return linea[len(prefijo):].strip()
    raise RuntimeError(f"El archivo '{ruta}' no define {CLAVE_API_ENV}")


def _consultar_lote_cloud(
    lote: list[str],
    url: str,
    modelo: str,
    transportador: Transportador,
    tiempo_espera: float,
    reintentos: int,
    retroceso_inicial: float,
) -> list[ResultadoLLM]:
    """Consulta un lote a la nube reintentando fallos transitorios del servidor.

    Los fallos de conexión (cierre anticipado, timeout, 429) son transitorios
    bajo carga; se reintenta con retroceso exponencial antes de marcar ERROR.
    """
    for intento in range(reintentos + 1):
        cuerpo = _cuerpo_consulta_cloud(modelo, lote)
        try:
            respuesta = transportador(url, cuerpo, tiempo_espera)
        except Exception as exc:
            if intento < reintentos:
                time.sleep(retroceso_inicial * (2 ** intento))
                continue
            return [
                _error(nombre, f"Fallo del servidor LLM al consultar el lote: {exc}")
                for nombre in lote
            ]
        return parsear_respuesta(respuesta, lote)
    return []


def consultar_nombres_cloud(
    nombres: list[str],
    *,
    api_key: str,
    modelo: str = MODELO_CLOUD_DEFECTO,
    url: str = URL_API_CLOUD,
    tamano_lote: int = TAMANO_LOTE,
    tiempo_espera: float = TIEMPO_ESPERA_DEFECTO,
    pausa_entre_lotes: float = PAUSA_ENTRE_LOTES_CLOUD,
    reintentos: int = REINTENTOS_CLOUD_DEFECTO,
    retroceso_inicial: float = RETROCESO_CLOUD_INICIAL,
    transporte: Transportador | None = None,
    on_progreso: Callable[[int, int], None] | None = None,
) -> list[ResultadoLLM]:
    """Consulta el LLM en la nube (Blablador, API compatible con OpenAI).

    Igual contrato que ``consultar_nombres`` (lotes, una pasada, fallos
    marcados con ``VEREDICTO_ERROR`` sin abortar), pero con autenticación
    Bearer, una pausa opcional entre lotes para respetar los límites de tasa
    del servicio y reintentos con retroceso exponencial para fallos de
    conexión transitorios.
    """
    normalizados = [normalizar_nombre(x) for x in nombres]
    consultados = [n for n in normalizados if n]
    transportador = transporte if transporte is not None else _transporte_cloud(api_key)
    lotes = partir_en_lotes(consultados, tamano_lote)
    total = len(lotes)
    consultados_resultados: list[ResultadoLLM] = []
    for indice, lote in enumerate(lotes, start=1):
        consultados_resultados.extend(
            _consultar_lote_cloud(
                lote,
                url,
                modelo,
                transportador,
                tiempo_espera,
                reintentos,
                retroceso_inicial,
            )
        )
        if on_progreso is not None:
            on_progreso(indice, total)
        if indice < total and pausa_entre_lotes > 0:
            time.sleep(pausa_entre_lotes)
    respuestas = iter(consultados_resultados)
    return [
        next(respuestas)
        if nombre
        else _error(nombre, "Nombre vacío tras normalizar")
        for nombre in normalizados
    ]


def consultar_nombres(
    nombres: list[str],
    *,
    modelo: str = MODELO_DEFECTO,
    host: str = HOST_DEFECTO,
    puerto: int = PUERTO_DEFECTO,
    tamano_lote: int = TAMANO_LOTE,
    tiempo_espera: float = TIEMPO_ESPERA_DEFECTO,
    transporte: Transportador | None = None,
    on_progreso: Callable[[int, int], None] | None = None,
) -> list[ResultadoLLM]:
    """Consulta el LLM local por todos los ``nombres`` en lotes de 25.

    Una sola pasada: cada nombre se consulta una única vez. Un fallo de
    servidor o de parseo afecta solo a los nombres de ese lote (marcados con
    ``VEREDICTO_ERROR``) y el resto continúa. Los nombres que quedan vacíos
    tras normalizar también se devuelven con ``VEREDICTO_ERROR``, sin
    consultarlos, para que cada nombre de entrada tenga su resultado.
    ``on_progreso(lote, total)`` se invoca al terminar cada lote para
    reportar avance.
    """
    normalizados = [normalizar_nombre(x) for x in nombres]
    consultados = [n for n in normalizados if n]
    url = URL_API.format(host=host, puerto=puerto)
    transportador = transporte if transporte is not None else _transporte_urllib
    lotes = partir_en_lotes(consultados, tamano_lote)
    total = len(lotes)
    consultados_resultados: list[ResultadoLLM] = []
    for indice, lote in enumerate(lotes, start=1):
        consultados_resultados.extend(
            _consultar_lote(lote, url, modelo, tiempo_espera, transportador)
        )
        if on_progreso is not None:
            on_progreso(indice, total)
    respuestas = iter(consultados_resultados)
    return [
        next(respuestas)
        if nombre
        else _error(nombre, "Nombre vacío tras normalizar")
        for nombre in normalizados
    ]
