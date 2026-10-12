/**
 * hybrid-section-visual-serve.mjs — build ONLY the Scene3D harness page (`scripts/hybrid-section-visual.html`) into a
 * static bundle and serve it with `vite preview` (run `hybrid-semantic-hardening`).
 *
 * Why: through the Vite dev server a page load is hundreds of module requests, and on this Windows machine local
 * connections were intermittently denied (`net::ERR_NETWORK_ACCESS_DENIED`), killing long browser checks. The static
 * bundle is two files. It is a measuring aid; the product build (`npm run build`) is not touched.
 *
 *   node scripts/hybrid-section-visual-serve.mjs build <outDir>
 *   node scripts/hybrid-section-visual-serve.mjs preview <outDir> [port=3101]     # serves on 127.0.0.1
 * then: node scripts/hybrid-section-visual-check.mjs --host 127.0.0.1 --port 3101 --out <new dir>
 */
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { build, preview } from "vite";
import react from "@vitejs/plugin-react";

const [mode, outArg, port = "3101"] = process.argv.slice(2);
if (!["build", "preview"].includes(mode) || !outArg) throw new Error("usage: build|preview <outDir> [port]");
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = resolve(outArg);
const common = { root, configFile: false, plugins: [react()], logLevel: "warn" };
if (mode === "build") {
  await build({ ...common, build: { outDir, emptyOutDir: true,
    rollupOptions: { input: join(root, "scripts", "hybrid-section-visual.html") } } });
  console.log(`built ${outDir}`);
} else {
  (await preview({ ...common, build: { outDir }, preview: { port: Number(port), host: "127.0.0.1", strictPort: true } })).printUrls();
}
