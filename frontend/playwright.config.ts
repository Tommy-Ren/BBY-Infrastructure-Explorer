import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  workers: process.env.CI ? 1 : 2,
  timeout: 60000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: process.env.EXPLORER_BASE_URL || "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    launchOptions: {
      args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: process.env.EXPLORER_BASE_URL
    ? undefined
    : [
        {
          command: `${process.platform === "win32" ? ".venv\\Scripts\\python.exe" : ".venv/bin/python"} -m uvicorn backend.app:app --port 8000`,
          cwd: path.resolve(".."),
          url: "http://127.0.0.1:8000/health",
          reuseExistingServer: !process.env.CI,
        },
        {
          command: "npm run dev",
          url: "http://127.0.0.1:5173",
          reuseExistingServer: !process.env.CI,
        },
      ],
});
