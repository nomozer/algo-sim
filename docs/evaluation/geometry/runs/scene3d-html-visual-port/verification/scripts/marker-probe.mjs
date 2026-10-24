// Right-angle marker on-screen leg length (px) across real learner interactions: default, orbit drags, wheel zoom.
// Usage: node marker-probe.mjs <worktree> <fixtures.json> <outDir>
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
const wt = resolve(process.argv[2]);
const out = resolve(process.argv[4]);
if (existsSync(out)) throw Error('fresh output directory required');
mkdirSync(out, { recursive: true });
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const fixtures = JSON.parse(readFileSync(resolve(process.argv[3]), 'utf8')).fixtures;
const url = 'http://127.0.0.1:3117';
const rows = [];
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const id of ['PERP-square-third', 'CORPUS-DEV03-construct', 'CORPUS-DEV10-prism-area']) {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
      await ctx.addInitScript(() => {
        window.__scenes = [];
        const hub = new EventTarget();
        hub.addEventListener('observe', e => { const d = e.detail; if (d?.isScene) window.__scenes.push(d);
          if (d?.isWebGLRenderer) { const r = d.render.bind(d); d.render = (s, c) => { window.__lastCam = c; return r(s, c); }; } });
        window.__THREE_DEVTOOLS__ = hub;
      });
      await ctx.route('**/*', route => { const u = new URL(route.request().url());
        if (u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
        if (u.pathname === '/api/auth/me') return route.fulfill({ json: null });
        if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue(); return route.abort(); });
      const page = await ctx.newPage();
      await page.goto(url);
      await page.evaluate(async env => { const { useAppStore } = await import('/src/state/store.ts'); localStorage.clear(); useAppStore.getState().loadEnvelope(env); },
        fixtures.find(f => f.id === id).envelope);
      const canvas = page.locator('.geo3d-canvas canvas');
      await canvas.waitFor();
      const slider = page.locator('.geo3d-scrub input[type=range]');
      await slider.fill(await slider.getAttribute('max'));
      await page.waitForTimeout(1000);
      const box = await canvas.boundingBox();
      const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
      const measure = async (state) => {
        await page.waitForTimeout(700);
        const m = await page.evaluate(() => {
          const scene = window.__scenes.at(-1), cam = window.__lastCam;
          const c = document.querySelector('.geo3d-canvas canvas').getBoundingClientRect();
          const V = cam.position.constructor; const res = [];
          scene.traverse(n => {
            const d = n.userData?.gocVuongDonVi; if (!d) return;
            let p = n, vis = true; while (p) { if (!p.visible) vis = false; p = p.parent; }
            n.updateMatrixWorld(true);
            const pos = n.geometry.getAttribute('position');
            const toPx = v => { const q = v.clone().project(cam); return [(q.x + 1) / 2 * c.width, (1 - q.y) / 2 * c.height]; };
            const foot = toPx(new V(...d.foot).applyMatrix4(n.parent.matrixWorld));
            const a = toPx(new V().fromBufferAttribute(pos, 0).applyMatrix4(n.matrixWorld));
            const b = toPx(new V().fromBufferAttribute(pos, 2).applyMatrix4(n.matrixWorld));
            // Expected world leg for a 0.014×H px target at the foot's view depth (camera-only math).
            const f = c.height / (2 * Math.tan(cam.fov * Math.PI / 360));
            const depth = -new V(...d.foot).applyMatrix4(n.parent.matrixWorld).applyMatrix4(cam.matrixWorldInverse).z;
            const pxT = Math.min(12, Math.max(8, 0.014 * c.height));
            const legWorldActual = n.scale.x * d.s0, legWorldExpected = Math.min(d.maxWorld, pxT * depth / f);
            res.push({ name: n.name || n.parent?.userData?.nhanChung, visible: vis,
              world_leg_ratio_actual_over_expected: +(legWorldActual / legWorldExpected).toFixed(3),
              leg_u_px: +Math.hypot(a[0] - foot[0], a[1] - foot[1]).toFixed(2), leg_v_px: +Math.hypot(b[0] - foot[0], b[1] - foot[1]).toFixed(2) });
          });
          return { canvas_h: Math.round(c.height), markers: res };
        });
        const file = `${id}-${viewport.width}-${state}.png`;
        await canvas.screenshot({ path: join(out, file) });
        rows.push({ id, viewport: viewport.width, state, file, ...m });
        console.log(id, viewport.width, state, JSON.stringify(m.markers.filter(x => x.visible).map(x => [x.leg_u_px, x.leg_v_px, x.world_leg_ratio_actual_over_expected])), 'hidden-dupes', m.markers.filter(x => !x.visible).length);
      };
      await measure('default');
      await page.mouse.move(cx, cy); await page.mouse.down(); await page.mouse.move(cx + 220, cy - 60, { steps: 12 }); await page.mouse.up();
      await measure('orbit');
      await page.mouse.move(cx, cy); await page.mouse.wheel(0, -500);
      await measure('zoom_in');
      await page.mouse.wheel(0, 1400);
      await measure('zoom_out');
      await ctx.close();
    }
  }
} finally { await browser.close(); writeFileSync(join(out, 'receipt.json'), JSON.stringify({ schema: 'right-angle-marker-probe/1', rows }, null, 2) + '\n'); }
