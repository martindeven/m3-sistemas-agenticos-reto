"""API de gestión de empleados."""
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, obtener_db
from models import Empleado
from schemas import (
    DEPARTAMENTOS_VALIDOS,
    EmpleadoActualizar,
    EmpleadoBaja,
    EmpleadoCrear,
    EmpleadoSalida,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestión de empleados")


@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    mensaje = exc.errors()[0].get("msg", "Datos inválidos")
    prefijo = "Value error, "
    if mensaje.startswith(prefijo):
        mensaje = mensaje[len(prefijo):]
    return JSONResponse(status_code=422, content={"detail": mensaje})


@app.get("/api/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


@app.get("/api/departamentos")
def departamentos() -> list[str]:
    return DEPARTAMENTOS_VALIDOS


@app.get("/api/empleados", response_model=list[EmpleadoSalida])
def listar_empleados(
    busqueda: str | None = Query(default=None),
    departamento: str | None = Query(default=None),
    db: Session = Depends(obtener_db),
) -> list[Empleado]:
    consulta = select(Empleado)
    if busqueda:
        patron = f"%{busqueda.lower()}%"
        consulta = consulta.where(
            or_(func.lower(Empleado.nombre).like(patron), func.lower(Empleado.correo).like(patron))
        )
    if departamento:
        consulta = consulta.where(Empleado.departamento == departamento)
    return list(db.scalars(consulta.order_by(Empleado.id)).all())


def generar_numero_empleado(db: Session) -> str:
    ultimo_id = db.scalar(select(Empleado.id).order_by(Empleado.id.desc()))
    return f"EMP-{(ultimo_id or 0) + 1:04d}"


@app.post("/api/empleados", response_model=EmpleadoSalida, status_code=201)
def crear_empleado(datos: EmpleadoCrear, db: Session = Depends(obtener_db)) -> Empleado:
    empleado = Empleado(
        numero_empleado=generar_numero_empleado(db),
        nombre=datos.nombre,
        correo=datos.correo,
        puesto=datos.puesto,
        departamento=datos.departamento,
        fecha_ingreso=datos.fecha_ingreso,
        estado="activo",
    )
    db.add(empleado)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    db.refresh(empleado)
    return empleado


def obtener_empleado_o_404(id_empleado: int, db: Session) -> Empleado:
    empleado = db.get(Empleado, id_empleado)
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado


@app.put("/api/empleados/{id_empleado}", response_model=EmpleadoSalida)
def editar_empleado(id_empleado: int, datos: EmpleadoActualizar, db: Session = Depends(obtener_db)) -> Empleado:
    empleado = obtener_empleado_o_404(id_empleado, db)
    if empleado.estado == "baja":
        raise HTTPException(status_code=409, detail="No se puede editar a un empleado dado de baja")
    if datos.puesto is not None:
        empleado.puesto = datos.puesto
    if datos.departamento is not None:
        empleado.departamento = datos.departamento
    db.commit()
    db.refresh(empleado)
    return empleado


@app.patch("/api/empleados/{id_empleado}/baja", response_model=EmpleadoSalida)
def dar_de_baja_empleado(id_empleado: int, datos: EmpleadoBaja, db: Session = Depends(obtener_db)) -> Empleado:
    empleado = obtener_empleado_o_404(id_empleado, db)
    if datos.fecha_baja < empleado.fecha_ingreso:
        raise HTTPException(
            status_code=422,
            detail="El campo 'fecha_baja' debe corregirse: no puede ser anterior a la fecha de ingreso",
        )
    empleado.estado = "baja"
    empleado.fecha_baja = datos.fecha_baja
    db.commit()
    db.refresh(empleado)
    return empleado
