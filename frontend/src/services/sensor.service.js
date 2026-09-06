import adapter from './adapter.js'

const sensorService = {
  getSensors() {
    return adapter.get('/api/sensors')
  },

  createSensor(data) {
    return adapter.post('/api/sensors', data)
  },

  getSensor(id) {
    return adapter.get(`/api/sensors/${id}`)
  },

  updateSensor(id, data) {
    return adapter.patch(`/api/sensors/${id}`, data)
  },
}

export default sensorService