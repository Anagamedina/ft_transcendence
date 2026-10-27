// Data export and import module: sensors from a CSV (Sensores → "Importar CSV").
// The tests work on a client they create and delete, because sensors cannot
// be deleted one by one: deleting the client removes its building and sensors.
import { test, expect, request as playwrightRequest } from '@playwright/test'
import { ADMIN, CLIENT, login, expectAdminHome } from './helpers.js'

const CLIENT_NAME = `E2E Importar ${Date.now()}`
const SITE_NAME = 'Edificio importado'
const HEADER = 'external_id;name;location;floor;min_pressure;max_pressure'

let api
let site

function csv(...rows) {
  return { name: 'sensores.csv', mimeType: 'text/csv', buffer: Buffer.from([HEADER, ...rows].join('\r\n') + '\r\n') }
}

test.beforeAll(async () => {
  // Same base URL as playwright.config.js: beforeAll has no test fixtures
  api = await playwrightRequest.newContext({
    baseURL: process.env.BASE_URL || 'https://localhost',
    ignoreHTTPSErrors: true,
  })
  expect((await api.post('/api/auth/login', { data: ADMIN })).ok()).toBe(true)
  // Floors 0 to 2 and one basement
  const created = await api.post('/api/organizations', {
    data: { name: CLIENT_NAME, first_site: { name: SITE_NAME, floors: 3, basements: 1 } },
  })
  expect(created.status()).toBe(201)
  const client = await created.json()
  const sites = await (await api.get(`/api/sites?organization_id=${client.id}`)).json()
  site = { ...sites.items[0], organization_id: client.id }
})

test.afterAll(async () => {
  await api.delete(`/api/organizations/${site.organization_id}`, { data: { confirm_name: CLIENT_NAME } })
  await api.dispose()
})

async function sensorsOfSite() {
  const body = await (await api.get(`/api/sensors?site_id=${site.id}&page_size=100`)).json()
  return body.items.map((sensor) => sensor.external_id).sort()
}

async function openImport(page) {
  await login(page, ADMIN)
  await expectAdminHome(page)
  await page.goto('/admin/sensors')
  await page.getByRole('button', { name: 'Importar CSV' }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await dialog.getByLabel('Edificio').selectOption({ label: `${CLIENT_NAME} · ${SITE_NAME}` })
  return dialog
}

test.describe.configure({ mode: 'serial' })

test.describe('sensors import', () => {
  test('the template can be downloaded', async ({ page }) => {
    const dialog = await openImport(page)
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      dialog.getByRole('button', { name: 'Descargar plantilla' }).click(),
    ])
    expect(download.suggestedFilename()).toBe('plantilla-sensores.csv')
  })

  test('the page only takes .csv files', async ({ page }) => {
    const dialog = await openImport(page)
    await dialog.getByLabel('Archivo CSV').setInputFiles({ name: 'notas.txt', mimeType: 'text/plain', buffer: Buffer.from('hola') })
    await expect(dialog.getByRole('alert')).toHaveText('Elige un archivo .csv.')
    await expect(page.getByRole('button', { name: 'Comprobar archivo' })).toBeDisabled()
  })

  test('every wrong line is shown at once and nothing is created', async ({ page }) => {
    const dialog = await openImport(page)
    await dialog.getByLabel('Archivo CSV').setInputFiles(
      csv(
        'E-1;Cocina;Planta 1;1;1,5;6',
        'E-2;;;0;1;6',
        'E-3;Ático;;9;1;6',
        'E-4;Al revés;;0;8;2',
        'E-1;Repetido;;0;1;6',
      ),
    )
    await page.getByRole('button', { name: 'Comprobar archivo' }).click()

    const errors = dialog.getByRole('table', { name: 'Errores del archivo' })
    await expect(errors.locator('tbody tr')).toHaveCount(4)
    const lines = await errors.locator('tbody tr td:first-child').allInnerTexts()
    expect(lines).toEqual(['3', '4', '5', '6'])
    await expect(errors).toContainText('El edificio va de la planta -1 a la 2: la planta 9 no existe.')
    await expect(dialog.getByText('4 líneas tienen errores')).toBeVisible()
    expect(await sensorsOfSite()).toEqual([])
  })

  test('the preview creates nothing, and confirming creates them all', async ({ page }) => {
    const dialog = await openImport(page)
    // Excel in Spanish: ";" and decimal comma
    await dialog.getByLabel('Archivo CSV').setInputFiles(
      csv('E-1;Cocina;Planta 1;1;1,5;6', 'E-2;Habitaciones;;2;1;6', 'E-3;Bombas;Sótano;-1;2;7,5'),
    )
    await page.getByRole('button', { name: 'Comprobar archivo' }).click()

    const preview = dialog.getByRole('table', { name: 'Sensores que se van a crear' })
    await expect(preview.locator('tbody tr')).toHaveCount(3)
    await expect(preview).toContainText('1,5 – 6')
    expect(await sensorsOfSite()).toEqual([])

    await page.getByRole('button', { name: 'Importar 3 sensores' }).click()
    await expect(dialog.getByRole('status')).toContainText(`3 sensores creados en ${SITE_NAME}.`)
    expect(await sensorsOfSite()).toEqual(['E-1', 'E-2', 'E-3'])
  })

  test('the same file again says the sensors already exist', async ({ page }) => {
    const dialog = await openImport(page)
    await dialog.getByLabel('Archivo CSV').setInputFiles(csv('E-1;Cocina;Planta 1;1;1,5;6'))
    await page.getByRole('button', { name: 'Comprobar archivo' }).click()
    await expect(dialog.getByRole('table', { name: 'Errores del archivo' })).toContainText(
      `${SITE_NAME} ya tiene un sensor «E-1».`,
    )
    expect(await sensorsOfSite()).toEqual(['E-1', 'E-2', 'E-3'])
  })

  test('a client cannot import', async ({ page }) => {
    await login(page, CLIENT)
    await expect(page).toHaveURL('/app')
    const response = await page.request.post('/api/sensors/import', {
      multipart: { file: csv('E-9;Otro;;0;1;6'), site_id: site.id },
    })
    expect(response.status()).toBe(403)
  })
})
