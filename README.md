# CLAVES 2007-2026: Consulta Longitudinal Abierta para la Visualización de la Educación Superior Musical en Chile

**Filtrado reproducible de programas de música en la Base de Datos de Matrícula del SIES (2007-2026)**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/Código-MIT-yellow.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Datos%20y%20documentos-CC%20BY%204.0-lightgrey.svg)](LICENSE-CC-BY-4.0.md)
[![Estado](https://img.shields.io/badge/estado-publicación%20académica-informational)](#)

---

## Resumen

Este repositorio documenta, de forma **auditable y reproducible**, el procedimiento mediante el cual se identificaron, extrajeron y documentaron los **programas de educación superior vinculados con la música en Chile** durante el período **2007-2026**, a partir de la Base de Datos de Matrícula del Servicio de Información de Educación Superior (SIES).

A partir de una base original de **280.160 registros** (58 columnas, 20 años), el procedimiento aisló **2.664 filas** correspondientes a **215 programas musicales** (≈ 0,95 % de la matrícula original), conservando la estructura y el formato exactos de la fuente. El método combina tres actores en turnos sucesivos —**la regla** (léxico y contexto), **el modelo** (un LLM como apoyo en los bordes) y **el humano** (decisión final en las zonas grises)—, registrando para cada programa su **veredicto, categoría, método y razón**.

> **Enfoque humanista.** La documentación metodológica (`metodologia/`) está escrita para lectores de pedagogía y música, no solo para programadores. El código es el respaldo técnico de ese relato, no su sustituto.

**Palabras clave:** educación superior musical · SIES · Chile · matrícula · clasificación léxica y semántica · modelo de lenguaje · revisión humana · ciencia abierta · datos abiertos.

---

## Tabla de contenidos

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Datos de origen](#2-datos-de-origen)
3. [Metodología](#3-metodología)
4. [Resultados](#4-resultados)
5. [Estructura del repositorio](#5-estructura-del-repositorio)
6. [Reproducibilidad](#6-reproducibilidad)
7. [Ética y uso de inteligencia artificial](#7-ética-y-uso-de-inteligencia-artificial)
8. [Limitaciones](#8-limitaciones)
9. [Cómo citar](#9-cómo-citar)
10. [Licencia](#10-licencia)
11. [Autoría y contacto](#11-autoría-y-contacto)

---

## 1. Contexto y motivación

La Base de Datos de Matrícula del SIES registra, año a año, la matrícula de la educación superior chilena. Aislar de ella los **programas musicales** plantea tres dificultades:

1. **El nombre no siempre dice "música".** Hay programas cuya identidad musical depende del contexto institucional o de un nombre de instrumento aislado.
2. **Existen trampas léxicas.** "Interpretación" (de idiomas), "acústica" (técnica o ambiental), "ultrasonido" (medicina), "audiovisual" o "licenciatura en artes" pueden confundirse con lo musical.
3. **Hay zonas grises genuinas.** Educación artística sin mención, híbridos "sonido y acústica", gestión cultural y teatro musical exigen juicio caso a caso.

El objetivo del estudio fue construir un conjunto de datos histórico, **auditable y reproducible**, con precisión alta y con la **trazabilidad completa** de cada decisión. Cuando existió duda razonable, el procedimiento **priorizó la inclusión** y derivó el caso a revisión humana.

---

## 2. Datos de origen

| Atributo | Valor |
|---|---|
| Fuente | Base de Datos de Matrícula en Educación Superior, **SIES / MINEDUC (Chile)** |
| Archivo | `Matricula_2007_2026_WEB_10_07_2026.csv` |
| Período | 2007-2026 (20 años) |
| Registros | 280.160 filas |
| Columnas | 58 |
| Separador | `;` |
| Encoding | `cp1252` (con 5 bytes no decodificables, aislados) |
| Glosario | `datos SIES/glosario_bases_matricula_2026.md` |

> **La base fuente no se distribuye en este repositorio** por su tamaño (≈ 149 MB, sobre el límite de 100 MB de GitHub) y porque es un recurso público descargable. Para reproducir el procedimiento, descargue la base desde el portal de datos abiertos del SIES/MINEDUC y deposítela en `datos SIES/` con el nombre exacto indicado arriba. Los detalles y la procedencia se documentan en [`datos SIES/README.md`](datos%20SIES/README.md).

---

## 3. Metodología

El procedimiento se organiza en **ocho etapas**, cada una con su documento narrativo en `metodologia/`, su script en `scripts/` y su registro de corrida en `logs/`. La síntesis completa está en [`metodologia/00-sintesis.md`](metodologia/00-sintesis.md) y la revisión metodológica formal en [`revision_metodologia.md`](revision_metodologia.md).

| # | Etapa | Qué hace | Documento | Script | Log |
|---|-------|----------|-----------|--------|-----|
| 1 | Integridad de los datos | Verifica filas, columnas, años, unicidad y encoding | `metodologia/01-verificacion-datos.md` | `scripts/01_integridad.py` | `logs/01-integridad.md` |
| 2 | Filtro léxico | Reglas explícitas de inclusión (69 conceptos) y exclusión (47) | `metodologia/02-filtro-lexico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 3 | Filtro semántico | Rescata por contexto (área genérica y CINE-F) lo que el nombre no dice | `metodologia/03-filtro-semantico.md` | `scripts/02_clasificacion.py` | `logs/02-clasificacion.md` |
| 4 | Cliente del modelo | Puente probado con el LLM (local y nube) | `metodologia/04-cliente-llm.md` | `scripts/03_cliente_llm.py` | `logs/03-cliente-llm.md` |
| 5 | Falsos negativos | Red de candidatos + muestra de control al LLM (84 nombres) | `metodologia/05-verificacion-falsos-negativos.md` | `scripts/04_verificacion_falsos_negativos.py` | `logs/04-*.md` |
| 6 | Falsos positivos | Incluidos fronterizos al LLM (67 nombres) | `metodologia/06-verificacion-falsos-positivos.md` | `scripts/05_verificacion_falsos_positivos.py` | `logs/05-*.md` |
| 7 | Revisión humana | Decisión soberana sobre 26 puntos frontera | `metodologia/07-revision-humana.md` | `scripts/06_*.py`, `scripts/07_*.py` | `logs/06-*.md`, `logs/07-*.md` |
| 8 | Ensamblado final | Clasificación total + matrícula musical filtrada | `metodologia/08-ensamblado-final.md` | `scripts/08_ensamblado_final.py` | `logs/08-ensamblado-final.md` |

### 3.1 Los tres turnos de decisión

- **La regla.** Un léxico y un conjunto de reglas de contexto que la máquina aplica siempre igual. Decide la mayoría y deja los bordes a la vista.
- **El modelo.** Un LLM (Ministral-3-14B vía Blablador, con una corrida exploratoria en local) que opina en lenguaje natural sobre los casos frontera, con veredicto tri-valor `INCLUIR / EXCLUIR / DUDOSO`, categoría y razón.
- **El humano.** Resuelve en última instancia los casos que ni la regla ni el modelo se atrevieron a decidir, mediante una aplicación HTML autocontenida. Su decisión es final.

### 3.2 Categorías del dominio

El clasificador asigna cada programa incluido a una de **nueve categorías**:

Pedagogía en música · Composición y arreglos · Interpretación musical · Teoría, musicología e investigación · Formación musical general · Producción musical y sonido · Musicoterapia · Gestión cultural · Otros.

El glosario de dominio y las reglas acordadas están en [`CONTEXT.md`](CONTEXT.md).

---

## 4. Resultados

### 4.1 Embudo del filtrado

| Etapa | Registros / programas |
|---|---|
| Base original | 280.160 filas · 58 columnas · 20 años |
| Programas únicos (nombre normalizado) | 16.684 |
| **Programas incluidos (final)** | **215** |
| Filas de matrícula conservadas | **2.664** (≈ 0,95 % del total) |
| Instituciones representadas | 49 |
| Combinaciones institución-programa | 284 |

### 4.2 Distribución final por veredicto

| Veredicto | Programas |
|---|---|
| INCLUIR | 215 |
| EXCLUIR | 16.469 |
| **Total** | **16.684** |

### 4.3 Método que resolvió cada inclusión

| Método | Programas incluidos |
|---|---|
| `lexico` (regla explícita) | 150 |
| `llm` (verificación asistida) | 52 |
| `humano` (revisión de zonas grises) | 13 |
| **Total** | **215** |

### 4.4 Programas incluidos por categoría

| Categoría | Programas |
|---|---|
| Interpretación musical | 80 |
| Pedagogía en música | 42 |
| Producción musical y sonido | 24 |
| Composición y arreglos | 17 |
| Otros | 15 |
| Formación musical general | 13 |
| Gestión cultural | 9 |
| Teoría, musicología e investigación | 8 |
| Musicoterapia | 7 |

### 4.5 Productos finales

- `prod/Musica_2007_2026_filtrado.csv` — **producto principal**: la matrícula musical 2007-2026 con las **mismas 58 columnas** y encoding `cp1252` de la fuente.
- `prod/clasificacion_total.csv` — veredicto, categoría, método y razón por programa.
- `prod/zonas_grises.csv` y `prod/zonas_grises_revisadas.csv` — los 26 puntos frontera y sus decisiones humanas.
- `prod/revisar_zonas_grises.html` — aplicación de revisión humana (autocontenida).

---

## 5. Estructura del repositorio

```
.
├── README.md                     # Este documento
├── LICENSE                       # MIT (código)
├── LICENSE-CC-BY-4.0.md          # CC BY 4.0 (datos y documentos)
├── CITATION.cff                  # Metadatos de citación
├── CONTRIBUTING.md               # Guía de contribución
├── CHANGELOG.md                  # Historial de versiones
├── CONTEXT.md                    # Glosario y reglas de dominio
├── revision_metodologia.md       # Revisión metodológica formal
├── pyproject.toml                # Configuración del proyecto y de pruebas
├── requirements.txt              # Dependencias de Python
├── .env.example                  # Variables de entorno (sin secretos)
├── datos SIES/
│   ├── README.md                 # Procedencia y descarga de la base fuente
│   └── glosario_bases_matricula_2026.md
├── metodologia/                  # Relato paso a paso (00-08) para el artículo
├── logs/                         # Registro duro de cada corrida
├── prod/                         # Productos finales e intermedios
├── scripts/                      # Orquestación del pipeline (01-08)
├── sies_musica/                  # Paquete con la lógica del clasificador
└── tests/                        # Pruebas automatizadas (pytest)
```

| Carpeta | Rol | Se versiona |
|---|---|---|
| `sies_musica/` | Lógica pura y reutilizable (clasificador, lectura, ensamblado, LLM) | Sí |
| `scripts/` | Orquestación por etapas; cada script es una corrida reproducible | Sí |
| `tests/` | Pruebas del comportamiento externo del clasificador y del ensamblado | Sí |
| `metodologia/` | Documentación narrativa para el artículo académico | Sí |
| `logs/` | Evidencia de cada corrida (indicadores, fechas, rutas) | Sí |
| `prod/` | Productos finales e intermedios | Sí |
| `datos SIES/` | Documentación de la fuente (la base cruda no se versiona) | Parcial |

---

## 6. Reproducibilidad

### 6.1 Requisitos

- **Python ≥ 3.14**
- Dependencias: `pandas` (ver `requirements.txt`).

### 6.2 Instalación

```bash
git clone https://github.com/pedro-iglesias-calonge/claves-2007-2026-FILTRO.git
cd claves-2007-2026-FILTRO
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.3 Preparación de los datos

Descargue la base fuente del SIES/MINEDUC y colóquela en:

```
datos SIES/Matricula_2007_2026_WEB_10_07_2026.csv
```

Consulte [`datos SIES/README.md`](datos%20SIES/README.md) para la procedencia y el formato.

### 6.4 Ejecución del pipeline

```bash
python scripts/01_integridad.py                  # Verificación de integridad
python scripts/02_clasificacion.py               # Filtro léxico + semántico
python scripts/03_cliente_llm.py                 # Prueba del cliente LLM
python scripts/04_verificacion_falsos_negativos.py   # Requiere LLM (local o --cloud)
python scripts/05_verificacion_falsos_positivos.py   # Requiere LLM (local o --cloud)
python scripts/06_generar_zonas_grises.py        # Zonas grises para revisión humana
python scripts/07_generar_app_revision.py        # Genera la app HTML de revisión
python scripts/08_ensamblado_final.py            # Ensamblado final
```

- Las etapas **04** y **05** requieren un LLM. Por defecto usan un servidor local (Ollama); con el flag `--cloud` usan Blablador y leen la clave de la variable de entorno `SIES_BLABLADOR_API_KEY` o del archivo `.env` (ver `.env.example`).
- La etapa **07** genera `prod/revisar_zonas_grises.html`, que se abre en el navegador. La decisión humana se descarga como `prod/zonas_grises_revisadas.csv`.
- La etapa **08** consume la base completa y produce los productos finales.

### 6.5 Pruebas

```bash
python -m pytest
```

Las pruebas cubren la tabla de nombres → veredicto/categoría del clasificador, el manejo de encoding y los invariantes del CSV de salida (58 columnas, encoding, integridad de las filas incluidas).

---

## 7. Ética y uso de inteligencia artificial

El uso del modelo de lenguaje fue **estrictamente asistivo**. El LLM emitió recomendaciones de clasificación sobre un conjunto frontera (nunca sobre los 16.684 nombres completos) y esas recomendaciones fueron tratadas como **insumos**, no como decisiones definitivas. Los casos ambiguos fueron resueltos por **revisión humana**, priorizando la inclusión cuando existía duda razonable. Cada decisión quedó registrada con su método y su razón, lo que permite auditar el aporte del modelo y el del juicio humano por separado.

---

## 8. Limitaciones

1. **Tasa de error del LLM.** 2 de 67 consultas (3 %) de la verificación de falsos positivos retornaron errores de parseo; se mantuvo la clasificación léxica original y se marcaron para revisión humana.
2. **Muestreo.** Las verificaciones de falsos negativos (84 casos) y positivos (67 casos) se hicieron sobre muestras, no sobre la totalidad de la base, lo que deja un margen de incertidumbre residual.
3. **Dependencia del léxico.** La clasificación inicial depende de la exhaustividad del vocabulario construido (69 términos de inclusión, 47 de exclusión), refinado iterativamente pero no necesariamente exhaustivo.
4. **Subjetividad en zonas grises.** Los 26 casos remitidos a revisión humana implican un juicio que, aunque documentado y trazable, no es completamente reproducible sin acceso a los mismos criterios de decisión.
5. **Categoría faltante.** Dos programas incluidos por decisión humana carecen de categoría asignada (ver §4.4).

---

## 9. Cómo citar

Si utiliza este procedimiento o los datos derivados, cite el repositorio. Los metadatos están en [`CITATION.cff`](CITATION.cff).

```bibtex
@misc{claves2007_2026,
  title        = {CLAVES 2007-2026: Consulta Longitudinal Abierta para la Visualización de la Educación Superior Musical en Chile},
  author       = {Pedro Iglesias},
  year         = {2026},
  howpublished = {\url{https://github.com/pedro-iglesias-calonge/claves-2007-2026-FILTRO}},
  note         = {Filtrado reproducible de programas de música en la Base de Datos de Matrícula del SIES}
}
```

---

## 10. Licencia

Este repositorio usa **licencias duales** según el tipo de material:

- **Código** (`sies_musica/`, `scripts/`, `tests/`): licencia **MIT**. Ver [`LICENSE`](LICENSE).
- **Datos, documentación y resultados** (`metodologia/`, `logs/`, `prod/`, `README.md`, `CONTEXT.md`, glosario): licencia **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**. Ver [`LICENSE-CC-BY-4.0.md`](LICENSE-CC-BY-4.0.md).

La base fuente SIES conserva sus propias condiciones de uso como dato público; este repositorio solo distribuye los **derivados** y la documentación del procedimiento.

---

## 11. Autoría y contacto

- **Autoría:** Pedro Iglesias
- **Afiliación:** Universidad Alberto Hurtado, Instituto de Música
- **ORCID:** [0000-0003-4678-3365](https://orcid.org/0000-0003-4678-3365)
- **Correo institucional:** ipedro@uahurtado.cl
- **Repositorio:** <https://github.com/pedro-iglesias-calonge/claves-2007-2026-FILTRO>
