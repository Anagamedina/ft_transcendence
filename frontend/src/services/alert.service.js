import httpAdapter from './httpAdapter.js'

const alertService = {
  getAlerts() {
    return httpAdapter.get('/api/alerts')
  },

  acknowledgeAlert(id) { //Indicar al sistema que se ha tomado conocimiento de la alerta.
    return httpAdapter.patch(`/api/alerts/${id}/acknowledge`)
  },

  resolveAlert(id) {
    return httpAdapter.patch(`/api/alerts/${id}/resolve`)
  },
}

export default alertService