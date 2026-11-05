# Plan · HU-10

## Versión 1 · [11:35:07]

Ya revisé `backend/{database,models,schemas,main}.py` y `frontend/src/DirectorioEmpleados.jsx` (ya tiene `fecha_ingreso` y `estado`, así que no hay que tocar el modelo de empleados). Aquí está el plan:

## Plan de implementación HU-10

### Backend

1. **`backend/vacaciones.py`** (nuevo): módulo puro, sin FastAPI.
   - `FESTIVOS = {2026: [...], 2027: [...]}` con las fechas de la tabla de festivos.
   - `es_dia_habil(fecha, anio)`, `contar_dias_habiles(inicio, fin)` (incluye ambos extremos).
   - `fecha_aniversario(fecha_ingreso)` → aniversario con regla del 29 de febrero.
   - `cumple_antiguedad(fecha_ingreso, fecha_inicio)`.
2. **`backend/models.py`**: agregar `Vacacion` (`id`, `empleado_id` FK a `empleados.id`, `fecha_inicio: Date`, `fecha_fin: Date`, `dias_habiles: int`). No se toca `Empleado`.
3. **`backend/schemas.py`**: `VacacionCrear` (`fecha_inicio`, `fecha_fin`), `VacacionSalida` (incluye `dias_restantes` y `dias_disponibles` iguales), `SaldoVacaciones` (`empleado_id`, `anio`, `dias_por_anio=12`, `dias_usados`, `dias_disponibles`, `solicitudes: list[SolicitudResumen]`).
4. **`backend/main.py`**: dos endpoints nuevos.
   - `POST /api/empleados/{id}/vacaciones`: valida en el orden exacto de la tabla (404 → 409 → 400 fin<inicio → 400 cruce de año → 400 año fuera de `FESTIVOS` → 400 antigüedad → 400 sin días hábiles → 400 excede disponibles), usando los `detail` literales de las convenciones. Calcula `dias_habiles`, suma usados del año vía consulta a `Vacacion`, persiste y responde 201.
   - `GET /api/empleados/{id}/vacaciones?anio=`: 404 si no existe el empleado; agrega usados/disponibles del año (default año actual) y lista `solicitudes`.
   - Reutiliza `obtener_empleado_o_404` ya existente.

### Frontend

5. **`frontend/src/VacacionesEmpleado.jsx`** (nuevo componente, uno por empleado activo):
   - Botón `vacaciones-abrir-{id}` (con `<span data-testid="vacaciones-empleado-{id}">` anidado) que al abrir hace `GET` del saldo y limpia el mensaje del directorio.
   - Panel con `vacaciones-disponibles` (solo número), campos `vacaciones-fecha-inicio`/`vacaciones-fecha-fin` (`type="date"`), botón `vacaciones-enviar` (con `<span data-testid="vacaciones-solicitar">` anidado).
   - Al enviar: `POST`; resultado en `vacaciones-mensaje` con `<span data-testid="mensaje-exito">` o `<span data-testid="mensaje-error">` anidado, texto exacto según el `detail` o el mensaje de éxito con N/M/año.
   - Lista `tabla-vacaciones` con `fila-vacaciones-{id}` y `dias-vacaciones-{id}` por solicitud.
6. **`DirectorioEmpleados.jsx`**: en `FilaEmpleado`, renderizar `<VacacionesEmpleado>` solo si `empleado.estado !== 'baja'`.

¿Apruebo este plan para empezar a implementar?

**Decisión:** Plan rechazado: Buen plan; ajusta 4 cosas sin cambiar lo demás: (1) después de un POST 201, vuelve a pedir el GET y actualiza vacaciones-disponibles y tabla-vacaciones; (2) solo puede haber un panel de vacaciones abierto a la vez en el directorio (el estado del empleado abierto vive en DirectorioEmpleados), para que vacaciones-fecha-inicio, vacaciones-mensaje, etc. no se dupliquen; (3) si FilaEmpleado es un <tr>, el panel va dentro de un <td colSpan> o en una fila aparte, nunca un div directo en el tr; (4) muestra el botón solo si empleado.estado === 'activo'. No cambies el comportamiento de HU-01 a HU-03.

## Versión 2 · [11:36:47]

Confirmado: `FilaEmpleado` es un `<tr>` dentro de `DirectorioEmpleados`, que mantiene el estado de la lista. Con esto el plan ajustado:

```markdown
# Plan HU-10 (ajustado tras revisión)

## Backend
- `backend/vacaciones.py` (nuevo): dict `FESTIVOS = {2026: [...], 2027: [...]}`, `calcular_dias_habiles(inicio, fin)`,
  `fecha_aniversario(fecha_ingreso)` (maneja 29-feb → 1-mar), `dias_usados_en_anio(sesion, empleado_id, anio)`.
- `backend/models.py`: nueva clase `Vacacion` (`id`, `empleado_id` FK, `fecha_inicio`, `fecha_fin`, `dias_habiles`). No se toca `Empleado`.
- `backend/schemas.py`: `VacacionCrear` (fecha_inicio, fecha_fin), `VacacionRespuesta` (201), `SaldoVacaciones` (GET, incluye `dias_por_anio=12`, `solicitudes`).
- `backend/main.py`: dos rutas nuevas sobre el router de empleados existente, sin tocar las de HU-01 a HU-03.
  - `POST /api/empleados/{id}/vacaciones`: valida en el orden exacto de la tabla (404→409→fecha_fin<inicio→cruce de año→año fuera de festivos→antigüedad→sin días hábiles→tope anual), calcula con `vacaciones.py`, inserta y responde con `dias_restantes` y `dias_disponibles` iguales.
  - `GET /api/empleados/{id}/vacaciones?anio=`: año por defecto = actual; agrega `dias_usados`, `dias_disponibles`, `solicitudes`.

## Frontend
- **Estado del panel abierto vive en `DirectorioEmpleados`**, no en `FilaEmpleado`: un solo `empleadoVacacionesAbiertoId` (o `null`) en el padre, pasado como prop a cada fila junto con `onAbrirVacaciones`/`onCerrarVacaciones`. Así solo un panel existe a la vez y no se duplican `data-testid` como `vacaciones-fecha-inicio` o `vacaciones-mensaje`.
- Al abrir un panel, el padre limpia el mensaje del directorio (`mensaje-exito`/`mensaje-error` generales) antes de mostrar el de vacaciones.
- `FilaEmpleado` (sigue siendo `<tr>`): botón `vacaciones-abrir-{id}` solo si `empleado.estado === 'activo'`; al hacer clic llama `onAbrirVacaciones(empleado.id)` en el padre.
- Nuevo componente `PanelVacaciones` (nuevo archivo `PanelVacaciones.jsx`), renderizado **solo cuando `empleadoVacacionesAbiertoId === empleado.id`**, como una **fila `<tr>` extra inmediatamente después de la fila del empleado**, con un único `<td colSpan={n}>` que envuelve todo el panel (nunca un `div` suelto dentro del `tr` principal).
- `PanelVacaciones`: al montarse hace `GET /api/empleados/{id}/vacaciones` para pintar `vacaciones-disponibles` y `tabla-vacaciones`/`fila-vacaciones-{id}`/`dias-vacaciones-{id}`; formulario con `vacaciones-fecha-inicio`, `vacaciones-fecha-fin`, botón `vacaciones-enviar`.
- Al enviar: `POST`; si éxito, **vuelve a pedir el `GET`** para refrescar `vacaciones-disponibles` y `tabla-vacaciones`, y muestra en `vacaciones-mensaje > mensaje-exito` el texto exacto; si falla, `vacaciones-mensaje > mensaje-error` con el `detail` tal cual (sin refrescar saldo).
- No se toca `FormularioEmpleado.jsx` ni la lógica de alta/baja de HU-01 a HU-03.
```

**Decisión:** Plan aprobado por una persona

