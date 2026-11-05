"""Sesión 1 · Agente 2, diseñador de pruebas: criterios de aceptación -> casos de prueba.

Uso:  python -m agentes.disenador_pruebas salida/HU-01/criterios.feature
"""
import json
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from agentes.analista import convenciones_citadas, escenarios, mensajes_exactos, patron_mensaje
from agentes.base import RAIZ, Herramienta, ejecutar_agente, herramientas_archivos, rel

# Campos que todo caso de vacaciones debe traer en `datos`
CAMPOS_VACACIONES = ("fecha_ingreso", "fecha_inicio", "fecha_fin")


class CasoPrueba(BaseModel):
    """Un caso de prueba: escenario que cubre, nivel (api o e2e), pasos, datos y resultado esperado."""
    id: str                          # CP-01, CP-02...
    escenario: str                   # nombre exacto del escenario Gherkin que cubre
    nivel: Literal["api", "e2e"]     # api: se prueba con HTTP; e2e: se prueba en el navegador
    precondiciones: list[str]
    pasos: list[str]
    datos: dict[str, str]
    resultado_esperado: str


class PlanPruebas(BaseModel):
    """Plan de pruebas de una historia: el contrato de casos_prueba.json."""
    historia: str
    casos: list[CasoPrueba]


SISTEMA = """Eres diseñador de pruebas de software. A partir de criterios de aceptación en Gherkin
escribes casos de prueba que luego otra persona automatizará.

Cómo trabajas:
1. Lee {criterios} y contexto/convenciones_app.md (ahí están la API y los data-testid de la pantalla).
2. Para cada escenario escribe al menos un caso de nivel "api". Si el escenario involucra la pantalla,
   escribe además uno de nivel "e2e" cuyos pasos mencionen los data-testid que se usan.
3. Usa datos concretos y únicos: cada caso con su propio nombre y correo (por ejemplo con el id del
   caso: ana.cp03@empresa.com), para que los casos no choquen entre sí. Usa el dominio empresa.com.
4. Si los criterios son de vacaciones:
   - Lee contexto/reglas_vacaciones.md y contexto/convenciones_vacaciones.md.
   - Toma las fechas de los ejemplos de reglas_vacaciones.md: 2026-12-21 al 2026-12-31 (8 días hábiles),
     2026-09-14 al 2026-09-18 (4, festivo el 16), 2026-07-11 al 2026-07-12 (0, fin de semana);
     ingreso 2025-12-21 con inicio 2026-12-21 (sí) o 2026-12-18 (no); ingreso 2024-03-10.
   - En "datos" incluye SIEMPRE fecha_ingreso, fecha_inicio y fecha_fin.
   - En "resultado_esperado" escribe el código HTTP y el `detail` copiado letra por letra.
   - Los pasos de los casos e2e usan los data-testid de la tabla de convenciones de vacaciones.
5. Guarda los casos llamando a la herramienta guardar_casos (no escribas el JSON a mano).
   - Guárdalos en LOTES de máximo 6 casos por llamada (varias llamadas): cada respuesta tuya tiene un
     tope de tamaño y un plan grande en una sola llamada se corta. Cada llamada agrega los casos nuevos
     y reemplaza los que tengan el mismo id; para corregir un caso, vuelve a enviarlo con su id.
   - Escribe poco texto fuera de la herramienta: el contenido va en los casos.
   - "nivel" solo puede ser "api" o "e2e".
   - En "datos" TODOS los valores son texto: "201", no 201; para un campo vacío usa "", nunca null.
   - En "escenario" copia el nombre del escenario EXACTAMENTE como aparece después de "Escenario:".
   - Si guardar_casos devuelve un error, corrige lo que indica y vuelve a llamarla.
6. Responde al final con una sola línea: cuántos casos escribiste."""


def testids_obligatorios(historia: Path) -> list[str]:
    """data-testid de la tabla «data-testid obligatorios» de las convenciones que cita la historia.

    Toma el texto entre backticks de la última columna de cada fila, hasta que termina la tabla.
    Sin convenciones citadas devuelve [].
    """
    testids: list[str] = []
    for archivo in convenciones_citadas(historia):
        dentro = False
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if "data-testid" in linea and "obligatorios" in linea:
                dentro = True
                continue
            if dentro and linea.strip().startswith("|"):
                valor = re.fullmatch(r"`(.+)`", linea.strip().strip("|").split("|")[-1].strip())
                if valor and valor[1] != "data-testid" and valor[1] not in testids:
                    testids.append(valor[1])
            elif dentro and testids:
                break                                     # terminó la tabla
    return testids


def historia_de(criterios: Path) -> Path | None:
    """Historia que corresponde a unos criterios: salida/HU-10/criterios.feature -> historias/HU-10-*.md."""
    return next(iter(sorted((RAIZ / "historias").glob(f"{criterios.parent.name}-*.md"))), None)


def validar_plan(texto: str, gherkin: str, mensajes: list[str] | None = None,
                 testids: list[str] | None = None, campos: tuple[str, ...] | None = None) -> list[str]:
    """Evaluador determinista: JSON válido y cada escenario cubierto por al menos un caso.

    Con `mensajes`, cada `detail` exacto debe aparecer en el resultado_esperado de algún caso.
    Con `testids`, los casos e2e deben usar los data-testid de las convenciones (entre todos, todos).
    Con `campos`, cada caso debe traer esas claves en `datos`.
    """
    try:
        plan = PlanPruebas.model_validate_json(texto)
    except ValidationError as e:
        return [f"El JSON no cumple el esquema: {e.errors()[:3]}"]
    cubiertos = {c.escenario.strip() for c in plan.casos}
    problemas = [f"Escenario sin casos: {e}" for e in escenarios(gherkin) if e not in cubiertos]
    ids = [c.id for c in plan.casos]
    if len(ids) != len(set(ids)):
        problemas.append("Hay ids de caso repetidos.")

    for m in mensajes or []:
        if not any(patron_mensaje(m).search(c.resultado_esperado) for c in plan.casos):
            problemas.append(f"Ningún caso espera el mensaje exacto: «{m}»")

    if testids:
        # «vacaciones-abrir-{empleado_id}» se busca por su prefijo, así vale «vacaciones-abrir-7»
        prefijos = {t: t.split("{")[0] for t in testids}
        e2e = [c for c in plan.casos if c.nivel == "e2e"]
        if not e2e:
            problemas.append("No hay casos e2e; la pantalla de vacaciones necesita al menos uno.")
        usados: set[str] = set()
        for c in e2e:
            texto_caso = " ".join(c.precondiciones + c.pasos + [c.resultado_esperado])
            propios = {t for t, p in prefijos.items() if p in texto_caso}
            if not propios:
                problemas.append(f"El caso e2e {c.id} no usa ningún data-testid de las convenciones.")
            usados |= propios
        if e2e:
            for t in testids:
                if t not in usados:
                    problemas.append(f"Ningún caso e2e usa el data-testid {t}.")

    for c in plan.casos if campos else []:
        faltan = [k for k in campos if k not in c.datos]
        if faltan:
            problemas.append(f"El caso {c.id} no incluye en datos: {', '.join(faltan)}.")
    return problemas


def herramienta_guardar_casos(destino: Path) -> Herramienta:
    """El contrato viaja en el esquema de la herramienta: el modelo llena campos, no escribe JSON a mano.

    Guarda por lotes: la primera llamada de esta ejecución empieza un archivo nuevo (descarta el de una
    corrida anterior); las siguientes agregan casos y reemplazan los que tengan el mismo id. Así un plan
    grande no tiene que caber en una sola respuesta del modelo (tope de max_tokens).
    """
    acumulados: dict[str, CasoPrueba] = {}          # id -> caso, vive mientras dure disenar_casos

    def guardar_casos(historia: str, casos: list) -> str:
        try:
            lote = PlanPruebas.model_validate({"historia": historia, "casos": casos})
        except ValidationError as e:  # el error regresa al modelo como texto, corto y accionable
            raise ValueError("Los casos no cumplen el esquema: " + "; ".join(
                f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()[:5]))
        for caso in lote.casos:
            acumulados[caso.id] = caso
        plan = PlanPruebas(historia=historia, casos=list(acumulados.values()))
        destino.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return (f"Lote de {len(lote.casos)} casos guardado; el archivo {rel(destino)} tiene {len(plan.casos)} "
                f"casos en total: {', '.join(acumulados)}")
    return Herramienta(
        "guardar_casos",
        "Guarda un LOTE de casos (máximo 6 por llamada) en casos_prueba.json y lo valida; si hay errores, los "
        "devuelve para que corrijas. Cada llamada agrega casos y reemplaza los de mismo id. "
        "Ejemplo: historia='HU-01', casos=[{'id': 'CP-01', 'escenario': 'Alta exitosa', 'nivel': 'api', "
        "'precondiciones': [], 'pasos': ['...'], 'datos': {'correo': 'ana@empresa.com'}, 'resultado_esperado': '...'}].",
        {"historia": {"type": "string"},
         "casos": {"type": "array", "items": CasoPrueba.model_json_schema()}},
        guardar_casos)


def disenar_casos(criterios: Path, max_intentos: int = 2, max_pasos: int = 20) -> Path:
    """Ejecuta al diseñador y valida su plan; si hay problemas, se los devuelve para que corrija.

    Las exigencias extra (mensajes, data-testid y campos de vacaciones) salen de las convenciones
    que cita la historia; en HU-01 a HU-03 quedan vacías y la validación es la de siempre.
    """
    historia = historia_de(criterios)
    mensajes = mensajes_exactos(historia) if historia else []
    testids = testids_obligatorios(historia) if historia else []
    campos = CAMPOS_VACACIONES if historia and any(
        "vacaciones" in p.name for p in convenciones_citadas(historia)) else None
    carpeta = criterios.parent
    destino = carpeta / "casos_prueba.json"
    lectura = [h for h in herramientas_archivos(lectura=[RAIZ / "contexto", carpeta], escritura=carpeta)
               if h.nombre != "escribir_archivo"]          # solo se escribe a través de guardar_casos
    herramientas = lectura + [herramienta_guardar_casos(destino)]
    sistema = SISTEMA.format(criterios=rel(criterios))
    gherkin = criterios.read_text(encoding="utf-8")
    tarea = f"Diseña los casos de prueba para {rel(criterios)}."
    for intento in range(1, max_intentos + 1):
        print(f"Diseñador de pruebas · intento {intento}")
        # Más pasos que el valor por defecto (10): guardar por lotes usa varias llamadas a guardar_casos
        ejecutar_agente(sistema, herramientas, tarea, max_pasos=max_pasos, nombre="disenador")
        problemas = validar_plan(destino.read_text(encoding="utf-8"), gherkin, mensajes, testids, campos) \
            if destino.exists() \
            else [f"No se escribió {rel(destino)}."]
        if not problemas:
            return destino
        tarea += "\n\nTu versión anterior tiene estos problemas; corrígelos:\n- " + "\n- ".join(problemas)
    raise ValueError("Casos inválidos tras varios intentos:\n- " + "\n- ".join(problemas))


if __name__ == "__main__":
    ruta = disenar_casos(Path(sys.argv[1]).resolve())
    plan = PlanPruebas.model_validate_json(ruta.read_text(encoding="utf-8"))
    print(f"\nListo: {rel(ruta)} · {len(plan.casos)} casos "
          f"({sum(c.nivel == 'api' for c in plan.casos)} api, {sum(c.nivel == 'e2e' for c in plan.casos)} e2e)")