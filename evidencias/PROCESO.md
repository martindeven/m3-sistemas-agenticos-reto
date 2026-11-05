# Proceso · Reto HU-10 Solicitar vacaciones

Cómo se llevó la fábrica de HU-03 en ESCALAR a HU-10 en **LISTA**: los prompts que se usaron con Claude Code para mejorar la fábrica (nunca `app/` ni `salida/` a mano), las iteraciones, las capturas y una reflexión.

## 1 · Prompts usados

Copiados de `GUIA_RETO_HU10.md`. Donde lo que se usó difiere de la guía, se indica en la nota que acompaña al prompt.

### P1 · Sección de compatibilidad en el contexto

```text
Lee contexto/convenciones_app.md, contexto/reglas_negocio.md, contexto/convenciones_vacaciones.md,
contexto/reglas_vacaciones.md y ../reto-files/"Guía del reto · HU-10 Solicitar vacaciones.md".
NO toques app/ ni salida/.

Agrega AL FINAL de contexto/convenciones_app.md una sección "## HU-10 · Compatibilidad y decisiones de
implementación" (en español, concisa) que diga:

1. Fuente de verdad: convenciones_vacaciones.md y reglas_vacaciones.md. Códigos 400/404/409 y los 8 mensajes
   `detail` EXACTOS en el orden de su tabla (404, 409, fin<inicio, cruza año, año sin festivos, antigüedad,
   sin días hábiles, excede). Copia la tabla tal cual.
2. Campos extra compatibles: el POST 201 devuelve `dias_restantes` Y `dias_disponibles` (mismo valor);
   el GET 200 devuelve `empleado_id`, `anio`, `dias_por_anio` (12), `dias_usados`, `dias_disponibles`, `solicitudes`.
   Si no se manda `anio`, se usa el año en curso.
3. Backend: los días hábiles se calculan SOLO en el backend, en un módulo backend/vacaciones.py con un dict
   FESTIVOS = {2026: [...], 2027: [...]} tomado de reglas_vacaciones.md. Se cuenta incluyendo inicio y fin.
   Aniversario: mismo día y mes del año siguiente; un 29 de febrero pasa al 1 de marzo si el año no es bisiesto.
   Nueva tabla `vacaciones` (id, empleado_id, fecha_inicio, fecha_fin, dias_habiles). create_all la crea sola.
   NO agregar columnas a `empleados` (fecha_ingreso y estado ya existen). No cambiar los endpoints de HU-01 a HU-03.
4. Frontend: los data-testid de convenciones y los de la Guía, anidados para que funcionen los dos:
   <button data-testid="vacaciones-abrir-{id}"><span data-testid="vacaciones-empleado-{id}">Solicitar vacaciones</span></button>
   <button data-testid="vacaciones-enviar"><span data-testid="vacaciones-solicitar">Solicitar</span></button>
   <div data-testid="vacaciones-mensaje"><span data-testid="mensaje-exito|mensaje-error">texto</span></div>
   El texto de vacaciones-mensaje es exactamente el detail del error o
   "Solicitud registrada: N días hábiles. Te quedan M días hábiles en AAAA."
   Campos de fecha (type="date"): vacaciones-fecha-inicio y vacaciones-fecha-fin.
   `vacaciones-disponibles` contiene solo el número. Lista: tabla-vacaciones, fila-vacaciones-{id}, dias-vacaciones-{id}.
   El botón solo aparece para empleados con estado "activo". El panel se muestra dentro del directorio y
   sus mensajes no deben duplicar los mensaje-exito/mensaje-error del directorio que ya estén visibles.
5. Pruebas: nunca escribir en la base de datos directamente; usar solo la API.

En contexto/reglas_negocio.md, agrega al final una nota de 2 líneas: las reglas de vacaciones usan 400/409
según convenciones_vacaciones.md, como excepción a la regla general de 422 de HU-01 a HU-03.
Muéstrame el diff.
```

### P2 · Validadores más estrictos (reflexión determinista)

```text
Mejora los validadores de la fábrica SIN tocar app/ ni salida/ y sin reescribir el bucle de agentes/base.py.

A) agentes/analista.py
 - Nueva función `mensajes_exactos(historia: Path) -> list[str]`: busca en el texto de la historia las
   referencias a contexto/convenciones_*.md. Si el archivo existe, extrae de la tabla "Errores: mensajes exactos"
   todos los valores `detail` entre backticks. Si no hay referencias, devuelve [] (así HU-01 a HU-03 no cambian).
 - `validar_gherkin(texto, mensajes=None)`: mantiene sus reglas actuales y además, si recibe mensajes:
   * cada mensaje aparece LETRA POR LETRA dentro de algún escenario; "N" se trata como número (regex \d+);
   * hay al menos un escenario por mensaje y al menos un camino feliz;
   * para la regla de tope hay un escenario de "límite exacto" (usar justo lo que queda, quedan 0) y otro de
     "excede por uno"; para antigüedad, un escenario del primer día con antigüedad (aceptado).
   Cada problema se devuelve como texto claro, por ejemplo "Falta el mensaje exacto: «...»".
 - `generar_criterios` pasa `mensajes_exactos(historia)` al validador.
 - Actualiza SISTEMA: un escenario por cada fila de la tabla de errores de las convenciones, con el código HTTP
   y el detail copiado letra por letra; sin "Antecedentes:" ni "Esquema del escenario:"; incluir los límites
   (tope exacto, excede por 1, primer día de antigüedad, periodo con festivo, periodo solo fin de semana).
B) agentes/disenador_pruebas.py
 - `validar_plan` recibe los mismos mensajes y exige que cada uno aparezca en el `resultado_esperado` de al menos
   un caso; en los casos e2e de HU-10, que se usen los data-testid de convenciones; en los casos de vacaciones,
   que `datos` incluya fecha_ingreso, fecha_inicio y fecha_fin.
 - Ajusta el prompt: datos concretos y únicos; fechas tomadas de los ejemplos de reglas_vacaciones.md.
C) Docstrings en español en todas las funciones nuevas o modificadas.
D) Crea tests_fabrica/test_validadores.py (carpeta nueva en la raíz, fuera de app/)
   con pytest: un Gherkin al que le falta un mensaje debe dar error, y uno completo debe pasar. Ejecútalo.
```

### P3 · Automatizador y verificación (por las fallas heredadas)

```text
Lee salida/HU-03/reporte.md (estado ESCALAR) y app/tests/ (solo lectura). Las fallas vienen de las pruebas, no de la app:
 - _marcar_baja() escribe en app/backend/datos/empleados.db del host (de root, y además no es el volumen del contenedor);
 - CP-13 y CP-14 esperan 'fecha_baja' en un 422 que Pydantic devuelve con su propio texto;
 - CP-10 E2E elige un departamento que no existe en el <select>.
No edites app/ a mano. Corrige al AGENTE:

1) agentes/automatizador.py, instrucciones nuevas (agrégalas a INSTRUCCIONES):
   - Nunca leer ni escribir la base de datos: todo dato de prueba se crea y se modifica por la API
     (POST /api/empleados, PATCH /api/empleados/{id}/baja con fecha_baja).
   - Correos únicos con uuid4; departamentos solo de: Tecnología, Ventas, Finanzas, Recursos Humanos, Operaciones.
   - Solo afirmar textos de error que el contexto fija letra por letra; para los 422 genéricos de validación,
     afirmar solo el código.
   - E2E: locators acotados al contenedor de la funcionalidad (por ejemplo, el panel de vacaciones o
     fila-empleado-{id}), porque mensaje-exito y mensaje-error existen en varios lugares.
   - HU-10: cada prueba crea su propio empleado. fecha_ingreso "2024-03-10" en general y "2025-12-21" para el
     límite de antigüedad (inicio 2026-12-21 → 201; inicio 2026-12-18 → 400). Periodos de ejemplo: 2026-12-21..31 = 8,
     2026-09-14..18 = 4, 2026-07-11..12 = 0 (400), 2026-08-03..14 = 10 y luego 2026-06-01..02 = 2 (quedan 0, aceptada),
     o 2026-06-01..03 = 3 (400 "quedan 2 días hábiles"); 2028 → 400 de año; 2026-12-28..2027-01-08 → 400 de año calendario.
   - El docstring de cada prueba empieza con su id CP-xx.
2) flujos/verificacion.py: `verificar_pruebas_escritas(hu, ids)` busca los ids SOLO en
   tests/api/test_{hu_min}*.py y tests/e2e/test_{hu_min}*_e2e.py. `ejecutar_pruebas` sigue corriendo toda la suite
   (regresión de HU-01 a HU-03) y además imprime cuántas pruebas son de la historia y cuántas de regresión.
3) Script nuevo flujos/regenerar_pruebas.py: uso `python -m flujos.regenerar_pruebas HU-02`. Llama SOLO a
   automatizador.automatizar(hu), que ya usa hooks y auditoría; luego corre verificacion.ejecutar_pruebas(hu)
   e imprime el resultado. Sirve para regenerar las pruebas de HU-01 a HU-03 con el agente corregido.
Docstrings en español. Muéstrame el diff.
```

> Además de P3, durante la regresión hubo dos ajustes pedidos en la conversación, sin un prompt de la guía. Al automatizador se le agregaron reglas de fechas coherentes y de `skip` justificado; a `regenerar_pruebas`, que le devuelva al agente las fallas de su historia (ver iteraciones 4 y 5).

### P4 · LangGraph completo (estado, checkpoints, HITL y streaming)

```text
Mejora flujos/flujo_s4.py (y flujo_s2.py solo si hace falta) para usar todas las características de LangGraph
que pide la rúbrica, sin cambiar el orden de las etapas ni quitar defensas:
1. Checkpointer persistente: SqliteSaver (langgraph.checkpoint.sqlite) en .langgraph/checkpoints.sqlite
   con sqlite3.connect(..., check_same_thread=False). thread_id = stem de la historia más la fecha y hora
   (ej. HU-10-solicitar-vacaciones-20261104-1830). Con la variable REANUDAR=<thread_id> se retoma un hilo pausado
   (por ejemplo, si se cerró la terminal en la aprobación del plan) usando get_state y Command(resume=...).
   Agrega langgraph-checkpoint-sqlite a requirements.txt.
2. Ejecuta con graph.stream(..., stream_mode="updates") e imprime "[HH:MM:SS] nodo → claves actualizadas".
3. La bitácora lleva marca de hora (prefijo [HH:MM:SS]).
4. Cada versión del plan se escribe en salida/<HU>/plan.md con su número y la decisión humana
   ("Plan aprobado por una persona" o "Plan rechazado: <comentario>"). La escritura la hace el código del flujo, no un agente.
5. Al terminar, el nodo reporte escribe además salida/<HU>/historial_estados.md con get_state_history
   (nodo, siguiente nodo, número de ciclos e intentos por checkpoint). Es la evidencia de los checkpoints.
6. Regenera el diagrama con flujos.util.dibuja_grafo.
7. Mantén el estado TypedDict y los reductores (bitacora y costo_usd con operator.add); documenta en un docstring
   del módulo qué nodos son workflow (código determinista) y cuáles agente (LLM).
También: agrega DEFENSAS=1 a .env.example con un comentario ("nunca 0 en el reto"); en .gitignore agrega
.langgraph/ y app/.tmp_fds.txt, y QUITA la línea auditoria.jsonl (es entregable). No modifiques seguridad/hooks.py
ni el bucle de agentes/base.py. Muéstrame el diff y ejecuta `python -c "import flujos.flujo_s4"` para verificar.
```

> Ajuste durante HU-10, sin un prompt de la guía: el diseñador se cortó por `max_tokens` y se cambió `guardar_casos` para guardar por lotes (iteración 7).

### P-capturas · Script de capturas de pantalla

```text
Crea evidencias/capturas.py (Python + Playwright sync, sin dependencias nuevas). El script:
 - crea por la API (http://localhost:8080/api) un empleado con correo único y fecha_ingreso 2024-03-10;
 - abre http://localhost:8080, hace clic en vacaciones-abrir-{id} y guarda evidencias/capturas/10_formulario.png;
 - pide 2026-12-21 a 2026-12-31 y guarda 11_exito.png (debe decir "Solicitud registrada: 8 días hábiles. Te quedan 4 días hábiles en 2026.");
 - pide 2026-07-11 a 2026-07-12 y guarda 12_error.png ("El periodo no incluye días hábiles");
 - guarda 13_tabla.png con tabla-vacaciones;
 - abre flujos/salidas/grafo_flujo_s4.html y guarda 14_grafo.png.
 Imprime al final qué capturas se guardaron. No toques app/ ni salida/.
```

### P5 · `salida/seguridad.md`

```text
Redacta salida/seguridad.md (es un entregable humano; lo reviso y lo firmo yo) con evidencia real de este repo:
- Lee evidencias/prompt_hardening.log, evidencias/ejecucion_HU-99.log, el reporte de HU-99 en salida/,
  seguridad/hooks.py, flujos/flujo_s4.py (filtrar_historia) y evidencias/auditoria_preparacion.jsonl.
- Tabla: | Ataque | Riesgo OWASP | ¿Funcionó sin defensas? | Defensa que lo detuvo | Evidencia |
  con la fila de la historia envenenada (ASI01) y la de contexto envenenado (ASI06; pon "no aplicó" si no lo hice).
  Incluye cuántas veces llegó el ataque con el prompt ingenuo y con el endurecido.
- Checklist de producción (6 puntos de guias/lab4-seguridad.md), cada uno con UNA línea de dónde se cumple
  (archivo y función).
- Mapeo a las 5 medidas del formato de entrega: validación de entradas (filtrar_historia), prompt hardening
  (<historia_no_confiable>, rol y límites), validación de salidas (validar_gherkin, validar_plan, verificacion.py,
  pruebas), sandboxing (confinar_escritura, confinar_lectura, comandos_permitidos, Docker), logging (auditoria.jsonl).
- Respuesta breve: qué capa detuvo HU-99 y por qué no bastaba con el prompt.
NO inventes resultados: si un dato no está en los logs, deja "PENDIENTE" y avísame.
```

> El paso 2 del Lab 4B se ejecutó después del primer borrador. El dato PENDIENTE se completó con `salida/HU-99/criterios.feature`.

### P6 · Documentación

```text
Actualiza la documentación de la fábrica (no toques app/ ni salida/):
1. README.md: qué es la fábrica; diagrama Mermaid del flujo s4 (filtro → analista → diseñador → planificar →
   aprobación HITL → construir → verificar → [desplegar ‖ automatizar] → E2E → triage ≤2 ciclos → reporte);
   tabla de agentes con su rol de la rúbrica (planificador = desarrollador en modo planificar; codificador =
   desarrollador en modo construir; tester = diseñador y automatizador; reviewer = verificación y triage; más
   analista, despliegue y filtro), sus herramientas y permisos; requisitos e instalación para Mac, Linux y Windows
   (PowerShell); variables de .env.example (sin valores); cómo correr una historia, cómo retomar con REANUDAR,
   cómo correr las pruebas (app/tests y tests_fabrica); seguridad y DEFENSAS; estructura de carpetas;
   un ejemplo completo con HU-10; troubleshooting.
2. CHANGELOG.md (formato Keep a Changelog, fecha 2026-11-xx, versión 1.1.0) con los cambios reales de
   contexto, validadores, automatizador, verificación, regenerar_pruebas, SqliteSaver, streaming, plan.md y .gitignore.
3. Revisa que las funciones públicas de agentes/ y flujos/ tengan docstrings en español; agrega los que falten.
4. evidencias/PROCESO.md: los prompts P1 a P7 usados (cópialos de GUIA_RETO_HU10.md), las iteraciones
   (resume evidencias/notas_iteraciones.md), el índice de capturas de evidencias/capturas/ y una reflexión
   (qué funcionó, qué mejorarías).
```


## 2 · Iteraciones

Resumen de `evidencias/notas_iteraciones.md`, donde están el detalle y la evidencia de cada una.

| # | Qué falló o faltaba | Qué se cambió en la fábrica | Resultado |
|---|---|---|---|
| 0 | La Guía y las convenciones se contradicen en códigos, textos y data-testid | Sección de compatibilidad en `contexto/convenciones_app.md` y una nota en `reglas_negocio.md` (P1) | Una sola fuente de verdad para todos los agentes |
| 1 | Los validadores solo revisaban la forma | `mensajes_exactos`, `validar_gherkin` y `validar_plan` con mensajes, límites, data-testid y fechas; `tests_fabrica` (P2) | 9 pruebas de la fábrica en verde |
| 2 | HU-03 en ESCALAR: 5 fallas de pruebas mal escritas; el triage culpó 2 veces al despliegue | Instrucciones del automatizador, búsqueda de ids por historia y `regenerar_pruebas` (P3) | — |
| 3 | HU-01 no tenía ningún archivo de prueba | Se regeneraron con el automatizador corregido | HU-01: 7 pruebas, 0 fallan |
| 4 | CP-05 y CP-06 con fechas incoherentes; CP-10 con un paso imposible en la pantalla | Reglas de fechas coherentes y `skip` justificado en el automatizador | CP-10 resuelto con `skip` |
| 5 | CP-05 y CP-06 seguían igual: el agente editaba sin reescribir | `regenerar_pruebas` le devuelve las fallas de la historia, una vez | Regresión en verde: 57 pasan, 2 se omiten |
| 6 | Preguntas abiertas del analista sobre HU-10 | Revisión humana: el endpoint existe y el 422 ya está cubierto → `si` | El flujo continuó |
| 7 | El diseñador se cortó por `max_tokens` | `guardar_casos` por lotes y `max_pasos=20`; se retomó con `REANUDAR` | 24 casos en el intento 1, sin repetir el análisis |
| 8 | Plan v1: no refrescaba el saldo, permitía paneles duplicados, un panel dentro de un `<tr>` y el botón con `!== 'baja'` | Rechazo con 4 cambios concretos | Plan v2 aprobado |
| 9 | — | — | HU-10 **LISTA**: 0 ciclos, 1.84 USD, `Pruebas de HU-10: 24 (0 fallan) · Regresión: 35 (0 fallan)` |

## 3 · Índice de capturas (`evidencias/capturas/`)

Las capturas C1 a C7 las tomó la persona; su descripción sale del nombre del archivo, la hora y la tabla de capturas de la guía. Las 10 a 14 las generó `evidencias/capturas.py`, que verifica el texto antes de cada una.

| Archivo | Qué muestra | Hora |
|---|---|---|
| `C1-app.png` | La app corriendo en http://localhost:8080 | 10:19 |
| `C1-docker-ps.png` | `docker compose ps` con los servicios arriba | 10:19 |
| `C2_pytest.png` | pytest de los validadores (`tests_fabrica`) | 10:31 |
| `C3-Flujo.png` | Diagrama del flujo s4 | 10:47 |
| `C4_pytest.png` | Regresión de HU-01 a HU-03 | 11:11 |
| `C5_HU-99.png` | HU-99 bloqueada por el filtro | 11:12 |
| `C6-plan.png` | El plan y la decisión humana | 11:39 |
| `C7-reporte.png` | `salida/HU-10/reporte.md` en LISTA | 11:44 |
| `10_formulario.png` | Panel de vacaciones abierto: 12 días disponibles y los campos de fecha | script |
| `11_exito.png` | «Solicitud registrada: 8 días hábiles. Te quedan 4 días hábiles en 2026.» y el saldo en 4 | script |
| `12_error.png` | 2026-07-11 a 2026-07-12 → «El periodo no incluye días hábiles» | script |
| `13_tabla.png` | `tabla-vacaciones`: 2026-12-21, 2026-12-31, 8 | script |
| `14_grafo.png` | El grafo de `flujo_s4`, con sus 19 nodos | script |

## 4 · Reflexión

**Qué funcionó**
- **Corregir al agente y no su resultado.** Las fallas de HU-03 eran de cómo el automatizador escribía las pruebas. Al corregir sus instrucciones, HU-10 salió con 0 ciclos de corrección, y las mismas reglas sirvieron para HU-01 a HU-03.
- **Validadores que leen el contexto.** `mensajes_exactos` saca los 8 mensajes de la tabla de las convenciones, así que los criterios no pueden pasar con un acento de menos. El analista pasó en el intento 1 con los 13 escenarios.
- **Checkpoints persistentes.** Cuando el diseñador se cortó, se corrigió el agente y se retomó el hilo con `REANUDAR`, sin repetir el filtro, el análisis ni las preguntas.
- **El humano en el momento de mayor influencia.** El plan v1 cumplía las reglas de la API, pero habría roto pruebas E2E. Un rechazo concreto bastó para que el v2 lo corrigiera.
- **Defensa en profundidad.** HU-99 la detuvo el filtro en código, a costo 0. El prompt ingenuo dejó pasar el ataque 1 de 1 veces.

**Qué mejoraría**
- **Auditoría completa.** Los agentes 1 y 2 (bucle de `base.py`) no escriben en `auditoria.jsonl`; solo los de Claude Code.
- **`curl` sin límite.** El desarrollador y el despliegue pueden usarlo sin restricción a `localhost`; el hook de comandos podría limitar el destino.
- **El triage se equivocó de responsable.** Culpó dos veces al despliegue de una falla de las pruebas (`readonly database`). Darle al triage el código de la prueba que falla, y no solo el mensaje, ayudaría a distinguirlo.
- **El diseñador propone pasos imposibles.** Escribió casos e2e que la pantalla no permite (un departamento fuera del `<select>`). Conviene una regla en su prompt, no solo en el automatizador.
- **Documentar los endpoints existentes en `contexto/`.** El analista preguntó por el endpoint de baja porque no estaba documentado. Una línea en `convenciones_app.md` evita esa pausa.
- **Guardar siempre la salida de la terminal.** La parte reanudada de HU-10 no quedó en `ejecucion_HU-10.log`. Conviene usar `tee` también al reanudar.
