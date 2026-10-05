/**
 * cuboid-final-review — focused browser check of the refusal card (task 5). 0 model calls.
 *
 * Runs only the cases of refusal_fixtures_cfr.py (three refusals with the new code, a proven-mismatch and an
 * unverified control, one served control) at the two registered viewports, on the production build: `dist/`
 * served statically, the problem typed into the real input, `/api/analyze` answered with the fixture envelope.
 * Assertions are the suite's own (`runNegative`/`runServed` of compiler-scene-suite.mjs): structured refusal,
 * learner message shown verbatim, problem label, no canvas, no answer, no overflow, no raw token, no console
 * error, no exception. The six families are not re-measured.
 *
 *   cd frontend && npm run build && node ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/\
 *     browser_refusal_cfr.mjs --cases <dir with CASES.json> --images <dir> --report <file.json>
 */
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { runNegative, runServed } from "../../../../../../frontend/scripts/compiler-scene-suite.mjs";
import { kiemDistMoi, phucVu } from "../../../../../../frontend/scripts/scene3d-orbit-gate.mjs";

const ROOT = resolve(import.meta.dirname, "../../../../../..");
const arg = (k) => resolve(process.argv[process.argv.indexOf(`--${k}`) + 1]);
const [casesDir, imagesDir, reportPath] = [arg("cases"), arg("images"), arg("report")];
const cases = JSON.parse(readFileSync(join(casesDir, "CASES.json"), "utf-8"));
const suite = JSON.parse(readFileSync(join(ROOT, "frontend/scripts/generic-tier-a-scenarios.json"), "utf-8"));

kiemDistMoi();
const { sv, cong } = await phucVu(join(ROOT, "frontend", "dist"));
const results = {};
try {
  for (const c of cases.cases) {
    const fixture = JSON.parse(readFileSync(join(casesDir, c.fixture), "utf-8"));
    results[c.case] = {};
    for (const viewport of suite.viewports) {
      const run = c.mode === "served" ? runServed : runNegative;
      const r = await run({ port: cong, viewport, fixture, expected: c.expected,
        outDir: join(imagesDir, c.case, viewport.id) });
      results[c.case][viewport.id] = r;
      console.log(`${c.case} ${viewport.id}: ${r.pass ? "PASS" : "FAIL"}`);
    }
  }
} finally {
  sv.close();
}
const pass = Object.values(results).every((byViewport) => Object.values(byViewport).every((r) => r.pass));
writeFileSync(reportPath, JSON.stringify({
  schema_version: "cfr-browser-refusal/1",
  measured_at: new Date().toISOString(),
  measurement_commit_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf-8" }).trim(),
  product_commit_sha: cases.product_commit_sha,
  product_tree_sha: cases.product_tree_sha,
  viewports: suite.viewports.map(({ id, width, height }) => ({ id, width, height })),
  application_llm_calls: 0,
  results,
  pass,
}, null, 2) + "\n", "utf-8");
console.log(`BROWSER_REFUSAL_CFR ${pass ? "PASS" : "FAIL"}`);
process.exit(pass ? 0 : 1);
