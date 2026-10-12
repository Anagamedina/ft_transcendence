import { test, expect } from '@playwright/test'
import { CLIENT, login, expectDashboard } from './helpers.js'

// Registro público con prueba de 7 días (B10, #140). Hasta la B10 solo un
// admin podía dar de alta cuentas. El formulario de /register con los
// campos nuevos es la F15-P (Florinda); mientras llega, se prueba por la API.

const PASSWORD = 'agua-que-no-se-escapa'

function newAccount() {
  const id = Date.now()
  return {
    name: 'E2E Visitor',
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
  expect((await created.json()).user.role).toBe('client')

  // The register response already opened the session.
  const me = await request.get('/api/me')
  expect(me.status()).toBe(200)
  expect((await me.json()).user.email).toBe(account.email)
})

test('the new account can log in from the login form', async ({ page, request }) => {
  const account = newAccount()
  expect((await request.post('/api/auth/register', { data: account })).status()).toBe(201)

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
