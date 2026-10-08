// Repro: first tap on «Các bước dựng» right after load at 390x844 (probe POLL_TIMEOUT twice). Diagnostic only.
// usage: node repro_steps_tap.mjs <dist> <fixture.json> <outDir> <n>
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const H = "file:///D:/Documents/projects/algo-sim/frontend/scripts/";
const { phucVu } = await import(H + "scene3d-orbit-gate.mjs");
const { openFixture, trustedClick } = await import(H + "compiler-scene-suite.mjs");
const { pollUntil } = await import(H + "compiler-scene-replay-lib.mjs");
const [dist, fx, out, n] = process.argv.slice(2);
mkdirSync(out, { recursive: true });
const fixture = JSON.parse(readFileSync(fx, "utf8"));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const ket = [];
for (let i = 0; i < Number(n); i += 1) {
  const { sv, cong } = await phucVu(dist);
  const { session: s } = await openFixture({ port: cong, viewport: { width: 390, height: 844 }, fixture });
  const o = { i };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    // Đo vị trí nút mỗi 100 ms trong 3 s sau khi canvas có mặt: dịch bố cục sau khi tải?
    const mau = [];
    for (let k = 0; k < 30; k += 1) {
      mau.push(await j(s, "(()=>{const b=document.querySelector('.geo3d-cac-buoc-mo');const r=b.getBoundingClientRect();"
        + "return [Math.round(performance.now()),Math.round(r.y),Math.round(document.querySelector('.geo3d-canvas').getBoundingClientRect().height),document.fonts.status]})()"));
      await sleep(100);
      if (k === 4 && process.env.TAP_EARLY) break;
    }
    o.samples = mau;
    o.shift = mau.some((m) => m[1] !== mau[0][1]) ? mau.filter((m, i) => i === 0 || m[1] !== mau[i - 1][1]) : [];
    const st = "(()=>{const b=document.querySelector('.geo3d-cac-buoc-mo');const r=b.getBoundingClientRect();"
      + "const h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);"
      + "return {rect:[r.x,r.y,r.width,r.height],hit:h?(h.className||h.tagName)+'':null,hit_is_button:b===h||b.contains(h),"
      + "canvas_h:document.querySelector('.geo3d-canvas').getBoundingClientRect().height,sy:scrollY,ih:innerHeight,"
      + "expanded:b.getAttribute('aria-expanded')}})()";
    o.before = await j(s, st);
    o.click = await trustedClick(s, "document.querySelector('.geo3d-cac-buoc-mo')");
    o.after_click = await j(s, st);
    o.opened = await pollUntil(() => j(s, "!!document.querySelector('[data-geometry-step]')"), Boolean, { timeoutMs: 5000 })
      .then(() => true, () => false);
    o.final = await j(s, st);
    if (!o.opened) await s.screenshot(join(out, `fail_${i}.png`));
  } catch (e) { o.error = String(e); }
  finally { await s.close(); sv.close(); }
  ket.push(o);
  console.log(i, o.opened, o.click, JSON.stringify(o.before), JSON.stringify(o.final));
}
writeFileSync(join(out, "repro.json"), JSON.stringify(ket, null, 2));
console.log(`opened ${ket.filter((x) => x.opened).length}/${ket.length}`);
