import { test, expect } from '@playwright/test'
import { ADMIN, CLIENT, login, expectDashboard, expectLogin } from './helpers.js'

test.fixme('an anonymous visitor cannot open the admin area', async ({ page }) => {
  await page.goto('/admin')
  await expectLogin(page)
})

test.fixme('a client cannot open the admin area', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
  await page.goto('/admin')
  await expect(page).not.toHaveURL('/admin')
})

test.fixme('an admin lands on the admin area after login', async ({ page }) => {
  await login(page, ADMIN)
  await expect(page).toHaveURL('/admin')
})
