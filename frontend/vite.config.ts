import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Chuyển tiếp API sang backend (docker compose up -d, cổng 8787)
      "/api": "http://localhost:8787",
    },
  },
  test: {
    // M7.14T: guard offline — mọi fetch trong test đều ném lỗi (0 network call)
    setupFiles: ["./src/test-setup.ts"],
  },
});
