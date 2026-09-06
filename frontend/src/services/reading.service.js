import adapter from './adapter.js'

const readingService = {
// Create a new reading for a sensor
  createReading(data) {
    return adapter.post('/api/readings', data)
  },

// Get all readings recorded by a specific sensor
  getSensorReadings(sensorId) {
    return adapter.get(`/api/sensors/${sensorId}/readings`)
  },
}

export default readingService