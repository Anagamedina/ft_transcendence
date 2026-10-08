import { test, expect } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard } from './helpers.js'

test('an admin registers a client and that client can log in', async ({ page, request }) => {
  const client = await request.post('/api/auth/login', { data: CLIENT })
  const organizationId = (await client.json()).user.organization_id

  const admin = await request.post('/api/auth/login', { data: ADMIN })
  expect(admin.status()).toBe(200)

  const newUser = {
    name: 'E2E Client',
    email: `e2e-${Date.now()}@aquaguard.dev`,
    password: 'e2e-password',
  }
  const created = await request.post('/api/auth/register', {
    data: { ...newUser, organization_id: organizationId },
  })
  expect(created.status()).toBe(201)

  await login(page, newUser)
  await expectDashboard(page)
})

test('registering the same email twice is rejected', async ({ request }) => {
  const client = await request.post('/api/auth/login', { data: CLIENT })
  const organizationId = (await client.json()).user.organization_id
  await request.post('/api/auth/login', { data: ADMIN })

  const duplicated = await request.post('/api/auth/register', {
    data: { name: 'Duplicated', email: CLIENT.email, password: 'e2e-password', organization_id: organizationId },
  })
  expect(duplicated.status()).toBe(409)
})

test('the public register form is rejected without an admin session', async ({ page }) => {
  await page.goto('/register')
  await page.getByLabel('Nombre').fill('E2E Anonymous')
  await page.getByLabel('Email').fill(`e2e-anon-${Date.now()}@aquaguard.dev`)
  await page.getByLabel('Contraseña').fill('e2e-password')
  await page.getByRole('button', { name: 'Crear cuenta' }).click()
  await expect(page.getByRole('alert')).toHaveText('No hay sesión iniciada.')
  await expect(page).toHaveURL('/register')
})
