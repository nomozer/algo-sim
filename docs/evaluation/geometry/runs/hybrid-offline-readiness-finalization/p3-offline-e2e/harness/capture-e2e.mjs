// HFOI P3 — real-browser offline E2E over the PRODUCT shell (hfoi-harness = main.tsx + one injected transport).
// usage: node capture-e2e.mjs <frontendDir> <harnessDist> <freshResponsesDir> <syntheticFixture> <samplesJson> <outDir>
// 0 provider calls: responses are the fresh output of the real preview endpoint with the frozen offline provider.
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, readdirSync } from "node:fs";
import { join, extname, resolve, basename } from "node:path";

const [fe, dist, fresh, synthetic, samplesPath, out] = process.argv.slice(2).map((p) => resolve(p));
const { chromium } = createRequire(join(fe, "package.json"))("playwright");
mkdirSync(out, { recursive: true });
const clone = (x) => JSON.parse(JSON.stringify(x));
const sha = (s) => createHash("sha256").update(s, "utf8").digest("hex");
const PROVEN = /đã\s*chứng\s*minh|được\s*chứng\s*minh|điều\s*phải\s*chứng\s*minh|đpcm|✓/i;
const LEAK = ["verification_gap", "insufficient_specification", "geometry_generation_failed", "refusal_cause", "reason_code",
  "OFFLINE_FIXTURE_ONLY", "hybrid_route_d_preview", "hybrid-route-d-preview", "TRUE_ON_CONFIGURATION", "UNVERIFIABLE"];

// ── responses served to the injected transport ────────────────────────────────────────────────────────────────
const RESP = {};
for (const f of readdirSync(fresh).filter((x) => x.endsWith(".json") && x !== "manifest.json")) {
  RESP[basename(f, ".json")] = JSON.parse(readFileSync(join(fresh, f), "utf8")).response;
}
RESP["synthetic-insufficient-specification-source"] = JSON.parse(readFileSync(synthetic, "utf8")).response;
const h07 = RESP["served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"];
const v1 = clone(h07); v1.route_d.answer_exact.f8.coef = "√3/2"; RESP["tampered-answer-coef"] = v1;
const v2 = clone(h07); v2.route_d.planner.goal_checks.f7.can_present_as_proven = true; RESP["tampered-proof-claim"] = v2;
const v3 = clone(RESP["served-H01_CUBE"]); v3.envelope.scene3d.chart_metric = [["1", "2", "0"], ["2", "1", "0"], ["0", "0", "1"]];
RESP["malformed-non-spd-metric"] = v3;

const samples = JSON.parse(readFileSync(samplesPath, "utf8"));
const sampleList = Array.isArray(samples) ? samples : samples.samples;
const llmOnly3D = sampleList.find((s) => s.id === "the-tich-chop").envelope;
const legacy2D = clone(llmOnly3D); delete legacy2D.scene3d;

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2" };
const sv = await new Promise((ok) => {
  const s = createServer((req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    if (path.startsWith("/responses/")) {
      const id = basename(path, ".json");
      res.writeHead(RESP[id] ? 200 : 404, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(RESP[id] ?? {}));
    }
    let p = join(dist, path);
    if (!existsSync(p) || statSync(p).isDirectory()) p = join(dist, "hfoi-harness.html");
    res.writeHead(200, { "Content-Type": MIME[extname(p)] ?? "application/octet-stream" });
    res.end(readFileSync(p));
  }).listen(0, "127.0.0.1", () => ok(s));
});
const origin = `http://127.0.0.1:${sv.address().port}`;

const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const results = [];
const apiSeen = new Set();
const captureImages = process.env.HFOI_CAPTURE_IMAGES === "1";

async function moTrang() {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message.slice(0, 200)}`));
  page.on("console", (m) => { if (m.type() === "error" && !/favicon|404/.test(m.text())) errors.push(m.text().slice(0, 200)); });
  page.on("request", (r) => { const u = new URL(r.url()); if (u.pathname.startsWith("/api/")) apiSeen.add(u.pathname); });
  await page.route("**/api/**", (route) => {
    const p = new URL(route.request().url()).pathname;
    if (p === "/api/health") return route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true,"hasKey":false,"cachedProblems":0}' });
    if (p === "/api/auth/me") return route.fulfill({ status: 200, contentType: "application/json", body: '{"user":null}' });
    return route.fulfill({ status: 404, contentType: "application/json", body: '{"error":"not mocked"}' });
  });
  await page.goto(`${origin}/hfoi-harness.html`);
  await page.waitForFunction(() => !!window.__HFOI__, null, { timeout: 30000 });
  return { ctx, page, errors };
}
const buocHien = async (page) => {
  const t = await page.locator(".geo3d-buoc-so").first().textContent();
  const m = /Bước (\d+)\/(\d+)/.exec(t ?? ""); return m ? [Number(m[1]), Number(m[2])] : [null, null];
};
async function denBuoc(page, k) {
  for (let g = 0; g < 60; g++) {
    const [i] = await buocHien(page); if (i === k) return;
    await page.getByRole("button", { name: i < k ? "Bước sau" : "Bước trước" }).first().click();
    await page.waitForTimeout(80);
  }
}
const chipsDom = (page) => page.evaluate(() => ({
  answers: [...document.querySelectorAll("[data-hybrid-answer]")].map((e) => e.textContent.trim()),
  observations: [...document.querySelectorAll("[data-route-d-observation]")].map((e) => e.textContent.trim()),
  lengthUnit: [...document.querySelectorAll("[data-length-unit]")].map((e) => e.textContent.trim()),
  canvases: document.querySelectorAll("canvas").length,
  text: document.body.innerText,
}));

try {
  // ── 12 served: walk every timeline step ────────────────────────────────────────────────────────────────────
  for (const id of Object.keys(RESP).filter((k) => k.startsWith("served-")).sort()) {
    const resp = RESP[id];
    const { ctx, page, errors } = await moTrang();
    const nap = await page.evaluate((u) => window.__HFOI__.nap(u), `/responses/${id}.json`);
    const rec = { id, kind: "served", response_sha256: sha(JSON.stringify(resp)), nap, steps: [], errors };
    if (nap.adapter === "ACCEPTED" && nap.active) {
      await page.waitForSelector(".geo3d-buoc-so", { timeout: 30000 });
      const pause = page.getByRole("button", { name: "Tạm dừng" }); if (await pause.count()) await pause.first().click();
      // Explicit consent before checking answer/timeline integrity; arriving at the last step never grants it.
      const disclosure = page.getByRole("button", { name: "Xem đáp án", exact: true });
      rec.initial_answers_hidden = (await chipsDom(page)).answers.length === 0;
      if (await disclosure.count()) await disclosure.click();
      const [, n] = await buocHien(page);
      const events = resp.envelope.scene3d.events;
      const measureStep = Object.fromEntries(Object.keys(resp.route_d.answers).map((k) =>
        [k, events.find((e) => e.object === `kq_${k}`)?.step_index]));
      const nObs = Object.keys(resp.route_d.planner.goal_checks ?? {}).length + Object.keys(resp.route_d.planner.negated_checks ?? {}).length;
      const groups = await page.evaluate((sc) => window.__HFOI__.buoc(sc), resp.envelope.scene3d);
      rec.ui_steps_match_groups = groups.length === n;
      const lastEvent = Math.max(...events.map((e) => e.step_index));
      for (let k = 1; k <= n; k++) {
        await denBuoc(page, k); await page.waitForTimeout(150);
        const d = await chipsDom(page);
        const stepIndex = groups[k - 1]?.anchor ?? -1;          // event index this UI step represents
        const expAnswers = Object.values(measureStep).filter((s) => s != null && s <= stepIndex).length;
        const expObs = stepIndex >= lastEvent ? nObs : 0;
        rec.steps.push({ step: k, of: n, answers: d.answers, observations: d.observations.length, lengthUnit: d.lengthUnit,
          ok_answers: d.answers.length === expAnswers, ok_observations: d.observations.length === expObs,
          ok_length_unit: (d.lengthUnit.length > 0) === Boolean(resp.envelope.scene3d.length_unit),
          proven_wording: PROVEN.test(d.text), leaks: LEAK.filter((x) => d.text.includes(x)) });
        if (captureImages && (k === n || (k === 1 && id.includes("H07")))) await page.screenshot({ path: join(out, `${id}__step${k}.png`) });
      }
    }
    rec.pass = nap.adapter === "ACCEPTED" && nap.active && rec.steps.length > 0 && errors.length === 0 && rec.ui_steps_match_groups
      && rec.steps.every((s) => s.ok_answers && s.ok_observations && s.ok_length_unit && !s.proven_wording && s.leaks.length === 0);
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} ${id} steps=${rec.steps.length}`); await ctx.close();
  }

  // ── refusals (25 + synthetic SOURCE): visible notice, structured wording, no leak ─────────────────────────
  for (const id of Object.keys(RESP).filter((k) => k.startsWith("refusal-") || k.startsWith("synthetic-")).sort()) {
    const env = RESP[id].envelope;
    const { ctx, page, errors } = await moTrang();
    const nap = await page.evaluate((u) => window.__HFOI__.nap(u), `/responses/${id}.json`);
    await page.waitForSelector(".refusal-facts", { timeout: 30000 });
    const dom = await page.evaluate(() => {
      const card = document.querySelector(".refusal-facts")?.closest(".card");
      const dd = [...(card?.querySelectorAll(".refusal-facts dd") ?? [])].map((e) => e.textContent.trim());
      return { eyebrow: card?.querySelector(".eyebrow")?.textContent.trim(), stage: dd[0], kind: dd[1],
        hint: card?.querySelector(".notes")?.textContent.trim() ?? null, canvases: document.querySelectorAll("canvas").length,
        text: document.body.innerText };
    });
    const exp = env.failure_category === "verification_gap"
      ? { eyebrow: "CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG" }
      : env.failure_category === "insufficient_specification"
        ? { eyebrow: env.refusal_cause === "SOURCE" ? "CHƯA ĐỦ DỮ KIỆN" : "CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN" } : {};
    const rec = { id, kind: "refusal", failure_category: env.failure_category, refusal_cause: env.refusal_cause, nap,
      dom: { ...dom, text: undefined }, errors,
      ok_eyebrow: !exp.eyebrow || dom.eyebrow === exp.eyebrow, ok_no_scene: dom.canvases === 0 && !nap.active,
      ok_not_ran_claim: env.failure_category !== "verification_gap" || !/chạy được|đã dựng/i.test(dom.kind ?? ""),
      ok_stage_not_old: !String(dom.stage).includes("phản hồi cũ"),
      ok_source_hint_only_if_source: env.refusal_cause === "SOURCE" || !/Bổ sung dữ liệu còn thiếu vào đề|sửa đề/.test(dom.hint ?? ""),
      leaks: LEAK.filter((x) => dom.text.includes(x)).concat(dom.text.includes(env.reason_code) ? [env.reason_code] : []) };
    rec.pass = rec.ok_eyebrow && rec.ok_no_scene && rec.ok_not_ran_claim && rec.ok_stage_not_old
      && rec.ok_source_hint_only_if_source && rec.leaks.length === 0 && errors.length === 0;
    if (captureImages && ["refusal-source-object-mismatch", "refusal-missing-ambiguous", "synthetic-insufficient-specification-source"].includes(id)) {
      await page.screenshot({ path: join(out, `${id}.png`) });
    }
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} ${id} eyebrow="${dom.eyebrow}" kind="${dom.kind}"`); await ctx.close();
  }

  // ── boundary rejections: gate responses and tampered wrappers never reach the store ─────────────────────────
  for (const id of [...Object.keys(RESP).filter((k) => k.startsWith("gate-")).sort(), "tampered-answer-coef", "tampered-proof-claim"]) {
    const { ctx, page, errors } = await moTrang();
    const nap = await page.evaluate((u) => window.__HFOI__.nap(u), `/responses/${id}.json`);
    const d = await chipsDom(page);
    const rec = { id, kind: "boundary-reject", nap, errors, pass: nap.adapter === "REJECTED" && !nap.active && d.canvases === 0 };
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} ${id} ${nap.reason ?? ""}`); await ctx.close();
  }

  // ── malformed metric: adapter accepts the wrapper, module boundary rejects; no 2D fallback ─────────────────
  {
    const { ctx, page, errors } = await moTrang();
    const nap = await page.evaluate((u) => window.__HFOI__.nap(u), "/responses/malformed-non-spd-metric.json");
    await page.waitForTimeout(500);
    const d = await chipsDom(page);
    const rec = { id: "malformed-non-spd-metric", kind: "fail-closed", nap, errors, canvases: d.canvases,
      pass: !nap.active && Boolean(nap.analysisError) && d.canvases === 0 && !document_has_2d(d.text) };
    if (captureImages) await page.screenshot({ path: join(out, "malformed-non-spd-metric.png") });
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} malformed-non-spd-metric`); await ctx.close();
  }

  // ── a refusal after a served scene leaves no previously accepted scene ────────────────────────────────────
  {
    const { ctx, page, errors } = await moTrang();
    const a = await page.evaluate(() => window.__HFOI__.nap("/responses/served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json"));
    await page.waitForSelector("canvas", { timeout: 30000 });
    const b = await page.evaluate(() => window.__HFOI__.nap("/responses/refusal-source-object-mismatch.json"));
    await page.waitForSelector(".refusal-facts", { timeout: 30000 });
    const d = await chipsDom(page);
    const rec = { id: "served-then-refusal", kind: "lifecycle", first: a, second: b, errors, canvases: d.canvases,
      pass: a.active && !b.active && b.unsupported && d.canvases === 0 && d.answers.length === 0 && d.observations.length === 0 };
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} served-then-refusal`); await ctx.close();
  }

  // ── LLM_ONLY compatibility: 3D sample unchanged (no Hybrid chips, no scale note), legacy 2D still opens ────
  for (const [id, env] of [["llm-only-3d-sample", llmOnly3D], ["legacy-2d-sample", legacy2D]]) {
    const { ctx, page, errors } = await moTrang();
    const st = await page.evaluate((e) => window.__HFOI__.napEnvelope(e), env);
    await page.waitForTimeout(1500);
    const d = await chipsDom(page);
    const rec = { id, kind: "llm-only-compat", state: st, errors, canvases: d.canvases,
      pass: st.active && errors.length === 0 && d.answers.length === 0 && d.observations.length === 0
        && !d.text.includes("trên hình dựng") && (id === "legacy-2d-sample" ? d.canvases === 0 : d.canvases > 0) };
    if (captureImages) await page.screenshot({ path: join(out, `${id}.png`) });
    results.push(rec); console.log(`${rec.pass ? "PASS" : "FAIL"} ${id} canvases=${d.canvases}`); await ctx.close();
  }
} finally {
  await browser.close();
  sv.close();
}

function document_has_2d(text) { return /Bước \d+\/\d+/.test(text); }

const forbidden = [...apiSeen].filter((p) => p === "/api/preview/hybrid" || p === "/api/analyze");
const summary = {
  schema: "HFOI_OFFLINE_E2E/1", provider_calls: 0, renderer: "chromium headless, ANGLE SwiftShader",
  injected_segment: "transport of the preview response (no product caller exists); everything else is the product shell",
  api_paths_seen: [...apiSeen].sort(), forbidden_calls: forbidden,
  total: results.length, pass: results.filter((r) => r.pass).length, results,
};
summary.pass_all = summary.pass === summary.total && forbidden.length === 0;
writeFileSync(join(out, "e2e-receipt.json"), JSON.stringify(summary, null, 1));
console.log(`E2E ${summary.pass}/${summary.total} forbidden=${forbidden.length}`);
process.exit(summary.pass_all ? 0 : 1);
