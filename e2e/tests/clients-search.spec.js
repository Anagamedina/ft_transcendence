// Advanced search module on Clientes (/admin/clients, B1 and B17):
// search, filters, sorting and pagination, all in one request.
import { test, expect } from '@playwright/test'
import { ADMIN, login, expectAdminHome } from './helpers.js'

async function openClients(page) {
  await login(page, ADMIN)
  await expectAdminHome(page)
  await page.goto('/admin/clients')
  await expect(page.getByRole('table', { name: 'Clientes' })).toBeVisible()
}

function table(page) {
  return page.getByRole('table', { name: 'Clientes' })
}

function header(page, label) {
  return table(page).getByRole('columnheader', { name: label })
}

// The name of each client row (the expand button "›" is not part of it)
async function names(page) {
  const cells = await table(page).locator('tbody > tr:first-child > th').allInnerTexts()
  return cells.map((text) => text.replace('›', '').trim())
}

async function openAlerts(page) {
  return (await table(page).locator('tbody > tr:first-child > td:last-child').allInnerTexts()).map(Number)
}

// Clicks a column header and waits for the list request it sends
async function sortBy(page, label) {
  const request = page.waitForRequest((r) => r.url().includes('/api/organizations?'))
  await header(page, label).getByRole('button').click()
  return new URL((await request).url()).searchParams
}

const isSorted = (list, compare) => list.every((value, i) => i === 0 || compare(list[i - 1], value) <= 0)
const byName = (a, b) => a.localeCompare(b, 'es')

test.describe('clients search', () => {
  test('the list starts by name and the header says so', async ({ page }) => {
    await openClients(page)
    expect(isSorted(await names(page), byName)).toBe(true)
    await expect(header(page, 'Cliente')).toHaveAttribute('aria-sort', 'ascending')
    await expect(header(page, 'Estado')).not.toHaveAttribute('aria-sort', /.*/)
  })

  test('a column header sorts the list and flips it on a second click', async ({ page }) => {
    await openClients(page)

    let params = await sortBy(page, 'Alertas')
    expect([params.get('sort'), params.get('order')]).toEqual(['open_alerts', 'desc'])
    await expect(header(page, 'Alertas')).toHaveAttribute('aria-sort', 'descending')
    await expect(header(page, 'Cliente')).toHaveAttribute('aria-sort', 'none')
    await expect.poll(async () => isSorted(await openAlerts(page), (a, b) => b - a)).toBe(true)

    params = await sortBy(page, 'Alertas')
    expect(params.get('order')).toBe('asc')
    await expect.poll(async () => isSorted(await openAlerts(page), (a, b) => a - b)).toBe(true)

    await sortBy(page, 'Cliente')
    await sortBy(page, 'Cliente')
    await expect(header(page, 'Cliente')).toHaveAttribute('aria-sort', 'descending')
    await expect.poll(async () => isSorted(await names(page), (a, b) => byName(b, a))).toBe(true)
  })

  test('search, filter and order go together and back to page 1', async ({ page }) => {
    await openClients(page)
    await sortBy(page, 'Sensores')

    const filtered = page.waitForRequest((r) => r.url().includes('status=ACTIVE'))
    await page.getByRole('group', { name: 'Filtrar por estado' }).getByRole('button', { name: /^Activos/ }).click()
    await filtered

    const searched = page.waitForRequest((r) => r.url().includes('q=o'))
    await page.getByRole('searchbox', { name: 'Buscar cliente' }).fill('o')
    const params = new URL((await searched).url()).searchParams
    expect(Object.fromEntries(params)).toMatchObject({
      status: 'ACTIVE',
      q: 'o',
      sort: 'sensor_count',
      order: 'desc',
      page: '1',
    })
  })

  test('the pages follow the order', async ({ page }) => {
    await openClients(page)
    const all = []
    for (let number = 1; ; number += 1) {
      const response = await page.request.get(
        `/api/organizations?sort=open_alerts&order=desc&page=${number}&page_size=2`,
      )
      const body = await response.json()
      all.push(...body.items.map((client) => client.open_alerts))
      if (number >= body.pages) break
    }
    expect(all.length).toBeGreaterThan(2)
    expect(isSorted(all, (a, b) => b - a)).toBe(true)
  })

  test('an unknown order is rejected', async ({ page }) => {
    await openClients(page)
    const response = await page.request.get('/api/organizations?sort=password_hash')
    expect(response.status()).toBe(422)
    expect((await response.json()).error.code).toBe('VALIDATION_ERROR')
  })

  test('the headers work with the keyboard', async ({ page }) => {
    await openClients(page)
    const request = page.waitForRequest((r) => r.url().includes('sort=trial_ends_at'))
    await header(page, 'Prueba').getByRole('button').focus()
    await page.keyboard.press('Enter')
    await request
    await expect(header(page, 'Prueba')).toHaveAttribute('aria-sort', 'ascending')
  })
})
