// Owner visual-approval refusal screens: real product refusal notice for Adapter /4 service refusal envelopes, desktop +
// mobile; records whether any technical code (reason_code / error_code / failure_category) is visible. 0 API calls.
// Usage: node refusal-screens.mjs <worktree> <port> <a4-fixtures.json> <outDir>
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

const [wtArg, port, a4Arg, outArg] = process.argv.slice(2);
const wt = resolve(wtArg), out = resolve(outArg), url = `http://127.0.0.1:${port}`;
if (existsSync(out)) throw Error('fresh output directory required');
mkdirSync(out, { recursive: true });
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const a4 = JSON.parse(readFileSync(resolve(a4Arg), 'utf8')).fixtures;
const IDS = ['GEO-contradictory-length', 'NEG-missing-height', 'NEG-negated-plane'];
const git = (...a) => execFileSync('git', a, { cwd: wt, encoding: 'utf8' }).trim();
const receipt = { schema: 'owner-refusal-screens/1', commit: git('rev-parse', 'HEAD'),
  tracked_changes: git('status', '--porcelain', '--untracked-files=no'), url, rows: [], errors: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const id of IDS) {
      const env = a4.find((f) => f.id === id).envelope;
      const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
      await ctx.route('**/*', (route) => { const u = new URL(route.request().url());
        if (u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
        if (u.pathname === '/api/auth/me') return route.fulfill({ json: null });
        if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue(); return route.abort(); });
      const page = await ctx.newPage();
      page.on('pageerror', (e) => receipt.errors.push({ id, message: e.message }));
      await page.goto(url);
      await page.evaluate(async (e) => { const { useAppStore } = await import('/src/state/store.ts'); localStorage.clear(); useAppStore.getState().loadUnsupported(e); }, env);
      await page.locator('section.card .eyebrow').waitFor();
      await page.waitForTimeout(500);
      const text = await page.evaluate(() => document.body.innerText);
      const codes = [env.reason_code, env.error_code, env.failure_category].filter(Boolean);
      const file = `refusal-${id}-${vp.width}.png`;
      await page.screenshot({ path: join(out, file) });
      receipt.rows.push({ id, viewport: `${vp.width}x${vp.height}`, file, reason_code: env.reason_code ?? null,
        technical_codes_visible: codes.filter((c) => text.includes(c)), details_drawer: text.includes('Chi tiết chẩn đoán'),
        canvas: await page.locator('.geo3d-canvas canvas').count() });
      console.log(id, vp.width, JSON.stringify(receipt.rows.at(-1).technical_codes_visible), receipt.rows.at(-1).details_drawer);
      await ctx.close();
    }
  }
} finally { await browser.close(); writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n'); }
console.log('ERRORS', receipt.errors.length);
