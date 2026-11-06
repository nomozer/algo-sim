// Offline two-tab browser E2E on a production build: two REAL Chrome tabs of one profile (same origin, shared
// localStorage), each driving the real composer (`#home-problem-input` → `#btn-composer-send` → `/api/analyze`).
// `/api/analyze` is answered from main's frozen Hybrid /4 fixtures (no provider call); every request's
// `Idempotency-Key` is recorded. Invariants checked after every scenario: no new record lost, statement and scene of
// each tab belong to its own record, no UI state leaks between attempts, one attempt per send (retry included),
// stored envelopes equal the served ones (no mutation), and a tab never shows a record that storage no longer holds.
// Usage: node scripts/axo-two-tab-browser-check.mjs --dist <dir> --out <fresh dir> [--headed] [--race-rounds N]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import assert from 'node:assert/strict';

const arg = (key, fallback) => process.argv.includes(key) ? process.argv[process.argv.indexOf(key) + 1] : fallback;
const dist = resolve(arg('--dist', 'dist'));
const out = resolve(arg('--out'));
const headless = !process.argv.includes('--headed');
const raceRounds = Number(arg('--race-rounds', '8'));   // keep the run under HISTORY_MAX_ITEMS (30): no eviction
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });

const HISTORY_PREFIX = 'algosim.history.v1:';   // one localStorage key per record
const fixtures = JSON.parse(readFileSync('../docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-frontend-fixtures.json', 'utf8'))
  .fixtures.filter((f) => f.response.route_d?.status === 'SERVED');
const byText = new Map(fixtures.map((f) => [f.problem_text.trim(), f]));
assert.ok(byText.size >= 3, `need ≥3 distinct served fixtures, got ${byText.size}`);
const [F1, F2, F3] = [...byText.values()];

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const analyzeLog = [];        // { key, text, tab, status }
let failNextFor = null;       // text whose next request answers 502 once
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname === '/api/analyze' && req.method === 'POST') {
    let raw = ''; req.on('data', (c) => { raw += c; }); req.on('end', () => {
      const text = JSON.parse(raw).input.content.trim();
      const row = { key: req.headers['idempotency-key'] ?? null, text: text.slice(0, 40), tab: req.headers['x-test-tab'] ?? null };
      analyzeLog.push(row);
      res.setHeader('Content-Type', 'application/json');
      if (failNextFor === text) { failNextFor = null; row.status = 502; res.statusCode = 502; res.end(JSON.stringify({ detail: 'Bad Gateway' })); return; }
      const f = byText.get(text);
      row.status = f ? 200 : 400;
      res.statusCode = row.status;
      res.end(JSON.stringify(f ? f.response : { error: 'unknown fixture' }));
    });
    return;
  }
  if (pathname.startsWith('/api/')) {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(pathname === '/api/health' ? { ok: true, hasKey: true } : { user: null }));
    return;
  }
  const file = join(dist, pathname.includes('.') ? pathname : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const report = { schema: 'axo-two-tab/1', dist, provider_calls: 0, fixtures: [F1.id, F2.id, F3.id], checks: [], forbidden: [] };
const save = () => writeFileSync(join(out, 'receipt.json'), JSON.stringify({ ...report, analyzeLog }, null, 2));

const browser = await chromium.launch({ channel: 'chrome', headless });
report.browser = browser.version();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 1 });
await ctx.route('**/*', (route) => {
  if (new URL(route.request().url()).origin !== url) { report.forbidden.push(route.request().url()); return route.abort(); }
  return route.continue();
});
const pageErrors = [];
const openTab = async (name) => {
  const p = await ctx.newPage();
  p.on('pageerror', (e) => pageErrors.push(`${name}: ${e.message}`));
  await p.route('**/api/analyze', (r) => r.continue({ headers: { ...r.request().headers(), 'x-test-tab': name } }));
  await p.goto(`${url}/`);
  await p.waitForFunction(() => !!window.__ALGO_SIM_STORE__);
  return p;
};
const A = await openTab('A');
const B = await openTab('B');

const check = async (name, fn) => {
  const row = { name }; report.checks.push(row);
  const errs = pageErrors.length;
  try {
    row.evidence = await fn();
    assert.deepEqual(pageErrors.slice(errs), [], 'page errors');
    await assertGlobalInvariants();
    row.status = 'PASS';
  } catch (e) {
    row.status = 'FAIL'; row.error = e.message.slice(0, 1500);
    for (const [n, p] of [['A', A], ['B', B]]) await p.screenshot({ path: join(out, `failure-${report.checks.length}-${n}.png`) }).catch(() => {});
  }
  save(); console.log(`${row.status} ${name}${row.error ? `: ${row.error}` : ''}`);
};

const st = (p) => p.evaluate(() => {
  const s = window.__ALGO_SIM_STORE__.getState();
  const env = s.active?.envelope;
  const ids = new Set(env?.scene3d?.objects.map((o) => o.id) ?? []);
  const base = (id) => String(id).split('#')[0].split('__')[0].split(':').pop();
  const rendered = window.__geo3d_rendered_object_ids ?? [];
  return {
    view: s.view, activeHistoryId: s.activeHistoryId,
    statement: document.querySelector('#dock-prob-statement')?.innerText.replace(/\s+/g, ' ').trim() ?? '',
    foreignRendered: rendered.filter((id) => !ids.has(id) && !ids.has(base(id))), renderedCount: rendered.length,
    currentStep: Number(document.querySelector('#dock-steps-ul [aria-current="step"]')?.getAttribute('data-step') ?? -1),
    playing: !!s.playing,
  };
});
const records = (p) => p.evaluate((pre) => Object.keys(localStorage).filter((k) => k.startsWith(pre)).sort().map((k) => JSON.parse(localStorage.getItem(k))), HISTORY_PREFIX);
const idle = (p) => p.waitForFunction(() => (window.__geo3d_step_highlight_state?.pulse ?? 0) < .001, null, { timeout: 15000 });
const plain = (s) => s.replace(/\s+/g, ' ').trim();

/** Real composer send; resolves when the tab shows the new attempt. */
const send = async (p, f) => {
  if (!(await p.locator('#home-problem-input').count())) { await p.goto(`${url}/`); }
  await p.waitForSelector('#home-problem-input');
  const before = await p.evaluate(() => window.__ALGO_SIM_STORE__.getState().activeHistoryId);
  await p.locator('#home-problem-input').fill(f.problem_text);
  await p.waitForFunction(() => !document.querySelector('#btn-composer-send')?.hasAttribute('disabled'));
  await p.locator('#btn-composer-send').click();
  await p.waitForFunction((b) => { const s = window.__ALGO_SIM_STORE__.getState(); return s.view === 'workspace' && s.activeHistoryId && s.activeHistoryId !== b; }, before, { timeout: 30000 });
  await p.waitForSelector('#dock-steps-ul [data-step]');
  const [id, env] = await p.evaluate(() => { const s = window.__ALGO_SIM_STORE__.getState(); return [s.activeHistoryId, JSON.stringify(s.active.envelope)]; });
  const parsed = JSON.parse(env);
  if (!clientEnv.has(f.id)) clientEnv.set(f.id, parsed);
  created.set(id, { f, scene: sceneOf(parsed) });
  return id;
};

/** Every attempt this run created: its fixture and the scene the tab showed when it was created. */
const created = new Map();   // id → { f, scene }
const clientEnv = new Map(); // fixture id → envelope as the client adapted it (docPhanHoiPhanTich), from a real send
const sceneOf = (env) => JSON.stringify(env?.scene3d ?? null, (k, v) => (k.startsWith('_') ? undefined : v));
const assertOwn = async (p, id) => {
  const s = await st(p);
  const { f } = created.get(id);
  assert.equal(s.activeHistoryId, id, 'tab shows another attempt');
  assert.ok(s.statement.startsWith(plain(f.problem_text).slice(0, 40)), `statement of another attempt: "${s.statement.slice(0, 60)}"`);
  assert.deepEqual(s.foreignRendered, [], 'objects of another scene rendered');
  assert.ok(s.renderedCount > 0, 'nothing rendered');
  return s;
};
const rawOf = (p) => records(p).then((r) => JSON.stringify(r));
async function assertGlobalInvariants() {
  // localStorage reaches the other renderer asynchronously: first wait until both tabs see the same bytes (bounded
  // poll on a condition, not a fixed sleep). Only a record missing AFTER convergence is lost.
  const t0 = Date.now();
  while ((await rawOf(A)) !== (await rawOf(B))) {
    assert.ok(Date.now() - t0 < 5000, 'tabs never converged on one history value');
    await A.waitForTimeout(25);
  }
  for (const p of [A, B]) {
    const recs = await records(p);
    assert.ok(recs.length < 30, `history reached its cap (${recs.length}); eviction would mask a lost record`);
    const ids = new Set(recs.map((r) => r.id));
    for (const [id, { f, scene }] of created) {
      assert.ok(ids.has(id), `record ${id} lost (seen from a tab)`);
      const r = recs.find((x) => x.id === id);
      assert.equal(plain(r.originalInput ?? ''), plain(f.problem_text), `record ${id} holds another statement`);
      assert.equal(sceneOf(r.envelope), scene, `record ${id} holds another/mutated scene`);
    }
    const s = await st(p);
    if (s.activeHistoryId) assert.ok(ids.has(s.activeHistoryId), 'tab shows a record storage no longer holds');
  }
  const keys = analyzeLog.filter((r) => r.status === 200).map((r) => r.key);
  assert.ok(keys.every((k) => /^a[0-9a-f]{32}$/u.test(k ?? '')), 'a served request without an attempt Idempotency-Key');
  assert.equal(new Set(keys).size, keys.length, 'one Idempotency-Key served twice (attempt duplicated)');
}

await check('1. A and B send two different problems at the same time', async () => {
  const [a, b] = await Promise.all([send(A, F1), send(B, F2)]);
 
  await assertOwn(A, a); await assertOwn(B, b);
  return { a, b };
});

await check('2. A and B send the same problem at the same time ⇒ two independent attempts', async () => {
  const [a, b] = await Promise.all([send(A, F3), send(B, F3)]);
  assert.notEqual(a, b);
 
  await assertOwn(A, a); await assertOwn(B, b);
  return { a, b };
});

await check('3. A saves history while B is reading and touching history (persistence race, repeated)', async () => {
  // B steps through its scene (each step = historyStore.touch: read-modify-write of the whole key) while A creates
  // attempts through the real composer. A lost update would drop A's record or B's cursor.
  const steps = await B.locator('#dock-steps-ul [data-step]').count();
  const bId = (await st(B)).activeHistoryId;
  const rounds = [];
  for (let i = 0; i < Math.min(raceRounds, 6); i++) {
    const stepper = (async () => { for (let k = 0; k < 8; k++) { await B.locator(`#dock-steps-ul [data-step="${k % steps}"]`).click(); } })();
    const [a] = await Promise.all([send(A, [F1, F2, F3][i % 3]), stepper]);
   
    rounds.push(a);
  }
  // Direct stress of the same persistence path (no UI): both tabs record/touch in the same instant.
  let direct = 0;
  for (let i = 0; i < raceRounds; i++) {
    // the store action the composer calls after a served response (`loadEnvelope(env, undefined, text, attemptId)`)
    const make = async (p, f) => {
      const id = await p.evaluate(([env, text]) => {
        const nid = 'a' + [...crypto.getRandomValues(new Uint8Array(16))].map((x) => x.toString(16).padStart(2, '0')).join('');
        window.__ALGO_SIM_STORE__.getState().loadEnvelope(env, undefined, text, nid);
        return nid;
      }, [clientEnv.get(f.id), f.problem_text]);
      created.set(id, { f, scene: sceneOf(clientEnv.get(f.id)) });
    };
    await Promise.all([make(A, F1), make(B, F2)]); direct += 2;
  }
  await B.waitForTimeout(0);
  const bRec = (await records(A)).find((r) => r.id === bId);
  return { uiRounds: rounds.length, directRecords: direct, bCursorSeenByA: bRec?.lastCursor ?? null };
});

await check('4. B reloads after A updated ⇒ B keeps its own attempt and sees A\'s records', async () => {
  const a = await send(A, F2);
  const bId = (await st(B)).activeHistoryId;
  await B.reload(); await B.waitForSelector('#dock-steps-ul [data-step]'); await idle(B);
  await assertOwn(B, bId);
  const seen = (await records(B)).map((x) => x.id);
  assert.ok(seen.includes(a), 'B does not see A\'s new record after reload');
  return { a, bId };
});

await check('5. A and B navigate and reopen different records, Back/Forward per tab', async () => {
  const ids = [...created.keys()];
  const [ra, rb] = [ids[0], ids[1]];
  for (const [p, id] of [[A, ra], [B, rb]]) {
    await p.evaluate((x) => window.__ALGO_SIM_STORE__.getState().reopenFromHistory(x), id);
    await p.waitForFunction((x) => window.__ALGO_SIM_STORE__.getState().activeHistoryId === x, id);
  }
  await assertOwn(A, ra); await assertOwn(B, rb);
  await A.goto(`${url}/library`); await A.goBack();
  await A.waitForFunction((x) => window.__ALGO_SIM_STORE__.getState().activeHistoryId === x, ra, { timeout: 15000 });
  await A.waitForSelector('#dock-steps-ul [data-step]'); await idle(A);
  await assertOwn(A, ra); await assertOwn(B, rb);
  return { ra, rb };
});

await check('6. A and B operate Scene3D, camera and steps independently', async () => {
  const drag = async (p, dx) => {
    const c = await p.locator('.geo3d-canvas canvas').boundingBox();
    await p.mouse.move(c.x + c.width / 2, c.y + c.height / 2); await p.mouse.down();
    await p.mouse.move(c.x + c.width / 2 + dx, c.y + c.height / 2 - 40, { steps: 8 }); await p.mouse.up();
    await p.mouse.wheel(0, -200);
  };
  const nA = await A.locator('#dock-steps-ul [data-step]').count();
  await Promise.all([
    (async () => { await A.locator(`#dock-steps-ul [data-step="${nA - 1}"]`).click(); await drag(A, 160); })(),
    (async () => { await B.locator('#dock-steps-ul [data-step="0"]').click(); await drag(B, -160); })(),
  ]);
  await Promise.all([idle(A), idle(B)]);
  const [sa, sb] = [await st(A), await st(B)];
  assert.equal(sa.currentStep, nA - 1, 'A step changed by B');
  assert.equal(sb.currentStep, 0, 'B step changed by A');
  await assertOwn(A, sa.activeHistoryId); await assertOwn(B, sb.activeHistoryId);
  return { aStep: sa.currentStep, bStep: sb.currentStep };
});

await check('7. A plays the construction while B creates a new attempt', async () => {
  const aId = (await st(A)).activeHistoryId;
  await A.locator('#dock-steps-ul [data-step="0"]').click(); await idle(A);
  await A.locator('#pa-play').click();
  const b = await send(B, F1);
  const sa = await assertOwn(A, aId);
  await assertOwn(B, b);
  await A.waitForFunction(() => !window.__ALGO_SIM_STORE__.getState().playing, null, { timeout: 30000 }).catch(() => {});
  return { aId, b, aPlayingDuringB: sa.playing };
});

await check('retry: a 502 then 200 inside one send reuses the same Idempotency-Key and records one attempt', async () => {
  const n0 = (await records(A)).length;
  failNextFor = F2.problem_text.trim();
  const a = await send(A, F2);
  const tail = analyzeLog.slice(-2);
  assert.deepEqual(tail.map((r) => r.status), [502, 200]);
  assert.equal(tail[0].key, tail[1].key, 'retry used another key');
  assert.equal(tail[1].key, a, 'key is not the attempt id');
  assert.equal((await records(A)).length, n0 + 1);
  return { a, keys: tail.map((r) => r.key) };
});

report.summary = { pass: report.checks.filter((c) => c.status === 'PASS').length, total: report.checks.length, attempts: created.size, analyzeRequests: analyzeLog.length };
save();
await browser.close(); server.close();
console.log(JSON.stringify(report.summary));
if (report.forbidden.length || report.summary.pass !== report.summary.total) process.exit(1);
