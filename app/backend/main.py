"""API de gestión de empleados."""
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, obtener_db
from models import Empleado, Vacacion
from schemas import (
    DEPARTAMENTOS_VALIDOS,
    EmpleadoActualizar,
    EmpleadoBaja,
    EmpleadoCrear,
    EmpleadoSalida,
    SaldoVacaciones,
    VacacionCrear,
    VacacionRespuesta,
)
from vacaciones import FESTIVOS, calcular_dias_habiles, dias_usados_en_anio, fecha_aniversario

TOPE_ANUAL_DIAS = 12

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


@app.post("/api/empleados/{id_empleado}/vacaciones", response_model=VacacionRespuesta, status_code=201)
def solicitar_vacaciones(
    id_empleado: int, datos: VacacionCrear, db: Session = Depends(obtener_db)
) -> VacacionRespuesta:
    empleado = obtener_empleado_o_404(id_empleado, db)
    if empleado.estado == "baja":
        raise HTTPException(
            status_code=409,
            detail="No se pueden solicitar vacaciones para un empleado dado de baja",
        )
    if datos.fecha_fin < datos.fecha_inicio:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio",
        )
    if datos.fecha_inicio.year != datos.fecha_fin.year:
        raise HTTPException(
            status_code=400,
            detail="Las vacaciones deben estar dentro de un mismo año calendario",
        )
    anio = datos.fecha_inicio.year
    if anio not in FESTIVOS:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden solicitar vacaciones en 2026 y 2027",
        )
    if datos.fecha_inicio < fecha_aniversario(empleado.fecha_ingreso):
        raise HTTPException(
            status_code=400,
            detail="Se requiere al menos un año de antigüedad a la fecha de inicio",
        )
    dias_habiles = calcular_dias_habiles(datos.fecha_inicio, datos.fecha_fin)
    if dias_habiles == 0:
        raise HTTPException(status_code=400, detail="El periodo no incluye días hábiles")
    dias_usados = dias_usados_en_anio(db, id_empleado, anio)
    dias_disponibles_antes = TOPE_ANUAL_DIAS - dias_usados
    if dias_habiles > dias_disponibles_antes:
        raise HTTPException(
            status_code=400,
            detail=f"La solicitud excede los días disponibles: quedan {dias_disponibles_antes} días hábiles",
        )

    vacacion = Vacacion(
        empleado_id=id_empleado,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        dias_habiles=dias_habiles,
    )
    db.add(vacacion)
    db.commit()
    db.refresh(vacacion)

    dias_restantes = dias_disponibles_antes - dias_habiles
    return VacacionRespuesta(
        id=vacacion.id,
        empleado_id=vacacion.empleado_id,
        fecha_inicio=vacacion.fecha_inicio,
        fecha_fin=vacacion.fecha_fin,
        dias_habiles=vacacion.dias_habiles,
        dias_restantes=dias_restantes,
        dias_disponibles=dias_restantes,
    )


@app.get("/api/empleados/{id_empleado}/vacaciones", response_model=SaldoVacaciones)
def consultar_vacaciones(
    id_empleado: int, anio: int | None = Query(default=None), db: Session = Depends(obtener_db)
) -> SaldoVacaciones:
    obtener_empleado_o_404(id_empleado, db)
    anio_consulta = anio or date.today().year

    solicitudes = list(
        db.scalars(
            select(Vacacion)
            .where(Vacacion.empleado_id == id_empleado)
            .where(Vacacion.fecha_inicio >= date(anio_consulta, 1, 1))
            .where(Vacacion.fecha_inicio <= date(anio_consulta, 12, 31))
            .order_by(Vacacion.fecha_inicio)
        ).all()
    )
    dias_usados = sum(s.dias_habiles for s in solicitudes)

    return SaldoVacaciones(
        empleado_id=id_empleado,
        anio=anio_consulta,
        dias_por_anio=TOPE_ANUAL_DIAS,
        dias_usados=dias_usados,
        dias_disponibles=TOPE_ANUAL_DIAS - dias_usados,
        solicitudes=solicitudes,
    )
