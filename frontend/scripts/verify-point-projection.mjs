/**
 * §6 + §10 — CHIẾU toạ độ thế giới ra màn hình rồi BẤM ĐÚNG CHỖ ĐÓ.
 *
 * Wave trước quét mù 2907 điểm ảnh và chỉ trúng `A`. Lần này không quét: tính
 * trước vị trí màn hình của từng đỉnh bằng chính camera của khung nhìn
 * (`(6,5,8)` nhìn về gốc, FOV 50°), rồi bấm vào đó. Nếu vẫn trượt thì lỗi
 * KHÔNG phải "đích bấm nhỏ" — đó mới là phép đo trả lời được câu hỏi.
 *
 * `camera.project` ở đây là CHẨN ĐOÁN TRÌNH BÀY: không giá trị nào của nó đi
 * vào `GeometryState`, checker hay phép đo.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import * as THREE from "three";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const GOC = join(import.meta.dirname, "..", "..");
const RA = join(GOC, "docs", "evaluation", "geometry", "manual-demo-5");
const env = JSON.parse(readFileSync(
  join(GOC, "docs", "evaluation", "geometry", "manual-demo", "envelope.json"), "utf8"));

const so = (s) => {
  const [a, b] = String(s).split("/");
  return b === undefined ? Number(a) : Number(a) / Number(b);
};
// Ô soi hiện NHÃN, không hiện id (`M` có nhãn "Trung điểm M của SA"). So id
// với nhãn là một phép so sai — chính nó đã báo `M` trượt ở lượt trước.
const DIEM = Object.fromEntries(
  env.scene3d.objects.filter((o) => o.type === "point3")
    .map((o) => [o.id, { xyz: o.xyz.map(so), nhan: o.label }]));

const s = new BrowserSession({ viewport: 1600, height: 1000, webgl: true });
await s.open();
await s.eval(`(async()=>{const st=await import(${JSON.stringify(s.mods.store)});
 const rg=await import(${JSON.stringify(s.mods.sims)});
 const reg=await import(${JSON.stringify(s.mods.registry)});
 if(reg.listSimulations().length===0) rg.registerAllSimulations();
 st.useAppStore.getState().loadEnvelope(${JSON.stringify(env)}); return 'ok';})()`);
await sleep(1600);
await s.eval(`(()=>{const i=document.querySelector('.geo3d-scrub input');
  const set=Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,'value').set;
  set.call(i,i.max); i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
await sleep(900);

const hop = JSON.parse(await s.eval(`(()=>{const c=document.querySelector('.geo3d canvas');
  const r=c.getBoundingClientRect();
  return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});})()`));

// Cùng camera mà `Scene3DWorkspace` dựng: FOV 50, near .1, far 200, ở (6,5,8).
const cam = new THREE.PerspectiveCamera(50, hop.w / hop.h, 0.1, 200);
cam.position.set(6, 5, 8);
cam.lookAt(0, 0, 0);
cam.updateMatrixWorld(true);

const DOC = `(()=>{const e=document.querySelector('.geo3d-inspect .geo3d-panel-title');
  return e?e.textContent:'';})()`;

const hang = [];
for (const [id, { xyz, nhan: mong }] of Object.entries(DIEM)) {
  const v = new THREE.Vector3(...xyz).project(cam);
  const sx = Math.round(hop.x + ((v.x + 1) / 2) * hop.w);
  const sy = Math.round(hop.y + ((1 - v.y) / 2) * hop.h);
  await s.mouse(sx, sy);
  const nhan = String(await s.eval(DOC) ?? "").trim();
  const dung = nhan === mong || nhan === id;
  hang.push({ id, nhan_mong_doi: mong, screen_x: sx, screen_y: sy,
              raycast_hit: !!nhan, returned: nhan || null, dung });
  console.log(`${dung ? "✅" : "❌"} ${id} @(${sx},${sy}) → ${nhan || "—"}`);
}

// Đồng bộ cây ↔ ô soi ở lần chọn cuối.
const dongBo = JSON.parse(await s.eval(`(()=>{
  const c=[...document.querySelectorAll('.geo3d-tree-item')]
    .filter(b=>b.getAttribute('aria-current')==='true');
  const soi=document.querySelector('.geo3d-inspect .geo3d-panel-title');
  return JSON.stringify({soCay:c.length,
    tenCay:c[0]?((c[0].childNodes[0]||{}).textContent||'').trim():'',
    tenSoi:soi?soi.textContent.trim():''});})()`));

const dat = hang.filter((h) => h.dung).length;
console.log(`\nĐIỂM: ${dat}/${hang.length} · đồng bộ cây/ô soi: ${JSON.stringify(dongBo)}`);
console.log("console:", JSON.stringify(s.consoleEvents.slice(0, 4)));
await s.screenshot(join(RA, "I-chon-diem-chieu.png"));
writeFileSync(join(RA, "POINT_PROJECTION.json"), JSON.stringify({
  khai: "Chiếu toạ độ thế giới → màn hình rồi bấm đúng chỗ. 0 API call.",
  diem: hang, dat: `${dat}/${hang.length}`, dong_bo: dongBo,
  console: s.consoleEvents,
}, null, 1) + "\n", "utf8");
await s.close();
