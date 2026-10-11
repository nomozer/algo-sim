// TEMPORARY diagnostic (untracked; moved to the run's diagnostics after use).
// Same server, browser session, viewport and fixtures as scene3d-orbit-gate.mjs; only READS the canvas box.
// usage: node scripts/orbit-canvas-probe.mjs <distDir> <label>
import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { phucVu } from "./scene3d-orbit-gate.mjs";

const [dist, label] = process.argv.slice(2);
const GOC = resolve(import.meta.dirname, "..", "..");
const thu = join(GOC, "docs", "evaluation", "geometry", "product-ui-result-rendering", "fixtures");
const { sv, cong } = await phucVu(resolve(dist), false);
const out = { label, dist, ca: [] };
try {
  const sess = new BrowserSession({ viewport: 1440, height: 900, webgl: true, url: `http://127.0.0.1:${cong}`, napModuleDev: false });
  await sess.open();
  await sleep(2500);
  for (const tag of ["p1", "p6", "p7"]) {
    const ten = readdirSync(thu).find((x) => x.startsWith(`${tag}_`));
    const fx = JSON.parse(readFileSync(join(thu, ten), "utf-8"));
    await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState().loadEnvelope(${JSON.stringify(fx.envelope)});return 1})()`);
    for (let i = 0; i < 60; i++) {
      if (await sess.eval("document.querySelectorAll('.geo3d-canvas canvas').length") > 0) break;
      await sleep(200);
    }
    await sleep(1200);
    const m = JSON.parse(await sess.eval("(function(){var c=document.querySelector('.geo3d-canvas canvas');"
      + "var r=c.getBoundingClientRect();return JSON.stringify({w:r.width,h:r.height,clientH:c.clientHeight,"
      + "innerW:innerWidth,innerH:innerHeight,dpr:devicePixelRatio});})()"));
    // OrbitControls: a horizontal drag of dx px rotates 2π·dx/clientHeight; the gate drags 700 px.
    m.predicted_one_drag_deg = 360 * 700 / m.clientH;
    out.ca.push({ tag, ...m });
  }
  await sess.close();
} finally { sv.close(); }
console.log(JSON.stringify(out));
