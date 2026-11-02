import { test, expect } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard, expectAdminHome, expectLogin } from './helpers.js'

test('an anonymous visitor is sent to login from a private route', async ({ page }) => {
  await page.goto('/app')
  await expectLogin(page)
})

test('public pages open without a session', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('link', { name: 'Entrar' }).first()).toBeVisible()
  // /privacy and /terms are kept as redirects to the single legal page.
  await page.goto('/privacy')
  await expect(page).toHaveURL('/legal')
  await page.goto('/terms')
  await expect(page).toHaveURL('/legal')
  await expect(page.getByRole('heading', { name: 'Información legal' })).toBeVisible()
})

test('logout closes the session and blocks private routes again', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
  await page.getByRole('button', { name: 'Cerrar sesión' }).click()
  await expectLogin(page)
  await page.goto('/app')
  await expectLogin(page)
})

test('two simultaneous sessions do not share data', async ({ browser }) => {
  const adminContext = await browser.newContext()
  const clientContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  const clientPage = await clientContext.newPage()

  await login(adminPage, ADMIN)
  await login(clientPage, CLIENT)
  await expectAdminHome(adminPage)
  await expectDashboard(clientPage)

  const adminMe = await adminContext.request.get('/api/me')
  const clientMe = await clientContext.request.get('/api/me')
  expect((await adminMe.json()).user.email).toBe(ADMIN.email)
  expect((await clientMe.json()).user.email).toBe(CLIENT.email)

  await adminContext.close()
  await clientContext.close()
})
