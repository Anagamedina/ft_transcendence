import adapter from "./adapter.js";

const readingService = {
  // Create a new reading for a sensor
  createReading(data) {
    return adapter.post("/api/readings", data);
  },

  // Get all readings recorded by a specific sensor
  getSensorReadings(sensorId) {
    return adapter.get(`/api/sensors/${sensorId}/readings`);
  },

  // Pressure of the last `days` days grouped in buckets, for the chart (B7).
  // -> { unit, min_pressure, max_pressure, bucket, from, to, points: [{ t, avg, min, max }] }
  // params (optional): { days = 7, bucket = '2h' }
  getSensorSeries(sensorId, params = {}) {
    return adapter.get(`/api/sensors/${sensorId}/readings/series`, { params });
  },
};

export default readingService;
