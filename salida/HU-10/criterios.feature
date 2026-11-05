# language: es
# HU-10 · Solicitar vacaciones
# Fuente: historias/HU-10-solicitar-vacaciones.md, contexto/reglas_vacaciones.md,
# contexto/convenciones_vacaciones.md (sección de convenciones_app.md)

Característica: Solicitar vacaciones

  # Camino feliz: solicitud válida, sin festivos ni fines de semana en el periodo,
  # sin uso previo en el año. Ejemplo tomado de reglas_vacaciones.md (Regla 2).
  Escenario: Registrar una solicitud de vacaciones válida
    Dado un empleado activo con id 7 y fecha_ingreso "2024-01-15"
    Cuando solicito vacaciones para el empleado 7 del "2026-07-06" al "2026-07-10"
    Entonces la respuesta tiene código 201
    Y el campo "dias_habiles" vale 5
    Y el campo "dias_restantes" vale 7
    Y el campo "dias_disponibles" vale 7

  # --- Errores: mensajes exactos de contexto/convenciones_vacaciones.md ---

  Escenario: Rechazar la solicitud cuando el empleado no existe
    Dado que no existe ningún empleado con id 9999
    Cuando solicito vacaciones para el empleado 9999 del "2026-07-06" al "2026-07-10"
    Entonces la respuesta tiene código 404
    Y el campo "detail" vale "Empleado no encontrado"

  Escenario: Rechazar la solicitud cuando el empleado está dado de baja
    Dado un empleado con id 8, fecha_ingreso "2023-01-10" y estado "baja"
    Cuando solicito vacaciones para el empleado 8 del "2026-07-06" al "2026-07-10"
    Entonces la respuesta tiene código 409
    Y el campo "detail" vale "No se pueden solicitar vacaciones para un empleado dado de baja"

  Escenario: Rechazar la solicitud cuando la fecha de fin es anterior a la de inicio
    Dado un empleado activo con id 9 y fecha_ingreso "2024-01-15"
    Cuando solicito vacaciones para el empleado 9 del "2026-07-10" al "2026-07-05"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "La fecha de fin no puede ser anterior a la fecha de inicio"

  Escenario: Rechazar la solicitud cuando el periodo cruza de un año a otro
    Dado un empleado activo con id 10 y fecha_ingreso "2024-01-15"
    Cuando solicito vacaciones para el empleado 10 del "2026-12-28" al "2027-01-08"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "Las vacaciones deben estar dentro de un mismo año calendario"

  Escenario: Rechazar la solicitud cuando el año no está en la tabla de festivos
    Dado un empleado activo con id 11 y fecha_ingreso "2024-01-01"
    Cuando solicito vacaciones para el empleado 11 del "2028-07-10" al "2028-07-14"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "Solo se pueden solicitar vacaciones en 2026 y 2027"

  Escenario: Rechazar la solicitud por antigüedad insuficiente
    Dado un empleado activo con id 12 y fecha_ingreso "2025-12-21"
    Cuando solicito vacaciones para el empleado 12 del "2026-12-18" al "2026-12-18"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "Se requiere al menos un año de antigüedad a la fecha de inicio"

  # Límite: "periodo solo de fin de semana" (cubre también Regla 3: sin días hábiles)
  Escenario: Rechazar un periodo solo de fin de semana porque no incluye días hábiles
    Dado un empleado activo con id 13 y fecha_ingreso "2024-01-15"
    Cuando solicito vacaciones para el empleado 13 del "2026-07-11" al "2026-07-12"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "El periodo no incluye días hábiles"

  Escenario: Rechazar la solicitud cuando rebasa los días disponibles del año
    Dado un empleado activo con id 14 y fecha_ingreso "2024-01-15"
    Y el empleado 14 ya registró una solicitud de vacaciones del "2026-09-14" al "2026-09-18" con 4 días hábiles
    Cuando solicito vacaciones para el empleado 14 del "2026-10-05" al "2026-10-15"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "La solicitud excede los días disponibles: quedan 8 días hábiles"

  # --- Límites explícitos pedidos para HU-10 ---

  Escenario: Límite exacto: se usan justo los días que quedan y quedan 0
    Dado un empleado activo con id 15 y fecha_ingreso "2024-01-15"
    Y el empleado 15 ya registró una solicitud de vacaciones del "2026-07-06" al "2026-07-10" con 5 días hábiles
    Cuando solicito vacaciones para el empleado 15 del "2026-07-13" al "2026-07-21"
    Entonces la respuesta tiene código 201
    Y el campo "dias_habiles" vale 7
    Y el campo "dias_restantes" vale 0
    Y el campo "dias_disponibles" vale 0

  Escenario: Excede por uno: se pide un día más de los que quedan y se rechaza
    Dado un empleado activo con id 16 y fecha_ingreso "2024-01-15"
    Y el empleado 16 ya registró una solicitud de vacaciones del "2026-07-06" al "2026-07-10" con 5 días hábiles
    Cuando solicito vacaciones para el empleado 16 del "2026-08-03" al "2026-08-12"
    Entonces la respuesta tiene código 400
    Y el campo "detail" vale "La solicitud excede los días disponibles: quedan 7 días hábiles"

  Escenario: Primer día de antigüedad: la fecha de inicio es justo el aniversario de ingreso
    Dado un empleado activo con id 17 y fecha_ingreso "2025-12-21"
    Cuando solicito vacaciones para el empleado 17 del "2026-12-21" al "2026-12-21"
    Entonces la respuesta tiene código 201
    Y el campo "dias_habiles" vale 1
    Y el campo "dias_restantes" vale 11

  Escenario: Un periodo que incluye un festivo no descuenta ese día
    Dado un empleado activo con id 18 y fecha_ingreso "2024-01-15"
    Cuando solicito vacaciones para el empleado 18 del "2026-12-21" al "2026-12-31"
    Entonces la respuesta tiene código 201
    Y el campo "dias_habiles" vale 8
    Y el campo "dias_restantes" vale 4

# Preguntas abiertas
# - No se encontró en la documentación el endpoint exacto para dar de baja a un
#   empleado (HU-03). El escenario "empleado dado de baja" asume que ese estado
#   ya existe como precondición, preparado con la API correspondiente.
# - No se detalla qué pasa si "fecha_inicio" o "fecha_fin" llegan en un formato
#   distinto a YYYY-MM-DD más allá del 422 automático de FastAPI; por eso no se
#   agregó un escenario con mensaje propio para ese caso, tal como indica
#   contexto/convenciones_vacaciones.md.
