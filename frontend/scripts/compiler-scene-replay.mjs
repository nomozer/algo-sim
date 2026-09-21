/**
 * PHÁT LẠI CẢNH DO COMPILER DỰNG — trong trình duyệt thật, 0 lượt gọi model.
 *
 * `STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET`
 * (2026-09-21).
 *
 * ─── PHÁT LẠI, KHÔNG PHẢI CHẠY LẠI ────────────────────────────────────────
 *
 * Envelope đưa vào đây do **primitive compiler tất định** sinh từ hợp đồng của
 * lượt Analyze thật, rồi đi qua nguyên bộ cổng của đường sản phẩm. Trang chỉ
 * việc VẼ nó. Mọi `/api/*` bị chặn ở **biên mạng** và trả bản đã đóng băng —
 * nên con số `APPLICATION_LLM_CALLS = 0` là một tính chất của phép chặn, không
 * phải một lời hứa.
 *
 * ─── VÌ SAO KHÔNG ĐỌC ĐIỂM ẢNH TỪ WEBGL ───────────────────────────────────
 *
 * `canvas.toDataURL` trên ngữ cảnh WebGL trả khung TRỐNG nếu không bật
 * `preserveDrawingBuffer`, và bật nó là sửa mã sản phẩm để chụp được ảnh —
 * đúng điều `ARCHITECTURE_MAP §8` cấm. Nên script này chỉ ghi **khung bao** của
 * canvas; phép đo điểm ảnh làm trên ẢNH CHỤP, ở bước dựng contact sheet.
 *
 * Cờ: `--envelope <tệp>`  `--ra <thư mục>`  `--bo-qua-build`  `--tiem <tên>`
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { BrowserSession, sleep } from "./browser-runner.mjs";
import { kiemDistMoi, phucVu } from "./scene3d-orbit-gate.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));

const GOC = resolve(import.meta.dirname, "..", "..");
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const MAC_DINH = join(GOC, "docs", "evaluation", "geometry", "photo-problem-to-scene",
  "structured-relation-revalidation");
const ENVELOPE_PATH = resolve(CO.envelope ?? join(MAC_DINH, "REPLAY_ENVELOPE.json"));
const RA = resolve(CO.ra ?? join(MAC_DINH, "browser"));
const TIEM = CO.tiem ? String(CO.tiem) : null;

const ENVELOPE = JSON.parse(readFileSync(ENVELOPE_PATH, "utf-8")).envelope;
const DE = JSON.parse(readFileSync(join(GOC, "docs", "evaluation", "geometry",
  "photo-problem-to-scene", "structured-relation-analyze-live",
  "LIVE_CASE_MANIFEST.json"), "utf-8")).input_text;

const NHAN_MONG = ["S", "A", "B", "C"];
const DAP_SO = "10";

/* Đếm MỌI lượt `/api/*` ngay trong trang: nếu trang lỡ gọi thêm đâu đó, con số
 * này nói ra, thay vì để phép chặn im lặng nuốt mất. */
const MOC = "(function(){var goc=window.fetch;window.__API__=[];window.__LOI__=[];"
  + "var ce=console.error;console.error=function(){try{window.__LOI__.push(Array.prototype.map"
  + ".call(arguments,String).join(' ').slice(0,200));}catch(e){}return ce.apply(this,arguments);};"
  + "window.addEventListener('error',function(e){window.__LOI__.push('onerror: '+String(e.message).slice(0,200));});"
  + "window.fetch=function(u,o){try{var url=String((u&&u.url)||u);if(url.indexOf('/api/')>=0)"
  + "window.__API__.push(new URL(url,location.href).pathname);}catch(e){}return goc.apply(this,arguments);};})();";

const json = async (sess, bt) => JSON.parse(await sess.eval(`JSON.stringify(${bt})`));

/* ⚠️ `BrowserSession.eval` dùng `returnByValue: true`, nên nó trả về GIÁ TRỊ JS
 * (boolean `true`), KHÔNG phải chuỗi `"true"`. Bản đầu so `=== "true"` và vì thế
 * mọi phép chờ đều hết giờ, kể cả khi điều kiện đã đúng từ lâu: cảnh dựng xong
 * mà cổng vẫn báo "không có canvas". Một bộ đo sai theo hướng BI QUAN cũng nguy
 * hiểm như bộ đo lạc quan — nó vu cho sản phẩm một lỗi không có. */
async function cho(sess, bieuThuc, ms = 25000) {
  const het = Date.now() + ms;
  for (;;) {
    if (await sess.eval(`(function(){try{return !!(${bieuThuc})}catch(e){return false}})()`)) {
      return true;
    }
    if (Date.now() > het) return false;
    await sleep(120);
  }
}

function goChu(sess, selector, giaTri) {
  return sess.eval(`(function(){var t=document.querySelector(${JSON.stringify(selector)});`
    + "if(!t)return false;var set=Object.getOwnPropertyDescriptor("
    + "window.HTMLTextAreaElement.prototype,'value').set;"
    + `set.call(t,${JSON.stringify(giaTri)});t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
}

/* Nút gửi của ô soạn đề là nút MŨI TÊN, không mang chữ — tra bằng `aria-label`.
 * Bản đầu tìm `textContent === 'Dựng mô phỏng'`; chữ ấy thuộc `PhotoProblemPanel`
 * (luồng ảnh), không thuộc ô gõ tay, nên phép bấm không bao giờ tìm thấy gì. */
const NUT_GUI = '[aria-label="Phân tích đề bằng AI"]';
const bamDung = `(function(){var b=document.querySelector(${JSON.stringify(NUT_GUI)});`
  + "if(!b||b.disabled)return false;b.click();return true})()";
const sanSang = `(function(){var b=document.querySelector(${JSON.stringify(NUT_GUI)});`
  + "return !!b&&!b.disabled})()";

async function motKhung(cong, rong, cao) {
  const ten = `${rong}x${cao}`;
  const ca = { khung: ten, kiem: {}, do: {} };
  const k = (ma, dat, chiTiet) => {
    ca.kiem[ma] = { dat: !!dat, ...(chiTiet === undefined ? {} : { chiTiet }) };
  };
  mkdirSync(RA, { recursive: true });

  const sess = new BrowserSession({
    viewport: rong, height: cao, webgl: true,
    url: `http://127.0.0.1:${cong}`, napModuleDev: false,
  });
  await sess.open();
  if (rong < 600) {
    await sess._send("Emulation.setDeviceMetricsOverride",
      { width: rong, height: cao, deviceScaleFactor: 2, mobile: true });
  }
  await sess.interceptJson("*/api/*", async ({ url }) => {
    const p = new URL(url).pathname;
    if (p === "/api/analyze") return { status: 200, body: ENVELOPE };
    if (p === "/api/health") return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    return { status: 404, body: { error: "ngoài bản phát lại" } };
  });
  await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC });
  await sess._send("Page.reload", {});

  try {
    await cho(sess, "document.querySelector('textarea')");
    await goChu(sess, "textarea", DE);
    await cho(sess, sanSang);
    const daBam = await sess.eval(bamDung);
    k("bam_dung_duoc", daBam === true, { daBam });

    const coCanh = await cho(sess, "document.querySelector('.geo3d-canvas canvas')");
    k("canvas_ton_tai", coCanh);
    if (!coCanh) {
      ca.dat = false;
      await sess.screenshot(join(RA, `${TIEM ? `tiem-${TIEM}-` : ""}${ten}-khong-canh.png`));
      return ca;
    }
    await sleep(900); // để vòng vẽ ổn định trước khi chụp

    const khung = await json(sess, "(function(){var c=document.querySelector('.geo3d-canvas canvas');"
      + "var r=c.getBoundingClientRect();return{x:Math.round(r.left),y:Math.round(r.top),"
      + "w:Math.round(r.width),h:Math.round(r.height)};})()");
    ca.do.canvas = khung;
    k("canvas_co_dien_tich", khung.w > 80 && khung.h > 80, khung);

    const nhan = await json(sess, "(function(){var e=document.querySelector('.geo3d-labels');"
      + "return e?Array.prototype.slice.call(e.children).map(function(x){return x.textContent.trim()}):[];})()");
    ca.do.nhan = nhan;
    k("nhan_du_S_A_B_C", NHAN_MONG.every((n) => nhan.includes(n)), nhan);

    const buoc0 = await json(sess, "(function(){var e=document.querySelector('.geo3d-buoc-so');"
      + "return e?e.textContent.trim():'';})()");
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');"
      + "if(b)b.click();})()");
    await sleep(350);
    const buoc1 = await json(sess, "(function(){var e=document.querySelector('.geo3d-buoc-so');"
      + "return e?e.textContent.trim():'';})()");
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước trước\"]');"
      + "if(b)b.click();})()");
    await sleep(350);
    const buoc2 = await json(sess, "(function(){var e=document.querySelector('.geo3d-buoc-so');"
      + "return e?e.textContent.trim():'';})()");
    ca.do.buoc = { dau: buoc0, sau: buoc1, ve: buoc2 };
    k("buoc_chuyen_qua_lai", buoc0 !== buoc1 && buoc2 === buoc0, ca.do.buoc);

    /* Đường `/api/*` HỢP LỆ của trang. `/api/auth/me` là phép hỏi phiên đăng
     * nhập — nó luôn chạy và không liên quan gì tới model; bản đầu bỏ sót nó và
     * chấm KHÔNG ĐẠT cho một hành vi đúng. Điều cổng này canh không phải "ít lời
     * gọi", mà là **không có đường nào ra ngoài ba đường đã chặn**. */
    /* Đáp số chỉ có ở BƯỚC CUỐI — `.geo3d-readout` trống ở bước 1/6, và đọc nó
     * ở đó rồi kết luận "không hiện đáp số" là vu cho sản phẩm một lỗi không có.
     * Tua tới cuối bằng chính nút của người học, không bằng một lối tắt. */
    for (let i = 0; i < 40; i += 1) {
      const con = await sess.eval("(function(){var b=document.querySelector("
        + "'[aria-label=\"Bước sau\"]');if(!b||b.disabled)return false;b.click();return true})()");
      if (con !== true) break;
      await sleep(120);
    }
    await sleep(500);
    const buocCuoi = await json(sess, "(function(){var e=document.querySelector('.geo3d-buoc-so');"
      + "return e?e.textContent.trim():'';})()");
    ca.do.buoc_cuoi = buocCuoi;
    const doc = await json(sess, "(function(){var e=document.querySelector('.geo3d-readout');"
      + "return e?e.textContent.replace(/\\s+/g,' ').trim().slice(0,240):'';})()");
    ca.do.readout = doc;
    k("dap_so_hien_dung", doc.includes(DAP_SO), { buocCuoi, doc });

    const tran = await json(sess, `(function(){var w=${rong};var ra={thietBi:w,`
      + "cuonNgang:document.documentElement.scrollWidth,ngoai:[]};"
      + "Array.prototype.slice.call(document.querySelectorAll('.geo3d,.geo3d-canvas,.geo3d-thanh,"
      + ".geo3d-readout,.composer-box')).forEach(function(e){var r=e.getBoundingClientRect();"
      + "if(r.width>0&&(r.left<-1||r.right>w+1))ra.ngoai.push({lop:e.className,"
      + "trai:Math.round(r.left),phai:Math.round(r.right)});});return ra;})()");
    ca.do.tran = tran;
    k("khong_tran_khung", tran.ngoai.length === 0 && tran.cuonNgang <= rong + 1, tran);

    /* Nút điều khiển phải THẤY ĐƯỢC và không bị vật khác che ở chính tâm nó. */
    const nut = await json(sess, "(function(){var ra=[];"
      + "['Bước trước','Bước sau'].forEach(function(nh){"
      + "var b=document.querySelector('[aria-label=\"'+nh+'\"]');"
      + "if(!b){ra.push({nhan:nh,co:false});return;}"
      + "var r=b.getBoundingClientRect();var t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);"
      + "ra.push({nhan:nh,co:true,rong:Math.round(r.width),cao:Math.round(r.height),"
      + "trongKhung:r.top>=0&&r.bottom<=window.innerHeight&&r.left>=0&&r.right<=window.innerWidth,"
      + "khongBiChe:!!t&&(t===b||b.contains(t))});});return ra;})()");
    ca.do.nut = nut;
    k("nut_buoc_khong_bi_che", nut.every((x) => x.co && x.khongBiChe), nut);

    const API_CHO_PHEP = ["/api/analyze", "/api/health", "/api/auth/me"];
    const api = await json(sess, "window.__API__");
    ca.do.api = api;
    const la = api.filter((p) => !API_CHO_PHEP.includes(p));
    ca.do.api_la = la;
    k("chi_goi_api_da_chan", la.length === 0, { api, la });
    k("dung_mot_lan_analyze",
      api.filter((p) => p === "/api/analyze").length === 1,
      api.filter((p) => p === "/api/analyze").length);

    const loi = await json(sess, "window.__LOI__");
    const nang = loi.filter((m) => !/favicon|DevTools|Download the React/i.test(m));
    ca.do.console = nang;
    k("khong_loi_console_nghiem_trong", nang.length === 0, nang);

    await sess.screenshot(join(RA, `${TIEM ? `tiem-${TIEM}-` : ""}${ten}.png`));
  } finally {
    await sess.close?.();
  }
  ca.dat = Object.values(ca.kiem).every((v) => v.dat);
  return ca;
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  if (!CO["bo-qua-build"]) kiemDistMoi();
  const { sv, cong } = await phucVu(DIST);
  const kq = {
    commit, chay_luc: new Date().toISOString(), tiem: TIEM,
    envelope: ENVELOPE_PATH.replace(GOC, "").replace(/\\/g, "/"),
    BANG_CHUNG: "PHÁT LẠI — envelope do compiler tất định dựng, mọi /api/* chặn ở biên mạng",
    APPLICATION_LLM_CALLS: 0,
    ca: [],
  };
  try {
    for (const [rong, cao] of [[1440, 900], [390, 844]]) {
      const ca = await motKhung(cong, rong, cao);
      kq.ca.push(ca);
      for (const [ma, v] of Object.entries(ca.kiem)) {
        console.log(`  ${ca.khung} ${ma}: ${v.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
      }
    }
  } finally {
    sv.close();
  }
  kq.dat = kq.ca.every((c) => c.dat);
  mkdirSync(RA, { recursive: true });
  const ten = TIEM ? `BROWSER_REPLAY_TIEM_${TIEM}.json` : "BROWSER_REPLAY_RESULT.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
