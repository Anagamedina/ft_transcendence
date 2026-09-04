import httpAdapter from './httpAdapter.js'

const sensorService = {
  getSensors() {
    return httpAdapter.get('/api/sensors')
  },

  createSensor(data) {
    return httpAdapter.post('/api/sensors', data)
  },

  getSensor(id) {
    return httpAdapter.get(`/api/sensors/${id}`)
  },

  updateSensor(id, data) {
    return httpAdapter.patch(`/api/sensors/${id}`, data)
  },
}

export default sensorService