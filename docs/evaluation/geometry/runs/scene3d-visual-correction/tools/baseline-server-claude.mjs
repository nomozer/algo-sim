import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
const repo = process.cwd(), root = resolve('frontend');
const { createServer } = await import(pathToFileURL(resolve('frontend/node_modules/vite/dist/node/index.js')));
const files = ['Scene3DExplorer.tsx', 'scene3d-view.tsx', 'scene3d-edge-visibility.ts'];
const original = new Map(files.map(name => {
  const path = `frontend/src/simulations/domains/geometry/${name}`;
  return [resolve(path).replaceAll('\\', '/'), execFileSync('git', ['show', `fe5f40b7:${path}`], { cwd: repo, encoding: 'utf8' })];
}));
const server = await createServer({ root, cacheDir: resolve('.superpowers/vite-cache-baseline-claude'), server: { host: '127.0.0.1', port: 3158, strictPort: true },
  plugins: [{ name: 'verified-baseline-source', enforce: 'pre', load(id) { return original.get(id.split('?')[0].replaceAll('\\', '/')) ?? null; } }] });
await server.listen();
console.log('Baseline fe5f40b7 on http://127.0.0.1:3158; three original source modules, separate cache, no checkout mutation.');
