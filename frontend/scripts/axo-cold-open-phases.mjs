// Cold-open phase breakdown of `/simulation/<sample>` on production builds, alternating builds (A B B A …), cache
// disabled per sample, after a controlled warm-up. Phases from the page's own clocks: HTML response, script fetch end,
// DOMContentLoaded, first WebGL context (GPU resources), first draw call, first rendered Scene3D objects. One CDP CPU
// profile per build summarises self time by script URL. 0 network beyond the local static server.
// Usage: node scripts/axo-cold-open-phases.mjs --dist-a <dir> --dist-b <dir> --out <fresh dir> [--rounds 6] [--sample pyramid-cross-section]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const dists = { A: resolve(arg('--dist-a')), B: resolve(arg('--dist-b')) };
const out = resolve(arg('--out'));
const rounds = Number(arg('--rounds', '6'));
const sample = arg('--sample', 'pyramid-cross-section');
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const serve = (dist) => new Promise((r) => {
  const s = createServer((req, res) => {
    const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.startsWith('/api/')) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(p === '/api/health' ? { ok: true, hasKey: false } : { user: null })); return; }
    const f = join(dist, p.includes('.') ? p : 'index.html');
    if (!f.startsWith(dist) || !existsSync(f)) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', mime[extname(f)] ?? 'application/octet-stream'); res.end(readFileSync(f));
  });
  s.listen(0, '127.0.0.1', () => r({ s, url: `http://127.0.0.1:${s.address().port}` }));
});
const servers = { A: await serve(dists.A), B: await serve(dists.B) };
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
await ctx.addInitScript(() => {
  const m = window.__phase = { glContext: null, firstDraw: null };
  const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (...a) {
    const g = gc.apply(this, a);
    if (g && /webgl/.test(String(a[0])) && m.glContext === null) {
      m.glContext = performance.now();
      for (const fn of ['drawArrays', 'drawElements']) {
        const o = g[fn].bind(g);
        g[fn] = (...x) => { if (m.firstDraw === null) m.firstDraw = performance.now(); return o(...x); };
      }
    }
    return g;
  };
});
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
const gpu = await cdp.send('SystemInfo.getInfo').then((i) => i.gpu.devices.map((d) => d.deviceString)).catch(() => null);
const measure = async (v) => {
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await page.goto(`${servers[v].url}/simulation/${sample}`);
  await page.waitForFunction(() => window.__phase.firstDraw !== null && (window.__geo3d_rendered_object_ids?.length ?? 0) > 0, null, { timeout: 30000 });
  const rendered = await page.evaluate(() => performance.now());
  return page.evaluate((renderedSeen) => {
    const nav = performance.getEntriesByType('navigation')[0];
    const js = performance.getEntriesByType('resource').filter((r) => r.name.endsWith('.js'));
    return {
      htmlResponseEnd: nav.responseEnd, scriptsFetched: Math.max(...js.map((r) => r.responseEnd)),
      scriptBytes: js.reduce((s, r) => s + (r.transferSize || r.encodedBodySize || 0), 0),
      domContentLoaded: nav.domContentLoadedEventEnd, glContext: window.__phase.glContext,
      firstDraw: window.__phase.firstDraw, renderedObjectsSeenBy: renderedSeen,
    };
  }, rendered);
};
for (const v of ['A', 'B', 'A', 'B']) await measure(v);           // warm-up: OS file cache, browser process, JIT of harness
const rows = [];
const order = Array.from({ length: rounds }, (_, i) => (i % 2 ? ['B', 'A', 'A', 'B'] : ['A', 'B', 'B', 'A'])).flat();
for (const v of order) rows.push({ build: v, ...(await measure(v)) });
const profiles = {};
for (const v of ['A', 'B']) {
  await cdp.send('Profiler.enable'); await cdp.send('Profiler.setSamplingInterval', { interval: 100 }); await cdp.send('Profiler.start');
  await measure(v);
  const { profile } = await cdp.send('Profiler.stop');
  const dt = profile.timeDeltas; const self = new Map();
  const byId = new Map(profile.nodes.map((n) => [n.id, n]));
  profile.samples.forEach((id, i) => {
    const f = byId.get(id).callFrame;
    const key = f.url ? f.url.replace(/^.*\/assets\//, 'assets/') : `(${f.functionName || 'program'})`;
    self.set(key, (self.get(key) ?? 0) + (dt[i] ?? 0) / 1000);
  });
  profiles[v] = [...self.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, ms]) => ({ where: k, selfMs: Math.round(ms * 10) / 10 }));
}
const phases = ['htmlResponseEnd', 'scriptsFetched', 'domContentLoaded', 'glContext', 'firstDraw', 'renderedObjectsSeenBy'];
const med = (xs) => { const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
const p95 = (xs) => { const s = [...xs].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.round(.95 * (s.length - 1)))]; };
const summary = Object.fromEntries(['A', 'B'].map((v) => [v, Object.fromEntries(phases.map((p) => {
  const xs = rows.filter((r) => r.build === v).map((r) => r[p]);
  return [p, { median: Math.round(med(xs) * 10) / 10, p95: Math.round(p95(xs) * 10) / 10 }];
}))]));
writeFileSync(join(out, 'cold-open-phases.json'), JSON.stringify({ sample, dists, gpu, browser: browser.version(), order, rows, summary, profiles }, null, 2));
console.log(JSON.stringify({ gpu, summary }, null, 1));
await browser.close(); for (const { s } of Object.values(servers)) s.close();
