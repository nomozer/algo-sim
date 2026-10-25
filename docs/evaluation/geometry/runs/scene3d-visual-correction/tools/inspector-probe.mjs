// Mode B inspector probe: after selecting a final result from the analysis panel, is the inspector open, and does it
// print the result again? node .superpowers/inspector-probe.mjs <url>
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
const { chromium } = createRequire(process.cwd() + "/frontend/package.json")("playwright");
const url = process.argv[2];
const samples = JSON.parse(readFileSync("frontend/src/data/geometry-samples.json", "utf8")).samples;
const fixture = (f) => JSON.parse(readFileSync(`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${f}_positive.json`, "utf8")).envelope;
const cases = [["cross_section", fixture("cross_section")], ["cuboid", fixture("cuboid")], ["cau-cat-mat-phang", samples.find((s) => s.id === "cau-cat-mat-phang").envelope],
  ["non-duong-sinh", samples.find((s) => s.id === "non-duong-sinh").envelope]];
const b = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const out = [];
for (const [id, env] of cases) {
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  await p.route("**/api/**", (r) => r.fulfill({ json: r.request().url().includes("/api/health") ? { status: "ok" } : null }));
  await p.goto(url);
  await p.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, env);
  await p.locator(".geo3d-canvas canvas").waitFor();
  await p.locator(".geo3d-scrub input").evaluate((el) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, el.max); el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); });
  await p.getByRole("button", { name: "Phân tích toán học", exact: true }).click();
  const rows = [];
  for (const item of await p.locator('section[aria-label="Kết quả toán học"] [data-analysis-item] button').all()) {
    await item.click(); await p.waitForTimeout(300);
    rows.push(await p.evaluate(() => {
      const sel = window.__geo3d_selected_id, soi = document.querySelector(".geo3d-soi");
      return { selected: sel, inspector_open: Boolean(soi && soi.offsetParent !== null),
        inspector_repeats: [...document.querySelectorAll(`[data-value-entity="${sel}"],[data-formula-entity="${sel}"]`)].length,
        link: [...(soi?.querySelectorAll('a[href="#geo3d-bang-phan-tich"]') ?? [])].map((a) => a.textContent),
        canvas_results: document.querySelectorAll(".geo3d-so-do.la-ket-qua").length };
    }));
  }
  out.push({ id, rows });
  await p.close();
}
await b.close();
console.log(JSON.stringify({ url, out }, null, 1));
