import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Chuyển tiếp API sang backend (docker compose up -d, cổng 8000)
      "/api": "http://localhost:8000",
    },
  },
  test: {
    // M7.14T: guard offline — mọi fetch trong test đều ném lỗi (0 network call)
    setupFiles: ["./src/test-setup.ts"],
  },
});
