/** Offline /4 fixture injection into the existing product. No server endpoint, route or model transport. */
import { chromium } from 'playwright';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { docPNG } from './png-pixels.mjs';

const root = resolve(import.meta.dirname, '../..');
const source = join(root, 'docs/evaluation/geometry/runs/hybrid-offline-consumer/results/fixtures.json');
const bytes = readFileSync(source), data = JSON.parse(bytes);
const sha = b => createHash('sha256').update(b).digest('hex');
const canonical = x => x === null || typeof x !== 'object' ? JSON.stringify(x)
  : Array.isArray(x) ? `[${x.map(canonical).join(',')}]`
    : `{${Object.keys(x).sort().map(k => `${JSON.stringify(k)}:${canonical(x[k])}`).join(',')}}`;
const fixtures = data.fixtures.map(row => {
  if (!row.reference) return row;
  const bundle = readFileSync(join(root, row.reference.file));
  if (sha(bundle) !== data.original_fixture_sha256) throw Error('historical fixture hash mismatch');
  const envelope = JSON.parse(bundle).fixtures[row.reference.index].envelope;
  if (sha(canonical(envelope)) !== row.reference.envelope_sha256) throw Error('fresh envelope mismatch');
  return { ...row, envelope };
});
const out = resolve(process.argv[2] ?? '');
if (!process.argv[2] || existsSync(out)) throw Error('fresh output directory required');
// Before the output directory exists: a dirty tree means the receipt does not identify the measured source.
const treeClean = execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim() === '';
mkdirSync(out, { recursive: true });
const url = 'http://127.0.0.1:3115';
const results = [], errors = [], forbidden = [];
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const assert = (value, message) => { if (!value) throw Error(message); };
let code = 0;
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport });
    await context.route('**/*', route => {
      const u = new URL(route.request().url());
      if (u.origin === url && u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
      if (u.origin === url && u.pathname === '/api/auth/me') return route.fulfill({ json: null });
      if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
      forbidden.push({ origin: u.origin, path: u.pathname });
      return route.abort();
    });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', e => errors.push({ type: 'exception', message: e.message }));
    page.on('console', m => { if (m.type() === 'error') errors.push({ type: 'console', message: m.text() }); });
    await page.goto(url);
    for (const fx of fixtures) {
      const row = { id: fx.id, viewport, status: fx.route_d.status, frames: [] };
      if (row.status === 'SERVED' && results.length) await page.goto(url);
      results.push(row);
      const loaded = await page.evaluate(async fx => {
        const a = await import('/src/simulations/domains/geometry/hybrid-preview-adapter.ts');
        const { useAppStore } = await import('/src/state/store.ts');
        const r = a.docPhanHoiHybrid(fx);
        if (!r.ok) return r;
        localStorage.clear();
        window.__adapter4 = { envelope: r.envelope, view: a.hybridViewCua(r.envelope) };
        if (r.envelope.status === 'ok') useAppStore.getState().loadEnvelope(r.envelope);
        else useAppStore.getState().loadUnsupported(r.envelope);
        return { ok: true, active: !!useAppStore.getState().active, error: useAppStore.getState().analysisError };
      }, fx);
      assert(loaded.ok && !loaded.error, `${fx.id}: consumer ${JSON.stringify(loaded)}`);
      if (fx.route_d.status !== 'SERVED') {
        await page.locator('canvas').waitFor({ state: 'detached' });
        assert(!loaded.active, `${fx.id}: refusal left active simulation`);
        const text = await page.locator('body').innerText();
        assert(text.includes(fx.envelope.learner_reason), `${fx.id}: refusal message absent`);
        assert(!text.includes(fx.route_d.refusal.code), `${fx.id}: refusal code leaked`);
        assert(!/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b|::/u.test(text), `${fx.id}: internal name leaked in refusal`);
        row.refusal = 'VISIBLE_NO_SCENE';
        continue;
      }
      await page.locator('.geo3d-canvas canvas').waitFor();
      const slider = page.locator('.geo3d-scrub input[type=range]');
      await slider.waitFor();
      const max = Number(await slider.getAttribute('max'));
      for (let step = 0; step <= max; step++) {
        await slider.fill(String(step));
        await page.waitForTimeout(65);
        const frame = await page.evaluate(async step => {
          const model = await import('/src/simulations/domains/geometry/scene3d-model.ts');
          const chart = await import('/src/simulations/domains/geometry/scene3d-chart.ts');
          const { withSubEntities, entitiesPresentAt } = await import('/src/simulations/domains/geometry/scene3d-subentities.ts');
          const { hybridTaiBuoc, giaTriDapSo } = await import('/src/simulations/domains/geometry/hybrid-preview-adapter.ts');
          const { envelope, view } = window.__adapter4;
          const scene = envelope.scene3d, world = withSubEntities(chart.veKhongGian(scene), model.objectsAt);
          const timeline = model.geometryTimeline(world);
          const anchor = timeline[step]?.anchor ?? step;
          const ids = entitiesPresentAt(world, anchor, model.objectsAt);
          const present = world.objects.filter(o => ids.has(o.id));
          const dependencies = present.flatMap(o => (o.depends ?? []).filter(id => !ids.has(id)).map(id => `${o.id}->${id}`));
          const rendered = window.__geo3d_rendered_object_ids ?? [];
          const unknown = rendered.filter(id => !world.objects.some(o => o.id === id || o.type === 'section' && new RegExp(`^${o.id}#\\d+c?f?$`).test(id)));
          const early = rendered.filter(id => !ids.has(id) && !present.some(o => o.type === 'section' && id.startsWith(o.id + '#')));
          const quantities = hybridTaiBuoc(view, world, anchor).answers;
          // Test-only operator readout. The learner UI's final-answer hiding policy is preserved.
          let readout = document.querySelector('[data-adapter4-readout]');
          if (!readout) { readout = document.createElement('aside'); readout.dataset.adapter4Readout = ''; document.body.append(readout); }
          readout.replaceChildren(...quantities.map(q => {
            const item = document.createElement('p'); item.dataset.quantity = q.quantity_id;
            item.textContent = `${scene.objects.find(o => o.id === q.quantity_id).label}: ${giaTriDapSo(q)}`; return item;
          }));
          const progress = scene.formation.steps[anchor]?.geometry_progress ?? [];
          const edgeIds = [...(window.__geo3d_visible_edge_ids ?? []), ...(window.__geo3d_hidden_edge_ids ?? []), ...(window.__geo3d_mixed_edge_ids ?? [])];
          const quantityEarly = quantities.map(q => q.quantity_id).filter(id => !ids.has(id));
          return { step, anchor, rendered, dependencies, unknown, early, quantityEarly, progress, edgeIds,
            duplicates: window.__geo3d_duplicate_visual_owner_ids ?? [],
            quantityIds: quantities.map(q => q.quantity_id), solids: rendered.filter(id => world.objects.find(o => o.id === id)?.type === 'solid') };
        }, step);
        assert(!frame.dependencies.length && !frame.unknown.length && !frame.early.length && !frame.duplicates.length, `${fx.id}: objects/dependencies ${JSON.stringify(frame)}`);
        assert(!frame.quantityEarly.length, `${fx.id}: answer before its quantity exists at ${step}: ${frame.quantityEarly}`);
        for (const progress of frame.progress) {
          const polygon = fx.envelope.scene3d.objects.find(o => o.id === progress.object_id).polygon;
          const count = progress.closed ? polygon.length : progress.visible_edge_ids.length + 1;
          const renderId = `${progress.object_id}#${count}${progress.closed ? 'c' : ''}${progress.fill_visible ? 'f' : ''}`;
          assert(frame.rendered.includes(renderId), `${fx.id}: section progress missing at ${step}: ${renderId}`);
          assert(!progress.fill_visible || progress.closed, `${fx.id}: open section filled`);
          // Independent of `entitiesPresentAt` (which admits every section sub-entity once the section exists).
          if (!progress.closed) {
            const sub = frame.rendered.filter(id => id.startsWith(`${progress.object_id}::`));
            assert(!sub.some(id => id.includes('::face:')), `${fx.id}: open section face drawn at ${step}`);
            const ahead = sub.filter(id => id.includes('::vertex:') && Number(id.split('::vertex:')[1]) > progress.visible_edge_ids.length);
            assert(!ahead.length, `${fx.id}: section vertices ahead of edges at ${step}: ${ahead}`);
          }
        }
        row.frames.push(frame);
      }
      const exact = fx.route_d.answer_exact;
      for (const [id, answer] of Object.entries(fx.route_d.answers)) {
        const text = await page.locator(`[data-quantity="kq_${id}"]`).innerText();
        const rhs = answer.includes('=') ? answer.slice(answer.lastIndexOf('=')+1).trim() : answer;
        assert(text.includes(rhs), `${fx.id}: readout mismatch`);
        assert(fx.envelope.scene3d.objects.find(o => o.id === `kq_${id}`).value.replace(/\s/g, '') === exact[id].coef.replace(/\s/g, ''), 'engine binding');
      }
      row.readouts = Object.keys(exact).length;
      const canvas = page.locator('.geo3d-canvas canvas');
      const filled = docPNG(await canvas.screenshot());
      await page.evaluate(() => window.__geo3d_set_section_fill_visible(false));
      const empty = docPNG(await canvas.screenshot());
      let ownPixels = 0;
      for (let i = 0; i < filled.rgba.length; i += 4) {
        if (Math.abs(filled.rgba[i]-empty.rgba[i])+Math.abs(filled.rgba[i+1]-empty.rgba[i+1])+Math.abs(filled.rgba[i+2]-empty.rgba[i+2]) > 30) ownPixels++;
      }
      assert(ownPixels > 0, `${fx.id}: section produced no own raster pixels`);
      row.sectionOwnPixels = ownPixels;
      await page.evaluate(() => window.__geo3d_set_section_fill_visible(true));
      // Product selection and highlight must keep canonical dash policy and geometry.
      await page.getByRole('button', { name: 'Khám phá', exact: true }).click();
      await page.getByRole('menuitemcheckbox', { name: 'Thành phần', exact: true }).click();
      const target = fx.route_d.sections.flatMap(s => s.vertices).find(v => v.provenance === 'DERIVED_FRESH')?.label
        ?? fx.envelope.scene3d.objects.find(o => o.type === 'section').id;
      const item = page.locator(`[data-tree-id="${target}"]`);
      await item.evaluate(el => { for (let p = el.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS') p.open = true; });
      const before = await page.evaluate(() => window.__geo3d_edge_dash_signature);
      await item.click(); await page.waitForTimeout(100);
      const selected = await page.evaluate(() => ({ id: window.__geo3d_selected_id, highlight: window.__geo3d_highlighted_ids, dash: window.__geo3d_edge_dash_signature }));
      assert(selected.id === target && selected.highlight.includes(target), `${fx.id}: highlight failed`);
      assert(JSON.stringify(before) === JSON.stringify(selected.dash), `${fx.id}: highlight changed dash policy`);
      row.selection = selected.id;
      if (fx.route_d.sections.some(s => s.vertices.some(v => v.label === target && v.provenance === 'DERIVED_FRESH'))) {
        const inspector = await page.locator('.geo3d-soi').innerText();
        assert(inspector.includes('Điểm dựng phụ'), `${fx.id}: derived role missing`);
        row.derivedRole = 'Điểm dựng phụ';
      }
      const text = await page.locator('body').innerText();
      assert(!/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b|::/u.test(text), `${fx.id}: internal name leaked`);
      const width = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(width <= viewport.width + 1, `${fx.id}: horizontal overflow ${width}`);
      if (['PARA-0', 'CORPUS-DEV10-prism-area', 'PARTIAL-1of2-construct'].includes(fx.id)) {
        const file = `${fx.id}-${viewport.width}.png`, png = await page.screenshot();
        writeFileSync(join(out, file), png); row.image = { file, sha256: sha(png) };
      }
      console.log(`${fx.id} ${viewport.width} PASS (${row.frames.length} frames)`);
    }
    await context.close();
  }
  assert(!errors.length && !forbidden.length, 'browser exception/console/network failure');
} catch (e) { code = 1; errors.push({ type: 'acceptance', message: e.message }); }
finally {
  await browser.close();
  const receipt = { status: code ? 'FAIL' : 'FRONTEND_CONSUMER_ACCEPTANCE_PASS', source_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    tree_clean: treeClean,
    source_sha256: sha(bytes), harness_sha256: sha(readFileSync(import.meta.filename)), browser: 'Chrome headless / SwiftShader', provider_calls: 0,
    math_authority: 'engine certificates and locked numeric oracle, not screenshots', human_visual_review: 'NOT_APPROVED',
    readout_scope: 'test-only operator readout via shared hybridTaiBuoc/giaTriDapSo; final answers remain hidden in learner UI',
    results, errors, forbidden };
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify({ status: receipt.status, rows: results.length, errors }));
}
process.exitCode = code;
