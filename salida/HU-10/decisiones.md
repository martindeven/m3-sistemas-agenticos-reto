# Decisiones · HU-10 Solicitar vacaciones

Ejecución final: hilo `HU-10-solicitar-vacaciones-20261105-1113`. Estado **LISTA**: 57 pruebas pasan, 2 se omiten con motivo, 0 ciclos de corrección y 1.84 USD (`reporte.md`, `historial_estados.md`).

**1. ¿Qué es workflow y qué es agente?** El orden de las etapas es un **workflow**: lo fija el grafo de `flujo_s4.py` y es el mismo para cualquier historia. También son workflow, porque los decide el código, `verificar`, `pruebas_e2e`, el reporte y cada `despues_de_*`. Por ejemplo, `despues_de_filtrar` mandó HU-10 a `analizar` y HU-99 a `fin`. Son **agentes** analista, diseñador, desarrollador, despliegue y automatizador: deciden qué leer, qué herramienta usar y cuántas veces. El analista, por ejemplo, leyó 6 archivos en 2 pasos y escribió en el 3.º (`evidencias/ejecucion_HU-10.log`). `filtrar_historia` y `triage` hacen una sola llamada estructurada a un LLM, sin bucle: clasifican y el código enruta.

**2. ¿Cómo se validó cada salida?**
- **Criterios:** `validar_gherkin` con los 8 `detail` de `convenciones_vacaciones.md`, un escenario por mensaje, el camino feliz y los límites («límite exacto», «excede por uno», «primer día de antigüedad»). Pasó en el intento 1 con 13 escenarios.
- **Casos:** `validar_plan` exige cada mensaje en algún `resultado_esperado`, los 6 data-testid en los casos e2e y `fecha_ingreso`/`fecha_inicio`/`fecha_fin` en `datos`. Quedaron 24 casos (13 de API y 11 e2e). Después de reanudar, pasó en el intento 1.
- **Código:** `verificar_app` (salud de la API y `npm run build`), OK en la construcción 1.
- **Despliegue:** `verificar_despliegue`, puertos 8000 y 8080.
- **Pruebas:** `verificar_pruebas_escritas`, que busca cada id solo en los archivos de la historia. Lo que atrapó: al acotar esa búsqueda se vio que HU-01 no tenía ningún archivo de prueba. Antes, el `CP-xx` de otra historia lo daba por cubierto.
- **Corte por tamaño:** el bucle de `base.py` cortó al diseñador con `max_tokens` en lugar de dejar pasar un JSON incompleto (log, línea 28).

**3. ¿Dónde intervine como persona?**
- **Preguntas abiertas:** respondí «si» (11:25:29). El endpoint de baja existe (`PATCH /api/empleados/{id}/baja`) y el 422 de formato ya lo cubrían las convenciones.
- **Plan:** me detuve a analizarlo y vi que tenía detalles, así que probé con otra iteración. Rechacé la versión 1 (11:35:07) pidiendo 4 cambios: refrescar el saldo después del POST, un solo panel abierto, el panel fuera del `<tr>` y el botón solo para empleados con estado `activo`. La versión 2 los incorporó y la aprobé (11:36:47, `plan.md`).
- **El corte por `max_tokens`:** fue lo que más me costó. La limitación de max_tokens detuvo el proceso en su momento, y tocó revisar el diseñador y hacerlo por lotes. Luego reanudé el hilo con `REANUDAR`, sin repetir el análisis ni las preguntas (checkpoints 5 y 6).

**4. ¿Qué arquitectura de orquestación y por qué?** Un **orquestador con flujo fijo** en LangGraph, con estado tipado, checkpoints en SQLite, dos pausas humanas (`interrupt`) y una **paralelización** puntual: `desplegar` y `automatizar` corren a la vez y se unen en `listo` (checkpoint 12 → 13). Usamos un supervisor LLM solo donde la ruta depende del contenido: `triage` elige qué agente corrige una falla. Para el resto, un supervisor añadiría costo y variación sin ganar nada, porque el orden de las etapas no cambia entre historias. Una red de agentes sin orquestador haría imposible la trazabilidad que pide el reto: criterios → casos → plan aprobado → código → pruebas.

**5. ¿Qué falló y qué corregí en el agente?**
- **Diseñador:** se cortó por `max_tokens` porque intentó guardar todo el plan en una sola llamada. Cambié `guardar_casos` para que guarde en lotes de máximo 6, reemplazando por id, con `max_pasos=20`.
- **Automatizador, en la regresión previa:** `salida/HU-03/reporte.md` terminó en ESCALAR por pruebas mal escritas. Escribían directo en SQLite (`readonly database`, que el triage atribuyó dos veces al despliegue), afirmaban textos de Pydantic y elegían un departamento que no existe. Le agregué reglas: solo la API, solo afirmar textos fijos, departamentos válidos, fechas coherentes y `skip` justificado cuando un paso es imposible en la pantalla. También hice que `regenerar_pruebas` le devuelva sus fallas, una vez.

No corregí los resultados porque la regla del reto lo prohíbe, y además el error se habría repetido: el mismo agente escribe las pruebas de la siguiente historia. Prueba de que la corrección funcionó: HU-10 no tuvo ningún ciclo de corrección.

**Qué cambiaría con otra semana:** agregar más seguridad y validaciones de control en los agentes; por ejemplo, las dos que quedaron parciales en `seguridad.md` (auditoría de los agentes 1 y 2, y `curl` limitado a `localhost`).
