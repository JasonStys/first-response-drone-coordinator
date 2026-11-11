/** @file Jason Stys: production UI build and planning utility coverage; lines: docs/SOURCE_MAP.md. */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
const version = JSON.parse(
  readFileSync(new URL("./package.json", import.meta.url), "utf8"),
).version;
export default defineConfig({
  define: { __APP_VERSION__: JSON.stringify(version) },
  root: "ui",
  plugins: [react()],
  build: { outDir: "../dist", emptyOutDir: true },
  test: {
    include: ["src/**/*.test.ts"],
    coverage: {
      include: ["src/domain.ts", "src/import_file.ts"],
      thresholds: { statements: 95, branches: 90, functions: 95, lines: 95 },
    },
  },
});
