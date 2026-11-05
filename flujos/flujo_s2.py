"""Sesión 2 · Flujo con estado: historia -> criterios -> casos -> plan aprobado -> código verificado.

Uso:  python -m flujos.flujo_s2 historias/HU-01-registrar-empleado.md
"""
import operator
import sys
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
"""QUITAR labs !!!! """
from agentes import desarrollador
from agentes.analista import generar_criterios, preguntas_abiertas
from agentes.base import hu_de
from agentes.disenador_pruebas import disenar_casos
from flujos.verificacion import verificar_app
from flujos.util import dibuja_grafo
MAX_INTENTOS = 2


class Estado(TypedDict, total=False):
    """Estado compartido del flujo; bitacora y costo_usd se acumulan con operator.add."""
    historia: str
    hu: str
    criterios: str
    preguntas: list[str]
    casos: str
    plan: str
    comentarios: str
    plan_aprobado: bool
    intentos: int
    app_ok: bool
    log_verificacion: str
    costo_usd: Annotated[float, operator.add]   # reducer: cada nodo suma su costo
    bitacora: Annotated[list[str], operator.add]


# --- Nodos -----------------------------------------------------------------
def analizar(s: Estado) -> Estado:
    """Nodo agente: el analista escribe y valida criterios.feature."""
    ruta = generar_criterios(Path(s["historia"]))                      # Agente 1
    return {"hu": hu_de(Path(s["historia"])), "criterios": str(ruta), "intentos": 0, "costo_usd": 0.0,
            "preguntas": preguntas_abiertas(ruta.read_text(encoding="utf-8")),
            "bitacora": [f"Criterios escritos en {ruta.name}"]}


def despues_de_analizar(s: Estado) -> Literal["pedir_aclaracion", "disenar_casos"]:
    """Arista condicional: si hay preguntas abiertas, pide aclaración; si no, diseña casos."""
    return "pedir_aclaracion" if s["preguntas"] else "disenar_casos"


def pedir_aclaracion(s: Estado) -> Estado:
    """Nodo humano (interrupt): pregunta si se continúa con preguntas abiertas; solo «si» continúa."""
    respuesta = interrupt({"preguntas": s["preguntas"],
                           "pregunta": "Hay preguntas abiertas. ¿Continuar de todos modos? (si/no)"})
    return {"bitacora": [f"Preguntas abiertas: la persona respondió '{respuesta}'"],
            "comentarios": "" if respuesta.strip().lower() == "si" else "detener"}


def despues_de_aclarar(s: Estado) -> Literal["disenar_casos", "__end__"]:
    """Arista condicional: termina si la persona no respondió «si»."""
    return END if s.get("comentarios") == "detener" else "disenar_casos"


def disenar(s: Estado) -> Estado:
    """Nodo agente: el diseñador escribe y valida casos_prueba.json."""
    ruta = disenar_casos(Path(s["criterios"]))                         # Agente 2
    return {"casos": str(ruta), "bitacora": [f"Casos de prueba escritos en {ruta.name}"]}


def planificar(s: Estado) -> Estado:
    """Nodo agente: el desarrollador propone un plan en modo solo lectura."""
    plan, costo = desarrollador.planificar(s["hu"], s.get("comentarios", ""))   # Agente 3, solo lectura
    return {"plan": plan, "costo_usd": costo}


def aprobar_plan(s: Estado) -> Estado:
    """Nodo humano (interrupt): «si» aprueba el plan; cualquier otro texto lo rechaza como comentario."""
    decision = interrupt({"plan": s["plan"], "pregunta": "¿Aprobar el plan? Escribe 'si' o tus comentarios"})
    if decision.strip().lower() == "si":
        return {"plan_aprobado": True, "bitacora": ["Plan aprobado por una persona"]}
    return {"plan_aprobado": False, "comentarios": decision, "bitacora": [f"Plan rechazado: {decision}"]}


def despues_de_aprobar(s: Estado) -> Literal["construir", "planificar"]:
    """Arista condicional: con el plan aprobado construye; si no, vuelve a planificar."""
    return "construir" if s["plan_aprobado"] else "planificar"


def construir(s: Estado) -> Estado:
    """Nodo agente: el desarrollador implementa el plan; si la verificación anterior falló, recibe su log."""
    errores = "" if s.get("app_ok", True) else s.get("log_verificacion", "")
    resumen, costo = desarrollador.construir(s["hu"], s["plan"], errores)      # Agente 3, edición
    return {"intentos": s["intentos"] + 1, "costo_usd": costo, "bitacora": [f"Construcción {s['intentos'] + 1}"]}


def verificar(s: Estado) -> Estado:
    """Nodo workflow: verificación determinista de la app (salud de la API y build del front-end)."""
    ok, log = verificar_app()                                          # determinista, sin LLM
    return {"app_ok": ok, "log_verificacion": log, "bitacora": [f"Verificación: {'OK' if ok else 'FALLA'}"]}


def despues_de_verificar(s: Estado) -> Literal["construir", "fin"]:
    """Arista condicional: reintenta construir hasta MAX_INTENTOS o termina."""
    return "construir" if not s["app_ok"] and s["intentos"] < MAX_INTENTOS else "fin"


def fin(s: Estado) -> Estado:
    """Nodo workflow: imprime el resumen y la bitácora."""
    print(f"\n=== {s['hu']} · app {'LISTA' if s.get('app_ok') else 'ESCALAR A UNA PERSONA'} "
          f"· {s.get('costo_usd', 0):.2f} USD ===")
    for linea in s.get("bitacora", []):
        print(" -", linea)
    return {}


def construir_grafo():
    """Arma y compila el grafo de la sesión 2 y dibuja su diagrama."""
    g = StateGraph(Estado)
    for nombre, fn in [("analizar", analizar), ("pedir_aclaracion", pedir_aclaracion),
                       ("disenar_casos", disenar), ("planificar", planificar), ("aprobar_plan", aprobar_plan),
                       ("construir", construir), ("verificar", verificar), ("fin", fin)]:
        g.add_node(nombre, fn)
    g.add_edge(START, "analizar")
    g.add_conditional_edges("analizar", despues_de_analizar)
    g.add_conditional_edges("pedir_aclaracion", despues_de_aclarar)
    g.add_edge("disenar_casos", "planificar")
    g.add_edge("planificar", "aprobar_plan")
    g.add_conditional_edges("aprobar_plan", despues_de_aprobar)
    g.add_edge("construir", "verificar")
    g.add_conditional_edges("verificar", despues_de_verificar)
    g.add_edge("fin", END)
    app = g.compile(checkpointer=InMemorySaver())
    #YA DIBUJA EL GRAFO ! 
    dibuja_grafo(app,"flujo_s2")
    return app


def ejecutar(app, historia: str) -> dict:
    """Corre el flujo y atiende cada pausa humana desde la terminal."""
    cfg = {"configurable": {"thread_id": Path(historia).stem}}
    out = app.invoke({"historia": str(Path(historia).resolve())}, cfg)
    while "__interrupt__" in out:
        pausa = out["__interrupt__"][0].value
        for clave in ("preguntas", "plan", "diagnostico"):
            if clave in pausa:
                print(f"\n--- {clave.upper()} ---\n{pausa[clave]}")
        out = app.invoke(Command(resume=input(pausa["pregunta"] + ": ")), cfg)
    return out


if __name__ == "__main__":
    #NO NECESITA COLOCAR --grafo, ya lo hace
    ejecutar(construir_grafo(), sys.argv[1])
