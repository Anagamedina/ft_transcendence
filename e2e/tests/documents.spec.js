// File upload and management module: types, client and server validation,
// access control, preview, progress and delete (/app/documents, B11 and F14).
import { test, expect } from '@playwright/test'
import { CLIENT, login } from './helpers.js'

const HOTEL = { email: 'hotel@aquaguard.dev', password: 'dev-client-only' }

// A real 1x1 PNG, so the API recognises it by its content
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)
const PDF = Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n')
const OVER_10_MB = Buffer.alloc(11 * 1024 * 1024, '0')

function file(name, mimeType, buffer) {
  return { name, mimeType, buffer }
}

async function openDocuments(page) {
  await login(page, HOTEL)
  await expect(page).toHaveURL('/app')
  await page.goto('/app/documents')
  await expect(page.getByRole('heading', { name: 'Documentos' })).toBeVisible()
}

// Deletes what the test uploaded, also when it failed halfway
async function removeDocuments(page, names) {
  const list = await (await page.request.get('/api/documents?page_size=100')).json()
  for (const doc of list.items.filter((d) => names.includes(d.filename))) {
    await page.request.delete(`/api/documents/${doc.id}`)
  }
}

async function siteId(page) {
  const sites = await (await page.request.get('/api/sites')).json()
  return sites.items[0].id
}

test.describe('documents', () => {
  test('the page rejects other types, empty files and files over 10 MB', async ({ page }) => {
    await openDocuments(page)
    const input = page.locator('input[type="file"]')
    const alert = page.locator('form [role="alert"]')

    await input.setInputFiles(file('virus.exe', 'application/octet-stream', Buffer.from('MZ')))
    await expect(alert).toHaveText('Formato no admitido. Usa PDF, JPG, PNG o CSV.')
    await input.setInputFiles(file('vacio.pdf', 'application/pdf', Buffer.alloc(0)))
    await expect(alert).toHaveText('El archivo está vacío.')
    await input.setInputFiles(file('grande.pdf', 'application/pdf', OVER_10_MB))
    await expect(alert).toHaveText('El archivo supera el límite de 10 MB.')
    await expect(page.getByRole('button', { name: 'Subir documento' })).toBeDisabled()
  })

  test('a client uploads an image and a PDF, previews and deletes them', async ({ page }) => {
    const names = ['e2e-plano.png', 'e2e-informe.pdf']
    await openDocuments(page)
    await removeDocuments(page, names)
    try {
      const form = page.locator('form')
      await form.locator('select').first().selectOption({ index: 1 })
      await form.locator('input[type="file"]').setInputFiles(file(names[0], 'image/png', PNG))
      await page.getByRole('button', { name: 'Subir documento' }).click()
      await expect(page.getByRole('cell', { name: names[0] })).toBeVisible()

      await form.locator('select').first().selectOption({ index: 1 })
      await form.locator('input[type="file"]').setInputFiles(file(names[1], 'application/pdf', PDF))
      await page.getByRole('button', { name: 'Subir documento' }).click()
      await expect(page.getByRole('cell', { name: names[1] })).toBeVisible()

      const row = (name) => page.getByRole('row').filter({ hasText: name })
      await row(names[0]).getByRole('button', { name: 'Vista previa' }).click()
      await expect(page.getByRole('img', { name: names[0] })).toBeVisible()
      await page.getByRole('button', { name: 'Cerrar', exact: true }).click()
      await row(names[1]).getByRole('button', { name: 'Vista previa' }).click()
      await expect(page.locator(`iframe[title="${names[1]}"]`)).toBeVisible()
      await page.getByRole('button', { name: 'Cerrar', exact: true }).click()

      page.on('dialog', (dialog) => dialog.accept())
      for (const name of names) {
        await row(name).getByRole('button', { name: 'Eliminar' }).click()
        await expect(row(name)).toHaveCount(0)
      }
    } finally {
      await removeDocuments(page, names)
    }
  })

  test('the upload shows its progress', async ({ page, browserName }) => {
    // Slowing the network down needs the Chrome DevTools protocol
    test.skip(browserName !== 'chromium', 'network throttling is Chromium only')
    const name = 'e2e-progreso.pdf'
    await openDocuments(page)
    try {
      const cdp = await page.context().newCDPSession(page)
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: 50,
        downloadThroughput: -1,
        uploadThroughput: 600 * 1024,
      })
      const form = page.locator('form')
      await form.locator('select').first().selectOption({ index: 1 })
      const big = Buffer.concat([Buffer.from('%PDF-1.4\n'), Buffer.alloc(3 * 1024 * 1024, '0')])
      await form.locator('input[type="file"]').setInputFiles(file(name, 'application/pdf', big))
      await page.getByRole('button', { name: 'Subir documento' }).click()

      const bar = page.getByRole('progressbar', { name: 'Progreso de subida' })
      await expect(bar).toBeVisible()
      await expect
        .poll(async () => Number(await bar.getAttribute('aria-valuenow')), { timeout: 10000 })
        .toBeGreaterThan(0)
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: 0,
        downloadThroughput: -1,
        uploadThroughput: -1,
      })
      await expect(page.getByRole('cell', { name })).toBeVisible({ timeout: 30000 })
    } finally {
      await removeDocuments(page, [name])
    }
  })

  test('the API checks the content and the size, not the file name', async ({ page }) => {
    await openDocuments(page)
    const site = await siteId(page)
    const upload = (name, mimeType, buffer) =>
      page.request.post('/api/documents', {
        multipart: { file: file(name, mimeType, buffer), site_id: site, kind: 'OTHER' },
      })

    const binary = await upload('binario.png', 'image/png', Buffer.from([0, 1, 2, 3, 255, 254]))
    expect(binary.status()).toBe(422)
    expect((await binary.json()).error.code).toBe('UNSUPPORTED_FILE_TYPE')

    const big = await upload('grande.pdf', 'application/pdf', OVER_10_MB)
    expect(big.status()).toBe(413)
    expect((await big.json()).error.code).toBe('FILE_TOO_LARGE')
  })

  test('another client cannot list, download or delete it', async ({ page, browser }) => {
    const name = 'e2e-privado.png'
    await openDocuments(page)
    const created = await page.request.post('/api/documents', {
      multipart: { file: file(name, 'image/png', PNG), site_id: await siteId(page), kind: 'PHOTO' },
    })
    expect(created.status()).toBe(201)
    const { id } = await created.json()

    const other = await browser.newPage()
    try {
      await login(other, CLIENT)
      await expect(other).toHaveURL('/app')
      const list = await (await other.request.get('/api/documents?page_size=100')).json()
      expect(list.items.map((d) => d.id)).not.toContain(id)
      expect((await other.request.get(`/api/documents/${id}/download`)).status()).toBe(404)
      expect((await other.request.delete(`/api/documents/${id}`)).status()).toBe(404)
    } finally {
      await other.close()
      await removeDocuments(page, [name])
    }
  })
})
