// TEMPORARY diagnostic (untracked; moved to the run's diagnostics after use).
// Replays step ② of scene3d-orbit-gate.mjs exactly (same MOC hook read from the gate source, same 700 px / 70-step
// drag, same angle function) and varies ONE thing: the wait after mouse release before reading poses.
// usage: node scripts/orbit-damping-probe.mjs <distDir> <waitMs,...>
import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { phucVu, trucQuay, vongQuanhTruc } from "./scene3d-orbit-gate.mjs";

const [dist, waits = "250,2000"] = process.argv.slice(2);
const GOC = resolve(import.meta.dirname, "..", "..");
const src = readFileSync(join(import.meta.dirname, "scene3d-orbit-gate.mjs"), "utf-8");
const MOC = /const MOC = `([\s\S]*?)`;/.exec(src)[1];
const thu = join(GOC, "docs", "evaluation", "geometry", "product-ui-result-rendering", "fixtures");
const { sv, cong } = await phucVu(resolve(dist), false);
const out = { dist, runs: [] };
try {
  const sess = new BrowserSession({ viewport: 1440, height: 900, webgl: true, url: `http://127.0.0.1:${cong}`, napModuleDev: false });
  await sess.open();
  await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC });
  await sess._send("Page.reload", {});
  await sleep(2500);
  for (const wait of waits.split(",").map(Number)) {
    for (const tag of ["p1", "p6", "p7"]) {
      const ten = readdirSync(thu).find((x) => x.startsWith(`${tag}_`));
      const fx = JSON.parse(readFileSync(join(thu, ten), "utf-8"));
      await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState().loadEnvelope(${JSON.stringify(fx.envelope)});return 1})()`);
      for (let i = 0; i < 60; i++) {
        if (await sess.eval("document.querySelectorAll('.geo3d-canvas canvas').length") > 0) break;
        await sleep(200);
      }
      const soBuoc = fx.expected_trace_event_count ?? 1;
      for (let i = 0; i < soBuoc + 4; i++) {
        const b = await sess.eval("(function(){var e=document.querySelector('.geo3d-buoc-so');return e?e.textContent:'';})()");
        const m = /(\d+)\s*\/\s*(\d+)/.exec(b);
        if (m && m[1] === m[2]) break;
        await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');if(b&&!b.disabled)b.click();return 1})()");
        await sleep(80);
      }
      await sleep(500);
      const hop = JSON.parse(await sess.eval("(function(){var r=document.querySelector('.geo3d-canvas canvas').getBoundingClientRect();return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});})()"));
      const cx = Math.round(hop.x + hop.w / 2), cy = Math.round(hop.y + hop.h / 2);
      const chuot = (type, x, y, buttons) => sess._send("Input.dispatchMouseEvent",
        { type, x: Math.round(x), y: Math.round(y), button: "left", buttons, clickCount: 1 });
      await sleep(2000);
      await sess.eval("(function(){window.__QUAY__.reset('vong');return 1})()");
      const x0 = cx - Math.min(350, Math.max(40, hop.w / 2 - 20)), x1 = x0 + 700;
      const t0 = Date.now();
      await chuot("mousePressed", x0, cy, 1);
      for (let i = 1; i <= 70; i++) { await chuot("mouseMoved", x0 + (700 * i) / 70, cy, 1); await sleep(10); }
      await chuot("mouseReleased", x1, cy, 0);
      const dragMs = Date.now() - t0;
      await sleep(wait);
      const v = JSON.parse(await sess.eval("JSON.stringify({tuThe:window.__QUAY__.tuThe.slice()})"));
      out.runs.push({ wait, tag, canvasH: hop.h, dragMs, frames: v.tuThe.length,
        deg: vongQuanhTruc(v.tuThe, trucQuay(v.tuThe).vec), predicted: 360 * 700 / hop.h });
    }
  }
  await sess.close();
} finally { sv.close(); }
console.log(JSON.stringify(out));
