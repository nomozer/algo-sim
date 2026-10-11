// TEMPORARY reviewer build config (untracked, deleted after review).
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  root: resolve(import.meta.dirname, ".."),
  plugins: [react()],
  build: { outDir: process.env.REVIEW_OUT, emptyOutDir: true, rollupOptions: { input: resolve(import.meta.dirname, "review-visual.html") } },
});
