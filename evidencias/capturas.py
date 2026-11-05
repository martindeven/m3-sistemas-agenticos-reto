"""Capturas de evidencia de HU-10 contra la app desplegada (Playwright síncrono, sin dependencias nuevas).

Crea un empleado por la API (nunca toca la base de datos), abre su panel de vacaciones, pide un periodo
válido y uno solo de fin de semana, y guarda capturas en evidencias/capturas/. Al final captura el
diagrama del flujo. Cada captura comprueba el texto esperado: si no coincide, la guarda igual, avisa
y el script termina con código 1, para que la evidencia nunca afirme algo que la pantalla no muestra.

Requiere la app arriba en el puerto 8080 (docker compose up -d en app/).

Uso:  python -m evidencias.capturas      (o: python evidencias/capturas.py)
"""
import sys
import uuid
from pathlib import Path

import httpx
from playwright.sync_api import Locator, Page, expect, sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
WEB = "http://localhost:8080"
API = f"{WEB}/api"
CARPETA = RAIZ / "evidencias" / "capturas"
GRAFO = RAIZ / "flujos" / "salidas" / "grafo_flujo_s4.html"

EXITO = "Solicitud registrada: 8 días hábiles. Te quedan 4 días hábiles en 2026."
ERROR = "El periodo no incluye días hábiles"

guardadas: list[str] = []
avisos: list[str] = []


def crear_empleado() -> dict:
    """Crea por la API un empleado activo con correo único y fecha_ingreso 2024-03-10."""
    datos = {"nombre": "Evidencia Vacaciones", "correo": f"evidencia.{uuid.uuid4().hex[:8]}@empresa.com",
             "puesto": "Analista", "departamento": "Tecnología", "fecha_ingreso": "2024-03-10"}
    r = httpx.post(f"{API}/empleados", json=datos, timeout=10)
    if r.status_code != 201:
        sys.exit(f"No se pudo crear el empleado: {r.status_code} {r.text}")
    return r.json()


def capturar(objetivo: Page | Locator, nombre: str) -> None:
    """Guarda la captura de la página completa o de un solo elemento y la anota en la lista."""
    ruta = CARPETA / nombre
    if isinstance(objetivo, Page):
        objetivo.screenshot(path=ruta, full_page=True)
    else:
        objetivo.screenshot(path=ruta)
    guardadas.append(nombre)


def capturar_zona(pagina: Page, locators: list[Locator], nombre: str, margen: int = 12) -> None:
    """Recorta la página al rectángulo que cubre varios elementos (por ejemplo la fila y su panel).

    El directorio acumula los empleados de todas las pruebas: una captura de página completa deja
    el panel diminuto al final, así que se recorta solo la zona que importa.
    """
    cajas = []
    for loc in locators:
        loc.scroll_into_view_if_needed()
        caja = loc.bounding_box()
        scroll = pagina.evaluate("() => ({x: window.scrollX, y: window.scrollY})")
        cajas.append({"x": caja["x"] + scroll["x"], "y": caja["y"] + scroll["y"],
                      "x2": caja["x"] + scroll["x"] + caja["width"], "y2": caja["y"] + scroll["y"] + caja["height"]})
    x, y = max(min(c["x"] for c in cajas) - margen, 0), max(min(c["y"] for c in cajas) - margen, 0)
    x2, y2 = max(c["x2"] for c in cajas) + margen, max(c["y2"] for c in cajas) + margen
    pagina.screenshot(path=CARPETA / nombre, full_page=True, clip={"x": x, "y": y, "width": x2 - x, "height": y2 - y})
    guardadas.append(nombre)


def comprobar_texto(locator: Locator, esperado: str, captura: str) -> None:
    """Espera el texto exacto; si no aparece, deja un aviso (la captura se guarda de todos modos)."""
    try:
        expect(locator).to_have_text(esperado, timeout=5000)
    except AssertionError:
        real = locator.inner_text() if locator.count() else "(no apareció)"
        avisos.append(f"{captura}: se esperaba «{esperado}» y la pantalla muestra «{real}»")


def solicitar(panel: Locator, inicio: str, fin: str) -> None:
    """Llena las fechas del panel y pulsa Solicitar."""
    panel.get_by_test_id("vacaciones-fecha-inicio").fill(inicio)
    panel.get_by_test_id("vacaciones-fecha-fin").fill(fin)
    panel.get_by_test_id("vacaciones-enviar").click()


def main() -> int:
    """Genera las cinco capturas e imprime cuáles se guardaron; devuelve 1 si algún texto no coincidió."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    empleado = crear_empleado()
    eid = empleado["id"]
    print(f"Empleado creado por la API: id={eid} · {empleado['correo']}")

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1400, "height": 900})

        # 10 · Formulario abierto
        pagina.goto(WEB)
        pagina.get_by_test_id(f"vacaciones-abrir-{eid}").click()
        panel = pagina.get_by_test_id(f"panel-vacaciones-{eid}")
        zona = [pagina.get_by_test_id(f"fila-empleado-{eid}"), panel]   # la fila del empleado y su panel
        expect(panel.get_by_test_id("vacaciones-disponibles")).to_have_text("12")
        capturar_zona(pagina, zona, "10_formulario.png")

        # 11 · Solicitud aceptada: 8 días hábiles, quedan 4
        solicitar(panel, "2026-12-21", "2026-12-31")
        mensaje = panel.get_by_test_id("vacaciones-mensaje")
        comprobar_texto(mensaje, EXITO, "11_exito.png")
        capturar_zona(pagina, zona, "11_exito.png")

        # 12 · Error: periodo solo de fin de semana
        solicitar(panel, "2026-07-11", "2026-07-12")
        comprobar_texto(mensaje, ERROR, "12_error.png")
        capturar_zona(pagina, zona, "12_error.png")

        # 13 · Tabla de solicitudes (solo el elemento)
        tabla = panel.get_by_test_id("tabla-vacaciones")
        expect(tabla).to_be_visible()
        capturar(tabla, "13_tabla.png")

        # 14 · Diagrama del flujo (Mermaid se carga del CDN; sin red se captura el texto del grafo)
        if GRAFO.exists():
            pagina.goto(GRAFO.as_uri())
            try:
                # El <svg> aparece antes de dibujarse: se espera a que existan los nodos del grafo
                pagina.locator(".mermaid svg g.node").first.wait_for(timeout=20000)
                pagina.wait_for_timeout(500)
                capturar(pagina.locator(".mermaid svg"), "14_grafo.png")
            except Exception:
                avisos.append("14_grafo.png: Mermaid no se dibujó (¿sin internet?); se capturó la página tal cual")
                capturar(pagina, "14_grafo.png")
        else:
            avisos.append(f"14_grafo.png: no existe {GRAFO.relative_to(RAIZ)}")

        navegador.close()

    print(f"\nCapturas guardadas en {CARPETA.relative_to(RAIZ)}/:")
    for nombre in guardadas:
        print(f"  - {nombre}")
    for aviso in avisos:
        print(f"  ⚠ {aviso}")
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
