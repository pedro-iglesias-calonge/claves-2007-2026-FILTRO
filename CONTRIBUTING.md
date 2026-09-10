# Guía de contribución

Gracias por su interés en este proyecto. Este repositorio acompaña una
publicación académica, por lo que la prioridad es la **trazabilidad** y la
**reproducibilidad** del procedimiento.

## Reportar un problema

Si detecta un error de clasificación, una inconsistencia en los datos derivados
o un fallo de reproducibilidad:

1. Abra un *issue* describiendo el caso.
2. Incluya el **nombre normalizado del programa**, el veredicto actual y el
   veredicto esperado, con una breve justificación.
3. Si es posible, indique el archivo o la etapa donde se observa el problema.

## Proponer cambios

1. Cree una rama descriptiva (`fix/...`, `docs/...`, `feat/...`).
2. Mantenga los cambios acotados y documentados.
3. Asegúrese de que las pruebas pasan antes de enviar el *pull request*:

   ```bash
   python -m pytest
   ```

4. Describa en el *pull request* qué cambia y por qué, y cómo se verificó.

## Estilo

- **Python:** siga el estilo existente; el proyecto se verifica con `mypy` en
  modo estricto (`pyproject.toml`).
- **Datos y resultados:** no edite a mano los archivos de `prod/`; regenérelos
  con los scripts correspondientes.
- **Documentación:** mantenga la coherencia con `CONTEXT.md` (glosario de
  dominio) y con la numeración de las etapas `01`-`08`.

## Convenciones de la metodología

- Cada etapa nueva debe registrarse en `metodologia/`, `scripts/` y `logs/`,
  siguiendo la numeración existente.
- Toda decisión debe quedar con **método** (`lexico`, `semantico`, `llm` o
  `humano`) y **razón**.
- Las zonas grises se resuelven por revisión humana; no se itera sobre el LLM.
