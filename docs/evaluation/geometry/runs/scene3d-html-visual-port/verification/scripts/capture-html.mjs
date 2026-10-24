// Screenshots of the owner's reference HTML (unmodified file) + pixel-size receipt derived from its own camera.
// Usage: node capture-html.mjs <playwright-dir> <html> <outDir>
import { createRequire } from 'node:module';
import { mkdirSync, existsSync, writeFileSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const { chromium } = createRequire(join(resolve(process.argv[2]), 'package.json'))('playwright');
const html = resolve(process.argv[3]);
const out = resolve(process.argv[4]);
if (existsSync(out)) throw Error('fresh output directory required');
mkdirSync(out, { recursive: true });
const SHAPES = ['chop_sa_vuong_day_vuong', 'chop_tu_giac_deu', 'chop_tam_giac_deu', 'chop_sa_vuong_abc',
  'hinh_hop_chu_nhat', 'lang_tru_tam_giac_deu', 'lang_tru_xien'];
const receipt = { schema: 'html-reference-capture/1', html_sha256: createHash('sha256').update(readFileSync(html)).digest('hex'),
  html_modified: false, rows: [], errors: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    page.on('pageerror', e => receipt.errors.push({ viewport, message: e.message }));
    await page.goto(pathToFileURL(html).href, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => typeof THREE !== 'undefined' && typeof selectShape === 'function');
    for (const id of SHAPES) {
      await page.evaluate(id => { selectShape(id); setCameraPreset('sgk'); setConstructionStep(4); }, id);
      await page.waitForTimeout(500);
      const info = await page.evaluate(() => {
        const el = document.getElementById('canvasContainer');
        const H = el.clientHeight, W = el.clientWidth;
        const f = H / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
        const d = camera.position.distanceTo(modelCentroid);
        const px = r => Number((2 * r * f / d).toFixed(2));
        return { canvas: [W, H], fov: camera.fov, cam_position: camera.position.toArray().map(v => +v.toFixed(3)),
          spherical: { theta: camSpherical.theta, phi: camSpherical.phi, radius: camSpherical.radius },
          target: camSpherical.target.toArray(), centroid_distance: +d.toFixed(3), px_per_world_unit: +(f / d).toFixed(2),
          stroke_px_at_centroid: { visible_edge: px(0.028), hidden_edge: px(0.028 * 0.84), section_edge: px(0.035),
            aux_fixed_edge: px(0.026), right_angle_marker_stroke: px(0.021), plane_border: px(0.017) },
          right_angle_marker_px: { size_0_34: px(0.34 / 2), size_0_36: px(0.36 / 2) },
          params: { a: state.a, h: state.h, b: state.b, opacity: state.opacity, sectionRatio: state.sectionRatio, sectionTilt: state.sectionTilt } };
      });
      const file = `HTML-${id}-${viewport.width}.png`;
      const buf = await page.locator('#canvasContainer').screenshot({ path: join(out, file) });
      receipt.rows.push({ id, viewport: `${viewport.width}x${viewport.height}`, step: 4, file,
        sha256: createHash('sha256').update(buf).digest('hex'), ...info });
      console.log(id, viewport.width, JSON.stringify(info.stroke_px_at_centroid), 'marker', JSON.stringify(info.right_angle_marker_px));
    }
    await ctx.close();
  }
} finally {
  await browser.close();
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
}
console.log('ERRORS', receipt.errors.length);
