/** @file Jason Stys: actual API/browser journeys without mocks; lines: docs/SOURCE_MAP.md. */
import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "tests/browser",
  workers: 1,
  retries: 0,
  timeout: 30000,
  expect: { timeout: 8000 },
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8862",
    reducedMotion: "reduce",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${process.env.COORD_PYTHON ?? "python"} tools/serve_demo.py --port 8862`,
    url: "http://127.0.0.1:8862/healthz",
    reuseExistingServer: false,
    timeout: 60000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
