import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const { chromium } = createRequire(resolve('frontend/package.json'))('playwright');
const run = resolve('docs/evaluation/geometry/runs/scene3d-visual-correction');
const source = resolve('docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/reference/matphang.html');
const out = join(run, 'verification/reference');
mkdirSync(out, { recursive: true });
const bytes = readFileSync(source), sha = b => createHash('sha256').update(b).digest('hex');
const receipt = { source: source.slice(process.cwd().length + 1), bytes: bytes.length, sha256: sha(bytes),
  normalized_lf_sha256: sha(bytes.toString().replace(/\r\n/g, '\n')), provider_calls: 0,
  execution: 'ORIGINAL_HTML_UNMODIFIED', cdn_failures: [], errors: [], rows: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('pageerror', e => receipt.errors.push(e.message.split('\n')[0]));
  page.on('requestfailed', r => receipt.cdn_failures.push({ url: r.url(), error: r.failure()?.errorText }));
  await page.goto(pathToFileURL(source).href, { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(1000);
  receipt.runtime = await page.evaluate(() => ({ title: document.title, three: window.THREE?.REVISION,
    canvas: document.querySelectorAll('canvas').length, select: typeof selectShape }));
  if (receipt.runtime.canvas && receipt.runtime.select === 'function') {
    const catalog = await page.evaluate(() => SHAPES_DB.map(s => ({ id: s.id, name: s.name })));
    receipt.catalog = catalog;
    for (const shape of catalog) {
      await page.evaluate(id => selectShape(id), shape.id);
      await page.waitForTimeout(120);
      const row = await page.evaluate(() => ({ id: state.currentShapeId ?? state.selectedShapeId,
        canvas: document.querySelectorAll('canvas').length, opacity: state.opacity,
        arcs: dynamicArcs.length, edges: dynamicEdges.length, labels: activeLabels.length }));
      row.id = shape.id;
      const image = await page.screenshot();
      row.image = `${shape.id}.png`; row.sha256 = sha(image);
      writeFileSync(join(out, row.image), image);
      receipt.rows.push(row);
    }
  }
} catch (e) { receipt.failure = e.message.split('\n')[0]; }
finally { await browser.close(); }
receipt.status = receipt.rows.length === 18 && !receipt.errors.length ? 'REFERENCE_EXECUTED' : 'REFERENCE_EXECUTION_GAP';
writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify({ status: receipt.status, runtime: receipt.runtime, rows: receipt.rows.length,
  errors: receipt.errors, cdn_failures: receipt.cdn_failures.length, failure: receipt.failure }));
