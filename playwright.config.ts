/** @file Jason Stys: actual API/browser journeys without mocks; lines: docs/SOURCE_MAP.md. */
import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
const localPython =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
const python =
  process.env.COORD_PYTHON ??
  (existsSync(localPython) ? localPython : "python");
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
  // Independent disposable DBs prevent browser engines consuming one another's real login budget.
  webServer: [8862, 18862, 28862].map((port) => ({
    command: `"${python}" tools/serve_demo.py --port ${port}`,
    url: `http://127.0.0.1:${port}/healthz`,
    reuseExistingServer: false,
    timeout: 60000,
  })),
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:8862" },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"], baseURL: "http://127.0.0.1:18862" },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"], baseURL: "http://127.0.0.1:28862" },
    },
  ],
});
