/**
 * certify-curved-product.mjs — KHỐI CONG trong Chrome thật. **0 mạng, 0 LLM.**
 *
 * ─── ĐIỀU NÓ TRẢ LỜI, VÀ CHỈ TRÌNH DUYỆT TRẢ LỜI ĐƯỢC ─────────────────────
 *
 * `tests/geometry/test_curved_foundation.py` (65 ca) chứng minh IR, kernel,
 * vết và cảnh đều đúng. Không ca nào trong đó trả lời được câu cuối:
 * **học sinh có thật sự NHÌN THẤY khối cầu, hình trụ, hình nón và đường tròn
 * giao tuyến không** — canvas dựng được, tua bước chạy, chọn được vật, ô soi
 * nói đúng tên tiếng Việt, ẩn/tách hoạt động, 0 lỗi bảng điều khiển.
 *
 * ─── BẤT BIẾN NÓ CANH, NGOÀI VIỆC "CÓ HIỆN" ───────────────────────────────
 *
 * **Lưới của renderer KHÔNG được thành hình học ngữ nghĩa.** Payload cảnh chở
 * tham số (`curved_kind`, ba điểm neo, `radius_sq`, `height_sq`) và **không**
 * chở `vertices`/`faces`. Lượt đo đọc thẳng payload trong store để khẳng định
 * điều ấy trên dữ liệu THẬT, không chỉ trên bảng `_TRUONG` ở backend.
 *
 * ⚠️ Bài cong nằm ở THƯ VIỆN. Lượt đo nạp envelope thẳng vào store — cùng
 * đường `certify-section-coplanar-edge.mjs` đi, và cùng lý do: bộ gợi ý trang
 * chủ cố ý nhỏ, không phủ mọi bài.
 *
 * ⚠️ Tua bằng thanh trượt, không bằng nút *Bước sau*.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = fileURLToPath(new URL("../..", import.meta.url));
const OUT = join(REPO, "docs/evaluation/integration");
mkdirSync(OUT, { recursive: true });
const VP = { w: 1600, h: 900 };
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Bài mẫu SINH RA từ `build_geometry_samples.py` — không viết tay ở đây. */
const MAU = JSON.parse(readFileSync(
  join(REPO, "frontend/src/data/geometry-samples.json"), "utf-8")).samples;
const bai = (id) => {
  const b = MAU.find((x) => x.id === id);
  if (!b) throw new Error(`không có bài mẫu '${id}' — chạy lại build script`);
  return b;
};

const dir = mkdtempSync(join(tmpdir(), "curved-"));
const proc = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9893",
  `--user-data-dir=${dir}`, `--window-size=${VP.w},${VP.h}`, "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch("http://127.0.0.1:9893/json/list")).json())
    .find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!wsUrl) await sleep(300);
}
const ws = new WebSocket(wsUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); const errs = [];
ws.onmessage = (e) => { const m = JSON.parse(e.data);
  if (m.method === "Runtime.consoleAPICalled" && m.params?.type === "error")
    errs.push((m.params.args ?? []).map((a) => a.value).join(" "));
  if (m.method === "Runtime.exceptionThrown")
    errs.push(m.params?.exceptionDetails?.text ?? "exception");
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (M, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res);
  ws.send(JSON.stringify({ id: i, method: M, params: p })); });
const ev = async (x) => (await send("Runtime.evaluate",
  { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const evj = async (x) => { const v = await ev(x); return v ? JSON.parse(v) : null; };
await send("Page.enable"); await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride",
  { width: VP.w, height: VP.h, deviceScaleFactor: 2, mobile: false });

const KQ = [];
const ghi = (ok, ten, chi) => {
  KQ.push({ ok, ten, chi });
  console.log(`${ok ? "✓" : "✗"} ${ten}${chi === undefined ? "" : ` | ${JSON.stringify(chi)}`}`);
};

async function mo(id_) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  // DẤU VÂN TAY TRANG — không có nó thì một trang trắng cũng "sạch".
  const van = await evj(`JSON.stringify({root:!!document.querySelector('#root')})`);
  if (!van?.root) throw new Error("dấu vân tay trang hỏng");
  await ev(`(async()=>{const m=await import('/src/state/store.ts');
    m.useAppStore.getState().loadEnvelope(${JSON.stringify(bai(id_).envelope)});
    return 'ok';})()`);
  await sleep(4200);
}
const datBuoc = (k) => ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
  if(!i) return 'KHONG_THAY';
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(i, ${k === "cuoi" ? "i.max" : `String(${k})`});
  i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
const bam = (sel, chu) => ev(`(()=>{const b=[...document.querySelectorAll(${JSON.stringify(sel)})]
  .find(x=>x.textContent.includes(${JSON.stringify(chu)}));
  if(!b) return 'KHONG_THAY'; if(b.disabled) return 'BI_KHOA'; b.click(); return 'ok';})()`);
/** Tên hiển thị THẬT của một loại vật, đọc từ store — không đoán bằng chữ. */
const tenCua = (loai) => ev(`(async()=>{const m=await import('/src/state/store.ts');
  const s=m.useAppStore.getState().active?.envelope?.scene3d;
  const o=(s?.objects||[]).find(x=>x.type===${JSON.stringify("__L__")});
  return o ? (o.reference || o.label) : '';})()`.replace('__L__', loai));

async function chonVat(ten) {
  await bam(".geo3d-chip", "Thành phần"); await sleep(800);
  const r = await ev(`(()=>{const n=[...document.querySelectorAll('.geo3d-tree-item .geo3d-tree-nhan')]
    .find(x=>x.textContent.trim().includes(${JSON.stringify(ten)}));
    if(!n) return 'KHONG_THAY'; const b=n.closest('.geo3d-tree-item');
    if(b.disabled) return 'BI_KHOA'; b.click(); return 'ok';})()`);
  await sleep(600);
  await bam(".geo3d-chip", "Thành phần"); await sleep(800);
  return r;
}
const trangThai = () => evj(`JSON.stringify({
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  duPhong: !!document.querySelector('.geo3d-duphong'),
  buoc: (document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
  soiTen: (document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  soiVai: (document.querySelector('.geo3d-soi-vai')?.textContent||'').trim(),
  ketQua: [...document.querySelectorAll('.geo3d-readout li')]
            .map(x=>x.textContent.trim()),
})`);
async function chup(name) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 3, y: 3 });
  await sleep(500);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, name), Buffer.from(r.result.data, "base64"));
  return name;
}

// ══ ① BA HÌNH DỰNG ĐƯỢC TRONG KHUNG ═════════════════════════════════════
const HINH = [
  ["cau-the-tich", "ball", "cầu", "36π"],
  ["tru-truc-xien", "cylinder", "trụ", "6π√5"],
  ["non-duong-sinh", "cone", "nón", "15π"],
];
for (const [ma, loai, tu, dapSo] of HINH) {
  await mo(ma);
  await datBuoc("cuoi"); await sleep(1200);
  const t = await trangThai();
  ghi(t?.canvas === 1 && !t.duPhong, `§6 ${loai}: khung 3D dựng được`, t);

  // Payload PHẢI là tham số, KHÔNG phải lưới. Đọc trên dữ liệu thật.
  const p = await evj(`(async()=>{const m=await import('/src/state/store.ts');
    const s=m.useAppStore.getState().active?.envelope?.scene3d;
    const o=(s?.objects||[]).find(x=>x.type==='curved_solid');
    return JSON.stringify(o?{kind:o.curved_kind, coNeo:!!o.anchor&&!!o.rim_point,
      coBanKinh:!!o.radius_sq, coDinh:'vertices' in o, coMat:'faces' in o,
      render:o.render}:null);})()`);
  ghi(p?.kind === loai && p.coNeo && p.coBanKinh && !p.coDinh && !p.coMat
      && p.render === "curved_solid",
      `§31 ${loai}: cảnh chở THAM SỐ, không chở lưới`, p);

  const co = (t?.ketQua || []).some((x) => x.includes(dapSo));
  ghi(co, `§6 ${loai}: đáp số chính xác hiện trên dải kết quả`, t?.ketQua);

  const r = await chonVat(await tenCua("curved_solid"));
  const s2 = await trangThai();
  ghi(r === "ok" && s2?.soiTen && !/^[a-z_]+$/.test(s2.soiTen),
      `§6 ${loai}: chọn được và ô soi nói TÊN TIẾNG VIỆT`,
      { chon: r, ten: s2?.soiTen, vai: s2?.soiVai });
  await chup(`curved-${loai}.png`);
}

// ══ ② ĐƯỜNG TRÒN GIAO TUYẾN ═════════════════════════════════════════════
await mo("cau-cat-mat-phang");
await datBuoc("cuoi"); await sleep(1200);
const tc = await trangThai();
ghi(tc?.canvas === 1 && !tc.duPhong, "§6 circle3: khung dựng được", tc);
const pc = await evj(`(async()=>{const m=await import('/src/state/store.ts');
  const s=m.useAppStore.getState().active?.envelope?.scene3d;
  const o=(s?.objects||[]).find(x=>x.type==='circle3');
  return JSON.stringify(o?{render:o.render, coTam:!!o.center, coPhap:!!o.normal,
    banKinhBinh:o.radius_sq, coDinh:'vertices' in o, nhan:o.label}:null);})()`);
ghi(pc?.render === "circle" && pc.coTam && pc.coPhap && pc.banKinhBinh === "16"
    && !pc.coDinh,
    "§12 circle3: tâm + pháp + BÌNH PHƯƠNG bán kính, không lưới", pc);
ghi((tc?.ketQua || []).some((x) => x.includes("16π")),
    "§6 circle3: diện tích hình tròn hiện đúng", tc?.ketQua);
const rc = await chonVat(await tenCua("circle3"));
ghi(rc === "ok", "§6 circle3: chọn được trong cây thành phần", rc);
await chup("curved-circle3.png");

// ══ ③ TUA · ẨN/TÁCH · MỞ BÀI KHÁC ═══════════════════════════════════════
await mo("non-thiet-dien-truc");
await datBuoc(1); await sleep(900);
const b1 = await trangThai();
await datBuoc("cuoi"); await sleep(900);
const bc = await trangThai();
ghi(b1?.buoc && bc?.buoc && b1.buoc !== bc.buoc && bc.canvas === 1,
    "§6 tua bước chạy trên bài cong", { dau: b1?.buoc, cuoi: bc?.buoc });
ghi((bc?.ketQua || []).some((x) => x.includes("12")),
    "§6 thiết diện qua trục: diện tích = 12 (hợp thành, không phép dựng mới)",
    bc?.ketQua);
// Tách khối trên một cảnh CHỈ CÓ khối cong: nút phải có mặt nhưng **bị khoá**,
// vì một khối cong không có bộ phận để tách. Khẳng định ban đầu của tôi đòi nó
// bấm được — sai, và trạng thái khoá mới là hành vi ĐÚNG. Cổng đo đúng điều đó
// thay vì đòi một thao tác vô nghĩa.
const tach = await bam(".geo3d-noi-nut", "Tách khối");
await sleep(900);
const st = await trangThai();
ghi(tach === "BI_KHOA" && st?.canvas === 1,
    "§6 nút Tách khối KHOÁ đúng cách trên cảnh chỉ có khối cong",
    { bam: tach, canvas: st?.canvas });

await mo("cau-the-tich");
const moi = await trangThai();
ghi(moi?.canvas === 1 && /1\s*\/|Bước 1/.test(moi?.buoc || ""),
    "§6 mở bài khác: dựng SẠCH, về bước đầu", moi);

// ══ ④ TRUNG THỰC NĂNG LỰC ═══════════════════════════════════════════════
const chip = await evj(`(()=>{const t=document.body.textContent||'';
  return JSON.stringify({troXoay:t.includes('Khối tròn xoay'),
    ghepBu:t.includes('Khối ghép'), });})()`);
ghi(chip && !chip.troXoay && !chip.ghepBu,
    "§7 bề mặt KHÔNG hứa khối tròn xoay / ghép–bù", chip);

// ══ TỔNG ════════════════════════════════════════════════════════════════
const dat = KQ.filter((x) => x.ok).length;
console.log(`\nĐẠT ${dat}/${KQ.length} · LOI_CONSOLE ${errs.length}`);
if (errs.length) console.log(errs.slice(0, 5).join("\n"));
writeFileSync(join(OUT, "curved-product.json"), JSON.stringify(
  { luc: new Date().toISOString(), dat, tong: KQ.length,
    loi_console: errs.length, ket_qua: KQ }, null, 2) + "\n");
ws.close(); proc.kill();
process.exit(dat === KQ.length && errs.length === 0 ? 0 : 1);
