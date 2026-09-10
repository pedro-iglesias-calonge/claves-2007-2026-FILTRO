"""Tests del cliente LLM (Ollama): parseo, lotes y manejo de fallos.

Seams confirmadas:
1. ``parsear_respuesta(texto, nombres)`` — función pura, sin red.
2. ``partir_en_lotes(nombres, tamano)`` — división pura.
3. ``consultar_nombres(nombres, transporte=...)`` — API pública con
   transporte HTTP inyectable; no aborta ante fallos.
"""

import json

import pytest

from sies_musica.cliente_llm import (
    _cuerpo_consulta_cloud,
    VEREDICTO_DUDOSO,
    VEREDICTO_ERROR,
    VEREDICTO_EXCLUIR,
    VEREDICTO_INCLUIR,
    consultar_nombres,
    consultar_nombres_cloud,
    leer_clave_api,
    parsear_respuesta,
    partir_en_lotes,
)


def _envelope_respuesta(texto: str) -> str:
    return json.dumps({"message": {"role": "assistant", "content": texto}})


def _envelope_openai(texto: str) -> str:
    return json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": texto}}]}
    )


def _json_ok(nombres: list[str]) -> str:
    return json.dumps(
        {
            "resultados": [
                {
                    "nombre": n,
                    "veredicto": "INCLUIR",
                    "categoria": "Otros",
                    "razon": "razon de " + n,
                }
                for n in nombres
            ]
        }
    )


# ---------------------------------------------------------------------------
# parsear_respuesta
# ---------------------------------------------------------------------------


def test_parsea_json_tri_valor() -> None:
    texto = _json_ok(["musica", "danza"])
    resultado = parsear_respuesta(texto, ["musica", "danza"])
    assert [r["nombre"] for r in resultado] == ["musica", "danza"]
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR
    assert resultado[0]["categoria"] == "Otros"
    assert resultado[0]["razon"] == "razon de musica"
    assert resultado[0]["metodo"] == "llm"


def test_parsea_los_tres_veredictos() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "musica", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r1"},
                {"nombre": "danza", "veredicto": "EXCLUIR", "categoria": "", "razon": "r2"},
                {"nombre": "sonido y acustica", "veredicto": "DUDOSO", "categoria": "", "razon": "r3"},
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["musica", "danza", "sonido y acustica"])
    veredictos = [r["veredicto"] for r in resultado]
    assert veredictos == [VEREDICTO_INCLUIR, VEREDICTO_EXCLUIR, VEREDICTO_DUDOSO]


def test_parsea_lista_desnuda_sin_envoltorio() -> None:
    texto = json.dumps(
        [{"nombre": "musica", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}]
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_quita_cercas_de_codigo() -> None:
    texto = "```json\n" + _json_ok(["musica"]) + "\n```"
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_envelope_openai_con_razonamiento_de_cercas_internas() -> None:
    contenido = _json_ok(["musica"])
    opcion = {
        "index": 0,
        "message": {"role": "assistant", "content": contenido},
        "reasoning": "Paso 1:\n```js\nconst x = 1\n```\nPaso 2:\n```\nif (x) {}\n```",
    }
    texto = json.dumps({"choices": [opcion]})
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_texto_prefijado_antes_del_json() -> None:
    texto = "Claro, aqui tienes:\n" + _json_ok(["musica"])
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_json_malformado_marca_error_todos() -> None:
    resultado = parsear_respuesta("esto no es json {", ["musica", "danza"])
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_ERROR, VEREDICTO_ERROR]
    assert "JSON" in resultado[0]["razon"]


def test_nombre_ausente_en_respuesta_marca_error() -> None:
    texto = _json_ok(["musica"])
    resultado = parsear_respuesta(texto, ["musica", "piano"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR
    assert resultado[1]["veredicto"] == VEREDICTO_ERROR
    assert "piano" in resultado[1]["razon"]


def test_item_con_nombre_desconocido_se_ignora() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "otro programa", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR


def test_veredicto_desconocido_marca_error() -> None:
    texto = json.dumps(
        {"resultados": [{"nombre": "musica", "veredicto": "TAL_VEZ", "categoria": "Otros", "razon": "r"}]}
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR


def test_razon_faltante_usa_mensaje_generico() -> None:
    texto = json.dumps(
        {"resultados": [{"nombre": "musica", "veredicto": "INCLUIR", "categoria": "Otros"}]}
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR
    assert resultado[0]["razon"]


def test_normaliza_nombre_con_tildes_y_mayusculas() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "Música", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_preserva_orden_de_entrada() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "b", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"},
                {"nombre": "a", "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"},
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["a", "b"])
    assert [r["nombre"] for r in resultado] == ["a", "b"]


def test_sin_campo_resultados_marca_error() -> None:
    resultado = parsear_respuesta("{}", ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR


def test_categoria_invalida_en_incluir_marca_error() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "musica", "veredicto": "INCLUIR", "categoria": "Música sacra", "razon": "r"}
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR
    assert "fuera de las 9" in resultado[0]["razon"]


def test_incluir_sin_categoria_marca_error() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "musica", "veredicto": "INCLUIR", "categoria": "", "razon": "r"}
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR


def test_excluir_con_categoria_vacia_no_es_error() -> None:
    texto = json.dumps(
        {
            "resultados": [
                {"nombre": "danza", "veredicto": "EXCLUIR", "categoria": "", "razon": "no musical"}
            ]
        }
    )
    resultado = parsear_respuesta(texto, ["danza"])
    assert resultado[0]["veredicto"] == VEREDICTO_EXCLUIR
    assert resultado[0]["categoria"] == ""


def test_parsea_envelope_openai() -> None:
    texto = _envelope_openai(_json_ok(["musica", "danza"]))
    resultado = parsear_respuesta(texto, ["musica", "danza"])
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_INCLUIR, VEREDICTO_INCLUIR]
    assert resultado[0]["nombre"] == "musica"


def test_texto_con_dos_json_usa_el_primero() -> None:
    texto = (
        'Prefacio. {"resultados": [{"nombre": "musica", "veredicto": "INCLUIR", '
        '"categoria": "Otros", "razon": "r"}]} Y luego otro {"a": 1}.'
    )
    resultado = parsear_respuesta(texto, ["musica"])
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


# ---------------------------------------------------------------------------
# partir_en_lotes
# ---------------------------------------------------------------------------


def test_lotes_divide_en_25() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    lotes = partir_en_lotes(nombres)
    assert [len(lote) for lote in lotes] == [25, 1]


def test_lotes_25_queda_en_un_solo_lote() -> None:
    nombres = [f"programa {i}" for i in range(25)]
    assert len(partir_en_lotes(nombres)) == 1


def test_lotes_vacio_devuelve_vacio() -> None:
    assert partir_en_lotes([]) == []


def test_lotes_respeta_tamano_personalizado() -> None:
    nombres = [f"programa {i}" for i in range(7)]
    lotes = partir_en_lotes(nombres, tamano=3)
    assert [len(lote) for lote in lotes] == [3, 3, 1]


def test_lotes_0_devuelve_vacio() -> None:
    assert partir_en_lotes(["a"], tamano=0) == []


def test_lotes_preserva_contenido() -> None:
    nombres = [f"programa {i}" for i in range(50)]
    resultado = [n for lote in partir_en_lotes(nombres) for n in lote]
    assert resultado == nombres


# ---------------------------------------------------------------------------
# consultar_nombres_cloud (modo Blablador)
# ---------------------------------------------------------------------------


def test_cuerpo_cloud_omite_formato_json() -> None:
    payload = json.loads(_cuerpo_consulta_cloud("alias-large", ["musica"]).decode("utf-8"))
    assert payload["model"] == "alias-large"
    assert "format" not in payload
    assert payload["messages"][0]["role"] == "system"
    assert "musica" in payload["messages"][1]["content"]


def test_consulta_cloud_envia_a_blablador_con_modelo_y_autorizacion() -> None:
    transporte = _TransporteFake()
    transporte.respuesta = _envelope_openai(_json_ok(["musica"]))
    resultado = consultar_nombres_cloud(["musica"], api_key="clave-secreta", transporte=transporte)
    assert len(transporte.llamadas) == 1
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR
    url = transporte.llamadas[0][0]
    assert url == "https://api.blablador.fz-juelich.de/v1/chat/completions"


def test_consulta_cloud_usa_pausa_entre_lotes() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    transporte = _transporte_exitoso([nombres[:25], nombres[25:]])
    consultar_nombres_cloud(
        nombres,
        api_key="clave-secreta",
        transporte=transporte,
        pausa_entre_lotes=0.001,
    )
    assert len(transporte.llamadas) == 2


def test_consulta_cloud_reporta_progreso() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    transporte = _transporte_exitoso([nombres[:25], nombres[25:]])
    avances: list[tuple[int, int]] = []
    consultar_nombres_cloud(
        nombres,
        api_key="clave-secreta",
        transporte=transporte,
        pausa_entre_lotes=0.001,
        on_progreso=lambda hecho, total: avances.append((hecho, total)),
    )
    assert avances == [(1, 2), (2, 2)]


def test_consulta_cloud_respuesta_openai_parsea() -> None:
    transporte = _TransporteFake()
    transporte.respuesta = _envelope_openai(_json_ok(["danza"]))
    resultado = consultar_nombres_cloud(["danza"], api_key="clave-secreta", transporte=transporte)
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR


def test_consulta_cloud_reintenta_fallo_transitorio_de_lote() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    fallas = {"programa 0": 2}

    def transporte_flaky(url: str, cuerpo: bytes, timeout: float) -> str:
        contenido = json.loads(cuerpo.decode("utf-8"))["messages"][1]["content"]
        if "programa 0" in contenido and fallas["programa 0"] > 0:
            fallas["programa 0"] -= 1
            raise TimeoutError("Remote end closed connection without response")
        return _envelope_openai(
            json.dumps(
                {
                    "resultados": [
                        {"nombre": n, "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}
                        for n in nombres
                    ]
                }
            )
        )

    resultado = consultar_nombres_cloud(
        nombres,
        api_key="clave-secreta",
        transporte=transporte_flaky,
        pausa_entre_lotes=0.001,
        reintentos=3,
        retroceso_inicial=0.001,
    )
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_INCLUIR] * 26


def test_consulta_cloud_agota_reintentos_y_marca_error() -> None:
    transporte = _TransporteFake()
    transporte.error = TimeoutError("Remote end closed connection without response")
    resultado = consultar_nombres_cloud(
        ["musica"],
        api_key="clave-secreta",
        transporte=transporte,
        reintentos=2,
        retroceso_inicial=0.001,
    )
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR
    assert "servidor" in resultado[0]["razon"]


def test_consulta_cloud_reintentos_cero_no_repite() -> None:
    transporte = _TransporteFake()
    transporte.error = TimeoutError("Remote end closed connection without response")
    resultado = consultar_nombres_cloud(
        ["musica"],
        api_key="clave-secreta",
        transporte=transporte,
        reintentos=0,
        retroceso_inicial=0.001,
    )
    assert len(transporte.llamadas) == 1
    assert resultado[0]["veredicto"] == VEREDICTO_ERROR


# ---------------------------------------------------------------------------
# leer_clave_api
# ---------------------------------------------------------------------------


def test_leer_clave_api_lee_variable_de_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIES_BLABLADOR_API_KEY", "clave-env")
    assert leer_clave_api() == "clave-env"


def test_leer_clave_api_lee_env_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIES_BLABLADOR_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("SIES_BLABLADOR_API_KEY=clave-archivo\n", encoding="utf-8")
    assert leer_clave_api(env) == "clave-archivo"


def test_leer_clave_api_ausente_lanza_error(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIES_BLABLADOR_API_KEY", raising=False)
    env = tmp_path / "no-existe.env"
    with pytest.raises(RuntimeError):
        leer_clave_api(env)


# ---------------------------------------------------------------------------
# consultar_nombres (transporte inyectable)
# ---------------------------------------------------------------------------


class _TransporteFake:
    """Transporte de prueba: graba llamadas y responde por config."""

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, bytes, float]] = []
        self.respuesta: str | None = None
        self.error: Exception | None = None

    def __call__(self, url: str, cuerpo: bytes, timeout: float) -> str:
        self.llamadas.append((url, cuerpo, timeout))
        if self.error is not None:
            raise self.error
        if self.respuesta is None:
            raise AssertionError("Transporte sin respuesta configurada")
        return self.respuesta


def _transporte_exitoso(
    nombres_por_lote: list[list[str]],
) -> _TransporteFake:
    cuerpo = json.dumps(
        {
            "resultados": [
                {"nombre": n, "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}
                for lote in nombres_por_lote
                for n in lote
            ]
        }
    )
    transporte = _TransporteFake()
    transporte.respuesta = _envelope_respuesta(cuerpo)
    return transporte


def test_consulta_nombres_usa_api_y_modelo() -> None:
    transporte = _transporte_exitoso([["musica"]])
    resultado = consultar_nombres(["musica"], transporte=transporte)
    assert len(transporte.llamadas) == 1
    url, cuerpo, _ = transporte.llamadas[0]
    assert url == "http://localhost:11434/api/chat"
    payload = json.loads(cuerpo.decode("utf-8"))
    assert payload["model"] == "gpt-oss:20b"
    assert payload["format"] == "json"
    assert "musica" in payload["messages"][1]["content"]
    assert resultado[0]["veredicto"] == VEREDICTO_INCLUIR
    assert resultado[0]["metodo"] == "llm"


def test_consulta_nombres_envia_lotes_de_25() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    transporte = _transporte_exitoso([nombres[:25], nombres[25:]])
    consultar_nombres(nombres, transporte=transporte)
    assert len(transporte.llamadas) == 2
    primer_cuerpo = json.loads(transporte.llamadas[0][1].decode("utf-8"))
    segundo_cuerpo = json.loads(transporte.llamadas[1][1].decode("utf-8"))
    assert primer_cuerpo["messages"][1]["content"].count('"programa ') == 25
    assert segundo_cuerpo["messages"][1]["content"].count('"programa ') == 1


def test_servidor_caido_marca_error_sin_abortar() -> None:
    transporte = _TransporteFake()
    transporte.error = ConnectionError("servidor apagado")
    resultado = consultar_nombres(["musica", "danza"], transporte=transporte)
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_ERROR, VEREDICTO_ERROR]
    assert "servidor" in resultado[0]["razon"]


def test_falla_de_un_lote_no_aborta_el_siguiente() -> None:
    nombres = [f"programa {i}" for i in range(26)]

    def transporte_mixto(url: str, cuerpo: bytes, timeout: float) -> str:
        contenido = json.loads(cuerpo.decode("utf-8"))["messages"][1]["content"]
        if "programa 0" in contenido:
            raise TimeoutError("timeout en el primer lote")
        return _envelope_respuesta(
            json.dumps(
                {
                    "resultados": [
                        {"nombre": n, "veredicto": "INCLUIR", "categoria": "Otros", "razon": "r"}
                        for n in nombres[25:]
                    ]
                }
            )
        )

    resultado = consultar_nombres(nombres, transporte=transporte_mixto)
    assert [r["veredicto"] for r in resultado[:25]] == [VEREDICTO_ERROR] * 25
    assert [r["veredicto"] for r in resultado[25:]] == [VEREDICTO_INCLUIR] * 1


def test_respuesta_malformada_no_aborta_lote() -> None:
    transporte = _TransporteFake()
    transporte.respuesta = _envelope_respuesta("no es json")
    resultado = consultar_nombres(["musica", "danza"], transporte=transporte)
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_ERROR, VEREDICTO_ERROR]


def test_on_progreso_reporta_avance_por_lote() -> None:
    nombres = [f"programa {i}" for i in range(26)]
    transporte = _transporte_exitoso([nombres[:25], nombres[25:]])
    avances: list[tuple[int, int]] = []
    consultar_nombres(
        nombres,
        transporte=transporte,
        on_progreso=lambda hecho, total: avances.append((hecho, total)),
    )
    assert avances == [(1, 2), (2, 2)]


def test_modelo_y_puerto_configurables() -> None:
    transporte = _transporte_exitoso([["musica"]])
    consultar_nombres(
        ["musica"],
        transporte=transporte,
        modelo="otro-modelo",
        host="10.0.0.5",
        puerto=9999,
    )
    url, cuerpo, _ = transporte.llamadas[0]
    assert url == "http://10.0.0.5:9999/api/chat"
    assert json.loads(cuerpo.decode("utf-8"))["model"] == "otro-modelo"


def test_normaliza_nombres_de_entrada() -> None:
    transporte = _transporte_exitoso([["composicion musical"]])
    resultado = consultar_nombres(["Composición Musical"], transporte=transporte)
    assert transporte.llamadas[0][1].decode("utf-8").count("composicion musical") >= 1
    assert resultado[0]["nombre"] == "composicion musical"


def test_nombre_vacio_tras_normalizar_marca_error() -> None:
    transporte = _transporte_exitoso([["musica"]])
    resultado = consultar_nombres(["musica", "  "], transporte=transporte)
    assert len(transporte.llamadas) == 1
    assert len(resultado) == 2
    assert [r["veredicto"] for r in resultado] == [VEREDICTO_INCLUIR, VEREDICTO_ERROR]
    assert resultado[1]["razon"]
