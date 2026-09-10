# Datos de origen

Esta carpeta documenta la fuente de datos y contiene el glosario oficial de
campos. **La base de matrícula cruda no se versiona en este repositorio.**

## Base de Datos de Matrícula SIES

| Atributo | Valor |
|---|---|
| Producto | Base de Datos de Matrícula en Educación Superior |
| Organismo | Servicio de Información de Educación Superior (SIES), Ministerio de Educación de Chile |
| Archivo esperado | `Matricula_2007_2026_WEB_10_07_2026.csv` |
| Período | 2007-2026 |
| Tamaño | ≈ 149 MB |
| Registros | 280.160 filas |
| Columnas | 58 |
| Separador | `;` |
| Encoding | `cp1252` |
| Glosario | [`glosario_bases_matricula_2026.md`](glosario_bases_matricula_2026.md) |

### Por qué no se incluye

- Supera el límite de 100 MB por archivo de GitHub.
- Es un recurso público que puede descargarse directamente desde las fuentes
  oficiales, de modo que versionarlo sería redundante.

### Cómo obtenerla

1. Ingrese al portal de datos abiertos del Ministerio de Educación de Chile
   (<https://datosabiertos.mineduc.cl/>) o al sitio del SIES
   (<https://www.sies.cl/>).
2. Busque la sección de **Bases de Datos de Matrícula en Educación Superior**.
3. Descargue la base del período **2007-2026**.
4. Coloque el archivo en esta carpeta con el nombre exacto
   `Matricula_2007_2026_WEB_10_07_2026.csv`.

> Si el archivo descargado tiene otro nombre o extensión, ajústelo o pase la
> ruta mediante los argumentos `--matricula` de los scripts que la aceptan
> (`06_generar_zonas_grises.py`, `08_ensamblado_final.py`).

## Glosario de campos

El archivo [`glosario_bases_matricula_2026.md`](glosario_bases_matricula_2026.md)
reproduce el glosario oficial de los 58 campos de la base (nombre, valores
posibles y descripción). Es la referencia para interpretar las columnas que el
pipeline conserva intactas en `prod/Musica_2007_2026_filtrado.csv`.

## Nota sobre encoding

La base fuente está codificada en **`cp1252`** y contiene **5 bytes no
decodificables**. El pipeline los aísla y registra durante la verificación de
integridad (`scripts/01_integridad.py`) y los reemplaza al leer, sin alterar el
resto de los datos. Los productos derivados se escriben en `cp1252` para
conservar el formato de la fuente.
