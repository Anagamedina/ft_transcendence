import { test } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard, expectAdminHome, expectLogin } from './helpers.js'

test('an anonymous visitor cannot open the admin area', async ({ page }) => {
  await page.goto('/admin')
  await expectLogin(page)
})

test('a client cannot open the admin area', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
  await page.goto('/admin')
  // The guard sends a client back to its own home.
  await expectDashboard(page)
})

test('an admin lands on the admin area after login', async ({ page }) => {
  await login(page, ADMIN)
  await expectAdminHome(page)
})
