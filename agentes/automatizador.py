"""Sesión 3 · Agente 5, automatizador: casos de prueba -> pruebas con pytest y Playwright.

Uso:  python -m agentes.automatizador HU-01
"""
import sys

from agentes.base import APP, SALIDA
from agentes.claude_code import EDICION, ejecutar_claude_code

INSTRUCCIONES = """Eres el ingeniero de automatización de pruebas del equipo. Conviertes casos de prueba
en pruebas automatizadas. Nunca modificas el código de la aplicación: si una prueba falla
porque la aplicación está mal, lo reportas, no lo arreglas.

Reglas de datos y aserciones:
- Nunca leas ni escribas la base de datos (ni sqlite3, ni SQLAlchemy, ni archivos .db): la base vive
  dentro del contenedor. Todo dato de prueba se crea y se modifica por la API:
  POST /api/empleados y PATCH /api/empleados/{id}/baja con {"fecha_baja": "AAAA-MM-DD"}.
- Correos únicos con uuid4 (por ejemplo f"ana.{uuid4().hex[:8]}@empresa.com"). Departamentos solo de:
  Tecnología, Ventas, Finanzas, Recursos Humanos, Operaciones.
- Fechas coherentes entre sí: crea al empleado con fecha_ingreso explícita (no dependas de un valor por
  defecto) y usa una fecha_baja posterior a ella (por ejemplo ingreso "2024-03-10", baja "2025-06-30").
  Una baja anterior al ingreso solo se usa en el caso que prueba precisamente ese error.
- Si un caso e2e pide un valor que la pantalla no ofrece (por ejemplo un departamento fuera del <select>),
  ese paso es inalcanzable desde la UI: no lo intentes. Marca el test con pytest.mark.skip y escribe en el
  motivo por qué es inalcanzable y qué caso de API lo cubre.
- Solo afirmes textos de error que el contexto fija letra por letra. En los 422 genéricos de validación
  (los que arma Pydantic) afirma solo el código; en E2E, solo que el mensaje de error es visible.
- E2E: acota los locators al contenedor de la funcionalidad, por ejemplo
  page.get_by_test_id(f"fila-empleado-{id}").get_by_test_id(...) o el panel de vacaciones, porque
  mensaje-exito y mensaje-error existen en varios lugares de la pantalla.
- HU-10: cada prueba crea su propio empleado. fecha_ingreso "2024-03-10" en general y "2025-12-21" para
  el límite de antigüedad (inicio 2026-12-21 -> 201; inicio 2026-12-18 -> 400). Periodos de ejemplo:
  · 2026-12-21..2026-12-31 = 8 días hábiles; 2026-09-14..2026-09-18 = 4; 2026-07-11..2026-07-12 = 0 (400).
  · 2026-08-03..2026-08-14 = 10 y luego 2026-06-01..2026-06-02 = 2 (quedan 0, aceptada),
    o 2026-06-01..2026-06-03 = 3 (400 "La solicitud excede los días disponibles: quedan 2 días hábiles").
  · Un periodo en 2028 -> 400 de año sin festivos; 2026-12-28..2027-01-08 -> 400 de año calendario.
- El docstring de cada prueba empieza con su id de caso (por ejemplo "CP-03: ...")."""

ESCRITURA = ["tests/*"]
PROGRAMAS = {"cd", "ls", "cat", "python", "python3", "pytest"}

TAREA = """Automatiza los casos de prueba de {hu}:

{casos}

Reglas:
- tests/conftest.py define dos fixtures: `url_api` (variable URL_API, por defecto http://localhost:8000)
  y `url_web` (variable URL_WEB, por defecto http://localhost:8080). Si ya existe, consérvalo.
- Casos de nivel "api": tests/api/test_{hu_min}.py con pytest y httpx.
- Casos de nivel "e2e": tests/e2e/test_{hu_min}_e2e.py con pytest-playwright (fixture `page`),
  usando page.get_by_test_id(...) con los data-testid de CLAUDE.md.
- Un test por caso; su docstring empieza con el id del caso (por ejemplo "CP-03: ...").
- Cada test crea sus propios datos con correos únicos (uuid) para poder repetirse sin choques.
- Comprueba la sintaxis con `python -m pytest tests --collect-only -q`. No ejecutes las pruebas completas.
Responde con la lista de archivos y cuántos tests escribiste."""



def automatizar(hu: str, errores: str = "") -> tuple[str, float]:
    """Pide a Claude Code que escriba en app/tests las pruebas de los casos de la historia.

    Si `errores` trae el diagnóstico de una ejecución anterior, se agrega al prompt para que corrija.
    Devuelve (respuesta final del agente, costo en USD).
    """
    casos = (SALIDA / hu / "casos_prueba.json").read_text(encoding="utf-8")
    prompt = TAREA.format(hu=hu, casos=casos, hu_min=hu.lower().replace("-", "_"))
    if errores:
        prompt += f"\n\nEstas pruebas fallaron y el diagnóstico dice que el error está en la prueba:\n{errores}"
    return ejecutar_claude_code(prompt, agente="automatizador", cwd=APP, herramientas=EDICION,
                                escritura=ESCRITURA, programas=PROGRAMAS, instrucciones=INSTRUCCIONES)


if __name__ == "__main__":
    print(automatizar(sys.argv[1])[0])
