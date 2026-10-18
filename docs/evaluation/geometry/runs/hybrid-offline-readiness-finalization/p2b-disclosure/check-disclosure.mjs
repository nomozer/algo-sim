// Offline real-browser disclosure tests. Usage: node check-disclosure.mjs <frontend> <harnessDist> <repo> <receipt.json>
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFileSync, writeFileSync, existsSync, statSync } from "node:fs";
import { resolve, join, extname } from "node:path";
import { createHash } from "node:crypto";
const [fe, dist, repo, out] = process.argv.slice(2).map((p) => resolve(p));
const { chromium } = createRequire(join(fe, "package.json"))("playwright");
const fx = join(repo, "docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2");
const json = (p) => JSON.parse(readFileSync(p, "utf8"));
const ids = ["served-H01_CUBE", "served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS", "served-H02_CUBOID_DISTANCE"];
const responses = Object.fromEntries(ids.concat("refusal-missing-ambiguous").map((id) => [id, json(join(fx, `${id}.json`)).response]));
const samples = json(join(fe, "src/data/geometry-samples.json"));
const sample = (Array.isArray(samples) ? samples : samples.samples).find((s) => s.id === "the-tich-chop").envelope;
const server = createServer((req, res) => {
  const path = new URL(req.url, "http://local").pathname;
  if (path.startsWith("/responses/")) {
    res.setHeader("Content-Type", "application/json");
    return res.end(JSON.stringify(responses[path.slice(11).replace(/\.json$/, "")]));
  }
  let p = join(dist, path);
  if (!existsSync(p) || statSync(p).isDirectory()) p = join(dist, "hfoi-harness.html");
  res.setHeader("Content-Type", ({ ".html": "text/html", ".js": "text/javascript", ".css": "text/css" })[extname(p)] ?? "application/octet-stream");
  res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.setDefaultTimeout(5000);
const errors = [], forbiddenRequests = [], results = [];
page.on("pageerror", (e) => errors.push(e.message.slice(0, 160)));
await page.route("**/*", (route) => {
  const u = new URL(route.request().url());
  if (u.hostname !== "127.0.0.1") { forbiddenRequests.push(u.origin); return route.abort(); }
  if (!u.pathname.startsWith("/api/")) return route.continue();
  if (["/api/analyze", "/api/preview/hybrid"].includes(u.pathname)) forbiddenRequests.push(u.pathname);
  return route.fulfill({ contentType: "application/json", body: u.pathname === "/api/health"
    ? '{"ok":true,"hasKey":false,"cachedProblems":0}' : '{"user":null}' });
});
const load = async (id) => {
  const r = await page.evaluate((id) => window.__HFOI__.nap(`/responses/${id}.json`), id);
  assert.equal(r.adapter, "ACCEPTED");
  await page.waitForSelector(".geo3d-buoc-so");
  const pause = page.getByRole("button", { name: "Tạm dừng", exact: true });
  if (await pause.count()) await pause.click();
};
const finalStep = async () => {
  for (let i = 0; i < 60; i++) {
    const next = page.getByRole("button", { name: "Bước sau", exact: true });
    if (await next.isDisabled()) return;
    await next.click();
  }
  assert.fail("timeline did not terminate");
};
const noAnswers = async () => assert.equal(await page.locator("[data-hybrid-answer]").count(), 0);
const test = async (name, fn) => {
  try { await fn(); results.push({ name, pass: true }); }
  catch (e) { results.push({ name, pass: false, reason: e.message.slice(0, 280) }); }
  console.log(`${results.at(-1).pass ? "PASS" : "FAIL"} ${name}`);
};
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/hfoi-harness.html`);
  await page.waitForFunction(() => !!window.__HFOI__);
  for (const id of ids) {
    await test(`${id}: hidden initially, final, orbit and reset; keyboard reveal/hide; no stale answers`, async () => {
      await load(id); await noAnswers();
      await finalStep(); await noAnswers();
      const button = page.getByRole("button", { name: "Xem đáp án", exact: true });
      assert.equal(await button.count(), 1);
      assert.equal(await button.getAttribute("aria-expanded"), "false");
      assert.ok(await page.locator("[data-length-unit]").isVisible());
      const canvas = page.locator("canvas").first();
      const box = await canvas.boundingBox();
      await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
      await page.mouse.down(); await page.mouse.move(box.x + box.width * 0.6, box.y + box.height * 0.6, { steps: 8 }); await page.mouse.up();
      await page.getByRole("button", { name: "Xem lại toàn hình", exact: true }).click();
      await noAnswers();
      await button.focus(); await page.keyboard.press("Enter");
      const answers = responses[id].route_d.answers;
      assert.equal(await page.locator("[data-hybrid-answer]").count(), Object.keys(answers).length);
      for (const [key, symbolic] of Object.entries(answers)) {
        assert.ok((await page.locator(`[data-hybrid-answer="kq_${key}"]`).innerText()).includes(symbolic.split("=").at(-1).trim()));
      }
      await page.getByRole("button", { name: "Ẩn đáp án", exact: true }).focus();
      await page.keyboard.press("Space"); await noAnswers();
      // Selection and show-all cannot reveal a duplicate result after the answers were hidden.
      await page.getByRole("button", { name: "Khám phá", exact: true }).click();
      await page.getByRole("menuitemcheckbox", { name: "Đại lượng", exact: true }).click();
      const q = responses[id].envelope.scene3d.objects.find((o) =>
        o.annotation?.witness && Object.keys(answers).some((k) => o.id === `kq_${k}`))?.id ?? `kq_${Object.keys(answers)[0]}`;
      await page.locator(`[data-quantity-id="${q}"]`).click();
      assert.equal(await page.locator(`[data-value-entity="${q}"], [data-formula-entity="${q}"]`).count(), 0);
      assert.equal(await page.locator(`[data-ann-id="${q}"]`).count(), 0);
      if (responses[id].envelope.scene3d.objects.find((o) => o.id === q)?.annotation?.witness) {
        assert.ok(await page.evaluate((q) => window.__geo3d_witness_ids?.includes(q), q), "hidden answer must preserve certified distance witness");
      }
      await noAnswers();
      // Same problem re-analysis is a new envelope too, not just a different title.
      await page.getByRole("button", { name: "Xem đáp án", exact: true }).click();
      await load(id); await finalStep(); await noAnswers();
      await page.getByRole("button", { name: "Xem đáp án", exact: true }).click();
      await load(ids.find((x) => x !== id)); await finalStep(); await noAnswers();
    });
  }
  await test("replacement refusal removes stale answer UI; LLM_ONLY and legacy still render", async () => {
    await load(ids[0]); await finalStep();
    await page.getByRole("button", { name: "Xem đáp án", exact: true }).click();
    await page.evaluate(() => window.__HFOI__.nap("/responses/refusal-missing-ambiguous.json"));
    await page.waitForSelector(".refusal-facts"); await noAnswers();
    assert.equal(await page.getByRole("button", { name: "Ẩn đáp án", exact: true }).count(), 0);
    await page.evaluate((e) => window.__HFOI__.napEnvelope(e), sample);
    await page.waitForSelector("canvas"); await noAnswers();
    assert.equal(await page.getByRole("button", { name: "Xem đáp án", exact: true }).count(), 0);
    const legacy = structuredClone(sample); delete legacy.scene3d;
    await page.evaluate((e) => window.__HFOI__.napEnvelope(e), legacy);
    await page.waitForTimeout(200);
    assert.equal(await page.locator("canvas").count(), 0);
  });
} finally {
  await browser.close(); await new Promise((r) => server.close(r));
}
const receipt = { schema: "PEDAGOGICAL_DISCLOSURE_BROWSER/1", date: new Date().toISOString(),
  fixture_sha256: Object.fromEntries(ids.map((id) => [id, createHash("sha256").update(JSON.stringify(responses[id])).digest("hex")])),
  results, errors, forbiddenRequests, pass: results.every((r) => r.pass) && errors.length === 0 && forbiddenRequests.length === 0 };
writeFileSync(out, JSON.stringify(receipt, null, 2) + "\n");
process.exitCode = receipt.pass ? 0 : 1;
