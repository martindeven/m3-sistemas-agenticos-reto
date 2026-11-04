# language: es

Característica: Editar y dar de baja a un empleado
  Como persona del área de Recursos Humanos
  quiero cambiar el puesto y el departamento de un empleado, y poder darlo de baja
  para mantener el directorio al día sin perder el historial

  Escenario: Editar correctamente el puesto y el departamento de un empleado activo
    Dado un empleado con numero_empleado "EMP-0007", correo "ana.lopez@empresa.com", puesto "Analista", departamento "Ventas" y estado "activo"
    Cuando edito el empleado "EMP-0007" con puesto "Analista Senior" y departamento "Tecnología"
    Entonces el sistema responde 200
    Y el empleado "EMP-0007" tiene puesto "Analista Senior"
    Y el empleado "EMP-0007" tiene departamento "Tecnología"
    Y el correo del empleado "EMP-0007" sigue siendo "ana.lopez@empresa.com"
    Y el numero_empleado del empleado sigue siendo "EMP-0007"

  Escenario: Dar de baja correctamente a un empleado activo
    Dado un empleado con numero_empleado "EMP-0007", estado "activo" y fecha_ingreso "2022-01-10"
    Cuando doy de baja al empleado "EMP-0007" con fecha_baja "2024-05-15"
    Entonces el sistema responde 200
    Y el empleado "EMP-0007" tiene estado "baja"
    Y el empleado "EMP-0007" tiene fecha_baja "2024-05-15"
    Y el empleado "EMP-0007" sigue apareciendo en el directorio

  Escenario: No se puede editar a un empleado que ya está dado de baja
    Dado un empleado con numero_empleado "EMP-0008" y estado "baja"
    Cuando intento editar el empleado "EMP-0008" con puesto "Gerente"
    Entonces el sistema responde 409
    Y el mensaje es "No se puede editar a un empleado dado de baja"

  Esquema del escenario: Editar con un puesto inválido responde 422
    Dado un empleado activo con numero_empleado "EMP-0009"
    Cuando edito el empleado "EMP-0009" con puesto "<puesto>"
    Entonces el sistema responde 422
    Y la pantalla indica que el campo "puesto" debe corregirse

    Ejemplos:
      | puesto |
      | A      |

  Escenario: Editar con un departamento que no está en la lista permitida responde 422
    Dado un empleado activo con numero_empleado "EMP-0010"
    Cuando edito el empleado "EMP-0010" con departamento "Marketing"
    Entonces el sistema responde 422
    Y la pantalla indica que el campo "departamento" debe corregirse

  Escenario: Dar de baja con una fecha de baja anterior a la fecha de ingreso responde 422
    Dado un empleado activo con numero_empleado "EMP-0011" y fecha_ingreso "2023-03-01"
    Cuando doy de baja al empleado "EMP-0011" con fecha_baja "2023-02-15"
    Entonces el sistema responde 422
    Y la pantalla indica que el campo "fecha_baja" debe corregirse

  Escenario: Dar de baja sin indicar la fecha de baja responde 422
    Dado un empleado activo con numero_empleado "EMP-0012"
    Cuando doy de baja al empleado "EMP-0012" sin indicar fecha_baja
    Entonces el sistema responde 422
    Y la pantalla indica que el campo "fecha_baja" debe corregirse

# Preguntas abiertas
# - ¿Qué debe hacer el sistema si en una edición se envían valores distintos para numero_empleado o correo? ¿Se ignoran esos campos o se rechaza toda la petición, y con qué código/mensaje?
# - ¿Se puede intentar dar de baja a un empleado que ya está en estado "baja"? ¿Qué código y mensaje debe responder el sistema en ese caso?
# - ¿Se puede editar la fecha_ingreso de un empleado? La historia solo menciona puesto y departamento como editables; se asumió que fecha_ingreso no es editable en esta HU.
