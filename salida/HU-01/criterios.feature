# language: es
Característica: Registrar empleado
  Como persona del área de Recursos Humanos
  quiero registrar a un empleado con su nombre, correo corporativo, puesto, departamento y fecha de ingreso
  para darlo de alta en la empresa

  Escenario: Registrar un empleado con datos válidos
    Dado que no existen empleados registrados previamente
    Cuando registro un empleado con nombre "Ana Torres", correo "ANA.TORRES@EMPRESA.COM", puesto "Desarrolladora", departamento "Tecnología" y fecha de ingreso "2024-01-15"
    Entonces el sistema responde con código 201
    Y el empleado queda registrado con numero_empleado "EMP-0001"
    Y el correo se guarda como "ana.torres@empresa.com"
    Y el estado del empleado es "activo"
    Y la pantalla muestra un mensaje de confirmación que incluye el número de empleado "EMP-0001"

  Escenario: Intentar registrar un empleado con un correo ya registrado
    Dado que existe un empleado registrado con correo "ana.torres@empresa.com"
    Cuando registro un empleado con nombre "Ana Torres", correo "Ana.Torres@empresa.com", puesto "Analista", departamento "Ventas" y fecha de ingreso "2024-02-01"
    Entonces el sistema responde con código 409
    Y el mensaje de error es "El correo ya está registrado"

  Escenario: Intentar registrar un empleado con un correo que no es corporativo
    Dado que no existen empleados registrados previamente
    Cuando registro un empleado con nombre "Luis Pérez", correo "luis.perez@gmail.com", puesto "Contador", departamento "Finanzas" y fecha de ingreso "2024-03-01"
    Entonces el sistema responde con código 422
    Y el mensaje de error es "Usa el correo corporativo @empresa.com"

  Escenario: Intentar registrar un empleado con una fecha de ingreso futura
    Dado que la fecha actual del sistema es "2024-05-10"
    Cuando registro un empleado con nombre "Marta Ruiz", correo "marta.ruiz@empresa.com", puesto "Gerente", departamento "Operaciones" y fecha de ingreso "2024-06-01"
    Entonces el sistema responde con código 422
    Y el mensaje de error es "La fecha de ingreso no puede ser futura"

  Escenario: Intentar registrar un empleado con un departamento que no está en la lista permitida
    Dado que no existen empleados registrados previamente
    Cuando registro un empleado con nombre "Carlos Díaz", correo "carlos.diaz@empresa.com", puesto "Supervisor", departamento "Marketing" y fecha de ingreso "2024-01-10"
    Entonces el sistema responde con código 422
    Y la pantalla indica que el campo "departamento" debe corregirse

# Preguntas abiertas
# - ¿Cuál es el texto exacto del mensaje de confirmación mostrado tras el registro exitoso? (el PO solo indica que debe incluir el número asignado)
# - ¿Cuál es el mensaje exacto que debe mostrarse en pantalla cuando el campo inválido es "nombre" o "puesto" (longitud fuera de rango)? Se usó "departamento" como ejemplo de la regla general (regla 3), pero no hay texto definido para cada campo.
