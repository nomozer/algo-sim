// node f4-harness-build.mjs <frontendDir> <outDir>  — builds scripts/f4-harness.html (same recipe as hybrid-section-visual-serve.mjs)
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
const [root, outDir] = process.argv.slice(2).map((p) => resolve(p));
const req = createRequire(join(root, "package.json"));
const { build } = await import(pathToFileURL(req.resolve("vite")).href);
const react = (await import(pathToFileURL(req.resolve("@vitejs/plugin-react")).href)).default;
await build({ root, configFile: false, plugins: [react()], logLevel: "warn",
  build: { outDir, emptyOutDir: true, rollupOptions: { input: join(root, "scripts", "f4-harness.html") } } });
console.log(`built ${outDir}`);
