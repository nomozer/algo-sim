// Final pre-main audit capture — F3/F4/F5/F6 on the PRODUCT build, real UI, Adapter /2 fixtures.
// /api/analyze answers with `fixture.response.envelope` exactly as frozen: each fixture's canonical
// `response` SHA-256 is checked against manifest.json before it is served (no hand-written response).
// F4 component harness (route_d outside the envelope) is a separate page: --harness <dir>.
// usage: node capture-f3-f6.mjs <frontendDir> <outDir> [--harness <builtHarnessDir>]
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from "node:fs";
import { join, extname, resolve } from "node:path";

const [frontend, out] = process.argv.slice(2).map((p) => resolve(p));
const hi = process.argv.indexOf("--harness");
const harnessDir = hi > 0 ? resolve(process.argv[hi + 1]) : null;
const { chromium } = createRequire(join(frontend, "package.json"))("playwright");
const FX = join(frontend, "..", "docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2");
mkdirSync(out, { recursive: true });

const canon = (v) => v === null || typeof v !== "object" ? JSON.stringify(v)
  : Array.isArray(v) ? `[${v.map(canon).join(",")}]`
  : `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(",")}}`;
const sha = (s) => createHash("sha256").update(s, "utf8").digest("hex");
const manifest = JSON.parse(readFileSync(join(FX, "manifest.json"), "utf8"));
function fixture(id) {
  const row = manifest.fixtures.find((r) => r.id === id);
  const fx = JSON.parse(readFileSync(join(FX, row.file), "utf8"));
  const got = sha(canon(fx.response));
  if (got !== row.response_sha256) throw new Error(`${id}: response sha ${got} != manifest ${row.response_sha256}`);
  return { row, fx };
}

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".ico": "image/x-icon" };
function serve(dir) {
  return new Promise((ok) => {
    const sv = createServer((req, res) => {
      let p = join(dir, decodeURIComponent(new URL(req.url, "http://x").pathname));
      if (!existsSync(p) || statSync(p).isDirectory()) p = join(dir, "index.html");
      res.writeHead(200, { "Content-Type": MIME[extname(p)] ?? "application/octet-stream" });
      res.end(readFileSync(p));
    }).listen(0, "127.0.0.1", () => ok({ sv, origin: `http://127.0.0.1:${sv.address().port}` }));
  });
}

const PROD = [
  // [id, feature, problem text typed in the real textarea]
  ...["refusal-source-object-mismatch", "refusal-source-goal-as-premise", "refusal-source-request-unanswered",
    "refusal-result-engine-self-check", "refusal-result-kernel-check", "refusal-result-scene-metric",
    "refusal-inconclusive-figure", "refusal-inconclusive-negated", "refusal-inconclusive-proof-only"].map((id) => [id, "F5"]),
  ...["refusal-missing-dimension", "refusal-missing-ambiguous", "refusal-missing-underdetermined"].map((id) => [id, "F6"]),
  ["refusal-invalid-zero-length", "F6-SOURCE"],
  ["served-H01_CUBE", "F3"], ["served-H14_REGULAR_TETRAHEDRON", "F3"], ["served-pyramid-midpoint-area-AB", "F3-none"],
  ["served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "F4-product"],
];
const LEAK = ["verification_gap", "insufficient_specification", "geometry_generation_failed", "refusal_cause",
  "reason_code", "UNKNOWN", "OFFLINE_FIXTURE_ONLY", "hybrid_route_d_preview", "generic.semantic_program", "Traceback"];
const PROVEN = /đã\s*chứng\s*minh|được\s*chứng\s*minh|điều\s*phải\s*chứng\s*minh|đpcm|✓/i;

const results = [];
const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const { sv, origin } = await serve(join(frontend, "dist"));
try {
  for (const [id, feature] of PROD) {
    const { row, fx } = fixture(id);
    const env = fx.response.envelope;
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message.slice(0, 200)));
    page.on("console", (m) => { if (m.type() === "error" && !/favicon|ERR_NETWORK_ACCESS_DENIED|404/.test(m.text())) errors.push(m.text().slice(0, 200)); });
    let served = null;
    await page.route("**/api/**", (route) => {
      const p = new URL(route.request().url()).pathname;
      if (p === "/api/analyze") { served = JSON.stringify(env); return route.fulfill({ status: 200, contentType: "application/json", body: served }); }
      if (p === "/api/health") return route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true,"hasKey":true,"cachedProblems":0}' });
      if (p === "/api/auth/me") return route.fulfill({ status: 200, contentType: "application/json", body: '{"user":null}' });
      return route.fulfill({ status: 404, contentType: "application/json", body: '{"error":"not mocked"}' });
    });
    await page.goto(origin);
    await page.waitForSelector("textarea", { timeout: 30000 });
    await page.fill("textarea", fx.source?.problem_text ?? "Cho hình chóp S.ABC.");
    await page.locator('button[aria-label="Phân tích đề bằng AI"]').click();
    const isRefusal = env.status === "unsupported";
    await page.waitForSelector(isRefusal ? ".refusal-facts" : "canvas", { timeout: 30000 });
    if (!isRefusal) await page.waitForTimeout(1500); // let WebGL paint
    const dom = await page.evaluate(() => {
      const card = document.querySelector(".refusal-facts")?.closest(".card");
      const q = (s) => (card?.querySelector(s)?.textContent ?? "").trim();
      const dd = [...(card?.querySelectorAll(".refusal-facts dd") ?? [])].map((e) => e.textContent.trim());
      return {
        eyebrow: q(".eyebrow"), body: card ? q("p") : null, hint: card ? (card.querySelector(".notes")?.textContent ?? null) : null,
        stage_label: dd[0] ?? null, kind_label: dd[1] ?? null,
        length_unit: [...document.querySelectorAll("[data-length-unit]")].map((e) => e.textContent.trim()),
        route_d_observation: [...document.querySelectorAll("[data-route-d-observation]")].map((e) => e.textContent.trim()),
        canvases: document.querySelectorAll("canvas").length,
        text: document.body.innerText,
      };
    });
    const png = `${feature}__${id}.png`;
    await page.screenshot({ path: join(out, png), fullPage: false });
    const leaks = LEAK.filter((k) => dom.text.includes(k)).concat(isRefusal && dom.text.includes(env.reason_code) ? [env.reason_code] : []);
    results.push({
      id, feature, path: "PRODUCT /api/analyze → store → SimulationWorkspace", manifest_response_sha256: row.response_sha256,
      served_envelope_sha256: sha(canon(JSON.parse(served))), envelope_identical_to_fixture: canon(JSON.parse(served)) === canon(env),
      expected: row.expected, screenshot: png,
      dom: { ...dom, text: undefined }, leaks, proven_wording: PROVEN.test(dom.text), page_errors: errors,
    });
    console.log(`${feature.padEnd(10)} ${id.padEnd(48)} eyebrow="${dom.eyebrow}" hint=${JSON.stringify(dom.hint)} kind="${dom.kind_label}" lu=${JSON.stringify(dom.length_unit)} obs=${dom.route_d_observation.length} leaks=${JSON.stringify(leaks)} errs=${errors.length}`);
    await ctx.close();
  }

  if (harnessDir) {
    const h = await serve(harnessDir);
    for (const id of ["served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "served-H01_CUBE"]) {
      const { row } = fixture(id);
      const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message.slice(0, 200)));
      await page.goto(`${h.origin}/scripts/f4-harness.html?id=${id}`);
      await page.waitForSelector("canvas", { timeout: 30000 });
      await page.waitForTimeout(1500);
      const dom = await page.evaluate(() => ({
        length_unit: [...document.querySelectorAll("[data-length-unit]")].map((e) => e.textContent.trim()),
        route_d_observation: [...document.querySelectorAll("[data-route-d-observation]")].map((e) => e.textContent.trim()),
        harness_sha: window.__fixtureSha ?? null, text: document.body.innerText,
      }));
      const png = `F4-component__${id}.png`;
      await page.screenshot({ path: join(out, png) });
      results.push({ id, feature: "F4-component", path: "COMPONENT HARNESS Scene3DExplorer(scene=envelope.scene3d, routeD=response.route_d)",
        manifest_response_sha256: row.response_sha256, harness_response_sha256: dom.harness_sha,
        screenshot: png, dom: { ...dom, text: undefined }, proven_wording: PROVEN.test(dom.text), page_errors: errors });
      console.log(`F4-comp    ${id.padEnd(48)} sha_ok=${dom.harness_sha === row.response_sha256} obs=${JSON.stringify(dom.route_d_observation)} lu=${JSON.stringify(dom.length_unit)} proven=${PROVEN.test(dom.text)} errs=${errors.length}`);
      await ctx.close();
    }
    h.sv.close();
  }
} finally {
  await browser.close();
  sv.close();
}
writeFileSync(join(out, "dom-receipts.json"), JSON.stringify({ schema: "PRE_MAIN_DOM_CAPTURE/1", live_ai_calls: 0, results }, null, 2));
