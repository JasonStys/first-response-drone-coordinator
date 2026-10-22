/** @file Jason Stys: production UI build and planning utility coverage; lines: docs/SOURCE_MAP.md. */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  root: "ui",
  plugins: [react()],
  build: { outDir: "../dist", emptyOutDir: true },
  test: {
    include: ["src/**/*.test.ts"],
    coverage: {
      include: ["src/domain.ts"],
      thresholds: { statements: 95, branches: 90, functions: 95, lines: 95 },
    },
  },
});
