# Convenciones de la aplicación de gestión de empleados

Este archivo se copia como `app/CLAUDE.md`. Claude Code lo lee antes de escribir código.

## Arquitectura

- `backend/`: FastAPI + SQLAlchemy 2 + SQLite, con Pydantic v2. El archivo `backend/main.py` expone la aplicación como `app`.
- La base de datos vive en `backend/datos/empleados.db`; la carpeta `datos/` se crea al arrancar si no existe.
- `backend/requirements.txt` lista las dependencias del backend.
- `frontend/`: React + Vite en JavaScript, sin librerías de componentes.
- Todo lo de la API cuelga de `/api`. Salud: `GET /api/salud` responde `{"estado": "ok"}`.

## Puertos

- Backend: 8000. Frontend en desarrollo: 5173, con proxy de `/api` hacia el puerto 8000.
- En Docker, el frontend se sirve en el puerto 8080 y redirige `/api` al servicio `backend`.
- El frontend siempre llama a la API con rutas relativas (`/api/...`).

## API

- Recurso principal: `/api/empleados`. Campos en español: `id`, `numero_empleado`, `nombre`, `correo`, `puesto`, `departamento`, `fecha_ingreso`, `estado`, `fecha_baja`, `creado_en`.
- Catálogo: `GET /api/departamentos` devuelve la lista de departamentos válidos.
- Fechas en formato ISO (`AAAA-MM-DD`).
- Errores con la forma `{"detail": "mensaje en español"}` y códigos 404, 409 o 422.
- Las historias futuras agregarán recursos nuevos (por ejemplo `/api/vacaciones`); el código debe permitir agregarlos sin reescribir lo existente.

## Selectores para pruebas (data-testid)

Todo elemento que una prueba necesite tocar lleva `data-testid` con estos nombres:

| Elemento | data-testid |
| --- | --- |
| Campos del formulario | `empleado-nombre`, `empleado-correo`, `empleado-puesto`, `empleado-departamento`, `empleado-fecha-ingreso` |
| Botón guardar | `empleado-guardar` |
| Mensajes | `mensaje-exito`, `mensaje-error` |
| Directorio y filas | `tabla-empleados`, `fila-empleado-{id}` |
| Datos por fila | `numero-empleado-{id}`, `estado-empleado-{id}` (texto «Activo» o «Baja») |
| Búsqueda y filtro | `buscar-empleados`, `filtro-departamento`, `sin-resultados` |
| Acciones por fila | `editar-empleado-{id}`, `baja-empleado-{id}` |
| Fecha de baja | `empleado-fecha-baja`, `confirmar-baja` |

## Reglas para quien programa

- Las reglas de negocio te llegan en el prompt; aquí no tienes acceso a carpetas superiores.
- Si `app/` ya tiene código de historias anteriores, extiéndelo sin romperlo.
- No agregues autenticación ni dependencias que no estén en esta lista sin justificarlo.
- Al terminar: `GET /api/salud` responde y `npm run build` termina sin errores.

# Convenciones de vacaciones (HU-10)

Complementa `contexto/convenciones_app.md`: mismo backend (FastAPI + SQLite), mismo frontend (React) y las mismas reglas de estilo. Las reglas de negocio están en `contexto/reglas_vacaciones.md`.

## Datos

- El empleado necesita una `fecha_ingreso` (texto `YYYY-MM-DD`). Si el modelo de HU-01 todavía no la tiene, se agrega como campo del empleado sin cambiar el comportamiento de HU-01 a HU-03.
- Nueva tabla `vacaciones`: `id`, `empleado_id`, `fecha_inicio`, `fecha_fin`, `dias_habiles`.
- Las fechas viajan siempre como texto `YYYY-MM-DD`.

## API

### Registrar una solicitud

`POST /api/empleados/{empleado_id}/vacaciones`

```json
{ "fecha_inicio": "2026-12-21", "fecha_fin": "2026-12-31" }
```

Respuesta `201`:

```json
{
  "id": 1,
  "empleado_id": 7,
  "fecha_inicio": "2026-12-21",
  "fecha_fin": "2026-12-31",
  "dias_habiles": 8,
  "dias_restantes": 4
}
```

`dias_restantes` son los días hábiles que le quedan al empleado en el año de la solicitud, ya descontada esta.

### Consultar el saldo del año

`GET /api/empleados/{empleado_id}/vacaciones?anio=2026`

Respuesta `200`:

```json
{
  "empleado_id": 7,
  "anio": 2026,
  "dias_usados": 8,
  "dias_disponibles": 4,
  "solicitudes": [
    { "id": 1, "fecha_inicio": "2026-12-21", "fecha_fin": "2026-12-31", "dias_habiles": 8 }
  ]
}
```

Si no se manda `anio`, se usa el año en curso.

## Errores: mensajes exactos

Todos los errores responden con el formato estándar de FastAPI, `{"detail": "<mensaje>"}`, con **exactamente** estos códigos y textos. El orden de la tabla es el orden en que se validan: se devuelve el primer error que aplique.

| Caso | Código | `detail` |
|---|---|---|
| El empleado no existe | 404 | `Empleado no encontrado` |
| El empleado está dado de baja | 409 | `No se pueden solicitar vacaciones para un empleado dado de baja` |
| `fecha_fin` es anterior a `fecha_inicio` | 400 | `La fecha de fin no puede ser anterior a la fecha de inicio` |
| El periodo cruza de un año a otro | 400 | `Las vacaciones deben estar dentro de un mismo año calendario` |
| El año no está en la tabla de festivos | 400 | `Solo se pueden solicitar vacaciones en 2026 y 2027` |
| Regla 1: menos de un año de antigüedad | 400 | `Se requiere al menos un año de antigüedad a la fecha de inicio` |
| Regla 3: el periodo no tiene días hábiles | 400 | `El periodo no incluye días hábiles` |
| Regla 2: rebasa los días disponibles | 400 | `La solicitud excede los días disponibles: quedan N días hábiles` |

En el último mensaje, `N` es el número de días que quedan en el año de la solicitud, por ejemplo `quedan 4 días hábiles` o `quedan 0 días hábiles`. Siempre se escribe `días hábiles`, también cuando `N` es 1.

Una fecha con formato inválido la rechaza FastAPI con su `422` automático; no hace falta un mensaje propio.

## Pantalla

- En el directorio de empleados, cada empleado activo tiene un botón **Solicitar vacaciones** que abre el formulario.
- El formulario muestra el saldo del año y, al enviar, el resultado: el mensaje de éxito o el `detail` exacto del error que devolvió la API.

`data-testid` obligatorios, para las pruebas E2E:

| Elemento | `data-testid` |
|---|---|
| Botón que abre el formulario (uno por empleado) | `vacaciones-abrir-{empleado_id}` |
| Campo de fecha de inicio | `vacaciones-fecha-inicio` |
| Campo de fecha de fin | `vacaciones-fecha-fin` |
| Botón de enviar | `vacaciones-enviar` |
| Días disponibles en el año | `vacaciones-disponibles` |
| Mensaje de resultado (éxito o error) | `vacaciones-mensaje` |

Mensaje de éxito exacto en `vacaciones-mensaje`: `Solicitud registrada: N días hábiles. Te quedan M días hábiles en AAAA.`

## HU-10 · Compatibilidad y decisiones de implementación

Esta sección resuelve las diferencias entre las convenciones de vacaciones (arriba) y la Guía del reto. Si algo choca, manda lo que dice aquí.

### 1. Fuente de verdad

- Mandan `convenciones_vacaciones.md` y `reglas_vacaciones.md` (su contenido está copiado arriba en este archivo y al final de las reglas de negocio). Los 422 y los textos de la Guía del reto no se usan.
- Códigos y `detail` exactos, en el orden en que se validan (se devuelve el primero que aplique):

| Caso | Código | `detail` |
|---|---|---|
| El empleado no existe | 404 | `Empleado no encontrado` |
| El empleado está dado de baja | 409 | `No se pueden solicitar vacaciones para un empleado dado de baja` |
| `fecha_fin` es anterior a `fecha_inicio` | 400 | `La fecha de fin no puede ser anterior a la fecha de inicio` |
| El periodo cruza de un año a otro | 400 | `Las vacaciones deben estar dentro de un mismo año calendario` |
| El año no está en la tabla de festivos | 400 | `Solo se pueden solicitar vacaciones en 2026 y 2027` |
| Regla 1: menos de un año de antigüedad | 400 | `Se requiere al menos un año de antigüedad a la fecha de inicio` |
| Regla 3: el periodo no tiene días hábiles | 400 | `El periodo no incluye días hábiles` |
| Regla 2: rebasa los días disponibles | 400 | `La solicitud excede los días disponibles: quedan N días hábiles` |

### 2. Campos extra compatibles

- `POST /api/empleados/{empleado_id}/vacaciones` → 201 con `id`, `empleado_id`, `fecha_inicio`, `fecha_fin`, `dias_habiles`, `dias_restantes` **y** `dias_disponibles` (los dos con el mismo valor).
- `GET /api/empleados/{empleado_id}/vacaciones?anio=AAAA` → 200 con `empleado_id`, `anio`, `dias_por_anio` (siempre 12), `dias_usados`, `dias_disponibles` y `solicitudes`.
- Si no se manda `anio`, se usa el año en curso.

### 3. Backend

- Los días hábiles se calculan **solo en el backend**, en el módulo `backend/vacaciones.py`, con un dict `FESTIVOS = {2026: [...], 2027: [...]}` que sale de la tabla de festivos de las reglas de vacaciones. El frontend nunca los calcula.
- El conteo incluye la fecha de inicio y la de fin.
- Aniversario: el mismo día y mes del año siguiente. Si cae en 29 de febrero y ese año no es bisiesto, se toma el 1 de marzo.
- Nueva tabla `vacaciones` (`id`, `empleado_id`, `fecha_inicio`, `fecha_fin`, `dias_habiles`). La crea `create_all` sola, sin migraciones.
- **No** se agregan columnas a `empleados`: `fecha_ingreso` y `estado` ya existen.
- Los endpoints de HU-01 a HU-03 no cambian.

### 4. Frontend

Los `data-testid` de las convenciones y los de la Guía van anidados para que funcionen los dos juegos:

```html
<button data-testid="vacaciones-abrir-{id}"><span data-testid="vacaciones-empleado-{id}">Solicitar vacaciones</span></button>
<button data-testid="vacaciones-enviar"><span data-testid="vacaciones-solicitar">Solicitar</span></button>
<div data-testid="vacaciones-mensaje"><span data-testid="mensaje-exito|mensaje-error">texto</span></div>
```

- El texto de `vacaciones-mensaje` es exactamente el `detail` del error o `Solicitud registrada: N días hábiles. Te quedan M días hábiles en AAAA.`
- Campos de fecha (`type="date"`): `vacaciones-fecha-inicio` y `vacaciones-fecha-fin`.
- `vacaciones-disponibles` contiene solo el número.
- Lista de solicitudes: `tabla-vacaciones`, `fila-vacaciones-{id}` y `dias-vacaciones-{id}`.
- El botón solo aparece en empleados con estado «activo».
- El panel se muestra dentro del directorio. Sus mensajes no deben duplicar un `mensaje-exito` o `mensaje-error` del directorio que ya esté visible (al abrir el panel, se limpia el mensaje del directorio).

### 5. Pruebas

- Las pruebas nunca escriben directo en la base de datos (ni SQLite ni sesiones de SQLAlchemy). Los datos se preparan solo con la API.
