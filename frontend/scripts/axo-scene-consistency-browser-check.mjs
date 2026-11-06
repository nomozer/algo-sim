// Offline browser E2E on a production build. Checks that (1) the construction flow carries no answer
// presentation and (2) statement / title / Scene3D / steps on screen always belong to the open record
// across sample routes, history, same-title problems, reload, A→B→A, rapid switching, playback and
// Back/Forward; plus responsive widths and REAL Chrome page zoom 110% (browser zoom preference, no DPR emulation).
// Usage: node scripts/axo-scene-consistency-browser-check.mjs --dist <dir> --out <fresh dir> [--headed]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import { tmpdir } from 'node:os';
import assert from 'node:assert/strict';

const arg = (key, fallback) => process.argv.includes(key) ? process.argv[process.argv.indexOf(key) + 1] : fallback;
const dist = resolve(arg('--dist', 'dist'));
const out = resolve(arg('--out'));
const headless = !process.argv.includes('--headed');
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const samples = JSON.parse(readFileSync('src/data/geometry-samples.json', 'utf8')).samples;
const sample = id => samples.find(s => s.id === id);

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
const report = { schema: 'axo-scene-consistency/1', dist, provider_calls: 0, checks: [], forbidden: [] };
const save = () => writeFileSync(join(out, 'receipt.json'), JSON.stringify(report, null, 2));
const guard = ctx => ctx.route('**/*', route => {
  if (new URL(route.request().url()).origin !== url) { report.forbidden.push(route.request().url()); return route.abort(); }
  return route.continue();
});

const browser = await chromium.launch({ channel: 'chrome', headless });
report.browser = browser.version();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
await guard(ctx);
let page = await ctx.newPage();
const pageErrors = []; page.on('pageerror', e => pageErrors.push(e.message));

const check = async (name, fn) => {
  const row = { name }; report.checks.push(row);
  try { row.evidence = await fn(); row.status = 'PASS'; }
  catch (e) { row.status = 'FAIL'; row.error = e.message.slice(0, 1500); await page.screenshot({ path: join(out, `failure-${report.checks.length}.png`) }).catch(() => {}); }
  save(); console.log(`${row.status} ${name}${row.error ? `: ${row.error}` : ''}`);
};
const idle = () => page.waitForFunction(() => (window.__geo3d_step_highlight_state?.pulse ?? 0) < .001, null, { timeout: 15000 }).then(() => page.waitForTimeout(150));
const steps = () => page.locator('#dock-steps-ul [data-step]').count();
const current = () => page.locator('#dock-steps-ul [aria-current="step"]').getAttribute('data-step').then(Number);
const toLast = async () => { const n = await steps(); while (await current() < n - 1) { await page.locator('#pa-next').click(); } await idle(); };
const store = (fn, a) => page.evaluate(([f, x]) => new Function('s', 'x', `return (${f})(s, x)`)(window.__ALGO_SIM_STORE__.getState(), x), [fn.toString(), a]);
const openRoute = async id => { await page.goto(`${url}/simulation/${id}`); await page.waitForSelector('#dock-steps-ul [data-step]'); await idle(); };
const loadEnv = async (env, sampleId, input) => {
  await store((s, x) => s.loadEnvelope(x[0], x[1] ?? undefined, x[2] ?? undefined), [env, sampleId ?? null, input ?? null]);
  await page.waitForSelector('#dock-steps-ul [data-step], .ws-unavailable-note, [data-unavailable]', { timeout: 15000 }).catch(() => {});
  await idle().catch(() => {});
};
const loadSample = id => loadEnv(sample(id).envelope, id);
// No answer presentation anywhere in the DOM (incl. hidden/aria text).
const ANSWER_MARKERS = ['dock-goal-reveal', 'dock-goal-conclusion', 'data-conclusion-id', 'KẾT LUẬN', 'Xem kết quả', 'Thu gọn kết quả'];
const assertNoAnswerSurface = async (answers = []) => {
  const html = await page.evaluate(() => document.documentElement.outerHTML);
  for (const m of ANSWER_MARKERS) assert.ok(!html.includes(m), `answer surface marker ${m}`);
  for (const a of answers) assert.ok(!html.includes(a), `answer ${a} in DOM`);
};
const consistency = () => page.evaluate(() => {
  const st = window.__ALGO_SIM_STORE__.getState();
  const env = st.active?.envelope;
  const ids = new Set(env?.scene3d?.objects.map(o => o.id) ?? []);
  // Render keys: `id__sub` (sub-entity), `kind:id` (companion), `id#<n>c…` (polygon carrier).
  const base = id => String(id).split('#')[0].split('__')[0].split(':').pop();
  const rendered = window.__geo3d_rendered_object_ids ?? [];
  return {
    activeSampleId: st.activeSampleId, activeHistoryId: st.activeHistoryId,
    statement: document.querySelector('#dock-prob-statement')?.innerText.replace(/\s+/g, ' ').trim() ?? '',
    title: document.querySelector('#top-prob-title')?.innerText.trim() ?? '',
    foreignRendered: rendered.filter(id => !ids.has(id) && !ids.has(base(id))),
    renderedCount: rendered.length,
    steps: document.querySelectorAll('#dock-steps-ul [data-step]').length,
    sceneObjects: [...ids],
  };
});
const assertConsistent = async (statementStart, { title = true } = {}) => {
  const c = await consistency();
  assert.ok(c.statement.startsWith(statementStart.slice(0, 50)), `statement mismatch: "${c.statement.slice(0, 70)}" vs "${statementStart.slice(0, 50)}"`);
  if (title) assert.ok(c.title && !/[a-z][A-Z]|_|Scene\b/u.test(c.title), `technical title: ${c.title}`);
  assert.deepEqual(c.foreignRendered, [], 'rendered objects from another scene');
  assert.ok(c.renderedCount > 0, 'nothing rendered');
  return c;
};
const plain = s => s.replace(/\s+/g, ' ').trim();
let checkRealZoom = null;

// Reuse this harness for the exact-oracle corpus without repeating the full viewer suite.
if (arg('--mathematical-corpus', null)) {
  const corpus = JSON.parse(readFileSync(resolve(arg('--mathematical-corpus')), 'utf8'));
  await page.route('**/api/health', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, hasKey: true }) }));
  for (const row of corpus) {
    await check(`mathematical authority ${row.id}: composer, attempt, history, reload, no answer surface`, async () => {
      await page.route('**/api/analyze', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify(row.response) }));
      await page.goto(`${url}/`); await page.waitForSelector('#home-problem-input');
      await page.locator('#home-problem-input').fill(row.input.problem_text);
      await page.waitForFunction(() => !document.querySelector('#btn-composer-send')?.hasAttribute('disabled'));
      await page.locator('#btn-composer-send').click();
      if (row.response.route_d.status === 'REFUSED') {
        await page.waitForFunction(() => !!window.__ALGO_SIM_STORE__.getState().unsupported);
        const state = await store(s => ({ unsupported: s.unsupported, active: s.active }));
        assert.equal(state.active, null, 'refusal retained another problem scene');
        assert.equal(state.unsupported.reason_code, row.response.envelope.reason_code);
        assert.equal(state.unsupported.failure_category, row.response.envelope.failure_category);
        await assertNoAnswerSurface();
        await page.unroute('**/api/analyze');
        return { status: 'REFUSED', code: state.unsupported.reason_code, category: state.unsupported.failure_category };
      }
      await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
      const record = await store(s => ({ id: s.activeHistoryId, statement: s.active.problemStatement,
        scene: JSON.stringify(s.active.envelope.scene3d), view: s.active.envelope.hybrid_preview }));
      assert.equal(record.statement, row.input.problem_text);
      assert.ok(record.view?.answers.length, 'missing backend answer binding');
      const verify = async () => {
        await page.waitForFunction(() => window.__geo3d_goal_completion?.status === 'reached');
        const state = await store(s => ({ id: s.activeHistoryId, statement: s.active.problemStatement,
          scene: JSON.stringify(s.active.envelope.scene3d), view: s.active.envelope.hybrid_preview }));
        assert.deepEqual(state, record, 'attempt/source/scene/evidence changed');
        assert.equal(await page.locator('#dock-goal-summary').count(), 0, 'certified goal still has warning');
        await assertNoAnswerSurface();
        assert.equal(await page.locator('[data-value-entity], [data-formula-entity]').count(), 0, 'internal result surfaced');
      };
      await verify(); await toLast(); await verify();
      await store((s, id) => s.reopenFromHistory(id), record.id); await idle(); await verify();
      await page.reload(); await page.waitForSelector('#dock-steps-ul [data-step]'); await idle(); await verify();
      if (row.id === 'right-prism') await page.screenshot({ path: join(out, 'right-prism-certified-no-answer.png') });
      await page.unroute('**/api/analyze');
      return { status: 'reached', attempt: record.id, answerBinding: record.view.answers };
    });
  }
  report.summary = { pass: report.checks.filter(c => c.status === 'PASS').length, fail: report.checks.filter(c => c.status === 'FAIL').length };
  save(); await browser.close(); server.close();
  console.log(JSON.stringify(report.summary));
  process.exit(report.summary.fail || report.forbidden.length ? 1 : 0);
}

if (!process.argv.includes('--interactions-only')) {
await page.goto(`${url}/library`);
await page.waitForFunction(() => !!window.__ALGO_SIM_STORE__);

for (const s of samples) {
  await check(`route ${s.id}: statement/title/scene consistent, no answer surface at first and final step`, async () => {
    await openRoute(s.id);
    const first = await assertConsistent(plain(s.envelope.description));
    await assertNoAnswerSurface();
    await toLast();
    const last = await assertConsistent(plain(s.envelope.description));
    await assertNoAnswerSurface();
    return { url: page.url(), title: first.title, steps: last.steps, renderedFirst: first.renderedCount, renderedLast: last.renderedCount };
  });
}

await check('given data and narration remain per step (cau-cat-mat-phang)', async () => {
  await openRoute('cau-cat-mat-phang');
  const per = [];
  const n = await steps();
  for (let i = 0; i < n; i++) {
    await page.locator(`#dock-steps-ul [data-step="${i}"]`).click(); await idle();
    const given = await page.locator('#dock-given-params').innerText();
    assert.match(given, /R = 5/); assert.match(given, /d\(I, \(P\)\) = 3/);
    per.push({ step: i, title: plain(await page.locator('#dock-steps-ul [aria-current="step"]').innerText()).slice(0, 90) });
    await assertNoAnswerSurface(['16π']);
  }
  await page.screenshot({ path: join(out, 'desktop-sphere-section-final.png') });
  return per;
});

await check('two problems with the same title keep separate statement and scene; history A → B → A', async () => {
  const a = { ...sample('cau-the-tich').envelope, title: 'Bài mặt cầu' };
  const b = { ...sample('cau-cat-mat-phang').envelope, title: 'Bài mặt cầu' };
  const ta = 'Đề A: mặt cầu tâm I đi qua điểm A, bán kính bằng độ dài IA.';
  const tb = 'Đề B: mặt cầu bán kính năm, mặt phẳng cách tâm một khoảng ba.';
  await loadEnv(a, null, ta); const idA = (await consistency()).activeHistoryId;
  await loadEnv(b, null, tb); const idB = (await consistency()).activeHistoryId;
  assert.notEqual(idA, idB);
  const seq = [];
  for (const [id, text, mustHave] of [[idA, ta, 'A'], [idB, tb, 'P'], [idA, ta, 'A']]) {
    await store((s, x) => s.reopenFromHistory(x), id);
    await page.waitForFunction(i => window.__ALGO_SIM_STORE__.getState().activeHistoryId === i, id); await idle();
    const c = await assertConsistent(text);
    assert.ok(c.sceneObjects.includes(mustHave), `scene of ${id} lacks ${mustHave}`);
    seq.push({ id, statement: c.statement.slice(0, 20), steps: c.steps });
  }
  return seq;
});

await check('legacy record without scene3d and a sample-like title gets an honest missing-data notice', async () => {
  const s = sample('cau-cat-mat-phang').envelope;
  const legacy = { ...s, config: { ...s.config, title: 'Bản ghi cũ tự gõ' } }; delete legacy.scene3d;
  await loadEnv(legacy, null, 'Đề cũ của học sinh, không phải bài mẫu.');
  await page.waitForFunction(() => document.body.innerText.includes('chưa có dữ liệu không gian 3D hợp lệ'), null, { timeout: 15000 });
  assert.equal(await page.locator('#dock-steps-ul [data-step]').count(), 0, 'sample steps shown for a legacy record');
  assert.equal(((await page.evaluate(() => window.__geo3d_rendered_object_ids)) ?? []).filter(i => i === 'C' || i === 'P').length, 0, 'sample scene rendered');
  await page.screenshot({ path: join(out, 'legacy-record-missing-data.png') });
  return { notice: true };
});

const statementSource = () => page.locator('#dock-prob-statement').getAttribute('data-statement-source');

// Phản hồi Hybrid /4 THẬT đã đóng băng của main (không dựng tay), phục vụ cho ô soạn đề qua `/api/analyze` giả, offline.
const hybridRow = JSON.parse(readFileSync('../docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-frontend-fixtures.json', 'utf8'))
  .fixtures.find((f) => f.response.route_d?.status === 'SERVED');
await check('real composer: two independent sends of the same statement ⇒ two attempts; a 502 then 200 retry ⇒ one attempt; reload keeps it', async () => {
  let analyzeCalls = 0; let failNext = false;
  await page.route('**/api/health', (r) => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, hasKey: true }) }));
  await page.route('**/api/analyze', (r) => {
    analyzeCalls += 1;
    if (failNext) { failNext = false; return r.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ detail: 'Bad Gateway' }) }); }
    return r.fulfill({ contentType: 'application/json', body: JSON.stringify(hybridRow.response) });
  });
  const records = () => page.evaluate(() => (Object.keys(localStorage).filter((k) => k.startsWith('algosim.history.v1:')).map((k) => JSON.parse(localStorage.getItem(k)))).map((x) => ({ id: x.id, input: x.originalInput })));
  const send = async () => {
    await page.goto(`${url}/`); await page.waitForSelector('#home-problem-input');
    await page.locator('#home-problem-input').fill(hybridRow.problem_text);
    await page.waitForFunction(() => !document.querySelector('#btn-composer-send')?.hasAttribute('disabled'));
    const before = analyzeCalls;
    await page.locator('#btn-composer-send').click();
    await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().view === 'workspace' && !!window.__ALGO_SIM_STORE__.getState().activeHistoryId, null, { timeout: 30000 });
    return { id: await page.evaluate(() => window.__ALGO_SIM_STORE__.getState().activeHistoryId), calls: analyzeCalls - before };
  };
  const startCount = (await records()).length;
  const a = await send();
  const b = await send();
  assert.notEqual(a.id, b.id, 'two sends merged into one attempt');
  assert.ok(/^a[0-9a-f]{32}$/u.test(a.id) && /^a[0-9a-f]{32}$/u.test(b.id), `attempt ids ${a.id} ${b.id}`);
  failNext = true;
  const c = await send();
  assert.equal(c.calls, 2, 'retry did not happen');
  const all = await records();
  assert.equal(all.length, startCount + 3, `expected 3 new attempts, got ${all.length - startCount}`);
  await page.reload(); await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
  assert.equal(await page.evaluate(() => window.__ALGO_SIM_STORE__.getState().activeHistoryId), c.id, 'reload changed the attempt');
  await assertConsistent(plain(hybridRow.problem_text));
  await page.goBack(); await page.waitForTimeout(400); await page.goForward();
  await page.waitForFunction((id) => window.__ALGO_SIM_STORE__.getState().activeHistoryId === id, c.id, { timeout: 15000 });
  await page.unroute('**/api/health'); await page.unroute('**/api/analyze');
  return { attempts: [a.id, b.id, c.id], retryCalls: c.calls, fixture: hybridRow.id };
});

for (const id of ['cau-cat-mat-phang', 'thiet-dien-chop', 'non-thiet-dien-truc']) {
  await check(`deep-frozen Scene3D survives every interaction (${id}): render, steps, play/replay, orbit, zoom, select, hide, isolate, restore, dock, switch, history`, async () => {
    const before = pageErrors.length;
    const envJson = await page.evaluate(([e, typed]) => {
      // Đóng băng sâu: mọi phép ghi vào dữ liệu cảnh có thẩm quyền sẽ ném TypeError (module ESM chạy strict mode).
      const freeze = (o) => { if (o && typeof o === 'object' && !Object.isFrozen(o)) { Object.freeze(o); for (const v of Object.values(o)) freeze(v); } return o; };
      const env = structuredClone(e); freeze(env.scene3d);
      window.__frozenEnv = env;
      window.__ALGO_SIM_STORE__.getState().loadEnvelope(env, undefined, typed);
      return JSON.stringify(env.scene3d);
    }, [sample(id).envelope, `Đề kiểm tra bất biến cảnh (${id}).`]);
    const recordId = (await consistency()).activeHistoryId;
    await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
    const n = await steps();
    for (let i = 0; i < n; i++) { await page.locator(`#dock-steps-ul [data-step="${i}"]`).click(); }
    await idle();
    await page.locator('#pa-play').click(); await page.waitForTimeout(600); await page.locator('#pa-play').click().catch(() => {});
    await page.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click(); await idle();
    await page.locator('#pa-play').click(); await page.waitForTimeout(400); // phát lại từ bước cuối
    await page.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click(); await idle();
    const c = await page.locator('.geo3d-canvas canvas').boundingBox();
    await page.mouse.move(c.x + c.width / 2, c.y + c.height / 2); await page.mouse.down();
    await page.mouse.move(c.x + c.width / 2 + 180, c.y + c.height / 2 - 60, { steps: 10 }); await page.mouse.up();
    await page.mouse.wheel(0, -240); await page.mouse.wheel(0, 240); await idle();
    await page.locator('[data-entity-chip]').first().click();
    for (const btn of ['#btn-card-hide', '#btn-restore-hidden-objects', '#btn-card-isolate', '#btn-restore-hidden-objects', '#btn-clear-pick']) {
      const b = page.locator(btn).first();
      if (await b.count() && await b.isVisible()) { await b.click(); await page.waitForTimeout(120); }
      else if (btn === '#btn-card-isolate' || btn === '#btn-card-hide') await page.locator('[data-entity-chip]').first().click().catch(() => {});
    }
    const collapse = page.locator('#btn-collapse-dock');
    if (await collapse.count() && await collapse.isVisible()) { await collapse.click(); await page.waitForTimeout(150); await page.locator('#btn-reopen-dock-capsule').click().catch(() => {}); }
    await loadSample('tru-thiet-dien-tron');
    await store((s, x) => s.reopenFromHistory(x), recordId); await idle();
    const after = await page.evaluate(() => JSON.stringify(window.__frozenEnv.scene3d));
    const errs = pageErrors.slice(before).filter((m) => /read.only|not extensible|Cannot assign|Cannot add property|Cannot delete/iu.test(m));
    assert.deepEqual(errs, [], `writes into frozen Scene3D: ${errs.join(' | ')}`);
    assert.equal(after, envJson, 'Scene3D content changed');
    assert.equal((await consistency()).activeHistoryId, recordId, 'history reopen changed the record');
    return { steps: n, pageErrorsDuringCheck: pageErrors.slice(before).length };
  });
}

await check('the viewer never mutates the opened Scene3D; reopening keeps the same record (no duplicate)', async () => {
  const r = await page.evaluate(async e => {
    const s = window.__ALGO_SIM_STORE__.getState();
    const before = JSON.stringify(e.scene3d);
    s.loadEnvelope(e, undefined, 'Đề kiểm tra dữ liệu cảnh không bị trình xem sửa.');
    const id = window.__ALGO_SIM_STORE__.getState().activeHistoryId;
    await new Promise(res => setTimeout(res, 1500)); // let the viewer render several frames
    const mutated = JSON.stringify(e.scene3d) !== before;
    const count = (Object.keys(localStorage).filter((k) => k.startsWith('algosim.history.v1:')).map((k) => JSON.parse(localStorage.getItem(k)))).length;
    window.__ALGO_SIM_STORE__.getState().reopenFromHistory(id);
    return { id, mutated, sameAfterReopen: window.__ALGO_SIM_STORE__.getState().activeHistoryId === id,
      countBefore: count, countAfter: (Object.keys(localStorage).filter((k) => k.startsWith('algosim.history.v1:')).map((k) => JSON.parse(localStorage.getItem(k)))).length };
  }, sample('cau-the-tich').envelope);
  assert.equal(r.mutated, false, 'viewer wrote into the envelope Scene3D');
  assert.equal(r.sameAfterReopen, true, 'reopen produced a different record');
  assert.equal(r.countAfter, r.countBefore, 'reopen duplicated the record');
  return r;
});

await check('submission sharing a sample program: own record and URL, statement survives reload, sample untouched', async () => {
  const typed = 'Đề học sinh: mặt cầu bán kính năm, mặt phẳng cách tâm ba; dựng đường tròn giao.';
  await loadEnv(sample('cau-cat-mat-phang').envelope, null, typed);
  const c = await consistency();
  assert.equal(c.activeSampleId, null, 'submission presented as a sample');
  assert.ok(c.activeHistoryId.startsWith('s'), `submission key ${c.activeHistoryId}`);
  await page.waitForFunction(id => location.pathname === `/simulation/${id}`, c.activeHistoryId);
  assert.equal(await statementSource(), 'learner');
  await page.reload(); await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
  const after = await assertConsistent(typed);
  assert.equal(after.activeHistoryId, c.activeHistoryId);
  assert.equal(await statementSource(), 'learner');
  await openRoute('cau-cat-mat-phang');
  await assertConsistent(plain(sample('cau-cat-mat-phang').envelope.description));
  assert.equal(await statementSource(), 'catalog');
  const rec = await page.evaluate(id => (Object.keys(localStorage).filter((k) => k.startsWith('algosim.history.v1:')).map((k) => JSON.parse(localStorage.getItem(k)))).find(x => x.id === id), c.activeHistoryId);
  assert.equal(rec?.originalInput, typed, 'submission record overwritten by sample opening');
  return { submission: c.activeHistoryId, url: `/simulation/${c.activeHistoryId}` };
});

await check('two statements compiling to the same program keep two records; selection does not cross records', async () => {
  const t1 = 'Đề một: mặt cầu tâm I qua A với IA bằng ba.';
  const t2 = 'Đề hai: cùng hình nhưng viết khác, tâm I, điểm A trên mặt cầu, IA = 3.';
  await loadEnv(sample('cau-the-tich').envelope, null, t1); const id1 = (await consistency()).activeHistoryId;
  await page.locator('[data-entity-chip]').first().click();
  const selected = await page.evaluate(() => window.__geo3d_selected_id);
  await loadEnv(sample('cau-the-tich').envelope, null, t2); const id2 = (await consistency()).activeHistoryId;
  assert.notEqual(id1, id2);
  assert.notEqual(await page.evaluate(() => window.__geo3d_selected_id ?? null), selected, 'selection carried into another record');
  await store((s, x) => s.reopenFromHistory(x), id1); await idle();
  await assertConsistent(t1);
  await store((s, x) => s.reopenFromHistory(x), id2); await idle();
  await assertConsistent(t2);
  return { id1, id2, selectedInFirst: selected };
});

await check('legacy record without a stored statement says so (no model description as statement)', async () => {
  const s = sample('cau-the-tich').envelope;
  const env = { ...s, config: { ...s.config, title: 'Bản ghi cũ không có đề' }, description: 'Lời mô tả kỹ thuật của hệ thống.' };
  await loadEnv(env, null, null);
  assert.equal(await statementSource(), 'missing');
  const text = plain(await page.locator('#dock-prob-statement').innerText());
  assert.ok(text.startsWith('Bản ghi này không lưu đề gốc.'), text);
  return { text };
});

await check('reload (F5) restores the same record, statement and step', async () => {
  await openRoute('tru-thiet-dien-tron');
  await page.locator('#dock-steps-ul [data-step="1"]').click(); await idle();
  const before = await assertConsistent(plain(sample('tru-thiet-dien-tron').envelope.description));
  await page.reload(); await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
  const after = await assertConsistent(plain(sample('tru-thiet-dien-tron').envelope.description));
  assert.equal(await current(), 1);
  assert.equal(after.activeSampleId, before.activeSampleId);
  return { step: 1, url: page.url() };
});

await check('rapid switching, switching during playback, Back/Forward keep record and scene together', async () => {
  await openRoute('tru-thiet-dien-tron');
  await page.locator('#pa-play').click();
  const seq = ['cau-the-tich', 'thiet-dien-chop', 'non-thiet-dien-truc', 'cau-cat-mat-phang', 'cau-the-tich', 'mat-cheo-sac'];
  await store((s, list) => { for (const [e, i] of list) s.loadEnvelope(e, i); }, seq.map(id => [sample(id).envelope, id]));
  await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'mat-cheo-sac');
  await page.waitForSelector('#dock-steps-ul [data-step]'); await idle();
  await assertConsistent(plain(sample('mat-cheo-sac').envelope.description));
  for (let i = 0; i < 6; i++) {
    const id = i % 2 ? 'cau-cat-mat-phang' : 'non-thiet-dien-truc';
    await page.locator('#pa-play').click().catch(() => {});
    await loadSample(id);
    await assertConsistent(plain(sample(id).envelope.description));
  }
  await page.goBack(); await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'non-thiet-dien-truc'); await idle();
  await assertConsistent(plain(sample('non-thiet-dien-truc').envelope.description));
  await page.goForward(); await page.waitForFunction(() => window.__ALGO_SIM_STORE__.getState().activeSampleId === 'cau-cat-mat-phang'); await idle();
  await assertConsistent(plain(sample('cau-cat-mat-phang').envelope.description));
  await assertNoAnswerSurface(['16π']);
  return { canvases: await page.evaluate(() => document.querySelectorAll('canvas').length) };
});

for (const id of ['thiet-dien-chop', 'mat-cheo-sac', 'tru-truc-xien', 'non-thiet-dien-truc', 'cau-cat-mat-phang']) {
  await check(`capture ${id}: first, middle, last step and two extra camera angles`, async () => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openRoute(id);
    const n = await steps();
    const shots = [];
    for (const [tag, i] of [['first', 0], ['middle', Math.floor((n - 1) / 2)], ['last', n - 1]]) {
      await page.locator(`#dock-steps-ul [data-step="${i}"]`).click(); await idle();
      const f = `scene-${id}-${tag}.png`; await page.screenshot({ path: join(out, f) }); shots.push(f);
    }
    const c = await page.locator('.geo3d-canvas canvas').boundingBox();
    for (const [k, dx, dy] of [['angle-a', 240, 0], ['angle-b', -160, -150]]) {
      await page.mouse.move(c.x + c.width / 2, c.y + c.height / 2); await page.mouse.down();
      await page.mouse.move(c.x + c.width / 2 + dx, c.y + c.height / 2 + dy, { steps: 12 }); await page.mouse.up(); await idle();
      const f = `scene-${id}-last-${k}.png`; await page.screenshot({ path: join(out, f) }); shots.push(f);
    }
    await assertNoAnswerSurface();
    return { steps: n, shots, edges: await page.evaluate(() => ({ visible: (window.__geo3d_visible_edge_ids ?? []).length, hidden: (window.__geo3d_hidden_edge_ids ?? []).length })) };
  });
}

for (const width of [360, 390, 430, 768, 820, 1024, 1280, 1440]) {
  await check(`responsive ${width}px: final step layout, no answer surface`, async () => {
    await page.setViewportSize({ width, height: width < 500 ? 844 : width === 1280 ? 800 : 900 });
    for (const id of ['thiet-dien-chop', 'cau-cat-mat-phang']) {
      await openRoute(id); await toLast();
      await assertNoAnswerSurface();
    }
    const box = await page.evaluate(() => {
      const c = document.querySelector('.geo3d-canvas canvas')?.getBoundingClientRect();
      return { docWidth: document.documentElement.scrollWidth, vw: innerWidth, canvasH: c?.height ?? 0 };
    });
    assert.ok(box.docWidth <= box.vw + 1, 'horizontal document overflow');
    assert.ok(box.canvasH > (width < 500 ? 250 : 350), '3D canvas too short');
    await page.screenshot({ path: join(out, `responsive-${width}-final.png`) });
    return box;
  });
}

checkRealZoom = async () => {
await browser.close();
await check('REAL Chrome page zoom 110% (default_zoom_level preference, no DPR emulation)', async () => {
  // Chrome zoom level z ↔ factor 1.2^z; 110% ⇒ z = ln 1.1 / ln 1.2.
  const profile = mkdtempSync(join(tmpdir(), 'axo-zoom-'));
  mkdirSync(join(profile, 'Default'), { recursive: true });
  writeFileSync(join(profile, 'Default', 'Preferences'), JSON.stringify({ partition: { default_zoom_level: { x: Math.log(1.1) / Math.log(1.2) } } }));
  const zctx = await chromium.launchPersistentContext(profile, { channel: 'chrome', headless, viewport: null, args: ['--window-size=1440,960'] });
  try {
    await guard(zctx);
    const zp = zctx.pages()[0] ?? await zctx.newPage();
    await zp.goto(`${url}/simulation/cau-cat-mat-phang`); await zp.waitForSelector('#dock-steps-ul [data-step]');
    const n = await zp.locator('#dock-steps-ul [data-step]').count();
    await zp.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click(); await zp.waitForTimeout(600);
    const m = await zp.evaluate(() => {
      const right = s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().right) : null; };
      return { dpr: devicePixelRatio, innerWidth, outerWidth, docWidth: document.documentElement.scrollWidth,
        dockRight: right('#ws-dock'), statementRight: right('#dock-prob-statement'), changeButtonRight: right('#btn-header-change-prob'),
        canvasRight: right('.geo3d-canvas canvas'), html: document.documentElement.outerHTML.includes('dock-goal-reveal') };
    });
    assert.ok(Math.abs(m.dpr - 1.1) < 0.011, `browser zoom not applied (dpr ${m.dpr})`);
    assert.ok(m.docWidth <= m.innerWidth + 1, 'horizontal overflow at 110%');
    for (const k of ['dockRight', 'statementRight', 'changeButtonRight', 'canvasRight']) assert.ok(m[k] !== null && m[k] <= m.innerWidth + 1, `${k} ${m[k]} beyond viewport ${m.innerWidth}`);
    assert.equal(m.html, false);
    // Playwright screenshots under browser zoom capture the window at device size without the zoom factor,
    // so this image is CROPPED on the right; the rects above are the layout evidence.
    await zp.screenshot({ path: join(out, 'real-zoom-110-final-cropped-capture.png') });
    return m;
  } finally { await zctx.close(); rmSync(profile, { recursive: true, force: true }); }
});
};

}
for (const id of ['thiet-dien-chop', 'non-thiet-dien-truc', 'cau-cat-mat-phang']) {
  await check(`starting a drag over an object does not rebuild the scene (${id}): 0 GPU buffers/programs deleted`, async () => {
    // Count real GPU lifecycle, including hover before drag; React commits alone prove neither allocation nor disposal.
    const dp = await ctx.newPage();
    try {
      await dp.addInitScript(() => {
        window.__gl = { c: 0, d: 0, contexts: 0 };
        window.__interactionLongTasks = [];
        new PerformanceObserver(l => { for (const e of l.getEntries()) window.__interactionLongTasks.push(e.duration); })
          .observe({ type: 'longtask', buffered: false });
        const gc = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function (...a) {
          const g = gc.apply(this, a);
          if (g && /webgl/.test(String(a[0])) && !g.__counted) {
            g.__counted = true;
            window.__gl.contexts++;
            for (const [fn, k] of [['createBuffer', 'c'], ['createProgram', 'c'], ['deleteBuffer', 'd'], ['deleteProgram', 'd']]) {
              const o = g[fn].bind(g); g[fn] = (...x) => { window.__gl[k] += 1; return o(...x); };
            }
          }
          return g;
        };
      });
      await dp.goto(`${url}/simulation/${id}`); await dp.waitForSelector('#dock-steps-ul [data-step]');
      const n = await dp.locator('#dock-steps-ul [data-step]').count();
      await dp.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click();
      await dp.waitForFunction(() => (window.__geo3d_step_highlight_state?.pulse ?? 0) < .001, null, { timeout: 15000 });
      const b = await dp.locator('.geo3d-canvas canvas').boundingBox();
      const rows = [];
      const measure = async (phase, action) => {
        await dp.evaluate(() => { window.__gl.c = 0; window.__gl.d = 0; window.__interactionLongTasks = []; });
        await action(); await dp.waitForTimeout(180);
        const row = await dp.evaluate(() => ({ ...window.__gl, hovered: window.__geo3d_hovered_object_id,
          builds: window.__geo3d_geometry_build_count ?? null, longTasks: [...window.__interactionLongTasks] }));
        rows.push({ phase, ...row }); return row;
      };
      // Discover two actually hittable objects in this projection. No label/fixture-specific hit coordinates.
      const hits = new Map();
      for (const fy of [.5, .4, .6, .3, .7]) {
        for (const fx of [.5, .4, .6, .3, .7]) {
          await dp.mouse.move(b.x + b.width * fx, b.y + b.height * fy); await dp.waitForTimeout(35);
          const h = await dp.evaluate(() => window.__geo3d_hovered_object_id);
          if (h && !hits.has(h)) hits.set(h, { x: b.x + b.width * fx, y: b.y + b.height * fy });
          if (hits.size >= 2) break;
        }
        if (hits.size >= 2) break;
      }
      assert.ok(hits.size >= 2, 'two distinct hover targets required');
      const [a, other] = [...hits.values()];
      await dp.mouse.move(2, 2); await dp.waitForTimeout(200);
      await measure('pointer-enter', () => dp.mouse.move(a.x, a.y));
      await measure('hover-A-to-B', () => dp.mouse.move(other.x, other.y));
      await measure('pointer-leave', () => dp.mouse.move(2, 2));
      await dp.mouse.move(a.x, a.y); await dp.waitForTimeout(180);
      await measure('click-select', () => dp.mouse.click(a.x, a.y));
      await measure('start-drag-hovered', () => dp.mouse.down());
      await measure('drag', async () => { for (let i = 1; i <= 20; i++) await dp.mouse.move(a.x + 4 * i, a.y); });
      await measure('release', () => dp.mouse.up());
      await measure('step', () => dp.locator('#dock-steps-ul [data-step="0"]').click());
      await measure('dock-collapse', () => dp.locator('#btn-collapse-dock').click());
      await dp.locator('#btn-reopen-dock-capsule').click();
      const hoverRows = rows.filter(r => ['pointer-enter', 'hover-A-to-B', 'pointer-leave'].includes(r.phase));
      assert.ok(hoverRows.every(r => r.c === 0 && r.d === 0), `hover allocated/disposed GPU objects: ${JSON.stringify(hoverRows)}`);
      assert.ok(hoverRows.every(r => r.contexts === 1), 'extra WebGL context');
      if (hoverRows.every(r => r.builds !== null)) assert.equal(new Set(hoverRows.map(r => r.builds)).size, 1, 'hover rebuilt geometry');
      assert.ok(rows.filter(r => ['start-drag-hovered', 'drag', 'release', 'dock-collapse'].includes(r.phase)).every(r => r.d === 0), 'drag/dock disposed GPU resources');
      return rows;
    } finally { await dp.close(); }
  });
}

if (checkRealZoom) await checkRealZoom();
report.pageErrors = pageErrors;
report.summary = { pass: report.checks.filter(c => c.status === 'PASS').length, fail: report.checks.filter(c => c.status === 'FAIL').length };
save();
await browser.close(); server.close();
console.log(JSON.stringify(report.summary));
if (report.summary.fail || report.forbidden.length) process.exitCode = 1;
