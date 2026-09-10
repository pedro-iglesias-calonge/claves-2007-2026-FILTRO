"""Etapa 01 — Lectura robusta y verificación de integridad.

Corre contra la base real y escribe el reporte de integridad en ``logs/``.
"""

from datetime import datetime
from pathlib import Path

from sies_musica.lectura import ReporteIntegridad, leer_matricula, reporte_integridad

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BASE = RAIZ / "datos SIES" / "Matricula_2007_2026_WEB_10_07_2026.csv"
RUTA_LOG = RAIZ / "logs" / "01-integridad.md"


def _a_markdown(reporte: ReporteIntegridad) -> str:
    ano_actual = datetime.now().year
    filas = []
    filas.append("# Etapa 01 — Verificación de integridad de la base")
    filas.append("")
    filas.append(f"Generado: {ano_actual}-{datetime.now().month:02d}-{datetime.now().day:02d}")
    filas.append(f"Archivo: `Matricula_2007_2026_WEB_10_07_2026.csv`")
    filas.append(f"Encoding confirmado: `{reporte['encoding']}` (BOM UTF-8 presente: {reporte['bom_utf8']})")
    filas.append(f"Bytes no decodificables leídos con reemplazo: {reporte['bytes_no_decodificables']}")
    filas.append("")
    filas.append("## Indicadores")
    filas.append("")
    filas.append(f"- Filas (matrículas): {reporte['filas']}")
    filas.append(f"- Columnas: {reporte['columnas']}")
    filas.append(f"- Años presentes: {', '.join(reporte['anios'])}")
    filas.append(f"- Nombres de carrera únicos (normalizados): {reporte['nombres_unicos_normalizados']}")
    filas.append(f"- Códigos de carrera únicos: {reporte['codigos_unicos']}")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
    df = leer_matricula(RUTA_BASE)
    reporte = reporte_integridad(df)
    RUTA_LOG.write_text(_a_markdown(reporte), encoding="utf-8")
    print(RUTA_LOG)
    print(f"Filas: {reporte['filas']} | Columnas: {reporte['columnas']} | "
          f"Nombres únicos: {reporte['nombres_unicos_normalizados']} | "
          f"Códigos únicos: {reporte['codigos_unicos']}")


if __name__ == "__main__":
    main()