import { test, expect, request as playwrightRequest } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard } from './helpers.js'

// Registro público con prueba de 7 días (B10, #140). Hasta la B10 solo un
// admin podía dar de alta cuentas. El formulario de /register con los
// campos nuevos es la F15-P (Florinda); mientras llega, se prueba por la API.
//
// Hace 4 registros y un login seguidos: lanzar contra un stack arrancado con
// `PUBLIC_RATE_LIMIT=1000r/m make up`, como el resto de Playwright (README),
// o el límite de Nginx puede responder 429.

const PASSWORD = 'agua-que-no-se-escapa'

// Every registration creates an organization in trial. They are deleted at
// the end (B16), with their user, so the demo data does not grow on each run.
const createdOrganizations = []

test.afterAll(async () => {
  const api = await playwrightRequest.newContext({
    baseURL: process.env.BASE_URL || 'https://localhost',
    ignoreHTTPSErrors: true,
  })
  await api.post('/api/auth/login', { data: ADMIN })
  for (const name of createdOrganizations) {
    const found = await (await api.get('/api/organizations', { params: { q: name } })).json()
    const organization = found.items.find((item) => item.name === name)
    if (organization) {
      await api.delete(`/api/organizations/${organization.id}`, { data: { confirm_name: name } })
    }
  }
  await api.dispose()
})

function newAccount() {
  const id = Date.now()
  return {
    name: 'Visitante de Prueba',
    email: `e2e-${id}@aquaguard.dev`,
    password: PASSWORD,
    organization_name: `E2E Org ${id}`,
    accept_terms: true,
  }
}

test('a visitor registers without a session and is already logged in', async ({ request }) => {
  const account = newAccount()

  const created = await request.post('/api/auth/register', { data: account })
  expect(created.status()).toBe(201)
  createdOrganizations.push(account.organization_name)
  expect((await created.json()).user.role).toBe('client')

  // The register response already opened the session.
  const me = await request.get('/api/me')
  expect(me.status()).toBe(200)
  expect((await me.json()).user.email).toBe(account.email)
})

test('the new account can log in from the login form', async ({ page, request }) => {
  const account = newAccount()
  expect((await request.post('/api/auth/register', { data: account })).status()).toBe(201)
  createdOrganizations.push(account.organization_name)

  await login(page, account)
  await expectDashboard(page)
})

test('registering the same email twice is rejected', async ({ request }) => {
  const duplicated = await request.post('/api/auth/register', {
    data: { ...newAccount(), email: CLIENT.email },
  })
  expect(duplicated.status()).toBe(409)
  expect((await duplicated.json()).error.code).toBe('EMAIL_ALREADY_EXISTS')
})

test('a weak password is rejected', async ({ request }) => {
  const weak = await request.post('/api/auth/register', {
    data: { ...newAccount(), password: 'password1234' },
  })
  expect(weak.status()).toBe(422)
  expect((await weak.json()).error.code).toBe('WEAK_PASSWORD')
})
