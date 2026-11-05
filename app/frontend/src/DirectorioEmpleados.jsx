import { Fragment, useEffect, useState } from 'react'
import PanelVacaciones from './PanelVacaciones.jsx'

const ESTADOS = {
  activo: 'Activo',
  baja: 'Baja',
}

const DEPARTAMENTOS_FIJOS = ['Tecnología', 'Ventas', 'Finanzas', 'Recursos Humanos', 'Operaciones']

function FilaEmpleado({ empleado, onCambio, onMensaje, onAbrirVacaciones }) {
  const [modo, setModo] = useState(null) // null | 'editar' | 'baja'
  const [puesto, setPuesto] = useState(empleado.puesto)
  const [departamento, setDepartamento] = useState(empleado.departamento)
  const [fechaBaja, setFechaBaja] = useState('')

  function cancelar() {
    setModo(null)
    setPuesto(empleado.puesto)
    setDepartamento(empleado.departamento)
    setFechaBaja('')
  }

  async function guardarEdicion() {
    onMensaje('', '')
    try {
      const respuesta = await fetch(`/api/empleados/${empleado.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ puesto, departamento }),
      })
      const cuerpo = await respuesta.json()

      if (!respuesta.ok) {
        onMensaje('', cuerpo.detail || 'No se pudo editar al empleado')
        return
      }

      onMensaje('Empleado actualizado correctamente', '')
      setModo(null)
      onCambio()
    } catch {
      onMensaje('', 'No se pudo conectar con el servidor')
    }
  }

  async function confirmarBaja() {
    onMensaje('', '')
    try {
      const respuesta = await fetch(`/api/empleados/${empleado.id}/baja`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fecha_baja: fechaBaja }),
      })
      const cuerpo = await respuesta.json()

      if (!respuesta.ok) {
        onMensaje('', cuerpo.detail || 'No se pudo dar de baja al empleado')
        return
      }

      onMensaje('Empleado dado de baja correctamente', '')
      setModo(null)
      onCambio()
    } catch {
      onMensaje('', 'No se pudo conectar con el servidor')
    }
  }

  return (
    <tr data-testid={`fila-empleado-${empleado.id}`}>
      <td data-testid={`numero-empleado-${empleado.id}`}>{empleado.numero_empleado}</td>
      <td>{empleado.nombre}</td>
      <td>
        {modo === 'editar' ? (
          <input
            data-testid="empleado-puesto"
            value={puesto}
            onChange={(e) => setPuesto(e.target.value)}
          />
        ) : (
          empleado.puesto
        )}
      </td>
      <td>
        {modo === 'editar' ? (
          <select
            data-testid="empleado-departamento"
            value={departamento}
            onChange={(e) => setDepartamento(e.target.value)}
          >
            {DEPARTAMENTOS_FIJOS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        ) : (
          empleado.departamento
        )}
      </td>
      <td data-testid={`estado-empleado-${empleado.id}`}>{ESTADOS[empleado.estado] || empleado.estado}</td>
      <td>
        {modo === 'editar' && (
          <>
            <button data-testid="empleado-guardar" onClick={guardarEdicion}>
              Guardar
            </button>
            <button onClick={cancelar}>Cancelar</button>
          </>
        )}
        {modo === 'baja' && (
          <>
            <input
              data-testid="empleado-fecha-baja"
              type="date"
              value={fechaBaja}
              onChange={(e) => setFechaBaja(e.target.value)}
            />
            <button data-testid="confirmar-baja" onClick={confirmarBaja}>
              Confirmar baja
            </button>
            <button onClick={cancelar}>Cancelar</button>
          </>
        )}
        {modo === null && (
          <>
            <button data-testid={`editar-empleado-${empleado.id}`} onClick={() => setModo('editar')}>
              Editar
            </button>
            {empleado.estado !== 'baja' && (
              <button data-testid={`baja-empleado-${empleado.id}`} onClick={() => setModo('baja')}>
                Dar de baja
              </button>
            )}
            {empleado.estado === 'activo' && (
              <button
                data-testid={`vacaciones-abrir-${empleado.id}`}
                onClick={() => onAbrirVacaciones(empleado.id)}
              >
                <span data-testid={`vacaciones-empleado-${empleado.id}`}>Solicitar vacaciones</span>
              </button>
            )}
          </>
        )}
      </td>
    </tr>
  )
}

function DirectorioEmpleados() {
  const [empleados, setEmpleados] = useState([])
  const [departamentos, setDepartamentos] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [departamento, setDepartamento] = useState('')
  const [mensajeExito, setMensajeExito] = useState('')
  const [mensajeError, setMensajeError] = useState('')
  const [empleadoVacacionesAbiertoId, setEmpleadoVacacionesAbiertoId] = useState(null)

  useEffect(() => {
    fetch('/api/departamentos')
      .then((respuesta) => respuesta.json())
      .then(setDepartamentos)
      .catch(() => setDepartamentos([]))
  }, [])

  function cargarEmpleados() {
    const parametros = new URLSearchParams()
    if (busqueda) parametros.set('busqueda', busqueda)
    if (departamento) parametros.set('departamento', departamento)

    fetch(`/api/empleados?${parametros.toString()}`)
      .then((respuesta) => respuesta.json())
      .then(setEmpleados)
      .catch(() => setEmpleados([]))
  }

  useEffect(cargarEmpleados, [busqueda, departamento])

  function mostrarMensaje(exito, error) {
    setMensajeExito(exito)
    setMensajeError(error)
  }

  function abrirVacaciones(id) {
    mostrarMensaje('', '')
    setEmpleadoVacacionesAbiertoId(id)
  }

  function cerrarVacaciones() {
    setEmpleadoVacacionesAbiertoId(null)
  }

  return (
    <section>
      <h1>Directorio de empleados</h1>

      <input
        data-testid="buscar-empleados"
        placeholder="Buscar por nombre o correo"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />

      <select
        data-testid="filtro-departamento"
        value={departamento}
        onChange={(e) => setDepartamento(e.target.value)}
      >
        <option value="">Todos</option>
        {departamentos.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      {mensajeExito && <p data-testid="mensaje-exito">{mensajeExito}</p>}
      {mensajeError && <p data-testid="mensaje-error">{mensajeError}</p>}

      {empleados.length === 0 ? (
        <p data-testid="sin-resultados">No se encontraron empleados</p>
      ) : (
        <table data-testid="tabla-empleados">
          <thead>
            <tr>
              <th>Número</th>
              <th>Nombre</th>
              <th>Puesto</th>
              <th>Departamento</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {empleados.map((empleado) => (
              <Fragment key={empleado.id}>
                <FilaEmpleado
                  empleado={empleado}
                  onCambio={cargarEmpleados}
                  onMensaje={mostrarMensaje}
                  onAbrirVacaciones={abrirVacaciones}
                />
                {empleadoVacacionesAbiertoId === empleado.id && (
                  <PanelVacaciones empleado={empleado} onCerrar={cerrarVacaciones} />
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default DirectorioEmpleados
