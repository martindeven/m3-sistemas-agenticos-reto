# Changelog

Todos los cambios relevantes de la fábrica se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [1.1.0] - 2026-11-05

Cambios para construir HU-10 · Solicitar vacaciones y dejar evidencia de cada etapa. No se editó a mano nada de `app/` ni de `salida/`.

### Added
- **Contexto de HU-10:** `historias/HU-10-solicitar-vacaciones.md`, `contexto/reglas_vacaciones.md` y `contexto/convenciones_vacaciones.md`, anexados al final de `reglas_negocio.md` y `convenciones_app.md`.
- **Compatibilidad entre fuentes:** sección «HU-10 · Compatibilidad y decisiones de implementación» en `contexto/convenciones_app.md`:
  - fuente de verdad y los 8 `detail` exactos;
  - `dias_restantes` y `dias_disponibles` en el POST, `dias_por_anio` en el GET;
  - días hábiles solo en `backend/vacaciones.py`;
  - data-testid anidados para cumplir la Guía y las convenciones;
  - pruebas solo por la API.
- **Excepción de códigos:** nota en `contexto/reglas_negocio.md`: vacaciones usa 400/409, como excepción al 422 de HU-01 a HU-03.
- **Analista:** `mensajes_exactos()`, `convenciones_citadas()` y `patron_mensaje()` en `agentes/analista.py`, para leer los mensajes exactos de las convenciones que cita la historia.
- **Diseñador:** `testids_obligatorios()`, `historia_de()` y `CAMPOS_VACACIONES` en `agentes/disenador_pruebas.py`.
- **Pruebas de la fábrica:** `tests_fabrica/test_validadores.py`, 9 pruebas sin LLM de los validadores.
- **`flujos/regenerar_pruebas.py`:** rehace las pruebas de una historia con el automatizador actual, corre la suite y le devuelve al agente las fallas de su historia una vez (`MAX_CORRECCIONES = 1`).
- **Checkpoints persistentes:** `SqliteSaver` en `.langgraph/checkpoints.sqlite` para `flujos/flujo_s4.py`, con `thread_id = <historia>-AAAAMMDD-HHMM`, y reanudación con `REANUDAR=<thread_id>` (`get_state` + `Command(resume=...)`).
- **Ejecución con streaming:** `app.stream(..., stream_mode="updates")`, que imprime `[HH:MM:SS] nodo → claves actualizadas`.
- **Evidencia que deja el flujo:**
  - `salida/<HU>/plan.md`: cada versión del plan con la decisión humana, escrito por el código del flujo;
  - `salida/<HU>/historial_estados.md`: los checkpoints, con `get_state_history`.
- **Bitácora con hora:** el decorador `con_hora` antepone `[HH:MM:SS]` a cada línea de la bitácora.
- **`evidencias/capturas.py`:** capturas de HU-10 con Playwright, verificando el texto antes de cada una.
- **Documentación:** `CHANGELOG.md` y `evidencias/PROCESO.md`.
- **Dependencia:** `langgraph-checkpoint-sqlite` en `requirements.txt`.
- **`.env.example`:** `DEFENSAS=1`, con la advertencia «Nunca 0 en el reto».

### Changed
- **`validar_gherkin(texto, mensajes=None)`:** con mensajes, exige:
  - cada `detail` letra por letra, uno por escenario;
  - el camino feliz;
  - los escenarios «límite exacto», «excede por uno» y «primer día de antigüedad».

  Sin mensajes, se comporta como antes (HU-01 a HU-03).
- **Prompt del analista:** un escenario por fila de la tabla de errores, sin `Antecedentes` ni `Esquema del escenario`, y con los límites.
- **`validar_plan(texto, gherkin, mensajes, testids, campos)`:** exige cada mensaje en algún `resultado_esperado`, los data-testid en los casos e2e y las fechas de vacaciones en `datos`.
- **Prompt del diseñador:** datos únicos y fechas tomadas de los ejemplos de `reglas_vacaciones.md`.
- **`guardar_casos` del diseñador:** guarda por **lotes** (máximo 6 por llamada, reemplaza por id) y `disenar_casos` usa `max_pasos=20`.
- **`INSTRUCCIONES` del automatizador:**
  - solo la API (`POST /api/empleados`, `PATCH /api/empleados/{id}/baja`);
  - correos `uuid4` y departamentos válidos;
  - fechas coherentes;
  - solo afirmar textos fijos;
  - locators acotados a su contenedor;
  - `skip` justificado si un paso es imposible en la pantalla;
  - datos de ejemplo para HU-10;
  - docstring con el id del caso.
- **`verificar_pruebas_escritas`:** busca los ids solo en `tests/api/test_{hu}*.py` y `tests/e2e/test_{hu}*_e2e.py`.
- **`ejecutar_pruebas`:** además del resultado, imprime y registra cuántas pruebas son de la historia y cuántas de regresión.
- **`flujo_s4.aprobar_plan`:** envuelve a `flujo_s2.aprobar_plan` para escribir `plan.md`. El nodo `fin` recibe `config` para escribir el historial.
- **`.gitignore`:** agrega `.langgraph/` y `app/.tmp_fds.txt`, y deja de ignorar `auditoria.jsonl`, que es entregable.
- **Docstrings:** en español en todas las funciones y clases públicas de `agentes/` y `flujos/`.
- **`README.md`:** reescrito con el diagrama del flujo, roles, instalación en Mac, Linux y Windows, `REANUDAR`, pruebas, seguridad, un ejemplo con HU-10 y troubleshooting.

### Fixed
- **Pruebas mal escritas que dejaron HU-03 en ESCALAR:**
  - escribían en el SQLite del host (`readonly database`);
  - afirmaban textos propios de Pydantic;
  - elegían un departamento que no está en el `<select>`.

  Corregido en las instrucciones del automatizador y regenerando las pruebas.
- **Trazabilidad engañosa:** un `CP-xx` de otra historia contaba como cubierto. Así se descubrió que HU-01 no tenía pruebas.
- **Corte del diseñador por `max_tokens`:** al guardar un plan grande en una sola llamada.
- **`historial_estados.md` vacío:** el `config` del nodo trae el namespace de la tarea; la consulta usa solo `thread_id`. Las horas del historial se muestran en hora local, no en UTC.

### Security
- **`.env.example`:** la clave de API versionada se reemplazó por el marcador `sk-ant-...`. La original sigue en el historial de git y debe revocarse.

## [1.0.0] - Lab 4

Fábrica base del curso: analista, diseñador, desarrollador, despliegue, automatizador y triage; flujos `flujo_s2`, `flujo_s3` y `flujo_s4`; hooks de seguridad.
