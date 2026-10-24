// Test transport only: official suite, mathematical oracles and thresholds remain byte-identical.
// The native Node WebSocket/Chrome port session timed out before Page.enable in this sandbox.
// Use the installed Playwright WebSocket transport and its headless sandbox flags.
import cp from 'node:child_process';
import { createRequire, syncBuiltinESMExports } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
let root = dirname(fileURLToPath(import.meta.url));
while (!existsSync(join(root,'frontend/package.json'))) {
  const parent = dirname(root);
  if (parent === root) throw Error('Repository root missing');
  root = parent;
}
const require = createRequire(join(root,'frontend/package.json'));
const core = dirname(require.resolve('playwright-core/package.json'));
globalThis.WebSocket = require(join(core,'lib/utilsBundle.js')).ws;
const spawn = cp.spawn;
cp.spawn = function(command,args,options) {
  if (typeof command === 'string' && /chrome(?:\.exe)?$/i.test(command))
    args = [...args,'--no-sandbox','--disable-dev-shm-usage','--no-first-run'];
  return spawn.call(this,command,args,options);
};
syncBuiltinESMExports();
