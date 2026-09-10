# Etapa 05 — Verificación de falsos negativos

## Qué se hizo

Se montó una **pasada de control de falsos negativos**: buscar programas que el motor excluyó pero que podrían ser musicales. Para no revisar los 16.684 nombres completos, se definió una **red de candidatos** acotada:

- **La red**: todos los nombres que viven en un **área genérica musical** (*"Música, Canto o Danza"* o *"Pedagogía en Artes y Música"*) pero cuyo nombre **no contiene ninguna señal léxica de música** (ni la palabra música, ni canto, ni instrumentos, ni otras pistas del filtro léxico). De esos se **deduplicaron los ya incluidos** y también los que ya vivían en la **zona gris** de la etapa 02 (los nombres ya `DUDOSO` no se re-consultan, en coherencia con la decisión de no iterar). Quedaron **34 nombres** como red de candidatos.
- **El control**: una **muestra aleatoria de 50 excluidos** (con semilla fija, reproducible), para que el modelo confirmara que la exclusión masiva de la etapa 02 no oculta falsos negativos en el resto del conjunto.

Ambos conjuntos se consultaron al modelo local **gpt-oss:20b** con el cliente de la etapa 04 (lotes de 25, una sola pasada). Cada veredicto del LLM se registró en la clasificación **con método `llm`** y su razón, y los `INCLUIR` del modelo se incorporaron a la clasificación.

En total se consultaron **84 nombres** (34 de la red + 50 de control), todos por primera y única vez.

### Replicación con un modelo en la nube

Como control adicional, la misma consulta se repitió con el modelo **alias-fast (Ministral-3-14B)** del servicio Blablador (Jülich Supercomputing Centre), usando el mismo cliente con transporte Bearer y reintentos con retroceso ante fallos de conexión transitorios (`scripts/04_verificacion_falsos_negativos.py --cloud`). El modelo de la nube confirmó el hallazgo del modelo local: **ningún `INCLUIR`** entre los 84 nombres (`EXCLUIR: 84`, `ERROR: 0`). Resultados en `prod/verificacion_falsos_negativos_cloud.csv`, clasificación en `prod/clasificacion_tras_falsos_negativos_cloud.csv` y log en `logs/04-verificacion-falsos-negativos-cloud.md`.

## Qué se descubrió

- **Cero falsos negativos incorporables**: de los 84 nombres consultados, el LLM no marcó **ninguno** como `INCLUIR`. La red de 34 candidatos y la muestra de control de 50 excluidos fueron confirmadas como exclusiones correctas (`EXCLUIR: 81`).
- **Control de confianza**: 49 de los 50 excluidos de la muestra fueron confirmados `EXCLUIR` por el modelo. El único no confirmado fue un error de servidor (un nombre ausente en la respuesta), no un desacuerdo.
- **Una zona gris nueva**: el modelo respondió `DUDOSO` a un solo nombre de la red, *pedagogía y licenciatura en artes*. Los nombres de educación artística que ya eran `DUDOSO` en la etapa 02 (por ejemplo *pedagogía en educación artística*) **no se re-consultaron**: se respetó la frontera de la zona gris y la decisión de no iterar sobre ella.
- **El veredicto final de la clasificación no cambió en volumen**: se mantienen 217 incluidos, 16.456 excluidos y 11 dudosos (10 previos + la nueva zona gris), pero ahora **82 veredictos llevan el método `llm`** documentado (los 84 consultados menos 2 errores de servidor).

## Por qué importa para el resto del estudio

1. **Cierra el frente de falsos negativos**: el motor no dejó fuera ningún programa musical entre los que viven en áreas musicales ni en la muestra de control. La medida tiene el peso que da el muestreo aleatorio reproducible, documentado en el log.
2. **El hallazgo es auditable**: cada uno de los 84 nombres tiene su veredicto del LLM con razón en `prod/verificacion_falsos_negativos.csv`.
3. **La zona gris crece con criterio**: el nuevo `DUDOSO` (con área musical) pasa a la revisión humana en lugar de decidirse en silencio, y los que ya estaban en zona gris no se vuelven a consultar.
4. **La restricción de recursos se respeta**: se consultaron 84 nombres, no miles; la verificación no re-corre la clasificación completa.
5. **La conclusión no depende de un solo modelo**: el modelo local y el de la nube coinciden en cero falsos negativos, lo que refuerza la confianza del frente. (El modelo de la nube fue en esta corrida más severo: confirmó los 84 como `EXCLUIR`, sin `DUDOSO`.)

## Registro

La lógica de selección y aplicación vive en `sies_musica/verificacion.py` y se prueba en `tests/test_verificacion.py` (red de candidatos, muestra de control reproducible y aplicación de veredictos sin red, con datos sintéticos). La corrida real está en `scripts/04_verificacion_falsos_negativos.py` (sin `--cloud` usa el modelo local gpt-oss:20b; con `--cloud` usa Blablador). Resultados locales en `prod/verificacion_falsos_negativos.csv` y clasificación en `prod/clasificacion_tras_falsos_negativos.csv`; la réplica en la nube añade el sufijo `_cloud`. Log en `logs/04-verificacion-falsos-negativos.md`.