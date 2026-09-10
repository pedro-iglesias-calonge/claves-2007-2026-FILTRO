# Etapa 02 — Filtro léxico

## Qué se hizo

Se construyó un **motor de clasificación** que decide, para cada nombre de carrera, si pertenece al universo musical. La decisión se toma en dos planos: primero se analiza **el nombre** (filtro léxico, esta etapa) y luego se consulta **el contexto** que entrega la base sobre ese programa (filtro semántico, etapa siguiente).

En esta etapa el motor reconoce las palabras que anuncian música:

- **La palabra directa:** música, musical, músico.
- **Las disciplinas:** composición, compositor, arreglos, teoría musical, musicología, investigación musical.
- **La interpretación:** canto, cantante, coral, coro, coros, interpretación musical, intérprete, dirección orquestal/coral/de orquestas/de agrupaciones musicales.
- **Los instrumentos:** piano, violín, viola, violonchelo, contrabajo, guitarra, flauta, saxofón, trompeta, trombón, tuba, corno, fagot, oboe, clarinete, arpa, percusión, bajo eléctrico.
- **El sonido y la producción:** sonido, sonora, producción musical, grabación.
- **Los oficios cercanos:** musicoterapia, gestión cultural, luthería (construcción de instrumentos).

Y reconoce también las palabras que, por parecidas, engañan. Son **exclusiones fuertes**: palabras que nunca bastan para llamar a un programa musical:

- **Idiomas y señas:** interpretación/traducción de idiomas o de lengua de señas (la interpretación de idiomas no es una actividad musical).
- **Otras artes:** artes visuales, artes plásticas, pintura, escultura, danza, coreografía, teatro puro, artes escénicas.
- **Cine y audiovisual.**
- **Acústica técnica** (de edificios, ambiental, submarina, vibraciones) y **ultrasonido médico**: la palabra "acústica" o "sonido" aquí no indica una actividad musical.
- **Terapias no musicales** (arte-terapia, dramaterapia, psicoterapia, kinesiterapia, etc.): solo la musicoterapia y las terapias de arte con mención musicoterapia pertenecen al universo.
- **"Licenciatura en artes" sin mención**: un grado general de artes no es, por sí mismo, un programa musical; las menciones (música, composición, sonido) desambiguan.
- **Palabras tramposas:** "instrumental" en contextos quirúrgicos o industriales, "instrumentos" de evaluación o de vuelo, "batería" química, "jazz" como gimnasia, "orquestando" como metáfora de gestión.

El motor devuelve, para cada nombre, un veredicto (`INCLUIR`, `EXCLUIR` o `DUDOSO`), una categoría de las 9 del estudio, el método usado (léxico o semántico) y una razón en lenguaje claro.

## Qué se descubrió

Al aplicar el filtro léxico a los 16.684 nombres únicos de la base:

- **217 nombres quedaron dentro del universo musical** por señales léxicas. El grupo más numeroso es la **interpretación musical** (85 nombres: pianistas, violinistas, intérpretes en canto, dirección de orquestas y coros), seguido de la **pedagogía en música** (33), la **producción musical y sonido** (19) y la **gestión cultural** (19).
- **10 nombres cayeron en la zona gris automática** sin que el léxico pueda decidirlos: los 4 híbridos "sonido y acústica" y las 6 carreras de "educación artística" pura (sin mención de música). Estos no se deciden solos: pasan a revisión humana.
- La palabra "instrumental" es ambigua: **"instrumental quirúrgico", "instrumentista eléctrico de plantas mineras"** o la "evaluación instrumental de riesgos laborales" no son música. Solo el "intérprete instrumental" (quien toca un instrumento) pertenece al universo musical.

## Por qué importa para el resto del estudio

1. El filtro léxico captura el **conjunto base del universo** (los nombres que contienen una señal musical directa), que es la mayoría de los programas musicales.
2. Las **exclusiones fuertes** operan sin dudas y sin gasto de consultas externas: los falsos positivos típicos (idiomas, danza, teatro, cine, acústica técnica, terapias) quedan fuera de inmediato.
3. Los **casos grises** se aíslan de forma deliberada: no se emite un veredicto automático cuando el nombre no ofrece una señal suficiente.
4. Lo que el léxico no decide es justamente lo que debe resolver la **etapa siguiente**, con el contexto que aporta la base.

## Registro

El motor vive en `sies_musica/clasificador.py` y se pone a prueba con la tabla de casos en `tests/test_clasificador.py` (incluyentes, excluyentes y zona gris). La corrida completa sobre la base está en `scripts/02_clasificacion.py` y sus resultados quedan en `prod/clasificacion_parcial.csv` y `logs/02-clasificacion.md`.
