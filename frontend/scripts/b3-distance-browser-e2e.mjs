/**
 * B3 distance /4 browser acceptance (run `b3-distance-browser-e2e`). Offline authored TypedFacts → real wrapper → the
 * product consumer (`docPhanHoiHybrid` → store), as `check-adapter4-browser.mjs` loads its fixtures; that checker is
 * section-centric, so distance scenes get their own checks here:
 *   served  — canvas renders; the perpendicular witness the engine certified is a rendered object; Mode A (analysis
 *             closed) shows no final answer; Mode B shows it exactly once, and its value squared equals the
 *             closed-form oracle written in the fixture (not engine output); the inspector of the selected answer adds
 *             no number absent from the problem text and the engine answer; no internal name; no horizontal overflow.
 *   refused — no scene, the learner reason is shown, the refusal code is not.
 * Usage: node scripts/b3-distance-browser-e2e.mjs --url http://127.0.0.1:3142 --fixtures f.json --out <fresh dir>
 */
import { chromium } from "playwright";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";

const arg = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : undefined; };
const URL_ = arg("--url"), OUT = arg("--out"), FX = arg("--fixtures");
if (!URL_ || !OUT || !FX || existsSync(OUT)) throw Error("--url, --fixtures and a fresh --out are required");
mkdirSync(OUT, { recursive: true });
const bytes = readFileSync(FX), data = JSON.parse(bytes);
const sha = (b) => createHash("sha256").update(b).digest("hex");

/** Squared value of an exact display coefficient "p", "p/q", "p√r", "p√r/q", "√r/q" (independent reader). */
function squareOf(coef) {
  const m = String(coef).replace(/\s/g, "").match(/^(\d+)?(?:√(\d+))?(?:\/(\d+))?$/);
  if (!m || (!m[1] && !m[2])) return null;
  const p = BigInt(m[1] ?? 1), r = BigInt(m[2] ?? 1), q = BigInt(m[3] ?? 1);
  return [p * p * r, q * q];
}
const frac = (s) => { const [a, b] = String(s).split("/"); return [BigInt(a), BigInt(b ?? 1)]; };
const eqFrac = ([a, b], [c, d]) => a * d === b * c;
const numbersIn = (t) => (t.match(/\d+(?:[.,]\d+)?/g) ?? []).map((x) => x.replace(",", "."));

const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const rows = [], errors = [], forbidden = [];
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const fx of data.fixtures) {
      const ctx = await browser.newContext({ viewport });
      await ctx.route("**/*", (r) => {
        const u = new URL(r.request().url());
        if (u.origin === URL_ && u.pathname === "/api/health") return r.fulfill({ json: { status: "ok", allow_live_ai: false } });
        if (u.origin === URL_ && u.pathname.startsWith("/api/")) return r.fulfill({ json: null });
        if (u.origin === URL_) return r.continue();
        forbidden.push(u.href); return r.abort();
      });
      const page = await ctx.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (e) => errors.push({ id: fx.id, message: e.message }));
      page.on("console", (m) => { if (m.type() === "error") errors.push({ id: fx.id, message: m.text() }); });
      await page.goto(URL_);
      const row = { id: fx.id, viewport: viewport.width, expected: fx.expected, checks: {} };
      rows.push(row);
      const loaded = await page.evaluate(async (fx) => {
        const a = await import("/src/simulations/domains/geometry/hybrid-preview-adapter.ts");
        const { useAppStore } = await import("/src/state/store.ts");
        const r = a.docPhanHoiHybrid(fx);
        if (!r.ok) return r;
        if (r.envelope.status === "ok") useAppStore.getState().loadEnvelope(r.envelope);
        else useAppStore.getState().loadUnsupported(r.envelope);
        return { ok: true, status: r.envelope.status, active: !!useAppStore.getState().active };
      }, fx);
      row.checks.consumed = loaded.ok === true;
      const text0 = async () => page.locator("body").innerText();
      if (fx.expected === "REFUSE") {
        await page.waitForTimeout(400);
        const t = await text0();
        row.checks.no_scene = (await page.locator(".geo3d-canvas canvas").count()) === 0 && !loaded.active;
        row.checks.reason_shown = t.includes(fx.envelope.learner_reason);
        row.checks.code_hidden = !t.includes(fx.route_d.refusal.code);
        row.checks.no_answer = !t.includes("Kết quả toán học");
        row.pass = Object.values(row.checks).every(Boolean);
        console.log(`${fx.id} ${viewport.width} ${row.pass ? "PASS" : "FAIL"} ${JSON.stringify(row.checks)}`);
        await ctx.close(); continue;
      }
      if (!loaded.ok || loaded.status !== "ok") {                   // the consumer rejected a served response
        row.consumer = loaded; row.pass = false;
        console.log(`${fx.id} ${viewport.width} FAIL consumer ${JSON.stringify(loaded).slice(0, 200)}`);
        await ctx.close(); continue;
      }
      await page.locator(".geo3d-canvas canvas").waitFor();
      await page.locator(".geo3d-scrub input").evaluate((el) => {
        const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        set.call(el, el.max); el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true }));
      });
      await page.waitForTimeout(700);
      const [qid] = Object.keys(fx.route_d.answers), kq = `kq_${qid}`;
      const coef = fx.route_d.answer_exact[qid].coef;
      const scene = fx.envelope.scene3d;
      // Certified perpendicularity reaches the scene either on a segment (`perpendicular_witness`, e.g. a right
      // prism's lateral edge) or on the answer itself (`annotation.witness`: from → foot on the plane).
      const segWitness = scene.objects.filter((o) => o.perpendicular_witness?.status === "ENGINE_VERIFIED").map((o) => o.id);
      const annWitness = scene.objects.find((o) => o.id === kq)?.annotation?.witness ?? null;
      const rendered = await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []);
      row.witness = { segments: segWitness, on_answer: annWitness ? { from: annWitness.from, foot: annWitness.foot, on: annWitness.on } : null };
      // Mode A: analysis closed — no answer surface anywhere (panel, canvas measurement labels).
      row.checks.mode_a_hidden = (await page.locator("[data-math-analysis-panel]").count()) === 0
        && !(await page.locator(".geo3d-so-do").allInnerTexts()).some((t) => t.replace(/\s/g, "").includes(coef.replace(/\s/g, "")));
      const shotA = await page.screenshot(); writeFileSync(join(OUT, `${fx.id}-${viewport.width}-mode-a.png`), shotA);
      // Mode B
      await page.getByRole("button", { name: "Phân tích toán học", exact: true }).click();
      const item = page.locator(`[data-analysis-item="${kq}"]`);
      await item.waitFor();
      const shown = (await item.locator(".geo3d-dai-luong-so").innerText()).replace(/\s/g, "");
      const rhs = shown.includes("=") ? shown.slice(shown.lastIndexOf("=") + 1) : shown;
      const sq = squareOf(rhs);
      row.shown = shown;
      const places = async () => {
        const has = (ts) => ts.filter((t) => t.replace(/\s/g, "").includes(shown)).length;
        return { analysis: has(await page.locator("[data-math-analysis-panel] .geo3d-dai-luong-so").allInnerTexts()),
          inspector: has(await page.locator(".geo3d-soi").allInnerTexts()), canvas_label: has(await page.locator(".geo3d-so-do").allInnerTexts()) };
      };
      row.places_after_opening = await places();
      row.checks.mode_b_once = (await page.locator(`[data-analysis-item="${kq}"]`).count()) === 1
        && Object.values(row.places_after_opening).reduce((s, n) => s + n, 0) === 1;
      row.checks.value_matches_oracle = sq !== null && eqFrac(sq, frac(fx.oracle_value_squared));
      row.checks.engine_binding = scene.objects.find((o) => o.id === kq)?.value?.replace(/\s/g, "") === coef.replace(/\s/g, "");
      await item.locator("button").click();
      await page.waitForTimeout(500);
      row.places_after_selecting = await places();          // reported for the Owner; not a pass/fail criterion here
      const witnessIds = await page.evaluate(() => window.__geo3d_witness_ids ?? []);
      row.witness.rendered_ids = witnessIds;
      // A witness counts only when it certifies THIS answer: on the answer itself, or a segment from the measured point
      // whose foot lies on the measured plane (provenance args). Other right-angle marks (e.g. lateral edges for a
      // skew-line distance) do not. Required to be drawn when provided; its absence is reported, not hidden.
      const prov = fx.route_d.source_provenance.find((x) => x.id === qid);
      const idOf = (label) => scene.objects.find((o) => (o.notation ?? o.label ?? "").replace(/[′’]/g, "'") === label.replace(/[′’]/g, "'"))?.id;
      const tiedSeg = prov?.args?.point && prov?.args?.plane
        ? scene.objects.filter((o) => o.perpendicular_witness?.status === "ENGINE_VERIFIED"
            && o.perpendicular_witness.from === idOf(prov.args.point)
            && [...(o.perpendicular_witness.plane_vertex_ids ?? [])].sort().join() === prov.args.plane.map(idOf).sort().join()).map((o) => o.id)
        : [];
      row.witness.provided_for_answer = annWitness !== null || tiedSeg.length > 0;
      row.witness.tied_segments = tiedSeg;
      row.checks.witness_rendered = !row.witness.provided_for_answer
        || (annWitness !== null && witnessIds.includes(kq)) || tiedSeg.some((id) => rendered.includes(id));
      const shotB = await page.screenshot(); writeFileSync(join(OUT, `${fx.id}-${viewport.width}-mode-b-selected.png`), shotB);
      const inspector = (await page.locator(".geo3d-soi").count()) ? await page.locator(".geo3d-soi").innerText() : "";
      const allowed = new Set([...numbersIn(fx.problem_text), ...numbersIn(coef)]);
      row.inspector_numbers = numbersIn(inspector);
      row.checks.inspector_no_new_math = row.inspector_numbers.every((n) => allowed.has(n));
      const t = await text0();
      row.checks.no_internal_name = !/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b|::/u.test(t);
      row.checks.no_overflow = (await page.evaluate(() => document.documentElement.scrollWidth)) <= viewport.width + 1;
      row.images = { mode_a: sha(shotA), mode_b: sha(shotB) };
      row.pass = Object.values(row.checks).every(Boolean);
      console.log(`${fx.id} ${viewport.width} ${row.pass ? "PASS" : "FAIL"} shown=${shown} ${JSON.stringify(row.checks)}`);
      await ctx.close();
    }
  }
} finally { await browser.close(); }
const status = rows.every((r) => r.pass) && !errors.length && !forbidden.length ? "B3_DISTANCE_BROWSER_PASS" : "FAIL";
writeFileSync(join(OUT, "receipt.json"), JSON.stringify({ status, fixtures_sha256: sha(bytes), harness_sha256: sha(readFileSync(import.meta.filename)),
  classification: data.classification, provider_calls: 0, browser: "Chrome headless / SwiftShader", url: URL_,
  human_visual_review: "NOT_APPROVED", rows, errors, forbidden }, null, 2) + "\n");
console.log(JSON.stringify({ status, rows: rows.length, errors: errors.length, forbidden: forbidden.length }));
process.exitCode = status === "FAIL" ? 1 : 0;
