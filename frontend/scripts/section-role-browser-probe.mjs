/**
 * Browser probe for the PROPOSED role-aware section check (`section-role-oracle.mjs`). Not part of any test tier and
 * not an official-suite oracle. Loads each envelope in real Chrome through the app store, selects the target from the
 * «Phân tích toán học» panel like a learner, screenshots the canvas and scores it; then repeats with injected faults.
 * Faults are applied at page start (three.js caches uniform values, so a mid-session switch would not re-upload):
 *   boundary_terracotta — every cobalt colour becomes terracotta (selected boundary lost; polygon edges are fat lines,
 *                         circle/ellipse rims are meshes — both are hit; fills are terracotta, so untouched)
 *   boundary_magenta    — every cobalt colour becomes magenta (wrong boundary colour)
 *   fill_grey           — terracotta colours of MESH programs become grey (semantic fill altered)
 *   fill_hidden         — the section fill is switched off through the existing harness hook
 *   wrong_object        — after selecting the target, the learner clicks another point instead
 * Usage: node scripts/section-role-browser-probe.mjs --url http://127.0.0.1:3142 --cases cases.json --out <dir>
 */
import { chromium } from "playwright";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { docPNG } from "./png-pixels.mjs";
import { LOP_PHU_KHUNG } from "./compiler-scene-replay-lib.mjs";
import { assessSectionRole, project, sectionBoundaryWorld } from "./section-role-oracle.mjs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const URL_ = arg("--url", "http://127.0.0.1:3142");
const OUT = arg("--out");
const CASES = JSON.parse(readFileSync(arg("--cases"), "utf8"));
const FAULTS = (arg("--faults", "none,boundary_terracotta,boundary_magenta,fill_grey,fill_hidden,wrong_object")).split(",");
const CAMERAS = arg("--cameras", "default").split(",");
mkdirSync(OUT, { recursive: true });

function initFault(fault) {
  const lineProg = new WeakSet(), locProg = new WeakMap();
  for (const P of [WebGLRenderingContext.prototype, WebGL2RenderingContext.prototype]) {
    const gul = P.getUniformLocation;
    P.getUniformLocation = function (prog, name) {
      const loc = gul.call(this, prog, name);
      if (name === "linewidth") lineProg.add(prog);
      if (loc) locProg.set(loc, prog);
      return loc;
    };
    const swap = (loc, r, g, b) => {
      const line = lineProg.has(locProg.get(loc));
      const cobalt = b > 0.5 && g < 0.3 && r < 0.1, terracotta = r > 0.45 && g < 0.2 && b < 0.08;
      if (fault === "boundary_terracotta" && cobalt) return [0.578, 0.102, 0.032];
      if (fault === "boundary_magenta" && cobalt) return [1, 0, 1];
      if (fault === "boundary_wrong_blue" && cobalt) return [0, 0.177888, 0.730461];
      if (fault === "fill_grey" && !line && terracotta) return [0.3, 0.3, 0.3];
      if (fault === "fill_wrong_orange" && !line && terracotta) return [0.964686, 0.287441, 0.045186];
      return null;
    };
    const u3f = P.uniform3f, u3fv = P.uniform3fv;
    P.uniform3f = function (loc, r, g, b) { const s = swap(loc, r, g, b); return s ? u3f.call(this, loc, ...s) : u3f.call(this, loc, r, g, b); };
    P.uniform3fv = function (loc, v, ...rest) {
      const s = v && v.length === 3 ? swap(loc, v[0], v[1], v[2]) : null;
      return s ? u3fv.call(this, loc, s) : u3fv.call(this, loc, v, ...rest);
    };
  }
}

const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const rows = [];
const failures = [];
try {
  for (const c of CASES) {
    const env = JSON.parse(readFileSync(c.envelope_file, "utf8"));
    const envelope = c.pick ? c.pick.split(".").reduce((o, k) => (/^\d+$/.test(k) ? o[Number(k)] : o[k]), env) : env;
    for (const width of [1440, 390]) {
      for (const cameraName of CAMERAS) for (const fault of FAULTS) {
        const ctx = await browser.newContext({ viewport: { width, height: width < 600 ? 844 : 900 }, deviceScaleFactor: width < 600 ? 2 : 1 });
        await ctx.route("**/*", (r) => {
          const u = new URL(r.request().url());
          if (u.hostname !== "127.0.0.1") return r.abort();
          if (u.pathname.startsWith("/api/")) return r.fulfill({ json: u.pathname === "/api/health" ? { ok: true, hasKey: false } : { user: null } });
          return r.continue();
        });
        await ctx.addInitScript(initFault, fault);
        const p = await ctx.newPage();
        const errors = [];
        p.on("pageerror", (e) => errors.push(e.message.split("\n")[0]));
        await p.goto(URL_);
        await p.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, envelope);
        await p.locator(".geo3d-canvas canvas").waitFor();
        await p.locator(".geo3d-scrub input").evaluate((el) => {
          const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
          set.call(el, el.max); el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true }));
        });
        await p.getByRole("button", { name: "Phân tích toán học", exact: true }).click();
        await p.locator(`[data-analysis-item="${c.item}"] button`).click();
        await p.waitForFunction((id) => window.__geo3d_selected_id === id, c.item, { timeout: 10000 });
        await p.waitForTimeout(700);
        const scene = await p.evaluate(() => window.__ALGO_SIM_STORE__.getState().active.envelope.scene3d);
        const box = await p.locator(".geo3d-canvas canvas").boundingBox();
        if (cameraName !== "default") {
          const dx = cameraName === "quarter" ? 0.25 : cameraName === "half" ? 0.5 : 0;
          const dy = cameraName === "high" ? 0.16 : cameraName === "low" ? -0.16 : 0;
          await p.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
          await p.mouse.down();
          await p.mouse.move(box.x + box.width * 0.5 + box.height * dx, box.y + box.height * (0.5 + dy), { steps: 16 });
          await p.mouse.up();
          await p.mouse.move(0, 0);
          await p.waitForTimeout(700);
        }
        if (fault === "wrong_object") {
          const cam0 = await p.evaluate(() => window.__geo3d_camera_snapshot);
          const pt = scene.objects.find((o) => o.id === c.wrong_point);
          const q = project(pt.xyz.map((s) => { const [a, b] = String(s).split("/"); return Number(a) / (b ? Number(b) : 1); }), cam0, { w: box.width, h: box.height });
          await p.mouse.click(box.x + q.x, box.y + q.y);
          await p.waitForTimeout(700);
        }
        if (fault === "fill_hidden") {
          await p.evaluate(() => window.__geo3d_set_section_fill_visible(false));
          await p.waitForTimeout(200);
        }
        await p.waitForFunction(() => {
          const value = JSON.stringify(window.__geo3d_camera_snapshot);
          window.__roleStableCount = window.__roleLastCamera === value ? (window.__roleStableCount ?? 0) + 1 : 0;
          window.__roleLastCamera = value;
          return window.__roleStableCount >= 4;
        }, null, { polling: 'raf', timeout: 15000 });
        const selected = await p.evaluate(() => window.__geo3d_selected_id ?? null);
        const overlays = await p.evaluate(([sel, b]) => [...document.querySelectorAll(sel)].filter((e) => e.offsetParent !== null)
          .map((e) => { const r = e.getBoundingClientRect(); return { x: r.x - b.x, y: r.y - b.y, w: r.width, h: r.height }; }), [LOP_PHU_KHUNG, box]);
        const cameraBefore = await p.evaluate(() => window.__geo3d_camera_snapshot);
        const png = await p.locator(".geo3d-canvas canvas").screenshot();
        const file = `${c.id}-${width}-${cameraName}-${fault}.png`;
        writeFileSync(join(OUT, file), png);
        const img = docPNG(png);
        const cam = await p.evaluate(() => window.__geo3d_camera_snapshot);
        if (JSON.stringify(cameraBefore) !== JSON.stringify(cam)) throw Error('CAMERA_CHANGED_DURING_CAPTURE');
        const world = sectionBoundaryWorld(scene, c.section, cam);
        const edges = (world ?? []).map((s) => ({ a: project(s.a, cam, { w: box.width, h: box.height }), b: project(s.b, cam, { w: box.width, h: box.height }), hidden: s.hidden, curve: Boolean(s.curve) }));
        const otherBoundaries = scene.objects.filter(o => o.id !== c.section && ["section", "circle3", "ellipse3"].includes(o.type))
          .map(o => sectionBoundaryWorld(scene, o.id, cam)).filter(Boolean)
          .map(boundary => boundary.map(s => ({ a: project(s.a, cam, { w: box.width, h: box.height }), b: project(s.b, cam, { w: box.width, h: box.height }), hidden: s.hidden })));
        const res = world ? assessSectionRole(img, { scale: img.w / box.width, box: { w: box.width, h: box.height }, overlays, edges, otherBoundaries })
          : { pass: false, verdict: "FAIL", reasons: ["BOUNDARY_SHAPE_UNSUPPORTED"] };
        const identity_ok = selected === c.item;
        const verdict = !identity_ok ? "FAIL" : res.verdict;
        rows.push({ case: c.id, shape: c.shape, width, cameraName, camera: cam, fault, file, sha256: createHash("sha256").update(png).digest("hex"),
          selected, identity_ok, pixel_pass: res.pass, reasons: res.reasons, edges: res.edges?.map(({ edge, hidden, visible, blue, coverage, scored, pass }) => ({ edge, hidden, curve: Boolean(edges[edge]?.curve), visible, blue, coverage, scored, pass })),
          hidden_arcs: res.hidden_arcs,
          fill: res.fill, blue: res.blue, verdict, errors });
        console.log(`${c.id} ${width} ${cameraName} ${fault}: identity=${identity_ok} ${verdict} ${res.reasons.join(",")}`);
        await ctx.close();
      }
    }
  }
} catch (e) { failures.push(e.message.split('\n')[0]); }
finally { await browser.close(); }
// A fault is only evidence where the same view, unfaulted, was certified: an UNCERTIFIABLE view proves nothing either way.
const view = (r) => `${r.case}|${r.width}|${r.cameraName}`;
const baseline = rows.filter((r) => r.fault === "none");
const certified = new Set(baseline.filter((r) => r.verdict === "PASS").map(view));
const faulted = rows.filter((r) => r.fault !== "none" && certified.has(view(r)));
const count = (list, v) => list.filter((r) => r.verdict === v).length;
const summary = { baseline_total: baseline.length, baseline_pass: count(baseline, "PASS"), baseline_fail: count(baseline, "FAIL"),
  baseline_uncertifiable: count(baseline, "UNCERTIFIABLE"),
  certified_views_per_case: Object.fromEntries(CASES.map((c) => [c.id, baseline.filter((r) => r.case === c.id && r.verdict === "PASS").length])),
  faults_on_certified_views: faulted.length, faults_detected: count(faulted, "FAIL"),
  faults_on_uncertifiable_views: rows.filter((r) => r.fault !== "none" && !certified.has(view(r))).length,
  expected_rows: CASES.length * 2 * CAMERAS.length * FAULTS.length, completed_rows: rows.length };
writeFileSync(join(OUT, "receipt.json"), JSON.stringify({ classification: "PROPOSED_ROLE_AWARE_ORACLE_EVIDENCE_NOT_OFFICIAL_SUITE", provider_calls: 0, url: URL_, summary, failures, rows }, null, 2));
console.log(JSON.stringify(summary));
process.exitCode = !failures.length && rows.length === summary.expected_rows && summary.baseline_fail === 0
  && Object.values(summary.certified_views_per_case).every((k) => k > 0) && summary.faults_detected === summary.faults_on_certified_views ? 0 : 1;
