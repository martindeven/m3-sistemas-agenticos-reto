# language: es

Característica: Consultar el directorio de empleados
  Como persona del área de Recursos Humanos
  Quiero ver el directorio de empleados, buscarlos por nombre o correo y filtrarlos por departamento
  Para encontrar rápido a una persona

  Escenario: Ver el directorio completo con los datos principales
    Dado que existen los siguientes empleados registrados:
      | numero_empleado | nombre      | puesto      | departamento | estado |
      | EMP-0001        | Ana Pérez   | Analista    | Tecnología   | activo |
      | EMP-0002        | Luis Gómez  | Vendedor    | Ventas       | activo |
    Cuando la persona de Recursos Humanos abre el directorio
    Entonces ve una lista con número de empleado, nombre, puesto, departamento y estado
    Y ve en la lista al empleado "EMP-0001" "Ana Pérez" "Analista" "Tecnología" "activo"
    Y ve en la lista al empleado "EMP-0002" "Luis Gómez" "Vendedor" "Ventas" "activo"

  Escenario: Buscar un empleado por nombre
    Dado que existe el empleado "EMP-0001" con nombre "Ana Pérez" en el directorio
    Cuando la persona de Recursos Humanos busca "Ana"
    Entonces ve al empleado "EMP-0001" "Ana Pérez" en los resultados de la búsqueda

  Escenario: Buscar un empleado por correo
    Dado que existe el empleado "EMP-0003" con correo "carlos.ruiz@empresa.com" en el directorio
    Cuando la persona de Recursos Humanos busca "carlos.ruiz@empresa.com"
    Entonces ve al empleado "EMP-0003" en los resultados de la búsqueda

  Escenario: La búsqueda no distingue mayúsculas de minúsculas
    Dado que existe el empleado "EMP-0001" con nombre "Ana Pérez" en el directorio
    Cuando la persona de Recursos Humanos busca "ANA PÉREZ"
    Entonces ve al empleado "EMP-0001" "Ana Pérez" en los resultados de la búsqueda

  Escenario: Filtrar empleados por departamento
    Dado que existen los siguientes empleados registrados:
      | numero_empleado | nombre      | departamento |
      | EMP-0001        | Ana Pérez   | Tecnología   |
      | EMP-0002        | Luis Gómez  | Ventas       |
    Cuando la persona de Recursos Humanos filtra el directorio por el departamento "Ventas"
    Entonces ve únicamente al empleado "EMP-0002" "Luis Gómez" "Ventas" en los resultados
    Y no ve al empleado "EMP-0001" en los resultados

  Escenario: Buscar un término que no coincide con ningún empleado
    Dado que existen empleados registrados en el directorio
    Cuando la persona de Recursos Humanos busca "Zutano Inexistente"
    Entonces ve el mensaje "No se encontraron empleados"

  Escenario: Un empleado dado de baja sigue apareciendo en el directorio
    Dado que existe el empleado "EMP-0004" con estado "baja" y fecha_baja "2024-01-10" en el directorio
    Cuando la persona de Recursos Humanos abre el directorio
    Entonces ve al empleado "EMP-0004" con estado "baja" en la lista

# Preguntas abiertas
# - ¿La búsqueda hace coincidencia exacta o parcial sobre el correo? Se asumió coincidencia exacta por ser único.
# - ¿Se puede combinar la búsqueda por texto con el filtro de departamento al mismo tiempo?
# - ¿El directorio pagina los resultados? ¿Cuántos empleados se muestran por página?
# - ¿Existe un orden por defecto para la lista (alfabético, por número de empleado, por fecha de ingreso)?
