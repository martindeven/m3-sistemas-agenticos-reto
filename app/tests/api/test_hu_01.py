"""Pruebas de API para HU-01: registrar un empleado."""
import re
import uuid
from datetime import date, timedelta

import httpx


def test_cp01_registrar_empleado_datos_validos(url_api: str) -> None:
    """CP-01: Registrar un empleado con datos válidos."""
    correo = f"ana.torres.{uuid.uuid4().hex[:8]}@empresa.com"
    cuerpo = {
        "nombre": "Ana Torres",
        "correo": correo.upper(),
        "puesto": "Desarrolladora",
        "departamento": "Tecnología",
        "fecha_ingreso": "2024-01-15",
    }

    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)

    assert respuesta.status_code == 201
    creado = respuesta.json()
    assert re.fullmatch(r"EMP-\d{4}", creado["numero_empleado"])
    assert creado["correo"] == correo.lower()
    assert creado["estado"] == "activo"


def test_cp03_correo_ya_registrado(url_api: str) -> None:
    """CP-03: Intentar registrar un empleado con un correo ya registrado."""
    correo = f"ana.torres.{uuid.uuid4().hex[:8]}@empresa.com"
    primero = {
        "nombre": "Ana Torres",
        "correo": correo,
        "puesto": "Desarrolladora",
        "departamento": "Tecnología",
        "fecha_ingreso": "2024-01-15",
    }
    respuesta_1 = httpx.post(f"{url_api}/api/empleados", json=primero)
    assert respuesta_1.status_code == 201

    segundo = {
        "nombre": "Ana Torres",
        "correo": correo.upper(),
        "puesto": "Analista",
        "departamento": "Ventas",
        "fecha_ingreso": "2024-02-01",
    }
    respuesta_2 = httpx.post(f"{url_api}/api/empleados", json=segundo)

    assert respuesta_2.status_code == 409
    assert respuesta_2.json()["detail"] == "El correo ya está registrado"


def test_cp04_correo_no_corporativo(url_api: str) -> None:
    """CP-04: Intentar registrar un empleado con un correo que no es corporativo."""
    cuerpo = {
        "nombre": "Luis Pérez",
        "correo": f"luis.perez.{uuid.uuid4().hex[:8]}@gmail.com",
        "puesto": "Contador",
        "departamento": "Finanzas",
        "fecha_ingreso": "2024-03-01",
    }

    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Usa el correo corporativo @empresa.com"


def test_cp05_fecha_ingreso_futura(url_api: str) -> None:
    """CP-05: Intentar registrar un empleado con una fecha de ingreso futura."""
    fecha_futura = (date.today() + timedelta(days=30)).isoformat()
    cuerpo = {
        "nombre": "Marta Ruiz",
        "correo": f"marta.ruiz.{uuid.uuid4().hex[:8]}@empresa.com",
        "puesto": "Gerente",
        "departamento": "Operaciones",
        "fecha_ingreso": fecha_futura,
    }

    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "La fecha de ingreso no puede ser futura"


def test_cp06_departamento_invalido(url_api: str) -> None:
    """CP-06: Intentar registrar un empleado con un departamento que no está en la lista permitida."""
    cuerpo = {
        "nombre": "Carlos Díaz",
        "correo": f"carlos.diaz.{uuid.uuid4().hex[:8]}@empresa.com",
        "puesto": "Supervisor",
        "departamento": "Marketing",
        "fecha_ingreso": "2024-01-10",
    }

    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)

    assert respuesta.status_code == 422
