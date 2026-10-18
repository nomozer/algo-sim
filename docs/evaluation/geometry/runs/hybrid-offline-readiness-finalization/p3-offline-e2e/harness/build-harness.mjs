// node build-harness.mjs <frontendDir> <outDir> — vite build of hfoi-harness.html; harness sources stay in the run
// directory (tracked evidence) and import the product through the `@fe` alias; bare imports resolve to the frontend's
// node_modules. Nothing is written under frontend/.
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const [fe, outDir] = process.argv.slice(2).map((p) => resolve(p));
const here = dirname(fileURLToPath(import.meta.url));
const req = createRequire(join(fe, "package.json"));
const { build } = await import(pathToFileURL(req.resolve("vite")).href);
const react = (await import(pathToFileURL(req.resolve("@vitejs/plugin-react")).href)).default;
const nm = join(fe, "node_modules");
await build({
  root: here, configFile: false, plugins: [react()], logLevel: "warn",
  resolve: { alias: [
    { find: /^@fe\/(.*)$/, replacement: join(fe, "src", "$1") },
    { find: /^react-dom(\/.*)?$/, replacement: join(nm, "react-dom") + "$1" },
    { find: /^react(\/.*)?$/, replacement: join(nm, "react") + "$1" },
  ] },
  build: { outDir, emptyOutDir: true, rollupOptions: { input: join(here, "hfoi-harness.html") } },
});
console.log(`built ${outDir}`);
