// MOCK ADAPTER — responses adhering to the same OpenAPI contract (Week 1 parallel)

import { alerts } from './fixtures/alerts.js'
import { dailyRows } from './fixtures/analytics.js'
import { overview } from './fixtures/overview.js'
import { readings } from './fixtures/readings.js'
import { sensors } from './fixtures/sensors.js'
import { sites } from './fixtures/sites.js'
import { systemStatus } from './fixtures/status.js'
import { demoBuilding, demoSensors, demoReadings } from './fixtures/building.js'
import { organizations } from './fixtures/organizations.js'

// The C-Edificio demo building (8 sensors on 6 floors) also appears in the
// admin sites and sensors lists, so the floor-by-floor view has real content.
// Clients do not see it (see getAccessibleSites).
sites.push(demoBuilding)
sensors.push(...demoSensors)

// Floors of a site from -basements to floors - 1, as the API checks (B3)
function floorInSite(floor, site) {
  return Number.isInteger(floor) && floor >= -site.basements && floor <= site.floors - 1
}

function floorOutOfSite(site) {
  return {
    status: 422,
    code: 'FLOOR_OUT_OF_SITE',
    message: `La planta tiene que estar entre ${-site.basements} y ${site.floors - 1} en este edificio.`,
    details: null,
  }
}

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

// Organizations that already exist in the mock, to answer 409
// ORGANIZATION_NAME_TAKEN. Same demo names as the admin clients mock.
const mockOrganizations = [
  { id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', name: 'Hotel Diagonal Mar' },
  { id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', name: 'Escola Gràcia' },
  { id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', name: 'Comunitat de veïns Sants' },
]

const MOCK_EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Error with the backend shape: { status, code, message, details }
function domainError(status, code, message) {
  return { status, code, message, details: null }
}

// Same rule as backend/app/shared/passwords.py (short list of common ones).
// Returns the error message, or null when the password is valid.
const MOCK_PASSWORD_MIN_LENGTH = 12
const MOCK_COMMON_PASSWORDS = [
  'password1234',
  'contraseña123',
  'qwertyuiop12',
  '123456789012',
  'abcdefghijkl',
  'aquaguard123',
  'aquaguard2026',
]

function checkMockPassword(password, email) {
  if (password.length < MOCK_PASSWORD_MIN_LENGTH) {
    return `La contraseña tiene que tener al menos ${MOCK_PASSWORD_MIN_LENGTH} caracteres.`
  }
  if (password.length > 128) {
    return 'La contraseña no puede pasar de 128 caracteres.'
  }

  const lower = password.toLowerCase()
  if (MOCK_COMMON_PASSWORDS.includes(lower) || new Set(lower).size < 5) {
    return 'Esa contraseña es demasiado fácil de adivinar. Elige otra.'
  }

  const normalizedEmail = email.toLowerCase()
  const localPart = normalizedEmail.split('@')[0]
  if (lower.includes(normalizedEmail) || (localPart.length >= 4 && lower.includes(localPart))) {
    return 'La contraseña no puede contener tu email.'
  }

  return null
}

// Imitates the Nginx limit on the register form (gateway/nginx.conf):
// rate=10r/m (one slot every 6 s) and burst=4, same algorithm as Nginx.
// Five quick attempts pass, the 6th gets 429, then one more every 6 s.
const REGISTER_SLOT_MS = 6 * 1000
const REGISTER_BURST = 4
let registerExcess = null
let registerLastTime = 0

function isRegisterRateLimited() {
  const now = Date.now()

  // First request: Nginx lets it through without counting it as excess
  if (registerExcess === null) {
    registerExcess = 0
    registerLastTime = now
    return false
  }

  const excess = Math.max(0, registerExcess - (now - registerLastTime) / REGISTER_SLOT_MS) + 1
  if (excess > REGISTER_BURST) {
    return true
  }

  registerExcess = excess
  registerLastTime = now
  return false
}

function rateLimitError() {
  return domainError(
    429,
    'TOO_MANY_REQUESTS',
    'Demasiadas peticiones. Espera un minuto y vuelve a intentarlo.'
  )
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

  // The demo building is only for the admin views (#169); the client
  // dashboard keeps its own fixture data
  return sites.filter(
    (site) =>
      site.organization_id === currentUser.organization_id &&
      site.id !== demoBuilding.id
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


// ---------------------------------------------------------------------------
// Organizations (B1, B16) and invitations (B4)
// ---------------------------------------------------------------------------

const DAY_MS = 24 * 60 * 60 * 1000
// TRIAL_DAYS and INVITATION_TTL_DAYS of the API (7 by default)
const TRIAL_DAYS = 7
const INVITATION_TTL_DAYS = 7

// Invitations (B4 has no routes yet: see invitations.service.js).
// Each one keeps its `code` here so F6 (#167) can find it by code; the API stores
// only a hash, and the responses never include it (see toInvitationResponse).
//
// Fixed demo codes, to test /registro?invitacion=CODE without creating one first:
//   AQUAGUARD-DEMO-INVITE   pending (same code as backend/seeds/seed_demo.py)
//   AQUAGUARD-DEMO-EXPIRED  expired  -> 410 INVITATION_EXPIRED
//   AQUAGUARD-DEMO-USED     accepted -> 404 INVITATION_NOT_FOUND
// They start again on every page load. The ones the admin creates are saved in
// localStorage, so their link still works after a reload in the same browser.
const MOCK_INVITATIONS_KEY = 'aquaguard_mock_invitations'

function demoInvitation(code, createdDaysAgo, expiresInDays, acceptedDaysAgo = null) {
  const now = Date.now()
  return {
    id: crypto.randomUUID(),
    organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    organization_name: 'Hotel Diagonal Mar',
    email: 'nuevo.gestor@hoteldiagonal.example.com',
    expires_at: new Date(now + expiresInDays * DAY_MS).toISOString(),
    accepted_at: acceptedDaysAgo === null ? null : new Date(now - acceptedDaysAgo * DAY_MS).toISOString(),
    revoked_at: null,
    created_by_name: 'Mock Admin',
    created_at: new Date(now - createdDaysAgo * DAY_MS).toISOString(),
    code,
    demo: true,
  }
}

function loadSavedInvitations() {
  try {
    const saved = JSON.parse(localStorage.getItem(MOCK_INVITATIONS_KEY) ?? '[]')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

function saveInvitations() {
  try {
    const own = invitations.filter((item) => !item.demo)
    localStorage.setItem(MOCK_INVITATIONS_KEY, JSON.stringify(own))
  } catch {
    // Storage full or blocked: the invitations still work until the page reloads
  }
}

const invitations = [
  demoInvitation('AQUAGUARD-DEMO-INVITE', 1, INVITATION_TTL_DAYS - 1),
  demoInvitation('AQUAGUARD-DEMO-EXPIRED', 9, -2),
  demoInvitation('AQUAGUARD-DEMO-USED', 3, INVITATION_TTL_DAYS - 3, 1),
  ...loadSavedInvitations(),
]

// InvitationResponse of the contract: without the code and the mock flags
function toInvitationResponse(invitation) {
  const { code, demo, ...response } = invitation
  return { ...response, status: invitationStatus(invitation) }
}

// The pending invitation with that code, or the API error:
// 410 when it expired, 404 when it does not exist, was accepted or was revoked
function findInvitationByCode(code) {
  const invitation = invitations.find((item) => item.code === code)
  const status = invitation ? invitationStatus(invitation) : null

  if (status === 'EXPIRED') {
    return { error: domainError(410, 'INVITATION_EXPIRED', 'La invitación ha caducado.') }
  }
  if (status !== 'PENDING') {
    return { error: domainError(404, 'INVITATION_NOT_FOUND', 'La invitación no existe o ya no es válida.') }
  }
  return { invitation }
}

// The code inside /api/invitations/by-code/{code}[/accept]
function codeFromUrl(url) {
  return decodeURIComponent(url.split('/')[4] ?? '')
}

// Imitates the Nginx limit on /api/invitations/by-code/ (gateway/nginx.conf):
// same rule as the register form (10r/m, burst=4), with its own counter
let invitationsExcess = null
let invitationsLastTime = 0

function isInvitationsRateLimited() {
  const now = Date.now()

  if (invitationsExcess === null) {
    invitationsExcess = 0
    invitationsLastTime = now
    return false
  }

  const excess =
    Math.max(0, invitationsExcess - (now - invitationsLastTime) / REGISTER_SLOT_MS) + 1
  if (excess > REGISTER_BURST) {
    return true
  }

  invitationsExcess = excess
  invitationsLastTime = now
  return false
}

function organizationNotFound() {
  return {
    status: 404,
    code: 'ORGANIZATION_NOT_FOUND',
    message: 'La organización no existe.',
    details: null,
  }
}

function conflict(code, message) {
  return { status: 409, code, message, details: null }
}

// Every organizations route is admin only, as in the API (401 / 403)
function adminCheck() {
  if (!currentUser) return authError()
  if (currentUser.role !== 'admin') return forbiddenError()
  return null
}

// The organization with its counters computed from the other fixtures,
// as the API does with GROUP BY (they are never stored)
function withCounters(organization) {
  const orgSites = sites.filter((site) => site.organization_id === organization.id)
  const orgSensors = sensors.filter((sensor) => sensor.organization_id === organization.id)
  const openAlerts = alerts.filter(
    (alert) => alert.organization_id === organization.id && alert.status !== 'RESOLVED'
  )
  return {
    ...organization,
    site_count: orgSites.length,
    sensor_count: orgSensors.length,
    open_alerts: openAlerts.length,
    critical_alerts: openAlerts.filter((alert) => alert.severity === 'CRITICAL').length,
  }
}

function findOrganization(url) {
  const id = url.split('/')[3]
  return organizations.find((organization) => organization.id === id) ?? null
}

// Lowercase text for searching ('es' handles Spanish/Catalan letters correctly)
function normalize(text) {
  return String(text).toLocaleLowerCase('es')
}

// The API compares names without case: 'hotel mar' and 'Hotel Mar' are the same client
function nameTaken(name, exceptId = null) {
  return organizations.some(
    (organization) => organization.id !== exceptId && normalize(organization.name) === normalize(name)
  )
}

// Same Page shape as the API, cutting the requested page
function toPage(items, params = {}) {
  const page = Number(params.page ?? 1)
  const pageSize = Number(params.page_size ?? 20)
  const start = (page - 1) * pageSize
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize),
  }
}

// Removes in place every item of a fixture list that matches
function removeWhere(list, matches) {
  let removed = 0
  for (let i = list.length - 1; i >= 0; i -= 1) {
    if (matches(list[i])) {
      list.splice(i, 1)
      removed += 1
    }
  }
  return removed
}

// Invitation status computed from its dates, as InvitationStatus in the API
function invitationStatus(invitation) {
  if (invitation.revoked_at) return 'REVOKED'
  if (invitation.accepted_at) return 'ACCEPTED'
  return new Date(invitation.expires_at) < new Date() ? 'EXPIRED' : 'PENDING'
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

    // List organizations (B1): filters, sorted by name, one page
    if (url === '/api/organizations') {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const params = config.params ?? {}
      const text = params.q ? normalize(params.q.trim()) : ''

      const items = organizations
        .filter((organization) => !params.status || organization.status === params.status)
        .filter((organization) =>
          text === ''
            ? true
            // Same fields the API searches: name, city, legal name and tax id
            : [organization.name, organization.city, organization.legal_name, organization.tax_id].some(
                (field) => field && normalize(field).includes(text)
              )
        )
        .map(withCounters)
        .filter((organization) =>
          params.has_open_alerts === undefined
            ? true
            : String(params.has_open_alerts) === 'true'
              ? organization.open_alerts > 0
              : organization.open_alerts === 0
        )
        .sort((a, b) => a.name.localeCompare(b.name, 'es'))

      return Promise.resolve({ data: toPage(items, params), status: 200 })
    }

    // Get one organization (B1)
    if (url.startsWith('/api/organizations/')) {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const organization = findOrganization(url)
      if (!organization) return Promise.reject(organizationNotFound())

      return Promise.resolve({ data: withCounters(organization), status: 200 })
    }

    // List invitations (B4). No session check: the B4 routes do not exist yet, so
    // this mock is also used with the real API, where the session is not the mock one
    if (url === '/api/invitations') {
      const params = config.params ?? {}
      const items = invitations
        .filter((item) => !params.organization_id || item.organization_id === params.organization_id)
        .map(toInvitationResponse)

      return Promise.resolve({ data: toPage(items, params), status: 200 })
    }

    // Open an invitation link (B4, public): only what the accept form needs
    if (url.startsWith('/api/invitations/by-code/')) {
      if (isInvitationsRateLimited()) {
        return Promise.reject(rateLimitError())
      }

      const { invitation, error } = findInvitationByCode(codeFromUrl(url))
      if (error) return Promise.reject(error)

      return Promise.resolve({
        data: {
          organization_name: invitation.organization_name,
          email: invitation.email,
          expires_at: invitation.expires_at,
        },
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
      // Temporary test: simulate a slow API response
      //await new Promise((resolve) => setTimeout(resolve, 2000));  
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

      // Sensors without fixture readings get 7 days of demo readings for the chart.
      // A sensor that never reported (last_seen_at null) has none, as in the API.
      const fixtureReadings = readings.filter(
        (reading) => reading.sensor_id === sensorId
      )
      // Demo readings only for the admin sensors view, so the client history stays as it was
      const useDemo =
        currentUser.role === 'admin' && fixtureReadings.length === 0 && sensor.last_seen_at
      const sensorReadings = useDemo ? demoReadings(sensor) : fixtureReadings

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

    // KPI cards of the dashboard (F12).
    if (url === '/api/analytics/overview') {
      if (!currentUser) {
        return Promise.reject(authError())
      }

      // A client has no "clients": both fields are null, as in the contract.
      if (currentUser.role !== 'admin') {
        return Promise.resolve({
          data: {
            ...overview,
            organizations_total: null,
            organizations_needing_attention: null,
          },
          status: 200,
        })
      }

      return Promise.resolve({
        data: { ...overview },
        status: 200,
      })
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

    // Public sign-up with a 7-day trial (B10, #140). Same order and codes as
    // backend/app/modules/auth/service.py: 429 (Nginx), 422, then 409.
    if (url === '/api/auth/register') {
      if (isRegisterRateLimited()) {
        return Promise.reject(rateLimitError())
      }

      const name = typeof data.name === 'string' ? data.name.trim() : ''
      const email = typeof data.email === 'string' ? data.email.trim() : ''
      const password = typeof data.password === 'string' ? data.password : ''
      const organizationName =
        typeof data.organization_name === 'string'
          ? data.organization_name.trim()
          : ''

      // Pydantic checks (generic VALIDATION_ERROR, one detail per field)
      if (!name || name.length > 120) {
        return Promise.reject(validationError('name', 'String should have 1-120 characters'))
      }
      if (!MOCK_EMAIL_PATTERN.test(email)) {
        return Promise.reject(validationError('email', 'value is not a valid email address'))
      }
      if (typeof data.organization_name !== 'string' || data.organization_name.length > 120) {
        return Promise.reject(validationError('organization_name', 'String should have at most 120 characters'))
      }
      if (typeof data.accept_terms !== 'boolean') {
        return Promise.reject(validationError('accept_terms', 'Input should be a valid boolean'))
      }

      // Domain checks
      if (!data.accept_terms) {
        return Promise.reject(domainError(
          422,
          'TERMS_NOT_ACCEPTED',
          'Tienes que aceptar los términos de uso para registrarte.'
        ))
      }

      const weakPasswordMessage = checkMockPassword(password, email)
      if (weakPasswordMessage) {
        return Promise.reject(domainError(422, 'WEAK_PASSWORD', weakPasswordMessage))
      }

      if (!organizationName) {
        return Promise.reject(domainError(422, 'INVALID_NAME', 'El nombre no puede estar vacío.'))
      }

      if (mockUser.some((user) => user.email.toLowerCase() === email.toLowerCase())) {
        return Promise.reject(domainError(409, 'EMAIL_ALREADY_EXISTS', 'Ese email ya está dado de alta.'))
      }

      if (mockOrganizations.some(
        (org) => org.name.toLowerCase() === organizationName.toLowerCase()
      )) {
        return Promise.reject(domainError(
          409,
          'ORGANIZATION_NAME_TAKEN',
          'Ya hay una organización con ese nombre.'
        ))
      }

      // Organization in TRIAL for 7 days, and its first client user
      const now = new Date()
      const organization = {
        id: crypto.randomUUID(),
        name: organizationName,
        status: 'trial',
        trial_ends_at: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      }
      mockOrganizations.push(organization)

      const newUser = {
        id: crypto.randomUUID(),
        email,
        name,
        role: 'client',
        organization_id: organization.id,
        created_at: now.toISOString(),
        password,
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

    // Create an organization (B1), with its first building in the same operation.
    // Created by the admin, so it starts ACTIVE (the public sign-up creates trials)
    if (url === '/api/organizations') {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const name = typeof data.name === 'string' ? data.name.trim() : ''
      if (name === '') {
        return Promise.reject({
          status: 422,
          code: 'INVALID_NAME',
          message: 'El nombre no puede estar vacío.',
          details: null,
        })
      }
      if (nameTaken(name)) {
        return Promise.reject(
          conflict('ORGANIZATION_NAME_TAKEN', 'Ya hay una organización con ese nombre.')
        )
      }

      const organization = {
        id: crypto.randomUUID(),
        name,
        status: 'ACTIVE',
        trial_ends_at: null,
        city: data.city ?? null,
        contact_email: data.contact_email ?? null,
        phone: data.phone ?? null,
        legal_name: data.legal_name ?? null,
        tax_id: data.tax_id ?? null,
        billing_email: data.billing_email ?? null,
        user_count: 0,
        created_at: new Date().toISOString(),
      }
      organizations.push(organization)

      if (data.first_site) {
        sites.push({
          id: crypto.randomUUID(),
          organization_id: organization.id,
          organization_name: organization.name,
          name: data.first_site.name,
          address: data.first_site.address ?? null,
          latitude: data.first_site.latitude ?? null,
          longitude: data.first_site.longitude ?? null,
          floors: data.first_site.floors ?? 1,
          basements: data.first_site.basements ?? 0,
          building_type: data.first_site.building_type ?? 'OTHER',
          district: null,
          sensor_count: 0,
          status: 'OK',
          created_at: organization.created_at,
        })
      }

      return Promise.resolve({ data: withCounters(organization), status: 201 })
    }

    // Status actions of an organization (B1): suspend, reactivate, extend-trial, activate
    if (url.startsWith('/api/organizations/')) {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const organization = findOrganization(url)
      if (!organization) return Promise.reject(organizationNotFound())

      const action = url.split('/')[4]

      if (action === 'suspend') {
        if (organization.status === 'SUSPENDED') {
          return Promise.reject(conflict('ORGANIZATION_ALREADY_SUSPENDED', 'Ya estaba suspendida.'))
        }
        organization.status = 'SUSPENDED'
      } else if (action === 'reactivate') {
        if (organization.status !== 'SUSPENDED') {
          return Promise.reject(conflict('ORGANIZATION_NOT_SUSPENDED', 'No estaba suspendida.'))
        }
        // Back to TRIAL if it still has a trial date, ACTIVE otherwise
        organization.status = organization.trial_ends_at ? 'TRIAL' : 'ACTIVE'
      } else if (action === 'extend-trial' || action === 'activate') {
        if (organization.status !== 'TRIAL') {
          return Promise.reject(conflict('ORGANIZATION_NOT_IN_TRIAL', 'La organización no está en prueba.'))
        }
        if (action === 'activate') {
          organization.status = 'ACTIVE'
          organization.trial_ends_at = null
        } else {
          // Adds the days to the end date, or to today if the trial already ended
          const now = new Date()
          const end = new Date(organization.trial_ends_at)
          const from = end > now ? end : now
          organization.trial_ends_at = new Date(from.getTime() + TRIAL_DAYS * DAY_MS).toISOString()
        }
      } else {
        return Promise.reject({
          status: 404,
          code: 'UNKNOWN_ENDPOINT',
          message: 'Mock endpoint not found.',
          details: null,
        })
      }

      return Promise.resolve({ data: withCounters(organization), status: 200 })
    }

    // Accept an invitation (B4, public): creates the client user and opens the
    // session, like the sign-up. Order: 429 (Nginx), 404/410, 422, then 409
    if (url.startsWith('/api/invitations/by-code/') && url.endsWith('/accept')) {
      if (isInvitationsRateLimited()) {
        return Promise.reject(rateLimitError())
      }

      const { invitation, error } = findInvitationByCode(codeFromUrl(url))
      if (error) return Promise.reject(error)

      const name = typeof data.name === 'string' ? data.name.trim() : ''
      const password = typeof data.password === 'string' ? data.password : ''

      // Pydantic checks (generic VALIDATION_ERROR, one detail per field)
      if (!name || name.length > 120) {
        return Promise.reject(validationError('name', 'String should have 1-120 characters'))
      }
      if (typeof data.accept_terms !== 'boolean') {
        return Promise.reject(validationError('accept_terms', 'Input should be a valid boolean'))
      }

      // Domain checks, same as the register (B10)
      if (!data.accept_terms) {
        return Promise.reject(domainError(
          422,
          'TERMS_NOT_ACCEPTED',
          'Tienes que aceptar los términos de uso para registrarte.'
        ))
      }

      const weakPasswordMessage = checkMockPassword(password, invitation.email)
      if (weakPasswordMessage) {
        return Promise.reject(domainError(422, 'WEAK_PASSWORD', weakPasswordMessage))
      }

      if (mockUser.some((user) => user.email.toLowerCase() === invitation.email)) {
        return Promise.reject(domainError(409, 'EMAIL_ALREADY_EXISTS', 'Ese email ya está dado de alta.'))
      }

      const now = new Date()
      const newUser = {
        id: crypto.randomUUID(),
        email: invitation.email,
        name,
        role: 'client',
        organization_id: invitation.organization_id,
        created_at: now.toISOString(),
        password,
      }
      mockUser.push(newUser)

      // One use only: the same link answers 404 from now on
      invitation.accepted_at = now.toISOString()
      saveInvitations()

      const organization = organizations.find((item) => item.id === invitation.organization_id)
      if (organization) organization.user_count = (organization.user_count ?? 0) + 1

      currentUser = newUser
      localStorage.setItem(MOCK_SESSION_KEY, newUser.id)

      return Promise.resolve({
        data: {
          user: toPublicUser(currentUser),
        },
        status: 201,
      })
    }

    // Create an invitation (B4). No session check: see GET /api/invitations
    if (url === '/api/invitations') {
      const email = typeof data.email === 'string' ? data.email.trim().toLowerCase() : ''
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return Promise.reject(validationError('email', 'A valid email is required.'))
      }

      if (!data.organization_id) {
        return Promise.reject(validationError('organization_id', 'organization_id is required.'))
      }
      // With the real API the client is not in the fixtures, so its name may be unknown here
      const organization = organizations.find((item) => item.id === data.organization_id)

      const code = Math.random().toString(36).slice(2, 14)
      const now = new Date()
      const invitation = {
        id: crypto.randomUUID(),
        organization_id: data.organization_id,
        organization_name: organization?.name ?? '',
        email,
        expires_at: new Date(now.getTime() + INVITATION_TTL_DAYS * DAY_MS).toISOString(),
        accepted_at: null,
        revoked_at: null,
        created_by_name: currentUser?.name ?? null,
        created_at: now.toISOString(),
        // Kept so GET /by-code/{code} can find it; never returned after this answer
        code,
      }
      invitations.push(invitation)
      saveInvitations()

      // code and url only in this answer, as in the API.
      // Same route and param that F6 (#167) reads: /registro?invitacion=CODE
      return Promise.resolve({
        data: {
          ...toInvitationResponse(invitation),
          code,
          url: `${window.location.origin}/registro?invitacion=${code}`,
        },
        status: 201,
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

      const floor = data.floor ?? 0
      if (!floorInSite(floor, site)) {
        return Promise.reject(floorOutOfSite(site))
      }

      // external_id is unique inside its site (409, as the API: exact match).
      // Case variants ('sens-001') are rejected earlier by SensorForm.
      if (sensors.some((item) => item.site_id === site.id && item.external_id === data.external_id)) {
        return Promise.reject({
          status: 409,
          code: 'EXTERNAL_ID_TAKEN',
          message: 'Ya hay un sensor con esa etiqueta en este edificio.',
          details: null,
        })
      }

      // A new sensor has never sent a reading: OFFLINE until the first one arrives
      const sensor = {
        id: crypto.randomUUID(),
        site_id: data.site_id,
        site_name: site.name,
        organization_id: site.organization_id,
        organization_name: site.organization_name,
        floor,
        external_id: data.external_id,
        name: data.name.trim(),
        location: data.location ?? null,
        sensor_type: data.sensor_type ?? 'PRESSURE',
        unit: data.unit ?? 'bar',
        min_pressure: data.min_pressure,
        max_pressure: data.max_pressure,
        status: 'OFFLINE',
        health: 'OFFLINE',
        last_seen_at: null,
        last_value: null,
        created_at: new Date().toISOString(),
      }

      sensors.push(sensor)
      site.sensor_count = (site.sensor_count ?? 0) + 1

      return Promise.resolve({
        data: { ...sensor },
        status: 201,
      })
    }

    // Create a site (B2). Same 409 as the API: exact name inside the same client.
    // Case variants ('torre sofia') are rejected earlier by SiteForm.
    if (url === '/api/sites') {
      // Admin only, as in the API (B2)
      if (!currentUser) {
        return Promise.reject(authError())
      }
      if (currentUser.role !== 'admin') {
        return Promise.reject(forbiddenError())
      }

      const sameName = sites.some(
        (site) =>
          site.organization_id === data.organization_id &&
          site.name === String(data.name).trim()
      )

      if (sameName) {
        return Promise.reject({
          status: 409,
          code: 'SITE_NAME_TAKEN',
          message: 'Ese cliente ya tiene un edificio con ese nombre.',
          details: null,
        })
      }

      const owner = organizations.find((organization) => organization.id === data.organization_id)

      const site = {
        id: crypto.randomUUID(),
        organization_id: data.organization_id,
        organization_name: owner?.name ?? 'Cliente',
        name: String(data.name).trim(),
        address: data.address || null,
        latitude: data.latitude ?? null,
        longitude: data.longitude ?? null,
        floors: data.floors ?? 1,
        basements: data.basements ?? 0,
        building_type: data.building_type ?? 'OTHER',
        district: null,
        sensor_count: 0,
        status: 'OK',
        created_at: new Date().toISOString(),
      }

      sites.push(site)

      return Promise.resolve({
        data: { ...site },
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
      alert.state = 'ACKNOWLEDGED'

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
      alert.state = 'RESOLVED'
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

      if (data.floor !== undefined) {
        const site = sites.find((item) => item.id === sensor.site_id)
        if (site && !floorInSite(data.floor, site)) {
          return Promise.reject(floorOutOfSite(site))
        }
      }

      Object.assign(sensor, {
        ...(data.floor !== undefined && {
          floor: data.floor,
        }),
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
        data: { ...sensor },
        status: 200,
      })
    }

    // Update an organization (B1): only name, contact and billing fields
    if (url.startsWith('/api/organizations/')) {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const organization = findOrganization(url)
      if (!organization) return Promise.reject(organizationNotFound())

      if (data.name !== undefined) {
        const name = String(data.name).trim()
        if (name === '') {
          return Promise.reject({ status: 422, code: 'INVALID_NAME', message: 'El nombre no puede estar vacío.', details: null })
        }
        if (nameTaken(name, organization.id)) {
          return Promise.reject(conflict('ORGANIZATION_NAME_TAKEN', 'Ya hay una organización con ese nombre.'))
        }
        organization.name = name
      }

      const EDITABLE = ['city', 'contact_email', 'phone', 'legal_name', 'tax_id', 'billing_email']
      for (const field of EDITABLE) {
        if (data[field] !== undefined) organization[field] = data[field]
      }

      return Promise.resolve({ data: withCounters(organization), status: 200 })
    }

    // Update a site (B2). Only the fields sent change; the client cannot change.
    if (url.startsWith('/api/sites/')) {
      // Admin only, as in the API (B2)
      if (!currentUser) {
        return Promise.reject(authError())
      }
      if (currentUser.role !== 'admin') {
        return Promise.reject(forbiddenError())
      }

      const id = url.split('/')[3]
      const site = sites.find((site) => site.id === id)

      if (!site) {
        return Promise.reject({
          status: 404,
          code: 'SITE_NOT_FOUND',
          message: 'El site indicado no existe.',
          details: null,
        })
      }

      const EDITABLE = ['name', 'address', 'latitude', 'longitude', 'floors', 'basements', 'building_type']
      for (const field of EDITABLE) {
        if (data[field] !== undefined) site[field] = data[field]
      }

      return Promise.resolve({
        data: { ...site },
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

    // Delete an organization and everything it owns (B16). Needs the exact name
    if (url.startsWith('/api/organizations/')) {
      const denied = adminCheck()
      if (denied) return Promise.reject(denied)

      const organization = findOrganization(url)
      if (!organization) return Promise.reject(organizationNotFound())

      if (config.data?.confirm_name !== organization.name) {
        return Promise.reject({
          status: 422,
          code: 'NAME_CONFIRMATION_MISMATCH',
          message: 'El nombre no coincide.',
          details: null,
        })
      }

      const owned = (item) => item.organization_id === organization.id
      const sensorIds = new Set(sensors.filter(owned).map((sensor) => sensor.id))

      const deleted = {
        readings: removeWhere(readings, (reading) => sensorIds.has(reading.sensor_id)),
        alerts: removeWhere(alerts, owned),
        sensors: removeWhere(sensors, owned),
        documents: 0,
        sites: removeWhere(sites, owned),
        invitations: removeWhere(invitations, owned),
        users: organization.user_count,
        organizations: removeWhere(organizations, (item) => item.id === organization.id),
      }
      saveInvitations()

      return Promise.resolve({
        data: { id: organization.id, name: organization.name, deleted, detached_admins: 0, deleted_files: 0 },
        status: 200,
      })
    }

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
Analytics     GET       /api/analytics/overview
Orgs          GET       /api/organizations
Orgs          GET       /api/organizations/{id}
Orgs          POST      /api/organizations
Orgs          PATCH     /api/organizations/{id}
Orgs          POST      /api/organizations/{id}/suspend | reactivate | extend-trial | activate
Orgs          DELETE    /api/organizations/{id}
Invitations   GET       /api/invitations
Invitations   POST      /api/invitations
Invitations   GET       /api/invitations/by-code/{code}
Invitations   POST      /api/invitations/by-code/{code}/accept
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