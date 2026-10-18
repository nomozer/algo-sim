// Offline browser gate: real input/button/store/shell, synthetic fault payloads labelled below.
// Usage: node check-boundary.mjs <candidate frontend directory> <new output directory>
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, resolve, extname } from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const [fe, out] = process.argv.slice(2).map(p => resolve(p));
const { chromium } = createRequire(join(fe, 'package.json'))('playwright');
const base = join(fe, '../docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2');
const load = (id) => JSON.parse(readFileSync(join(base, id + '.json'), 'utf8')).response;
const diag = (x) => [[x,'0','0'],['0','1','0'],['0','0','1']];
const mutated = (metric, bypass = false) => {
  const env = load('served-H01_CUBE').envelope;
  env.scene3d = bypass ? { chart_metric: metric } : { ...env.scene3d, chart_metric: metric };
  return env;
};
const legacy = load('served-H01_CUBE').envelope;
delete legacy.scene3d;
const cases = [
  ['malformed', mutated([['1']]), 'error'],
  ['non-SPD', mutated(diag('-1')), 'error'],
  ['overflow', mutated(diag('9'.repeat(400))), 'error'],
  ['finite-SPD-overflow', mutated(diag('1'+'0'.repeat(40))), 'error'],
  ['fallback-bypass', mutated(diag('-1'), true), 'error'],
  ['valid-3D', load('served-H01_CUBE').envelope, '3d'],
  ['valid-legacy-2D', legacy, '2d'],
  ['F4-product-locked', load('served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED').envelope, '3d'],
];
mkdirSync(out, { recursive: true });
const mime = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.svg':'image/svg+xml' };
const sv = createServer((req, res) => {
  let p = join(fe, 'dist', new URL(req.url, 'http://x').pathname);
  if (!existsSync(p) || statSync(p).isDirectory()) p = join(fe,'dist/index.html');
  res.writeHead(200, { 'Content-Type': mime[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
});
await new Promise((r) => sv.listen(0,'127.0.0.1',r));
const origin = `http://127.0.0.1:${sv.address().port}`;
const browser = await chromium.launch({ headless:true, args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
const results = [];
try {
  for (const [id,env,want] of cases) {
    const ctx = await browser.newContext({ viewport:{width:1440,height:900} });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await ctx.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.origin !== origin) return route.abort();
      if (url.pathname === '/api/analyze') return route.fulfill({json:env});
      if (url.pathname === '/api/health') return route.fulfill({json:{ok:true,hasKey:true,cachedProblems:0}});
      if (url.pathname === '/api/auth/me') return route.fulfill({json:{user:null}});
      if (url.pathname.startsWith('/api/')) return route.fulfill({status:404,json:{error:'offline'}});
      return route.continue();
    });
    await page.goto(origin);
    await page.locator('textarea').fill('Cho hình chóp S.ABC. Tính thể tích.');
    await page.locator('button[aria-label="Phân tích đề bằng AI"]').click();
    await page.waitForSelector(want === 'error' ? '.error-banner' : want === '3d' ? 'canvas' : '.workspace-card');
    const receipt = await page.evaluate(() => ({
      canvases:document.querySelectorAll('canvas').length,
      stages2d:document.querySelectorAll('.workspace-card').length,
      errors:[...document.querySelectorAll('.error-banner')].map(e=>e.textContent),
      observations:document.querySelectorAll('[data-route-d-observation]').length,
      history:JSON.parse(localStorage.getItem('algosim.history.v1') || '[]').length,
    }));
    assert.equal(errors.length,0,id);
    assert.equal(receipt.observations,0,id);
    assert.equal(receipt.history,want === 'error' ? 0 : 1,id);
    assert.equal(receipt.canvases,want === '3d' ? 1 : 0,id);
    if (want === 'error') assert.equal(receipt.stages2d,0,id);
    await page.screenshot({path:join(out,id+'.png')});
    results.push({id, input_kind:want==='error'?'synthetic fault':id.startsWith('valid-legacy')?'scene omitted from fixture':'offline fixture envelope',
      sent_sha256:createHash('sha256').update(JSON.stringify(env)).digest('hex'),want,...receipt,page_errors:errors});
    console.log(id+': PASS');
    await ctx.close();
  }
} finally { await browser.close(); await new Promise(r=>sv.close(r)); }
const repo = resolve(fe,'..');
const candidate_head = execFileSync('git',['-c',`safe.directory=${repo}`,'-C',repo,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const dist_files = ['index.html',...readdirSync(join(fe,'dist/assets')).map(p=>'assets/'+p)].sort().map(path => ({
  path, sha256:createHash('sha256').update(readFileSync(join(fe,'dist',path))).digest('hex'),
}));
writeFileSync(join(out,'boundary-browser.json'),JSON.stringify({schema:'SCENE3D_BOUNDARY_BROWSER/1',candidate_head,dist_files,live_calls:0,results},null,2)+'\n');
