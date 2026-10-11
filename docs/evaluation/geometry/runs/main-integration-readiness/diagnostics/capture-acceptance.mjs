// Scratch-only capture script: harness scenes (desktop + mobile) and the REAL product app on the same p1 fixture.
// The session opens on the product app (BrowserSession's readiness check needs it), then navigates.
// usage: node scripts/capture-acceptance.mjs <harnessDist> <productDist> <outDir> <fixturesDir>
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { phucVu } from "./scene3d-orbit-gate.mjs";

const [harnessDist, productDist, out, fixtures] = process.argv.slice(2).map((p) => resolve(p));
mkdirSync(out, { recursive: true });
const ids = ["tetra-S.ABC-no-projection", "tetra-A-to-SBC", "tetra-B-to-SAC", "tetra-C-to-SAB", "square-intersect-AC-BD",
  "square-proj-D-to-SBC", "square-compose-SO-AM", "square-proj-A-to-SO", "square-BN-AD-outside", "product-fixture-p1"];
const info = {};
const doc = (sess) => sess.eval("JSON.stringify({w:window.__geo3d_witness_ids||[],canvas:document.querySelectorAll('canvas').length,"
  + "labels:[...document.querySelectorAll('.geo3d-label')].filter(e=>getComputedStyle(e).opacity!=='0').map(e=>e.textContent.trim()).join(''),"
  + "scrollW:document.documentElement.scrollWidth})");

const h = await phucVu(harnessDist, false);
const p = await phucVu(productDist, false);
try {
  const sess = new BrowserSession({ viewport: 1280, height: 900, webgl: true, url: `http://127.0.0.1:${p.cong}`, napModuleDev: false });
  await sess.open();
  await sleep(2500);
  // ── REAL product app, p1 fixture ──
  const fx = JSON.parse(readFileSync(join(fixtures, readdirSync(fixtures).find((x) => x.startsWith("p1_"))), "utf-8"));
  await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState().loadEnvelope(${JSON.stringify(fx.envelope)});return 1})()`);
  await sleep(1500);
  for (let i = 0; i < (fx.expected_trace_event_count ?? 1) + 4; i++) {
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');if(b&&!b.disabled)b.click();return 1})()");
    await sleep(120);
  }
  await sleep(1500);
  info["product-app-p1"] = JSON.parse(await doc(sess));
  await sess.screenshot(join(out, "product-app-p1.png"));
  // ── harness scenes ──
  const shot = async (name, q, vp) => {
    await sess.setViewport(vp);
    await sess._send("Page.navigate", { url: `http://127.0.0.1:${h.cong}/scripts/review-visual.html?${q}` });
    await sleep(2500);
    info[name] = JSON.parse(await doc(sess));
    await sess.screenshot(join(out, `${name}.png`));
  };
  const desk = { width: 1280, height: 900, dpr: 1 }, mob = { width: 390, height: 844, dpr: 1 };
  for (let i = 0; i < ids.length; i++) await shot(`d${i}-${ids[i]}`, `i=${i}&aux=0`, desk);
  for (const i of [1, 5, 7]) await shot(`d${i}-${ids[i]}-aux1`, `i=${i}&aux=1`, desk);
  for (const i of [1, 5]) await shot(`m${i}-${ids[i]}`, `i=${i}&aux=1`, mob);
  await sess.close();
} finally { h.sv.close(); p.sv.close(); }
writeFileSync(join(out, "capture-info.json"), JSON.stringify(info, null, 1));
console.log(JSON.stringify(info));
