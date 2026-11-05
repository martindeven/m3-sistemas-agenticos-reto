"""Pruebas de los validadores deterministas de la fábrica (sin LLM ni red).

Uso:  python -m pytest tests_fabrica -v
"""
import json

from agentes.analista import mensajes_exactos, validar_gherkin
from agentes.base import RAIZ
# Se importa el módulo, no la función: pytest recogería «testids_obligatorios» como si fuera una prueba
from agentes import disenador_pruebas as disenador
from agentes.disenador_pruebas import CAMPOS_VACACIONES, validar_plan

HU01 = RAIZ / "historias" / "HU-01-registrar-empleado.md"
HU10 = RAIZ / "historias" / "HU-10-solicitar-vacaciones.md"
MENSAJES = mensajes_exactos(HU10)

# Un escenario de error por cada fila de la tabla; N se sustituye por un número concreto
ERRORES = [
    ("Empleado inexistente", 404, "Empleado no encontrado"),
    ("Empleado dado de baja", 409, "No se pueden solicitar vacaciones para un empleado dado de baja"),
    ("Fechas invertidas", 400, "La fecha de fin no puede ser anterior a la fecha de inicio"),
    ("Periodo que cruza de año", 400, "Las vacaciones deben estar dentro de un mismo año calendario"),
    ("Año sin festivos", 400, "Solo se pueden solicitar vacaciones en 2026 y 2027"),
    ("Sin antigüedad", 400, "Se requiere al menos un año de antigüedad a la fecha de inicio"),
    ("Solo fin de semana", 400, "El periodo no incluye días hábiles"),
    ("Excede por uno", 400, "La solicitud excede los días disponibles: quedan 4 días hábiles"),
]
ACEPTADOS = [
    ("Solicitud aceptada con festivo", "2026-12-21", "2026-12-31", "Solicitud registrada: 8 días hábiles. Te quedan 4 días hábiles en 2026."),
    ("Límite exacto", "2026-07-13", "2026-07-21", "Solicitud registrada: 7 días hábiles. Te quedan 0 días hábiles en 2026."),
    ("Primer día de antigüedad", "2026-12-21", "2026-12-21", "Solicitud registrada: 1 días hábiles. Te quedan 11 días hábiles en 2026."),
]


def escenario(titulo: str, entonces: str) -> str:
    """Bloque Gherkin mínimo con Dado, Cuando y Entonces."""
    return (f"  Escenario: {titulo}\n"
            f"    Dado un empleado activo con fecha de ingreso 2025-12-21\n"
            f"    Cuando solicita vacaciones\n"
            f"    Entonces {entonces}\n\n")


def gherkin_hu10(omitir: str | None = None, reemplazo: tuple[str, str] | None = None) -> str:
    """Gherkin completo de HU-10; `omitir` quita un escenario y `reemplazo` altera un texto."""
    texto = "# language: es\nCaracterística: Solicitar vacaciones\n\n"
    for titulo, ini, fin, msg in ACEPTADOS:
        texto += escenario(titulo, f'la API responde 201 del {ini} al {fin} y muestra "{msg}"')
    for titulo, codigo, msg in ERRORES:
        if titulo != omitir:
            texto += escenario(titulo, f'la API responde {codigo} con "{msg}"')
    if reemplazo:
        texto = texto.replace(*reemplazo)
    return texto


def test_mensajes_exactos_de_hu10():
    assert len(MENSAJES) == 8
    assert MENSAJES[0] == "Empleado no encontrado"
    assert MENSAJES[-1] == "La solicitud excede los días disponibles: quedan N días hábiles"


def test_historias_sin_convenciones_no_tienen_mensajes():
    assert mensajes_exactos(HU01) == []


def test_gherkin_completo_pasa():
    assert validar_gherkin(gherkin_hu10(), MENSAJES) == []


def test_gherkin_sin_un_mensaje_da_error():
    problemas = validar_gherkin(gherkin_hu10(omitir="Empleado inexistente"), MENSAJES)
    assert "Falta el mensaje exacto: «Empleado no encontrado»" in problemas


def test_mensaje_sin_acento_da_error():
    texto = gherkin_hu10(reemplazo=("no incluye días hábiles", "no incluye dias hábiles"))
    assert "Falta el mensaje exacto: «El periodo no incluye días hábiles»" in validar_gherkin(texto, MENSAJES)


def test_falta_limite_exacto_da_error():
    texto = gherkin_hu10(reemplazo=("Límite exacto", "Otra solicitud"))
    assert any("límite exacto" in p for p in validar_gherkin(texto, MENSAJES))


def test_sin_mensajes_se_mantienen_las_reglas_de_siempre():
    texto = ("# language: es\nCaracterística: Registrar empleado\n\n"
             + escenario("Alta exitosa", "ve el mensaje de éxito")
             + escenario("Correo repetido", 've "El correo ya está registrado"'))
    assert validar_gherkin(texto) == []


def plan_hu10(omitir_mensaje: str | None = None) -> str:
    """Plan de pruebas mínimo que cubre los escenarios de gherkin_hu10()."""
    datos = {"fecha_ingreso": "2025-12-21", "fecha_inicio": "2026-12-21", "fecha_fin": "2026-12-31"}
    casos = []
    for i, (titulo, _, _, msg) in enumerate(ACEPTADOS, 1):
        casos.append({"id": f"CP-{i:02}", "escenario": titulo, "nivel": "api", "precondiciones": [],
                      "pasos": ["POST"], "datos": datos, "resultado_esperado": f"201 · {msg}"})
    for titulo, codigo, msg in ERRORES:
        esperado = "400" if msg == omitir_mensaje else f"{codigo} · {msg}"
        casos.append({"id": f"CP-{len(casos) + 1:02}", "escenario": titulo, "nivel": "api", "precondiciones": [],
                      "pasos": ["POST"], "datos": datos, "resultado_esperado": esperado})
    pasos_e2e = [f"usa {t.replace('{empleado_id}', '7')}" for t in disenador.testids_obligatorios(HU10)]
    casos.append({"id": "CP-99", "escenario": "Límite exacto", "nivel": "e2e", "precondiciones": [],
                  "pasos": pasos_e2e, "datos": datos, "resultado_esperado": "ve el mensaje de éxito"})
    return json.dumps({"historia": "HU-10", "casos": casos}, ensure_ascii=False)


def test_plan_completo_pasa():
    problemas = validar_plan(plan_hu10(), gherkin_hu10(), MENSAJES, disenador.testids_obligatorios(HU10), CAMPOS_VACACIONES)
    assert problemas == []


def test_plan_sin_un_mensaje_da_error():
    plan = plan_hu10(omitir_mensaje="Empleado no encontrado")
    problemas = validar_plan(plan, gherkin_hu10(), MENSAJES)
    assert "Ningún caso espera el mensaje exacto: «Empleado no encontrado»" in problemas
