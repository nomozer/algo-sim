// Probe: does opening «Phân tích toán học» (Mode B) or selecting a quantity move the camera? 0 API calls.
// Usage: node camera-modeb-probe.mjs <worktree> <port> <fixture.json> <width> <height>
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const [wtArg, port, fx, w, h] = process.argv.slice(2);
const wt = resolve(wtArg);
const url = `http://127.0.0.1:${port}`;
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const env = JSON.parse(readFileSync(resolve(fx), 'utf8')).envelope;
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const ctx = await browser.newContext({ viewport: { width: Number(w), height: Number(h) } });
await ctx.route('**/*', (route) => { const u = new URL(route.request().url());
  if (u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
  if (u.pathname === '/api/auth/me') return route.fulfill({ json: null });
  if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue(); return route.abort(); });
const page = await ctx.newPage();
await page.goto(url);
await page.evaluate(async (e) => { const { useAppStore } = await import('/src/state/store.ts'); localStorage.clear(); useAppStore.getState().loadEnvelope(e); }, env);
await page.locator('.geo3d-canvas canvas').waitFor();
const slider = page.locator('.geo3d-scrub input[type=range]');
await slider.fill(await slider.getAttribute('max'));
const cam = async (tag) => { await page.waitForTimeout(2500);
  const c = await page.evaluate(() => ({ cam: window.__geo3d_camera_snapshot, dash: window.__geo3d_edge_dash_signature }));
  const p = c.cam?.position ?? c.cam?.camera_position;
  console.log(tag, JSON.stringify(p?.map((x) => +x.toFixed(2))), 'dash', JSON.stringify(c.dash)); };
await cam('neutral');
await page.locator('[data-mo-bang="phan-tich"]').click();
await cam('modeB-open');
await page.locator('[data-mo-bang="phan-tich"]').click();
await cam('modeB-closed');
await browser.close();
