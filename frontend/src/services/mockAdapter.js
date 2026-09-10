// MOCK ADAPTER — responses adhering to the same OpenAPI contract (Week 1 parallel).

import { alerts } from './fixtures/alerts.js'
import { readings } from './fixtures/readings.js'
import { sensors } from './fixtures/sensors.js'
import { sites } from './fixtures/sites.js'


const mockUser = { //fictitious user, used when the frontend requests "GET /api/me"
  id: '99999999-9999-4999-8999-999999999999',
  email: 'mock@example.com',
  name: 'Mock User',
  role: 'admin',
  organization_id: null,
  created_at: '2026-08-01T08:00:00Z',
}

let isAuthenticated = true

/*
We create an object that
has the same methods as httpAdapter.
It returns a promise
that is already resolved, with the data we want,
to replicate the behavior of the real adapter.
*/

const mockAdapter = {
  get(url, config = {}) {
    console.log('[MOCK GET]', url, config)

    // Get all sites
    if (url === '/api/sites') { //= endpoint
      return Promise.resolve({ // = "Create a Promise (that is already resolved) with the value below"
        data: {
          // Paginated response: current page, number of items, and total pages
          items: sites,
          total: sites.length,
          page: 1,
          page_size: Math.max(sites.length, 1),
          pages: sites.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get all sensors
    if (url === '/api/sensors') {
      return Promise.resolve({
        data: {
          items: sensors,
          total: sensors.length,
          page: 1,
          page_size: Math.max(sensors.length, 1),
          pages: sensors.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get sensors belonging to a specific site
    if (url.startsWith('/api/sites/') && url.endsWith('/sensors')) {
      const siteId = url.split('/')[3]

      const site = sites.find((site) => site.id === siteId) //searching the site in the array

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found',
          details: null,
        })
      }

      const siteSensors = sensors.filter( //Keeps only the elements that meet this condition
        (sensor) => sensor.site_id === siteId 
      )

      return Promise.resolve({
        data: {
          items: siteSensors,
          total: siteSensors.length,
          page: 1,
          page_size: Math.max(siteSensors.length, 1),
          pages: siteSensors.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get a specific site
    if (url.startsWith('/api/sites/')) {
      const id = url.split('/')[3]

      const site = sites.find((site) => site.id === id)

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found',
          details: null,
        })
      }

      return Promise.resolve({
        data: site,
        status: 200,
      })
    }

    // Get readings belonging to a specific sensor
    if (
      url.startsWith('/api/sensors/') &&
      url.endsWith('/readings')
    ) {
      const sensorId = url.split('/')[3]

      const sensor = sensors.find((sensor) => sensor.id === sensorId)

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found',
          details: null,
        })
      }

      const sensorReadings = readings.filter(
        (reading) => reading.sensor_id === sensorId
      )

      return Promise.resolve({
        data: {
          items: sensorReadings,
          total: sensorReadings.length,
          page: 1,
          page_size: Math.max(sensorReadings.length, 1),
          pages: sensorReadings.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get a specific sensor
    if (url.startsWith('/api/sensors/')) {
      const id = url.split('/')[3] // splits the url string at every "/", retrieves the 4th element, and stores it in the variable

      const sensor = sensors.find((sensor) => sensor.id === id)

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found',
          details: null,
        })
      }

      return Promise.resolve({
        data: sensor,
        status: 200,
      })
    }

    // Get all alerts
    if (url === '/api/alerts') {
      return Promise.resolve({
        data: {
          items: alerts,
          total: alerts.length,
          page: 1,
          page_size: Math.max(alerts.length, 1),
          pages: alerts.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get the currently authenticated user
    if (url === '/api/me') {
      if (!isAuthenticated) {
        return Promise.reject({
          status: 401,
          code: 'UNAUTHORIZED',
          message: 'Authentication required.',
          details: null,
        })
      }

      return Promise.resolve({
        data: {
          user: mockUser,
        },
        status: 200,
      })
    }

    // Unknown endpoint
    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found.',
      details: null,
    })
  },

  post(url, data = {}, config = {}) {
    console.log('[MOCK POST]', url, data, config)

    // Register
    if (url === '/api/auth/register') {
      return Promise.resolve({
        data: {
          user: mockUser,
        },
        status: 201,
      })
    }

    // Login
    if (url === '/api/auth/login') {
      isAuthenticated = true

      return Promise.resolve({
        data: {
          user: mockUser,
        },
        status: 200,
      })
    }

    // Logout
    if (url === '/api/auth/logout') {
      isAuthenticated = false

      return Promise.resolve({
        data: {
          message: 'Session closed.',
        },
        status: 200,
      })
    }

    // Create a reading
    if (url === '/api/readings') {
      const sensor = sensors.find(
        (sensor) => sensor.id === data.sensor_id
      )

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found',
          details: null,
        })
      }

      if (data.pressure < 0 || data.pressure > 25) {
        return Promise.reject({
            status: 422,
            code: 'VALIDATION_ERROR',
            message: 'Invalid request.',
            details: [
            {
                field: 'pressure',
                message: 'Pressure must be between 0 and 25 bar.',
                type: 'value_error',
            },
            ],
        })
      }

      const reading = {
        id: crypto.randomUUID(),
        sensor_id: data.sensor_id,
        pressure: data.pressure,
        measured_at:
          data.measured_at ?? new Date().toISOString(), // = If value on the left is null or undefined, then use the one on the right
        created_at: new Date().toISOString(),
      }

      readings.push(reading) //= Add `reading` to the end of the `readings` array
      
      return Promise.resolve({
        data: reading,
        status: 201, // = created with succes
      })
    }

    // Create a sensor
    if (url === '/api/sensors') {
      const site = sites.find(
        (site) => site.id === data.site_id
      )

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found',
          details: null,
        })
      }

      if (
        data.min_pressure < 0 ||
        data.min_pressure > 25 ||
        data.max_pressure < 0 ||
        data.max_pressure > 25 ||
        data.min_pressure >= data.max_pressure
        ) {
        return Promise.reject({
            status: 422,
            code: 'VALIDATION_ERROR',
            message: 'Invalid request.',
            details: [
            {
                field: 'min_pressure',
                message: 'min_pressure must be lower than max_pressure.',
                type: 'value_error',
            },
            ],
        })
      }

      const sensor = {
        id: crypto.randomUUID(),
        site_id: data.site_id,
        name: data.name,
        location: data.location ?? null,
        sensor_type: data.sensor_type ?? 'PRESSURE',
        min_pressure: data.min_pressure,
        max_pressure: data.max_pressure,
        status: 'ONLINE',
        last_seen_at: null,
        created_at: new Date().toISOString(),
      }

      sensors.push(sensor)

      return Promise.resolve({
        data: sensor,
        status: 201,
      })
    }

   // Unknown endpoint
     return Promise.reject({
        status: 404,
        code: 'UNKNOWN_ENDPOINT',
        message: 'Mock endpoint not found.',
        details: null,
    })
  },

  patch(url, data = {}, config = {}) {
    console.log('[MOCK PATCH]', url, data, config)

    // Acknowledge an alert
    if (url.endsWith('/acknowledge')) {
      const id = url.split('/')[3]

      const alert = alerts.find((alert) => alert.id === id)

      if (!alert) {
        return Promise.reject({
          status: 404,
          code: 'ALERT_NOT_FOUND',
          message: 'Alert not found',
          details: null,
        })
      }

      alert.acknowledged_at = new Date().toISOString()

      return Promise.resolve({
        data: alert,
        status: 200,
      })
    }

    // Resolve an alert
    if (url.endsWith('/resolve')) {
      const id = url.split('/')[3]

      const alert = alerts.find((alert) => alert.id === id)

      if (!alert) {
        return Promise.reject({
          status: 404,
          code: 'ALERT_NOT_FOUND',
          message: 'Alert not found',
          details: null,
        })
      }

      alert.status = 'RESOLVED'
      alert.resolved_at = new Date().toISOString()

      return Promise.resolve({
        data: alert,
        status: 200,
      })
    }

    // Update a sensor
    if (
      url.startsWith('/api/sensors/') &&
      !url.endsWith('/readings')
    ) {
      const id = url.split('/')[3]

      const sensor = sensors.find(
        (sensor) => sensor.id === id
      )

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found',
          details: null,
        })
      }

      if (
        (data.min_pressure !== undefined &&
            (data.min_pressure < 0 || data.min_pressure > 25)) ||
        (data.max_pressure !== undefined &&
            (data.max_pressure < 0 || data.max_pressure > 25)) ||
        (
            data.min_pressure !== undefined &&
            data.max_pressure !== undefined &&
            data.min_pressure >= data.max_pressure
        ) ||
        (
            data.min_pressure !== undefined &&
            data.max_pressure === undefined &&
            data.min_pressure >= sensor.max_pressure
        ) ||
        (
            data.max_pressure !== undefined &&
            data.min_pressure === undefined &&
            data.max_pressure <= sensor.min_pressure
        )
        ) {
        return Promise.reject({
            status: 422,
            code: 'VALIDATION_ERROR',
            message: 'Invalid request.',
            details: [
            {
                field: 'min_pressure',
                message: 'min_pressure must be lower than max_pressure.',
                type: 'value_error',
            },
          ],
        })
      }

      Object.assign(sensor, {
        ...(data.name !== undefined && {
          name: data.name,
        }),
        ...(data.location !== undefined && {
          location: data.location,
        }),
        ...(data.min_pressure !== undefined && {
          min_pressure: data.min_pressure,
        }),
        ...(data.max_pressure !== undefined && {
          max_pressure: data.max_pressure,
        }),
      })

      return Promise.resolve({
        data: sensor,
        status: 200,
      })
    }

    // Unknown endpoint
    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found',
      details: null,
    })
  },

  delete(url, config = {}) {
    console.log('[MOCK DELETE]', url, config)

    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found.',
      details: null,
    })
  },
}

export default mockAdapter

/*Here is exactly what the services tell us the MockAdapter must support: :

Domaine	Méthode	Endpoint
Auth	POST	/api/auth/register
Auth	POST	/api/auth/login
Auth	POST	/api/auth/logout
Auth	GET	/api/me
Sites	GET	/api/sites
Sites	GET	/api/sites/{id}
Sites	GET	/api/sites/{id}/sensors
Sensors	GET	/api/sensors
Sensors	GET	/api/sensors/{id}
Sensors	POST	/api/sensors
Sensors	PATCH	/api/sensors/{id}
Readings	POST	/api/readings
Readings	GET	/api/sensors/{id}/readings
Alerts	GET	/api/alerts
Alerts	PATCH	/api/alerts/{id}/acknowledge
Alerts	PATCH	/api/alerts/{id}/resolve
*/


/*
All endpoints work the same way; GET request essentially does this:

Which URL is being requested?
        ↓
Check the corresponding `if` statement
        ↓
Fetch the data
        ↓
Verify that it exists
        ↓
Return a Promise
*/