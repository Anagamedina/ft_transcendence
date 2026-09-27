import adapter from './adapter.js'

const alertService = {
  getAlerts() {
    return adapter.get('/api/alerts')
  },

  acknowledgeAlert(id) { //Indicates to the system that the alert has been acknowledged
    return adapter.patch(`/api/alerts/${id}/acknowledge`)
  },

  resolveAlert(id) {
    return adapter.patch(`/api/alerts/${id}/resolve`)
  },
}

export default alertService