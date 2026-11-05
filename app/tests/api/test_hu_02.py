"""Pruebas de API para HU-02: consultar el directorio de empleados."""
import uuid

import httpx


def _crear_empleado(
    url_api: str,
    *,
    nombre: str,
    puesto: str,
    departamento: str,
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


def test_cp01_ver_directorio_completo(url_api: str) -> None:
    """CP-01: Ver el directorio completo con los datos principales."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")
    luis = _crear_empleado(url_api, nombre="Luis Gómez", puesto="Vendedor", departamento="Ventas")

    respuesta = httpx.get(f"{url_api}/api/empleados")

    assert respuesta.status_code == 200
    empleados = {e["id"]: e for e in respuesta.json()}

    encontrado_ana = empleados[ana["id"]]
    assert encontrado_ana["numero_empleado"] == ana["numero_empleado"]
    assert encontrado_ana["nombre"] == "Ana Pérez"
    assert encontrado_ana["puesto"] == "Analista"
    assert encontrado_ana["departamento"] == "Tecnología"
    assert encontrado_ana["estado"] == "activo"

    encontrado_luis = empleados[luis["id"]]
    assert encontrado_luis["numero_empleado"] == luis["numero_empleado"]
    assert encontrado_luis["nombre"] == "Luis Gómez"
    assert encontrado_luis["puesto"] == "Vendedor"
    assert encontrado_luis["departamento"] == "Ventas"
    assert encontrado_luis["estado"] == "activo"


def test_cp03_buscar_empleado_por_nombre(url_api: str) -> None:
    """CP-03: Buscar un empleado por nombre."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": "Ana Pérez"})

    assert respuesta.status_code == 200
    ids = [e["id"] for e in respuesta.json()]
    assert ana["id"] in ids
    [encontrado] = [e for e in respuesta.json() if e["id"] == ana["id"]]
    assert encontrado["nombre"] == "Ana Pérez"


def test_cp05_buscar_empleado_por_correo(url_api: str) -> None:
    """CP-05: Buscar un empleado por correo."""
    correo = f"carlos.ruiz.{uuid.uuid4().hex[:8]}@empresa.com"
    cuerpo = {
        "nombre": "Carlos Ruiz",
        "correo": correo,
        "puesto": "Contador",
        "departamento": "Finanzas",
        "fecha_ingreso": "2024-01-15",
    }
    creado = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert creado.status_code == 201
    carlos = creado.json()

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": correo})

    assert respuesta.status_code == 200
    ids = [e["id"] for e in respuesta.json()]
    assert carlos["id"] in ids


def test_cp07_busqueda_no_distingue_mayusculas(url_api: str) -> None:
    """CP-07: La búsqueda no distingue mayúsculas de minúsculas."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": "ANA PÉREZ"})

    assert respuesta.status_code == 200
    ids = [e["id"] for e in respuesta.json()]
    assert ana["id"] in ids


def test_cp09_filtrar_empleados_por_departamento(url_api: str) -> None:
    """CP-09: Filtrar empleados por departamento."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")
    luis = _crear_empleado(url_api, nombre="Luis Gómez", puesto="Vendedor", departamento="Ventas")

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"departamento": "Ventas"})

    assert respuesta.status_code == 200
    ids = [e["id"] for e in respuesta.json()]
    assert luis["id"] in ids
    assert ana["id"] not in ids


def test_cp11_buscar_termino_sin_coincidencias(url_api: str) -> None:
    """CP-11: Buscar un término que no coincide con ningún empleado."""
    termino = f"Zutano Inexistente {uuid.uuid4().hex}"

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": termino})

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_cp13_empleado_de_baja_sigue_en_directorio(url_api: str) -> None:
    """CP-13: Un empleado dado de baja sigue apareciendo en el directorio."""
    empleado = _crear_empleado(
        url_api, nombre="Diana Flores", puesto="Analista", departamento="Operaciones", fecha_ingreso="2024-01-01"
    )

    baja = httpx.patch(f"{url_api}/api/empleados/{empleado['id']}/baja", json={"fecha_baja": "2024-01-10"})
    assert baja.status_code == 200

    respuesta = httpx.get(f"{url_api}/api/empleados")

    assert respuesta.status_code == 200
    [encontrado] = [e for e in respuesta.json() if e["id"] == empleado["id"]]
    assert encontrado["estado"] == "baja"
    assert encontrado["fecha_baja"] == "2024-01-10"
