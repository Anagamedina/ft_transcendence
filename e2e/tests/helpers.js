import { expect } from '@playwright/test'

export const ADMIN = { email: 'admin@aquaguard.dev', password: 'dev-admin-only' }
export const CLIENT = { email: 'client@aquaguard.dev', password: 'dev-client-only' }

export async function login(page, user) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Contraseña').fill(user.password)
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
}

// Client home since the role-based routes (F1): /dashboard now redirects here.
export async function expectDashboard(page) {
  await expect(page).toHaveURL('/app')
  await expect(page.getByRole('heading', { name: 'Panel de control', exact: true })).toBeVisible()
}

export async function expectAdminHome(page) {
  await expect(page).toHaveURL('/admin')
  await expect(page.getByRole('heading', { name: 'Panel', exact: true })).toBeVisible()
}

// The guard adds ?redirect=<private route>, so only the path is compared.
export async function expectLogin(page) {
  await expect(page).toHaveURL(/\/login(\?.*)?$/)
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
}
