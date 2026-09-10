# Etapa 07 — Revisión humana de las zonas grises

## Qué se hizo

Se construyó el **mecanismo que conecta el pipeline con la decisión humana**: una etapa sin red y sin LLM que reúne los **puntos frontera** (los 26 `DUDOSO` de la clasificación de la etapa anterior) en `prod/zonas_grises.csv`. Cada punto lleva su **veredicto**, la **categoría** (vacía en la duda), el **método** que la generó, la **razón** (del LLM o de la regla léxica) y una **etiqueta de origen** que explica por qué cayó en la zona gris:

- **DUDOSO del LLM**: el modelo no lo resolvió en las pasadas de falsos negativos y positivos.
- **Híbrido "sonido y acústica"**: la acústica técnica convive con el sonido, y el filtro no lo resuelve automáticamente.
- **Educación artística pura**: programas de educación artística sin mención de música.
- **Ambiguo no clasificable**: cualquier otro punto que llegue a la zona gris sin que ninguna regla lo explique.

Sobre la misma lista se genera `prod/zonas_grises_revisadas.csv`, el **template de la revisión humana**: las mismas filas más dos columnas vacías, `decision_final` y `categoria_final`, para que el humano registre su decisión por punto — *incluir* (con su categoría) o *excluir*. El formato es legible por máquina: la etapa de ensamblado podrá leer, para cada `nombre_normalizado`, su decisión y su categoría.

Dos garantías de la etapa: **la decisión humana no itera sobre el LLM** (no se re-consulta nada; el archivo de zonas grises es un registro estático de la duda, no una nueva consulta al modelo) y **el template no se sobreescribe** si ya existe: la revisión humana puede llevarse a cabo en varias sesiones sin riesgo de perder decisiones en curso.

Para sostener esa revisión se construyó también una **aplicación HTML de un solo archivo** (`prod/revisar_zonas_grises.html`): presenta los mismos 26 puntos como tarjetas —su nombre normalizado y sus instituciones— con botones para **incluir** o **excluir** y un selector de las 9 categorías al incluir. El avance se guarda solo en el navegador, y el botón *Descargar CSV* entrega `prod/zonas_grises_revisadas.csv` en el mismo formato del template (9 columnas, utf-8 sin BOM), listo para que la etapa de ensamblado lo lea. La aplicación se regenera sin perder las decisiones ya anotadas en el archivo de revisión.

## Qué se descubrió

- **Veintiséis puntos esperan la decisión humana**, y vienen de tres orígenes bien marcados: **16 `DUDOSO` del LLM**, **6 de educación artística pura** y **4 híbridos "sonido y acústica"**. No hubo ambiguos sin explicación: todas las dudas de la corrida tienen una razón registrada.
- **La duda del LLM se concentra en gestión cultural y sonido**: diplomados y diplomas de postítulo en gestión cultural, técnico/a en arte y gestión cultural, magíster en patrimonio y gestión cultural, los programas de *sonido* y *tecnología en sonido e iluminación*, y la frontera *pedagogía y licenciatura en artes*. Es la misma zona que el modelo de la nube resolvió de manera más severa en la etapa anterior: esto confirma que la frontera de la gestión cultural es la más sensible del estudio.
- **La educación artística pura**: seis programas de educación artística (pedagogía, magíster, postítulo y un nombre extenso con mención donde aparece "educación artística") que no mencionan ninguna palabra musical. La regla no los excluyó de plano ni los incluyó: los dejó para que la revisión humana decida si la influencia artística es suficiente.
- **Los híbridos de sonido y acústica**: cuatro programas de ingeniería y técnicos de sonido y acústica, donde la acústica técnica podría tirar del programa fuera de lo musical. El filtro los resguardó para la decisión humana.
- **Cada punto conserva su nombre original**: además del nombre normalizado (la unidad de decisión), el archivo incluye el nombre real con el que aparece el programa en la matrícula, para que la revisión humana trabaje con el nombre tal como figura en la fuente.

## Por qué importa para el resto del estudio

1. **La frontera se resuelve de forma deliberada**: los casos que el motor y el modelo no pudieron resolver pasan a decisión humana y no se resuelven por defecto.
2. **La decisión humana es definitiva y única**: el template establece que la respuesta es por punto y no vuelve a preguntar al LLM; cada decisión queda registrada en el archivo de revisión.
3. **El formato está pensado para el ensamblado**: `zonas_grises_revisadas.csv` es legible por máquina (una fila por punto, `decision_final` y `categoria_final`), de modo que la etapa siguiente podrá incorporar cada decisión al producto final con su categoría o descartar el punto.
4. **La revisión puede hacerse en varias sesiones**: el archivo de revisión no se sobreescribe; la decisión humana puede editarse en varias pasadas sin riesgo.
5. **Los tres orígenes de la duda quedan documentados**: la metodología permite entender por qué estos veintiséis programas están en la frontera, sin necesidad de inferir el criterio.

## Registro

La lógica vive en `sies_musica/zonas_grises.py` (selección de las zonas grises, etiqueta de origen y escritura de ambos formatos), y se prueba en `tests/test_zonas_grises.py` con datos sintéticos, sin red. La corrida está en `scripts/06_generar_zonas_grises.py`. La aplicación de revisión se genera con `scripts/07_generar_app_revision.py` (lee el template y la matrícula para mostrar las instituciones de cada nombre) y queda en `prod/revisar_zonas_grises.html`. Resultados en `prod/zonas_grises.csv` y template de revisión en `prod/zonas_grises_revisadas.csv`. Log en `logs/06-zonas-grises.md`.