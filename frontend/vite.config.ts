import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Chuyển tiếp API sang backend (docker compose up -d, cổng 8787)
      "/api": "http://localhost:8787",
    },
  },
});
