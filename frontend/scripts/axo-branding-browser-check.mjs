// Offline production-build check of Axo identity in a real Chrome (run axo-postmerge-consolidation): for the home page,
// library, history and a 3D simulation route, in a FRESH context at desktop and phone width: tab title, the icon link and
// what it serves (status, content type, SHA-256), the header logo, any visible "AlgoSim", failed requests and console
// errors; then a reload and an in-app navigation (title follows the view). Screenshots of each page and of the icon.
// Usage: node scripts/axo-branding-browser-check.mjs --dist <dir> --out <fresh dir> [--expect-axo]
// Without --expect-axo it only records (used for the "before" build). 0 model calls.
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import assert from 'node:assert/strict';

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const dist = resolve(arg('--dist', 'dist'));
const out = resolve(arg('--out'));
const expectAxo = process.argv.includes('--expect-axo');
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname.startsWith('/api/')) {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(pathname === '/api/health' ? { ok: true, hasKey: true } : { user: null }));
    return;
  }
  const asset = pathname.includes('.');
  const file = join(dist, asset ? pathname : 'index.html');      // SPA fallback only for routes, never for assets
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: 'chrome', headless: true });
// The receipt names the build by its index.html hash, never by a local path.
const distIndexSha256 = createHash('sha256').update(readFileSync(join(dist, 'index.html'))).digest('hex');
const report = { schema: 'axo-branding/1', distIndexSha256, expectAxo, provider_calls: 0, browser: browser.version(), pages: [], checks: [] };
const ROUTES = [['home', '/'], ['library', '/library'], ['history', '/history'], ['simulation', '/simulation/thiet-dien-chop']];

for (const [vw, vh] of [[1440, 900], [390, 844]]) {
  for (const [name, path] of ROUTES) {
    const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });     // fresh: no cached icon
    const page = await ctx.newPage();
    const failed = [], consoleErrors = [];
    page.on('response', (r) => { if (r.status() >= 400) failed.push(`${r.status()} ${new URL(r.url()).pathname}`); });
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
    await page.goto(`${url}${path}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    const read = () => page.evaluate(() => ({
      title: document.title,
      icon: [...document.querySelectorAll('link[rel~="icon"]')].map((l) => l.getAttribute('href')),
      headerLogo: !!document.querySelector('.axo-logo-svg, [aria-label="Axo logo"]'),
      algoSimVisible: /AlgoSim/.test(document.body.innerText),
    }));
    const first = await read();
    const iconHref = first.icon[0];
    let iconFetch = null;
    if (iconHref && !iconHref.startsWith('data:')) {
      const r = await page.request.get(new URL(iconHref, url).toString());
      const body = await r.body();
      iconFetch = { status: r.status(), type: r.headers()['content-type'], sha256: createHash('sha256').update(body).digest('hex') };
    }
    await page.screenshot({ path: join(out, `${name}-${vw}.png`) });
    await page.reload({ waitUntil: 'networkidle' }); await page.waitForTimeout(300);
    const afterReload = await read();
    report.pages.push({ route: path, viewport: `${vw}x${vh}`, ...first, iconFetch, afterReload, failed, consoleErrors });
    await ctx.close();
  }
}

// In-app navigation: the title follows the view without a reload.
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const titles = {};
  for (const v of ['library', 'history', 'home']) {
    await page.evaluate((view) => window.__ALGO_SIM_STORE__?.getState().setView(view), v);
    await page.waitForTimeout(250);
    titles[v] = await page.title();
  }
  report.navigation = titles;
  // The "before" build has no /favicon.svg: record the 404 instead of failing.
  const fav = await page.goto(`${url}/favicon.svg`).catch((e) => ({ status: () => e.message.slice(0, 80) }));
  report.faviconDirect = fav.status();
  if (fav.status() === 200) await page.screenshot({ path: join(out, 'favicon-served.png') });
  await ctx.close();
}

if (expectAxo) {
  const check = (name, fn) => { try { fn(); report.checks.push({ name, status: 'PASS' }); } catch (e) {
    report.checks.push({ name, status: 'FAIL', error: e.message.slice(0, 400) }); } };
  for (const p of report.pages) {
    check(`${p.route} @${p.viewport}`, () => {
      assert.ok(p.title.includes('Axo') && !p.title.includes('AlgoSim'), `title ${p.title}`);
      assert.equal(p.afterReload.title, p.title, 'reload changed the title');
      assert.deepEqual(p.icon, ['/favicon.svg']);
      assert.equal(p.iconFetch?.status, 200); assert.match(p.iconFetch.type, /image\/svg\+xml/);
      assert.equal(p.algoSimVisible, false, 'visible AlgoSim');
      assert.deepEqual(p.failed, [], 'failed requests');
      assert.deepEqual(p.consoleErrors, [], 'console errors');
    });
  }
  check('in-app navigation retitles the tab', () => {
    assert.equal(report.navigation.library, 'Thư viện | Axo');
    assert.equal(report.navigation.history, 'Lịch sử | Axo');
    assert.ok(report.navigation.home.startsWith('Axo'));
  });
}
report.summary = { pass: report.checks.filter((c) => c.status === 'PASS').length, total: report.checks.length };
writeFileSync(join(out, 'receipt.json'), JSON.stringify(report, null, 2));
await browser.close(); server.close();
console.log(JSON.stringify({ summary: report.summary, sample: report.pages.slice(0, 4).map((p) => [p.route, p.title, p.icon, p.iconFetch?.status ?? null]) }));
process.exitCode = expectAxo && report.summary.pass !== report.summary.total ? 1 : 0;
