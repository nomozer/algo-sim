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
 * `[0,0,1]` chuẩn 1,000.
 *
 * ⚠️ **Cửa sổ đứng yên khác 0 KHÔNG phải dấu hiệu của lỗi đo ấy** — bản chú
 * thích trước nói vậy và nó sai. Kiểm lại 2026-09-12: để cảnh lắng thêm 2 giây
 * rồi mới mở cửa sổ thì thu được **0 khung**, vì renderer chỉ vẽ khi có việc.
 * Những khung ấy có thật; chúng là đuôi damping còn chạy nốt sau loạt bấm
 * "Bước sau". Nay cửa sổ mở sau khi cảnh lắng và đọc 0,0–0,3° ở mọi bản dựng.
 *
 * Từ `viewMatrix` cột-chính `m`, hướng từ ĐIỂM NHÌN tới CAMERA là `(m2,m6,m10)`
 * — không cần biết `target` ở đâu:
 *
 *   phương vị = atan2(m6, m2)        góc cực = acos(m10)
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong chuỗi tiêm vào trang.
 */
import { createServer } from "node:http";
import { existsSync, readFileSync, writeFileSync, mkdirSync, statSync, readdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve, extname } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const GOC = resolve(CO.goc ?? join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
/**
 * Bản dựng đem đo. Mặc định `frontend/dist` của chính kho này.
 *
 * `--dist <đường dẫn>` trỏ sang một bản dựng KHÁC — thường là `dist/` của một
 * worktree ở commit cũ. Có nó thì mới đối chiếu được **cùng một cổng** qua
 * nhiều mốc, và đó chính là phép thử đã lộ ra rằng công thức trục cũ chấm bản
 * trục-cố-định thấp hơn bản trục-trôi (xem `trucQuay`). Không có cờ này thì
 * mỗi lần nghi ngờ cổng lại phải viết một bộ đo riêng — và bộ đo riêng ấy tự
 * nó cũng chưa được chứng.
 */
const DIST = CO.dist ? resolve(String(CO.dist)) : join(FE, "dist");
/** Đo bản dựng ngoài ⇒ `kiemDistMoi` vô nghĩa (nó so với `src/` của kho này). */
const DIST_NGOAI = Boolean(CO.dist);
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
      D.tuThe.push({ pv: pv, cuc: cuc, cos: m[10], viTri: totN, t: performance.now(),
        m: m });
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

/* ═══ TRỤC QUAY — ĐO ĐỘ NHẤT QUÁN, KHÔNG ĐO "CÓ PHẢI TRỤC Z KHÔNG" ═══════
 *
 * ⚠️ Bản trước của hàm này đo **nhầm đại lượng**, và cái tên `chuanTruc` khiến
 * không ai nghi. Nó lấy `dPv / (dPv + dCuc)` với phương vị/cực định nghĩa
 * quanh trục **Z**, tức nó trả lời *"có quay quanh Z không"* chứ không phải
 * *"trục có cố định không"*. Hai câu ấy khác nhau, và sự khác ấy đã ship một
 * phán quyết sai.
 *
 * ─── ĐO ĐƯỢC, TRÊN BA BẢN DỰNG ───────────────────────────────────────────
 *
 * Cùng một cú kéo NGANG THUẦN 300 px, cùng khung nhìn, cùng DPR:
 *
 * | bản dựng   | ‖trục‖ ĐÚNG | trục thật              | hàm cũ đọc ra |
 * |------------|-------------|------------------------|---------------|
 * | `e6c2330`  | **1,000**   | `[0, 1, 0]` — cố định  | 0,525–0,532   |
 * | `1a553b8`  | **1,000**   | `[0, 1, 0]` — cố định  | 0,526–0,531   |
 * | `56350f7`  | 0,600–0,610 | `[0,57; −0,05; 0,82]`  | 0,546–0,548   |
 *
 * Hàng cuối là ca trục **trôi thật** (`SCENE3D_INTERACTION_SMOOTHNESS_
 * REGRESSION_DIAGNOSIS` đo độc lập: 0,608–0,680). Hàm cũ chấm nó **CAO HƠN**
 * hai bản có trục cố định tuyệt đối — trong dải này nó **nghịch chiều** với
 * thứ nó khai là đang đo. Nó chỉ trông đúng khi sản phẩm tình cờ quay quanh Z.
 *
 * ─── CÔNG THỨC ĐÚNG, chép từ báo cáo chẩn đoán ───────────────────────────
 *
 * Với hai ma trận liên tiếp `A`, `B`: `R = Aᵀ·B`, rút trục từ phần phản đối
 * xứng, **chuẩn hoá dấu** (ép thành phần lớn nhất dương để trục và trục đối
 * không triệt tiêu nhau khi lấy trung bình), rồi trung bình vectơ đơn vị.
 *
 *   ‖trung bình‖ = 1  ⇔ mọi khung quay quanh CÙNG một trục → bàn xoay
 *   ‖trung bình‖ < 1  ⇔ trục đổi giữa các khung → lộn nhào
 *
 * Đại lượng này **không giả định trục nào**. Quay quanh Y cho 1,000 y như
 * quay quanh Z — và đó là điểm mấu chốt: *"trục là Y"* là một **sự kiện**,
 * không phải một lỗi.
 */

const _g = (m, r, c) => m[c * 4 + r];

/** Trục quay giữa hai ma trận, đã chuẩn hoá dấu. `null` khi không quay. */
function trucGiuaHaiKhung(a, b) {
  const R = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      let s = 0;
      for (let k = 0; k < 3; k++) s += _g(a, k, i) * _g(b, k, j);
      R[i][j] = s;
    }
  }
  const v = [R[2][1] - R[1][2], R[0][2] - R[2][0], R[1][0] - R[0][1]];
  const n = Math.hypot(v[0], v[1], v[2]);
  if (n < 1e-9) return null;
  const u = v.map((x) => x / n);
  const k = u.map(Math.abs).indexOf(Math.max(...u.map(Math.abs)));
  return u[k] < 0 ? u.map((x) => -x) : u;
}

/**
 * Trục quay trung bình và độ nhất quán của nó.
 *
 * Trả `{ vec, chuan }`: `vec` là trục đơn vị trung bình, `chuan` ∈ [0, 1] là
 * độ nhất quán. `chuan` mới là thứ `TRUC_TROI` được phép nhìn vào.
 */
export function trucQuay(tuThe) {
  const mats = tuThe.map((t) => t.m).filter((m) => m && m.length === 16);
  if (mats.length < 3) return { vec: [0, 0, 0], chuan: 0, soMau: 0 };
  const us = [];
  for (let i = 1; i < mats.length; i++) {
    const t = trucGiuaHaiKhung(mats[i - 1], mats[i]);
    if (t) us.push(t);
  }
  if (us.length === 0) return { vec: [0, 0, 0], chuan: 0, soMau: 0 };
  const tb = [0, 1, 2].map((k) => us.reduce((s, u) => s + u[k], 0) / us.length);
  const chuan = Math.hypot(...tb);
  return {
    vec: (chuan > 1e-9 ? tb.map((x) => x / chuan) : [0, 0, 0]).map((x) => +x.toFixed(3)),
    chuan: +chuan.toFixed(3),
    soMau: us.length,
  };
}

/**
 * Tổng góc quay giữa các khung liên tiếp, độ — KHÔNG phụ thuộc trục.
 * `acos((tr(Aᵀ·B) − 1)/2)`, cùng công thức với báo cáo chẩn đoán.
 */
export function tongGocKhung(tuThe) {
  const mats = tuThe.map((t) => t.m).filter((m) => m && m.length === 16);
  let tong = 0;
  for (let i = 1; i < mats.length; i++) {
    const a = mats[i - 1], b = mats[i];
    let s = 0;
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) s += _g(a, r, c) * _g(b, r, c);
    const na = Math.hypot(_g(a, 0, 0), _g(a, 1, 0), _g(a, 2, 0));
    const nb = Math.hypot(_g(b, 0, 0), _g(b, 1, 0), _g(b, 2, 0));
    tong += Math.acos(Math.max(-1, Math.min(1, (s / (na * nb) - 1) / 2))) * 180 / Math.PI;
  }
  return tong;
}

/** Tên trục cho người đọc — THÔNG TIN, không phải phán quyết. */
export function tenTruc(vec) {
  const [x, y, z] = vec.map(Math.abs);
  if (y > 0.95) return "Y";
  if (z > 0.95) return "Z";
  if (x > 0.95) return "X";
  return "chéo";
}

/**
 * Tổng góc quay QUANH CHÍNH TRỤC ĐÃ ĐO — không phải phương vị quanh Z.
 *
 * ⚠️ `thaoCuon(pv)` giả định trục Z y như hàm trục cũ: trên một bản quay quanh
 * Y nó đọc ra 12° cho một cú kéo dài cả nghìn độ, vì phương vị theo Z không
 * cộng dồn khi trục là Y. Ở đây chiếu hướng nhìn xuống mặt phẳng ⟂ trục rồi
 * cộng dồn góc trong mặt phẳng ấy.
 */
export function vongQuanhTruc(tuThe, truc) {
  const mats = tuThe.map((t) => t.m).filter((m) => m && m.length === 16);
  if (mats.length < 2 || Math.hypot(...truc) < 0.5) return 0;
  const a = truc;
  /* Hai vectơ đơn vị trực giao với trục, làm hệ toạ độ trong mặt phẳng quay. */
  const tam = Math.abs(a[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
  const e1n = [a[1] * tam[2] - a[2] * tam[1], a[2] * tam[0] - a[0] * tam[2],
    a[0] * tam[1] - a[1] * tam[0]];
  const n1 = Math.hypot(...e1n);
  if (n1 < 1e-9) return 0;
  const e1 = e1n.map((x) => x / n1);
  const e2 = [a[1] * e1[2] - a[2] * e1[1], a[2] * e1[0] - a[0] * e1[2],
    a[0] * e1[1] - a[1] * e1[0]];
  let tong = 0, truoc = null;
  for (const m of mats) {
    const d = [_g(m, 2, 0), _g(m, 2, 1), _g(m, 2, 2)];
    const goc = Math.atan2(
      d[0] * e2[0] + d[1] * e2[1] + d[2] * e2[2],
      d[0] * e1[0] + d[1] * e1[1] + d[2] * e1[2],
    ) * 180 / Math.PI;
    if (truoc !== null) {
      let dd = goc - truoc;
      while (dd > 180) dd -= 360;
      while (dd < -180) dd += 360;
      tong += dd;
    }
    truoc = goc;
  }
  return Math.abs(tong);
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
      trucQuayVec: [0, 0, 0], trucTen: "không đọc được",
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
  /* Đợi damping lắng HẲN trước khi mở cửa sổ. Không đợi thì cửa sổ bắt phải
     đuôi chuyển động của chính loạt bấm "Bước sau" và đọc ra 1,6–2,0°, trông
     y như bộ đo tự bịa — xem chú thích ở `yenTong`. */
  await sleep(2000);
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
    /* CỬA SỔ CHỨNG: không ai chạm chuột ⇒ phải bằng 0.
     *
     * Đo bằng TỔNG GÓC giữa hai khung, không bằng phương vị quanh Z — phương vị
     * quanh Z không cộng dồn khi trục quay là Y, nên nó không dùng được làm
     * phép tự kiểm trên mọi bản dựng.
     *
     * ⚠️ Con số 1,6–2,0° từng đọc được ở p6/p7 KHÔNG phải nhiễu của bộ đo, và
     * đây là chỗ tôi đoán sai một lần rồi phải sửa. Phép thử: để cảnh lắng
     * thêm 2 giây rồi mới mở cửa sổ ⇒ thu được **0 khung**, vì renderer chỉ vẽ
     * khi có việc. Nghĩa là những khung ấy CÓ THẬT, và chúng là đuôi damping
     * của `OrbitControls` còn chạy nốt sau loạt bấm "Bước sau". Nên cửa sổ
     * phải mở SAU khi cảnh lắng, nếu không nó đo chuyển động của chính mình. */
    yenTong: tongGocKhung(yen.tuThe),
    /* Vòng đo QUANH CHÍNH TRỤC đã đo, không quanh Z mặc định — xem
       `vongQuanhTruc`. Trên bản quay quanh Y, cách cũ đọc 12° cho một cú kéo
       cả nghìn độ. */
    vongNgangDo: vongQuanhTruc(vong.tuThe, trucQuay(vong.tuThe).vec),
    nhieuVongDo: vongQuanhTruc(nhieuVong.tuThe, trucQuay(nhieuVong.tuThe).vec),
    chuanTruc: trucQuay(vong.tuThe).chuan,
    trucQuayVec: trucQuay(vong.tuThe).vec,
    trucTen: tenTruc(trucQuay(vong.tuThe).vec),
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

/**
 * `dist/` phải MỚI HƠN `src/`, nếu không cổng đang đo một bản dựng cũ.
 *
 * ⚠️ Đây là bản sửa của một kết luận SAI đã xảy ra thật trong wave này: một
 * phép tiêm lỗi không biên dịch được, `npm run build` đỏ, `--bo-qua-build` bỏ
 * qua, và cổng đo `dist/` của **phép tiêm TRƯỚC ĐÓ** — trả về đúng trạng thái
 * lỗi nhưng của sai nguyên nhân. Cổng `build-freshness` cũ đã đi theo nhánh
 * prototype bị từ chối; đây là chỗ nó quay lại.
 */
export function kiemDistMoi() {
  const moiNhat = (thu) => {
    let t = 0;
    const di = (d) => {
      for (const e of readdirSync(d, { withFileTypes: true })) {
        if (e.name === "node_modules" || e.name.startsWith(".")) continue;
        const f = join(d, e.name);
        if (e.isDirectory()) di(f);
        else t = Math.max(t, statSync(f).mtimeMs);
      }
    };
    if (existsSync(thu)) di(thu);
    return t;
  };
  const tDist = moiNhat(DIST);
  const tSrc = moiNhat(join(FE, "src"));
  if (tDist === 0) throw new Error("DIST_THIEU — chưa có bản dựng nào để đo.");
  if (tSrc > tDist) {
    throw new Error("DIST_CU — `dist/` cũ hơn `src/` "
      + `(${Math.round((tSrc - tDist) / 1000)} s). Chạy \`npm run build\` trước, `
      + "và ĐỪNG tin số đo nào cho tới lúc ấy.");
  }
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"] && !DIST_NGOAI) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  if (!DIST_NGOAI) kiemDistMoi();
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
        + `trục=${r.trucTen}${JSON.stringify(r.trucQuayVec)} ‖${r.chuanTruc.toFixed(3)}‖  `
        + `cos∈[${r.cucMin.toFixed(2)},${r.cucMax.toFixed(2)}]  `
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
