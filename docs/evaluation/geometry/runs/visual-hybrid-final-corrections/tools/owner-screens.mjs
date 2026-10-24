// Owner visual-approval screenshots: real product page, real envelopes (offline samples + Adapter /4 service fixtures),
// full viewport, desktop + mobile, Mode A (default) and one Mode B. 0 API calls. Usage:
// node owner-screens.mjs <worktree> <port> <a4-fixtures.json> <outDir>
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

const [wtArg, port, a4Arg, outArg] = process.argv.slice(2);
const wt = resolve(wtArg), out = resolve(outArg), url = `http://127.0.0.1:${port}`;
if (existsSync(out)) throw Error('fresh output directory required');
mkdirSync(out, { recursive: true });
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const samples = JSON.parse(readFileSync(join(wt, 'frontend/src/data/geometry-samples.json'), 'utf8')).samples;
const a4 = JSON.parse(readFileSync(resolve(a4Arg), 'utf8')).fixtures;
const CASES = [
  ['plane-name-P', 'sample', 'cau-cat-mat-phang', 'A', 'declared plane name (P) grounded in the problem; Hình phụ on (the plane is auxiliary at the last step)'],
  ['section-named-cycle', 'sample', 'thiet-dien-chop', 'A', 'section through named midpoints'],
  ['section-unnamed-vertices', 'a4', 'CORPUS-DEV01-construct', 'A', 'section through unnamed intersections: named by its plane'],
  ['coincident-points', 'a4', 'PERP-square-third', 'A', 'coincident identity A ≡ H ≡ H1'],
  ['hidden-edges-mode-a', 'sample', 'the-tich-chop', 'A', 'hidden edges dashed; final answers not shown (Mode A)'],
  ['mode-b-reveal', 'sample', 'the-tich-chop', 'B', 'learner opened «Phân tích toán học»: answers shown'],
];
const envOf = ([, kind, id]) => kind === 'sample' ? samples.find((s) => s.id === id).envelope : a4.find((f) => f.id === id).envelope;
const git = (...a) => execFileSync('git', a, { cwd: wt, encoding: 'utf8' }).trim();
const receipt = { schema: 'owner-visual-screens/1', commit: git('rev-parse', 'HEAD'),
  tracked_changes: git('status', '--porcelain', '--untracked-files=no'), url, rows: [], errors: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const c of CASES) {
      const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
      await ctx.route('**/*', (route) => { const u = new URL(route.request().url());
        if (u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
        if (u.pathname === '/api/auth/me') return route.fulfill({ json: null });
        if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue(); return route.abort(); });
      const page = await ctx.newPage();
      page.on('pageerror', (e) => receipt.errors.push({ case: c[0], message: e.message }));
      await page.goto(url);
      const env = envOf(c);
      await page.evaluate(async (e) => { const { useAppStore } = await import('/src/state/store.ts'); localStorage.clear(); useAppStore.getState().loadEnvelope(e); }, env);
      await page.locator('.geo3d-canvas canvas').waitFor();
      const slider = page.locator('.geo3d-scrub input[type=range]');
      await slider.fill(await slider.getAttribute('max'));
      if (c[3] === 'B') await page.locator('[data-mo-bang="phan-tich"]').click();
      if (c[0] === 'plane-name-P') {
        await page.locator('[data-mo-nhom="hien-thi"]').click();
        await page.locator('.geo3d-menu-hop [role^=menuitem]', { hasText: 'Hình phụ' }).click();
        await page.locator('[data-mo-nhom="hien-thi"]').click();
      }
      await page.waitForTimeout(1800);
      const finals = new Set((env.scene3d.events ?? []).filter((e) => e.semantic_kind === 'FINAL_RESULT').map((e) => e.object));
      const shown = await page.evaluate(() => ({
        labels: [...document.querySelectorAll('.geo3d-label, .geo3d-nhan-mp')].map((e) => e.textContent.trim()),
        measure_ids: [...document.querySelectorAll('.geo3d-so-do')].map((e) => e.dataset.annId),
        analysis_open: !!document.querySelector('[data-math-analysis-panel]') }));
      const file = `${c[0]}-${vp.width}.png`;
      await page.screenshot({ path: join(out, file) });
      const notations = env.scene3d.objects.filter((o) => ['plane3', 'section'].includes(o.type))
        .map((o) => ({ id: o.id, type: o.type, notation: o.notation, label: o.label }));
      receipt.rows.push({ case: c[0], source: `${c[1]}:${c[2]}`, mode: c[3], what: c[4], viewport: `${vp.width}x${vp.height}`,
        file, visible_point_and_plane_labels: shown.labels, analysis_open: shown.analysis_open,
        final_label_ids_shown: shown.measure_ids.filter((id) => finals.has(id)), plane_and_section_identity: notations });
      console.log(c[0], vp.width, c[3], JSON.stringify(shown.labels.slice(0, 12)));
      await ctx.close();
    }
  }
} finally { await browser.close(); writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n'); }
console.log('ERRORS', receipt.errors.length);
