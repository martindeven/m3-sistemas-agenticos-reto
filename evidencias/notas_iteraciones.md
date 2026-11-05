# Notas de iteraciones HU-10

## 0 · Preparación del contexto

- **Qué pasaba:** la Guía del reto y las convenciones se contradicen. La Guía pide 422, otros textos y otros data-testid (`vacaciones-empleado-{id}`, `vacaciones-solicitar`, `mensaje-exito/error`); las convenciones piden 400/409.
- **Qué cambié:**
  - En `contexto/convenciones_app.md`, sección «HU-10 · Compatibilidad y decisiones de implementación»:
    - fuente de verdad: las convenciones y sus 8 `detail` exactos;
    - campos extra compatibles (`dias_restantes` y `dias_disponibles`, `dias_por_anio`);
    - cálculo de días hábiles solo en `backend/vacaciones.py`;
    - data-testid anidados para cumplir los dos juegos;
    - pruebas solo por la API.
  - En `contexto/reglas_negocio.md`, una nota sobre la excepción de 400/409.
- **Por qué:** todos los agentes leen `contexto/`. Si la decisión no queda escrita ahí, cada ejecución elige una versión distinta.

## 1 · Validadores del analista y del diseñador

- **Qué pasaba:** `validar_gherkin` y `validar_plan` solo revisaban la forma del archivo. Un mensaje mal copiado o un límite faltante pasaba sin que nadie lo notara, y las pruebas ocultas califican los textos letra por letra.
- **Qué cambié:**
  - **Analista** (`agentes/analista.py`): `mensajes_exactos()` lee la tabla de errores de las convenciones que cita la historia. `validar_gherkin` exige:
    - cada `detail` letra por letra, uno por escenario;
    - el camino feliz;
    - los escenarios «límite exacto», «excede por uno» y «primer día de antigüedad».
  - **Diseñador** (`agentes/disenador_pruebas.py`): `validar_plan` exige:
    - cada mensaje en algún `resultado_esperado`;
    - los data-testid en los casos e2e;
    - `fecha_ingreso`/`fecha_inicio`/`fecha_fin` en `datos`.
  - **Pruebas de la fábrica:** `tests_fabrica/test_validadores.py`, 9 pruebas.
- **Por qué:** reflexión guiada por un evaluador determinista. El código decide si la salida es válida y le devuelve al agente qué corregir. HU-01 a HU-03 no cambian, porque no citan convenciones.

## 2 · Regresión de HU-03 en ESCALAR (antes de HU-10)

- **Qué falló** (`salida/HU-03/reporte.md`): 5 pruebas, todas por cómo estaban escritas, no por la app.
  - `_marcar_baja()` escribía con sqlite3 en la base del host → `attempt to write a readonly database`. El triage culpó **dos veces** al agente de despliegue y gastó los 2 ciclos.
  - CP-13 y CP-14 afirmaban `'fecha_baja'` dentro del texto de un 422 que arma Pydantic.
  - CP-10 E2E elegía «Marketing» en un `<select>` que no ofrece esa opción.
- **Qué cambié:**
  - **Automatizador** (`agentes/automatizador.py`), reglas nuevas en `INSTRUCCIONES`:
    - solo la API (`POST /api/empleados`, `PATCH …/baja`);
    - correos `uuid4` y departamentos válidos;
    - solo afirmar textos fijos;
    - locators acotados a su contenedor;
    - datos de ejemplo para HU-10.
  - **Verificación** (`flujos/verificacion.py`):
    - `verificar_pruebas_escritas` busca los ids solo en los archivos de la historia;
    - `ejecutar_pruebas` separa las pruebas de la historia de las de regresión.
  - **Script nuevo** `flujos/regenerar_pruebas.py`, para rehacer las pruebas de una historia con el agente corregido.
- **Por qué en el agente:** el mismo agente iba a escribir las pruebas de HU-10. Corregir los archivos a mano habría dejado el error listo para repetirse.

## 3 · Regenerar HU-01

- **Resultado:** `Pruebas de HU-01: 7 (0 fallan) · Regresión: 28 (5 fallan)`. Las 5 fallas eran las pruebas viejas de HU-02 y HU-03, todavía sin regenerar.
- **Hallazgo:** antes **no existía ningún archivo de prueba de HU-01**. La búsqueda acotada de ids lo dejó ver; antes, un `CP-xx` de otra historia lo daba por cubierto.
- **Bien resuelto por el agente:** CP-07 (departamento inválido en el `<select>`) quedó como `skip` con el motivo y el caso de API que lo cubre (CP-06).

## 4 · Regenerar HU-03 (primer intento)

- **Qué falló:** `Pruebas de HU-03: 14 (3 fallan) · Regresión: 21 (0 fallan)`.
  - CP-05 y CP-06: el empleado se creaba con el `fecha_ingreso` por defecto (2024-01-15) y se daba de baja el 2024-01-10, antes del ingreso. La app respondió 422, correctamente, y la prueba nunca llegó a probar el 409.
  - CP-10 E2E: el caso pedía literalmente «Marketing» y el agente obedeció al caso, no a la regla.
- **Qué cambié en el automatizador:**
  - fechas coherentes y explícitas: baja posterior al ingreso, salvo en el caso que prueba ese error;
  - si un caso e2e pide un valor que la pantalla no ofrece, el test va con `skip` y su motivo.
- **Por qué:** el error de fechas se repetiría en HU-10, con `fecha_ingreso` y los periodos de vacaciones.

## 5 · Regenerar HU-03 (segundo intento)

- **Qué falló:** CP-10 quedó resuelto con `skip`, pero CP-05 y CP-06 seguían igual: `2 failed, 31 passed, 2 skipped`.
- **Diagnóstico** (`auditoria.jsonl`): el agente **no reescribió** los archivos. Solo hizo 2 `Edit` sobre CP-10, y `test_hu_03.py` conservaba la hora de la corrida anterior. Sin el log de fallas, no sabía qué revisar.
- **Qué cambié:** `flujos/regenerar_pruebas.py` ahora le devuelve al automatizador las fallas **de esta historia** (no las de regresión), una vez como máximo (`MAX_CORRECCIONES = 1`), y vuelve a correr la suite.
- **Por qué:** una regla en el prompt no basta si el agente no recibe la señal de qué incumplió. Es el mismo patrón de la fábrica: verificación determinista → error al agente → límite de intentos.
- **Resultado:** regresión en verde, `57 passed, 2 skipped` (`evidencias/pytest_final.log`).

## 6 · HU-10 · Preguntas abiertas del analista

- **Qué preguntó:** no encontró en el contexto el endpoint para dar de baja; y si las fechas con formato inválido necesitan un mensaje propio.
- **Qué decidí:** respondí `si` (11:25:29). El endpoint existe (`PATCH /api/empleados/{id}/baja`) y el 422 de formato ya lo cubren las convenciones.
- **Pendiente para otra corrida:** documentar `PATCH /api/empleados/{id}/baja` en `contexto/convenciones_app.md`, para que el analista no lo vuelva a preguntar. No lo cambié a mitad de la ejecución para no darles a los agentes un contexto distinto al del analista.

## 7 · HU-10 · El diseñador se cortó por max_tokens

- **Qué falló** (`evidencias/ejecucion_HU-10.log`, línea 28): `stop_reason=max_tokens`. Intentó guardar todos los casos (13 escenarios, API + e2e) en una sola llamada a `guardar_casos`, y con el razonamiento del modelo pasó el tope de 16 000 tokens de `base.py`. El bucle cortó con un error en lugar de guardar un JSON incompleto.
- **Qué cambié** (`agentes/disenador_pruebas.py`):
  - `guardar_casos` guarda en lotes de máximo 6 y reemplaza por id;
  - el prompt pide lotes y poco texto fuera de la herramienta;
  - `max_pasos=20`.
- **Por qué:** el mensaje del bucle ofrecía «súbelo o pide una salida más corta». Elegí la salida más corta para no tocar el bucle de `base.py`.
- **Reanudación:** `REANUDAR=HU-10-solicitar-vacaciones-20261105-1113`. El hilo siguió desde `disenar_casos` sin repetir el filtro, el análisis ni las preguntas (checkpoints 5 y 6 de `historial_estados.md`). El diseñador pasó en el intento 1 con 24 casos (13 de API y 11 e2e).

## 8 · HU-10 · Aprobación del plan

- **Versión 1, rechazada a las 11:35:07.** Cumplía las reglas de la API, pero:
  1. no refrescaba `vacaciones-disponibles` ni `tabla-vacaciones` después del POST;
  2. permitía varios paneles abiertos, con data-testid duplicados que fallan en el modo estricto de Playwright;
  3. metía el panel dentro de un `<tr>`;
  4. mostraba el botón con `!== 'baja'` en lugar de `=== 'activo'`.
- **Versión 2, aprobada a las 11:36:47.** Incorporó los 4 cambios. Los `<span>` anidados ya no se mencionaban, pero `app/CLAUDE.md` los trae (la copia de `convenciones_app.md`).
- **Evidencia:** `salida/HU-10/plan.md` (versiones 1 y 2 con su decisión). Revisé el plan contra la checklist de la guía con apoyo de Claude Code; las decisiones de rechazar y aprobar fueron mías.

## 9 · Resultado final

- `salida/HU-10/reporte.md`: **LISTA**, 0 ciclos de corrección, 1.84 USD.
- `Pruebas de HU-10: 24 (0 fallan) · Regresión: 35 (0 fallan)`: 57 pasan y 2 se omiten (CP-07 de HU-01 y CP-10 de HU-03, ambos inalcanzables desde la pantalla).
- `evidencias/capturas/10_formulario.png` a `14_grafo.png`, generadas con `evidencias/capturas.py`. Los textos se verificaron letra por letra antes de cada captura.
