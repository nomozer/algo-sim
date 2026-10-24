// Run the official first-closed-section measurement independently of obsolete quantity-picker UX.
// No copied measurement logic, changed oracle, threshold or product hook.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const [wt, suitePath, fixtures, out] = process.argv.slice(2).map(p => resolve(p));
const moduleAt = p => import(pathToFileURL(join(wt, p)).href);
const { openFixture, sectionFillEvidence, trustedOrbit, currentStep, jsonEval, trustedClick } =
  await moduleAt('frontend/scripts/compiler-scene-suite.mjs');
const { phucVu } = await moduleAt('frontend/scripts/scene3d-orbit-gate.mjs');
const { pollUntil, validateSuiteManifest, settleCamera } = await moduleAt('frontend/scripts/compiler-scene-replay-lib.mjs');
const suite = JSON.parse(readFileSync(suitePath));
validateSuiteManifest(suite, wt);
const candidate = JSON.parse(readFileSync(join(wt, 'docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json')));
if (suite.product_commit_sha !== candidate.product_commit_sha || suite.product_tree_sha !== candidate.measured_system.tree_hash)
  throw Error('PRODUCT_PROVENANCE_MISMATCH');
mkdirSync(out, { recursive: true });
const sha = b => createHash('sha256').update(b).digest('hex');
const report = { schema: 'official-section-fill-closure/1',
  measurement_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: wt, encoding: 'utf8' }).trim(),
  product_commit: suite.product_commit_sha, measured_system_hash: suite.product_tree_sha,
  official_module_sha256: sha(readFileSync(join(wt, 'frontend/scripts/compiler-scene-suite.mjs'))),
  suite_sha256: sha(readFileSync(suitePath)), provider_calls: 0, rows: [], errors: [] };
const { sv, cong } = await phucVu(join(wt, 'frontend/dist'));
try {
  for (const scenario of suite.scenarios) {
    const fx = JSON.parse(readFileSync(join(fixtures, scenario.positive_fixture)));
    if (!fx.envelope.scene3d.objects.some(o => o.type === 'section' && o.polygon?.length >= 3)) continue;
    for (const viewport of suite.viewports) {
      const row = { id: scenario.id, viewport: viewport.id };
      report.rows.push(row);
      let session;
      try {
        const opened = await openFixture({ port: cong, viewport, fixture: fx });
        session = opened.session;
        await pollUntil(() => session.eval("!!document.querySelector('.geo3d-canvas canvas')"), Boolean);
        row.section_fill = await sectionFillEvidence(session, fx.envelope.scene3d);
        row.analyze_calls = opened.analyzeCalls();
        const index = row.section_fill.closed_ui_step;
        await session.eval(`(()=>{const e=document.querySelector('.geo3d-scrub input[type=range]');
          Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,${index});
          e.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
        await pollUntil(() => currentStep(session), s => s?.index === index);
        const settle = () => settleCamera(() => jsonEval(session,
          '({snapshot:window.__geo3d_camera_snapshot||null,frame_count:(window.__geo3d_occlusion_performance||{}).frame_count||0})'));
        await settle();
        row.images = [];
        for (const angle of ['closed-default', 'closed-orbit']) {
          if (angle === 'closed-orbit') { await trustedOrbit(session, { dx: 120, dy: -25 }); await settle(); }
          const file = `${scenario.id}-${viewport.id}-${angle}.png`;
          await session.screenshot(join(out, file));
          row.images.push({ file, sha256: sha(readFileSync(join(out, file))) });
        }
        await trustedClick(session, '[...document.querySelectorAll("button")].find(e=>(e.textContent||"").includes("Hiển thị"))');
        row.auxiliary_requested = await trustedClick(session,
          '[...document.querySelectorAll("[role=menuitemcheckbox]")].find(e=>(e.textContent||"").includes("Hình phụ"))');
        await session.eval('document.activeElement?.blur();document.body.click();true');
        if (row.auxiliary_requested) {
          await settle();
          const file = `${scenario.id}-${viewport.id}-auxiliary.png`;
          await session.screenshot(join(out, file));
          row.images.push({ file, sha256: sha(readFileSync(join(out, file))) });
        }
        row.pass = row.section_fill.pass && row.analyze_calls === 1;
        console.log(row.id, row.viewport, 'first closed step', index, row.pass ? 'PASS' : 'FAIL');
      } catch (e) {
        row.pass = false;
        row.error = String(e.message).split('\n')[0];
        report.errors.push({ id: row.id, viewport: row.viewport, code: row.error });
      } finally { await session?.close(); }
    }
  }
} finally {
  sv.close();
  report.pass = report.rows.length > 0 && report.rows.every(r => r.pass);
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(report, null, 2) + '\n');
}
process.exitCode = report.pass ? 0 : 1;
