"""Pruebas de API para HU-03: editar y dar de baja a un empleado."""
import uuid
from datetime import date

import httpx


def _correo_unico(prefijo: str) -> str:
    return f"{prefijo}.{uuid.uuid4().hex[:8]}@empresa.com"


def _crear_empleado(url_api: str, **datos) -> dict:
    cuerpo = {
        "nombre": "Empleado de prueba",
        "correo": _correo_unico("empleado"),
        "puesto": "Puesto de prueba",
        "departamento": "Tecnología",
        "fecha_ingreso": date.today().isoformat(),
    }
    cuerpo.update(datos)
    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()


def _dar_de_baja(url_api: str, empleado_id: int, fecha_baja: str) -> dict:
    respuesta = httpx.patch(f"{url_api}/api/empleados/{empleado_id}/baja", json={"fecha_baja": fecha_baja})
    assert respuesta.status_code == 200
    return respuesta.json()


def test_cp01_editar_puesto_y_departamento_empleado_activo(url_api: str) -> None:
    """CP-01: Editar correctamente el puesto y el departamento de un empleado activo."""
    correo = _correo_unico("ana.lopez")
    empleado = _crear_empleado(
        url_api,
        nombre="Ana López",
        correo=correo,
        puesto="Analista",
        departamento="Ventas",
    )

    respuesta = httpx.put(
        f"{url_api}/api/empleados/{empleado['id']}",
        json={"puesto": "Analista Senior", "departamento": "Tecnología"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["puesto"] == "Analista Senior"
    assert cuerpo["departamento"] == "Tecnología"
    assert cuerpo["correo"] == correo
    assert cuerpo["numero_empleado"] == empleado["numero_empleado"]


def test_cp03_dar_de_baja_empleado_activo(url_api: str) -> None:
    """CP-03: Dar de baja correctamente a un empleado activo."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2022-01-10")

    respuesta = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": "2024-05-15"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "baja"
    assert cuerpo["fecha_baja"] == "2024-05-15"

    directorio = httpx.get(f"{url_api}/api/empleados")
    assert directorio.status_code == 200
    ids = [e["id"] for e in directorio.json()]
    assert empleado["id"] in ids


def test_cp05_no_editar_empleado_dado_de_baja(url_api: str) -> None:
    """CP-05: No se puede editar a un empleado que ya está dado de baja."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2020-01-01")
    _dar_de_baja(url_api, empleado["id"], "2024-01-10")

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"puesto": "Gerente"})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No se puede editar a un empleado dado de baja"


def test_cp07_editar_con_puesto_invalido(url_api: str) -> None:
    """CP-07: Editar con un puesto inválido responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"puesto": "A"})

    assert respuesta.status_code == 422
    assert "puesto" in respuesta.json()["detail"]


def test_cp09_editar_con_departamento_no_permitido(url_api: str) -> None:
    """CP-09: Editar con un departamento que no está en la lista permitida responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.put(f"{url_api}/api/empleados/{empleado['id']}", json={"departamento": "Marketing"})

    assert respuesta.status_code == 422
    assert "departamento" in respuesta.json()["detail"]


def test_cp11_dar_de_baja_con_fecha_anterior_a_ingreso(url_api: str) -> None:
    """CP-11: Dar de baja con una fecha de baja anterior a la fecha de ingreso responde 422."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2023-03-01")

    respuesta = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": "2023-02-15"},
    )

    assert respuesta.status_code == 422
    assert "fecha_baja" in respuesta.json()["detail"]


def test_cp13_dar_de_baja_sin_fecha_baja(url_api: str) -> None:
    """CP-13: Dar de baja sin indicar la fecha de baja responde 422."""
    empleado = _crear_empleado(url_api)

    respuesta = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": ""},
    )

    assert respuesta.status_code == 422
    assert "fecha_baja" in respuesta.json()["detail"]
