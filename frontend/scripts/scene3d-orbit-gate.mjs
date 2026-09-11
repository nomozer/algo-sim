/**
 * scene3d-orbit-gate.mjs — CỔNG QUAY: đủ 360°, sáu hướng, trục ổn định.
 *
 * ─── VÌ SAO KHÔNG DÙNG LẠI `scene3d-interaction-probe.mjs` ────────────────
 *
 * Probe đo **độ mượt và độ ổn định của trục** trong một cú kéo ngắn. Cổng này
 * hỏi câu khác hẳn: *người học có quay được hết hình không*. Câu ấy cần tư thế
 * camera TUYỆT ĐỐI (phương vị, góc cực), không chỉ cần biến thiên giữa hai
 * khung. Gộp hai câu vào một script thì mỗi lần sửa câu này lại làm số của câu
 * kia mất giá trị.
 *
 * ─── LẤY TƯ THẾ CAMERA MÀ KHÔNG ĐỤNG MÃ SẢN PHẨM ─────────────────────────
 *
 * Camera nằm trong closure của `Scene3DWorkspace`. Nhưng mọi shader của
 * three.js đều nhận `viewMatrix` làm uniform, và **ma trận ấy giống nhau ở mọi
 * lệnh vẽ trong cùng một khung** — trong khi `modelViewMatrix` đổi theo từng
 * vật. Nên trong một khung, gom mọi ma trận 4×4 đi qua `uniformMatrix4fv` rồi:
 *
 *   ① nhóm theo **VỊ TRÍ UNIFORM**, bỏ vị trí nào nhận nhiều hơn một giá trị
 *      trong cùng một khung — đó là `modelViewMatrix`;
 *   ② bỏ ma trận chiếu (phối cảnh có `m[15] === 0`, biến đổi cứng thì `=== 1`);
 *   ③ trong phần còn lại, lấy giá trị được NHIỀU VỊ TRÍ khác nhau cùng ghi.
 *
 * ⚠️ Bản đầu đếm tần suất **giá trị** thay vì nhóm theo vị trí. Nó đúng ở p1
 * rồi sai ở p6/p7 — hai ca ấy có nhiều vành cùng một tâm nên các
 * `modelViewMatrix` trùng nhau và áp đảo `viewMatrix` về số lần đếm. Triệu
 * chứng là cổng báo `TRUC_TROI` cho p6/p7 trong khi probe độc lập đọc ra trục
 * `[0,0,1]` chuẩn 1,000. Dấu hiệu bắt được lỗi đo: **cửa sổ đứng yên khác 0**
 * (1,6–1,9° khi không ai chạm chuột). Sau khi nhóm theo vị trí, cửa sổ ấy về
 * đúng 0,0° ở cả ba ca — đó là phép tự kiểm của bộ đo.
 *
 * Từ `viewMatrix` cột-chính `m`, hướng từ ĐIỂM NHÌN tới CAMERA là `(m2,m6,m10)`
 * — không cần biết `target` ở đâu:
 *
 *   phương vị = atan2(m6, m2)        góc cực = acos(m10)
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong chuỗi tiêm vào trang.
 */
import { createServer } from "node:http";
import { existsSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve, extname } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const GOC = resolve(CO.goc ?? join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const RA = resolve(CO.ra ?? join(GOC, "docs", "evaluation", "geometry", "scene3d-orbit-gate"));
const TAGS = (CO.ca ?? "p1,p6,p7").split(",");
const TIEM = CO.tiem ? String(CO.tiem) : null;

/** Ngưỡng đã khai TRƯỚC khi đo — không nới sau khi thấy số. */
export const NGUONG = {
  /** Chuẩn của trục quay trung bình. 1 = bàn xoay; <1 = lộn nhào. */
  CHUAN_TRUC: 0.99,
  /** Phương vị tháo cuộn tối thiểu của một cú kéo ngang dài. */
  VONG_NGANG_DO: 360,
  /** |cos(góc cực)| để coi là đã tới đỉnh/đáy. */
  COS_CUC: 0.9,
  /** Bước nhảy tư thế giữa hai khung coi là SNAP (độ). */
  SNAP_DO: 25,
};

export const TRANG_THAI = {
  DAT: "DAT",
  TRUC_TROI: "TRUC_TROI",
  KHONG_DU_VONG: "KHONG_DU_VONG",
  THIEU_HUONG_NHIN: "THIEU_HUONG_NHIN",
  CO_SNAP: "CO_SNAP",
  TU_KHOP_KHUNG: "TU_KHOP_KHUNG",
  CANH_RONG: "CANH_RONG",
  KHONG_DOC_DUOC_CAMERA: "KHONG_DOC_DUOC_CAMERA",
  /** Không có canvas nào để đo — cảnh không dựng nổi (thường là crash vòng lặp). */
  CANH_KHONG_DUNG: "CANH_KHONG_DUNG",
};

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".woff2": "font/woff2", ".ico": "image/x-icon" };

export function phucVu(thuMuc, thieuChunk = false) {
  return new Promise((res) => {
    const sv = createServer((rq, rp) => {
      let p = decodeURIComponent(rq.url.split("?")[0]);
      if (p === "/") p = "/index.html";
      // Phép tiêm ⑧: chunk JS biến mất. Server KHÔNG được trả index.html thay —
      // làm vậy thì chunk mất vẫn HTTP 200 và cổng không thấy gì.
      if (thieuChunk && /assets\/index-.*\.js$/.test(p)) { rp.writeHead(404); rp.end(""); return; }
      let f = join(thuMuc, p);
      if (!existsSync(f) || statSync(f).isDirectory()) {
        if (extname(p) !== "") { rp.writeHead(404); rp.end("khong co"); return; }
        f = join(thuMuc, "index.html");
      }
      rp.writeHead(200, { "Content-Type": MIME[extname(f)] ?? "application/octet-stream" });
      rp.end(readFileSync(f));
    });
    let i = 0;
    const congs = [0, 8261, 8262, 8263, 8264, 8265, 8266];
    const thu = () => {
      sv.removeAllListeners("error");
      sv.once("error", () => { i += 1; if (i < congs.length) thu(); });
      sv.listen(congs[i], "127.0.0.1", () => res({ sv, cong: sv.address().port }));
    };
    thu();
  });
}

/* ─── móc đo, tiêm TRƯỚC mọi script của trang ─── */
const MOC = `
(function () {
  var D = { tuThe: [], draws: 0, buffers: 0, programs: 0, canvasTao: 0, ctxs: 0, moc: '' };
  window.__QUAY__ = D;
  D.reset = function (nhan) { D.moc = nhan; D.tuThe.length = 0; D.draws = 0;
    D.buffers = 0; D.programs = 0; D.canvasTao = 0; };

  var ceGoc = Document.prototype.createElement;
  Document.prototype.createElement = function (t) {
    if (String(t).toLowerCase() === 'canvas') D.canvasTao += 1;
    return ceGoc.apply(this, arguments);
  };

  /* ─── NHẬN DẠNG "viewMatrix", nhóm theo VỊ TRÍ UNIFORM ──────────────────
   *
   * Bản đầu đếm tần suất GIÁ TRỊ và lấy ma trận lặp nhiều nhất. Nó đúng ở p1
   * rồi sai ở p6/p7: hai ca ấy có nhiều vành/đường cùng một tâm, nên các
   * "modelViewMatrix" TRÙNG NHAU và áp đảo "viewMatrix" về số lần.
   *
   * Dấu hiệu thật nằm ở CHỖ GHI, không ở giá trị. Trong một khung, three.js
   * ghi "modelViewMatrix" **nhiều giá trị khác nhau** vào cùng một vị trí
   * uniform (mỗi vật một giá trị), còn "viewMatrix" thì mọi lần ghi đều **cùng
   * một giá trị**. Nên:
   *
   *   ① bỏ vị trí nào nhận nhiều hơn một giá trị trong khung → đó là modelView;
   *   ② trong các vị trí còn lại, lấy giá trị được NHIỀU VỊ TRÍ KHÁC NHAU cùng
   *      ghi — "viewMatrix" của mọi program đều mang cùng một giá trị, còn
   *      modelView của một vật đơn độc thì không ai đồng ý cùng.
   */
  var idViTri = new WeakMap(), demViTri = 0;
  function khoaViTri(loc) {
    if (!loc) return 'nil';
    var id = idViTri.get(loc);
    if (id === undefined) { id = ++demViTri; idViTri.set(loc, id); }
    return id;
  }
  var khung = new Map();   // khoá vị trí → { giaTri, nhieu }
  function chot() {
    if (khung.size === 0) return;
    var theoGiaTri = new Map();
    khung.forEach(function (v) {
      if (v.nhieu) return;                        // ① nhiều giá trị ⇒ modelView
      if (Math.abs(v.giaTri[15] - 1) > 1e-6) return;  // ma trận chiếu ⇒ bỏ
      var k = v.giaTri.join(',');
      theoGiaTri.set(k, (theoGiaTri.get(k) || 0) + 1);
    });
    var tot = null, totN = 0;
    theoGiaTri.forEach(function (n, k) { if (n > totN) { totN = n; tot = k; } });
    if (tot) {
      var m = tot.split(',').map(Number);
      var pv = Math.atan2(m[6], m[2]) * 180 / Math.PI;
      var cuc = Math.acos(Math.max(-1, Math.min(1, m[10]))) * 180 / Math.PI;
      D.tuThe.push({ pv: pv, cuc: cuc, cos: m[10], viTri: totN, t: performance.now() });
    }
    khung = new Map();
  }

  var gcGoc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (kind) {
    var ctx = gcGoc.apply(this, arguments);
    if (ctx && /webgl/.test(String(kind)) && !ctx.__daBoc) {
      ctx.__daBoc = true; D.ctxs += 1;
      var de = ctx.drawElements.bind(ctx), da = ctx.drawArrays.bind(ctx);
      var cb = ctx.createBuffer.bind(ctx), cp = ctx.createProgram.bind(ctx);
      var um = ctx.uniformMatrix4fv.bind(ctx);
      ctx.drawElements = function () { D.draws += 1; return de.apply(null, arguments); };
      ctx.drawArrays = function () { D.draws += 1; return da.apply(null, arguments); };
      ctx.createBuffer = function () { D.buffers += 1; return cb.apply(null, arguments); };
      ctx.createProgram = function () { D.programs += 1; return cp.apply(null, arguments); };
      ctx.uniformMatrix4fv = function (loc, tr, v) {
        if (v && v.length === 16) {
          var k = khoaViTri(loc);
          var cu = khung.get(k);
          var moi = Array.prototype.slice.call(v);
          if (!cu) khung.set(k, { giaTri: moi, nhieu: false });
          else if (!cu.nhieu && cu.giaTri.join(',') !== moi.join(',')) cu.nhieu = true;
        }
        return um.apply(null, arguments);
      };
    }
    return ctx;
  };

  var raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (fn) {
    return raf(function (t) { chot(); return fn(t); });
  };
})();
`;

/** Tháo cuộn một dãy phương vị (độ) thành đường đi liên tục. */
export function thaoCuon(pv) {
  if (pv.length === 0) return { tong: 0, chuoi: [] };
  const chuoi = [pv[0]];
  let tong = 0;
  for (let i = 1; i < pv.length; i++) {
    let d = pv[i] - pv[i - 1];
    while (d > 180) d -= 360;
    while (d < -180) d += 360;
    tong += d;
    chuoi.push(chuoi[i - 1] + d);
  }
  return { tong, chuoi };
}

/** Trục quay trung bình suy từ dãy tư thế: quay quanh z ⇒ góc cực đứng yên. */
export function chuanTruc(tuThe) {
  if (tuThe.length < 3) return 0;
  // Với quỹ đạo quanh trục z, |Δcực| phải ≈ 0 trong khi phương vị chạy.
  let dPv = 0, dCuc = 0;
  for (let i = 1; i < tuThe.length; i++) {
    let a = tuThe[i].pv - tuThe[i - 1].pv;
    while (a > 180) a -= 360;
    while (a < -180) a += 360;
    dPv += Math.abs(a);
    dCuc += Math.abs(tuThe[i].cuc - tuThe[i - 1].cuc);
  }
  if (dPv + dCuc === 0) return 0;
  return dPv / (dPv + dCuc);
}

/** Sáu hướng nhìn đã chạm tới chưa. */
export function sauHuong(tuThe) {
  const ra = { truoc: false, sau: false, trai: false, phai: false, tren: false, duoi: false };
  for (const t of tuThe) {
    if (t.cos > NGUONG.COS_CUC) { ra.tren = true; continue; }
    if (t.cos < -NGUONG.COS_CUC) { ra.duoi = true; continue; }
    const a = ((t.pv % 360) + 360) % 360;
    if (a < 45 || a >= 315) ra.truoc = true;
    else if (a < 135) ra.phai = true;
    else if (a < 225) ra.sau = true;
    else ra.trai = true;
  }
  return ra;
}

/** Số lần tư thế nhảy quá `SNAP_DO` giữa hai khung liên tiếp. */
export function demSnap(tuThe, nguong = NGUONG.SNAP_DO) {
  let n = 0;
  for (let i = 1; i < tuThe.length; i++) {
    let a = tuThe[i].pv - tuThe[i - 1].pv;
    while (a > 180) a -= 360;
    while (a < -180) a += 360;
    const d = Math.hypot(a, tuThe[i].cuc - tuThe[i - 1].cuc);
    if (d > nguong) n += 1;
  }
  return n;
}

export async function motCa(sess, fx) {
  const env = JSON.stringify(fx.envelope);
  await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState().loadEnvelope(${env});return 1})()`);
  for (let i = 0; i < 60; i++) {
    const n = await sess.eval(
      "document.querySelectorAll('.geo3d-canvas canvas').length");
    if (n > 0) break;
    await sleep(200);
  }
  const soBuoc = fx.expected_trace_event_count ?? 1;
  for (let i = 0; i < soBuoc + 4; i++) {
    const b = await sess.eval(
      "(function(){var e=document.querySelector('.geo3d-buoc-so');return e?e.textContent:'';})()");
    const m = /(\d+)\s*\/\s*(\d+)/.exec(b);
    if (m && m[1] === m[2]) break;
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');"
      + "if(b&&!b.disabled)b.click();return 1})()");
    await sleep(80);
  }
  await sleep(500);

  /* Cảnh không dựng nổi thì trả về một trạng thái CÓ TÊN, không ném.
   * Phép tiêm "auto-fit khi đang xoay" đi đúng đường này: khớp khung gọi
   * `update()`, `update()` phát `change`, `change` gọi lại khớp khung — đệ quy
   * vô hạn, React tháo cây, canvas biến mất. Một cổng ném ngoại lệ ở đây sẽ
   * trông y như lỗi hạ tầng. */
  const hopThô = await sess.eval(
    "(function(){var c=document.querySelector('.geo3d-canvas canvas');"
    + "if(!c) return 'KHONG_CO_CANVAS';"
    + "var r=c.getBoundingClientRect();"
    + "return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});})()");
  if (typeof hopThô !== "string" || hopThô.indexOf("{") !== 0) {
    return { tag: fx.tag, trangThai: TRANG_THAI.CANH_KHONG_DUNG, chiTiet: String(hopThô),
      docDuocCamera: false, vongNgangDo: 0, nhieuVongDo: 0, chuanTruc: 0,
      cucMin: 0, cucMax: 0, huong: {}, snap: 0, capPhat: 0, draws: 0, ctxs: 0,
      yenTong: 0, khungDo: {} };
  }
  const hop = JSON.parse(hopThô);
  const cx = Math.round(hop.x + hop.w / 2);
  const cy = Math.round(hop.y + hop.h / 2);
  const chuot = (type, x, y, buttons) => sess._send("Input.dispatchMouseEvent",
    { type, x: Math.round(x), y: Math.round(y), button: "left", buttons, clickCount: 1 });

  /**
   * Một cử chỉ kéo liên tục: nhấn, đi qua các mốc, thả.
   *
   * ⚠️ Cả điểm đầu lẫn điểm cuối phải nằm TRONG canvas. `mousePressed` rơi ra
   * ngoài thì OrbitControls không nhận cử chỉ nào cả, và cổng đọc ra "camera
   * đứng yên" — một kết luận sai trông y như trục bị kẹt.
   *
   * Quy đổi của OrbitControls: kéo ngang `dx` px quay `2π·dx/clientHeight`.
   * Với canvas ~545 px cao thì 545 px ngang ≈ 360°; ở đây lấy dư một quãng.
   */
  const keo = async (dx, dy, buoc = 60) => {
    const bienX = Math.max(40, hop.w / 2 - 20);
    const bienY = Math.max(40, hop.h / 2 - 20);
    const x0 = cx - Math.min(Math.abs(dx) / 2, bienX) * Math.sign(dx || 1);
    const y0 = cy - Math.min(Math.abs(dy) / 2, bienY) * Math.sign(dy || 1);
    const x1 = x0 + dx, y1 = y0 + dy;
    await chuot("mousePressed", x0, y0, 1);
    for (let i = 1; i <= buoc; i++) {
      await chuot("mouseMoved", x0 + ((x1 - x0) * i) / buoc,
        y0 + ((y1 - y0) * i) / buoc, 1);
      await sleep(10);
    }
    await chuot("mouseReleased", x1, y1, 0);
    await sleep(250);
  };

  const doc = async () => JSON.parse(await sess.eval(
    "JSON.stringify({tuThe:window.__QUAY__.tuThe.slice(),draws:window.__QUAY__.draws,"
    + "buffers:window.__QUAY__.buffers,programs:window.__QUAY__.programs,"
    + "canvasTao:window.__QUAY__.canvasTao,ctxs:window.__QUAY__.ctxs})"));
  const dat = async (nhan) => sess.eval(
    `(function(){window.__QUAY__.reset('${nhan}');return 1})()`);

  // ── ① đứng yên: chứng rằng phép đọc tư thế không tự bịa chuyển động ──
  await dat("yen");
  await sleep(900);
  const yen = await doc();

  // ── ② một cú kéo ngang DÀI: phải tháo cuộn quá 360° ──
  await dat("vong");
  await keo(700, 0, 70);
  const vong = await doc();

  // ── ③ kéo tiếp hai cú cùng chiều: không được đụng tường nào ──
  await dat("nhieuvong");
  await keo(700, 0, 70);
  await keo(700, 0, 70);
  const nhieuVong = await doc();

  // ── ④ kéo dọc lên tới đỉnh, rồi xuống tới đáy ──
  await dat("doc");
  await keo(0, -380, 50);
  await keo(0, 420, 55);
  await keo(0, 420, 55);
  const doc2 = await doc();

  const tatCa = [...vong.tuThe, ...nhieuVong.tuThe, ...doc2.tuThe];
  const huong = sauHuong(tatCa);
  const capPhat = vong.buffers + vong.programs + vong.canvasTao
    + nhieuVong.buffers + nhieuVong.programs + nhieuVong.canvasTao
    + doc2.buffers + doc2.programs + doc2.canvasTao;

  return {
    tag: fx.tag,
    docDuocCamera: vong.tuThe.length > 5,
    khungDo: { yen: yen.tuThe.length, vong: vong.tuThe.length,
      nhieuVong: nhieuVong.tuThe.length, doc: doc2.tuThe.length },
    yenTong: Math.abs(thaoCuon(yen.tuThe.map((t) => t.pv)).tong),
    vongNgangDo: Math.abs(thaoCuon(vong.tuThe.map((t) => t.pv)).tong),
    nhieuVongDo: Math.abs(thaoCuon(nhieuVong.tuThe.map((t) => t.pv)).tong),
    chuanTruc: chuanTruc(vong.tuThe),
    cucMin: Math.min(...doc2.tuThe.map((t) => t.cos)),
    cucMax: Math.max(...doc2.tuThe.map((t) => t.cos)),
    huong,
    snap: demSnap(vong.tuThe) + demSnap(nhieuVong.tuThe),
    capPhat,
    ctxs: vong.ctxs,
    draws: vong.draws,
  };
}

export function phanLoai(r) {
  if (!r.docDuocCamera) return TRANG_THAI.KHONG_DOC_DUOC_CAMERA;
  if (r.draws === 0) return TRANG_THAI.CANH_RONG;
  if (r.chuanTruc < NGUONG.CHUAN_TRUC) return TRANG_THAI.TRUC_TROI;
  if (r.vongNgangDo < NGUONG.VONG_NGANG_DO) return TRANG_THAI.KHONG_DU_VONG;
  if (!Object.values(r.huong).every(Boolean)) return TRANG_THAI.THIEU_HUONG_NHIN;
  if (r.snap > 0) return TRANG_THAI.CO_SNAP;
  if (r.capPhat > 0) return TRANG_THAI.TU_KHOP_KHUNG;
  return TRANG_THAI.DAT;
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  const { sv, cong } = await phucVu(DIST, TIEM === "thieu-chunk");
  const kq = { commit, chay_luc: new Date().toISOString(), tiem: TIEM, nguong: NGUONG, ca: [] };
  try {
    const sess = new BrowserSession({ viewport: 1440, height: 900, webgl: true,
      url: `http://127.0.0.1:${cong}`, napModuleDev: false });
    await sess.open();
    await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC });
    await sess._send("Page.reload", {});
    await sleep(2500);
    const thu = join(GOC, "docs", "evaluation", "geometry",
      "product-ui-result-rendering", "fixtures");
    for (const tag of TAGS) {
      const { readdirSync } = await import("node:fs");
      const ten = readdirSync(thu).find((x) => x.startsWith(`${tag}_`));
      const fx = { tag, ...JSON.parse(readFileSync(join(thu, ten), "utf-8")) };
      const r = await motCa(sess, fx);
      r.trangThai = r.trangThai ?? phanLoai(r);
      kq.ca.push(r);
      console.log(`  ${tag}: ${r.trangThai}  vòng=${r.vongNgangDo.toFixed(0)}°  `
        + `trục=${r.chuanTruc.toFixed(3)}  cos∈[${r.cucMin.toFixed(2)},${r.cucMax.toFixed(2)}]  `
        + `snap=${r.snap}  cấp phát=${r.capPhat}  yên=${r.yenTong.toFixed(1)}°`);
    }
    await sess.close();
  } finally { sv.close(); }
  kq.dat = kq.ca.every((c) => c.trangThai === TRANG_THAI.DAT);
  mkdirSync(RA, { recursive: true });
  const ten = TIEM ? `ORBIT_GATE_TIEM_${TIEM}.json` : "ORBIT_GATE.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
