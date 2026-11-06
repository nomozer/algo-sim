// Production-only, offline, symmetric browser measurement. Never writes into an earlier run.
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import { gzipSync } from 'node:zlib';
import ts from 'typescript';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const arg = (key, fallback) => process.argv.includes(key) ? process.argv[process.argv.indexOf(key) + 1] : fallback;
const dist = resolve(arg('--dist', 'dist'));
const out = resolve(arg('--out'));
const seconds = Number(arg('--seconds', '15'));
const headed = process.argv.includes('--headed');
const software = process.argv.includes('--software');
const uiOnly = process.argv.includes('--ui');
const navOnly = process.argv.includes('--navigation');
const scenariosOnly = process.argv.includes('--scenarios');
const stepsOnly = process.argv.includes('--step-profile');
const only = arg('--only', '').split(',').filter(Boolean);
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const json = path => JSON.parse(readFileSync(path, 'utf8'));
const samples = json('src/data/geometry-samples.json').samples;
const audit = json('../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json');
const source = readFileSync('src/simulations/domains/geometry/axo-cross-family-scene3d-acceptance.test.tsx', 'utf8');
const fixture = (name, text = source) => {
  const file = ts.createSourceFile('fixture.tsx', text, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TSX);
  let expression;
  const visit = node => { if (ts.isVariableDeclaration(node) && node.name.getText(file) === name) expression = node.initializer?.getText(file); ts.forEachChild(node, visit); };
  visit(file); assert.ok(expression, `Missing existing fixture ${name}`);
  return vm.runInNewContext(ts.transpileModule(`(${expression});`, {
    compilerOptions: { target: ts.ScriptTarget.ES2022 },
  }).outputText);
};
const baseEnvelope = samples[0].envelope;
const fixtures = [
  ...['thiet-dien-chop', 'cau-cat-mat-phang', 'non-thiet-dien-truc', 'tru-thiet-dien-tron', ...(process.argv.includes('--inspect') ? ['cau-the-tich', 'mat-cheo-sac', 'mp-vuong-goc-duong', 'tru-truc-xien'] : [])].map(id => ({ id, envelope: samples.find(s => s.id === id).envelope })),
  { id: 'cube-hexagon', envelope: { ...baseEnvelope, title: 'Lập phương và thiết diện UVWXYZ', description: 'Cho hình lập phương PQRS.P′Q′R′S′ cạnh 2. Gọi U, V, W lần lượt là trung điểm của PQ, QR, RR′. Dựng thiết diện của hình lập phương bởi mặt phẳng (UVW).', scene3d: fixture('CUBE_HEX_SCENE') } },
  { id: 'oblique-prism', envelope: { ...baseEnvelope, title: 'Lăng trụ xiên', description: 'Dựng lăng trụ xiên ABC.A′B′C′ với đáy ABC và đường cao A′H vuông góc với (ABC), H thuộc đáy. Phân biệt đường cao với cạnh bên AA′.', scene3d: fixture('OBLIQUE_PRISM_SCENE') } },
  // SYNTHETIC. The frozen family07 problem_text uses the letter D for two points (midpoint of SA and the second apex);
  // the scene names them D and D1, so the presented statement is the corrected one locked in fixture-point-identity.test.tsx.
  { id: 'dense-multi-solid', envelope: { ...baseEnvelope, title: 'Khối chóp và khối thành phần', description: fixture('DENSE_MULTI_SOLID_STATEMENT', readFileSync('src/simulations/domains/geometry/fixture-point-identity.test.tsx', 'utf8')), scene3d: audit.find(s => s.id.startsWith('family07')).scene } },
  ...(process.argv.includes('--inspect') ? [{ id: 'true-oblique-cylinder', envelope: { ...baseEnvelope, title: 'Hình trụ xiên thật', description: 'Hai đường tròn đáy có mặt phẳng song song; trục OO′ không vuông góc với đáy. Quan sát đường cao và trục của hình trụ xiên.', scene3d: fixture('TRUE_OBLIQUE_CYLINDER_SCENE') } }] : []),
].filter(f => !only.length || only.includes(f.id));
// Keep synthetic fixtures independent in the existing config-keyed history/recovery stores.
for (const f of fixtures.filter(f => !samples.some(s => s.id === f.id))) {
  f.envelope.config = { ...f.envelope.config, title: f.envelope.title };
}
writeFileSync(join(out, 'inputs.json'), JSON.stringify(fixtures.map(f => ({ id: f.id, description: f.envelope.description, scene3d: f.envelope.scene3d })), null, 2));
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname.startsWith('/api/')) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(pathname === '/api/health' ? { ok: true, hasKey: false } : { user: null })); return; }
  const file = join(dist, pathname.includes('.') ? pathname : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const stats = a => {
  const x = [...a].sort((a, b) => a - b);
  return { n: x.length, median: x[Math.floor(x.length * .5)] ?? null, p95: x[Math.floor(x.length * .95)] ?? null, p99: x[Math.floor(x.length * .99)] ?? null, max: x.at(-1) ?? null };
};
const report = { schema: 'axo-performance/1', dist, seconds, headed, software, viewport: { width: 1440, height: 900 }, dpr: 1, provider_calls: 0, rows: [], errors: [], forbidden: [] };
let browser;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: !headed, args: software ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [] });
  report.browser = browser.version();
  const system = await browser.newBrowserCDPSession();
  report.gpu = (await system.send('SystemInfo.getInfo')).gpu;
  const ctx = await browser.newContext({ viewport: report.viewport, deviceScaleFactor: 1 });
  await ctx.route('**/*', route => {
    if (new URL(route.request().url()).origin !== url) { report.forbidden.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  await ctx.addInitScript(() => {
    const m = window.__axoMeasure = { active: false, frames: [], callbacks: [], events: [], longTasks: [], gl: {}, primitives: { triangles: 0, lines: 0 }, contexts: 0, commits: 0, lastDraw: 0, draws: 0, phase: '' };
    new MutationObserver(() => {
      if (!m.libraryQueued && document.querySelector('#view-library [data-lib-prob]')) {
        m.libraryQueued = true;
        requestAnimationFrame(() => { m.libraryPaint = performance.now(); });
      }
    }).observe(document, { subtree: true, childList: true });
    const hook = { supportsFiber: true, inject: () => 1, onCommitFiberRoot: () => { if (m.active) m.commits++; }, onCommitFiberUnmount() {} };
    window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = hook;
    new PerformanceObserver(list => { if (m.active) for (const e of list.getEntries()) m.longTasks.push({ phase: m.phase, t: e.startTime, ms: e.duration }); }).observe({ type: 'longtask', buffered: false });
    const raf = window.requestAnimationFrame.bind(window);
    let last = null;
    window.requestAnimationFrame = fn => raf(t => {
      const start = performance.now(), before = m.draws;
      fn(t);
      if (!m.active) return;
      m.callbacks.push({ phase: m.phase, t, ms: performance.now() - start, drew: before !== m.draws });
      if (before !== m.draws && last !== t) {
        m.frames.push({ phase: m.phase, t, interval: last === null ? null : t - last }); last = t;
      }
    });
    const getContext = HTMLCanvasElement.prototype.getContext;
    const seen = new WeakSet();
    HTMLCanvasElement.prototype.getContext = function(...args) {
      const gl = getContext.apply(this, args);
      if (gl && args[0].startsWith('webgl') && !seen.has(gl)) {
        seen.add(gl); m.contexts++;
        for (const name of ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced', 'createBuffer', 'deleteBuffer', 'bufferData', 'createProgram', 'deleteProgram', 'createTexture', 'deleteTexture']) {
          const original = gl[name]; if (!original) continue;
          gl[name] = function(...a) {
            if (m.active) m.gl[name] = (m.gl[name] ?? 0) + 1;
            if (m.active && name.startsWith('draw')) {
              const count = name.startsWith('drawElements') ? a[1] : a[2];
              const instances = name.endsWith('Instanced') ? (name.startsWith('drawElements') ? a[4] : a[3]) : 1;
              if (a[0] === gl.TRIANGLES) m.primitives.triangles += count / 3 * instances;
              else if (a[0] === gl.TRIANGLE_STRIP || a[0] === gl.TRIANGLE_FAN) m.primitives.triangles += Math.max(0, count - 2) * instances;
              else if (a[0] === gl.LINES) m.primitives.lines += count / 2 * instances;
              else if (a[0] === gl.LINE_STRIP) m.primitives.lines += Math.max(0, count - 1) * instances;
            }
            if (name.startsWith('draw')) {
              m.lastDraw = performance.now(); m.draws++;
              if (!m.firstSceneDraw && window.__geo3d_rendered_object_ids?.length) m.firstSceneDraw = m.lastDraw;
            }
            return original.apply(this, a);
          };
        }
        const ext = gl.getExtension('WEBGL_debug_renderer_info');
        m.renderer = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
        m.gpuTimerAvailable = !!gl.getExtension('EXT_disjoint_timer_query_webgl2');
      }
      return gl;
    };
    const add = EventTarget.prototype.addEventListener, remove = EventTarget.prototype.removeEventListener;
    const wrappers = new WeakMap();
    EventTarget.prototype.addEventListener = function(type, fn, options) {
      if (!fn || !['pointerdown', 'pointermove', 'pointerup', 'wheel'].includes(type)) return add.call(this, type, fn, options);
      let byType = wrappers.get(fn); if (!byType) wrappers.set(fn, byType = new Map());
      let wrapped = byType.get(type);
      if (!wrapped) { wrapped = function(e) { const t = performance.now(); try { return typeof fn === 'function' ? fn.call(this, e) : fn.handleEvent(e); } finally { if (m.active) m.events.push({ phase: m.phase, type, ms: performance.now() - t }); } }; byType.set(type, wrapped); }
      return add.call(this, type, wrapped, options);
    };
    EventTarget.prototype.removeEventListener = function(type, fn, options) { return remove.call(this, type, wrappers.get(fn)?.get(type) ?? fn, options); };
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  page.on('pageerror', e => report.errors.push(e.message.split('\n')[0]));
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Performance.enable');
  const startProfile = async () => {
    await cdp.send('Profiler.enable'); await cdp.send('Profiler.start');
    await cdp.send('Tracing.start', { categories: 'devtools.timeline,v8,blink.user_timing,disabled-by-default-devtools.timeline', transferMode: 'ReturnAsStream' });
  };
  const stopProfile = async name => {
    const profile = await cdp.send('Profiler.stop');
    writeFileSync(join(out, `${name}-cpu.json.gz`), gzipSync(JSON.stringify(profile.profile)));
    const complete = new Promise(r => cdp.once('Tracing.tracingComplete', r)); await cdp.send('Tracing.end');
    const { stream } = await complete; let trace = '';
    while (true) { const data = await cdp.send('IO.read', { handle: stream }); trace += data.data; if (data.eof) break; }
    await cdp.send('IO.close', { handle: stream });
    writeFileSync(join(out, `${name}-trace.json.gz`), gzipSync(trace));
  };
  await page.goto(url);
  await page.waitForFunction(() => !!window.__ALGO_SIM_STORE__);
  const save = () => writeFileSync(join(out, 'receipt.json'), JSON.stringify(report, null, 2));
  const snapshot = () => page.evaluate(() => ({
    camera: window.__geo3d_camera_snapshot, target: window.__geo3d_camera_target,
    visible: window.__geo3d_visible_edge_ids, hidden: window.__geo3d_hidden_edge_ids, mixed: window.__geo3d_mixed_edge_ids,
    spans: window.__geo3d_edge_spans, duplicates: window.__geo3d_duplicate_visual_owner_ids,
    rendered: window.__geo3d_rendered_object_ids, witnesses: window.__geo3d_witness_ids,
    fat: window.__geo3d_fat_line_summary, goal: window.__geo3d_goal_completion,
    rendererStats: window.__geo3d_renderer_stats ?? null,
    stepState: window.__geo3d_step_highlight_state,
    selectedId: window.__geo3d_selected_id,
    roles: window.__geo3d_step_visual_roles,
    auxiliaryHidden: window.__geo3d_auxiliary_hidden_ids,
    layers: { shell: window.__geo3d_shell_visible, plane: window.__geo3d_plane_visible, section: window.__geo3d_section_visible },
    inputObjects: window.__ALGO_SIM_STORE__?.getState().active?.envelope?.scene3d?.objects.map(o => ({ id: o.id, type: o.type, render: o.render })),
  }));
  const load = async envelope => {
    const t = await page.evaluate(e => { const t = performance.now(); window.__ALGO_SIM_STORE__.getState().loadEnvelope(e); return t; }, envelope);
    await page.waitForFunction(t => window.__axoMeasure.lastDraw > t && !!document.querySelector('#dock-steps-ul [data-step]'), t);
    return page.evaluate(t => window.__axoMeasure.lastDraw - t, t);
  };
  const settle = () => page.waitForFunction(() => (window.__geo3d_step_highlight_state?.pulse ?? 0) < .001 && performance.now() - window.__axoMeasure.lastDraw > 120);
  const stepTo = async index => {
    const t = await page.evaluate(i => { const t = performance.now(); document.querySelector(`#dock-steps-ul [data-step="${i}"]`).click(); return t; }, index);
    await page.waitForFunction(t => window.__axoMeasure.lastDraw > t, t);
    return page.evaluate(t => window.__axoMeasure.lastDraw - t, t);
  };
  const orbit = async (duration, phase) => {
    const b = await page.locator('.geo3d-canvas canvas').boundingBox();
    await page.evaluate(p => window.__axoMeasure.phase = p, phase);
    const x = b.x + b.width * .48, y = b.y + b.height * .46;
    await page.mouse.move(x, y); await page.mouse.down();
    const end = Date.now() + duration * 1000;
    let i = 0;
    while (Date.now() < end) {
      await page.mouse.move(x + Math.sin(i * .11) * b.width * .2, y + Math.sin(i * .07) * b.height * .10);
      i++;
      await new Promise(r => setTimeout(r, 16)); // Defined input cadence, excluded from latency measurements.
    }
    await page.mouse.up();
  };
  if (navOnly) {
    report.navigation = { coldLibraryMs: [], coldOpenMs: [], warmReopenMs: [], backMs: [], forwardMs: [] };
    const timed = async (action, ready) => {
      const t = await page.evaluate(() => performance.now()); await action(); await ready(t);
      return page.evaluate(t => window.__axoMeasure.lastDraw - t, t);
    };
    for (let i = 0; i < 12; i++) {
      await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
      await page.goto(`${url}/library`);
      await page.waitForFunction(() => window.__axoMeasure.libraryPaint > 0);
      report.navigation.coldLibraryMs.push(await page.evaluate(() => window.__axoMeasure.libraryPaint));
      assert.equal(await page.locator('.geo3d-canvas canvas').count(), 0, 'Library must not mount a scene');
      await page.goto(`${url}/simulation/pyramid-cross-section`);
      await page.waitForFunction(() => window.__axoMeasure.lastDraw > 0 && window.__geo3d_rendered_object_ids?.length > 0);
      report.navigation.coldOpenMs.push(await page.evaluate(() => window.__axoMeasure.firstSceneDraw));
      await cdp.send('Network.setCacheDisabled', { cacheDisabled: false });
      await page.evaluate(e => window.__ALGO_SIM_STORE__.getState().loadEnvelope(e, 'cau-the-tich'), samples.find(s => s.id === 'cau-the-tich').envelope);
      await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'cau-the-tich'); await settle();
      report.navigation.warmReopenMs.push(await load(samples.find(s => s.id === 'thiet-dien-chop').envelope)); await settle();
      report.navigation.backMs.push(await timed(() => page.goBack(), t => page.waitForFunction(t => window.__axoMeasure.lastDraw > t && window.__ALGO_SIM_STORE__.getState().activeSampleId === 'cau-the-tich', t)));
      await settle();
      report.navigation.forwardMs.push(await timed(() => page.goForward(), t => page.waitForFunction(t => window.__axoMeasure.lastDraw > t && window.__ALGO_SIM_STORE__.getState().activeSampleId === 'thiet-dien-chop', t)));
      save();
    }
    report.navigation.summary = Object.fromEntries(Object.entries(report.navigation).filter(([,v]) => Array.isArray(v)).map(([k,v]) => [k, stats(v)]));
    console.log(JSON.stringify(report.navigation.summary)); save();
  }
  if (uiOnly) {
    report.uiChecks = [];
    let currentAction = '';
    const check = async (name, fn) => {
      if (process.argv.includes('--responsive-only') && !name.startsWith('responsive')) return;
      if (process.argv.includes('--zoom-only') && !name.startsWith('desktop browser zoom')) return;
      if (process.argv.includes('--memory-only') && !name.startsWith('22 problem')) return;
      const row = { name }; report.uiChecks.push(row);
      try { row.evidence = await fn(); row.status = 'PASS'; }
      catch (e) { row.status = 'FAIL'; row.error = e.message.slice(0, 2200); row.action = currentAction; await page.screenshot({ path: join(out, `failure-${report.uiChecks.length}.png`) }).catch(() => {}); }
      save(); console.log(`${row.status} ${name}${row.error ? `: ${row.error}` : ''}`);
    };
    const selectChip = async id => {
      currentAction = `select object ${id}`;
      const chip = page.locator(`[data-entity-chip="${id}"]`).first();
      if (!await chip.isVisible()) {
        const more = page.locator('#btn-dock-entities-more');
        if (await more.count() && await more.getAttribute('aria-expanded') !== 'true') await more.click();
      }
      await page.locator(`[data-entity-chip="${id}"]`).first().click();
      await page.waitForFunction(id => window.__geo3d_selected_id === id, id);
    };
    const loadSample = async id => { const s = samples.find(s => s.id === id); await load(s.envelope); const n = await page.locator('#dock-steps-ul [data-step]').count(); await stepTo(n - 1); await settle(); return n; };
    // The construction flow presents no answers: no reveal button, no conclusion panel, no answer text in the DOM.
    const assertNoAnswerSurface = async (...answers) => {
      assert.equal(await page.locator('#dock-goal-reveal, #dock-goal-conclusion, [data-conclusion-id]').count(), 0, 'Answer surface present');
      const html = await page.evaluate(() => document.documentElement.outerHTML);
      for (const a of answers) assert.ok(!html.includes(a), `Answer ${a} present in DOM`);
    };
    await check('sphere final step carries no answer surface, given data stays', async () => {
      await loadSample('cau-cat-mat-phang');
      await assertNoAnswerSurface('16π');
      assert.match(await page.locator('#dock-given-params').innerText(), /R = 5/);
      await stepTo(0); await assertNoAnswerSurface('16π');
      await loadSample('cau-the-tich');
      await assertNoAnswerSurface('36π');
      return { sphere: await snapshot() };
    });
    await check('one-step sphere Play Pause and renderer reuse', async () => {
      await loadSample('cau-the-tich');
      const contexts = await page.evaluate(() => window.__axoMeasure.contexts);
      assert.equal(await page.locator('#dock-steps-ul [data-step]').count(), 1);
      await page.locator('#pa-play').click();
      await page.waitForFunction(() => window.__geo3d_sphere_formation_state?.progress > 0 && window.__geo3d_sphere_formation_state?.progress < 1);
      const during = await page.evaluate(() => window.__geo3d_sphere_formation_state);
      await page.locator('#pa-play').click();
      await page.waitForFunction(() => window.__geo3d_sphere_formation_state?.progress === 1);
      assert.equal(await page.evaluate(() => window.__axoMeasure.contexts), contexts);
      return { during, after: await snapshot() };
    });
    await check('X selection preserves IX, hiding X preserves sphere, Undo and Ctrl+Z', async () => {
      await loadSample('cau-cat-mat-phang');
      await stepTo(0); await selectChip('cau__ref_pt');
      let state = await snapshot();
      assert.ok(state.rendered.includes('cau__radius'), 'IX must be rendered with X');
      await page.locator('#btn-card-hide').click();
      await page.waitForFunction(() => window.__geo3d_auxiliary_hidden_ids.includes('cau__ref_pt') || !window.__geo3d_rendered_object_ids.includes('cau__ref_pt'));
      state = await snapshot(); assert.ok(state.rendered.includes('cau'), 'Sphere must survive hiding X');
      await page.locator('#btn-undo-interaction').click();
      await page.waitForFunction(() => window.__geo3d_rendered_object_ids.includes('cau__ref_pt'));
      await page.keyboard.press('Control+z');
      await page.waitForFunction(() => !window.__geo3d_selected_id);
      await selectChip('cau__ref_pt');
      await page.evaluate(() => { const input = document.createElement('input'); input.id = 'acceptance-text'; document.body.append(input); input.focus(); });
      await page.keyboard.type('abc'); await page.keyboard.press('Control+z');
      assert.equal(await page.locator('#acceptance-text').inputValue(), '');
      assert.equal(await page.evaluate(() => window.__geo3d_selected_id), 'cau__ref_pt');
      await page.locator('#acceptance-text').evaluate(el => el.remove());
      return { afterHide: state, restored: await snapshot() };
    });
    await check('camera panels, zoom reversal, reset and geometric orbit center', async () => {
      await loadSample('thiet-dien-chop');
      await page.locator('#btn-reset-pos').click(); await settle(); const original = await snapshot();
      await page.locator('#btn-collapse-dock').click(); await settle(); const collapsed = await snapshot();
      assert.deepEqual(collapsed.camera.position, original.camera.position);
      await page.locator('#btn-reopen-dock-capsule').click(); await settle();
      assert.deepEqual((await snapshot()).camera.position, original.camera.position);
      await orbit(1, 'ui-reverse'); await page.mouse.wheel(0, -300); await settle();
      await page.locator('#btn-reset-pos').click(); await settle(); const reset = await snapshot();
      assert.deepEqual(reset.camera.position, original.camera.position);
      return { original, collapsed, reset };
    });
    await check('canonical and Vietnamese URLs, per-problem Back Forward F5 snapshots', async () => {
      await page.goto(`${url}/simulation/thiet-dien-chop`); await page.waitForSelector('#dock-steps-ul [data-step]'); await settle();
      await page.waitForURL('**/simulation/pyramid-cross-section');
      await stepTo(2); await settle();
      const before = await page.locator('#dock-steps-ul [aria-current="step"]').getAttribute('data-step');
      await page.evaluate(e => window.__ALGO_SIM_STORE__.getState().loadEnvelope(e, 'cau-the-tich'), samples.find(s => s.id === 'cau-the-tich').envelope);
      await page.waitForURL('**/simulation/sphere-radius-and-volume');
      await page.goBack(); await page.waitForSelector('#dock-steps-ul [data-step]');
      await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'thiet-dien-chop');
      assert.equal(await page.locator('#dock-steps-ul [aria-current="step"]').getAttribute('data-step'), before);
      await page.reload(); await page.waitForSelector('#dock-steps-ul [data-step]');
      assert.equal(await page.locator('#dock-steps-ul [aria-current="step"]').getAttribute('data-step'), before);
      await page.goForward(); await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'cau-the-tich');
      return { restoredStep: before, url: page.url() };
    });
    const sphereTests = readFileSync('src/simulations/domains/geometry/axo-pedagogical-presentation-policy.test.tsx', 'utf8');
    // SYNTHETIC fixtures (not product routes). Each carries its own statement and a distinct config identity:
    // reusing samples[0]'s config made the store resolve them to the S.ABCD sample (URL, saved step, statement).
    const sphereBoundary = {
      greatCircleScene: ['Mặt phẳng qua tâm cắt mặt cầu', 'Cho mặt cầu (S) tâm I bán kính R = 5 và mặt phẳng (P) đi qua tâm I. Dựng giao tuyến của (P) và (S).'],
      tangentScene: ['Mặt phẳng tiếp xúc với mặt cầu', 'Cho mặt cầu (S) tâm K bán kính R = 5 và mặt phẳng (α) cách K một khoảng bằng 5. Dựng điểm chung của (α) và (S).'],
      nonIntersectingScene: ['Mặt phẳng không cắt mặt cầu', 'Cho mặt cầu (S) tâm I bán kính R = 5 và mặt phẳng (P) cách I một khoảng bằng 7. Xét vị trí tương đối của (P) và (S).'],
    };
    for (const [name, [title, description]] of Object.entries(sphereBoundary)) {
      await check(`sphere boundary ${name}`, async () => {
        const scene = fixture(name, sphereTests);
        await page.evaluate(e => window.__ALGO_SIM_STORE__.getState().loadEnvelope(e), { ...baseEnvelope, title, description, source: 'synthetic_fixture', config: { ...baseEnvelope.config, title }, scene3d: scene });
        await page.waitForSelector('#ws-dock');
        assert.equal(await page.evaluate(() => window.__ALGO_SIM_STORE__.getState().activeSampleId), null, 'Synthetic fixture resolved to a catalog sample');
        assert.ok((await page.locator('#ws-dock').innerText()).includes(description), 'Dock statement does not match fixture');
        if (name === 'nonIntersectingScene') {
          await page.waitForSelector('.ws-math-contradiction-note');
          assert.equal(await page.locator('#dock-goal-conclusion').count(), 0);
          return { synthetic: true, refused: true, text: await page.locator('.ws-math-contradiction-note').innerText() };
        }
        await page.waitForSelector('#dock-steps-ul [data-step]'); await stepTo((await page.locator('#dock-steps-ul [data-step]').count()) - 1); await settle();
        const state = await snapshot();
        assert.deepEqual(state.duplicates, []);
        if (name === 'tangentScene') assert.equal(state.rendered.some(id => id.startsWith('circle')), false);
        const file = `${name}.png`; await page.screenshot({ path: join(out, file) }); return { synthetic: true, file, state };
      });
    }
    await check('22 problem switches retain one WebGL context with collected heap samples', async () => {
      for (const id of ['cau-cat-mat-phang', 'thiet-dien-chop', 'tru-thiet-dien-tron']) await loadSample(id);
      const heap = [], contexts = await page.evaluate(() => window.__axoMeasure.contexts);
      const switches = Number(arg('--switches', '22'));
      for (let i = 0; i < switches; i++) {
        await loadSample(['cau-cat-mat-phang', 'thiet-dien-chop', 'tru-thiet-dien-tron'][i % 3]);
        if (i % 3 === 0 || i === switches - 1) { await cdp.send('HeapProfiler.collectGarbage'); heap.push({ i, ...await cdp.send('Runtime.getHeapUsage') }); }
      }
      assert.equal(await page.evaluate(() => window.__axoMeasure.contexts), contexts);
      return { contexts, switches, warmupScenes: 3, heap };
    });
    for (const width of arg('--ui-widths', '360,390,430,768,1024,1440').split(',').map(Number)) {
      await page.setViewportSize({ width, height: width < 500 ? 844 : 900 });
      for (let repeat = 0; repeat < Number(arg('--ui-repeat', '1')); repeat++) {
      for (const id of arg('--ui-samples', 'cau-the-tich,cau-cat-mat-phang,thiet-dien-chop,tru-thiet-dien-tron,non-thiet-dien-truc').split(',')) {
        await check(`responsive ${width} ${id} cards, labels and scrolling`, async () => {
          currentAction = `load ${id}`;
          const n = await loadSample(id);
          // Per-problem recovery restores the last selection (e.g. X chosen by the X-selection check), and a
          // selected retired auxiliary keeps its chip only while selected. Start from no selection so the chip
          // list is the step's own list instead of a leftover from an earlier check.
          currentAction = 'clear restored selection';
          if (await page.locator('#btn-clear-pick').count()) await page.locator('#btn-clear-pick').click();
          await page.waitForFunction(() => !window.__geo3d_selected_id);
          const ids = await page.locator('[data-entity-chip]').evaluateAll(els => [...new Set(els.map(el => el.dataset.entityChip))]);
          const cards = [];
          for (const objectId of ids.slice(0, 8)) {
            await selectChip(objectId);
            const box = await page.locator('.context-object-card').evaluate(card => {
              const b = card.getBoundingClientRect(), title = card.querySelector('#ctx-obj-title'), close = card.querySelector('#btn-clear-pick').getBoundingClientRect();
              const t = title.getBoundingClientRect();
              return { id: window.__geo3d_selected_id, left: b.left, right: b.right, height: b.height, titleRight: t.right, closeLeft: close.left, titleOverflow: title.scrollWidth - title.clientWidth, cardOverflow: card.scrollWidth - card.clientWidth };
            });
            assert.ok(box.left >= -1 && box.right <= width + 1, 'Card is outside viewport');
            assert.ok(box.titleRight <= box.closeLeft + 1, 'Title overlaps close button');
            assert.ok(box.cardOverflow <= 1, 'Card text overflows');
            if (width < 500) assert.ok(box.height < 844 * .55, 'Card consumes most mobile viewport');
            cards.push(box); currentAction = `close object ${objectId}`; await page.locator('#btn-clear-pick').click();
          }
          const dimensions = await page.evaluate(() => {
            const canvas = document.querySelector('.geo3d-canvas canvas').getBoundingClientRect();
            return { documentWidth: document.documentElement.scrollWidth, viewport: innerWidth, canvas: { width: canvas.width, height: canvas.height }, touchAction: getComputedStyle(document.querySelector('.geo3d-canvas canvas')).touchAction };
          });
          assert.ok(dimensions.documentWidth <= dimensions.viewport + 1, 'Horizontal document overflow');
          assert.ok(dimensions.canvas.height > (width < 500 ? 250 : 350), '3D canvas is too short');
          assert.equal(dimensions.touchAction, 'none');
          if (id === 'cau-cat-mat-phang') { currentAction = 'no answer surface at final step'; await assertNoAnswerSurface('16π'); }
          const file = `responsive-${width}-${id}.png`; await page.screenshot({ path: join(out, file) });
          for (const i of [0, Math.floor((n - 1) / 2), n - 1]) {
            currentAction = `card at step ${i}`; await stepTo(i);
            const chips = page.locator('[data-entity-chip]:visible');
            if (!await chips.count()) await page.locator('#btn-dock-entities-more').click();
            assert.ok(await chips.count(), 'Step has no selectable object');
            await chips.first().click(); assert.equal(await page.locator('.context-object-card').count(), 1);
            await page.locator('#btn-clear-pick').click();
          }
          return { dimensions, cards, file };
        });
      }
      }
    }
    await check('desktop browser zoom 110 percent', async () => {
      await page.setViewportSize({ width: 1440, height: 900 }); await loadSample('cau-cat-mat-phang');
      await page.keyboard.press('Control+Equal');
      const nativeZoom = await page.waitForFunction(() => devicePixelRatio > 1.05 && devicePixelRatio < 1.15, null, { timeout: 2000 }).then(() => true, () => false);
      if (!nativeZoom) await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1309, height: 818, deviceScaleFactor: 1.1, mobile: false });
      await settle();
      const result = await page.evaluate(() => ({ width: innerWidth, dpr: devicePixelRatio, scrollWidth: document.documentElement.scrollWidth }));
      assert.ok(result.scrollWidth <= result.width + 1);
      result.nativeZoom = nativeZoom;
      result.method = nativeZoom ? 'Chrome keyboard browser zoom 110 percent' : 'CDP effective CSS viewport and DPR equivalent; browser UI zoom itself NOT TESTED';
      await page.screenshot({ path: join(out, 'desktop-effective-110-percent.png') }); return result;
    });
  }
  for (const f of uiOnly || navOnly ? [] : fixtures) {
    const row = { id: f.id, loadMs: [], stepMs: [], images: [], variants: [] }; report.rows.push(row); save();
    try {
      for (let i = 0; i < 3; i++) row.loadMs.push(await load(f.envelope));
      const count = await page.locator('#dock-steps-ul [data-step]').count(); row.stepCount = count;
      await stepTo(count - 1); await settle();
      row.before = await snapshot();
      for (const section of f.envelope.scene3d.objects.filter(o => o.surface_role === 'SECTION_REGION' && o.render === 'polygon')) {
        assert.ok(row.before.rendered.some(id => id === section.id || id.startsWith(`${section.id}#`)), `Final section ${section.id} was not rendered`);
        assert.ok(row.before.fat.maxSectionBorderWidth > 0, 'Section has no visible border');
      }
      if (process.argv.includes('--inspect')) {
        for (let angle = 0; angle < 3; angle++) {
          if (angle) await orbit(.3, `inspect-${angle}`);
          await settle();
          const file = `${f.id}-angle-${angle}.png`; await page.screenshot({ path: join(out, file) });
          row.images.push({ file, snapshot: await snapshot() });
        }
        save(); continue;
      }
      row.heapBefore = (await cdp.send('Runtime.getHeapUsage')).usedSize;
      if (stepsOnly) await startProfile();
      if (!scenariosOnly) {
      await page.evaluate(() => { window.__axoMeasure.active = true; window.__axoMeasure.phase = 'step-changes'; window.__axoMeasure.gl = {}; });
      for (let i = 0; i < 24; i++) row.stepMs.push(await stepTo(i % 2 ? count - 1 : Math.max(0, count - 2)));
      row.stepResources = await page.evaluate(() => { window.__axoMeasure.active = false; return { ...window.__axoMeasure.gl }; });
      if (stepsOnly) {
        await stopProfile(`${f.id}-steps`); row.stepSummary = stats(row.stepMs); save();
        console.log(JSON.stringify({ id: f.id, stepProfile: row.stepSummary, resources: row.stepResources })); continue;
      }
      await settle();
      row.heapBefore = (await cdp.send('Runtime.getHeapUsage')).usedSize;
      await page.evaluate(() => { const m = window.__axoMeasure; m.active = true; m.frames = []; m.callbacks = []; m.events = []; m.longTasks = []; m.gl = {}; m.commits = 0; window.__geo3d_reset_occlusion_performance?.(); });
      await orbit(seconds, 'continuous-orbit');
      await page.evaluate(() => window.__axoMeasure.active = false);
      row.orbit = await page.evaluate(() => ({ ...window.__axoMeasure, occlusion: window.__geo3d_occlusion_performance }));
      row.frameMs = stats(row.orbit.frames.slice(1).filter(f => f.phase === 'continuous-orbit' && f.interval !== null).map(f => f.interval));
      row.fps = row.frameMs.median === null ? null : 1000 / row.frameMs.median;
      const perFrame = new Map();
      for (const cb of row.orbit.callbacks.filter(f => f.drew)) {
        const entry = perFrame.get(cb.t) ?? { ms: 0, renders: 0 };
        entry.ms += cb.ms; entry.renders++; perFrame.set(cb.t, entry);
      }
      row.callbackMs = stats([...perFrame.values()].map(f => f.ms));
      row.rendersPerFrame = stats([...perFrame.values()].map(f => f.renders));
      row.events = Object.fromEntries(['pointerdown', 'pointermove', 'pointerup', 'wheel'].map(type => [type, stats(row.orbit.events.filter(e => e.type === type).map(e => e.ms))]));
      await settle();
      await startProfile();
      await orbit(3, 'profile-orbit');
      await stopProfile(f.id);
      }
      for (const variant of ['reverse', 'zoom', 'selected', 'hidden', 'isolated', 'collapsed', 'after-steps', 'returned']) {
        const reopen = page.locator('#btn-reopen-dock-capsule'); if (await reopen.isVisible()) await reopen.click();
        const restore = page.locator('#btn-restore-hidden-objects'); if (await restore.count()) await restore.click();
        const clear = page.locator('#btn-clear-pick'); if (await clear.count()) await clear.click();
        await stepTo(count - 1); await page.locator('#btn-reset-pos').click(); await settle();
        if (['selected', 'hidden', 'isolated'].includes(variant)) {
          await page.locator('[data-entity-chip]').first().click();
          await page.waitForFunction(() => !!window.__geo3d_selected_id);
          const selected = await page.evaluate(() => window.__geo3d_selected_id);
          if (variant === 'hidden' || variant === 'isolated') {
            const button = page.locator(variant === 'hidden' ? '#btn-card-hide' : '#btn-card-isolate');
            await button.click();
            assert.match(await button.getAttribute('class'), /is-active/);
            if (variant === 'hidden') assert.ok(!(await snapshot()).rendered.includes(selected), 'Hidden entity is still rendered');
            else assert.match(await page.locator('#dock-visibility-restore-bar').innerText(), /chỉ xem/);
          }
        }
        if (variant === 'collapsed') { await page.locator('#btn-collapse-dock').click(); assert.ok(await page.locator('#btn-reopen-dock-capsule').isVisible()); }
        if (variant === 'after-steps') { for (let j = 0; j < 4; j++) await stepTo(j % 2 ? count - 1 : 0); }
        if (variant === 'returned') { await load(samples.find(s => s.id === 'cau-the-tich').envelope); await load(f.envelope); await stepTo(count - 1); }
        await settle();
        await page.evaluate(phase => { const m = window.__axoMeasure; m.active = true; m.phase = phase; m.frames = []; m.callbacks = []; m.events = []; m.longTasks = []; m.gl = {}; m.primitives = { triangles: 0, lines: 0 }; m.commits = 0; }, variant);
        const responseMs = [];
        if (variant === 'zoom') {
          const b = await page.locator('.geo3d-canvas canvas').boundingBox(); await page.mouse.move(b.x + b.width * .5, b.y + b.height * .5);
          for (const delta of [150, -150, 250, -250]) {
            const t = await page.evaluate(() => performance.now()); await page.mouse.wheel(0, delta);
            await page.waitForFunction(t => window.__axoMeasure.lastDraw > t, t);
            responseMs.push(await page.evaluate(t => window.__axoMeasure.lastDraw - t, t));
          }
        }
        await orbit(1, variant);
        const motion = await page.evaluate(() => { window.__axoMeasure.active = false; return { ...window.__axoMeasure }; });
        const frameMs = stats(motion.frames.slice(1).map(f => f.interval));
        row.variants.push({ name: variant, snapshot: await snapshot(), frameMs, medianCadenceFps: frameMs.median ? 1000 / frameMs.median : null, responseMs, motion });
      }
      await settle(); row.after = await snapshot(); row.heapAfter = (await cdp.send('Runtime.getHeapUsage')).usedSize;
      for (let angle = 0; angle < (scenariosOnly ? 0 : 3); angle++) {
        if (angle) await orbit(.25, `capture-${angle}`);
        await settle();
        const file = `${f.id}-angle-${angle}.png`;
        await page.screenshot({ path: join(out, file) }); row.images.push({ file, snapshot: await snapshot() });
      }
      row.stepSummary = stats(row.stepMs); row.loadSummary = stats(row.loadMs);
      console.log(JSON.stringify({ id: f.id, medianCadenceFps: row.fps, frameMs: row.frameMs, cpuMs: row.callbackMs, stepMs: row.stepSummary, contexts: row.orbit?.contexts, buffers: row.orbit?.gl.createBuffer ?? 0, commits: row.orbit?.commits, variants: row.variants.length }));
    } catch (e) { row.error = e.message.split('\n')[0]; console.log(`${f.id}: ${row.error}`); }
    save();
  }
  report.summary = { stepMs: stats(report.rows.flatMap(r => r.stepMs)), frameMs: stats(report.rows.flatMap(r => r.orbit?.frames.slice(1).filter(f => f.interval !== null).map(f => f.interval) ?? [])) };
  save(); await ctx.close();
} finally { await browser?.close(); await new Promise(r => server.close(r)); }
process.exitCode = report.errors.length || report.forbidden.length || report.rows.some(r => r.error) || report.uiChecks?.some(r => r.status === 'FAIL') ? 1 : 0;
