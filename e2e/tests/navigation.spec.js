import { test, expect } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard, expectLogin } from './helpers.js'

test('an anonymous visitor is sent to login from a private route', async ({ page }) => {
  await page.goto('/dashboard')
  await expectLogin(page)
})

test('public pages open without a session', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('link', { name: 'Iniciar sesión' }).first()).toBeVisible()
  await page.goto('/privacy')
  await expect(page).toHaveURL('/privacy')
  await page.goto('/terms')
  await expect(page).toHaveURL('/terms')
})

test('logout closes the session and blocks private routes again', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
  await page.getByRole('button', { name: 'Logout' }).click()
  await expectLogin(page)
  await page.goto('/dashboard')
  await expectLogin(page)
})

test('two simultaneous sessions do not share data', async ({ browser }) => {
  const adminContext = await browser.newContext()
  const clientContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  const clientPage = await clientContext.newPage()

  await login(adminPage, ADMIN)
  await login(clientPage, CLIENT)
  await expectDashboard(adminPage)
  await expectDashboard(clientPage)

  const adminMe = await adminContext.request.get('/api/me')
  const clientMe = await clientContext.request.get('/api/me')
  expect((await adminMe.json()).user.email).toBe(ADMIN.email)
  expect((await clientMe.json()).user.email).toBe(CLIENT.email)

  await adminContext.close()
  await clientContext.close()
})
