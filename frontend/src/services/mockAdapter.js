// MOCK ADAPTER — responses adhering to the same OpenAPI contract (Week 1 parallel)

import { alerts } from './fixtures/alerts.js'
import { dailyRows } from './fixtures/analytics.js'
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
    organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
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

function authError() {
  return {
    status: 401,
    code: "UNAUTHORIZED",
    message: "Authentication required.",
    details: null,
  };
}

function forbiddenError() {
  return {
    status: 403,
    code: "FORBIDDEN",
    message: "You do not have access to this resource.",
    details: null,
  };
}

function validationError(field, message) {
  return {
    status: 422,
    code: "VALIDATION_ERROR",
    message: "Invalid request.",
    details: [
      {
        field,
        message,
        type: "value_error",
      },
    ],
  };
}

function getAccessibleSites() {
  if (!currentUser) return []

  if (currentUser.role === "admin") {
    return sites
  }

  if (
    currentUser.role !== "client" ||
    !currentUser.organization_id
  ) {
    return []
  }

  return sites.filter(
    (site) =>
      site.organization_id === currentUser.organization_id
  )
}

function getAccessibleSensors() {
  const siteIds = new Set(
    getAccessibleSites().map((site) => site.id)
  )

  return sensors.filter((sensor) =>
    siteIds.has(sensor.site_id)
  )
}

function canAccessSensor(sensorId) {
  return getAccessibleSensors().some(
    (sensor) => sensor.id === sensorId
  )
}

function getAccessibleAlerts() {
  const sensorIds = new Set(
    getAccessibleSensors().map((sensor) => sensor.id)
  )

  return alerts.filter((alert) =>
    sensorIds.has(alert.sensor_id)
  )
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
        return Promise.reject(authError())
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
    if (url === "/api/sites") {
      if (!currentUser) {
        return Promise.reject(authError());
      }

      const items = getAccessibleSites();

      return Promise.resolve({
        data: {
          items,
          total: items.length,
          page: 1,
          page_size: Math.max(items.length, 1),
          pages: items.length === 0 ? 0 : 1,
        },
        status: 200,
      });
    }

    // Get all sensors.
    if (url === "/api/sensors") {
      if (!currentUser) {
        return Promise.reject(authError());
      }

      const items = getAccessibleSensors();

      return Promise.resolve({
        data: {
          items,
          total: items.length,
          page: 1,
          page_size: Math.max(items.length, 1),
          pages: items.length === 0 ? 0 : 1,
        },
        status: 200,
      });
    }

    // Get sensors belonging to a specific site.
    if (
      url.startsWith('/api/sites/') &&
      url.endsWith('/sensors')
    ) {
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      const accessibleSite = getAccessibleSites().some(
        (accessibleSite) => accessibleSite.id === siteId
      )

      if (!accessibleSite) {
        return Promise.reject(forbiddenError())
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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      const accessibleSite = getAccessibleSites().some(
        (accessibleSite) => accessibleSite.id === id
      )

      if (!accessibleSite) {
        return Promise.reject(forbiddenError())
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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (!canAccessSensor(sensorId)) {
        return Promise.reject(forbiddenError())
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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (!canAccessSensor(id)) {
        return Promise.reject(forbiddenError())
      }

      return Promise.resolve({
        data: sensor,
        status: 200,
      })
    }

    // Get all alerts.
    if (url === "/api/alerts") {
      if (!currentUser) {
        return Promise.reject(authError());
      }

      const items = getAccessibleAlerts().map((alert) => ({
        ...alert,
      }));

      return Promise.resolve({
        data: {
          items,
          total: items.length,
          page: 1,
          page_size: Math.max(items.length, 1),
          pages: items.length === 0 ? 0 : 1,
        },
        status: 200,
      });
    }

    // Analytics export (F19): JSON rows for the charts or a CSV Blob.
    if (url === '/api/analytics/export') {
      if (!currentUser) {
        return Promise.reject(authError())
      }

      const { format = 'csv', from, to } = config.params ?? {}

      const end = to ? new Date(to) : new Date()
      const start = from
        ? new Date(from)
        : new Date(end.getTime() - 30 * 86400000)

      if (
        Number.isNaN(start.getTime()) ||
        Number.isNaN(end.getTime()) ||
        start >= end
      ) {
        return Promise.reject({
          status: 422,
          code: 'INVALID_DATE_RANGE',
          message: '`from` tiene que ser anterior a `to`.',
          details: null,
        })
      }

      const rows = dailyRows(start, end)

      if (format === 'json') {
        return Promise.resolve({
          data: rows,
          status: 200,
        })
      }

      if (format !== 'csv') {
        return Promise.reject({
          status: 422,
          code: 'INVALID_FORMAT',
          message: 'Format must be csv or json.',
          details: null,
        })
      }

      const header = Object.keys(rows[0] ?? { date: '' })

      const csv = [
        header.join(','),
        ...rows.map((r) =>
          header.map((k) => r[k] ?? '').join(',')
        ),
      ].join('\n')

      return Promise.resolve({
        data: new Blob([csv], { type: 'text/csv' }),
        headers: {
          'content-disposition':
            'attachment; filename="aquaguard-analytics-mock.csv"',
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
      const email =
        typeof data.email === 'string'
          ? data.email.trim()
          : ''

      if (!email) {
        return Promise.reject({
          status: 422,
          code: 'VALIDATION_ERROR',
          message: 'A valid email is required.',
          details: null,
        })
      }

      if (
        mockUser.some(
          (user) => user.email.toLowerCase() === email.toLowerCase()
        )
      ) {
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
      localStorage.setItem(MOCK_SESSION_KEY, newUser.id);

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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (!canAccessSensor(data.sensor_id)) {
        return Promise.reject(forbiddenError())
      }

      if (
        typeof data.pressure !== 'number' ||
        !Number.isFinite(data.pressure) ||
        data.pressure < 0 ||
        data.pressure > 25
      ) {
        return Promise.reject(
          validationError(
            'pressure',
            'Pressure must be a number between 0 and 25 bar.'
          )
        )
      }

      let measuredAt = new Date().toISOString()

      if (data.measured_at !== undefined) {
        const parsedDate = new Date(data.measured_at)

        if (
          typeof data.measured_at !== 'string' ||
          Number.isNaN(parsedDate.getTime())
        ) {
          return Promise.reject(
            validationError(
              'measured_at',
              'measured_at must be a valid date.'
            )
          )
        }

        measuredAt = parsedDate.toISOString()
      }

      const reading = {
        id: crypto.randomUUID(),
        sensor_id: data.sensor_id,
        pressure: data.pressure,
        measured_at: measuredAt,
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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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
        !getAccessibleSites().some(
          (accessibleSite) => accessibleSite.id === data.site_id
        )
      ) {
        return Promise.reject(forbiddenError())
      }

      if (
        typeof data.name !== 'string' ||
        !data.name.trim()
      ) {
        return Promise.reject(
          validationError('name', 'A sensor name is required.')
        )
      }

      if (
        typeof data.min_pressure !== 'number' ||
        !Number.isFinite(data.min_pressure) ||
        typeof data.max_pressure !== 'number' ||
        !Number.isFinite(data.max_pressure) ||
        data.min_pressure < 0 ||
        data.min_pressure > 25 ||
        data.max_pressure < 0 ||
        data.max_pressure > 25 ||
        data.min_pressure >= data.max_pressure
      ) {
        return Promise.reject(
          validationError(
            'min_pressure',
            'Pressure limits must be numbers between 0 and 25, with min_pressure lower than max_pressure.'
          )
        )
      }

      const sensor = {
        id: crypto.randomUUID(),
        site_id: data.site_id,
        name: data.name.trim(),
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
    if (url.startsWith('/api/alerts/') && url.endsWith('/acknowledge')) {
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (
        !getAccessibleAlerts().some(
          (accessibleAlert) => accessibleAlert.id === id
        )
      ) {
        return Promise.reject(forbiddenError())
      }

      alert.acknowledged_at = new Date().toISOString()

      return Promise.resolve({
        data: { ...alert },
        status: 200,
      })
    }

    // Resolve an alert.
    if (url.startsWith('/api/alerts/') && url.endsWith('/resolve')) {
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (
        !getAccessibleAlerts().some(
          (accessibleAlert) => accessibleAlert.id === id
        )
      ) {
        return Promise.reject(forbiddenError())
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
      if (!currentUser) {
        return Promise.reject(authError())
      }

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

      if (!canAccessSensor(id)) {
        return Promise.reject(forbiddenError())
      }

      // Validate pressure values only when they are provided.
      if (
        (
          data.min_pressure !== undefined &&
          (
            typeof data.min_pressure !== 'number' ||
            !Number.isFinite(data.min_pressure) ||
            data.min_pressure < 0 ||
            data.min_pressure > 25
          )
        ) ||
        (
          data.max_pressure !== undefined &&
          (
            typeof data.max_pressure !== 'number' ||
            !Number.isFinite(data.max_pressure) ||
            data.max_pressure < 0 ||
            data.max_pressure > 25
          )
        )
      ) {
        return Promise.reject(
          validationError(
            'min_pressure',
            'Pressure limits must be numbers between 0 and 25.'
          )
        )
      }

      const nextMin =
        data.min_pressure !== undefined
          ? data.min_pressure
          : sensor.min_pressure

      const nextMax =
        data.max_pressure !== undefined
          ? data.max_pressure
          : sensor.max_pressure

      if (nextMin >= nextMax) {
        return Promise.reject(
          validationError(
            'min_pressure',
            'min_pressure must be lower than max_pressure.'
          )
        )
      }

      if (
        data.name !== undefined &&
        (
          typeof data.name !== 'string' ||
          !data.name.trim()
        )
      ) {
        return Promise.reject(
          validationError('name', 'Sensor name cannot be empty.')
        )
      }

      if (
        data.location !== undefined &&
        data.location !== null &&
        typeof data.location !== 'string'
      ) {
        return Promise.reject(
          validationError('location', 'Location must be a string or null.')
        )
      }

      Object.assign(sensor, {
        ...(data.name !== undefined && {
          name: data.name.trim(),
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

/*
Here is exactly what the services tell us the MockAdapter must support:

Domaine       Méthode   Endpoint
Auth          POST      /api/auth/register
Auth          POST      /api/auth/login
Auth          POST      /api/auth/logout
Auth          GET       /api/me
Sites         GET       /api/sites
Sites         GET       /api/sites/{id}
Sites         GET       /api/sites/{id}/sensors
Sensors       GET       /api/sensors
Sensors       GET       /api/sensors/{id}
Sensors       POST      /api/sensors
Sensors       PATCH     /api/sensors/{id}
Readings      POST      /api/readings
Readings      GET       /api/sensors/{id}/readings
Alerts        GET       /api/alerts
Alerts        PATCH     /api/alerts/{id}/acknowledge
Alerts        PATCH     /api/alerts/{id}/resolve
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