// Offline production-build check of `session_required` in a real Chrome: the page sends a problem with NO session cookie
// (an expired or never-issued session); the stub server answers like the backend (`reserve_analysis_usage`): 401
// `session_required` + an httponly `Set-Cookie`, running nothing; with the cookie it serves a recorded Hybrid /4 response.
// Asserted: exactly two /api/analyze requests, the same Idempotency-Key, the second one carries the issued cookie, the
// scene renders, and a page whose cookies are always dropped gets one refusal per send (no loop). 0 model calls.
// Usage: node scripts/axo-session-required-browser-check.mjs --dist <dir> --out <fresh dir> [--headed]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import assert from 'node:assert/strict';

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const dist = resolve(arg('--dist', 'dist'));
const out = resolve(arg('--out'));
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const corpus = JSON.parse(readFileSync('../docs/evaluation/geometry/runs/axo-final-mathematical-reliability/inputs/corpus.json', 'utf8'));
const prism = corpus.find((r) => r.id === 'right-prism');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };

const log = [];
let dropCookies = false;
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const cookie = /algosim_session=([\w-]+)/.exec(dropCookies ? '' : req.headers.cookie ?? '')?.[1] ?? null;
  if (pathname === '/api/analyze' && req.method === 'POST') {
    let raw = ''; req.on('data', (c) => { raw += c; }); req.on('end', () => {
      log.push({ key: req.headers['idempotency-key'] ?? null, cookie, text: JSON.parse(raw).input.content.slice(0, 30) });
      res.setHeader('Content-Type', 'application/json');
      if (!cookie) {
        res.statusCode = 401;
        res.setHeader('Set-Cookie', `algosim_session=s${log.length}${Date.now()}; HttpOnly; SameSite=Lax; Path=/`);
        res.end(JSON.stringify({ error: 'Phiên làm việc chưa sẵn sàng.', reason_code: 'session_required' }));
        return;
      }
      res.end(JSON.stringify(prism.response));
    });
    return;
  }
  if (pathname.startsWith('/api/')) {       // no session is issued on page load: the analyze refusal must issue it
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
const browser = await chromium.launch({ channel: 'chrome', headless: !process.argv.includes('--headed') });
const report = { schema: 'axo-session-required/1', dist, provider_calls: 0, browser: browser.version(), checks: [], forbidden: [] };
const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
await ctx.route('**/*', (r) => (new URL(r.request().url()).origin !== url
  ? (report.forbidden.push(r.request().url()), r.abort()) : r.continue()));
const page = await ctx.newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message));
const send = async () => {
  await page.goto(`${url}/`); await page.waitForSelector('#home-problem-input');
  await page.locator('#home-problem-input').fill(prism.input.problem_text);
  await page.waitForFunction(() => !document.querySelector('#btn-composer-send')?.hasAttribute('disabled'));
  await page.locator('#btn-composer-send').click();
};
const check = async (name, fn) => {
  try { report.checks.push({ name, status: 'PASS', ...(await fn()) }); } catch (e) {
    report.checks.push({ name, status: 'FAIL', error: String(e.message).slice(0, 600) });
  }
};

await check('no session at send: one refusal issues the cookie, the same attempt is retried once and served', async () => {
  await send();
  await page.waitForSelector('#dock-steps-ul [data-step]', { timeout: 30000 });
  assert.equal(log.length, 2, `analyze requests ${log.length}`);
  assert.ok(log[0].key && log[0].key === log[1].key, 'retry changed the attempt ID');
  assert.equal(log[0].cookie, null);
  assert.ok(log[1].cookie, 'the retry did not carry the issued cookie');
  const cookies = await ctx.cookies(url);
  assert.ok(cookies.some((c) => c.name === 'algosim_session' && c.httpOnly), 'issued cookie not stored as httponly');
  return { requests: log.length };
});

await check('a page whose cookie never arrives gets the refusal once per send, never a loop', async () => {
  log.length = 0; dropCookies = true;
  await send();
  await page.waitForFunction(() => !!window.__ALGO_SIM_STORE__?.getState().analysisError
    || !!window.__ALGO_SIM_STORE__?.getState().clientFailure, null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(1500);
  assert.equal(log.length, 2, `analyze requests ${log.length}`);
  assert.equal(await page.locator('#dock-steps-ul [data-step]').count(), 0, 'a scene was shown without a session');
  return { requests: log.length };
});

report.pageErrors = errors;
report.summary = { pass: report.checks.filter((c) => c.status === 'PASS').length, total: report.checks.length };
writeFileSync(join(out, 'receipt.json'), JSON.stringify({ ...report, log }, null, 2));
await browser.close(); server.close();
console.log(JSON.stringify(report.summary));
process.exitCode = report.summary.pass === report.summary.total && !report.forbidden.length ? 0 : 1;
