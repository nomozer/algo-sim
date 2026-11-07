/**
 * photo-problem-browser-check.mjs — CAMERA-FIRST → KHOANH VÙNG/XOAY → ĐỌC → XEM LẠI → Ô NHẬP → DỰNG & TOOLBAR 3D.
 *
 * Run `image-capture-crop-extraction` trên Chrome thật với bản dựng tĩnh `dist/`, **0 lượt gọi model**: mọi `/api/*`
 * bị chặn ở BIÊN MẠNG (`interceptJson`) và trả JSON đóng băng (phản hồi đọc ảnh do backend dựng, envelope p3).
 * Máy ảnh là máy ảnh GIẢ: `getUserMedia` + `enumerateDevices` bị thay bằng luồng `canvas.captureStream()` (hoặc từ chối
 * `NotAllowedError` / vắng camera sau `OverconstrainedError`).
 *
 * ⚠️ Bằng chứng FIXTURE cho GIAO DIỆN. Không chứng minh provider thật đọc được ảnh thật, cũng không chứng minh máy ảnh
 * vật lý trên thiết bị thật (`REAL_CAMERA_DEVICE_VERIFIED = NO`, `REAL_DEVICE_CAMERA_NOT_VERIFIED`).
 *
 * Khung: 1440×900 · 1309×818 DPR 1.1 (Chrome phóng 110 %) · 768×1024 DPR 2 (Tablet chạm) · 390×844 DPR 2 (Mobile chạm).
 * Kiểm:
 *   A  tải trang KHÔNG gọi camera; bấm “Chụp ảnh đề bài” mở THẲNG màn camera (không qua hộp thoại chọn trung gian),
 *      desktop ưu tiên webcam mặc định, mobile/tablet ưu tiên facingMode environment; đổi máy ảnh dừng luồng cũ → chụp
 *      dừng luồng mới → vào chỉnh ảnh; đổi ảnh → chọn ảnh có sẵn dừng camera & KHÔNG tự đọc; đặt lại khung + kéo khung
 *      (chuột / chạm) đúng vùng đỏ ⇒ ảnh GỬI ĐI có đúng cỡ 600×400 đỏ; bấm Đọc hai lần = MỘT yêu cầu; xem lại + sửa ký
 *      hiệu toán; hỏi trước khi thay chữ đang gõ; “Dùng đề này” KHÔNG tự gọi /api/analyze; thu hồi hết object URL; bấm
 *      #btn-composer-send ⇒ /api/analyze nhận đúng văn bản đã sửa → cảnh 3D; thanh công cụ 3D không còn #btn-undo-interaction
 *      dư thừa và vẫn giữ đủ #btn-reset-pos, #btn-xray, điều hướng bước #pa-next
 *   B  ảnh dọc + Xoay phải + Giữ nguyên ⇒ gửi TỆP GỐC nguyên byte + rotation 90; Escape giữ chữ đang gõ; mở lại vào thẳng camera
 *   C  Xoay phải rồi cắt ⇒ vùng gửi đi đổi chiều đúng (400×600), vẫn đỏ
 *   D  ảnh EXIF orientation 6 ⇒ khoanh theo ảnh NGƯỜI HỌC THẤY (đã áp EXIF), vùng gửi đi đúng
 *   E  máy chủ tắt đọc ảnh (503 LIVE_AI_DISABLED) ⇒ lời người học, không lộ tên cấu hình; thử lại được
 *   F  đóng hộp thoại khi đang mở máy ảnh ⇒ mọi track kết thúc (`ended`); trên mobile khi camera sau báo OverconstrainedError ⇒ tự fallback
 *   G  từ chối quyền máy ảnh ⇒ lời dễ hiểu, bấm chọn ảnh từ máy ngay tại chỗ (không bật hộp thoại chọn khác)
 *   H  không tràn ngang ở cả camera · khoanh vùng · xem lại; bẫy Tab giữ focus trong hộp thoại
 *   I  luồng GÕ TAY không hồi quy
 *
 * Cờ: --bo-qua-build · --ra <thư mục> · --tiem <lech-khung|tu-dong-doc>
 * ⚠️ Backtick KHÔNG được xuất hiện trong chuỗi tiêm vào trang.
 */
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
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
const RUN = join(GOC, "docs", "evaluation", "geometry", "runs", "image-capture-crop-extraction");
const RA = resolve(CO.ra ?? join(RUN, "browser"));
const TIEM = CO.tiem ? String(CO.tiem) : null;

const CU = join(GOC, "docs", "evaluation", "geometry", "photo-problem-to-scene");
const REVIEW = JSON.parse(readFileSync(join(CU, "browser_fixture_review.json"), "utf-8"));
const ENVELOPE = JSON.parse(readFileSync(join(GOC, "docs", "evaluation", "geometry",
  "product-ui-result-rendering", "fixtures", "p3_mat_cau_va_thiet_dien_tron.json"), "utf-8")).envelope;
const FX = JSON.parse(readFileSync(join(RUN, "fixtures", "fixtures.json"), "utf-8"));
const anh = (k) => join(RUN, "fixtures", FX[k].file);
const DE_GOC = REVIEW.assessment.problem_text;
const DE_SUA = DE_GOC.replace("I(0;0;0)", "I(0; 0; 0)") + "\nSA ⊥ SB, AB ∥ CD, A′.";
const DE_CU = "Đề em đang gõ dở.";
const DE_GO_TAY = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp.";

/* Ghi lại TRONG TRANG: yêu cầu /api/*, thân yêu cầu đọc ảnh, object URL còn sống, cú bấm input tệp. */
const MOC = "(function(){var goc=window.fetch;window.__ANH__=[];window.__THAN_ANH__=null;"
  + "window.fetch=function(u,o){try{var url=String((u&&u.url)||u);if(url.indexOf('/api/')>=0){"
  + "var b=o&&o.body?String(o.body):'';var r={url:url,len:b.length};"
  + "if(url.indexOf('/api/image/extract')>=0){var j=JSON.parse(b);r.rotation=j.rotation;r.mime=j.mime_type;r.contentLen=(j.content||'').length;window.__THAN_ANH__=j;}"
  + "if(url.indexOf('/api/analyze')>=0){var k=JSON.parse(b);r.input=k.input;}"
  + "window.__ANH__.push(r);}}catch(e){}return goc.apply(this,arguments);};"
  + "var tao=URL.createObjectURL.bind(URL),thu=URL.revokeObjectURL.bind(URL);window.__URL__=new Set();"
  + "URL.createObjectURL=function(x){var u=tao(x);window.__URL__.add(u);return u;};"
  + "URL.revokeObjectURL=function(u){window.__URL__.delete(u);return thu(u);};"
  + "var bam=HTMLInputElement.prototype.click;window.__BAM_INPUT__=[];"
  + "HTMLInputElement.prototype.click=function(){window.__BAM_INPUT__.push({type:this.type,capture:this.getAttribute('capture')});"
  + "if(this.getAttribute('capture'))return;return bam.apply(this,arguments);};})();";

/* Máy ảnh GIẢ: 2 videoinput (cam-1 1280×720, cam-2 960×720), ghi nhận constraints, đếm stop(), kiểm từ chối & fallback. */
const MAY_ANH = (cheDo) => "(function(){window.__CAM__={calls:0,stopped:0,streams:[],constraints:[]};"
  + "if(!navigator.mediaDevices)return;"
  + "navigator.mediaDevices.enumerateDevices=function(){return Promise.resolve("
  + (cheDo === "khong-co"
    ? "[]"
    : "[{deviceId:'cam-1',kind:'videoinput',label:'Camera 1',groupId:'g1'},{deviceId:'cam-2',kind:'videoinput',label:'Camera 2',groupId:'g2'}]")
  + ");};"
  + "navigator.mediaDevices.getUserMedia=function(c){window.__CAM__.calls++;"
  + "try{window.__CAM__.constraints.push(JSON.parse(JSON.stringify(c||{})));}catch(e){window.__CAM__.constraints.push({});}"
  + (cheDo === "tu-choi"
    ? "return Promise.reject(new DOMException('denied','NotAllowedError'));"
    : cheDo === "khong-co"
      ? "return Promise.reject(new DOMException('none','NotFoundError'));"
      : (cheDo === "sau-vang"
        ? "if(c&&c.video&&typeof c.video==='object'&&c.video.facingMode){return Promise.reject(new DOMException('no-rear','OverconstrainedError'));}"
        : "")
        + "var dev=(c&&c.video&&typeof c.video==='object'&&c.video.deviceId&&c.video.deviceId.exact)?c.video.deviceId.exact:'cam-1';"
        + "var cv=document.createElement('canvas');cv.width=(dev==='cam-2'?960:1280);cv.height=720;var x=cv.getContext('2d');"
        + "function ve(){x.fillStyle='#ffffff';x.fillRect(0,0,cv.width,cv.height);x.fillStyle='#dc0000';x.fillRect(240,180,480,320);}"
        + "ve();var s=cv.captureStream(15);var t=setInterval(ve,100);s.getTracks().forEach(function(k){"
        + "k.getSettings=function(){return {deviceId:dev,width:cv.width,height:cv.height};};"
        + "var st=k.stop.bind(k);k.stop=function(){window.__CAM__.stopped++;clearInterval(t);st();};});"
        + "window.__CAM__.streams.push(s);return Promise.resolve(s);")
  + "};})();";

async function cho(sess, bieuThuc, ms = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (await sess.eval(`(function(){try{return !!(${bieuThuc})}catch(e){return false}})()`)) return true;
    await sleep(120);
  }
  return false;
}

const json = async (sess, bieuThuc) => JSON.parse(await sess.eval(`(async function(){return JSON.stringify(await (${bieuThuc}));})()`));

async function datTep(sess, selector, duongDan) {
  const r = await sess._send("Runtime.evaluate", { expression: `document.querySelector(${JSON.stringify(selector)})` });
  const objectId = r.result?.result?.objectId;
  if (!objectId) return false;
  await sess._send("DOM.setFileInputFiles", { files: [duongDan], objectId });
  return true;
}
const INPUT_TAI = "input[type=file][accept='image/png,image/jpeg,image/webp']:not([capture])";

/** Bấm nút theo CHỮ (trong hộp thoại nếu có). `lan = 2` ⇒ hai cú bấm trong CÙNG một khung. */
function bam(sess, chu, lan = 1) {
  return sess.eval("(function(){var g=document.querySelector('[role=dialog]')||document;"
    + "var b=Array.prototype.slice.call(g.querySelectorAll('button'))"
    + `.find(function(x){return x.textContent.replace(/\\s+/g,' ').trim()===${JSON.stringify(chu)}});`
    + `if(!b||b.disabled)return false;for(var i=0;i<${lan};i++)b.click();return true})()`);
}

function goChu(sess, selector, giaTri) {
  return sess.eval(`(function(){var t=document.querySelector(${JSON.stringify(selector)});if(!t)return false;`
    + "var set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;"
    + `set.call(t,${JSON.stringify(giaTri)});t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
}

const manHinh = (sess) => sess.eval("(function(){var d=document.querySelector('[role=dialog]');return d?d.getAttribute('data-photo-screen'):null})()");

async function moHopThoai(sess) {
  await sess.eval("(function(){document.querySelector('#btn-composer-plus').click();return 1})()");
  await cho(sess, "document.querySelector('#menu-item-camera')", 4000);
  await sess.eval("(function(){document.querySelector('#menu-item-camera').click();return 1})()");
  return cho(sess, "document.querySelector('[role=dialog][data-photo-screen]')", 4000);
}

/** Kéo từ (x1, y1) tới (x2, y2): chuột (desktop) hoặc chạm (tablet/mobile) — đều sinh pointer event thật. */
async function keo(sess, x1, y1, x2, y2, cham) {
  const buoc = 8;
  if (cham) {
    await sess._send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: x1, y: y1 }] });
    for (let i = 1; i <= buoc; i++) {
      await sess._send("Input.dispatchTouchEvent", { type: "touchMove",
        touchPoints: [{ x: x1 + ((x2 - x1) * i) / buoc, y: y1 + ((y2 - y1) * i) / buoc }] });
    }
    await sess._send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  } else {
    await sess._send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x1, y: y1 });
    await sess._send("Input.dispatchMouseEvent", { type: "mousePressed", x: x1, y: y1, button: "left", buttons: 1, clickCount: 1 });
    for (let i = 1; i <= buoc; i++) {
      await sess._send("Input.dispatchMouseEvent", { type: "mouseMoved", button: "left", buttons: 1,
        x: x1 + ((x2 - x1) * i) / buoc, y: y1 + ((y2 - y1) * i) / buoc });
    }
    await sess._send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x2, y: y2, button: "left", buttons: 0, clickCount: 1 });
  }
  await sleep(150);
}

/** Kéo góc TRÊN-TRÁI và DƯỚI-PHẢI của khung (đang = cả ảnh) tới vùng đỏ [x0, y0, x1, y1] (pixel gốc của ảnh hiển thị). */
async function khoanh(sess, red, cham) {
  const docHinh = () => json(sess, "(function(){var i=document.querySelector('.photo-crop-image');var r=i.getBoundingClientRect();"
    + "var tay=function(o){var h=document.querySelector('.ReactCrop__drag-handle.ord-'+o).getBoundingClientRect();return [h.left+h.width/2,h.top+h.height/2]};"
    + "return {l:r.left,t:r.top,w:r.width,h:r.height,nw:i.naturalWidth,nh:i.naturalHeight,tl:tay('nw'),br:tay('se')}})()");
  const hinh = await docHinh();
  const lech = TIEM === "lech-khung" ? 40 : 0;
  const den = (h, px, py) => [h.l + (px / h.nw) * h.w + lech, h.t + (py / h.nh) * h.h];
  const [ax, ay] = den(hinh, red[0], red[1]);
  await keo(sess, hinh.tl[0], hinh.tl[1], ax, ay, cham);
  const hinh2 = await docHinh();
  const [bx, by] = den(hinh2, red[2] + 1, red[3] + 1);
  await keo(sess, hinh2.br[0], hinh2.br[1], bx, by, cham);
  return hinh2;
}

/** Giải mã ẢNH ĐÃ GỬI trong trang: cỡ thật + màu tại bốn góc trong (6 %) và tâm. */
function giaiMaAnhGui(sess) {
  return json(sess, "new Promise(function(res){var j=window.__THAN_ANH__;if(!j){res(null);return;}var im=new Image();"
    + "im.onload=function(){var c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;var x=c.getContext('2d');x.drawImage(im,0,0);"
    + "var w=c.width,h=c.height,p=function(fx,fy){var d=x.getImageData(Math.floor(w*fx),Math.floor(h*fy),1,1).data;return [d[0],d[1],d[2]]};"
    + "res({w:w,h:h,mime:j.mime_type,rotation:j.rotation,mau:[p(0.06,0.06),p(0.94,0.06),p(0.06,0.94),p(0.94,0.94),p(0.5,0.5)]});};"
    + "im.onerror=function(){res({loi:1})};im.src='data:'+j.mime_type+';base64,'+j.content;})");
}
const doHet = (mau) => mau.every(([r, g, b]) => r > 170 && g < 70 && b < 70);
const gan = (a, b, sai = 6) => Math.abs(a - b) <= sai;

async function moTrang(cong, khung, { camera = "gia", doc = "review" } = {}) {
  const sess = new BrowserSession({ viewport: khung.w, height: khung.h, webgl: true,
    url: `http://127.0.0.1:${cong}`, napModuleDev: false });
  await sess.open();
  await sess._send("Emulation.setDeviceMetricsOverride",
    { width: khung.w, height: khung.h, deviceScaleFactor: khung.dpr, mobile: !!khung.cham });
  if (khung.cham) {
    await sess._send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
    await sess._send("Emulation.setUserAgentOverride", {
      userAgent: "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
      userAgentMetadata: {
        brands: [{ brand: "Chromium", version: "130" }],
        fullVersionList: [{ brand: "Chromium", version: "130.0.0.0" }],
        platform: "Android",
        platformVersion: "14.0.0",
        architecture: "",
        model: "Pixel 7",
        mobile: true,
      },
    });
  }
  await sess.interceptJson("*/api/*", async ({ url }) => {
    const p = new URL(url).pathname;
    if (p === "/api/image/extract") {
      await sleep(400);                                   // cú bấm thứ hai phải rơi vào lúc ĐANG đọc
      if (doc === "tat") {
        return { status: 503, body: { error: "Chế độ trích xuất trực tiếp (live AI) đang bị khoá bởi cấu hình máy chủ (ALLOW_LIVE_AI=0).",
          reason_code: "LIVE_AI_DISABLED", failure_kind: "INFRASTRUCTURE_FAILURE" } };
      }
      return { status: 200, body: REVIEW };
    }
    if (p === "/api/analyze") return { status: 200, body: ENVELOPE };
    if (p === "/api/health") return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    return { status: 404, body: { error: "không có trong bản kiểm" } };
  });
  await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC + MAY_ANH(camera) });
  await sess._send("Page.reload", {});
  await cho(sess, "document.querySelector('#btn-composer-plus')");
  return sess;
}

async function trongKhung(sess, rongThietBi) {
  return json(sess, `(function(){var w=${rongThietBi};`
    + "var ra={thietBi:w,innerWidth:window.innerWidth,cuonNgang:document.documentElement.scrollWidth,ngoai:[]};"
    + "Array.prototype.slice.call(document.querySelectorAll('[role=dialog],[role=dialog] button,.photo-camera-stage,.photo-crop-image,.photo-text')).forEach(function(e){"
    + "var r=e.getBoundingClientRect();if(r.width>0&&(r.left<-1||r.right>w+1))ra.ngoai.push({lop:String(e.className),trai:Math.round(r.left),phai:Math.round(r.right)});});"
    + "return ra;})()");
}

async function motKhung(cong, khung) {
  const ten = `${khung.w}x${khung.h}@${khung.dpr}`;
  const ca = { khung: ten, cham: !!khung.cham, kiem: {} };
  const k = (ma, dat, chiTiet) => { ca.kiem[ma] = { dat: !!dat, ...(chiTiet === undefined ? {} : { chiTiet }) }; };
  mkdirSync(RA, { recursive: true });
  const chup = (sess, buoc) => sess.screenshot(join(RA, `${TIEM ? `tiem-${TIEM}-` : ""}${ten}-${buoc}.png`));
  const loiTrang = [];

  /* ── A. Camera-First → Đổi camera → Chụp → Đổi ảnh/Thư viện → Khoanh vùng → Đọc → Xem lại → Ô nhập → Dựng & Toolbar 3D ── */
  let sess = await moTrang(cong, khung);
  try {
    const camLucTaiTrang = await sess.eval("window.__CAM__.calls");
    await goChu(sess, ".composer-text", DE_CU);
    const mo = await moHopThoai(sess);
    const sanCam1 = await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth===1280&&!!document.querySelector('#btn-photo-switch-camera')})()", 8000);
    await sleep(120);
    const chon = await json(sess, "(function(){var d=document.querySelector('[role=dialog]');var c=window.__CAM__;return{"
      + "man:d.getAttribute('data-photo-screen'),tieuDe:(document.querySelector('#photo-dialog-title')||{}).textContent,"
      + "nhan:d.getAttribute('aria-labelledby'),focusTrong:d.contains(document.activeElement),"
      + "nut:Array.prototype.slice.call(d.querySelectorAll('button')).map(function(b){return b.textContent.replace(/\\s+/g,' ').trim()}),"
      + "calls:c.calls,c0:c.constraints[0]||null}})()");
    const dungRangBuocDau = khung.cham
      ? chon.c0?.video?.facingMode?.ideal === "environment" && !chon.c0?.video?.deviceId
      : !!chon.c0?.video && !chon.c0?.video?.facingMode && !chon.c0?.video?.deviceId;
    k("A1_CAMERA_TRUC_TIEP_TU_MENU", camLucTaiTrang === 0 && mo && sanCam1 && chon.man === "camera"
      && chon.tieuDe === "Chụp ảnh đề bài" && chon.nhan && chon.focusTrong
      && !chon.nut.includes("Chụp bằng máy ảnh") && chon.nut.includes("Chọn ảnh có sẵn")
      && chon.nut.includes("Đổi máy ảnh") && chon.nut.includes("Chụp ảnh")
      && chon.calls === 1 && dungRangBuocDau, { camLucTaiTrang, ...chon });

    await chup(sess, "0-camera");

    // Đổi máy ảnh (cam-1 1280 → cam-2 960), xác nhận luồng cũ dừng rồi bấm Chụp ảnh → vào thẳng Khoanh vùng
    await bam(sess, "Đổi máy ảnh");
    const sanCam2 = await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth===960})()", 6000);
    await bam(sess, "Chụp ảnh");
    const vaoTuChup = await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth===960", 8000);
    const sauChup = await json(sess, "(function(){var c=window.__CAM__;return{calls:c.calls,c1:c.constraints[1]||null,"
      + "ended:c.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})}),"
      + "anh:[document.querySelector('.photo-crop-image').naturalWidth,document.querySelector('.photo-crop-image').naturalHeight]}})()");
    k("A2_DOI_CAMERA_VA_CHUP_DUNG_LUONG", sanCam2 && vaoTuChup && sauChup.calls === 2
      && sauChup.c1?.video?.deviceId?.exact === "cam-2" && sauChup.ended
      && sauChup.anh[0] === 960 && sauChup.anh[1] === 720, sauChup);

    // Đổi ảnh → về màn camera → chọn ảnh có sẵn từ thư viện ⇒ luồng camera dừng ngay & không tự gọi /api/image/extract
    await bam(sess, "Đổi ảnh");
    await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0})()", 6000);
    await datTep(sess, INPUT_TAI, anh("landscape"));
    const vaoChinh = await cho(sess, `document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth===${FX.landscape.stored_size[0]}`, 8000);
    const camDungKhiChonAnh = await sess.eval("window.__CAM__.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})})");
    if (TIEM === "tu-dong-doc") { await bam(sess, "Giữ nguyên ảnh"); await sleep(200); await bam(sess, "Đọc đề trong ảnh"); await sleep(600); }
    const docSom = (await json(sess, "window.__ANH__")).filter((r) => r.url.includes("/api/image/extract")).length;
    k("A_CHON_ANH_KHONG_TU_DOC", vaoChinh && camDungKhiChonAnh && docSom === 0,
      { vaoChinh, camDungKhiChonAnh, soYeuCauDoc: docSom });
    if (TIEM === "tu-dong-doc") { ca.dat = false; return ca; }

    await chup(sess, "1-chinh-anh");
    // Khoanh thử → Đặt lại khung về cả ảnh → Khoanh lại vùng đỏ (kiểm cả Reset & Chỉnh lại vùng crop)
    await khoanh(sess, FX.landscape.red_stored, !!khung.cham);
    await bam(sess, "Đặt lại khung");
    const daDatLai = await cho(sess, "((document.querySelector('.photo-crop-size')||{}).textContent||'').indexOf('Cả ảnh')>=0", 3000);
    const hinh = await khoanh(sess, FX.landscape.red_stored, !!khung.cham);
    const nhanCo = await sess.eval("(document.querySelector('.photo-crop-size')||{}).textContent||''");
    await chup(sess, "2-da-khoanh");
    await bam(sess, "Cắt theo khung");
    const sanSang = await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='prepared'", 8000);
    await bam(sess, "Đọc đề trong ảnh", 2);
    const daDoc = await cho(sess, "document.querySelector('#photo-problem-text')", 8000);
    const yc = (await json(sess, "window.__ANH__")).filter((r) => r.url.includes("/api/image/extract"));
    k("A_BAM_DOC_HAI_LAN_CHI_MOT_YEU_CAU", daDatLai && sanSang && daDoc && yc.length === 1,
      { daDatLai, soYeuCauDoc: yc.length });
    const gui = await giaiMaAnhGui(sess);
    k("A_CAT_DUNG_PIXEL", gui && gan(gui.w, 600) && gan(gui.h, 400) && gui.rotation === 0 && gui.mime === "image/png" && doHet(gui.mau),
      { anhGui: gui, nhanCo, hienThi: { w: Math.round(hinh.w), h: Math.round(hinh.h), goc: [hinh.nw, hinh.nh] } });

    const xemLai = await json(sess, "(function(){var t=document.querySelector('#photo-problem-text');return{giaTri:t.value,nhan:t.labels.length,"
      + "xacNhan:!!document.querySelector('.photo-confirm input'),doiChieu:!!document.querySelector('[role=dialog] details img, [role=dialog] details summary')}})()");
    await goChu(sess, "#photo-problem-text", DE_SUA);
    await sess.eval("(function(){var c=document.querySelector('.photo-confirm input');if(c&&!c.checked)c.click();return 1})()");
    await chup(sess, "3-xem-lai");
    await bam(sess, "Dùng đề này");
    const hoiThay = await cho(sess, "Array.prototype.slice.call(document.querySelectorAll('[role=dialog] [role=alert]')).some(function(e){return e.textContent.indexOf('Thay bằng đề vừa đọc')>=0})", 3000);
    const oNhapChuaDoi = (await sess.eval("document.querySelector('.composer-text').value")) === DE_CU;
    await bam(sess, "Thay nội dung");
    const dong = await cho(sess, "!document.querySelector('[role=dialog]')", 4000);
    const oNhap = await sess.eval("document.querySelector('.composer-text').value");
    const sauDung = (await json(sess, "window.__ANH__")).filter((r) => r.url.includes("/api/analyze")).length;
    k("A_XEM_LAI_SUA_VA_HOI_TRUOC_KHI_THAY", xemLai.giaTri === DE_GOC && xemLai.nhan === 1 && hoiThay && oNhapChuaDoi
      && dong && oNhap === DE_SUA.trim(), { ...xemLai, hoiThay, oNhapChuaDoi, oNhapSau: oNhap });
    k("A_DUNG_DE_NAY_KHONG_TU_GIAI", sauDung === 0, { soYeuCauDung: sauDung });
    const urlSong = await sess.eval("window.__URL__.size");
    k("A_THU_HOI_OBJECT_URL", urlSong === 0, { urlConSong: urlSong });

    await cho(sess, "!document.querySelector('#btn-composer-send').disabled", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const canh = await cho(sess, "document.querySelector('.geo3d-canvas canvas')", 30000);
    const dung = (await json(sess, "window.__ANH__")).filter((r) => r.url.includes("/api/analyze"));
    k("A_DUNG_HINH_BANG_VAN_BAN_DA_SUA", canh && dung.length === 1 && dung[0]?.input?.type === "text"
      && dung[0]?.input?.content === DE_SUA.trim(), { soYeuCauDung: dung.length, input: dung[0]?.input });

    // Kiểm thanh công cụ Scene3D: đã xoá #btn-undo-interaction dư thừa, vẫn hoạt động điều hướng bước (#pa-prev/#pa-next) và #btn-reset-pos
    await cho(sess, "document.querySelector('#floating-toolbar-3d')", 6000);
    const buocTruoc = await sess.eval("(document.querySelector('#pa-counter')||{}).textContent||''");
    await sess.eval("(function(){var p=document.querySelector('#pa-prev');var n=document.querySelector('#pa-next');if(p&&!p.disabled)p.click();else if(n&&!n.disabled)n.click();var r=document.querySelector('#btn-reset-pos');if(r)r.click();return 1})()");
    await sleep(250);
    const tb = await json(sess, "(function(){return{khongUndo:!document.querySelector('#btn-undo-interaction'),"
      + "coReset:!!document.querySelector('#btn-reset-pos'),coXray:!!document.querySelector('#btn-xray'),"
      + "coDisplay:!!document.querySelector('#btn-display-pop'),coGeoCustom:!!document.querySelector('#btn-geo-custom-pop'),"
      + "buocSau:(document.querySelector('#pa-counter')||{}).textContent||''}})()");
    k("A_THANH_CONG_CU_3D_KHONG_CON_UNDO_THUA", tb.khongUndo && tb.coReset && tb.coXray && tb.coDisplay
      && tb.coGeoCustom && tb.buocSau !== "" && (tb.buocSau !== buocTruoc || buocTruoc.includes("/1")),
      { buocTruoc, ...tb });

    await sleep(400);
    await chup(sess, "4-canh");
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── B. ảnh dọc + xoay + giữ nguyên ⇒ tệp gốc nguyên byte + rotation; Escape giữ chữ đang gõ; mở lại vào thẳng camera ── */
  sess = await moTrang(cong, khung);
  try {
    await goChu(sess, ".composer-text", DE_CU);
    await moHopThoai(sess);
    await datTep(sess, INPUT_TAI, anh("portrait"));
    await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth>0");
    await bam(sess, "Xoay phải");
    const xoay = await cho(sess, "(function(){var i=document.querySelector('.photo-crop-image');return i&&i.naturalWidth>i.naturalHeight})()", 6000);
    await bam(sess, "Giữ nguyên ảnh");
    await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='prepared'", 6000);
    await bam(sess, "Đọc đề trong ảnh");
    await cho(sess, "document.querySelector('#photo-problem-text')", 8000);
    const r = (await json(sess, "window.__ANH__")).find((x) => x.url.includes("/api/image/extract"));
    const goc = Math.ceil(statSync(anh("portrait")).size / 3) * 4;
    k("B_GIU_NGUYEN_GUI_TEP_GOC_VA_GOC_XOAY", xoay && r?.rotation === 90 && r?.mime === "image/jpeg" && r?.contentLen === goc,
      { xoayHienThi: xoay, rotation: r?.rotation, mime: r?.mime, contentLen: r?.contentLen, mong: goc });
    await sess._send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await sess._send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    const dongEsc = await cho(sess, "!document.querySelector('[role=dialog]')", 3000);
    const giuChu = (await sess.eval("document.querySelector('.composer-text').value")) === DE_CU;
    await moHopThoai(sess);
    const moLai = await manHinh(sess);
    await sess.eval("(function(){document.querySelector('[role=dialog] .axo-modal-close').click();return 1})()");
    await sleep(150);
    const camDung = await sess.eval("window.__CAM__.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})})");
    k("B_ESCAPE_GIU_CHU_MO_LAI_VE_CAMERA", dongEsc && giuChu && moLai === "camera" && camDung,
      { dongEsc, giuChu, moLai, camDung });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── C. xoay rồi cắt · D. EXIF orientation 6 ── */
  for (const [ma, khoa, xoayPhai, mong] of [["C_XOAY_ROI_CAT_DUNG_CHIEU", "landscape", true, [400, 600]],
    ["D_EXIF_KHOANH_THEO_ANH_NGUOI_HOC_THAY", "exif6", false, [400, 600]]]) {
    sess = await moTrang(cong, khung);
    try {
      await moHopThoai(sess);
      await datTep(sess, INPUT_TAI, anh(khoa));
      await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth>0");
      let red = FX[khoa].red_displayed ?? FX[khoa].red_stored;
      if (xoayPhai) {
        await bam(sess, "Xoay phải");
        await cho(sess, "(function(){var i=document.querySelector('.photo-crop-image');return i&&i.naturalHeight>i.naturalWidth})()", 6000);
        const [W0, H0] = FX[khoa].stored_size;
        const nat = await json(sess, "[document.querySelector('.photo-crop-image').naturalWidth,document.querySelector('.photo-crop-image').naturalHeight]");
        const s = nat[0] / H0;
        red = [(H0 - 1 - red[3]) * s, red[0] * s, (H0 - 1 - red[1]) * s, red[2] * s];
        void W0;
      }
      const nat = await json(sess, "[document.querySelector('.photo-crop-image').naturalWidth,document.querySelector('.photo-crop-image').naturalHeight]");
      await khoanh(sess, red, !!khung.cham);
      await bam(sess, "Cắt theo khung");
      await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='prepared'", 8000);
      await bam(sess, "Đọc đề trong ảnh");
      await cho(sess, "document.querySelector('#photo-problem-text')", 8000);
      const gui = await giaiMaAnhGui(sess);
      k(ma, gui && gan(gui.w, mong[0], 8) && gan(gui.h, mong[1], 8) && gui.rotation === 0 && doHet(gui.mau),
        { anhGui: gui, anhHienThi: nat });
      loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
    } finally {
      await sess.close();
    }
  }

  /* ── E. máy chủ tắt đọc ảnh ── */
  sess = await moTrang(cong, khung, { doc: "tat" });
  try {
    await moHopThoai(sess);
    await datTep(sess, INPUT_TAI, anh("landscape"));
    await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth>0");
    await bam(sess, "Giữ nguyên ảnh");
    await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='prepared'", 6000);
    await bam(sess, "Đọc đề trong ảnh");
    const loi = await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='error'", 8000);
    const chu = await sess.eval("document.querySelector('[role=dialog]').textContent");
    k("E_TAT_DOC_ANH_LOI_NGUOI_HOC", loi && /tạm tắt/.test(chu) && !/ALLOW_LIVE_AI|LIVE_AI_DISABLED|GEMINI/.test(chu)
      && /Thử đọc lại/.test(chu), { chu: chu.slice(0, 240) });
    await chup(sess, "5-loi");
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── F. đóng máy ảnh giải phóng track (+ trên mobile/tablet kiểm fallback khi camera sau vắng) ── */
  sess = await moTrang(cong, khung, { camera: khung.cham ? "sau-vang" : "gia" });
  try {
    await moHopThoai(sess);
    const san = await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0})()", 8000);
    await sess.eval("(function(){document.querySelector('[role=dialog] .axo-modal-close').click();return 1})()");
    await sleep(250);
    const dongMa = await json(sess, "(function(){var c=window.__CAM__;return{calls:c.calls,stopped:c.stopped,"
      + "ended:c.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})})}})()");
    const mongCalls = khung.cham ? 2 : 1;
    k("F_DONG_KHI_DANG_MO_MAY_ANH_DUNG_LUONG", san && dongMa.calls === mongCalls && dongMa.stopped >= 1 && dongMa.ended,
      { san, mongCalls, ...dongMa });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── G. từ chối quyền máy ảnh ⇒ báo lỗi ngắn gọn + chọn ảnh từ máy ngay tại chỗ (trên mobile có thêm lối máy ảnh gốc) ── */
  sess = await moTrang(cong, khung, { camera: "tu-choi" });
  try {
    await moHopThoai(sess);
    const bao = await cho(sess, "(function(){var a=document.querySelector('[role=dialog] [role=alert]');return a&&a.textContent.indexOf('cấp quyền máy ảnh')>=0})()", 6000);
    const nutLoi = await json(sess, "Array.prototype.slice.call(document.querySelectorAll('[role=dialog] button')).map(function(b){return b.textContent.replace(/\\s+/g,' ').trim()})");
    if (khung.cham) {
      await bam(sess, "Mở máy ảnh thiết bị");
    }
    const bamNative = khung.cham ? (await json(sess, "window.__BAM_INPUT__")).some((b) => b.capture === "environment") : true;
    await datTep(sess, INPUT_TAI, anh("landscape"));
    const vaoChinhTuLoi = await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth>0", 6000);
    k("G_TU_CHOI_QUYEN_VAN_CHON_ANH_DUOC", bao && nutLoi.includes("Chọn ảnh từ máy")
      && !nutLoi.includes("Chụp bằng máy ảnh") && bamNative && vaoChinhTuLoi,
      { bao, nutLoi, bamNative, vaoChinhTuLoi });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── H. bố cục không tràn ngang (camera · khoanh vùng · xem lại) + bẫy Tab ── */
  sess = await moTrang(cong, khung);
  try {
    await moHopThoai(sess);
    await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0})()", 8000);
    const k0 = await trongKhung(sess, khung.w);
    for (let i = 0; i < 6; i++) {
      await sess._send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
      await sess._send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    }
    const giuFocus = await sess.eval("(function(){var d=document.querySelector('[role=dialog]');return !!d&&d.contains(document.activeElement)})()");
    await datTep(sess, INPUT_TAI, anh("portrait"));
    await cho(sess, "document.querySelector('.photo-crop-image')&&document.querySelector('.photo-crop-image').naturalWidth>0");
    const k1 = await trongKhung(sess, khung.w);
    await bam(sess, "Giữ nguyên ảnh");
    await cho(sess, "document.querySelector('[role=dialog]').getAttribute('data-photo-screen')==='prepared'", 6000);
    await bam(sess, "Đọc đề trong ảnh");
    await cho(sess, "document.querySelector('#photo-problem-text')", 8000);
    const k2 = await trongKhung(sess, khung.w);
    const ok = (x) => x.innerWidth <= khung.w + 1 && x.cuonNgang <= khung.w + 1 && x.ngoai.length === 0;
    k("H_KHONG_TRAN_NGANG_VA_GIU_FOCUS", giuFocus && ok(k0) && ok(k1) && ok(k2),
      { giuFocus, camera: k0, chinhAnh: k1, xemLai: k2 });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── I. luồng gõ tay không hồi quy ── */
  sess = await moTrang(cong, khung);
  try {
    await goChu(sess, ".composer-text", DE_GO_TAY);
    await cho(sess, "!document.querySelector('#btn-composer-send').disabled", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const canh = await cho(sess, "document.querySelector('.geo3d-canvas canvas')", 30000);
    const yc = await json(sess, "window.__ANH__");
    const dung = yc.filter((r) => r.url.includes("/api/analyze"));
    k("I_GO_TAY_KHONG_HOI_QUY", canh && dung.length === 1 && dung[0]?.input?.content === DE_GO_TAY
      && yc.every((r) => !r.url.includes("/api/image/extract")), { soYeuCauDung: dung.length });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  ca.loiTrang = loiTrang;
  k("Z_KHONG_LOI_TRANG", loiTrang.length === 0, loiTrang.slice(0, 5));
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
  const kq = {
    commit,
    chay_luc: new Date().toISOString(),
    tiem: TIEM,
    BANG_CHUNG: "FIXTURE_UI — provider và dựng hình bị chặn ở biên mạng; máy ảnh GIẢ (getUserMedia + enumerateDevices bị thay)",
    APPLICATION_LLM_CALLS: 0,
    REAL_CAMERA_DEVICE_VERIFIED: "NO",
    CAMERA_VERIFICATION_NOTE: "REAL_DEVICE_CAMERA_NOT_VERIFIED",
    ca: [],
  };
  const KHUNG = [
    { w: 1440, h: 900, dpr: 1 },
    { w: 1309, h: 818, dpr: 1.1 },
    { w: 768, h: 1024, dpr: 2, cham: true },
    { w: 390, h: 844, dpr: 2, cham: true },
  ];
  try {
    for (const khung of KHUNG) {
      const ca = await motKhung(cong, khung);
      kq.ca.push(ca);
      for (const [ma, v] of Object.entries(ca.kiem)) console.log(`  ${ca.khung} ${ma}: ${v.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
      if (TIEM) break;
    }
  } finally {
    sv.close();
  }
  kq.dat = kq.ca.every((c) => c.dat);
  mkdirSync(RA, { recursive: true });
  const ten = TIEM ? `PHOTO_BROWSER_CHECK_TIEM_${TIEM}.json` : "PHOTO_BROWSER_CHECK.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), { encoding: "utf-8", flag: "wx" });
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
