import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  expect: { timeout: 5000 },
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'https://localhost',
    ignoreHTTPSErrors: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  // Chrome (required by the subject), plus Firefox and WebKit (Safari's
  // engine) for the "additional browsers" module. They share one database and
  // the specs create and delete fixed names, so each browser waits for the
  // previous one instead of running at the same time.
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] }, dependencies: ['chromium'] },
    { name: 'webkit', use: { ...devices['Desktop Safari'] }, dependencies: ['firefox'] },
  ],
})
