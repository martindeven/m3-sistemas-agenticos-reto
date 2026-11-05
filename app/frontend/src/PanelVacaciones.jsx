import { useEffect, useState } from 'react'

function PanelVacaciones({ empleado, onCerrar }) {
  const [saldo, setSaldo] = useState(null)
  const [fechaInicio, setFechaInicio] = useState('')
  const [fechaFin, setFechaFin] = useState('')
  const [mensajeExito, setMensajeExito] = useState('')
  const [mensajeError, setMensajeError] = useState('')

  function cargarSaldo() {
    fetch(`/api/empleados/${empleado.id}/vacaciones`)
      .then((respuesta) => respuesta.json())
      .then(setSaldo)
      .catch(() => setSaldo(null))
  }

  useEffect(cargarSaldo, [empleado.id])

  async function enviar() {
    setMensajeExito('')
    setMensajeError('')
    try {
      const respuesta = await fetch(`/api/empleados/${empleado.id}/vacaciones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fecha_inicio: fechaInicio, fecha_fin: fechaFin }),
      })
      const cuerpo = await respuesta.json()

      if (!respuesta.ok) {
        setMensajeError(cuerpo.detail || 'No se pudo registrar la solicitud')
        return
      }

      const anio = cuerpo.fecha_inicio.slice(0, 4)
      setMensajeExito(
        `Solicitud registrada: ${cuerpo.dias_habiles} días hábiles. Te quedan ${cuerpo.dias_restantes} días hábiles en ${anio}.`
      )
      setFechaInicio('')
      setFechaFin('')
      cargarSaldo()
    } catch {
      setMensajeError('No se pudo conectar con el servidor')
    }
  }

  return (
    <tr data-testid={`panel-vacaciones-${empleado.id}`}>
      <td colSpan={6}>
        <h2>Vacaciones de {empleado.nombre}</h2>
        <button onClick={onCerrar}>Cerrar</button>

        <p>
          Días disponibles:{' '}
          <span data-testid="vacaciones-disponibles">{saldo ? saldo.dias_disponibles : ''}</span>
        </p>

        <label>
          Fecha de inicio
          <input
            data-testid="vacaciones-fecha-inicio"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
          />
        </label>

        <label>
          Fecha de fin
          <input
            data-testid="vacaciones-fecha-fin"
            type="date"
            value={fechaFin}
            onChange={(e) => setFechaFin(e.target.value)}
          />
        </label>

        <button data-testid="vacaciones-enviar" onClick={enviar}>
          <span data-testid="vacaciones-solicitar">Solicitar</span>
        </button>

        {(mensajeExito || mensajeError) && (
          <div data-testid="vacaciones-mensaje">
            {mensajeExito && <span data-testid="mensaje-exito">{mensajeExito}</span>}
            {mensajeError && <span data-testid="mensaje-error">{mensajeError}</span>}
          </div>
        )}

        {saldo && saldo.solicitudes.length > 0 && (
          <table data-testid="tabla-vacaciones">
            <thead>
              <tr>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Días hábiles</th>
              </tr>
            </thead>
            <tbody>
              {saldo.solicitudes.map((solicitud) => (
                <tr key={solicitud.id} data-testid={`fila-vacaciones-${solicitud.id}`}>
                  <td>{solicitud.fecha_inicio}</td>
                  <td>{solicitud.fecha_fin}</td>
                  <td data-testid={`dias-vacaciones-${solicitud.id}`}>{solicitud.dias_habiles}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </td>
    </tr>
  )
}

export default PanelVacaciones
