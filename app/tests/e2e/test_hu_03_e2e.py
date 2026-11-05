"""Pruebas end-to-end para HU-03: editar y dar de baja a un empleado."""
import uuid

import httpx
import pytest
from playwright.sync_api import Page, expect


def _crear_empleado(
    url_api: str,
    *,
    nombre: str = "Empleado Prueba",
    puesto: str = "Analista",
    departamento: str = "Ventas",
    fecha_ingreso: str = "2024-01-15",
) -> dict:
    correo = f"{uuid.uuid4().hex[:10]}@empresa.com"
    cuerpo = {
        "nombre": nombre,
        "correo": correo,
        "puesto": puesto,
        "departamento": departamento,
        "fecha_ingreso": fecha_ingreso,
    }
    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_cp02_editar_puesto_y_departamento(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Editar correctamente el puesto y el departamento de un empleado activo."""
    empleado = _crear_empleado(url_api, puesto="Analista", departamento="Ventas")

    page.goto(url_web)
    page.get_by_test_id(f"editar-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("empleado-puesto").fill("Analista Senior")
    fila.get_by_test_id("empleado-departamento").select_option("Tecnología")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.locator("section").get_by_test_id("mensaje-exito")).to_be_visible()
    expect(fila).to_contain_text("Analista Senior")
    expect(fila).to_contain_text("Tecnología")


def test_cp04_dar_de_baja_empleado_activo(page: Page, url_api: str, url_web: str) -> None:
    """CP-04: Dar de baja correctamente a un empleado activo."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2022-01-10")

    page.goto(url_web)
    page.get_by_test_id(f"baja-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("empleado-fecha-baja").fill("2024-05-15")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.locator("section").get_by_test_id("mensaje-exito")).to_be_visible()
    expect(fila.get_by_test_id(f"estado-empleado-{empleado['id']}")).to_have_text("Baja")
    tabla = page.get_by_test_id("tabla-empleados")
    expect(tabla.get_by_test_id(f"fila-empleado-{empleado['id']}")).to_be_visible()


def test_cp06_no_editar_empleado_de_baja(page: Page, url_api: str, url_web: str) -> None:
    """CP-06: No se puede editar a un empleado que ya está dado de baja."""
    empleado = _crear_empleado(url_api)
    baja = httpx.patch(f"{url_api}/api/empleados/{empleado['id']}/baja", json={"fecha_baja": "2024-05-15"})
    assert baja.status_code == 200

    page.goto(url_web)
    page.get_by_test_id(f"editar-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("empleado-puesto").fill("Gerente")
    fila.get_by_test_id("empleado-guardar").click()

    mensaje_error = page.locator("section").get_by_test_id("mensaje-error")
    expect(mensaje_error).to_be_visible()
    expect(mensaje_error).to_have_text("No se puede editar a un empleado dado de baja")


def test_cp08_editar_puesto_invalido(page: Page, url_api: str, url_web: str) -> None:
    """CP-08: Editar con un puesto inválido responde con error."""
    empleado = _crear_empleado(url_api)

    page.goto(url_web)
    page.get_by_test_id(f"editar-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("empleado-puesto").fill("A")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.locator("section").get_by_test_id("mensaje-error")).to_be_visible()


@pytest.mark.skip(
    reason=(
        "CP-10: inalcanzable desde la UI porque el <select> de empleado-departamento "
        "solo ofrece los departamentos válidos (Tecnología, Ventas, Finanzas, Recursos "
        "Humanos, Operaciones); no existe opción 'Marketing' para seleccionar. "
        "Cubierto por el caso de API CP-09 (test_hu_03.py)."
    )
)
def test_cp10_editar_departamento_invalido(page: Page, url_api: str, url_web: str) -> None:
    """CP-10: Editar con un departamento que no está en la lista permitida responde con error."""


def test_cp12_baja_con_fecha_anterior_a_ingreso(page: Page, url_api: str, url_web: str) -> None:
    """CP-12: Dar de baja con una fecha de baja anterior a la fecha de ingreso responde con error."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2023-03-01")

    page.goto(url_web)
    page.get_by_test_id(f"baja-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("empleado-fecha-baja").fill("2023-02-15")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.locator("section").get_by_test_id("mensaje-error")).to_be_visible()


def test_cp14_baja_sin_fecha(page: Page, url_api: str, url_web: str) -> None:
    """CP-14: Dar de baja sin indicar la fecha de baja responde con error."""
    empleado = _crear_empleado(url_api)

    page.goto(url_web)
    page.get_by_test_id(f"baja-empleado-{empleado['id']}").click()

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.locator("section").get_by_test_id("mensaje-error")).to_be_visible()
