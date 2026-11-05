"""Pruebas end-to-end para HU-01: registrar un empleado."""
import uuid

import httpx
import pytest
from playwright.sync_api import Page, expect


def test_cp02_registrar_empleado_datos_validos(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Registrar un empleado con datos válidos."""
    correo = f"ana.torres.{uuid.uuid4().hex[:8]}@empresa.com"

    page.goto(url_web)
    page.get_by_test_id("empleado-nombre").fill("Ana Torres")
    page.get_by_test_id("empleado-correo").fill(correo.upper())
    page.get_by_test_id("empleado-puesto").fill("Desarrolladora")
    page.get_by_test_id("empleado-departamento").select_option("Tecnología")
    page.get_by_test_id("empleado-fecha-ingreso").fill("2024-01-15")
    page.get_by_test_id("empleado-guardar").click()

    mensaje_exito = page.get_by_test_id("mensaje-exito")
    expect(mensaje_exito).to_be_visible()

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": correo})
    assert respuesta.status_code == 200
    [creado] = [e for e in respuesta.json() if e["correo"] == correo]
    expect(mensaje_exito).to_contain_text(creado["numero_empleado"])


@pytest.mark.skip(
    reason=(
        "CP-07 pide elegir el departamento inválido 'Marketing', pero "
        "data-testid='empleado-departamento' es un <select> con únicamente las opciones "
        "del catálogo (Tecnología, Ventas, Finanzas, Recursos Humanos, Operaciones); la "
        "pantalla real no permite seleccionar un valor fuera de esa lista, así que el "
        "escenario no es alcanzable desde la UI. El caso equivalente a nivel API ya está "
        "cubierto por CP-06."
    )
)
def test_cp07_departamento_invalido(page: Page, url_web: str) -> None:
    """CP-07: Intentar registrar un empleado con un departamento que no está en la lista permitida."""
