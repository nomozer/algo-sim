// Real Chromium on the production build + loopback measured_app (local-first, ALLOW_LIVE_AI=0, no provider call).
// The learner path: type the problem, build, walk the construction timeline step by step, orbit / zoom / reset the
// camera, select an object, and check that no final answer is printed. Measures first-model and per-step latency and
// the JS heap across repeated problem switches (resource cleanup). Automated, not a student study.
// Constraint-defined plane sections (∥ plane, ⊥ line, ∥ base, line + point) plus the earlier section / intersection /
// altitude / 60°-not-120° cases; pan and the auxiliary toggle added (independent-geometry-plane-constraints).
// Usage (worktree root): node <this> <frontend/dist> <out_dir> [backendPort]
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const [dist, outDir] = process.argv.slice(2, 4).map((p) => resolve(p));
const backendPort = Number(process.argv[4] ?? 8767);
const P = 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. ';
const CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. ";
const MSA = 'Gọi M là trung điểm của SA. ';
const SEC = 'Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).';
const CASES = {
  section_parallel_plane: { goal: 'section', text: P + MSA + 'Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). ' + SEC },
  section_perpendicular_line: { goal: 'section', text: CUBE + "Mặt phẳng (P) đi qua B và vuông góc với đường thẳng AC'. Tìm thiết diện của hình lập phương cắt bởi (P)." },
  section_base_word: { goal: 'section', text: P + MSA + 'Mặt phẳng (P) qua M và song song với mặt đáy. Tìm thiết diện của hình chóp với mặt phẳng (P).' },
  section_line_point: { goal: 'section', text: P + 'Gọi M là trung điểm của SC. Mặt phẳng (P) chứa AB và đi qua M. ' + SEC },
  section_pyramid: { goal: 'section', text: P + 'Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).' },
  intersection_SAB_SCD: { goal: 'intersection', text: P + 'Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD).' },
  altitude_face_perp: { goal: 'altitude', text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.' },
  planes_60_not_120: { goal: 'angle', text: P + 'Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD).' },
};
const VIEWPORTS = [[1920, 1080], [1366, 768], [768, 1024], [390, 844]];
const FULL_VIEWPORT_CASES = new Set(['section_parallel_plane', 'section_perpendicular_line']);

const server = createServer((req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (path.startsWith('/api/')) {
    const proxy = request({ host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers }, (up) => {
      res.writeHead(up.statusCode, up.headers); up.pipe(res);
    });
    proxy.on('error', () => { res.writeHead(502); res.end(); });
    req.pipe(proxy); return;
  }
  const file = join(dist, path.includes('.') ? path : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' }[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--js-flags=--expose-gc', '--enable-precise-memory-info'] });

const frames = (page, n = 2) => page.evaluate((k) => new Promise((ok) => { const f = (i) => (i ? requestAnimationFrame(() => f(i - 1)) : ok()); f(k); }), n);
const counter = async (page) => {
  const t = (await page.locator('#pa-counter').innerText().catch(() => '')).match(/(\d+)\s*\/\s*(\d+)/);
  return t ? [Number(t[1]), Number(t[2])] : null;
};

async function load(page, text) {
  const box = page.getByRole('textbox', { name: 'Đề bài hình học không gian', exact: true });
  if (!(await box.isVisible().catch(() => false))) {          // in the workspace: the learner's "change problem" path
    await page.getByRole('button', { name: 'Đổi đề toán' }).first().click();
    await box.waitFor({ timeout: 15000 });
  }
  for (let k = 0; k < 3 && (await box.inputValue()) !== text; k++) {   // a re-render can clear a value typed too early
    await box.fill(text);
    await page.waitForTimeout(150);
  }
  const resp = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST', { timeout: 120000 });
  const t0 = Date.now();
  await page.getByRole('button', { name: 'Phân tích đề bằng AI', exact: true }).click();
  const body = await (await resp).json();
  await page.waitForSelector('#pa-counter', { timeout: 60000 });
  await page.waitForFunction(() => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent), null, { timeout: 60000 });
  await frames(page, 3);
  return { body, firstModelMs: Date.now() - t0 };
}

// A rendered owner id may carry a display suffix ("td_sec#4cf"): the goal is present when its id or id#suffix is drawn.
const has = (ids, id) => Boolean(ids?.some((x) => x === id || x.startsWith(id + '#')));

async function walkTimeline(page) {
  let c = await counter(page);
  for (let i = 0; i < 60 && c && c[0] > 1; i++) { await page.click('#pa-prev'); await frames(page); c = await counter(page); }
  const steps = [];
  for (let i = 0; i < 60; i++) {
    c = await counter(page);
    steps.push({ step: c?.[0], of: c?.[1],
      angle_construction_ids: await page.evaluate(() => window.__geo3d_angle_construction_ids ?? []),
      altitude_construction_ids: await page.evaluate(() => window.__geo3d_altitude_construction_ids ?? []),
      rendered_ids: await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []),
      witness_ids: await page.evaluate(() => window.__geo3d_witness_ids ?? []),
      rendered: (await page.evaluate(() => window.__geo3d_rendered_object_ids ?? [])).length });
    if (!c || c[0] >= c[1] || await page.isDisabled('#pa-next')) break;
    const t0 = await page.evaluate(() => performance.now());
    await page.click('#pa-next');
    await frames(page);
    steps.at(-1).next_ms = (await page.evaluate(() => performance.now())) - t0;
  }
  return steps;
}

async function cameraChecks(page) {
  const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
  const canvas = page.locator('canvas').first();
  const box = await canvas.boundingBox();
  const s0 = await snap();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  const t0 = await page.evaluate(() => performance.now());
  await page.mouse.move(box.x + box.width / 2 + 120, box.y + box.height / 2 + 30, { steps: 8 });
  await page.mouse.up();
  await frames(page);
  const orbitMs = (await page.evaluate(() => performance.now())) - t0;
  const s1 = await snap();
  await page.mouse.wheel(0, -300);
  await frames(page, 4);
  const s2 = await snap();
  const reset = page.getByRole('button', { name: /Đặt lại|Khôi phục/ }).first();
  let s3 = null;
  if (await reset.count() && await reset.isVisible()) { await reset.click(); await frames(page, 4); s3 = await snap(); }
  return { snapshot_available: s0 !== 'null', orbit_changes_camera: s1 !== s0, zoom_changes_camera: s2 !== s1,
           reset_available: s3 !== null, reset_returns_to_initial: s3 === null ? null : s3 === s0, orbit_ms: orbitMs };
}

// Pan (right-button drag: OrbitControls screen-space panning) and the "Hình phụ" display toggle (#btn-display-pop → #chk-aux).
async function panAndAuxiliary(page) {
  const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
  const box = await page.locator('canvas').first().boundingBox();
  const p0 = await snap();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down({ button: 'right' });
  await page.mouse.move(box.x + box.width / 2 + 90, box.y + box.height / 2 + 40, { steps: 8 });
  await page.mouse.up({ button: 'right' });
  await frames(page, 3);
  const p1 = await snap();
  const out = { pan_changes_camera: p1 !== p0 };
  const btn = page.locator('#btn-display-pop');
  if (await btn.count() && await btn.isVisible()) {
    await btn.click(); await frames(page);
    const chk = page.locator('#chk-aux');
    const hidden0 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
    const rendered0 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
    if (await chk.count() && await chk.isVisible()) {
      await chk.click(); await frames(page, 3);
      const hidden1 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
      const rendered1 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
      await chk.click(); await frames(page, 3);
      const hidden2 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
      Object.assign(out, { aux_toggle_available: true, aux_hidden_before: hidden0, aux_hidden_toggled: hidden1, aux_hidden_restored: hidden2,
                           rendered_before: rendered0, rendered_toggled: rendered1,
                           aux_toggle_changes_rendering: hidden1 !== hidden0 || rendered1 !== rendered0, aux_toggle_restores: hidden2 === hidden0 });
    } else out.aux_toggle_available = false;
    await page.keyboard.press('Escape'); await frames(page);
  } else out.aux_toggle_available = false;
  return out;
}

async function selectionCheck(page, goalId) {
  const chip = goalId && await page.locator(`[data-entity-chip="${goalId}"]`).count()
    ? page.locator(`[data-entity-chip="${goalId}"]`).first() : page.locator('[data-entity-chip]').first();
  if (goalId && !(await chip.isVisible().catch(() => false))) {          // goal chips may sit behind "Xem thêm"
    const more = page.locator('#btn-dock-entities-more');
    if (await more.count() && await more.isVisible()) { await more.click(); await frames(page); }
  }
  if (!(await chip.count()) || !(await chip.isVisible())) return { chip_available: false };
  const id = await chip.getAttribute('data-entity-chip');
  await chip.click();
  await frames(page);
  const sel = await page.evaluate(() => window.__geo3d_selected_id ?? null);
  return { chip_available: true, chip_id: id, selected_id: sel, selects: sel === id };
}

const rows = [];
const perf = [];
const cleanup = {};
try {
  for (const [name, c] of Object.entries(process.env.ONLY_CLEANUP ? {} : CASES)) {
    for (const [w, h] of VIEWPORTS) {
      if (!FULL_VIEWPORT_CASES.has(name) && w !== 1366) continue;
      const ctx = await browser.newContext({ viewport: { width: w, height: h } });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
      await page.goto(ORIGIN, { waitUntil: 'networkidle' });
      const { body, firstModelMs } = await load(page, c.text);
      const status = body.route_d?.status;
      const answers = Object.values(body.route_d?.answers ?? {});
      const steps = status === 'SERVED' ? await walkTimeline(page) : [];
      const last = steps.at(-1);
      const before = steps.slice(0, -1);
      const cam = status === 'SERVED' ? await cameraChecks(page) : null;
      const panAux = status === 'SERVED' ? await panAndAuxiliary(page) : null;
      const objs = body.envelope?.scene3d?.objects ?? [];
      const goalId = c.goal === 'section' ? objs.find((o) => o.type === 'section')?.id
        : c.goal === 'intersection' ? objs.find((o) => o.producer === 'intersect_plane_plane')?.id : null;
      const sel = status === 'SERVED' ? await selectionCheck(page, goalId) : null;
      const text = await page.evaluate(() => document.body.innerText);
      const leaked = answers.filter((a) => {
        const v = String(a).replace(/^cos²=/, '').replace(/\s/g, '');
        return v.length >= 2 && text.replace(/\s/g, '').includes(v);
      });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      const minTarget = await page.evaluate(() => Math.min(...['#pa-prev', '#pa-next'].map((s) => {
        const r = document.querySelector(s)?.getBoundingClientRect(); return r ? Math.min(r.width, r.height) : 0; })));
      const row = {
        case: name, goal: c.goal, viewport: `${w}x${h}`, status, first_model_ms: firstModelMs,
        timeline_steps: steps.length, timeline: steps,
        goal_object_id: goalId ?? null,
        construction_only_at_conclusion: c.goal === 'angle'
          ? (last?.angle_construction_ids?.length === 1 && before.every((s) => s.angle_construction_ids.length === 0))
          : c.goal === 'altitude'
            ? (last?.altitude_construction_ids?.length === 1 && before.every((s) => s.altitude_construction_ids.length === 0))
            : (Boolean(goalId) && has(last?.rendered_ids, goalId) && !has(steps[0]?.rendered_ids, goalId)),
        camera: cam, pan_and_auxiliary: panAux, selection: sel,
        answer_text_on_page: leaked, cos2_text_on_page: /cos²/.test(text),
        horizontal_overflow_px: overflow, step_button_min_px: minTarget, page_errors: errors,
      };
      row.pass = status === 'SERVED' && steps.length >= 2 && row.construction_only_at_conclusion !== false
        && cam?.orbit_changes_camera && cam?.zoom_changes_camera && panAux?.pan_changes_camera && leaked.length === 0 && !row.cos2_text_on_page
        && overflow <= 0 && errors.length === 0 && (w > 500 || minTarget >= 40) && (!goalId || sel?.selects === true);
      rows.push(row);
      perf.push({ case: name, viewport: row.viewport, first_model_ms: firstModelMs,
        step_ms: steps.map((s) => s.next_ms).filter((x) => x !== undefined), orbit_ms: cam?.orbit_ms ?? null,
        heap_mb: await page.evaluate(() => (performance.memory?.usedJSHeapSize ?? 0) / 2 ** 20) });
      console.log(JSON.stringify({ case: name, viewport: row.viewport, pass: row.pass, steps: steps.length, ms: firstModelMs }));
      await ctx.close();
    }
  }

  // Resource cleanup: switch between two problems repeatedly in ONE page; heap after forced GC must not keep growing.
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const page = await ctx.newPage();
  await page.goto(ORIGIN, { waitUntil: 'networkidle' });
  // A guest has ONE trial simulation (product policy). The switch loop signs up a synthetic account in the measured
  // app's own throwaway SQLite file (no real person, `example.invalid`, a random password generated per run), then reloads.
  const signup = await page.evaluate(async () => (await fetch('/api/auth/register', { method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: `e2e-${Date.now()}@example.invalid`, displayName: 'E2E', password: crypto.randomUUID() }) })).status);
  await page.reload({ waitUntil: 'networkidle' });
  cleanup.synthetic_signup_status = signup;
  const heap = async () => { await page.evaluate(() => window.gc && window.gc()); await frames(page, 4);
    return page.evaluate(() => (performance.memory?.usedJSHeapSize ?? 0) / 2 ** 20); };
  const series = [];
  cleanup.series = series;
  for (let i = 0; i < 6; i++) {   // 12 analyses: the 16th of a fresh account is refused by the product's rate limit
    for (const k of ['section_pyramid', 'intersection_SAB_SCD']) {
      try {
        await load(page, CASES[k].text);
      } catch (e) {
        cleanup.error = { cycle: i, case: k, message: String(e.message).slice(0, 160),
          page_text: (await page.evaluate(() => document.body.innerText)).slice(0, 300) };
        throw e;
      }
      const steps = await walkTimeline(page);
      series.push({ cycle: i, case: k, heap_mb: await heap(), canvases: await page.locator('canvas').count(), steps: steps.length,
                    rendered: (await page.evaluate(() => window.__geo3d_rendered_object_ids ?? [])).length });
    }
  }
  // Isolated Scene3D check (no new analysis, so no history growth): walk the same timeline 15 times.
  const walkHeap = [await heap()];
  for (let i = 0; i < 15; i++) { await walkTimeline(page); if (i % 5 === 4) walkHeap.push(await heap()); }
  cleanup.timeline_walk_heap_mb = walkHeap;
  cleanup.timeline_walk_growth_mb = walkHeap.at(-1) - walkHeap[0];
  const firstHalf = series.slice(2, 6).map((s) => s.heap_mb), secondHalf = series.slice(-4).map((s) => s.heap_mb);
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  Object.assign(cleanup, { method: '6 cycles × 2 problems in one signed-in page (each analysis is kept in the learner history), forced GC (--expose-gc) before each reading; plus 15 timeline walks of one problem with no new analysis', series,
    heap_mean_early_mb: mean(firstHalf), heap_mean_late_mb: mean(secondHalf), heap_growth_mb: mean(secondHalf) - mean(firstHalf),
    canvas_count_constant: new Set(series.map((s) => s.canvases)).size === 1 });
  await ctx.close();
} finally {
  const env = { browser: browser.version(), headless: true, backend: 'measured_app loopback, HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0' };
  writeFileSync(join(outDir, 'scene3d_browser_e2e.json'), JSON.stringify({ ...env, category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY',
    rows: rows.map(({ timeline, ...r }) => r), passed: rows.filter((r) => r.pass).length, total: rows.length }, null, 2) + '\n');
  writeFileSync(join(outDir, 'browser_construction_timeline.json'), JSON.stringify({ ...env,
    rule: 'the goal object (section polygon / intersection line / altitude / angle construction) is absent at the first step and present at the last; steps walked with the real ←/→ buttons',
    rows: rows.map((r) => ({ case: r.case, viewport: r.viewport, construction_only_at_conclusion: r.construction_only_at_conclusion,
      steps: r.timeline.map(({ rendered_ids, ...x }) => x) })) }, null, 2) + '\n');
  writeFileSync(join(outDir, 'browser_performance_profile.json'), JSON.stringify({ ...env,
    note: 'host desktop, headless; first_model_ms = send click → canvas with a timeline (includes local parse + solve + scene build); step_ms = click → 2 animation frames',
    rows: perf, physical_low_end: 'PHYSICAL_LOW_END_NOT_MEASURED' }, null, 2) + '\n');
  writeFileSync(join(outDir, 'resource_cleanup_audit.json'), JSON.stringify({ ...env, ...cleanup }, null, 2) + '\n');
  await browser.close(); server.close();
}
if (!rows.every((r) => r.pass)) process.exitCode = 1;
