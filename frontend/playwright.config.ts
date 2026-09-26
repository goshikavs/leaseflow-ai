import { defineConfig, devices } from "@playwright/test";

const e2ePort = process.env.E2E_FRONTEND_PORT ?? "3100";
const apiPort = process.env.E2E_API_PORT ?? "8100";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: `http://127.0.0.1:${e2ePort}`,
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: "../backend",
      url: `http://127.0.0.1:${apiPort}/health`,
      reuseExistingServer: false,
      env: {
        EXTRACTION_PROVIDER: "fixture",
        DATABASE_URL: "sqlite:///./data/e2e.db",
        STORAGE_DIR: "./data/e2e-uploads",
        CORS_ORIGINS: `http://127.0.0.1:${e2ePort}`,
      },
    },
    {
      command: `npx next dev --port ${e2ePort}`,
      url: `http://127.0.0.1:${e2ePort}`,
      reuseExistingServer: false,
      env: {
        NEXT_PUBLIC_API_URL: `http://127.0.0.1:${apiPort}`,
        NEXT_PUBLIC_DEMO_MODE: "true",
      },
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
