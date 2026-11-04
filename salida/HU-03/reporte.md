# Reporte · HU-03

**Estado:** ESCALAR A UNA PERSONA
**Costo de agentes:** 2.37 USD
**Ciclos de corrección:** 2

## Bitácora
- Filtro de historia: OK
- Criterios escritos en criterios.feature
- Preguntas abiertas: la persona respondió 'si'
- Casos de prueba escritos en casos_prueba.json
- Plan aprobado por una persona
- Construcción 1
- Verificación: OK
- Pruebas automatizadas: OK (14 casos)
- Despliegue: OK
- Despliegue y pruebas listos
- Pruebas E2E: 5 failed, 23 passed, 1 warning in 39.41s
- Triage → despliegue: La base de datos SQLite está en modo solo lectura ("attempt to write a readonly database"), lo que impide ejecutar la operación de dar de baja (escritura). Esto ocurre tanto en la prueba API como en la E2E equivalente, indicando un problema de infraestructura/entorno (permisos de archivo o contenedor con filesystem readonly) y no un defecto de lógica de negocio ni de la prueba.
- Despliegue corregido
- Pruebas E2E: 5 failed, 23 passed, 1 warning in 38.91s
- Triage → despliegue: La base de datos SQLite está en modo solo lectura, impidiendo escribir el cambio de estado a "baja" (sqlite3.OperationalError: attempt to write a readonly database). Esto afecta tanto a la prueba API como a la E2E del mismo caso, indicando un problema de infraestructura/entorno de despliegue (permisos de archivo o volumen montado como read-only), no de la lógica de negocio ni de la prueba.
- Despliegue corregido
- Pruebas E2E: 5 failed, 23 passed, 1 warning in 38.93s

## Última ejecución de pruebas
```
5 failed, 23 passed, 1 warning in 38.93s
- tests.api.test_hu_02::test_cp13_empleado_baja_sigue_en_directorio
  sqlite3.OperationalError: attempt to write a readonly database
- tests.api.test_hu_03::test_cp13_dar_de_baja_sin_fecha_baja
  AssertionError: assert 'fecha_baja' in 'Input should be a valid date or datetime, input is too short'
- tests.e2e.test_hu_02_e2e::test_cp14_empleado_baja_sigue_en_directorio[chromium]
  sqlite3.OperationalError: attempt to write a readonly database
- tests.e2e.test_hu_03_e2e::test_cp10_editar_con_departamento_no_permitido[chromium]
  playwright._impl._errors.TimeoutError: Locator.select_option: Timeout 30000ms exceeded.
Call log:
  - waiting for get_by_test_id("fila-empleado-28").get_by_test_id("empleado-departamento")
    - locator resolved to <select data-testid="empleado-departamento">…</select>
  - attempting select option action
    2 × waiting for element to be visible and enabled
      - did not find some options
    - 
- tests.e2e.test_hu_03_e2e::test_cp14_dar_de_baja_sin_fecha_baja[chromium]
  AssertionError: Locator expected to contain text 'fecha_baja'
Actual value: Input should be a valid date or datetime, input is too short 
Call log:
  - Expect "to_contain_text" get_by_test_id("mensaje-error") with timeout 5000ms
  - waiting for get_by_test_id("mensaje-error")
    13 × locator resolved to <p data-testid="mensaje-error">Input should be a valid date or datetime, input i…</p>
       -
```