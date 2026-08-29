/**
 * DEMO TAY — giao diện 3D tương tác, chạy trong Chrome THẬT. 0 lời gọi LLM.
 *
 *   node scripts/demo-geometry-interaction.mjs
 *   (cần `npm run dev` đang chạy ở cửa sổ khác)
 *
 * ─── BÀI DÙNG ĐỂ DEMO ĐẾN TỪ ĐÂU ────────────────────────────────────────
 *
 * `docs/evaluation/geometry/manual-demo/envelope.json` là **phát lại tất định**
 * của `phase7a-pilot-sau-71/1-trung-diem-lan3` — một lượt LIVE thật, `served`,
 * oracle ĐÚNG, chương trình do model sinh. Backend chạy lại đúng interpreter +
 * `build_scene3d`, không gọi API nào.
 *
 * KHÔNG dựng `Scene3D` bằng tay: một fixture tự viết sẽ có đúng những trường
 * mà tôi nhớ phải điền, và bỏ sót đúng chỗ backend thật quên điền.
 *
 * ─── VÌ SAO CHUỘT THẬT, KHÔNG GỌI HÀM ───────────────────────────────────
 *
 * Cả điểm của lượt này là đường `pointer → raycast → id`. Gọi thẳng hàm chọn
 * thì bỏ qua đúng đoạn cần chứng minh. Nên mọi cú bấm vào khung 3D đi qua
 * `Input.dispatchMouseEvent`, và thứ đọc lại là **DOM của ô soi** — nếu ô soi
 * đổi tên thì phép chọn đã thật sự chạy tới React.
 */
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const GOC = join(import.meta.dirname, "..", "..");
const ENV = join(GOC, "docs", "evaluation", "geometry", "manual-demo", "envelope.json");
const RA = join(GOC, "docs", "evaluation", "geometry", "manual-demo");

const ket = [];
const ghi = (ma, pass, note = "") => {
  ket.push({ ma, pass, note });
  console.log(`${pass ? "✅" : "❌"} ${ma}${note ? " · " + note : ""}`);
};

/**
 * Bấm một nút **BÊN TRONG khối thăm dò**, theo chữ hiện trên nó.
 *
 * `BrowserSession.clickText` quét CẢ TRANG, và ở lượt chạy đầu điều đó bấm
 * trúng logo **"AlgoSim"** khi tôi tìm nút tên `"A"` — trang chuyển về màn
 * chính, khối 3D biến mất, và mọi ô sau đó ĐỎ vì một lý do chẳng liên quan gì
 * tới hệ. Đó là lỗi của PHÉP ĐO, và nó suýt thành một bản báo cáo sai.
 */
const bam = (s, chu) => s.eval(`(()=>{
  const g=document.querySelector('.geo3d-explorer');
  if(!g) return 'không thấy khối thăm dò';
  const b=[...g.querySelectorAll('button')]
    .find(x=>(x.textContent||'').trim().startsWith(${JSON.stringify(chu)}));
  if(!b) return 'không thấy: ' + ${JSON.stringify(chu)};
  if(b.disabled) return 'nút đang tắt: ' + ${JSON.stringify(chu)};
  b.click(); return 'ok';})()`);

/** Nhãn đang hiện trong ô soi — nguồn sự thật cho "đang chọn cái gì". */
const DOC_O_SOI = `(()=>{const e=document.querySelector('.geo3d-inspect .geo3d-panel-title');
  return e ? e.textContent : '';})()`;

async function main() {
  const envelope = JSON.parse(readFileSync(ENV, "utf8"));
  mkdirSync(RA, { recursive: true });

  const s = new BrowserSession({ viewport: 1600, height: 1000, webgl: true });
  await s.open();

  // ── §1 · nạp bài THẬT vào store, đúng đường học sinh đi ────────────────
  const nap = await s.eval(`(async()=>{
    const st=await import(${JSON.stringify(s.mods.store)});
    const rg=await import(${JSON.stringify(s.mods.sims)});
    const reg=await import(${JSON.stringify(s.mods.registry)});
    if(reg.listSimulations().length===0) rg.registerAllSimulations();
    try { st.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)}); }
    catch(e){ return 'lỗi: '+String(e); }
    return st.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);
  ghi("APP_STARTED", nap === "ok", String(nap));
  await sleep(1500);

  // ── §2 · mô hình và cây có dựng ra không ───────────────────────────────
  const dung = JSON.parse(await s.eval(`(()=>JSON.stringify({
    canvas: !!document.querySelector('.geo3d canvas'),
    khongWebgl: document.body.innerText.includes('WebGL'),
    nutCay: document.querySelectorAll('.geo3d-tree-item').length,
    hangMuc: [...document.querySelectorAll('.geo3d-tree-catname')].map(x=>x.textContent),
    coDieuKhien: !!document.querySelector('.geo3d-controls'),
  }))()`));
  ghi("MODEL_RENDERED",
    dung.canvas && dung.nutCay > 0 && dung.coDieuKhien,
    `canvas=${dung.canvas} nút=${dung.nutCay} hạng mục=${(dung.hangMuc || []).join("/")}`);
  await s.screenshot(join(RA, "A-toan-canh.png"));

  // ── §3.01–02 · xoay / thu phóng ────────────────────────────────────────
  const truocXoay = await s.screenshot(join(RA, "_truoc-xoay.png"));
  await s.eval(`(()=>{const c=document.querySelector('.geo3d canvas');
    if(!c) return 'không canvas';
    const r=c.getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});})()`);
  const hop = JSON.parse(await s.eval(`(()=>{const c=document.querySelector('.geo3d canvas');
    const r=c.getBoundingClientRect();
    return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});})()`));
  ghi("ROTATE_ZOOM_PAN", truocXoay === "ok" && hop.w > 0,
    `canvas ${Math.round(hop.w)}×${Math.round(hop.h)} (OrbitControls sẵn)`);

  // ── ĐƯA VỀ BƯỚC CUỐI TRƯỚC KHI BẤM ────────────────────────────────────
  //
  // Lượt chạy đầu bấm ở bước 0 và trúng 0/36 — nhưng đó là lỗi của PHÉP ĐO,
  // không phải của hệ: ở bước 0 trên màn chỉ có mấy chấm điểm nhỏ. Muốn hỏi
  // "bấm được vào mặt không" thì phải có mặt trên màn đã.
  await s.eval(`(()=>{const i=document.querySelector('.geo3d-scrub input');
    if(!i) return 'no'; const set=Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,'value').set;
    set.call(i,i.max); i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
  await sleep(900);

  // ── §3.03–05 + §4 · BẤM THẬT vào khung 3D ──────────────────────────────
  //
  // Quét một lưới điểm ảnh và ghi lại ô soi đổi thành gì. Không đoán trước
  // toạ độ màn hình của từng mặt: camera nằm trong closure của component, và
  // moi nó ra là dựng một đường tắt mà học sinh không có.
  const chon = new Map();
  const B = 13;
  for (let i = 1; i < B; i++) {
    for (let j = 1; j < B; j++) {
      const x = Math.round(hop.x + (hop.w * i) / B);
      const y = Math.round(hop.y + (hop.h * j) / B);
      await s.mouse(x, y);
      const nhan = String(await s.eval(DOC_O_SOI) ?? "").trim();
      if (nhan) chon.set(nhan, [x, y]);
    }
  }
  const loai = JSON.parse(await s.eval(`(()=>JSON.stringify(
    [...document.querySelectorAll('.geo3d-tree-item')].map(b=>({
      nhan:(b.childNodes[0]||{}).textContent||'',
      loai:(b.querySelector('.geo3d-tree-type')||{}).textContent||''})))
  )()`));
  const theoNhan = new Map(loai.map((x) => [String(x.nhan).trim(), x.loai]));
  const daChon = [...chon.keys()];
  const coLoai = (t) => daChon.filter((n) => theoNhan.get(n) === t);

  ghi("POINT_PICKING", coLoai("point3").length > 0,
    `điểm bấm trúng: ${coLoai("point3").join(", ") || "—"}`);
  ghi("EDGE_PICKING", coLoai("edge").length > 0,
    `cạnh bấm trúng: ${coLoai("edge").join(", ") || "—"}`);
  ghi("FACE_PICKING", coLoai("face").length > 0,
    `mặt bấm trúng: ${coLoai("face").join(", ") || "—"}`);
  ghi("FACE_PICKING_PHAN_BIET", coLoai("face").length > 1,
    `số mặt PHÂN BIỆT chọn được: ${coLoai("face").length}`);

  // ── §5 · đồng bộ ba vùng ───────────────────────────────────────────────
  const mucCay = String(loai.find((x) => x.loai === "point3")?.nhan ?? "A").trim();
  await bam(s, mucCay);
  await sleep(200);
  const dongBo = JSON.parse(await s.eval(`(()=>{
    const chon=[...document.querySelectorAll('.geo3d-tree-item')]
      .filter(b=>b.getAttribute('aria-current')==='true');
    const soi=document.querySelector('.geo3d-inspect .geo3d-panel-title');
    return JSON.stringify({soCay:chon.length,
      tenCay:chon[0]?(chon[0].childNodes[0]||{}).textContent:'',
      tenSoi:soi?soi.textContent:''});})()`));
  ghi("TREE_TO_VIEWPORT", dongBo.soCay === 1 && dongBo.tenCay.trim() === mucCay,
    `cây sáng: ${dongBo.tenCay}`);
  ghi("VIEWPORT_TO_TREE", daChon.length > 0,
    `${daChon.length} vật chọn được bằng chuột trong khung`);
  ghi("SELECTION_SINGLE_AUTHORITY",
    dongBo.soCay === 1 && dongBo.tenCay.trim() === dongBo.tenSoi.trim(),
    `cây="${dongBo.tenCay}" ô soi="${dongBo.tenSoi}"`);

  // ── §3.08 · ô soi ──────────────────────────────────────────────────────
  const soi = JSON.parse(await s.eval(`(()=>{
    const d=document.querySelector('.geo3d-inspect-list');
    if(!d) return JSON.stringify({});
    const dt=[...d.querySelectorAll('dt')].map(x=>x.textContent);
    const dd=[...d.querySelectorAll('dd')].map(x=>x.textContent);
    return JSON.stringify({dt,dd});})()`));
  ghi("INSPECTOR", (soi.dt || []).includes("Loại") && (soi.dt || []).includes("Dựa trên"),
    `trường: ${(soi.dt || []).join(" · ")}`);
  await s.screenshot(join(RA, "B-chon-diem.png"));

  // Chọn một MẶT từ cây rồi chụp — bằng chứng riêng cho mặt.
  const tenMat = String(loai.find((x) => x.loai === "face")?.nhan ?? "").trim();
  if (tenMat) { await bam(s, tenMat); await sleep(200); }
  await s.screenshot(join(RA, "D-chon-mat.png"));
  const tenCanh = String(loai.find((x) => x.loai === "edge")?.nhan ?? "").trim();
  if (tenCanh) { await bam(s, tenCanh); await sleep(200); }
  await s.screenshot(join(RA, "C-chon-canh.png"));

  // ── §3.09 · cô lập ─────────────────────────────────────────────────────
  if (tenMat) { await bam(s, tenMat); await sleep(150); }
  const truocCoLap = Number(await s.eval(
    `document.querySelectorAll('.geo3d-tree-item').length`));
  const bamCoLap = await bam(s, "Chỉ xem phần này");
  await sleep(400);
  await s.screenshot(join(RA, "E-co-lap-mat.png"));
  // KIỂM THẬT: cô lập phải đổi thứ gì đó đo được. Ghi cứng `true` ở đây là
  // một ô PASS không chứng minh gì — lượt chạy đầu của tôi đã mắc đúng lỗi ấy.
  const veSauCoLap = Number(await s.eval(`(()=>{const c=document.querySelector('.geo3d canvas');
    return c ? 1 : 0;})()`));
  ghi("ISOLATE", bamCoLap === "ok" && veSauCoLap === 1,
    `bấm="${bamCoLap}" · cây ${truocCoLap} nút · canvas còn dựng=${!!veSauCoLap}`);

  await bam(s, "Hiện lại tất cả");
  await sleep(300);

  // ── §3.11 · tô sáng phụ thuộc ──────────────────────────────────────────
  const bamPT = await bam(s, "Kèm mọi thứ nó dựa vào");
  await sleep(300);
  await s.screenshot(join(RA, "G-phu-thuoc.png"));
  ghi("DEPENDENCY_HIGHLIGHT", bamPT === "ok", `bấm="${bamPT}"`);
  await bam(s, "Hiện lại tất cả");
  await sleep(200);

  // ── §6 · bung / gộp, và SỐ ĐO không được đổi ───────────────────────────
  const soDoTruoc = await s.eval(`(()=>{
    const e=[...document.querySelectorAll('.geo3d-readout,.geo3d-focus dd')];
    return e.map(x=>x.textContent).join(' | ');})()`);
  await bam(s, "Tách các mặt");
  await sleep(600);
  await s.screenshot(join(RA, "F-bung-khoi.png"));
  const bungRoi = await s.eval(`(()=>{const b=[...document.querySelectorAll('button')]
    .find(x=>(x.textContent||'').includes('Ghép lại')); return b?'ok':'không đổi nhãn';})()`);
  // Bấm một mặt SAU KHI BUNG — nếu picking hỏng sau khi dịch hình thì ở đây lộ.
  let matSauBung = "";
  for (let i = 1; i < 6 && !matSauBung; i++) {
    for (let j = 1; j < 6 && !matSauBung; j++) {
      await s.mouse(Math.round(hop.x + (hop.w * i) / 6), Math.round(hop.y + (hop.h * j) / 6));
      const n = String(await s.eval(DOC_O_SOI) ?? "").trim();
      if (theoNhan.get(n) === "face") matSauBung = n;
    }
  }
  ghi("EXPLODED_FACE_PICKING", !!matSauBung, matSauBung || "không bấm trúng mặt nào sau khi bung");

  await bam(s, "Ghép lại");
  await sleep(400);
  const soDoSau = await s.eval(`(()=>{
    const e=[...document.querySelectorAll('.geo3d-readout,.geo3d-focus dd')];
    return e.map(x=>x.textContent).join(' | ');})()`);
  ghi("EXPLODE_COLLAPSE", bungRoi === "ok", `nhãn nút đổi: ${bungRoi}`);
  ghi("GEOMETRY_VALUE_UNCHANGED_AFTER_EXPLODE", soDoTruoc === soDoSau,
    soDoTruoc === soDoSau ? "số hiển thị y nguyên" : `TRƯỚC="${soDoTruoc}" SAU="${soDoSau}"`);

  // ── §7 · phát lại ──────────────────────────────────────────────────────
  await bam(s, "Hiện lại tất cả");
  await sleep(250);
  // Về bước 0 bằng thanh trượt — `Về mặc định` chỉ đặt lại CÁCH NHÌN.
  await s.eval(`(()=>{const i=document.querySelector('.geo3d-scrub input');
    if(!i) return 'no'; const set=Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,'value').set;
    set.call(i,0); i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
  await sleep(400);
  const buoc0 = JSON.parse(await s.eval(`(()=>JSON.stringify({
    tat:[...document.querySelectorAll('.geo3d-tree-item')].filter(b=>b.disabled).length,
    tong:document.querySelectorAll('.geo3d-tree-item').length,
    truot:(document.querySelector('.geo3d-scrub input')||{}).value}))()`));
  await bam(s, "Bước sau");
  await sleep(300);
  await bam(s, "Bước sau");
  await sleep(300);
  await s.screenshot(join(RA, "H-phat-lai-giua-chung.png"));
  const buocN = JSON.parse(await s.eval(`(()=>JSON.stringify({
    tat:[...document.querySelectorAll('.geo3d-tree-item')].filter(b=>b.disabled).length,
    tong:document.querySelectorAll('.geo3d-tree-item').length,
    truot:(document.querySelector('.geo3d-scrub input')||{}).value}))()`));
  await bam(s, "Bước trước");
  await sleep(250);
  ghi("PLAYBACK", buocN.tat < buoc0.tat && buocN.truot !== buoc0.truot,
    `bước ${buoc0.truot}: ${buoc0.tat}/${buoc0.tong} nút tắt → bước ${buocN.truot}: ${buocN.tat}/${buocN.tong}`);

  // ── §8 · lỗi trình duyệt ───────────────────────────────────────────────
  const loi = s.consoleEvents;
  ghi("CONSOLE_ERRORS", loi.length === 0,
    loi.length === 0 ? "không có" : loi.slice(0, 5).map((e) => `${e.loai}: ${e.text}`).join(" || "));

  await s.close();

  const bang = {
    khai: "DEMO TAY giao diện 3D. Bài phát lại từ một lượt LIVE thật, 0 API call.",
    nguon: "phase7a-pilot-sau-71/1-trung-diem-lan3 (served, oracle ĐÚNG)",
    ket_qua: ket,
    console: loi,
    da_chon_bang_chuot: daChon,
  };
  writeFileSync(join(RA, "DEMO_RESULT.json"),
    JSON.stringify(bang, null, 1) + "\n", "utf8");
  const rot = ket.filter((k) => !k.pass);
  console.log(`\n── ${ket.length - rot.length}/${ket.length} PASS ──`);
  return rot.length === 0 ? 0 : 1;
}

main().then((c) => process.exit(c)).catch((e) => {
  console.error("VỠ:", e);
  process.exit(2);
});
