const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: './',
  timeout: 120000,
  expect: {
    timeout: 15000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ['html', { outputFolder: path.join(__dirname, '../reports/html') }],
    ['list']
  ],
  use: {
    baseURL: process.env.VITE_API_URL || 'http://localhost:5173',
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    video: 'on',
    screenshot: 'on',
    trace: 'retain-on-failure',
    actionTimeout: 15000,
    navigationTimeout: 30000,
    launchOptions: {
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-size=1920,1080',
        '--font-render-hinting=none',
      ],
    },
  },
  outputDir: path.join(__dirname, '../recordings/raw'),
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
