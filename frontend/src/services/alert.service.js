import adapter from './adapter.js'

const alertService = {
  getAlerts() {
    return adapter.get('/api/alerts')
  },

  acknowledgeAlert(id) { //Indicar al sistema que se ha tomado conocimiento de la alerta.
    return adapter.patch(`/api/alerts/${id}/acknowledge`)
  },

  resolveAlert(id) {
    return adapter.patch(`/api/alerts/${id}/resolve`)
  },
}

export default alertService