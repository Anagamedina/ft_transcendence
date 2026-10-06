import { test, expect } from '@playwright/test'
import { CLIENT, login, expectDashboard } from './helpers.js'

test('a client logs in and lands on the dashboard', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
})

test('wrong password shows an error and stays on login', async ({ page }) => {
  await login(page, { email: CLIENT.email, password: 'wrong-password' })
  await expect(page.getByRole('alert')).toHaveText('Email o contraseña incorrectos.')
  await expect(page).toHaveURL('/login')
})

test('unknown email shows the same error as a wrong password', async ({ page }) => {
  await login(page, { email: 'nobody@aquaguard.dev', password: 'wrong-password' })
  await expect(page.getByRole('alert')).toHaveText('Email o contraseña incorrectos.')
})

test('the session survives a page reload', async ({ page }) => {
  await login(page, CLIENT)
  await expectDashboard(page)
  await page.reload()
  await expectDashboard(page)
})
