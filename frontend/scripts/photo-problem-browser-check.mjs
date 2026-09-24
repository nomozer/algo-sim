/**
 * photo-problem-browser-check.mjs — ẢNH ĐỀ BÀI → XEM LẠI → DỰNG, trên Chrome thật.
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END §9/§12/§13. Chạy trên bản dựng tĩnh `dist/`
 * (không cần `npm run dev`), **0 lượt gọi model**: mọi `/api/*` bị chặn ở BIÊN
 * MẠNG (`interceptJson`) và trả JSON đóng băng —
 *
 *   - phản hồi đọc ảnh do CHÍNH mã backend dựng
 *     (`backend/scripts/build_photo_problem_corpus.py` → `browser_fixture_*.json`);
 *   - envelope dựng hình là fixture p3 đã khoá (`product-ui-result-rendering`).
 *
 * ⚠️ Đây là bằng chứng FIXTURE cho GIAO DIỆN. Nó không chứng minh một provider
 * thật đọc được một ảnh thật.
 *
 * Hỏi, ở 1440×900 và 390×844 (mô phỏng điện thoại, DPR 2):
 *   ① có nút Chụp ảnh / Tải ảnh; input chụp mang `capture="environment"`
 *   ② chọn ảnh bằng `DOM.setFileInputFiles` ⇒ ảnh xem trước GIẢI MÃ được
 *   ③ xoay ⇒ ảnh xem trước xoay, yêu cầu đọc mang `rotation = 90`
 *   ④ bấm "Đọc đề trong ảnh" HAI lần liền ⇒ đúng MỘT yêu cầu đọc
 *   ⑤ ô nội dung có `label`, điền sẵn; phải xác nhận mới mở nút dựng
 *   ⑥ sửa nội dung ⇒ `/api/analyze` nhận ĐÚNG văn bản đã sửa, dạng `text`, MỘT lần
 *   ⑦ cảnh 3D dựng được (canvas)
 *   ⑧ không tràn ngang; khối ảnh và nút ảnh nằm trong khung nhìn
 *   ⑨ ảnh chỉ có hình ⇒ lời từ chối ở `role=alert`, nút dựng khoá, 0 yêu cầu dựng
 *   ⑩ luồng GÕ TAY vẫn đi `/api/analyze` dạng `text` và dựng được cảnh
 *
 * Cờ: --bo-qua-build · --ra <thư mục> · --tiem <sai-van-ban|tran-ngang>
 * Phép tiêm chứng minh bộ đo đỏ được: `sai-van-ban` so văn bản gửi đi với bản
 * CHƯA sửa (⑥ phải KHÔNG ĐẠT); `tran-ngang` chèn CSS làm khối ảnh rộng 900 px
 * (⑧ phải KHÔNG ĐẠT ở 390×844).
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong chuỗi tiêm vào trang.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
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
const BANG_CHUNG = join(GOC, "docs", "evaluation", "geometry", "photo-problem-to-scene");
const RA = resolve(CO.ra ?? join(BANG_CHUNG, "browser"));
const TIEM = CO.tiem ? String(CO.tiem) : null;

const REVIEW = JSON.parse(readFileSync(join(BANG_CHUNG, "browser_fixture_review.json"), "utf-8"));
const REJECTED = JSON.parse(readFileSync(join(BANG_CHUNG, "browser_fixture_rejected.json"), "utf-8"));
const ENVELOPE = JSON.parse(readFileSync(join(GOC, "docs", "evaluation", "geometry",
  "product-ui-result-rendering", "fixtures", "p3_mat_cau_va_thiet_dien_tron.json"), "utf-8")).envelope;
const ANH_REVIEW = join(BANG_CHUNG, "corpus", "c09_de_va_hinh_cau.webp");
const ANH_REJECT = join(BANG_CHUNG, "corpus", "c11_chi_co_hinh.png");
const DE_GOC = REVIEW.assessment.problem_text;
/** Một lần sửa kiểu người học hay làm: thêm khoảng trắng trong toạ độ. */
const DE_SUA = DE_GOC.replace("I(0;0;0)", "I(0; 0; 0)");
const DE_GO_TAY = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp.";

/* Ghi lại từng yêu cầu `/api/*` NGAY TRONG TRANG: thân yêu cầu đọc ảnh có thể
 * vài trăm KB, mà `Fetch.requestPaused` không bảo đảm chở `postData` lớn. */
const MOC = "(function(){var goc=window.fetch;window.__ANH__=[];"
  + "window.fetch=function(u,o){try{var url=String((u&&u.url)||u);if(url.indexOf('/api/')>=0){"
  + "var b=o&&o.body?String(o.body):'';var r={url:url,len:b.length};"
  + "if(url.indexOf('/api/image/extract')>=0){var j=JSON.parse(b);r.rotation=j.rotation;r.mime=j.mime_type;r.coNoiDung=!!j.content;}"
  + "if(url.indexOf('/api/analyze')>=0){var k=JSON.parse(b);r.input=k.input;}"
  + "window.__ANH__.push(r);}}catch(e){}return goc.apply(this,arguments);};})();";

async function cho(sess, bieuThuc, ms = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (await sess.eval(`(function(){try{return !!(${bieuThuc})}catch(e){return false}})()`)) return true;
    await sleep(150);
  }
  return false;
}

const json = async (sess, bieuThuc) => JSON.parse(await sess.eval(`JSON.stringify(${bieuThuc})`));

async function datTep(sess, selector, duongDan) {
  const r = await sess._send("Runtime.evaluate", { expression: `document.querySelector(${JSON.stringify(selector)})` });
  const objectId = r.result?.result?.objectId;
  if (!objectId) return false;
  await sess._send("DOM.setFileInputFiles", { files: [duongDan], objectId });
  return true;
}

/** Bấm nút theo CHỮ trên nút. `lan = 2` ⇒ hai cú bấm trong CÙNG một khung. */
function bam(sess, chu, lan = 1) {
  return sess.eval("(function(){var b=Array.prototype.slice.call(document.querySelectorAll('button'))"
    + `.find(function(x){return x.textContent.trim()===${JSON.stringify(chu)}});`
    + `if(!b||b.disabled)return false;for(var i=0;i<${lan};i++)b.click();return true})()`);
}

function goChu(sess, selector, giaTri) {
  return sess.eval(`(function(){var t=document.querySelector(${JSON.stringify(selector)});if(!t)return false;`
    + "var set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;"
    + `set.call(t,${JSON.stringify(giaTri)});t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
}

const nutDungMo = "(function(){var b=Array.prototype.slice.call(document.querySelectorAll('button'))"
  + ".find(function(x){return x.textContent.trim()==='Dựng mô phỏng'});return !!b&&!b.disabled})()";

async function moTrang(cong, rong, cao, cheDo) {
  const sess = new BrowserSession({ viewport: rong, height: cao, webgl: true,
    url: `http://127.0.0.1:${cong}`, napModuleDev: false });
  await sess.open();
  if (rong < 600) {
    await sess._send("Emulation.setDeviceMetricsOverride",
      { width: rong, height: cao, deviceScaleFactor: 2, mobile: true });
  }
  await sess.interceptJson("*/api/*", async ({ url }) => {
    const p = new URL(url).pathname;
    if (p === "/api/image/extract") {
      await sleep(500); // cú bấm thứ hai phải rơi vào lúc ĐANG đọc
      return { status: 200, body: cheDo.doc === "rejected" ? REJECTED : REVIEW };
    }
    if (p === "/api/analyze") return { status: 200, body: ENVELOPE };
    if (p === "/api/health") return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    return { status: 404, body: { error: "không có trong bản kiểm" } };
  });
  await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC });
  await sess._send("Page.reload", {});
  await cho(sess, "document.querySelector('.composer-photo-btn')");
  return sess;
}

/**
 * Tràn ngang, đo theo BỀ RỘNG THIẾT BỊ — không theo `innerWidth`.
 *
 * ⚠️ Bản đầu so `scrollWidth` với `innerWidth`, và về cấu tạo KHÔNG BAO GIỜ đỏ
 * được ở 390×844: dưới giả lập di động, trang rộng hơn thiết bị làm trình duyệt
 * THU NHỎ trang, và `innerWidth` phình theo đúng nội dung (đo được 924 khi khối
 * ảnh bị tiêm rộng 900 px). Lỗi tràn tự che chính nó. Phép tiêm `tran-ngang` là
 * thứ lộ ra điều ấy — nó trả ĐẠT trên bản đầu.
 */
async function trongKhung(sess, rongThietBi) {
  return json(sess, `(function(){var w=${rongThietBi};`
    + "var ra={thietBi:w,innerWidth:window.innerWidth,cuonNgang:document.documentElement.scrollWidth,ngoai:[]};"
    + "Array.prototype.slice.call(document.querySelectorAll('.composer-box,.photo-panel,.composer-photo-btn,"
    + ".photo-actions button,.photo-text,.photo-build button')).forEach(function(e){var r=e.getBoundingClientRect();"
    + "if(r.width>0&&(r.left<-1||r.right>w+1))ra.ngoai.push({lop:e.className,trai:Math.round(r.left),phai:Math.round(r.right)});});"
    + "return ra;})()");
}

async function motKhung(cong, rong, cao) {
  const ten = `${rong}x${cao}`;
  const ca = { khung: ten, kiem: {} };
  const k = (ma, dat, chiTiet) => { ca.kiem[ma] = { dat: !!dat, ...(chiTiet === undefined ? {} : { chiTiet }) }; };
  mkdirSync(RA, { recursive: true });
  const chup = async (sess, buoc) => sess.screenshot(join(RA, `${TIEM ? `tiem-${TIEM}-` : ""}${ten}-${buoc}.png`));

  /* ── A. luồng ảnh có xem lại ── */
  const cheDo = { doc: "review" };
  let sess = await moTrang(cong, rong, cao, cheDo);
  try {
    const nut = await json(sess, "(function(){return{nut:Array.prototype.slice.call(document.querySelectorAll('.composer-photo-btn')).map(function(b){return b.textContent.trim()}),"
      + "chup:!!document.querySelector('input[type=file][capture=environment][accept=\"image/png,image/jpeg,image/webp\"]'),"
      + "goTay:!!document.querySelector('.composer-text')&&!document.querySelector('.composer-text').disabled}})()");
    k("1_CO_NUT_CHUP_VA_TAI_ANH", nut.nut.includes("Chụp ảnh") && nut.nut.includes("Tải ảnh") && nut.chup, nut);
    if (TIEM === "tran-ngang") {
      await sess.eval("(function(){var s=document.createElement('style');s.textContent='.photo-panel{width:900px}';document.head.appendChild(s);return 1})()");
    }

    await datTep(sess, "input[type=file][accept='image/png,image/jpeg,image/webp']:not([capture])", ANH_REVIEW);
    const giaiMa = await cho(sess, "document.querySelector('.photo-preview')&&document.querySelector('.photo-preview').naturalWidth>0");
    k("2_ANH_XEM_TRUOC_GIAI_MA", giaiMa);

    await bam(sess, "Xoay ảnh");
    const xoay = await cho(sess, "document.querySelector('.photo-preview').style.transform==='rotate(90deg)'", 4000);
    k("3a_XEM_TRUOC_XOAY", xoay);

    await bam(sess, "Đọc đề trong ảnh", 2);
    const daDoc = await cho(sess, "document.querySelector('#photo-problem-text')");
    const yeuCau = await json(sess, "window.__ANH__");
    const doc = yeuCau.filter((r) => r.url.includes("/api/image/extract"));
    k("3b_GUI_KEM_GOC_XOAY", doc[0]?.rotation === 90 && doc[0]?.coNoiDung === true, doc[0]);
    k("4_BAM_DOC_HAI_LAN_CHI_MOT_YEU_CAU", daDoc && doc.length === 1, { soYeuCauDoc: doc.length });

    const xemLai = await json(sess, "(function(){var t=document.querySelector('#photo-problem-text');var c=document.querySelector('.photo-confirm input');"
      + "return{giaTri:t?t.value:null,nhan:t?t.labels.length:0,xacNhan:!!c,trangThai:(document.querySelector('.photo-status')||{}).textContent||''}})()");
    const khoaTruocXacNhan = !(await sess.eval(nutDungMo));
    k("5_XEM_LAI_CO_NHAN_PHAI_XAC_NHAN", xemLai.giaTri === DE_GOC && xemLai.nhan === 1 && xemLai.xacNhan && khoaTruocXacNhan,
      { ...xemLai, khoaTruocXacNhan });
    await chup(sess, "1-xem-lai");

    const khung = await trongKhung(sess, rong);
    k("8_KHONG_TRAN_NGANG", khung.innerWidth <= rong + 1 && khung.cuonNgang <= rong + 1
      && khung.ngoai.length === 0, khung);

    await goChu(sess, "#photo-problem-text", DE_SUA);
    await sess.eval("(function(){var c=document.querySelector('.photo-confirm input');if(c&&!c.checked)c.click();return 1})()");
    const moSauXacNhan = await cho(sess, nutDungMo, 4000);
    await bam(sess, "Dựng mô phỏng", 2);
    const canh = await cho(sess, "document.querySelector('.geo3d-canvas canvas')", 30000);
    const sau = await json(sess, "window.__ANH__");
    const dung = sau.filter((r) => r.url.includes("/api/analyze"));
    const mongDoi = TIEM === "sai-van-ban" ? DE_GOC : DE_SUA;
    k("6_DUNG_BANG_VAN_BAN_DA_SUA", moSauXacNhan && dung.length === 1
      && dung[0]?.input?.type === "text" && dung[0]?.input?.content === mongDoi,
      { soYeuCauDung: dung.length, input: dung[0]?.input });
    k("7_CANH_3D_DUNG_DUOC", canh);
    await sleep(800);
    await chup(sess, "2-canh");
    ca.loiTrang = sess.consoleEvents.filter((e) => e.loai === "exception");
  } finally {
    await sess.close();
  }

  /* ── B. ảnh chỉ có hình ⇒ từ chối an toàn ── */
  cheDo.doc = "rejected";
  sess = await moTrang(cong, rong, cao, cheDo);
  try {
    await datTep(sess, "input[type=file][accept='image/png,image/jpeg,image/webp']:not([capture])", ANH_REJECT);
    await cho(sess, "document.querySelector('.photo-preview')");
    await bam(sess, "Đọc đề trong ảnh");
    const tuChoi = await cho(sess, "document.querySelector('.photo-alert')");
    const loi = tuChoi ? await sess.eval("document.querySelector('.photo-alert').getAttribute('role')+'|'+document.querySelector('.photo-alert').textContent") : "";
    const khoa = !(await sess.eval(nutDungMo));
    await bam(sess, "Dựng mô phỏng");
    await sleep(400);
    const dung = (await json(sess, "window.__ANH__")).filter((r) => r.url.includes("/api/analyze"));
    k("9_ANH_CHI_CO_HINH_TU_CHOI_AN_TOAN", tuChoi && loi.startsWith("alert|") && loi.includes("chỉ có hình vẽ")
      && khoa && dung.length === 0, { loi, khoa, soYeuCauDung: dung.length });
    await chup(sess, "3-tu-choi");
  } finally {
    await sess.close();
  }

  /* ── C. luồng gõ tay không hồi quy ── */
  sess = await moTrang(cong, rong, cao, cheDo);
  try {
    await goChu(sess, ".composer-text", DE_GO_TAY);
    await cho(sess, "!document.querySelector('.composer-send').disabled", 4000);
    await sess.eval("(function(){document.querySelector('.composer-send').click();return 1})()");
    const canh = await cho(sess, "document.querySelector('.geo3d-canvas canvas')", 30000);
    const yc = await json(sess, "window.__ANH__");
    const dung = yc.filter((r) => r.url.includes("/api/analyze"));
    const doc = yc.filter((r) => r.url.includes("/api/image/extract"));
    k("10_GO_TAY_KHONG_HOI_QUY", canh && dung.length === 1 && dung[0]?.input?.type === "text"
      && dung[0]?.input?.content === DE_GO_TAY && doc.length === 0, { soYeuCauDung: dung.length, soYeuCauDoc: doc.length });
  } finally {
    await sess.close();
  }

  ca.dat = Object.values(ca.kiem).every((x) => x.dat);
  return ca;
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  kiemDistMoi();
  const { sv, cong } = await phucVu(DIST);
  const kq = { commit, chay_luc: new Date().toISOString(), tiem: TIEM,
    BANG_CHUNG: "FIXTURE_UI — provider và dựng hình bị chặn ở biên mạng", APPLICATION_LLM_CALLS: 0, ca: [] };
  try {
    for (const [rong, cao] of [[1440, 900], [390, 844]]) {
      const ca = await motKhung(cong, rong, cao);
      kq.ca.push(ca);
      for (const [ma, v] of Object.entries(ca.kiem)) console.log(`  ${ca.khung} ${ma}: ${v.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
    }
  } finally {
    sv.close();
  }
  kq.dat = kq.ca.every((c) => c.dat);
  mkdirSync(RA, { recursive: true });
  const ten = TIEM ? `PHOTO_BROWSER_CHECK_TIEM_${TIEM}.json` : "PHOTO_BROWSER_CHECK.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
