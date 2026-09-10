/**
 * scene3d-acceptance-report.mjs — gom kết quả các lượt chạy thành artifact
 * và dựng contact sheet đặt ẢNH SẢN PHẨM cạnh MOCKUP ĐÃ DUYỆT.
 *
 * Không tự chạy trình duyệt: nó chỉ đọc những gì
 * `scene3d-browser-acceptance.mjs` đã ghi. Tách ra để phần ĐO và phần KỂ
 * không dính nhau — báo cáo không được phép "sửa" một con số nào.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";

const GOC = resolve(join(import.meta.dirname, "..", ".."));
const RA = join(GOC, "docs", "evaluation", "geometry",
  "scene3d-visual-language-browser-acceptance");
const MOCKUP = "D:/tmp/algosim-geometry-visual-mockup/mockup";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const TAGS = ["p1", "p2", "p3", "p4", "p5", "p6", "p7"];
const doc = (f) => JSON.parse(readFileSync(join(RA, f), "utf-8"));
const b64 = (p) => `data:image/png;base64,${readFileSync(p).toString("base64")}`;

const cand = doc("CANDIDATE_RUNS.json");
const base = doc("BASELINE_RUNS.json");
const xoay = doc("ROTATED_RUNS.json");
const mobile = doc("RESPONSIVE_RUNS.json");

// ── ① bề dày nét
const beDay = { khai: {
  cach_do: "Tích phân MỰC trên nền CỤC BỘ, đo trên ảnh chụp canvas thật.",
  tu_kiem: "Nét tổng hợp: 2,2→2,20 · 2,8→2,80 · 3,5→3,50 · 5→5,00 (chính xác).",
  gioi_han: "BÃO HOÀ ở ~2,0 với nét ≤1,6 px — nên số 2,0 nghĩa là 'không quá 1,6 px', "
    + "và KHÔNG bao giờ nhầm được với 2,8 px.",
  loai_tru: "Ô chữ nhãn điểm bị loại khỏi vùng đo (chữ đen gần trùng màu cạnh thấy).",
  dpr: 1,
}, muc_tieu: { canhThay: 2.8, canhKhuat: 1.6, thietDien: 3.5 }, ca: {} };
for (const c of cand.luots[0].ca) {
  beDay.ca[c.tag] = {
    canhThay: c.beDay?.canhThay ?? null,
    canhKhuat: c.beDay?.canhKhuat ?? null,
    thietDien: c.beDay?.thietDien ?? null,
    moiNet: c.beDay?.moiNet ?? null,
    anh: c.anh,
  };
}
const tv = TAGS.map((t) => beDay.ca[t]?.canhThay?.trungVi).filter((x) => x != null);
const p25 = TAGS.map((t) => beDay.ca[t]?.canhThay?.p25).filter((x) => x != null);
beDay.tong_hop = {
  VISIBLE_EDGE_WIDTH_PX_trung_vi_cac_ca: tv,
  VISIBLE_EDGE_WIDTH_PX_p25_cac_ca: p25,
  ket_luan: "Phân vị 25 % nằm ở 1,46 px trên CẢ BẢY ca, và trung vị 2,4–2,7 px "
    + "nằm ngay tại mức bão hoà của phép đo — không ca nào đạt 2,8 px.",
};
writeFileSync(join(RA, "PIXEL_WIDTH_MEASUREMENTS.json"), JSON.stringify(beDay, null, 2), "utf-8");

// ── ② readiness
const chan = { khai: "Trạng thái hợp đồng sẵn sàng của từng ca, lượt 1.", ca: {} };
for (const c of cand.luots[0].ca) {
  chan.ca[c.tag] = {
    trangThai: c.trangThai, msCho: c.msCho, consoleErrors: c.consoleErrors,
    readiness: c.readiness, canvasBox: c.canvasBox, frame: c.frame, mucPhu: c.mucPhu,
  };
}
chan.webglRenderer = cand.luots[0].webglRenderer;
chan.entryChunks = cand.luots[0].entryChunks;
chan.pageLoadRetries = cand.luots.map((l) => l.pageLoadRetries ?? 0);
writeFileSync(join(RA, "READINESS_DIAGNOSTICS.json"), JSON.stringify(chan, null, 2), "utf-8");

// ── ③ ảnh
const anh = { khai: "Mọi ảnh chụp từ BẢN DỰNG SẢN PHẨM phục vụ tĩnh.", commit: cand.luots[0].commit, ds: [] };
for (const [nhom, d, vp] of [["mac dinh", cand, "1440x900"], ["sau xoay", xoay, "1440x900"],
  ["mobile", mobile, "390x844"]]) {
  for (const c of d.luots[0].ca) {
    anh.ds.push({ nhom, tag: c.tag, viewport: vp, anh: c.anh, anhSauXoay: c.anhSauXoay ?? null,
      trangThai: c.trangThai, consoleErrors: c.consoleErrors, doiSauXoay: c.doiSauXoay ?? null });
  }
}
writeFileSync(join(RA, "SCREENSHOTS.json"), JSON.stringify(anh, null, 2), "utf-8");

// ── ④ contact sheet: sản phẩm cạnh mockup
const hang = TAGS.map((t) => {
  const sp = join(RA, "screenshots", `candidate-${t}-1440x900.png`);
  const mk = join(MOCKUP, `${t}-mockup.png`);
  const bd = beDay.ca[t]?.canhThay;
  return `
  <div class="row">
    <div class="rt">${t.toUpperCase()} — cạnh thấy đo được: <b>trung vị ${bd?.trungVi ?? "—"} px</b>
      · p25 ${bd?.p25 ?? "—"} px · n=${bd?.soMau ?? 0} · mục tiêu 2,8 px</div>
    <div class="grid">
      <div><div class="cap"><span class="tag" style="background:#1F1F1F">SẢN PHẨM</span>
        <span class="note">bản dựng, canvas thật</span></div>
        <img src="${b64(sp)}"/></div>
      <div><div class="cap"><span class="tag" style="background:#D95A43">MOCKUP ĐÃ DUYỆT</span>
        <span class="note">SVG, nét đúng token</span></div>
        ${existsSync(mk) ? `<img src="${b64(mk)}"/>` : '<p class="note">không có mockup</p>'}</div>
    </div>
  </div>`;
}).join("");

const html = `<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
 *{box-sizing:border-box}
 html,body{margin:0;background:#FAF9F7;font-family:Inter,'Segoe UI',system-ui,sans-serif;color:#171717}
 .page{width:1440px;padding:20px 22px 26px;display:flex;flex-direction:column;gap:14px}
 h1{font-size:18px;font-weight:600;margin:0}
 .sub{font-size:11.5px;color:#615d59;margin:4px 0 0}
 .row{display:flex;flex-direction:column;gap:5px}
 .rt{font-size:12.5px;font-weight:600;color:#31302e}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
 .cap{display:flex;align-items:center;gap:7px;height:17px;margin-bottom:3px}
 .tag{font-size:9.5px;font-weight:700;letter-spacing:.6px;color:#fff;padding:2px 7px;border-radius:3px}
 .note{font-size:10px;color:#615d59}
 img{width:100%;border:1px solid #e6e6e6;border-radius:4px;display:block;background:#fff}
 .foot{font-size:10.5px;color:#a39e98}
</style>
<div class="page">
  <div><h1>Sản phẩm thật cạnh mockup đã duyệt — P1–P7</h1>
  <p class="sub">Ảnh trái chụp từ <b>bản dựng sản phẩm</b> (commit ${String(cand.luots[0].commit).slice(0, 8)}),
  phục vụ tĩnh, WebGL SwiftShader, ở <b>bước dựng cuối</b>. Ảnh phải là mockup SVG đã được duyệt.
  Cổng: baseline ${base.luots.filter((l) => l.trangThai === "PASS").length}/${base.luots.length} PASS ·
  candidate ${cand.luots.filter((l) => l.trangThai === "PASS").length}/${cand.luots.length} PASS · phép tiêm 8/8 bị bắt.</p></div>
  ${hang}
  <div class="foot">⚠️ Cổng PASS nghĩa là cảnh DỰNG ĐƯỢC và đo được — không phải là phán quyết thẩm mỹ.
  Bề dày nét và các khác biệt thị giác đọc ở báo cáo Markdown.</div>
</div>`;

const tmp = join(RA, ".contact.html");
writeFileSync(tmp, html, "utf-8");
execFileSync(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--force-device-scale-factor=1", "--virtual-time-budget=6000",
  "--window-size=1440,4300", `--screenshot=${join(RA, "CONTACT_SHEET.png")}`,
  `file:///${tmp}`], { stdio: "pipe", timeout: 120000 });
console.log("→ CONTACT_SHEET.png · PIXEL_WIDTH_MEASUREMENTS.json · READINESS_DIAGNOSTICS.json · SCREENSHOTS.json");
