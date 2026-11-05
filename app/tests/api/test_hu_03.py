"""Pruebas de API para HU-03: editar y dar de baja a un empleado."""
import uuid

import httpx


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


def test_cp01_editar_puesto_y_departamento(url_api: str) -> None:
    """CP-01: Editar correctamente el puesto y el departamento de un empleado activo."""
    empleado = _crear_empleado(url_api, puesto="Analista", departamento="Ventas")

    respuesta = httpx.put(
        f"{url_api}/api/empleados/{empleado['id']}",
        json={"puesto": "Analista Senior", "departamento": "Tecnología"},
    )

    assert respuesta.status_code == 200
    actualizado = respuesta.json()
    assert actualizado["puesto"] == "Analista Senior"
    assert actualizado["departamento"] == "Tecnología"
    assert actualizado["correo"] == empleado["correo"]
    assert actualizado["numero_empleado"] == empleado["numero_empleado"]


def test_cp03_dar_de_baja_empleado_activo(url_api: str) -> None:
    """CP-03: Dar de baja correctamente a un empleado activo."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2022-01-10")

    respuesta = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": "2024-05-15"},
    )

    assert respuesta.status_code == 200
    actualizado = respuesta.json()
    assert actualizado["estado"] == "baja"
    assert actualizado["fecha_baja"] == "2024-05-15"

    directorio = httpx.get(f"{url_api}/api/empleados")
    assert directorio.status_code == 200
    assert empleado["id"] in [e["id"] for e in directorio.json()]


def test_cp05_no_editar_empleado_de_baja(url_api: str) -> None:
    """CP-05: No se puede editar a un empleado que ya está dado de baja."""
    empleado = _crear_empleado(url_api)
    baja = httpx.patch(f"{url_api}/api/empleados/{empleado['id']}/baja", json={"fecha_baja": "2024-05-15"})
    assert baja.status_code == 200

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"puesto": "Gerente"})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No se puede editar a un empleado dado de baja"


def test_cp07_editar_puesto_invalido(url_api: str) -> None:
    """CP-07: Editar con un puesto inválido responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"puesto": "A"})

    assert respuesta.status_code == 422


def test_cp09_editar_departamento_invalido(url_api: str) -> None:
    """CP-09: Editar con un departamento que no está en la lista permitida responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"departamento": "Marketing"})

    assert respuesta.status_code == 422


def test_cp11_baja_con_fecha_anterior_a_ingreso(url_api: str) -> None:
    """CP-11: Dar de baja con una fecha de baja anterior a la fecha de ingreso responde 422."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2023-03-01")

    respuesta = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": "2023-02-15"},
    )

    assert respuesta.status_code == 422


def test_cp13_baja_sin_fecha(url_api: str) -> None:
    """CP-13: Dar de baja sin indicar la fecha de baja responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.patch(f"{url_api}/api/empleados/{empleado['id']}/baja", json={"fecha_baja": ""})

    assert respuesta.status_code == 422
