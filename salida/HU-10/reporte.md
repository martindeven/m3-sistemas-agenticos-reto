# Reporte · HU-10

**Estado:** LISTA
**Costo de agentes:** 1.84 USD
**Ciclos de corrección:** 0

## Bitácora
- [11:13:32] Filtro de historia: OK
- [11:15:36] Criterios escritos en criterios.feature
- [11:25:29] Preguntas abiertas: la persona respondió 'si'
- [11:32:34] Casos de prueba escritos en casos_prueba.json
- [11:35:07] Plan rechazado: Buen plan; ajusta 4 cosas sin cambiar lo demás: (1) después de un POST 201, vuelve a pedir el GET y actualiza vacaciones-disponibles y tabla-vacaciones; (2) solo puede haber un panel de vacaciones abierto a la vez en el directorio (el estado del empleado abierto vive en DirectorioEmpleados), para que vacaciones-fecha-inicio, vacaciones-mensaje, etc. no se dupliquen; (3) si FilaEmpleado es un <tr>, el panel va dentro de un <td colSpan> o en una fila aparte, nunca un div directo en el tr; (4) muestra el botón solo si empleado.estado === 'activo'. No cambies el comportamiento de HU-01 a HU-03.
- [11:36:47] Plan aprobado por una persona
- [11:40:32] Construcción 1
- [11:40:34] Verificación: OK
- [11:42:52] Pruebas automatizadas: OK (24 casos)
- [11:41:12] Despliegue: OK
- [11:42:52] Despliegue y pruebas listos
- [11:43:02] Pruebas E2E: 57 passed, 2 skipped, 1 warning in 8.93s

## Última ejecución de pruebas
```
57 passed, 2 skipped, 1 warning in 8.93s
Pruebas de HU-10: 24 (0 fallan) · Regresión: 35 (0 fallan)

```