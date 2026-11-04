import { useState } from 'react'

const DEPARTAMENTOS = ['Tecnología', 'Ventas', 'Finanzas', 'Recursos Humanos', 'Operaciones']

const DATOS_VACIOS = {
  nombre: '',
  correo: '',
  puesto: '',
  departamento: DEPARTAMENTOS[0],
  fecha_ingreso: '',
}

function FormularioEmpleado() {
  const [datos, setDatos] = useState(DATOS_VACIOS)
  const [mensajeExito, setMensajeExito] = useState('')
  const [mensajeError, setMensajeError] = useState('')

  function actualizarCampo(campo, valor) {
    setDatos((anterior) => ({ ...anterior, [campo]: valor }))
  }

  async function guardar(evento) {
    evento.preventDefault()
    setMensajeExito('')
    setMensajeError('')

    try {
      const respuesta = await fetch('/api/empleados', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos),
      })
      const cuerpo = await respuesta.json()

      if (!respuesta.ok) {
        setMensajeError(cuerpo.detail || 'No se pudo registrar al empleado')
        return
      }

      setMensajeExito(`Empleado registrado con número ${cuerpo.numero_empleado}`)
      setDatos(DATOS_VACIOS)
    } catch {
      setMensajeError('No se pudo conectar con el servidor')
    }
  }

  return (
    <form onSubmit={guardar}>
      <h1>Registrar empleado</h1>

      <label>
        Nombre
        <input
          data-testid="empleado-nombre"
          value={datos.nombre}
          onChange={(e) => actualizarCampo('nombre', e.target.value)}
          required
        />
      </label>

      <label>
        Correo
        <input
          data-testid="empleado-correo"
          type="email"
          value={datos.correo}
          onChange={(e) => actualizarCampo('correo', e.target.value)}
          required
        />
      </label>

      <label>
        Puesto
        <input
          data-testid="empleado-puesto"
          value={datos.puesto}
          onChange={(e) => actualizarCampo('puesto', e.target.value)}
          required
        />
      </label>

      <label>
        Departamento
        <select
          data-testid="empleado-departamento"
          value={datos.departamento}
          onChange={(e) => actualizarCampo('departamento', e.target.value)}
        >
          {DEPARTAMENTOS.map((departamento) => (
            <option key={departamento} value={departamento}>
              {departamento}
            </option>
          ))}
        </select>
      </label>

      <label>
        Fecha de ingreso
        <input
          data-testid="empleado-fecha-ingreso"
          type="date"
          value={datos.fecha_ingreso}
          onChange={(e) => actualizarCampo('fecha_ingreso', e.target.value)}
          required
        />
      </label>

      <button type="submit" data-testid="empleado-guardar">
        Guardar
      </button>

      {mensajeExito && <p data-testid="mensaje-exito">{mensajeExito}</p>}
      {mensajeError && <p data-testid="mensaje-error">{mensajeError}</p>}
    </form>
  )
}

export default FormularioEmpleado
