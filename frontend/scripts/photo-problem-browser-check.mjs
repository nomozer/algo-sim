/**
 * photo-problem-browser-check.mjs — Ô NHẬP THỐNG NHẤT · CAMERA-FIRST TỐI GIẢN · ĐÍNH KÈM ẢNH/PDF/DOCX · CHỈ XỬ LÝ KHI BẤM "DỰNG HÌNH" · SCENE3D.
 *
 * Chạy trên Chrome thật với bản dựng tĩnh `dist/`, **0 lượt gọi model thật**: mọi `/api/*`
 * bị chặn ở BIÊN MẠNG (`interceptJson`) và trả JSON đóng băng khớp hợp đồng `POST /api/input/prepare` + `POST /api/analyze`.
 * Máy ảnh là máy ảnh GIẢ LẬP (`getUserMedia` + `enumerateDevices` qua `canvas.captureStream()`).
 *
 * Bằng chứng FIXTURE cho GIAO DIỆN & LUỒNG TƯƠNG TÁC:
 * - `REAL_CAMERA_DEVICE_VERIFIED = "NO"` (`REAL_DEVICE_CAMERA_NOT_VERIFIED`)
 * - `LIVE_GEMINI_IMAGE_EXTRACTION_VERIFIED = "NO"`
 * - `APPLICATION_LLM_CALLS = 0`
 *
 * Bốn khung nhìn bắt buộc (§22):
 *   1. Desktop 1440×900 DPR 1
 *   2. Chrome phóng 110% (1309×818 DPR 1.1)
 *   3. Tablet 768×1024 DPR 2 (chạm)
 *   4. Mobile 390×844 DPR 2 (chạm)
 *
 * Quy tắc: KHÔNG BAO GIỜ dùng ký tự backtick bên trong chuỗi JS tiêm vào trình duyệt.
 */
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { kiemDistMoi, phucVu } from "./scene3d-orbit-gate.mjs";

const CO = Object.fromEntries(
  process.argv.slice(2).reduce((a, x, i, ds) => {
    if (x.startsWith("--")) {
      a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
    }
    return a;
  }, []),
);

const GOC = resolve(import.meta.dirname, "..", "..");
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const RUN = join(GOC, "docs", "evaluation", "geometry", "runs", "image-capture-crop-extraction");
const RA = resolve(CO.ra ?? join(RUN, "browser"));

const ENVELOPE = JSON.parse(
  readFileSync(
    join(
      GOC,
      "docs",
      "evaluation",
      "geometry",
      "product-ui-result-rendering",
      "fixtures",
      "p3_mat_cau_va_thiet_dien_tron.json",
    ),
    "utf-8",
  ),
).envelope;

const ANH_CORPUS = join(
  GOC,
  "docs",
  "evaluation",
  "geometry",
  "photo-problem-to-scene",
  "corpus",
  "c08_de_va_hinh_chop.png",
);

const DE_BO_SUNG = "Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4";
const DE_TRICH_XUAT =
  "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy. Biết SA = 4. Tính thể tích khối chóp S.ABCD.";
const DE_BAI_2 =
  "Cho mặt cầu tâm I bán kính R = 5 và mặt phẳng (P) cách I một khoảng bằng 3. Dựng đường tròn giao tuyến của (P) và mặt cầu.";
const DE_CHUA_CHAC =
  "Cho mặt cầu tâm I(0;0;0) bán kính R = 5 cắt mặt phẳng (P) theo giao tuyến đường tròn.";
const DE_DA_SUA =
  "Cho mặt cầu tâm I(0; 0; 0) bán kính R = 5 cắt mặt phẳng (P) theo giao tuyến đường tròn, SA ⊥ SB, A′.";
const DE_GO_TAY =
  "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp.";

/** Sinh bảng CRC32 & gói ZIP STORE không nén để tạo tệp .docx hợp lệ 100% trong thư mục tạm. */
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[i] = c >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function buildMinimalStoreZip(entries) {
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  for (const [name, contentStr] of entries) {
    const nameBuf = Buffer.from(name, "utf-8");
    const dataBuf = Buffer.from(contentStr, "utf-8");
    const sum = crc32(dataBuf);

    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0);
    lh.writeUInt16LE(20, 4);
    lh.writeUInt16LE(0, 6);
    lh.writeUInt16LE(0, 8);
    lh.writeUInt16LE(0, 10);
    lh.writeUInt16LE(0, 12);
    lh.writeUInt32LE(sum, 14);
    lh.writeUInt32LE(dataBuf.length, 18);
    lh.writeUInt32LE(dataBuf.length, 22);
    lh.writeUInt16LE(nameBuf.length, 26);
    lh.writeUInt16LE(0, 28);
    localParts.push(lh, nameBuf, dataBuf);

    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0);
    ch.writeUInt16LE(20, 4);
    ch.writeUInt16LE(20, 6);
    ch.writeUInt16LE(0, 8);
    ch.writeUInt16LE(0, 10);
    ch.writeUInt16LE(0, 12);
    ch.writeUInt16LE(0, 14);
    ch.writeUInt32LE(sum, 16);
    ch.writeUInt32LE(dataBuf.length, 20);
    ch.writeUInt32LE(dataBuf.length, 24);
    ch.writeUInt16LE(nameBuf.length, 28);
    ch.writeUInt16LE(0, 30);
    ch.writeUInt16LE(0, 32);
    ch.writeUInt16LE(0, 34);
    ch.writeUInt16LE(0, 36);
    ch.writeUInt32LE(0, 38);
    ch.writeUInt32LE(offset, 42);
    centralParts.push(ch, nameBuf);

    offset += lh.length + nameBuf.length + dataBuf.length;
  }
  const centralBuf = Buffer.concat(centralParts);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(0, 4);
  eocd.writeUInt16LE(0, 6);
  eocd.writeUInt16LE(entries.length, 8);
  eocd.writeUInt16LE(entries.length, 10);
  eocd.writeUInt32LE(centralBuf.length, 12);
  eocd.writeUInt32LE(offset, 16);
  eocd.writeUInt16LE(0, 20);
  return Buffer.concat([...localParts, centralBuf, eocd]);
}

function taoTepTam(thuMucTam) {
  const pdfPath = join(thuMucTam, "de-hinh-khong-gian.pdf");
  const pdfMultiPath = join(thuMucTam, "de-nhieu-bai.pdf");
  const docxPath = join(thuMucTam, "de-chop-sabcd.docx");
  const minimalPdf = Buffer.from(
    "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n",
    "utf-8",
  );
  writeFileSync(pdfPath, minimalPdf);
  writeFileSync(pdfMultiPath, minimalPdf);
  const docxBuf = buildMinimalStoreZip([
    [
      "[Content_Types].xml",
      '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
    ],
    [
      "word/document.xml",
      '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy.</w:t></w:r></w:p></w:body></w:document>',
    ],
  ]);
  writeFileSync(docxPath, docxBuf);
  return { pdfPath, pdfMultiPath, docxPath };
}

/* Ghi nhận trong trang: mọi yêu cầu /api/*, các objectURL đang sống, cú bấm input[capture]. Không chứa backtick. */
const MOC =
  "(function(){var goc=window.fetch;window.__API__=[];"
  + "window.fetch=function(u,o){try{var url=String((u&&u.url)||u);if(url.indexOf('/api/')>=0){"
  + "var b=o&&o.body?String(o.body):'';var r={url:url,len:b.length,ts:Date.now()};"
  + "if(url.indexOf('/api/input/prepare')>=0){var j=JSON.parse(b);r.filename=j.filename;r.mime=j.mime_type;r.userText=j.user_text||null;r.selectedCandidateId=j.selected_candidate_id||null;r.contentLen=(j.content||'').length;}"
  + "if(url.indexOf('/api/analyze')>=0){var k=JSON.parse(b);r.input=k.input;}"
  + "window.__API__.push(r);}}catch(e){}return goc.apply(this,arguments);};"
  + "var tao=URL.createObjectURL.bind(URL),thu=URL.revokeObjectURL.bind(URL);window.__URL__=new Set();"
  + "URL.createObjectURL=function(x){var u=tao(x);window.__URL__.add(u);return u;};"
  + "URL.revokeObjectURL=function(u){window.__URL__.delete(u);return thu(u);};"
  + "var bam=HTMLInputElement.prototype.click;window.__BAM_INPUT__=[];"
  + "HTMLInputElement.prototype.click=function(){window.__BAM_INPUT__.push({id:this.id||'',type:this.type,capture:this.getAttribute('capture')});"
  + "if(this.getAttribute('capture'))return;return bam.apply(this,arguments);};})();";

/* Máy ảnh giả lập: 2 camera, 1 camera, từ chối quyền, không có thiết bị, bận thiết bị, hoặc lỗi camera sau trên di động. */
function taoMayAnhGia(cheDo) {
  const dsThietBi =
    cheDo === "khong-co"
      ? "[]"
      : cheDo === "mot-cam"
        ? "[{deviceId:'cam-1',kind:'videoinput',label:'Camera 1',groupId:'g1'}]"
        : "[{deviceId:'cam-1',kind:'videoinput',label:'Camera 1',groupId:'g1'},{deviceId:'cam-2',kind:'videoinput',label:'Camera 2',groupId:'g2'}]";

  let thanGetUserMedia = "";
  if (cheDo === "tu-choi") {
    thanGetUserMedia = "return Promise.reject(new DOMException('denied','NotAllowedError'));";
  } else if (cheDo === "khong-co") {
    thanGetUserMedia = "return Promise.reject(new DOMException('none','NotFoundError'));";
  } else if (cheDo === "ban") {
    thanGetUserMedia = "return Promise.reject(new DOMException('busy','NotReadableError'));";
  } else {
    const loiCamSau =
      cheDo === "sau-vang"
        ? "if(c&&c.video&&typeof c.video==='object'&&c.video.facingMode){return Promise.reject(new DOMException('no-rear','OverconstrainedError'));}"
        : "";
    thanGetUserMedia =
      loiCamSau
      + "var dev=(c&&c.video&&typeof c.video==='object'&&c.video.deviceId&&c.video.deviceId.exact)?c.video.deviceId.exact:'cam-1';"
      + "var cv=document.createElement('canvas');cv.width=(dev==='cam-2'?960:1280);cv.height=720;var x=cv.getContext('2d');"
      + "function ve(){x.fillStyle='#f8fafc';x.fillRect(0,0,cv.width,cv.height);x.fillStyle='#1e293b';x.fillRect(180,140,cv.width-360,cv.height-280);}"
      + "ve();var s=cv.captureStream(15);var t=setInterval(ve,100);s.getTracks().forEach(function(k){"
      + "k.getSettings=function(){return {deviceId:dev,width:cv.width,height:cv.height};};"
      + "var st=k.stop.bind(k);k.stop=function(){window.__CAM__.stopped++;clearInterval(t);st();};});"
      + "window.__CAM__.streams.push(s);return Promise.resolve(s);";
  }

  return (
    "(function(){window.__CAM__={calls:0,stopped:0,streams:[],constraints:[]};"
    + "if(!navigator.mediaDevices)return;"
    + "navigator.mediaDevices.enumerateDevices=function(){return Promise.resolve("
    + dsThietBi
    + ");};"
    + "navigator.mediaDevices.getUserMedia=function(c){window.__CAM__.calls++;"
    + "try{window.__CAM__.constraints.push(JSON.parse(JSON.stringify(c||{})));}catch(e){window.__CAM__.constraints.push({});}"
    + thanGetUserMedia
    + "};})()"
  );
}

if (MOC.includes("\x60") || taoMayAnhGia("gia").includes("\x60")) {
  throw new Error("Chuỗi tiêm vào trình duyệt tuyệt đối không được chứa ký tự backtick.");
}

async function cho(sess, bieuThuc, ms = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    const ok = await sess.eval("(function(){try{return !!(" + bieuThuc + ")}catch(e){return false}})()");
    if (ok) return true;
    await sleep(110);
  }
  return false;
}

const json = async (sess, bieuThuc) =>
  JSON.parse(await sess.eval("(async function(){return JSON.stringify(await (" + bieuThuc + "));})()"));

async function datTep(sess, selector, duongDan) {
  const r = await sess._send("Runtime.evaluate", {
    expression: "document.querySelector(" + JSON.stringify(selector) + ")",
  });
  const objectId = r.result?.result?.objectId;
  if (!objectId) return false;
  await sess._send("DOM.setFileInputFiles", { files: [duongDan], objectId });
  return true;
}

const INPUT_ANH_PHU = "input[type=file][accept='image/png,image/jpeg,image/webp']:not([capture])";

function goChu(sess, selector, giaTri) {
  return sess.eval(
    "(function(){var t=document.querySelector("
      + JSON.stringify(selector)
      + ");if(!t)return false;"
      + "var set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;"
      + "set.call(t,"
      + JSON.stringify(giaTri)
      + ");t.dispatchEvent(new Event('input',{bubbles:true}));return true})()",
  );
}

async function moCameraTuMenu(sess) {
  await sess.eval("(function(){document.querySelector('#btn-composer-plus').click();return 1})()");
  await cho(sess, "document.querySelector('#menu-item-camera')", 4000);
  await sess.eval("(function(){document.querySelector('#menu-item-camera').click();return 1})()");
  return cho(sess, "document.querySelector('#photo-camera-dialog')", 4000);
}

async function trongKhung(sess, rongThietBi) {
  return json(
    sess,
    "(function(){var w="
      + String(rongThietBi)
      + ";var ra={thietBi:w,innerWidth:window.innerWidth,cuonNgang:document.documentElement.scrollWidth,ngoai:[]};"
      + "Array.prototype.slice.call(document.querySelectorAll('#home-composer-box,[role=dialog],[role=dialog] button,.photo-camera-stage,#composer-candidate-picker,#composer-extraction-confirm')).forEach(function(e){"
      + "var r=e.getBoundingClientRect();if(r.width>0&&(r.left<-1.5||r.right>w+1.5))ra.ngoai.push({id:e.id||String(e.className),trai:Math.round(r.left),phai:Math.round(r.right)});});"
      + "return ra;})()",
  );
}

async function moTrang(cong, khung, { camera = "gia", cheDoPrepare = "ready" } = {}) {
  const sess = new BrowserSession({
    viewport: khung.w,
    height: khung.h,
    webgl: true,
    url: "http://127.0.0.1:" + String(cong),
    napModuleDev: false,
  });
  await sess.open();
  await sess._send("Emulation.setDeviceMetricsOverride", {
    width: khung.w,
    height: khung.h,
    deviceScaleFactor: khung.dpr,
    mobile: !!khung.cham,
  });
  if (khung.cham) {
    await sess._send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
    await sess._send("Emulation.setUserAgentOverride", {
      userAgent:
        "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
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

  await sess.interceptJson("*/api/*", async ({ url, request }) => {
    const p = new URL(url).pathname;
    if (p === "/api/input/prepare") {
      const postData = request?.postData;
      const req = postData ? JSON.parse(postData) : {};
      if (cheDoPrepare === "cham") {
        await sleep(550);
      } else {
        await sleep(180);
      }
      if (cheDoPrepare === "tat") {
        return {
          status: 503,
          body: {
            error: "Chế độ trích xuất trực tiếp (live AI) đang bị khoá bởi cấu hình máy chủ (ALLOW_LIVE_AI=0).",
            reason_code: "LIVE_AI_DISABLED",
            failure_kind: "INFRASTRUCTURE_FAILURE",
          },
        };
      }
      if (cheDoPrepare === "confirm") {
        return {
          status: 200,
          body: {
            schema: "unified-input-prepare/1",
            status: "needs_confirmation",
            source_kind: "image",
            problem_text: DE_CHUA_CHAC,
            learner_message: "Ảnh có một ký hiệu nhỏ hơi mờ, em kiểm tra nhanh trước khi dựng hình.",
            reason_code: null,
            flag_messages: ["Phần rìa tạp chí trên đầu trang đã được tự động loại bỏ."],
            uncertain_tokens: [
              { token: "R = 5", alternatives: ["R = 3"], location: "dòng 1", reason: "nét in mảnh" },
            ],
            missing_regions: [],
            candidates: [],
            provenance: { noise_filtered: true },
            metrics: {
              vlm_calls: 1,
              used_vlm: true,
              raw_input_bytes: 8200,
              vlm_payload_bytes: 5400,
              uncropped_baseline_bytes: 8200,
              processing_ms: 120,
            },
          },
        };
      }
      if ((req.filename || "").includes("nhieu-bai") && !req.selected_candidate_id) {
        return {
          status: 200,
          body: {
            schema: "unified-input-prepare/1",
            status: "needs_selection",
            source_kind: "pdf",
            problem_text: "",
            learner_message: "Tài liệu có 2 bài toán độc lập. Em chạm chọn bài muốn dựng hình.",
            reason_code: "MULTIPLE_PROBLEMS_DETECTED",
            flag_messages: [],
            uncertain_tokens: [],
            missing_regions: [],
            candidates: [
              {
                candidate_id: "cand-1",
                label: "Bài 1 (Trang 1)",
                preview_snippet: "Cho hình chóp S.ABC có đáy đều cạnh a...",
                preview_data_url: null,
                page_number: 1,
                has_figure: false,
                problem_text: DE_GO_TAY,
              },
              {
                candidate_id: "cand-2",
                label: "Bài 2 (Trang 1 · kèm hình vẽ)",
                preview_snippet: "Cho mặt cầu tâm I bán kính R = 5 và mặt phẳng (P)...",
                preview_data_url: null,
                page_number: 1,
                has_figure: true,
                problem_text: DE_BAI_2,
              },
            ],
            provenance: { page_count: 1 },
            metrics: {
              vlm_calls: 0,
              used_vlm: false,
              raw_input_bytes: 1024,
              vlm_payload_bytes: 0,
              uncropped_baseline_bytes: 0,
              processing_ms: 18,
            },
          },
        };
      }
      const chosenText = req.selected_candidate_id === "cand-2" ? DE_BAI_2 : DE_TRICH_XUAT;
      return {
        status: 200,
        body: {
          schema: "unified-input-prepare/1",
          status: "ready",
          source_kind: (req.filename || "").endsWith(".docx")
            ? "docx"
            : (req.filename || "").endsWith(".pdf")
              ? "pdf"
              : "image",
          problem_text: chosenText,
          learner_message: null,
          reason_code: null,
          flag_messages: [],
          uncertain_tokens: [],
          missing_regions: [],
          candidates: [],
          provenance: { supplemental_merged: Boolean(req.user_text) },
          metrics: {
            vlm_calls: 0,
            used_vlm: false,
            raw_input_bytes: 2048,
            vlm_payload_bytes: 0,
            uncropped_baseline_bytes: 0,
            processing_ms: 24,
          },
        },
      };
    }
    if (p === "/api/analyze") return { status: 200, body: ENVELOPE };
    if (p === "/api/health") return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    if (p.startsWith("/api/auth/")) return { status: 200, body: { authenticated: false, user: null } };
    return { status: 404, body: { error: "không có trong bản kiểm" } };
  });

  await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC + taoMayAnhGia(camera) });
  await sess._send("Page.reload", {});
  await cho(sess, "document.querySelector('#btn-composer-plus')");
  return sess;
}

async function motKhung(cong, khung, tepTam) {
  const ten = khung.w + "x" + khung.h + "@" + khung.dpr;
  const ca = { khung: ten, cham: !!khung.cham, kiem: {} };
  const k = (ma, dat, chiTiet) => {
    ca.kiem[ma] = { dat: !!dat, ...(chiTiet === undefined ? {} : { chiTiet }) };
  };
  mkdirSync(RA, { recursive: true });
  const chup = (sess, buoc) => sess.screenshot(join(RA, ten + "-" + buoc + ".png"));
  const loiTrang = [];

  /* ── A. Camera-First tối giản → đổi camera → chụp 1 ảnh → tự đính kèm chip, đóng dialog ngay, 0 màn crop, 0 AI sớm ── */
  let sess = await moTrang(cong, khung);
  try {
    const camLucTaiTrang = await sess.eval("window.__CAM__.calls");
    await goChu(sess, "#home-problem-input", DE_BO_SUNG);
    const mo = await moCameraTuMenu(sess);
    const sanCam1 = await cho(
      sess,
      "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth===1280&&!!document.querySelector('#btn-photo-switch-camera')})()",
      8000,
    );
    await sleep(120);
    const infoCam = await json(
      sess,
      "(function(){var d=document.querySelector('#photo-camera-dialog');var dr=d.getBoundingClientRect();"
        + "var sh=document.querySelector('#btn-photo-capture').getBoundingClientRect();"
        + "var disc=document.querySelector('.photo-shutter-disc').getBoundingClientRect();"
        + "var lib=document.querySelector('#btn-photo-library').getBoundingClientRect();"
        + "var sw=document.querySelector('#btn-photo-switch-camera').getBoundingClientRect();"
        + "var c=window.__CAM__;return{"
        + "man:d.getAttribute('data-photo-screen'),tieuDe:(document.querySelector('#photo-dialog-title')||{}).textContent,"
        + "focusTrong:d.contains(document.activeElement),dialogW:Math.round(dr.width),"
        + "shutterW:Math.round(sh.width),shutterH:Math.round(sh.height),"
        + "discW:Math.round(disc.width),discH:Math.round(disc.height),"
        + "shutterLechTam:Math.round(Math.abs((sh.left+sh.width/2)-(dr.left+dr.width/2))),"
        + "thuTuTraiPhai:(lib.left<sh.left&&sh.right<=sw.right),"
        + "calls:c.calls,c0:c.constraints[0]||null}})()",
    );
    const dungRangBuocDau = khung.cham
      ? infoCam.c0?.video?.facingMode?.ideal === "environment" && !infoCam.c0?.video?.deviceId
      : !!infoCam.c0?.video && !infoCam.c0?.video?.facingMode && !infoCam.c0?.video?.deviceId;
    const dungBoCucCamera =
      khung.w <= 640
        ? infoCam.shutterW === 64
          && infoCam.shutterH === 64
          && infoCam.discW === 48
          && infoCam.discH === 48
          && infoCam.shutterLechTam <= 6
          && infoCam.thuTuTraiPhai
        : infoCam.dialogW <= 564 && infoCam.thuTuTraiPhai;

    k(
      "A1_CAMERA_TOI_GIAN_TRUC_TIEP",
      camLucTaiTrang === 0
        && mo
        && sanCam1
        && infoCam.man === "camera"
        && infoCam.tieuDe === "Chụp ảnh đề bài"
        && infoCam.focusTrong
        && infoCam.calls === 1
        && dungRangBuocDau
        && dungBoCucCamera,
      { camLucTaiTrang, ...infoCam },
    );

    await chup(sess, "0-camera");

    // Đổi sang cam-2 (960x720), chụp 1 ảnh -> dừng toàn bộ track, đóng dialog, đính kèm thẳng thành chip trong composer!
    await sess.eval("(function(){document.querySelector('#btn-photo-switch-camera').click();return 1})()");
    const sanCam2 = await cho(
      sess,
      "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth===960})()",
      6000,
    );
    await sess.eval("(function(){document.querySelector('#btn-photo-capture').click();return 1})()");
    const daDinhKemChip = await cho(
      sess,
      "!document.querySelector('#photo-camera-dialog')&&!!document.querySelector('#composer-files-wrap .file-preview-card .composer-file-thumb')",
      8000,
    );
    const sauChup = await json(
      sess,
      "(function(){var c=window.__CAM__;return{"
        + "calls:c.calls,c1:c.constraints[1]||null,"
        + "ended:c.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})}),"
        + "khongCoManCrop:!document.querySelector('.photo-crop-image'),"
        + "giuChuGoTay:document.querySelector('#home-problem-input').value,"
        + "apiTruocDungHinh:window.__API__.filter(function(r){return r.url.indexOf('/api/input/prepare')>=0||r.url.indexOf('/api/image/extract')>=0||r.url.indexOf('/api/analyze')>=0}).length"
        + "}})()",
    );
    k(
      "A2_CHUP_TU_DINH_KEM_KHONG_MAN_CROP_KHONG_GOI_AI",
      sanCam2
        && daDinhKemChip
        && sauChup.calls === 2
        && sauChup.c1?.video?.deviceId?.exact === "cam-2"
        && sauChup.ended
        && sauChup.khongCoManCrop
        && sauChup.giuChuGoTay === DE_BO_SUNG
        && sauChup.apiTruocDungHinh === 0,
      sauChup,
    );

    await chup(sess, "1-attached-chip");

    /* ── C. Xem trước chip · đổi sang PDF · đổi sang DOCX · xoá tệp · thu hồi hết objectURL · 0 AI trước khi bấm Dựng hình ── */
    await sess.eval("(function(){document.querySelector('#composer-files-wrap .file-preview-card').click();return 1})()");
    const moXemTruoc = await cho(sess, "!!document.querySelector('#composer-single-file-modal .single-file-preview-img')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-replace-file-modal').click();return 1})()");
    await datTep(sess, "#home-file-input", tepTam.pdfPath);
    const daDoiSangPdf = await cho(
      sess,
      "document.querySelector('#composer-files-wrap .file-name-ext')&&document.querySelector('#composer-files-wrap .file-name-ext').textContent==='.pdf'",
      5000,
    );

    // Đổi tiếp sang DOCX và xác nhận 0 objectURL rò rỉ từ ảnh cũ, 0 lượt gọi AI khi đính kèm PDF/DOCX
    await sess.eval("(function(){document.querySelector('#composer-files-wrap .file-preview-card').click();return 1})()");
    await cho(sess, "!!document.querySelector('#btn-replace-file-modal')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-replace-file-modal').click();return 1})()");
    await datTep(sess, "#home-file-input", tepTam.docxPath);
    const daDoiSangDocx = await cho(
      sess,
      "document.querySelector('#composer-files-wrap .file-name-ext')&&document.querySelector('#composer-files-wrap .file-name-ext').textContent==='.docx'",
      5000,
    );
    const trangThaiDoiTep = await json(
      sess,
      "(function(){return{urlConSong:window.__URL__.size,chu:document.querySelector('#home-problem-input').value,"
        + "apiTruocDungHinh:window.__API__.filter(function(r){return r.url.indexOf('/api/input/prepare')>=0||r.url.indexOf('/api/image/extract')>=0||r.url.indexOf('/api/analyze')>=0}).length}})()",
    );

    // Xoá hẳn chip, đính kèm lại ảnh rồi đính kèm lại DOCX để kiểm cả xoá tệp & đính kèm ảnh từ máy
    await sess.eval("(function(){document.querySelector('#composer-files-wrap .file-card-remove').click();return 1})()");
    const daXoaChip = await cho(sess, "!document.querySelector('#composer-files-wrap')", 4000);
    await datTep(sess, "#home-file-input", ANH_CORPUS);
    const daChonAnh = await cho(
      sess,
      "document.querySelector('#composer-files-wrap .file-name-ext')&&document.querySelector('#composer-files-wrap .file-name-ext').textContent==='.png'",
      5000,
    );
    await sess.eval("(function(){document.querySelector('#composer-files-wrap .file-card-remove').click();return 1})()");
    await cho(sess, "!document.querySelector('#composer-files-wrap')", 4000);
    const urlSauKhiXoaAnh = await sess.eval("window.__URL__.size");

    await datTep(sess, "#home-file-input", tepTam.docxPath);
    await cho(sess, "!!document.querySelector('#composer-files-wrap .file-preview-card')", 4000);

    k(
      "C_CHON_ANH_PDF_DOCX_DOI_XOA_KHONG_RO_URL_KHONG_GOI_AI",
      moXemTruoc
        && daDoiSangPdf
        && daDoiSangDocx
        && daXoaChip
        && daChonAnh
        && trangThaiDoiTep.urlConSong === 0
        && urlSauKhiXoaAnh === 0
        && trangThaiDoiTep.chu === DE_BO_SUNG
        && trangThaiDoiTep.apiTruocDungHinh === 0,
      { moXemTruoc, daDoiSangPdf, daDoiSangDocx, daXoaChip, daChonAnh, urlSauKhiXoaAnh, ...trangThaiDoiTep },
    );

    /* ── D. Kết hợp văn bản gõ tay + DOCX -> Bấm "Dựng hình" (chống bấm đúp) -> /api/input/prepare -> /api/analyze -> Scene3D ── */
    await sess.eval(
      "(function(){var b=document.querySelector('#btn-composer-send');b.click();b.click();return 1})()",
    );
    const lenCanh3D = await cho(sess, "!!document.querySelector('.geo3d-canvas canvas')", 30000);
    await sleep(250);
    const kqDung = await json(
      sess,
      "(function(){var api=window.__API__.filter(function(r){return r.url.indexOf('/api/health')<0});"
        + "var prep=api.filter(function(r){return r.url.indexOf('/api/input/prepare')>=0});"
        + "var ana=api.filter(function(r){return r.url.indexOf('/api/analyze')>=0});"
        + "var tb=document.querySelector('#floating-toolbar-3d');"
        + "return{soPrep:prep.length,soAna:ana.length,prep0:prep[0]||null,ana0:ana[0]||null,"
        + "coToolbar:!!tb,khongConUndo:!document.querySelector('#btn-undo-interaction'),"
        + "coReset:!!document.querySelector('#btn-reset-pos'),coXray:!!document.querySelector('#btn-xray'),"
        + "coNext:!!document.querySelector('#pa-next')}})()",
    );
    if (kqDung.coNext) {
      await sess.eval("(function(){var n=document.querySelector('#pa-next');if(n&&!n.disabled)n.click();return 1})()");
    }
    const vanConCanvas = await sess.eval("!!document.querySelector('.geo3d-canvas canvas')");
    k(
      "D_KET_HOP_CHU_VA_TEP_DUNG_SCENE3D_KHONG_ANH_HUONG_BUOC_DUNG",
      lenCanh3D
        && vanConCanvas
        && kqDung.soPrep === 1
        && kqDung.soAna === 1
        && kqDung.prep0?.filename === "de-chop-sabcd.docx"
        && kqDung.prep0?.userText === DE_BO_SUNG
        && kqDung.ana0?.input?.content === DE_TRICH_XUAT
        && kqDung.coToolbar
        && kqDung.khongConUndo
        && kqDung.coReset
        && kqDung.coXray,
      kqDung,
    );

    await chup(sess, "2-scene3d");
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── B. Trên desktop chỉ có 1 camera: ẩn nút đổi camera; đóng bằng Escape dừng toàn bộ MediaStreamTrack ── */
  sess = await moTrang(cong, khung, { camera: "mot-cam" });
  try {
    await goChu(sess, "#home-problem-input", DE_BO_SUNG);
    await moCameraTuMenu(sess);
    await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0})()", 6000);
    await sleep(150);
    const coNutDoi = await sess.eval("!!document.querySelector('#btn-photo-switch-camera')");
    await sess._send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await sess._send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    const daDong = await cho(sess, "!document.querySelector('#photo-camera-dialog')", 4000);
    const sauEsc = await json(
      sess,
      "(function(){var c=window.__CAM__;return{"
        + "ended:c.streams.every(function(s){return s.getTracks().every(function(t){return t.readyState==='ended'})}),"
        + "chu:document.querySelector('#home-problem-input').value}})()",
    );
    const dungAnNutDoi = khung.cham ? true : !coNutDoi;
    k("B_MOT_CAMERA_VA_ESCAPE_DUNG_TRACK", dungAnNutDoi && daDong && sauEsc.ended && sauEsc.chu === DE_BO_SUNG, {
      coNutDoi,
      daDong,
      ...sauEsc,
    });
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── E. Tài liệu nhiều bài (needs_selection) -> bảng chọn 1 chạm bên dưới ô nhập -> dựng đúng bài đã chọn ── */
  sess = await moTrang(cong, khung);
  try {
    await datTep(sess, "#home-file-input", tepTam.pdfMultiPath);
    await cho(sess, "!!document.querySelector('#composer-files-wrap .file-preview-card')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const hienChonBai = await cho(sess, "!!document.querySelector('#composer-candidate-picker [data-candidate-id=\"cand-2\"]')", 8000);
    const khongTuDoanBaiDau = await sess.eval(
      "window.__API__.filter(function(r){return r.url.indexOf('/api/analyze')>=0}).length===0",
    );
    await sleep(220);
    await chup(sess, "3-candidate-picker");
    await sess.eval("(function(){document.querySelector('[data-candidate-id=\"cand-2\"]').click();return 1})()");
    const lenCanhBai2 = await cho(sess, "!!document.querySelector('.geo3d-canvas canvas')", 30000);
    const anaBai2 = await json(
      sess,
      "window.__API__.filter(function(r){return r.url.indexOf('/api/analyze')>=0})",
    );
    k(
      "E_NHIEU_BAI_CHON_1_CHAM_KHONG_TU_DOAN",
      hienChonBai && khongTuDoanBaiDau && lenCanhBai2 && anaBai2.length === 1 && anaBai2[0]?.input?.content === DE_BAI_2,
      { hienChonBai, khongTuDoanBaiDau, lenCanhBai2, soAna: anaBai2.length },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── F1. Huỷ xử lý đang chạy (#btn-composer-cancel) giữ nguyên văn bản & chip đính kèm ── */
  sess = await moTrang(cong, khung, { cheDoPrepare: "cham" });
  try {
    await goChu(sess, "#home-problem-input", DE_BO_SUNG);
    await datTep(sess, "#home-file-input", ANH_CORPUS);
    await cho(sess, "!!document.querySelector('#composer-files-wrap .file-preview-card')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const hienNutHuy = await cho(sess, "!!document.querySelector('#btn-composer-cancel')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-cancel').click();return 1})()");
    await sleep(650);
    const sauHuy = await json(
      sess,
      "(function(){return{dangChay:document.querySelector('#btn-composer-send').getAttribute('aria-busy'),"
        + "conChip:!!document.querySelector('#composer-files-wrap .file-preview-card'),"
        + "conChu:document.querySelector('#home-problem-input').value,"
        + "soAna:window.__API__.filter(function(r){return r.url.indexOf('/api/analyze')>=0}).length}})()",
    );
    k(
      "F1_HUY_DANG_CHAY_GIU_NGUYEN_TEP_VA_CHU",
      hienNutHuy && sauHuy.dangChay === "false" && sauHuy.conChip && sauHuy.conChu === DE_BO_SUNG && sauHuy.soAna === 0,
      { hienNutHuy, ...sauHuy },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── F2. Nhiễu trang sách được lọc + xác nhận ký hiệu mờ (needs_confirmation) cho phép sửa văn bản trước khi dựng ── */
  sess = await moTrang(cong, khung, { cheDoPrepare: "confirm" });
  try {
    await datTep(sess, "#home-file-input", ANH_CORPUS);
    await cho(sess, "!!document.querySelector('#composer-files-wrap .file-preview-card')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const hienXacNhan = await cho(sess, "!!document.querySelector('#composer-extraction-confirm #photo-problem-text')", 8000);
    const khoaTruocTick = await sess.eval("document.querySelector('#btn-confirm-extracted-build').disabled");
    await goChu(sess, "#photo-problem-text", DE_DA_SUA);
    await sess.eval("(function(){document.querySelector('#chk-confirm-extracted-text').click();return 1})()");
    await cho(sess, "!document.querySelector('#btn-confirm-extracted-build').disabled", 3000);
    await sess.eval("(function(){document.querySelector('#btn-confirm-extracted-build').click();return 1})()");
    const lenCanhSauSua = await cho(sess, "!!document.querySelector('.geo3d-canvas canvas')", 30000);
    const anaSua = await json(
      sess,
      "window.__API__.filter(function(r){return r.url.indexOf('/api/analyze')>=0})",
    );
    k(
      "F2_LOC_NHIEU_VA_SUA_NOI_DUNG_CHUA_CHAC_CHAN",
      hienXacNhan && khoaTruocTick && lenCanhSauSua && anaSua.length === 1 && anaSua[0]?.input?.content === DE_DA_SUA,
      { hienXacNhan, khoaTruocTick, lenCanhSauSua },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── G. Lỗi quyền / không có camera / thiết bị bận có thông báo phân biệt rõ + fallback chọn ảnh; mobile tự lùi khi camera sau lỗi ── */
  sess = await moTrang(cong, khung, { camera: "tu-choi" });
  try {
    await moCameraTuMenu(sess);
    const hienLoiQuyen = await cho(sess, "!!document.querySelector('[role=alert]')", 5000);
    const loiQuyen = await sess.eval("(document.querySelector('[role=alert]')||{}).textContent||''");
    if (khung.cham) {
      await sess.eval("(function(){var b=document.querySelector('#btn-photo-native-camera');if(b)b.click();return 1})()");
    }
    const bamNative = khung.cham
      ? (await json(sess, "window.__BAM_INPUT__")).some((b) => b.capture === "environment")
      : true;
    await sess.eval("(function(){document.querySelector('#btn-photo-pick-fallback').click();return 1})()");
    await datTep(sess, INPUT_ANH_PHU, ANH_CORPUS);
    const dinhKemTuFallback = await cho(
      sess,
      "!document.querySelector('#photo-camera-dialog')&&!!document.querySelector('#composer-files-wrap .file-preview-card')",
      6000,
    );
    k(
      "G1_LOI_QUYEN_CAMERA_VA_FALLBACK_CHON_ANH",
      hienLoiQuyen && loiQuyen.includes("từ chối") && bamNative && dinhKemTuFallback,
      { loiQuyen, bamNative, dinhKemTuFallback },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  sess = await moTrang(cong, khung, { camera: "khong-co" });
  let loiKhongCo = "";
  try {
    await moCameraTuMenu(sess);
    await cho(sess, "!!document.querySelector('[role=alert]')", 5000);
    loiKhongCo = await sess.eval("(document.querySelector('[role=alert]')||{}).textContent||''");
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  sess = await moTrang(cong, khung, { camera: khung.cham ? "sau-vang" : "ban" });
  try {
    await moCameraTuMenu(sess);
    if (khung.cham) {
      const tuLuiThanhCong = await cho(
        sess,
        "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0&&window.__CAM__.calls===2})()",
        8000,
      );
      k("G2_PHAN_BIET_LOI_THIET_BI_VA_FALLBACK_MOBILE", loiKhongCo.includes("Không tìm thấy máy ảnh") && tuLuiThanhCong, {
        loiKhongCo,
        tuLuiThanhCong,
      });
    } else {
      await cho(sess, "!!document.querySelector('[role=alert]')", 5000);
      const loiBan = await sess.eval("(document.querySelector('[role=alert]')||{}).textContent||''");
      k(
        "G2_PHAN_BIET_LOI_THIET_BI_VA_FALLBACK_MOBILE",
        loiKhongCo.includes("Không tìm thấy máy ảnh") && loiBan.includes("không khả dụng"),
        { loiKhongCo, loiBan },
      );
    }
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── H. Hạ tầng tắt đọc ảnh (503 LIVE_AI_DISABLED) không lộ biến môi trường + không tràn ngang + bẫy Tab giữ focus ── */
  sess = await moTrang(cong, khung, { cheDoPrepare: "tat" });
  try {
    await moCameraTuMenu(sess);
    await cho(sess, "(function(){var v=document.querySelector('.photo-camera-video');return v&&v.videoWidth>0})()", 8000);
    const kCam = await trongKhung(sess, khung.w);
    for (let i = 0; i < 6; i++) {
      await sess._send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
      await sess._send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    }
    const giuFocus = await sess.eval(
      "(function(){var d=document.querySelector('#photo-camera-dialog');return !!d&&d.contains(document.activeElement)})()",
    );
    await sess.eval("(function(){document.querySelector('#btn-photo-dialog-close').click();return 1})()");
    await cho(sess, "!document.querySelector('#photo-camera-dialog')", 4000);

    await datTep(sess, "#home-file-input", ANH_CORPUS);
    await cho(sess, "!!document.querySelector('#composer-files-wrap .file-preview-card')", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const hienLoi503 = await cho(
      sess,
      "document.body.innerText.indexOf('chưa sẵn sàng')>=0||document.body.innerText.indexOf('tạm tắt')>=0",
      6000,
    );
    const khongLoBien = await sess.eval(
      "document.body.innerText.indexOf('ALLOW_LIVE_AI')<0&&document.body.innerText.indexOf('GEMINI_API_KEY')<0",
    );
    const kHome = await trongKhung(sess, khung.w);
    const okKhung = (x) => x.innerWidth <= khung.w + 1 && x.cuonNgang <= khung.w + 1 && x.ngoai.length === 0;
    k(
      "H_503_AN_BIEN_KHONG_TRAN_NGANG_VA_BAY_TAB",
      giuFocus && hienLoi503 && khongLoBien && okKhung(kCam) && okKhung(kHome),
      { giuFocus, hienLoi503, khongLoBien, kCam, kHome },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  /* ── I. Luồng gõ tay thuần văn bản không hồi quy ── */
  sess = await moTrang(cong, khung);
  try {
    await goChu(sess, "#home-problem-input", DE_GO_TAY);
    await cho(sess, "!document.querySelector('#btn-composer-send').disabled", 4000);
    await sess.eval("(function(){document.querySelector('#btn-composer-send').click();return 1})()");
    const canh = await cho(sess, "!!document.querySelector('.geo3d-canvas canvas')", 30000);
    const yc = await json(sess, "window.__API__.filter(function(r){return r.url.indexOf('/api/health')<0})");
    const dung = yc.filter((r) => r.url.includes("/api/analyze"));
    k(
      "I_GO_TAY_THUAN_KHONG_HOI_QUY",
      canh
        && dung.length === 1
        && dung[0]?.input?.content === DE_GO_TAY
        && yc.every((r) => !r.url.includes("/api/input/prepare") && !r.url.includes("/api/image/extract")),
      { soYeuCau: yc.length, soAnalyze: dung.length },
    );
    loiTrang.push(...sess.consoleEvents.filter((e) => e.loai === "exception"));
  } finally {
    await sess.close();
  }

  ca.loiTrang = loiTrang;
  k("Z_KHONG_LOI_CONSOLE_EXCEPTION", loiTrang.length === 0, loiTrang.slice(0, 5));
  ca.dat = Object.values(ca.kiem).every((x) => x.dat);
  return ca;
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  kiemDistMoi();
  const thuMucTam = mkdtempSync(join(tmpdir(), "axo-unified-e2e-"));
  const tepTam = taoTepTam(thuMucTam);
  const { sv, cong } = await phucVu(DIST);
  const kq = {
    schema: "unified-problem-input-browser-check/1",
    commit,
    chay_luc: new Date().toISOString(),
    BANG_CHUNG:
      "FIXTURE_UI — /api/input/prepare và /api/analyze bị chặn ở biên mạng; máy ảnh GIẢ LẬP (getUserMedia + enumerateDevices qua canvas.captureStream)",
    APPLICATION_LLM_CALLS: 0,
    REAL_CAMERA_DEVICE_VERIFIED: "NO",
    LIVE_GEMINI_IMAGE_EXTRACTION_VERIFIED: "NO",
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
      const ca = await motKhung(cong, khung, tepTam);
      kq.ca.push(ca);
      for (const [ma, v] of Object.entries(ca.kiem)) {
        console.log("  " + ca.khung + " " + ma + ": " + (v.dat ? "ĐẠT" : "KHÔNG ĐẠT"));
      }
    }
  } finally {
    sv.close();
    rmSync(thuMucTam, { recursive: true, force: true });
  }
  kq.dat = kq.ca.every((c) => c.dat);
  mkdirSync(RA, { recursive: true });
  const duongDanJson = join(RA, "PHOTO_BROWSER_CHECK.json");
  writeFileSync(duongDanJson, JSON.stringify(kq, null, 2) + "\n", "utf-8");
  console.log("-> " + duongDanJson + "  " + (kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"));
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
