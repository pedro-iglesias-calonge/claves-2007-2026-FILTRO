# Etapa 06 — Cazar falsos positivos: ¿metimos música de sobra?

_Enfoque humanista: el motor puede pecar por exceso. Un programa cuya inclusión descansa en una señal débil (una palabra ancha como "canto" o "sonido", un contexto de gestión cultural) merece una segunda mirada. Esta etapa pone a prueba las inclusiones fronterizas: los que entraron, verificar que de verdad pertenecen._

## Qué se hizo

Se montó una **pasada de control de falsos positivos**: revisar los **incluidos fronterizos**, es decir, los programas que el motor incluyó **sin que su nombre contenga la palabra clave núcleo *"música"* o *"musical"***. Son inclusiones que descansan en señales secundarias (canto, coro, sonido, instrumentos, gestión cultural) y por eso son las más expuestas a un falso positivo.

De los 217 incluidos de la etapa 02, **67 eran fronterizos**. Se consultaron al modelo local **gpt-oss:20b** con el cliente de la etapa 04 (lotes de 25, una sola pasada):

- Los `EXCLUIR` del LLM **se retiraron de la inclusión** (veredicto `EXCLUIR`, método `llm`, con la razón del modelo).
- Los `DUDOSO` del LLM **se marcaron para zonas grises** con método `llm`, **sin re-consultarlos**: quedan esperando la decisión humana de la etapa siguiente, que no vuelve a preguntar al modelo.
- Todo veredicto del LLM se registró con **método `llm`** y su razón.

## Qué se descubrió

- **Ningún falso positivo retirado en esta corrida**: el LLM no marcó `EXCLUIR` a ninguno de los 67 fronterizos. Las dudas del modelo se canalizaron todas a la zona gris: cuando la evidencia era insuficiente, prefirió `DUDOSO` antes que descartar. (El cliente admite los tres valores; en corridas anteriores con otros nombres el `EXCLUIR` sí apareció.)
- **Quince nuevos dudosos marcados para zonas grises**: el modelo respondió `DUDOSO` a 15 programas, en su mayoría de **gestión cultural** (diplomas y diplomados de postítulo en gestión cultural, gestión cultural aplicada, gestión cultural del patrimonio, magíster en patrimonio y gestión cultural, técnico/a en arte y gestión cultural) y también a los dos programas de **sonido** de la frontera (*sonido* y *tecnología en sonido e iluminación*). Quedan **marcados para zonas grises**, sin re-consultar, para que la revisión humana decida.
- **La mayoría se confirma**: 52 de los 67 fronterizos fueron confirmados `INCLUIR` por el modelo, con su categoría y razón.
- **Sin errores de servidor en esta corrida**: los 67 nombres recibieron veredicto; la clasificación previa se conserva intacta para todo el lote.
- **La clasificación quedó así tras la pasada**: de los 217 incluidos previos, 15 pasaron a dudosos; la clasificación final es **202 incluidos**, **16.456 excluidos** y **26 dudosos** (11 que venían de las etapas 02 y 04 + 15 nuevos de gestión cultural y sonido que se suman a la zona gris).

### Replicación con un modelo en la nube

La misma verificación se repitió con **alias-fast (Ministral-3-14B)** de Blablador (`scripts/05_verificacion_falsos_positivos.py --cloud`), leyendo la clasificación de la réplica en la nube de la etapa 05. El modelo de la nube fue más estricto que el local respecto de la **gestión cultural**: retiró de la inclusión (método `llm`) a **12** programas de gestión cultural (diplomas y diplomados de postítulo, técnico/a en arte y gestión cultural, magíster en patrimonio y gestión cultural) y marcó para zonas grises a **6** (gestión cultural, magíster en gestión cultural y aplicada, diplomado gestión cultural del patrimonio, y los dos programas de *sonido*: *sonido* y *sonido profesional*). Confirmó **47** de los 67 fronterizos como `INCLUIR`; **2** errores de categoría (el modelo respondió *Musicología e investigación* en lugar de *Teoría, musicología e investigación* para el magíster en artes mención musicología, así que el parser las conservó con su veredicto previo).

La clasificación de la réplica en la nube quedó en **199 incluidos**, **16.469 excluidos** y **16 dudosos**. Resultados en `prod/verificacion_falsos_positivos_cloud.csv`, clasificación en `prod/clasificacion_tras_falsos_positivos_cloud.csv` y log en `logs/05-verificacion-falsos-positivos-cloud.md`.

## Por qué importa para el resto del estudio

1. **La inclusión ya no es un monólogo de reglas**: las inclusiones más dudosas pasaron por un segundo lector, y las que el modelo descartó no se mantienen por inercia.
2. **La zona gris se enriquece antes de la revisión humana**: pasan a ella los programas que el colaborador externo duda en confirmar (gestión cultural y sonido), un conjunto coherente que el humano podrá revisar con contexto en la etapa siguiente.
3. **Los veredictos no fabrican decisiones**: ningún nombre fue retirado ni marcado sin el respaldo de una razón del LLM; todo veredicto está registrado con método `llm`.
4. **Ninguna retirada ni marcado se hace sin respaldo**: cada veredicto del LLM está en los CSV de veredictos (`prod/verificacion_falsos_positivos.csv` y `_cloud`) con su razón.
5. **El criterio depende del colaborador externo**: el modelo local prefirió no retirar nada y dudar en 15; el de la nube retiró 12 programas de gestión cultural y dudó en 6. La frontera de la gestión cultural es la más sensible y merece atención en la revisión humana; la decisión final es del humano, no de un solo modelo.

## Registro

La lógica de selección y aplicación vive en `sies_musica/verificacion.py` (selección de fronterizos y fusión de veredictos con método `llm`), y se prueba en `tests/test_verificacion.py` con datos sintéticos, sin red. La corrida real está en `scripts/05_verificacion_falsos_positivos.py` (sin `--cloud` usa el modelo local gpt-oss:20b; con `--cloud` usa Blablador). Resultados locales en `prod/verificacion_falsos_positivos.csv` y clasificación en `prod/clasificacion_tras_falsos_positivos.csv`; la réplica en la nube añade el sufijo `_cloud`. Log en `logs/05-verificacion-falsos-positivos.md`.