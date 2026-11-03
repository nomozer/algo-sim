// Pre-fix UI disclosure audit: real dist + real uvicorn (staging-replay, 0 live calls), every SERVED case.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, statSync, writeFileSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import { extname, join, normalize, resolve } from "node:path";
const W = process.argv[2];
const OUT = process.argv[3];
const { chromium } = await import(`file:///${W}/frontend/node_modules/playwright/index.mjs`);
const RUN = join(W, "docs/evaluation/geometry/runs/hybrid-master-backend-replacement");
const DIST = join(W, "frontend/dist");
const PY = join(W, "backend/.venv/Scripts/python.exe");
const ONLY = process.env.ONLY ? new Set(process.env.ONLY.split(",")) : null;

const port0 = () => new Promise((r) => { const s = net.createServer(); s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => r(p)); }); });
const bp = await port0();
const tmp = mkdtempSync(join(os.tmpdir(), "disc-audit-"));
const child = spawn(existsSync(PY) ? PY : "python", ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(bp), "--log-level", "warning"], {
  cwd: join(W, "backend"),
  env: { ...process.env, PYTHONIOENCODING: "utf-8", GEMINI_API_KEY: "", ALLOW_LIVE_AI: "0", HYBRID_V2_LOCAL_ANALYZE: "0",
    DATABASE_URL: `sqlite:///${join(tmp, "a.db").replace(/\\/g, "/")}`, HYBRID_ROUTE_MODE: "staging-replay",
    HYBRID_REPLAY_CORPUS: join(RUN, "product-integration-staging-corpus.json") },
  stdio: ["ignore", "inherit", "inherit"],
});
for (let i = 0; i < 150; i++) { try { if ((await fetch(`http://127.0.0.1:${bp}/api/health`)).ok) break; } catch {} await new Promise((r) => setTimeout(r, 200)); }
const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };
const gw = http.createServer((req, res) => {
  const u = (req.url || "/").split("?")[0];
  if (u.startsWith("/api")) {
    const p = http.request({ hostname: "127.0.0.1", port: bp, path: req.url, method: req.method, headers: req.headers }, (pr) => { res.writeHead(pr.statusCode, pr.headers); pr.pipe(res); });
    req.pipe(p); return;
  }
  let f = resolve(DIST, normalize(u === "/" ? "index.html" : u.slice(1)));
  if (!existsSync(f) || statSync(f).isDirectory()) f = join(DIST, "index.html");
  res.writeHead(200, { "content-type": MIME[extname(f)] || "application/octet-stream" }); res.end(readFileSync(f));
});
await new Promise((r) => gw.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${gw.address().port}`;

const ver = JSON.parse(readFileSync(join(RUN, "product-integration-16-classes-verification.json"), "utf8"));
const cases = ver.categories.flatMap((c) => c.cases.map((x) => ({ ...x, category: c.category_id }))).filter((c) => c.route_d_status === "SERVED" && (!ONLY || ONLY.has(c.case_id)));

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });
let analyzeCalls = 0;
page.on("request", (r) => { if (r.url().includes("/api/analyze")) analyzeCalls++; });
await page.goto(base, { waitUntil: "networkidle" });
await page.evaluate(async () => { await fetch("/api/auth/register", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "audit@student.local", displayName: "Audit", password: ["Mat", "Khau!2026x"].join("") }) }); });
await page.reload({ waitUntil: "networkidle" });

// Every text a student (or a screen reader) can receive: rendered text + live/sr regions + tooltip/aria text.
const snap = () => page.evaluate(() => {
  const root = document.querySelector(".geo3d-xuong") || document.body;
  const attrs = [...root.querySelectorAll("[title],[aria-label],[aria-description]")].flatMap((e) => [e.getAttribute("title"), e.getAttribute("aria-label"), e.getAttribute("aria-description")]).filter(Boolean);
  return (root.textContent || "") + "\n" + attrs.join("\n");
});
const clickIf = async (loc) => { if (await loc.count() && await loc.first().isVisible() && await loc.first().isEnabled()) { await loc.first().click(); return true; } return false; };
const openMenuItem = async (group, name) => {
  await clickIf(page.locator(`[data-mo-nhom="${group}"]`));
  const it = page.locator(`[role^=menuitem]`, { hasText: name });
  const ok = await clickIf(it);
  await page.keyboard.press("Escape").catch(() => {});
  return ok;
};

const results = [];
for (const c of cases) {
  const r = { case_id: c.case_id, category: c.category, problem_text: c.problem_text, answers: c.answers, stages: {} };
  try {
    await page.locator(".composer-text").waitFor({ state: "visible", timeout: 15000 });
    await page.locator(".composer-text").fill(c.problem_text);
    const resp = page.waitForResponse((x) => x.url().includes("/api/analyze") && x.request().method() === "POST", { timeout: 30000 });
    await page.locator(".composer-send").click();
    const j = await (await resp).json();
    r.route_d_answers = j.route_d?.answers ?? null;
    await page.locator(".geo3d-xuong").waitFor({ state: "visible", timeout: 15000 });
    await page.waitForTimeout(400);
    r.initial_step = (await page.locator(".geo3d-buoc-so").textContent().catch(() => ""))?.trim();
    r.autoplay = (await page.locator('button[aria-label="Tạm dừng"]').count()) > 0;
    r.observations = await page.locator("[data-route-d-observation]").allTextContents();
    r.guidance = (await page.locator("[data-learner-guidance]").textContent().catch(() => "")) || "";
    r.stages.load = await snap();
    // step to the end
    let steps = "";
    for (let k = 0; k < 80; k++) { if (!(await clickIf(page.locator('button[aria-label="Bước sau"]')))) break; await page.waitForTimeout(60); steps += "\n" + await snap(); }
    r.final_step = (await page.locator(".geo3d-buoc-so").textContent().catch(() => ""))?.trim();
    r.observations_final = await page.locator("[data-route-d-observation]").allTextContents();
    r.stages.steps = steps;
    await clickIf(page.locator("button.geo3d-cac-buoc-mo"));
    r.steps_panel = (await page.locator("nav.geo3d-cac-buoc").textContent().catch(() => "")) || "";
    r.stages.steps_panel = await snap();
    await clickIf(page.locator("button.geo3d-cac-buoc-mo.la-mo"));
    r.has_show_all = await openMenuItem("hien-thi", "Hiện tất cả số đo");
    r.stages.show_all = await snap();
    if (r.has_show_all) await openMenuItem("hien-thi", "Hiện tất cả số đo");
    r.has_quantities = await openMenuItem("kham-pha", "Đại lượng");
    let insp = "";
    if (r.has_quantities) {
      r.quantity_panel = (await page.locator(".geo3d-ngan", { hasText: "Các đại lượng" }).textContent().catch(() => "")) || "";
      const ids = await page.locator("[data-quantity-id]").evaluateAll((es) => es.map((e) => e.getAttribute("data-quantity-id")));
      for (const id of ids) { await page.locator(`[data-quantity-id="${id}"]`).first().click().catch(() => {}); await page.waitForTimeout(40); insp += "\n" + await snap(); }
    }
    r.stages.quantities = insp;
    await openMenuItem("kham-pha", "Thành phần");
    await page.locator(".geo3d-tree details").evaluateAll((ds) => ds.forEach((d) => (d.open = true)));
    const treeIds = await page.locator("[data-tree-id]").evaluateAll((es) => es.map((e) => e.getAttribute("data-tree-id")));
    let tree = "";
    for (const id of treeIds) { await page.locator(`[data-tree-id="${id}"]`).first().click().catch(() => {}); await page.waitForTimeout(30); tree += "\n" + await snap(); }
    r.stages.tree_inspector = tree;
    r.tree_count = treeIds.length;
    await page.locator('[data-mo-bang="de"]').click().catch(() => {});
    r.de_panel = (await page.locator(".geo3d-de").textContent().catch(() => "")) || "";
    // Mode B (user-requested) — the rendered answer strings
    if (await clickIf(page.locator('[data-mo-bang="phan-tich"]'))) {
      r.mode_b_results = await page.locator('[data-semantic-role="REQUESTED_RESULT"] .geo3d-dai-luong-so').allTextContents();
    }
    await page.locator(".geo3d-quay-lai").click();
  } catch (e) {
    r.error = String(e).slice(0, 400);
    await page.goto(base, { waitUntil: "networkidle" }).catch(() => {});
  }
  results.push(r);
  process.stderr.write(`${c.case_id} ${r.error ? "ERR" : "ok"}\n`);
}
writeFileSync(OUT, JSON.stringify({ errors, analyzeCalls, cases: results.length, results }, null, 1));
await browser.close(); gw.close(); child.kill();
process.exit(0);
