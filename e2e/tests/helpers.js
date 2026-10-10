import { expect } from '@playwright/test'

export const ADMIN = { email: 'admin@aquaguard.dev', password: 'dev-admin-only' }
export const CLIENT = { email: 'client@aquaguard.dev', password: 'dev-client-only' }

export async function login(page, user) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Contraseña').fill(user.password)
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
}

export async function expectDashboard(page) {
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
}

export async function expectLogin(page) {
  await expect(page).toHaveURL('/login')
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
}
