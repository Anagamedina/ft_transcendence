// MOCK ADAPTER — responses adhering to the same OpenAPI contract (Week 1 parallel)

import { alerts } from './fixtures/alerts.js'
import { readings } from './fixtures/readings.js'
import { sensors } from './fixtures/sensors.js'
import { sites } from './fixtures/sites.js'
import { systemStatus } from './fixtures/status.js'

// Mock users used for authentication tests.
const mockUser = [
  {
    id: "99999999-9999-4999-8999-999999999999",
    email: "test@example.com",
    name: "Mock Admin",
    role: "admin",
    organization_id: null,
    created_at: "2026-08-01T08:00:00Z",
    password: "123",
  },
  {
    id: "88888888-8888-4888-8888-888888888888",
    email: "client@example.com",
    name: "Mock Client",
    role: "client",
    organization_id: null,
    created_at: "2026-08-01T08:00:00Z",
    password: "123",
  },
]

let currentUser = null

const MOCK_SESSION_KEY = "aquaguard_mock_user_id";

function restoreMockUser() {
  const userId = localStorage.getItem(MOCK_SESSION_KEY);

  currentUser = mockUser.find((user) => user.id === userId) ?? null;
}

restoreMockUser();

// Remove the password before returning a user to the frontend.
function toPublicUser(user) {
  if (!user) return null

  const { password, ...publicUser } = user
  return publicUser
}

/*
 * The mock adapter exposes the same methods as httpAdapter.
 * Each method returns a Promise to simulate an HTTP response.
 */

const mockAdapter = {
  // GET requests
  get(url, config = {}) {
    console.log('[MOCK GET]', url, config)

    // Get the currently authenticated user.
    if (url === '/api/me') {
      if (!currentUser) {
        return Promise.reject({
          status: 401,
          code: 'UNAUTHORIZED',
          message: 'Authentication required.',
          details: null,
        })
      }

      return Promise.resolve({
        data: {
          user: toPublicUser(currentUser),
        },
        status: 200,
      })
    }

    // Get the public status page data.
    if (url === '/api/status') {
      return Promise.resolve({
        data: systemStatus,
        status: 200,
      })
    }

    // Get all sites.
    if (url === '/api/sites') {
      return Promise.resolve({
        data: {
          items: sites,
          total: sites.length,
          page: 1,
          page_size: Math.max(sites.length, 1),
          pages: sites.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Get all sensors.
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

    // Get sensors belonging to a specific site.
    if (
      url.startsWith('/api/sites/') &&
      url.endsWith('/sensors')
    ) {
      const siteId = url.split('/')[3]
      const site = sites.find((site) => site.id === siteId)

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found.',
          details: null,
        })
      }

      const siteSensors = sensors.filter(
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

    // Get a specific site.
    if (url.startsWith('/api/sites/')) {
      const id = url.split('/')[3]
      const site = sites.find((site) => site.id === id)

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found.',
          details: null,
        })
      }

      return Promise.resolve({
        data: site,
        status: 200,
      })
    }

    // Get readings belonging to a specific sensor.
    if (
      url.startsWith('/api/sensors/') &&
      url.endsWith('/readings')
    ) {
      const sensorId = url.split('/')[3]
      const sensor = sensors.find(
        (sensor) => sensor.id === sensorId
      )

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found.',
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

    // Get a specific sensor.
    if (url.startsWith('/api/sensors/')) {
      const id = url.split('/')[3]
      const sensor = sensors.find(
        (sensor) => sensor.id === id
      )

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found.',
          details: null,
        })
      }

      return Promise.resolve({
        data: sensor,
        status: 200,
      })
    }

    // Get all alerts.
    if (url === '/api/alerts') {
      return Promise.resolve({
        data: {
          items: alerts.map((alert) => ({ ...alert })),
          total: alerts.length,
          page: 1,
          page_size: Math.max(alerts.length, 1),
          pages: alerts.length === 0 ? 0 : 1,
        },
        status: 200,
      })
    }

    // Handle unknown endpoints.
    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found.',
      details: null,
    })
  },

  // POST requests
  post(url, data = {}, config = {}) {
    if (url.startsWith('/api/auth/')) {
      console.log('[MOCK POST]', url)
    } else {
      console.log('[MOCK POST]', url, data, config)
    }

    // Register a new mock client.
    if (url === '/api/auth/register') {
      const email = data.email

      if (
        typeof email !== 'string' ||
        !email.trim()
      ) {
        return Promise.reject({
          status: 422,
          code: 'VALIDATION_ERROR',
          message: 'A valid email is required.',
          details: null,
        })
      }

      if (mockUser.some((user) => user.email === email)) {
        return Promise.reject({
          status: 409,
          code: 'EMAIL_ALREADY_EXISTS',
          message: 'This email is already registered.',
          details: null,
        })
      }

      if (
        typeof data.password !== 'string' ||
        !data.password
      ) {
        return Promise.reject({
          status: 422,
          code: 'VALIDATION_ERROR',
          message: 'A password is required.',
          details: null,
        })
      }

      const newUser = {
        id: crypto.randomUUID(),
        email,
        name: data.name || 'Mock Client',
        role: 'client',
        organization_id: null,
        created_at: new Date().toISOString(),
        password: data.password,
      }

      mockUser.push(newUser);
      currentUser = newUser;
      localStorage.setItem(MOCK_SESSION_KEY, user.id);

      return Promise.resolve({
        data: {
          user: toPublicUser(currentUser),
        },
        status: 201,
      })
    }

    // Log in a mock user.
    if (url === '/api/auth/login') {
      const user = mockUser.find(
        (item) =>
          item.email === data.email &&
          item.password === data.password
      )

      if (!user) {
        return Promise.reject({
          status: 401,
          code: 'INVALID_CREDENTIALS',
          message: 'Invalid email or password.',
          details: null,
        })
      }

      currentUser = user;
      localStorage.setItem(MOCK_SESSION_KEY, user.id);

      return Promise.resolve({
        data: {
          user: toPublicUser(currentUser),
        },
        status: 200,
      })
    }

    // Log out the current mock user.
    if (url === '/api/auth/logout') {
      currentUser = null;
      localStorage.removeItem(MOCK_SESSION_KEY);

      return Promise.resolve({
        data: {
          message: 'Session closed.',
        },
        status: 200,
      })
    }

    // Create a reading.
    if (url === '/api/readings') {
      const sensor = sensors.find(
        (sensor) => sensor.id === data.sensor_id
      )

      if (!sensor) {
        return Promise.reject({
          status: 404,
          code: 'SENSOR_NOT_FOUND',
          message: 'Sensor not found.',
          details: null,
        })
      }

      if (
        data.pressure < 0 ||
        data.pressure > 25
      ) {
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
          data.measured_at ?? new Date().toISOString(),
        created_at: new Date().toISOString(),
      }

      readings.push(reading)

      return Promise.resolve({
        data: reading,
        status: 201,
      })
    }

    // Create a sensor.
    if (url === '/api/sensors') {
      const site = sites.find(
        (site) => site.id === data.site_id
      )

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'Site not found.',
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

    // Handle unknown endpoints.
    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found.',
      details: null,
    })
  },

  // PATCH requests
  patch(url, data = {}, config = {}) {
    console.log('[MOCK PATCH]', url, data, config)

    // Acknowledge an alert.
    if (url.endsWith('/acknowledge')) {
      const id = url.split('/')[3]
      const alert = alerts.find(
        (alert) => alert.id === id
      )

      if (!alert) {
        return Promise.reject({
          status: 404,
          code: 'ALERT_NOT_FOUND',
          message: 'Alert not found.',
          details: null,
        })
      }

      alert.acknowledged_at = new Date().toISOString()

      return Promise.resolve({
        data: { ...alert },
        status: 200,
      })
    }

    // Resolve an alert.
    if (url.endsWith('/resolve')) {
      const id = url.split('/')[3]
      const alert = alerts.find(
        (alert) => alert.id === id
      )

      if (!alert) {
        return Promise.reject({
          status: 404,
          code: 'ALERT_NOT_FOUND',
          message: 'Alert not found.',
          details: null,
        })
      }

      alert.status = 'RESOLVED'
      alert.resolved_at = new Date().toISOString()

      return Promise.resolve({
        data: { ...alert },
        status: 200,
      })
    }

    // Update a sensor.
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
          message: 'Sensor not found.',
          details: null,
        })
      }

      if (
        (data.min_pressure !== undefined &&
          (data.min_pressure < 0 ||
            data.min_pressure > 25)) ||
        (data.max_pressure !== undefined &&
          (data.max_pressure < 0 ||
            data.max_pressure > 25)) ||
        (data.min_pressure !== undefined &&
          data.max_pressure !== undefined &&
          data.min_pressure >= data.max_pressure) ||
        (data.min_pressure !== undefined &&
          data.max_pressure === undefined &&
          data.min_pressure >= sensor.max_pressure) ||
        (data.max_pressure !== undefined &&
          data.min_pressure === undefined &&
          data.max_pressure <= sensor.min_pressure)
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

    // Handle unknown endpoints.
    return Promise.reject({
      status: 404,
      code: 'UNKNOWN_ENDPOINT',
      message: 'Mock endpoint not found.',
      details: null,
    })
  },

  // DELETE requests
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