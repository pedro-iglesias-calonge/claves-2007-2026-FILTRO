# Etapa 04 — Cliente del modelo de lenguaje

## Qué se hizo

Se construyó un **cliente reutilizable** (`sies_musica/cliente_llm.py`) que consulta al modelo local **gpt-oss:20b** servido por Ollama en `localhost:11434`. El cliente es una interfaz de consulta, no una decisión: recibe una lista de nombres de programa y devuelve, para cada uno, un veredicto (`INCLUIR`, `EXCLUIR` o `DUDOSO`), una categoría de las 9 del estudio y una razón breve.

El cliente funciona así:

- **Por lotes de 25.** Los nombres se consultan en grupos de a lo más 25, en **una sola pasada**: cada nombre se pregunta una única vez, sin iteraciones. Esto responde a la restricción de recursos de cómputo del estudio.
- **Con formato JSON.** Se le pide al modelo responder en JSON estructurado: un objeto por nombre con su veredicto, categoría y razón. El cliente valida la respuesta: descarta cercas de código, tolera texto antes del JSON, acepta el sobre de respuesta de Ollama y normaliza tildes y mayúsculas para casar los nombres devueltos con los consultados.
- **Sin romper el lote.** Si el servidor no está disponible, tarda demasiado o devuelve una respuesta malformada, **el lote no se abandona**: los nombres afectados quedan marcados como `ERROR` con la razón del fallo y el proceso continúa con el siguiente lote. El resto de los nombres recibe su veredicto.
- **Sin ver la base completa.** El cliente recibe solo el conjunto que el pipeline le pase (la frontera de candidatos o las muestras de control). Los 16.684 nombres completos nunca se envían al modelo.

## Qué se descubrió

Al probar el cliente contra el modelo real (prueba de humo con 50 nombres: los 10 candidatos dudosos de la etapa anterior más una muestra aleatoria de 40 excluidos):

- El modelo **respondió con veredictos para 49 de 50 nombres** en dos lotes de 25, con categoría y razón en cada caso.
- El caso restante reveló el valor del manejo de fallos: el modelo **omitió un nombre** en su respuesta. El cliente no lo inventó ni abortó: lo marcó como `ERROR` con la razón *"nombre ausente en la respuesta del LLM"*, para que la etapa siguiente decida.
- La muestra de excluidos fue confirmada como tal por el modelo (sin falsos positivos evidentes en la muestra), y los dudosos de la etapa anterior fueron reevaluados por el modelo.

## Por qué importa para el resto del estudio

1. Es la **herramienta de las dos etapas siguientes**: la verificación de falsos negativos y la de falsos positivos consultarán este mismo cliente.
2. El **manejo de fallos** es condición de confianza: un servidor que cae a mitad de la consulta no puede dejar el estudio a medias. El registro queda en el log de la etapa.
3. La **limitación de la frontera** protege el recurso de cómputo y mantiene la metodología reproducible: la consulta se hace sobre conjuntos definidos, nunca sobre los 16.684 nombres.
4. El **veredicto humano final** no se ve alterado: los `ERROR` y los `DUDOSO` se aíslan para la revisión de las etapas siguientes.

## Registro

El cliente vive en `sies_musica/cliente_llm.py` y se prueba en `tests/test_cliente_llm.py` (parseo de la respuesta, división en lotes y manejo de fallos con un transporte simulado, sin red). La prueba de humo contra el modelo real está en `scripts/03_cliente_llm.py`, con sus resultados en `prod/verificacion_llm_demo.csv` y el log de la corrida en `logs/03-cliente-llm.md`.
